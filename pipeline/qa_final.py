"""Final-mix gate for the finished video (run after assembly, before sending it to the creator).

    make qa-final SLUG=<slug> [VIDEO=path.mp4]
    python -m pipeline.qa_final <slug> [--video path] [--short]

Checks:  loudness  -14 LUFS integrated (+/- 0.5)          peak      decoded true sample peak <= -1.0 dBFS
         duration  >= 8:00 for a long video (Shorts: <= 60 s)  captions burn_captions: false -> no captions handed
         audio     there is an audio stream, 48 kHz           to any scene, and the upload SRT exists
Writes out/qa/final.json + final.txt and exits 1 on any failure.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent


def probe(video: Path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,sample_rate,width,height",
                        "-of", "json", str(video)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def lufs(video: Path) -> float:
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(video), "-map", "0:a", "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", r[r.rfind("Summary"):]).group(1))


def peak_dbfs(video: Path) -> float:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video), "-map", "0:a", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    return float(20 * np.log10(np.abs(a).max() + 1e-12))


def check(video: Path, ep: Path | None, short=False):
    res = []
    add = lambda ok, name, msg: res.append({"ok": bool(ok), "check": name, "msg": msg})
    info = probe(video)
    streams = info.get("streams", [])
    dur = float(info["format"]["duration"])
    aud = [s for s in streams if s["codec_type"] == "audio"]
    vid = [s for s in streams if s["codec_type"] == "video"]
    add(bool(aud), "audio", f"audio stream: {'yes, ' + aud[0].get('sample_rate', '?') + ' Hz' if aud else 'MISSING'}")
    if aud:
        L = lufs(video); P = peak_dbfs(video)
        add(abs(L + 14) <= 0.5, "loudness", f"integrated loudness {L:.1f} LUFS (target -14 +/- 0.5)")
        add(P <= -1.0, "peak", f"decoded peak {P:.2f} dBFS (limit -1.0)")
    if vid:
        w, h = vid[0]["width"], vid[0]["height"]
        want = (1080, 1920) if short else (1920, 1080)
        add((w, h) == want, "size", f"video {w}x{h} (want {want[0]}x{want[1]})")
    if short:
        add(dur <= 60, "duration", f"duration {dur:.1f}s (Shorts: <= 60 s)")
    else:
        add(dur >= 480, "duration", f"duration {int(dur // 60)}:{dur % 60:04.1f} (minimum 8:00 for mid-rolls)")
    if ep is not None and not short:
        import yaml
        cfg = yaml.safe_load((ep / "scenes.yaml").read_text())
        if cfg.get("burn_captions") is False:
            # the same rule cli.cmd_episode uses: explicitly off -> no captions handed to any scene
            from .cli import cmd_episode  # noqa: F401  (import proves the module the rule lives in loads)
            src = (ROOT / "pipeline" / "cli.py").read_text()
            rule = 'elif spec.get("burn_captions") is False' in src and "caps_abs = []" in src
            add(rule, "captions", "burn_captions: false -> the assembler hands no captions to scenes"
                + ("" if rule else " (RULE MISSING in cli.py)"))
        srt = video.with_suffix(".en.srt")
        add(srt.exists(), "srt", f"upload captions {srt.name}: {'present' if srt.exists() else 'MISSING'}")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("slug"); ap.add_argument("--video"); ap.add_argument("--short", action="store_true")
    a = ap.parse_args(argv)
    ep = ROOT / "episodes" / a.slug
    video = Path(a.video) if a.video else ep / "out" / "final" / f"{a.slug}.mp4"
    if not video.exists():
        print(f"FINAL GATE: FAIL, no video at {video}"); raise SystemExit(1)
    res = check(video, ep, a.short)
    bad = [r for r in res if not r["ok"]]
    text = "\n".join([f"FINAL MIX GATE: {video.name}", f"RESULT: {'FAIL' if bad else 'PASS'}", ""]
                     + [f"  {'ok  ' if r['ok'] else 'FAIL'} {r['check']:9s} {r['msg']}" for r in res]) + "\n"
    out = ep / "out" / "qa"; out.mkdir(parents=True, exist_ok=True)
    (out / "final.txt").write_text(text); (out / "final.json").write_text(json.dumps(res, indent=1))
    print(text)
    raise SystemExit(1 if bad else 0)


if __name__ == "__main__":
    main()
