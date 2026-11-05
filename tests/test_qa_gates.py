"""Each QA check must FIRE on a known-bad case and stay quiet on a good one (a gate that always passes is useless).
    python -m pytest tests/test_qa_gates.py   (or: python -m tests.test_qa_gates)"""
from types import SimpleNamespace

from pipeline.numbers import agrees, spoken_numbers
from pipeline.qa_visual import check_scene

W, H = 1920, 1080


def spec(dur=6.0, cues=None, **kw):
    return {"W": W, "H": H, "duration": dur, "fps": 30, "n_frames": int(dur * 30), "cues": cues or {"a1": [0.2, 5.8]},
            "captions": [], "qa": {"anchors": kw.pop("anchors", [])}, "_tweens": kw.pop("tweens", []), **kw}


def text(i, r, op=1.0, txt="label", role="", anchor=""):
    return {"id": i, "text": txt, "op": op, "r": r, "role": role, "anchor": anchor}


def piece(i, p=(0, 0, 0), r=(700, 400, 760, 460)):
    return {"id": i, "kind": "decor", "name": "card", "op": 1, "p": list(p), "s": [1], "r": list(r)}


def states(fn, dur=6.0, auto=True, step=3):
    """auto: a new piece appears every second (object coverage) unless the case brings its own objects"""
    out = []
    for f in list(range(0, int(dur * 30), step)) + [int(dur * 30) - 2, int(dur * 30) - 1]:
        t = f / 30
        texts, objs, tw = fn(t)
        if auto and not objs:
            objs = [piece(500 + k, (k, 0, 0), (700 + k * 70, 400, 760 + k * 70, 460)) for k in range(int(t) + 1) if k < 6]
        out.append({"t": t, "texts": texts, "objs": objs, "tw": tw, "f": f})
    return out


SC = SimpleNamespace(id="s", render="bars")
OK_TEXT = [400, 400, 600, 450]


def checks(issues, sev="error"):
    return sorted({i["check"] for i in issues if i["sev"] == sev})


def busy(t):     # a new label every second: good coverage
    return [text(100 + k, [200, 200 + k * 50, 300, 240 + k * 50]) for k in range(int(t) + 1) if k < 6]


def test_clean_scene_passes():
    iss, _ = check_scene(SC, spec(), states(lambda t: (busy(t), [], [])), {"a1": "x"}, {})
    assert checks(iss) == [], iss


def test_unsafe_label():
    iss, _ = check_scene(SC, spec(), states(lambda t: (busy(t) + [text(1, [10, 10, 300, 60])], [], [])), {}, {})
    assert "safe" in checks(iss)


def test_overlap():
    iss, _ = check_scene(SC, spec(), states(lambda t: (busy(t) + [text(1, OK_TEXT), text(2, [450, 410, 650, 460])], [], [])), {}, {})
    assert "overlap" in checks(iss)


def test_half_faded_and_tween_at_cut():
    def f(t):
        return busy(t) + [text(1, OK_TEXT, op=min(1, max(0.0, (t - 5.5) / 0.6)))], [], ["bar grows"] if t > 5.9 else []
    iss, _ = check_scene(SC, spec(), states(f), {}, {})
    msgs = " ".join(i["msg"] for i in iss if i["check"] == "cut")
    assert "half-faded" in msgs and "cut off" in msgs


def test_object_moving_at_cut():
    def f(t):
        return busy(t), [{"id": 7, "kind": "key", "name": "card", "op": 1, "p": [t, 0, 0], "s": [1], "r": [500, 500, 600, 600]}], []
    assert "cut" in checks(check_scene(SC, spec(), states(f), {}, {})[0])


def test_coverage_gap():
    iss, _ = check_scene(SC, spec(dur=9.0, cues={"a1": [0.2, 8.8]}), states(lambda t: ([text(1, OK_TEXT)], [], []), 9.0, auto=False), {"a1": "x"}, {})
    assert "coverage" in checks(iss)


def test_coverage_ignores_captions_and_callouts():
    """only text popping up while narrating (the creator: 'the only thing that moves is a caption') fails coverage"""
    sp = spec(dur=9.0, cues={"a1": [0.2, 8.8]})
    texty = lambda t: ([text(100 + k, [200, 200 + k * 50, 300, 240 + k * 50], role="callout") for k in range(int(t) + 1)], [], [])
    assert "coverage" in checks(check_scene(SC, sp, states(texty, 9.0, auto=False), {"a1": "x"}, {})[0])
    assert "coverage" not in checks(check_scene(SC, sp, states(texty, 9.0), {"a1": "x"}, {})[0])


