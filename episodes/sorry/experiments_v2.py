"""Sorry! v2: the skill meter for every rule combination, plus the official Team rules, random floors and habits
under the recommended rules.
    python3 episodes/sorry/experiments_v2.py [--games N] [--seed S] [--out DIR] [--pick JSON]
Skill meter = how often the best bot wins against three Normal players (fair share 25%; Team rules: a team of two
best bots against two Normal players, fair share 50%). Game length = mean turns per game (every player's turn
counts, a 2's extra draw is the same turn). --games is games per test. Writes v2.json with the true total."""
import argparse, itertools, json, subprocess
from pathlib import Path
import importlib.util

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("exp1", HERE / "experiments.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

SLIDES = {0: "classic", 2: "every slide, your own colour too", 3: "no slides"}
SWITCHES = ["start_out", "no_exact", "two_no_draw", "sorry_four", "hand5"]
# the recommended rules (picked from a local scan of every combination; see script.md)
PICK = {"start_out": True, "no_exact": True, "hand": 5}


def key(r):
    parts = []
    if r.get("slides"):
        parts.append(["", "slides_own", "slides_all", "no_slides"][r["slides"]])
    for s in SWITCHES:
        if (s == "hand5" and r.get("hand") == 5) or r.get(s):
            parts.append(s)
    return "+".join(parts) or "classic"


def combos():
    for sl in (0, 2, 3):  # 1 (2020 sheet: slide only on your own colour) needs the 2020 board layout: not tested
        for bits in itertools.product([0, 1], repeat=len(SWITCHES)):
            r = {}
            if sl:
                r["slides"] = sl
            for s, b in zip(SWITCHES, bits):
                if b:
                    r.update({"hand": 5} if s == "hand5" else {s: True})
            yield r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--pick", default=None, help="JSON rules for the recommended set (default PICK)")
    ap.add_argument("--only", default="combos,extras,habits")
    a = ap.parse_args()
    G, S = a.games, a.seed
    pick = json.loads(a.pick) if a.pick else PICK
    only = set(a.only.split(","))
    out = Path(a.out) if a.out else HERE / "data"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(E.BIN), "."], cwd=E.SIM, check=True)
    res = {"games_per_test": G, "seed": S, "pick": pick, "pick_key": key(pick)}
    total = 0

    def game(*args, **kw):
        nonlocal total
        r = E.run(G, S, *args, **kw)
        total += r["games"]
        return {k: v for k, v in r.items() if k not in ("card_swing", "card_forfeit")} if "test_win" in r else r

    if "combos" in only:
        res["combos"] = []
        for r in combos():
            b = game(rules=r, test=E.BEST)
            res["combos"].append({"key": key(r), "rules": r, "best": b["test_win"], "turns": b["mean_turns"],
                                  "games": b["games"]})
            print(f"{key(r):55s} best {100*b['test_win']:5.2f}  turns {b['mean_turns']:6.1f}", flush=True)

    if "extras" in only:
        X = res["extras"] = {}
        singles = {"classic": {}, "slides_all": {"slides": 2}, "no_slides": {"slides": 3},
                   "start_out": {"start_out": True}, "no_exact": {"no_exact": True}, "two_no_draw": {"two_no_draw": True},
                   "sorry_four": {"sorry_four": True}, "hand5": {"hand": 5}, "hand3": {"hand": 3},
                   "rules2020": {"two_no_draw": True, "sorry_four": True}, "pick": pick}
        X["random_floor"] = {k: game(rules=r, test=E.HABITS["random"])["test_win"] for k, r in singles.items()}
        X["hand3_best"] = game(rules={"hand": 3}, test=E.BEST)
        X["mirror_pick"] = game(rules=pick)
        T = {"teams": True}
        X["teams_mirror"] = game(rules=T)
        X["teams_best"] = game(rules=T, test=E.BEST)
        X["teams_random"] = game(rules=T, test=E.HABITS["random"])
        X["teams_pick_best"] = game(rules={**pick, **T}, test=E.BEST)
        X["players_pick"] = {f"{n}p": game(players=n, rules=pick, test=E.BEST) for n in (2, 3)}
        X["players_pick_mirror"] = {f"{n}p": game(players=n, rules=pick) for n in (2, 3)}
        for k, v in X.items():
            print(k, json.dumps(v)[:200], flush=True)

    if "habits" in only:
        H = res["habits_pick"] = {}
        habits = {**E.HABITS, "saver": {"name": "saver", "keep": 0.5},   # 5-card hand: saves Sorry! and 11s
                  "best_no_keep": {**E.BEST, "keep": 0}}
        for k, p in habits.items():
            H[k] = game(rules=pick, test=p)
            print(f"pick habit {k:16s} {100*H[k]['test_win']:5.2f}", flush=True)
        H["best"] = game(rules=pick, test=E.BEST)

    res["total_games"] = total
    (out / "v2.json").write_text(json.dumps(res, indent=1))
    print(f"total games simulated: {total:,} -> {out / 'v2.json'}")


if __name__ == "__main__":
    main()
