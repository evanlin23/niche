"""Connect 4 experiments: habit ladder, look-ahead, first-player edge, opening column.
    python3 episodes/connect-4/experiments.py [--games N per seat] [--seed S] [--out DIR]"""
import argparse, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "sims" / "connect4" / "c4b"
BOTS = {
    "random": {"name": "random"},
    "win_block": {"name": "win_block", "win_block": True},
    "center": {"name": "center", "win_block": True, "center": True},
    "careful": {"name": "careful", "win_block": True, "center": True, "careful": True},
    "look2": {"name": "look2", "win_block": True, "careful": True, "depth": 2},
    "look4": {"name": "look4", "win_block": True, "careful": True, "depth": 4},
    "look6": {"name": "look6", "win_block": True, "careful": True, "depth": 6},
}
SEED = 1


def match(a, b, games):
    return json.loads(subprocess.run([str(BIN), "-a", json.dumps(a), "-b", json.dumps(b), "-games", str(games), "-seed", str(SEED)],
                                     capture_output=True, text=True, check=True).stdout)


def main():
    global SEED
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=100_000)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--out", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args(); SEED = a.seed; G = a.games
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"; out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=BIN.parent, check=True)
    res = {"games_per_test": G, "bots": BOTS, "ladder": {}, "mirror": {}, "openings": {}}
    names = list(BOTS)
    print("ladder (each bot vs the one below it)")
    for lo, hi in zip(names, names[1:]):
        g = G if BOTS[hi].get("depth", 0) < 6 else max(2000, G // 50)
        r = match(BOTS[hi], BOTS[lo], g)
        res["ladder"][f"{hi}_vs_{lo}"] = r
        print(f"  {hi:10s} vs {lo:10s}  win {r['a_win_overall'] * 100:5.1f}%  draws {(r['draw_a_first'] + r['draw_a_second']) / 2 * 100:4.1f}%  moves {r['mean_moves']:.1f}")
    print("mirror matches: does going first help?")
    for n in names:
        g = G if BOTS[n].get("depth", 0) < 6 else max(2000, G // 50)
        r = match(BOTS[n], BOTS[n], g)
        res["mirror"][n] = r
        print(f"  {n:10s} first player wins {r['a_win_first'] * 100:5.1f}%  second {(1 - r['a_win_first'] - r['draw_a_first']) * 100:5.1f}%  draws {r['draw_a_first'] * 100:4.1f}%")
    print("opening column (careful bot, forced first move) vs careful bot")
    for col in range(1, 8):
        r = match(dict(BOTS["careful"], first_col=col), BOTS["careful"], G)
        res["openings"][str(col)] = r
        print(f"  column {col}: first player wins {r['a_win_first'] * 100:5.1f}%")
    (out / "results.json").write_text(json.dumps(res, indent=1)); print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
