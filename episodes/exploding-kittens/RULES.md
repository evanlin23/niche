# Exploding Kittens (Original Edition): rules digest used by the simulator

Source: official rulebook, Exploding Kittens Original Edition, ©2025 printing (LONS-202504-79):
https://cdn.shopify.com/s/files/1/0345/9180/1483/files/ekoe-instructions-english.pdf
(linked from https://www.explodingkittens.com/pages/rules-kittens). Checked 2026-11-04.

## Deck: 56 cards
| Card | Count | Effect (official wording, condensed) |
|---|---|---|
| Exploding Kitten | 4 | Show immediately; unless you play a Defuse you are out. |
| Defuse | 6 | Play instead of exploding; secretly put the Kitten back anywhere in the Draw Pile. |
| Attack | 4 | End your turn without drawing; next player takes 2 turns. If a victim plays Attack, their current + remaining untaken turns PLUS 2 pass on (victim who completed 1 of 2 turns -> next takes 3). |
| Skip | 4 | End your turn without drawing. Vs an Attack it ends only 1 of the turns. |
| Favor | 4 | Any other player gives you 1 card of THEIR choice. |
| Shuffle | 4 | Shuffle the Draw Pile. |
| See the Future | 5 | Privately view top 3 cards, put back in same order. |
| Nope | 5 | Stop any action except Exploding Kitten / Defuse, any time, even on others' turns; Nope a Nope = Yup. Noped cards are lost. |
| Cat cards | 20 (5 kinds x 4) | Powerless alone; matching pair steals a random card from any player. |

Special combos: ANY two cards with the same title = pair (steal random card from a player);
three of a kind = name a card, take it if the target has it.

## Setup
1. Remove 4 Kittens and 6 Defuses. Deal 1 Defuse to each player.
2. Shuffle 2 extra Defuses back into the deck (only 1 in a 5-player game); remove the rest.
3. Deal 7 cards to each player (hand = 8 with the Defuse).
4. Insert (players - 1) Kittens; remove extras. Shuffle. First player chosen; clockwise.
(Optional "faster game" variant for 2-3 players: remove about one third of the deck before
inserting Kittens. Not used unless stated.)

## Turn
Play any number of cards (or none), then draw from the top to end the turn (unless a card ended it).
No hand limit. Last player alive wins.

## Simulator assumptions (said out loud in the video)
- Nope windows: after each Nope-able action, the affected player (target / attacked player) may
  Nope; the actor may Nope back, alternating. Other players only Nope a Skip/Shuffle when their own
  policy says so. (Real tables have more free-for-all Noping.)
- Bots track only public information + what they saw themselves (See the Future, own Kitten
  placement, cards given/stolen to/from them). No cheating.
