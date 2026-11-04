"""Merge experiment shards (equal games each, independent seeds) into data/*.json.

    python3 episodes/exploding-kittens/merge_shards.py shards_dir/
Win rates are averaged across shards; CIs are recomputed for the pooled game count.
"""
import json, math, sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def merge(objs, games_total):
    a = objs[0]
    if isinstance(a, dict):
        out = {}
        for k in a:
            if k == "ci" and "win" in a:
                continue
            out[k] = merge([o[k] for o in objs], games_total)
        if "win" in a and "ci" in a:
            p = out["win"]
            out["ci"] = 1.96 * math.sqrt(p * (1 - p) / games_total)
        return out
    if isinstance(a, list):
        return [merge([o[i] for o in objs], games_total) for i in range(len(a))]
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return sum(objs) / len(objs)
    return a


def main(src, dest=None):
    global DATA
    if dest:
        DATA = Path(dest); DATA.mkdir(parents=True, exist_ok=True)
    shards = sorted(d for d in Path(src).glob("*/") if (d / "results.json").exists())
    per = json.loads((shards[0] / "results.json").read_text())["games_per_test"]
    total = per * len(shards)
    counts = {}
    for name in ("results.json", "final.json", "extra.json"):
        objs = [json.loads((s / name).read_text()) for s in shards if (s / name).exists()]
        if len(objs) != len(shards):
            raise SystemExit(f"{name}: only {len(objs)}/{len(shards)} shards")
        m = merge(objs, total)
        if name == "results.json":
            m["games_per_test"] = total
            m["shards"] = len(shards)
        (DATA / name).write_text(json.dumps(m, indent=1))
    r = json.loads((DATA / "results.json").read_text())
    runs = 4 + sum(len(v) for v in r.values() if isinstance(v, list))
    x = json.loads((DATA / "extra.json").read_text())
    extra_runs = sum(len(v) for v in x["2p"].values()) + len(x["myth_shuffle"]) + len(x["myth_pair_noncats"]) + 2 * len(x["tables"]) + 3
    final_runs = 8 + 7
    games = (runs + extra_runs + final_runs) * total
    (DATA / "total_games.json").write_text(json.dumps({"games": games, "per_test": total, "tests": runs + extra_runs + final_runs}, indent=1))
    print(f"merged {len(shards)} shards: {total:,} games per test, {games:,} games total")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
