"""Generic shard merge: average every numeric leaf of each JSON file across shards (equal games per shard).
    python -m pipeline.merge_shards shards_dir/ out_dir/"""
import json, sys
from pathlib import Path


def merge(objs):
    a = objs[0]
    if isinstance(a, dict):
        return {k: merge([o[k] for o in objs]) for k in a}
    if isinstance(a, list):
        return [merge([o[i] for o in objs]) for i in range(len(a))]
    if isinstance(a, (int, float)) and not isinstance(a, bool):
        return sum(objs) / len(objs)
    return a


def main(src, dst):
    shards = sorted(d for d in Path(src).glob("*/") if any(d.glob("*.json")))
    dst = Path(dst); dst.mkdir(parents=True, exist_ok=True)
    for f in sorted({p.name for s in shards for p in s.glob("*.json")}):
        objs = [json.loads((s / f).read_text()) for s in shards if (s / f).exists()]
        m = merge(objs)
        if isinstance(m, dict) and "games_per_test" in m:
            m["games_per_test"] = int(round(m["games_per_test"] * len(objs)))
            m["shards"] = len(objs)
        (dst / f).write_text(json.dumps(m, indent=1))
    print(f"merged {len(shards)} shards into {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
