"""Audio mix (narration + ducked music), SRT captions, concatenation and muxing."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from . import music
from .timeline import Scene
from .tts import SR, write_wav


def narration_track(scenes: list[Scene], duration: float) -> np.ndarray:
    out = np.zeros(int(duration * SR) + SR, np.float32)
    for sc in scenes:
        for t0, sp in sc.speech:
            i = int(t0 * SR)
            out[i:i + len(sp.audio)] += sp.audio[: len(out) - i]
    return out[: int(duration * SR)]


def _smooth(x: np.ndarray, sec: float) -> np.ndarray:
    k = max(1, int(sec * SR))
    c = np.cumsum(np.concatenate([[0], x]))
    y = (c[k:] - c[:-k]) / k
    return np.concatenate([y, np.full(k - 1, y[-1] if len(y) else 0)])


def mix(scenes: list[Scene], duration: float, out_wav: Path, mood="curious",
        music_db=-20.0, duck_db=-9.0, seed=0) -> Path:
    voice = narration_track(scenes, duration)
    voice = voice / (np.abs(voice).max() + 1e-9) * 0.89
    bed = music.bed(duration, mood, seed)[: len(voice)]
    env = _smooth((np.abs(voice) > 0.02).astype(np.float32), 0.25)
    env = np.clip(_smooth(env, 0.4) * 3, 0, 1)
    gain = 10 ** ((music_db + duck_db * env) / 20)
    stereo_bed = np.stack([bed, np.roll(bed, int(0.012 * SR))], 1) * gain[:, None]
    out = stereo_bed + voice[:, None]
    write_wav(out_wav, out / max(1.0, np.abs(out).max()))
    return out_wav


def srt(chunks, path: Path) -> Path:
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    lines = []
    for i, (s, e, txt) in enumerate(chunks, 1):
        lines += [str(i), f"{ts(s)} --> {ts(e)}", txt, ""]
    Path(path).write_text("\n".join(lines))
    return Path(path)


def concat(parts: list[Path], out: Path) -> Path:
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lst), "-c", "copy", str(out)], check=True)
    lst.unlink()
    return out


def mux(video: Path, audio: Path, out: Path, loudnorm=True) -> Path:
    af = ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"] if loudnorm else []
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-i", str(audio),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", *af, "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    return out
