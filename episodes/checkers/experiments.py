"""Checkers experiments: engine checks, first-move edge, the forced-jump rule, skill, habits.
    python3 episodes/checkers/experiments.py [--games N] [--seed S] [--out DIR] [--all]
--games = games per test for the fast bots; 2-move players run N/40 games per test and 4-move players N/1000
(they are 10-100x slower). Writes results.json with the true total of games."""
import argparse, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "sims" / "checkers"
BIN = SIM / "cksim"

RANDOM = {"name": "random", "random": True}
CASUAL = {"name": "casual", "depth": 1}     # looks at its own move and every forced jump that follows
CLUB = {"name": "club", "depth": 2}         # also looks at the opponent's best reply
THINKER = {"name": "thinker", "depth": 4}   # four moves ahead
OPTIONAL = {"optional": True}
HUFF = {"huff": True}
HABITS = {  # one change from the casual player (official rules)
    "back_row": dict(CASUAL, name="back_row", back_row=20),   # keep your back row home
    "center": dict(CASUAL, name="center", center=10),         # take the centre
    "edges": dict(CASUAL, name="edges", edge=10),             # hug the sides ("edges are safe")
    "rush": dict(CASUAL, name="rush", advance=5),             # race men forward to king them
    "trade_when_ahead": dict(CASUAL, name="trade_when_ahead", trade=5),
    "kings_precious": dict(CASUAL, name="kings_precious", king_val=200),
    "kings_cheap": dict(CASUAL, name="kings_cheap", king_val=100),
}


def run(games, seed, a, b, rules=None, mode="game"):
    cmd = [str(BIN), "-mode", mode, "-games", str(games), "-seed", str(seed), "-rules", json.dumps(rules or {}),
           "-a", json.dumps(a), "-b", json.dumps(b)]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    G, S = a.games, a.seed
    G2, G4 = max(2, G // 40), max(2, G // 1000)
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=SIM, check=True)
    res = {"games_per_test": G, "games_per_test_club": G2, "games_per_test_thinker": G4, "seed": S}
    total = 0

    def game(x, y, rules=None, n=G):
        nonlocal total
        r = run(n, S, x, y, rules)
        total += r["games"]
        return r

    # 1. engine checks: perft (exact counts) and random play vs exact enumeration (exact_check.py)
    exact = json.loads((Path(__file__).resolve().parent / "data" / "exact_check.json").read_text())
    pf = json.loads(subprocess.run([str(BIN), "-mode", "perft", "-depth", "10"], capture_output=True, text=True, check=True).stdout)["perft"]
    rc = run(G, S, RANDOM, RANDOM, mode="randcheck")
    res["engine_check"] = {"perft_engine": pf, "perft_python": exact["perft"], "perft_published": exact["perft_published"],
                           "math": {"capture_within_6_plies": exact["capture_within_6_plies"]},
                           "engine": rc}
    print(f"perft engine {pf[:7]} python {exact['perft']}")
    print(f"random play, jump within 6 plies: math {100*exact['capture_within_6_plies']:.3f}%  engine {100*rc['capture_within_6_plies']:.3f}%")

    # 2. mirror (identical players, colours alternate): fairness + first-move edge
    res["mirror"] = {"random": game(RANDOM, RANDOM), "casual": game(CASUAL, CASUAL), "club": game(CLUB, CLUB, n=G2)}
    # 3. the forced-jump rule: official vs optional jumps vs the old huffing rule
    res["rules"] = {
        "random_optional": game(RANDOM, RANDOM, OPTIONAL),
        "casual_optional": game(CASUAL, CASUAL, OPTIONAL),
        "casual_huff": game(CASUAL, CASUAL, HUFF),
        "club_optional": game(CLUB, CLUB, OPTIONAL, n=G2),
        "club_huff": game(CLUB, CLUB, HUFF, n=G2),
    }
    for k, r in list(res["mirror"].items()) + list(res["rules"].items()):
        print(f"{k:16s} first {100*r['first_player_win']:.2f}  second {100*r['second_player_win']:.2f}  draw {100*r['draw']:.2f}  plies {r['mean_plies']:.0f}")
    # 4. skill under each rule: does looking further ahead pay more with forced jumps?
    res["skill"] = {
        "casual_vs_random": game(CASUAL, RANDOM),
        "casual_vs_random_optional": game(CASUAL, RANDOM, OPTIONAL),
        "club_vs_casual": game(CLUB, CASUAL, n=G2),
        "club_vs_casual_optional": game(CLUB, CASUAL, OPTIONAL, n=G2),
        "club_vs_casual_huff": game(CLUB, CASUAL, HUFF, n=G2),
        "thinker_vs_club": game(THINKER, CLUB, n=G4),
        "thinker_vs_club_optional": game(THINKER, CLUB, OPTIONAL, n=G4),
    }
    for k, r in res["skill"].items():
        print(f"{k:26s} wins {100*r['a_win']:.2f}  loses {100*r['b_win']:.2f}  draws {100*r['draw']:.2f}")
    # 5. one-habit tests vs a casual player
    res["habits"] = {k: game(p, CASUAL) for k, p in HABITS.items()}
    res["habits_club"] = {k: game(dict(CLUB, name=k + "_club", **{kk: vv for kk, vv in HABITS[k].items() if kk not in ("name", "depth")}), CLUB, n=G2)
                          for k in ("back_row", "center")}
    for k, r in list(res["habits"].items()) + list(res["habits_club"].items()):
        print(f"habit {k:18s} wins {100*r['a_win']:.2f}  loses {100*r['b_win']:.2f}  score {100*r['a_score']:.2f}")
    res["total_games"] = total
    (out / "results.json").write_text(json.dumps(res, indent=1))
    print(f"total games simulated: {total:,} -> {out / 'results.json'}")


if __name__ == "__main__":
    main()
