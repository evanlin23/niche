# Editing the narration yourself (10-minute guide)

You get `out/review/<slug>-narration-vN.mp3`: your voice only, already cleaned, laid out exactly like the video.
You cut what you don't like, export, send it back, and the video is rebuilt around your edit.

## Tool
- **Audacity** (free, Mac M1 native): https://www.audacityteam.org/download/ ← best
- No install? **AudioMass** in the browser: https://audiomass.co (same steps, fewer features)

## The 5 moves you need (Audacity)
1. **Open** the mp3 (File → Open). You see the waveform: speech = fat blobs, silence = flat line.
2. **Find the spot.** Click in the timeline ruler at the time (e.g. 0:20) and press Space to play.
   Zoom: Cmd + 1 (in) / Cmd + 3 (out). Cmd + F fits the whole file.
3. **Select and delete.** Drag across the bad bit (burp, repeated words, "sorry, let me try again"), press Space to
   hear just the selection, then press **Delete**. Cmd + Z undoes anything.
   - Cut from silence to silence (start and end the selection in a flat part), and the join will be invisible.
   - Before deleting, press **Z**: it snaps the selection edges to zero crossings, so no clicks.
4. **Listen to the join.** Click ~2 s before it and press Space. If you hear a click or a word sounds chopped,
   Cmd + Z and select a bit wider (or narrower).
5. **Long pause?** Select most of the silence (leave ~0.3 s) and Delete. For many at once:
   Effect → Special → Truncate Silence (Threshold -40 dB, Duration 0.5 s, Truncate to 0.35 s).

**Don't** use noise reduction, normalize, or EQ: that's already done, and doing it twice makes it sound worse.

## Export and send
File → Export Audio → **WAV** (Signed 16-bit is fine), then send the file in the chat as usual.
Mention roughly what you changed ("cut a burp at 0:20, removed the second 'two matching cat cards'").

## What happens next (my side)
The edited file is re-split into lines by matching it against the script (the same tool as for your raw
recordings), each line is marked `"processed": true` so it isn't cleaned again, the timing is rebuilt
(it gets a little shorter), and the video is re-rendered to match. Captions follow automatically.

## Tips that save editing time while recording
- Mess up? Stop, breathe, and say the **whole sentence** again. Restarts mid-sentence are the hardest cuts.
- Turn your head away for a cough, burp or sip: it keeps the noise off the words.
- Leave a full second of silence after each retake: it gives you a clean place to cut.
