# Gin Rummy: rules digest used by the simulator

Checked 2026-11-04. Source: Bicycle (US Playing Card Company), "Gin Rummy": https://bicyclecards.com/how-to-play/gin-rummy
Comparison reference (fan site, used only for what Bicycle leaves out and for common variants):
https://www.pagat.com/rummy/ginrummy.html

## Rules as simulated (Bicycle)
- 2 players, one 52-card deck, no jokers. Ace low (A-2-3 is a run, Q-K-A is not). Card values: ace 1, 2-10 face
  value, J/Q/K 10.
- Deal 10 cards each; the next card is turned up to start the discard pile.
- The non-dealer may take the upcard (and discard); if they pass, the dealer may take it; if both pass, the
  non-dealer draws from the stock. After that: draw from the stock or the discard pile, then discard. You may not
  discard the card you just picked up from the discard pile.
- Melds: 3 or 4 of a rank, or 3+ cards in a row of one suit. A card counts in one meld only. Unmatched cards are
  deadwood.
- Knock: discard, then show your hand, if your deadwood is 10 or less. Gin: no deadwood. Knocking is optional.
- After a knock or Gin, the opponent shows their hand and may lay off deadwood cards on the knocker's melds.
  Bicycle's wording allows this against Gin too; we follow Bicycle and test "no layoffs on Gin" as a variant.
- Scoring a hand: Gin = 20 + the opponent's deadwood. Knock and win = the difference in deadwood. If the
  opponent's deadwood is equal or lower (an undercut), the opponent scores 10 + the difference.
- Game: first to 100 points. Bonuses (100 for the game, 20 per hand won, 100 for a shutout) change the final
  score but not who won, so the simulator records the game winner. The winner of a hand deals the next one.

## Not in the Bicycle text (our choices, said on screen if they matter)
- If the stock is down to two cards and nobody has knocked, the hand is void and redealt by the same dealer (the
  standard rule; Pagat).
- The defender arranges their own melds first, then lays off (the way most players do it).

## Variants tested
- No layoffs against Gin (Pagat's rule).
- 25-point Gin bonus and 25-point undercut bonus (Pagat lists 25 as a common alternative to 20/10).

## Bots (see only their own hand, the discard pile, and what the opponent picked up or threw away)
- **Normal:** takes the discard only if it goes straight into a meld; otherwise draws blind. Throws the card that
  leaves the least deadwood (ties: the card with the fewest partners in hand). **Knocks the moment it can.**
- Knock thresholds: knock only at 8 or less, 6, 4, 2, or only with Gin; and two "go for Gin, then knock late"
  rules.
- Habits: picks up any discard that lowers deadwood; never takes the discard; dumps high cards first; watches the
  opponent's pickups; random discards.

## Engine check (plain counting)
The chance that a 10-card deal already holds at least one meld, counted exactly (exact_check.py):
1,573,725,206 / 3,955,006,055 = 39.791%. The engine deals hands and runs its meld finder; it must match.
