"""
Voracious Cows

The cows eat the grass, then the dirt, then the stone underneath them...
until they dig too deep.
When they touch the lava... well... cooked beef I guess.
"""

from __future__ import annotations

import sys
import random
import shutil
import time



from lib.vectors import Vector2, DIRS_NEIGH8
from lib.buffer import Buffer
from lib.utils import snoise2
from lib.colours import lerp_colours
from lib.custom_types import Colour

STARTING_DENSITY = 80
NUM_COWS = 100

_DENSITY_COLOURS: dict[float, Colour] = {
    STARTING_DENSITY: (45, 180, 20),  # deep grass
    STARTING_DENSITY * 0.9: (12, 45, 5),  # grass
    STARTING_DENSITY * 0.899: (43, 29, 21),  # dark, top-level dirt
    STARTING_DENSITY * 0.799: (168, 149, 116),  # lighter, start of stone
    STARTING_DENSITY * 0.6: (180, 180, 180),  # light stone
    0: (20, 20, 20)  # deep grey
}

def calc_density_lookup_table() -> dict[int, Colour]:
    table: dict[int, Colour] = {}

    # Sort milestones by density (descending) to make range checking easier
    milestones = sorted(_DENSITY_COLOURS.items(), key=lambda x: -x[0])

    # Assuming we want a table from 0 up to STARTING_DENSITY
    for d in range(int(STARTING_DENSITY) + 1):
        # Default to the lowest defined color if density is exactly 0 or below
        color = milestones[-1][1]

        # Look for the two milestones this density 'd' falls between
        for i in range(len(milestones) - 1):
            upper_d, upper_col = milestones[i]
            lower_d, lower_col = milestones[i+1]

            if lower_d <= d <= upper_d:
                # Calculate how far 'd' is between lower and upper
                # Handle division by zero just in case milestones are identical
                if upper_d == lower_d:
                    color = upper_col
                else:
                    t = (d - lower_d) / (upper_d - lower_d)
                    color = lerp_colours(lower_col, upper_col, t)
                break

        table[d] = color

    return table

DENSITY_COLOURS = calc_density_lookup_table()

class Tile:
    def __init__(self, density: int = STARTING_DENSITY):
        self.density = density

    def is_lava(self) -> bool:
        return self.density == 0

    def get_colour(self) -> Colour:
        if self.is_lava():
            return (255, random.randint(0, 100), 0)

        return DENSITY_COLOURS[self.density]

class Cow:
    def __init__(self, x: int, y: int, *, env: Environment) -> None:
        self.pos = Vector2(x, y)
        self.env = env

    def get_tile_under(self) -> Tile:
        assert isinstance(self.pos.y, int) and isinstance(self.pos.x, int)
        return self.env.tiles[self.pos.y][self.pos.x]

    def burnt(self) -> bool:
        """Return whether the cow is cooked beef, lol"""
        tile = self.get_tile_under()
        return tile.is_lava()

    def wander(self, env_w: int, env_h: int) -> None:
        valid_moves = []
        weights = []

        # First, gather all valid (in-bounds) moves
        for direction in DIRS_NEIGH8:
            tx = int(self.pos.x + direction.x)
            ty = int(self.pos.y + direction.y)

            if 0 <= tx < env_w and 0 <= ty < env_h:
                valid_moves.append((direction, self.env.tiles[ty][tx]))

        if not valid_moves:
            return

        # Separate safe moves from lava moves
        safe_options = [(direc, tile) for direc, tile in valid_moves if not tile.is_lava()]

        if safe_options:
            # Organic weighted movement
            # Only pick from tiles that aren't lava
            moves = [opt[0] for opt in safe_options]
            weights = [1 + (opt[1].density / STARTING_DENSITY) * 4 for opt in safe_options]
            chosen_direction = random.choices(moves, weights=weights, k=1)[0]
        else:
            # Trapped
            # Only if every single valid neighbor is lava, pick a random direction
            moves = [opt[0] for opt in valid_moves]
            chosen_direction = random.choice(moves)

        self.pos += chosen_direction

    def eat(self) -> None:
        assert isinstance(self.pos.y, int) and isinstance(self.pos.x, int)
        tile = self.env.tiles[self.pos.y][self.pos.x]
        tile.density = max(0, tile.density - 1)

class Environment:
    def __init__(self, w: int, h: int) -> None:
        size = w, h

        self.NOISE_BASE = random.randint(1, 999)
        self.reset_tiles(*size)
        self.reset_cows(*size)
        self.buf = Buffer(width=w, height=h)

    def reset_cows(self, w: int, h: int) -> None:
        self.cows: list[Cow] = [
            Cow(x=random.randint(0, w - 1), y=random.randint(0, h - 1), env=self)
            for _ in range(NUM_COWS)
        ]

    def reset_tiles(self, w: int, h: int) -> None:
        self.tiles = []
        for y in range(h):
            row = []
            for x in range(w):
                density_offset = snoise2(x, y, scale=0.02, octaves=4, base=self.NOISE_BASE)
                density = int(STARTING_DENSITY * (0.95 + 0.05 * density_offset))
                tile = Tile(density=int(density))
                row.append(tile)
            self.tiles.append(row)

    def reset(self) -> None:
        size = self.get_size()
        self.reset_tiles(*size)
        self.reset_cows(*size)

    def resize(self, new_w: int, new_h: int) -> None:
        cur_size = self.get_size()
        new_size = new_w, new_h

        if (new_w, new_h) == cur_size:
            return

        self.reset_tiles(*new_size)
        self.reset_cows(*new_size)

        self.buf.resize_and_clear(*new_size)
        self.update_buf()

    def get_size(self) -> tuple[int, int]:
        return (len(self.tiles[0]), len(self.tiles))

    def update_buf(self) -> None:
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                self.buf.set_pix(x=x, y=y, colour=tile.get_colour())

        for cow in self.cows:
            assert isinstance(cow.pos.x, int) and isinstance(cow.pos.y, int)
            cow_pos = (cow.pos.x, cow.pos.y)
            self.buf.set_pix(*cow_pos, colour=(255, 255, 230))

    def update(self) -> None:
        env_size = get_vis_size()
        self.resize(*env_size)

        # Remove burnt cows
        self.cows = [cow for cow in self.cows if not cow.burnt()]

        # If all the cows died from the lava, reset
        if not self.cows:
            print("\033[H\033[J")

            empty_rows = env_size[1] // 4 - 1
            print("\n" * empty_rows)
            print("THE COWS HAVE FALLEN".center(env_size[0]))
            time.sleep(3)

            self.reset()

        # Cows eat, then wander
        # If they wandered, then eat, they wouldn't get a chance to move away
        # before the cows standing on lava got deleted.
        for cow in self.cows:
            cow.eat()
            cow.wander(*env_size)

        self.update_buf()

def get_vis_size() -> tuple[int, int]:
    tw, th = shutil.get_terminal_size()
    return tw, 2 * (th - 1)  # -2 because th-1 causes flicker FOR SOME REASON?!

def run():
    print("\033[H\033[J\033[?25l")

    env = Environment(*get_vis_size())

    while True:
        env.update()
        print("\033[H", end='')
        print(env.buf.render())
        print("Press Ctrl-C to exit.", end='', flush=True)
        time.sleep(0.005)

def main():
    try:
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
