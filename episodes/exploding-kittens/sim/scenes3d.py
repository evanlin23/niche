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
    "ranking": lambda: dict(fair=20, maxV=50, players=5, items=[
        item("The Hoarder", rk("The Hoarder"), CORAL, "b5@hoarder"),
        item("The Panicker", rk("The Panicker"), CORAL, "b5@panicker"),
        item("The Gambler", rk("The Gambler"), CORAL, "b5@gambler"),
        item("The Normal Player", rk("The Normal Player"), CREAM, "b5@normal"),
        item("The Patient One", rk("The Patient One"), MUSTARD, "b5@patient", True)]),
    "ranking_hook": lambda: dict(fair=20, maxV=50, players=5, items=[
        item("best bot", rk("The Patient One"), MUSTARD, "o4@thirty", True),
        item("worst bot", rk("The Hoarder"), CORAL, "o4@eleven")]),
    "patience": lambda: dict(fair=25, maxV=40, players=4, items=[
        item("normal player", sw("random_play", 0.15), CREAM, "p2@twenty"),
        item("never play cards for fun", sw("random_play", 0.0), MUSTARD, "p2@thirty", True),
        item("play cards on a whim half the time", sw("random_play", 0.5), CORAL, "p3@fourteen")]),
    "dodge": lambda: dict(fair=25, maxV=40, players=4, items=[
        item("the Panicker: 1 in 4", sw("avoid", 0.25), CORAL, "d2@sixteen"),
        item("dodge at 1 in 3", sw("avoid", 0.33), CORAL, "d3@coin-0.3"),
        item("dodge at a coin flip", sw("avoid", 0.5), CREAM, "d3@coin"),
        item("only when you KNOW", sw("avoid", 1.0), MUSTARD, "d3@know", True)]),
    "future": lambda: dict(fair=25, maxV=40, players=4, items=[
        item("never use it", sw("future", 2.0), CORAL, "f2@never"),
        item("use it right away", sw("future", 0.0), CORAL, "f2@using_it_the"),
        item("use it at 1 in 3 odds", sw("future", 0.3), MUSTARD, "f3@peek", True)]),
    "placement": lambda: dict(fair=25, maxV=40, players=4, items=[
        item("random", sw("placement", "random"), CREAM, "k2@random"),
        item("bottom", sw("placement", "bottom"), CORAL, "k3@worse"),
        item("top", sw("placement", "top"), TEAL, "k4@top"),
        item("next player's draw", sw("placement", "next"), MUSTARD, "k5@thirty", True)]),
    "steal": lambda: dict(fair=25, maxV=56, players=4, items=[
        item("the Patient One", pct(F["vs_casual"]["4"]["win"]), MUSTARD, "s2@forty", True),
        item("without pair steals", abl("pair_steal"), CORAL, "s2@thirty"),
        item("without Favors", abl("favor_use"), CORAL, "s2@thirty_four")]),
    "small": lambda: dict(fair=25, maxV=40, players=4, items=[
        item("give a random card", sw("give_worst", False), CREAM, "x2@random"),
        item("give your worst card", sw("give_worst", True), MUSTARD, "x2@three", True),
        item("never Nope", sw("nope_defend", 0.0), CORAL, "x3@twenty"),
        item("Nope half the time", sw("nope_defend", 0.5), CREAM, "x3@always"),
        item("always Nope", sw("nope_defend", 1.0), MUSTARD, "x3@twenty#2", True)]),
    "seats": lambda: dict(fair=None, maxV=72, items=[
        item("2 players: first", pct(R["seats"]["2"]["seat_win"][0]), MUSTARD, "t2@fifty", True),
        item("2 players: second", pct(R["seats"]["2"]["seat_win"][1]), CREAM, "t2@fifty+0.4"),
        item("5 players: first", pct(R["seats"]["5"]["seat_win"][0]), CREAM, "t3@first"),
        item("5 players: last", pct(R["seats"]["5"]["seat_win"][4]), MUSTARD, "t3@last", True)]),
    "twoplayer": lambda: dict(fair=50, maxV=92, fairSide="left", players=2, items=[
        item("normal player", sw2("patience", 0.15), CREAM, "t4@stop"),
        item("never play for fun", sw2("patience", 0.0), MUSTARD, "t4@sixty", True),
        item("cards on a whim half the time", sw2("patience", 0.5), CORAL, "t5@nineteen"),
        item("no pair steals", sw2("steal", False), CORAL, "t5@thirty"),
        item("See the Future right away", sw2("future", 0.0), CORAL, "t5@nine")]),
    "attacks": lambda: dict(fair=None, maxV=52, unit="%", items=[
        item("4 players: normal table", pct(X["tables"]["casual"]["explode_under_attack"]), CREAM, "d5@one_explosion"),
        item("2 players", pct(X["explode_under_attack_by_n"]["2"]), CORAL, "d6@two_in"),
        item("4 Patient Ones", pct(X["tables"]["best"]["explode_under_attack"]), MUSTARD, "d6@thirteen", True)]),
    "tables": lambda: dict(fair=25, maxV=72, players=4, items=[
        item("vs a normal table", pct(X["tables"]["casual"]["best_win"]), CREAM, "r2@forty"),
        item("vs an aggressive table", pct(X["tables"]["aggressive"]["best_win"]), MUSTARD, "r2@fifty", True),
        item("vs hoarders", pct(X["tables"]["hoarder"]["best_win"]), CREAM, "r2@half")]),
    "length": lambda: dict(fair=None, maxV=45, unit=" turns", players=4, items=[
        item("normal table", round(X["tables"]["casual"]["mean_turns"], 1), CREAM, "r4@thirty"),
        item("four Patient Ones", round(X["tables"]["best"]["mean_turns"], 1), MUSTARD, "r4@twenty", True)]),
    "final": lambda: dict(fair=None, maxV=82, items=[
        *[x for n, at in (("2", "w4@sixty"), ("3", "w3@half"), ("4", "w3@forty"), ("5", "w4@twenty_nine")) for x in (
            item(f"{n} players: fair", round(100 / int(n), 1), GREY, at),
            item(f"{n} players: strategy", pct(F["vs_casual"][n]["win"]), MUSTARD, at + "+0.3", n == "4"))]]),
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


