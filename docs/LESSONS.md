# Lessons learned (read this before starting a new episode)

Collected while making video 1 (Exploding Kittens). Newest lessons are folded into the checklist at the bottom.

## Niche & positioning
- **Format that works:** "how to win a game people actually play, proven by simulating billions of games".
  Credibility (tested, not opinion) + an existing audience (players) + a reason to watch (they want to win).
- **Don't copy PerfectPlay's title formula** ("The Best X Strategy, Tested on N Million Games"): 8+ copycat
  channels using it get 0–6K views. Big hits ask *one specific question* or promise a *surprising verdict*.
- **Only games with fully public rules/components.** We own no physical games; numbers printed only on
  cards/boards (e.g. Game of Life 2021) can't be verified, and wrong numbers kill credibility.
  Good: published deck lists (Exploding Kittens, Uno), standard decks, dice games, digital games.
- **Pick by demand vs competition:** run the YouTube scan (`docs/game-search-scan-*.txt`). Exploding Kittens
  had 8.6M views across top "strategy" results and zero simulation videos.
- **Widen the audience early:** follow niche-but-big games with games everyone knows (Uno, Yahtzee, Connect 4).

## Script (see docs/script-style-guide.md and docs/perfectplay-structure-notes.md)
- Structure that works: relatable cold open (the people at *your* table) → headline numbers in ~20 s →
  credibility (official rules + an engine check against plain math) → **state a limitation early and pay it
  off at the end** → named bots → ranking first, then "a ranking doesn't tell you why" → one-habit tests vs a
  stated number to beat → **mistakes** framing → a true confession/aside → recipe → callback + comment question.
- **Never explain a result with an untested reason.** Label guesses as guesses (we cut one and said so on camera).
- **Every number traces to a data file** (listed at the top of script.md). Re-check after any re-run.
- Add a 10-second game primer after the hook for people who haven't played.
- If you mention a threshold ("1 in 3"), tell viewers how to *see* it at the table (count cards ÷ Kittens).
- `make lint-script` before recording: banned AI phrases, symbols, digits, long sentences.

## Simulation
- Write engines in Go (≈270k games/s/core). Python is too slow for billions.
- **Test the rules** (setup counts, edge cases like stacking Attacks) before trusting any result.
- Bots only use information a real player has. Say this on camera.
- Run **one-variable experiments** vs a fixed "normal" table; fair share is the baseline.
- **Mirror check:** when every seat uses the "best" bot, each must win exactly the fair share.
- **Make big numbers true:** GitHub Actions (`simulate.yml`, 20 shards × independent seeds) ran 10.2 billion games
  in ~30 min for free. Results moved ≤0.17 points from 1M→100M games per test, so rounded script numbers held.

