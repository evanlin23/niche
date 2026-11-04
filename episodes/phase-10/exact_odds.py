"""Exact chance that a 10-card Phase 10 deal already holds each Phase (plain combinatorics, no simulation).

    python3 episodes/phase-10/exact_odds.py      -> data/exact_deal.json

Deck (Mattel HHR41): numbers 1-12, 8 of each (2 per colour x 4 colours), 8 Wild, 4 Skip = 108 cards.
We sum over every possible count of each number in the hand, weight it by the number of ways to pick those
cards, and ask whether the Phase can be built (Wilds fill gaps, Skips never help, at least one numbered card).
Written separately from the Go engine on purpose, so the two can check each other."""
import json
from math import comb

import numpy as np
from pathlib import Path

HAND = 10
TOTAL = comb(108, HAND)
PH = {1: ("sets", 3, 3), 2: ("setrun", 3, 4), 3: ("setrun", 4, 4), 4: ("run", 7), 5: ("run", 8), 6: ("run", 9),
      7: ("sets", 4, 4), 9: ("sets", 5, 2), 10: ("sets", 5, 3)}


def number_vectors():
    """Every way to hold k <= 10 numbered cards: counts per number (each 0..8), as one numpy array."""
    rows, weights = [], []
    c = [0] * 12
    def rec(i, left, w):
        if i == 12:
            rows.append(tuple(c)); weights.append(w)
            return
        for x in range(0, min(8, left) + 1):
            c[i] = x
            rec(i + 1, left - x, w * comb(8, x))
        c[i] = 0
    rec(0, HAND, 1)
    return np.array(rows, dtype=np.int64), weights


def missing_sets(C, A, B):
    """Fewest cards still missing for two sets (sizes A and B), trying every pair of numbers, same number allowed."""
    best = np.full(len(C), 99)
    for a in range(12):
        best = np.minimum(best, np.maximum(0, A + B - C[:, a]))  # both sets from the same number
        for b in range(12):
            if a != b:
                best = np.minimum(best, np.maximum(0, A - C[:, a]) + np.maximum(0, B - C[:, b]))
    return best


def missing_run(C, L):
    best = np.full(len(C), 99)
    for s in range(0, 12 - L + 1):
        best = np.minimum(best, (C[:, s:s + L] == 0).sum(axis=1))
    return best


def missing_setrun(C, A, L):
    """Set of A + run of L: try every set number a and every run window; a card can't be in both."""
    best = np.full(len(C), 99)
    for s in range(0, 12 - L + 1):
        for a in range(12):
            in_window = s <= a < s + L
            gaps_other = sum((C[:, x] == 0).astype(np.int64) for x in range(s, s + L) if x != a)
            if in_window:
                # the run uses a real a (if there is one) and the set takes what is left, or a Wild plays the a
                has = C[:, a] > 0
                use_real = gaps_other + np.maximum(0, A - (C[:, a] - 1))
                use_wild = gaps_other + 1 + np.maximum(0, A - C[:, a])
                m = np.where(has, np.minimum(use_real, use_wild), use_wild)
            else:
                m = gaps_other + np.maximum(0, A - C[:, a])
            best = np.minimum(best, m)
    return best


def main():
    C, weights = number_vectors()
    k = C.sum(axis=1)
    r = HAND - k  # cards in hand that are Wild or Skip
    p = {}
    for ph, d in PH.items():
        if d[0] == "sets":
            m = missing_sets(C, d[1], d[2])
        elif d[0] == "run":
            m = missing_run(C, d[1])
        else:
            m = missing_setrun(C, d[1], d[2])
        tot = 0
        for i in range(len(C)):
            if k[i] == 0 or m[i] > r[i]:
                continue  # no numbered card, or not enough Wild/Skip slots to cover the gaps
            ri = int(r[i])
            tot += weights[i] * sum(comb(8, ww) * comb(4, ri - ww) for ww in range(int(m[i]), min(8, ri) + 1) if ri - ww <= 4)
        p[ph] = tot
    # Phase 8: seven cards of one colour (24 numbered cards per colour)
    p8 = 0
    for c1 in range(HAND + 1):
        for c2 in range(HAND + 1 - c1):
            for c3 in range(HAND + 1 - c1 - c2):
                for c4 in range(HAND + 1 - c1 - c2 - c3):
                    k = c1 + c2 + c3 + c4
                    top = max(c1, c2, c3, c4)
                    if top == 0:
                        continue
                    r = HAND - k
                    w = comb(24, c1) * comb(24, c2) * comb(24, c3) * comb(24, c4)
                    for ww in range(max(0, 7 - top), min(8, r) + 1):
                        if r - ww <= 4:
                            p8 += w * comb(8, ww) * comb(4, r - ww)
    p[8] = p8
    out = {"hand": HAND, "deck": 108, "deal_complete_exact": [p[k] / TOTAL for k in range(1, 11)]}
    dst = Path(__file__).resolve().parent / "data" / "exact_deal.json"
    dst.write_text(json.dumps(out, indent=1))
    for k in range(1, 11):
        print(f"phase {k:2d}: {100 * p[k] / TOTAL:7.3f}%")


if __name__ == "__main__":
    main()
