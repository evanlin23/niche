# Sorry!: rules digest used by the simulator

Checked 2026-11-04. Main source: Hasbro's classic Sorry! instructions (item 00390, (c)1934/2003, 4 pawns each):
https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/d0dc3b91-28ec-4f9a-b32b-31306ae2cb17/af23343336930172b83a82fd2897c930.pdf
That sheet says only "deck of cards (no 6s or 9s)". The deck mix and board counts come from two other Hasbro sheets:
- Hasbro Retro Series "Sorry! 1958 Edition", B3218 ((c)2014):
  https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/168f2cc8-37c4-4780-83ac-b5b6c5e2ce3e/B3218CV00_I_Retro_Sorry_ENG_P1_1_FAR.pdf
  "The Pack consists of 44 cards, four each of the denominations: 1, 2, 3, 4, 5, 7, 8, 10, 11, 12 and four Sorry
  cards. (In addition one extra card of the denomination '1' is included ...)". "Margin squares are the 60 squares
  around the edge of the board." "Safety zone is the name given to the 5 Colored squares preceding each home."
- Hasbro Sorry! A5065 ((c)2020), which prints the board and lists "45 Cards":
  https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/4c59d570-cc28-4577-b8b2-21a3e159a534/A5065A440_418895_SORRY_20_INST.pdf

## Components
- 45 cards: five 1s; four each of 2, 3, 4, 5, 7, 8, 10, 11, 12; four Sorry! cards. (44 + the extra 1 = 45, matching
  the "45 cards" printed on modern sheets. The 1958 sheet calls the fifth 1 optional; tested as an edition.)
- 4 pawns per player, 2-4 players.
- Board: 60 track squares. Each side, counted clockwise from the corner: a slide from square 1 to square 4
  (4 squares), the Safety Zone entry at square 2, the Start exit circle at square 4, and a slide from square 9 to
  square 13 (5 squares). Safety Zone: 5 squares, then Home. So a pawn needs 64 forward moves from its Start exit
  to Home. **Not printed as text:** slide lengths and positions were counted on the board diagram printed in the
  A5065 sheet (the classic boards share this layout). On the classic board, each side's slides are that side's colour.

## Classic rules (00390) as simulated
- On your turn draw the top card and move if you can. If you can move you must, even if it hurts you.
  If you can't, you forfeit. Reshuffle the discards when the pack runs out.
- Start a pawn only with a 1 or a 2 (it goes onto your Start exit circle; no extra move). You may not have two of
  your pawns on that circle. An opponent on it is bumped.
- 1: start a pawn or move 1. 2: start a pawn or move 2, **then draw again** (even if you couldn't move).
  3, 5, 8, 12: forward. 4: backward 4. 7: forward 7 or split between two pawns (all 7 must be used; can't start a
  pawn). 10: forward 10 or backward 1. 11: forward 11 or switch one of your pawns with an opponent's (open track
  only); if you can't go forward 11 you may decline to switch. Sorry!: move a pawn from your Start onto any
  opponent's pawn on the track and bump it home to its Start; if you can't, you forfeit.
- Jump over any pawns (they count as squares). Landing on an opponent bumps it back to its Start. You can't land
  on your own pawn.
- Slides: land exactly on the triangle of a slide that isn't your colour and you slide to the end, bumping every
  pawn on the slide, your own too. On your own colour's slide you stay put. Passing over a triangle does nothing.
- Your Safety Zone: only your colour, never entered by a backward move, but you may move backward out of it.
  You can't move forward past your own Safety Zone entry. A backward move can take a pawn behind its entry, so a 4
  played from the Start exit leaves the pawn 2 squares from its Safety Zone ("the shortcut").
- Home needs an exact count. First player with all four pawns Home wins.

