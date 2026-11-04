# Knock or Go for Gin? A Billion Games Say It Depends on One House Rule

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.
Big run: 1,008,000,000 full games to 100 points = 10,207,738,794 hands (GitHub Actions run 41875817486, 20 shards
x 18 tests x 2.8M games). Claims: "over a billion games", "ten billion hands".

## Number sources (data/results.json; Bicycle rules; each test bot plays two-player games against the Normal bot)
- Normal: knocks the moment its deadwood is 10 or less; takes a discard only if it goes into a meld.
- Knocking ("knock"): wait for 8 or less 44.46%; 6 or less 39.91%; 4 or less 37.17%; 2 or less 36.75%; Gin only 39.55%.
  ("late") Gin early, knock at 10 once the stock is down to 10 cards: 38.53%; knock at 4, then 10 late: 36.67%.
- Habits ("habits"): takes any discard that lowers deadwood 44.85%; never takes the discard 5.13%; dumps high cards
  first 43.43%; watches the opponent's pickups 50.34% (+-0.01); random discards 0.002%.
- Rules ("rules"): no layoffs against Gin: Gin-only bot 40.98%. 25-point Gin and undercut bonus: Gin-only bot 67.40%;
  knock at 6 or less 51.64%. Mirrors under both variants 49.99%.
- Undercuts ("undercut_rate_of_knocks", all knocks in those games): Normal vs Normal 4.10%; when one player hunts Gin,
  33.68% of knocks get undercut.
- Mirror ("mirror"): 50.00%; the player who plays first in the first hand wins 50.19%; 10.68 hands per game;
  Gin in 2.23% of decided hands.
- Engine check ("engine_check"): a 10-card deal holds at least one meld, math 1,573,725,206 / 3,955,006,055 = 39.791%
  (exact_check.py), engine 39.793% (56M deals).
- The deadwood counter agrees with a brute-force counter on 30,000 test hands (sims/gin/game_test.go).
- Explanations marked "my guess" are not tested.

## Cold open
[o1] Every gin player has an opinion about knocking.
[o2] Your grandpa knocks the second he hits ten. Your mom never knocks, she waits for gin. And somebody always says knocking early is for cowards.
[o3] So I turned those players into bots, gave them the official rules, and had them play over a billion games to a hundred points.
[o4] Here's the answer. Knock the moment you can. A player who waits for gin wins only forty percent of games against one who knocks right away.
[o5] Unless your family plays one particular house rule. Then it flips, and the gin hunter wins two games in three.

## The game in ten seconds
[g1] Quick rules. Ten cards each. Draw, then discard. Make sets of the same rank, or runs in one suit. Cards that don't fit are deadwood. Get your deadwood to ten or less and you can knock. Get it to zero and that's gin.

## Can you trust it
[c1] I used the official rules from Bicycle, the playing card company. Knock at ten or less. Gin is worth twenty points plus your opponent's deadwood. If you knock and your opponent has the same or less deadwood, that's an undercut, and they get ten points plus the difference.
[c2] To check the engine, I used plain counting. The chance that your first ten cards already hold a set or a run can be counted exactly. It's thirty nine point seven nine percent.
[c3] Over fifty six million deals, my engine says thirty nine point seven nine.
[c4] One limit. My bots can't read faces. They knock at ten even when you look like you're one card from gin. Keep that in mind. I'll come back to it.

## Meet the players
[p1] Here's the table. It's a two player game, so each bot plays against the Normal player.
[p2] The Normal player picks up a discard only if it fits straight into a meld. It throws whatever card leaves the least deadwood. And it knocks the moment it can.
[p3] The Gin Hunter never knocks. The Patient player waits until it's down to six or less. And the Grabber takes any discard that lowers its deadwood, meld or not.

## Mistake one: waiting
[m1] Fifty percent is a fair game, so that's the number to beat.
[m2] Mistake one is waiting for a better knock. Waiting for eight or less wins forty four percent. Six or less, forty. Two or less, thirty seven.
[m3] The Gin Hunter does about the same, forty percent. It loses six games in ten.
[m4] I also tried the clever version. Go for gin early, then knock at ten once the deck runs low. Thirty nine percent. Still a mistake.
[m5] My guess is that every turn you wait is a turn your opponent gets to knock first. And they'll catch you holding a lot of cards.

## Mistake two: the discard pile
[d1] Mistake two is how you use the discard pile.
[d2] The Grabber takes any card that lowers its deadwood, even if it doesn't make a meld. Forty five percent. My guess is that a card that doesn't make a meld isn't worth giving up a fresh card from the deck.
[d3] But never picking up is far worse. A player who always draws from the deck wins five games in a hundred.
[d4] So take a discard when it goes straight into a meld, and only then.

## Mistake three: dumping high cards
[h1] Mistake three is the one every beginner learns. Throw your kings and queens first, because they count ten.
[h2] A bot that dumps its highest card whenever it has a choice wins forty three percent. The Normal player throws the card with the fewest partners instead. A lonely king goes. A queen next to a jack stays.
[h3] If this is already changing how you play, subscribe. There's a new game every week.

## Watching your opponent
[w0] What about watching what your opponent picks up, and not feeding them? It helps, but barely. Fifty point three percent. Real, but small.

## The house rule
[r1] Now the twist. A common house rule gives bigger bonuses. Twenty five points for gin, and twenty five for an undercut, instead of twenty and ten.
[r2] With those rules, the Gin Hunter beats the quick knocker sixty seven percent of the time.
[r3] When one player hunts for gin, a third of the other player's knocks get undercut. My guess is that with a ten point bonus those undercuts aren't worth enough, and with twenty five they are.
[r4] Even knocking at six or less beats knocking at ten under those rules, fifty two percent.
[r5] And the other house rule people argue about, no laying off against gin, barely changes anything. The Gin Hunter goes from forty to forty one.

## The aside
[a1] One thing I had to get right before trusting any of this was the deadwood count. Some hands can be split into melds several different ways.
[a2] So I checked my engine against a slow brute force counter that tries every possible split, on thirty thousand hands. They agreed on every single one.

## The recipe
[x1] So here's what over a billion games of gin say.
[x2] With the official rules, knock the moment you can. Don't wait for a better hand, and don't wait for gin.
[x3] Pick up a discard only when it goes straight into a meld. And when you throw, keep cards that connect, even if they're high.
[x4] But if your family plays twenty five points for an undercut, stop knocking at ten. Hunt for gin, or at least wait until you're down to six.

## Close
[y1] Remember, my bots can't read faces. If you can tell your opponent is about to go gin, that part is still up to you.
[y2] So which do you play, ten for an undercut or twenty five? Tell me in the comments.
