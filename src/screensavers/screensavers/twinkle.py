import sys
import shutil
import random

from screensavers.utils.clock import Clock
from screensavers.utils.kb_input_manager import KBInputManager, Keys
from screensavers.utils.vectors import Vector2
from screensavers.utils.custom_types import Colour
from screensavers.utils.colours import lerp_colours, rgb_to_str, COL_RESET

FPS = 60
STAR_SPAWN_CHANCE = 0.025  # stars per cell
VIEWPORT_SCROLL_SPEED = 60  # pix/s
WRAP_SIZE = (2_000, 1_500)

MIN_TWINKLE_FREQ = 0.1
MAX_TWINKLE_FREQ = 3

STAR_CHARS = "+*·•✦"

def make_star_colours() -> list[Colour]:
    BASE_COLOURS = [
        (255, 225, 165),
        (165, 225, 255),
        (255, 161, 176)
    ]

    colours = [
        (255, 255, 255)
    ]

    for bc in BASE_COLOURS:
        for intensity in (0.2, 0.4, 0.6, 0.8, 1):
            colour = lerp_colours((255, 255, 255), bc, intensity)
            colours.append(colour)

    return colours

def get_visible_area() -> tuple[int, int]:
    term_w, term_h = shutil.get_terminal_size()
    return term_w, term_h - 1

class Star:
    def __init__(
            self,
            pos: Vector2,
            colour: Colour,
            char: str,
            twinkle_freq: float  # cycles/s
        ) -> None:
        self.phase = 0
        self.pos = pos
        self.colour = colour
        self.char = char
        self.twinkle_freq = twinkle_freq
        self._cached_colour_str = rgb_to_str(colour)

    def is_visible(self, env_x: float, env_y: float, env_w: float, env_h: float) -> bool:
        x, y = self.pos
        return (
            env_x < x < env_x + env_w
            and env_y < y < env_y + env_h
        )

    def render(self) -> str:
        return f"{self._cached_colour_str}{self.char}"

    def update(self, dt_s: float) -> None:
        self.phase += dt_s * self.twinkle_freq
        self.phase = self.phase % 1

class Starfield:
    def __init__(self) -> None:
        self.clock = Clock()
        self.kb = KBInputManager()
        self.stars: list[Star] = []

        self.star_colours: list[Colour] = make_star_colours()
        self.spawn_stars()

        self.viewport_pos: Vector2 = Vector2(0, 0)

    def spawn_stars(self) -> None:
        total_cells = WRAP_SIZE[0] * WRAP_SIZE[1]
        num_stars = int(total_cells * STAR_SPAWN_CHANCE)

        for _ in range(num_stars):
            pos = Vector2(
                random.randint(0, WRAP_SIZE[0] - 1),
                random.randint(0, WRAP_SIZE[1] - 1)
            )
            colour = random.choice(self.star_colours)
            char = random.choice(STAR_CHARS)
            twinkle_freq = random.uniform(MIN_TWINKLE_FREQ, MAX_TWINKLE_FREQ)
            self.stars.append(Star(pos=pos, colour=colour, char=char, twinkle_freq=twinkle_freq))

    def update(self, dt_s) -> None:
        self.kb.update()
        for star in self.stars:
            star.update(dt_s=dt_s)

    def take_input(self, dt_s) -> None:
        # 2x multiplier on horizontal speed makes up for the fact that
        # terminal characters are taller than they are wide.

        if self.kb.is_down(Keys.W):
            self.viewport_pos.y -= VIEWPORT_SCROLL_SPEED * dt_s
        if self.kb.is_down(Keys.S):
            self.viewport_pos.y += VIEWPORT_SCROLL_SPEED * dt_s
        if self.kb.is_down(Keys.A):
            self.viewport_pos.x -= VIEWPORT_SCROLL_SPEED * dt_s * 2
        if self.kb.is_down(Keys.D):
            self.viewport_pos.x += VIEWPORT_SCROLL_SPEED * dt_s * 2
        self.viewport_pos = self.viewport_pos.wrap(env_w=WRAP_SIZE[0], env_h=WRAP_SIZE[1])

    def render(self) -> str:
        vis_w, vis_h = get_visible_area()

        buf = [[" "] * vis_w for _ in range(vis_h)]

        for star in self.stars:
            # If the star is not within the visible area, skip it
            if not star.is_visible(env_x=self.viewport_pos.x, env_y=self.viewport_pos.y, env_w=vis_w, env_h=vis_h):
                continue

            # Calculate the position of the star in relation to the viewport
            view_x, view_y = int(star.pos.x - self.viewport_pos.x), int(star.pos.y - self.viewport_pos.y)

            # Draw it to the buffer
            buf[view_y][view_x] = star.render()

        return "\n".join("".join(row) for row in buf) + COL_RESET

def run():
    starfield = Starfield()

    while True:
        dt_s = starfield.clock.tick(FPS)
        starfield.update(dt_s)
        starfield.take_input(dt_s)

        print(starfield.render())
        print(f"Position: ({starfield.viewport_pos.x:,.2f}, {starfield.viewport_pos.y:,.2f}) | Press Ctrl-C to exit.", end='', flush=True)

def main():
    try:
        print("\033[H\033[J\033[?25l")
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h", end='')
    sys.exit(0)

if __name__ == "__main__":
    main()