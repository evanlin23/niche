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
- "Billions": results.json 12.6B + v2.json 7.7B rounds.
- Local runs (200k-500k per test) until the Actions runs merge; re-check every number after.

## Cold open
[o1] Everybody plays Uno a little bit differently.
[o2] Some people allow plus twos to stack. Some people say that we need to swap hands when anyone plays a seven. And some people will force you to keep drawing and drawing and drawing until you can play, and somebody else always says that that isn't a real rule.
[o3] So, I took every house rule I could find, gave them to bots, and played billions of rounds of Uno.
[o4] I wanted to find the best way to play. Rounds that don't drag on forever, where playing well actually wins you more games.
[o5] Turns out the rules decide how much skill Uno even has. Some rule sets let a good player win more than a third of the time. One makes playing well lose you games. And a bunch of the rules you think are official, aren't.

## The game in thirty seconds
[g1] If it's been a while since you've played, the rule sheet goes like this. Everyone gets seven cards, and one card gets flipped face up from the deck to start the pile.
[g2] On your turn you match the top card by color or by number, or you play a Wild. First one to get to zero cards wins the round.
[g3] Skip makes the next player miss a turn. Reverse flips the direction. Draw Two makes the next player draw two and lose their turn. A Wild lets you pick the color.
[g4] Now, the Wild Draw Four. I'd bet most people have never heard this part. Officially, you can only play it when you have nothing in the current color. If someone thinks you cheated, they can challenge you, and if you're caught, you draw the four yourself.
[g6] The sheet also says you can't stack plus twos. And when you can't play, you draw one card. One. Not until you find something.
[g5] Fun fact, that challenge barely matters. Challenging every plus four, or bluffing one, changes your win rate by about half a point.

## Can you trust it
[c3] I checked my simulator against plain math. The chance your opening hand has at least one Wild is fifty five point eight percent, and over ten million deals my simulator got the same.
[c6] The bots only know what a real player knows: their own hand, the top card, and how many cards everyone's holding. A normal bot plays any card that matches and picks the color it holds the most of.

## How much skill is in Uno?
[m1] How do you measure skill in a card game? I take my best bot, give it every good habit I could find, and sit it down with three normal players.
[m2] If Uno were pure luck, it would win one round in four. Twenty five percent.
[m3] Under the official rules, it wins twenty nine. Four points of skill. Most of official Uno is the cards you're dealt.
[m4] For comparison, my best Exploding Kittens bot won forty and a half percent at the same size table. So official Uno sits pretty close to the luck end.

## House rules on the meter
[r1] Now let's put the house rules on the meter, one at a time.
[r2] Stacking, the rule everybody looks up, nudges it to thirty. Barely a bump.
[r3] Seven Zero, where a seven swaps hands, drags it down to twenty six. My guess is it's hard to plan a hand when someone can take it from you. It also wipes out the edge for going first. Officially, whoever starts wins almost twenty seven percent of rounds. With Seven Zero, it's dead even.
[r4] Jump In, where anyone holding the exact same card can slap it down out of turn, pushes it up to thirty and a half.
[r5] The free plus four, the way most people play it, any time, no challenges? Thirty one. That's the highest of any single house rule. I've played it that way my whole life without knowing it wasn't the real rule.
[r6] Draw until you can play barely moves the meter at all. It makes everything take forever. Eighty two turns a round instead of forty seven, and one round in ten goes past a hundred and seventy.
[r7] The one that kills skill? Not being allowed to go out on an action card or a Wild. That drops the meter to twenty five and a half, basically pure luck, and the rounds get longer too.
[r8] What if you throw every house rule in at once? Stacking, Seven Zero, Jump In, draw until you can play, the free plus four. You get eighty six turns a round, and less skill than the official game. Twenty eight and a half.
[r9] One more I tried for fun: Bounce, where a Reverse sends a plus two right back at whoever played it. Twenty nine. It changes nothing. It just feels amazing.

