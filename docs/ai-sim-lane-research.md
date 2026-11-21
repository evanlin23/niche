# The "AI learns X" lane: research for a possible new direction (2026-11-21)

Research and planning only. Nothing was built, rendered or bought. All data was fetched on Saturday 21 November 2026,
about 1:35–2:00 pm CST. Read with `docs/simulation-niche-research.md` §5–8, `docs/automatable-niches.md` and
`docs/LESSONS.md`.

**Verdict:** a conditional go. Start with one pilot (an egg drop designed by evolution, §6). Channels only weeks old have
broken out here in the last 90 days, and its Shorts are among the biggest we've measured. The flood is real, though: 119 new "AI learns" channels with a median of 9 subscribers. We only win with
Buh as a real character, the creator's voice, a story with a cheat in it, and 12–15 minute videos. Volume won't do it.

## 0. Method, sources, limits
- **Sources.** Every number carries one of three tags:
  - **[C]** a channel's public Videos and Shorts tabs plus its public RSS feed
    (`youtube.com/feeds/videos.xml?channel_id=...`), saved in `docs/ai-sim-lane-channels-2026-11-21.json` under the
    handle shown.
  - **[S]** search results, saved in `docs/ai-sim-lane-scan-2026-11-21.txt`.
  - **A URL**, for anything else.
