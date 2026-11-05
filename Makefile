SLUG ?= traffic-jams
JOBS ?= 3
PY ?= python3

.PHONY: setup episode shorts preview preview-shorts thumb pack all test lint-script voice qa-visual qa-final qa stills shorts-native test-gates

setup:            ## install deps + download default voice
	$(PY) -m pip install -r requirements.txt
	$(PY) -m piper.download_voices en_US-ryan-high --data-dir .voices

episode:          ## full 1080p60 long-form render (+ SRT, metadata)
	$(PY) -m pipeline.cli episode $(SLUG) --jobs $(JOBS)

shorts:           ## 1080x1920 shorts re-rendered from the episode sims
	$(PY) -m pipeline.cli shorts $(SLUG) --jobs $(JOBS)

preview:          ## fast 480p30 long-form render for iteration
	$(PY) -m pipeline.cli episode $(SLUG) --preview --jobs $(JOBS)

preview-shorts:
	$(PY) -m pipeline.cli shorts $(SLUG) --preview --jobs $(JOBS)

thumb:
	$(PY) -m pipeline.cli thumb $(SLUG)

pack:             ## Gumroad source pack zip
	$(PY) -m pipeline.cli pack $(SLUG)

all: episode shorts thumb pack

test:
	$(PY) -m tests.test_sims

lint-script:      ## check narration for AI tells + TTS problems (docs/script-style-guide.md)
	$(PY) -m pipeline.lint_script episodes/$(SLUG)/script.md

recording-script: ## printable script for recording your own voice, one file per line
	$(PY) -m pipeline.recording_script episodes/$(SLUG)

split:            ## split ONE long recording into per-line files: make split SLUG=... REC=path/to/file.m4a
	$(PY) -m pipeline.split_recording episodes/$(SLUG) "$(REC)"

# ---------------------------------------------------------------- production kit: gates (docs/scene-kit.md)
TTS ?= recorded
VOICE_ENV = TTS_ENGINE=$(TTS) VOICE_DIR=episodes/$(SLUG)/voice

voice:            ## whole voice chain + final check: make voice SLUG=... REC=rec.m4a   (report + listen file)
	$(PY) -m pipeline.voice_gate episodes/$(SLUG) $(REC) $(if $(FROM),--from-step $(FROM),)

qa-visual:        ## visual gate (stage state per frame): make qa-visual SLUG=... [VIDEO=out.mp4] [VERTICAL=1] [TTS=silent]
	$(VOICE_ENV) $(PY) -m pipeline.qa_visual $(SLUG) $(if $(VIDEO),--video $(VIDEO),) $(if $(VERTICAL),--vertical,) $(if $(ONLY),--only $(ONLY),)

qa-final:         ## final mix gate: -14 LUFS, peak <= -1 dBFS, >= 8:00, no burned captions
	$(PY) -m pipeline.qa_final $(SLUG) $(if $(VIDEO),--video $(VIDEO),)

qa: qa-visual qa-final

stills:           ## stills + contact sheet per scene: make stills SLUG=... [VERTICAL=1]
	$(VOICE_ENV) $(PY) -m pipeline.stills $(SLUG) $(if $(VERTICAL),--vertical,)

shorts-native:    ## native 9:16 Shorts (shorts_native.yaml): make shorts-native SLUG=... [ONLY=id] [AUDIO=long.mp4]
	$(VOICE_ENV) $(PY) -m pipeline.shorts_native $(SLUG) $(if $(ONLY),--only $(ONLY),) $(if $(AUDIO),--audio $(AUDIO),)

test-gates:       ## every QA check fires on a known-bad case
	$(PY) -m tests.test_qa_gates
