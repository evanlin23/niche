"""Stochastic SEIR epidemic on a contact network (agent-based)."""
from __future__ import annotations

import numpy as np

from .base import Model

S, E, I, R = 0, 1, 2, 3


class SEIRNetwork(Model):
    """Discrete-time SEIR on an adjacency list.

    beta: per-contact infection probability per unit time
    sigma: 1/incubation time, gamma: 1/infectious time
    """

    def __init__(self, neighbors: list[np.ndarray], beta=0.3, sigma=1 / 3, gamma=1 / 5,
                 initial_infected=(0,), seed=0, dt=0.1):
        super().__init__(seed=seed, dt=dt)
        self.nb = neighbors
        self.n = len(neighbors)
        self.beta, self.sigma, self.gamma = beta, sigma, gamma
        self.state = np.zeros(self.n, dtype=np.int8)
        self.state[list(initial_infected)] = I

    @staticmethod
    def random_geometric(n, radius, seed=0):
        rng = np.random.default_rng(seed)
        pos = rng.random((n, 2))
        d = np.linalg.norm(pos[:, None] - pos[None], axis=-1)
        nb = [np.flatnonzero((d[i] < radius) & (np.arange(n) != i)) for i in range(n)]
        return pos, nb

    def step(self) -> None:
        st = self.state
        new = st.copy()
        inf = st == I
        for i in np.flatnonzero(st == S):
            k = inf[self.nb[i]].sum()
            if k and self.rng.random() < 1 - (1 - self.beta * self.dt) ** k:
                new[i] = E
        u = self.rng.random(self.n)
        new[(st == E) & (u < self.sigma * self.dt)] = I
        new[(st == I) & (u < self.gamma * self.dt)] = R
        self.state = new

    def counts(self) -> np.ndarray:
        return np.bincount(self.state, minlength=4)

    def snapshot(self) -> dict:
        return {"state": self.state, "counts": self.counts()}
