# Camera and motion research (for premium-looking 3D explainers)

Summary of a web research pass. Numbers are starting values to tune, not laws.
No published breakdown of PerfectPlaySim's camera work was found.

## Speeds
- Judder rule of thumb: an object should take >= ~7 s to cross the frame (4 s minimum in Samuelson's manual;
  10-12 s safer at 24 fps). Example: 45 deg pan in >= 8 s with a 35 mm lens.
  dvxuser.com/threads/24-fps-pan-speed-strobing.375267, premiumbeat.com/blog/cinematography-tip-capture-smooth-panning-shots-at-24fps
- In pixels: <= ~275 px/s at 1080p, about 6-9 px per frame at 30 fps.
- Manim's ambient camera rotation default is ~1.15 deg/s (docs.manim.community ThreeDScene).
- Orbit 2-4 deg/s around the table centre (up to 6 on tight, plain shots). Hero orbit 20-40 deg over 8-12 s.
  Push-in 10-20% of distance over 4-6 s. Crane: 5-15 deg elevation change over 6-8 s.
- Ease in-out (sine/cubic), ~25-30% of the move accelerating and decelerating. Don't stack orbit + push + tilt
  at full strength.

## Labels
- Screen-facing overlay labels projected from a stable anchor (bar top centre), same camera matrix as the frame,
  no smoothing (it makes labels trail), sub-pixel positions (rounding causes stair-stepping on slow moves).
- Animate label size with transforms, not font-size. Keep inside ~5% safe margins; fade out over 0.3 s if the
  anchor leaves the safe area.

## Cuts
- Hard cuts on narration beats. Chapter changes may use a quick 0.25-0.5 s dip.
- Consecutive shots should differ by >= 30 deg of angle or >= 1.5x size, otherwise it reads as a jump cut.

## Cheap offline quality
- 30 fps. Motion blur unnecessary at <= 6 px/frame.
- Supersampling 2-4x for thin edges and text. Subtle vignette (10-20%), very light grain (0.5-1%) to dither
  banding on the gradient floor (test after YouTube compression), low bloom, ACES/AgX tone mapping.

## Pacing (creator-blog numbers, not controlled studies)
- Something meaningful changes every 4-8 s; new shot every 15-30 s (10-20 s in the first minute);
  bigger pattern break every 60-90 s.
