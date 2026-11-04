"""Find stumbles in recorded lines and write cut ranges for pipeline/tighten_voice.py.

Normal transcription (what split_recording uses) silently cleans up disfluencies: "the best of - the best of
them" comes back as "the best of them". So this re-transcribes each line *verbatim* (Whisper primed with a
disfluent prompt) and looks for:
  - restarts: a phrase immediately said again ("the best of | the best of them") -> cut the first attempt
  - fillers: um / uh / er / hmm -> cut
Only repeats that are NOT in the script are cut (so "had had" in a script survives).

    python -m pipeline.find_stumbles episodes/<slug> [--lines o4 b2]   -> episodes/<slug>/voice/_stumbles.json
Then: python -m pipeline.tighten_voice episodes/<slug>/voice --cuts episodes/<slug>/voice/_stumbles.json
Uses voice/_orig/<id>.wav when present (times then refer to the original files, as tighten_voice expects).
"""
import argparse
import json
import re
from math import gcd
from pathlib import Path

import numpy as np
import soundfile as sf

PROMPT = "Umm, let me think like, hmm... Okay, here's what, uh, I- I saw. The the thing is, um, you know."
FILLERS = {"um", "umm", "uh", "uhh", "er", "erm", "hmm", "mm", "ah"}
norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())


def load16(p):
    from scipy.signal import resample_poly
    a, sr = sf.read(p, dtype="float32")
    a = a if a.ndim == 1 else a.mean(1)
    g = gcd(sr, 16000)
    return resample_poly(a, 16000 // g, sr // g).astype("float32")


def verbatim(model, path):
    segs, _ = model.transcribe(load16(path), language="en", word_timestamps=True, initial_prompt=PROMPT,
                               condition_on_previous_text=False, beam_size=5)
    return [(w.word.strip(), float(w.start), float(w.end)) for s in segs for w in s.words]


def find_cuts(words, script_text):
    toks = [(norm(w), s, e) for w, s, e in words if norm(w)]
    script = " " + " ".join(norm(w) for w in script_text.split()) + " "
    cuts, notes, i = [], [], 0
    while i < len(toks):
        if toks[i][0] in FILLERS:
            cuts.append((toks[i][1] - 0.02, toks[i][2] + 0.02)); notes.append(f"filler '{toks[i][0]}' @{toks[i][1]:.2f}")
            i += 1; continue
        hit = None
        for k in range(min(6, (len(toks) - i) // 2), 0, -1):   # longest repeated phrase first
            a = [t[0] for t in toks[i:i + k]]
            b = [t[0] for t in toks[i + k:i + 2 * k]]
            if a == b and (" " + " ".join(a + b) + " ") not in script:
                if k == 1 and a[0] in ("that", "had", "is"):
                    continue
                hit = k; break
            # partial restart: "the best of | the best of them" also matches above; "wor- | worst" = prefix
            if k == 1 and b and a[0] and b[0].startswith(a[0]) and a[0] != b[0] and len(a[0]) <= 4:
                hit = 1; break
        if hit:
            s, e = toks[i][1], toks[i + hit][1]
            cuts.append((s - 0.02, e - 0.03))
            notes.append(f"restart '{' '.join(t[0] for t in toks[i:i + hit])}' @{s:.2f}-{e:.2f}")
            i += hit
        else:
            i += 1
    return cuts, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--lines", nargs="*")
    ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    ep = Path(a.episode); vd = ep / "voice"
    script = {m.group(1): m.group(2) for m in re.finditer(r"^\[(\w+)\] (.*)$", (ep / "script.md").read_text(), re.M)}
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    out_p = vd / "_stumbles.json"
    out = json.loads(out_p.read_text()) if out_p.exists() else {}
    report = []
    for lid in (a.lines or sorted(script)):
        src = vd / "_orig" / f"{lid}.wav"
        src = src if src.exists() else vd / f"{lid}.wav"
        if not src.exists():
            continue
        words = verbatim(model, src)
        cuts, notes = find_cuts(words, script[lid])
        out[lid] = [[round(s, 3), round(e, 3)] for s, e in cuts]
        if notes:
            report.append(f"{lid}: " + "; ".join(notes) + "\n    heard: " + " ".join(w for w, _, _ in words))
        print(lid, notes or "clean", flush=True)
    out_p.write_text(json.dumps(out, indent=1))
    (vd / "_stumbles.txt").write_text("\n".join(report) + "\n")
    print(f"{sum(1 for v in out.values() if v)} lines with stumbles -> {out_p}")


if __name__ == "__main__":
    main()
