# Agent prompt: research the next games, then simulate the best one

Copy everything below the line into a new Claude Code session on this repo (branch: your working branch).
Fill in the three `<…>` values first. Defaults are in brackets.

---

You are working in the `niche` repo for the YouTube channel **Buh Simulates**: "how to win a game people
actually play, proven by simulating billions of games". Read these first, in order, and follow them:
`docs/LESSONS.md`, `docs/next-episodes.md`, `docs/game-niche-research.md`, `docs/perfectplay-structure-notes.md`,
`docs/script-style-guide.md`. Look at one finished episode as the reference implementation:
`episodes/battleship/` (RULES.md, experiments.py, data/) and `sims/battleship/` (Go engine).

## Task (bounded: stop when the acceptance checklist is done)

**Part A: research (no code).** Find the best <N=5> candidate games for the next videos, excluding games we
already have (Exploding Kittens, Uno, Connect 4, Shut the Box, Battleship) and <EXCLUDE=none>.
For each candidate, collect with sources:
1. **Demand:** total views of the top ~20 YouTube results for "<game> strategy", "how to win <game>", and the
   most argued-about rule ("<game> <house rule>"). Use the same method as `docs/game-search-scan-*.txt`
   and save your raw numbers to `docs/game-search-scan-<date>.txt`.
2. **Competition:** existing simulation / "I solved X" videos and their views. A big existing sim video is a
   minus; zero sim videos with high demand is the sweet spot.
3. **Virality angle:** one specific, argument-starting question the video answers (pattern that works:
   "I tested every Uno house rule. One breaks the game."). Generic "best strategy" angles score low.
4. **Verifiability:** link to the official rules / component list (publisher PDF or instruction sheet).
   **Reject the game if any number we'd need (deck counts, board layout, scoring) can't be verified from a
   public source.** We own no physical copies. Wrong numbers kill credibility.
5. **Simulability:** are there real decisions to test (not pure luck)? Rough engine size in Go?
6. **Audience/RPM note:** kids' games reach far but earn less; gambling games are ad-unfriendly.
Score each 1–5 on demand, competition (5 = none), angle, verifiability, simulability. Write the table and a
one-paragraph recommendation into `docs/next-episodes.md` (add a dated section, keep the old one).

**Part B: build and simulate the top pick** (only if it scored ≥ 4 on verifiability).
1. `episodes/<slug>/RULES.md`: rules digest + source links + date checked + any edition differences.
2. Go engine in `sims/<slug>/` with **rule tests** (`go test`): setup counts, every special card/rule, edge cases.
3. Bots that only use information a real player has. A "normal" baseline bot, then one-habit variants.
4. `episodes/<slug>/experiments.py` with `--games N --seed S --out DIR --all` (same interface as
   `episodes/battleship/experiments.py`) writing `data/results.json`.
5. **Engine check:** one result the engine must reproduce from plain math (e.g. a probability you can compute
   exactly) — write both numbers in the data file.
6. **Mirror check:** when every seat uses the same bot, each seat wins its fair share (± noise). If not, find the bug.
7. Pilot locally (small N), then the **big run on GitHub Actions**: `.github/workflows/simulate.yml` with
   `episode=<slug>`, `extra_args=--all`, and `games_per_shard` chosen so the total is at least
   **<MIN_GAMES=1,000,000,000> simulated games** (20 shards × tests × games_per_shard) and finishes in < 1 h.
   Merge with `episodes/<slug>/merge_shards.py` if numbers need more than averaging, else the generic merge.
   Record the true total in the data file. Scripts may only claim what the total supports
   ("billions" needs ≥ 2B; otherwise "over a billion" / "hundreds of millions").
8. `episodes/<slug>/script.md` draft in the house structure, every number traced in the header to a data key,
   untested explanations labelled "my guess", `make lint-script` clean.

## Rules
- Only public rules/components. Never copy PerfectPlay's titles, wording or look. Never link the code anywhere
  (descriptions, end cards, comments).
- Don't touch other episodes, the render pipeline, or voice files. Don't commit music, voice audio or `out/`.
- Commit small, descriptive commits; push to the working branch. No pull requests unless asked.
- If something blocks you (rules not verifiable, engine can't pass the mirror check), stop and write what you
  found and why into `docs/next-episodes.md` instead of guessing.

## Acceptance checklist (report each item back with evidence)
- [ ] Research table with sources + recommendation in `docs/next-episodes.md`; raw scan file committed.
- [ ] RULES.md with official source links.
- [ ] `go test ./...` passes in `sims/<slug>`.
- [ ] Engine check: math vs engine numbers, within 0.1 percentage points.
- [ ] Mirror check passes.
- [ ] Big run finished: Actions run URL, total games ≥ <MIN_GAMES>, merged `data/results.json` committed.
- [ ] Script draft, lint clean, every number traceable.
- [ ] Final message: the recommended title/angle, the 3 most surprising results, and anything you'd re-check.
