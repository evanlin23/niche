"""Stills + contact sheet per scene (both orientations), for iterating before any full render.

    python -m pipeline.stills <slug> [--vertical] [--only id ...] [--at 0.35 0.8 1.0] [--scale 0.5] [--out DIR]

`--at` = fractions of each scene's duration (1.0 = the last frame, i.e. what is on screen at the cut).
Timing: recorded voice JSON if present (TTS_ENGINE=recorded VOICE_DIR=...), else TTS_ENGINE=silent estimates.
Writes DIR/<scene>-<k>.png and DIR/contact.png.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent


def scenes_for(slug):
    from .timeline import build, load_yaml, parse_script
    ep = ROOT / "episodes" / slug
    return ep, build(load_yaml(ep / "scenes.yaml")["scenes"], parse_script(ep / "script.md"), ROOT / ".cache" / "tts")


def specs(slug, vertical=False, only=None, short=None):
    from .cli import SceneCtx, _strip, load_3d_module
    from .render import Format
    ep, scenes = scenes_for(slug)
    mod = load_3d_module(ep)
    fmt = Format("short" if vertical else "long", 1080 if vertical else 1920, 1920 if vertical else 1080, 30, 1.0)
    out = []
    for sc in scenes:
        if only and sc.id not in only:
            continue
        ctx = SceneCtx(_strip(sc), fmt, ep, [], engine="3d")
        if short:
            ctx.short = short
        out.append((sc, mod.build_spec(ctx)))
    return ep, scenes, out


def render_frames(jobs, scale):
    """jobs: [(spec, [frame,...], [png path,...])] -> one browser session for everything (pipeline/web/probe.js)."""
    tmp = ROOT / ".cache" / "specs"; tmp.mkdir(parents=True, exist_ok=True)
    items = []
    for spec, frames, pngs in jobs:
        fd, sp = tempfile.mkstemp(suffix=".json", dir=tmp)
        with os.fdopen(fd, "w") as f:
            json.dump(dict(spec, scale=scale), f)
        items.append({"spec": "/" + str(Path(sp).relative_to(ROOT)), "W": spec["W"], "H": spec["H"], "scale": scale,
                      "shots": [{"frame": fr, "png": str(p)} for fr, p in zip(frames, pngs)]})
    job = tmp / f"stills-{os.getpid()}.json"
    job.write_text(json.dumps({"root": str(ROOT), "items": items, "mode": "shots"}))
    from .render3d import _env
    try:
        subprocess.run(["node", str(ROOT / "pipeline" / "web" / "probe.js"), str(job)], check=True, env=_env())
    finally:
        for it in items:
            (ROOT / it["spec"].lstrip("/")).unlink(missing_ok=True)
        job.unlink(missing_ok=True)


def contact(pngs, labels, out, cols=4, w=480):
    ims = [Image.open(p) for p in pngs]
    if not ims:
        return None
    h = int(w * ims[0].height / ims[0].width)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 26)), (20, 24, 22))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype(str(ROOT / "pipeline/web/fonts/rubik-latin-700.ttf"), 16)
    except OSError:
        f = None
    for i, (im, lab) in enumerate(zip(ims, labels)):
        x, y = i % cols * w, i // cols * (h + 26)
        sheet.paste(im.convert("RGB").resize((w, h)), (x, y + 26))
        d.text((x + 6, y + 4), lab, fill=(240, 230, 200), font=f)
    sheet.save(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--only", nargs="*"); ap.add_argument("--at", nargs="*", type=float, default=[0.5, 1.0])
    ap.add_argument("--scale", type=float, default=0.5); ap.add_argument("--out")
    a = ap.parse_args(argv)
    ep, _, sp = specs(a.slug, a.vertical, a.only)
    out = Path(a.out) if a.out else ep / "out" / ("stills-v" if a.vertical else "stills")
    out.mkdir(parents=True, exist_ok=True)
    jobs, pngs, labels = [], [], []
    for sc, spec in sp:
        n = spec["n_frames"]
        frames = [min(n - 1, int(f * n)) for f in a.at]
        ps = [out / f"{sc.id}-{k}.png" for k in range(len(frames))]
        jobs.append((spec, frames, ps)); pngs += ps
        labels += [f"{sc.id} t={fr / 30:.1f}s" for fr in frames]
    render_frames(jobs, a.scale)
    print("contact sheet:", contact(pngs, labels, out / "contact.png", cols=4 if not a.vertical else 6, w=480 if not a.vertical else 270))


if __name__ == "__main__":
    main()
