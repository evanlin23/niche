"""Voice gate: the whole voice chain in one command, then a final check that fails loudly.

    make voice SLUG=<slug> REC=path/to/recording.m4a          (several recordings: REC="a.m4a b.m4a")
    python -m pipeline.voice_gate episodes/<slug> rec.m4a [--from-step N] [--check-only]

Steps (each must succeed before the next runs; a failing step stops the chain with its output):
  1 split_recording   per-line clips + timing          5 audio_qa          noises filled, edges trimmed
  2 extend_tails      chopped word endings restored     6 match_voice       same tone/level across sessions
  3 find_stumbles     restarts/repeats -> cut ranges    7 final check       below
  4 tighten_voice     cuts + pauses capped at 0.35 s

Final check (per line + the narration as it will be heard):
  transcript   Whisper hears the line; every script word must be there and nothing extra (number words normalised)
  endings      no line starts/ends mid-sound (abrupt word endings)        (audio_qa.final_check)
  extra        no leftover speech outside the script words >= 0.3 s     (audio_qa.final_check)
  silence      no >= 10 ms of digital silence (dropouts), in lines or in the narration track
  clipping     no sample >= -0.3 dBFS, no run of 3+ samples at full scale
  gaps         no pause > 0.6 s inside a line (tighten caps them at 0.35 s), no gap > 1.5 s between lines
Writes voice/_report_voice.txt (readable, git-ignored: it holds transcripts) and voice/_listen.mp3 (the full
narration on the video timeline, for the creator) and exits 1 if anything failed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 48000


def run_step(n, name, cmd):
    print(f"\n=== step {n}: {name} ===\n$ {' '.join(cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"\nVOICE GATE: step {n} ({name}) FAILED (exit {r.returncode}). Fix it and re-run with --from-step {n}.")
        raise SystemExit(r.returncode or 1)


def chain(ep: Path, recs: list[str], start=1):
    py = sys.executable
    vd = ep / "voice"
    steps = [
        ("split_recording", [py, "-m", "pipeline.split_recording", str(ep), *recs[:1]]),
        ("extend_tails", [py, "-m", "pipeline.extend_tails", str(ep), *recs]),
        ("find_stumbles", [py, "-m", "pipeline.find_stumbles", str(ep)]),
        ("tighten_voice", [py, "-m", "pipeline.tighten_voice", str(vd), "--cuts", str(vd / "_stumbles.json")]
         + (["--words", str(vd / "_verbatim.json")] if (vd / "_verbatim.json").exists() else [])),
        ("audio_qa", [py, "-m", "pipeline.audio_qa", str(ep)]),
        ("match_voice", [py, "-m", "pipeline.match_voice", str(vd)]),
    ]
    for i, (name, cmd) in enumerate(steps, 1):
        if i >= start:
            run_step(i, name, cmd)


# ------------------------------------------------------------------ measurements (pure functions, unit-tested)
def digital_silence_ms(a: np.ndarray, sr=SR) -> float:
    z = np.abs(a) < 1e-7
    if not z.any():
        return 0.0
    d = np.diff(np.r_[0, z.astype(np.int8), 0])
    starts, ends = np.flatnonzero(d == 1), np.flatnonzero(d == -1)
    return float((ends - starts).max() / sr * 1000)


def clipping(a: np.ndarray) -> tuple[float, int]:
    """(peak dBFS, longest run of samples at >= 0.999 full scale)"""
    pk = float(20 * np.log10(np.abs(a).max() + 1e-12))
    hot = np.abs(a) >= 0.999
    if not hot.any():
        return pk, 0
    d = np.diff(np.r_[0, hot.astype(np.int8), 0])
    return pk, int((np.flatnonzero(d == -1) - np.flatnonzero(d == 1)).max())


def internal_gaps(words, min_gap=0.6):
    """Pauses longer than min_gap between consecutive (aligned) words: [(after_word, start, length)]"""
    out = []
    for (w0, _, e0, *_), (w1, s1, *_) in zip(words, words[1:]):
        if s1 - e0 > min_gap:
            out.append((w0, round(e0, 2), round(s1 - e0, 2)))
    return out


def word_diff(script: str, heard: list[str]):
    """(missing script words, extra heard words), numbers spelled out on both sides."""
    import difflib
    from .split_recording import norm, spoken
    exp = [x for t in script.split() for x in spoken(t) if norm(x)]
    exp = [norm(x) for x in exp]
    got = [norm(x) for h in heard for x in spoken(h) if norm(x)]
    fill = {"um", "uh", "erm", "hmm", "mm"}
    got = [g for g in got if g not in fill]
    sm = difflib.SequenceMatcher(None, exp, got, autojunk=False)
    miss, extra = [], []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op in ("delete", "replace"):
            miss += exp[a0:a1]
        if op in ("insert", "replace"):
            extra += got[b0:b1]
    return miss, extra


# ------------------------------------------------------------------ the final check
def final_check(ep: Path, transcript=True):
    from .timeline import parse_script
    vd = ep / "voice"
    vd.mkdir(exist_ok=True)
    script = parse_script(ep / "script.md")
    report, fails = [], 0
    model = None
    if transcript:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(os.environ.get("VOICE_GATE_MODEL", "small.en"), device="cpu", compute_type="int8")
        except ImportError:
            report.append("SKIPPED transcript check: faster-whisper is not installed (pip install faster-whisper)")
            fails += 1
    # 1) audio_qa's own end/start + extra-speech + digital-silence checks
    r = subprocess.run([sys.executable, "-m", "pipeline.audio_qa", str(ep), "--final-check"], cwd=ROOT,
                       capture_output=True, text=True)
    fc = [l for l in r.stdout.splitlines() if l.strip() and "final check: clean" not in l]
    if fc:
        fails += len(fc)
        report.append("audio_qa final check:\n" + "\n".join("  FAIL " + l for l in fc))
    if r.returncode not in (0, 1):
        fails += 1; report.append("audio_qa --final-check crashed:\n" + r.stderr[-2000:])
    # 2) per line
    import soundfile as sf
    for lid, text in script.items():
        wav, js = vd / f"{lid}.wav", vd / f"{lid}.json"
        if not wav.exists():
            fails += 1; report.append(f"[{lid}] FAIL missing: no {wav.name} (not recorded / not split)")
            continue
        a, sr = sf.read(wav, dtype="float32")
        a = a if a.ndim == 1 else a.mean(1)
        meta = json.loads(js.read_text()) if js.exists() else {}
        probs = []
        ms = digital_silence_ms(a, sr)
        if ms >= 10:
            probs.append(f"digital silence {ms:.0f} ms (dropout)")
        pk, run = clipping(a)
        if pk >= -0.3 or run >= 3:
            probs.append(f"clipping: peak {pk:.2f} dBFS, {run} samples at full scale")
        words = meta.get("aligned_words") or meta.get("words") or []
        for w, s0, ln in internal_gaps(words):
            probs.append(f"pause {ln:.2f}s after '{w}' at {s0:.2f}s")
        if model is not None:
            from .split_recording import norm
            a16 = a[::3] if sr == 48000 else a
            segs, _ = model.transcribe(a16, language="en", beam_size=5, initial_prompt=None, vad_filter=False)
            heard = " ".join(s.text for s in segs).replace("%", " percent").split()
            miss, extra = word_diff(text, heard)
            if miss or extra:
                probs.append("transcript differs from script: "
                             + (f"missing [{' '.join(miss)}] " if miss else "") + (f"extra [{' '.join(extra)}]" if extra else "")
                             + "  -> listen; if the take is right, update script.md to what was said")
        if probs:
            fails += len(probs)
            report.append(f"[{lid}]\n" + "\n".join("  FAIL " + p for p in probs))
    # 3) the narration as it will be heard: lines on the video timeline with the room-tone bed
    listen = vd / "_listen.mp3"
    try:
        os.environ.setdefault("TTS_ENGINE", "recorded"); os.environ.setdefault("VOICE_DIR", str(vd))
        from .compose import narration_track
        from .timeline import build, load_yaml
        from .tts import write_wav
        scenes = build(load_yaml(ep / "scenes.yaml")["scenes"], dict(script), ROOT / ".cache" / "tts")
        total = sum(s.duration for s in scenes)
        nar = narration_track(scenes, total)
        idx = np.flatnonzero(np.abs(nar) > 1e-4)
        body = nar[idx[0]: idx[-1]] if len(idx) else nar
        ms = digital_silence_ms(body)
        if ms >= 10:
            fails += 1; report.append(f"[narration] FAIL digital silence {ms:.0f} ms inside the narration track")
        gaps = []
        for sc in scenes:
            ends = sorted((sc.start + c.start, sc.start + c.end, c.id) for c in sc.cues.values())
            gaps += [(b[0] - a[1], a[2], b[2]) for a, b in zip(ends, ends[1:])]
        for g, l0, l1 in gaps:
            if g > 1.5:
                fails += 1; report.append(f"[narration] FAIL {g:.1f}s gap between {l0} and {l1}")
        tmp = vd / "_listen.wav"
        write_wav(tmp, nar / max(1.0, np.abs(nar).max()))
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(tmp), "-b:a", "160k", str(listen)], check=True)
        tmp.unlink()
        report.append(f"listen file: {listen}  ({total / 60:.1f} min, the narration exactly as timed in the video)")
    except Exception as e:                                   # never hide a failure here
        fails += 1; report.append(f"[narration] FAIL could not build the listen file: {e}")
    # cut list for the creator (what was removed and where)
    cuts = []
    st = vd / "_stumbles.json"
    if st.exists():
        for lid, rs in json.loads(st.read_text()).items():
            for s0, e0 in rs:
                cuts.append(f"  {lid}: cut {s0:.2f}-{e0:.2f}s (restart/repeat)")
    for js in sorted(vd.glob("*.json")):
        if js.name.startswith("_"):
            continue
        for ev in json.loads(js.read_text()).get("qa_edits", []):
            cuts.append(f"  {js.stem}: {ev['action']} {ev['start']}-{ev['end']}s ({ev.get('kind', 'noise')})")
    head = [f"VOICE GATE: {ep.name}", f"RESULT: {'FAIL' if fails else 'PASS'}  ({fails} problems in {len(script)} lines)", ""]
    text = "\n".join(head + report + (["", "Edits made (send this list with the listen file):"] + cuts if cuts else [])) + "\n"
    (vd / "_report_voice.txt").write_text(text)
    print(text)
    print(f"report: {vd / '_report_voice.txt'}")
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("episode"); ap.add_argument("recordings", nargs="*")
    ap.add_argument("--from-step", type=int, default=1)
    ap.add_argument("--check-only", action="store_true", help="skip the chain, run the final check")
    ap.add_argument("--no-transcript", action="store_true")
    a = ap.parse_args(argv)
    ep = Path(a.episode).resolve()
    if not a.check_only:
        if not a.recordings and a.from_step <= 2:
            ap.error("give the recording(s): make voice SLUG=... REC=path.m4a")
        chain(ep, a.recordings, a.from_step)
    print("\n=== step 7: final check ===", flush=True)
    raise SystemExit(1 if final_check(ep, not a.no_transcript) else 0)


if __name__ == "__main__":
    main()
