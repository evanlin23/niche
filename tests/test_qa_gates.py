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


def states(fn, dur=6.0):
    out = []
    for f in list(range(0, int(dur * 30), 3)) + [int(dur * 30) - 2, int(dur * 30) - 1]:
        t = f / 30
        texts, objs, tw = fn(t)
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
    iss, _ = check_scene(SC, spec(dur=9.0, cues={"a1": [0.2, 8.8]}), states(lambda t: ([text(1, OK_TEXT)], [], []), 9.0), {"a1": "x"}, {})
    assert "coverage" in checks(iss)


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
