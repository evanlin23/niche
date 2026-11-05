# Scene kit + QA gates (production kit)

Everything an episode session needs to go from script to a checked render without hand-built scenes or eyeballing.
Code: `pipeline/web/kit.js` (templates), `pipeline/kit.py` (anchors, data refs, specs), `pipeline/qa_visual.py`,
`pipeline/voice_gate.py`, `pipeline/qa_final.py`, `pipeline/shorts_native.py`. Demo of every template:
`episodes/kit-demo/` (silent timing, never published).

## Handoff: how an episode session uses this

1. **Scenes.** Write `episodes/<slug>/scenes.yaml` with kit templates (`render: bars`, `deck`, `table`, ... below).
   No `sim/scenes3d.py` and no `web/scenes.js` are needed: the CLI falls back to `pipeline/kit.py` and
   `/pipeline/web/kit.js`. If the game needs a custom scene, add `web/scenes.js`:
   ```js
   import { KIT, Kit, buildWith } from '/pipeline/web/kit.js';
   const myBoard = async (stage, spec) => { const K = new Kit(stage, spec); K.header({}); K.contentRect(); /* ... */ return K.frame((t) => {}); };
   export const build = buildWith({ ...KIT, myBoard });
   ```
   Build custom scenes on `Kit` (header rows, `fit`, `tw`, `key`) and the gates check them like the rest.
2. **Numbers** come from data files, never typed: `value: "=results.json:placement[value=next].win*100"`
   (`file:path` with `[key=value]` list filters, optional `*scale`, `/round0..9`, default 1 decimal).
3. **Timing** is word anchors: `at: k5@thirty`, `k5@thirty#2` (2nd time), `k5@first_card` (phrase),
   `k5@thirty+0.3`, `k5` (line start), `k5:end`. Before the voice exists use `TTS=silent` (estimated timing).
4. **Iterate with stills**: `make stills SLUG=<slug>` and `make stills SLUG=<slug> VERTICAL=1` (contact sheets in
   `out/stills*/`).
5. **Gates** (each one command, each fails loudly with a readable report; details below):
   - after recording: `make voice SLUG=<slug> REC=rec.m4a` -> `voice/_report_voice.txt` + `voice/_listen.mp3`
   - before any render: `make qa-visual SLUG=<slug>` (and `VERTICAL=1` for anything that becomes a Short)
   - after the Actions render, locally: `make qa-visual SLUG=<slug> VIDEO=out/final/<slug>.mp4` (adds pixel checks)
   - after assembly: `make qa-final SLUG=<slug>`
   - any change to the kit: `.github/workflows/kit-ci.yml` renders the torture test (`episodes/kit-torture`) in both
     orientations and runs every gate; locally `python -m pipeline.render_check kit-torture [--vertical]`
   A gate that fails is fixed at the source (scenes.yaml, the take, the kit), never waived silently. If a rule is
   wrong, fix the rule in the gate with a test in `tests/test_qa_gates.py` (`make test-gates`).
6. **Shorts**: `episodes/<slug>/shorts_native.yaml` (below), render on Actions with
   `.github/workflows/shorts.yml`, then put the real mix in locally:
   `python -m pipeline.shorts_native <slug> --assemble --audio episodes/<slug>/out/final/<slug>.mp4`.

## Layout rules the kit guarantees

- One template works in **16:9 and 9:16**: the 3D content is fitted into a content rect (camera distance found by
  search, then a view offset centres it), the DOM text sits in rows: title, player pill, notes, callouts (16:9:
  callouts in a footer row above the brand; 9:16: under the notes). Rows never overlap each other or the content.
- Every label is clamped to the 5% title-safe area; projected labels move sub-pixel (no jitter).
- Always moving: fitted orbit (about 1 deg/s, max +/-6 deg) + push-in; overhead text uses a level push-in.
- Every eased transition is a registered tween (`K.tw(name, at, dur)`) that **finishes before the last frame**,
  so a word anchored to the very end of a scene can't produce a cut-off animation.
- Hard cuts; only the end card fades. Cards square-on, stacked by real thickness, inserted cards between their
  neighbours' heights (deck order = stacking order).
- Shorts chrome (only when rendered as a Short): hook on top, big word-timed captions (1-3 words, one line,
  from the aligned voice) above a compact "Full video on my channel" + Buh. The scene title is replaced by the
  hook; the player pill stays. **The first second decides everything** (the first EK Short kept 24% of viewers:
  it opened on an empty table): in a Short every template's main visual (`K.build`) is pre-built so frame 1 shows
  it nearly built and still growing, the word anchors become emphasis pulses, and the camera opens on a quick
  sideways swing (fastest at frame 1, settled by 1.2 s, included in the camera fit) at full framing.

