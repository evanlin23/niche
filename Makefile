SLUG ?= traffic-jams
JOBS ?= 3
PY ?= python3

.PHONY: setup episode shorts preview preview-shorts thumb pack all test lint-script

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
