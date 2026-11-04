# UNO: rules digest used by the simulator

Source: official Mattel instruction sheet, UNO GDJ85 (112-card edition):
https://service.mattel.com/instruction_sheets/GDJ85-Eng.pdf (checked 2026-11-04).

## Deck: 112 cards
- 19 per colour (blue, green, red, yellow): one 0, two each of 1–9 (76 total)
- 8 Draw Two, 8 Reverse, 8 Skip (2 per colour)
- 4 Wild, 4 Wild Draw Four, 1 Wild Shuffle Hands, 3 Wild Customizable (blank house-rule wilds)

## Official rules (the baseline)
- Deal 7 each; flip the top card to start the discard pile (action cards at the start apply; a Wild Draw 4
  is returned to the deck).
- On your turn: match colour, number or symbol, or play a Wild. Otherwise draw ONE card; if it's playable you
  may play it immediately. You may also choose not to play a playable card and draw instead.
- Draw Two: next player draws 2 and misses their turn. **No stacking** (it's played "on a matching colour or on
  another Draw Two" by the player whose turn it is; the victim just draws).
- Reverse: direction flips (with 2 players it acts like a Skip, standard interpretation).
- Skip: next player loses their turn.
- Wild: choose the colour. Can be played even if you have another playable card.
- Wild Draw 4: choose colour, next player draws 4 and loses their turn. **Only legal if you have no card of the
  colour on the discard pile.** The victim may challenge: guilty player draws 4 instead; if innocent, the
  challenger draws 6.
- Wild Shuffle Hands: all hands collected, shuffled, dealt back starting left of the player; then choose colour.
- Wild Customizable: write any house rule (simulator treats them as plain Wilds unless a variant says otherwise).
- Say "UNO" at one card (simulator assumes everyone always does).
- Round ends when someone empties their hand; they score opponents' cards (numbers face value; Draw Two,
  Reverse, Skip 20; Wilds 50). First to 500 wins the game. Empty draw pile -> reshuffle the discard pile.

## House rules tested (variants, one at a time)
- Stacking: Draw Two on Draw Two / Wild Draw 4 on Wild Draw 4, penalties add up.
- 7-0: playing a 7 swaps hands with a chosen player; playing a 0 rotates all hands.
- Jump-in: an identical card (colour + number) can be played out of turn.
- Draw until you can play (instead of drawing one).
- Forced play: must play if you can.
- Free Wild Draw 4 (no colour restriction, no challenges).
