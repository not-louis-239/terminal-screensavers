import random

def chance(p: float, /) -> bool:
    """Usage:

    if chance(p):  # p is a float between 0 and 1"""

    if not 0 <= p <= 1:
        raise ValueError("chance: p must be between 0 and 1")

    return random.random() < p

def clamp(v: float, clamp_range: tuple[float, float], /) -> float:
    lower, upper = clamp_range
    return max(lower, min(upper, v))
