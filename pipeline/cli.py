"""Command line entry point.

  python -m pipeline.cli episode SLUG [--preview] [--jobs N] [--only SCENE_ID]
  python -m pipeline.cli shorts  SLUG [--preview] [--only SHORT_ID]
  python -m pipeline.cli thumb   SLUG
  python -m pipeline.cli pack    SLUG
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import multiprocessing as mp
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import compose, metadata, package, render
from .render import LONG, SHORT, Format
from .timeline import build, caption_chunks, load_yaml, parse_script

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class SceneCtx:
    """Everything a scene renderer gets."""
    scene: object                 # timeline.Scene (cues, duration, params)
    fmt: Format
    ep_dir: Path
    captions: list = field(default_factory=list)   # [(start, end, text)] scene-relative
    hook: str | None = None       # shorts only
    engine: str = "2d"            # "2d" (skia) or "3d" (Three.js tabletop stage)

    @property
    def params(self):
        return self.scene.params

    @property
    def duration(self):
        return self.scene.duration


def load_scenes_module(ep_dir: Path):
    path = ep_dir / "sim" / "scenes.py"
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(f"ep_{ep_dir.name.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_3d_module(ep_dir: Path):
    path = ep_dir / "sim" / "scenes3d.py"
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(f"ep3d_{ep_dir.name.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _render_job(job):
    ep_dir, ctx, out = job
    t0 = time.time()
    if ctx.engine == "3d":
        from . import render3d
        spec = load_3d_module(ep_dir).build_spec(ctx)
        render3d.render(spec, out, scale=ctx.fmt.scale)
    else:
        mod = load_scenes_module(ep_dir)
        fn = mod.SCENES[ctx.scene.render]
        render.render_video(out, ctx.fmt, ctx.duration, fn(ctx))
    return f"{ctx.scene.id}: {ctx.duration:.1f}s video in {time.time() - t0:.0f}s"


def _strip(sc):
    s = copy.copy(sc)
    s.speech = []
    return s


def _run_jobs(jobs, n):
    if n <= 1:
        for j in jobs:
            print(" ", _render_job(j), flush=True)
        return
    with mp.get_context("fork").Pool(n) as pool:
        for msg in pool.imap_unordered(_render_job, jobs):
            print(" ", msg, flush=True)


def cmd_episode(slug, preview=False, jobs=3, only=None, assemble=False):
    ep = ROOT / "episodes" / slug
    out = ep / "out" / ("preview" if preview else "final")
    cache = ROOT / ".cache" / "tts"
    texts = parse_script(ep / "script.md")
    spec = load_yaml(ep / "scenes.yaml")
    scenes = build(spec["scenes"], texts, cache)
    total = sum(s.duration for s in scenes)
    print(f"[{slug}] {len(scenes)} scenes, {total / 60:.1f} min", flush=True)
    fmt = render.preview(LONG) if preview else LONG
    if spec.get("engine") == "3d":
        fmt = Format("long", 1920, 1080, 30, 1 / 3 if preview else 1.0)
    caps_abs = caption_chunks(scenes, max_words=12, max_chars=80)
    parts, todo = [], []
    for i, sc in enumerate(scenes):
        p = out / "scenes" / f"{i:02d}-{sc.id}.mp4"
        parts.append(p)
        if only and sc.id not in only:
            continue
        caps = [(s - sc.start, e - sc.start, t) for s, e, t in caps_abs if sc.start <= s < sc.start + sc.duration]
        todo.append((ep, SceneCtx(_strip(sc), fmt, ep, caps, engine=spec.get("engine", "2d")), p))
    _run_jobs(todo, jobs)
    if only and not assemble:
        return
    video = compose.concat(parts, out / "video-noaudio.mp4")
    audio = compose.mix(scenes, total, out / "audio.wav", mood=spec.get("music", "curious"))
    final = compose.mux(video, audio, out / f"{slug}.mp4")
    compose.srt(caps_abs, out / f"{slug}.en.srt")
    meta = load_yaml(ep / "meta.yaml")
    metadata.build(meta["long"], scenes, out, "long")
    (out / "timeline.json").write_text(json.dumps(
        [{"id": s.id, "start": round(s.start, 2), "duration": round(s.duration, 2),
          "cues": {k: [round(c.start + s.start, 2), round(c.end + s.start, 2)] for k, c in s.cues.items()}}
         for s in scenes], indent=1))
    video.unlink()
    print(f"[{slug}] wrote {final}")


def cmd_shorts(slug, preview=False, jobs=3, only=None):
    ep = ROOT / "episodes" / slug
    out = ep / "out" / ("preview" if preview else "final") / "shorts"
    cache = ROOT / ".cache" / "tts"
    spec = load_yaml(ep / "shorts.yaml")
    meta = load_yaml(ep / "meta.yaml")
    engine = load_yaml(ep / "scenes.yaml").get("engine", "2d")
    fmt = render.preview(SHORT) if preview else SHORT
    if engine == "3d":
        fmt = Format("short", 1080, 1920, 30, 1 / 3 if preview else 1.0)
    built = []
    for sh in spec["shorts"]:
        if only and sh["id"] not in only:
            continue
        scenes = build([{**sh, "id": sh["id"]}], {}, cache, line_gap=0.25, default_pad=(0.15, 1.2))
        sc = scenes[0]
        caps = caption_chunks(scenes, max_words=4, max_chars=24, absolute=False)
        built.append((sh, scenes, (ep, SceneCtx(_strip(sc), fmt, ep, caps, sh.get("hook"), engine), out / f"{sh['id']}-noaudio.mp4")))
    _run_jobs([b[2] for b in built], jobs)
    for sh, scenes, job in built:
        dur = scenes[0].duration
        audio = compose.mix(scenes, dur, out / f"{sh['id']}.wav", mood=sh.get("music", "curious"),
                            music_db=-19, seed=7)
        final = compose.mux(job[2], audio, out / f"{sh['id']}.mp4")
        job[2].unlink(); audio.unlink()
        m = dict(meta["short_defaults"]); m.update(sh.get("meta", {}))
        metadata.build(m, None, out, sh["id"])
        print(f"  short {sh['id']}: {dur:.1f}s -> {final}")


def cmd_thumb(slug):
    ep = ROOT / "episodes" / slug
    out = ep / "out" / "final"
    out.mkdir(parents=True, exist_ok=True)
    if load_yaml(ep / "scenes.yaml").get("engine", "2d") == "3d":
        from . import render3d
        p = render3d.render(load_3d_module(ep).thumbnail_spec(), out / "thumbnail.png", scale=2 / 3, png_frame=0)
    else:
        mod = load_scenes_module(ep)
        p = render.render_still(out / "thumbnail.png", 1280, 720, mod.thumbnail)
    print("wrote", p)


def cmd_pack(slug):
    ep = ROOT / "episodes" / slug
    print("wrote", package.build(ep, ep / "out" / "final"))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pipeline")
    ap.add_argument("cmd", choices=["episode", "shorts", "thumb", "pack", "all"])
    ap.add_argument("slug")
    ap.add_argument("--preview", action="store_true", help="480p / 30 fps fast render")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--only", nargs="*", help="render only these scene / short ids")
    ap.add_argument("--assemble", action="store_true", help="with --only: re-assemble the full video from existing scene files")
    a = ap.parse_args(argv)
    if a.cmd in ("episode", "all"):
        cmd_episode(a.slug, a.preview, a.jobs, a.only, a.assemble)
    if a.cmd in ("shorts", "all"):
        cmd_shorts(a.slug, a.preview, a.jobs, a.only)
    if a.cmd in ("thumb", "all"):
        cmd_thumb(a.slug)
    if a.cmd in ("pack", "all"):
        cmd_pack(a.slug)


if __name__ == "__main__":
    main()
