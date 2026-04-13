import time
import random
from noise import snoise2 as _snoise2

def chance(p: float, /) -> bool:
    """
    Usage:

    >>> if chance(0.3):
    ...     print("30% chance")
    >>> else:
    ...     print("70% chance")
    """

    if not 0 <= p <= 1:
        raise ValueError("chance: p must be between 0 and 1")

    return random.random() < p

def collapse(n: float) -> int:
    """
    Stochastically round a float to the nearest integers.
    Uses the fractional component as the probability to round up,
    ensuring the average number over time equals the precise float value of n.

    example usage:
    >>> for _ in range(collapse(5)):
    ...     do_something()
    """
    n_down = int(n)
    if chance(n % 1):
        return n_down + 1
    return n_down

def clamp(v: float, clamp_range: tuple[float, float], /) -> float:
    lower, upper = clamp_range
    if lower > upper:
        raise ValueError("clamp_range must be a tuple of (lower, upper) where lower <= upper")
    return max(lower, min(upper, v))

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def snoise2(
        x: float, y: float, *, scale: float = 1.0,
        octaves: int = 1, persistence: float = 0.5,
        repeatx: int | None = None, repeaty: int | None = None,
        lacunarity: float = 2.0, base: int | None = None,
    ) -> float:
    """Return a float from -1 to 1 based on snoise2 function."""

    if scale == 0:
        raise ValueError("Scale cannot be zero.")

    x *= scale
    y *= scale

    kwargs = {
        "octaves": octaves,
        "persistence": persistence,
        "lacunarity": lacunarity,
    }

    if repeatx is not None:
        kwargs["repeatx"] = repeatx
    if repeaty is not None:
        kwargs["repeaty"] = repeaty
    if base is not None:
        kwargs["base"] = base

    return _snoise2(x, y, **kwargs)