## How I play
[i1] This is how I've always played. Plus twos stack on plus twos and plus fours on plus fours, but you can't mix them. Plus four whenever you want. And if you have a bunch of the same number, you can dump them all at once.
[i2] That last one changes a lot. Rounds drop from forty seven turns to about forty, and my best bot wins thirty one percent.
[i3] Out of a hundred and ninety two rule combinations I tested, that lands in the top sixth for skill. So apparently I've been playing one of the better versions of Uno this whole time.
[i4] One habit matters a ton with that rule. If you hold back and play your matching numbers one at a time, you win fourteen percent of rounds instead of twenty five. That's one of the biggest mistakes in this whole video.
[i5] The giant stacks people love? With my rules, someone draws eight or more at once in about one round in nine. Ten or more, less than one round in a hundred.

## Other tables
[t1] If you mostly play one on one, the meter shifts. My best bot wins fifty four percent, against a fair share of fifty, and whoever goes first wins fifty one and a half.
[t2] With Seven Zero, every seven swaps your hand with your only opponent, and the best bot falls to barely over fifty.
[p1] More people? The box says up to ten. Every extra player adds about seven turns, so a ten player round takes about ninety one.

## The extremes
[x1] What if you wanted Uno to be pure luck? Easy. After every single turn, everyone passes their entire hand to the next player.
[x2] My best bot drops to twenty four percent. That's below a fair share. Under that rule, being good at Uno makes you worse at Uno. My guess is every good move you set up gets handed to the next person.
[x3] Or you could use a rule Mattel actually prints on the rule sheet, as an idea for the blank cards. Tell a joke. If anybody laughs, you discard down to one card. If nobody laughs, you draw four.
[x4] I counted a laugh as a coin flip, because my bots aren't funny. It drags the meter down to twenty six and a half. The official suggestion turns Uno into a coin toss.
[x7] Without any silly rules, the most luck-driven Uno I found is draw until you can play, dumping matching numbers, and no going out on an action card. The best bot wins twenty three and a half. Below fair. Nobody should play this.
[x5] The most skillful Uno I could find? Stacking, Jump In, the free plus four, and, of all things, draw until you can play. The best bot wins thirty five percent.
[x6] The catch is that a round takes eighty four turns. Nobody has that kind of time.

## The best way to play
[b1] Here's what I'd play, if you want it fast and you want playing well to pay off.
[b2] Stacking, Jump In, the free plus four, and dumping all your matching numbers at once. Rounds take about thirty nine turns, faster than the official game, and the best bot wins thirty two percent. That's almost twice the skill of the official rules.
[b3] If you'd rather keep it a coin toss so anyone at the table can win, add Seven Zero.

## How to win
[w1] Now, how to win under those rules, biggest habit first. Every number is one bot changing one habit, against three normal players.
[w2] Number one. Dump every card of a number together. Hold some back and you drop from twenty five percent to fifteen.
[w3] Number two. Hold your Wilds. Don't play a Wild while you've got another card you can play. That alone gets you to twenty nine.
[w4] Number three. Always stack when you can. A bot that never stacks, and just eats the cards, wins about twenty two and a half.
[w5] The rest is small stuff. Switching into the color you hold the most of is worth about a point and a half, and jumping in whenever you can is worth about one.
[w6] There's one more habit that beats almost all of these, and it's the one my bots were never allowed to get wrong.

## Saying Uno
[u1] Remember how my bots never argue about the rules? They also never forgot to say Uno. So I made them forget.
[u2] Officially, if you forget and someone catches you before the next player goes, you draw two cards.
[u3] I set the table so everyone forgets one time in four, and catches a forgetter half the time. A bot that never forgets wins thirty percent. That's a bigger edge than holding your Wilds.
[u4] A bot that always forgets wins five. And catching other people barely matters, about half a point. Just say Uno.
[u5] Some tables make it four cards instead of two. Then never forgetting gets you to thirty two percent. Under the rules I'd play, it's twenty nine, right up there with holding your Wilds.

## Close
[e1] Under the official rules, Uno is mostly luck. Under the rules I'd play, a good player gets almost twice the edge, and a round is over in thirty nine turns. That's the best way to play Uno I found.
[n1] Next up is Sorry!. It's supposed to be pure luck, but my best bot won a third of its games.
[e2] Tell me where your table lands on the meter, and what rule you'd add to it. I'll read every one.
