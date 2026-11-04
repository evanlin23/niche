"""Make every recording session sound like one session.

Lines recorded on different days (pick-ups, re-records) differ in room noise, mic distance (tone) and level.
Each line's <id>.json may carry "session": "<name>" (default "main"); that session's room tone lives in
_roomtone_<name>.wav (main: _roomtone.wav).

    python -m pipeline.match_voice episodes/<slug>/voice

measures the long-term spectrum of the cleaned speech per session and writes _match.json with an EQ curve
(1/3-octave, +-8 dB, 100 Hz-12 kHz) that maps each session onto the main one. pipeline/tts.py applies it
(after noise cleanup) together with level(): every line is set to the same active speech level.
"""
import json
import sys
from pathlib import Path

import numpy as np

SR = 48000
TARGET_DB = -20.0          # active speech level (dBFS RMS of the voiced frames)


def voiced(a, win=0.03):
    hop = int(SR * win); n = len(a) // hop
    if n == 0:
        return a
    fr = a[: n * hop].reshape(n, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    return fr[db > db.max() - 30].ravel()


def level(a):
    """Same loudness for every line: active speech RMS -> TARGET_DB, peaks soft-limited below -1 dBFS."""
    v = voiced(a)
    rms = np.sqrt(np.mean(v ** 2)) + 1e-9
    a = a * (10 ** (TARGET_DB / 20) / rms)
    lim = 0.89
    return np.where(np.abs(a) > lim * 0.8, np.sign(a) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(a) - lim * 0.8) / (lim * 0.2))), a).astype(np.float32)


def floor_db(a, win=0.03):
    hop = int(SR * win); n = len(a) // hop
    db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    return float(np.percentile(db, 10))


def match_floor(a, cur, target, win=0.01, reach=14):
    """Downward expander: pull the quiet frames (room noise between words) from `cur` down to `target` dB,
    leaving speech untouched (full effect 0-4 dB above the floor, fading out by 14 dB above it)."""
    drop = cur - target
    if drop <= 1.0:
        return a
    hop = int(SR * win); n = len(a) // hop
    db = 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    k = np.clip((cur + reach - db) / max(reach - 4, 2), 0, 1)  # 1 near the floor, 0 for speech
    g = 10 ** (-drop * k / 20)
    g = np.convolve(np.pad(g, 3, mode="edge"), np.ones(7) / 7, "valid")   # ~70 ms smoothing, no pumping
    gs = np.interp(np.arange(len(a)), np.arange(n) * hop + hop / 2, g)
    return (a * gs).astype(np.float32)


def bands():
    c = 100 * 2 ** (np.arange(0, 22) / 3)       # 100 Hz .. ~12.7 kHz, 1/3 octave
    return c[c <= 12700]


def ltas(chunks):
    """Long-term average spectrum (dB) of voiced speech, per 1/3-octave band."""
    n = 4096; win = np.hanning(n); acc = np.zeros(n // 2 + 1); k = 0
    for a in chunks:
        v = voiced(a)
        for i in range(0, len(v) - n, n // 2):
            acc += np.abs(np.fft.rfft(v[i:i + n] * win)) ** 2; k += 1
    f = np.fft.rfftfreq(n, 1 / SR); p = acc / max(k, 1)
    out = []
    for c in bands():
        m = (f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))
        out.append(10 * np.log10(p[m].mean() + 1e-20))
    return np.array(out)


def apply_eq(a, curve):
    """Zero-phase EQ: interpolate the band gains (dB) over the FFT of the whole line."""
    if not curve:
        return a
    f = np.fft.rfftfreq(len(a), 1 / SR)
    g = np.interp(np.log2(np.maximum(f, 1)), np.log2(curve["f"]), curve["g"], left=curve["g"][0], right=curve["g"][-1])
    return np.fft.irfft(np.fft.rfft(a) * 10 ** (g / 20), len(a)).astype(np.float32)


def session_of(meta):
    return meta.get("session", "main")


def roomtone_path(d: Path, session):
    return d / ("_roomtone.wav" if session == "main" else f"_roomtone_{session}.wav")


def main():
    from .voice_clean import clean, load
    d = Path(sys.argv[1])
    groups = {}
    for js in sorted(d.glob("*.json")):
        if js.name.startswith("_") or not js.with_suffix(".wav").exists():
            continue
        groups.setdefault(session_of(json.loads(js.read_text())), []).append(js.with_suffix(".wav"))
    spec, floors = {}, {}
    for s, wavs in groups.items():
        rt = roomtone_path(d, s)
        noise = load(rt) if rt.exists() else None
        cl = [clean(load(w), noise, do_trim=False) for w in wavs]
        spec[s] = ltas(cl)
        floors[s] = float(np.median([floor_db(level(x)) for x in cl]))
        print(f"session {s}: {len(wavs)} lines, noise floor {floors[s]:.1f} dB")
    out = {}
    ref = spec.get("main")
    for s, sp in spec.items():
        if s == "main" or ref is None:
            continue
        diff = ref - sp
        diff -= np.median(diff)                                  # level is handled separately
        diff = np.convolve(np.pad(diff, 1, mode="edge"), [0.25, 0.5, 0.25], "valid")   # smooth
        diff = np.clip(diff, -8, 8)
        out[s] = {"f": bands().round(1).tolist(), "g": diff.round(2).tolist(),
                  "floor": round(floors[s], 1), "target_floor": round(floors["main"], 1)}
        print(f"  {s} -> main EQ (dB): " + " ".join(f"{f:.0f}:{g:+.1f}" for f, g in zip(bands(), diff)))
    (d / "_match.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
