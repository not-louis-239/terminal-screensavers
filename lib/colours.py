from lib.custom_types import Colour
from lib.utils import lerp, clamp

def col(code: int, bg: bool = False) -> str:
    return f"\033[{48 if bg else 38};5;{code}m"

def rgb_to_str(colour: Colour, /, *, bg: bool = False) -> str:
    r, g, b = colour
    return f"\033[{48 if bg else 38};2;{r};{g};{b}m"

def lerp_colours(c1: Colour, c2: Colour, t: float) -> Colour:
    return (
        int(lerp(c1[0], c2[0], t)),
        int(lerp(c1[1], c2[1], t)),
        int(lerp(c1[2], c2[2], t))
    )

def add_colours(c1: Colour, c2: Colour, /) -> Colour:
    r1, g1, b1 = c1
    r2, g2, b2 = c2

    rf, gf, bf = (
        clamp(int(r1 + r2), (0, 255)),
        clamp(int(g1 + g2), (0, 255)),
        clamp(int(b1 + b2), (0, 255))
    )

    return (rf, gf, bf)  # type: ignore

def subtract_colours(c1: Colour, c2: Colour, /) -> Colour:
    return (
        int(c1[0] - c2[0]),
        int(c1[1] - c2[1]),
        int(c1[2] - c2[2])
    )

def multiply_colours(c1: Colour, c2: Colour, /) -> Colour:
    r_c1_norm, g_c1_norm, b_c1_norm = c1[0] / 255, c1[1] / 255, c1[2] / 255
    r_c2_norm, g_c2_norm, b_c2_norm = c2[0] / 255, c2[1] / 255, c2[2] / 255
    return (
        int(r_c1_norm * r_c2_norm * 255),
        int(g_c1_norm * g_c2_norm * 255),
        int(b_c1_norm * b_c2_norm * 255)
    )

def scale_brightness(colour: Colour, scalar: float) -> Colour:
    r, g, b = colour[0], colour[1], colour[2]
    return (int(r * scalar), int(g * scalar), int(b * scalar))

# Colourless formatting options
FAINT = "\033[2m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
INVERTED = "\033[7m"
STRIKE = "\033[9m"

COL_RESET = "\033[0m"

def show_palette() -> None:
    for i in range(16):
        for j in range(16):
            idx = i * 16 + j
            print(f"{col(idx)}{idx:03}", end=" ")
        print()

if __name__ == "__main__":
    show_palette()