## Interpretations (the sheet is silent; said on screen if they matter)
- A Sorry! card that drops your pawn onto a triangle of another colour slides it (the sheet says "regardless of
  which card sent you there, any time you land ... on the triangle ... slide"). Same for an 11 switch (printed).
- After an 11 switch only your pawn can slide; the opponent's pawn simply takes your old square.
- Seats sit in colour order and play passes clockwise; 2 players use opposite colours; 3 players leave one side empty.

## Team rules (official variation, classic 00390 sheet; also "Partnership Games" in the 1958 sheet)
Re-checked 2026-11-06 (pdftotext of the sheets above). "RED is always YELLOW's partner, and GREEN is always BLUE's."
"you may move, or BUMP! your own or your partner's pawn in accordance with the card drawn." "If you land on a space
occupied by a partner's pawn, BUMP it back to its START!" "SORRY! cards must be used. If there's no one else to pick
on, this means you might send your own or your partner's pawn back!" "7 means you may split a move among any or all
eight of your team's pawns" (simulated: between any two of the eight). "If you drew a 1 or 2, you may start or move a
pawn of either partner." "The first partnership to get all eight pawns into their respective HOMEs wins the game."
Simulated as written; an 11 switches only with an opponent. Partners sit opposite (seats 0/2 and 1/3). Two players
who each play two opposite colours and may move either play the same game.

## House rules (not on any sheet; common at home; tested on the skill meter in data/v2.json)
- **Start with one pawn out:** every player begins with one pawn on its Start exit circle.
- **No exact count:** a pawn can reach Home with any card that gets it there (extra steps are wasted). It still
  can't pass its Safety Zone entry.
- **Slide on every slide:** slide on your own colour's slides too. On the classic board your own short slide starts
  one square before your Safety Zone entry, so landing on it sends a pawn past its entry and round again.
- **No slides.**
- The 2020 sheet's slide rule ("land ... on the triangle at the beginning of your color slide, slide ... If you land
  on a slide that isn't your color, don't slide") is NOT tested: on the classic layout that would push every pawn
  past its own Safety Zone entry; the 2020 board's layout can't be read reliably from the printed diagram.

## Edition differences (tested as variants)
- **2020 rules (A5065):** a 2 does **not** draw again (the 2 card text: "Move one of your pawns forward two from
  START or if in play, move forward two spaces", no draw again); a Sorry! card may instead "move forward 4"; and the
  slide rule is reversed (slide on your own colour). We test the first two only (see House rules).
- **1958 pack:** 44 cards, without the fifth 1.
- **"Variation for adults" (00390 sheet):** hold 5 cards, play one per turn, draw back to 5; if none can move, discard
  one and draw. We treat a played 2 as "play again from your refilled hand".
- 2013 edition A5065 (Fire and Ice, 3 pawns) is a different game; not simulated.

## Bots (only see the board and their own card)
- **Normal:** for the card it drew, picks the legal move that maximises its pawns' total progress minus the
  opponents' average progress (moves as far as possible, bumps when it can).
- One-habit variants: random move; spreader (prefers moving back pawns); runner (prefers moving its front pawn,
  values progress near Home more); front pawn always (rule of thumb), or unless a bump is available; careful
  (avoids ending within reach of opponents' next card); safety first; peaceful (ignores opponents); avenger
  (Sorry! always on the opponent's furthest pawn); switcher (11 always swaps with the opponent's furthest pawn);
  never switch; never split a 7; never use the 10 to go back 1; one pawn at a time.
- **Best found:** runner + careful + safety first. In the 5-card variation it also weighs what the card it plays
  would be worth later ("keep" 0.5 x the card's average swing from data/results.json: saves Sorry! cards and 11s).
- Under the Team rules every bot values its team's eight pawns against the other team's.

## Engine check (plain math)
With 45 cards and only the 1s (five) and 2s (four) starting a pawn, the chance that nobody in a 4-player game gets
a pawn out in the first round is 36/45 x 35/44 x 34/43 x 33/42 = 39.535%. The first player gets one out on turn 1
with 9/45 = 20%. The engine plays real first rounds and must match both (data/results.json, engine_check).
