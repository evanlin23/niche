# Where to Hide Your Ships in Battleship (and How the Computer Finds Them Anyway)

Narrated lines are `[id] text`. Style: docs/script-style-guide.md. Structure: docs/perfectplay-structure-notes.md.
Big run: 36 tests x 10M games = 360M games. Script numbers re-checked against it.

## Number sources (data/results.json; classic Hasbro A3264 fleet 5-4-3-3-2, 10x10)
- Shots to sink a randomly placed fleet: Random 95.39 (median 97); Hunter (random until a hit, then neighbours) 62.2;
  Checkerboard (hunter that only searches every other square) 55.2; Calculator (probability map) 44.3.
- Head to head: Hunter beats Random 98.7%; Checkerboard beats Hunter 64.6%; Calculator beats Checkerboard 80.3%;
  Calculator beats Hunter 85.3%. Mirror: equal bots 50/50 except going first (51-52%; ties go to the first player).
- Engine check: a random shooter needs the last of 17 ship squares among 100: 17 x 101 / 18 = 95.39 shots on
  paper; engine 95.39 (10M games).
- Hiding vs the Hunter (shots it needs): random 62.2, spread out 66.9, edges 62.7, corners 62.1, centre 60.2,
  clustered 55.1. Spread vs random placer (both Hunters): 59.2% wins. Clustered: 36.6%. Centre: 46.2%.
- Hiding vs the Calculator: random 44.3, spread 44.2, edges 45.5, corners 45.8, centre 42.1, cluster 44.6.
  Edges vs random placer (both Calculators): 53.6%. Corners: 54.8%.
- House rule "only say hit" (don't name the ship): Calculator 44.29 -> 44.85 shots. Other bots never use the name.

## Cold open
[o1] Everybody has a Battleship strategy. Hide in the corners. Line your ships up along the edge. Bunch them all together so they're hard to find.
[o2] And then there's how you shoot. Most people fire at random until they hit something.
[o3] So I built bots that hide and hunt in all those different ways, and had them play hundreds of millions of games.
[o4] Here's the headline. Where you hide matters less than you think. How you shoot matters way more. The best shooter needs less than half the shots of a random one.

## The game in ten seconds
[g1] Quick rules. Each player hides five ships on a ten by ten grid. You take turns calling out squares. Hit or miss. Sink the whole fleet first and you win.

## Can you trust it
[c1] My version follows the official Hasbro rules. Five ships, from the five square Carrier down to the two square Patrol Boat. Seventeen squares of ship in total.
[c2] And one rule a lot of people skip. When you hit a ship, your opponent has to tell you which ship it was.
[c3] To check the engine, I used plain math. If you shoot completely at random, you finish when you find the last of those seventeen squares. On paper, that takes ninety five point three nine shots on average. Over ten million games, my engine says ninety five point three nine.

## Meet the shooters
[s1] Here are the shooters.
[s2] The Beginner fires at random. The Hunter fires at random too, but once it gets a hit, it checks the squares around it until the ship sinks.
[s3] The Checkerboard does the same thing, but while it's searching, it only fires at every other square, like the black squares on a chess board. The smallest ship is two squares long, so it can't hide between them.
[s4] And the Calculator. Before every shot, it counts every way the remaining ships could still fit on the board, and fires where the most of them overlap.

## The results
[r1] The Beginner needs ninety five shots to sink a fleet. Almost the whole board.
[r2] The Hunter needs sixty two. That one habit, checking around a hit, beats the Beginner ninety nine games out of a hundred.
[r3] The Checkerboard needs fifty five, and beats the Hunter sixty five percent of the time.
[r4] And the Calculator needs forty four. Against the Checkerboard, it wins eighty percent of games.

## Where to hide
[h1] Now the other half. Where should you put your ships?
[h2] Against a Hunter, which is how most people play, the worst thing you can do is bunch your ships together. Clustered fleets win only thirty seven percent of games. My guess is that one hit leads the Hunter straight into the next ship.
[h3] The best thing is to spread them out, so no two ships touch. That wins sixty percent of games against the same opponent.
[h4] Corners and edges? Against a Hunter, they barely matter at all.

## Against the Calculator
[k1] But the Calculator is different.
[k2] It knows ships fit more easily in the middle of the board, so it shoots there first. Against the Calculator, ships on the edges win fifty four percent of games, and ships in the corners win fifty five.
[k3] So the corner people were half right. Corners help, but only against a really good shooter.

## The house rule
[x1] And remember that rule about naming the ship you hit? A lot of families just say hit.
[x2] It barely matters. The Calculator needs about half a shot more. Everyone else doesn't use the name anyway.

## Going first
[f1] Does going first help? A little. Between two equal shooters, the first player wins between fifty one and fifty two percent of games.
[f2] That's because if you both need the same number of shots, you get there first.

## The recipe
[w1] So here's how to win at Battleship.
[w2] When you shoot, search in a checkerboard pattern, and when you get a hit, finish that ship before you go back to searching.
[w3] When you hide, spread your ships out and never let them touch. If your opponent is good, push them toward the edges.

## Close
[e1] Where do you hide your Carrier? Tell me in the comments.
