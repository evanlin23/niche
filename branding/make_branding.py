"""Render channel art with the 3D stage (same look as the videos).

    python3 branding/make_branding.py
Writes branding/avatar.png (800x800) and branding/banner.png (2560x1440, text inside the
1546x423 safe area so it shows on phones, TVs and desktop).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import render3d

OUT = Path(__file__).resolve().parent
BASE = {"module": "/episodes/exploding-kittens/web/scenes.js", "type": "statement", "fps": 30, "duration": 3.0,
        "n_frames": 91, "cues": {}, "captions": [], "theme": "custom", "font": "rubik",
        "look": "clean-sage", "quality": "high", "ssaa": 2}


def shot(name, W, H, lines, size, scale=1.0):
    spec = dict(BASE, W=W, H=H, lines=[{"text": l[0], "at": 0.0, "color": l[1], "scale": (l[2] if len(l) > 2 else 1)} for l in lines],
                params={"size": size, "max_width": 12, "no_brand": True, "static": True})
    render3d.render(spec, OUT / f"{name}.png", scale=scale, png_frame=45)
    print("wrote", OUT / f"{name}.png")


shot("avatar", 800, 800, [("BUH", "MUSTARD")], 2.2)
shot("banner", 2560, 1440, [("BUH SIMULATES", None, 1.75), ("I simulate games so you can win them", "MUSTARD")], 0.5, scale=1.0)
