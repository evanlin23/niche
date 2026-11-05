"""Python twins of the kit's easing curves (pipeline/web/stage.js), for tests and analysis."""


def smooth(t: float) -> float:
    """stage.js `ease`: smoothstep, zero speed at both ends"""
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)
