"""Render an episode's scenes (silent, either orientation) and run EVERY visual gate on the finished video:
stage-state checks (safe area, overlaps, cut, coverage, numbers, clipping, fill) + pixels (black frames, flashes,
flicker). Used by CI for the kit demo + torture test, so no glitchy card layout can come out of the kit.

    python -m pipeline.render_check <slug> [--vertical] --list                 # CI: render jobs (~6 s chunks)
    python -m pipeline.render_check <slug> [--vertical] --job <scene>:<k>/<n>
    python -m pipeline.render_check <slug> [--vertical] --assemble             # concat + gates; exit 1 on any error
    python -m pipeline.render_check <slug> [--vertical]                        # all of it locally
Timing: TTS_ENGINE=silent (or recorded with VOICE_DIR).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHUNK_S = 6.0


def outdir(slug, vertical):
    d = ROOT / "episodes" / slug / "out" / ("check-v" if vertical else "check-h")
    (d / "parts").mkdir(parents=True, exist_ok=True)
    return d


def jobs(slug, vertical):
    from .stills import specs
    _, _, sp = specs(slug, vertical)
    out = []
    for sc, spec in sp:
        n = max(1, round(spec["duration"] / CHUNK_S))
        out += [f"{sc.id}:{k}/{n}" for k in range(n)]
    return out


def render_job(slug, vertical, job):
    from . import render3d
    from .stills import specs
    sid, kn = job.split(":")
    k, n = (int(x) for x in kn.split("/"))
    _, _, sp = specs(slug, vertical, [sid])
    order = [s.id for s, _ in specs(slug, vertical)[2]]
    sc, spec = sp[0]
    nf = spec["n_frames"]
    out = outdir(slug, vertical) / "parts" / f"{order.index(sid):02d}-{sid}.part{k:02d}.mp4"
    render3d.render(spec, out, scale=1.0, frames=(nf * k // n, nf * (k + 1) // n))
    print(f"{job}: -> {out}")


def assemble(slug, vertical):
    from . import compose, qa_visual
    from .stills import specs
    d = outdir(slug, vertical)
    _, scenes, sp = specs(slug, vertical)
    parts = []
    for i, (sc, _) in enumerate(sp):
        ps = sorted((d / "parts").glob(f"{i:02d}-{sc.id}.part*.mp4"))
        if not ps:
            raise FileNotFoundError(f"no rendered parts for {sc.id}")
        parts += ps
    video = compose.concat(parts, d / f"{slug}.mp4")
    tl = [{"id": s.id, "start": s.start, "duration": s.duration} for s in scenes]
    errs = qa_visual.run(slug, video=video, vertical=vertical, out_dir=d / "qa", timeline=tl, contact_every=2)
    print(f"{slug} ({'9:16' if vertical else '16:9'}): {'FAIL' if errs else 'PASS'}, report {d / 'qa' / 'visual.txt'}")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--vertical", action="store_true")
    ap.add_argument("--list", action="store_true"); ap.add_argument("--job"); ap.add_argument("--assemble", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        print(json.dumps(jobs(a.slug, a.vertical))); return
    if a.job:
        render_job(a.slug, a.vertical, a.job); return
    if not a.assemble:
        for j in jobs(a.slug, a.vertical):
            render_job(a.slug, a.vertical, j)
    raise SystemExit(1 if assemble(a.slug, a.vertical) else 0)


if __name__ == "__main__":
    main()
