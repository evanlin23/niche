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

## 3. Shortlist, ranked
1. **Chess from real games: what actually wins at your rating.** Lichess publishes every rated game for free, and its
   opening explorer gives win rates by rating band without any download. Code does the analysis and draws the board;
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
explorer (free, no download), one question each ("Is the Fried Liver trap worth it under 1000?"). They need a board
template (new visual code) and narration. Map Shorts (lane E) come next, once a map template exists; they need no voice.
