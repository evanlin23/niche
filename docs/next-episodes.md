# Next episodes (from the 2026-11-04 scans; raw data in docs/game-search-scan-*.txt)

Criteria: public rules/components, people actually play it, decisions to test (not pure luck), demand
(top-20 search views), and no strong simulation video already.

| # | Game & angle | Demand signal | Competition | Notes |
|---|---|---|---|---|
| 2 | **Uno: "I tested every house rule. One breaks the game."** + official-rules habits | "uno stacking rule" 13.9M, 0 sim videos | none | Teased at the end of video 1. Official rules (Mattel GDJ85) say no stacking, draw one. |
| 3 | **Battleship: where to hide your ships vs how to hunt** | 5.3M | a few "algorithm" videos, no placement study | Universal, rules public, great heat-map visuals. |
| 4 | **Monopoly Deal** | 6.4M | 0 sim videos | Deck list public (110 cards). Adjacent to PerfectPlay's Monopoly hit without copying it. |
| 5 | **Sorry!** | 11.6M | none | Rules public (Hasbro). Younger audience = lower RPM; good reach. |
| 6 | **Connect 4: beat your friends without memorising the solver** | 14.9M | 2swap "I Solved Connect 4" 1.7M | Human-usable rules of thumb vs perfect play. |
| 3b | **Shut the Box: "your house rule makes it 14x harder"** | ~1.3–2.7M (small) | dedicated videos ≤122K; an "I Solved Shut the Box" upload has 0 views | Public-domain pub game, **exactly solvable** (sims/shutbox/solve.py). Perfect play shuts 1–9 any-combination 7.14%; sum-or-split rule 0.51%; 1–12: 0.36% / 0.03%. Great for a short video + Shorts series; pairs with the Uno house-rule theme. |
| later | Skip-Bo (5.6M), Crazy Eights (4.1M), Go Fish (5.9M), Dominoes (6.0M), Phase 10 (3.1M), Yahtzee (2.4M, solved), Blackjack (22M, gambling = ad-unfriendly) | | | |

Rule of thumb from the scans: a specific, argued-about question ("is stacking allowed?") beats generic
"best strategy" searches by ~10x (uno stacking rule 13.9M vs uno strategy 1.2M).

---

# 2026-11-04 (c): 57 games screened, 14-episode plan (about 3 months at one a week)

Raw numbers: `docs/game-search-scan-2026-11-04c.txt` (yt-dlp, logged out, US, top 20 results per query).
Per game: "<game> strategy", "how to win <game>", the most argued rule (or rules search), and
"<game> simulated million games" for competition. **Demand** = combined views of the unique videos across the first
three queries whose title actually names the game (filters out Fortnite/Roblox/Minecraft noise). The figure in
brackets leaves out the single biggest video, because one viral upload can dominate (Monopoly: one MrBeast video is
142M of 186M).

## Benchmark: what Perfect Play's uploads did against the same market measure

| Their video | Views (checked 2026-11-04) | Uploaded | Market (top-result views) |
|---|---|---|---|
| Monopoly | 2.76M | 2026-10-13 | 186M (43.5M without MrBeast) |
| Catan | 325K | 2026-10-31 | 9.6M |
| Risk | 194K | Oct 2026 (date blocked) | 5.6M |
| Minesweeper | 46K | 2026-10-16 | 9.0M |

Lesson: market size alone doesn't predict views. Minesweeper has Catan's market and got a seventh of the views:
it's a solo game, so there's no "people at your table" cold open and no rival to beat. **The hits are multiplayer
games families argue over.** So the plan only takes multiplayer table games with a market of roughly 4M+,
and puts the biggest household names first.

