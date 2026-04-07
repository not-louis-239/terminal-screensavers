import random

from lib.utils import lerp
from lib.custom_types import Colour

def chance(p: float, /) -> bool:
    """Usage:

    if chance(p):  # p is a float between 0 and 1"""

    if not 0 <= p <= 1:
        raise ValueError("chance: p must be between 0 and 1")

    return random.random() < p

def clamp(v: float, clamp_range: tuple[float, float], /) -> float:
    lower, upper = clamp_range
    return max(lower, min(upper, v))

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def lerp_colours(c1: Colour, c2: Colour, t: float) -> Colour:
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t))
    )