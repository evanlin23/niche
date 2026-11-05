"""Two guards on the voice chain's inputs (both found on a real recording):

1. Headroom. A float recording (e.g. an m4a from a phone/DAW) can store peaks ABOVE full scale. Every later step
   writes 16-bit WAV (tts.write_wav clips at +-1.0), so those peaks were flattened. `prepare_inputs` measures each
   recording's true peak up front and, if it is above 0 dBFS, writes a gain-reduced float copy (peak at
   HEADROOM_DBFS) in voice/_input/ that the whole chain uses instead. Logged in voice/_input_check.json and the
   voice report.

2. Stale backups. tighten_voice / extend_tails work from voice/_orig/ (the untightened split). Those backups used
   to be made once and reused forever, so a NEW recording got processed against the OLD backups. Now every split
   line carries `source` (fingerprint of the recording it was cut from) and `sync_orig` compares it with the
   backup's: missing -> back up, different -> refresh (and say so), equal -> reuse; current line not fingerprinted
   (split before this guard) -> refuse (pass allow_legacy=True / --legacy-orig to reuse old, unfingerprinted backups on purpose).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

HEADROOM_DBFS = -4.5          # where an over-full-scale recording's peak is put (the Uno session's setting)


def fingerprint(path) -> str:
    """sha256 of the file's bytes (first 16 hex chars) + size: the identity of a recording."""
    p = Path(path); h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return f"{h.hexdigest()[:16]}:{p.stat().st_size}"


def decode_peak(path) -> float:
    """Peak |sample| of the decoded recording, all channels, as float (values > 1.0 are kept)."""
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    return float(np.abs(a).max()) if len(a) else 0.0


def headroom_gain_db(peak: float, target_dbfs: float = HEADROOM_DBFS) -> float:
    """Gain to apply: 0 when the recording is within full scale, else what puts its peak at target_dbfs."""
    if peak <= 1.0:
        return 0.0
    return round(target_dbfs - 20 * np.log10(peak), 2)


def prepare_inputs(voice_dir: Path, recs: list[str]) -> tuple[list[str], list[dict]]:
    """Recordings for the chain: over-full-scale ones replaced by a gain-reduced float WAV in voice/_input/."""
    voice_dir = Path(voice_dir); out, log = [], []
    for r in recs:
        pk = decode_peak(r)
        g = headroom_gain_db(pk)
        e = {"recording": Path(r).name, "peak_dbfs": round(20 * np.log10(pk + 1e-12), 2), "gain_db": g}
        if g:
            d = voice_dir / "_input"; d.mkdir(parents=True, exist_ok=True)
            dst = d / f"{Path(r).stem}.headroom.wav"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(r), "-af", f"volume={g}dB",
                            "-c:a", "pcm_f32le", str(dst)], check=True)
            e.update(used=str(dst), peak_after_dbfs=round(20 * np.log10(decode_peak(dst) + 1e-12), 2))
            print(f"[headroom] {Path(r).name}: peak {e['peak_dbfs']:+.2f} dBFS is ABOVE full scale -> "
                  f"{g:+.2f} dB before splitting (peak now {e['peak_after_dbfs']:+.2f} dBFS), using {dst}")
            out.append(str(dst))
        else:
            e["used"] = str(r); out.append(str(r))
        log.append(e)
    voice_dir.mkdir(parents=True, exist_ok=True)
    (voice_dir / "_input_check.json").write_text(json.dumps(log, indent=1))
    return out, log


class StaleBackup(RuntimeError):
    pass


def sync_orig(voice_dir: Path, lines=None, allow_legacy=False) -> dict:
    """Make voice/_orig/ match the current split. Returns {line id: 'backed-up' | 'refreshed' | 'reused'}."""
    d = Path(voice_dir); orig = d / "_orig"; orig.mkdir(exist_ok=True)
    out, legacy = {}, []
    for js in sorted(d.glob("*.json")):
        lid = js.stem
        if lid.startswith("_") or (lines and lid not in lines) or not js.with_suffix(".wav").exists():
            continue
        oj = orig / js.name
        cur = json.loads(js.read_text()).get("source")
        if not oj.exists() or not (orig / f"{lid}.wav").exists():
            act = "backed-up"
        else:
            old = json.loads(oj.read_text()).get("source")
            if cur is None:                          # current line not fingerprinted: can't tell
                if not allow_legacy:
                    legacy.append(lid); continue
                act = "reused"
            elif cur is not None and cur == old:
                act = "reused"
            else:
                act = "refreshed"
        if act != "reused":
            for p in (js.with_suffix(".wav"), js):
                shutil.copy2(p, orig / p.name)
            if act == "refreshed":
                print(f"[orig] {lid}: backup was cut from a different recording ({old} vs {cur}) -> refreshed")
        out[lid] = act
    if legacy:
        raise StaleBackup(
            f"voice/_orig/ backups for {len(legacy)} lines ({', '.join(legacy[:6])}{'...' if len(legacy) > 6 else ''}) "
            "carry no recording fingerprint, so they can't be matched to the current split. Re-split "
            "(make voice SLUG=... REC=...) or, if these backups ARE from the current recording, pass --legacy-orig.")
    return out