def _dense(fn, dur=4.0):
    return states(lambda t: ([], fn(t), []), dur, auto=False, step=1)


def test_sync_late_and_on_time():
    from pipeline.qa_visual import check_sync
    from pipeline.web_ease import smooth
    anc = [{"ref": "a1@go", "t": 1.5, "path": "params.play[0].at"}]
    move = lambda t0: (lambda t: [piece(1, (3 * smooth((t - t0) / 0.6), 0, 0))])
    late, _ = check_sync(spec(dur=4.0, anchors=anc), _dense(move(1.75)))
    ok, offs = check_sync(spec(dur=4.0, anchors=anc), _dense(move(1.45)))
    assert [i["check"] for i in late] == ["sync"] and ok == [], (late, ok)
    assert abs(offs[0]["offset"]) < 0.15
    two = [dict(anc[0]), dict(anc[0], path="params.play[1].at")]          # two cards on one word: both must move
    one_moves, _ = check_sync(spec(dur=4.0, anchors=two), _dense(move(1.45)))
    assert "only 1 objects" in one_moves[0]["msg"]


def test_smooth_teleport_and_eased():
    from pipeline.qa_visual import check_smooth
    from pipeline.web_ease import smooth
    eased = _dense(lambda t: [piece(1, (3 * smooth((t - 1) / 0.6), 0, 0))])
    jump = _dense(lambda t: [piece(1, (3 * smooth((t - 1) / 0.6) + (1.0 if t > 2.5 else 0), 0, 0))])
    linear = _dense(lambda t: [piece(1, (3 * min(1, max(0, (t - 1) / 0.6)), 0, 0))])   # instant start and stop
    assert check_smooth(eased) == []
    assert check_smooth(jump) and check_smooth(linear)


def test_continuity_jump_vs_continuous_vs_new_shot():
    import math
    from pipeline.qa_visual import check_continuity
    def cam(yaw, d=20.0, elev=40):
        e, y = math.radians(elev), math.radians(yaw)
        dvec = [-math.cos(e) * math.sin(y), -math.sin(e), -math.cos(e) * math.cos(y)]
        return {"t": 0, "f": 0, "texts": [], "objs": [], "cam": {"p": [-v * d for v in dvec], "d": dvec, "fov": 30}}
    A, B = SimpleNamespace(id="a"), SimpleNamespace(id="b")
    sp = [(A, {"type": "table"}), (B, {"type": "table"})]
    run = lambda ya, yb: check_continuity(sp, {"a": [cam(ya)], "b": [cam(yb)]})[0]
    assert [i["check"] for i in run(5, -5)] == ["continuity"]      # +5 -> -5 deg orbit restart: a jump
    assert run(5, 5) == [] and run(5, 40) == []                    # continuous shot / clearly different shot
    sp2 = [(A, {"type": "table"}), (B, {"type": "bars"})]
    assert check_continuity(sp2, {"a": [cam(5)], "b": [cam(-5)]})[0] == []   # different template: any cut is fine


def test_number_mismatch_and_match():
    bad = lambda t: (busy(t) + ([text(1, OK_TEXT, txt="31.0%", anchor="a1@thirty")] if t > 1 else []), [], [])
    good = lambda t: (busy(t) + ([text(1, OK_TEXT, txt="35.4%", anchor="a1@thirty")] if t > 1 else []), [], [])
    script = {"a1": "The best won thirty five percent."}
    assert "numbers" in checks(check_scene(SC, spec(), states(bad), script, {})[0])
    assert "numbers" not in checks(check_scene(SC, spec(), states(good), script, {})[0])


def test_burned_captions():
    sp = spec(captions=[[0, 1, "hi"]])
    assert "captions" in checks(check_scene(SC, sp, states(lambda t: (busy(t), [], [])), {}, {"burn_captions": False})[0])


