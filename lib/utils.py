import random

def chance(p: float, /) -> bool:
    """Usage:

    if chance(p):  # p is a float between 0 and 1"""

    if not 0 <= p <= 1:
        raise ValueError("chance: p must be between 0 and 1")

    return random.random() < p

def clamp(v: float, clamp_range: tuple[float, float], /) -> float:
    lower, upper = clamp_range
    if lower > upper:
        raise ValueError("clamp_range must be a tuple of (lower, upper) where lower <= upper")
    return max(lower, min(upper, v))

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t