## Scoring (1-5 each, total out of 25)
- **D**emand: by total demand, 12M+ = 5, 7-12M = 4, 4-7M = 3, 2-4M = 2, under 2M = 1; minus 1 if one video is over half of it.
- **C**ompetition: 5 = no simulation/data video above 10K views; 4 = 10-50K; 3 = 50-500K; 2 = 0.5-2M; 1 = over 2M,
  or Perfect Play already made it (we don't copy). Zero-view copycats ("Tested on N Million Games") don't count.
- **A**ngle: is there one specific question people already argue about?
- **V**erifiability: 5 = every number we need is in a publisher/governing-body source; 4 = publisher source with a
  small, stated gap; 3 = key numbers only on cards/boards or fan sites; 1-2 = unverifiable. Under 4 = not built.
- **S**imulability: real decisions to test and an engine fast enough for a billion games (1 = pure luck).

## Screened table (57 games)

| Game | Demand M (w/o top) | Biggest sim/data video | Angle (the question) | D | C | A | V | S | Tot | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| Sorry! | 15.1 (3.7) | copycat 0.6K | Sorry! is "all luck". Then why does one habit win far more? | 4 | 5 | 4 | 4 | 4 | 21 | **Plan 1 (build)** |
| Checkers | 7.8 (5.8) | checkersTV "Is checkers solved?" 233K | Do you really have to jump? The rule most families skip | 4 | 3 | 5 | 5 | 4 | 21 | **Plan 2 (build)** |
| Gin Rummy | 7.7 (4.3) | none over 2K | Knock now, or wait for Gin? | 4 | 5 | 4 | 4 | 5 | 22 | **Plan 3 (build)** |
| Mancala | 6.4 (4.2) | only 0-view copycats | Two printed rulebooks disagree on one rule, and it decides who wins | 3 | 5 | 5 | 4 | 5 | 22 | Plan 4 |
| Skip-Bo | 6.0 (3.2) | none | How much of Skip-Bo is luck? The discard-pile habit that matters | 3 | 5 | 4 | 4 | 4 | 20 | Plan 5 |
| Yahtzee | 3.9 (2.8) | Ballpark Figures "I Solved Yahtzee*" 1.1M | The highest-scoring strategy isn't the one that beats your family | 2 | 2 | 4 | 5 | 5 | 18 | Plan 6 (quick win, head-to-head angle Ballpark didn't cover) |
| Go Fish | 6.1 (4.6) | none | Does memory win Go Fish, or who you ask? | 3 | 5 | 3 | 5 | 3 | 19 | Plan 7 (quick win; kids, lower RPM) |
| Liar's Dice | 7.1 (2.2) | GTO video 1K | When should you call liar? | 3 | 5 | 4 | 4 | 4 | 20 | Plan 8 |
| Phase 10 | 4.2 (3.0) | 0-view podcast | Which Phase is the hardest? | 3 | 5 | 5 | 5 | 4 | 22 | Plan 9 (engine already built, see below) |
| Farkle | 2.7 (1.4) | 0-view copycats | Every family scores Farkle differently; one rule changes when to stop | 2 | 5 | 4 | 5 | 5 | 21 | Plan 10 (quick win) |
| Chinese Checkers | 5.4 (3.3) | none | Does going first win, and is the long hop chain worth it? | 3 | 5 | 3 | 4 | 4 | 19 | Plan 11 |
| Coup | 3.4 (1.6) | none | Should you ever tell the truth in Coup? | 1 | 5 | 4 | 5 | 3 | 18 | Plan 12 (quick win; teen/party audience) |
| Mexican Train | 4.3 (3.1) | none | Your train or the Mexican train? | 3 | 5 | 3 | 4 | 4 | 19 | Plan 13 (older audience, good RPM) |
| Cribbage | 4.7 (2.5) | none | Which two cards go in the crib? | 3 | 5 | 4 | 5 | 4 | 21 | Plan 14 (older audience, good RPM) |
| Solitaire (Klondike) | 9.5 (6.6) | 3.7K | Draw 3 vs Draw 1: how much harder? | 4 | 5 | 4 | 4 | 4 | 21 | Alternate: solo game (Minesweeper lesson) |
| Clue | 7.0 (5.6) | copycat 1.2K | Which suggestion habit finds the killer fastest? | 4 | 5 | 3 | 3 | 3 | 18 | Alternate: room distances are only printed on the board |
| Rummikub | 3.9 (2.3) | 2K | Hold the joker or play it? | 2 | 5 | 3 | 5 | 3 | 18 | Alternate: table-rearranging search is a large engine |
| Spades | 2.7 (1.6) | 1K | Is bidding nil worth it? | 2 | 5 | 4 | 3 | 3 | 17 | Alternate: Bicycle page has no nil/partnership scoring |
| Backgammon | 5.3 (3.0) | copycat 0 | When to take the double | 3 | 5 | 4 | 5 | 4 | 21 | Alternate: doubling cube = gambling-adjacent, strong bots (GNU BG) already public |
| Dominoes (draw/block) | 4.9 (3.6) | none | Lead your doubles first? | 3 | 5 | 2 | 3 | 4 | 17 | Alternate: folk rules, no publisher sheet (Mexican Train covers dominoes) |
| Monopoly Deal | 3.5 (1.5) | none | Bank it or play it? Is Just Say No the best card? | 1 | 5 | 4 | 3 | 4 | 17 | Rejected for now: rent per colour and property values printed only on cards (Hasbro B0965/E3113/G0351 sheets don't list them) |
| Ticket to Ride | 4.3 (3.0) | Math The World 32K | Long routes or many tickets? | 3 | 4 | 3 | 3 | 3 | 16 | Rejected: route map and ticket list only on board/cards |
| Scrabble | 13.3 (8.7) | copycats 0 | Keep the S? Exchange or play? | 5 | 5 | 3 | 4 | 2 | 19 | Rejected: official word list is licensed; move generation too slow for billions |
| Crazy Eights | 4.2 (2.9) | none | When to play your 8 | 3 | 5 | 2 | 4 | 3 | 17 | Rejected: too close to our Uno episode (maybe a Short) |
| Codenames | 9.4 (7.0) | none | - | 4 | 5 | 2 | 4 | 1 | 16 | Rejected: word association, can't be simulated honestly |
| Guess Who | 76.8 (45.8) | Mark Rober 31M | - | 5 | 1 | 3 | 4 | 4 | 17 | Rejected: Mark Rober's video owns the question |
| Monopoly | 186 (43.5) | Perfect Play 2.76M; b2studios 12.1M | - | 4 | 1 | - | 5 | 4 | - | Rejected: Perfect Play's hit, we don't copy |
| Catan | 9.6 (6.7) | Perfect Play 325K; Ioana Roman 394K | - | 4 | 1 | - | 4 | 4 | - | Rejected: Perfect Play |
| Risk | 5.6 | Perfect Play 194K; Numberphile 1.2M | - | 3 | 1 | - | 4 | 4 | - | Rejected: Perfect Play |
| Minesweeper | 9.0 (7.0) | Perfect Play 46K | - | 4 | 1 | - | 5 | 4 | - | Benchmark only (Perfect Play, solo) |
| The Game of Life | 28.9 (14.1) | Mark Rober segment | College or career? | 4 | 2 | 5 | 2 | 4 | 17 | Rejected: card/space values only printed on components (see LESSONS) |
| Snakes and Ladders | 9.7 (5.9) | Vsauce2 2.5M; Numberphile 238K | - | 4 | 1 | 2 | 4 | 1 | 12 | Rejected: pure luck, already covered |
| Candy Land | 36.7 (18.4) | 0-view copycat | - | 4 | 5 | 2 | 2 | 1 | 14 | Rejected: pure luck; deck mix not on the sheet |
| War | 16.0 (0.9) | - | - | 4 | 5 | 1 | 5 | 1 | 16 | Rejected: pure luck (demand is one Fortnite video) |
| Left Center Right | 1.5 (0.8) | - | - | 1 | 5 | 1 | 4 | 1 | 12 | Rejected: pure luck |
| Hearts | 1.2 (0.6) | - | Shoot the moon? | 1 | 5 | 4 | 4 | 4 | 18 | Rejected: low demand |
| Euchre | 1.9 (1.3) | - | Stick the dealer? | 1 | 5 | 4 | 4 | 4 | 18 | Rejected: low demand, regional |
| Sushi Go | 1.3 (1.0) | - | - | 1 | 5 | 3 | 4 | 4 | 17 | Rejected: low demand |
| Love Letter | 0.6 (0.4) | - | - | 1 | 5 | 3 | 4 | 3 | 16 | Rejected: low demand |
| Five Crowns | 1.8 (1.1) | - | - | 1 | 5 | 3 | 5 | 4 | 18 | Rejected: low demand |
| Can't Stop | 0.2 (0.1) | - | - | 1 | 5 | 4 | 4 | 5 | 19 | Rejected: tiny demand |
| Qwixx | 1.1 (0.9) | - | - | 1 | 5 | 3 | 4 | 4 | 17 | Rejected: low demand |
| Trouble | 0.8 (0.4) | - | - | 1 | 5 | 2 | 3 | 2 | 13 | Rejected: low demand, few decisions |
| Stratego | 1.2 (0.8) | copycat 5K | - | 1 | 5 | 3 | 4 | 3 | 16 | Rejected: low demand |
| Dots and Boxes | 2.8 (0.6) | Numberphile 2.2M | - | 1 | 1 | 3 | 4 | 4 | 13 | Rejected: covered |
| 2048 | 8.4 (6.3) | Steve Mould 652K | Corner strategy? | 4 | 2 | 3 | 5 | 4 | 18 | Rejected: solo, covered |
| Balatro | 14.5 (12.7) | none | - | 5 | 5 | 3 | 2 | 2 | 17 | Rejected for now: numbers only from fan wiki, huge engine |
| Blackjack | 39.8 (26.9) | big math channels | - | 5 | 2 | 2 | 4 | 4 | 17 | Rejected: gambling = ad-unfriendly, crowded |
| Poker | 38.5 (27.9) | many | - | 5 | 1 | 2 | 4 | 3 | 15 | Rejected: gambling, crowded |
| Rock Paper Scissors | 45.2 (29.7) | Primer 4.6M; Numberphile 4.9M | - | 5 | 1 | 2 | 5 | 2 | 15 | Rejected: covered, answer is "random" |
| Chess | 60.9 (53.4) | many | - | 5 | 1 | 2 | 5 | 2 | 15 | Rejected: crowded, engine bots are the whole genre |
| Mahjong | 26.6 (13.9) | none | - | 5 | 5 | 3 | 2 | 2 | 17 | Rejected: rules differ by country; US card (NMJL) is copyrighted, changes yearly |
| Hangman | 32.3 (18.2) | jan Misali 7.4M | Best first letter | 5 | 1 | 3 | 2 | 3 | 14 | Rejected: covered; folk rules, word list choice |
| Sudoku | 26.0 (19.1) | Numberphile 6.9M | - | 5 | 1 | 2 | 5 | 2 | 15 | Rejected: solo puzzle, covered |
| Othello | 2.6 (1.9) | solved 2023 | - | 2 | 3 | 2 | 4 | 4 | 15 | Rejected: low demand |
| Spider Solitaire | 0.6 (0.4) | - | - | 1 | 5 | 3 | 4 | 3 | 16 | Rejected: solo, low demand |
| FreeCell | 1.0 (0.7) | 7K | - | 1 | 5 | 3 | 4 | 3 | 16 | Rejected: solo, low demand |

## The 14-episode plan

Order rule (2026-11-04, from the creator): the biggest household-name **multiplayer** games first; after that,
alternate a big-audience game with a quick win (small engine); never two near-identical games back to back
(rummy-style games, dice games and the two checkers games are kept apart; Skip-Bo and Phase 10, both Mattel family
card games, too).

| # | Game | Working title | Hook (one line) | Experiments (3-5) | Engine |
|---|---|---|---|---|---|
| 1 | Sorry! | I Played a Billion Games of Sorry! Your Family Is Moving the Wrong Pawn | "It's a luck game. Then why does one habit win almost twice as often?" | which pawn to move (rush one vs spread); the 11 swap (always / only forward / never); split 7 or not; back up with the 4 near Start; Sorry! target (leader vs nearest); house rules: draw-again on 2, slide on your own colour, 5-card adult variation (luck vs skill) | M |
| 2 | Checkers | You Have to Jump. I Tested What Happens If You Don't | "Half of you have been playing checkers wrong, and it changes who wins" | forced-capture rule vs optional capture ("huffing"); first-move advantage; keep the back row; trade down when ahead; centre vs edges | M |
| 3 | Gin Rummy | Knock or Go for Gin? A Billion Hands Settle It | "Knocking the second you can is the most common mistake" | knock at 10 vs wait for low deadwood vs Gin only; when to take the upcard; discarding high cards early; reading the opponent's pickups; undercut risk | M |
| 4 | Mancala | Two Mancala Rulebooks Disagree. One Rule Decides Who Wins | "Who gets the leftover stones? Your answer changes the winner" | both printed end-of-game rules; capture-on-empty variants; first player advantage (exact solve where possible); greedy extra-turn vs capture bots | S |
| 5 | Skip-Bo | How Much of Skip-Bo Is Luck? | "A perfect Skip-Bo player still loses ... of games" | discard-pile organisation; playing Skip-Bo cards early vs saving; blocking the next player; stock-first vs hand-first; luck share (best vs random play) | M |
| 6 | Yahtzee | The Yahtzee Strategy That Scores Most Loses to Your Family | "Max points and max wins are different strategies" | chase the upper bonus; when to scratch Yahtzee; the Joker rule; head-to-head habits vs score-maximising | S |
| 7 | Go Fish | Does Memory Win Go Fish? | "Remembering who asked for what is worth ..." | memory vs no memory; who to ask; asking for your biggest set; player count | S |
| 8 | Liar's Dice | When to Call Liar | "There's a number that tells you when to call" | call threshold; bluff rate; wild ones vs not; player count | M |
| 9 | Phase 10 | Which Phase Is the Hardest? | "It isn't the one everyone complains about" | in-game completion rate per Phase; taking from the discard pile; laying down right away vs waiting; who to Skip; hitting on others' Phases | M (built) |
| 10 | Farkle | Every Family Scores Farkle Differently | "One scoring rule flips when you should stop rolling" | stop thresholds; PlayMonster vs other scoring tables; 500 to get on the board | S |
| 11 | Chinese Checkers | Does Going First Win Chinese Checkers? | "The first-move edge, and the hop chain that wins" | first-move edge by player count; hop-chain vs single-step bots; leaving a back marble | M |
| 12 | Coup | Should You Ever Tell the Truth in Coup? | "Honest players win ...%" | bluff rate; challenge threshold; who to target; 2-player rule | S |
| 13 | Mexican Train | Your Train or the Mexican Train? | "Most players start the wrong train" | own train first vs Mexican train; play doubles early; hoarding high tiles | M |
| 14 | Cribbage | Which Two Cards Go in the Crib? | "Your crib throw costs you ... points a game" | discard rules of thumb vs exact best throw; pegging habits; first-dealer edge | M |

Alternates if one fails a check: Solitaire (Klondike), Backgammon, Rummikub, Spades, Clue (if the board can be verified).

### Rules sources for the 14 (checked 2026-11-04) and what's still unverified
1. **Sorry!**: Hasbro classic 00390 (2003) https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/d0dc3b91-28ec-4f9a-b32b-31306ae2cb17/af23343336930172b83a82fd2897c930.pdf ;
   Hasbro Retro 1958 edition B3218 (deck mix: 44 cards, four each of 1,2,3,4,5,7,8,10,11,12 and Sorry!, plus one extra 1;
   60 margin squares; 5 safety squares) https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/168f2cc8-37c4-4780-83ac-b5b6c5e2ce3e/B3218CV00_I_Retro_Sorry_ENG_P1_1_FAR.pdf ;
   Hasbro A5065 (2020, board diagram) https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/4c59d570-cc28-4577-b8b2-21a3e159a534/A5065A440_418895_SORRY_20_INST.pdf .
   *Unverified in text:* slide lengths and positions (4 and 5 squares) come from counting the printed board diagram; the
   modern 45-card mix is inferred from the 1958 list (44 + the extra 1 = 45, matching "45 cards" on modern sheets).
2. **Checkers**: Hasbro B7718 (2015, "you must jump") https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/9f2031f8-db2b-4af0-90d2-bc8aa2c66478/B77180000%20SW%20Checkers%20INST.pdf ;
   WCDF rules (adopted by the American Checker Federation) https://wcdf.net/rules/rules_of_checkers_english.pdf . *Unverified:* nothing needed.
3. **Gin Rummy**: Bicycle https://bicyclecards.com/how-to-play/gin-rummy (knock at 10 or less, Gin 20, undercut 10, game 100,
   game bonus 100, 20 per hand won). *Unverified:* what happens when the stock runs out, and laying off against Gin
   (Bicycle is unclear; Pagat differs). We'll state the rule we use on screen.
