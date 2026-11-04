"""Automatic narration QA: find and fix what a listener would notice, without a human pass.

Runs after tighten_voice (it edits the tightened line wavs in place; re-run both, in that order, to rebuild).

For every line:
  1. Forced alignment (torchaudio MMS_FA, wav2vec2) of the script words -> exact start/end of every word
     (~20 ms). Whisper's word times are too loose: it stretched "The" over a burp.
  2. Every sound OUTSIDE the words is an event. Measured on the cleaned audio (what the listener hears):
       breath  (noisy, high-frequency, moderate level)          -> turned down 12 dB (kept: sounds natural)
       click / mouth smack (very short, sharp)                  -> replaced with room tone
       burp / cough / hum / anything else voiced                -> replaced with room tone
     Leading / trailing noises before the first / after the last word are always replaced.
  3. Words the aligner is unsure about (low score) are listed: mumbles, leftover restarts, ad-libs.
  4. Every stumble-cut join is checked: a join inside a word = chopped word (listed).
  5. Verification: the edited line is re-transcribed and must still contain every script word.
Report: voice/_qa.txt (times in line seconds and, with --timeline, video time). Edits: "qa_edits" in each json.

    python -m pipeline.audio_qa episodes/<slug> [--lines o4 g3] [--dry-run]
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
_FA = {}


def fa():
    if not _FA:
        import torch, torchaudio
        b = torchaudio.pipelines.MMS_FA
        _FA.update(torch=torch, ta=torchaudio, model=b.get_model(with_star=False).eval(),
                   tok=b.get_tokenizer(), align=b.get_aligner(), sr=b.sample_rate)
    return _FA


NUMWORDS = None


def words_for_alignment(text):
    out = []
    for w in text.split():
        n = re.sub(r"[^a-z']", "", w.lower().replace("-", " "))
        if n.strip("'"):
            out.append((w, n))
    return out


def align(audio48, text):
    """[(script word, start s, end s, score)] for the script words, via CTC forced alignment."""
    F = fa(); torch, ta = F["torch"], F["ta"]
    wav = torch.from_numpy(audio48).float()[None]
    wav = ta.functional.resample(wav, SR, F["sr"])
    words = words_for_alignment(text)
    if not words:
        return []
    with torch.inference_mode():
        em, _ = F["model"](wav)
        spans = F["align"](em[0], F["tok"]([n for _, n in words]))
    ratio = wav.size(1) / em.size(1) / F["sr"]
    out = []
    for (w, _), sp in zip(words, spans):
        s, e = sp[0].start * ratio, sp[-1].end * ratio
        score = float(np.exp(np.mean([np.log(max(x.score, 1e-6)) for x in sp])))
        out.append((w, round(s, 3), round(e, 3), round(score, 3)))
    return out


FILLERS = {"um", "umm", "uh", "uhh", "er", "erm", "hmm", "mm", "ah"}
_WH = {}


def heard(audio48):
    """Plain transcription (normalized words) for the before/after safety check."""
    if not _WH:
        from faster_whisper import WhisperModel
        _WH["m"] = WhisperModel("small.en", device="cpu", compute_type="int8")
    from scipy.signal import resample_poly
    a16 = resample_poly(audio48, 1, 3).astype(np.float32)
    segs, _ = _WH["m"].transcribe(a16, language="en", beam_size=5, vad_filter=False)
    text = " ".join(s.text for s in segs).replace("%", " percent")      # "25%" must still count "percent"
    return [re.sub(r"[^a-z0-9']", "", w.lower()) for w in text.split() if re.sub(r"[^a-z0-9']", "", w.lower())]


def words_inside(audio48, ev, script_text, pad=0.4):
    """Words Whisper (primed with this line's script) hears inside the event."""
    if not _WH:
        heard(np.zeros(SR, np.float32))
    from scipy.signal import resample_poly
    t0 = max(0.0, ev["start"] - pad)
    seg = audio48[int(t0 * SR): int((ev["end"] + pad) * SR)]
    a16 = resample_poly(seg, 1, 3).astype(np.float32)
    segs, _ = _WH["m"].transcribe(a16, language="en", beam_size=5, word_timestamps=True,
                                  initial_prompt=script_text, condition_on_previous_text=False)
    out = []
    for sg in segs:
        for w in sg.words:
            n = re.sub(r"[^a-z0-9%']", "", w.word.lower()).replace("%", "percent")
            if not n or n in FILLERS:
                continue
            mid = t0 + (w.start + w.end) / 2
            if ev["start"] + 0.02 <= mid <= ev["end"] - 0.02:
                out.append(n)
    return out


def lost_words(before, after):
    """Words heard before the edit that are gone after it (ignoring repeats the edit was meant to remove)."""
    import difflib
    sm = difflib.SequenceMatcher(None, before, after, autojunk=False)
    gone = []
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op in ("delete", "replace"):
            seg = before[a0:a1]
            gone += [w for w in seg if before.count(w) > after.count(w) and w not in after[max(0, b0 - 3):b1 + 3]]
    return gone


def frames(a, win=0.01):
    hop = int(SR * win); n = len(a) // hop
    fr = a[: n * hop].reshape(n, hop)
    return fr, 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)


