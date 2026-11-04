"""Drive the Three.js stage (pipeline/web) frame-by-frame in headless Chromium.

A scene's spec is plain JSON: {module, W, H, fps, duration, n_frames, cues, ...scene data}.
Large float arrays are passed base64-encoded (see f32()).
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
CAPTURE = ROOT / "pipeline" / "web" / "capture.js"


def f32(a) -> str:
    return base64.b64encode(np.ascontiguousarray(a, np.float32).tobytes()).decode()


def _env():
    env = dict(os.environ)
    if shutil.which("npm"):
        g = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
        env["NODE_PATH"] = os.pathsep.join(p for p in (env.get("NODE_PATH"), g) if p)
    return env


def render(spec: dict, out: Path, scale: float = 1.0, crf: int = 18, png_frame: int | None = None,
           frames: tuple[int, int] | None = None) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmpdir = ROOT / ".cache" / "specs"
    tmpdir.mkdir(parents=True, exist_ok=True)
    spec = dict(spec, scale=scale)
    fd, sp = tempfile.mkstemp(suffix=".json", dir=tmpdir)
    with os.fdopen(fd, "w") as f:
        json.dump(spec, f)
    job = {"root": str(ROOT), "spec": "/" + str(Path(sp).relative_to(ROOT)), "out": str(out),
           "width": int(round(spec["W"] * scale / 2) * 2), "height": int(round(spec["H"] * scale / 2) * 2),
           "fps": spec["fps"], "crf": crf}
    if frames is not None:
        job["from"], job["to"] = frames
    if png_frame is not None:
        job["only_frame"] = png_frame
        job["png"] = str(out)
    jp = Path(sp).with_suffix(".job.json")
    jp.write_text(json.dumps(job))
    try:
        subprocess.run(["node", str(CAPTURE), str(jp)], check=True, env=_env())
    finally:
        Path(sp).unlink(missing_ok=True)
        jp.unlink(missing_ok=True)
    return out
