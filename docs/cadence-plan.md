# Posting more often: cadence plan (2026-11-04)

Goal from the creator: upload every few days, ideally daily.

## Recommendation
- **Daily Short** (7 a week), starting now. 36 are already written: `docs/shorts-backlog.md` (lint clean, every
  number traced). That's five weeks of daily Shorts before any new simulation.
- **Two long videos a week** (for example Tuesday and Friday), moving to three once scene templates exist.
- **Not daily long videos.** The limits are your recording time and the visuals, not the simulations. Quality of
  title, thumbnail and watch time matters more per long video than frequency. And YouTube's rule against
  mass-produced, repetitive content (the "inauthentic content" policy noted in NICHE_RESEARCH_PROMPT.md) is a risk if
  long videos start to look like the same template with a new game. Every video here is a different game or a
  different finding, which keeps us on the right side of it.

## Where the time goes (per long video)
| Step | Who | Time | Notes |
|---|---|---|---|
| Research, engine, rule tests, big run, script | Claude + GitHub Actions | about a day per new game | 8 long scripts already written; big runs take 20-50 min on Actions |
| Script review | you | 15-20 min | read it aloud once |
| Voice recording | you | 1-1.5 h | one long take; `make split` does the rest |
| Scenes (visuals) | Claude + you | the slowest step | only Exploding Kittens and Uno have scenes so far |
| Render | GitHub Actions | 30-40 min | scenes split into 10 s chunks |
| Mix, upload kit (3 titles, 3 thumbnails, description, captions) | Claude + you | 1 h | |

**The real bottlenecks:** your recording time, and scenes. Two fixes:
1. **One recording session a week:** two long scripts (about 2,000 words) plus seven Shorts (about 400 words) in one
   sitting, roughly 2 to 2.5 hours with retakes.
2. **Reusable scene templates** for game videos (a board, a card fan, a ranking chart, a "number to beat" chart),
   so each new game reuses the same building blocks with its own data. This is render-pipeline work, best done once
   (Exploding Kittens' scenes are the starting point).

## Long videos ready to go (script written, numbers traced)
1. Exploding Kittens (voice in progress, has scenes)
2. Sorry! (1.0B games)
3. Uno (has scenes)
4. Checkers (1.0B games)
5. Shut the Box (quick, exact maths)
6. Gin Rummy (1.0B games)
7. Battleship
8. Connect 4

That's four weeks at two a week. Next to build (about a day each): Phase 10 (engine done, needs the big run and
script), "I ranked 9 family games from luck to skill" (uses existing engines), Mancala, The Price Is Right wheel,
White Elephant (December), then the rest of the 14-game plan in `docs/next-episodes.md`.

## Four-week calendar (L = long video, S = Short from docs/shorts-backlog.md)
| Week | Mon | Tue | Wed | Thu | Fri | Sat | Sun |
|---|---|---|---|---|---|---|---|
| 1 | S ek1 | **L Exploding Kittens** + S ek2 | S so3 | S ek3 | **L Sorry!** + S so1 | S ek4 | S so2 |
| 2 | S so4 | **L Uno** + S un1 | S so5 | S un2 | **L Checkers** + S ck1 | S un3 | S ck2 |
| 3 | S ck3 | **L Shut the Box** + S sb1 | S ck4 | S sb2 | **L Gin Rummy** + S gn1 | S so6 | S gn2 |
| 4 | S gn3 | **L Battleship** + S bs1 | S ck5 | S bs2 | **L Connect 4** + S c41 | S gn4 | S bs3 |

Left over after four weeks: so7, un4, gn5, c42 (fillers), plus new Shorts from each new long video (4-6 each).

## Each week, in order
1. Monday: Claude drafts the next two long scripts and seven Shorts; you review.
2. One recording session (two long scripts and seven Shorts).
3. Claude splits and cleans the audio, maps scenes, renders on Actions, builds the upload kits.
4. Schedule the week's uploads in YouTube Studio in one go.