def classify(seg):
    """breath | click | voiced (burp, cough, hum, laugh...)."""
    dur = len(seg) / SR
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg)))) ** 2 + 1e-18
    f = np.fft.rfftfreq(len(seg), 1 / SR)
    band = (f > 80) & (f < 8000)
    p = spec[band]; fb = f[band]
    flat = float(np.exp(np.mean(np.log(p))) / np.mean(p))
    cent = float((fb * p).sum() / p.sum())
    low = float(p[fb < 400].sum() / p.sum())
    peak = float(np.abs(seg).max() / (np.sqrt(np.mean(seg ** 2)) + 1e-9))
    if dur < 0.06 and peak > 4:
        kind = "click"
    elif flat > 0.08 and cent > 1200 and low < 0.25:
        kind = "breath"
    else:
        kind = "voiced"
    return kind, dict(dur=round(dur, 3), flat=round(flat, 3), cent=int(cent), low=round(low, 2))


def events(clean_audio, word_spans, pad=0.035):
    """Sounds outside the words: contiguous frames 10 dB+ above the line's noise floor, >= 40 ms."""
    _, db = frames(clean_audio)
    floor = np.percentile(db, 10)
    loud = db > floor + 10
    speech = np.zeros(len(db), bool)
    for _, s, e, _ in word_spans:
        speech[max(0, int((s - pad) / 0.01)): int((e + pad) / 0.01) + 1] = True
    cand = loud & ~speech
    out, i = [], 0
    while i < len(cand):
        if cand[i]:
            j = i
            while j < len(cand) and cand[j]:
                j += 1
            if (j - i) >= 4:
                s, e = i * 0.01, j * 0.01
                kind, feat = classify(clean_audio[int(s * SR): int(e * SR)])
                out.append(dict(start=round(s, 2), end=round(e, 2), kind=kind, peak_db=round(float(db[i:j].max() - floor), 1), **feat))
            i = j
        else:
            i += 1
    return out, float(floor)


def roomtone_fill(n, room, level_like=None):
    """The session's real room tone at its natural level (= what silence sounds like in that recording)."""
    if room is None or len(room) < n:
        return np.zeros(n, np.float32)
    k = np.random.default_rng(0).integers(0, len(room) - n + 1)
    return room[k:k + n].astype(np.float32).copy()


def plan(evs, words, dur):
    """Decide per event: cut | fill | duck | keep (report only). Conservative mid-line, strict at the edges."""
    first = words[0][1] if words else 0.0
    last = words[-1][2] if words else dur
    out = []
    for ev in evs:
        d = ev["end"] - ev["start"]
        edge = ev["end"] <= first + 0.02 or ev["start"] >= last - 0.02
        near = min([abs(ev["start"] - e) for _, s0, e, _ in words] + [abs(s0 - ev["end"]) for _, s0, e, _ in words] + [9])
        if near < 0.06 and not (ev["kind"] == "voiced" and d >= 0.3):
            act = "keep"                                   # touches a word: its onset or decaying tail, not noise
        elif edge:
            act = "fill"                                   # burp / breath / click before or after the line
        elif ev["kind"] == "voiced" and d >= 0.3:
            act = "cut"                                    # extra speech: leftover restart, ad-lib, cough
        elif ev["kind"] == "voiced" and d >= 0.12:
            act = "fill"                                   # burp, hum, cough fragment
        elif ev["kind"] == "breath" and d >= 0.08:
            act = "duck"
        elif ev["kind"] == "click" and ev["peak_db"] > 25:
            act = "fill"
        else:
            act = "keep"                                   # tiny blip at a word edge: usually part of the word
        out.append(dict(ev, action=act))
    return out


