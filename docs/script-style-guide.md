# Script style guide: sounding like a person, not a model

Every script gets checked against this before it goes to TTS (or to you to read).
The research on "AI slop" tells is consistent: generic language that could fit any video,
balanced-but-empty takes, no opinion, visuals that don't match the words, and every video
sounding interchangeable. So the rules below push the other way.

## 1. Have a verdict, and say it early
- State the answer in the first 30 seconds, then spend the video earning it. "Skip college.
  Here's the catch." beats "Is college worth it? Let's find out."
- Take sides. If the data says one option wins, say it wins. No "it depends on your play style".
- When it genuinely does depend, say exactly on what, with numbers: "College wins in a
  2-player game. With 4 players, it loses."

## 2. Be specific: numbers, names, moments
- Every claim has a number from our simulation or a cited source. "Most of the time" -> "61% of the time".
- Say numbers the way people say them: "about a third", "one in five", "two hundred grand".
- Reference real moments in the game players will recognize (the midlife spinout, the
  100K tuition bill, the 2-card career pick). That's what makes it feel like someone who plays.

## 3. Show the process, including what went wrong
- "My first version of the sim had a bug: nobody ever took out a loan. Fixing it changed the answer."
- Mention the assumptions out loud: edition, player count, how the bots decide. Credibility
  comes from admitting the limits, not from sounding confident.
- First person. "I ran", "I expected", "I was wrong about".

## 4. Write for the ear
- Read every line out loud. If you run out of breath, split it.
- Short sentences. Contractions. The occasional fragment. Vary rhythm: long, short. Short.
- One idea per sentence. No stacked clauses.
- For TTS: commas and full stops are the pacing controls. Avoid parentheses, slashes,
  abbreviations ("vs", "e.g.", "approx"), and symbols. Write "fifty K" or "fifty thousand", not "$50K".

## 5. Every line earns its place on screen
- Each line should point at something the viewer sees right then. If nothing on screen
  changes, the line is probably filler.
- Cut any sentence that would fit in a video about a different game.

## 6. Personality comes from the subject
- The humor is in the game and its absurdities ("The game charges you fifty K to have twins.
  Twins pay you a hundred K back. Have twins.").
- One running bit per episode is plenty. No forced jokes.

## 7. Banned (instant AI tells)
Words/phrases: delve, dive in, let's dive, buckle up, in today's video, without further ado,
it's important to note, it's worth noting, in conclusion, ultimately, game-changer, unlock,
landscape, tapestry, navigate, realm, journey, testament, crucial, pivotal, furthermore,
moreover, additionally, whether you're a ... or a ..., the answer might surprise you,
here's the kicker, mind-blowing, ever wondered, at the end of the day, a deep dive,
seamless, robust, elevate, harness, embark.

Patterns:
- "It's not just X, it's Y" (once per script, max).
- Rule-of-three lists for rhythm ("fast, simple, and powerful").
- Em-dash chains, rhetorical questions stacked back to back.
- Ending with a moral or "so next time you...". End with the verdict, or the next question.
- Recaps that repeat what was just said.
- Hedging chains: "may potentially", "could arguably".

## 7b. Sound like a person, not a template (creator feedback on the Uno draft)
Sources: Wikipedia "Signs of AI writing" (WikiProject AI Cleanup) and creator notes. `make lint-script` checks most of these.
- No label fragments as sentences: "Spoiler." "Confession." "One limitation." Say it as a sentence you'd actually
  say: "I'll be honest, the first time I ran this it was wrong."
- "Here's why / here's the thing / so here's my question": max 2 per script. Usually just delete the setup.
- No repeated templates ("X is the sneaky one", "X is the mean one", "X is the strange one"): max 1.
- No slogan pairs ("It makes great stories. It barely changes the game.") more than twice. Real explanations
  have a "because" in them.
- No stock quips ("Bring snacks.", "Hold onto that."). One joke that comes from the actual data beats five quips.
- Parallel lists of the same shape ("If you want X, add Y" four times): break the pattern, cut one, merge two.
- Fewer than 15% of sentences start with And/But/So.
- Significance inflation and copula avoidance are banned: "stands as", "serves as", "underscores", "highlighting",
  "a testament", "broader", "pivotal", "showcasing".
- Put the creator in it: what you expected before running it, what surprised you, what you play at home,
  which result you didn't believe and re-ran. At least one real "I thought... but" moment per section.
- Uneven rhythm: some 3-word sentences, some long ones that run on a bit the way people talk.
- At most one short credibility beat (the engine check). No debugging or re-run stories; personality comes from
  reacting to results.
- The creator re-words anything that doesn't sound like them while recording. Captions follow what they said.

## 8. Structure that works for "I simulated it" game videos
1. Hook (0:00–0:20): the decision + the surprising answer or number. Show it on the board.
2. Credibility (≤30 s): edition, how many games, how the bots play. Keep it brisk.
3. The main question, answered with one clear chart.
4. The twist: when the answer flips (player count, timing, a specific card).
5. 2–3 smaller decisions people argue about, rapid-fire, each with a number.
6. The "perfect strategy" in one sentence + the win rate it gets.
7. End on the next game, or a question for the comments that people will actually fight about.

## Pre-flight checklist
- [ ] Verdict stated in the first 30 s
- [ ] Every number traced to sim output or a source (listed in script.md notes)
- [ ] Read aloud once, timing checked
- [ ] Banned-list search (the pipeline lints for it: `make lint-script`)
- [ ] Each line maps to a scene/visual
- [ ] Assumptions stated once, plainly
