"""Frame-exact offline rendering: draw each frame with skia, pipe raw RGBA to FFmpeg.

Never screen-captures; the frame index fully determines the image.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

try:                      # 2D (skia) engine only; the 3D engine (render3d) works without it
    import skia
except ImportError:       # e.g. no libEGL on the machine
    skia = None

try:
    from . import style as S
except ImportError:
    S = None


@dataclass
class Format:
    name: str
    width: int      # logical canvas size (drawing coordinates)
    height: int
    fps: int = 60
    scale: float = 1.0  # output pixels per logical pixel (preview < 1)

    @property
    def out_size(self):
        w = int(round(self.width * self.scale / 2)) * 2
        h = int(round(self.height * self.scale / 2)) * 2
        return w, h


LONG = Format("long", 1920, 1080, 60)
SHORT = Format("short", 1080, 1920, 60)


def preview(fmt: Format) -> Format:
    return Format(fmt.name, fmt.width, fmt.height, 30, 480 / min(fmt.width, fmt.height))


DrawFn = Callable[[object, float, int], None]   # (canvas, t_seconds, frame_index)


def render_video(path: Path, fmt: Format, duration: float, draw: DrawFn,
                 crf: int = 18, preset: str = "veryfast", threads: int = 2) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    W, H = fmt.out_size
    n = max(1, int(round(duration * fmt.fps)))
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fmt.fps), "-i", "-",
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
           "-threads", str(threads), "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surface = skia.Surface(W, H)
    buf = np.empty((H, W, 4), np.uint8)
    try:
        for i in range(n):
            t = i / fmt.fps
            with surface as c:
                c.save()
                c.scale(fmt.scale, fmt.scale)
                c.clear(S.BG)
                draw(c, t, i)
                c.restore()
            surface.readPixels(skia.ImageInfo.Make(W, H, skia.kRGBA_8888_ColorType, skia.kPremul_AlphaType), buf)
            proc.stdin.write(buf.tobytes())
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode:
        raise RuntimeError(f"ffmpeg failed for {path}")
    return path


def render_still(path: Path, width: int, height: int, draw: Callable[[object], None]) -> Path:
    surface = skia.Surface(width, height)
    with surface as c:
        c.clear(S.BG)
        draw(c)
    surface.makeImageSnapshot().save(str(path), skia.kPNG)
    return Path(path)