4. **Mancala**: Endless Games "Classic Mancala" (2015) https://www.buffalolib.org/sites/default/files/gaming-unplugged/inst/Mancala%20Instructions%20Copy%201.pdf ;
   Wood Expressions sheet https://www.smithsonianstore.com/product_images/uploaded_images/Mancala_Instructions.pdf .
   *Unverified:* there is no single official rulebook; the two disagree on who gets the leftover stones (that's the episode).
5. **Skip-Bo**: Mattel 42050 (1999) https://service.mattel.com/instruction_sheets/42050.pdf (144 numbered 1-12 + 18 Skip-Bo = 162;
   30 stock cards for 2-4 players, 20 for 5+; 4 building piles; 4 discard piles each; 5-card hand). *Unverified:* "12 of
   each number" is implied (144 = 12 x 12) but not printed.
6. **Yahtzee**: Hasbro C2406 (2016) https://assets-us-01.kc-usercontent.com:443/500e0a65-283d-00ef-33b2-7f1f20488fe2/dc9b58d3-d756-4880-abec-f3cd01ce01fd/C24060000_Yahtzee_Classic_17_INST.pdf . Complete.
7. **Go Fish**: Bicycle https://bicyclecards.com/how-to-play/go-fish (7 cards for 2-3 players, 5 for 4-5, books of 4).
   *Unverified:* whether drawing the asked-for rank from the pond gives another turn.
