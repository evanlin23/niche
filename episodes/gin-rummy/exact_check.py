"""Gin rummy engine check by plain counting (no simulation, written separately from the Go engine).

Chance that a 10-card deal from 52 already holds at least one meld (3+ of a rank, or 3+ in a row in one suit,
ace low, no wrap). We count the deals with NO meld rank by rank: at each rank a hand may hold that rank in at
most 2 suits (3 would be a set), and no suit may hold 3 ranks in a row. State = cards so far + current run length
(0, 1 or 2) in each suit.
    python3 episodes/gin-rummy/exact_check.py  -> data/exact_check.json"""
import json
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path


def no_meld_deals(hand=10):
    states = {(0, (0, 0, 0, 0)): 1}
    choices = [()] + [(s,) for s in range(4)] + list(combinations(range(4), 2))
    for _rank in range(13):
        nxt = {}
        for (k, runs), ways in states.items():
            for ch in choices:
                k2 = k + len(ch)
                if k2 > hand:
                    continue
                new = []
                ok = True
                for s in range(4):
                    if s in ch:
                        if runs[s] == 2:
                            ok = False  # would make three in a row in this suit
                            break
                        new.append(runs[s] + 1)
                    else:
                        new.append(0)
                if ok:
                    key = (k2, tuple(new))
                    nxt[key] = nxt.get(key, 0) + ways
        states = nxt
    return sum(w for (k, _), w in states.items() if k == hand)


def main():
    none = no_meld_deals()
    p = 1 - Fraction(none, comb(52, 10))
    out = {"deal_has_meld": float(p), "deal_has_meld_fraction": f"{p.numerator}/{p.denominator}",
           "no_meld_deals": none, "all_deals": comb(52, 10)}
    (Path(__file__).resolve().parent / "data" / "exact_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
