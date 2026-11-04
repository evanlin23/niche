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


ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def say_int(n: int) -> list[str]:
    if n < 20:
        return [ONES[n]]
    if n < 100:
        return [TENS[n // 10]] + ([ONES[n % 10]] if n % 10 else [])
    if n < 1000:
        return [ONES[n // 100], "hundred"] + (say_int(n % 100) if n % 100 else [])
    for div, name in ((10**9, "billion"), (10**6, "million"), (1000, "thousand")):
        if n >= div:
            return say_int(n // div) + [name] + (say_int(n % div) if n % div else [])
    return [str(n)]


def spoken(token: str) -> list[str]:
    """'13.04%' -> thirteen point zero four percent ; '35' -> thirty five ; else [token]"""
    t = token.lower().replace(",", "")
    m = re.fullmatch(r"\$?(\d+)(?:\.(\d+))?(%?)", re.sub(r"[^\d.%$]", "", t)) if re.search(r"\d", t) else None
    if not m:
        return [token]
    out = say_int(int(m[1]))
    if m[2]:
        out += ["point"] + [ONES[int(d)] for d in m[2]]
    if m[3] or "percent" in t:
        out += ["percent"]
    return out


def norm(w: str) -> str:
    w = re.sub(r"[^a-z0-9]", "", w.lower())
    return {"oh": "zero", "o": "zero"}.get(w, w)


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


def expand_numbers(words):
    """Split digit tokens into spoken words (timing spread evenly) so they match the script."""
    merged = []
    for w in words:                      # Whisper sometimes splits "13.04%" into "13" + ".04%"
        n, s0, e0, raw = w
        if merged and re.match(r"^\.\d", raw) and re.fullmatch(r"\d+", merged[-1][3].strip()):
            p = merged[-1]
            merged[-1] = (p[0], p[1], e0, p[3].strip() + raw)
        else:
            merged.append(tuple(w))
    out = []
    for n, s0, e0, raw in merged:
        raw = raw.strip().rstrip(".,!?;:")
        parts = spoken(raw) if re.search(r"\d", raw) else [raw]
        if len(parts) == 1 and parts[0] == raw:
            out.append((n, s0, e0, raw)); continue
        d = (e0 - s0) / len(parts)
        for i, p in enumerate(parts):
            out.append((norm(p), s0 + i * d, s0 + (i + 1) * d, p))
    return out


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


def phrases(text: str, min_words=3):
    """Split a line at punctuation into phrases; merge tiny ones into a neighbour."""
    parts = [p.strip() for p in re.split(r"(?<=[.,;:?!])\s+", text) if p.strip()]
    out = []
    for p in parts:
        if out and (len(p.split()) < min_words or len(out[-1].split()) < min_words):
            out[-1] = out[-1] + " " + p
        else:
            out.append(p)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("recording")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--only", nargs="*", help="re-record mode: only match/replace these line ids")
    a = ap.parse_args()
    ep = Path(a.episode)
    out = ep / "voice"
    out.mkdir(parents=True, exist_ok=True)
    lines = parse_script(ep / "script.md")
    if a.only:
        lines = {k: v for k, v in lines.items() if k in a.only}
    full = load(a.recording, SR)
    cache = out / "_transcript.json"
    key = f"{Path(a.recording).stat().st_size}:{a.model}"
    if cache.exists() and json.loads(cache.read_text()).get("key") == key:
        words = [tuple(w) for w in json.loads(cache.read_text())["words"]]
    else:
        words = transcribe(load(a.recording, 16000), a.model)
        cache.write_text(json.dumps({"key": key, "words": words}))
    words = expand_numbers(words)
    # map mishearings onto script vocabulary ("diffuses"->"defuses", "notes"->"nopes", "favours"->"favors")
    vocab = {norm(w) for t in lines.values() for w in t.split() if norm(w)}
    fixed = []
    for n, s0, e0, raw in words:
        if n not in vocab and len(n) >= 4:
            best = max(vocab, key=lambda v: difflib.SequenceMatcher(None, n, v).ratio())
            if difflib.SequenceMatcher(None, n, best).ratio() >= 0.72:
                n = best
        fixed.append((n, s0, e0, raw))
    words = fixed
    # align PHRASES (so mid-line restarts are fine), then stitch each line back together
    units = {}
    for lid, text in lines.items():
        for k, ph in enumerate(phrases(text)):
            units[f"{lid}#{k}"] = ph
    al = align(units, words)
    from .tts import write_wav
    if not a.only:
        write_wav(out / "_roomtone.wav", room_tone(full, SR))
    fade = int(0.015 * SR)
    room = room_tone(full, SR)          # joins between spliced pieces are filled with real room tone, never zeros
    report = []
    for lid, text in lines.items():
        keys = [k for k in units if k.split("#")[0] == lid]
        got = [(k, al[k]) for k in keys if al[k]]
        missing = [units[k] for k in keys if not al[k]]
        if not got:
            report.append(f"MISSING  [{lid}] {text[:70]}")
            continue
        # group phrases that are contiguous in the recording into one clip
        clips, cur = [], None
        for k, m in got:
            if cur and m["start_w"] <= cur[1] + 1 and words[m["start_w"]][1] - words[cur[1] - 1][2] < 0.8:
                cur = (cur[0], m["end_w"])
            else:
                if cur:
                    clips.append(cur)
                cur = (m["start_w"], m["end_w"])
        clips.append(cur)
        audio, wts, t = [], [], 0.0
        for ci, (sw, ew) in enumerate(clips):
            ws = words[sw:ew]
            s0 = max(0.0, ws[0][1] - (0.15 if ci == 0 else 0.10))
            e0 = ws[-1][2] + (0.3 if ci == len(clips) - 1 else 0.15)   # word endings decay past the timestamp
            seg = full[int(s0 * SR):int(e0 * SR)].copy()
            if len(seg) > 2 * fade:
                seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
            if ci:
                n = int(0.12 * SR)
                fill = np.resize(room, n).astype(np.float32) if len(room) else np.zeros(n, np.float32)
                audio.append(fill); t += 0.12
            wts += [(w[3], w[1] - s0 + t, w[2] - s0 + t) for w in ws]
            audio.append(seg); t += len(seg) / SR
        y = np.concatenate(audio)
        write_wav(out / f"{lid}.wav", y)
        (out / f"{lid}.json").write_text(json.dumps({"duration": len(y) / SR, "words": wts}))
        score = min(m["score"] for _, m in got)
        retake = any(m["takes"] > 1 for _, m in got)
        flag = "CHECK " if (score < 0.75 or missing) else "ok    "
        note = (f"  spliced from {len(clips)} takes" if len(clips) > 1 else "") + ("  (retakes found, used the last)" if retake else "")
        note += ("  MISSING PHRASE: " + " | ".join(missing)) if missing else ""
        report.append(f"{flag}  [{lid}] {len(y) / SR:5.1f}s  worst match {score:.2f}{note}")
        said = " ".join(w[0] for w in wts)
        (out / f"{lid}.said.txt").write_text(said + "\n")
    (out / ("_report-rerecord.txt" if a.only else "_report.txt")).write_text("\n".join(report) + "\n")
    print("\n".join(report))
    found = sum(1 for r in report if not r.startswith("MISSING"))
    print(f"\n{found}/{len(lines)} lines found. Files in {out}/")


if __name__ == "__main__":
    main()
