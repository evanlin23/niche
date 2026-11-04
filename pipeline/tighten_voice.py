"""Tighten recorded narration: shorter pauses inside lines, trimmed lead/tail, optional cuts (stumbles).

Rewrites VOICE_DIR/<id>.wav and <id>.json in place (word timings shifted to match), keeping the untouched
originals in VOICE_DIR/_orig/ the first time it runs, so it can always be re-run from the originals.

    python -m pipeline.tighten_voice episodes/<slug>/voice [--max-pause 0.35] [--cuts cuts.json]

cuts.json: {"<line id>": [[start, end], ...]}  seconds in the ORIGINAL file, removed before tightening
(used for stumbles / false starts that the transcript doesn't show).
"""
import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME = 0.01


def silent_runs(a, sr, min_len):
    hop = int(sr * FRAME)
    n = len(a) // hop
    e = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1))
    db = 20 * np.log10(e + 1e-9)
    thr = np.percentile(db, 95) - 32          # 32 dB under the loud parts = pause
    sil = db < thr
    runs, i = [], 0
    while i < n:
        if sil[i]:
            j = i
            while j < n and sil[j]:
                j += 1
            if (j - i) * FRAME >= min_len:
                runs.append((i * FRAME, j * FRAME))
            i = j
        else:
            i += 1
    return runs


def apply_cuts(a, sr, words, cuts, fade=0.012):
    """Remove [s,e) ranges (seconds), crossfading the joins; shift/drop words."""
    cuts = sorted((max(0.0, s), min(len(a) / sr, e)) for s, e in cuts if e > s)
    if not cuts:
        return a, words
    keep, prev = [], 0.0
    for s, e in cuts:
        keep.append((prev, s)); prev = e
    keep.append((prev, len(a) / sr))
    f = int(sr * fade)
    out = []
    for s, e in keep:
        seg = a[int(s * sr): int(e * sr)].copy()
        if len(seg) > 2 * f:
            seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        out.append(seg)
    a2 = np.concatenate(out)

    def shift(t):
        d = 0.0
        for s, e in cuts:
            if t >= e:
                d += e - s
            elif t > s:
                return s - d
        return t - d
    w2 = []
    for w, s, e in words:
        if any(s >= cs and e <= ce for cs, ce in cuts):
            continue                              # word was inside a cut
        w2.append((w, round(shift(s), 3), round(shift(e), 3)))
    return a2, w2


def tighten(a, sr, words, max_pause=0.35, lead=0.08, tail=0.15):
    cuts = []
    for s, e in silent_runs(a, sr, max_pause + 0.1):
        if s <= 0.001 or e >= len(a) / sr - 0.001:
            continue                              # ends handled below
        mid = (s + e) / 2
        cuts.append((mid - (e - s - max_pause) / 2, mid + (e - s - max_pause) / 2))
    a, words = apply_cuts(a, sr, words, cuts)
    if words:                                     # lead / tail relative to the first / last word
        s0 = max(0.0, words[0][1] - lead)
        e1 = min(len(a) / sr, words[-1][2] + tail)
        a = a[int(s0 * sr): int(e1 * sr)]
        words = [(w, round(s - s0, 3), round(e - s0, 3)) for w, s, e in words]
    return a, words, sum(e - s for s, e in cuts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("voice_dir")
    ap.add_argument("--max-pause", type=float, default=0.35)
    ap.add_argument("--cuts", default=None)
    ap.add_argument("--words", default=None, help="verbatim word timings {id: [[w,s,e],...]} (find_stumbles)")
    a = ap.parse_args()
    d = Path(a.voice_dir); orig = d / "_orig"; orig.mkdir(exist_ok=True)
    cuts = json.loads(Path(a.cuts).read_text()) if a.cuts else {}
    vwords = json.loads(Path(a.words).read_text()) if a.words else {}
    before = after = 0.0
    for js in sorted(d.glob("*.json")):
        if js.name.startswith("_"):
            continue
        wav = js.with_suffix(".wav")
        if not wav.exists():
            continue
        for p in (wav, js):                       # originals kept once; always work from them
            if not (orig / p.name).exists():
                shutil.copy2(p, orig / p.name)
        audio, sr = sf.read(orig / wav.name, dtype="float32")
        meta = json.loads((orig / js.name).read_text())
        words = [tuple(w) for w in (vwords.get(js.stem) or meta["words"])]
        words = [w for w in words if any(ch.isalnum() for ch in w[0])]
        before += len(audio) / sr
        audio, words = apply_cuts(audio, sr, words, [tuple(c) for c in cuts.get(js.stem, [])])
        audio, words, _ = tighten(audio, sr, words, a.max_pause)
        after += len(audio) / sr
        sf.write(wav, audio, sr)
        meta.update(duration=round(len(audio) / sr, 3), words=[list(w) for w in words])
        js.write_text(json.dumps(meta))
    print(f"narration {before:.1f}s -> {after:.1f}s ({before - after:.1f}s of pauses removed)")


if __name__ == "__main__":
    main()
