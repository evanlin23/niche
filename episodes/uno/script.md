# The Best Way to Play Uno

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.
Lines marked (creator) are the creator's own wording, verbatim; the rest is a draft for the creator to rewrite.

## Number sources (4 players; "best bot" vs three normal bots; fair share 25)
- Skill meter = best bot's win rate (data/v2.json `combos[key=...].best`, every rule combination; data/extras.json
  `rules.*.best` for the fun rules). official 29.0 (+4); stacking 30.0; Seven Zero 26.2; Jump In 30.6; free +4 31.0
  (highest single rule); draw until 29.5; multi-play 28.6; no going out on an action 25.6.
- Turns per round (`turns`): official 47.0; draw until 82.3 (p90 172, results.json); multi 35.2; no_action_out 54.9.
- How I play (`stack+free_d4+multi`): 40.3 turns, best 30.9, rank 29 of 192 (top sixth). One card at a time under it:
  `habits_mine["one card at a time"]` 14.4.
- Extremes: pass_every (extras) best 24.0, turns 82.7. Joke card (GDJ85 blank-card suggestion, laugh = coin flip):
  best 26.4, turns 40.6. Most skill: `stack+jump_in+draw_until+free_d4` 35.3, 84 turns.
- Pick (`stack+jump_in+free_d4+multi`, extras `pick`): 39.2 turns, best 31.9-32.1 (edge ~7 vs official 4 = almost 2x).
  Habits under it (extras `habits_pick`): one card at a time 15.3, hold wilds 29.2, never stack 22.7, always stack 25.5,
  switch to best colour 26.6, random colour 23.6, always jump in 26.0, never 24.2. UNO under it (`uno_pick`): never forgets 29.3.
- UNO calling (v2 `uno.official`; table forgets 1 in 4, catches half, assumption said on camera): never forgets 30.4,
  always forgets 4.9, always catches 25.7 (+0.7). Penalty 4 (`uno.penalty4`): never forgets 32.1.
- g5: results.json habits (official): always challenge 24.4, never 25.2, bluff 25.0. r8: v2 `stack+stack_mix+seven_zero+jump_in+
  draw_until+free_d4` best 28.5, turns 86.3. r9: extras `bounce` best 29.2. i5: v2 `stack+free_d4+multi` hits 8+ 10.9%,
  10+ 0.9%. t1/t2: results.json two_player (official smart 54.2, first 51.6; seven_zero 50.6). p1: players.10 91.1.
- w5: habits_pick always jump in 26.0 (+1). e1: pick edge ~7 vs official 4, 39.2 turns.
- r3: first seat official 26.8, seven_zero 25.1 (results.json). x7: v2 `draw_until+multi+no_action_out` best 23.4. u5: extras uno_pick never forgets 29.3.
- Exploding Kittens reference: episodes/exploding-kittens/data/final.json `vs_casual.4.win` = 40.5 (fair 25).
- Engine check: opening hand has a Wild, math 55.81%, engine 55.84% (data/engine_check.json).
- Rules: Mattel GDJ85 sheet (no stacking, draw one, +4 only without the current colour, challenge 4/6, UNO: caught -> 2).
- Total rounds: results.json 12.6B + v2.json 414 tests x 20M = 8.28B + extras.json 28 tests x 100M = 2.8B = 23.68B
  ("over twenty three billion"; re-check after the Actions merges).
- u6 race (local 2M, seed 11; re-run on Actions): table forget 0.5 + catch 1 (= coin-flip race); never loses race 40.9 (official),
  always loses 0.0 (official; caught at one card every time, draws to 3). b3: v2 `stack+seven_zero+jump_in+free_d4+multi` 27.5.
- Big runs merged 2026-11-05: data/v2.json (Actions 41975265272, 20M per test), data/extras.json (Actions 41976054240, 100M
  per test). How I play ranks 23 of 192 (top sixth holds; top eighth too). Everything at once 28.7 (< official 29.0).
  Catching: always 25.8 / never 24.2 vs normal 25.0 ("less than a point"). Race (data/race.json, 20M local): always wins
  40.9 official, always loses 0.0028% (= 3 in 100,000; rare wins via Shuffle Hands / empty piles), pick 37.5 / 8.2.
- Script lines match the creator's recording (rec1, 2026-11-05) except pick-ups r8, u4, u6.

