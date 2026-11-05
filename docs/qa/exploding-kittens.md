# Exploding Kittens through the new gates (2026-11-05)

`make qa-visual SLUG=exploding-kittens` on the published scene list (recorded timing, stage state every 0.1 s).
Full report: `docs/qa/exploding-kittens-visual.txt` / `.json`. EK was **not** re-rendered (except as noted);
these are content issues for the record, fixed for every future episode by the kit (which handles each case).

**Result: FAIL, 79 errors, 49 warnings** (52 safe-area, 19 overlap, 6 coverage, 2 cut-off, 4 anchor warnings,
39 "number shown but not said" warnings).

| # | finding | where | kit behaviour now |
|---|---|---|---|
| 1 | Kitten "at the bottom" lay on top of the last card, so a card showed under it (creator spotted it; no gate saw it: stacking order) | placement | **fixed** in EK scenes.js + kit (deck order = stacking order, wider gap). Re-render `placement` (+ the Short) if the video is re-cut |
| 2 | "BUH SIMULATES" brand at (56, 36) is 40 px outside title-safe | all 32 scenes | kit brand sits bottom-left inside safe |
| 3 | Seat names and event pills on the table run off the safe area (THE PATIENT ONE 54 px, BOOM / DEFUSED 53 px) | cold | kit labels are clamped to title-safe; table fitted to the content rect |
| 4 | Pawn names in "meet the bots" 12-49 px outside safe at the bottom | meet | lineup fitted above/below the habits panel |
| 5 | Callout chips sit on the bottom row of pile labels ("5 × Nope", "5 × See the Future") for most of the scene, 16 overlaps | rules | callouts have their own row, never over the content |
| 6 | "4 × Exploding Kittens" label 27 px outside safe | rules | clamped |
| 7 | "TOP OF DECK" 17 px outside safe | placement | clamped, row fitted |
| 8 | A counting bar value passes over the fair-share label (one frame each) | ranking, small, twoplayer | fair label beside the line (16:9) / in the pill (9:16), value size follows bar spacing |
| 9 | 5.3-7.9 s of narration with nothing new on screen | five (6.9 s), check (7.9 s), seats (6.0 s), future (5.5 s), odds (5.4 s), small (5.3 s) | the gate fails these before render; add a word-anchored callout/event |
| 10 | Bar still growing at the cut (anchored to the scene's last word) | patience, length | kit tweens always finish before the last frame |
| 11 | Statement lines not timed to a spoken word (first word never said) | check ("math says 13.04%"), m4 (2 lines), confession | warn: give them an `at:` anchor |
| 12 | Title card props partly off-screen (ring of cards around the words) | title | kit title ring is fitted inside the frame |

Numbers: no on-screen number contradicts the line it is anchored to (0 errors). 39 values are shown without being
said (e.g. the attacks chart 22.8 / 38.2 / 7.4% while the line says "almost one in four"); those are warnings and
fine when the voice gives the rounded version.

Pipeline bugs found while building the gates (fixed): `pipeline/render.py` imported skia at module load, so the 3D
path failed on machines without libEGL; EK's anchor resolver drops a callout whose word isn't spoken with only a log line
("callout skipped"; none in EK today): the anchors gate now fails on any unresolved anchor; kit tweens could outlast
the last frame by one frame (the last frame is `(n-1)/fps`, not the duration).
