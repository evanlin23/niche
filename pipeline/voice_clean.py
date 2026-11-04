"""Clean up a home voice recording (phone/laptop mic, noisy room).

    python -m pipeline.voice_clean in.m4a out.wav [--noise-from 0.5 --noise-to 12]

Chain: high-pass (rumble) -> spectral-gating noise reduction learned from a room-tone clip
(the quietest stretch, or the range you give) -> gentle de-ess + compression -> trim -> normalise.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import numpy as np

SR = 48000


def load(path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
                          "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def ffilter(a: np.ndarray, af: str) -> np.ndarray:
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-i", "-",
                        "-af", af, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       input=a.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def frames_db(a, win=0.05):
    w = int(win * SR)
    n = len(a) // w
    return np.array([20 * np.log10(np.sqrt(np.mean(a[i * w:(i + 1) * w] ** 2)) + 1e-9) for i in range(n)]), w


def room_tone(a, seconds=1.5):
    """Quietest contiguous stretch (used as the noise profile)."""
    db, w = frames_db(a)
    k = max(1, int(seconds / 0.05))
    if len(db) <= k:
        return a
    s = np.convolve(db, np.ones(k) / k, mode="valid")
    i = int(np.argmin(s))
    return a[i * w:(i + k) * w]


def trim(a, pad=0.15, thresh_below_peak=30, max_gap=0.7):
    """Keep the main spoken phrase: grow outwards from the loudest moment, bridging pauses < max_gap."""
    db, w = frames_db(a, 0.02)
    act = db > db.max() - thresh_below_peak
    peak = int(np.argmax(db))
    gap = int(max_gap / 0.02)
    s = e = peak
    i = peak
    while i > 0:
        j = i - 1
        while j >= 0 and not act[j] and i - j <= gap:
            j -= 1
        if j < 0 or not act[j]:
            break
        s = i = j
    i = peak
    while i < len(act) - 1:
        j = i + 1
        while j < len(act) and not act[j] and j - i <= gap:
            j += 1
        if j >= len(act) or not act[j]:
            break
        e = i = j
    return a[max(0, s * w - int(pad * SR)):min(len(a), (e + 1) * w + int(pad * SR))]


def clean(a: np.ndarray, noise: np.ndarray | None = None, strength=0.9) -> np.ndarray:
    import noisereduce as nr
    a = ffilter(a, "highpass=f=80,lowpass=f=15000")
    noise = room_tone(a) if noise is None else ffilter(noise, "highpass=f=80,lowpass=f=15000")
    a = nr.reduce_noise(y=a, sr=SR, y_noise=noise, stationary=True, prop_decrease=strength,
                        n_fft=2048, freq_mask_smooth_hz=300, time_mask_smooth_ms=60)
    # voice polish: de-ess, gentle compression, presence
    a = ffilter(a, "deesser=i=0.4,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=4,"
                   "equalizer=f=180:t=q:w=1:g=-2,equalizer=f=4000:t=q:w=1:g=1.5")
    a = trim(a)
    return (a / (np.abs(a).max() + 1e-9) * 0.89).astype(np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("dst")
    ap.add_argument("--noise-from", type=float); ap.add_argument("--noise-to", type=float)
    ap.add_argument("--strength", type=float, default=0.9)
    a = ap.parse_args()
    x = load(a.src)
    noise = x[int(a.noise_from * SR):int(a.noise_to * SR)] if a.noise_from is not None else None
    y = clean(x, noise, a.strength)
    from pipeline.tts import write_wav
    write_wav(Path(a.dst), y, SR)
    print(f"wrote {a.dst} ({len(y) / SR:.1f}s)")


if __name__ == "__main__":
    main()
