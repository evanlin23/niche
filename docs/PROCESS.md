# Buh Simulates: how an episode gets made (end to end)

Read this first, then `docs/LESSONS.md` (the why behind every rule) and `docs/scene-kit.md` (templates + gates).
Exploding Kittens (`episodes/exploding-kittens/`) is the reference episode for every step.

**Quality is ensured by gates, not by eyeballing.** Four commands, each fails loudly with a readable report;
a step is done only when its gate passes (fix the source, never waive a failure silently):
| when | command | report |
|---|---|---|
| after recording | `make voice SLUG=<slug> REC=rec.m4a` | `voice/_report_voice.txt` + `voice/_listen.mp3` |
| before any render | `make qa-visual SLUG=<slug>` (+ `VERTICAL=1` for Shorts) | `out/qa/visual.txt` + `contact.png` |
| after the render | `make qa-visual SLUG=<slug> VIDEO=out/final/<slug>.mp4` | adds black-frame / flash checks |
| after assembly | `make qa-final SLUG=<slug>` | `out/qa/final.txt` |

## Ground rules (never break)
- Public repo. **Never commit** voice audio, music, full transcripts or `out/`. Never link the code anywhere
  (descriptions, end cards, comments). Only games whose rules/components are publicly verifiable.
- Never copy PerfectPlay's titles, wording or look.
- Voice = the creator's own recording, lightly cleaned (`voice_style: studio`). No AI voice, no generative
  enhancement (tried, rejected: it changed words).
- Give the creator times in **US Central time**. Make production decisions yourself; explain briefly.
- Commit + push every change on your working branch. No PRs unless asked.

## 0. Pick the game
`docs/next-episodes.md` has the 14-episode plan (demand, competition, angle, verified rules link).

## 1. Simulate
1. `episodes/<slug>/RULES.md`: official rules digest + source links + date checked.
2. Go engine in `sims/<slug>/` with rule tests (`go test ./...`).
3. Bots that only know what a real player knows: a "normal" baseline + one-habit variants.
4. `episodes/<slug>/experiments.py --games N --seed S --out DIR --all` -> `data/results.json`.
5. Engine check (a number provable by math) and mirror check (same bot everywhere = fair shares).
6. Big run on Actions: `.github/workflows/simulate.yml` (episode, extra_args `--all`, games_per_shard).
   Claims must match totals ("billions" needs >= 2B).

## 2. Script
- House structure: `docs/script-style-guide.md`, `docs/perfectplay-structure-notes.md`.
- Every number traced to a data key in the script header. Guesses labelled "my guess".
- `make lint-script SLUG=<slug>`. Length target **8:20+** (8:00 minimum for mid-rolls).
- `make recording-script SLUG=<slug>` -> one clean sheet for the creator.

## 3. Record (creator)
Phone recorder ~15-20 cm away, quiet room. 10 s of silence first, then read top to bottom with 1-2 s
between lines. Fumble = pause, redo the whole sentence (the last take wins). Send the m4a in the session chat.