def test_spoken_numbers():
    assert spoken_numbers("eleven and a half") == [11.5]
    assert spoken_numbers("thirteen point oh four percent") == [13.04]
    assert spoken_numbers("more than ten billion times") == [1e10]
    assert spoken_numbers("a billion games") == [1e9]
    assert spoken_numbers("Two more, third.") == [2.0, 3.0]
    assert agrees(35.4, [35]) and not agrees(31.0, [35]) and agrees(10.2e9, [1e10])
    # punctuation ends a number; unit words don't chain; "a hundred and ..." (Uno episode)
    assert spoken_numbers("With the free plus four, thirty one.") == [4.0, 31.0]
    assert spoken_numbers("wins about twenty three. Four points") == [23.0, 4.0]
    assert spoken_numbers("a hundred and thirty eight") == [138.0]
    assert spoken_numbers("one hundred and twelve cards") == [112.0]
    assert spoken_numbers("All hundred and twelve cards, the hundred and eight card deck") == [112.0, 108.0]


# ------------------------------------------------------------------ voice gate measurements
def test_voice_measurements():
    import numpy as np
    from pipeline.voice_gate import clipping, digital_silence_ms, internal_gaps, word_diff
    a = (np.random.default_rng(1).standard_normal(48000) * 0.01).astype(np.float32)
    assert digital_silence_ms(a) < 10
    b = a.copy(); b[1000:1000 + 960] = 0.0
    assert digital_silence_ms(b) >= 19
    c = a.copy(); c[500:505] = 1.0
    pk, run = clipping(c)
    assert pk >= -0.01 and run == 5 and clipping(a)[1] == 0
    assert internal_gaps([["a", 0, 0.3], ["b", 1.2, 1.5], ["c", 1.6, 1.9]]) == [("a", 0.3, 0.9)]
    assert word_diff("It won 35% of games.", "it won thirty five percent of games".split()) == ([], [])
    miss, extra = word_diff("The best of them won.", "the best of the best of them won".split())
    assert extra and not miss


def test_voice_input_headroom():
    """A float recording with peaks ABOVE full scale is gain-reduced before splitting; a normal one is untouched."""
    import json
    import subprocess
    import tempfile
    from pathlib import Path
    import numpy as np
    import soundfile as sf
    from pipeline.voice_source import decode_peak, headroom_gain_db, prepare_inputs
    assert headroom_gain_db(0.9) == 0.0 and headroom_gain_db(1.0) == 0.0
    assert abs(headroom_gain_db(2.0) - (-4.5 - 6.02)) < 0.01
    d = Path(tempfile.mkdtemp())
    t = np.arange(48000 * 2) / 48000
    hot = (1.6 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)            # +4.1 dBFS, stored as float
    sf.write(d / "hot.wav", hot, 48000, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(d / "hot.wav"), "-c:a", "aac", "-b:a", "256k",
                    str(d / "hot.m4a")], check=True)                       # the real case: a float m4a
    sf.write(d / "ok.wav", (0.5 * hot / 1.6).astype(np.float32), 48000, subtype="FLOAT")
    assert decode_peak(d / "hot.m4a") > 1.2
    used, log = prepare_inputs(d / "voice", [str(d / "hot.m4a"), str(d / "ok.wav")])
    assert log[0]["gain_db"] < 0 and used[0].endswith(".headroom.wav")
    assert abs(log[0]["peak_after_dbfs"] - (-4.5)) < 0.3, log[0]
    assert log[1]["gain_db"] == 0.0 and used[1] == str(d / "ok.wav")
    assert json.loads((d / "voice" / "_input_check.json").read_text())[0]["recording"] == "hot.m4a"


def test_voice_orig_backups_keyed_to_recording():
    """voice/_orig/ backups: reused for the same recording, refreshed for a new one, refused when unfingerprinted."""
    import json
    import tempfile
    from pathlib import Path
    from pipeline.voice_source import StaleBackup, fingerprint, sync_orig
    d = Path(tempfile.mkdtemp())
    (d / "a.m4a").write_bytes(b"take one"); (d / "b.m4a").write_bytes(b"take two")
    fa, fb = fingerprint(d / "a.m4a"), fingerprint(d / "b.m4a")
    assert fa != fb and fa == fingerprint(d / "a.m4a")
    v = d / "voice"; v.mkdir()
    def split(src, audio):                     # what split_recording writes
        (v / "l1.wav").write_bytes(audio); (v / "l1.json").write_text(json.dumps({"words": [], "source": src}))
    split(fa, b"split-A")
    assert sync_orig(v) == {"l1": "backed-up"}
    (v / "l1.wav").write_bytes(b"tightened-A")             # tighten_voice output (meta keeps the source)
    assert sync_orig(v) == {"l1": "reused"} and (v / "_orig" / "l1.wav").read_bytes() == b"split-A"
    split(fb, b"split-B")                                  # NEW recording: the old backup must not be used
    assert sync_orig(v) == {"l1": "refreshed"} and (v / "_orig" / "l1.wav").read_bytes() == b"split-B"
    (v / "l1.json").write_text(json.dumps({"words": []}))   # split before the guard: can't tell -> refuse
    try:
        sync_orig(v); assert False, "unfingerprinted backup was reused silently"
    except StaleBackup:
        pass
    assert sync_orig(v, allow_legacy=True) == {"l1": "reused"}


