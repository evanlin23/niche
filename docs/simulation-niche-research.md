# The wider "simulation" niche on YouTube (research 2026-11-05)

Raw data: `docs/sim-niche-scan-2026-11-05.txt` (39 topics x 4 searches, top 20 results each, 3,120 results) and
`docs/sim-niche-channels-2026-11-05.json` (30 channels: subscribers + their 12 latest long videos). Method as in the
game scans: yt-dlp, logged out, US. Limits: view counts of search results (not search volume), one snapshot,
long-form only (Shorts not measured), and the latest 12 uploads have no dates, so "recent" means "latest 12".

## 1. "Simulation" means five different things on YouTube

| Lane | Who | Size | Fit for us |
|---|---|---|---|
| **Real-life "Simulating X for 100 days"** (terrariums, animals, eggs) | Dr. Plants (6.0M subs, median of latest 12 videos 80M), TerraGreen (4.6M, 10.5M), Aquarium Info (6.3M, 8.5M), Leafy Street (1.7M, 3.1M) | the biggest by far: Dr. Plants alone is 1.5B views across our searches | none: it's filmed, not computed. It also means "simulating" in a title doesn't signal "code" to viewers |
| **Game-world events** ("1000 players simulate civilization", Minecraft) | Grox (8.1M subs, median 43.5M), MrBeast Gaming, ish (2.2M, 0.9M), MARCUSK (0.7M, 3.9M) | huge, needs hundreds of real players | none |
| **Satisfying physics / marble races** | MIKAN (3.1M subs, median 5.9M), Kawaken 3DCG (0.6M, 1.8M), C4D4U (2.4M, ~10K), Jelle's Marble Runs (1.5M, 30K), Fubeca's (1.1M, 40K) | collapsing: most have big subscriber counts and tiny recent views (MIKAN is the exception) | low: crowded, low RPM, little to say |
| **AI learns / agents** (reinforcement learning) | AI Warehouse (0.8M subs, median 4.9M), Code Bullet (3.5M, 2.0M), b2studios (0.4M, 0.2M; "AI Learns Insane Monopoly Strategies" 12.1M), Pezzza's Work (0.2M, 0.1M), Emergent Garden (0.3M, 0.3M) | strong at the top | possible side lane, but training agents and 3D physics are a different production |
| **Data / strategy simulation** (our lane) | Primer (1.9M subs, median 1.7M), 2swap (0.4M, 1.9M), Ballpark Figures (40K subs, median 1.0M), Perfect Play (about 10K subs, median 270K, Monopoly 2.7M), euverus (20K subs, one 33M video: "Traffic flow measured on 30 different 4-way junctions") | mid-sized but **the best views-to-subscribers ratios in the whole scan** | ours |

Also seen: sandbox comedy ("I built a parking lot that traps people", Let's Game It Out 6.6M subs, median 3.3M;
GrayStillPlays 8.6M subs, median 0.3M) and sports re-simulations ("I simulated the next 10 years of NBA history",
Med 0.5M subs, median 0.4M; Clique Productions, Danny2K 0.4-0.8M; "World Cup with every country", Ghiellini).

## 2. Who's winning right now (views per video vs subscribers)
| Channel | Subs | Median views, latest 12 | Ratio | What they do |
|---|---|---|---|---|
| Perfect Play | ~10K | 270K | ~30 | game strategy "tested on N million games" (our closest competitor) |
| Ballpark Figures | 40K | 1.0M | ~28 | 30-45 minute "I Solved Wordle / Yahtzee / Hangman" |
| Dr. Plants | 6.0M | 80M | 13 | real-life terrariums (different niche) |
| AI Warehouse | 0.8M | 4.9M | 6 | "AI Learns to ..." |
| Grox | 8.1M | 43.5M | 5 | Minecraft villager events |
| MARCUSK | 0.7M | 3.9M | 5 | Minecraft civilization events |
| 2swap | 0.4M | 1.9M | 5 | maths/game solving ("I Solved Connect 4") |
| Primer | 1.9M | 1.7M | 0.9 | evolution / game theory with blobs |
| Code Bullet | 3.5M | 2.0M | 0.6 | coding comedy, AI learns |

