# Phantom Traffic Jam — simulation source pack

The exact simulation behind the "I Simulated It" episode *Why Traffic Jams Appear From Nowhere*.

**What's inside**
- `sims/idm.py` — Intelligent Driver Model (Treiber et al., 2000) on a ring road, with brake events
  and a wave-smoothing "blue car" controller (inspired by Stern et al., 2018).
- `sims/base.py` — tiny seeded, fixed-timestep simulation framework + recorder.
- `sims/*.py` — bonus modules: SEIR epidemic network, boids, cellular automata, grid pathfinding.
- `run_traffic.py` — runs all three experiments from the video and saves space-time diagrams as PNGs.

**Requirements:** Python 3.10+, `pip install numpy pillow`

```bash
python run_traffic.py                       # jam / more-room / smoother -> 3 PNGs + printed stats
python run_traffic.py --cars 35 --decel 3   # try your own
```

Things to try: change `T` (time headway) or `a` (acceleration) in `IDMParams`, add several smoother
cars, or brake twice. Can you find the density where jams stop forming?
