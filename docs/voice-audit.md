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

## 2. Audit of the free voices we can run here
In progress: all 38 free voices (28 Kokoro, 10 Piper) have read the same passage from our scripts, and the automated
scoring (`tools/voice_audit/`) is running. Results and a ranking will go here.