8. **Liar's Dice**: Asmodee Perudo rules (French/Spanish) https://www.magasindejouets.fr/img/cms/regles/asmodee/regles-du-jeu-perudo.pdf ;
   RNK Sales https://rnkgaming.com/wp-content/uploads/2021/03/Liars-Dice-Rules.pdf . *Unverified:* no English publisher
   sheet for Perudo; the Milton Bradley 1987 "lose the difference" rule.
9. **Phase 10**: Mattel HHR41 (2021, 40th anniversary) https://service.mattel.com/instruction_sheets/HHR41-Eng.pdf ; older Mattel
   W5800 sheet https://service.mattel.com/instruction_sheets/w5800i.pdf (same deck). *Unverified:* what happens when the draw
   pile runs out (sheet is silent; we reshuffle the discards).
10. **Farkle**: PlayMonster (2016) https://www.playmonster.com/wp-content/uploads/2018/06/Farkle-Rules.pdf . Other printed tables differ
   (Elverson: three 1s = 1,000 and a three-Farkle penalty), which is the angle.
11. **Chinese Checkers**: Maple Landmark 50303 sheet https://maplelandmark.com/client_media/files/Instructions/50303%20Chinese%20Checkers%20Instructions.pdf .
   *Still to read in full:* jump/move wording and whether you may stop in other players' points.