Common params on every template: `title`, `pill` (free text), `callouts: [{text, at, color?: CORAL|CREAM}]`
(one at a time, word-timed), `notes: [{text, at}]` (stay until the next note), `no_brand`, `yaw` (orbit degrees).

## Templates (scenes.yaml params)

### statement / title: big 3D words on the floor with an orbit
```yaml
- id: m4
  render: statement            # title = same + "BUH SIMULATES" kicker + a ring of our cards
  lines: [k1]
  params:
    size: 1.0
    lines:
    - 'Mistake 4:'                                   # appears when its first word is spoken
    - {text: hiding the Kitten, color: MUSTARD, at: k1@hiding}   # or an explicit anchor
```
On 9:16 long lines wrap in two automatically. The first line is up from frame 0 (never an empty floor).

### bars: ranking / comparison chart
```yaml
- id: ranking
  render: bars
  lines: [b5]
  params:
    title: One table, five bots
    callouts: [{text: "Seats shuffled every game", at: b5@shuffled}]
    chart:
      players: 5          # pill "5 players · fair share 20%" always on screen
      fair: 20            # fair-share line (16:9: labelled beside the line; 9:16: the pill says it)
      unit: '%'           # maxV optional: default = tallest bar at ~75% of the axis
      decimals: 1
      items:
      - {label: The Patient One, value: "=ranking-5p.json:table[name=The Patient One].win*100", color: MUSTARD, at: b5@thirty, hl: true}
      - {label: The Hoarder, value: "=ranking-5p.json:table[name=The Hoarder].win*100", color: CORAL, at: b5@eleven}
```
Each bar grows on its word and counts up; label wrap width and value size follow the bar spacing. An item with
`context: true` (a value implied by what is said, e.g. the 2-player complement) is shown without an anchor and the
number gate treats it like the fair-share line.

### deck: card piles (rules) or a spread row (placement), optional chart
```yaml
- id: rules                     # piles: each named card flies up big while it is said
  render: deck
  lines: [g1, g2]
  params:
    title: Original edition · 56 cards
    pill: 4 players
    name_words: {kitten: 0, kittens: 0, defuse: 1, cat: 2}     # word -> pile index (or highlights: [[pile, at]])
    piles:
    - {card: 0, count: 4, label: 4 × Exploding Kitten}
    - {card: 1, count: 6, label: 6 × Defuse}
    - {card: [8, 9, 10, 11, 12], count: 20, label: 20 × Cat cards}
- id: placement                 # row: the hero card moves between slots on the words, a gap opens
  render: deck
  lines: [k2, k3]
  params:
    row: {count: 12, ends: [TOP OF DECK, BOTTOM]}
    hero: 0
    plan: [[k2@random, 6], [k3@bottom, 12], [k4@top, 0]]       # [anchor, slot]; slot = count means the bottom
    chart: {players: 4, fair: 25, items: [...]}                 # beside on 16:9, below on 9:16
```
Card faces: an EK type number, `'back'`, `'uno:<colour>:<kind>'`, or a generic face `{name: SKIP, color: BLUE, value: 7}`.
Cards only ever come from `kitCard()` and stack with `layerY(i)` (`CARD_SEP` apart along the normal); see "Never again:
cards" in docs/LESSONS.md. Custom scenes must use them too (the static gate fails hand-built cards).

### fan: a hand held by a seat
```yaml
- id: hand
  render: fan
  lines: [f1]
  params:
    seat_label: YOU
    cards: [3, 6, 1, 8, 2]
    highlights: [{card: 0, at: f1@skip, label: SKIP}, {card: 2, at: f1@defuse, label: DEFUSE}]   # lift + name pill
    play: [{card: 4, at: f1@attack}]                                                             # to the pile
```

### table: N seats with pawns, hands, deck and discard
```yaml
- id: cold
  render: table
  lines: [o1, o2]
  params:
    players: 5                                  # as many seats as bots discussed
    names: [THE PATIENT ONE, THE NORMAL PLAYER, THE GAMBLER, THE PANICKER, THE HOARDER]
    hands: 5                                    # or a list per seat; hands face their owners
    highlight: [[2, o2@plays], [3, o2@skips]]   # pawn hops, name turns mustard
    turns:                                      # word-timed plays/draws with a pill over the seat
    - {at: o2@plays, seat: 2, ev: play, card: 2, label: ATTACK}
    - {at: o2@steals, seat: 4, ev: draw}
    turns_auto: {from: 0.4, every: 1.2}         # optional: keep play going round the table
    out: [[3, o3@out]]                          # pawn tips over
```

