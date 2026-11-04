"""Audio mix (narration + ducked music), SRT captions, concatenation and muxing."""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np

from . import music
from .timeline import Scene
from .tts import SR, write_wav


def _room_bed(n: int, level_db: float) -> np.ndarray | None:
    """Continuous room tone for the gaps between lines (cleaned like the voice, at the lines' own floor level)."""
    import os
    vd = Path(os.environ.get("VOICE_DIR", ""))
    rt = vd / "_roomtone.wav"
    if not os.environ.get("VOICE_DIR") or not rt.exists():
        return None
    from .voice_clean import ffilter, load
    # raw room tone, only band-limited: running it through the noise reduction would strip the very noise we
    # want here and leave a bed full of near-silent holes
    r = ffilter(load(rt), "highpass=f=80,lowpass=f=12000")
    hop = 480; m = len(r) // hop                      # keep only steady room frames (drop dropouts / bumps)
    fr = r[: m * hop].reshape(m, hop); fdb = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-12)
    med = np.median(fdb)
    r = fr[(fdb > med - 4) & (fdb < med + 4)].ravel()
    if len(r) < SR // 4:
        return None
    # loop with crossfades so the bed has no seams
    seg, xf = len(r), int(0.05 * SR)
    out = np.zeros(n + seg, np.float32); pos = 0
    ramp = np.sqrt(np.linspace(0, 1, xf, dtype=np.float32))   # equal-power crossfade: no dip at the seams
    while pos < n:
        piece = r.copy(); piece[:xf] *= ramp; piece[-xf:] *= ramp[::-1]
        out[pos:pos + seg] += piece; pos += seg - xf
    out = out[:n]
    rms = np.sqrt(np.mean(out ** 2)) + 1e-12
    return (out * (10 ** (level_db / 20) / rms)).astype(np.float32)


def narration_track(scenes: list[Scene], duration: float) -> np.ndarray:
    """All narration lines on the timeline. Gaps between lines get a continuous room-tone bed at the lines' own
    background level: pure digital silence between lines sounds like the audio dropping out."""
    n = int(duration * SR)
    out = np.zeros(n + SR, np.float32)
    cover = np.zeros(n + SR, np.float32)
    floors = []
    for sc in scenes:
        for t0, sp in sc.speech:
            i = int(t0 * SR)
            a = sp.audio[: len(out) - i]
            out[i:i + len(a)] += a
            cover[i:i + len(a)] = 1.0
            if len(a) > SR // 2:
                hop = 480; m = len(a) // hop
                db = 20 * np.log10(np.sqrt((a[: m * hop].reshape(m, hop) ** 2).mean(1)) + 1e-9)
                floors.append(np.percentile(db, 10))
    out, cover = out[:n], cover[:n]
    if floors:
        fl = float(np.median(floors))
        bed = _room_bed(n, fl - 3.0)                          # a touch under the lines' floor
        if bed is not None:
            # where the track dips well under the normal background (gaps between lines, and spots inside lines
            # where a fill or the cleanup left it too quiet), bring the room back in, with smooth edges
            hop = 480; m = n // hop
            db = 20 * np.log10(np.sqrt((out[: m * hop].reshape(m, hop) ** 2).mean(1)) + 1e-9)
            need = np.clip((fl - 4 - db) / 6, 0, 1)            # 0 at the normal floor, 1 when 10 dB under it
            need = np.maximum(need, 1.0 - cover[: m * hop: hop])   # gaps between lines: always
            k = 5
            need = np.convolve(np.pad(need, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), "valid")
            g = np.interp(np.arange(n), np.arange(m) * hop + hop / 2, need).astype(np.float32)
            out = out + bed * g
    return out


def _smooth(x: np.ndarray, sec: float) -> np.ndarray:
    k = max(1, int(sec * SR))
    c = np.cumsum(np.concatenate([[0], x]))
    y = (c[k:] - c[:-k]) / k
    return np.concatenate([y, np.full(k - 1, y[-1] if len(y) else 0)])


AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac")
ROOT = Path(__file__).resolve().parent.parent


def _bandlimit(a: np.ndarray) -> np.ndarray:
    import subprocess
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-i", "-",
                        "-af", "highpass=f=140,lowpass=f=12000", "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                       input=a.astype(np.float32).tobytes(), capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.float32).copy()


def music_bed(duration: float, mood: str, seed: int = 0) -> np.ndarray:
    """Music under the voice. `mood` is either a procedural mood ("curious", "tension") or a
    file / folder of tracks (e.g. "music/" with YouTube Audio Library downloads). Tracks are
    played in order, looped, and crossfaded (4 s) to fill the duration."""
    from .tts import read_wav
    tracks = []
    for item in (mood if isinstance(mood, list) else [mood]):
        p = Path(item) if item else None
        if p is not None and not p.is_absolute():
            p = ROOT / p
        if p is not None and p.is_dir():
            tracks += sorted(x for x in p.iterdir() if x.suffix.lower() in AUDIO_EXT)
        elif p is not None and p.is_file():
            tracks.append(p)
    if not tracks:
        return music.bed(duration, mood if isinstance(mood, str) and mood in music.PROGRESSIONS else "curious", seed)
    n, xf = int(duration * SR), int(4 * SR)
    out = np.zeros(0, np.float32)
    k = 0
    while len(out) < n:
        t = read_wav(tracks[k % len(tracks)])
        t = _bandlimit(t)                                          # keep bass mud out from under the voice
        t = t / (np.sqrt(np.mean(t ** 2)) + 1e-9) * 0.12          # equal loudness between tracks
        if len(out) >= xf and len(t) > xf:
            ramp = np.sqrt(np.linspace(0, 1, xf, dtype=np.float32))   # equal-power crossfade: no dip at the seams
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
