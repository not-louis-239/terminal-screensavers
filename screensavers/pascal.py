import math
import sys
import shutil
from dataclasses import dataclass
from typing import Callable

from lib.kb_input_manager import KBInputManager, Keys
from lib.clock import Clock
from lib.colours import col, lerp_colours
from lib.vectors import Vector2

FPS = 60
SCROLL_SPEED_VERT = 40  # pixels/s
SCROLL_SPEED_HORIZ = 60  # pixels/s
CELL_SIZE = 10

# TODO: optimise this so a freaking terminal screensaver doesn't heat up my computer

def nCr(n: int, r: int) -> int:
    return math.comb(n, r)

def get_visible_area() -> tuple[int, int]:
    term_w, term_h = shutil.get_terminal_size()
    return (term_w, term_h - 1)

def format_number(n: int) -> str:
    prefixes: dict[int, str] = {  # max number they can handle, prefix
        1_000: '',
        1_000_000: 'k',
        1_000_000_000: 'm',
        1_000_000_000_000: 'g',
        1_000_000_000_000_000: 't',
        1_000_000_000_000_000_000: 'p',
        1_000_000_000_000_000_000_000: 'e',
        1_000_000_000_000_000_000_000_000: 'z',
        1_000_000_000_000_000_000_000_000_000: 'y'
    }

    for max_threshold, prefix in prefixes.items():
        if n < max_threshold:
            string = f"{1000 * n / max_threshold:.{2 if n >= 1000 else 0}f}{prefix}"
            break
    else:
        exp = math.floor(math.log10(n))
        mantissa = n / (10**exp)
        string = f"{mantissa:.2f}e{exp}"

    return string[:CELL_SIZE - 1].center(CELL_SIZE - 1) + " "

@dataclass
class ColourMode:
    name: str
    func: Callable[[int], str]

def get_colour_modes() -> list[ColourMode]:
    def mod2(n):
        return "\033[96m" if n % 2 == 0 else "\033[93m"
    def mod3(n):
        mod3 = n % 3
        colours = ("\033[92m", "\033[91m", "\033[94m")
        return colours[mod3]
    def mod10(n):
        odd_colours = (col(27), col(33), col(39), col(45), col(51))
        even_colours = (col(202), col(208), col(214), col(220), col(226))
        mod10 = n % 10
        if mod10 % 2 == 0:
            idx = mod10 // 2
            colour = even_colours[idx]
        else:
            idx = (mod10 - 1) // 2
            colour = odd_colours[idx]
        return colour
    def squares(n):
        if n < 0: return "\033[90m"
        root = int(n**0.5)
        return "\033[95m" if root * root == n else "\033[90m"
    def magnitude(n):
        if n <= 0: return "\033[37m"
        # Determine 'power' - using 256-color mode if supported
        order = math.log10(n) if n > 0 else 0

        milestones = {
            0: (0, 0, 140),
            3: (0, 100, 255),
            8: (80, 255, 255),
            13: (255, 255, 80),
            18: (255, 100, 0),
            24: (255, 100, 255),
            30: (255, 255, 255)
        }

        def get_magnitude_colour(n):
            if n <= 0:
                first = milestones[0]
                return f"\033[38;2;{first[0]};{first[1]};{first[2]}m"

            # log10(n) tells us how many digits/magnitude we have
            mag = math.log10(n)

            # Identify the milestones our current magnitude falls between
            keys = sorted(milestones.keys())

            # Handle values beyond our highest milestone
            if mag >= keys[-1]:
                c = milestones[keys[-1]]
                return f"\033[38;2;{c[0]};{c[1]};{c[2]}m"

            # Find the interval
            lower_k = keys[0]
            upper_k = keys[-1]

            for i in range(len(keys) - 1):
                if keys[i] <= mag < keys[i+1]:
                    lower_k = keys[i]
                    upper_k = keys[i+1]
                    break

            # Calculate t (0.0 to 1.0) within this specific milestone gap
            # Example: If mag is 5, and we are between 3 and 8, t = (5-3)/(8-3) = 0.4
            gap = upper_k - lower_k
            t = (mag - lower_k) / gap

            c1 = milestones[lower_k]
            c2 = milestones[upper_k]

            # Assuming col() converts RGB to your terminal format
            # and lerp_colours handles the math
            rgb = lerp_colours(c1, c2, t)
            return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

        return get_magnitude_colour(n)

    return [
        ColourMode(name="Modulo 2", func=mod2),
        ColourMode(name="Modulo 3", func=mod3),
        ColourMode(name="Modulo 10", func=mod10),
        ColourMode(name="Squares", func=squares),
        ColourMode(name="Magnitude", func=magnitude)
    ]