### lineup: meet the players
```yaml
- id: meet
  render: lineup
  lines: [b2, b3]
  params:
    bots:
    - name: The Gambler
      color: CORAL
      at: b3@gambler                            # steps forward, panel shows its habits
      habits: [{text: Plays cards on a whim, at: b3@whim}]
```
16:9: habits panel above the pawns; 9:16: below them (two rows of pawns when more than three).

### grid: checkers (board on the floor) or connect-4 (upright)
```yaml
- id: jump
  render: grid
  lines: [g1]
  params:
    pill: 2 players
    style: checkers          # or connect4
    rows: 8
    cols: 8
    pieces: [[5, 0, RED], [2, 1, BLACK], [4, 3, RED]]              # [row, col, colour, king?]
    moves:
    - {at: g1@first, from: [5, 0], to: [4, 1]}
    - {at: g1@jumps, from: [2, 1], to: [6, 5], capture: [[4, 3]]}  # hop arc, captured piece lifts away
    - {at: g1@king, from: [6, 5], to: [7, 4], king: true}
    highlight: [{at: g1@side, until: g1@then, cells: [[4, 1]], color: MUSTARD}]
# connect4: moves: [{at: c1@drops, col: 3, color: RED}]   (falls to the lowest free cell)
```

### track: Sorry!/Ludo-style loop
```yaml
- id: bump
  render: track
  lines: [k1]
  params:
    pill: 4 players
    length: 60                              # squares around the loop (15 per side)
    colors: [RED, BLUE, YELLOW, GREEN]
    start_square: [4, 19, 34, 49]           # where each colour enters the loop
    home_len: 5
    slides: [{from: 1, len: 4, player: 0}]
    pawns: [{id: r1, player: 0, on: start}, {id: b1, player: 1, on: 30}]     # on: start | square | home:k
    moves:
    - {at: k1@leaves, pawn: r1, to: 4}      # steps square by square
    - {at: k1@bumped, pawn: r1, to: start}  # bump back to start
    highlight: [{at: k1@seven, until: k1@bumped, squares: [5, 6, 7, 8, 9, 10, 11]}]
```

### odds: probability grid
```yaml
- id: odds
  render: odds
  lines: [p4]
  params:
    item: card                 # or dot
    hit_face: 0                # face of a "hit" (shown face up, the rest face down)
    frames:                    # headline + sub change on the words; cards leave to a discard pile in frame
    - {at: p4@first, total: 23, hits: 3, head: "First draw: 3 Kittens in 23 cards", sub: "13% (about 1 in 7)"}
    - {at: p4@last, total: 4, hits: 3, head: "3 Kittens in 4 cards", sub: "mostly Kittens"}
```

### checklist: the recipe
```yaml
- id: recipe
  render: checklist
  lines: [w2]
  params:
    title: The Patient One
    items:
    - {text: Don't play cards for fun, at: w2@don't}
    - {text: Only dodge when you know, at: w2@only, verdict: "+5 pts", color: MUSTARD}   # optional verdict pill
    cards: [0, 1, 3, 6, 7, 8]                                                          # decor, kept in frame
```

### endcard: next video + subscribe + Buh
```yaml
- id: endcard
  render: endcard
  min_duration: 12
  pad: [0, 0]
  params: {next_title: I Tested Every Uno House Rule}
```
Buh is the round teal cyclops, always happy (`makeBuh`). 16:9 leaves the YouTube end-screen slots free (video left,
subscribe right). The only scene that fades out.

## The gates

### Visual: `make qa-visual SLUG=<slug> [VIDEO=...] [VERTICAL=1] [ONLY="a b"]`
Probes the stage state of every scene (every 0.1 s + the last two frames) without drawing, then:

| check | rule | severity |
|---|---|---|
| anchors | every word anchor in scenes.yaml resolves; statement lines without a spoken first word are flagged | error / warn |
| safe | every visible label inside the 5% title-safe area; kit `key` objects too; other props inside the frame | error / warn |
| overlap | no two visible labels overlap (> 12% of the smaller) | error |
| cut | at the last frame nothing is still fading, moving or mid-tween (ambient loops: warn) | error |
| coverage | no more than 5 s of narration without a new visual event (label appears/changes, object appears/starts moving, kit tween) | error |
| numbers | numbers on screen agree with the script line they're anchored to (spoken forms understood: "thirty five", "eleven and a half", "ten billion", "thirteen point oh four"); unsaid numbers warn; player count / fair share are context | error / warn |
| captions | `burn_captions: false` -> nothing burned in | error |
| pixels (with VIDEO) | no black frames, no 1-2 frame brightness flashes or dips | error |
| clipping | oriented-box test on every probed frame: no interpenetration (cards, pieces, pawns, bars), parallel overlapping cards >= 0.003 apart along the normal, no card under the table | error |
| fill (Shorts) | the built main visual (with its labels) fills >= 75% of the content band height (text-only scenes: either dimension) | error |
| flicker (with VIDEO) | pixels toggling A->B->A >= 3x/s in place on <= 0.02% of the frame (z-fighting, shimmer) | error |
| static | episode scene files build no cards themselves (`pipeline/qa_static.py`) | error |
| opening (Shorts) | frame 1 at least 60% as full as the clip's median frame (content band), frame-to-frame motion in the first 0.5 s / 1 s | error |

