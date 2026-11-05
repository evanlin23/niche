# Automatable niches: gap radar (research 2026-11-05)

Question from the creator: which niches, games or not, can be made mostly by code (simulation, exact maths, public data,
code-made visuals, narration optional), and where is the empty gap that Perfect Play found for board games (section 8
of `docs/simulation-niche-research.md`)?

Raw data: `docs/gap-radar-2026-11-05.txt` (64 topics, 36 game, puzzle, gambling or sports and 28 not; 4 searches each:
a "demand" query, a "data or simulation" query, and both again with YouTube's "this year" filter; top 20 results each;
5,120 results plus a 240-result chess and puzzle follow-up) and `docs/gap-radar-2026-11-05.json` (per-topic sums and
20 channels with their latest 20 long videos and Shorts). Same limits as before: view counts of search results, not
search volume; one logged-out snapshot; "this year" is YouTube's filter (uploaded in 2026).

## 1. Automatable formats that are growing right now
Median views of the latest 20 long videos vs subscribers (above 1 means the algorithm pushes them beyond their base):
| Channel | Subs | Median | Ratio | What it is |
|---|---|---|---|---|
| Mapocalypse | 7.6K | 34K | 4.5 | 40-min "I Simulated..." on real maps ("I Simulated Yellowstone Erupting, Day by Day" 67K) |
| Data Vision | 2.3K | 9.5K | 4.1 | world-map data explainers |
| MotionAthlete | 190K | 549K | 2.9 | short 3D sports simulations ("How Much Do Hurdles Actually Slow You Down? 3D Realistic Simulation" 141K) |
| Cottereau | 291K | 505K | 1.7 | 2-min map animations from data ("History of the World: Every Year" 3.1M; "Assembling France by Average Income" 101K) |
| Memeable Data | 276K | 478K | 1.7 | 11-min "Every Level of ..." data explainers ("Every Level of Population Collapse in 13 Minutes" 1.1M) |
| We Love Stats | 20.6K | 33K | 1.6 | data bar-chart races |
| MetaBallStudios | 1.98M | 1.0M | 0.5 | 3D size comparisons; titles carry "(3D without AI)" |
| ExtinctZoo | 1.55M | 683K | 0.4 | animated science comparisons |
| Reigarw Comparisons | 2.14M | 545K | 0.25 | "Probability Comparison" videos |
| WatchData / Infinite Comparison | 1.69M / 808K | 90K / 53K | 0.05-0.07 | "Comparison: ..." videos, fading |
| Doomsday Math | 1.4K | 2.4K | 1.8 (tiny) | "What If ... We Ran 10,000 Simulations": the copycat template, now in disasters |

What it says: map and data animation, real-map simulations and 3D sports physics are growing. Generic "comparison"
channels are fading. MetaBallStudios advertising "without AI" shows viewers are wary of AI content, so "made with
code, checked against real data" is worth saying on screen.

## 2. Where demand is big and fresh supply is thin
| Topic | Demand (top-20 views) | Best data or simulation video | Verdict |
|---|---|---|---|
| **Chess, from real games** | "statistically best chess opening" 25.2M; "chess opening win rate by rating" 35.7M (GothamChess "BEST Chess Openings by Elo" 4.57M) | Lichess-database videos total 0.6M all-time; this year's best is "10 Gambits That Actually Win (89 Million Lichess Games)", 41K | **the biggest gap found**: a huge audience, free data, almost no data videos |
| Asteroid impact what-if | 42.6M; this year's median 10K | MetaBallStudios "ASTEROID IMPACT Comparison" 10.4M (old); ExtinctZoo 961K this year | open for real-science impact simulations |
| Megaquake, supervolcano | 34.3M; few results this year | Doomsday Math 336K (template channel); Mapocalypse Yellowstone 67K | open, but copycats are arriving |
| Hurricanes | 14.6M; none this year in the top 20 | a TV-station storm simulator, 4.1M | seasonal (June to November) |
| Three-body problem | 42.9M; 3.0M this year | Popperish's three-star simulations 140K (§5) | physics simulations, smaller |
| Zombie outbreak | 28.9M; 14.1M this year, median 510K | Brute Force Lab "I Released One Zombie in Manhattan" 650K | live, getting crowded |
| Mario Kart stats | 22.2M | best data video this year 94K | game-specific, mid-sized |
| Rent vs buy, investing backtests | 19.6M / 6.9M | Logical Money 1.96M this year | high ad rates, crowded by finance creators |
| NYT puzzles | Connections brute force 297K (Cael4Scale, 3.2K subs); Strands and Spelling Bee near zero | | small |
| Size and speed comparisons | 495.6M / 127.4M, still live (4.0M and 17.3M videos this year) | | huge, owned by million-sub incumbents |
| Squid Game | 29.0M all-time, 0.5M this year | | the fad is over |

## 3. Shortlist, ranked (first pass; section 5 rechecks it against real searches)
1. **Chess from real games: what actually wins at your rating.** Lichess publishes every rated game monthly under CC0
   (database.lichess.org: "Use them for research, commercial purpose, publication, anything you like"). Its opening
   explorer gives win rates by rating band, but now needs a free Lichess API token (our request got a 401). Code does the analysis and draws the board;
   a chess engine marks the mistakes. Example titles: "The Opening That Wins Most Under 1200", "The Move That Loses the
   Most Games at Every Rating", "Does the London System Actually Win More?". It's multiplayer and about beating real
   people, and it uses real human games rather than bots, a stronger claim than ours or Perfect Play's. Their viewers
   ask for chess ("Chess when?!"), so be first. Risk: chess fans are experts and will check every claim (our checks
   are the answer). Narration needed.