## 4. Voice pipeline: `make voice SLUG=<slug> REC=rec.m4a` (gate)
One command runs the chain below in order, stops at the first failing step (resume with `FROM=<step>`), then the
final check (transcript vs script, abrupt endings, digital silence, clipping, long gaps) and writes the report and
the listen file.
Two input guards run first (`pipeline/voice_source.py`): a recording whose peaks are stored above full scale (a
float m4a) is gain-reduced to a -4.5 dBFS peak in `voice/_input/` before splitting, so nothing clips downstream
(reported at the top of the voice report); and `voice/_orig/` backups are keyed to the recording each line was
split from (fingerprint in every line's json): a new recording refreshes them, an unfingerprinted backup is
refused (`LEGACY_ORIG=1` to reuse one on purpose). Never silently reused.
The individual steps, for reference:
```
python -m pipeline.split_recording episodes/<slug> rec.m4a          # per-line clips + json timing
python -m pipeline.extend_tails   episodes/<slug> rec.m4a          # restore chopped word endings
python -m pipeline.find_stumbles  episodes/<slug>                   # restarts/repeats -> _stumbles.json
python -m pipeline.tighten_voice  episodes/<slug>/voice --cuts episodes/<slug>/voice/_stumbles.json
python -m pipeline.audio_qa       episodes/<slug>                   # burps/clicks/dropouts; then --final-check
python -m pipeline.match_voice    episodes/<slug>/voice             # same tone/level across sessions
```
- Update `script.md` to what was actually said (captions come from it), then re-run the alignment steps.
- Send the creator one full-narration listen + a short list of anything you changed. Fix what they hear.

## 5. Visuals (scene kit: `docs/scene-kit.md`)
- `episodes/<slug>/scenes.yaml` (copy EK's header: `engine: 3d`, `look: clean-sage`, `grade`,
  `burn_captions: false`, `voice_style: studio`, `music:`) with **kit templates** (statement, title, bars, deck,
  fan, table, lineup, grid, track, odds, checklist, endcard). No scenes3d.py / web/scenes.js unless the game needs
  a custom scene (build it on `Kit`). Numbers as data refs (`"=results.json:..."`), timing as word anchors.
- Stills: `make stills SLUG=<slug>` (+ `VERTICAL=1`); gate: `make qa-visual SLUG=<slug>` must PASS before
  the full render (use `TTS=silent` before the voice exists).
- **Everything the narration says that can be shown gets its own scene** (creator rule, Uno): a rule being explained is
  played out at a table, a habit is shown in a hand, a number gets a chart or a callout the moment it's said. One beat
  per scene, roughly 5-20 s; never park a topic on one chart for 40+ s. Group lines only when they show the same thing.
- Everything moves and follows the voice: events anchored to words (`'line@word'`), never more than ~5 s
  without something new; player count always shown; cards square-on; hard cuts between scenes.
- Iterate with local stills (`allstills`-style PNGs per scene) before any full render.
- Full render on Actions: `render.yml` with `slug=<slug>`, `tts_engine=recorded`, `ssaa=1.5`
  (~40-70 min, chunked). Re-render single scenes with `only="sceneA sceneB"`.

## 6. Assemble + QA (locally; music is not in git)
- Music: YouTube Audio Library tracks in `music/` (local only; ask the creator to upload them to a new
  session). Same three as EK: Days Are Long (Silent Partner), Renunciation (Asher Fulero), Ponderous Days
  (Joel Cummins).
- Download the run's `scene-*` artifacts into `episodes/<slug>/out/final/scenes/`, then
  `TTS_ENGINE=recorded VOICE_DIR=episodes/<slug>/voice python -m pipeline.cli episode <slug> --only none --assemble`
- Gates: `make qa-visual SLUG=<slug> VIDEO=episodes/<slug>/out/final/<slug>.mp4` (black frames, flashes,
  contact sheet every 10 s) and `make qa-final SLUG=<slug>` (-14 LUFS, decoded peak <= -1 dBFS, >= 8:00,
  no burned captions, SRT present). Both must PASS before anything goes to the creator.
- Send the creator the 1080p file + a 720p preview.

## 7. Upload kit (one GitHub issue per episode, like issue #1)
Title + 3 thumbnails (1280x720) for A/B testing, description with chapters (from
`out/final/description-long.txt`), SRT (`out/final/<slug>.en.srt`), tags, playlist
"Board & Card Games, Simulated", end screen (video left / subscribe right template, "Best for viewer" until the
next video is out), pinned comment = the argument-starter question. Branding lives in `branding/`.

## 8. Shorts (native 9:16, no extra recording)
`episodes/<slug>/shorts_native.yaml` picks moments (script lines) and kit templates; `.github/workflows/shorts.yml`
renders them at 1080x1920 (hook, word-timed captions, "Full video on my channel" + Buh) and runs the visual gate in
9:16. Locally put the long video's own mix in: `python -m pipeline.shorts_native <slug> --assemble --audio
episodes/<slug>/out/final/<slug>.mp4`, then `python -m pipeline.qa_final <slug> --short --video <short>.mp4`.