## Cold open
[o1] Everybody plays Uno a little bit differently.
[o2] Some people will allow plus twos to stack. Some people will say that you have to swap hands with someone whenever you play a seven. And some people will force you to keep drawing and drawing until you can play, and somebody else will always say that that isn't a real rule.
[o3] So, I took every house rule I could find, gave them to bots, and played over twenty three billion rounds of Uno.
[o4] I wanted to find the best way to play. Rounds that don't drag on forever, and where playing well actually wins you more games.
[o5] The rules decide how much skill Uno even has. Some rule sets let a good player win more than a third of the time. One makes playing well lose you games, and a bunch of the rules you think are official actually aren't.

## The game in thirty seconds
[g1] If it's been a while since you've played, the rule sheet goes like this. Everyone gets seven cards, and one card gets flipped face up from the deck to start the pile.
[g2] On your turn, you can play a card that matches the top card either by color or by number, or you can play a Wild. The first one to get to zero cards wins the game.
[g3] A Skip makes the next player miss a turn. Reverse flips the direction. Draw Two makes the next player draw two and they lose their turn. A Wild lets you pick the color.
[g4] Now, the Wild Draw Four. I bet that most people have never even heard of this part. Officially, you can only play it when you have nothing left in the current color. If someone thinks you cheated, they can challenge you, and if you get caught, you have to draw the four cards yourself.
[g5] And fun fact, that challenge barely even matters anyway. Challenging every plus four or bluffing one changes your win rate by about half a point.
[g6] The sheet also says that you can't stack plus twos. And when you can't play, you draw one card. One. Not to draw cards until you find something you can play.

## Can you trust it
[c3] I checked my simulator against plain math. The chance that your opening hand has at least one Wild is fifty five point eight percent, and over ten million deals my simulator got the same.
[c6] Also, the bots only know what a real player would know. Their own hand, the top card, and how many cards everyone's holding. A normal bot plays any card that matches and picks the color it holds the most of.

## How much skill is in Uno?
[m1] How do you even measure the skill in a card game? For me, I took my best bot, gave it every good habit I could find, and sat it down with three normal players.
[m2] If Uno was pure luck, it would win one round in four, exactly twenty five percent.
[m3] Under the official rules, it wins twenty nine, four points of skill. If we follow the official rules, most of the game is just the cards that you're dealt and the cards you draw.
[m4] And for comparison, when I tested Exploding Kittens, my best bot won forty and a half percent of the time at a table of the same size. So the official version of Uno sits pretty close to the luck end.

## House rules on the meter
[r1] Now let's check each of the house rules, one at a time.
[r2] First is stacking, which I guess is the rule that everybody has looked up at least once. This rule nudges the best bot to thirty percent, that's barely anything.
[r3] Next is Seven Zero, where playing a seven swaps your hand with someone and playing a zero passes everyone's hand around the table. This drags down the win rate to twenty six percent. My guess is that it's hard to plan a hand strategically when someone can just take it from you at any time. This rule also wipes out the edge of going first. If we follow the official rules, whoever starts wins almost twenty seven percent of rounds, with Seven Zero it's dead even.
[r4] Now we can look at Jump In, where anyone holding the exact same card can slap it down out of turn, and this pushes it up to thirty and a half percent.
[r5] Now the free plus four is how most people play it, a plus four at any time you want with no challenges. This brings us up to thirty one percent. That's the highest of any single house rule, and I've essentially played it like this my whole life without even knowing it wasn't a real rule.
[r6] The rule that says that you have to draw until you can play barely moves the meter at all. All it does is make everything take forever. Rounds take eighty two turns instead of forty seven normally, and one round in ten even takes over a hundred and seventy turns.
[r7] The rule that actually kills skill is not being allowed to go out on an action card or a Wild. This drops the meter to twenty five and a half percent, which is basically pure luck, and the rounds get longer too.
[r8] And what if you throw every house rule in at once? Stacking, Seven Zero, Jump In, draw until you can play, the free plus four. You get eighty six turns a round, and less skill than the official game at twenty eight and a half percent.
[r9] Another thing I tried for fun was Bounce, where a Reverse sends a plus two right back at whoever played it. The win rate stays at twenty nine, it changes nothing, it's just really fun to do.

## How I play
[i1] This is how I've always played. Plus twos stack on plus twos, and plus fours on plus fours, but you can't mix them. You can play a plus four whenever you want, and if you have a bunch of the same number you can dump them all at once.
[i2] This last one changes a lot. Rounds drop from forty seven turns to around forty, and my best bot wins thirty one percent of the time.
[i3] Out of the one hundred and ninety two rule combinations I tested, this combination lands in the top sixth for skill. So apparently I've just been playing one of the better versions of Uno my entire life.
[i4] One habit matters a ton with this combination. If you hold back and play your matching numbers one at a time, you win fourteen percent of rounds instead of twenty five. Basically, if you can dump your numbers, just dump them.
[i5] I also checked how big the stacks get. With my rules, in about one round of nine, somebody has to pick up eight or more cards at once. Ten or more happens in less than one round in a hundred.

