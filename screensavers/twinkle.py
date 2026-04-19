import sys
import random

from lib.clock import Clock
from lib.kb_input_manager import KBInputManager, Keys
from lib.vectors import Vector2
from lib.custom_types import Colour
from lib.colours import lerp_colours

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
        if self.kb.is_down(Keys.W):
            self.viewport_pos.y -= VIEWPORT_SCROLL_SPEED * dt_s
        if self.kb.is_down(Keys.S):
            self.viewport_pos.y += VIEWPORT_SCROLL_SPEED * dt_s
        if self.kb.is_down(Keys.A):
            self.viewport_pos.x -= VIEWPORT_SCROLL_SPEED * dt_s
        if self.kb.is_down(Keys.D):
            self.viewport_pos.x += VIEWPORT_SCROLL_SPEED * dt_s
        self.viewport_pos = self.viewport_pos.wrap(env_w=WRAP_SIZE[0], env_h=WRAP_SIZE[1])

def run():
    starfield = Starfield()

    while True:
        dt_s = starfield.clock.tick(FPS)
        starfield.update(dt_s)
        starfield.take_input(dt_s)

def main():
    try:
        print("\033[H\033[J\033[?25l")
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h", end='')
    sys.exit(0)
