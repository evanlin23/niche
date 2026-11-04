"""Title / description (with chapters + sources) / tags for upload."""
from __future__ import annotations

import json
from pathlib import Path

from .timeline import Scene


def chapters(scenes: list[Scene]) -> list[tuple[float, str]]:
    out = []
    for sc in scenes:
        if sc.chapter:
            out.append((0.0 if not out else sc.start, sc.chapter))
    # YouTube: first chapter at 0:00, >= 3 chapters, each >= 10 s
    merged = []
    for t, name in out:
        if merged and t - merged[-1][0] < 10:
            continue
        merged.append((t, name))
    return merged


def fmt_ts(t: float) -> str:
    t = int(t)
    return f"{t // 3600}:{t // 60 % 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def build(meta: dict, scenes: list[Scene] | None, out_dir: Path, kind="long") -> dict:
    desc = [meta["description"].strip(), ""]
    if scenes and kind == "long":
        ch = chapters(scenes)
        if len(ch) >= 3:
            desc += ["Chapters"] + [f"{fmt_ts(t)} {n}" for t, n in ch] + [""]
    if meta.get("links"):
        desc += [f"{k}: {v}" for k, v in meta["links"].items()] + [""]
    if meta.get("sources"):
        desc += ["Sources & models"] + [f"• {s}" for s in meta["sources"]] + [""]
    if meta.get("music_note"):
        desc += [meta["music_note"]]
    data = {
        "title": meta["title"],
        "description": "\n".join(desc).strip() + "\n",
        "tags": meta.get("tags", []),
        "category": meta.get("category", "Education"),
        "made_for_kids": False,
        "contains_synthetic_media": meta.get("contains_synthetic_media", False),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"metadata-{kind}.json").write_text(json.dumps(data, indent=2))
    (out_dir / f"description-{kind}.txt").write_text(f"{data['title']}\n\n{data['description']}")
    return data
