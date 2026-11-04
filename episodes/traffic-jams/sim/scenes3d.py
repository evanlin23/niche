"""3D (tabletop) spec builders for Episode 1. Each returns plain JSON for
episodes/traffic-jams/web/scenes.js, which draws it with the shared Three.js stage."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from pipeline.render3d import f32

HERE = Path(__file__).resolve().parent
EP = HERE.parent
_spec = importlib.util.spec_from_file_location("tj_scenes2d", HERE / "scenes.py")
S2 = importlib.util.module_from_spec(_spec)
sys.modules["tj_scenes2d"] = S2
_spec.loader.exec_module(S2)

FPS = 30
MODULE = "/episodes/traffic-jams/web/scenes.js"
KMH = 3.6


def base(ctx) -> dict:
    sc = ctx.scene
    n = max(1, int(round(sc.duration * FPS)))
    return {
        "module": MODULE, "type": sc.render, "W": ctx.fmt.width, "H": ctx.fmt.height, "fps": FPS,
        "duration": sc.duration, "n_frames": n, "id": sc.id,
        "cues": {k: [c.start, c.end] for k, c in sc.cues.items()},
        "params": sc.params, "captions": ctx.captions, "hook": ctx.hook,
    }


def frame_times(ctx, n):
    return [S2.sim_time(ctx, i / FPS) for i in range(n)]


def sim_block(run_name, t_lo, t_hi):
    r = S2.run(run_name)
    i0 = max(0, int(np.floor(t_lo / 0.1)) - 1)
    i1 = min(len(r.t) - 1, int(np.ceil(t_hi / 0.1)) + 1)
    return {"t0": float(r.t[i0]), "dt": 0.1, "count": i1 - i0 + 1, "n": int(r["x"].shape[1]),
            "length": S2.RING_M, "x": f32(r["x"][i0:i1 + 1]), "v": f32(r["v"][i0:i1 + 1] * KMH)}


# ------------------------------------------------------------- printed space-time sheet
PAPER = np.array([236, 232, 222])
SLATE = np.array([58, 65, 82]); AMBER = np.array([255, 182, 39]); RED = np.array([229, 72, 77])


def sheet_png(run_name, t0, t1, w=1500, h=760) -> str:
    out = EP / "out" / "assets" / f"st-{run_name}-{int(t0)}-{int(t1)}-{w}x{h}.png"
    if out.exists():
        return "/" + str(out.relative_to(EP.parent.parent))
    out.parent.mkdir(parents=True, exist_ok=True)
    r = S2.run(run_name)
    img = np.zeros((h, w, 3), np.uint8) + PAPER.astype(np.uint8)
    cols = np.linspace(t0, t1, w + 1)
    idx = np.clip(np.interp(cols, r.t, np.arange(len(r.t))), 0, len(r.t) - 1)
    i0 = np.floor(idx).astype(int); i1 = np.minimum(i0 + 1, len(r.t) - 1); wgt = (idx - i0)[:, None]
    xs = r["x"][i0] * (1 - wgt) + r["x"][i1] * wgt
    vs = (r["v"][i0] * (1 - wgt) + r["v"][i1] * wgt) * KMH
    ys = (xs % S2.RING_M) / S2.RING_M * (h - 1)
    f = np.clip(vs / 50.0, 0, 1)
    colr = np.where((f < 0.5)[..., None], RED + (AMBER - RED) * (f / 0.5)[..., None],
                    AMBER + (SLATE - AMBER) * ((f - 0.5) / 0.5)[..., None]).astype(np.uint8)
    for c in range(w):
        a_, b_ = ys[c], ys[c + 1]
        for k in range(xs.shape[1]):
            a, b = a_[k], b_[k]
            segs = [(a, h - 1), (0, b)] if b < a - h / 2 else [(min(a, b), max(a, b))]
            for s0, s1 in segs:
                img[max(0, int(s0) - 1):min(h, int(s1) + 2), c] = colr[c, k]
    Image.fromarray(img[::-1]).save(out)
    return "/" + str(out.relative_to(EP.parent.parent))


# ------------------------------------------------------------- per-scene builders
def ring(ctx):
    s = base(ctx)
    p = ctx.params
    s["frame_t"] = frame_times(ctx, s["n_frames"])
    lo = min(s["frame_t"]) - 65
    s["sim"] = sim_block(p["run"], max(0, lo), max(s["frame_t"]) + 1)
    if p.get("panel") == "spacetime" or p.get("mode") in ("spacetime", "ring_st"):
        st = p.get("st_range", [p["t0"], p["t1"]])
        s["sheet"] = {"url": sheet_png(p["run"], st[0], st[1]), "t0": st[0], "t1": st[1]}
    if p.get("mode") == "spacetime":
        tj, xj = S2.jam_anchor(p["run"], p.get("wave_t", 650.0), 120.0)
        s["jam_guide"] = [tj, xj, tj + 120, xj - 3.89 * 120]
    s["smoother_on"] = S2.RUNS[p["run"]]["smoother"]
    s["brake"] = list(S2.BRAKE[1:3]) if S2.RUNS[p["run"]]["brake"] else None
    return s


def spacetime(ctx):
    s = base(ctx)
    p = ctx.params
    s["sheet"] = {"url": sheet_png(p["run"], p["t0"], p["t1"]), "t0": p["t0"], "t1": p["t1"]}
    tj, xj = S2.jam_anchor(p["run"], p.get("wave_t", 700.0), 100.0)
    s["jam_guide"] = [tj, xj, tj + 100, xj - 3.89 * 100]
    return s


def chain(ctx):
    s = base(ctx)
    mins = S2.chain_minima()
    s["mins"] = [float(m) for m in mins]
    s["first_stop"] = int(np.argmax(mins < 1.0))
    return s


def why(ctx):
    s = base(ctx)
    r = S2.run("tap")
    sel = (r.t >= 18) & (r.t <= 50)
    s["lag"] = {"t": r.t[sel].tolist(), "lead": (r["v"][sel, 0] * KMH).tolist(), "follow": (r["v"][sel, 39] * KMH).tolist()}
    return s


def title(ctx):
    s = base(ctx)
    r = S2.run("tap")
    i = int(700 / 0.1)
    s["still"] = {"x": (r["x"][i] % S2.RING_M).tolist(), "v": (r["v"][i] * KMH).tolist()}
    return s


def endcard(ctx):
    s = base(ctx)
    r = S2.run("smooth")
    i = int(1000 / 0.1)
    s["still"] = {"x": (r["x"][i] % S2.RING_M).tolist(), "v": (r["v"][i] * KMH).tolist()}
    return s


def simple(ctx):
    return base(ctx)


def short(ctx):
    return ring(ctx)


def thumbnail_spec():
    r = S2.run("tap")
    i = int(760 / 0.1)
    return {"module": MODULE, "type": "thumb", "W": 1920, "H": 1080, "fps": FPS, "duration": 1 / FPS,
            "n_frames": 1, "cues": {}, "params": {},
            "still": {"x": (r["x"][i] % S2.RING_M).tolist(), "v": (r["v"][i] * KMH).tolist()}}


SPECS = {"ring": ring, "spacetime": spacetime, "chain": chain, "why": why, "title": title,
         "endcard": endcard, "experiment": simple, "equation": simple, "short": short}


def build_spec(ctx) -> dict:
    return SPECS[ctx.scene.render](ctx)
