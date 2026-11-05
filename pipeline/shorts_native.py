"""Native vertical Shorts (1080x1920): chosen moments of the long episode re-rendered with the kit's 9:16 layouts,
hook headline on top, big word-timed captions, "Full video on my channel" + Buh at the bottom. The voice and music
are cut from the long episode's own audio, so nothing is re-recorded.

    make shorts-native SLUG=<slug> [ONLY=id] [AUDIO=out/final/<slug>.mp4]
    python -m pipeline.shorts_native <slug> [--only id ...] [--audio long.mp4|wav]      # render + assemble locally
    python -m pipeline.shorts_native <slug> --list                                     # CI: render jobs (~6 s each)
    python -m pipeline.shorts_native <slug> --job <short>:<scene>:<k>/<n>               # CI: render one chunk
    python -m pipeline.shorts_native <slug> --assemble [--audio ...]                    # CI: concat + audio + QA

episodes/<slug>/shorts_native.yaml:
    shorts:
    - id: kitten-placement
      hook: "Where do you put\\nthe Kitten back?"
      title: "..."                # YouTube title; description below
      description: "..."
      scenes:                     # kit templates (pipeline/web/kit.js), lines from script.md, any word anchors
      - {id: kp, render: deck, lines: [k2, k3, k4, k5], params: {...}}

Timing is the LONG video's timing: each Short is the span [first line - 0.15 s, last line + tail] of the long
timeline, and its scenes tile that span (cut halfway between lines), so the cut audio lines up word for word.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W, H, FPS = 1080, 1920, 30
CHUNK_S = 6.0


def load(slug):
    import yaml
    from .timeline import build, load_yaml, parse_script
    ep = ROOT / "episodes" / slug
    cfg = yaml.safe_load((ep / "shorts_native.yaml").read_text())
    texts = parse_script(ep / "script.md")
    long_scenes = build(load_yaml(ep / "scenes.yaml")["scenes"], dict(texts), ROOT / ".cache" / "tts")
    cues = {}
    for sc in long_scenes:
        for lid, c in sc.cues.items():
            cues[lid] = (sc.start + c.start, sc.start + c.end, [(w, sc.start + a, sc.start + b) for w, a, b in c.words], c.text)
    return ep, cfg, cues


def plan_short(sh, cues):
    """-> (t0, t1, [timeline.Scene with long-video timing, scene-relative])"""
    from .timeline import Cue, Scene
    order = [lid for s in sh["scenes"] for lid in s["lines"]]
    missing = [l for l in order if l not in cues]
    if missing:
        raise KeyError(f"short {sh['id']}: lines not in the long video: {missing}")
    t0 = cues[order[0]][0] - sh.get("lead", 0.15)
    t1 = cues[order[-1]][1] + sh.get("tail", 0.8)
    bounds = [t0]
    for a, b in zip(sh["scenes"], sh["scenes"][1:]):
        bounds.append((cues[a["lines"][-1]][1] + cues[b["lines"][0]][0]) / 2)
    bounds.append(t1)
    scenes = []
    for k, s in enumerate(sh["scenes"]):
        st, en = bounds[k], bounds[k + 1]
        sc = Scene(s.get("id", f"{sh['id']}-{k}"), s["render"], copy.deepcopy(s.get("params", {}) or {}))
        sc.start, sc.duration = st, en - st
        for lid in s["lines"]:
            a, b, ws, text = cues[lid]
            sc.cues[lid] = Cue(lid, text, a - st, b - st, [(w, x - st, y - st) for w, x, y in ws])
        scenes.append(sc)
    return t0, t1, scenes


def specs_for(slug, only=None):
    from .cli import SceneCtx
    from .render import Format
    from . import kit
    ep, cfg, cues = load(slug)
    fmt = Format("short", W, H, FPS, 1.0)
    out = []
    for sh in cfg["shorts"]:
        if only and sh["id"] not in only:
            continue
        t0, t1, scenes = plan_short(sh, cues)
        specs = []
        for sc in scenes:
            words = [(w, a, b) for c in sc.cues.values() for w, a, b in c.words]
            ctx = SceneCtx(sc, fmt, ep, [], engine="3d")
            ctx.short = {"hook": sh["hook"], "words": words}
            specs.append((sc, kit.build_spec(ctx, module=sh.get("module", "/pipeline/web/kit.js"))))
        out.append((sh, t0, t1, scenes, specs))
    return ep, out


def parts_dir(ep):
    d = ep / "out" / "shorts-native" / "parts"; d.mkdir(parents=True, exist_ok=True)
    return d


def jobs(slug, only=None):
    _, shorts = specs_for(slug, only)
    out = []
    for sh, _, _, scenes, specs in shorts:
        for sc, spec in specs:
            n = max(1, round(spec["duration"] / CHUNK_S))
            out += [f"{sh['id']}:{sc.id}:{k}/{n}" for k in range(n)]
    return out


def render_job(slug, job):
    from . import render3d
    sid, scid, kn = job.split(":")
    k, n = (int(x) for x in kn.split("/"))
    ep, shorts = specs_for(slug, [sid])
    for sh, _, _, scenes, specs in shorts:
        for sc, spec in specs:
            if sc.id != scid:
                continue
            nf = spec["n_frames"]
            out = parts_dir(ep) / f"{sid}--{sc.id}.part{k:02d}.mp4"
            render3d.render(spec, out, scale=1.0, frames=(nf * k // n, nf * (k + 1) // n))
            print(f"{job}: frames {nf * k // n}-{nf * (k + 1) // n} -> {out}")
            return out
    raise KeyError(job)


def assemble(slug, only=None, audio_src=None, qa=True):
    from . import compose
    ep, shorts = specs_for(slug, only)
    outd = ep / "out" / "shorts-native"
    pd = parts_dir(ep)
    results = []
    for sh, t0, t1, scenes, specs in shorts:
        parts = []
        for sc, _ in specs:
            ps = sorted(pd.glob(f"{sh['id']}--{sc.id}.part*.mp4"))
            if not ps:
                raise FileNotFoundError(f"no rendered parts for {sh['id']} / {sc.id} in {pd}")
            parts += ps
        video = compose.concat(parts, outd / f"{sh['id']}-noaudio.mp4")
        dur = t1 - t0
        wav = outd / f"{sh['id']}.wav"
        if audio_src and Path(audio_src).exists():
            # the long episode's own mix (voice + music), cut to the same span, short fades at the edges
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", str(audio_src),
                            "-vn", "-af", f"afade=t=in:d=0.08,afade=t=out:st={max(0, dur - 0.35):.3f}:d=0.35",
                            "-ar", "48000", "-ac", "2", str(wav)], check=True)
            note = f"audio cut from {Path(audio_src).name} at {t0:.2f}-{t1:.2f}s"
            final = compose.mux(video, wav, outd / f"{sh['id']}.mp4")
        else:
            # no long-episode audio here (CI: voice and music never leave the creator's machine): silent track,
            # same length; run again locally with --audio out/final/<slug>.mp4 to put the real mix in
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
                            "-t", f"{dur:.3f}", str(wav)], check=True)
            note = "NO AUDIO SOURCE: silent track (re-run locally with --audio <long video>)"
            final = compose.mux(video, wav, outd / f"{sh['id']}.mp4", loudnorm=False)
        video.unlink(missing_ok=True); wav.unlink(missing_ok=True)
        (outd / f"{sh['id']}.txt").write_text(f"{sh.get('title', '')}\n\n{sh.get('description', '')}\n\n"
                                               f"source span in the long video: {t0:.2f}-{t1:.2f}s\n{note}\n")
        print(f"short {sh['id']}: {dur:.1f}s -> {final}  ({note})")
        results.append((sh, final, scenes, specs))
    if qa:
        from . import qa_visual
        errs = 0
        for sh, final, scenes, specs in results:
            errs += qa_visual.run(slug, video=None, vertical=True, out_dir=outd / f"qa-{sh['id']}",
                                  scenes_override=(scenes, specs))
        return errs
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--only", nargs="*"); ap.add_argument("--audio")
    ap.add_argument("--list", action="store_true"); ap.add_argument("--job"); ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--no-qa", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        print(json.dumps(jobs(a.slug, a.only))); return
    if a.job:
        render_job(a.slug, a.job); return
    if not a.assemble:
        for j in jobs(a.slug, a.only):
            render_job(a.slug, j)
    raise SystemExit(1 if assemble(a.slug, a.only, a.audio, not a.no_qa) else 0)


if __name__ == "__main__":
    main()
