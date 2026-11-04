"""Pluggable text-to-speech with caching and word timings.

Engines:
  kokoro      local, free, natural (default). KOKORO_VOICE=am_michael|bm_george|...
  recorded    your own voice: VOICE_DIR/<line id>.wav|m4a|mp3 (missing lines -> kokoro)
  piper       local, free, more robotic. Voice auto-downloaded into .voices/
  elevenlabs  set ELEVENLABS_API_KEY (+ optional ELEVENLABS_VOICE_ID); returns
              character alignment, which we convert to exact word timings.
Select with env TTS_ENGINE=kokoro|recorded|piper|elevenlabs.

Word timings: ElevenLabs gives them exactly. For Piper we estimate from character
counts within each line (good to ~0.1 s for captions); install faster-whisper and
set TTS_ALIGN=whisper for acoustic alignment.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000


@dataclass
class Speech:
    audio: np.ndarray            # float32 mono @ SR
    words: list[tuple[str, float, float]]   # (word, start, end) seconds

    @property
    def duration(self) -> float:
        return len(self.audio) / SR


def read_wav(path: Path) -> np.ndarray:
    """Any audio file -> float32 mono @ SR (via ffmpeg)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le",
                          "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def write_wav(path: Path, audio: np.ndarray, sr: int = SR) -> None:
    a = np.clip(audio, -1, 1)
    if a.ndim == 1:
        a = a[:, None]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(a.shape[1]); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((a * 32767).astype("<i2").tobytes())


def trim_silence(a: np.ndarray, thr=0.01, keep=0.06) -> np.ndarray:
    idx = np.flatnonzero(np.abs(a) > thr)
    if not len(idx):
        return a
    k = int(keep * SR)
    return a[max(0, idx[0] - k): idx[-1] + k]


def estimate_words(text: str, dur: float) -> list[tuple[str, float, float]]:
    words = text.split()
    weights = np.array([len(w) + 1.5 for w in words], float)
    edges = np.concatenate([[0], np.cumsum(weights)]) / weights.sum() * dur
    return [(w, float(edges[i]), float(edges[i + 1])) for i, w in enumerate(words)]


class Piper:
    name = "piper"

    def __init__(self, voice=os.environ.get("PIPER_VOICE", "en_US-ryan-high"),
                 length_scale=float(os.environ.get("PIPER_LENGTH_SCALE", "1.15"))):
        self.voice, self.length_scale = voice, length_scale
        self.dir = ROOT / ".voices"
        self.model = self.dir / f"{voice}.onnx"

    def key(self) -> str:
        return f"piper:{self.voice}:{self.length_scale}"

    def ensure(self):
        if not self.model.exists():
            self.dir.mkdir(exist_ok=True)
            subprocess.run([sys.executable, "-m", "piper.download_voices", self.voice,
                            "--data-dir", str(self.dir)], check=True)

    def synth(self, text: str, out: Path) -> list | None:
        self.ensure()
        subprocess.run([sys.executable, "-m", "piper", "-m", str(self.model), "-f", str(out),
                        "--length-scale", str(self.length_scale)],
                       input=text.encode(), check=True, capture_output=True)
        return None


class Kokoro:
    """Open-source Kokoro-82M (ONNX). Much more natural than Piper; free, local."""
    name = "kokoro"

    def __init__(self, voice=os.environ.get("KOKORO_VOICE", "am_michael"),
                 speed=float(os.environ.get("KOKORO_SPEED", "0.95"))):
        self.voice, self.speed = voice, speed
        self.dir = ROOT / ".voices" / "kokoro"
        self._k = None

    def key(self) -> str:
        return f"kokoro:{self.voice}:{self.speed}"

    def ensure(self):
        base = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
        self.dir.mkdir(parents=True, exist_ok=True)
        for f in ("kokoro-v1.0.onnx", "voices-v1.0.bin"):
            if not (self.dir / f).exists():
                urllib.request.urlretrieve(base + f, self.dir / f)

    def synth(self, text: str, out: Path) -> None:
        if self._k is None:
            self.ensure()
            from kokoro_onnx import Kokoro as K
            self._k = K(str(self.dir / "kokoro-v1.0.onnx"), str(self.dir / "voices-v1.0.bin"))
        lang = "en-gb" if self.voice.startswith("b") else "en-us"
        audio, sr = self._k.create(text, voice=self.voice, speed=self.speed, lang=lang)
        write_wav(out, np.asarray(audio, np.float32), sr)
        return None


class Recorded:
    """Your own voice: one file per narration line, named <line id>.<wav|m4a|mp3>,
    in VOICE_DIR (e.g. episodes/<slug>/voice). Missing lines fall back to Kokoro."""
    name = "recorded"

    def __init__(self):
        self.dir = Path(os.environ.get("VOICE_DIR", "voice"))
        self.fallback = Kokoro()

    def find(self, line_id):
        for ext in ("wav", "m4a", "mp3", "flac", "ogg"):   # _roomtone/_report are helpers, never lines
            p = self.dir / f"{line_id}.{ext}"
            if p.exists():
                return p
        return None

    def key(self) -> str:
        return f"recorded:{self.dir.resolve()}"


