"""Agent-based model base class + state recorder."""
from __future__ import annotations

import numpy as np


class Model:
    """Base class for fixed-timestep, seeded simulations.

    Subclasses implement `step()` (advance by self.dt) and `snapshot()` (return a
    dict of numpy arrays describing the current state).
    """

    dt: float = 0.05

    def __init__(self, seed: int = 0, dt: float | None = None):
        self.rng = np.random.default_rng(seed)
        if dt is not None:
            self.dt = dt
        self.t = 0.0
        self.steps = 0

    # -- override ---------------------------------------------------------
    def step(self) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def snapshot(self) -> dict:  # pragma: no cover - abstract
        raise NotImplementedError

    # -- helpers ----------------------------------------------------------
    def advance(self) -> None:
        self.step()
        self.steps += 1
        self.t = self.steps * self.dt

    def run(self, t_end: float, sample_every: float | None = None) -> "Recorder":
        """Run until t_end, recording snapshots every `sample_every` seconds."""
        rec = Recorder()
        sample_every = sample_every or self.dt
        every = max(1, int(round(sample_every / self.dt)))
        rec.add(self.t, self.snapshot())
        while self.t < t_end - 1e-9:
            self.advance()
            if self.steps % every == 0:
                rec.add(self.t, self.snapshot())
        return rec


class Recorder:
    """Time series of model snapshots, stacked into arrays on `finalize()`."""

    def __init__(self):
        self._t: list[float] = []
        self._rows: list[dict] = []
        self.t: np.ndarray | None = None
        self.data: dict[str, np.ndarray] = {}

    def add(self, t: float, snap: dict) -> None:
        self._t.append(t)
        self._rows.append({k: np.array(v, copy=True) for k, v in snap.items()})

    def finalize(self) -> "Recorder":
        self.t = np.asarray(self._t)
        keys = self._rows[0].keys() if self._rows else []
        self.data = {k: np.stack([r[k] for r in self._rows]) for k in keys}
        return self

    def __getitem__(self, key: str) -> np.ndarray:
        return self.data[key]

    def index(self, t: float) -> float:
        """Fractional sample index for time t (clamped)."""
        return float(np.clip(np.interp(t, self.t, np.arange(len(self.t))), 0, len(self.t) - 1))

    def at(self, key: str, t: float) -> np.ndarray:
        """Linearly interpolated state at time t."""
        f = self.index(t)
        i = int(np.floor(f))
        j = min(i + 1, len(self.t) - 1)
        w = f - i
        arr = self.data[key]
        return arr[i] * (1 - w) + arr[j] * w
