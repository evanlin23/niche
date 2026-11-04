# I Simulated 10 Billion Games of Exploding Kittens. Here's How to Win.

Narrated lines are `[id] text`. Everything else is notes. Style: docs/script-style-guide.md.
Structure follows docs/perfectplay-structure-notes.md (beats only, our own words and data).

## Number sources (data/*.json). Re-check every number after the 10-billion-game merge.
- Ranking, 5 bots, random seats (ranking-5p.json): Patient 35.4, Normal 21.9, Gambler 17.0, Panicker 14.2, Hoarder 11.5. Fair 20.
- Engine check: first card drawn is a Kitten, 4 players. Math 3/23 = 13.04%. Sim (10M shuffles) 13.07%.
- One-habit tests vs three Normal Players (results.json): random play 0 -> 30.4, normal 25.05, half -> 14.5.
  Panic-dodge at 1 in 4 -> 16.1, at a coin flip -> 22.7, only when sure -> 25.05. Attack vs Skip first 15.9 vs 16.1.
  See the Future never 22.5, immediately 22.3, at 1 in 3 25.05. Placement next 30.2, top 29.3, random 25.05, bottom 23.7.
  Give worst card 27.9. Nope never 21.2, always 26.9. Shuffle if Kitten on top: +0.8. Pairing action cards 20.1.
- Patient One (best bot) vs normal table (final.json): 2p 59.5, 3p 51.1, 4p 40.6, 5p 29.5. All four Patient: 25.0 each.
  Ablation: no pair steals 32.5, no Favors 34.0.
- Seats (all normal): 2p first 52.4. 5p first 19.6, last 20.5. Two player: patience 68.5.
- Tables (extra.json): vs aggressive 53.2, vs hoarders 50.2.
- Kitten odds over a game (traced games): first draw ~1 in 7, last draws mostly Kittens.
- Rulebook: "save your cards early in the game while your chance of exploding is low."
- f4 rule: future_risk 0.3 = Kittens/cards >= 0.3, i.e. about 3.3 cards per Kitten or fewer (2 Kittens -> 6-7 cards).
- Added lines (second recording): explosions under Attack (extra.json): 4p normal table 22.8% (almost 1 in 4),
  2p 38.2% (almost 2 in 5), table of 4 Patient Ones 7.4% (about 1 in 13). Game length: normal 4p 32.4 turns,
  4 Patient Ones 25.0. Two players vs a normal bot (fair 50): whim half the time 18.7, no pair steals 37.1,
  See the Future right away 41.3 (-8.7), never play for fun 68.4. Final: 2p 59.6%, 5p 29.5% (fair 20).
  Rules lines g2-g4: official rulebook (turn = play any number of cards, then draw; Kittens = players - 1).
- Aside is true: an earlier draft explained the bottom-of-deck result with an untested reason; it was cut.

## Cold open
[o1] Every Exploding Kittens table has the same people.
[o2] The one who plays every card the second it lands in their hand. The one who Skips as soon as the deck starts to feel dangerous. And the one who never steals anything, because stealing feels rude.
[o3] So I turned them into bots, sat them at the same table, and had them play Exploding Kittens more than ten billion times.
[o4] The best of them won thirty five percent of its games. The worst won eleven and a half.
[o5] And the gap wasn't luck, or some secret combo. It came down to five mistakes, and most tables make every one of them.

## The game in thirty seconds
[g1] If you've never played: everyone draws from one deck, and whoever draws an Exploding Kitten is out, unless they have a Defuse. Every other card helps you avoid drawing, or makes somebody else draw. Last player standing wins.
[g4] There's always one Kitten fewer than there are players, so exactly one person survives.
[g2] On your turn, you can play as many cards as you like. Then you end your turn by drawing one card. That draw is where people explode.
[g3] Skip ends your turn without drawing. Attack does the same, and the next player has to take two turns. See the Future shows you the top three cards. Shuffle mixes the deck. Favor makes someone give you a card of their choice. Two matching cat cards steal a random card from anyone. And a Nope cancels almost anything.

## Can you trust it
[c1] First, the game. My version follows the official rulebook for the original edition. Fifty six cards, four Kittens, six Defuses, Attacks that stack, and Nopes that cancel other Nopes.
[c2] Before trusting it with strategy, I checked something boring. With four players, the chance that the very first card anyone draws is a Kitten is three in twenty three. That's thirteen point oh four percent.
[c3] Across ten million shuffles, my deck said thirteen point oh seven. Close enough.
[c4] The bots only know what a real player knows. Their own hand, whatever they saw with See the Future, and where they hid a Kitten.
[c5] There is only one thing they can't do, though. They can't lie. Real players bluff about where they put the Kitten. Mine just put it there. Keep that in mind, because I'll come back to it.

## Meet the bots
[b1] Here's who's at the table.
[b2] The Normal Player plays like most people. It dodges when it knows a Kitten is coming, it hides Kittens at random, and now and then it plays a card just because it's fun.
[b3] The Gambler plays cards on a whim, half the time. The Panicker Skips as soon as one card in four could be a Kitten. The Hoarder never steals and never peeks.
[b4] And then there's the Patient One. I'll get back to what it does.
[b5] One table, seats shuffled every game. The Patient One won thirty five percent. The Normal Player, twenty two. The Gambler, seventeen. The Panicker, fourteen. And the Hoarder, eleven and a half. A fair share is twenty.
[b6] But a ranking doesn't tell you why. So I switched to a cleaner test. Three Normal Players, plus one test bot that changes a single habit. One hundred million games for each change. Twenty five is the number to beat.

