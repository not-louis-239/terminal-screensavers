import random

import time
import shutil
import math
import json
from math import sin, cos
from dataclasses import dataclass
from pathlib import Path

from lib.buffer import Buffer
from lib.vectors import Vector2
from lib.custom_types import Colour
from lib.utils import lerp_colours
from lib.dirs import DIRS
from lib.kb_input_manager import KBInputManager, Keys

MOVEMENT_SPEED = 80  # units per second
TURN_SPEED = 1.8  # radians/s max
FPS = 60

@dataclass
class SerpentTheme:
    name: str
    body_colours: list[Colour]

def load_themes() -> list[SerpentTheme]:
    themes = []

    with open((DIRS.assets.json.serpent_themes / "serpent_themes.json").path(), "r", encoding="utf-8") as f:
        themes_raw = json.load(f)["themes"]

    for name, theme in themes_raw.items():
        themes.append(SerpentTheme(name, theme["body_colours"]))

    return themes

def get_colour_from_gradient(colors: list[Colour], t: float):
    if len(colors) == 1: return colors[0]

    # Scale t to the number of segments in the gradient
    scaled_t = t * (len(colors) - 1)
    index = int(scaled_t)
    local_t = scaled_t - index

    if index >= len(colors) - 1:
        return colors[-1]

    return lerp_colours(colors[index], colors[index + 1], local_t)

class Serpent:
    def __init__(self, length: int, head_x: float, head_y: float,) -> None:
        self.head = Vector2(head_x, head_y)

        self.heading: float = random.uniform(0, 2 * math.pi)  # radians
        self.turn_velocity: float = 0

        self.length = length
        self.trails: list[Vector2] = []

    def move(self, dt_s: float, vp_w: int, vp_h: int) -> None:
        # Calculate the unit vector for the serpent's current heading
        heading_unit = Vector2(
            cos(self.heading), sin(self.heading)
        )

        # Add the old head position to the trails list
        old_head = self.head.copy()
        self.trails.append(old_head)

        # Move the head
        step = heading_unit * MOVEMENT_SPEED * dt_s
        self.head += step

        # Cull old trails
        self.trails = self.trails[-self.length:]

        # Make the serpent wrap around the screen
        self.head.x %= vp_w
        self.head.y %= vp_h

        # Make the serpent turn randomly
        noise = random.uniform(-1, 1)

        self.turn_velocity += noise * TURN_SPEED * dt_s
        self.turn_velocity *= 0.95  # damping

        self.heading += self.turn_velocity
        self.heading %= 2 * math.pi

def run():
    themes = load_themes()
    theme_idx = 0

    term_w, term_h = shutil.get_terminal_size()
    buffer = Buffer(term_w, term_h)
    serpent = Serpent(320, random.uniform(0, term_w), random.uniform(0, term_h))
    kb = KBInputManager()

    while True:
        kb.update()

        term_w, term_h = shutil.get_terminal_size()
        vis_w, vis_h = term_w, 2 * (term_h - 1)

        serpent.move(1 / FPS, vis_w, vis_h)

        # Change serpent theme by pressing Space
        if kb.went_down(Keys.SPACE):
            theme_idx += 1
            theme_idx %= len(themes)

        # Resize buffer if terminal size changed since last frame
        if (vis_w, vis_h) != buffer.get_size():
            buffer.resize_and_clear(vis_w, vis_h)

        t = time.time() * 5  # speed of shimmer effect

        # Draw the serpent to the buffer
        buffer.clear()

        current_theme = themes[theme_idx]
        body_colours = current_theme.body_colours

        for i, segment in enumerate(serpent.trails):
            frac = i / len(serpent.trails)  # 0 = tail, 1 = head

            shimmer = math.sin(t - i * 0.2) * 40
            base_colour = get_colour_from_gradient(body_colours, 1 - frac)  # XXX: I don't know why I have to do 1 - frac, I'll figure it out later
            final_colour = tuple(max(0, min(255, int(c + shimmer))) for c in base_colour)
            assert len(final_colour) == 3

            buffer.draw_circle((int(segment.x), int(segment.y)), 1 + 1.2 * frac, final_colour)
        buffer.draw_circle((int(serpent.head.x), int(serpent.head.y)), 2.6, body_colours[0])

        # Clear screen and draw the buffer
        print("\033[H", end='', flush=True)  # avoid \033[J as it causes unnecessary flicker
        print(buffer.render())

        hud_text = f"Theme: {current_theme.name}"
        print(f"{hud_text:<24} | Press Ctrl-C to exit.", end='', flush=True)

        time.sleep(1 / FPS)

def main():
    try:
        print("\033[H\033[J\033[?25l", end='', flush=True)
        run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[H\033[J[\033[?25h", end='', flush=True)

if __name__ == "__main__":
    main()