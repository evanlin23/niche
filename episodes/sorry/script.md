# I Played a Billion Games of Sorry! Your Family Is Moving the Wrong Pawn

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.
Big run: 1,006,250,000 games (GitHub Actions run 41872745692, 20 shards x 28.75 tests x 1.75M games; the three
5-card-variation tests ran a quarter of the games). Claims say "over a billion" (not "billions").

## Number sources (data/results.json unless noted; classic Hasbro rules, 4 players, three Normal opponents)
- Fair share 25%. Best bot (runner + careful + safety first) 33.78%; random mover 4.90%; worst habit (spreader) 8.93%.
- Habits (key in data/results.json "habits"): runner 32.33; front pawn unless a bump 28.82; front pawn always 24.18;
  safety first 27.95; careful 27.24; never back 1 with a ten 24.94; one pawn at a time 24.74; never split a seven 23.72;
  peaceful 23.37; avenger (Sorry! on the leader's furthest pawn) 19.89; never switch 19.23; switcher (eleven always swaps
  with the leader's furthest pawn) 13.88; spreader 8.93.
- Luck: Normal at a table of random movers 64.33; best at a table of random movers 72.96 (fair 25).
- Engine check ("engine_check"): nobody gets a pawn out in round one, math 36x35x34x33 / 45x44x43x42 = 39.535%,
  engine 39.551% (35M first rounds); first player out on turn one, math 20.000%, engine 19.993%.
- Card values ("mirror" -> "4p" -> "card_swing", net squares of progress per draw: own gain plus opponents' average loss):
  Sorry! 40.2, eleven 10.4, twelve 6.0, ten 4.9, seven 4.6, eight 4.2, four 3.8, five 3.3, two 2.7 (before its extra
  draw), three 2.3, one 2.0. Twelves can't be used 56.7% of the time ("card_forfeit"). Game length 287.6 turns = 72 each.
- Going first, 4 players: 24.91%; 2 players: 50.00% (no real edge).
- Mirror check: 4 Normal players 24.92-25.08% per seat (more than noise at 35M games: exact ties were broken by board
  order; with random tie-breaks 24.99-25.01%, data/supplementary_mirror_randtie.json); 4 best bots 24.99-25.02%;
  2 players 49.98/50.02. Habit tests rotate the test bot through every seat, so the tie effect averages out.
- Three players ("mirror" -> "3p"): the seat whose side runs into the empty side wins 39.84%, the others 30.06 and 30.10.
  Same games with no bumping at all ("3p_no_interaction"): 33.23-33.50%. The colour rotation check (any three colours,
  same result) was run locally during development: always the colour just before the empty side, about 40%.
- Player count ("players"): best vs Normal, 2 players 55.20% (fair 50); 3 players 42.48% (fair 33.3).
- Editions ("editions"): 2020 rules (two doesn't draw again; Sorry! may move four instead) best 32.17%, random 4.03%;
  1958 44-card pack best 33.33%; 5-card adult variation best 31.73% (8.75M games).
- Fully random player in the 5-card variation: 0.074% (data/supplementary_hand5_random.json, 4M games, local run after
  the big run; the big run's "hand5_random" used a half-random bot and is not quoted).
- Explanations marked "my guess" are not tested.

## Cold open
[o1] Everybody plays Sorry! a little differently.
[o2] Your little brother always moves whichever pawn is furthest behind. Your aunt swaps with the leader every time she draws an eleven. And your uncle saves every Sorry! card for whoever's winning.
[o3] So I turned those habits into bots, gave them Hasbro's official rules, and had them play over a billion games.
[o4] Here's the headline. At a table of four, a fair share is one game in four. The best bot won a third of its games. The worst habit won one in eleven.
[o5] Sorry! is supposed to be pure luck. It isn't. It comes down to a few mistakes, and you're probably making at least one of them.

## The game in ten seconds
[g1] Quick rules. Draw a card, move a pawn. Get all four pawns from your Start to your Home. Land on someone and they go back to their Start. Sorry.

## Can you trust it
[c1] My version follows Hasbro's classic rules. Forty five cards, no sixes and no nines. Only a one or a two gets you out of Start, and a two lets you draw again.
[c2] Slides, the seven you can split, the eleven that swaps, the four that moves you backwards. All in there, square for square.
[c3] To check the engine, I used plain math. With four players, nobody gets a pawn out in the first round if the first four cards are all useless.
[c4] On paper that happens thirty nine point five four percent of the time. Over thirty five million first rounds, my engine says thirty nine point five five.
[c5] One thing my bots don't do is hold a grudge. They never gang up on the leader on purpose. Keep that in mind. I'll come back to it at the end.

## Meet the players
[p1] Here's the table.
[p2] The Normal player always makes the move that gets it furthest, and bumps people whenever it can.
[p3] The Spreader moves whichever pawn is furthest behind. The Runner does the opposite, and pushes its front pawn home first.
[p4] The Switcher swaps with the leader on every eleven. The Avenger always aims its Sorry! card at the leader's best pawn.
[p5] And the Careful player won't stop right in front of an opponent if it can help it.

## The ranking
[r1] Here's how each one did against three Normal players. One in four is a fair share, so twenty five percent is the number to beat.
[r2] At the bottom, a bot that moves completely at random wins about one game in twenty. So no, it's not all luck.
[r3] The Spreader wins nine percent. The Switcher, fourteen. The Avenger, twenty.
[r4] The Careful player beats the table with twenty seven percent. The Runner wins thirty two.
[r5] But a ranking doesn't tell you why. So let's take the habits one at a time.

## Mistake one: spreading out
[m1] Mistake one is spreading your pawns around the board. It feels safe. It's the worst habit I tested, apart from playing at random.
[m2] My guess is that every pawn on the track is a target, and a pawn that's halfway around costs you a lot when it gets sent home.
[m3] The Runner does the opposite. It mostly pushes its front pawn, gets it into the Safety Zone, and then moves on to the next one. That habit alone wins thirty two percent.
[m4] If you want one rule to remember, try this. Move your front pawn, unless you can bump someone. That simple rule wins twenty nine percent.
[m5] And it needs that exception. Always moving the front pawn, even when a bump is sitting right there, wins only twenty four. Worse than doing nothing special.

## Mistake two: the eleven
[e1] Mistake two is the eleven.
[e2] Swapping with the leader every single time feels like justice. It wins fourteen percent. My guess is that a lot of those swaps send your own pawn backwards.
[e3] But never swapping is a mistake too. That wins nineteen percent.
[e4] The Normal player swaps only when the swap beats just moving eleven. That's the whole trick.

## Mistake three: the Sorry! card
[s1] Mistake three. Aiming every Sorry! card at the leader's best pawn wins twenty percent.
[s2] When you play a Sorry!, your pawn lands where theirs was. My guess is that where you land matters as much as who you hit. The Normal player picks the spot that's best for both.
[s3] If this is already changing how you play, subscribe. There are more games coming.

## The cards
[k1] Speaking of the Sorry! card, here's what every card is worth. I measured how far each one moves the race, counting your progress and what it costs your opponents.
[k2] The Sorry! card is worth almost four times an eleven. Nothing else comes close.
[k3] And here's my favorite. The four, the card that moves you backwards, is worth more than the five.
[k4] Back up four squares from your Start circle and you're two squares from the entrance to your Safety Zone. You just skipped almost the whole board.
[k5] The twelve sounds great, but more than half the time you can't use it at all.

## The aside
[a1] One true story from making this. My first fairness test failed.
[a2] With three players, one seat won forty percent of the time instead of a third. I assumed it was a bug in my code.
[a3] It wasn't. With three players one side of the board is empty. The player whose pawns run into that empty side first wins forty percent. The other two win thirty each.
[a4] When I switched off bumping completely, the three seats evened out. So it comes from the bumping, not from the code.
[a5] So if you play with three, pick the color whose side comes just before the empty side, going the way the pawns move.

## Your edition
[d1] One more thing. Check the year on your box.
[d2] In the newer rules, a two doesn't let you draw again, and a Sorry! card can move you forward four instead. The best bot still wins thirty two percent there.
[d3] And there's a variation for adults on the classic instructions. Hold five cards and choose which one to play.
[d4] That's where skill really shows. A player who picks cards at random wins less than one game in a thousand.

## The recipe
[w1] So here's what over a billion games of Sorry! say.
[w2] Push your front pawn home first, unless you can bump someone.
[w3] Don't stop right in front of an opponent if you have a choice, and get into your Safety Zone whenever you can.
[w4] Swap with an eleven only when it moves you forward. And play your Sorry! where it puts you furthest along.
[w5] Do all of that and the best bot wins a third of its games at a table of four, against players who already play pretty well.

## Close
[x1] Remember, my bots never hold a grudge. Whether your family gangs up on the leader is still up to you.
[x2] So who gets your Sorry! card, the leader or the person who just bumped you? Tell me in the comments.
