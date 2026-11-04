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
- Measure jitter, don't eyeball it: track a label's centroid frame by frame (2nd-difference std in px).
  Chrome still snaps `translate3d` text; a tiny `rotate(0.02deg)` forces true sub-pixel compositing.
- Hidden 3D text must not cast shadows (`visible=false` until it appears): otherwise a dark blurry "ghost"
  of words not yet spoken sits on the floor. Statement scenes show their first line from the start (never
  open on an empty floor); later lines appear on their spoken cue.
- Keep decorative props fully in frame and clear of text (the checklist card fan was half off-screen).
- While a rules line names each card, light up that pile (lift + mustard label), timed from the word cues.

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
- **Studio voice without AI** (`voice_style: studio` in scenes.yaml): WPE de-reverb (signal processing, no
  model), broadcast EQ, two-stage compression, light saturation, expander. The creator doesn't want AI voice
  enhancement. Biggest real upgrade is still the room: record in a closet full of clothes, phone ~15 cm away.
- **Several sessions, one voice:** tag pick-up lines with `"session": "<name>"` in their json, save that
  session's room tone as `_roomtone_<name>.wav`, run `python -m pipeline.match_voice episodes/<slug>/voice`.
  Every line is leveled to -20 dB speech; other sessions get an EQ match and a noise-floor match to "main".
- **Tight pacing:** pauses inside lines capped at 0.35 s, 0.08 s lead / 0.15 s tail per line, 0.25 s between
  lines, 0.2/0.35 s scene pads. Video 1 lost 91 s of dead air and stumbles (8:50 -> ~7:20).
- **Never trust the transcript for audio QA.** Whisper stretches words over noises (it timed "The" across a
  burp) and deletes repeats. `python -m pipeline.audio_qa episodes/<slug>` force-aligns the script words
  (torchaudio MMS_FA, ~20 ms accuracy), then treats every sound outside the words as an event:
  burp/cough/hum -> replaced with the session's real room tone, extra speech >= 0.3 s -> cut, breath -> -12 dB,
  tiny blips at word edges -> kept (usually part of the word). Then each line is trimmed to its first/last word.
  Safety: every edited line is re-transcribed; an edit that removes ANY spoken word (script or not, e.g. an
  unscripted "percent") is undone, one edit at a time.
- **Chopped endings come from the split, not the cleanup.** `split_recording` ends each clip where the SCRIPT
  ends, so any extra spoken word ("...back to it later", "25 percent", "of the time") was cut off at the source.
  Fix: make script.md match the take, then `python -m pipeline.extend_tails episodes/<slug> <recordings...>`
  finds every clip in the original recordings and extends it while the sound continues. Heads are capped at
  0.15 s (a longer head pulled in the previous take: "lie.", "4%"); tails can run 1.2 s but check what they
  added (e2 pulled in the start of the next line). Run before tighten_voice.
- **Repeats are cut upstream, by hand-checked ranges** in `_stumbles.json` (Whisper hides many repeats even in
  verbatim mode; the aligner finds them as "speech outside the script words"). The QA step only blanks noises
  and protects anything that sounds like words; an automatic repeat cut once nearly deleted real content.
- The room bed must be RAW room tone (band-limited, steady frames only, equal-power loop crossfades). A
  noise-reduced bed is full of near-silent holes. The bed also fills dips inside lines (fills and cleanup can
  leave a spot 20 dB under the background). Check: no 10 ms frame > 12 dB under the narration's floor.
- **Room tone under the gaps.** The narration track used to be pure silence between lines; each line carries its
  own faint room noise, so the background cut out at every line end (heard as dropouts at 3:13, 5:40).
  `compose.narration_track` now lays a seamless room-tone bed under the gaps at the lines' own level.
- **Never insert digital silence.** The splitter put 0.12 s of zeros at every splice (14 lines) and the room-tone
  file had a zero run: next to speech that is an audible dropout. Splices and fills use real room tone; the
  final check fails any 10 ms of exact zeros.
- Don't double-cut: a range in `_stumbles.json` AND `_manual_cuts.json` removes audio twice ("The door is a
  kitchen..."). Keep each fix in one place.
- **Align to what was said, protect every word.** The script can differ from the take (an extra "percent").
  Before any fill/cut, Whisper (primed with the script line) listens to that spot; if it hears a word there,
  the spot is kept. Transcripts write "percent" as "%": normalise it or the safety check misses it.