Output: `out/qa/visual.txt` (readable; problems repeated across 3+ scenes printed once), `visual.json`,
`contact.png` (mid + cut frame of every scene, or every 10 s of the video). Exit 1 on any error.

### Voice: `make voice SLUG=<slug> REC=rec.m4a [FROM=n]`
Runs split -> extend_tails -> find_stumbles -> tighten -> audio_qa -> match_voice (stops at the first failing step;
resume with `FROM=n`), then the final check per line: transcript vs script (Whisper, number words normalised;
missing/extra words listed), abrupt starts/ends, leftover speech outside the script, digital silence >= 10 ms,
clipping (>= -0.3 dBFS or 3+ samples at full scale), pauses > 0.6 s inside a line, gaps > 1.5 s between lines, digital
silence in the assembled narration. Writes `voice/_report_voice.txt` (git-ignored: it has transcripts) and
`voice/_listen.mp3` (the narration exactly as timed in the video) plus the list of every cut. Send both to the
creator.

### Final mix: `make qa-final SLUG=<slug> [VIDEO=...]`
-14 LUFS integrated (+/- 0.5), decoded peak <= -1.0 dBFS, duration >= 8:00 (Shorts: <= 60 s, `--short`), 1920x1080,
48 kHz audio present, upload SRT present, and the no-burned-captions rule present in the assembler. Writes
`out/qa/final.txt` / `final.json`.

## Native Shorts: `episodes/<slug>/shorts_native.yaml`
```yaml
shorts:
- id: kitten-placement
  hook: "Where do you put\nthe Kitten back?"
  title: "..."
  description: "..."
  scenes:                                   # kit templates; lines from script.md; same anchors as the long video
  - {id: kp-bottom, render: deck, lines: [k3], params: {...}}         # open on the spoken hook
  - {id: kp-random, render: deck, lines: ["k2@most"], params: {...}}  # then go back; 'k2@most' starts at that word
  - {id: kp-best, render: deck, lines: [k4, k5], params: {...}}
```
Each scene is one contiguous span of the long video, but scenes can come from anywhere, so the Short opens on
its hook (spoken within ~1 s) and then gives the setup. The audio is those spans cut from `out/final/<slug>.mp4`
and joined (15 ms fades), so it lines up word for word. CI renders ~6 s chunks in
parallel (`shorts.yml`), assembles, runs the visual gate in 9:16 and uploads `<id>.mp4` + `<id>.txt` + QA. CI has
no voice or music, so its files carry a silent track; the local `--assemble --audio ...` run puts the mix in (and
normalises to -14 LUFS through the same `compose.mux` as the long video).

## Status (2026-11-05)
- Kit: 12 templates; `episodes/kit-demo` passes `qa-visual` in 16:9 and 9:16 (0 errors).
- Gates: `make test-gates` (11 tests, each check fires on a known-bad case). EK run: `docs/qa/exploding-kittens.md`.
- Shorts: 4 EK Shorts rendered natively at 1080x1920 on Actions ("Render native Shorts" run #6), all PASS the
  9:16 gate including the opening check (frame-1 fill vs clip median / first-second motion):
  kitten-placement 25.5 s (0.64 / 0.61), same-cards 32.6 s (1.15 / 0.41), going-first 13.0 s (0.72 / 0.33),
  steal 29.5 s (0.78 / 0.65). Each opens on its spoken hook. Runs #4-#5 failed this check before the fixes
  (frame 1 half-empty, then too still), as did the earlier cut Shorts (0.34 / 0.56 fill). They carry a silent
  track until the local `--assemble --audio` run (voice/music are local only).
- Not yet exercised end to end: `make voice` on a real recording (needs the creator's next take; the step
  chain is the existing tools, the new final-check measurements are unit-tested) and `qa-final` on a full
  episode mix (tested on a synthetic mux; EK's final file is local to the creator).