12. **Coup**: Indie Boards & Cards rulebook (third-party host) https://upload.snakesandlattes.com/rules/c/Coup.pdf . Complete for the base game.
13. **Mexican Train**: Puremco / University Games 54006 (2016) https://www.universitygames.com/_files/ugd/05f72c_4adf51aa5fdc4239904bf079809cfc78.pdf .
   *Unverified:* the sheet marks double-12 as 4+ players only; the 50-point double-blank appears only in its Chickenfoot section.
14. **Cribbage**: American Cribbage Congress rulebook (2025) https://www.cribbage.org/NewSite/rules/rulebook_2025.pdf . Complete.

### Where things stand (2026-11-04, end of session)
- **Built and simulated (plan 1-3):** Sorry! (1,006,250,000 games, Actions run 41872745692), Checkers
  (1,022,544,000 games, run 41874542377), Gin Rummy (1,008,000,000 full games to 100 = 10.2 billion hands, run 41875817486).
  Each has RULES.md, a Go engine with rule tests in sims/<slug>, experiments.py, merged data/results.json and a
  lint-clean script.md draft. Engine checks and mirror checks are recorded in each data file.
- **Phase 10** (was planned #1 before the creator moved the household names first): Go engine `sims/phase10`, rule
  tests (phase detector checked against a brute-force solver), mirror check (4 equal bots: 24.6-25.5% per seat) and
  the engine check (deal odds for all ten Phases match exact combinatorics within 0.01 points) are done and committed.
  Pilot: never taking from the discard pile wins 3.6% at a 4-player table (fair share 25%); waiting for someone else
  to lay down first 21.6%; not hitting on other players' Phases 17.2%. In-game, Phase 7 (two sets of four) is the
  least often completed. Big run and script are parked until its slot.
- Findings that changed the plan: in Checkers the forced-jump rule doesn't have one simple effect (more draws without
  it for casual players, fewer for stronger ones); in Gin Rummy the knock-or-wait answer flips with the undercut bonus.
