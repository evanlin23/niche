# Synthetic voices: market check and audit (research 2026-11-05)

Goal: a narrator voice that can run unattended and doesn't sound like AI. The tool is in `tools/voice_audit/`; the
audio is not committed (repo rule).

## 1. Market (seen 2026-11-05; prices per 1M characters; a 10-minute script is about 9,000 characters)
**Quality rankings.** Artificial Analysis Speech Arena (artificialanalysis.ai/text-to-speech/leaderboard): Eleven v4
1334, Eleven v4 Turbo 1331, Qwen-Audio-3.1-TTS-Plus 1301, Cartesia Sonic 3.6 1293, Gemini 3.8 Flash TTS 1282,
Fish Audio Drama 3 1272 (best open weights), Kokoro 1061. TTS Arena V2 (Hugging Face): Gradium 2026.10 1586
(preliminary), "Aurora" 1560, CastleFlow 1547, Inworld TTS MAX 1545, Eleven v3 1498; the best open model is Kokoro at
1465, in 30th place.

**Hosted, and what a 10-minute script costs at the listed rate:**
| Service | Price | Per 10-min script | Commercial use |
|---|---|---|---|
| ElevenLabs v4 | $80 (Artificial Analysis) | about $0.72 | paid plans from $6/mo; the free plan is "non-commercial purposes" (terms 2026-10-09) |
| Gemini 3.8 Flash TTS | about $0.0135/min until 2026-12-31 | about $0.14 | check terms |
| Google Chirp 3 HD | $30, 1M characters free each month | free at our volume | yes |
| Azure Neural / HD | $15 / $22 | $0.14 / $0.20 | yes |
| Amazon Polly Neural / Generative | $16 / $30 | $0.14 / $0.27 | yes |
| Inworld TTS-2 | $25, commercial licence included | $0.23 | yes |
| OpenAI tts-1 / tts-1-hd | $15 / $30, shut down 2027-01-06 | | requires telling listeners the voice is AI-generated, so it doesn't fit |
Voice cost is negligible whichever we pick. The choice is about quality and licence.

**Open weights we could run ourselves.**
- Commercial use allowed: Kokoro-82M (Apache-2.0), Kyutai Pocket TTS (CC-BY-4.0; CPU, long text), Chatterbox (MIT;
  watermarked; clones a voice from a short clip), NeuTTS Air (Apache-2.0, watermarked), Phonon (Apache-2.0), and,
  GPU only, Qwen3-TTS, Zonos, CSM-1B, Dia2 and Orpheus (Apache-2.0).
- With conditions: Fish Audio Drama 3 (commercial use only under USD 500k revenue a year); Higgs TTS 3 (credit required).
- No: F5-TTS (CC-BY-NC), XTTS-v2 (Coqui licence), Fish S2 Pro. StyleTTS2 and VibeVoice require telling listeners the
  voice is synthetic.

