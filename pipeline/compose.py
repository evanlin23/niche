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


AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")
ROOT = Path(__file__).resolve().parent.parent


def music_bed(duration: float, mood: str, seed: int = 0) -> np.ndarray:
    """Music under the voice. `mood` is either a procedural mood ("curious", "tension") or a
    file / folder of tracks (e.g. "music/" with YouTube Audio Library downloads). Tracks are
    played in order, looped, and crossfaded (4 s) to fill the duration."""
    from .tts import read_wav
    p = Path(mood) if mood else None
    if p is not None and not p.is_absolute():
        p = ROOT / p
    tracks = []
    if p is not None and p.is_dir():
        tracks = sorted(x for x in p.iterdir() if x.suffix.lower() in AUDIO_EXT)
    elif p is not None and p.is_file():
        tracks = [p]
    if not tracks:
        return music.bed(duration, mood if mood in music.PROGRESSIONS else "curious", seed)
    n, xf = int(duration * SR), int(4 * SR)
    out = np.zeros(0, np.float32)
    k = 0
    while len(out) < n:
        t = read_wav(tracks[k % len(tracks)])
        t = t / (np.sqrt(np.mean(t ** 2)) + 1e-9) * 0.12          # equal loudness between tracks
        if len(out) >= xf and len(t) > xf:
            ramp = np.linspace(0, 1, xf, dtype=np.float32)
            out[-xf:] = out[-xf:] * (1 - ramp) + t[:xf] * ramp
            t = t[xf:]
        out = np.concatenate([out, t.astype(np.float32)])
        k += 1
    out = out[:n]
    fi, fo = int(1.5 * SR), int(4 * SR)
    out[:fi] *= np.linspace(0, 1, fi); out[-fo:] *= np.linspace(1, 0, fo)
    return out / (np.abs(out).max() + 1e-9)


def mix(scenes: list[Scene], duration: float, out_wav: Path, mood="curious",
        music_db=-20.0, duck_db=-9.0, seed=0) -> Path:
    voice = narration_track(scenes, duration)
    voice = voice / (np.abs(voice).max() + 1e-9) * 0.89
    bed = music_bed(duration, mood, seed)[: len(voice)]
    if len(bed) < len(voice):
        bed = np.pad(bed, (0, len(voice) - len(bed)))
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
