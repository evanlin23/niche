"""Merge gin rummy shards (independent seeds, equal games each): average every rate, sum the game counts,
recompute 95% intervals for the pooled games.
    python3 episodes/sorry/merge_shards.py shards_dir/ [out_dir]"""
import json, math, sys
from pathlib import Path

COUNT_KEYS = {"games", "hands", "total_games", "total_hands", "games_per_test"}


def merge(objs):
    a = objs[0]
    if isinstance(a, dict):
        m = {}
        for k in a:
            vals = [o[k] for o in objs]
            if k in COUNT_KEYS and all(isinstance(v, (int, float)) for v in vals):
                m[k] = int(sum(vals))
            elif k == "seed":
                m[k] = [o[k] for o in objs]
            else:
                m[k] = merge(vals)
        if "a_win" in m and "games" in m:
            p = m["a_win"]
            m["ci95"] = 1.96 * math.sqrt(p * (1 - p) / m["games"])
        return m
    if isinstance(a, list):
        return [merge([o[i] for o in objs]) for i in range(len(a))]
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return sum(objs) / len(objs)
    return a


def main(src, dst=None):
    dst = Path(dst) if dst else Path(__file__).resolve().parent / "data"
    dst.mkdir(parents=True, exist_ok=True)
    shards = sorted(d for d in Path(src).glob("*/") if (d / "results.json").exists())
    objs = [json.loads((d / "results.json").read_text()) for d in shards]
    m = merge(objs)
    m["shards"] = len(objs)
    # the engine check's exact math is the same in every shard; keep it exact, not averaged
    m["engine_check"]["math"] = objs[0]["engine_check"]["math"]
    (dst / "results.json").write_text(json.dumps(m, indent=1))
    print(f"merged {len(objs)} shards: {m['total_games']:,} games ({m['total_hands']:,} hands), {m['games_per_test']:,} per test")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