def card_highlights(ctx):
    """When the narration names a card type, that pile lifts and lights up: {group index: time}."""
    import re
    names = {"kitten": 0, "kittens": 0, "defuse": 1, "attack": 2, "skip": 3, "favor": 4, "shuffle": 5,
             "nope": 6, "see": 7, "cat": 8, "matching": 8, "steal": 8}
    out = {}
    for lid in ("g3",):                       # the card rundown
        c = ctx.scene.cues.get(lid)
        if not c:
            continue
        for w, t0, t1 in c.words:
            k = names.get(re.sub(r"[^a-z]", "", w.lower()))
            if k is not None and k not in out:
                out[k] = round(t0, 3)
    return {str(k): v for k, v in out.items()}


def resolve_at(ctx, ref):
    """'b5@hoarder' -> scene time of the word 'hoarder' in line b5 (force-aligned voice timing).
    Forms: 'id@word', 'id@word#2' (2nd occurrence), 'id@word+0.3', 'id@a_b' (first word of a phrase a b).
    Plain numbers and 'id', 'id+1.5', 'id:end' pass through (stage.at handles them)."""
    import re
    if not isinstance(ref, str) or "@" not in ref:
        return ref
    m = re.match(r"^(\w+)@([\w']+)(?:#(\d+))?([+-][\d.]+)?$", ref)
    if not m:
        raise ValueError(f"bad anchor {ref}")
    lid, word, nth, off = m.group(1), m.group(2), int(m.group(3) or 1), float(m.group(4) or 0)
    cue = ctx.scene.cues.get(lid)
    if cue is None:
        raise KeyError(f"anchor {ref}: line {lid} not in scene {ctx.scene.id}")
    norm = lambda w: re.sub(r"[^a-z0-9']", "", w.lower())
    seq = [norm(x) for x in word.split("_")]
    ws = [(norm(w), t0) for w, t0, _ in cue.words]
    hits = [ws[i][1] for i in range(len(ws) - len(seq) + 1) if [w for w, _ in ws[i:i + len(seq)]] == seq]
    if len(hits) < nth:
        raise KeyError(f"anchor {ref}: word not found in {lid}: {' '.join(w for w, _ in ws)}")
    return round(hits[nth - 1] + off, 3)


def resolve_all(ctx, obj):
    if isinstance(obj, dict):
        return {k: (resolve_at(ctx, v) if k in ("at", "until") else resolve_all(ctx, v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [resolve_all(ctx, x) for x in obj]
    return obj


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
        if ln.get("at"):                  # explicit word anchor ('b6@twenty') wins over first-word matching
            at = resolve_at(ctx, ln["at"]) + 0.05
        out.append({"text": ln["text"], "at": max(0.05, at - 0.05), "color": ln.get("color")})
    if out and out[0]["at"] > 0.3:      # never open on an empty floor: the first line is up from the start
        out[0]["at"] = 0.05
    return out


def build_spec(ctx) -> dict:
    s = base(ctx)
    p = ctx.params
    if ctx.scene.render == "statement":
        s["lines"] = statement_lines(ctx)
    if ctx.scene.render == "deck56":
        s["highlights"] = card_highlights(ctx)
    if p.get("chart"):
        s["chart"] = resolve_all(ctx, CHARTS[p["chart"]]())
    s["params"] = resolve_all(ctx, s["params"])           # notes / checklist items can use word anchors too
    if ctx.scene.render in ("table", "short"):
        tr = demo_trace(p.get("seed", 123))
        s["trace"] = {"events": tr["events"], "players": tr["players"], "winner": tr["result"]["Winner"]}
    return s


def thumbnail_spec(variant="A"):
    tr = demo_trace(123)
    return {"module": MODULE, "type": "thumb", "W": 1920, "H": 1080, "fps": FPS, "duration": 1 / FPS,
            "n_frames": 1, "cues": {}, "params": {}, "theme": "custom", "font": "rubik", **LOOK,
            "headline": pct(F["vs_casual"]["4"]["win"]), "variant": variant,
            "trace": {"events": tr["events"], "players": tr["players"], "winner": tr["result"]["Winner"]}}
