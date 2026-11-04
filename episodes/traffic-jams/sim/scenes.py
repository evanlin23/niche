"""Scene renderers for Episode 1: "Why Traffic Jams Appear From Nowhere".

Each entry in SCENES is a factory: fn(ctx) -> draw(canvas, t, frame_index).
`ctx.scene` carries duration, params and narration cue times (scene-relative),
so on-screen events are synced to the voice-over.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np
import skia

from pipeline import style as S
from pipeline.charts import Axes, SpaceTime, bars, line_series
from pipeline.draw import (car_on_ring, ease, fade, paint, pill, rrect, text,
                           text_block, text_width, window)
from sims import RingRoad
from sims.idm import BrakeEvent, Smoother

KMH = 3.6
V_COLOR = 15.0          # m/s mapped to full teal
RING_M = 1000.0

# ---------------------------------------------------------------- simulations
RUNS = {
    "tap": dict(n=40, brake=True, smoother=None, t_end=1000),
    "calm": dict(n=40, brake=False, smoother=None, t_end=200),
    "gaps": dict(n=30, brake=True, smoother=None, t_end=420),
    "smooth": dict(n=40, brake=True, smoother=620.0, t_end=1100),
}
BRAKE = (0, 20.0, 23.0, 2.0)      # car, start, end, decel
SMOOTH_CAR = 20


@lru_cache(None)
def run(name):
    cfg = RUNS[name]
    brakes = [BrakeEvent(*BRAKE)] if cfg["brake"] else []
    sm = [Smoother(SMOOTH_CAR, cfg["smoother"])] if cfg["smoother"] else []
    return RingRoad(cfg["n"], RING_M, brakes=brakes, smoothers=sm).run(cfg["t_end"], 0.1).finalize()


@lru_cache(None)
def spacetime(name, t0, t1, w, h):
    r = run(name)
    return SpaceTime(r.t, r["x"], r["v"], RING_M, t0, t1, w, h, V_COLOR, thickness=2)


@lru_cache(None)
def chain_minima(name="tap", n_handoffs=330):
    """Lowest speed reached by each successive car as the dip propagates backwards."""
    r = run(name)
    v = r["v"] * KMH
    n = v.shape[1]
    tprev = int(BRAKE[1] / 0.1)
    out = []
    for k in range(n_handoffs):
        c = (-k) % n
        seg = v[tprev:tprev + 150, c]
        j = int(np.argmin(seg))
        out.append(seg[j])
        tprev += j
    return np.array(out)


def jam_anchor(name, t_from, span=100.0, ws=-3.89):
    """First time >= t_from where the stopped cars' centre sits high enough on the
    ring that a guide line of slope ws over `span` seconds stays inside the plot."""
    r = run(name)
    for t in np.arange(t_from, r.t[-1] - span, 2.0):
        i = int(t / 0.1)
        m = r["v"][i] * KMH < 5
        if m.sum() < 2:
            continue
        ang = (r["x"][i][m] % RING_M) / RING_M * 2 * np.pi
        pos = np.angle(np.mean(np.exp(1j * ang))) % (2 * np.pi) / (2 * np.pi) * RING_M
        if pos > -ws * span + 80 and pos < RING_M - 60:
            return float(t), float(pos)
    return float(t_from), RING_M * 0.8


# --------------------------------------------------------------- time mapping
def sim_time(ctx, t):
    """Scene time -> sim time. Linear t0..t1, optionally pinned so that sim time
    `anchor.sim` happens exactly when narration cue `anchor.cue` starts."""
    p = ctx.params
    t0, t1, D = p["t0"], p["t1"], ctx.duration
    a = p.get("anchor")
    if a:
        ta = ctx.scene.cue(a["cue"], D / 2) + a.get("offset", 0.0)
        if t <= ta:
            return t0 + (a["sim"] - t0) * (t / max(ta, 1e-6))
        return a["sim"] + (t1 - a["sim"]) * ((t - ta) / max(D - ta, 1e-6))
    return t0 + (t1 - t0) * (t / D)


def at(ctx, ref, default=0.0):
    """A param time reference: number (seconds) or cue id (start) or 'cue_id+1.5'."""
    if ref is None:
        return default
    if isinstance(ref, (int, float)):
        return float(ref)
    off = 0.0
    if "+" in ref:
        ref, o = ref.split("+")
        off = float(o)
    end = ref.endswith(":end")
    ref = ref.replace(":end", "")
    return (ctx.scene.cue_end(ref, default) if end else ctx.scene.cue(ref, default)) + off


# ---------------------------------------------------------------- components
def watermark(c, W=1920):
    text(c, S.CHANNEL_NAME, 56, 70, 22, S.MUTED, "bold")


def draw_ring(c, ctx, t_sim, cx, cy, R, run_name, highlight=(), brake_tag=True,
              car_len=17, car_w=10, alpha=1.0, label_tracked=None):
    r = run(run_name)
    x = r.at("x", t_sim)
    v = r.at("v", t_sim)
    # road
    c.drawCircle(cx, cy, R, paint(S.with_alpha(S.PANEL, alpha), 34))
    c.drawCircle(cx, cy, R + 17, paint(S.with_alpha(S.GRID, alpha), 2))
    c.drawCircle(cx, cy, R - 17, paint(S.with_alpha(S.GRID, alpha), 2))
    hl = dict(highlight)
    braking = BRAKE[1] <= t_sim < BRAKE[2] + 1.0
    smoother_on = RUNS[run_name]["smoother"] and t_sim >= RUNS[run_name]["smoother"] - 8
    for i in range(len(x)):
        col = S.speed_color(v[i] / V_COLOR)
        outline = None
        role = hl.get(i)
        if role == "brake":
            outline = S.AMBER
        elif role == "track":
            outline = S.TEXT
        elif role == "smooth":
            if smoother_on:
                col = S.BLUE
                outline = S.with_alpha(S.BLUE, 0.6)
        if alpha < 1:
            col = S.with_alpha(col, alpha)
        px, py = car_on_ring(c, cx, cy, R, (x[i] % RING_M) / RING_M, col, car_len, car_w, outline)
        if role == "brake" and brake_tag and braking and RUNS[run_name]["brake"]:
            ang = (x[i] % RING_M) / RING_M * 2 * math.pi - math.pi / 2
            pill(c, "BRAKING", cx + (R + 70) * math.cos(ang), cy + (R + 70) * math.sin(ang) - 18,
                 20, align="center")
    return x, v


def speed_legend(c, x, y, alpha=1.0):
    w = 260
    for k in range(w):
        c.drawLine(x + k, y, x + k, y + 12, paint(S.with_alpha(S.speed_color(k / w), alpha), 1.2, aa=False))
    text(c, "stopped", x, y + 40, 20, S.MUTED, alpha=alpha)
    text(c, f"{V_COLOR * KMH:.0f}+ km/h", x + w, y + 40, 20, S.MUTED, align="right", alpha=alpha)


def speed_chart(c, ctx, t_sim, x, y, w, h, run_name, cars, colors, labels, span=60.0, alpha=1.0,
                title="Speed (km/h)"):
    r = run(run_name)
    lo = max(0.0, t_sim - span)
    ax = Axes(x, y, w, h, (lo, lo + span), (0, 80))
    ax.frame(c, yticks=(0, 20, 40, 60, 80), ylabel=title, alpha=alpha)
    i0, i1 = int(lo / 0.1), int(t_sim / 0.1)
    ts = np.append(r.t[i0:i1 + 1], t_sim)
    for car, col in zip(cars, colors):
        vs = np.append(r["v"][i0:i1 + 1, car], r.at("v", t_sim)[car]) * KMH
        line_series(c, ax, ts, vs, col, 4, alpha)
    lx = x
    for lab, col in zip(labels, colors):
        c.drawCircle(lx + 8, y + h + 40, 7, paint(S.with_alpha(col, alpha)))
        text(c, lab, lx + 24, y + h + 47, 21, S.TEXT, alpha=alpha)
        lx += text_width(lab, 21) + 70
    text(c, f"t = {t_sim:5.0f} s", x + w, y - 18, 22, S.MUTED, "medium", "right", alpha)


def stopped_chart(c, ctx, t_sim, x, y, w, h, run_name, span=240.0, t_from=None, alpha=1.0):
    r = run(run_name)
    lo = t_from if t_from is not None else max(0.0, t_sim - span)
    ax = Axes(x, y, w, h, (lo, lo + span), (0, 12))
    ax.frame(c, yticks=(0, 4, 8, 12), ylabel="Cars stopped (< 5 km/h)", alpha=alpha)
    i0, i1 = int(lo / 0.1), int(t_sim / 0.1)
    if i1 > i0 + 1:
        cnt = (r["v"][i0:i1 + 1] * KMH < 5).sum(1)
        line_series(c, ax, r.t[i0:i1 + 1], cnt, S.RED, 4, alpha)
    text(c, f"t = {t_sim:5.0f} s", x + w, y - 18, 22, S.MUTED, "medium", "right", alpha)


def notes(c, ctx, t, items, default_size=30):
    for it in items or []:
        s, e = at(ctx, it.get("at"), 0.0), at(ctx, it.get("until"), ctx.duration)
        a = window(t, s, e)
        if a <= 0:
            continue
        x, y = it["pos"]
        if it.get("pill"):
            pill(c, it["text"], x, y, it.get("size", 26), bg=getattr(S, it.get("color", "AMBER")),
                 align=it.get("align", "left"), alpha=a)
        else:
            text_block(c, it["text"], x, y, it.get("size", default_size), it.get("width", 760),
                       getattr(S, it.get("color", "TEXT")), it.get("weight", "semibold"),
                       it.get("align", "left"), alpha=a)


def scene_fade(c, t, D, W=1920, H=1080, fin=0.35, fout=0.35):
    a = max(1 - fade(t, 0, fin), fade(t, D - fout, fout))
    if a > 0.001:
        c.drawRect(skia.Rect.MakeWH(W, H), paint(S.with_alpha(S.BG, a)))


# ------------------------------------------------------------------ scenes
def ring_scene(ctx):
    """Ring road with an optional right-hand panel: chart | stopped | spacetime | none."""
    p = ctx.params
    layout = p.get("layout", "split")
    run_name = p["run"]
    hl = [(int(k), v) for k, v in (p.get("highlight") or {}).items()]
    panel = p.get("panel", "chart")
    D = ctx.duration
    if panel == "spacetime":
        st_t0, st_t1 = p.get("st_range", (p["t0"], p["t1"]))
        st = spacetime(run_name, st_t0, st_t1, 760, 640)

    def draw(c, t, i):
        ts = sim_time(ctx, t)
        if layout == "center":
            draw_ring(c, ctx, ts, 960, 560, 400, run_name, hl, car_len=19, car_w=11)
        else:
            draw_ring(c, ctx, ts, 540, 560, 370, run_name, hl)
            pa = fade(t, at(ctx, p.get("panel_at"), 0.0), 0.6)
            if panel == "chart":
                cars = p.get("chart_cars", [39])
                cols = [getattr(S, k) for k in p.get("chart_colors", ["TEXT"])]
                speed_chart(c, ctx, ts, 1080, 300, 760, 420, run_name, cars, cols,
                            p.get("chart_labels", ["tracked car"]), alpha=pa)
            elif panel == "stopped":
                stopped_chart(c, ctx, ts, 1080, 300, 760, 420, run_name,
                              span=p["t1"] - p["t0"], t_from=p["t0"], alpha=pa)
            elif panel == "spacetime":
                x0, y0 = 1080, 200
                rrect(c, x0 - 4, y0 - 4, 768, 648, 6, S.with_alpha(S.PANEL, pa))
                st.draw(c, x0, y0, 760, 640, ts, pa)
                text(c, "position", x0 - 14, y0 + 20, 20, S.MUTED, align="right", alpha=pa)
                text(c, "time →", x0 + 760, y0 + 680, 20, S.MUTED, align="right", alpha=pa)
                text(c, "Space-time diagram", x0, y0 - 24, 24, S.MUTED, "medium", alpha=pa)
            if p.get("legend", True):
                speed_legend(c, 1080, 900, fade(t, at(ctx, p.get("legend_at"), 0.0), 0.5))
        if p.get("title"):
            text(c, p["title"], 56, 130, 44, S.TEXT, "bold", alpha=fade(t, 0.1))
        notes(c, ctx, t, p.get("notes"))
        watermark(c)
        scene_fade(c, t, D, fin=p.get("fade_in", 0.35), fout=p.get("fade_out", 0.35))
    return draw


def title_scene(ctx):
    p = ctx.params
    D = ctx.duration

    def draw(c, t, i):
        ts = 300 + t * 2
        draw_ring(c, ctx, ts, 960, 540, 470, "tap", alpha=0.18, car_len=20, car_w=12)
        a = fade(t, 0.2, 0.6)
        text(c, S.CHANNEL_NAME, 960, 400, 30, S.AMBER, "bold", "center", a)
        for k, line in enumerate(p["lines"]):
            text(c, line, 960, 520 + k * 96, 84, S.TEXT, "black", "center", fade(t, 0.4 + 0.2 * k, 0.6))
        text(c, p.get("sub", ""), 960, 760, 30, S.MUTED, "medium", "center", fade(t, 1.0, 0.6))
        scene_fade(c, t, D)
    return draw


def experiment_scene(ctx):
    D = ctx.duration
    facts = [("exp1", "22 cars"), ("exp1+3.0", "230 m circuit"), ("exp1+6.0", "target: 30 km/h"),
             ("exp2", "no lights · no junctions"), ("exp3", "result: a jam, anyway")]

    def draw(c, t, i):
        cx, cy, R = 560, 560, 330
        c.drawCircle(cx, cy, R, paint(S.PANEL, 40))
        jam = fade(t, at(ctx, "exp3+1.0"), 2.5)
        base = t * 0.035
        for k in range(22):
            ang0 = k / 22
            # illustrative only: after exp3 a cluster forms and drifts backwards
            d = ((ang0 + base - (0.5 - 0.02 * t)) % 1) - 0.5
            squeeze = jam * 0.08 * math.exp(-(d / 0.12) ** 2) * np.sign(d) * -1
            f = ang0 + base + squeeze
            slow = jam * math.exp(-(d / 0.07) ** 2)
            col = S.speed_color(1 - slow)
            car_on_ring(c, cx, cy, R, f % 1, col, 26, 14)
        text(c, "230 m", cx, cy + 10, 40, S.MUTED, "semibold", "center")
        text(c, "Sugiyama et al. (2008)", 1080, 250, 46, S.TEXT, "bold", alpha=fade(t, 0.2))
        text(c, "New Journal of Physics 10, 033001", 1080, 296, 24, S.MUTED, alpha=fade(t, 0.4))
        for k, (cue, s) in enumerate(facts):
            a = fade(t, at(ctx, cue), 0.5)
            col = S.RED if "jam" in s else S.TEXT
            c.drawCircle(1096, 392 + k * 82 - 10, 7, paint(S.with_alpha(col, a)))
            text(c, s, 1124, 392 + k * 82, 38, col, "semibold", alpha=a)
        text(c, "(animation is illustrative)", 1080, 880, 20, S.MUTED, alpha=fade(t, at(ctx, "exp3+1.0")))
        notes(c, ctx, t, ctx.params.get("notes"))
        watermark(c)
        scene_fade(c, t, D)
    return draw


def _eq(c, x, y, parts, size, t, ctx):
    """parts: [(text, color_name or None, highlight_window)]"""
    for s, col, win in parts:
        hi = 0.0
        if win:
            hi = window(t, at(ctx, win[0]), at(ctx, win[1]), 0.4)
        base = S.TEXT
        color = S.lerp_color(base, getattr(S, col), hi) if col else base
        w = text_width(s, size, "medium")
        if hi > 0:
            rrect(c, x - 6, y - size * 0.95, w + 12, size * 1.3, 10,
                  S.with_alpha(getattr(S, col), 0.16 * hi))
        text(c, s, x, y, size, color, "medium")
        x += w
    return x


def equation_scene(ctx):
    D = ctx.duration
    go = ("mod3", "mod4")
    dist = ("mod4", "mod6")

    def draw(c, t, i):
        text(c, "The Intelligent Driver Model", 160, 190, 54, S.TEXT, "bold", alpha=fade(t, 0.1))
        text(c, "Treiber, Hennecke & Helbing — Phys. Rev. E 62, 1805 (2000)", 160, 240, 24, S.MUTED,
             alpha=fade(t, 0.3))
        a = fade(t, at(ctx, "mod2"), 0.6)
        if a > 0:
            c.saveLayerAlpha(None, int(a * 255))
            _eq(c, 160, 420, [("acceleration = a · [ ", None, None), ("1 − (v / v₀)⁴", "TEAL", go),
                              (" − ", None, None), ("( s* / s )²", "RED", dist), (" ]", None, None)], 60, t, ctx)
            _eq(c, 160, 540, [("s* = ", None, None), ("s₀ + v·T + v·Δv / 2√(ab)", "RED", ("mod4", "mod5"))],
                46, t, ctx)
            c.restore()
        text(c, "urge to go", 520, 320, 30, S.TEAL, "semibold", alpha=window(t, at(ctx, "mod3"), at(ctx, "mod6")))
        text(c, "urge to keep your distance", 900, 320, 30, S.RED, "semibold",
             alpha=window(t, at(ctx, "mod4"), at(ctx, "mod6")))
        # two-car diagram
        da = fade(t, at(ctx, "mod4"), 0.6)
        if da > 0:
            y = 760
            c.drawLine(140, y + 40, 1780, y + 40, paint(S.with_alpha(S.GRID, da), 3))
            fx = 420 + 30 * math.sin(t * 0.8)
            rrect(c, fx, y - 10, 150, 46, 10, S.with_alpha(S.TEAL, da))
            rrect(c, 1180, y - 10, 150, 46, 10, S.with_alpha(S.TEAL, da))
            text(c, "you", fx + 75, y + 82, 24, S.MUTED, align="center", alpha=da)
            text(c, "car ahead", 1255, y + 82, 24, S.MUTED, align="center", alpha=da)
            c.drawLine(fx + 160, y + 13, 1170, y + 13, paint(S.with_alpha(S.AMBER, da), 3))
            text(c, "gap  s", (fx + 1170) / 2 + 80, y - 26, 30, S.AMBER, "semibold", "center", da)
            text(c, "v", fx + 75, y - 26, 30, S.TEXT, "semibold", "center", da)
            text(c, "Δv = closing speed", 1350, y - 26, 26, S.MUTED, alpha=da)
        pa = window(t, at(ctx, "mod6"), D + 1)
        if pa > 0:
            rows = ["v₀ = 108 km/h", "T = 1.2 s", "a = 0.8 m/s²", "b = 1.5 m/s²", "s₀ = 2 m"]
            for k, r in enumerate(rows):
                text(c, r, 1450, 380 + k * 52, 30, S.MUTED, "medium", alpha=pa)
            text(c, "same for every car", 1450, 380 + 5 * 52 + 10, 26, S.AMBER, "semibold", alpha=pa)
        watermark(c)
        scene_fade(c, t, D)
    return draw


def chain_scene(ctx):
    D = ctx.duration
    mins = chain_minima()
    n = len(mins)
    first_stop = int(np.argmax(mins < 1.0))

    def draw(c, t, i):
        text(c, "Lowest speed as the slowdown passes each car", 160, 170, 46, S.TEXT, "bold", alpha=fade(t, 0.1))
        ax = Axes(200, 260, 1560, 560, (-1, n), (0, 60))
        ax.frame(c, yticks=(0, 20, 40, 60), ylabel="km/h", xlabel="car-to-car handoffs →",
                 xticks=(0, 40, 80, 120, 160, 200, 240, 280, 320), alpha=fade(t, 0.2))
        r0, r1 = at(ctx, "amp1+1.0"), at(ctx, "amp3+2.5")
        k = int(n * ease((t - r0) / max(1e-6, r1 - r0)))
        bars(c, ax, np.arange(k), mins[:k], [S.speed_color(m / (V_COLOR * KMH)) for m in mins[:k]], 0.7)
        # laps
        la = fade(t, at(ctx, "amp1+2"), 0.5)
        for lap in range(1, n // 40 + 1):
            px, _ = ax.px(lap * 40 - 0.5, 0)
            if lap * 40 <= k:
                c.drawLine(px, 262, px, 820, paint(S.with_alpha(S.GRID, la), 1))
                text(c, f"lap {lap + 1}", px + 8, 284, 18, S.MUTED, alpha=la)
        a2 = window(t, at(ctx, "amp2"), D + 1)
        if a2 > 0 and k > 30:
            px, py = ax.px(12, 47)
            pill(c, "softened", px - 40, py - 80, 24, bg=S.TEAL, alpha=a2)
        a3 = window(t, at(ctx, "amp3"), D + 1)
        if a3 > 0 and k > first_stop:
            px, py = ax.px(first_stop, 2)
            pill(c, f"first full stop · handoff {first_stop}", px - 330, py - 120, 24, bg=S.RED,
                 fg=S.TEXT, alpha=a3)
        text(c, f"first car: {mins[0]:.0f} km/h", 200, 900, 26, S.AMBER, "semibold", alpha=fade(t, at(ctx, "amp1+1")))
        a4 = fade(t, at(ctx, "amp4"), 0.6)
        if a4 > 0:
            pill(c, "STRING INSTABILITY", 960, 930, 36, bg=S.AMBER, align="center", alpha=a4)
        watermark(c)
        scene_fade(c, t, D)
    return draw


def spacetime_scene(ctx):
    p = ctx.params
    D = ctx.duration
    t0, t1 = p["t0"], p["t1"]
    W, H = 1500, 760
    st = spacetime(p["run"], t0, t1, W, H)
    X, Y = 260, 170

    def draw(c, t, i):
        r0, r1 = at(ctx, p.get("reveal_from", "st2")), at(ctx, p.get("reveal_to", "st3"))
        ts = t0 + (t1 - t0) * ease((t - r0) / max(1e-6, r1 - r0)) if t >= r0 else t0
        rrect(c, X - 6, Y - 6, W + 12, H + 12, 8, S.PANEL)
        st.draw(c, X, Y, W, H, ts)
        ax = Axes(X, Y, W, H, (t0 / 60, t1 / 60), (0, 1000))
        ax.frame(c, yticks=(0, 250, 500, 750, 1000), ytick_fmt="{:g} m",
                 xticks=range(int(t0 / 60), int(t1 / 60) + 1, 2), xtick_fmt="{:g} min", alpha=fade(t, 0.2))
        text(c, "position on ring", X, Y - 24, 24, S.MUTED, "medium", alpha=fade(t, 0.2))
        a = fade(t, at(ctx, "st2"), 0.5)
        if a > 0:
            # traffic direction arrow
            c.drawLine(140, 820, 140, 380, paint(S.with_alpha(S.TEAL, a), 5))
            c.drawLine(140, 380, 122, 410, paint(S.with_alpha(S.TEAL, a), 5))
            c.drawLine(140, 380, 158, 410, paint(S.with_alpha(S.TEAL, a), 5))
            text(c, "traffic", 140, 860, 22, S.TEAL, "semibold", "center", a)
        a3 = fade(t, at(ctx, "st3+2.5"), 0.6)
        if a3 > 0:
            # wave slope: -14 km/h  => dx/dt = -3.9 m/s ; draw a guide line over one stripe
            tt0, xx0 = jam_anchor(p["run"], p.get("wave_t", 700.0))
            ws = p.get("wave_speed", -3.89)
            tt1 = tt0 + 100
            x0p, y0p = ax.px(tt0 / 60, xx0)
            x1p, y1p = ax.px(tt1 / 60, xx0 + ws * 100)
            c.drawLine(x0p - 30, y0p - 30 * (y1p - y0p) / (x1p - x0p), x1p + 30, y1p + 30 * (y1p - y0p) / (x1p - x0p),
                       paint(S.with_alpha(S.TEXT, a3), 5))
            pill(c, "jam moves backwards · ~14 km/h", x1p - 470, y1p + 30, 26, bg=S.RED, fg=S.TEXT, alpha=a3)
        a4 = window(t, at(ctx, "st4"), D + 1)
        if a4 > 0:
            pill(c, "real highways: ~15–20 km/h", X + 20, Y + 20, 26, bg=S.AMBER, alpha=a4)
        watermark(c)
        scene_fade(c, t, D)
    return draw


def why_scene(ctx):
    D = ctx.duration
    r = run("tap")

    def draw(c, t, i):
        text(c, "Two ingredients", 160, 160, 52, S.TEXT, "bold", alpha=fade(t, 0.1))
        # LAG panel
        a1 = fade(t, at(ctx, "why2"), 0.5)
        if a1 > 0:
            rrect(c, 140, 230, 800, 660, 18, S.with_alpha(S.PANEL, a1))
            text(c, "1 · LAG", 190, 300, 40, S.AMBER, "black", alpha=a1)
            ax = Axes(220, 380, 660, 380, (18, 50), (25, 60))
            ax.frame(c, yticks=(30, 40, 50, 60), ylabel="km/h", alpha=a1)
            k = ease((t - at(ctx, "why2")) / 6)
            te = 18 + 32 * k
            sel = (r.t >= 18) & (r.t <= te)
            if sel.sum() > 1:
                line_series(c, ax, r.t[sel], r["v"][sel, 0] * KMH, S.AMBER, 4, a1)
                line_series(c, ax, r.t[sel], r["v"][sel, 39] * KMH, S.TEXT, 4, a1)
            text(c, "car ahead", 230, 830, 22, S.AMBER, alpha=a1)
            text(c, "you (reacting later)", 400, 830, 22, S.TEXT, alpha=a1)
        a2 = fade(t, at(ctx, "why3"), 0.5)
        if a2 > 0:
            rrect(c, 980, 230, 800, 660, 18, S.with_alpha(S.PANEL, a2))
            text(c, "2 · DENSITY", 1030, 300, 40, S.RED, "black", alpha=a2)
            for row, (n, label, col) in enumerate([(40, "40 cars → 20 m gaps", S.RED), (30, "30 cars → 28 m gaps", S.TEAL)]):
                y = 440 + row * 220
                text(c, label, 1030, y - 30, 30, col, "semibold", alpha=a2)
                span = 700
                L = 1000 / n
                for k2 in range(int(250 / L) + 1):
                    x = 1030 + k2 * L * span / 250
                    if x + 5 * span / 250 > 1030 + span:
                        break
                    rrect(c, x, y, 5 * span / 250, 34, 5, S.with_alpha(col, a2))
            text(c, "(250 m of road shown)", 1030, 820, 22, S.MUTED, alpha=a2)
        watermark(c)
        scene_fade(c, t, D)
    return draw


def endcard_scene(ctx):
    D = ctx.duration
    p = ctx.params

    def draw(c, t, i):
        draw_ring(c, ctx, 950 + t * 2, 960, 540, 470, "smooth", {SMOOTH_CAR: "smooth"}.items(),
                  alpha=0.15, car_len=20, car_w=12)
        a = fade(t, 0.3, 0.6)
        text(c, p.get("next_label", "NEXT EPISODE"), 260, 300, 28, S.AMBER, "bold", alpha=a)
        rrect(c, 260, 330, 800, 450, 16, S.with_alpha(S.PANEL, a))    # end-screen video slot
        text(c, p.get("next_title", ""), 660, 570, 40, S.TEXT, "bold", "center", a)
        c.drawCircle(1440, 555, 150, paint(S.with_alpha(S.PANEL, a)))  # subscribe slot
        text(c, "subscribe", 1440, 565, 30, S.MUTED, "semibold", "center", a)
        text(c, "Simulation code: link in the description", 960, 900, 30, S.MUTED, "medium", "center", a)
        scene_fade(c, t, D, fout=1.0)
    return draw


# ------------------------------------------------------------------ shorts
def _captions(c, ctx, t, y, W=1080):
    for s, e, txt in ctx.captions:
        if s - 0.05 <= t < e + 0.12:
            size = 64
            lines = []
            words, cur = txt.upper().split(), ""
            for w in words:
                tt = (cur + " " + w).strip()
                if text_width(tt, size, "black") > W - 160 and cur:
                    lines.append(cur); cur = w
                else:
                    cur = tt
            lines.append(cur)
            pop = 1 + 0.08 * (1 - ease((t - s) / 0.12))
            for k, ln in enumerate(lines):
                yy = y + k * size * 1.15
                c.save()
                c.translate(W / 2, yy)
                c.scale(pop, pop)
                # outline
                f = S.font(size, "black")
                w = f.measureText(ln)
                stroke = paint(0xFF000000, 12)
                c.drawString(ln, -w / 2, 0, f, stroke)
                c.drawString(ln, -w / 2, 0, f, paint(S.TEXT if k else S.AMBER))
                c.restore()
            break


def short_scene(ctx):
    p = ctx.params
    D = ctx.duration
    run_name = p["run"]
    hl = [(int(k), v) for k, v in (p.get("highlight") or {}).items()]
    mode = p.get("mode", "ring")
    if mode in ("spacetime", "ring_st"):
        st0, st1 = p.get("st_range", (p["t0"], p["t1"]))
        sth = 760 if mode == "spacetime" else 400
        st = spacetime(run_name, st0, st1, 940, sth)

    def draw(c, t, i):
        ts = sim_time(ctx, t)
        # hook (visible from frame 0)
        hook = ctx.hook or ""
        hy = 250
        for k, ln in enumerate(hook.split("\n")):
            text(c, ln, 540, hy + k * 92, 80, S.TEXT, "black", "center")
        if mode == "ring":
            draw_ring(c, ctx, ts, 540, 900, 400, run_name, hl, car_len=22, car_w=13)
            if p.get("chart"):
                pass
        elif mode == "ring_st":
            draw_ring(c, ctx, ts, 540, 720, 270, run_name, hl, car_len=18, car_w=11)
            rrect(c, 66, 1176, 948, 408, 8, S.PANEL)
            st.draw(c, 70, 1180, 940, 400, ts)
        else:
            rrect(c, 66, 466, 948, 768, 8, S.PANEL)
            rev = p.get("reveal", [0.3, D * 0.6])
            tt = p["t0"] + (p["t1"] - p["t0"]) * ease((t - rev[0]) / (rev[1] - rev[0]))
            st.draw(c, 70, 470, 940, 760, tt)
            text(c, "time →", 1010, 1280, 26, S.MUTED, align="right")
            text(c, "position", 70, 450, 26, S.MUTED)
            a = fade(t, at(ctx, p.get("arrow_at", 5.0)), 0.5)
            if a > 0:   # cars travel (almost straight) up the diagram
                col = S.with_alpha(S.TEAL, a)
                c.drawLine(40, 1180, 40, 560, paint(col, 6))
                c.drawLine(40, 560, 22, 592, paint(col, 6))
                c.drawLine(40, 560, 58, 592, paint(col, 6))
                pill(c, "cars ↑", 70, 500, 30, bg=S.TEAL, alpha=a)
            a2 = fade(t, at(ctx, p.get("jam_at", 9.0)), 0.5)
            if a2 > 0:
                ws = -3.89
                tj, xj = jam_anchor(run_name, p.get("wave_t", 650.0), 120.0)
                fx = lambda tt: 70 + (tt - p["t0"]) / (p["t1"] - p["t0"]) * 940
                fy = lambda xx: 470 + 760 - xx / RING_M * 760
                c.drawLine(fx(tj), fy(xj), fx(tj + 120), fy(xj + ws * 120), paint(S.with_alpha(S.TEXT, a2), 6))
                pill(c, "jam ↓ ~14 km/h", fx(tj + 120) - 200, fy(xj + ws * 120) + 20, 34, bg=S.RED, fg=S.TEXT, alpha=a2)
        notes(c, ctx, t, p.get("notes"), 40)
        _captions(c, ctx, t, p.get("caption_y", 1460))
        text(c, S.CHANNEL_NAME, 540, 1700 if mode != "ring_st" else 1760, 26, S.MUTED, "bold", "center")
        a = 1 - fade(t, 0, 0.15)
        if a > 0:
            c.drawRect(skia.Rect.MakeWH(1080, 1920), paint(S.with_alpha(S.BG, a)))
    return draw


# ---------------------------------------------------------------- thumbnail
def thumbnail(c):
    c.save()
    c.scale(1280 / 1920, 720 / 1080)
    st = spacetime("tap", 300, 1000, 1920, 1080)
    p = skia.Paint(); p.setAlphaf(0.35)
    c.drawImageRect(st.skimg, skia.Rect.MakeWH(1920, 1080), skia.SamplingOptions(), p)
    c.drawRect(skia.Rect.MakeWH(1920, 1080), paint(S.with_alpha(S.BG, 0.35)))
    draw_ring(c, None, 760, 1380, 560, 420, "tap", car_len=26, car_w=15)
    text(c, "ONE", 90, 330, 190, S.TEXT, "black")
    text(c, "BRAKE", 90, 520, 190, S.AMBER, "black")
    text(c, "TAP.", 90, 710, 190, S.TEXT, "black")
    pill(c, "NO ACCIDENT. STILL STUCK.", 100, 800, 52, bg=S.RED, fg=S.TEXT, weight="black")
    c.restore()


SCENES = {
    "ring": ring_scene,
    "title": title_scene,
    "experiment": experiment_scene,
    "equation": equation_scene,
    "chain": chain_scene,
    "spacetime": spacetime_scene,
    "why": why_scene,
    "endcard": endcard_scene,
    "short": short_scene,
}
