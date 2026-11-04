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

    def cue(self, cid, default=0.0) -> float:
        return self.cues[cid].start if cid in self.cues else default

    def cue_end(self, cid, default=0.0) -> float:
        return self.cues[cid].end if cid in self.cues else default


def build(scene_specs: list[dict], texts: dict[str, str], cache_dir: Path,
          line_gap=0.75, default_pad=(0.6, 0.9)) -> list[Scene]:
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
            sp: Speech = speak(texts[lid], cache_dir)
            words = [(w, cur + s, cur + e) for w, s, e in sp.words]
            sc.cues[lid] = Cue(lid, texts[lid], cur, cur + sp.duration, words)
            sc.speech.append((t + cur, sp))
            cur += sp.duration + gap
        cur = cur - (gap if spec.get("lines") else 0) + pad[1]
        sc.duration = max(cur, float(spec.get("min_duration", 0)))
        scenes.append(sc)
        t += sc.duration
    return scenes


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


def load_yaml(path: Path):
    return yaml.safe_load(Path(path).read_text())
