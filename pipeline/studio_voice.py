"""'Studio voice' without AI: classic signal processing only.

  1. De-reverb: WPE (weighted prediction error, Nakatani et al. 2010). A linear-prediction filter estimated from
     the recording itself predicts the room's late echo from the past few frames and subtracts it. No trained
     model, nothing learned from other voices.
  2. Broadcast EQ: rumble cut, a little low-end warmth (like a close mic's proximity effect), less boxiness
     (300-500 Hz is where small rooms ring), presence for clarity, a gentle 'air' shelf.
  3. Two-stage compression (fast peaks + slow leveling) for an even, up-front voice.
  4. A touch of soft saturation (tape-style harmonics, 15% wet) for density.
  5. Downward expander: the room tail between words is pulled down a little more.

Applied in pipeline/tts.py after noise cleanup when the episode's scenes.yaml has `voice_style: studio`
(or STUDIO_VOICE=1). `python -m pipeline.studio_voice episodes/<slug> <ids...>` writes A/B samples.
"""
import sys
from pathlib import Path

import numpy as np

SR = 48000


def dereverb(a, taps=10, delay=3, iterations=3):
    from nara_wpe.wpe import wpe
    from nara_wpe.utils import stft, istft
    size, shift = 1024, 256
    Y = stft(a[None, :], size=size, shift=shift).transpose(2, 0, 1)      # (freq, ch, frames)
    Z = wpe(Y, taps=taps, delay=delay, iterations=iterations, statistics_mode="full").transpose(1, 2, 0)
    z = istft(Z, size=size, shift=shift)[0][: len(a)]
    if len(z) < len(a):
        z = np.pad(z, (0, len(a) - len(z)))
    return z.astype(np.float32)


EQ = ("highpass=f=75,"
      "lowshelf=f=140:g=2.5,"                  # warmth / proximity
      "equalizer=f=380:t=q:w=1.1:g=-3.5,"      # boxy small-room resonance
      "equalizer=f=900:t=q:w=1.4:g=-1.2,"      # nasal 'phone' honk
      "equalizer=f=3400:t=q:w=1.0:g=2.5,"      # presence / intelligibility
      "highshelf=f=10000:g=2.5,"               # air
      "deesser=i=0.35")
COMP = ("acompressor=threshold=-20dB:ratio=3.5:attack=3:release=60:makeup=2,"     # peaks
        "acompressor=threshold=-26dB:ratio=2:attack=40:release=350:makeup=2")      # leveling


def saturate(a, drive=1.6, mix=0.15):
    pk = np.abs(a).max() + 1e-9
    x = a / pk
    return (pk * ((1 - mix) * x + mix * np.tanh(drive * x) / np.tanh(drive))).astype(np.float32)


def expander(a, thresh_db=-46, ratio=1.8, win=0.01):
    hop = int(SR * win); n = len(a) // hop
    if n < 3:
        return a
    db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    g_db = np.where(db < thresh_db, (db - thresh_db) * (ratio - 1), 0.0)
    g = 10 ** (np.convolve(np.pad(g_db, 4, mode="edge"), np.ones(9) / 9, "valid") / 20)
    return (a * np.interp(np.arange(len(a)), np.arange(n) * hop + hop / 2, g)).astype(np.float32)


def _floor_and_speech(a, win=0.03):
    hop = int(SR * win); n = len(a) // hop
    db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    return float(np.percentile(db, 10)), float(np.percentile(db, 90))


def studio(a, reverb=True):
    """Studio chain that never makes the background louder relative to the voice: compression lifts quiet
    parts (room noise too), so afterwards the noise between words is pulled back down to the line's
    original voice-to-noise distance."""
    from .voice_clean import ffilter
    from .match_voice import match_floor
    if reverb:
        a = dereverb(a)
    f0, s0 = _floor_and_speech(a)
    a = ffilter(a, EQ + "," + COMP)
    a = saturate(a)
    f1, s1 = _floor_and_speech(a)
    target = s1 - (s0 - f0)                       # same speech-to-noise gap as before processing
    a = match_floor(a, f1, target, reach=6)       # only the floor itself: word tails above it stay natural
    return (a / (np.abs(a).max() + 1e-9) * 0.89).astype(np.float32)


def main():
    """A/B file: for each line -> current | EQ+compression | de-reverb+EQ+compression, separated by beeps."""
    from .voice_clean import clean, load
    from .match_voice import level
    from .tts import write_wav
    ep = Path(sys.argv[1]); vd = ep / "voice"; ids = sys.argv[2:]
    room = load(vd / "_roomtone.wav")
    beep = (0.15 * np.sin(2 * np.pi * 880 * np.arange(int(0.12 * SR)) / SR)).astype(np.float32)
    gap = np.zeros(int(0.5 * SR), np.float32)
    out = []
    for lid in ids:
        src = vd / "_orig" / f"{lid}.wav"
        raw = load(src if src.exists() else vd / f"{lid}.wav")
        cur = level(clean(raw, room, do_trim=False))
        for k, x in enumerate((cur, level(studio(clean(raw, room, do_trim=False), reverb=False)),
                               level(studio(clean(dereverb(raw), room, do_trim=False), reverb=False)))):
            out += [beep] * (k + 1) + [gap, x, gap, gap]
    path = ep / "out" / "review" / "voice-ab.wav"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_wav(path, np.concatenate(out))
    print("wrote", path)


if __name__ == "__main__":
    main()