- **What was fetched.** About 370 logged-out YouTube searches (37 lane queries in three modes: relevance, "this
  year", newest first; 72 discovery queries; 52 ideas × 2 for the gap scan; 12 rechecks). That gave 1,163 channels
  (latest 60 long videos and 30 Shorts each) and 1,163 RSS feeds. Two research agents read public web pages for the
  feasibility facts and the written descriptions of top videos. Their sources are linked inline.
- **What the numbers mean.** Exact numbers come from RSS (exact publish time, views and likes for the latest 15
  uploads, plus the channel's creation date). Channel-tab views are YouTube's rounded display ("2.15M"). Older
  upload dates come from YouTube's relative text, so "7 yrs ago" means 7.0–7.99 years.
- **Limits:**
  1. YouTube refused this container's requests for watch pages ("Sign in to confirm you're not a bot"), so I could
     not read transcripts, the exact dates of old videos, or comments. The hooks in §3 therefore come from written
     sources, thumbnails and titles, and say so where it matters.
  2. The copycat count only covers channels that came up in these searches, so it's a lower bound.
  3. I can't hear voices, so "automated" is inferred from upload pace and titles.

## 1. Landscape: the biggest channels and videos in the lane
"Median" is the median views of the latest 20 long videos (fewer if the channel has fewer).
"Long/12 mo" is long uploads since 21 Nov 2025, counted from RSS when the feed covers the year; Shorts are counted
separately. Length is the median length of those latest videos. All numbers are [C] unless marked.

| Channel | Subs | Median | Best (video id, age) | Long/12 mo, last long | Character / host | Length | Title pattern (real examples) |
|---|---|---|---|---|---|---|---|
| Code Bullet @CodeBullet | 3.47M | 2.15M | 14.8M "A.I. Learns to play Flappy Bird" (WSW-5m8lRMs, 7 yrs) [S] | 5; 6 Oct 2026 | creator's voice, self-deprecating (nerdist.com/article/coder-tetris-ai-world-record); robot "CB" avatar on thumbnails | 19.6 min | "A.I. Learns To Play HAPPY WHEELS" 3.96M; "Using A.I. to DESTROY Minesweeper" 5.66M |
| AI Warehouse @aiwarehouse | 832K | 4.9M (12 videos) | 13.8M "AI Learns to Walk (deep reinforcement learning)" (L_4BPjLBF4E, 3 yrs) [S] | 1; **24 Nov 2025: no long video for 12 months** | Albert, an orange cube with eyes, plus a blue rival team (thumbnails; youtube.fandom.com/wiki/AI_Warehouse, fan wiki) | 10.8 min | "AI Learns to Play Tag (and breaks the game)" 9.77M; "...Soccer (and breaks physics)" 8.90M |
| Yosh @yoshtm | 428K | 3.25M | 17.7M "Training an unbeatable AI in Trackmania" (Dw3BZ6O_8LY, 3 yrs) [S] | 2 + 12 Shorts; 26 Oct 2026 | creator vs his own AI (theautopian.com/how-a-youtuber-spent-years-teaching-ai-how-to-beat-him-at-virtual-racing) | 15.4 min | "AI just Broke Trackmania's Greatest World Record" 7.82M; Shorts "AI vs Trackmania - A01…A12" 0.8M–16.4M |
| Primer @PrimerBlobs | 1.94M | 3.45M | 25.0M "Simulating the Evolution of Aggression" (YNMkADpvO4w, 7 yrs) [S] | 1; 31 Dec 2025 | blob characters | 13.3 min | "Simulating the Evolution of Rock, Paper, Scissors" 4.6M |
| b2studios @b2stud | 363K | 415K | 12.1M "AI Learns Insane Monopoly Strategies" (dkvFcYBznPI, 4 yrs) [S] | 5; 10 Nov 2026 | creator-led | 13.4 min | "Can AI Run McDonalds?" 1.11M; "I Forced AI To Learn 4D Movement" 1.89M |
| carykh @carykh | 742K | 256K | 5.2M "Evolution Simulator (Part 1/4)" (GOFws_hhZs8, 11 yrs) [S] | 10; 19 Nov 2026 | creator (Cary Huang, en.wikipedia.org/wiki/Cary_and_Michael_Huang) | 17.8 min | "Mass Extinction Simulator" 1.3M; now mostly maths curiosities |
| Peter Whidden @peterwhidden | 72K | one video | 10.2M "Training AI to Play Pokemon with Reinforcement Learning" (DcYLT37ImBY, 9 Oct 2023) | 0 | creator's voice over a swarm of games (speedrun.substack.com/p/three-viral-experiments-with-ai-powered-games) | 33.9 min | descriptive |
| SethBling @SethBling | 1.97M | 89K | 11.5M "MarI/O - Machine Learning for Video Games" (qv6UVOQ0F44, 11 yrs) [S] | 7 (not AI); 26 Nov 2025 | creator | 9.9 min | one-off in the lane |
| Samuel Arzt @SamuelArzt | 51.5K | 235K | 11.7M "Deep Learning Cars" (Aut32pR5PQA, 10 yrs) [S] | 0; 10 Apr 2020 | none | 6.3 min | descriptive |
| Pezzza's Work @PezzzasWork | 205K | 181K | 3.05M "Evolving AIs - Predator vs Prey, who will win?" (qwrp3lB-jkQ, 4 yrs) [S] | 13; 5 Nov 2026 | creator; blobs with eyes on thumbnails | 18.4 min | "Two AIs Learn to Collaborate to Fight Zombies" 667K; "AI Chicken learns to RUN" 150K |
| davidrandallmiller | 55.2K | 2 videos | 4.47M "I programmed some creatures. They Evolved." (N3tRFayqVtk, 56 min) | 0; Dec 2020 | creator | 28.5 min | first-person claim |
| cozmouz @cozmouz | 99.2K | 74K | 2.92M "I Trapped this AI Centipede in a Simulation for 1000 Years" (oFqwcngsts8, 31 Mar 2025) | 3; 26 Sep 2026 | none | 10.5 min | "I Tortured this AI Humanoid in a Dark Room for 5000 Years": 8.8K in 2026 (the drama template wore out) |
| Icoso @icoso | 107K | 170K | 2.35M "I Made an Evolution Simulator (with silly little guys)" (f7vH2Li9KOw, 1 yr) | ~6; 31 Oct 2026 | "silly little guys" (green faces) | 7.6 min | now makes game-dev videos |
| Emergent Garden @EmergentGarden | 294K | 108K | 1.91M "4 AIs Survive 10 Days in Minecraft" (KxaPYhfJV4U, 2 yrs) | 10; 10 Oct 2026 | creator | 20.9 min | LLM agents plus artificial life ("Rogue AI Agents" 829K) |
| MrMommsen @MrMommsen | 40.2K | 73K | 2.13M "AI Learns How To Play The Worlds Hardest Game" (GRvtWan5cTM, 2 yrs) | 0; 25 Jan 2025 | none | 8.3 min | "AI Learns How To Play X" |
| Linesight @linesight-rl | 30.7K | 4.2K | 1.88M "I Trained an AI for 2 Years on Trackmania. It's Breaking Records." (cUojVsCJ51I, 2 yrs) | 0; May 2024 | none | short clips | |
| AI Tango @aitango | 24K | 41K | 1.53M "AI Learns to DESTROY old CPUs / Mario Kart Wii" (VIwGxOdXGfw, 3 yrs) | 3; 31 Oct 2026 | none | 10.2 min | "AI Learns to DESTROY X" |
| The Bibites @TheBibitesDigitalLife | 102K | 85K | 927K "What will happen after 100h of evolution?" (sEPh6bAQVP0, 4 yrs) | ~6; 9 Oct 2026 | the Bibites (its own game) | 21.8 min | battle-royale series; likes 9.35% of views (highest in the table) |
| kavan @kevkev-70 | 173K | 44K | 393K "Training AI to Backflip in C++/Python" (vKDj_XIKW7o, 7 Sep 2026); channel best 3.3M (black holes) | 2; 7 Sep 2026 | creator, code on screen | 8.4 min | "Training AI to X in C++" |
| Kartenovis @Kartenovis (created 1 Jun 2026) | 3.64K | one video | **1.37M** "2048 but the AI Can't Stop Learning" (qGvLiyoNTIE, 11 Sep 2026, its first long video) | 1 | none | 5.4 min | game name + twist |
| Simulated Seeds @Simulatedseeds (created 28 Oct 2026) | 2,280 | 5.3K | **535K** "I Let Evolution Design a Predator. Then I Blindfolded It." (o-RN7P74OsU, 13 Nov 2026) | 16 in 3 weeks (daily) | none | 15.5 min | "I Let Evolution…. Then I…" |
| Overcomputed @overcomputed (created 4 Nov 2026) | 1,370 | 2 videos | **171K** "I Let Evolution Design a Chess Army. Only Bishops Survived." (11 Nov 2026, first video) | 2 | none | 22.3 min | result as the twist |
| Rollo's Lab @RollosLab (account Sep 2025) | 2,680 | 27K | 168K "AI Learns to Escape the Lab (Inspired by AI Warehouse)" (lSyb1RljX30) | 4 + many Shorts | **Rollo**, a named agent ("Can Rollo escape all 9 rooms?") | 12.8 min | an open AI Warehouse clone |
| M37 @m37channel (created 24 Aug 2026) | 958 | 1.75K | 226K Short "I Evolved AI to Dodge a Bull. Then the Bull Evolved Back." (RmbzHPjwEYA) | 35 long since ~Sep 2026 | none | 12.9 min | "I Evolved X. Did It Find Y?" |
| **Pip Simulates** @PipSimulates (account 2019, first upload 12 Nov 2026 12:39 pm CST) | 114 | 613 | 5,303 "Simulating Two AI Bots Inventing Their Own Language" (8NIOW2YduU8, 16 Nov) | 5 long every ~2 days + 10 Shorts | wind-up toy robots with faces (thumbnails) | 8.4 min | "Simulating…", "I Let AI…"; Shorts 54–1,418 views |

What the table says:
1. **The giants are slowing down or have stopped.**
   - AI Warehouse, the clearest owner of "a character learns a physical task", hasn't posted a long video since
     24 Nov 2025 [C]. Its slot is open.
   - Others have stopped too: Peter Whidden (2023), Samuel Arzt (2020), davidrandallmiller (2020), MrMommsen (Jan 2025).
   - carykh and Icoso have moved to other topics.
2. **Typical views for active channels:** 74K–3.5M per long video. Lengths: 10–20 min, up to 34 min for a deep
   dive (Whidden 33.9).
3. **The biggest Shorts in this research are here** [C]:
   - Yosh's "AI vs Trackmania" series: 12 Shorts, May–Oct 2026, 0.8M–16.4M each.
   - AI Warehouse's "AI Learns to Dodge": 11.8M.
   - Compare the board-game template channels: 487 median per Short (§5 of the sim research).
4. **New channels are breaking out right now.**
   - Kartenovis: 1.37M on its first long video.
   - Simulated Seeds: 535K in 8 days on a channel 3 weeks old.
   - Overcomputed: 171K on its first video.
   - That never happened in the board-game flood (§5).
5. **Pip Simulates:**
   - It started 8 days after our Exploding Kittens video (posted 4 Nov, `docs/LESSONS.md`).
   - Its name follows the same pattern as ours, and it has a robot mascot.
   - Its long videos get 395–5,303 views, with likes at 1.3–5.1% of views [C].
   - It's one of the 119 channels in §2, not a leader. Its upload pace (a long video every 2 days, plus Shorts)
     looks like a pipeline.

## 2. Copycat check: how flooded is the lane?
**Method.**
- **Lane channel:** among the 1,163 channels, at least 2 titles about agents learning or evolving (my regex: AI,
  neural, creature, robot, agent or evolution, together with learn, train, evolve, generation, simulate or
  reinforcement), and at least half of the channel's titles. That gave 123 channels.
- **Borderline cases:** read by hand, adding 60 that passed a looser cut. I excluded AI-generated "evolution"
  morphs, Animal Revolt gameplay, lectures and kids' content.
- **"Started 2025–26":** the account was created in 2025 or later, or the first upload is in 2025 or later.

| Measure | Result [C] |
|---|---|
| Channels started 2025–26 | **119** (29 started in 2025, 90 in 2026; **60 posted their first video after 21 Sep 2026**) |
| Subscribers | median **9**; 96 under 100; 111 under 1,000; none at 10,000 |
| Views per long video | median of each channel's median: **116**; all 684 long videos: median 185 |
| Views per Short | median of each channel's median: **741**; all 642 Shorts: median 852 |
| Length | median 6.7 min |
| Likes / views (long videos with 100+ views) | median 1.24% (287 videos); established channels: Code Bullet 4.87%, b2studios 4.51%, Primer 3.93%, Pezzza 3.79% |
| Pace | 43 of the 80 channels with 5+ recent uploads post 3.5 or more a week (Pip Simulates, M37, Simulated Seeds among them) |
| Titles (666 lane titles) | **37% start "AI Learns…"**, 14% put "(deep) reinforcement learning" in the title, 8% "I Trained an AI…", 10% are questions, 5% lead with a time scale ("1,000 days") |

The "AI Learns to X" opener is this lane's version of the board-game "Tested on N Million Games". Several channels
name AI Warehouse in their titles ("Inspired by AI Warehouse": Rollo's Lab, AI Outpost, MEK Squad), and one channel
posts "AI Warehouse Voiceover" videos (Dominic Villegas) [C].

**The 12 that grow** (1,000+ subscribers or a 50K+ video) [C]:

| Channel | Started | Subs | Best |
|---|---|---|---|
| Kartenovis | Aug 2026 | 3,640 | 1.37M |
| Simulated Seeds | Oct 2026 | 2,280 | 535K |
| Emeka Moemeka | Aug 2025 | 6,470 | 353K "I Trained an AI to Play Clash Royale…" |
| Alex Wittman | Apr 2025 | 9,650 | 314K "A.I. Learns to Optimize Factorio Blueprints" |
| M37 | Sep 2026 | 958 | 226K Short |
| Kadambi Engineering | Jul 2026 | 5,710 | 176K "AI Learns Minecraft PvP" |
| Overcomputed | Nov 2026 | 1,370 | 171K |
| Rollo's Lab | Sep 2025 (account) | 2,680 | 168K |
| TheToadAI | May 2026 | 993 | 158K "Can an AI Trained on Old Mario Beat New Mario?" |
| Coding Stick | 2025 | 726 | 64K |
| Aydan | Nov 2026 | 608 | 52K "I Trained an AI to Beat M7" (Hypixel SkyBlock) |
| Weinreich AI | 2025 | 1,020 | 23K, with 30 Shorts |

**What separates them** (counts from the table above):
1. **They ride a fan community.** 7 of the 12 are about a game with a big audience: Mario, Minecraft, Factorio,
   Hypixel, chess, 2048, Clash Royale. This matches §5 of the sim research, where the channels with real audiences
   (Pokémon, Magic) served a fandom.
2. **They're longer.** The growers' median length is 11.3 min; the rest, 6.2 min.
3. **The title names a specific, surprising result.**
   - Examples: "Only Bishops Survived.", "Then I Blindfolded It.", "Then the Bull Evolved Back.", "Old Mario Beat
     New Mario?"
   - Compare the generic "AI Learns to X (deep reinforcement learning)".
   - A question mark alone doesn't separate them: 11% of titles in both groups are questions.
4. **A named character helps Shorts.** 5 of Rollo's 9 recent Shorts got 13K–30K, against the lane's median Short of 852.
5. **Volume doesn't.**
   - M37 posts every 1–2 days, and the median of its 35 long videos is 636 views.
   - Pip Simulates posted 5 long videos in 9 days; its best got 5.3K.
   - Simulated Seeds posts daily: one video hit 535K, the rest got 1.3K–79K.
6. **Even the hits are shallow.** Likes are 1.04% of views on Simulated Seeds' 535K video and 1.12% on
   Kartenovis's, the same level as Perfect Play (0.59%, §5). Big views without fans, again.

**Policy context.** On 15 July 2025, YouTube renamed "repetitious content" to "inauthentic content". One of its
examples is "AI-generated content made with generic or unoriginal templates" (support.google.com/youtube/answer/1311392).
A wall of "AI Learns to X" channels is exactly what that rule describes.

## 3. What works: concrete patterns from the top videos
**The hook in the first 10 seconds.** I couldn't read transcripts (see §0), so this comes from written sources and
from what each thumbnail promises.
- **Peter Whidden:** opens on a swarm of runs: "Right now we're watching 20,000 games played by an AI…"
  (speedrun.substack.com/p/three-viral-experiments-with-ai-powered-games).
- **The same shot on thumbnails:** the whole population at once, then one survivor.
  - AI Warehouse "AI Learns to Walk": a crowd of Alberts piled behind a wall while one walks to the goal, with a
    counter reading 98684.
  - Code Bullet "Flappy Bird": a flock of birds.
  - Yosh: "HUMANS" (a swarm) vs "AI" (one circled car).
- **Code Bullet:** builds the game in the first half and brings in the AI from about 8:30. His hook is the build,
  not the AI (nerdist.com/article/coder-tetris-ai-world-record).
- **For us:** frame 1 should show the swarm or the failure, already moving, which matches our Shorts rule in
  LESSONS.

**Character arc.**
- **AI Warehouse:** Albert (an orange cube with eyes) against a blue team. Their two biggest recent titles sell
  Albert misbehaving: "(and breaks the game)" 9.77M, "(and breaks physics)" 8.90M [C].
- **Yosh:** the arc is the creator against his own AI.
  1. A 3-year project.
  2. The AI beats him after 35 hours with its brakes disabled.
  3. He wins back by using brakes.
  4. About 100 more hours until the AI learns to brake (theautopian.com, as above).
- **Whidden:** failures tied to human life: "curiosity… makes us vulnerable to distractions"
  (techcrunch.com/2023/10/18/after-50000-hours-this-ai-can-play-pokemon-red).
- **Rollo's Lab:** a named agent with a quest: "Can Rollo escape all 9 rooms?" [C].
- **Icoso:** cute agents pay. "(with silly little guys)" got 2.35M [C].
- **cozmouz shows the limit of drama alone:** "I Trapped this AI…" got 2.9M, then "I Tortured this AI…" fell to
  8.8K–42K in 2026 [C].

**Failure moments.**
- **Code Bullet:**
  - His walker "eventually learns to walk, albeit backwards" (daily.dev/posts/ai-learns-to-walk-3d-part-2--pbzbbsd0t).
  - In "A.I. Learns To Walk", a creature clips one leg into the other and slides. It's listed as specification
    gaming at youtu.be/K-wIZuAA3EY?t=486 (Krakovna's list, below).
- **Whidden's agent:** stares at the water in Pallet Town forever, and avoids Pokémon Centers after a reward bug
  (TechCrunch, as above).
- **b2studios sells the falls in the title:** "AI Tries Snowboarding (and falls a lot)", 371K [C].

**"It cheated" twists** (the lane's best-paid beat):
- **Yosh:** "AI Learns to Exploit a Glitch in a Racing Game" got 6.6M and "AI just Broke Trackmania's Greatest World
  Record" 7.82M [C]. For the A01 record, a brute-force search found "a tiny misaligned road seam", and the record
  went 23.79 → 23.64 (dexerto.com/gaming/youtuber-uses-ai-to-shatter-trackmanias-untouchable-record-3246676).
- **OpenAI hide and seek:** forts at about 25M rounds, ramps at 100M, ramp-locking at 110M, "box surfing" at 380M
  (technologyreview.com/2019/09/17/75427).
- **Krakovna's specification-gaming list** is a ready source of twists, with credits (vkrakovna.wordpress.com/2018/04/02/specification-gaming-examples-in-ai/):
  - Karl Sims' tall creatures that "run" by falling over, and clapping body parts to exploit a collision bug
    (karlsims.com/papers/siggraph94.pdf).
  - A boat that circles reward targets instead of finishing (openai.com, faulty reward functions).
  - A Tetris agent that pauses forever (cs.cmu.edu/~tom7/mario/mario.pdf).
- **Our rule:** show the cheat, patch the rule on camera, and say so. Viewers love the cheat, and honesty is our
  brand (LESSONS: never explain with an untested reason).

**Run length, said on screen.**
- Whidden: "50,000 hours" (thumbnail text "For 50k Hours…"; TechCrunch).
- Yosh: 100 AIs × 100 generations in 2021 (hackaday.com/2021/01/17/ai-learns-to-drive-trackmania), and 3,000+
  attempts and about 400 hours for the A01 record (shazoo.ru, 2025-09-08).
- SethBling: 34 generations in about 24 hours (en.wikipedia.org/wiki/SethBling).
- These scales go inside the video. Time-scale titles are now copycat material: 5% of new titles, including
  "30,000 Days" (Pip) and "1000 Years" (cozmouz) [C].

**Thumbnails** (30 top thumbnails checked by eye; video ids in §1):
1. **Before and after split:** b2studios Spider-Man GEN 1 | GEN 771 (7.5M); Pezzza's cat GEN 0 | GEN 1000 (1.49M).
   But Pip Simulates uses the same split (DAY 1 | DAY 30,000), so the split is no longer a differentiator.
2. **A character with eyes** on most of them: Albert, Primer's blobs, Pezzza's blobs, Icoso's guy, Pip's robots.
3. **A question that teases:** "BUY THE BROWNS?" (b2studios, 12.1M), "Share or Take?" (Primer, 25.0M). This matches
   LESSONS: thumbnails ask, never answer.
4. **A big counter:** AI Warehouse's 98684.
5. **No small-percentage-next-to-big-percentage look** anywhere in this lane.

**Length.**
- Established channels: 10–20 min (§1).
- Growers among new channels: 11.3 min; everyone else: 6.1 min (§2).
- Deep dives that became references run 28–56 min (Whidden 34, davidrandallmiller 56, The Bibites 22–48).

## 4. Gaps: 20 underserved ideas
**How to read this.** "Demand" is the top result and the median of a plain search for the activity. "Coverage" is
the best video an AI or evolution search ("AI learns X", "AI designs X") turned up. Both come from [S], gap-scan
lines. Hooks are questions or claims, with no number first. Any claim must be literally true once we've run it, so
most stay questions until the data answers them.

**Effort:**
- **S:** no new physics (Go engines or a ball in flight); about 1 week.
- **M:** rigid-body physics plus evolution of a design or a simple controller; about 2 weeks for the first, 1 week
  after that.
- **L:** an articulated body learning a contact-heavy skill, or a custom water or air model; 3–4 weeks.

| # | Idea | Hook | Demand | Coverage (why underserved) | Effort |
|---|---|---|---|---|---|
| 1 | Egg drop | Can evolution design an egg drop that survives the roof? | Mark Rober "Egg Drop From Space" 153M; "1st place Egg Drop project ideas" 43.6M | none: no AI or evolution egg drop in "AI learns egg drop" | M |
| 2 | Domino run | Can an AI plan a domino run that climbs stairs? | median 7.9M; Hevesh5 triple spiral 155.5M | none (results are a software company called Domino) | M |
| 3 | Marble run | What does evolution build when you ask for the slowest marble run? | median 2.1M; 126.2M top | best 7.6K (2020); 2026 uploads at 3–30 views | M |
| 4 | Trebuchet | Does evolution reinvent the trebuchet, or find something stranger? | median 617K; Tom Stanton "Supersonic Trebuchet" 5.5M (2026) | one evolved trebuchet from Nobody Drew This (4 subs, Nov 2026) [C] | M |
| 5 | Bottle flip | How much water does a bottle flip really need? | top 20: 1.12B; Dude Perfect 697M | KUKA real robot 108K (2017); a sim attempt at 53 views | M |
| 6 | Free throw | Will a robot that learns free throws from scratch shoot underhand? | Wilt Chamberlain free throws 3.6M; "Why All Pro Basketball Players Shoot Free Throws Wrong" 1.27M | only real robots (Toyota 78K) | S |
| 7 | Penalty kick | Should the goalkeeper just stand still? Two self-taught AIs settle it. | median 122K; 3.1M top | AIdan 3.3K, Neu Lab AI about 1K | S |
| 8 | Mini golf | Is there a hole-in-one on every mini-golf hole? | median 512K; "18 Amazing Hole In Ones!" 29.3M | b2studios golf 913K (regular golf, 2024); Strategy Lab AI 976 | S |
| 9 | Tug of war | Put five robots on one rope. Does one learn to stop pulling? | median 186K; "23 Lego Vehicles Tug-Of-War" 13.4M (2026) | Tiny Brain Lab 60 views; robot news clips | M |
| 10 | Musical chairs | Do robots learn to shove at musical chairs? | 184M in the top 20, mostly kids' songs (129M) | Mads Lab AI 1.6K | M |
| 11 | Floor is lava | Can Buh learn the floor is lava before the floor wins? | Stay Wild "Extreme Floor Is Lava Challenge!" 14.8M (posted 17 Nov 2026); kids' songs dominate the rest | Ai dev KitcHen 15K, KawAI 6.7K, Moby Motion 3.8K | M |
| 12 | Sheepdog | Can one robot dog herd fifty sheep? | "Worlds Worst Sheepdog" 23.5M; median 170K | Michael Rechtin 5.4K (2021), Longy Dev 880 | M (flock from `sims/boids.py`) |
| 13 | Stone skipping | Is there a perfect angle to skip a stone? | WIRED "Why It's Almost Impossible to Skip a Stone" 16.3M | none | M (custom water model) |
| 14 | Riding a bike | What's harder for a robot: walking or riding a bike? | median 1.04M; 19.6M top | motorcycle RL 12K (2024); BadlyTrained 1.1K | L |
| 15 | Trampoline | How many flips does a robot learn before it lands on its head? | median 275K; 10.1M top | only AI-generated clips, no learning sim | L |
| 16 | Skateboard | Nobody told the AI skateboards can jump. Does it find the ollie? | median 856K; Braille "how to ollie" 11.6M | "Investigating the AI Skateboarder" 609K is about AI video, not training | L |
| 17 | Paper airplane | Can evolution fold a paper plane that beats the record design? | median 3.8M; "WORLD RECORD Paper Airplane" 28.1M | none | L (needs an air model) |
| 18 | Jenga | Two robots play Jenga. Does the winner learn to leave a trap? | median 553K (mixed with a song) | MIT real robot 171K (2019); no self-play | L |
| 19 | Liar's Dice | Does an AI that teaches itself Liar's Dice learn to lie? | median 124K; rules explainer 4.9M; Markiplier's Liar's Bar 4.6M (§6) | only LLM channels (The Model Wars, 4 views) | S (no physics; exact binomial checks) |
| 20 | Uno | Left alone with Uno, does an AI learn to hoard its Draw Fours? | Uno appears in 15 "how to win" autocompletes (`automatable-niches.md` §5); b2studios' Monopoly self-play 12.1M | "AI learns uno" returns only Arduino Uno | S (`sims/uno` exists) |

**Already taken by tiny copycats in Oct–Nov 2026, so skip** [C]:
- high jump / Fosbury flop (M37)
- juggling (M37)
- rocket landing (5+ channels)
- hide and seek, tag, sumo, red light green light, dodgeball (AI Warehouse at 1.0M–9.8M, plus clones)
- LLM-built bridges (Q Labs 634K)

## 5. Feasibility on our stack
**What we already have:**
- **Renderer:** Three.js, rendered frame by frame in headless Chromium. Specs already carry base64 Float32 arrays
  (`pipeline/render3d.py`, `f32()`).
- **QA gates:** clipping, flicker, word sync and smoothness (`pipeline/qa_visual.py`).
- **Voice pipeline.**
- **Go engines for 9 games** (`sims/`).
- **A 20-runner Actions sharding pattern** (`.github/workflows/simulate.yml`).

**What we'd add:**

| Piece | Choice | Facts (sources) | My estimate |
|---|---|---|---|
| Physics, design-evolution ideas (1–5, 8, 9, 12) | **`@dimforge/rapier3d-deterministic`** in Node, the same engine the browser could run | v0.21.0 (25 Sep 2026), Apache-2.0 (registry.npmjs.org/@dimforge/rapier3d-deterministic). Plain `rapier3d` dropped enhanced determinism in 0.15 (github.com/dimforge/rapier.js/blob/master/CHANGELOG.md). Cross-platform determinism needs the same insertion order and no `Math.sin` for initial values (rapier.rs/docs/user_guides/javascript/determinism). Joints with motors (rapier.rs/docs/user_guides/javascript/joints). Snapshots via `takeSnapshot()` (rapier.rs/docs/user_guides/javascript/serialization) | 3–4 days to wrap it, including a speed benchmark (not run: research only) |
| Physics, articulated-RL ideas (11, 14–16) | **MuJoCo (Python) + Gymnasium**, CPU | `pip install mujoco`; `mujoco.rollout` and batch are "bit-identical" whatever the thread count (mujoco.readthedocs.io/en/latest/python.html); Apache-2.0. Gymnasium MuJoCo v5 envs (gymnasium.farama.org/environments/mujoco/) | later; 1–2 weeks the first time |
| Skip | cannon-es | last release v0.20.0 on 12 Aug 2022; no determinism statement found (registry.npmjs.org/cannon-es) | |
| Learning, design ideas | **evolution: simple GA or CMA-ES** (pycma, BSD-3; or about 200 lines in JS) | ES matched RL on humanoid walking: 10 min on 1,440 cores (arxiv.org/abs/1703.03864); a simple GA did Atari in about 4 h on one desktop (arxiv.org/abs/1712.06567); Karl Sims: population 300 × 100 generations in about 3 h on a 32-processor CM-5 (karlsims.com/papers/siggraph94.pdf) | 1 day |
| Learning, control ideas | **PPO with Stable-Baselines3 on CPU** | SB3 docs: PPO "is meant to be run primarily on the CPU" (stable-baselines3.readthedocs.io/en/master/modules/ppo.html). RL Zoo budgets: Walker2d 1e6 steps, Humanoid 1e7 (github.com/DLR-RM/rl-baselines3-zoo/blob/master/hyperparams/ppo.yml). CleanRL: Humanoid isn't learned at 1M steps (docs.cleanrl.dev/rl-algorithms/ppo/). No maintained JS RL or NEAT library: neataptic says "unmaintained" (github.com/wagenaartje/neataptic) | Humanoid-scale runs need checkpoint and resume across 6-h jobs |
| Self-play ideas (19–20) | our Go engines, plus counterfactual regret minimisation (CFR) or policy-gradient self-play in Go | no new dependencies | 3–5 days each |
| Compute | **GitHub Actions on the public repo, CPU only** | standard runner: 4 CPU, 16 GB, free on public repos (docs.github.com/en/actions/reference/runners/github-hosted-runners; docs.github.com/en/billing/concepts/product-billing/github-actions); 6 h per job, 20 concurrent jobs on Free, matrix up to 256 (docs.github.com/en/actions/reference/limits) | 20 runners × 4 cores = 80 cores. Design evolution: guess 50 ms per 5-second drop → 200 designs × 1,000 generations ≈ 2 min; 100 times slower still fits one 6-h job. **Benchmark before trusting this** |
| Island model | each runner evolves its own population; merge the best between rounds | no cross-runner sync needed; fits `simulate.yml` | 0.5–1 day |
| Recording for replay | **record per-frame transforms** (position + quaternion per body) for the episodes we'll show; keep each genome plus seed too | Rapier snapshots don't load across versions ("can't be loaded anymore", github.com/dimforge/rapier/blob/master/CHANGELOG.md), so pin the version, and archive transforms, not snapshots | 40 bodies × 7 floats × 4 bytes × 30 fps × 6 s ≈ 0.2 MB per drop; a 200-design swarm shot ≈ 40 MB. Feeds straight into `f32()` |
| Renderer additions | replay module (instanced meshes for swarms); Buh variants (Buh as the learner; one eye for squint/fail/win); generation counter; Gen 1 vs Gen N split; ghost trails; egg-splat effect | | 4–5 days |
| QA gates | the clipping check must allow real contact (penetration up to the engine's allowed slop); a new **replay integrity** gate: re-simulated hash = recorded hash, and no body teleports between frames | Rapier's guide suggests MD5 of snapshots to check determinism (rapier.rs/docs/user_guides/javascript/determinism) | 1–2 days |

**Anything that costs money or needs a key?**
- **API keys:** none.
- **Paid only if we choose it:**
  - GPU runners: $0.052/min, and they need a Team plan with a card on file
    (docs.github.com/en/billing/reference/actions-runner-pricing). Avoid; CPU is enough at this scale.
  - Artifact storage over 500 MB: the Free plan's quota; whether it applies to public repos is unclear. Overage is
    $0.25 per GB-month (docs.github.com/en/actions/reference/limits). Prune replays and keep only shown episodes.
  - Making the repo private: runners drop to 2 CPU and minutes become metered.
- **Retention:** artifacts last 90 days at most on public repos, so download the replays we'll keep.

## 6. Recommendation
**Go on the AI-learns lane, conditionally.** I checked it against two alternatives, and neither beats it overall.

| | AI learns X (this lane) | Alt A: Buh teaches itself family games (self-play on our Go engines) | Alt B: AI models play family games, graded by our bots (§7.1 lane B) |
|---|---|---|---|
| Ceiling | 1–17M long videos, 1–16M Shorts (§1) | b2studios Monopoly 12.1M, Code Bullet Connect 4 5.1M ([S]), but rare | Turing Games median 353K (§6) |
| New channels breaking out now | **yes**: 1.37M, 535K and 171K in the last 90 days | not seen | no; LLM copycats at 13–67 subs (§6) |
| Flood | 119 channels, median 9 subs | board-game flood, median 58 views (§5) | copycats exist (§6) |
| Shorts fit (motion from frame 1) | **best**: a swarm or a failure already moving | weak: cards on a table kept 24% (LESSONS) | medium |
| Build cost | M–L per idea; first video about 2–2.5 weeks | **S**: engines exist | S–M, plus **$10–270 per video in API** (§7.1) |
| Fit with Buh and our voice | **best**: Buh is the learner | good | good |

Alt A is cheaper but no stronger, so fold it into the lane as a second format (ideas 19–20). Alt B costs money every
video, and its characters (the models) go out of date.

**Conditions for the go:**
1. Buh is the AI. The creator's real voice is the trainer and narrator, like Yosh against his own AI.
2. Twelve to fifteen minute videos, each with one cheat-and-patch beat.
3. Titles that name a specific result or ask a specific question. Never "AI Learns to X", never "I Let Evolution
   Design X. Then…".
4. Thumbnails that ask, never answer.
5. A look that's clearly ours: the studio floor, teal one-eyed Buh. Pip's wind-up robots and AI Warehouse's cubes
   must not come to mind.
6. Before posting on Buh Simulates, hide the old reaction videos that fed it unrelated Suggested traffic
   (LESSONS, "First data"); otherwise use a fresh channel.

### Pilot: the egg drop (idea 1)
**Why this one:**
- Huge, practical search intent: the school project, with Mark Rober at 153M and 43.6M.
- No AI or evolution coverage at all.
- Rigid-body physics only, with evolution over a few dozen design numbers, so it's deterministic and the replay is
  exact.
- Failures are funny (splats), and a cheat is likely, such as a design that wins by never landing.
- Buh has a clear role: the engineer who keeps losing eggs.

**Before building, verify:**
- A published figure for egg strength, to set the break threshold.
- A real public school egg-drop rule set (size, mass, materials budget), to cite. Same rule as LESSONS: only public,
  checkable inputs.

**Long video, 12–15 min:**
1. Cold open on the strangest design falling, cut before the result.
2. The rules, from a real competition.
3. A Gen 1 splat montage.
4. The first survivor.
5. **The cheat:** show it, patch the rule, say so.
6. The drop height rises each round.
7. Evolved designs against the internet's usual tips (parachute, straw cage, cushioning).
8. The verdict on which tricks matter, then a callback and the comment question.

**Working titles, to test in Test & compare:**
- "Can Evolution Win the Egg Drop?"
- "What Would Evolution Build to Save an Egg?"
- "Every Egg-Drop Trick, Tested by Evolution"

Thumbnail: Buh holding an egg over the edge, a strange contraption half-visible, and "WILL IT CRACK?".

**Shorts (native vertical, 20–35 s, built from the same replays).** Each opens with the egg already falling and Buh
on screen by second 2.
- (a) Gen 1 against the final design.
- (b) The design that cheated.
- (c) "Which school egg-drop trick matters most?"
- (d) A Buh blooper.

Post Short (a) 2 days before the long video, then (b) and (c) on the two days after. Same time each day, with the
long video set as Related video.

**What to measure** (YouTube Studio, at 7 and 28 days):
- Long video: impressions and CTR, average view duration and % viewed, and where traffic comes from (lane videos or
  the old reaction videos).
- Engagement: likes/views, subs per 1,000 views, comments per 1,000.
- Shorts: stayed-to-watch, views, likes/views, subs per 1,000.

| Threshold | Fail | Pass | Strong | Basis |
|---|---|---|---|---|
| Long video views at 28 days | under 1,000 | 5,000 | 50,000 | new lane channels' median long video 185 and Pip's best 5.3K (§2); 50K is the bar for growing (§2) |
| Likes / views | under 2% | 3% | 5% | new channels 1.24%; Code Bullet 4.87%, b2studios 4.51% (§2) |
| Average % viewed | under 25% | 35% | 45% | my choice, no published bar |
| Subs per 1,000 views | under 1 | 2 | 5 | Perfect Play converts 2.6 (§5); my choice |
| Short stayed-to-watch at 7 days | under 50% | 60% | 70% | LESSONS target; 1of10 (§7.2) |
| Short views at 7 days | under 500 | 1,300 | 10,000 | lane median Short 852 (§2); 500–1,300 for tiny channels (§5) |

**Decision:**
- Long video and Shorts both pass: build the series (next: domino run, then trebuchet, then the first RL idea).
- Shorts pass but the long video fails: stay Shorts-first and run a second pilot (domino run) before another long
  video.
- Both fail: stop the lane and fall back to Alt A.

**Cost:** about 2–2.5 weeks of engineering (my estimate: harness 3–4 days, replay and visuals 4–5, gates 1–2), $0 in
compute, 2.5–3 hours of creator time (`docs/cadence-plan.md`), and about 30–40 minutes of rendering on Actions
(LESSONS).

## Raw data
- `docs/ai-sim-lane-scan-2026-11-21.txt`: every search row, gap-scan row and recheck.
- `docs/ai-sim-lane-channels-2026-11-21.json`: the landscape channels and the 119 new lane channels, with latest
  videos, Shorts and RSS entries.
