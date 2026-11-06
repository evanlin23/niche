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

Timing is the LONG video's timing. Each scene is one contiguous span of the long video (`lines` in order; 'k2@most'
starts a line at that word), scenes may come from anywhere (open on the hook, then go back), and the Short's audio
is those spans cut from the long mix and joined, so it lines up word for word.
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
    if any((ep / "voice").glob("*.json")):        # a recorded episode: always use its real timing, never TTS estimates
        os.environ.setdefault("TTS_ENGINE", "recorded"); os.environ.setdefault("VOICE_DIR", str(ep / "voice"))
    cfg = yaml.safe_load((ep / "shorts_native.yaml").read_text())
    texts = parse_script(ep / "script.md")
    long_scenes = build(load_yaml(ep / "scenes.yaml")["scenes"], dict(texts), ROOT / ".cache" / "tts")
    cues = {}
    for sc in long_scenes:
        for lid, c in sc.cues.items():
            cues[lid] = (sc.start + c.start, sc.start + c.end, [(w, sc.start + a, sc.start + b) for w, a, b in c.words], c.text)
    return ep, cfg, cues


def _line(ref, cues):
    """'k3' -> whole line; 'k2@most' -> the line from the word 'most' on (so a Short can open on its hook)."""
    from .kit import norm
    lid, _, word = ref.partition("@")
    if lid not in cues:
        raise KeyError(f"line {lid} is not in the long video")
    a, b, ws, text = cues[lid]
    if not word:
        return lid, a, b, ws, text
    seq = [norm(x) for x in word.split("_")]
    for i in range(len(ws) - len(seq) + 1):
        if [norm(w[0]) for w in ws[i:i + len(seq)]] == seq:
            ws = ws[i:]
            return lid, ws[0][1], b, ws, " ".join(text.split()[-len(ws):])
    raise KeyError(f"{ref}: '{word}' is not spoken in {lid}")


def plan_short(sh, cues):
    """-> (segments, [timeline.Scene]) . Each scene is ONE contiguous span of the long video (its lines in order);
    scenes may come from anywhere (a Short can open on the hook line and go back). segments = [(src_t0, src_t1)]
    in long-video seconds, one per scene; the Short is their concatenation."""
    from .timeline import Cue, Scene
    order = list(cues)
    spans = []
    for s in sh["scenes"]:
        ls = [_line(r, cues) for r in s["lines"]]
        ids = [l[0] for l in ls]
        pos = [order.index(i) for i in ids]
        if pos != list(range(pos[0], pos[0] + len(pos))):
            raise ValueError(f"short {sh['id']} scene {s.get('id')}: lines {ids} are not consecutive in the long video")
        spans.append((ls, pos))
    segs = []
    for k, (ls, pos) in enumerate(spans):
        st = ls[0][1] - sh.get("lead", 0.12)
        en = ls[-1][2] + sh.get("tail", 0.3)
        # joined to the previous/next scene in the long video: cut halfway between the lines (seamless audio)
        if k and spans[k - 1][1][-1] + 1 == pos[0] and "@" not in sh["scenes"][k]["lines"][0]:
            st = (spans[k - 1][0][-1][2] + ls[0][1]) / 2
        if k + 1 < len(spans) and pos[-1] + 1 == spans[k + 1][1][0] and "@" not in sh["scenes"][k + 1]["lines"][0]:
            en = (ls[-1][2] + spans[k + 1][0][0][1]) / 2
        if k + 1 == len(spans):
            en = ls[-1][2] + sh.get("end_tail", 0.8)
        segs.append((st, en))
    scenes, t = [], 0.0
    for k, (s, (ls, _), (st, en)) in enumerate(zip(sh["scenes"], spans, segs)):
        sc = Scene(s.get("id", f"{sh['id']}-{k}"), s["render"], copy.deepcopy(s.get("params", {}) or {}))
        sc.start, sc.duration = t, en - st
        for lid, a, b, ws, text in ls:
            sc.cues[lid] = Cue(lid, text, a - st, b - st, [(w, x - st, y - st) for w, x, y in ws])
        scenes.append(sc); t += sc.duration
    from .timeline import mark_chains
    mark_chains(scenes)                          # same-template cuts: one continuous shot, or a clearly new one
    return segs, scenes


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
        segs, scenes = plan_short(sh, cues)
        specs = []
        for k, sc in enumerate(scenes):
            words = [(w, a, b) for c in sc.cues.values() for w, a, b in c.words]
            ctx = SceneCtx(sc, fmt, ep, [], engine="3d")
            ctx.short = {"hook": sh["hook"], "words": words, "first": k == 0, "game": sh.get("game", cfg.get("game", ""))}
            specs.append((sc, kit.build_spec(ctx, module=sh.get("module", "/pipeline/web/kit.js"))))
        out.append((sh, segs, None, scenes, specs))
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
    for sh, segs, _, scenes, specs in shorts:
        parts = []
        for sc, _ in specs:
            ps = sorted(pd.glob(f"{sh['id']}--{sc.id}.part*.mp4"))
            if not ps:
                raise FileNotFoundError(f"no rendered parts for {sh['id']} / {sc.id} in {pd}")
            parts += ps
        video = compose.concat(parts, outd / f"{sh['id']}-noaudio.mp4")
        dur = sum(e - b for b, e in segs)
        wav = outd / f"{sh['id']}.wav"
        span = ", ".join(f"{b:.2f}-{e:.2f}s" for b, e in segs)
        if audio_src and Path(audio_src).exists():
            # the long episode's own mix (voice + music): one cut per scene, joined with 15 ms fades
            n = len(segs)
            fc = "".join(f"[0:a]atrim={b:.3f}:{e:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,"
                         f"afade=t=out:st={max(0, e - b - 0.015):.3f}:d=0.015[a{i}];" for i, (b, e) in enumerate(segs))
            fc += "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,afade=t=in:d=0.06,afade=t=out:st={max(0, dur - 0.35):.3f}:d=0.35[o]"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(audio_src), "-filter_complex", fc, "-map", "[o]",
                            "-ar", "48000", "-ac", "2", str(wav)], check=True)
            note = f"audio cut from {Path(audio_src).name} at {span}"
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
                                               f"source spans in the long video: {span}\n{note}\n")
        print(f"short {sh['id']}: {dur:.1f}s -> {final}  ({note})")
        results.append((sh, final, scenes, specs))
    if qa:
        from . import qa_visual
        errs = 0
        for sh, final, scenes, specs in results:
            tl = [{"id": sc.id, "start": sc.start, "duration": sc.duration} for sc in scenes]
            errs += qa_visual.run(slug, video=final, vertical=True, out_dir=outd / f"qa-{sh['id']}",
                                  scenes_override=(scenes, specs), timeline=tl, contact_every=2, short=True)
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
