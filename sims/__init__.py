"""Reusable, deterministic simulation modules.

Every model is seeded and stepped with a fixed timestep, so the same config
always produces the same frames (required for frame-exact offline rendering).
"""
from .base import Model, Recorder
from .idm import RingRoad, IDMParams
from .seir import SEIRNetwork
from .boids import Boids
from .ca import CellularAutomaton, forest_fire_step, life_step
from .pathfinding import Grid, bfs, astar