2. **Map data animations (Shorts first, music only).** Cottereau's model applied to public data (census, Natural Earth
   boundaries): "Every town in X", "Assembling the US by income". Data maps, not hand-drawn history maps. This is the most
   automatable lane and needs no voice. A map template is new visual code (about a day).
3. **Science what-ifs simulated on real maps** (asteroid impact, megaquake, supervolcano ash, storm surge, zombie spread):
   the closest fit to our simulation strength, using published models and public population data. Mapocalypse's ratio
   (4.5) shows the demand. Risks: the template copycats have arrived (Doomsday Math), real disasters need a careful
   tone, and long videos run 40 minutes.
4. **3D sports physics** (MotionAthlete's ratio 2.9): needs athlete animation, so it's harder. Later.

Not recommended: generic comparisons (fading), size and speed comparisons (incumbents with millions of subscribers),
finance (crowded, credibility-heavy), Squid Game (fad over).

## 4. How to test cheaply
Add chess as lane D in the Shorts probe (`docs/simulation-niche-research.md` §7.2): three Shorts from the Lichess opening
explorer (free, needs an API token from a Lichess account) or one monthly CC0 database file, one question each ("Is the Fried Liver trap worth it under 1000?"). They need a board
template (new visual code) and narration. Map Shorts (lane E) come next, once a map template exists; they need no voice.

## 5. Gaps that pass the creator's four tests (second pass, 2026-11-05)
The tests: everyone has played it, people want to win, they search how to win, and "simulated" or "solved" makes the
answer believable. Raw data: `docs/win-intent-scan-2026-11-05.txt` and `docs/win-intent-2026-11-05.json`.

**Method.**
- **What people want to win:** YouTube's own autocomplete for "how to win at", "how to always win", "how to beat",
  "best strategy for" and similar, each followed by every letter and 100 two-letter starts. That gave 5,749 real
  suggestions.
- **Ranking:** how many of those suggestions name each thing (chess 34, nim 29, Monopoly 22, rock paper scissors 22,
  blackjack 19, Risk 19, Fortnite 16, tic-tac-toe 16, poker 15, Uno 15, mancala 15, ...).
- **Checks:** 58 candidates, each searched as "how to win at X" and "X solved simulated math" (all time and this
  year), plus a look at who owns the top results. The section 3 lanes were rechecked with 25 real autocomplete
  searches each.

| Candidate | Top-20 "how to win" results | Who owns them | Verdict |
|---|---|---|---|
| **Chess, from real games** | "how to win at chess every time" 32.3M; "is the london system good" 22.5M; "chess opening win rate" 41.9M | chess personalities (GothamChess has 386M across these searches). Data channels: wintrcat (31.9K subs, median 84K, "Rare Anomalies in Chess" 1.2M) and Man vs Chess (1.3K subs, median 922; "10 Gambits That Actually Win (89 Million Lichess Games)" 41K) | **the one big open gap**: nobody answers "what wins at your rating" with data |
| Guess Who | 92.7M | Mark Rober "BEST Guess Who Strategy- 96% WIN record" 31.0M | taken |
| Tic-tac-toe | 38.5M | DaveHax 15.4M; "There are Exactly 14 Different Games of Tic-Tac-Toe" 7.8M | taken |
| Mario Party | 29.3M | ZoomZike's "Identifying Luck: Mario Party" series (105K subs, median 103K) | taken |
| Claw machines | 40.5M | Vox "It's not you. Claw machines are rigged." 10.0M; Arcade Matt (1.85M subs) | taken |
| Pool, bowling, ping pong | 15-37M | lesson channels; Stand-up Maths' pool video 1.2M | skill games: practice is the answer, not simulation |
| Mario Kart World | 8.3M | tips channels; Nathaniel Bandy's item ranking 4.4M | mid-sized; mechanics only from fan datamines |
| Go Fish, BS, War, Solitaire, Monopoly Deal | the real how-to videos get 1-4M each (bigger totals came from unrelated games with the same name) | wikiHow and how-to channels | small on YouTube |
| Hide and seek, musical chairs, dodgeball | 56-240M | MrBeast, Ben Azelart, children's songs | kids' content; a simulation would look like a toy |
| Mancala, dominoes, euchre, nim, dots and boxes, chopsticks | under 7M each | | small; fine for Shorts |
| Blackjack, poker, roulette | blackjack 30.3M (§2) | casino streamers, template channels | passes, but it's gambling: advertiser limits |

**What this changes.**
1. **Chess from real games is the only large gap that passes all four tests.** wintrcat shows data chess can grow fast,
   with curiosities ("Rare Anomalies"). Nobody does "how to win at your rating, from 90 million real games". Before
   committing, give it the same deep check our board games got: the top 50 chess channels, Shorts, and the copycats.
2. **Most universal games already have one big data or maths video** (Mark Rober, Vox, ZoomZike, Perfect Play,
   2swap, Ballpark Figures) or are small on YouTube. Our family-game lane (Uno, Exploding Kittens, Sorry!, Gin,
   Checkers) is mid-sized but has no data winner yet.
3. **Section 3's lanes 2 and 3 fail the tests:** there is nothing to win. Their real searches are owned by kids' songs
   and game-map comparisons (maps) and by Kurzgesagt, What If and RealLifeLore (what-ifs). Treat them as side ideas.
4. **Search intent for our own plan:** in the "how to win" autocomplete, Uno appears 15 times, mancala 15, Battleship
   12, Connect 4 10, Exploding Kittens 8, Gin Rummy 7, Checkers 7 and Yahtzee 6. Sorry!, Phase 10, Skip-Bo, Farkle and
   Cribbage don't appear at all; for Sorry! that may only be because "sorry" is a common word.
5. **Limits:** search-result views aren't search volume; autocomplete counts are a rough popularity signal; one
   logged-out snapshot.
