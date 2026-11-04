"""Boids (Reynolds 1987): separation, alignment, cohesion in a periodic 2D box."""
from __future__ import annotations

import numpy as np

from .base import Model


class Boids(Model):
    def __init__(self, n=200, size=(160.0, 90.0), speed=12.0, radius=8.0,
                 w_sep=1.5, w_ali=1.0, w_coh=0.8, seed=0, dt=1 / 60):
        super().__init__(seed=seed, dt=dt)
        self.size = np.asarray(size)
        self.pos = self.rng.random((n, 2)) * self.size
        ang = self.rng.random(n) * 2 * np.pi
        self.vel = np.c_[np.cos(ang), np.sin(ang)] * speed
        self.speed, self.radius = speed, radius
        self.w = np.array([w_sep, w_ali, w_coh])   # toggle rules by zeroing weights

    def step(self) -> None:
        d = self.pos[None] - self.pos[:, None]             # i -> j
        d -= np.round(d / self.size) * self.size           # periodic
        dist = np.linalg.norm(d, axis=-1) + np.eye(len(self.pos)) * 1e9
        near = dist < self.radius
        cnt = np.maximum(near.sum(1, keepdims=True), 1)
        sep = -(d * (near / dist ** 2)[..., None]).sum(1)
        ali = (near @ self.vel) / cnt - self.vel
        coh = (d * near[..., None]).sum(1) / cnt
        steer = self.w[0] * sep * 10 + self.w[1] * ali + self.w[2] * coh * 0.2
        self.vel += steer * self.dt * 4
        sp = np.linalg.norm(self.vel, axis=1, keepdims=True) + 1e-9
        self.vel = self.vel / sp * self.speed
        self.pos = (self.pos + self.vel * self.dt) % self.size

    def snapshot(self) -> dict:
        return {"pos": self.pos, "vel": self.vel}
