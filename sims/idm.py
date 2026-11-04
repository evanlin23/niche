"""Intelligent Driver Model (Treiber, Hennecke & Helbing, Phys. Rev. E 62, 1805, 2000)
on a single-lane ring road.

Features used by the traffic episode:
  * brake events   (one driver brakes at a fixed deceleration for a time window)
  * smoother cars  (a "wave-dampening" controller in the spirit of Stern et al. 2018:
                    drive at the recent mean traffic speed, never faster than IDM allows)
Positions are stored *unwrapped* (cumulative distance) so they can be interpolated;
take `% length` when drawing.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .base import Model


@dataclass
class IDMParams:
    v0: float = 30.0     # desired speed (m/s)
    T: float = 1.2       # time headway (s)
    a: float = 0.8       # max acceleration (m/s^2)
    b: float = 1.5       # comfortable deceleration (m/s^2)
    s0: float = 2.0      # jam distance (m)
    delta: float = 4.0   # acceleration exponent
    car_length: float = 5.0


@dataclass
class BrakeEvent:
    car: int
    t_start: float
    t_end: float
    decel: float = 4.0


@dataclass
class Smoother:
    car: int
    t_on: float
    window: float = 40.0   # seconds of mean-speed history used as the target
    gain: float = 0.3      # 1/s


class RingRoad(Model):
    def __init__(self, n_cars=40, length=1000.0, params: IDMParams | None = None,
                 brakes: list[BrakeEvent] | None = None,
                 smoothers: list[Smoother] | None = None,
                 seed=0, dt=0.05, jitter=0.0):
        super().__init__(seed=seed, dt=dt)
        self.p = params or IDMParams()
        self.n = n_cars
        self.length = float(length)
        self.brakes = brakes or []
        self.smoothers = smoothers or []
        spacing = self.length / n_cars
        self.x = np.arange(n_cars) * spacing + self.rng.normal(0, jitter, n_cars)
        self.v = np.full(n_cars, self.equilibrium_speed(spacing - self.p.car_length))
        self.leader = np.roll(np.arange(n_cars), -1)    # car i follows car i+1
        self._mean_hist: list[float] = []

    # -- physics ----------------------------------------------------------
    def equilibrium_speed(self, gap: float) -> float:
        p = self.p
        vs = np.linspace(0, p.v0, 20001)[:-1]
        s_eq = (p.s0 + vs * p.T) / np.sqrt(1 - (vs / p.v0) ** p.delta)
        return float(vs[np.argmin(np.abs(s_eq - gap))])

    def gaps(self) -> np.ndarray:
        g = (self.x[self.leader] - self.x) % self.length - self.p.car_length
        return g

    def accel(self) -> np.ndarray:
        p = self.p
        v = self.v
        gap = np.maximum(self.gaps(), 0.1)
        dv = v - v[self.leader]
        s_star = p.s0 + np.maximum(0.0, v * p.T + v * dv / (2 * np.sqrt(p.a * p.b)))
        return p.a * (1 - (v / p.v0) ** p.delta - (s_star / gap) ** 2)

    def step(self) -> None:
        acc = self.accel()
        self._mean_hist.append(float(self.v.mean()))
        for s in self.smoothers:
            if self.t >= s.t_on:
                k = max(1, int(s.window / self.dt))
                target = float(np.mean(self._mean_hist[-k:]))
                acc[s.car] = min(acc[s.car], s.gain * (target - self.v[s.car]))
        for b in self.brakes:
            if b.t_start <= self.t < b.t_end:
                acc[b.car] = -b.decel
        self.v = np.maximum(0.0, self.v + acc * self.dt)
        self.x = self.x + self.v * self.dt

    def snapshot(self) -> dict:
        return {"x": self.x, "v": self.v}


def wave_speed(t: np.ndarray, x: np.ndarray, v: np.ndarray, length: float,
               slow: float = 3.0) -> float:
    """Estimate jam propagation speed (m/s, negative = backwards) by tracking the
    circular mean position of slow cars over time."""
    ts, ys = [], []
    for ti, xi, vi in zip(t, x, v):
        m = vi < slow
        if m.sum() < 2:
            continue
        ang = (xi[m] % length) / length * 2 * np.pi
        ys.append(np.angle(np.mean(np.exp(1j * ang))) % (2 * np.pi) / (2 * np.pi) * length)
        ts.append(ti)
    if len(ts) < 10:
        return float("nan")
    ys = np.unwrap(np.asarray(ys) / length * 2 * np.pi) / (2 * np.pi) * length
    return float(np.polyfit(ts, ys, 1)[0])
