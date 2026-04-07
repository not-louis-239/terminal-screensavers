import random

from math import sin, cos
import time
import shutil
import math

from lib.buffer import Buffer
from lib.vectors import Vector2

MOVEMENT_SPEED = 5  # units per second
TURN_SPEED = 60  # radians/s max
FPS = 60

class Serpent:
    def __init__(
            self, length: int, head_x: int, head_y: int,
            head_colour: tuple[int, int, int], tail_colour: tuple[int, int, int]
        ) -> None:
        self.head = Vector2(head_x, head_y)
        self.heading: float = 0  # radians
        self.length = length
        self.trails: list[Vector2] = []

        self.head_colour = head_colour
        self.tail_colour = tail_colour

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
        self.heading += random.uniform(-TURN_SPEED, TURN_SPEED)
        self.heading %= 2 * math.pi * dt_s

def run():
    head_colour = (255, 255, 128)
    tail_colour = (0, 192, 128)

    buffer = Buffer(*shutil.get_terminal_size())
    serpent = Serpent(200, 10, 10, head_colour, tail_colour)

    while True:
        term_w, term_h = shutil.get_terminal_size()
        vis_w, vis_h = term_w, 2 * (term_h - 1)

        serpent.move(1 / FPS, vis_w, vis_h)

        # Resize buffer if terminal size changed since last frame
        if (vis_w, vis_h) != buffer.get_size():
            buffer.resize_and_clear(vis_w, vis_h)

        # Draw the serpent to the buffer
        buffer.clear()
        for segment in serpent.trails:
            buffer.set_pix(int(segment.x), int(segment.y), tail_colour)
        buffer.set_pix(int(serpent.head.x), int(serpent.head.y), head_colour)

        # Clear screen and draw the buffer
        print("\033[H\033[J", end='', flush=True)
        print(buffer.render())
        print("Press Ctrl-C to exit.", end='', flush=True)

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