def widen(ev, db, floor, spans, max_ext=0.12, gap=0.02):
    """Grow an event outward while the sound is still above floor+4 dB (its soft onset and tail), but never into
    a neighbouring word. Returns (start, end) in seconds."""
    lo_lim = max([e for _, s0, e, _ in spans if e <= ev["start"] + 0.005] + [0.0]) + gap
    hi_lim = min([s0 for _, s0, e, _ in spans if s0 >= ev["end"] - 0.005] + [len(db) * 0.01]) - gap
    i, j = int(ev["start"] / 0.01), int(ev["end"] / 0.01)
    k = 0
    while i > 0 and (i - 1) * 0.01 >= lo_lim and db[i - 1] > floor + 4 and k < max_ext / 0.01:
        i -= 1; k += 1
    k = 0
    while j < len(db) and (j + 1) * 0.01 <= hi_lim and db[j] > floor + 4 and k < max_ext / 0.01:
        j += 1; k += 1
    return max(i * 0.01, 0.0), j * 0.01


def fix(raw, plan_, room, spans=None, clean_db=None):
    """Apply fill / duck to the raw line audio, then remove the 'cut' ranges. Returns audio, cut ranges."""
    a = raw.copy()
    _, db = frames(raw)
    quiet = 10 ** (np.percentile(db, 10) / 20)
    cuts = []
    if spans is not None and clean_db is not None:          # cover the soft edges of each noise too
        fl = np.percentile(clean_db, 10)
        plan_ = [dict(ev, start=widen(ev, clean_db, fl, spans)[0], end=widen(ev, clean_db, fl, spans)[1])
                 if ev["action"] in ("fill", "duck") else ev for ev in plan_]
    for ev in plan_:
        s, e = int(ev["start"] * SR), int(ev["end"] * SR)
        if e <= s:
            continue
        f = min(int(0.004 * SR), (e - s) // 4)
        ramp = np.zeros(e - s, np.float32)                  # how much ORIGINAL to keep: 1 at the edges, 0 inside
        if f > 0:
            ramp[:f] = np.linspace(1, 0, f); ramp[-f:] = np.linspace(0, 1, f)
        if ev["action"] == "duck":
            g = 10 ** (-12 / 20); a[s:e] = a[s:e] * (g + (1 - g) * ramp)
        elif ev["action"] == "fill":
            a[s:e] = a[s:e] * ramp + roomtone_fill(e - s, room, quiet) * (1 - ramp)
        elif ev["action"] == "cut":
            cuts.append((ev["start"] - 0.02, ev["end"] + 0.02))
    return a, cuts


def _selftest():
    rng = np.random.default_rng(1)
    raw = (rng.standard_normal(SR) * 0.01).astype(np.float32)
    raw[int(0.3 * SR):int(0.5 * SR)] += np.sin(np.arange(int(0.2 * SR)) * 2 * np.pi * 250 / SR).astype(np.float32) * 0.5
    room = (rng.standard_normal(SR * 2) * 0.01).astype(np.float32)
    out, _ = fix(raw, [dict(start=0.3, end=0.5, action="fill")], room)
    before = np.sqrt(np.mean(raw[int(0.32 * SR):int(0.48 * SR)] ** 2))
    after = np.sqrt(np.mean(out[int(0.32 * SR):int(0.48 * SR)] ** 2)); floor = np.sqrt(np.mean(room ** 2))
    assert after < floor * 1.5, f"fill is not at room-tone level ({after:.4f} vs room {floor:.4f})"
    out, _ = fix(raw, [dict(start=0.3, end=0.5, action="duck")], room)
    after = np.sqrt(np.mean(out[int(0.32 * SR):int(0.48 * SR)] ** 2))
    assert after < before / 3, "duck did not turn it down"


def trim_to_words(vd: Path, lid: str, lead=0.08, tail=0.15):
    """Trim a line to its first/last ALIGNED word (after noises were filled, the transcript-free edges)."""
    from .tighten_voice import apply_cuts
    wav, js = vd / f"{lid}.wav", vd / f"{lid}.json"
    meta = json.loads(js.read_text()); aw = meta.get("aligned_words")
    if not aw:
        return 0.0
    a, sr = sf.read(wav, dtype="float32"); dur = len(a) / sr
    _, db = frames(a); fl = np.percentile(db, 10)
    i = int(aw[-1][2] / 0.01)                        # CTC word ends are early: follow the sound until it has decayed
    while i < len(db) - 1 and (db[i] > fl + 6 or db[min(i + 5, len(db) - 1)] > fl + 6) and i * 0.01 < aw[-1][2] + 0.8:
        i += 1
    j = int(aw[0][1] / 0.01)
    while j > 0 and db[j - 1] > fl + 6 and j * 0.01 > aw[0][1] - 0.3:
        j -= 1
    s0 = max(0.0, j * 0.01 - lead); e1 = min(dur, i * 0.01 + tail)
    cuts = [c for c in ((0.0, s0), (e1, dur)) if c[1] - c[0] > 0.02]
    if not cuts:
        return 0.0
    a, words = apply_cuts(a, sr, [tuple(w) for w in meta["words"]], cuts)
    sf.write(wav, a, sr)
    meta.update(words=[list(w) for w in words], duration=round(len(a) / sr, 3),
                aligned_words=[[w, round(x - s0, 3), round(y - s0, 3), sc] for w, x, y, sc in aw])
    js.write_text(json.dumps(meta))
    return sum(c[1] - c[0] for c in cuts)


def final_check(ep: Path):
    """After all edits: no line may end (or start) mid-sound, and no extra speech >= 0.3 s may remain outside the
    aligned script words (= leftover repeat). Prints problems; exit code 1 if any."""
    from .voice_clean import clean, load
    vd = ep / "voice"
    script = {m.group(1): m.group(2) for m in re.finditer(r"^\[(\w+)\] (.*)$", (ep / "script.md").read_text(), re.M)}
    room = load(vd / "_roomtone.wav") if (vd / "_roomtone.wav").exists() else None
    bad = []
    for lid, text in script.items():
        if not (vd / f"{lid}.wav").exists():
            continue
        cl = clean(load(vd / f"{lid}.wav"), room, do_trim=False)
        _, db = frames(cl); fl = np.percentile(db, 10)
        if db[-3:].max() > fl + 15:
            bad.append(f"{lid}: ends abruptly (last 30 ms at +{db[-3:].max() - fl:.0f} dB)")
        if db[:3].max() > fl + 15:
            bad.append(f"{lid}: starts abruptly")
        spans = align(cl, text)
        evs, _ = events(cl, spans)
        for ev in evs:
            if ev["kind"] == "voiced" and ev["end"] - ev["start"] >= 0.3:
                hw = words_inside(cl, ev, text)
                if hw:
                    bad.append(f"{lid}: extra speech {ev['start']}-{ev['end']}s '{' '.join(hw)}'")
    (vd / "_final_check.txt").write_text("\n".join(bad) + "\n")
    print("\n".join(bad) or "final check: clean")
    raise SystemExit(1 if bad else 0)


def main():
    import sys
    if "--final-check" in sys.argv:
        final_check(Path(sys.argv[1])); return
    if "--trim-only" in sys.argv:
        ep = Path(sys.argv[1]); vd = ep / "voice"
        ids = re.findall(r"^\[(\w+)\] ", (ep / "script.md").read_text(), re.M)
        total = sum(trim_to_words(vd, lid) for lid in ids)
        print(f"trimmed {total:.1f}s of dead air at line edges")
        return
    _selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--lines", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--min-score", type=float, default=0.25)
    a = ap.parse_args()
    from .voice_clean import clean, load
    from .match_voice import roomtone_path, session_of
    ep = Path(a.episode); vd = ep / "voice"
    script = {m.group(1): m.group(2) for m in re.finditer(r"^\[(\w+)\] (.*)$", (ep / "script.md").read_text(), re.M)}
    report = []
    rooms = {}
    for lid in (a.lines or list(script)):
        wav, js = vd / f"{lid}.wav", vd / f"{lid}.json"
        if not wav.exists() or not js.exists():
            continue
        meta = json.loads(js.read_text())
        sess = session_of(meta)
        if sess not in rooms:
            rp = roomtone_path(vd, sess)
            rooms[sess] = load(rp) if rp.exists() else None
        raw = load(wav)
        cl = clean(raw, rooms[sess], do_trim=False)
        spans = align(cl, script[lid])
        evs, floor = events(cl, spans)
        weak = [(w, s, sc) for w, s, e, sc in spans if sc < a.min_score]
        chopped = [t for t in meta.get("stumble_cuts", []) if any(s + 0.03 < t < e - 0.03 for _, s, e, _ in spans)]
        lines = []
        for ev in evs:
            lines.append(f"  {ev['start']:6.2f}-{ev['end']:5.2f}s  {ev['kind']:7s} +{ev['peak_db']:4.1f} dB  "
                         f"(flat {ev['flat']}, {ev['cent']} Hz, low {ev['low']})")
        for w, s, sc in weak:
            lines.append(f"  {s:6.2f}s  unsure word '{w}' (score {sc}) -> listen: mumble / leftover restart?")
        for t in chopped:
            lines.append(f"  {t:6.2f}s  cut join lands INSIDE a word -> chopped word?")
        if lines:
            report.append(f"[{lid}]\n" + "\n".join(lines))
        pl = plan(evs, spans, len(raw) / SR)
        sw_norm = [re.sub(r"[^a-z0-9']", "", w.lower()) for w in script[lid].split()]
        for ev in pl:                                    # never blank or cut a real word; DO cut repeats
            if ev["action"] in ("fill", "cut"):
                hw = words_inside(cl, ev, script[lid])
                if not hw:
                    continue
                repeat = (len(hw) >= 2 and ev["end"] - ev["start"] >= 0.3
                          and all(w in sw_norm for w in hw))   # same words are already aligned in the line
                if repeat:
                    ev["action"] = "cut"; ev["repeat"] = " ".join(hw)
                    report.append(f"[{lid}] cut repeat {ev['start']}-{ev['end']}s: '{' '.join(hw)}'")
                else:
                    ev["action"] = "keep"; ev["protected_word"] = " ".join(hw)
                    report.append(f"[{lid}] kept {ev['start']}-{ev['end']}s: it is a word ('{' '.join(hw)}')")
        lines = [ln + "  -> " + ev["action"] for ln, ev in zip(lines, pl)] + lines[len(pl):]
        if lines:
            report[-1] = f"[{lid}]\n" + "\n".join(lines) if report and report[-1].startswith(f"[{lid}]") else report[-1]
        if not a.dry_run and any(ev["action"] != "keep" for ev in pl):
            from .tighten_voice import apply_cuts
            fixed, cuts = fix(raw, pl, rooms[sess], spans, frames(cl)[1])
            words = [tuple(w) for w in meta["words"]]
            fixed, words = apply_cuts(fixed, SR, words, cuts)
            hb, ha = heard(cl), heard(clean(fixed, rooms[sess], do_trim=False))
            sw = [re.sub(r"[^a-z0-9']", "", w.lower()) for w in script[lid].split()]
            gone = [w for w in lost_words(hb, ha) if w not in FILLERS]   # ANY spoken word, script or not
            if gone:                                     # some edit removed real words: keep only the safe ones
                safe = []
                for ev in [e for e in pl if e["action"] != "keep"]:
                    trial = [dict(e, action=e["action"] if (e in safe or e is ev) else "keep") for e in pl]
                    f2, c2 = fix(raw, trial, rooms[sess], spans, frames(cl)[1])
                    f2, _ = apply_cuts(f2, SR, [tuple(w) for w in meta["words"]], c2)
                    h2 = heard(clean(f2, rooms[sess], do_trim=False))
                    if not [w for w in lost_words(hb, h2) if w not in FILLERS]:
                        safe.append(ev)
                    else:
                        report.append(f"[{lid}] skipped {ev['action']} {ev['start']}-{ev['end']}s: it removed words")
                pl = [dict(e, action=e["action"] if e in safe else "keep") for e in pl]
                fixed, cuts = fix(raw, pl, rooms[sess], spans, frames(cl)[1])
                words = [tuple(w) for w in meta["words"]]
                fixed, words = apply_cuts(fixed, SR, words, cuts)
                print(lid, f"kept {len(safe)} safe edits", flush=True)
            # proof: every filled spot must now sit near the noise floor (measured on what the listener hears)
            chk = clean(fixed, rooms[sess], do_trim=False); _, dbc = frames(chk); fl = np.percentile(dbc, 10)
            shift = 0.0
            for ev in sorted(pl, key=lambda e: e["start"]):
                if ev["action"] == "cut":
                    shift += ev["end"] - ev["start"] + 0.04
                elif ev["action"] == "fill":
                    i0, i1 = int((ev["start"] - shift) / 0.01) + 2, int((ev["end"] - shift) / 0.01) - 2   # interior only
                    if i1 > i0 and dbc[i0:i1].max() > fl + 8:
                        report.append(f"[{lid}] STILL AUDIBLE after fill at {ev['start']}-{ev['end']}s (+{dbc[i0:i1].max()-fl:.0f} dB)")
            sf.write(wav, fixed, SR)
            meta.update(words=[list(w) for w in words], duration=round(len(fixed) / SR, 3))
            meta["qa_edits"] = [ev for ev in pl if ev["action"] != "keep"]
            if cuts:                                     # re-align after removing time
                spans = align(clean(fixed, rooms[sess], do_trim=False), script[lid])
        meta["aligned_words"] = [list(x) for x in spans]
        if not a.dry_run:
            js.write_text(json.dumps(meta))
            trim_to_words(vd, lid)
        print(lid, f"{len(evs)} events", f"{len(weak)} unsure words", f"{len(chopped)} chopped joins", flush=True)
    (vd / "_qa.txt").write_text("\n\n".join(report) + "\n")
    print(f"report -> {vd / '_qa.txt'}")


if __name__ == "__main__":
    main()
