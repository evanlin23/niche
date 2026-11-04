"""Grid / graph pathfinding with exploration order recorded (for animation)."""
from __future__ import annotations

import heapq
from collections import deque

import numpy as np


class Grid:
    def __init__(self, walls: np.ndarray):
        self.walls = walls.astype(bool)
        self.h, self.w = walls.shape

    @classmethod
    def random(cls, h, w, density=0.25, seed=0):
        rng = np.random.default_rng(seed)
        walls = rng.random((h, w)) < density
        walls[0, 0] = walls[-1, -1] = False
        return cls(walls)

    def neighbors(self, c):
        r, q = c
        for dr, dq in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nq = r + dr, q + dq
            if 0 <= nr < self.h and 0 <= nq < self.w and not self.walls[nr, nq]:
                yield (nr, nq)


def _path(prev, goal):
    if goal not in prev:
        return []
    out = [goal]
    while prev[out[-1]] is not None:
        out.append(prev[out[-1]])
    return out[::-1]


def bfs(grid: Grid, start, goal):
    """Returns (path, visit_order)."""
    prev = {start: None}
    order = []
    dq = deque([start])
    while dq:
        c = dq.popleft()
        order.append(c)
        if c == goal:
            break
        for n in grid.neighbors(c):
            if n not in prev:
                prev[n] = c
                dq.append(n)
    return _path(prev, goal), order


def astar(grid: Grid, start, goal):
    """Manhattan-heuristic A*. Returns (path, visit_order)."""
    h = lambda c: abs(c[0] - goal[0]) + abs(c[1] - goal[1])
    prev = {start: None}
    g = {start: 0}
    pq = [(h(start), 0, start)]
    order, seen = [], set()
    while pq:
        _, gc, c = heapq.heappop(pq)
        if c in seen:
            continue
        seen.add(c)
        order.append(c)
        if c == goal:
            break
        for n in grid.neighbors(c):
            ng = gc + 1
            if ng < g.get(n, 1e18):
                g[n] = ng
                prev[n] = c
                heapq.heappush(pq, (ng + h(n), ng, n))
    return _path(prev, goal), order
