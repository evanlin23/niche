"""Small drawing helpers on top of skia (all coordinates are logical pixels)."""
from __future__ import annotations

import math

import numpy as np
import skia

from . import style as S


def paint(color: int, stroke: float | None = None, aa=True, cap=skia.Paint.kRound_Cap) -> skia.Paint:
    p = skia.Paint(AntiAlias=aa, Color=color)
    if stroke is not None:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    return p


def text_width(s: str, size: float, weight="regular") -> float:
    return S.font(size, weight).measureText(s)


def text(c: skia.Canvas, s: str, x: float, y: float, size=32, color=S.TEXT,
         weight="regular", align="left", alpha=1.0):
    """Draw text with baseline at y. align: left|center|right."""
    if alpha <= 0:
        return
    f = S.font(size, weight)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    c.drawString(s, x, y, f, paint(S.with_alpha(color, alpha * S.rgba(color)[3] / 255)))


def wrap(s: str, size: float, max_w: float, weight="regular") -> list[str]:
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t, size, weight) > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def text_block(c, s, x, y, size, max_w, color=S.TEXT, weight="regular", align="left",
               line_h=1.3, alpha=1.0) -> float:
    lines = wrap(s, size, max_w, weight)
    for i, ln in enumerate(lines):
        text(c, ln, x, y + i * size * line_h, size, color, weight, align, alpha)
    return y + len(lines) * size * line_h


def rrect(c, x, y, w, h, r, color, stroke=None):
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint(color, stroke))


def pill(c, s, x, y, size=24, fg=S.BG, bg=S.AMBER, weight="semibold", align="left", alpha=1.0, pad=None):
    if alpha <= 0:
        return
    pad = pad or size * 0.55
    w = text_width(s, size, weight) + 2 * pad
    h = size * 1.6
    if align == "center":
        x -= w / 2
    rrect(c, x, y, w, h, h / 2, S.with_alpha(bg, alpha))
    text(c, s, x + pad, y + h / 2 + size * 0.36, size, fg, weight, alpha=alpha)
    return w


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def fade(t: float, start: float, dur: float = 0.4) -> float:
    return ease((t - start) / dur) if dur > 0 else float(t >= start)


def window(t: float, start: float, end: float, dur: float = 0.35) -> float:
    """1 inside [start, end] with eased fade in/out."""
    return min(fade(t, start, dur), 1 - fade(t, end - dur, dur))


def car_on_ring(c, cx, cy, radius, pos_frac, color, length_px=22, width_px=12, outline=None):
    ang = pos_frac * 2 * math.pi - math.pi / 2
    x, y = cx + radius * math.cos(ang), cy + radius * math.sin(ang)
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang) + 90)
    r = skia.Rect.MakeXYWH(-width_px / 2, -length_px / 2, width_px, length_px)
    c.drawRRect(skia.RRect.MakeRectXY(r, 3.5, 3.5), paint(color))
    if outline:
        c.drawRRect(skia.RRect.MakeRectXY(r.makeOutset(4, 4), 6, 6), paint(outline, 3))
    c.restore()
    return x, y


def image_from_array(arr: np.ndarray) -> skia.Image:
    """uint8 HxWx4 RGBA -> skia image."""
    return skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
