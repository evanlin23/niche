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


def main():
    global SEED
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=500_000)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--all", action="store_true", help="accepted for workflow compatibility"); ap.add_argument("--out", default=None)
    a = ap.parse_args(); SEED = a.seed; G = a.games
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"; out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=BIN.parent, check=True)
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
    (out / "results.json").write_text(json.dumps(res, indent=1)); print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
