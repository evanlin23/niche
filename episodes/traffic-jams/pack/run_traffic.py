"""Reproduce the three experiments from the video and save space-time diagrams.

    python run_traffic.py [--cars 40] [--length 1000] [--decel 2.0] [--minutes 15]
"""
import argparse

import numpy as np
from PIL import Image

from sims import RingRoad
from sims.idm import BrakeEvent, Smoother, wave_speed


def spacetime_png(rec, length, path, w=1200, h=600, vmax=15.0):
    img = np.full((h, w, 3), 14, np.uint8)
    cols = np.linspace(0, len(rec.t) - 1, w).astype(int)
    red, amber, teal = np.array([229, 72, 77]), np.array([255, 182, 39]), np.array([46, 196, 182])
    for ci, i in enumerate(cols):
        y = ((rec["x"][i] % length) / length * (h - 1)).astype(int)
        f = np.clip(rec["v"][i] / vmax, 0, 1)[:, None]
        col = np.where(f < 0.5, red + (amber - red) * f / 0.5, amber + (teal - amber) * (f - 0.5) / 0.5)
        img[h - 1 - y, ci] = col.astype(np.uint8)
    Image.fromarray(img).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cars", type=int, default=40)
    ap.add_argument("--length", type=float, default=1000.0)
    ap.add_argument("--decel", type=float, default=2.0)
    ap.add_argument("--minutes", type=float, default=15)
    a = ap.parse_args()
    T = a.minutes * 60
    brake = [BrakeEvent(0, 20, 23, a.decel)]
    runs = {
        "1-jam": RingRoad(a.cars, a.length, brakes=brake),
        "2-more-room": RingRoad(int(a.cars * 0.75), a.length, brakes=brake),
        "3-smoother": RingRoad(a.cars, a.length, brakes=brake, smoothers=[Smoother(a.cars // 2, T * 0.6)]),
    }
    for name, model in runs.items():
        rec = model.run(T, 0.5).finalize()
        v = rec["v"] * 3.6
        ws = wave_speed(rec.t, rec["x"], rec["v"], a.length) * 3.6
        print(f"{name:12s} cars={model.n:3d}  final min speed={v[-1].min():5.1f} km/h  "
              f"stopped now={int((v[-1] < 5).sum()):2d}  wave speed={ws:6.1f} km/h")
        spacetime_png(rec, a.length, f"{name}.png")
    print("saved 1-jam.png, 2-more-room.png, 3-smoother.png")


if __name__ == "__main__":
    main()
