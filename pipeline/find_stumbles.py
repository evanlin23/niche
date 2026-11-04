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


def find_cuts(words, script_text, max_back=40):
    """Restart = the speaker goes back and re-says words they just said: tokens [i, j) are an abandoned
    attempt when toks[j:j+m] == toks[i:i+m] (m >= 2, or m == 1 when the attempt is one word) and that
    repetition isn't in the script. Cut [start of i, start of j). Fillers are cut too."""
    toks = [(norm(w), s, e) for w, s, e in words if norm(w)]
    script = " " + " ".join(norm(w) for w in script_text.split()) + " "
    cuts, notes = [], []
    j, floor = 1, 0
    while j < len(toks):
        if toks[j - 1][0] in FILLERS:
            cuts.append((toks[j - 1][1] - 0.02, toks[j - 1][2] + 0.02)); notes.append(f"filler '{toks[j-1][0]}' @{toks[j-1][1]:.2f}")
        best = None
        for i in range(max(floor, j - max_back), j):         # earliest restart point wins (longest abandoned attempt)
            m = 0
            while j + m < len(toks) and i + m < j and toks[i + m][0] == toks[j + m][0]:
                m += 1
            need = 1 if j - i == 1 else 2 if j - i <= 3 else 3   # long abandoned attempts need a 3-word match
            if m >= need:
                rep = " " + " ".join(t[0] for t in toks[i:j]) + " " + " ".join(t[0] for t in toks[j:j + m]) + " "
                if rep in script or (j - i == 1 and toks[i][0] in ("that", "had", "is", "one")):
                    continue
                phrase = " " + " ".join(t[0] for t in toks[j:j + m]) + " "
                if script.count(phrase) >= 2:            # the script itself repeats it ("take away its ...")
                    continue
                best, m_best = i, m
                break
        if best is not None:
            # words just before the restart that the script needs there (speaker started mid-line, then went
            # back to the start: "it dodges ... The Normal Player plays ... It dodges ...") are kept
            sw = script.split(); ph = [t[0] for t in toks[j:j + m_best]]
            k = j
            for p in range(len(sw) - len(ph) + 1):
                if sw[p:p + len(ph)] == ph:
                    r = 0
                    while j - 1 - r > best and p - 1 - r >= 0 and toks[j - 1 - r][0] == sw[p - 1 - r]:
                        r += 1
                    k = j - r if r >= 3 else j
                    break
            s0, e0 = toks[best][1], toks[k][1]
            cuts.append((s0 - 0.02, e0 - 0.03))
            notes.append(f"restart '{' '.join(t[0] for t in toks[best:j])}' @{s0:.2f}-{e0:.2f}")
            floor = j                                 # the kept attempt can't be cut by a later match
            j += max(1, m_best)                       # skip past the repeated words (no shifted re-detections)
            continue
        j += 1
    # merge overlapping cuts
    cuts.sort(); merged = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]))
        else:
            merged.append(c)
    return merged, notes


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
