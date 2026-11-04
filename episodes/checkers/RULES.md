# Checkers (American / English draughts): rules digest used by the simulator

Checked 2026-11-04.
- WCDF Rules of Draughts (adopted by the American Checker Federation): https://wcdf.net/rules/rules_of_checkers_english.pdf
  (same text as the ACF's download https://www.usacheckers.com/downloads/WCDF_Revised_Rules.doc).
- Hasbro Star Wars 3D Checkers B7718 ((c)2015), a mass-market US instruction sheet:
  https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/9f2031f8-db2b-4af0-90d2-bc8aa2c66478/B77180000%20SW%20Checkers%20INST.pdf
  ("you **must** jump ... You must continue to jump until there are no more jumps available").

## Rules as simulated (WCDF)
- 8x8 board, 32 playing squares; each player has a playing square on their near left (1.4). 12 men each on the
  first three rows (1.11). The darker side (Red/Black) moves first (1.13).
- Men move one square diagonally forward; kings one square diagonally forward or backward (1.15, 1.17).
- A jump goes over an adjacent opponent piece to the empty square beyond (1.18). **Jumps are compulsory**;
  with several, you may choose any (no rule to take the most); a multiple jump must be completed (1.20).
  A piece can only be jumped once in a sequence; captured pieces come off at the end (1.19, 1.20).
- A man reaching the far row becomes a king and the move ends, even mid-jump (1.16, 1.19).
- Win: the opponent has no legal move (no pieces, or all blocked) (1.30).
- Draw: the same position for the third time (1.32.1), or 40 moves by each player with no man advanced and no
  capture (1.32.2). A hard stop at 400 plies (200 moves each) counts as a draw; it practically never triggers.
- Not simulated: touch-move, clocks, the "ballot" openings used in tournaments (games start from the normal
  starting position).

## House rules tested
- **Optional jumps:** you may decline a jump.
- **Huffing** (an old rule, dropped from official play): jumps are optional, but if you skip one, your opponent
  removes ("huffs") a piece that could have jumped (a king if one could), then moves. Our bots always huff and
  know their opponent will.

## Bots (perfect information: both see the whole board)
- **Random:** any legal move.
- **Casual:** tries each of its moves and plays out every forced jump that follows, then counts material
  (man 100, king 130); ties broken at random.
- **Club:** also considers the opponent's best reply (2 plies + forced jumps).
- **Thinker:** 4 plies + forced jumps (slow, so tested on fewer games).
- One-habit variants of Casual (and two of Club): keep the back row, take the centre, hug the edges, rush men
  forward, trade when ahead, value kings higher (200) or lower (100).

## Engine checks (plain counting)
1. perft: the number of distinct move sequences from the start must match the published values for American
   checkers (7, 49, 302, 1469, 7361, 36768, 179740, 845931, 3963680, 18391564); an independent Python move
   generator (exact_check.py) reproduces the first seven.
2. If both sides move uniformly at random, the exact chance that a jump is played within the first 6 plies is
   54420409/64538880 = 84.322% (summing over every possible opening); the engine must match it.
