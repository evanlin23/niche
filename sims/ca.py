"""Cellular automata: generic runner + forest-fire (percolation) and Life rules."""
from __future__ import annotations

import numpy as np

from .base import Model

EMPTY, TREE, FIRE, ASH = 0, 1, 2, 3


def _neighbors4(mask: np.ndarray) -> np.ndarray:
    out = np.zeros_like(mask)
    out[1:] |= mask[:-1]; out[:-1] |= mask[1:]
    out[:, 1:] |= mask[:, :-1]; out[:, :-1] |= mask[:, 1:]
    return out


def forest_fire_step(grid: np.ndarray, rng=None) -> np.ndarray:
    new = grid.copy()
    new[grid == FIRE] = ASH
    new[(grid == TREE) & _neighbors4(grid == FIRE)] = FIRE
    return new


def life_step(grid: np.ndarray, rng=None) -> np.ndarray:
    n = sum(np.roll(np.roll(grid, i, 0), j, 1)
            for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0))
    return ((n == 3) | ((grid == 1) & (n == 2))).astype(grid.dtype)


class CellularAutomaton(Model):
    def __init__(self, grid: np.ndarray, rule=life_step, seed=0, dt=1.0):
        super().__init__(seed=seed, dt=dt)
        self.grid = grid.copy()
        self.rule = rule

    @classmethod
    def forest(cls, shape=(100, 100), density=0.59, seed=0):
        rng = np.random.default_rng(seed)
        g = (rng.random(shape) < density).astype(np.int8) * TREE
        g[:, 0][g[:, 0] == TREE] = FIRE
        return cls(g, forest_fire_step, seed=seed)

    def step(self) -> None:
        self.grid = self.rule(self.grid, self.rng)

    def snapshot(self) -> dict:
        return {"grid": self.grid}