class ElevenLabs:
    name = "elevenlabs"

    def __init__(self):
        self.api_key = os.environ["ELEVENLABS_API_KEY"]
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")
        self.model_id = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")

    def key(self) -> str:
        return f"11labs:{self.voice_id}:{self.model_id}"

    def synth(self, text: str, out: Path) -> list:
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/with-timestamps",
            data=json.dumps({"text": text, "model_id": self.model_id}).encode(),
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"})
        res = json.load(urllib.request.urlopen(req, timeout=120))
        mp3 = out.with_suffix(".mp3")
        mp3.write_bytes(base64.b64decode(res["audio_base64"]))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), str(out)], check=True)
        al = res["alignment"]
        words, cur, start = [], "", None
        for ch, s, e in zip(al["characters"], al["character_start_times_seconds"],
                            al["character_end_times_seconds"]):
            if ch.isspace():
                if cur:
                    words.append((cur, start, prev_e))
                cur, start = "", None
            else:
                start = s if start is None else start
                cur += ch
                prev_e = e
        if cur:
            words.append((cur, start, prev_e))
        return words


def engine():
    name = os.environ.get("TTS_ENGINE", "kokoro")
    return {"piper": Piper, "kokoro": Kokoro, "recorded": Recorded, "elevenlabs": ElevenLabs}[name]()


_ENGINE = None


def default_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = engine()
    return _ENGINE


def _whisper_words(path: Path, text: str):
    from faster_whisper import WhisperModel  # optional dependency
    m = WhisperModel("base.en", compute_type="int8")
    segs, _ = m.transcribe(str(path), word_timestamps=True, initial_prompt=text)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]


def speak(text: str, cache_dir: Path, eng=None, line_id: str | None = None) -> Speech:
    eng = eng or default_engine()
    cache_dir.mkdir(parents=True, exist_ok=True)
    if isinstance(eng, Recorded):
        src = eng.find(line_id) if line_id else None
        meta_only = eng.dir / f"{line_id}.json" if line_id else None
        if src is None and meta_only is not None and meta_only.exists():
            # timing-only mode (e.g. GitHub render without the audio): silent placeholder of the
            # recorded length + exact word timings; the real voice is mixed in where the wavs live
            m = json.loads(meta_only.read_text())
            return Speech(np.zeros(int(m["duration"] * SR), np.float32), [tuple(w) for w in m["words"]])
        if src is None:
            return speak(text, cache_dir, eng.fallback)
        meta = src.with_suffix(".json")             # written by pipeline/split_recording.py
        split = meta.exists()
        if os.environ.get("VOICE_CLEAN", "1") != "0":     # denoise + polish (+ trim) (pipeline/voice_clean.py)
            from .voice_clean import clean, load as load48
            rt = eng.dir / "_roomtone.wav"
            audio = clean(load48(src), load48(rt) if rt.exists() else None, do_trim=not split)
        else:
            audio = trim_silence(read_wav(src), thr=0.02, keep=0.08)
            audio = audio / (np.abs(audio).max() + 1e-9) * 0.9
        if split:
            words = [tuple(w) for w in json.loads(meta.read_text())["words"]]
        elif os.environ.get("TTS_ALIGN") == "whisper":
            words = _whisper_words(src, text)
        else:
            words = estimate_words(text, len(audio) / SR)
        return Speech(audio, words)
    h = hashlib.sha1((eng.key() + "|" + text).encode()).hexdigest()[:16]
    wav, meta = cache_dir / f"{h}.wav", cache_dir / f"{h}.json"
    if not (wav.exists() and meta.exists()):
        raw = cache_dir / f"{h}.raw.wav"
        words = eng.synth(text, raw)
        audio = read_wav(raw)
        lead = 0.0
        if words is None:                       # trim engine padding before estimating timings
            idx = np.flatnonzero(np.abs(audio) > 0.01)
            if len(idx):
                lead = max(0, idx[0] / SR - 0.06)
            audio = trim_silence(audio)
        write_wav(wav, audio)
        if words is None:
            if os.environ.get("TTS_ALIGN") == "whisper":
                words = _whisper_words(wav, text)
            else:
                words = estimate_words(text, len(audio) / SR)
        else:
            words = [(w, s - lead, e - lead) for w, s, e in words]
        meta.write_text(json.dumps({"text": text, "words": words}))
        raw.unlink(missing_ok=True)
    return Speech(read_wav(wav), [tuple(w) for w in json.loads(meta.read_text())["words"]])
