# I Solved Every Game of Shut the Box. Your House Rule Makes It 14 Times Harder.

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.

## Number sources (data/results.json; exact = dynamic programming over every board, sim = Monte Carlo)
- Tiles 1-9, any combination: perfect 7.14% (about 1 in 14); biggest tile first 6.96; fewest tiles 7.00;
  random 2.04; smallest first 1.05; most tiles 1.04. Sim matches exact (perfect sim 7.15).
- Tiles 1-9, sum OR split only: perfect 0.51% (about 1 in 200); biggest/fewest 0.31; random 0.32; most tiles 0.31.
- Tiles 1-12: any 0.36% (1 in 280); sum-or-split 0.03% (about 1 in 3,000).
- One-die rule (roll one die once 7, 8, 9 are down), 1-9 any: perfect 7.42%, biggest first 5.56%.
- Scoring (leftover tiles added up, lower is better), 1-9 any: perfect low-score play 11.2; biggest first 11.4;
  random 20.1; most tiles 24.2.
- Ratio 7.14 / 0.51 = 14.0. Ratio 6.96 / 1.04 = 6.7 ("almost seven times").
- Confession is true: the first exact evaluation of the random player froze one random choice per board; fixed
  to average over all moves; now exact 2.04 vs simulated 2.03.

## Cold open
[o1] Shut the Box is the pub game with the wooden tiles, numbered one to nine. Roll two dice, flip down tiles that add up to your roll, and try to flip them all.
[o2] Everyone who plays it has a system. Take the big tiles first. Take as many tiles as you can. Just go with your gut.
[o3] So I solved it. Every possible board, every possible roll. Then I had bots play billions of games to make sure the math holds up.
[o4] Here's the headline. Played perfectly, you shut the box about one game in fourteen. But there's a popular house rule that makes it fourteen times harder. Even for perfect play.

## The rules in ten seconds
[g1] Quick rules. You roll two dice. You flip down any open tiles that add up to the total. If you can't, your turn is over, and the tiles still standing are your score. Shut them all, and you win outright.

## Can you trust it
[c1] Shut the Box is small enough to solve exactly. Nine tiles means only five hundred and twelve possible boards. For each one, the computer checks every roll and every move, and works out which choice gives you the best chance.
[c2] Then I replayed billions of games with the perfect strategy, rolling real random dice. Perfect play shut the box seven point one four percent of the time on paper. In the simulation, seven point one five.
[c3] Confession. The first time I checked my random player, the math and the simulation disagreed. My exact calculation had frozen one random choice per board instead of averaging over all of them. Fixed, they now agree to a hundredth of a percent.

## The systems
[s1] So let's test the systems people actually use.
[s2] The Big Spender always takes the biggest tile it can. The Minimalist flips as few tiles as possible. The Sweeper flips as many as possible, cleaning up the small ones first. And the Coin Flipper just picks any legal move.
[s3] The Big Spender shuts the box six point nine six percent of the time. Perfect play is seven point one four. That's ninety eight percent as good as a computer that knows every board.
[s4] The Minimalist is right there too, at seven percent. The Coin Flipper manages two.
[s5] And the Sweeper? One percent. Almost seven times worse than the Big Spender. Flipping lots of small tiles feels productive. My guess is that you need those small tiles at the end, when only small totals are left.

## The house rule
[h1] Now the house rule. In a lot of homes, you can't flip any combination you like. You can flip one tile that matches the total, or the two tiles that match each die. Sum or split. Nothing else.
[h2] That rule changes everything. Even perfect play only shuts the box half a percent of the time. About one game in two hundred.
[h3] And strategy barely matters anymore. The Big Spender, the Sweeper and the Coin Flipper all land within a few hundredths of a percent of each other. With sum or split, Shut the Box is basically a lottery.

## Twelve tiles
[t1] Some boxes go up to twelve.
[t2] With any combination allowed, perfect play shuts a twelve tile box about once in two hundred and eighty games. With sum or split, about once in three thousand. You could play every day for years and never see it.

## The one die rule
[d1] One more common rule. Once the seven, eight and nine are down, you roll just one die.
[d2] For perfect play, that helps a little. Seven point four two percent instead of seven point one four.
[d3] But for the Big Spender, it hurts. It drops to five and a half. My guess is that the one die rule rewards a slightly different plan, and the simple habit doesn't adjust.

## Playing for points
[p1] Plenty of tables don't play for the shut. They add up the tiles left standing, and the lowest score wins.
[p2] Same lesson. Perfect play leaves about eleven points on average. The Big Spender, about eleven and a half. The Sweeper leaves twenty four.

## The recipe
[w1] So here's how to play Shut the Box.
[w2] Take the biggest tile you can, every time. Don't spend your small tiles early. And if your family plays sum or split, stop worrying about strategy, because you're mostly playing the dice.

## Close
[e1] Next, I'm playing Battleship, to find out where to hide your ships.
[e2] And tell me which rule your family uses. Any combination, or sum or split?
