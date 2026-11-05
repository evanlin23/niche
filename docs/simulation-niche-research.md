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
| Checkout lines / queues | 36M (mostly comedy) | no one with views, but six template videos with 0-21 views (see section 5) | open, but already cluttered: our backlog's "other line" episode |
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

## 5. The copycat flood (research 2026-11-05, second pass)
Raw data: `docs/sim-copycats-2026-11-05.json` (35 template channels and 8 winners: the template video's full
metadata, latest 30 long videos, latest 30 Shorts) and `docs/sim-copycats-scan-2026-11-05.txt` (format matches from all
earlier scans, 70 per-game searches, 20 Shorts searches). Same method and limits as above.

**What happened.** Perfect Play posted its Monopoly video on 13 October 2026. It has 2.78M views. Within days, dozens
of channels started posting the same video for other games, often with the same title wording ("The Best X Strategy,
Tested on N Million Games"). Of the 35 template channels I measured:
- 32 posted their template video on or after 13 October.
- Median 11 subscribers (26 of 35 under 100). Median views of the template video: 58 (21 under 100, 27 under 1,000).
- Median length 9 minutes, the same as Perfect Play.
- Several look automated: they mix unrelated topics (Uno next to Voyager 1, Ludo next to a mystery thriller series), and
  one posted "Opus 5.5 Didn't Generate This Video. It Compiled It." Many are probably pipelines much like ours.
Another 9 such channels showed up in the per-game searches (Odds&Boards, Played It Out, Proven Moves, TENVAR,
I Calculated It, Ten Million Rolls, Monte Carlo Games, Robot Game Night, House Rules Sim), so it's over 40 in all.

**Our games are already covered by template videos** (long videos found, all channels):
| Game | Template videos | Best of them |
|---|---|---|
| Uno | 11 | all under 1,000 views |
| Battleship | 8 | Jacab Thomas 10.2K, the rest under 1,000 |
| Yahtzee | 4 | Jacab Thomas 4.0K (plus Ballpark Figures' "I Solved Yahtzee*" 1.1M) |
| Connect 4 | 3 | Jacab Thomas 1.4K (plus 2swap's "I Solved Connect 4" 1.7M) |
| Ludo, Mancala, Farkle | 3, 2, 2 | under 100 |
| Sorry!, Checkers | 1 each | Jacab Thomas 617 and 521 |
| Phase 10, Price Is Right (Plinko) | 1 each | under 10 |
| Monopoly, Catan, Risk | 17, 9, 2 | Perfect Play; the copies peak at 10K |
| Exploding Kittens | only ours | |
| Gin Rummy, Shut the Box, Skip-Bo, Go Fish, Liar's Dice, Chinese Checkers, Coup, Mexican Train, Cribbage, White Elephant, Secret Hitler, Werewolf, Cheat, Azul | none found | |

**Shorts do much better than long videos on new channels.** For the 19 template channels under 500 subscribers that
post both, the median long video gets 21 views and the median Short 487. Shorts win on 17 of the 19. Even channels
with 0-10 subscribers get 500-1,300 views per Short. Ours matches that: our first Short has 174 views, while the
Exploding Kittens long video (posted 4 November) showed 0 views logged out on 5 November (new counts can lag, so
check YouTube Studio). Our channel has 173 subscribers.

**Perfect Play is strong but shallow.** Catan (posted 31 October) is gaining about 40,000 views a day; Monopoly is still
gaining about 33,000 a day. But it has 8,810 subscribers from 3.36M views (0.26%). Likes on Monopoly are 0.59% of
views, with 0.21 comments per 1,000 views. Those are copycat-level numbers (0.3-1.4% likes). The channels with real
audiences look different:
| Channel | Video | Length | Likes / views | Comments per 1K views |
|---|---|---|---|---|
| Perfect Play | Monopoly, 2.78M | 8 min | 0.59% | 0.21 |
| Ballpark Figures | I Solved Yahtzee*, 1.12M | 33 min | 2.07% | 1.16 |
| Ioana Roman (a quant developer, on camera) | 47,000 games of Catan, 394K | 17 min | 2.85% | 1.86 |
| Astroid Videos | 1.8M Pokémon battles, 3.11M | 22 min | 3.20% | 1.51 |
| Gym Leader Matt (posted 23 Oct 2026) | 17M Pokémon battles, 276K | 51 min | 2.46% | 5.79 |
| 2swap | I Solved Connect 4, 1.73M | 18 min | 4.35% | 1.74 |
| SmithPlays Pokémon | 3.4M battles, 207K | 34 min | 4.37% | 4.77 |
| Dr Ruckus MTG | 5M Magic games, 213K | 28 min | 7.75% | 8.90 |
My reading: Perfect Play's views come from huge game names, not from people who care about the channel. The channels
people care about are longer, deeper, have a person behind them, and often serve a fan community (Pokémon, Magic).

**What this means.**
1. Copying Perfect Play's format is finished for newcomers. The "N million games" title is now the most crowded
   signal in the niche, and a wall of near-identical channels is exactly what YouTube's inauthentic-content rule
   targets. All three of our Exploding Kittens test titles use it, and title B uses Perfect Play's own
   "Tested on N Games" wording. Sorry! ("I Played a Billion Games of...") and Checkers do too.
2. The data/strategy lane itself isn't dead. The winners that don't copy Perfect Play (Ballpark Figures, 2swap,
   the Pokémon and Magic channels) have the strongest audiences in the scan.
3. A new channel's first views come from Shorts. Long videos from a 173-subscriber channel in a crowded template
   will get very little until the channel has an audience.
4. Next step: pick a lane that keeps our assets (fast engines, billion-game runs, the creator's real voice) but
   doesn't look like the flood. Candidates are measured in section 6.

## 6. Is there a lane without copycats? (research 2026-11-05, third pass)
Raw data: `docs/sim-lanes-scan-2026-11-05.txt` (12 candidate lanes, 48 searches) and
`docs/sim-lanes-channels-2026-11-05.json` (9 channels: latest 20 long videos and 20 Shorts).

| Lane (4 searches each, long videos) | Unique videos | Median views | Who's winning |
|---|---|---|---|
| Pokémon battle simulations | 62 | 402K | TerminalMontage animations; Astroid Videos (423K subs); SmithPlays (298K) |
| Balatro / roguelike maths | 71 | 118K | Balatro University, let's-players (a solo game) |
| "Rules everyone plays wrong" | 72 | 114K | Mark Rober "I Solved Every Board Game" 20.2M; Veritasium "Game of Life wrong" 11.6M; "Everyone Plays Monopoly Wrong" 2.0M |
| Party games (Secret Hitler, Werewolf, Coup, Codenames) | 68 | 87K | let's-play groups (Smosh, Polygon); one sim video: Brute Force Lab "How Many Werewolves Make a Fair Game?" 348K |
| AI models play social games | 72 | 42K | Turing Games (114K subs, median of latest 17 long videos 353K): "I Forced 5 AIs to Work Together" 3.5M, "10 AIs Play Mafia" 2.6M |
| AI models play board games | 65 | 30K | Croissant "4 AIs play 4 Player Chess" 1.9M; Quinn Henry "7 AIs play Diplomacy" 868K; GothamChess AI chess 3.5-5M |
| AI self-play (reinforcement learning) | 64 | 31K | b2studios "AI Learns Insane Monopoly Strategies" 12.1M; AI Warehouse |
| Bot leagues and events | 71 | 27K | Jelle's Marble League (old hits) |
| Game-show maths | 56 | 23K | clips of the shows themselves, almost no maths videos |

**The AI-models lane already has copycats too.** Next to Turing Games there are Played by Machines (13 subscribers,
median 68 views across 10 Secret Hitler and Mafia videos), Mind Machines (22 subs, median 145, Werewolf),
AI vs AI Poker (67 subs) and others, most posted in the last weeks. So **changing lanes alone doesn't escape the
flood.** Any format that trends gets copied within days by automated channels.

**What the winners share, in every lane:** a host with a personality (Turing Games, Croissant, GothamChess,
Ioana Roman); a question or a story in the title, not a big number ("How Many Werewolves Make a Fair Game?",
"I Forced 5 AIs to Work Together...(it was bad)"); 12 to 60 minutes; stakes and drama (lying, betrayal, a
grandmaster). The copycats share the opposite: a number-first title, about 9 minutes, no person.

**Options for Buh Simulates, best first:**
1. **AI models play family games, with our billion-game bot as the referee.** For example: ChatGPT, Claude, Gemini and
   others play Liar's Dice, Coup, Gin Rummy or Sorry!, and every move is graded against a bot that has played a
   billion games (for example: how often each model called "liar" on a bid that was probably true). Why it fits: it's the fastest-growing lane;
   the models are ready-made characters with a rivalry; bluffing games are where language models are fun to watch;
   family card games are barely covered (Deep Logic's "AI Plays Uno" has 249 views; no Gin, Sorry! or Liar's Dice
   found); and the grading is something no other AI-games channel can do. New models every few months give natural
   rematches. Costs: API keys and per-game model costs (measure with a pilot), plus a chat-and-table visual.
   Pilot: **Liar's Dice**. The chance that a bid is true given your own dice is plain maths (a binomial), so every
   call and every bid can be graded exactly. Liar's Bar (a video game version) shows the demand: Markiplier's
   video has 4.6M views.
2. **Question-led game science with a visible host**, using the engines and scripts we already have. Retitle them as
   questions and findings, with no "N billion games" up front. Brute Force Lab gets 348K with this at 2.7K subscribers.
   Cheapest option, but it's the closest to the flood.
3. **Pokémon battle simulations.** Highest demand (median 402K), but big established channels, Nintendo's IP, a
   different audience, and it only works if the host knows Pokémon well.

Whichever lane: daily Shorts (the only thing that reliably gets a new channel seen), fewer but longer and more
personal long videos, and titles that lead with a question or a finding.
