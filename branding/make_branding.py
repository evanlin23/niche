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


if "--v2" not in sys.argv:
    shot("avatar", 800, 800, [("BUH", "MUSTARD")], 2.2)
    shot("banner", 2560, 1440, [("BUH SIMULATES", None, 1.75), ("I simulate games so you can win them", "MUSTARD")], 0.311, scale=1.0)


# ---- v2: Buh, the channel character (same 3D look as the videos) ----
MASCOT = {"module": "/episodes/exploding-kittens/web/scenes.js", "type": "mascot", "fps": 30, "duration": 1.0,
          "n_frames": 31, "cues": {}, "captions": [], "theme": "custom", "font": "rubik",
          "look": "clean-sage", "quality": "high", "ssaa": 2}


def mascot(name, W, H, params, scale=1.0):
    render3d.render(dict(MASCOT, W=W, H=H, params=params), OUT / f"{name}.png", scale=scale, png_frame=5)
    print("wrote", OUT / f"{name}.png")


if __name__ == "__main__" and "--v2" in sys.argv:
    mascot("avatar-buh", 800, 800, {"expr": "happy", "turn": 0.0, "cam": [0, 2.6, 6.4], "look": [0, 2.45, 0], "fov": 34})
    # banner: Buh on the right of the 1546x423 safe area, name + tagline on the left (2560x1440 canvas)
    mascot("banner-buh", 2560, 1440, {"expr": "smug", "turn": -0.35, "at": [3.3, 0, 0], "cam": [0, 2.0, 18.5], "look": [0, 1.9, 0], "fov": 30,
                                     "texts": [{"text": "BUH SIMULATES", "x": 560, "y": 610, "size": 112},
                                               {"text": "I simulate games so you can win.", "x": 566, "y": 760, "size": 56, "color": "MUSTARD"}]})
    for e in ("happy", "shocked", "smug"):
        mascot(f"buh-{e}", 1200, 1200, {"expr": e, "turn": -0.3, "cam": [0, 2.7, 9.4], "look": [0.3, 1.85, 0]})
