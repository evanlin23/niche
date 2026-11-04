"""3D spec builders for the Exploding Kittens episode (game-night look).
All chart numbers are read from data/*.json, never typed by hand."""
from __future__ import annotations

import json
import subprocess
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
EP = HERE.parent
ROOT = EP.parent.parent
FPS = 30
MODULE = "/episodes/exploding-kittens/web/scenes.js"

R = json.loads((EP / "data" / "results.json").read_text())
F = json.loads((EP / "data" / "final.json").read_text())
import os
import yaml
CFG = yaml.safe_load((EP / "scenes.yaml").read_text())
LOOK = {"look": CFG.get("look"), "quality": CFG.get("quality", "normal"),
        "ssaa": float(os.environ.get("RENDER_SSAA", CFG.get("ssaa", 1)))}
X = json.loads((EP / "data" / "extra.json").read_text())
RK = json.loads((EP / "data" / "ranking-5p.json").read_text())

NAVY, CORAL, MUSTARD, TEAL, CREAM, BLUE, GREY = "#22304a", "#ff6b57", "#f2b134", "#2a9d8f", "#f4ead5", "#4c8dff", "#8d8273"


def pct(x):
    return round(x * 100, 1)


def sw(key, value):
    for row in R[key]:
        if row["value"] == value:
            return pct(row["win"])
    raise KeyError((key, value))


def sw2(key, value):
    for row in X["2p"][key]:
        if row["value"] == value:
            return pct(row["win"])
    raise KeyError((key, value))


def abl(drop):
    for a in F["ablation"]:
        if a["drop"] == drop:
            return pct(a["win"])
    raise KeyError(drop)


def item(label, value, color=CREAM, at=0, hl=False):
    return {"label": label, "value": value, "color": color, "at": at, "hl": hl}


def rk(name):
    return next(pct(t["win"]) for t in RK["table"] if t["name"] == name)


CHARTS = {
    "ranking": lambda: dict(fair=20, maxV=50, items=[
        item("The Hoarder", rk("The Hoarder"), CORAL, "b5+7.5"),
        item("The Panicker", rk("The Panicker"), CORAL, "b5+6"),
        item("The Gambler", rk("The Gambler"), CORAL, "b5+4.5"),
        item("The Normal Player", rk("The Normal Player"), CREAM, "b5+3"),
        item("The Patient One", rk("The Patient One"), MUSTARD, "b5+0.8", True)]),
    "ranking_hook": lambda: dict(fair=20, maxV=50, items=[
        item("worst bot", rk("The Hoarder"), CORAL, "o4+2.2"),
        item("best bot", rk("The Patient One"), MUSTARD, "o4", True)]),
    "patience": lambda: dict(fair=25, maxV=40, items=[
        item("play cards on a whim half the time", sw("random_play", 0.5), CORAL, "p3"),
        item("normal player", sw("random_play", 0.15), CREAM, "p2"),
        item("never play cards for fun", sw("random_play", 0.0), MUSTARD, "p2+2.5", True)]),
    "dodge": lambda: dict(fair=25, maxV=40, items=[
        item("the Panicker: 1 in 4", sw("avoid", 0.25), CORAL, "d2+3"),
        item("dodge at 1 in 3", sw("avoid", 0.33), CORAL, "d3"),
        item("dodge at a coin flip", sw("avoid", 0.5), CREAM, "d3+0.8"),
        item("only when you KNOW", sw("avoid", 1.0), MUSTARD, "d3+3", True)]),
    "future": lambda: dict(fair=25, maxV=40, items=[
        item("never use it", sw("future", 2.0), CORAL, "f2"),
        item("use it right away", sw("future", 0.0), CORAL, "f2+2"),
        item("use it at 1 in 3 odds", sw("future", 0.3), MUSTARD, "f3", True)]),
    "placement": lambda: dict(fair=25, maxV=40, items=[
        item("bottom", sw("placement", "bottom"), CORAL, "k3"),
        item("random", sw("placement", "random"), CREAM, "k2+3"),
        item("top", sw("placement", "top"), TEAL, "k4"),
        item("next player's draw", sw("placement", "next"), MUSTARD, "k5", True)]),
    "steal": lambda: dict(fair=25, maxV=56, items=[
        item("the Patient One", pct(F["vs_casual"]["4"]["win"]), MUSTARD, "s2+2", True),
        item("without pair steals", abl("pair_steal"), CORAL, "s2+4.5"),
        item("without Favors", abl("favor_use"), CORAL, "s2+6.5")]),
    "small": lambda: dict(fair=25, maxV=40, items=[
        item("give a random card", sw("give_worst", False), CREAM, "x2"),
        item("give your worst card", sw("give_worst", True), MUSTARD, "x2+1.5", True),
        item("never Nope", sw("nope_defend", 0.0), CORAL, "x3"),
        item("Nope half the time", sw("nope_defend", 0.5), CREAM, "x3+1"),
        item("always Nope", sw("nope_defend", 1.0), MUSTARD, "x3+2.5", True)]),
    "seats": lambda: dict(fair=None, maxV=72, items=[
        item("2 players: first", pct(R["seats"]["2"]["seat_win"][0]), MUSTARD, "t2", True),
        item("2 players: second", pct(R["seats"]["2"]["seat_win"][1]), CREAM, "t2"),
        item("5 players: first", pct(R["seats"]["5"]["seat_win"][0]), CREAM, "t3"),
        item("5 players: last", pct(R["seats"]["5"]["seat_win"][4]), MUSTARD, "t3+1", True)]),
    "twoplayer": lambda: dict(fair=50, maxV=92, items=[
        item("cards on a whim half the time", sw2("patience", 0.5), CORAL, "q2+3"),
        item("no pair steals", sw2("steal", False), CORAL, "q3"),
        item("See the Future right away", sw2("future", 0.0), CORAL, "q4"),
        item("normal player", sw2("patience", 0.15), CREAM, "q2"),
        item("never play for fun", sw2("patience", 0.0), MUSTARD, "q2+1.5", True)]),
    "attacks": lambda: dict(fair=None, maxV=52, unit="%", items=[
        item("2 players", pct(X["explode_under_attack_by_n"]["2"]), CORAL, "a1"),
        item("3 players", pct(X["explode_under_attack_by_n"]["3"]), CORAL, "a1+0.6"),
        item("4 players", pct(X["tables"]["casual"]["explode_under_attack"]), MUSTARD, "a1+1.2", True),
        item("5 players", pct(X["explode_under_attack_by_n"]["5"]), CORAL, "a1+1.8")]),
    "tables": lambda: dict(fair=25, maxV=72, items=[
        item("vs a normal table", pct(X["tables"]["casual"]["best_win"]), CREAM, "r2"),
        item("vs an aggressive table", pct(X["tables"]["aggressive"]["best_win"]), MUSTARD, "r2+3", True),
        item("vs hoarders", pct(X["tables"]["hoarder"]["best_win"]), CREAM, "r2+6")]),
    "final": lambda: dict(fair=None, maxV=82, items=[
        *[x for n in ("2", "3", "4", "5") for x in (
            item(f"{n} players: fair", round(100 / int(n), 1), GREY, "w3"),
            item(f"{n} players: strategy", pct(F["vs_casual"][n]["win"]), MUSTARD, "w3+0.5", n == "4"))]]),
}