- Fills must cover a noise's soft onset and tail (grow the region until the sound is within 4 dB of the floor,
  stopping short of the neighbouring words), else its edges stay audible.
- **Verify the result, not the edit list.** The first QA version reported 63 fills that did nothing (an inverted
  gain ramp). Now a self-test runs before every pass and every fill is re-measured afterwards ("STILL AUDIBLE").
  Same rule for everything: after an automatic fix, measure the output.
- Order of the voice pipeline: `split_recording` -> `find_stumbles` -> `tighten_voice` (+ `_manual_cuts.json`)
  -> `audio_qa` -> `match_voice`. Re-running `tighten_voice` rebuilds every line from `_orig/`, so always run
  `audio_qa` again after it. Any timing change makes a running render stale: cancel it and re-render.
- Single-word restarts ("Once a card - once one card") slip past `find_stumbles` (it wants a 2-word match);
  the final full-narration check against the script catches them. Fix with `_manual_cuts.json`.
- Pick-up sessions: use the LAST complete take of each line; watch for hidden asides at the start of a take
  ("sorry, let's try that again"); update script.md to the words actually said (captions follow it).
- Review flow for the creator: export the narration on the exact video timeline plus a list of every cut
  (time + words either side). They can also edit it themselves: docs/edit-your-own-audio.md.
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
- `render.yml` has an `only` input (space-separated scene ids) to re-render just the scenes that changed;
  assemble locally after swapping in their parts.
- Don't commit: music, voice audio, full transcripts, out/. `.gitignore` covers ALL audio anywhere under
  `episodes/*/voice/` (a new backup folder once slipped 27 voice clips into a public commit).

- **Clipping:** single-pass `loudnorm` + AAC let the final audio peak at +2.1 dBFS (the creator's friend heard
  it). `compose.mux` now applies the exact gain to -14 LUFS, a look-ahead limiter, and MEASURES the encoded
  file, lowering the ceiling until the decoded peak is <= -1 dBFS.

## Packaging
- **Never link the code** (repo, simulator) in descriptions, end cards or comments. The creator's call.
- **Length: at least 8:00** (mid-roll ads), with margin (aim ~8:20). If short, add real content from unused
  data or a fuller game primer (rules from the official sheet), never filler. Order: what the game is ->
  how a turn works -> what each card does.
- Captions for upload are the script's own words and punctuation, timed from the voice (two balanced lines,
  sentence breaks). Raw transcription captions (no punctuation, broken lines) are not acceptable.
- The music credit must be true (we use YouTube Audio Library tracks, credited by name), never "generated".
- Every episode goes in the public playlist **Board & Card Games, Simulated** (featured on the channel page);
  add theme playlists ("House Rules, Tested", Shorts) once a theme has 2+ videos.
- One GitHub issue per episode holds the full upload kit: files, titles, description to paste, settings,
  pinned comment. The video itself stays out of the public repo (music licence).
- 3 title/thumbnail pairs for YouTube **Test & compare** (winner = watch time). Every claim must be literally true.
- Mid-video subscribe ask right after a payoff, never in the opening.
- Pinned comment = the argument-starter question from the ending.

## Working with the creator
- They want autonomy: make the production decisions (studio sound, pacing, cuts) and explain briefly.
- No AI voice enhancement. Signal processing only.
- Plan ~14 episodes ahead; research + build in parallel with docs/agent-prompts/game-research-and-sim.md
  (give that agent its own branch).

## Per-episode checklist
1. Demand/competition scan → pick game → confirm public rules (save source link in RULES.md).
2. Go engine + rule tests → baseline "normal" bot → one-variable experiments → mirror check → big run on Actions.
3. Script in the PerfectPlay-style structure → lint → read aloud.
4. Scenes: map every line; contact sheet of stills.
5. Recording sheet → one long take → `make split` → `find_stumbles` → `tighten_voice` → `audio_qa`
   → `match_voice` → full-narration check vs script → listen-list (narration mp3 + cut list) → pick-ups.
6. Render on Actions (recorded timing) → assemble locally with voice + music → contact sheet, brightness-dip
   scan, loudness (-14 LUFS), caption check.
7. Upload kit: 3 titles + 3 thumbnails, description with chapters, SRT, pinned comment, end screen.
