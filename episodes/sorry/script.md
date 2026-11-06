# The Best Way to Play Sorry!

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: the Uno episode (skill meter).
Draft for the creator to rewrite in their own words; captions follow what they actually say.

## Number sources (4 players; "best bot" vs three Normal bots; fair share 25 unless said)
Skill meter = best bot's win rate, data/v2.json `combos[key=...].best`; game length = `combos[key=...].turns` (turns
per game, every player's turn counts). v2.json comes from Actions run 42172916225 (merge pending: the numbers below
are the local scan, seeds 42/77/9, 100k games per test; re-check every one after the merge).
- Official classic rules (`classic`): best 33.9, turns 277 (about 69 each). Random mover (`extras.random_floor.classic`)
  4.9 = about 1 in 20. results.json (1B games) agrees: luck.best_vs_normal 33.78, random 4.90.
- Uno official 29.0 (episodes/uno/script.md header, v2 `combos[key=official].best`): edge 4.0 vs Sorry! 8.9 ("more
  than twice"). Exploding Kittens 40.5 (episodes/exploding-kittens/data/final.json `vs_casual.4.win`).
- Engine check (results.json `engine_check`): nobody out in round one, math 39.535%, engine 39.551%.
- House rules one at a time: start_out 34.2 / 259.5 turns; no_exact 32.2 / 176; slides_all 33.8 / 296;
  no_slides 34.7 / 263; 2020 rules (`two_no_draw+sorry_four`) 32.2 / 291; two_no_draw alone 33.6 / 303.
- Team rules (`extras.teams_best`): best team 56.6 vs fair 50. Players (results.json `players`): 2p 55.2 (fair 50),
  3p 42.5 (fair 33.3). Three-player seat (results.json `mirror.3p`): 39.8 / 30.1 / 30.1; no bumping
  (`mirror.3p_no_interaction`): 33.2-33.5.
- 5-card variation (`hand5`): best 34.8, 117 turns; random (`extras.random_floor.hand5`) 0.07 = under 1 in 1,000.
- Pick (`start_out+no_exact+hand5`): best 39.2, 86 turns (277 / 86 = 3.2 = "about a third of the time").
  No slides on top (`no_slides+start_out+no_exact+hand5`): 40.3, 81 turns.
- Card values (results.json `mirror.4p.card_swing`, classic): Sorry! 40.2, eleven 10.4 ("almost four times"),
  four 3.8 > five 3.3. Twelve unusable 56.7% (`card_forfeit.12`).
- Three cards (`extras.hand3_best`): 33.2, 158 turns.
- [n1] (next-game teaser) is recorded later as a pick-up once the next game is set.
- Habits under the pick (`habits_pick.*.test_win`, local 100k): runner 31.4; spreader 7.3; random 0.18; best 39.2 vs
  best_no_keep 32.5; careful 27.3; safety_first 27.0 ("about two points" each); never_switch 16.8; switcher 21.3;
  lead (always front pawn) 19.7; avenger 20.3; front_unless_bump 25.8; never_back1 25.1; saver alone 26.6.
- Pick at other tables (`extras.players_pick`): 2p 57.8 (fair 50); 3p 47.3 (fair 33.3). Teams under the pick
  (`extras.teams_pick_best`): 69.4 (fair 50) = "almost seven in ten".
- Total games: results.json 1,006,250,000 + v2.json total_games (about 1.3B) = "over two billion" (re-check).

## Cold open
[o1] Sorry! is supposed to be pure luck. You draw a card and you do what it says.
[o2] But when I put it on my skill meter, Sorry! came out with more than twice the skill of Uno.
[o3] And the official rule sheet has a variation printed on it that almost nobody plays. It makes the game more skillful, and it finishes in about a third of the time.
[o4] I gave Hasbro's rules and every house rule I could find to bots, and had them play over two billion games. I wanted to find the best way to play Sorry!

## How to play
[g1] If it's been a while, here's how Sorry! works. Everyone has four pawns in their Start, and you win by getting all four around the board and into your Home.
[g2] There are no dice. On your turn you draw a card and move that many spaces. The deck has forty five cards, with no sixes and no nines.
[g3] You can only leave Start with a one or a two. And a two lets you draw again.
[g4] A few cards are special. The four moves you backwards. The seven can be split between two pawns. The ten moves you ten forward or one back.
[g5] The eleven moves eleven, or swaps one of your pawns with anyone else's on the board.
[g6] And the Sorry! card. You take a pawn out of your Start, put it on someone else's pawn, and send theirs back to their Start.
[g7] Landing on someone with any card bumps them back to Start too. And if you land on a triangle of another color, you slide to the end and bump everyone on the slide.
[g8] The last five spaces before your Home are your Safety Zone. Nobody else can get in, and you need the exact count to get Home.

## Can you trust it
[c1] I checked my simulator against plain math. With four players, the chance that nobody gets a pawn out in the first round is thirty nine and a half percent.
[c2] Over thirty five million first rounds, my simulator landed within two hundredths of a percent of that.
[c3] The bots only know what a real player knows, the board and the card they drew. A normal bot takes the move that gets it furthest, and bumps people whenever it can.

## The skill meter
[m1] So how do you measure skill in a game like this? I take my best bot, give it every good habit I found, and sit it down with three normal players.
[m2] If Sorry! was pure luck, it would win one game in four. Twenty five percent.
[m3] Under the official rules it wins thirty four. That's nine points of skill. I honestly expected it to land right next to Uno.
[m4] Uno's official rules only gave my best bot twenty nine, so Sorry! has more than twice the skill. Exploding Kittens is still ahead at forty and a half.
[m5] And at the bottom, a bot that moves completely at random wins about one game in twenty. So no, it's not all luck.
[m6] The problem is the length. An official game takes two hundred and seventy seven turns. That's about sixty nine turns for every player.

## Where the skill comes from
[k1] Part of that skill is knowing what your cards are worth. I measured how far each card moves the race, counting your progress and what it costs everyone else.
[k2] The Sorry! card is worth almost four times an eleven. Nothing else comes close.
[k3] My favorite is the four, the card that moves you backwards. It's worth more than the five.
[k4] Back up four from your Start circle and you're two spaces from your Safety Zone. You just skipped almost the whole board.
[k5] The twelve sounds great, but more than half the time you can't use it at all.

## House rules on the meter
[r1] Now let's put the house rules on the meter, one at a time.
[r2] A common one is starting with one pawn already out. That nudges the meter up to thirty four, and cuts about eighteen turns.
[r3] No exact count, where any card that reaches your Home gets you in. This one cuts the game by more than a third, down to a hundred and seventy six turns. It costs a little skill. The best bot drops to thirty two.
[r4] Sliding on every slide, even your own color, sounds harmless. But your own slide starts right before the entrance to your Safety Zone. You slide straight past it and go around the board again.
[r5] So that rule barely moves the meter, and games get longer, almost three hundred turns.
[r6] No slides at all goes the other way. Thirty five percent, and a slightly shorter game.
[r7] The newer twenty twenty rules take away the two's extra draw, and let a Sorry! card move you forward four instead. That drops the meter to thirty two, and adds about fourteen turns.
[r8] The classic sheet also has official Team rules. Partners sit across from each other, and you can move either partner's pawns. A team of two best bots wins fifty six and a half percent, against a fair share of fifty.
[r9] One on one, the best bot wins fifty five percent, against a fair share of fifty. With three players, forty two and a half, against a fair share of thirty three.

## The three player seat
[t1] But three players hides something weirder. One side of the board is empty, and one seat wins forty percent of the games. The other two win thirty each.
[t2] I thought that was a bug. So I switched off bumping completely, and all three seats evened out at a third. It comes from the bumping.
[t3] So with three players, take the color whose pawns run onto the empty side first.

## The best way to play
[b1] Now the variation almost nobody plays. It's printed right on the classic rule sheet, as the variation for adults.
[b2] Everyone holds five cards. On your turn you pick one, play it, and draw back up to five.
[b3] On its own, that cuts the game to a hundred and seventeen turns, and the best bot wins thirty five percent.
[b4] But the part I didn't expect was the bottom of the meter. A player who picks cards at random wins less than one game in a thousand.
[b5] Even three cards gets you most of the way. The best bot wins thirty three percent, and a game takes a hundred and fifty eight turns.
[b6] Now add no exact count, and start everyone with one pawn out. The best bot wins thirty nine percent, and a game takes eighty six turns instead of two hundred and seventy seven.
[b7] That's more skill than the official game, in about a third of the time. That's how I'd play Sorry!
[b8] It works with any number of players too. One on one, the best bot wins fifty eight percent. With Team rules, a team of two good players wins almost seven games in ten.
[b9] If you want the most skill I found, take the slides out as well. That gets the best bot to forty. But the slides are half the fun, so I'd keep them.

## How to win
[w1] So how do you win under those rules? Every number here is one bot changing one habit, against three normal players.
[w2] Number one. Push one pawn all the way home before you worry about the next. That habit alone wins thirty one percent.
[w3] Spreading your moves over all four pawns feels safe. It's the worst habit I tested, apart from playing at random. Seven percent.
[w4] Number two. Save your Sorry! cards and your elevens for a moment that's worth it. When I took that one habit away from my best bot, it fell from thirty nine to thirty two and a half.
[w5] Number three. Don't stop right in front of an opponent if you can help it, and get into your Safety Zone whenever you can. Each of those is worth about two points.
[w6] Number four. Use the eleven to switch when the switch moves you forward. Never switching drops you to seventeen. Switching with the leader every single time, twenty one.
[w7] And one I got wrong. I thought you should always move your front pawn. But doing that even when you could bump someone drops you to twenty.
[w8] Aiming every Sorry! card at the leader isn't great either. Twenty percent. Your pawn lands where theirs was, so where you land matters as much as who you hit.

## Close
[e1] Under the official rules, Sorry! already has more than twice the skill of Uno. Hold five cards, skip the exact count, start with a pawn out, and a good player wins almost two games in five.
[e2] Do you play with the exact count, or does any card get you Home? Tell me in the comments.
