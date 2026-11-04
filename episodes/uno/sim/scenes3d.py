"""3D specs for the UNO episode. Chart values come from data/results.json only."""
from __future__ import annotations
import importlib.util, json, os, sys
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
EP = HERE.parent
FPS = 30
MODULE = "/episodes/uno/web/scenes.js"
R = json.loads((EP / "data" / "results.json").read_text())
CFG = yaml.safe_load((EP / "scenes.yaml").read_text())
LOOK = {"look": CFG.get("look"), "quality": CFG.get("quality", "normal"), "ssaa": float(os.environ.get("RENDER_SSAA", CFG.get("ssaa", 1)))}
_ek = importlib.util.spec_from_file_location("ek3d", EP.parent / "exploding-kittens" / "sim" / "scenes3d.py")
EK = importlib.util.module_from_spec(_ek); sys.modules["ek3d"] = EK; _ek.loader.exec_module(EK)
NAVY, CORAL, MUSTARD, TEAL, CREAM, GREY = "#22304a", "#ff6b57", "#f2b134", "#2a9d8f", "#f4ead5", "#8d8273"
V = R["variants"]; T2 = R["two_player"]; H = R["habits"]
pct = lambda x: round(x * 100, 1)
it = lambda label, value, color=CREAM, at=0, hl=False: {"label": label, "value": round(value, 1), "color": color, "at": at, "hl": hl}
CHARTS = {
    "hook": lambda: dict(fair=None, maxV=110, unit="", items=[
        it("official rules", V["official"]["table"]["mean_turns"], CREAM, "o4"),
        it("draw until you can play", V["draw_until"]["table"]["mean_turns"], CORAL, "o4+1.2", True)]),
    "length": lambda: dict(fair=None, maxV=110, unit="", items=[
        it("jump in", V["jump_in"]["table"]["mean_turns"], TEAL, "x2"),
        it("official", V["official"]["table"]["mean_turns"], CREAM, "x1"),
        it("forced play", V["forced_play"]["table"]["mean_turns"], CREAM, "x2+5"),
        it("Seven Zero", V["seven_zero"]["table"]["mean_turns"], CREAM, "x2+2.5"),
        it("stacking", V["stacking"]["table"]["mean_turns"], CREAM, "x2+2"),
        it("free +4", V["free_draw4"]["table"]["mean_turns"], CREAM, "x2+3"),
        it("draw until you can play", V["draw_until"]["table"]["mean_turns"], CORAL, "x3", True)]),
    "stack": lambda: dict(fair=None, maxV=10, items=[
        it("official", pct(V["official"]["table"]["share_rounds_with_10plus_draw"]), CREAM, "s2"),
        it("stacking +2s", pct(V["stacking"]["table"]["share_rounds_with_10plus_draw"]), MUSTARD, "s2+1", True),
        it("+2s and +4s", pct(V["stacking_mixed"]["table"]["share_rounds_with_10plus_draw"]), CORAL, "s2+4")]),
    "sevenzero": lambda: dict(fair=25, maxV=40, items=[
        it("goes first: official", pct(V["official"]["table"]["first_seat_win"]), CREAM, "z2"),
        it("goes first: Seven Zero", pct(V["seven_zero"]["table"]["first_seat_win"]), MUSTARD, "z2+4"),
        it("best bot: official", pct(V["official"]["smart_vs_normal"]), CREAM, "z3"),
        it("best bot: Seven Zero", pct(V["seven_zero"]["smart_vs_normal"]), CORAL, "z3+2", True)]),
    "everything": lambda: dict(fair=None, maxV=110, unit="", items=[
        it("official", V["official"]["table"]["mean_turns"], CREAM, "a2"),
        it("all house rules", V["everything"]["table"]["mean_turns"], CORAL, "a2+2", True)]),
    "twoplayer": lambda: dict(fair=50, maxV=70, items=[
        it("goes first", pct(T2["official"]["table"]["first_seat_win"]), CREAM, "t2"),
        it("best bot: official", pct(T2["official"]["smart_vs_normal"]), MUSTARD, "t2+3"),
        it("best bot: Seven Zero", pct(T2["seven_zero"]["smart_vs_normal"]), CORAL, "t2+5", True)]),
    "luck": lambda: dict(fair=25, maxV=40, items=[
        it("normal player", 25.0, CREAM, "k2"), it("best bot", pct(H["all smart habits"]), MUSTARD, "k2+1.5", True)]),
    "habits": lambda: dict(fair=25, maxV=40, items=[
        it("random Wild color", pct(H["random colour choice"]), CORAL, "h3"),
        it("dump high cards", pct(H["dump high cards"]), CORAL, "h5"),
        it("challenge every +4", pct(H["always challenge"]), CREAM, "h4"),
        it("bluff +4s", pct(H["bluff Draw 4 half the time"]), CREAM, "h4+1"),
        it("hold your Wilds", pct(H["hold wilds"]), MUSTARD, "h2", True)]),
}


def base(ctx):
    s = EK.base(ctx); s["module"] = MODULE; s.update(LOOK); return s


def build_spec(ctx):
    s = base(ctx)
    if ctx.params.get("chart"):
        s["chart"] = CHARTS[ctx.params["chart"]]()
    if ctx.scene.render == "statement":
        s["lines"] = EK.statement_lines(ctx)
    return s
