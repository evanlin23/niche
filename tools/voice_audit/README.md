# Voice audit (research tool, not part of the render pipeline)

Checks a synthetic voice for the usual AI tells, on the same 10-line passage taken from our scripts
(numbers, game names, a question, "Buh").

    python -m venv venv && . venv/bin/activate
    pip install kokoro-onnx piper-tts faster-whisper praat-parselmouth soundfile num2words
    # models: kokoro-v1.0.onnx + voices-v1.0.bin (github.com/thewh1teagle/kokoro-onnx releases) in <work>/models/,
    # Piper voices via `python -m piper.download_voices <voice> --data-dir <work>/models/piper`
    python synth.py <work> kokoro am_michael        # writes <work>/out/kokoro_am_michael/{<line>.wav,_full.wav,_meta.json}
    python audit.py <work> <work>/out/kokoro_*      # prints one JSON line per voice, writes <work>/out/_audit.json

`synth.py` and `audit.py` expect `passage.txt` in `<work>/tools/`. Lines are synthesized one by one, as the pipeline does,
so drift between lines shows up.

Metrics (per voice):
- `wer`: Whisper small.en word error rate against the script (numbers normalised). Catches mispronunciations.
- `low_conf`: words Whisper heard with probability under 0.5 (mumbled or odd stress).
- `f0_sd_st`: pitch spread in semitones. Low means monotone.
- `end_melody_corr`: how alike the last 0.8 s pitch contours of the lines are (mean pairwise correlation). High means
  every sentence ends with the same tune (sing-song).
- `line_pitch_drift_st`, `timbre_drift` (max MFCC cosine distance x1000 from the passage mean), `loud_sd_db`: drift
  between separately synthesized lines, the "accent keeps changing" tell.
- `wps`, `rate_cv`, `pauses_per_100w`: pace, how much it varies between lines, pauses inside lines.

These are proxies. The final call is a blind listen and the Shorts test. Never commit the audio (repo rule).
