"""Checkers engine checks from plain counting, written separately from the Go engine (board as (row, col)).

1. perft: the number of distinct move sequences from the start position, 1..7 plies (published values for
   American checkers: 7, 49, 302, 1469, 7361, 36768, 179740).
2. If both players pick uniformly at random among their legal moves, the exact chance that a jump happens in
   the first 6 plies (3 moves each): sum over every game prefix of its probability.
    python3 episodes/checkers/exact_check.py   -> data/exact_check.json"""
import json
from fractions import Fraction
from pathlib import Path

PUBLISHED = [7, 49, 302, 1469, 7361, 36768, 179740]


def start():
    red = {(r, c) for r in range(3) for c in range(8) if (r + c) % 2 == 0}
    white = {(r, c) for r in range(5, 8) for c in range(8) if (r + c) % 2 == 0}
    return (frozenset(red), frozenset(white), frozenset(), 0)


def moves(pos):
    red, white, kings, side = pos
    me, opp = (red, white) if side == 0 else (white, red)
    occ = red | white
    fwd = 1 if side == 0 else -1
    out = []

    def dirs(sq):
        return [(1, -1), (1, 1), (-1, -1), (-1, 1)] if sq in kings else [(fwd, -1), (fwd, 1)]

    def jumps(start_sq, at, king, captured, path_occ):
        found = False
        ds = [(1, -1), (1, 1), (-1, -1), (-1, 1)] if king else [(fwd, -1), (fwd, 1)]
        for dr, dc in ds:
            o = (at[0] + dr, at[1] + dc)
            l = (at[0] + 2 * dr, at[1] + 2 * dc)
            if not (0 <= l[0] < 8 and 0 <= l[1] < 8):
                continue
            if o in opp and o not in captured and l not in path_occ:
                found = True
                cap = captured | {o}
                if not king and l[0] == (7 if side == 0 else 0):
                    out_caps.add((start_sq, l, frozenset(cap)))
                    continue
                jumps(start_sq, l, king, cap, path_occ)
        if not found and captured:
            out_caps.add((start_sq, at, frozenset(captured)))

    out_caps = set()
    for s in me:
        jumps(s, s, s in kings, frozenset(), occ - {s})
    if out_caps:
        return [("jump", a, b, c) for a, b, c in out_caps]
    for s in me:
        for dr, dc in dirs(s):
            t = (s[0] + dr, s[1] + dc)
            if 0 <= t[0] < 8 and 0 <= t[1] < 8 and t not in occ:
                out.append(("step", s, t, frozenset()))
    return out


def apply(pos, m):
    red, white, kings, side = pos
    _, a, b, cap = m
    me, opp = (set(red), set(white)) if side == 0 else (set(white), set(red))
    k = set(kings)
    me.discard(a); me.add(b)
    opp -= cap
    k -= cap
    if a in k:
        k.discard(a); k.add(b)
    elif b[0] == (7 if side == 0 else 0):
        k.add(b)
    nr, nw = (me, opp) if side == 0 else (opp, me)
    return (frozenset(nr), frozenset(nw), frozenset(k), 1 - side)


def perft(pos, d):
    if d == 0:
        return 1
    return sum(perft(apply(pos, m), d - 1) for m in moves(pos))


def p_jump_within(pos, plies):
    """Probability that a jump is played within `plies` plies when every legal move is equally likely."""
    if plies == 0:
        return Fraction(0)
    ms = moves(pos)
    if not ms:
        return Fraction(0)
    if ms[0][0] == "jump":  # jumps are compulsory, so a jump happens now
        return Fraction(1)
    return sum(p_jump_within(apply(pos, m), plies - 1) for m in ms) / len(ms)


def main():
    s = start()
    pf = [perft(s, d) for d in range(1, 8)]
    pj = p_jump_within(s, 6)
    out = {"perft": pf, "perft_published": PUBLISHED, "perft_matches_published": pf == PUBLISHED,
           "capture_within_6_plies": float(pj), "capture_within_6_plies_fraction": f"{pj.numerator}/{pj.denominator}"}
    dst = Path(__file__).resolve().parent / "data" / "exact_check.json"
    dst.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
