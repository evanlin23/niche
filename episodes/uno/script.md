# I Tested Every Uno House Rule. One of Them Breaks the Game.

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.
Re-check every number after the big run (data/results.json).

## Number sources (data/results.json, 4 players, normal bots unless noted)
- Round length (turns): official 47.1 (median 42, 1 in 10 rounds > 76); stacking 49.9; mixed stacking 49.7;
  7-0 48.0; jump-in 44.4; draw until you can play 82.3 (median 59, 1 in 10 > 172); forced play 47.1; free +4 50.1;
  everything at once 86.4.
- Rounds with a 10+ card hit: stacking 0.9%, mixed stacking 4.6%, everything 6.0%.
- Player who goes first: official 26.8%, 7-0 25.1%. Fair 25.
- Smart bot vs normal table: official 28.8, 7-0 26.1, free +4 31.2, draw until 29.5.
- Habits (official): hold Wilds 28.8; random Wild color 22.5; switch to best color 26.5; save attacks 25.5;
  challenges 24.6-25.1; bluff 25.1; dump high cards 23.8.
- Cards drawn per round (whole table): official 24.7, draw until 72.9. Everything at once: 86.4 turns, 6.0% rounds with a 10+ hit.
- Two players: first player 51.4%; smart bot official 54.1, 7-0 50.6; draw until 53.1 turns vs 33.9.
- Engine check: opening hand has at least one Wild: math 55.81%, engine 55.84% (10M deals). The first version of
  the check measured hands after the starting card (Draw Two, Shuffle Hands) and was off: true story.
- Official rules: Mattel instruction sheet GDJ85 (112 cards). No stacking; draw one card, may play it.

## Cold open
[o1] Every family plays Uno a little differently.
[o2] Somebody stacks their plus twos. Somebody swaps hands on a seven. Somebody makes you keep drawing until you can play. And somebody always says that's not a real rule.
[o3] So I took every house rule I could find, gave them to bots, and played billions of rounds of Uno.
[o4] One of those rules makes the average round seventy five percent longer. And one round in ten turns into a marathon of more than a hundred and seventy turns.

## The game in ten seconds
[g1] Quick refresher. Match the top card by color or number, or play a Wild. Action cards skip people, reverse direction, or make them draw. First one out of cards wins the round.

## Can you trust it
[c1] My version follows the official rule sheet that comes in the box today. A hundred and twelve cards, including the new Wild Shuffle Hands card and three blank Wilds.
[c2] And here's the first surprise. According to that rule sheet, you can't stack plus twos. And when you can't play, you draw one card. Not until you find one.
[c3] To check the engine, I compared it with plain math. The chance your opening hand has at least one Wild is fifty five point eight percent. Over ten million deals, my engine says the same, to a tenth of a percent.
[c4] Confession. The first time I ran that check, it was off. I had been looking at hands after the first card was flipped, and a Draw Two or a Shuffle Hands had already changed them. So the check caught a bug in the check.
[c5] One limitation. My bots never forget to say Uno, and they never argue about the rules. Hold onto that one.

## Meet the house rules
[r1] Here are the rules I tested, one at a time, against the official game.
[r2] Stacking, where you can answer a plus two with a plus two and pass the pile along. Seven Zero, where a seven swaps hands and a zero rotates everyone's hands. Jump In, where anyone holding the exact same card can play it out of turn.
[r3] Draw until you can play. Forced play, where you have to play if you can. And the free plus four, with no color rule and no challenges.

## The results
[x1] Under the official rules, a round of four players takes about forty seven turns.
[x2] Jump In makes rounds shorter, about six percent. Stacking, Seven Zero and the free plus four each add a few turns. Forced play changes nothing at all, because almost everybody already plays when they can.
[x3] And then there's draw until you can play. Eighty two turns on average. Seventy five percent longer.
[x4] The average isn't even the worst part. With the official rules, one round in ten goes past seventy six turns. With draw until you can play, one in ten goes past a hundred and seventy.
[x5] Here's why. Under the official rules, the table draws about twenty five cards in a round. With draw until you can play, it draws seventy three. Nearly three times as many. Hands grow instead of shrinking, and everyone drifts further from Uno. That's the rule that breaks the game.

## Stacking
[s1] What about stacking? Everyone remembers the round where somebody got hit with sixteen cards.
[s2] It's rarer than it feels. With plus twos stacking on plus twos, only about one round in a hundred has anyone draw ten or more at once. Let plus fours join the stack, and it's still under one in twenty.
[s3] It makes great stories. It barely changes the game.

## Seven Zero
[z1] Seven Zero is the sneaky one.
[z2] Under the official rules, the player who goes first wins almost twenty seven percent of four player rounds. A fair share is twenty five. With Seven Zero, that edge disappears completely.
[z3] It also cuts how much skill matters. My best bot's edge over a normal player shrinks by more than half. My guess is that when your hand can be taken from you, planning ahead stops paying off.

## Everything at once
[a1] Of course, some families play with all of these rules at the same time.
[a2] Stacking, Seven Zero, Jump In, draw until you can play, and the free plus four, all together. Eighty six turns a round on average. And six rounds in a hundred, somebody draws ten or more cards in one go.

## Two players
[t1] If you mostly play one on one, a couple of things change.
[t2] The player who goes first wins fifty one and a half percent of the time. And Seven Zero is even harsher. My best bot goes from fifty four percent to barely over fifty. With two players, Seven Zero just hands your cards to the only other person at the table.

## So can you actually get good at Uno?
[k1] Which raises the uncomfortable question. Can you actually get good at Uno?
[k2] I gave my best bot every habit that helped. Against three normal players, it wins twenty nine percent of rounds. A fair share is twenty five.
[k3] That's a real edge, but it's small. Uno is mostly luck. Which is probably why everyone is willing to play it.

## The habits that help
[h1] Still, if you want those extra four points, almost all of them come from one habit.
[h2] Hold your Wilds. Don't play a Wild while you have another card you can play. That alone takes you from twenty five percent to twenty nine.
[h3] And when you do play a Wild, pick the color you hold the most of. Picking a color at random drops you to twenty two and a half.
[h4] Some things people argue about barely matter. Challenging a plus four, bluffing one, or saving your attack cards for someone close to winning. All within about half a point.
[h5] One that backfires. Dumping your high point cards early feels smart, but it lowers your chance of winning the round.

## The recipe
[w1] So here's the house rule verdict.
[w2] If you want shorter, punchier rounds, add Jump In. If you want chaos stories, add stacking. If you want luck to decide more of the game, add Seven Zero.
[w3] And never, ever play draw until you can play. Unless you really like drawing cards.

## Close
[e1] Remember the one thing my bots never do? Argue about the rules. Which might be the real reason Uno takes forever at your house.
[e2] Next, I'm playing Battleship, to find out where to hide your ships. Tell me where you always put yours.