@lru_cache(None)
def demo_trace(seed=123):
    import importlib.util
    spec = importlib.util.spec_from_file_location("ekx", EP / "experiments.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    out = subprocess.run([str(ROOT / "sims" / "ek" / "eksim"), "-players", "4", "-trace", "-seed", str(seed),
                          "-test", json.dumps(m.BEST), "-base", json.dumps(m.CASUAL)],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def base(ctx) -> dict:
    sc = ctx.scene
    n = max(1, int(round(sc.duration * FPS)))
    return {"module": MODULE, "type": sc.render, "W": ctx.fmt.width, "H": ctx.fmt.height, "fps": FPS,
            "duration": sc.duration, "n_frames": n, "id": sc.id, "theme": "custom", "font": "rubik",
            "cues": {k: [c.start, c.end] for k, c in sc.cues.items()},
            "params": sc.params, "captions": ctx.captions, "hook": ctx.hook, **LOOK}


def statement_lines(ctx):
    """Display lines appear when the narration reaches each line's first word."""
    import re
    norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())
    words = [w for c in ctx.scene.cues.values() for w in c.words]
    out, i = [], 0
    for ln in ctx.params["lines"]:
        ln = ln if isinstance(ln, dict) else {"text": ln}
        first = norm(ln["text"].split()[0])
        j = i
        while j < len(words) and norm(words[j][0]) != first:
            j += 1
        at = words[j][1] if j < len(words) else (words[i][1] if i < len(words) else 0.3)
        if j < len(words):
            i = j + 1
        out.append({"text": ln["text"], "at": max(0.15, at - 0.05), "color": ln.get("color")})
    return out


def build_spec(ctx) -> dict:
    s = base(ctx)
    p = ctx.params
    if ctx.scene.render == "statement":
        s["lines"] = statement_lines(ctx)
    if p.get("chart"):
        s["chart"] = CHARTS[p["chart"]]()
    if ctx.scene.render in ("table", "short"):
        tr = demo_trace(p.get("seed", 123))
        s["trace"] = {"events": tr["events"], "players": tr["players"], "winner": tr["result"]["Winner"]}
    return s


def thumbnail_spec():
    tr = demo_trace(123)
    return {"module": MODULE, "type": "thumb", "W": 1920, "H": 1080, "fps": FPS, "duration": 1 / FPS,
            "n_frames": 1, "cues": {}, "params": {}, "theme": "custom", "font": "rubik", **LOOK,
            "headline": pct(F["vs_casual"]["4"]["win"]),
            "trace": {"events": tr["events"], "players": tr["players"], "winner": tr["result"]["Winner"]}}
