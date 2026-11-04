# Shorts backlog: 36 ready-to-record Shorts from existing data

Each Short is one surprising number from a finished simulation, 25-35 seconds, ending with a pointer to the full
video. Narrated lines are `[id] text` so `python -m pipeline.lint_script docs/shorts-backlog.md` checks them.
Numbers come from the "Number sources" header of each episode's script.md (already traced there to data files),
or from data/results.json for Sorry!, Checkers and Gin Rummy (keys given). Render with each episode's shorts.yaml
(9:16, re-rendered from the same simulation, not cropped). Record a week of them in one session.

Order: alternate games so no two days in a row are the same game; post the Shorts for a game in the week its long
video goes up, then keep the rest for quiet days.

## Sorry! (data: episodes/sorry/data/results.json)

### so1: the backward card (mirror.4p.card_swing: four 3.84, five 3.32)
On screen: "The BACKWARD card beats the 5"
[so1a] In Sorry!, the four moves you backwards. It sounds like one of the worst cards in the deck.
[so1b] I played over a billion games and measured how far every card moves you. The backwards four beats the five.
[so1c] Here's why. Back up four from your Start circle and you're two squares from the entrance to your Safety Zone.
[so1d] You just skipped almost the whole board. Full video on my channel.

### so2: three-player seat (mirror.3p.seat_win: 39.84 vs 30.06 and 30.10)
On screen: "Playing Sorry! with 3? Pick THIS color"
[so2a] If you play Sorry! with three people, one color wins way more than the others.
[so2b] With three players, one side of the board is empty. The player whose pawns run into that empty side first wins forty percent of games.
[so2c] The other two win thirty each. When I switched off bumping, the three seats evened out.
[so2d] So pick the color whose side comes just before the empty one, going the way the pawns move.

### so3: it's not luck (luck.random_vs_normal 4.90; habits.spreader 8.93)
On screen: "Sorry! is NOT luck"
[so3a] Everyone says Sorry! is pure luck. So I made a bot that moves completely at random.
[so3b] At a table of four, a fair share is one game in four. The random bot wins about one in twenty.
[so3c] A bot that spreads its pawns around the board wins one in eleven.
[so3d] The habit that actually wins is the opposite. Push your front pawn home first. Full breakdown on my channel.

### so4: the Sorry! card (mirror.4p.card_swing: Sorry 40.2, eleven 10.4; card_forfeit twelve 56.7%)
On screen: "Every Sorry! card, ranked"
[so4a] I ranked every card in Sorry! by how much it moves the race.
[so4b] The Sorry! card is worth almost four times the eleven. Nothing else comes close.
[so4c] And the twelve sounds amazing, but more than half the time you can't use it at all.
[so4d] Want to know where the backwards four lands? It's higher than you think. Full video on my channel.

### so5: the one rule (habits.front_unless_bump 28.82; habits.lead 24.18; fair 25)
On screen: "One Sorry! rule = more wins"
[so5a] Here's one rule that makes you win more Sorry! games.
[so5b] Move your front pawn, unless you can bump someone. At a table of four, that wins twenty nine percent instead of twenty five.
[so5c] But you need the exception. Always moving the front pawn, even when a bump is right there, wins only twenty four.
[so5d] I tested it over a billion games. Full video on my channel.

### so6: the first round (engine_check: math 39.535, engine 39.551)
On screen: "4 in 10 Sorry! games start like this"
[so6a] In four out of ten Sorry! games with four players, nobody gets a single pawn out in the first round.
[so6b] Only a one or a two lets you start. That's nine cards out of forty five.
[so6c] The chance the first four cards are all useless is thirty nine point five four percent. My simulation says thirty nine point five five.
[so6d] So if your first round is boring, that's normal. Full video on my channel.

### so7: the adult rules (supplementary_hand5_random.json: 0.074%; luck.random_vs_normal 4.90)
On screen: "The secret ADULT version of Sorry!"
[so7a] The Sorry! instructions have a hidden variation for adults. You hold five cards and choose which one to play.
[so7b] In the normal game, a player who moves at random still wins one game in twenty.
[so7c] With five cards in your hand, a random player wins less than one game in a thousand.
[so7d] That's where skill really shows. Full video on my channel.

## Checkers (data: episodes/checkers/data/results.json)

### ck1: the back row (habits.back_row a_score 60.19; habits_club.back_row 63.88)
On screen: "The most boring checkers trick wins"
[ck1a] The best checkers habit I found is boring. Keep your back row at home.
[ck1b] Against a normal player, keeping those four pieces home scores sixty percent of the points. Against a stronger player, sixty four.
[ck1c] Your back row is where your opponent gets a king. If it's full, they can't crown anything.
[ck1d] I played over a billion games to find it. Full video on my channel.

