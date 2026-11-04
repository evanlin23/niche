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


def shifter(cuts):
    """Map a time in the uncut audio to the cut audio."""
    def shift(t):
        d = 0.0
        for s, e in cuts:
            if t >= e:
                d += e - s
            elif t > s:
                return s - d
        return t - d
    return shift


def join_points(cuts):
    """Where each cut's join lands in the cut audio."""
    sh = shifter(cuts)
    return [sh(e) for s, e in cuts]


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
    pause_shift = shifter(sorted(cuts)); s0 = 0.0
    # lead / tail from the AUDIO (first / last loud frame), never from the transcript: a transcript that
    # stops early must not chop the end of the line off
    hop = int(sr * FRAME); n = len(a) // hop
    if n:
        e = 20 * np.log10(np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
        loud = np.flatnonzero(e > np.percentile(e, 95) - 32)
        if len(loud):
            s0 = max(0.0, loud[0] * FRAME - lead)
            e1 = min(len(a) / sr, (loud[-1] + 1) * FRAME + tail)
            a = a[int(s0 * sr): int(e1 * sr)]
            words = [(w, round(max(0.0, s - s0), 3), round(min(e1 - s0, e - s0), 3)) for w, s, e in words]
    return a, words, (lambda t: pause_shift(t) - s0)


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
        vw = vwords.get(js.stem)
        if vw and meta["words"] and vw[-1][2] < meta["words"][-1][2] - 0.6:
            print(f"  {js.stem}: verbatim transcript stops early, using the original word timings")
            vw = None
        words = [tuple(w) for w in (vw or meta["words"])]
        words = [w for w in words if any(ch.isalnum() for ch in w[0])]
        before += len(audio) / sr
        lc = sorted((max(0.0, x), y) for x, y in cuts.get(js.stem, []))
        audio, words = apply_cuts(audio, sr, words, [tuple(c) for c in lc])
        joins = join_points(lc)
        audio, words, mapper = tighten(audio, sr, words, a.max_pause)
        meta["stumble_cuts"] = [round(mapper(t), 3) for t in joins]   # where each stumble cut lands (s)
        after += len(audio) / sr
        sf.write(wav, audio, sr)
        meta.update(duration=round(len(audio) / sr, 3), words=[list(w) for w in words])
        js.write_text(json.dumps(meta))
    print(f"narration {before:.1f}s -> {after:.1f}s ({before - after:.1f}s of pauses removed)")


if __name__ == "__main__":
    main()