## Other tables
[t1] If you mostly play one on one, the meter shifts. My best bot wins fifty four percent against a fair share of fifty, and whoever goes first wins fifty one and a half percent of the time.
[t2] With Seven Zero, every seven swaps your hand with your only opponent, and the best bot falls to barely over fifty percent.
[p1] Also, if we have more people, every extra player adds around seven turns, so a ten player round takes around ninety one turns.

## The extremes
[x1] What if you wanted Uno to just be pure luck? That's really easy. After every single turn, just force everyone to pass their hand to the next player.
[x2] My best bot drops to twenty four percent, which is below a fair share of twenty five. Under that rule, being good at Uno makes you worse at Uno. My guess is that every good move you set up gets handed to the next person.
[x3] Or you could just use one of the ideas printed on the official rule sheet for the blank cards. You tell a joke, and if anyone laughs, you get to discard down to one card. If nobody laughs, you have to draw four.
[x4] I simulated a laugh as a coin flip, because my bots aren't funny enough. This rule drags the meter down to twenty six and a half percent. The official suggestion turns Uno into mostly a coin toss.
[x7] Without any silly rules, the most luck-driven Uno I found is this one. Draw until you can play, dump your matching numbers, and no going out on an action card. The best bot wins twenty three and a half, which is below the fair share. In my opinion, nobody should play like this.
[x5] On the other hand, here's the most skillful Uno I could find. Stacking, Jump In, the free plus four, and, of all things, draw until you can play. The best bot wins thirty five percent.
[x6] The only catch is that a round now takes eighty four turns, almost double the official version.

## The best way to play
[b1] Now here's what I would play if you want games to be both fast and skill based.
[b2] Stacking, Jump In, the free plus four, and dumping all your matching numbers at once. Rounds now take around thirty nine turns, which is faster than the official game, and the best bot wins thirty two percent. That's almost twice the skill of the official rules.
[b3] If you'd rather keep it a coin toss so anyone at the table can win, just add Seven Zero.

## How to win
[w1] Now how do you win under those rules? There are four big habits to follow. Every number is one bot changing one habit against three normal players.
[w2] Number one. Dump every card of a number together. If you hold any back, you drop from winning twenty five percent to fifteen percent.
[w3] Number two. Hold your Wilds. Don't play a Wild while you have another card you can play. That alone gets you to twenty nine percent.
[w4] Number three. Always stack when you can. A bot that never stacks, and just takes the cards instead of passing them on, wins around twenty two and a half percent of the time.
[w5] The rest is all just small stuff. Switching into the color you hold most of is worth about a point and a half, and jumping in whenever you can is worth about one.
[w6] Finally there's one habit that beats almost all of them, and it's the one that my bots were never allowed to get wrong.

## Saying Uno
[u1] Remember how my bots never argue about the rules? They also never forget to say Uno. So I made them forget.
[u2] Officially, if you forget and someone catches you before the next player goes, you draw two cards.
[u3] I set the table so everyone forgets to say Uno one time in four, and someone catches a forgetter half the time. A bot that never forgets wins thirty percent, which is a bigger edge than holding onto your Wilds.
[u4] A bot that always forgets wins five percent of the time. Catching other people that forget barely matters, less than a point. So just make sure you say Uno.
[u5] Also, some tables make you draw four cards instead of just two. Then never forgetting gets you to thirty two percent. Under the rules I would play, it lands at twenty nine, right up there with holding onto your Wilds.
[u6] And at a lot of tables, it's a race. The second you're down to one card, if someone else yells Uno before you do, you draw two. I made that race a coin flip. A bot that always wins the race wins forty one percent of rounds. A bot that always loses, under the official rules, basically never wins. Three rounds in a hundred thousand. Every time it gets to one card, it gets back up to three.

## Close
[e1] Under the official rules, Uno is mostly luck. Under the rules I would play, a good player gets almost twice the edge, and a round is over in thirty nine turns, about eight turns faster. That's the best way to play Uno that I found.
[n1] Next up is Sorry. It's supposed to be pure luck, but my best bot won a third of its games.
[e2] Tell me where your table lands on the meter, and what rule you'd add to it. I'll read every one.
