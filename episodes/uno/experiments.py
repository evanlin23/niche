"""UNO experiments: every house rule vs the official rules, plus one-habit tests.
    python3 episodes/uno/experiments.py [--games N] [--seed S] [--out DIR]"""
import argparse, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "sims" / "uno" / "unosim"
NORMAL = dict(name="normal", color_choice="most", challenge="p30", jump_prob=0.5, stack_prob=0.8, play_drawn=True)
SMART = dict(NORMAL, name="smart", hold_wilds=True, attack_small=2, change_color=True, challenge="smart")
VARIANTS = {"official": {}, "stacking": {"stack": True}, "stacking_mixed": {"stack": True, "stack_mix": True},
            "seven_zero": {"seven_zero": True}, "jump_in": {"jump_in": True}, "draw_until": {"draw_until": True},
            "forced_play": {"forced": True}, "free_draw4": {"free_d4": True},
            "everything": {"stack": True, "stack_mix": True, "seven_zero": True, "jump_in": True, "draw_until": True, "free_d4": True}}
SEED = 1


def run(rules, base=NORMAL, test=None, games=500_000, allsame=False, players=4):
    cmd = [str(BIN), "-players", str(players), "-games", str(games), "-seed", str(SEED), "-rules", json.dumps(rules), "-base", json.dumps(base)]
    if test: cmd += ["-test", json.dumps(test)]
    if allsame: cmd += ["-allsame"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


# ---------------------------------------------------------------- v2: "the best way to play Uno"
BEST = dict(NORMAL, name="best", hold_wilds=True, attack_small=2, change_color=True, challenge="smart", stack_prob=1.0, jump_prob=1.0)
MINE = {"stack": True, "multi": True, "free_d4": True}          # how the creator plays: same-type stacking, multi-play, free +4
TOGGLES = ["seven_zero", "jump_in", "draw_until", "free_d4", "multi", "no_action_out"]


def combos():
    import itertools
    for st in ("none", "same", "mixed"):
        for bits in itertools.product((0, 1), repeat=len(TOGGLES)):
            R = {k: True for k, b in zip(TOGGLES, bits) if b}
            if st != "none": R["stack"] = True
            if st == "mixed": R["stack_mix"] = True
            yield R


def key(R):
    return "+".join(k for k in ["stack", "stack_mix"] + TOGGLES if R.get(k)) or "official"


def run_v2(G):
    res = {"games_per_test": G, "best": BEST, "normal": NORMAL, "mine": MINE, "combos": []}
    for R in combos():
        t = run(R, games=G, allsame=True); b = run(R, test=BEST, games=G)
        res["combos"].append({"key": key(R), "rules": R, "turns": t["mean_turns"], "p90": t["p90_turns"], "first": t["first_seat_win"],
                              "best": b["test_win_rate"], "hits": t["share_rounds_max_hit_at_least"]})
        print(f"{key(R):60s} turns {t['mean_turns']:6.1f} best {b['test_win_rate']*100:5.2f}", flush=True)
    # habits under the official rules and under "how I play" (one change vs a normal table)
    HAB = [("hold wilds", {"hold_wilds": True}), ("random colour", {"color_choice": "random"}), ("switch to best colour", {"change_color": True}),
           ("always stack", {"stack_prob": 1.0}), ("never stack", {"stack_prob": 0.0}), ("one card at a time", {"multi": "one"}),
           ("attack when next has <=2", {"attack_small": 2}), ("dump high cards", {"dump_high": True}), ("all best habits", {k: v for k, v in BEST.items() if k != "name"})]
    res["habits_mine"] = {lab: run(MINE, test=dict(NORMAL, name=lab, **ch), games=G)["test_win_rate"] for lab, ch in HAB}
    # calling UNO (GDJ85: forget and get caught before the next turn -> draw 2). Table: forgets 1 in 4, catches half the time (assumption).
    U = dict(NORMAL, forget=0.25, catch=0.5)
    res["uno_table"] = {"forget": 0.25, "catch": 0.5}
    res["uno"] = {}
    for rname, R in [("official", {"uno_call": True}), ("penalty4", {"uno_call": True, "uno_penalty": 4}), ("mine", dict(MINE, uno_call=True))]:
        r = {}
        for lab, ch in [("normal", {}), ("never forgets", {"forget": 0.0}), ("forgets half", {"forget": 0.5}), ("always forgets", {"forget": 1.0}),
                        ("always catches", {"catch": 1.0}), ("never catches", {"catch": 0.0})]:
            r[lab] = run(R, base=U, test=dict(U, name=lab, **ch), games=G)["test_win_rate"]
        r["table"] = run(R, base=U, games=G, allsame=True)
        res["uno"][rname] = r
        print(rname, {k: round(v * 100, 2) for k, v in r.items() if k != "table"}, flush=True)
    return res


def main():
    global SEED
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=500_000)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--all", action="store_true", help="accepted for workflow compatibility"); ap.add_argument("--out", default=None)
    ap.add_argument("--v2", action="store_true", help="skill meter: every rule combination, UNO calling, 'how I play' -> v2.json")
    ap.add_argument("--matches", type=int, default=0, help="only play N whole games to 500 points per rule set -> matches.json")
    a = ap.parse_args(); SEED = a.seed; G = a.games
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"; out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=BIN.parent, check=True)
    if a.v2:
        (out / "v2.json").write_text(json.dumps(run_v2(G), indent=1)); print("wrote", out / "v2.json"); return
    if a.matches:
        m = {"games_per_rule_set": a.matches}
        for name in ("official", "draw_until", "stacking", "seven_zero", "jump_in", "free_draw4", "everything"):
            cmd = [str(BIN), "-match", "-players", "4", "-games", str(a.matches), "-seed", str(SEED), "-rules", json.dumps(VARIANTS[name]), "-base", json.dumps(NORMAL)]
            m[name] = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
            print(f"{name:14s} rounds {m[name]['mean_rounds_per_game']:5.2f}  turns {m[name]['mean_turns_per_game']:6.1f}", flush=True)
        (out / "matches.json").write_text(json.dumps(m, indent=1)); print("wrote", out / "matches.json"); return
    res = {"games_per_test": G, "normal": NORMAL, "smart": SMART, "variants": {}, "habits": {}}
    print(f"{'variant':16s} {'turns':>6s} {'median':>6s} {'p90':>5s} {'1st seat':>8s} {'max hit':>7s} {'10+ hit':>7s} {'smart bot':>9s}")
    for name, R in VARIANTS.items():
        base = run(R, games=G, allsame=True)
        sk = run(R, test=SMART, games=G)
        res["variants"][name] = {"rules": R, "table": base, "smart_vs_normal": sk["test_win_rate"]}
        print(f"{name:16s} drawn {base['mean_cards_drawn_per_round']:5.1f} {base['mean_turns']:6.1f} {base['median_turns']:6.0f} {base['p90_turns']:5.0f} {base['first_seat_win']*100:7.1f}% {base['mean_max_hit']:7.1f} {base['share_rounds_with_10plus_draw']*100:6.1f}% {sk['test_win_rate']*100:8.1f}%")
    print("\nhabits (official rules, one change vs normal table)")
    for label, change in [("hold wilds", {"hold_wilds": True}), ("attack when next has <=2", {"attack_small": 2}),
                          ("switch to your best colour", {"change_color": True}), ("random colour choice", {"color_choice": "random"}),
                          ("never challenge", {"challenge": "never"}), ("always challenge", {"challenge": "always"}),
                          ("smart challenge", {"challenge": "smart"}), ("bluff Draw 4 half the time", {"bluff": 0.5}),
                          ("play randomly", {"random": 1.0}), ("dump high cards", {"dump_high": True}),
                          ("all smart habits", {k: v for k, v in SMART.items() if k != "name"})]:
        r = run({}, test=dict(NORMAL, name=label, **change), games=G)
        res["habits"][label] = r["test_win_rate"]
        print(f"  {label:28s} {r['test_win_rate']*100:5.1f}%  ±{r['ci95']*100:.2f}")
    print("\ntwo players")
    res["two_player"] = {}
    for name in ("official", "draw_until", "stacking", "seven_zero"):
        base = run(VARIANTS[name], games=G, allsame=True, players=2)
        sk = run(VARIANTS[name], test=SMART, games=G, players=2)
        res["two_player"][name] = {"table": base, "smart_vs_normal": sk["test_win_rate"]}
        print(f"  {name:12s} turns {base['mean_turns']:5.1f}  1st {base['first_seat_win']*100:4.1f}%  smart {sk['test_win_rate']*100:4.1f}%  drawn {base['mean_cards_drawn_per_round']:.1f}")
    print("\none habit inside each house rule (4 players, vs normal table)")
    res["house_habits"] = {}
    for label, rname, change in [("always stack", "stacking", {"stack_prob": 1.0}), ("never stack", "stacking", {"stack_prob": 0.0}),
                                 ("always stack (mixed)", "stacking_mixed", {"stack_prob": 1.0}), ("never stack (mixed)", "stacking_mixed", {"stack_prob": 0.0}),
                                 ("seven to a random player", "seven_zero", {"swap_target": "random"}),
                                 ("always jump in", "jump_in", {"jump_prob": 1.0}), ("never jump in", "jump_in", {"jump_prob": 0.0}),
                                 ("hold wilds (free +4)", "free_draw4", {"hold_wilds": True}), ("hold wilds (draw until)", "draw_until", {"hold_wilds": True}),
                                 ("hold wilds (seven zero)", "seven_zero", {"hold_wilds": True})]:
        r = run(VARIANTS[rname], test=dict(NORMAL, name=label, **change), games=G)
        res["house_habits"][label] = {"rules": rname, "win": r["test_win_rate"]}
        print(f"  {label:28s} {r['test_win_rate']*100:5.1f}%")
    print("\nplayer count (official vs draw until, all normal)")
    res["players"] = {}
    for n in (2, 3, 4, 5, 6, 8, 10):
        o = run({}, games=G, allsame=True, players=n); d = run(VARIANTS["draw_until"], games=G, allsame=True, players=n)
        res["players"][str(n)] = {"official": o, "draw_until": d}
        print(f"  {n:2d} players  turns {o['mean_turns']:5.1f} -> {d['mean_turns']:5.1f}  first {o['first_seat_win']*100:4.1f}% (fair {100/n:.1f})")
    print("\nclassic 108-card deck (no Shuffle Hands, no blank wilds)")
    classic = {"no_shuffle": True, "no_custom": True}
    base = run(classic, games=G, allsame=True); sk = run(classic, test=SMART, games=G)
    res["classic_deck"] = {"table": base, "smart_vs_normal": sk["test_win_rate"]}
    print(f"  turns {base['mean_turns']:.1f}  first {base['first_seat_win']*100:.1f}%  smart {sk['test_win_rate']*100:.1f}%")
    runs = 2 * len(VARIANTS) + len(res["habits"]) + 2 * len(res["two_player"]) + len(res["house_habits"]) + 2 * len(res["players"]) + 2
    res["runs"] = runs; res["total_games"] = runs * G
    (out / "results.json").write_text(json.dumps(res, indent=1)); print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
