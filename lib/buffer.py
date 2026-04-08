from __future__ import annotations

from pathlib import Path
from typing import cast

from PIL import Image

from .custom_types import Colour, AColour
from .colours import COL_RESET
from .utils import rgb_to_str

class Buffer:
    _CLEAR: AColour = (0, 0, 0, 0)

    def __init__(self, width: int, height: int) -> None:
        self.pixels: list[list[AColour]] = [[self._CLEAR for _ in range(width)] for _ in range(height)]

    @classmethod
    def load_from_img(cls, img_path: Path, /) -> Buffer:
        with Image.open(img_path, "r") as img:
            # Convert to RGB to ensure we get (R, G, B) tuples
            # (Prevents issues with PNG transparency or Grayscale)
            img = img.convert("RGBA")
            width, height = img.size

            # Create the new Buffer instance
            new_buffer = cls(width, height)

            # Load pixel data into a flat access object for speed
            pixel_data = img.load()

            # Populate the nested list
            # Outer list is rows (height), inner list is columns (width)
            assert pixel_data is not None
            new_buffer.pixels = [
                [cast(AColour, pixel_data[x, y])
                for x in range(width)]
                for y in range(height)
            ]

            assert all(all(len(pix) == 4 for pix in row) for row in new_buffer.pixels)

            return new_buffer

    def get_width(self) -> int:
        return len(self.pixels[0])

    def get_height(self) -> int:
        return len(self.pixels)

    def get_size(self) -> tuple[int, int]:
        return (self.get_width(), self.get_height())

    def fill(self, colour: AColour) -> None:
        self.pixels = [[colour for _ in range(self.get_width())] for _ in range(self.get_height())]

    def clear(self) -> None:
        self.fill(self._CLEAR)

    def resize_and_clear(self, width: int, height: int) -> None:
        self.pixels = [[self._CLEAR for _ in range(width)] for _ in range(height)]

    def set_pix(self, x: int, y: int, colour: Colour | AColour, wrap: bool = False) -> None:
        if len(colour) == 3:
            colour = (*colour, 255)

        w, h = self.get_size()

        if wrap:
            x %= w
            y %= h
        if 0 <= y < h and 0 <= x < w:
            self.pixels[y][x] = colour

    def get_pix(self, x: int, y: int, wrap: bool = False) -> AColour:
        w, h = self.get_size()

        if wrap:
            x %= w
            y %= h
        if 0 <= y < h and 0 <= x < w:
            return self.pixels[y][x]
        return self._CLEAR

    def blit(self, other: Buffer, start_x: int = 0, start_y: int = 0) -> None:
        for y, row in enumerate(other.pixels):
            for x, colour in enumerate(row):
                bg_r, bg_g, bg_b, bg_a = self.get_pix(x + start_x, y + start_y)
                fg_r, fg_g, fg_b, fg_a = colour

                # Get normalised alpha values
                fg_a_norm = fg_a / 255.0
                bg_a_norm = bg_a / 255.0

                # Calculate new alpha
                out_a_norm = fg_a_norm + bg_a_norm * (1.0 - fg_a_norm)

                if out_a_norm <= 0:
                    new_colour = self._CLEAR
                else:
                    # Calculate the new RGB channels
                    # We divide by a_out to "un-premultiply" the color
                    new_r = (fg_r * fg_a_norm + bg_r * bg_a_norm * (1.0 - fg_a_norm)) / out_a_norm
                    new_g = (fg_g * fg_a_norm + bg_g * bg_a_norm * (1.0 - fg_a_norm)) / out_a_norm
                    new_b = (fg_b * fg_a_norm + bg_b * bg_a_norm * (1.0 - fg_a_norm)) / out_a_norm

                    new_colour = (
                        int(min(255, max(0, new_r))),
                        int(min(255, max(0, new_g))),
                        int(min(255, max(0, new_b))),
                        int(min(255, max(0, out_a_norm * 255)))
                    )

                # Assign directly to avoid double-blending logic in set_pix
                self.set_pix(x + start_x, y + start_y, new_colour, wrap=False)

    def draw_line(self, x0, y0, x1, y1, colour):
        if len(colour) == 3:
            colour = (*colour, 255)

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

    def draw_rect(self, x: int, y: int, w: int, h: int, colour: Colour | AColour) -> None:
        if len(colour) == 3:
            colour = (*colour, 255)

        for ix in range(x, x + w):
            for iy in range(y, y + h):
                self.set_pix(ix, iy, colour)

    def draw_circle(self, centre: tuple[int, int], r: float, colour: Colour | AColour) -> None:
        cx, cy = centre

        if len(colour) == 3:
            colour = (*colour, 255)

        r_sq = r**2
        for y in range(int(cy - r), int(cy + r) + 1, 1):
            for x in range(int(cx - r), int(cx + r) + 1, 1):
                dx, dy = x - cx, y - cy
                if dx*dx + dy*dy <= r_sq:
                    self.set_pix(x, y, colour)

    def __repr__(self) -> str:
        return f"Buffer(width={self.get_width()}, height={self.get_height()})"

    def render(self) -> str:
        rendered_rows: list[list[str]] = []
        width, height = self.get_size()

        # Track the state of the terminal colour and only add colour codes
        # if it changed since the last pixel
        current_fg = None
        current_bg = None

        for y in range(0, height, 2):
            row_segments: list[str] = []

            for x in range(0, width):
                top_col: Colour = self.get_pix(x, y)[:3]

                if y + 1 < height:
                    # Bottom row in bounds
                    bottom_col: Colour | None = self.get_pix(x, y + 1)[:3]
                else:
                    # bottom row out of bounds
                    bottom_col: Colour | None = None

                # Note: using upper half-block character so that if the
                # buffer has an odd number of rows, the bottom out-of-bounds
                # row can appear as fully transparent

                # XXX: ignoring alpha in rendering for now

                # Update Background if it changed
                if bottom_col != current_bg:
                    if bottom_col is not None:
                        row_segments.append(rgb_to_str(bottom_col, bg=True))
                    else:
                        row_segments.append(COL_RESET)
                    current_bg = bottom_col

                # Update Foreground if it changed
                if top_col != current_fg:
                    row_segments.append(rgb_to_str(top_col))
                    current_fg = top_col

                row_segments.append("▀")

            rendered_rows.append(row_segments)

            current_fg = None
            current_bg = None

        # Only append COL_RESET at the end once for efficiency, prevents I/O saturation
        return "\n".join(["".join(row_segments) for row_segments in rendered_rows]) + COL_RESET