## Visuals
- Look: clean seamless studio, **sage** floor (`look: clean-sage`), soft shadows, our own card designs
  (never the publisher's art), Rubik font, mustard/coral accents. Avoid PerfectPlay's slate + yellow + Oswald.
- **Text:** extruded 3D text lying on the floor, camera nearly overhead, bright self-lit faces + darker sides,
  darker floor behind it, *level* push-in (orbiting an overhead camera tilts the words).
- **Smoothness without a GPU:** supersampling (`ssaa: 1.5`) + glossy materials + reflections (`quality: high`).
- Charts: read values from data files only; give tall charts headroom (max value ≤ ~75% of the axis);
  put footnote pills under the title, not over bar labels; fair-share label must stay on screen.
- Cards in flight should not cast hard shadows (they look like holes in the table).
- Always render one still per scene and eyeball a contact sheet before a full render.
- **Hard cuts between scenes.** A dip to the background at every scene boundary reads as a flash. Only the end
  card fades out. (`scrim()` defaults to no fade; a scene can opt in with `fade_in`/`fade_out` in its spec.)
- **Labels that follow the camera must be sub-pixel.** `left/top` snap to whole pixels, so projected labels
  wiggle during a push-in or orbit. `Stage.updateTexts` now moves manual labels with `translate3d` and uses
  tabular numbers so counting values don't shift width. Check with a frame-by-frame clip, not stills.
- Hide bars until they start growing (a 0-height rounded box still renders as a flat slab on the floor).
- Check motion with a low-res clip of the whole scene (`SCALE=0.35`), stills hide jitter and flashes.

## Camera (research notes, see sources in docs/camera-research.md)
- One dominant move per shot. Slow orbit 1-4 deg/s (we use ~1 deg/s, max +/-8 deg for wide charts: wider arcs
  make the edge bars lean and the fair-share line tilt), push-in 10-20% of distance on a key reveal.
- Speed cap: nothing should cross the frame faster than ~7 s per frame width (about 6-9 px per frame at 1080p30).
- Never fully still, but hold near-still while a dense label must be read. 30 fps is enough for slow moves.
- Keep labels inside a 5% title-safe margin; clamp projected positions.
- Overhead text shots don't orbit (rotating an overhead camera tilts the words); use a level push-in.

## Voice
- **One long recording is easiest.** Pixel Recorder ~15–20 cm away, 10 s of room tone first, pause between
  lines, redo the whole phrase on a mistake. `make split` aligns it with Whisper at *phrase* level, keeps the
  last take, splices mid-line restarts, and handles numbers ("13.04%" vs "thirteen point oh four").
- **Transcripts hide stumbles.** Whisper cleans up restarts ("the best of - the best of them" -> "the best of
  them") and fillers, so the normal split can't see them. `python -m pipeline.find_stumbles episodes/<slug>`
  re-transcribes verbatim and writes cut ranges; then `python -m pipeline.tighten_voice episodes/<slug>/voice
  --cuts .../_stumbles.json --words .../_verbatim.json`. Video 1 had restarts in 19 of 59 lines.
- **Tight pacing:** pauses inside lines capped at 0.35 s, 0.08 s lead / 0.15 s tail per line, 0.25 s between
  lines, 0.2/0.35 s scene pads. Video 1 lost 91 s of dead air and stumbles (8:50 -> ~7:20).
- Transcribers drop fast words like "percent": check the audio (voiced gap) before asking for a re-record.
- Re-records: `split_recording --only <ids>` replaces just those lines. Compare takes; keep the cleaner one.
- Cleanup (high-pass, noise profile from room tone, de-ess, compression) handles light rain/street noise.
  It can't fix overlapping loud sounds (thunder, sirens): redo those lines.
- Your natural pace (~190 wpm) matches PerfectPlay (175–193). Slow down only on key lines and punchlines.
- **Captions follow script.md**, so update script text to what was actually said.
- Voice audio stays local (public repo); GitHub gets only per-line timing JSON.

## Music
- YouTube Audio Library, "No attribution required". Files stay local (licence ≠ redistribution).
- "Contemplative" = slow sparse piano/pads, minor-ish, no drums/vocals/swells. Measure tracks (loudness range,
  busyness, swell) and let the creator pick by ear from a sampler. High-pass music under the voice.

## Pipeline & ops
- Rendering is CPU-bound (software WebGL): 4–7 s/frame at 1080p with ssaa 1.5 on GitHub runners (3D text and
  soft shadows are the expensive parts). Video 1 took ~2.5 h because one runner per scene meant the longest scene
  set the wall time. Now scenes are split into ~10 s chunks (RENDER_CHUNK=k/n), so a whole episode takes ~30–40 min.
- Final mix happens locally (voice + licensed music), visuals on GitHub.
- Don't commit: music, voice audio, full transcripts, out/.

## Packaging
- **Never link the code** (repo, simulator) in descriptions, end cards or comments. The creator's call.
- 3 title/thumbnail pairs for YouTube **Test & compare** (winner = watch time). Every claim must be literally true.
- Mid-video subscribe ask right after a payoff, never in the opening.
- Pinned comment = the argument-starter question from the ending.

## Per-episode checklist
1. Demand/competition scan → pick game → confirm public rules (save source link in RULES.md).
2. Go engine + rule tests → baseline "normal" bot → one-variable experiments → mirror check → big run on Actions.
3. Script in the PerfectPlay-style structure → lint → read aloud.
4. Scenes: map every line; contact sheet of stills.
5. Recording sheet → one long take → `make split` → review report → re-record list.
6. Render on Actions (recorded timing) → assemble locally with voice + music → spot-check frames.
7. Upload kit: 3 titles + 3 thumbnails, description with chapters, SRT, pinned comment, end screen.