def test_pixel_flash_and_black():
    import subprocess, tempfile
    from pathlib import Path
    from pipeline.qa_visual import pixel_checks
    d = Path(tempfile.mkdtemp())
    # 4 s grey, one white frame at 1 s, black from 2.0 to 2.5 s
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x3a5a52:s=320x180:r=30:d=4",
                    "-vf", "drawbox=c=white:t=fill:enable='eq(n,30)',drawbox=c=black:t=fill:enable='between(t,2,2.5)'",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "v.mp4")], check=True)
    iss, _ = pixel_checks(d / "v.mp4", [{"id": "s", "start": 0, "duration": 4}])
    msgs = " ".join(i["msg"] for i in iss)
    assert "flash" in msgs and "black" in msgs, msgs
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x3a5a52:s=320x180:r=30:d=3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "ok.mp4")], check=True)
    assert pixel_checks(d / "ok.mp4", [{"id": "s", "start": 0, "duration": 3}])[0] == []
    # a hard cut to a darker scene is a step, not a dip
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x5a8a7e:s=320x180:r=30:d=2",
                    "-f", "lavfi", "-i", "color=c=0x2c463f:s=320x180:r=30:d=2", "-filter_complex", "[0][1]concat=n=2:v=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "step.mp4")], check=True)
    assert pixel_checks(d / "step.mp4", [{"id": "s", "start": 0, "duration": 4}])[0] == []


def test_short_opening():
    import subprocess, tempfile
    from pathlib import Path
    from pipeline.qa_visual import opening_checks
    d = Path(tempfile.mkdtemp())
    # bad: 1.5 s of an empty, still frame, then a busy moving pattern
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x3a5a52:s=270x480:r=30:d=1.5",
                    "-f", "lavfi", "-i", "testsrc2=s=270x480:r=30:d=3", "-filter_complex", "[0][1]concat=n=2:v=1",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "bad.mp4")], check=True)
    iss, _ = opening_checks(d / "bad.mp4")
    msgs = " ".join(i["msg"] for i in iss)
    assert "empty" in msgs and "still" in msgs, msgs
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=s=270x480:r=30:d=3",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "good.mp4")], check=True)
    assert opening_checks(d / "good.mp4")[0] == []


def test_flicker():
    import subprocess, tempfile
    from pathlib import Path
    from pipeline.qa_visual import flicker_check
    d = Path(tempfile.mkdtemp())
    # bad: a patch that toggles light/dark every frame (z-fighting), on a slowly panning background
    move = "drawbox=x='40+t*60':y=300:w=200:h=140:c=0xf2b134:t=fill"     # smooth motion: must NOT count as flicker
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x33504b:s=540x960:r=30:d=2",
                    "-vf", move + ",drawbox=x=200:y=600:w=120:h=60:c=white:t=fill:enable='mod(n,2)'",
                    "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(d / "bad.mp4")], check=True)
    iss, m = flicker_check(d / "bad.mp4", [{"id": "s", "start": 0, "duration": 2}])
    assert iss and "flicker" in iss[0]["msg"], m
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x33504b:s=540x960:r=30:d=2",
                    "-vf", move, "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(d / "ok.mp4")], check=True)
    assert flicker_check(d / "ok.mp4", [{"id": "s", "start": 0, "duration": 2}])[0] == []


if __name__ == "__main__":
    import sys
    fails = 0
    for k, v in list(globals().items()):
        if k.startswith("test_"):
            try:
                v(); print("ok  ", k)
            except AssertionError as e:
                fails += 1; print("FAIL", k, e)
    sys.exit(1 if fails else 0)
