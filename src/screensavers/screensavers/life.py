from __future__ import annotations

import random
import time
import sys
import shutil

from screensavers.utils.utils import chance
from screensavers.utils.buffer import Buffer
from screensavers.utils.custom_types import Colour

STARTING_ALIVE_CHANCE = 0.35
SPONTANEOUS_BIRTH_CHANCE = 0.0005  # per cell, per frame

AGE_COLOURS: dict[int, Colour] = {
    0: (0, 0, 100),      # Deep Navy (Just born/Background)
    1: (0, 0, 200),      # Strong Blue
    2: (75, 0, 200),     # Indigo
    3: (120, 0, 200),    # Deep Purple
    4: (170, 0, 255),    # Bright Purple
    5: (220, 0, 255),    # Magenta
    6: (255, 0, 200),    # Hot Pink
    7: (255, 0, 120),    # Deep Rose
    8: (255, 0, 50),     # Crimson
    9: (255, 0, 0),      # Pure Red
    10: (255, 50, 0),    # Red-Orange
    11: (255, 80, 0),    # Orange
    12: (255, 110, 0),   # Bright Orange
    13: (255, 140, 0),   # Amber
    14: (255, 170, 0),   # Gold
    15: (255, 200, 0),   # Yellow-Orange
    16: (255, 220, 0),   # Lemon Yellow
    17: (255, 255, 0),   # Pure Yellow
    18: (255, 255, 100), # Pale Yellow
    19: (255, 255, 150), # Cream
    20: (255, 255, 200), # Near White
    21: (255, 255, 255)  # Pure White (The "Ancient" cells)
}

MAX_AGE = max(AGE_COLOURS.keys())

class Cell:
    def __init__(self, age: int = 0, alive: bool = False) -> None:
        self.age: int = age
        self.alive: bool = alive

    def copy(self) -> Cell:
        return Cell(age=self.age, alive=self.alive)

    def get_render_colour(self) -> Colour:
        if not self.alive:
            return AGE_COLOURS[0]
        return AGE_COLOURS.get(self.age, AGE_COLOURS[MAX_AGE])

class ConwayLife:
    def __init__(self, grid_w: int, grid_h: int) -> None:
        self.grid = [[Cell(alive=chance(STARTING_ALIVE_CHANCE)) for _ in range(grid_w)] for _ in range(grid_h)]
        self.buf = Buffer(width=grid_w, height=grid_h)

    def get_grid_size(self) -> tuple[int, int]:
        return (len(self.grid[0]), len(self.grid))

    def copy_grid(self) -> list[list[Cell]]:
        return [[c.copy() for c in row] for row in self.grid]

    def resize(self, new_w: int, new_h: int) -> None:
        grid_w, grid_h = self.get_grid_size()
        if (new_w, new_h) == (grid_w, grid_h):
            return

        self.buf.resize_and_clear(width=new_w, height=new_h)

        new_grid: list[list[Cell]] = []

        for y in range(new_h):
            cells = []
            for x in range(new_w):
                if x < grid_w and y < grid_h:
                    # Transfer over existing cells
                    cells.append(self.grid[y][x])
                else:
                    # Add empty cells as placeholders if out of bounds (can happen when resizing up)
                    cells.append(Cell(alive=chance(STARTING_ALIVE_CHANCE)))
            new_grid.append(cells)

        self.grid = new_grid

        self.update_buf()

    def update_buf(self) -> None:
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if cell.alive:
                    self.buf.set_pix(x=x, y=y, colour=cell.get_render_colour())
                else:
                    self.buf.set_pix(x=x, y=y, colour=(0, 0, 0))

    def update(self) -> None:
        new_grid = self.copy_grid()
        grid_w, grid_h = self.get_grid_size()

        for y in range(grid_h):
            for x in range(grid_w):
                neighbour_diffs = [
                    (-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)
                ]

                num_live_neighbours = 0
                for dx, dy in neighbour_diffs:
                    if 0 <= x + dx < grid_w and 0 <= y + dy < grid_h:
                        if self.grid[y + dy][x + dx].alive:
                            num_live_neighbours += 1

                is_alive = self.grid[y][x].alive
                new_cell = new_grid[y][x]

                if is_alive:
                    if (num_live_neighbours < 2 or num_live_neighbours > 3):
                        new_cell.alive = False
                        new_cell.age = 0
                    else:
                        new_cell.age += 1
                elif not is_alive and (num_live_neighbours == 3 or chance(SPONTANEOUS_BIRTH_CHANCE)):
                    new_cell.alive = True
                    new_cell.age = 0

        self.grid = new_grid
        self.update_buf()

    def render(self) -> str:
        return self.buf.render()

def calc_visible_area() -> tuple[int, int]:
    term_w, term_h = shutil.get_terminal_size()
    vis_w, vis_h = term_w, 2 * (term_h - 1)
    return (vis_w, vis_h)

def run() -> None:
    print("\033[H\033[J\033[?25l")

    sim = ConwayLife(*calc_visible_area())

    while True:
        print("\033[H")
        sim.resize(*calc_visible_area())
        sim.update()
        print(sim.render())
        print("Press Ctrl-C to exit.", flush=True, end='')
        time.sleep(0.05)

def main() -> None:
    try:
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h", flush=True)  # Clear screen and show cursor
    sys.exit(0)

if __name__ == "__main__":
    main()
