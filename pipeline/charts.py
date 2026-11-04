"""Live charts bound to simulation state."""
from __future__ import annotations

import numpy as np
import skia

from . import style as S
from .draw import paint, text


class Axes:
    """A rectangle mapping data (x, y) -> pixels with optional grid + labels."""

    def __init__(self, x, y, w, h, xlim, ylim):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xlim, self.ylim = xlim, ylim

    def px(self, xv, yv):
        fx = (np.asarray(xv) - self.xlim[0]) / (self.xlim[1] - self.xlim[0])
        fy = (np.asarray(yv) - self.ylim[0]) / (self.ylim[1] - self.ylim[0])
        return self.x + fx * self.w, self.y + self.h - fy * self.h

    def frame(self, c, yticks=(), ytick_fmt="{:g}", xlabel=None, ylabel=None, alpha=1.0,
              xticks=(), xtick_fmt="{:g}"):
        g = S.with_alpha(S.GRID, alpha)
        for yv in yticks:
            _, py = self.px(self.xlim[0], yv)
            c.drawLine(self.x, py, self.x + self.w, py, paint(g, 1.5))
            text(c, ytick_fmt.format(yv), self.x - 12, py + 7, 20, S.MUTED, align="right", alpha=alpha)
        for xv in xticks:
            px, _ = self.px(xv, self.ylim[0])
            text(c, xtick_fmt.format(xv), px, self.y + self.h + 30, 20, S.MUTED, align="center", alpha=alpha)
        c.drawLine(self.x, self.y + self.h, self.x + self.w, self.y + self.h, paint(S.with_alpha(S.MUTED, alpha), 2))
        if xlabel:
            text(c, xlabel, self.x + self.w, self.y + self.h + 30 + (28 if xticks else 0), 20, S.MUTED, align="right", alpha=alpha)
        if ylabel:
            text(c, ylabel, self.x, self.y - 18, 22, S.MUTED, weight="medium", alpha=alpha)


def line_series(c, ax: Axes, xs, ys, color, width=4.0, alpha=1.0):
    if len(xs) < 2:
        return
    px, py = ax.px(xs, ys)
    path = skia.Path()
    path.moveTo(float(px[0]), float(py[0]))
    for a, b in zip(px[1:], py[1:]):
        path.lineTo(float(a), float(b))
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(ax.x, ax.y - 10, ax.w, ax.h + 20))
    c.drawPath(path, paint(S.with_alpha(color, alpha), width))
    c.restore()
    c.drawCircle(float(px[-1]), float(py[-1]), width * 1.6, paint(S.with_alpha(color, alpha)))


def bars(c, ax: Axes, xs, heights, colors, width_frac=0.75, alpha=1.0):
    bw = ax.w / (ax.xlim[1] - ax.xlim[0]) * width_frac
    for xv, hv, col in zip(xs, heights, colors):
        px, py = ax.px(xv, hv)
        _, p0 = ax.px(xv, ax.ylim[0])
        c.drawRect(skia.Rect.MakeLTRB(float(px - bw / 2), float(py), float(px + bw / 2), float(p0)),
                   paint(S.with_alpha(col, alpha)))


def histogram(c, ax: Axes, values, bins, color=S.TEAL, alpha=1.0):
    h, edges = np.histogram(values, bins=bins, range=ax.xlim)
    centers = (edges[:-1] + edges[1:]) / 2
    bars(c, ax, centers, h, [color] * len(h), width_frac=0.9 * (edges[1] - edges[0]), alpha=alpha)


class SpaceTime:
    """Space-time diagram (time on x, ring position on y), pre-rasterised once.

    Each vehicle trajectory is drawn as a continuous trail coloured by speed.
    `reveal(t)` gives the pixel column up to which the image should be shown.
    """

    def __init__(self, t: np.ndarray, x: np.ndarray, v: np.ndarray, length: float,
                 t0: float, t1: float, w_px: int, h_px: int, vmax: float,
                 thickness: int = 2):
        self.t0, self.t1, self.w, self.h = t0, t1, w_px, h_px
        img = np.zeros((h_px, w_px, 4), np.uint8)
        lut = np.array([S.rgba(S.speed_color(i / 255)) for i in range(256)], np.uint8)
        cols = np.linspace(t0, t1, w_px + 1)
        idx = np.clip(np.interp(cols, t, np.arange(len(t))), 0, len(t) - 1)
        i0 = np.floor(idx).astype(int)
        w = idx - i0
        i1 = np.minimum(i0 + 1, len(t) - 1)
        xs = x[i0] * (1 - w[:, None]) + x[i1] * w[:, None]       # (w_px+1, N)
        vs = v[i0] * (1 - w[:, None]) + v[i1] * w[:, None]
        ys = (xs % length) / length * (h_px - 1)
        cidx = np.clip(vs / vmax * 255, 0, 255).astype(int)
        for col in range(w_px):
            ya, yb = ys[col], ys[col + 1]
            for car in range(xs.shape[1]):
                a, b = ya[car], yb[car]
                if b < a - h_px / 2:   # wrapped around the top (not float jitter)
                    segs = [(a, h_px - 1), (0, b)]
                else:
                    segs = [(min(a, b), max(a, b))]
                colr = lut[cidx[col, car]]
                for s0, s1 in segs:
                    lo = int(s0) - thickness // 2
                    hi = int(s1) + thickness - thickness // 2
                    img[max(0, lo):min(h_px, hi), col] = colr
        self.img = img[::-1].copy()     # position increases upwards
        self.skimg = skia.Image.fromarray(self.img, colorType=skia.kRGBA_8888_ColorType)

    def draw(self, c, x, y, w, h, t_now: float | None = None, alpha=1.0):
        frac = 1.0 if t_now is None else float(np.clip((t_now - self.t0) / (self.t1 - self.t0), 0, 1))
        if frac <= 0:
            return
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x, y, w * frac, h))
        p = skia.Paint(AntiAlias=True)
        p.setAlphaf(alpha)
        c.drawImageRect(self.skimg, skia.Rect.MakeXYWH(x, y, w, h),
                        skia.SamplingOptions(skia.FilterMode.kLinear), p)
        c.restore()