**Piper voice licences** (from each voice's MODEL_CARD on huggingface.co/rhasspy/piper-voices):
- Usable for a monetised channel: joe (CC0); norman, john and cori (public-domain LibriVox recordings);
  northern_english_male (CC-BY-SA 4.0).
- Not usable: ryan and hfc_male (CC BY-NC-SA), lessac (a Blizzard 2013 research licence).
- Unclear: amy and alan ("see URL").
- **ryan is the pipeline's Piper default, and it is non-commercial.** Kokoro, the main default, is fine.

**YouTube rules.**
- Disclosure (support.google.com/youtube/answer/14328491): required for content that "Makes a real person appear to
  say or do something they didn't do", alters real footage, or "Generates a realistic scene that didn't actually
  occur". The page lists "Cloning one's own voice to create voice overs or dubs" as needing no disclosure. A TTS
  narrator isn't named; that it needs no label is my inference.
- Monetisation (support.google.com/youtube/answer/1311392): not monetisable is "AI-generated content made with generic
  or unoriginal templates giving the impression of mass production without adding the creator's original, authentic
  insights or perspective". A synthetic voice is allowed; sameness isn't.

**Known tells, with sources.**
- Missing breaths: a detector separated human speech from TTS using breathing alone (arxiv.org/abs/2404.15143).
- Cadence and pacing: in a listener study (doi.org/10.1371/journal.pone.0285333), people spotted synthetic speech 73%
  of the time; per a secondary summary, they cited breathing and pacing.
- Chunk joins: synthesizing text in chunks changes the speaker at the joins and causes "severe loudness inconsistency"
  (arxiv.org/abs/2606.18485). That matches Perfect Play's "random accent changes" comments.
- Misread numbers (ElevenLabs prompting guide).
- I found no published source for "sing-song" or pitch-spread thresholds, so those checks are mine.

## 2. Audit of the 38 free voices we can run here (28 Kokoro, 10 Piper)
Same 10-line passage for every voice (numbers, game names, a question, "Buh"), each line synthesized separately as the
pipeline does. Raw results: `docs/voice-audit-2026-11-05.json`. Method and metrics: `tools/voice_audit/README.md`.

| Voice | Licence | Word error | Pitch spread (st) | Same ending tune | Pitch drift between lines (st) | Pauses /100 words | Verdict |
|---|---|---|---|---|---|---|---|
| Kokoro af_heart (female, US) | Apache-2.0 | 2.3% | 3.87 | 0.21 | 0.40 | 11.0 | **best overall** |
| Kokoro bm_lewis (male, UK) | Apache-2.0 | 1.2% | 3.91 | 0.26 | 0.47 | 12.2 | **best male** |
| Kokoro af_bella (female, US) | Apache-2.0 | 4.1% | 4.29 | 0.05 | 0.37 | 11.0 | good |
| Kokoro am_michael (male, US, pipeline default) | Apache-2.0 | 3.5% | 3.38 | 0.47 | 0.45 | 10.5 | good, a little repetitive |
| Kokoro am_echo, af_sky, af_sarah | Apache-2.0 | 2.9-5.2% | 3.7-3.9 | 0.23-0.53 | 0.2-0.5 | 8-11 | fine |
| Kokoro bm_george, af_kore, af_alloy, am_eric, am_fenrir | Apache-2.0 | 4.7-5.8% | 3.2-4.8 | **0.79-0.88** | 0.3-0.6 | 3.5-12.8 | sing-song: nearly every line ends with the same tune |
| Kokoro am_eric, am_liam, af_jessica | Apache-2.0 | 4.7-5.2% | 4.0-4.4 | 0.43-0.81 | 0.3-0.5 | 2.9-5.2 | rushed: about 3.5 words a second, few pauses |
| Kokoro bm_fable | Apache-2.0 | 4.7% | 4.28 | 0.56 | 0.55 | **0.0** | no pauses at all inside lines |
| Kokoro am_onyx, bf_emma, bf_isabella | Apache-2.0 | 4.7-5.2% | **2.2-2.7** | 0.31-0.51 | 0.2-0.3 | 4-6 | flat (monotone) |
| Kokoro af_nicole, am_santa | Apache-2.0 | 1.2-4.7% | 4.8-5.4 | 0.04-0.11 | 0.4-0.7 | 8-17 | character voices (whispery, jolly) |
| Piper cori, john (public domain) | usable | 2.9-3.5% | 3.3-4.0 | 0.33-0.46 | **1.5-2.1** | 9-11 | clear, but the pitch jumps between lines |
| Piper joe (CC0), norman (PD), northern_english_male (CC-BY-SA) | usable | 7-10% | 2.5-3.9 | 0.12-0.47 | 0.5-1.4 | 6-12 | more errors and drift |
| Piper ryan, hfc_male, lessac, amy, alan | not usable or unclear | 4.7-7% | 1.9-4.7 | 0.5-0.66 | 0.4-1.2 | 2-9 | licence rules them out |

What the numbers say:
1. **Kokoro beats Piper on every drift measure.** Between separately synthesized lines, Piper's pitch moves 0.4-2.1
   semitones and its loudness 0.6-1.6 dB; Kokoro's moves 0.2-0.7 st and 0.1-0.6 dB. That's the "accent keeps
   changing" tell, and the per-line pipeline makes it worse.
2. **Five Kokoro voices are sing-song** (ending-tune correlation 0.79-0.88) and three are flat. Avoid them.
3. **"Buh" is unstable.** Whisper heard it as "Bu", "Bah", "Ba", "Bo" and once "Imba" depending on the voice. The
   mascot's name needs a fixed pronunciation (a phoneme override or a respelling, tested by ear). "Gin" coming back as
   "jin" is a homophone, not an error.
4. **Free isn't good enough on its own.** Our best free voice is Kokoro, and independent listeners rank Kokoro far
   below the paid leaders (1061 vs 1334 on Artificial Analysis). The metrics pick the best free voice; they don't make
   it human.
5. Limits: no human baseline yet (the creator's dry recording would be the right one; the published video has music
   under it), and the thresholds are my judgement, not published standards.

## 3. Recommendation
1. **For the probe, test your own voice against Kokoro af_heart or bm_lewis on the same Short** (§7.2 of
   `docs/simulation-niche-research.md`). Stayed-to-watch decides.
2. **Best route to full automation without losing the host: clone your own voice.** YouTube lists "Cloning one's own
   voice to create voice overs or dubs" as needing no disclosure. Options: ElevenLabs (paid plan, the top-ranked
   voice) or Chatterbox (MIT, open, watermarked). Run the same audit on the clone against your real recordings.
3. Whatever voice: synthesize a paragraph at a time rather than line by line, normalise loudness over the whole
   narration, fix the pronunciation of "Buh" and game names, and stop using Piper ryan (non-commercial).

## 4. Creator's verdict (2026-11-05)
After listening to the best free voices (af_heart, bm_lewis, am_michael) and two flagged ones, the creator judged them
not good enough and will record narration manually. The voice probe in §7.2 is dropped. Cloning the creator's own
voice stays an option for later; it would need the same audit against real recordings.
