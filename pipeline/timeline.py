"""Script + scene list -> timeline (scene start/end, narration cue times, captions)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .tts import Speech, speak

LINE_RE = re.compile(r"^\[([A-Za-z0-9_-]+)\]\s+(.+)$")


def parse_script(path: Path) -> dict[str, str]:
    lines = {}
    for raw in Path(path).read_text().splitlines():
        m = LINE_RE.match(raw.strip())
        if m:
            lines[m.group(1)] = m.group(2).strip()
    return lines


@dataclass
class Cue:
    id: str
    text: str
    start: float          # relative to scene start
    end: float
    words: list           # (word, start, end) relative to scene start


@dataclass
class Scene:
    id: str
    render: str
    params: dict
    start: float = 0.0
    duration: float = 0.0
    cues: dict[str, Cue] = field(default_factory=dict)
    chapter: str | None = None
    speech: list = field(default_factory=list)   # [(abs_start, Speech)]
    chain: dict | None = None                   # consecutive scenes on the same template: one continuous shot

    def cue(self, cid, default=0.0) -> float:
        return self.cues[cid].start if cid in self.cues else default

    def cue_end(self, cid, default=0.0) -> float:
        return self.cues[cid].end if cid in self.cues else default


def build(scene_specs: list[dict], texts: dict[str, str], cache_dir: Path,
          line_gap=0.25, default_pad=(0.2, 0.35)) -> list[Scene]:
    scenes, t = [], 0.0
    for spec in scene_specs:
        pad = spec.get("pad", default_pad)
        gap = spec.get("gap", line_gap)
        sc = Scene(spec["id"], spec["render"], spec.get("params", {}) or {},
                   chapter=spec.get("chapter"))
        sc.start = t
        cur = pad[0]
        for lid in spec.get("lines", []):
            if isinstance(lid, dict):            # inline text (used by shorts)
                lid, text = lid["id"], lid["text"]
                texts[lid] = text
            sp: Speech = speak(texts[lid], cache_dir, line_id=lid)
            words = [(w, cur + s, cur + e) for w, s, e in sp.words]
            sc.cues[lid] = Cue(lid, texts[lid], cur, cur + sp.duration, words)
            sc.speech.append((t + cur, sp))
            cur += sp.duration + gap
        cur = cur - (gap if spec.get("lines") else 0) + pad[1]
        sc.duration = max(cur, float(spec.get("min_duration", 0)))
        scenes.append(sc)
        t += sc.duration
    mark_chains(scenes)
    return scenes


def mark_chains(scenes):
    """Consecutive scenes on the same template share one continuous camera move (a cut between two shots of the same
    layout from slightly different angles reads as a jump). `params: {shot: new}` starts a new, clearly different shot."""
    i = 0
    while i < len(scenes):
        j = i
        while j + 1 < len(scenes) and scenes[j + 1].render == scenes[i].render and \
                (scenes[j + 1].params or {}).get("shot") != "new":
            j += 1
        if j > i:
            t0, total = scenes[i].start, sum(s.duration for s in scenes[i:j + 1])
            for k in range(i, j + 1):
                scenes[k].chain = {"t0": round(scenes[k].start - t0, 4), "total": round(total, 4), "index": k - i,
                                   "n": j - i + 1}
        i = j + 1


def caption_chunks(scenes: list[Scene], max_words=7, max_chars=42, absolute=True):
    """Split narration into short caption chunks: [(start, end, text)]."""
    out = []
    for sc in scenes:
        off = sc.start if absolute else 0.0
        for cue in sc.cues.values():
            chunk = []
            for w in cue.words:
                chunk.append(w)
                txt = " ".join(x[0] for x in chunk)
                end_sentence = w[0][-1] in ".?!,;:" and len(chunk) >= 3
                if len(chunk) >= max_words or len(txt) >= max_chars or end_sentence:
                    out.append((off + chunk[0][1], off + chunk[-1][2], txt))
                    chunk = []
            if chunk:
                out.append((off + chunk[0][1], off + chunk[-1][2], " ".join(x[0] for x in chunk)))
    return out


def _script_timed_tokens(cue):
    """Script words (with punctuation) timed from the recognised words: difflib alignment on normalised text,
    unmatched script words interpolated between their matched neighbours."""
    import difflib, re
    norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
    toks = cue.text.split()
    words = cue.words
    if not toks:
        return []
    if not words:
        n = len(toks); d = (cue.end - cue.start) / n
        return [(t, cue.start + i * d, cue.start + (i + 1) * d) for i, t in enumerate(toks)]
    sm = difflib.SequenceMatcher(None, [norm(t) for t in toks], [norm(w[0]) for w in words], autojunk=False)
    st = [None] * len(toks); en = [None] * len(toks)
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            st[a + k], en[a + k] = words[b + k][1], words[b + k][2]
    # anchor the ends, then interpolate gaps
    if st[0] is None: st[0], en[0] = words[0][1], words[0][2]
    if st[-1] is None: st[-1], en[-1] = words[-1][1], words[-1][2]
    i = 0
    while i < len(toks):
        if st[i] is None:
            j = i
            while st[j] is None: j += 1
            a, b = en[i - 1], st[j]
            for k in range(i, j):
                f0, f1 = (k - i) / (j - i), (k - i + 1) / (j - i)
                st[k], en[k] = a + (b - a) * f0, a + (b - a) * f1
            i = j
        i += 1
    return list(zip(toks, st, en))


def script_caption_chunks(scenes: list[Scene], max_chars=84, line_chars=42):
    """Upload captions: the script's own words and punctuation (not the transcription), timed from the voice.
    Chunks end at sentence ends where possible and are wrapped into at most two lines."""
    out = []
    for sc in scenes:
        for cue in sc.cues.values():
            toks = _script_timed_tokens(cue)
            chunk = []
            for i, (w, s0, e0) in enumerate(toks):
                chunk.append((w, s0, e0))
                txt = " ".join(x[0] for x in chunk)
                nxt = len(txt) + 1 + len(toks[i + 1][0]) if i + 1 < len(toks) else 0
                sentence_end = w[-1] in ".?!" and len(txt) > 20
                clause_end = w[-1] in ",;:" and len(txt) > 50
                if sentence_end or clause_end or nxt > max_chars or i + 1 == len(toks):
                    ws = txt.split()
                    if len(txt) <= line_chars or len(ws) < 2:
                        lines = [txt]
                    else:   # two balanced lines: break at the space closest to the middle
                        cut = min(range(1, len(ws)), key=lambda k: abs(len(" ".join(ws[:k])) - len(" ".join(ws[k:]))))
                        lines = [" ".join(ws[:cut]), " ".join(ws[cut:])]
                    out.append((sc.start + chunk[0][1], sc.start + chunk[-1][2], "\n".join(lines)))
                    chunk = []
    # no overlaps, and keep each caption up for at least ~0.8 s when there is room
    for k in range(len(out) - 1):
        s0, e0, t0 = out[k]
        e0 = min(max(e0, s0 + 0.8), out[k + 1][0])
        out[k] = (s0, e0, t0)
    return out


def load_yaml(path: Path):
    return yaml.safe_load(Path(path).read_text())
