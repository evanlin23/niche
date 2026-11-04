"""Battleship experiments: hunters, placements, the 'say which ship' rule, head-to-head.
    python3 episodes/battleship/experiments.py [--games N] [--seed S] [--out DIR]"""
import argparse, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "sims" / "battleship" / "bship"
SEED = 1
HUNTERS = {m: {"name": m, "mode": m, "labels": True} for m in ["random", "hunt_target", "parity", "density"]}
PLACERS = {"random": {"mode": "random"}, "edges": {"mode": "edges", "bias": 3}, "center": {"mode": "center", "bias": 3},
           "corners": {"mode": "corners", "bias": 4}, "cluster": {"mode": "cluster", "bias": 8}, "spread": {"mode": "spread"}}


def run(hunter, placer=None, games=20000, hunter2=None, placer2=None):
    cmd = [str(BIN), "-hunter", json.dumps(hunter), "-placer", json.dumps(placer or PLACERS["random"]), "-games", str(games), "-seed", str(SEED)]
    if hunter2: cmd += ["-hunter2", json.dumps(hunter2)]
    if placer2: cmd += ["-placer2", json.dumps(placer2)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def main():
    global SEED
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--out", default=None); ap.add_argument("--all", action="store_true")
    a = ap.parse_args(); SEED = a.seed; G = a.games
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"; out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=BIN.parent, check=True)
    res = {"games_per_test": G, "hunters": {}, "no_labels": {}, "placement": {}, "h2h": {}}
    print("hunters (official rule: told which ship)")
    for n, h in HUNTERS.items():
        r = run(h, games=G); res["hunters"][n] = r
        r2 = run(dict(h, labels=False), games=G); res["no_labels"][n] = r2
        print(f"  {n:12s} {r['mean_shots_a']:5.1f} shots   house rule (just 'hit'): {r2['mean_shots_a']:5.1f}")
    print("placement: shots each hunter needs (higher = better hiding)")
    for pn, p in PLACERS.items():
        res["placement"][pn] = {}
        row = []
        for hn in ["hunt_target", "parity", "density"]:
            # the hunter shoots at a fleet placed with strategy p (p is the opponent's placer)
            r = run(HUNTERS[hn], placer=PLACERS["random"], placer2=p, games=G)
            res["placement"][pn][hn] = r["mean_shots_a"]; row.append(f"{hn} {r['mean_shots_a']:5.1f}")
        print(f"  {pn:8s} " + "  ".join(row))
    print("head to head (A vs B, alternating who goes first)")
    for an, bn in [("density", "parity"), ("parity", "hunt_target"), ("density", "hunt_target"), ("hunt_target", "random"), ("density", "density")]:
        r = run(HUNTERS[an], hunter2=HUNTERS[bn], games=G)
        res["h2h"][f"{an}_vs_{bn}"] = r
        print(f"  {an:12s} vs {bn:12s} A wins {r['a_win'] * 100:5.1f}%   first player wins {r['first_player_win'] * 100:5.1f}%")
    print("placement head to head (same hunter both sides; A hides its fleet differently)")
    res["placement_h2h"] = {}
    for hn, pn in [("hunt_target", "spread"), ("hunt_target", "cluster"), ("hunt_target", "center"), ("density", "edges"), ("density", "corners")]:
        r = run(HUNTERS[hn], placer=PLACERS[pn], hunter2=HUNTERS[hn], placer2=PLACERS["random"], games=G)
        res["placement_h2h"][f"{pn}_vs_{hn}"] = r
        print(f"  hide '{pn}' vs a {hn} opponent: A wins {r['a_win'] * 100:5.1f}%")
    (out / "results.json").write_text(json.dumps(res, indent=1)); print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
