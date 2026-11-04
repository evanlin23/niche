"""Restore word endings (and beginnings) that the first split chopped off.

The splitter cut each line where the SCRIPT said it ended; when the speaker said a little more ("...come back to
it later", "25 percent"), or a word's decay ran past the cut, the clip ends mid-sound. This finds each line's
_orig clip inside the original long recordings (normalized cross-correlation of the clip's last/first second)
and extends it from the source while the sound is still going, stopping at the first real pause (60 ms near the
noise floor), at most --max-ext seconds. Takes, splices and order are untouched.

    python -m pipeline.extend_tails episodes/<slug> rec1.m4a [rec2.m4a ...] [--max-ext 1.2]
Run before tighten_voice (it rewrites voice/_orig/<id>.wav + .json, keeping a backup in voice/_orig_pre_extend/).
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
DS = 8000


def load(path):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def down(a):
    from scipy.signal import resample_poly
    return resample_poly(a, 1, SR // DS).astype(np.float32)


def locate(template, src_ds):
    """Best normalized-correlation match of template (48k) in a downsampled source. Returns (pos_s, score)."""
    from scipy.signal import fftconvolve
    t = down(template); t = t - t.mean(); tn = np.linalg.norm(t) + 1e-9
    corr = fftconvolve(src_ds, t[::-1], mode="valid")
    s2 = np.concatenate([[0.0], np.cumsum(src_ds.astype(np.float64) ** 2)])
    win = np.sqrt(np.maximum(s2[len(t):] - s2[:-len(t)], 1e-12))
    nc = corr / (win[: len(corr)] * tn)
    i = int(np.argmax(nc))
    return i / DS, float(nc[i])


def frame_db(a, win=0.01):
    hop = int(SR * win); n = len(a) // hop
    return 20 * np.log10(np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("recordings", nargs="+")
    ap.add_argument("--max-ext", type=float, default=1.2)
    ap.add_argument("--lines", nargs="*")
    a = ap.parse_args()
    ep = Path(a.episode); od = ep / "voice" / "_orig"; bk = ep / "voice" / "_orig_pre_extend"; bk.mkdir(exist_ok=True)
    srcs = [(Path(r).name, load(r)) for r in a.recordings]
    srcs_ds = [(n, x, down(x)) for n, x in srcs]
    floor = {n: np.percentile(frame_db(x), 10) for n, x, _ in srcs_ds}
    for js in sorted(od.glob("*.json")):
        lid = js.stem
        if a.lines and lid not in a.lines:
            continue
        wav = od / f"{lid}.wav"
        if not wav.exists():
            continue
        clip, _ = sf.read(wav, dtype="float32")
        L = min(len(clip), SR)
        best = None
        for n, x, xd in srcs_ds:                     # where does the clip's END come from?
            pos, sc = locate(clip[-L:], xd)
            if best is None or sc > best[2]:
                best = (n, x, sc, pos)
        n, x, sc, pos = best
        added_tail = added_head = 0.0
        if sc > 0.8:
            end_src = pos + L / SR                    # source time where the clip currently ends
            db = frame_db(x); fl = floor[n]
            i = int(end_src / 0.01); k = 0; quiet = 0
            while i + k < len(db) and k * 0.01 < a.max_ext:
                quiet = quiet + 1 if db[i + k] < fl + 6 else 0
                if quiet >= 6:
                    break
                k += 1
            ext = max(0, k - quiet) * 0.01
            if ext >= 0.03:
                extra = x[int(end_src * SR): int((end_src + ext + 0.05) * SR)]
                f = int(0.03 * SR); extra = extra.copy(); extra[-f:] *= np.linspace(1, 0, f)
                clip = np.concatenate([clip, extra]); added_tail = ext
        # beginning: same idea, backwards
        best = None
        for n2, x2, xd2 in srcs_ds:
            pos2, sc2 = locate(clip[:L], xd2)
            if best is None or sc2 > best[2]:
                best = (n2, x2, sc2, pos2)
        n2, x2, sc2, pos2 = best
        if sc2 > 0.8:
            db = frame_db(x2); fl = floor[n2]
            i = int(pos2 / 0.01); k = 0; quiet = 0
            while i - k - 1 >= 0 and k * 0.01 < 0.15:   # only a word's soft onset: longer pulls in the previous take
                quiet = quiet + 1 if db[i - k - 1] < fl + 6 else 0
                if quiet >= 6:
                    break
                k += 1
            ext = max(0, k - quiet) * 0.01
            if ext >= 0.03:
                extra = x2[int((pos2 - ext - 0.03) * SR): int(pos2 * SR)].copy()
                f = int(0.02 * SR); extra[:f] *= np.linspace(0, 1, f)
                clip = np.concatenate([extra, clip]); added_head = len(extra) / SR
        if added_tail or added_head:
            for p in (wav, js):
                if not (bk / p.name).exists():
                    shutil.copy2(p, bk / p.name)
            meta = json.loads(js.read_text())
            meta["words"] = [[w, round(s + added_head, 3), round(e + added_head, 3)] for w, s, e in meta["words"]]
            meta["duration"] = round(len(clip) / SR, 3)
            meta["extended"] = {"head": round(added_head, 3), "tail": round(added_tail, 3), "source": n}
            sf.write(wav, clip, SR); js.write_text(json.dumps(meta))
            if added_head:                            # keep stumble cuts / verbatim timings in sync with the clip
                for name in ("_stumbles.json", "_verbatim.json"):
                    pth = ep / "voice" / name
                    if pth.exists():
                        d = json.loads(pth.read_text())
                        if d.get(lid):
                            d[lid] = [[x[0] + added_head, x[1] + added_head] if name == "_stumbles.json"
                                      else [x[0], x[1] + added_head, x[2] + added_head] for x in d[lid]]
                            pth.write_text(json.dumps(d))
        print(f"{lid:4s} end match {sc:.2f} in {n[:18]:18s} +tail {added_tail:.2f}s  +head {added_head:.2f}s", flush=True)


if __name__ == "__main__":
    main()
