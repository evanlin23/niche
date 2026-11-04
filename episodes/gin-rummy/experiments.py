"""Gin rummy experiments: when to knock, what to pick up, what to throw, rule variants. Full games to 100.
    python3 episodes/gin-rummy/experiments.py [--games N] [--seed S] [--out DIR] [--all]
Writes results.json with the true totals (games, and hands inside them)."""
import argparse, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "sims" / "gin"
BIN = SIM / "ginsim"

NORMAL = {"name": "normal", "knock": 10, "take": "meld", "tie": "keep"}   # knocks the moment it can
KNOCK = {f"knock_{k}": dict(NORMAL, name=f"knock_{k}", knock=k) for k in (8, 6, 4, 2)}
KNOCK["gin_only"] = dict(NORMAL, name="gin_only", knock=0)
LATE = {
    "gin_then_knock_late": dict(NORMAL, name="gin_then_knock_late", knock=0, knock_late=10, late_stock=10),
    "knock4_then_10_late": dict(NORMAL, name="knock4_then_10_late", knock=4, knock_late=10, late_stock=14),
}
HABITS = {
    "take_lower": dict(NORMAL, name="take_lower", take="lower"),   # picks up any discard that lowers deadwood
    "never_take": dict(NORMAL, name="never_take", take="never"),   # always draws blind
    "dump_high": dict(NORMAL, name="dump_high", tie="high"),       # throws high cards first
    "watcher": dict(NORMAL, name="watcher", watch=True),           # doesn't feed the opponent's pickups
    "random_discards": dict(NORMAL, name="random_discards", random=True),
}
NO_LAYOFF = {"no_layoff_on_gin": True}
BONUS25 = {"gin_bonus": 25, "undercut_bonus": 25}


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
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=SIM, check=True)
    res = {"games_per_test": G, "seed": S}
    tot = {"games": 0, "hands": 0}

    def game(x, y=NORMAL, rules=None):
        r = run(G, S, x, y, rules)
        tot["games"] += r["games"]
        tot["hands"] += r["hands"]
        return r

    exact = json.loads((Path(__file__).resolve().parent / "data" / "exact_check.json").read_text())
    ck = run(G, S, NORMAL, NORMAL, mode="deal")
    res["engine_check"] = {"math": {"deal_has_meld": exact["deal_has_meld"]}, "engine": ck}
    print(f"deal holds a meld: math {100*exact['deal_has_meld']:.3f}%  engine {100*ck['deal_has_meld']:.3f}%")

    res["mirror"] = game(NORMAL)
    m = res["mirror"]
    print(f"mirror: A {100*m['a_win']:.2f}%  playing first {100*m['a_win_when_a_plays_first']:.2f}%  hands/game {m['mean_hands_per_game']:.2f}  gin {100*m['gin_rate']:.2f}%")
    res["knock"] = {k: game(p) for k, p in KNOCK.items()}
    res["late"] = {k: game(p) for k, p in LATE.items()}
    res["habits"] = {k: game(p) for k, p in HABITS.items()}
    for grp in ("knock", "late", "habits"):
        for k, r in res[grp].items():
            print(f"{grp:6s} {k:22s} wins {100*r['a_win']:.2f}% +-{100*r['ci95']:.2f}")
    res["rules"] = {
        "no_layoff_mirror": game(NORMAL, NORMAL, NO_LAYOFF),
        "no_layoff_gin_only": game(KNOCK["gin_only"], NORMAL, NO_LAYOFF),
        "bonus25_mirror": game(NORMAL, NORMAL, BONUS25),
        "bonus25_gin_only": game(KNOCK["gin_only"], NORMAL, BONUS25),
        "bonus25_knock_6": game(KNOCK["knock_6"], NORMAL, BONUS25),
    }
    for k, r in res["rules"].items():
        print(f"rules  {k:22s} A wins {100*r['a_win']:.2f}%")
    res["total_games"] = tot["games"]
    res["total_hands"] = tot["hands"]
    (out / "results.json").write_text(json.dumps(res, indent=1))
    print(f"total: {tot['games']:,} games ({tot['hands']:,} hands) -> {out / 'results.json'}")


if __name__ == "__main__":
    main()