## Mistake one: playing for fun
[p1] Mistake number one is playing cards for fun.
[p2] Take the Normal Player and remove the urge to play random cards. Same bot otherwise. It goes from twenty five to thirty.
[p3] Push it the other way, cards on a whim half the time, and it falls to fourteen.
[p4] Every Skip you spend early is one you don't have later. And later is when it counts. At the first draw, about one card in seven is a Kitten. In the last few draws, most of what's left is Kittens.
[p5] The rulebook actually tells you this. Save your cards early, while your chance of exploding is low. Almost nobody listens.

## Mistake two: panicking
[d1] Mistake number two is panicking.
[d2] Once one card in four is a Kitten, the deck feels dangerous, and most people start Skipping. That's the Panicker, and it only wins sixteen.
[d3] Wait for a coin flip, and you still lose ground. The only rule that held up is the boring one. Skip or Attack when you know the next card is a Kitten. Not when you feel like it.
[d4] And if you're wondering, Attack or Skip barely matters when you're dodging. The gap was a fraction of a point.
[d5] Here's where people actually get caught. At a normal table of four, almost one explosion in four happens to someone under Attack, stuck taking two turns in a row.
[d6] With two players, it's almost two in five. But at a table of four Patient Ones, it's only about one in thirteen. My guess is that patient players still have a Skip in hand when the Attack lands.

## Mistake three: looking at the wrong time
[f1] Which brings us to mistake number three. Looking at the wrong time.
[f2] The only way to know what's coming is See the Future. Never using it costs you about two and a half points. Using it the moment you draw it costs about the same.
[f3] The best time is when roughly one card in three could be a Kitten. Peek then. If the top card is a Kitten, dodge. If it isn't, draw, and keep your Skip.
[f4] And you can tell when that is. Count the cards left in the deck, and divide by the Kittens still in it. About three cards per Kitten, and it's time to look. Two Kittens left means six cards or fewer.

## Mistake four: hiding it in the wrong place
[k1] Mistake number four happens right after you survive.
[k2] You drew a Kitten, you played your Defuse, and now you can put it back anywhere you like. Most people tuck it in at random. That's exactly average.
[k3] The bottom of the deck feels safe. It's actually worse than random. My best guess is that a Kitten at the bottom just waits for whoever is left, and that could easily be you.
[k4] The best spot is the first card the next player will draw. Usually that's the top. If you're under an Attack, count your turns. One more turn to take means second from the top. Two more, third.
[k5] That one change takes a bot from twenty five to thirty.
[cta] If that just saved you a Defuse, please subscribe. Uno is next.

## A quick confession
[a1] Quick confession about that bottom of the deck result. The first draft of this script had a neat explanation for it. Then I noticed I had never actually tested the explanation, only the result.
[a2] So I cut it. The numbers in this video come from the simulation. When I give you a reason, I'll tell you if it's a guess.

## Mistake five: being polite
[s1] Mistake number five is being too polite.
[s2] Cat pairs and Favors look like the weakest cards in the deck. Against a normal table, the Patient One wins forty percent. Take away its pair steals, and it drops to thirty two. Take away its Favors, thirty four.
[s3] That's a big part of why the Hoarder finished last. Every steal is a lottery ticket for someone else's Defuse. Aim it at the biggest hand.
[s4] One warning. Any two matching cards count as a pair, not just cats. Don't pair up your Attacks or Skips. A bot that did that won twenty percent. You're trading two escapes for one random card.

## The small stuff
[x1] A few smaller habits, quickly.
[x2] When someone hits you with a Favor, hand over your worst card, not a random one. That's worth about three points.
[x3] Nope every Attack and every steal aimed at you. A bot that never Nopes wins twenty one percent. One that always does wins twenty seven.
[x4] And if you see a Kitten on top and can't dodge, Shuffle. It helps, just not by much. Less than a point.

## The arguments
[t1] Now the argument every table has. Does going first matter?
[t2] With two players, it does. The first player wins fifty two percent of the time.
[t3] With five players, it flips. The last seat does a little better than the first. You get to watch a few draws before you risk anything.
[t4] And if you mostly play one on one, every one of these habits gets louder. Stop playing cards for fun in a two player game, and you win sixty eight percent.
[t5] The mistakes cost you more as well. Play cards on a whim half the time, and you drop to nineteen percent. Skip the pair steals, and you're down to thirty seven. Even using See the Future the moment you draw it costs you almost nine points.

## Does it hold up
[r1] Does any of this work against good players?
[r2] Against a normal table, the Patient One wins forty percent. Against an aggressive table that throws Attacks around, fifty three. Against a table of hoarders, half its games.
[r3] But sit four Patient Ones at the same table, and each one wins exactly one game in four. It doesn't break the game. It only works because other people make the mistakes.
[r4] It also makes games even faster. A normal table of four takes around thirty two turns. Four Patient Ones finish in twenty five.

## The recipe
[w1] So here's what ten billion games taught me.
[w2] Don't play cards for fun. Only dodge when you know. Peek with See the Future once the odds reach one in three. Put the Kitten where the next player draws. Steal from the biggest hand. Give away junk, and Nope anything aimed at you.
[w3] That's the Patient One. Forty percent at a table of four, and more than half its games with three.
[w4] With two players, it wins sixty percent. With five, twenty nine and a half, where a fair share is twenty.

## Close
[e1] Remember the one thing my bots can't do? Lie.
[e2] They never pretend the Kitten is on top when it isn't. They never act nervous when they're safe. That part of Exploding Kittens is still all yours.
[e3] Next, I'm testing Uno house rules, because one of them completely breaks the game. Tell me which one you think it is.
