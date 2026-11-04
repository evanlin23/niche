# How to Beat Your Friends at Connect 4 (Without Memorizing the Solution)

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.

## Number sources (data/results.json; bots: random < win_block < center < careful < look2)
- Ladder: win/block vs random 96.1%; + centre vs win/block 67.8%; + careful vs centre 61.1%; look 2 vs careful 84.3%.
  look 4 vs look 2: 46.9% (20% draws); look 6 vs look 4: 54.9%.
- First player (mirror): random 55.1 vs 44.7; centre bots 53.3 vs 43.2; careful 45.7 vs 37.1 (17% draws).
- Opening column (careful bots): centre 49.3%, columns 3/5 43.8/43.7, columns 2/6 43.4/43.2, edges 38.8/38.6.
- Engine check (sims/connect4 solver, `c4 -openings`): MUST reproduce the 1988 result (first player wins only
  by opening in the centre; columns 3 and 5 draw; the rest lose). DONE: matches (data/solver.json): centre win, columns 3/5 draw, others lose. c2 stays. c3 needs one check: solver took ~6.5 runner-hours; confirm the bot experiments took less in total.

## Cold open
[o1] Connect Four was solved in 1988. A computer worked out that the first player can always win, if they start in the middle and never make a mistake.
[o2] That's no help at all when you're playing your little brother. You can't memorize a solution with trillions of positions.
[o3] So I built bots that play like people, from complete beginners to pretty sharp players, and had them play millions of games against each other.
[o4] Here's the headline. One simple habit beats a beginner ninety six games out of a hundred. And looking just two moves ahead beats a careful player more than eight times in ten.

## Can you trust it
[c1] First, the engine. It plays on the standard seven by six grid, drops discs exactly like the real thing, and checks every row, column and diagonal for four in a row.
[c2] To make sure it understands the game, I gave it the hardest test there is. Solving the whole thing from an empty board. It found the same answer as the 1988 proof. Start in the middle and you can force a win. Start one column over and the best you can do is a draw. Start anywhere else and you lose.
[c3] Confession: that one check took longer to run than every other experiment in this video combined.

## The ladder
[l1] Now the bots. Each one adds a single habit to the one before it.
[l2] The Beginner drops discs at random. The Blocker takes a win when it sees one, and blocks yours. That one habit beats the Beginner ninety six percent of the time.
[l3] If you only remember one thing from this video, it's this. Before every move, check for a four you can finish, and a four they can finish.

## Habit two: the middle
[m1] The second habit is the middle.
[m2] There are more ways to make four through the middle column than through any other. So the next bot plays toward the center whenever it can.
[m3] Against the Blocker, it wins sixty eight percent of games. Same reflexes, just better aim.

## Habit three: don't set them up
[s1] Habit three is the sneaky one. Never play directly underneath a spot where your opponent could win.
[s2] If you fill the square below their winning square, you just handed them the next move. The Careful bot never does that, and it beats the center bot sixty one percent of the time.

## Habit four: two moves ahead
[t1] The fourth habit is the big one. Look two moves ahead. For each move you could make, ask what your opponent would do next.
[t2] That bot beats the Careful bot eighty four percent of the time.
[t3] And here's the surprise. Looking four or six moves ahead, with only a rough sense of what a good position looks like, didn't reliably beat looking two. My guess is that past a point, it's not about how far you look. It's about knowing what you're looking for.

## Going first
[f1] What about going first? With perfect play, it's a guaranteed win. With real people, it's a nudge.
[f2] Between two players who use the middle, the first player wins fifty three percent of games and the second wins forty three. The rest are draws.
[f3] And where you start matters, even for normal players. Opening in the middle column wins forty nine percent of games for the first player. Opening on an edge, under thirty nine.

## The recipe
[w1] So here's how to beat your friends at Connect Four.
[w2] Check for wins and blocks every single move. Play toward the middle. Never fill the square under their winning spot. And before you drop a disc, ask what they'll do next.
[w3] And if you get to go first, start in the middle. The computer from 1988 would approve.

## Close
[e1] Which game should I simulate next? Tell me in the comments, and tell me the house rule your family swears by.