Takeaway: **small channels doing careful "I solved / I tested" strategy videos are being pushed hard by the
algorithm right now** (ratios of 28-30). That's direct evidence for our format, and a warning: Perfect Play and
Ballpark Figures are in the same space, so packaging and topic choice decide who gets the views.

## 3. Topics people search that need simulation, and who already owns them
| Topic | Top-result views (4 searches) | Simulation-style competition | Verdict for us |
|---|---|---|---|
| Plane boarding | 75M | CGP Grey "Fastest way to board a plane" 37.5M | skip: owned |
| Traffic / junctions | 108M | CGP Grey 44.6M; euverus 33.6M (20K-sub channel) | a "tested 30 designs" comparison can still go viral; we already have a traffic episode |
| Checkout lines / queues | 36M (mostly comedy) | only a 0-view "Why you always pick the wrong queue (Solved)" | **open**: our backlog's "other line" episode |
| Elevators | 31M (explainers) | none with real data | open, smaller |
| Parking | 102M (mostly driving lessons) | "AI Learns to Park" 3.1M; Let's Game It Out comedy | open for "where to park: closest spot vs first spot you see" |
| Dating / optimal stopping (37% rule) | 103M (mostly unrelated) | Veritasium-style maths | crowded by big explainers |
| Wealth inequality / economy | 73M | Primer "Simulating Supply and Demand" 4.9M | crowded at the top |
| Game theory / evolution | 188M / 137M | Primer (25M, 15.8M) | skip: Primer owns it |
| Epidemics | 450M (one COVID animation) | Primer 6.2M, 3Blue1Brown 5.2M | skip: owned |
| Monty Hall / probability paradoxes | 65M | Vsauce2, Veritasium | skip as long videos, maybe Shorts |
| Lottery | 103M (MrBeast 58.8M) | Python tutorials only | gambling-adjacent; one "how long until you win" Short at most |
| Stock market / trading | 53M | "I made a market simulation to see if patterns are real" 1.2M | finance, high RPM, crowded by finance creators |
| Personal finance Monte Carlo | 3.9M | almost nothing | high RPM but tiny search demand |
| Sports re-simulations | NBA 11M, soccer 54M, other 7M | Med/Clique/Danny2K 0.3-0.8M; "I simulated the World Cup 10,000 times" 0.4M | possible seasonal side series (NBA/NFL seasons, March Madness, 2028 Olympics) |
| Battle simulators (army vs army) | 525M | UEBS/TABS channels, but RTS Battle Room's recent median is ~10K | saturated, low value |
| AI learns to play | 166M | AI Warehouse, Code Bullet, b2studios | strong but different production |
| Sorting / pathfinding visualizers | 65M | old viral videos (15 sorts 29M) | saturated |
| Rubik's cube / solvers | 492M (tutorials) | tutorials | not our format |

## 4. What this means for Buh Simulates
1. **Stay in the data-strategy lane, with games at the centre.** It has the best growth signal in the whole scan,
   and our engines, checks and billion-game runs are exactly what makes those channels credible.
2. **Out-package the direct competitors.** Perfect Play and Ballpark Figures prove the demand. Our edge must be:
   a specific argued-about question per video (never "the best X strategy"), multiplayer games, honest numbers, and
   visuals that look different from Perfect Play's.
3. **Borrow formats that work:**
   - "I tested every X" comparisons (euverus: 33M views at 20K subscribers for 30 junction designs measured side by side).
     For us: "I tested every house rule", "every opening", "every card".
   - Longer "I solved X" deep dives (Ballpark Figures runs 30-45 minutes) for the biggest games.
   - "AI learns" style packaging for a game where a bot trains itself, if we ever add self-play.
4. **Adjacent topics with open space** (everyday decisions people argue about, no simulation competitor found):
   which checkout line, where to park, elevators, plus the game-show maths and White Elephant ideas from
   `docs/next-episodes.md`. Good as Shorts and occasional long videos.
5. **Avoid:** plane boarding, traffic in general, epidemics, evolution and game theory (CGP Grey, Primer and
   Veritasium own them); marble races and satisfying physics (collapsing); battle simulators (saturated); anything
   titled "Simulating X for 100 days" (viewers expect live animals).
6. **Seasonal side series:** sports re-simulations are a steady 0.3-0.8M per video for small channels. NBA and NFL
   seasons, March Madness and the 2028 Olympics give natural dates. This is a different audience from board games,
   so only as a side series.
