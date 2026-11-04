"""Shut the Box: exact solutions + Monte Carlo replay for every rule variant.
    python3 episodes/shut-the-box/experiments.py [--games N per strategy] [--seed S] [--out DIR]"""
import argparse, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "sims" / "shutbox" / "shutbox"
VARIANTS = {"9_any": ["-n", "9", "-mode", "any"], "9_any_onedie": ["-n", "9", "-mode", "any", "-oneDie"],
            "9_sumsplit": ["-n", "9", "-mode", "sumsplit"], "9_sumsplit_onedie": ["-n", "9", "-mode", "sumsplit", "-oneDie"],
            "12_any": ["-n", "12", "-mode", "any"], "12_sumsplit": ["-n", "12", "-mode", "sumsplit"]}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--games", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = Path(a.out) if a.out else Path(__file__).resolve().parent / "data"; out.mkdir(parents=True, exist_ok=True)
    subprocess.run(["go", "build", "-o", str(BIN), "."], cwd=BIN.parent, check=True)
    res = {"games_per_test": a.games, "variants": {}}
    for name, args in VARIANTS.items():
        r = json.loads(subprocess.run([str(BIN), *args, "-games", str(a.games), "-seed", str(a.seed)],
                                      capture_output=True, text=True, check=True).stdout)
        res["variants"][name] = r
        print(name, f"perfect {r['perfect_shut_exact'] * 100:.2f}%", flush=True)
    res["tests"] = len(VARIANTS) * 7
    (out / "results.json").write_text(json.dumps(res, indent=1)); print("wrote", out / "results.json")


if __name__ == "__main__":
    main()
