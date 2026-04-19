from src.screensavers.utils.vectors import IntVector2
from src.screensavers.utils.colours import col, COL_RESET
import shutil
import time

STEP_DELAY = 0.1

COL_INT_MARKER = 8
COL_INT_ON = 7
COL_INT_OFF = 0
COL_INT_ANT = 2

DIRS: dict[int, IntVector2] = {
    0: IntVector2(0, 1),  # North
    1: IntVector2(1, 0),  # East
    2: IntVector2(0, -1),  # South
    3: IntVector2(-1, 0)  # West
}

class EndlessGrid:
    def __init__(self):
        self.active_lights: set[IntVector2] = set()

    def is_active(self, p: IntVector2, /) -> bool:
        return p in self.active_lights

class LangtonsAnt:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.pos = IntVector2(x, y)
        self.facing = 0

    def step(self, grid: EndlessGrid) -> None:
        # Implementation of the Langton's Ant algorithm here
        assert isinstance(self.pos, IntVector2), "pos must be an IntVector2"
        assert isinstance(grid, EndlessGrid), "grid must be an EndlessGrid"

        if grid.is_active(self.pos):
            self.facing -= 1  # turn left
            grid.active_lights.remove(self.pos)
        else:
            new = self.pos.copy()
            assert isinstance(new, IntVector2), "new must be an IntVector2"

            self.facing += 1  # turn right
            grid.active_lights.add(new)

        self.facing %= 4
        self.pos += DIRS[self.facing]

def run():
    print("\033[?25l", end='', flush=True)

    ant = LangtonsAnt(10, 10)
    grid = EndlessGrid()

    while True:
        ant.step(grid)

        print("\033[H", end='')

        term_w, term_h = shutil.get_terminal_size()

        visible_h = 2 * (term_h - 1)
        viewport_w, viewport_h = term_w, visible_h

        start_x, start_y = int(ant.pos.x - viewport_w // 2), int(ant.pos.y - viewport_h // 2)

        buf = ""

        for y in range(start_y, start_y + viewport_h, 2):
            for x in range(start_x, start_x + viewport_w):
                top_active = grid.is_active(IntVector2(x, y))
                bottom_active = grid.is_active(IntVector2(x, y + 1))

                if (x, y) == (ant.pos.x, ant.pos.y):
                    col_top = COL_INT_ANT
                elif top_active:
                    col_top = COL_INT_ON
                elif x % 10 == 0 and y % 10 == 0:
                    col_top = COL_INT_MARKER
                else:
                    col_top = COL_INT_OFF

                if (x, y + 1) == (ant.pos.x, ant.pos.y):
                    col_bottom = COL_INT_ANT
                elif bottom_active:
                    col_bottom = COL_INT_ON
                elif x % 10 == 0 and (y + 1) % 10 == 0:
                    col_bottom = COL_INT_MARKER
                else:
                    col_bottom = COL_INT_OFF

                buf += f"{col(col_top)}{col(col_bottom, bg=True)}▀{COL_RESET}"
            buf += "\n"
        print(buf, end='', flush=True)

        # flush=True is needed here or else the exit message won't print
        print(f"{COL_RESET}Press Ctrl-C to exit.", end='', flush=True)

        time.sleep(STEP_DELAY)

def main():
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor and clear screen
        print("\033[H\033[J\033[?25h", end='', flush=True)

if __name__ == "__main__":
    main()