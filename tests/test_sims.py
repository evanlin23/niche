"""Sanity checks for the simulation library. Run: python -m tests.test_sims"""
import numpy as np

from sims import (Boids, CellularAutomaton, Grid, RingRoad, SEIRNetwork, astar, bfs)
from sims.idm import BrakeEvent, Smoother, wave_speed


def test_idm_uniform_flow_is_stationary():
    r = RingRoad(40, 1000).run(60, 1.0).finalize()
    assert np.ptp(r["v"][-1]) < 1e-6


def test_idm_brake_tap_creates_persistent_jam():
    r = RingRoad(40, 1000, brakes=[BrakeEvent(0, 20, 23)]).run(400, 0.5).finalize()
    assert r["v"][-1].min() < 1.0                      # someone is stopped long after
    assert wave_speed(r.t[200:], r["x"][200:], r["v"][200:], 1000) < 0   # wave moves backwards


def test_idm_low_density_is_stable():
    r = RingRoad(30, 1000, brakes=[BrakeEvent(0, 20, 23)]).run(400, 0.5).finalize()
    assert r["v"][-1].std() < 0.5


def test_smoother_dissolves_jam():
    r = RingRoad(40, 1000, brakes=[BrakeEvent(0, 20, 23)],
                 smoothers=[Smoother(20, 250)]).run(650, 0.5).finalize()
    assert r["v"][-1].min() > 5 and r["v"][-1].std() < 0.5


def test_determinism():
    a = RingRoad(40, 1000, brakes=[BrakeEvent(0, 5, 8)], jitter=0.5, seed=3).run(50).finalize()
    b = RingRoad(40, 1000, brakes=[BrakeEvent(0, 5, 8)], jitter=0.5, seed=3).run(50).finalize()
    assert np.array_equal(a["x"], b["x"])


def test_other_modules_run():
    pos, nb = SEIRNetwork.random_geometric(200, 0.12, seed=1)
    m = SEIRNetwork(nb, initial_infected=[0, 1, 2], seed=1)
    m.run(60, 1.0)
    assert m.counts().sum() == 200
    Boids(50).run(1.0)
    ca = CellularAutomaton.forest((50, 50), 0.7, seed=0)
    ca.run(60)
    g = Grid.random(30, 30, 0.2, seed=2)
    p1, _ = bfs(g, (0, 0), (29, 29)); p2, _ = astar(g, (0, 0), (29, 29))
    assert len(p1) == len(p2)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
