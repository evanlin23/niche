# You Have to Jump. I Played a Billion Games of Checkers to See Why.

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.
Big run: 1,022,544,000 games (GitHub Actions run 41874542377, 20 shards; fast-bot tests 3.6M games per shard,
2-move "club" tests 90K, 4-move "thinker" tests 3.6K). Claims say "over a billion".

## Number sources (data/results.json; WCDF rules; "score" = wins + half of draws)
- Engine check ("engine_check"): both sides moving at random, a jump within the first 6 plies: math
  54420409/64538880 = 84.322% (exact_check.py, every possible opening), engine 84.320% (72M games). perft from the
  start matches the published counts: 7, 49, 302, 1469 ... 18,391,564 at 10 plies.
- Skill ("skill"): Casual beats Random 99.75% (loses 0.03). Club vs Casual: wins 61.85, loses 4.06, draws 34.09.
  Thinker vs Club: wins 65.06, loses 4.13 (72K games).
- Mirror ("mirror", colours alternate): Casual first player 23.04% wins, second 24.81%, draws 52.15%; Club first 28.28,
  second 28.99; Random first 47.22, second 48.70. Every mirror scores 49.99-50.00% for each side.
- Habits vs Casual ("habits", score): keep the back row 60.19 (wins 35.25, loses 14.88); take the centre 41.59
  (wins 17.74, loses 34.56); rush men forward 40.20 (wins 11.31, loses 30.90); hug the edges 50.18 with 80.23% draws;
  trade when ahead 52.04; kings worth 200: 49.04; kings worth 100: 48.65.
- Habits vs Club ("habits_club", 1.8M games): back row 63.88 (wins 43.43, loses 15.67); centre 48.14.
- The jump rule ("rules", draws): Casual mirror official 52.15, optional jumps 76.53, huffing 72.61 (0.65 huffs a game).
  Club mirror official 42.73, optional 35.09, huffing 30.22.
- Skill by rule: Club vs Casual wins 61.85 official, 50.11 optional, 58.03 huffing. Thinker vs Club 65.06 official,
  74.56 optional (72K games each, +-0.35).
- Game length: Casual mirror 160 plies = 80 moves each.
- Outside source: checkers is solved, perfect play from the start is a draw (Schaeffer et al., Science 317, 2007).
- True story: the first huffing bots didn't model being huffed and lost a piece to huffing 7.6 times a game (pilot,
  2026-11-04, fixed before the big run).
- Explanations marked "my guess" are not tested.

## Cold open
[o1] Every family has a checkers rule that isn't in the rulebook.
[o2] Some people let you skip a jump if you don't like it. Some old timers huff your piece if you miss one. And some kids have never heard that jumping is required at all.
[o3] So I built checkers bots, gave them every version of the rules, and had them play over a billion games.
[o4] Here's the headline. The single best habit I found is boring. Keep your back row at home. It turns an even game into sixty percent of the points.
[o5] And the jump rule changes the game a lot more than you'd think. Just not the way I expected.

## The game in ten seconds
[g1] Quick rules. Twelve pieces each, on the dark squares. Move one square diagonally forward. Jump a piece to capture it. Reach the far side and you get a king, which can move backwards too.

## Can you trust it
[c1] My version follows the rules of the World Checkers and Draughts Federation, which the American federation uses. The same rule is printed in a Hasbro box. If you can jump, you must. If you can keep jumping, you must finish.
[c2] To check the engine, I took the case where both players move completely at random. You can count every possible opening by hand, or at least a computer can.
[c3] That count says someone jumps in the first three moves each eighty four point three two percent of the time. Over seventy two million random games, my engine says eighty four point three two.
[c4] One thing to keep in mind. My bots look a few moves ahead, not twenty. They are not grandmasters. I'll come back to that at the end.

## Meet the players
[p1] Here are the players.
[p2] The Casual player looks at each of its moves and every jump that follows, then counts pieces. That's most of us.
[p3] The Club player also looks at your best reply. And the Thinker looks four moves ahead.
[p4] Looking ahead pays. The Casual player beats a random one almost every single game. The Club player beats the Casual player sixty two percent of the time and loses only four.

## The habits
[h1] Now the habits. Each one is a Casual player with one change, playing against a normal Casual player.
[h2] I'm counting points, where a win is one and a draw is half. An even matchup is fifty percent. That's the number to beat.

## Mistake one: rushing for a king
[m1] Mistake one is racing your pieces forward to get a king. It's the most natural thing in the world, and it's the worst habit I tested. Forty percent of the points.
[m2] My guess is that men out in front have nobody behind them, so they get picked off.

## Mistake two: the center
[m3] Mistake two surprised me. Every strategy guide says control the center. A Casual player who grabs the center scores forty two percent.
[m4] With the Club player, the center habit is close to even, forty eight. So the center might be worth it, but only if you look far enough ahead to defend it. That part is my guess.

## The edges
[m5] What about hugging the edges, because pieces on the side can't be jumped? It doesn't lose. Fifty percent. But four games in five end in a draw. You're not losing. You're just not playing.

## The back row
[b1] And here's the winner. Keep the four pieces on your back row at home as long as you can.
[b2] Against a Casual player, that one habit scores sixty percent. It wins thirty five games in a hundred and loses only fifteen.
[b3] With the Club player it's even stronger. Sixty four percent.
[b4] Your back row is the row where your opponent gets a king. If it's full, they can't crown anything.
[b5] If you want to beat the people you play, subscribe. There's a new game every week.

## The jump rule
[j1] Now the rule everybody argues about. What happens if jumps are optional?
[j2] For two Casual players, three games in four end in a draw. With the official rule, it's about half.
[j3] The old huffing rule, where your opponent removes the piece that should have jumped, comes out almost the same. Seventy three percent draws.
[j4] Here's what I didn't expect. For two Club players it goes the other way. Optional jumps mean fewer draws, thirty five percent instead of forty three.
[j5] And it changes who wins. With forced jumps, the Club player beats the Casual player sixty two percent of the time. With optional jumps, only fifty.
[j6] Between the Club player and the Thinker, it flips again. Optional jumps help the Thinker. So I can't promise you the rule always rewards skill.
[j7] My guess for the Casual players is that forced jumps are a trap. Look one move further than your opponent and you can make them jump into a bad spot. Take the rule away and the trap is gone.

## Going first
[f1] Does going first help? Not for my bots. Whenever both sides played the same way, the second player won slightly more often. For two Casual players, twenty five percent against twenty three.

## The aside
[a1] One true story. My first huffing bots didn't know they could be huffed.
[a2] So they kept skipping jumps they didn't like, and lost a piece to huffing almost eight times a game. I had to teach them about the rule before I could test it.

## The recipe
[w1] So here's what over a billion games of checkers say.
[w2] Keep your back row home. Don't race your men forward for a king. Don't grab the center unless you can defend it.
[w3] When you're ahead, trade pieces. It's a small edge, but it's real.
[w4] And play the real rule. It's the one in the box, and for most families it means a lot fewer draws.

## Close
[x1] Remember, my bots only look a few moves ahead. Checkers was solved in two thousand and seven. With perfect play from both sides, it's a draw.
[x2] But nobody at your table plays perfectly. So do you play with forced jumps, or are you a huffer? Tell me in the comments.
