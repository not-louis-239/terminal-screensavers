from __future__ import annotations

from .custom_types import Colour
from .colours import COL_RESET

class Buffer:
    _BLACK: Colour = (0, 0, 0)

    def __init__(self, width: int, height: int) -> None:
        self.pixels: list[list[Colour]] = [[self._BLACK for _ in range(width)] for _ in range(height)]

    def _rgb_to_str(self, colour: Colour, /, *, bg: bool = False) -> str:
        r, g, b = colour
        return f"\033[{48 if bg else 38};2;{r};{g};{b}m"

    def get_width(self) -> int:
        return len(self.pixels[0])

    def get_height(self) -> int:
        return len(self.pixels)

    def get_size(self) -> tuple[int, int]:
        return (self.get_width(), self.get_height())

    def fill(self, colour: Colour) -> None:
        self.pixels = [[colour for _ in range(self.get_width())] for _ in range(self.get_height())]

    def clear(self) -> None:
        self.fill(self._BLACK)

    def resize_and_clear(self, width: int, height: int) -> None:
        self.pixels = [[self._BLACK for _ in range(width)] for _ in range(height)]

    def set_pix(self, x: int, y: int, colour: Colour, wrap: bool = False) -> None:
        if wrap:
            x %= self.get_width()
            y %= self.get_height()
        if 0 <= y < self.get_height() and 0 <= x < self.get_width():
            self.pixels[y][x] = colour

    def get_pix(self, x: int, y: int, wrap: bool = False) -> Colour:
        if wrap:
            x %= self.get_width()
            y %= self.get_height()
        if 0 <= y < self.get_height() and 0 <= x < self.get_width():
            return self.pixels[y][x]
        return self._BLACK

    def blit(self, other: Buffer, start_x: int = 0, start_y: int = 0) -> None:
        for y, row in enumerate(other.pixels):
            for x, val in enumerate(row):
                self.set_pix(x + start_x, y + start_y, val)

    def draw_line(self, x0, y0, x1, y1, colour):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            self.set_pix(x0, y0, colour)

            if x0 == x1 and y0 == y1:
                break

            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def __repr__(self) -> str:
        return f"Buffer(width={self.get_width()}, height={self.get_height()})"

    def render(self) -> str:
        rendered_rows: list[list[str]] = []
        width, height = self.get_width(), self.get_height()

        for y in range(0, height, 2):
            row: list[str] = []
            for x in range(0, width):
                top_col = self.get_pix(x, y)

                # Note: using upper half-block character so that if the
                # buffer has an odd number of rows, the bottom out-of-bounds
                # row can appear as fully transparent

                if y + 1 < height:  # bottom row in-bounds
                    bottom_col = self.get_pix(x, y + 1)
                    char = f"{self._rgb_to_str(top_col)}{self._rgb_to_str(bottom_col, bg=True)}▀{COL_RESET}"
                else:  # bottom row out of bounds
                    char = f"{self._rgb_to_str(top_col)}▀{COL_RESET}"

                row.append(char)
            rendered_rows.append(row)

        return "\n".join(["".join(row) for row in rendered_rows])