### ck2: forced jumps (rules.casual_optional draw 76.53; mirror.casual draw 52.15)
On screen: "You HAVE to jump in checkers"
[ck2a] In official checkers, if you can jump, you have to. A lot of families skip that rule.
[ck2b] I tested both. With forced jumps, about half of casual games end in a draw.
[ck2c] Make jumps optional, and three games in four end in a draw. The rule is what makes the game a fight.
[ck2d] Full video on my channel.

### ck3: rushing for a king (habits.rush a_score 40.20)
On screen: "Stop rushing for a king"
[ck3a] Racing your pieces forward to get a king feels like the right move in checkers.
[ck3b] It's the worst habit I tested. Forty percent of the points against a normal player.
[ck3c] My guess is that men out in front have nobody behind them, so they get picked off.
[ck3d] Here's what to do instead. Full video on my channel.

### ck4: going first (mirror.casual first 23.04, second 24.81)
On screen: "Go SECOND in checkers?"
[ck4a] Does going first help in checkers? For my bots, no.
[ck4b] Whenever both sides played the same way, the second player won slightly more often.
[ck4c] For two casual players, twenty five percent wins for the second player against twenty three for the first. The rest are draws.
[ck4d] Over a billion games. Full video on my channel.

### ck5: the center myth (habits.center a_score 41.59; habits_club.center 48.14)
On screen: "Control the center? Not in checkers"
[ck5a] Every strategy guide says control the center. So I tested it.
[ck5b] A casual player who grabs the center scores forty two percent against a normal player. That's a losing habit.
[ck5c] For stronger players it's close to even. My guess is the center only pays if you look far enough ahead to defend it.
[ck5d] Full video on my channel.

## Gin Rummy (data: episodes/gin-rummy/data/results.json)

### gn1: knock or wait (knock.gin_only 39.55)
On screen: "Knock or wait for gin?"
[gn1a] In gin rummy, should you knock the moment you can, or wait for gin?
[gn1b] I played over a billion games. A player who always waits for gin wins only forty percent against one who knocks right away.
[gn1c] With the official rules, knock the moment you can.
[gn1d] But one house rule flips it. Full video on my channel.

### gn2: the house rule (rules.bonus25_gin_only 67.40)
On screen: "This gin house rule flips everything"
[gn2a] Some families play gin with a bigger bonus. Twenty five points for gin and for an undercut, instead of twenty and ten.
[gn2b] With those rules, a player who hunts for gin beats a quick knocker sixty seven percent of the time.
[gn2c] So the right strategy depends on one number in your house rules.
[gn2d] Which one do you play? Full video on my channel.

### gn3: the discard pile (habits.never_take 5.13; habits.take_lower 44.85)
On screen: "Never pick up the discard? Big mistake"
[gn3a] Some gin players never pick up from the discard pile. They always draw blind.
[gn3b] That player wins five games in a hundred.
[gn3c] But grabbing every low card is a mistake too. Forty five percent. Take a discard only when it goes straight into a meld.
[gn3d] Full video on my channel.

### gn4: dumping high cards (habits.dump_high 43.43)
On screen: "Don't throw your kings first"
[gn4a] Every beginner learns to throw kings and queens first in gin, because they count ten.
[gn4b] A bot that always dumps its highest card wins forty three percent of games.
[gn4c] Throw the card with the fewest partners instead. A lonely king goes. A queen next to a jack stays.
[gn4d] Full video on my channel.

### gn5: your opening hand (engine_check: 39.791 math, 39.793 engine)
On screen: "4 in 10 gin hands start with a meld"
[gn5a] In gin rummy, about four opening hands in ten already hold a set or a run.
[gn5b] You can count it exactly. Thirty nine point eight percent.
[gn5c] I dealt fifty six million hands to check my simulator, and it matched.
[gn5d] So if your first hand has nothing, that's normal. Six hands in ten don't. Full video on my channel.

## Exploding Kittens (numbers: episodes/exploding-kittens/script.md header)

### ek1: where to put the Kitten (placement next 30.2, bottom 23.7, random 25.05)
On screen: "Where should you put the Kitten back?"
[ek1a] When you defuse an Exploding Kitten, you get to put it back anywhere in the deck.
[ek1b] Bottom of the deck sounds safe. It's actually the worst choice I tested. Twenty four percent at a table of four.
[ek1c] Put it where the next player draws first, usually right on top, and you win thirty percent.
[ek1d] Full video on my channel.

### ek2: the Patient One (ranking 5 players: Patient 35.4, fair 20)
On screen: "The Exploding Kittens habit that wins"
[ek2a] At a table of five in Exploding Kittens, a fair share is one game in five.
[ek2b] The best bot I built wins more than a third of its games.
[ek2c] Its secret is patience. It saves its cards early, while the chance of exploding is low.
[ek2d] Full video on my channel.

### ek3: the first draw (engine check 3 in 23 = 13.04%)
On screen: "1 in 8 games: boom on the first draw"
[ek3a] In a four player game of Exploding Kittens, the very first card drawn is a Kitten about one time in eight.
[ek3b] Three Kittens in a deck of twenty three cards. Three in twenty three is thirteen percent.
[ek3c] My simulator said the same thing over ten million shuffles. That's how I know it plays by the real rules.
[ek3d] Full video on my channel.

