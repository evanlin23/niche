"""Visual QA gate: every scene of an episode (or a Short), checked from the stage state frame by frame.

    make qa-visual SLUG=<slug> [VIDEO=path.mp4] [VERTICAL=1]
    python -m pipeline.qa_visual <slug> [--video out/final/<slug>.mp4] [--only id ...] [--vertical] [--no-stills]

Checks (per scene; error = gate fails, warn = look at it, info = FYI):
  anchors     every word anchor in scenes.yaml resolves to a spoken word                       (error)
  safe        every visible text label inside the 5% title-safe area; kit 'key' objects too      (error)
              other objects inside the frame                                                    (warn)
  overlap     no two visible labels overlap                                                     (error)
  cut         at the last frame nothing is half-faded, still moving or mid-tween                 (error; ambient loops warn)
  coverage    no stretch of narration longer than 5 s without a new visual event               (error)
  numbers     numbers on screen agree with the script line they are anchored to                 (error; unsaid = warn)
  captions    burn_captions: false -> nothing burned in                                          (error)
  pixels      (with --video) no black frames, no brightness flashes / dips                       (error)
Writes out/qa/visual.json, out/qa/visual.txt (readable), out/qa/contact.png. Exit code 1 if any error.
Timing: the recorded voice JSON (VOICE_DIR) if present, else TTS_ENGINE=silent estimates.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAP_MAX = 5.0        # seconds of narration without a new visual event
STEP = 3             # probe every 3rd frame (0.1 s) + the last two frames


def _issue(sev, check, msg, t0=None, t1=None, **kw):
    d = {"sev": sev, "check": check, "msg": msg}
    if t0 is not None:
        d["t"] = [round(t0, 2), round(t1 if t1 is not None else t0, 2)]
    d.update(kw)
    return d


# ------------------------------------------------------------------ probing
def probe(spec_list, workdir: Path):
    """spec_list: [(scene_id, spec)] -> {scene_id: [state, ...]} via pipeline/web/probe.js (one browser)."""
    tmp = ROOT / ".cache" / "specs"; tmp.mkdir(parents=True, exist_ok=True)
    items, outs = [], {}
    for sid, spec in spec_list:
        fd, sp = tempfile.mkstemp(suffix=".json", dir=tmp)
        with os.fdopen(fd, "w") as f:
            json.dump(dict(spec, scale=1.0), f)
        n = spec["n_frames"]
        frames = sorted(set(list(range(0, n, STEP)) + [max(0, n - 2), n - 1]))
        out = workdir / f"probe-{sid}.jsonl"; outs[sid] = out
        items.append({"spec": "/" + str(Path(sp).relative_to(ROOT)), "W": spec["W"], "H": spec["H"], "scale": 1.0,
                      "frames": frames, "fps": spec["fps"], "out": str(out)})
    job = tmp / f"probe-{os.getpid()}.json"
    job.write_text(json.dumps({"root": str(ROOT), "items": items, "mode": "probe"}))
    from .render3d import _env
    try:
        r = subprocess.run(["node", str(ROOT / "pipeline" / "web" / "probe.js"), str(job)], env=_env())
    finally:
        for it in items:
            (ROOT / it["spec"].lstrip("/")).unlink(missing_ok=True)
        job.unlink(missing_ok=True)
    res = {}
    for sid, p in outs.items():
        states = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
        res[sid] = states
    return res


# ------------------------------------------------------------------ checks
def rect_inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0]); h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def area(r):
    return max(0, r[2] - r[0]) * max(0, r[3] - r[1])


def check_scene(sc, spec, states, script, cfg):
    W, H = spec["W"], spec["H"]
    S = (W * 0.05, H * 0.05, W * 0.95, H * 0.95)
    issues = []
    errs = [s["error"] for s in states if "error" in s]
    states = [s for s in states if "error" not in s]
    for e in errs:
        issues.append(_issue("error", "page", f"scene crashed in the browser: {e}"))
    if not states:
        issues.append(_issue("error", "page", "no stage state (scene failed to build)"))
        return issues, []
    dur = spec["duration"]

    # ---- safe area + overlaps (deduplicated per element / pair)
    safe_bad, frame_bad, over = {}, {}, {}
    for st in states:
        t = st["t"]
        vis = [x for x in st["texts"] if x["op"] >= 0.05]
        for x in vis:
            r = x["r"]
            out = max(S[0] - r[0], S[1] - r[1], r[2] - S[2], r[3] - S[3])
            if out > 1.5:
                k = (x["id"], x["text"][:40])
                a = safe_bad.setdefault(k, [t, t, 0, x["role"]]); a[1] = t; a[2] = max(a[2], out)
        strong = [x for x in vis if x["op"] >= 0.3]
        for i in range(len(strong)):
            for j in range(i + 1, len(strong)):
                a, b = strong[i], strong[j]
                inter = rect_inter(a["r"], b["r"])
                if inter > 150 and inter > 0.12 * min(area(a["r"]), area(b["r"])):
                    k = (min(a["id"], b["id"]), max(a["id"], b["id"]))
                    o = over.setdefault(k, [t, t, a["text"][:40], b["text"][:40], 0]); o[1] = t; o[4] = max(o[4], inter)
        for o in st["objs"]:
            if not o["r"] or o["op"] < 0.05:
                continue
            r = o["r"]
            if o["kind"] == "key":
                out = max(S[0] - r[0], S[1] - r[1], r[2] - S[2], r[3] - S[3])
                if out > 2:
                    a = frame_bad.setdefault((o["id"], "safe"), [t, t, 0, o["name"], "error", "outside title-safe"]); a[1] = t; a[2] = max(a[2], out)
            else:
                out = max(-r[0], -r[1], r[2] - W, r[3] - H)
                if out > 2:
                    a = frame_bad.setdefault((o["id"], "frame"), [t, t, 0, o["name"], "warn", f"({o['kind']}) partly off-screen"]); a[1] = t; a[2] = max(a[2], out)
    for (eid, txt), (t0, t1, px, role) in safe_bad.items():
        issues.append(_issue("error", "safe", f"label '{txt}' ({role or 'text'}) leaves the title-safe area by {px:.0f}px", t0, t1))
    loose = defaultdict(list)          # un-annotated objects (episodes not on the kit): one line per scene
    for (oid, _), (t0, t1, px, name, sev, what) in frame_bad.items():
        if sev == "warn":
            loose[what].append((t0, t1, px))
        else:
            issues.append(_issue(sev, "safe", f"object {name}#{oid} {what} by {px:.0f}px", t0, t1))
    for what, v in loose.items():
        issues.append(_issue("warn", "safe", f"{len(v)} objects {what} (up to {max(x[2] for x in v):.0f}px): check props "
                                             f"stay in frame", min(x[0] for x in v), max(x[1] for x in v)))
    for k, (t0, t1, ta, tb, ar) in over.items():
        issues.append(_issue("error", "overlap", f"labels overlap: '{ta}' and '{tb}' ({ar:.0f} px²)", t0, t1))

    # ---- cut: the last frame
    last, prev = states[-1], states[-2] if len(states) > 1 else states[-1]
    is_end = sc.render == "endcard" or spec.get("fade_out")
    if not is_end:
        # half-faded = partly transparent AND still changing (a label deliberately dimmed to 0.55 is a steady state)
        pt = {x["id"]: x["op"] for x in prev["texts"]}
        for x in last["texts"]:
            if 0.05 < x["op"] < 0.95 and abs(x["op"] - pt.get(x["id"], 0.0)) > 0.01:
                issues.append(_issue("error", "cut", f"label '{x['text'][:40]}' is half-faded ({x['op']:.2f}) at the cut", dur))
        pv = {o["id"]: o for o in prev["objs"]}
        for o in last["objs"]:
            if 0.05 < o["op"] < 0.95 and abs(o["op"] - pv.get(o["id"], {"op": 0})["op"]) > 0.01:
                issues.append(_issue("error", "cut", f"object {o['name']}#{o['id']} is half-faded ({o['op']:.2f}) at the cut", dur))
            q = pv.get(o["id"])
            if q:
                mv = max(abs(a - b) for a, b in zip(o["p"], q["p"]))
                if mv > 0.003 or abs(o["s"][0] - q["s"][0]) > 0.003:
                    sev = "warn" if o["kind"] == "idle" else "error"
                    issues.append(_issue(sev, "cut", f"object {o['name']}#{o['id']} ({o['kind']}) still moving at the cut "
                                                      f"({mv * 30:.2f} units/s)", dur))
        for name in last.get("tw", []):
            issues.append(_issue("error", "cut", f"animation '{name}' is cut off mid-way", dur))

    # ---- events
    events = []
    tx = defaultdict(list); ob = defaultdict(list)
    for st in states:
        for x in st["texts"]:
            tx[x["id"]].append((st["t"], x["op"], x["text"]))
        for o in st["objs"]:
            ob[o["id"]].append((st["t"], o["p"], o["op"]))
    seen_t = sorted(s["t"] for s in states)
    dt = 0.1
    for k, ser in tx.items():
        prev_op, prev_txt, stable_since = 0.0, None, -9
        last_t = None
        for t, op, txt in ser:
            if last_t is not None and t - last_t > dt * 1.6:
                prev_op = 0.0                    # it was invisible in between
            if op >= 0.5 > prev_op:
                events.append((t, "text", txt[:40]))
            elif op >= 0.5 and txt != prev_txt and t - stable_since >= 0.4:
                events.append((t, "text-change", txt[:40]))
            if txt != prev_txt:
                stable_since = t
            prev_op, prev_txt, last_t = op, txt, t
    for k, ser in ob.items():
        last_t, lp, moving_since, still_since = None, None, None, -9
        for t, p, op in ser:
            if last_t is None or t - last_t > dt * 1.6:
                if t > 0.05:
                    events.append((t, "object-appears", str(k)))
                still_since = t
            elif lp is not None:
                mv = max(abs(a - b) for a, b in zip(p, lp))
                if mv > 0.01:
                    if t - still_since >= 0.4:
                        events.append((t, "object-moves", str(k)))
                    still_since = t + 1e-6
            last_t, lp = t, p
    for w in spec.get("_tweens", []):
        events.append((w["at"], "tween", w["name"]))
    events.sort()
    ev_times = [e[0] for e in events]

    # ---- coverage: narration without anything new on screen
    speech = sorted((c[0], c[1], lid) for lid, c in spec["cues"].items())
    pts = [0.0] + [t for t in ev_times if 0 <= t <= dur] + [dur]
    for a, b in zip(pts, pts[1:]):
        if b - a <= GAP_MAX:
            continue
        talk = sum(max(0, min(b, e) - max(a, s)) for s, e, _ in speech)
        if talk > GAP_MAX:
            lines = [lid for s, e, lid in speech if min(b, e) > max(a, s)]
            issues.append(_issue("error", "coverage", f"{b - a:.1f} s with no new visual event while narrating "
                                                      f"({', '.join(lines)}): add a word-anchored event", a, b))

    # ---- numbers
    from .numbers import agrees, screen_numbers, spoken_numbers
    from .kit import line_of
    scene_said = {lid: spoken_numbers(script.get(lid, "")) for lid in spec["cues"]}
    all_said = [n for v in scene_said.values() for n in v]
    anchors = spec.get("qa", {}).get("anchors", [])
    settled = {}
    for k, ser in tx.items():
        run, rt = 0, None
        for i, (t, op, txt) in enumerate(ser):
            if op >= 0.5 and i and ser[i - 1][2] == txt and ser[i - 1][1] >= 0.5:
                run += 1
            else:
                run, rt = 0, t
            if run >= 2 and (k, txt) not in settled:
                settled[(k, txt)] = rt
    roles = {x["id"]: (x["role"], x["anchor"]) for st in states for x in st["texts"]}
    for (k, txt), t in settled.items():
        role, anc = roles.get(k, ("", ""))
        if role in ("brand", "caption", "hook", "cta"):
            continue
        nums = [n for n in screen_numbers(txt)]
        if not nums:
            continue
        line = line_of(anc) if anc else None
        if not line:
            near = [a for a in anchors if abs(a["t"] - t) <= 0.6]
            line = near[0]["line"] if near else None
        static = t <= 0.25 and not line
        # meta numbers (player count, fair share, "Mistake 4") are context, not claims: only FYI when unsaid
        meta = role in ("pill", "fair", "title", "kicker", "context") or bool(re.search(r"fair share|\bplayers?\b|mistake", txt, re.I))
        pct = {float(m.replace(",", "")) for m in re.findall(r"(\d[\d,]*(?:\.\d+)?)\s*%", txt)}
        for x in nums:
            if meta:
                if not agrees(x, all_said):
                    issues.append(_issue("info", "numbers", f"'{txt}' shows {x:g} (context, not said)", t))
                continue
            said_here = scene_said.get(line) or []
            if x in pct:            # a percentage is compared with percentage-like numbers ("the first seat" is not 1%)
                said_here = [v for v in said_here if v > 5]
            if line and said_here:
                if not agrees(x, said_here):
                    issues.append(_issue("error", "numbers", f"'{txt}' shows {x:g} but {line} says "
                                                             f"{', '.join(f'{v:g}' for v in said_here)}", t))
            elif not agrees(x, all_said):
                sev = "info" if static else "warn"
                issues.append(_issue(sev, "numbers", f"'{txt}' shows {x:g}, not said in this scene"
                                                     + (f" (anchored to {line})" if line else ""), t))

    # ---- clipping: interpenetrating objects, cards too close to their neighbour (z-fight), cards under the table
    clip = {}
    for st in states:
        for a, b, depth, kind in st.get("clips", []):
            k = (a, b, kind)
            c = clip.setdefault(k, [st["t"], st["t"], depth]); c[1] = st["t"]
            c[2] = max(c[2], depth) if kind != "too-close" else min(c[2], depth)
    WHAT = {"intersect": "intersects", "too-close": "is too close to (z-fight risk, gap", "below": "sinks into the"}
    for (a, b, kind), (t0, t1, depth) in sorted(clip.items(), key=lambda kv: kv[1][0]):
        msg = (f"{a} intersects {b} (depth {depth:.3f})" if kind == "intersect" else
               f"{a} is only {depth:.4f} from {b} along its normal (parallel overlapping cards need >= 0.003)" if kind == "too-close"
               else f"{a} sinks {depth:.3f} below the table surface")
        issues.append(_issue("error", "clipping", msg, t0, t1))

    # ---- fill (Shorts): the main visual must fill the content band (creator: "too small, empty middle")
    if spec.get("short"):
        fills = []
        for st in states:
            if st["t"] < max(1.0, 0.75 * dur) or not st.get("content"):     # the built visual (last quarter)
                continue
            rs = [o["r"] for o in st["objs"] if o["r"] and o["kind"] in ("key", "decor") and o["op"] > 0.05]
            rs += [x["r"] for x in st["texts"] if x["role"] in ("value", "label", "fair", "context") and x["op"] > 0.3]   # a chart = bars + its labels
            if rs:
                c = st["content"]
                y0 = max(c[1], min(r[1] for r in rs)); y1 = min(c[3], max(r[3] for r in rs))
                fh = max(0, y1 - y0) / max(1, c[3] - c[1])
                if sc.render in ("statement", "title"):       # words can't be stretched: filling the width counts too
                    x0 = max(c[0], min(r[0] for r in rs)); x1 = min(c[2], max(r[2] for r in rs))
                    fh = max(fh, max(0, x1 - x0) / max(1, c[2] - c[0]))
                fills.append(fh)
        if fills:
            fm = sorted(fills)[len(fills) // 2]
            spec.setdefault("_metrics", {})["fill"] = round(fm, 3)
            if fm < 0.75:
                issues.append(_issue("error", "fill", f"the main visual fills only {fm:.0%} of the content band height "
                                                      f"(need 75%): scale it up / frame the camera on it"))

    # ---- captions
    if cfg.get("burn_captions") is False and spec.get("captions"):
        issues.append(_issue("error", "captions", f"burn_captions is false but {len(spec['captions'])} captions were passed to the scene"))
    if cfg.get("burn_captions") is False and not spec.get("short"):
        for st in states:
            if any(x["role"] == "caption" for x in st["texts"]):
                issues.append(_issue("error", "captions", "a caption is drawn although burn_captions is false", st["t"])); break
    return issues, events


# ------------------------------------------------------------------ anchors (straight from scenes.yaml)
def check_anchors(scenes, ep):
    from .kit import Resolver, is_anchor
    out = defaultdict(list)
    for sc in scenes:
        R = Resolver(sc, ep)
        def walk(o, path):
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, f"{path}.{k}")
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f"{path}[{i}]")
            elif is_anchor(o):
                R.at(o, path, drop_on_error=True)
        walk(sc.params, "params")
        for e in R.errors:
            out[sc.id].append(_issue("error", "anchors", e["error"] + f"  [{e['path']}]"))
        # statement lines that never found their first word fall back silently: flag them
        if sc.render in ("statement",) and sc.params.get("lines") and sc.cues:
            from .kit import norm
            words = {norm(w) for c in sc.cues.values() for w, _, _ in c.words}
            for ln in sc.params["lines"]:
                text = ln["text"] if isinstance(ln, dict) else ln
                if not (isinstance(ln, dict) and ln.get("at")) and norm(str(text).split()[0]) not in words:
                    out[sc.id].append(_issue("warn", "anchors", f"statement line '{text}' is not timed to a spoken word "
                                                                 f"(first word not said): give it an 'at' anchor"))
    return out


# ------------------------------------------------------------------ pixels (rendered video)
def pixel_checks(video: Path, timeline):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", "scale=320:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                        "-f", "null", "-"], capture_output=True, text=True)
    ys = [float(m) for m in re.findall(r"YAVG=([\d.]+)", r.stderr)]
    fps = 30.0
    issues = []
    import numpy as np
    y = np.array(ys)
    if not len(y):
        return [_issue("error", "pixels", f"could not read frames of {video}")], []
    def where(t):
        for s in timeline:
            if s["start"] <= t < s["start"] + s["duration"]:
                return s["id"]
        return "?"
    black = np.flatnonzero(y <= 20)          # limited-range black measures 16
    if len(black):
        runs = np.split(black, np.flatnonzero(np.diff(black) > 1) + 1)
        for rr in runs:
            t0, t1 = rr[0] / fps, (rr[-1] + 1) / fps
            if rr[-1] >= len(y) - 2 * fps and where(t0) in ("endcard", "?"):
                continue                              # the end card's own fade-out
            issues.append(_issue("error", "pixels", f"black frames in {where(t0)}", t0, t1, scene=where(t0)))
    k = 7
    near_black = np.zeros(len(y), bool)
    for b in black:
        near_black[max(0, b - k): b + k + 1] = True   # black runs are reported above, not as flashes
    for i in range(k, len(y) - k):
        if near_black[i]:
            continue
        # a flash/dip differs from BOTH sides in the same direction (a hard cut is a step: one side agrees)
        before, after = np.median(y[i - k:i]), np.median(y[i + 1:i + k + 1])
        db, da = y[i] - before, y[i] - after
        if abs(db) > 14 and abs(da) > 14 and np.sign(db) == np.sign(da):
            t = i / fps
            issues.append(_issue("error", "pixels", f"brightness {'flash' if db > 0 else 'dip'} "
                                                    f"({y[i]:.0f} vs {before:.0f}/{after:.0f}) in {where(t)}", t, scene=where(t)))
    # collapse neighbours
    out, last = [], None
    for it in issues:
        if last and it["check"] == "pixels" and last["msg"].split("(")[0] == it["msg"].split("(")[0] and it["t"][0] - last["t"][1] < 0.2:
            last["t"][1] = it["t"][1]; continue
        out.append(it); last = it
    return out, ys


def flicker_check(video: Path, timeline, w=540, h=960, T=24, min_repeats=3, limit=0.0002):
    """Z-fighting / shimmer: pixels whose brightness jumps and comes straight back (A -> B -> A) between consecutive
    frames, REPEATEDLY in the same place (>= 3 times within 1 s). A fast-moving card toggles each pixel once as it
    passes; coplanar faces fighting in the depth buffer toggle in place, frame after frame.
    Error when, in any 1 s window, more than 0.02% of the frame's pixels flicker like that (the card hands in the first
    native same-cards Short: well over; clean renders: ~0)."""
    import numpy as np
    vw, vh = (w, h)
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                         "-of", "csv=p=0", str(video)], capture_output=True, text=True).stdout.strip().split(",")
    if pr and len(pr) == 2 and int(pr[0]) > int(pr[1]):
        vw, vh = h, w                                      # landscape video
    p = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf", f"scale={vw}:{vh},format=gray",
                          "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    n, fps = vw * vh, 30
    prev2 = prev1 = None
    toggles = []                                           # per frame: boolean toggle mask (packed)
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        f = np.frombuffer(buf, np.uint8).reshape(vh, vw).astype(np.int16)
        if prev2 is not None:
            d1, d2 = prev1 - prev2, f - prev1
            toggles.append((np.abs(d1) > T) & (np.abs(d2) > T) & (np.sign(d1) != np.sign(d2)) & (np.abs(f - prev2) < T // 2))
        prev2, prev1 = prev1, f
    p.wait()
    def where(t):
        for sc in timeline:
            if sc["start"] <= t < sc["start"] + sc["duration"]:
                return sc["id"]
        return "?"
    issues, worst, runs = [], 0.0, []
    for i in range(0, max(1, len(toggles) - fps + 1), fps // 2):
        win = toggles[i:i + fps]
        if not win:
            break
        cnt = np.sum(win, axis=0)
        bad = cnt >= min_repeats
        frac = float(bad.mean())
        worst = max(worst, frac)
        if frac > limit:
            ys, xs = np.nonzero(bad)
            box = (xs.min() / vw, ys.min() / vh, xs.max() / vw, ys.max() / vh)
            if runs and i <= runs[-1][1]:
                runs[-1][1] = i + fps; runs[-1][2] = max(runs[-1][2], frac)
            else:
                runs.append([i, i + fps, frac, box])
    for i0, i1, frac, box in runs:
        t0, t1 = (i0 + 1) / fps, (i1 + 1) / fps
        issues.append(_issue("error", "flicker", f"flicker (z-fighting/shimmer) in {where(t0)}: {frac:.3%} of pixels toggle "
                                                 f">= {min_repeats}x per second in place (limit {limit:.2%}), around x "
                                                 f"{box[0]:.0%}-{box[2]:.0%}, y {box[1]:.0%}-{box[3]:.0%}", t0, t1, scene=where(t0)))
    return issues, {"flicker_worst_1s": round(worst, 6)}


def opening_checks(video: Path, band=(0.20, 0.78)):
    """Shorts: the first second decides everything (first EK Short kept 24% of viewers; it opened on an empty table).
    Frame 1 must already be populated (non-background pixels in the content band >= 60% of the clip's median frame)
    and moving (median frame-to-frame change over the first 0.5 s >= 0.1 grey levels, mean over 1 s >= 0.25)."""
    import numpy as np
    w, h = 72, 128
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-vf", f"scale={w}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)[:, int(h * band[0]):int(h * band[1])]
    if len(f) < 32:
        return [_issue("error", "opening", "clip shorter than a second")], {}
    busy = np.array([(np.abs(x - np.median(x)) > 14).mean() for x in f])
    med = float(np.median(busy))
    mot = np.abs(np.diff(f[:31], axis=0)).mean(axis=(1, 2))
    m = {"first_frame_fill": round(float(busy[0]), 3), "median_fill": round(med, 3),
         "fill_ratio": round(float(busy[0]) / max(med, 1e-6), 2), "motion_first_half_s": round(float(np.median(mot[:15])), 3),
         "motion_first_s": round(float(mot.mean()), 3)}
    out = []
    if busy[0] < 0.6 * med:
        out.append(_issue("error", "opening", f"frame 1 is nearly empty: {m['fill_ratio']:.0%} as full as a typical frame "
                                              f"(need 60%): start with the main visual already on screen", 0))
    if m["motion_first_half_s"] < 0.1 or m["motion_first_s"] < 0.25:
        out.append(_issue("error", "opening", f"too still in the first second (frame change {m['motion_first_half_s']:.2f} "
                                              f"/ {m['motion_first_s']:.2f}; need 0.10 / 0.25): move from frame 1", 0, 1))
    return out, m


def contact_from_video(video: Path, out: Path, every=10):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True).stdout.strip() or 0)
    rows = max(1, -(-int(dur // every + 1) // 6))          # grid sized to the video (no empty rows)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf",
                    f"fps=1/{every},scale=384:-2,tile=6x{rows}", "-frames:v", "1", str(out)], check=True)
    return out


# ------------------------------------------------------------------ report
def write_report(res, out_dir: Path, title):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "visual.json").write_text(json.dumps(res, indent=1))
    lines = [f"VISUAL QA: {title}", ""]
    tot = defaultdict(int)
    for sid, r in res["scenes"].items():
        for it in r["issues"]:
            tot[(it["sev"], it["check"])] += 1
    nerr = sum(v for (s, _), v in tot.items() if s == "error")
    nwarn = sum(v for (s, _), v in tot.items() if s == "warn")
    lines.append(f"RESULT: {'FAIL' if nerr else 'PASS'}  ({nerr} errors, {nwarn} warnings)")
    lines.append("by check: " + ", ".join(f"{c} {s}:{n}" for (s, c), n in sorted(tot.items())))
    lines.append("")
    # the same problem in many scenes (e.g. a shared label) is printed once
    seen = defaultdict(list)
    for sid, r in res["scenes"].items():
        for it in r["issues"]:
            if it["sev"] != "info":
                seen[(it["sev"], it["check"], it["msg"])].append(sid)
    common = {k for k, v in seen.items() if len(v) >= 3}
    if common:
        lines.append("[across scenes]")
        for k in sorted(common):
            lines.append(f"  {k[0].upper():5s} {k[1]:9s} {'':14s} {k[2]}  -> {len(seen[k])} scenes: {', '.join(seen[k])}")
        lines.append("")
    for sid, r in res["scenes"].items():
        its = [i for i in r["issues"] if i["sev"] != "info" and (i["sev"], i["check"], i["msg"]) not in common]
        if not its:
            continue
        lines.append(f"[{sid}]  ({r.get('duration', 0):.1f}s, {r.get('events', 0)} events)")
        for it in sorted(its, key=lambda i: (i["sev"] != "error", i.get("t", [0])[0])):
            ts = f"{it['t'][0]:6.2f}-{it['t'][1]:<6.2f}s" if "t" in it else " " * 14
            lines.append(f"  {it['sev'].upper():5s} {it['check']:9s} {ts} {it['msg']}")
        lines.append("")
    (out_dir / "visual.txt").write_text("\n".join(lines) + "\n")
    return nerr, "\n".join(lines)


def run(slug, video=None, only=None, vertical=False, stills=True, out_dir=None, short=None, scenes_override=None,
        timeline=None, contact_every=10):
    from .stills import contact, render_frames, specs
    from .timeline import load_yaml, parse_script
    ep = ROOT / "episodes" / slug
    cfg = load_yaml(ep / "scenes.yaml")
    script = parse_script(ep / "script.md")
    if scenes_override is not None:
        scenes, sp = scenes_override
    else:
        _, scenes, sp = specs(slug, vertical, only, short)
    out_dir = Path(out_dir) if out_dir else ep / "out" / ("qa-v" if vertical else "qa")
    out_dir.mkdir(parents=True, exist_ok=True)
    anchor_issues = check_anchors([s for s in scenes if not only or s.id in only], ep)
    from .qa_static import run as static_run           # hand-built cards in the episode's scene code
    own_code = any(str(spec.get("module", "")).startswith(f"/episodes/{slug}/web/") for _, spec in sp)
    st_bad = static_run([slug]) if (ep / "web").is_dir() and own_code else {}   # only when scenes run its own code
    print(f"[qa] probing {len(sp)} scenes ...", flush=True)
    states = probe([(sc.id, spec) for sc, spec in sp], out_dir)
    res = {"slug": slug, "vertical": vertical, "scenes": {}}
    for sc, spec in sp:
        st = states.get(sc.id, [])
        spec["_tweens"] = st[0].get("alltw", []) if st else []     # kit scenes: every registered transition
        issues, events = check_scene(sc, spec, st, script, cfg)
        issues = anchor_issues.get(sc.id, []) + issues
        res["scenes"][sc.id] = {"duration": spec["duration"], "events": len(events), "issues": issues, **spec.get("_metrics", {}),
                                "event_times": [round(e[0], 2) for e in events][:400]}
    for f, v in st_bad.items():
        res["scenes"].setdefault("static", {"issues": []})["issues"] += [
            _issue("error", "static", f"{f} line {x['line']}: {x['why']}") for x in v]
    if video:
        tl = ep / "out" / "final" / "timeline.json"
        if timeline is None:
            timeline = json.loads(tl.read_text()) if tl.exists() else [{"id": s.id, "start": s.start, "duration": s.duration} for s in scenes]
        pix, _ = pixel_checks(Path(video), timeline)
        fl, fm = flicker_check(Path(video), timeline)
        pix += fl
        res["flicker"] = fm
        if short:
            op, metrics = opening_checks(Path(video))
            pix += op
            res["opening"] = metrics
        for it in pix:
            res["scenes"].setdefault(it.get("scene", "video"), {"issues": []})["issues"].append(it)
        res["contact"] = str(contact_from_video(Path(video), out_dir / "contact.png", contact_every))
    elif stills:
        jobs, pngs, labels = [], [], []
        for sc, spec in sp:
            n = spec["n_frames"]
            fr = [n // 2, n - 1]
            ps = [out_dir / f"still-{sc.id}-{k}.png" for k in range(2)]
            jobs.append((spec, fr, ps)); pngs += ps; labels += [f"{sc.id} mid", f"{sc.id} cut"]
        render_frames(jobs, 0.25)
        res["contact"] = str(contact(pngs, labels, out_dir / "contact.png", cols=6 if not vertical else 8, w=320 if not vertical else 180))
        for p in pngs:
            p.unlink(missing_ok=True)
    for p in out_dir.glob("probe-*.jsonl"):
        p.unlink()
    nerr, text = write_report(res, out_dir, f"{slug}{' (9:16)' if vertical else ''}")
    print(text)
    print(f"report: {out_dir / 'visual.txt'}  json: {out_dir / 'visual.json'}  contact: {res.get('contact')}")
    return nerr


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--video"); ap.add_argument("--only", nargs="*")
    ap.add_argument("--vertical", action="store_true"); ap.add_argument("--no-stills", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    raise SystemExit(1 if run(a.slug, a.video, a.only, a.vertical, not a.no_stills, a.out) else 0)


if __name__ == "__main__":
    main()
