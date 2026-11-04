Drop background tracks here (mp3/wav/m4a), e.g. from YouTube Studio -> Audio Library
(Genre: Ambient, Mood: Calm/Inspirational, no drums). Then set `music: music/` in an
episode's scenes.yaml. Tracks play in filename order, loop, crossfade, and duck under the voice.
Check each track's licence line in the Audio Library (some ask for a credit in the description).

Note: tracks here are NOT committed (public repo; Audio Library licence covers use in your
videos, not redistribution). GitHub Actions renders therefore fall back to generated music;
the final mix with these tracks is assembled locally (`python -m pipeline.cli episode <slug> --only none --assemble`).
