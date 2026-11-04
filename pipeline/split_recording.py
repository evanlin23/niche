"""Split ONE long voice recording into per-line files, matched against script.md.

    python -m pipeline.split_recording episodes/<slug> path/to/recording.m4a [--model small.en]

- Transcribes with Whisper (word timestamps), then finds each script line in order.
- Retakes are fine: if you say a line more than once, the LAST take before the next line wins.
- Skipped lines are reported; the render fills them with the AI voice.
- Writes episodes/<slug>/voice/<id>.wav (raw cut) + <id>.json (word timings) + _roomtone.wav
  (quietest stretch, used as the noise profile when cleaning) + _report.txt.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
from pathlib import Path

import numpy as np

from .timeline import parse_script

SR = 48000


def norm(w: str) -> str:
    return re.sub(r"[^a-z0-9]", "", w.lower())


def load(path, sr):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def transcribe(audio16, model_name):
    from faster_whisper import WhisperModel
    m = WhisperModel(model_name, compute_type="int8")
    segs, _ = m.transcribe(audio16, word_timestamps=True, vad_filter=True)
    words = []
    for s in segs:
        for w in s.words:
            if norm(w.word):
                words.append((norm(w.word), w.start, w.end, w.word.strip()))
    return words


def similarity(a: list[str], b: list[str]) -> float:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def takes(line_words, words, threshold):
    """Distinct takes of a line in the transcript: (start, end, score). Overlapping windows
    are clustered and only the best window of each cluster is kept."""
    n = len(line_words)
    raw = []
    for i in range(len(words)):
        if difflib.SequenceMatcher(None, words[i][0], line_words[0]).ratio() < 0.5 and \
           difflib.SequenceMatcher(None, words[i][0], line_words[min(1, n - 1)]).ratio() < 0.5:
            continue
        best = (0.0, 0)
        for L in range(max(1, n - 3), n + 4):
            if i + L > len(words):
                break
            sc = similarity(line_words, [w[0] for w in words[i:i + L]])
            if sc > best[0]:
                best = (sc, L)
        if best[0] >= threshold:
            raw.append((i, i + best[1], best[0]))
    out = []
    for c in sorted(raw):
        if out and c[0] < out[-1][1] - max(1, n // 3):     # overlaps previous take -> same take
            if c[2] > out[-1][2]:
                out[-1] = c
        else:
            out.append(c)
    return out


def align(lines: dict[str, str], words, threshold=0.6):
    """Pick at most one take per line, in script order, maximising total match.
    Ties go to LATER takes (so a retake beats the botched first attempt)."""
    ids = list(lines)
    toks = {k: [norm(w) for w in v.split() if norm(w)] for k, v in lines.items()}
    T = max(1, len(words))
    # states: list of (end_index, total, picks) on a Pareto front
    states = [(0, 0.0, {})]
    for lid in ids:
        new = list(states)                       # skipping this line is allowed
        for (s0, e0, sc) in takes(toks[lid], words, threshold):
            prior = [st for st in states if st[0] <= s0]
            if not prior:
                continue
            b = max(prior, key=lambda st: st[1])
            gain = sc + 0.05 * s0 / T            # small bonus for later takes
            new.append((e0, b[1] + gain, {**b[2], lid: (s0, e0, sc)}))
        new.sort(key=lambda st: (st[0], -st[1]))
        front, best = [], -1.0
        for st in new:                           # keep states not dominated (earlier end & higher total)
            if st[1] > best + 1e-9:
                front.append(st); best = st[1]
        states = front
    picks = max(states, key=lambda st: st[1])[2]
    result = {}
    for lid in ids:
        if lid in picks:
            s0, e0, sc = picks[lid]
            n_takes = len([t for t in takes(toks[lid], words, threshold)])
            result[lid] = {"start_w": s0, "end_w": e0, "score": sc, "takes": n_takes}
        else:
            result[lid] = None
    return result


def room_tone(a, sr, seconds=2.0):
    w = int(0.05 * sr)
    db = np.array([20 * np.log10(np.sqrt(np.mean(a[i * w:(i + 1) * w] ** 2)) + 1e-9) for i in range(len(a) // w)])
    k = int(seconds / 0.05)
    s = np.convolve(db, np.ones(k) / k, mode="valid")
    i = int(np.argmin(s))
    return a[i * w:(i + k) * w]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("recording")
    ap.add_argument("--model", default="small.en")
    a = ap.parse_args()
    ep = Path(a.episode)
    out = ep / "voice"
    out.mkdir(parents=True, exist_ok=True)
    lines = parse_script(ep / "script.md")
    full = load(a.recording, SR)
    words = transcribe(load(a.recording, 16000), a.model)
    al = align(lines, words)
    from .tts import write_wav
    write_wav(out / "_roomtone.wav", room_tone(full, SR))
    report = []
    for lid, m in al.items():
        if m is None:
            report.append(f"MISSING  [{lid}] {lines[lid][:60]}")
            continue
        ws = words[m["start_w"]:m["end_w"]]
        s, e = max(0.0, ws[0][1] - 0.15), ws[-1][2] + 0.3
        write_wav(out / f"{lid}.wav", full[int(s * SR):int(e * SR)])
        (out / f"{lid}.json").write_text(json.dumps({"duration": e - s, "words": [(w[3], w[1] - s, w[2] - s) for w in ws]}))
        flag = "CHECK " if m["score"] < 0.8 else "ok    "
        tk = f" ({m['takes']} takes, used the best/last)" if m["takes"] > 1 else ""
        report.append(f"{flag}  [{lid}] {e - s:5.1f}s  match {m['score']:.2f}{tk}")
    (out / "_report.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    found = sum(1 for m in al.values() if m)
    print(f"\n{found}/{len(lines)} lines found. Files in {out}/")


if __name__ == "__main__":
    main()
