"""Exact optimal play for Shut the Box (dynamic programming over all tile states).

    python3 sims/shutbox/solve.py
Rules: 'any' = knock down any combination of open tiles adding to the roll;
'sumsplit' = the single tile equal to the sum, OR the two dice values as separate tiles.
one_die_rule: roll one die once tiles 7+ are all down.
"""
from functools import lru_cache
from itertools import combinations


def solve(N=9, mode="any", one_die_rule=False):
    tiles = list(range(1, N + 1))

    def moves(mask, roll):
        s = sum(roll)
        out = []
        if mode == "any":
            u = [t for t in tiles if mask >> t & 1]
            for r in range(1, len(u) + 1):
                out += [sum(1 << t for t in c) for c in combinations(u, r) if sum(c) == s]
        else:
            if s <= N and mask >> s & 1:
                out.append(1 << s)
            if len(roll) == 2:
                a, b = roll
                if a != b and mask >> a & 1 and mask >> b & 1:
                    out.append((1 << a) | (1 << b))
        return out

    @lru_cache(None)
    def V(mask):
        if mask == 0:
            return 1.0
        one = one_die_rule and not any(mask >> t & 1 for t in tiles if t >= 7)
        rolls = [((d,), 1 / 6) for d in range(1, 7)] if one else [((a, b), 1 / 36) for a in range(1, 7) for b in range(1, 7)]
        return sum(p * max((V(mask & ~m) for m in moves(mask, r)), default=0.0) for r, p in rolls)

    return V(sum(1 << t for t in tiles))


if __name__ == "__main__":
    for N in (9, 12):
        for mode in ("any", "sumsplit"):
            for one in (False, True):
                print(f"tiles 1-{N:2d} {mode:8s} one-die={one!s:5s}: {solve(N, mode, one) * 100:6.2f}%")