### ek4: Nope cards (Nope never 21.2, always 26.9, normal 25.05)
On screen: "Save your Nope or use it?"
[ek4a] Should you save your Nope cards, or use them?
[ek4b] A bot that never Nopes wins twenty one percent at a table of four. One that always Nopes wins twenty seven.
[ek4c] Hoarding them is a mistake. Full video on my channel.

## Uno (numbers: episodes/uno/script.md header)

### un1: the worst house rule (draw until you can play 82.3 vs 47.1 turns; 1 in 10 rounds over 172)
On screen: "This Uno house rule ruins the game"
[un1a] One Uno house rule makes the average round seventy five percent longer.
[un1b] It's drawing until you can play. Official rules say you draw one card.
[un1c] With the house rule, one round in ten lasts more than a hundred and seventy turns.
[un1d] I tested every Uno house rule. Full video on my channel.

### un2: stacking (stacking 49.9 vs official 47.1 turns)
On screen: "Stacking +2s in Uno: what it really does"
[un2a] Stacking plus twos isn't in the official Uno rules. But does it change the game?
[un2b] Barely. Rounds get about three turns longer.
[un2c] The rule everyone fights about is not the one that ruins the game. Full video on my channel.

### un3: hold your Wilds (hold Wilds 28.8, fair 25)
On screen: "Stop playing your Wild early"
[un3a] In Uno, a lot of people play their Wild card the first chance they get.
[un3b] A bot that holds its Wilds until it needs them wins twenty nine percent at a table of four, where fair is twenty five.
[un3c] Hold them. Full video on my channel.

### un4: going first (first player 26.8, fair 25)
On screen: "Going first in Uno matters"
[un4a] Does going first matter in Uno?
[un4b] At a table of four, the first player wins twenty seven percent of rounds instead of twenty five.
[un4c] Small, but real. Over billions of rounds. Full video on my channel.

## Battleship (numbers: episodes/battleship/script.md header)

### bs1: how many shots (random 95.39, Calculator 44.3)
On screen: "Random shooting takes 95 shots"
[bs1a] If you shoot at random in Battleship, you need ninety five shots on average to sink the fleet. Almost the whole board.
[bs1b] The best shooter I built needs forty four.
[bs1c] It counts every way the ships could still fit, and fires where most of them overlap. Full video on my channel.

### bs2: don't cluster (clustered 36.6%, spread 59.2% vs Hunters)
On screen: "Never hide your ships like this"
[bs2a] Bunching your Battleship ships together feels sneaky. It's the worst way to hide them.
[bs2b] Against a normal shooter, clustered fleets win only thirty seven percent of games.
[bs2c] Spread them out so no two ships touch, and you win fifty nine. Full video on my channel.

### bs3: the checkerboard (Hunter 62.2 shots, Checkerboard 55.2)
On screen: "The Battleship checkerboard trick"
[bs3a] Here's a Battleship trick. While you're searching, only shoot every other square, like a checkerboard.
[bs3b] The smallest ship is two squares long, so it can't hide between your shots.
[bs3c] That one change saves seven shots a game, and wins sixty five percent against a normal hunter. Full video on my channel.

## Connect 4 (numbers: episodes/connect-4/script.md header)

### c41: first move (opening column: centre 49.3, edges 38.8; solver: only centre wins)
On screen: "The only winning first move in Connect 4"
[c41a] In Connect Four, only one first move wins with perfect play. The middle column.
[c41b] My solver checked every opening. The columns next to it draw. Everything else loses.
[c41c] Even for normal bots, starting in the middle wins forty nine percent. Starting on the edge, thirty nine. Full video on my channel.

### c42: going first (careful bots 45.7 vs 37.1, 17% draws)
On screen: "Always go first in Connect 4"
[c42a] Going first in Connect Four is a big deal.
[c42b] Between two careful bots, the first player wins forty six percent and the second only thirty seven. The rest are draws.
[c42c] So if you win the coin flip, go first, and start in the middle. Full video on my channel.

## Shut the Box (numbers: episodes/shut-the-box/script.md header)

### sb1: the house rule (any combination 7.14% vs sum or split 0.51%)
On screen: "Your Shut the Box rule makes it 14x harder"
[sb1a] Shutting the box with perfect play happens about one game in fourteen.
[sb1b] But some people play a stricter rule. You can only flip the sum, or the two dice separately.
[sb1c] With that rule, perfect play shuts the box about once in two hundred games. Fourteen times harder. Full video on my channel.

### sb2: smallest first (smallest first 1.05%, biggest first 6.96%)
On screen: "Flip the BIG tiles first"
[sb2a] In Shut the Box, flipping your smallest tiles first feels safe. It's the worst habit there is.
[sb2b] Smallest first shuts the box about once in a hundred games. Biggest first, almost seven times as often.
[sb2c] Biggest first is almost as good as perfect play. Full video on my channel.
