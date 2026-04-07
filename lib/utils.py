import random

from lib.custom_types import Colour

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

def lerp_colours(c1: Colour, c2: Colour, t: float) -> Colour:
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t))
    )

# TODO: Move rgb_to_string to colours module
def rgb_to_str(colour: Colour, /, *, bg: bool = False) -> str:
    r, g, b = colour
    return f"\033[{48 if bg else 38};2;{r};{g};{b}m"