class ViewWindow:
    def __init__(self) -> None:
        self.clock = Clock()
        self.kb = KBInputManager()
        self.pos = Vector2(0, 0)
        self.colour_mode_idx: int = 0
        self.colour_modes: list[ColourMode] = get_colour_modes()

    def update(self) -> None:
        self.kb.update()

    def take_input(self, dt_s: float) -> None:
        if self.kb.is_down(Keys.W):
            self.pos.y -= SCROLL_SPEED_VERT * dt_s
        if self.kb.is_down(Keys.S):
            self.pos.y += SCROLL_SPEED_VERT * dt_s
        if self.kb.is_down(Keys.A):
            self.pos.x -= SCROLL_SPEED_HORIZ * dt_s
        if self.kb.is_down(Keys.D):
            self.pos.x += SCROLL_SPEED_HORIZ * dt_s
        if self.kb.went_down(Keys.SPACE):
            self.colour_mode_idx = (self.colour_mode_idx + 1) % len(self.colour_modes)

    def draw(self) -> None:
        vis_w, vis_h = get_visible_area()
        y_offset = vis_h // 2
        min_y = int(self.pos.y) - y_offset

        buf: list[list[str]] = [[' '] * vis_w for _ in range(vis_h)]

        screen_centre_x = vis_w // 2

        for screen_y in range(vis_h):
            y = min_y + screen_y
            if y < 0:
                continue

            # Determine which 'r' values are potentially on screen.
            # We want to check enough 'r' values to cover the screen width.
            # Since the triangle is centred, r = y/2 is our screen centre.
            centre_r = y / 2

            # How many 'r' units fit in half the screen?
            r_range_half = (vis_w / CELL_SIZE) / 2 + 1

            # Calculate the bounds of r based on the camera position
            # We shift the centre of our search based on the camera x
            camera_r_offset = (self.pos.x / CELL_SIZE)

            start_r = int(centre_r + camera_r_offset - r_range_half)
            end_r = int(centre_r + camera_r_offset + r_range_half)

            # Iterate through the calculated r-range
            for r in range(start_r, end_r):
                if 0 <= r <= y:
                    num = nCr(y, r)
                    string = format_number(num)
                    colour = self.colour_modes[self.colour_mode_idx].func(num)

                    # Standard centring logic
                    centre_adjustment = (r - y / 2) * CELL_SIZE
                    start_x = int(screen_centre_x - self.pos.x + centre_adjustment)

                    for i, char in enumerate(string):
                        plot_x = start_x + i
                        if 0 <= plot_x < vis_w:
                            if i == len(string) - 1:
                                buf[screen_y][plot_x] = char + "\033[0m"
                            else:
                                buf[screen_y][plot_x] = colour + char

        print("\033[H", end='')
        print("\n".join(''.join(row) for row in buf))

        hud_str = f"\033[0mHighlight: {self.colour_modes[self.colour_mode_idx].name}"
        print(f"{hud_str:<24} | Press Ctrl-C to exit.", flush=True)

def run():
    wn = ViewWindow()

    while True:
        dt_s = wn.clock.tick(fps=FPS)
        wn.update()
        wn.take_input(dt_s)
        wn.draw()

def main():
    try:
        print("\033[H\033[J\033[?25l")
        run()
    except KeyboardInterrupt:
        pass

    print("\033[0m\033[H\033[J\033[?25h")
    sys.exit(0)

if __name__ == '__main__':
    main()