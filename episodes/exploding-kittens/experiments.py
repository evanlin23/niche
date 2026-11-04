"""Run all Exploding Kittens experiments with the Go engine (sims/ek).

    python3 episodes/exploding-kittens/experiments.py [--games 2000000]

Writes episodes/exploding-kittens/data/results.json. Every number in the script comes from here.
"""
import argparse, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "sims" / "ek" / "eksim"
OUT = Path(__file__).resolve().parent / "data" / "results.json"

# A "typical table": dodges only when it KNOWS a Kitten is on top, hides Kittens at random,
# plays cards on a whim sometimes, Nopes attacks on itself half the time.
CASUAL = dict(name="casual", avoid_risk=1.0, prefer_attack=False, future_risk=0.3, shuffle_if_ek=True,
              attack_free=0.0, placement="random", pair_steal=True, pair_noncats=False, triple_defuse=False,
              favor_use=True, steal_target="random", steal_when=0.0, nope_defend=0.5, nope_skip_seen=False,
              yup=0.3, random_play=0.15, give_worst=False)


def run(test=None, base=CASUAL, players=4, games=1_000_000, seed=1, allsame=False):
    cmd = [str(BIN), "-players", str(players), "-games", str(games), "-seed", str(seed), "-base", json.dumps(base)]
    if test:
        cmd += ["-test", json.dumps(test)]
    if allsame:
        cmd += ["-allsame"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


def variant(**kw):
    d = dict(CASUAL); d.update(kw); d["name"] = ",".join(f"{k}={v}" for k, v in kw.items()) or "casual"
    return d


def sweep(label, key, values, games, base=CASUAL, extra=None, players=4):
    rows = []
    for v in values:
        kw = dict(extra or {}); kw[key] = v
        r = run(variant(**kw), base=base, games=games, players=players)
        rows.append({"value": v, "win": r["test_win_rate"], "ci": r["ci95"], "fair": r["fair_share"],
                     "defuses": r["test_defuses_per_game"], "first_out": r["test_first_out_rate"]})
        print(f"  {label:14s} {key}={v!s:8s} win {r['test_win_rate']*100:5.2f}% ±{r['ci95']*100:.2f}  "
              f"first-out {r['test_first_out_rate']*100:4.1f}%")
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=2_000_000)
    G = ap.parse_args().games
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=BIN.parent, check=True)
    res = {"games_per_test": G, "casual": CASUAL}
    print("seat study (all casual)")
    res["seats"] = {}
    for n in (2, 3, 4, 5):
        r = run(players=n, games=G, allsame=True)
        res["seats"][n] = {"seat_win": r["seat_win_rate"], "mean_turns": r["mean_turns"]}
        print(f"  {n}p seats {[round(x*100,2) for x in r['seat_win_rate']]}  turns {r['mean_turns']:.1f}")
    print("experiments vs a casual table (4 players)")
    res["placement"] = sweep("placement", "placement", ["random", "top", "next", "second", "third", "middle", "bottom"], G)
    res["avoid"] = sweep("avoid", "avoid_risk", [1.0, 0.5, 0.4, 0.33, 0.25, 0.2, 0.15, 0.1, 0.05], G)
    res["attack_vs_skip"] = sweep("attack>skip", "prefer_attack", [False, True], G, extra={"avoid_risk": 0.25})
    res["future"] = sweep("future", "future_risk", [2.0, 0.5, 0.3, 0.2, 0.1, 0.0], G)
    res["random_play"] = sweep("random play", "random_play", [0.0, 0.15, 0.3, 0.5], G)
    res["pair_steal"] = sweep("pair steal", "pair_steal", [False, True], G)
    res["steal_target"] = sweep("steal target", "steal_target", ["random", "most", "next"], G)
    res["steal_when"] = sweep("steal when", "steal_when", [0.0, 0.1, 0.2, 0.3], G)
    res["triple_defuse"] = sweep("triple", "triple_defuse", [False, True], G)
    res["favor"] = sweep("favor", "favor_use", [False, True], G)
    res["nope_defend"] = sweep("nope defend", "nope_defend", [0.0, 0.5, 1.0], G)
    res["nope_skip_seen"] = sweep("nope skip", "nope_skip_seen", [False, True], G)
    res["give_worst"] = sweep("give worst", "give_worst", [False, True], G)
    res["attack_free"] = sweep("attack free", "attack_free", [0.0, 0.2, 0.5, 1.0], G)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()


BEST = dict(CASUAL, name="best", avoid_risk=1.0, future_risk=0.3, placement="next", random_play=0.0,
            attack_free=0.0, nope_defend=1.0, give_worst=True, pair_steal=True, favor_use=True,
            steal_target="most", steal_when=0.2, yup=1.0)


def final(G):
    out = {"best": BEST, "vs_casual": {}, "vs_best": {}, "ablation": []}
    for n in (2, 3, 4, 5):
        r = run(BEST, players=n, games=G)
        m = run(BEST, base=BEST, players=n, games=G)
        out["vs_casual"][n] = {"win": r["test_win_rate"], "ci": r["ci95"], "fair": r["fair_share"]}
        out["vs_best"][n] = {"win": m["test_win_rate"], "seat_win": m["seat_win_rate"]}
        print(f"  {n}p  best vs casual {r['test_win_rate']*100:5.2f}% (fair {100/n:.1f}%)   best mirror {m['test_win_rate']*100:5.2f}%")
    # ablation: remove one habit at a time (4p)
    for k, v in [("placement", "random"), ("random_play", 0.15), ("nope_defend", 0.5), ("give_worst", False),
                 ("future_risk", 2.0), ("pair_steal", False), ("favor_use", False)]:
        r = run(dict(BEST, **{k: v}), games=G)
        out["ablation"].append({"drop": k, "to": v, "win": r["test_win_rate"]})
        print(f"  without {k}={v}: {r['test_win_rate']*100:5.2f}%")
    p = OUT.parent / "final.json"
    p.write_text(json.dumps(out, indent=1))
    print("wrote", p)
