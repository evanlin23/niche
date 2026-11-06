"""Sorry! experiments: engine check, mirror check, luck vs skill, one-habit tests, card values, editions.
    python3 episodes/sorry/experiments.py [--games N] [--seed S] [--out DIR] [--all]
--games is games per test (the adult 5-card-hand tests run a quarter of that: they're 5x slower).
Writes results.json (all numbers) with the true total of games simulated."""
import argparse, json, subprocess
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "sims" / "sorry"
BIN = SIM / "sorrysim"

NORMAL = {"name": "normal"}
BEST = {"name": "best", "rush": 3, "danger": 1, "safe_first": True, "keep": 0.5}  # keep: only used in the 5-card variation
HABITS = {  # one change from the normal player each
    "random": {"name": "random", "random": True},
    "spreader": {"name": "spreader", "rush": 0.5},       # spreads moves over all pawns
    "runner": {"name": "runner", "rush": 3},             # pushes the front pawn home
    "lead": {"name": "lead", "lead": True},              # rule of thumb: always move the front pawn if it can
    "front_unless_bump": {"name": "front_unless_bump", "lead": True, "lead_bump": True},  # ...unless you can bump someone
    "careful": {"name": "careful", "danger": 1},         # avoids squares opponents can hit next turn
    "safety_first": {"name": "safety_first", "safe_first": True},
    "peaceful": {"name": "peaceful", "hurt": -1},        # ignores opponents, plays its own race
    "avenger": {"name": "avenger", "sorry_lead": True},  # Sorry! always bumps the opponent's furthest pawn
    "switcher": {"name": "switcher", "switch_lead": True},  # 11 always swaps with the opponent's furthest pawn
    "never_switch": {"name": "never_switch", "no_switch": True},
    "never_split": {"name": "never_split", "no_split": True},
    "never_back1": {"name": "never_back1", "no_back10": True},
    "one_at_a_time": {"name": "one_at_a_time", "start_late": True},
}
RULES_2020 = {"two_no_draw": True, "sorry_four": True}


def run(games, seed, players=4, rules=None, base=None, test=None, mode="game"):
    cmd = [str(BIN), "-mode", mode, "-games", str(games), "-seed", str(seed), "-players", str(players),
           "-rules", json.dumps(rules or {}), "-base", json.dumps(base or NORMAL)]
    if test:
        cmd += ["-test", json.dumps(test)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def exact_checks():
    """Plain math. 45 cards; only a 1 (five) or a 2 (four) starts a pawn."""
    none4 = Fraction(36 * 35 * 34 * 33, 45 * 44 * 43 * 42)  # first 4 cards of the pack are all non-starters
    first = Fraction(9, 45)
    return {"nobody_out_after_round1": float(none4), "first_player_out_turn1": float(first)}


def main():
    import sys
    if "--v2" in sys.argv:  # the skill-meter run (rule combinations, Team rules, habits under the pick)
        sys.argv.remove("--v2")
        import importlib.util
        sp = importlib.util.spec_from_file_location("v2", Path(__file__).resolve().parent / "experiments_v2.py")
        v2 = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(v2)
        return v2.main()
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    G, S = a.games, a.seed
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=SIM, check=True)
    res = {"games_per_test": G, "seed": S}
    total = 0

    def game(key, *args, n=G, **kw):
        nonlocal total
        r = run(n, S, *args, **kw)
        total += r["games"]
        return r

    # 1. engine check vs plain math (first-round deals, not counted as games)
    ex = exact_checks()
    ck = run(G, S, mode="check")
    res["engine_check"] = {"math": ex, "engine": ck}
    print(f"engine check: nobody out after round 1  math {100*ex['nobody_out_after_round1']:.3f}%  engine {100*ck['nobody_out_after_round1']:.3f}%")
    print(f"              first player out on turn 1 math {100*ex['first_player_out_turn1']:.3f}%  engine {100*ck['first_player_out_turn1']:.3f}%")

    # 2. mirror: everyone plays the same; each seat should win its fair share. Also card values and game length.
    res["mirror"] = {}
    for n in (2, 3, 4):
        r = game("mirror", players=n)
        res["mirror"][f"{n}p"] = r
        print(f"mirror {n}p: seats " + " ".join(f"{100*x:.2f}" for x in r["seat_win"]) + f"  first player {100*r['first_player_win']:.2f}%  turns {r['mean_turns']:.0f}")
    res["mirror"]["4p_best"] = game("mirror", base=BEST)
    # 3 players leave one side of the board empty. Control: the same games with no interaction at all
    # (no bumps, Sorry!, switches; slides don't bump) must give every seat a third.
    res["mirror"]["3p_no_interaction"] = game("mirror", players=3, rules={"no_interact": True})
    print("mirror 3p no interaction: " + " ".join(f"{100*x:.2f}" for x in res["mirror"]["3p_no_interaction"]["seat_win"]))
    print("mirror 4p best bots: " + " ".join(f"{100*x:.2f}" for x in res["mirror"]["4p_best"]["seat_win"]))

    # 3. luck vs skill
    res["luck"] = {
        "random_vs_normal": game("luck", test=HABITS["random"]),
        "best_vs_normal": game("luck", test=BEST),
        "normal_vs_random": game("luck", base=HABITS["random"], test=NORMAL),
        "best_vs_random": game("luck", base=HABITS["random"], test=BEST),
    }
    for k, r in res["luck"].items():
        print(f"luck {k:18s} {100*r['test_win']:.2f}%")

    # 4. one-habit tests at a 4-player table of normal players (fair share 25%)
    res["habits"] = {}
    for k, p in HABITS.items():
        if k == "random":
            continue
        r = game("habit", test=p)
        res["habits"][k] = r
        print(f"habit {k:14s} {100*r['test_win']:.2f}% +-{100*r['ci95']:.2f}")

    # 5. player count
    res["players"] = {f"{n}p": game("players", players=n, test=BEST) for n in (2, 3)}
    for k, r in res["players"].items():
        print(f"best vs normal {k}: {100*r['test_win']:.2f}% (fair {100*r['fair_share']:.1f}%)")

    # 6. editions and the adult variation
    res["editions"] = {
        "rules2020_mirror": game("ed", rules=RULES_2020),
        "rules2020_best": game("ed", rules=RULES_2020, test=BEST),
        "rules2020_random": game("ed", rules=RULES_2020, test=HABITS["random"]),
        "no_extra_one_best": game("ed", rules={"no_extra_one": True}, test=BEST),
        "hand5_mirror": game("ed", n=max(1, G // 4), rules={"hand": 5}),
        "hand5_best": game("ed", n=max(1, G // 4), rules={"hand": 5}, test=BEST),
        "hand5_random": game("ed", n=max(1, G // 4), rules={"hand": 5}, test=HABITS["random"]),
    }
    for k, r in res["editions"].items():
        print(f"edition {k:18s} " + (f"{100*r['test_win']:.2f}%" if "test_win" in r else "seats " + " ".join(f"{100*x:.2f}" for x in r["seat_win"])) + f"  turns {r['mean_turns']:.0f}")

    res["total_games"] = total
    (out / "results.json").write_text(json.dumps(res, indent=1))
    print(f"total games simulated: {total:,}  -> {out / 'results.json'}")


if __name__ == "__main__":
    main()
