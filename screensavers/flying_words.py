"""flying_words.py"""

import sys
import shutil
import random
import time
import termios
import json
from dataclasses import dataclass
from typing import Literal
from pathlib import Path

from lib.utils import chance, clamp
from lib.kb_input_manager import KBInputManager, Keys

FPS = 60
SPAWN_CHANCE = 0.5
MIN_SPEED = 30
MAX_SPEED = 50

START_TEMP = 20
ABS_ZERO = -273.15
MAX_TEMP = 150

@dataclass
class KeywordGroup:
    weight: float
    colour: tuple[int, int, int]
    words: list[str]

@dataclass
class KeywordPack:
    name: str
    kw_groups: list[KeywordGroup]

# Load keyword packs
def load_kw_packs() -> dict[str, KeywordPack]:
    with open(Path(__file__).parent.parent / "data" / "kw_packs.json") as f:
        kw_packs_raw = json.load(f)["kw_packs"]

    kw_packs: dict[str, KeywordPack] = {}

    # FIXME: AttributeError: 'list' object has no attribute 'items'
    for pack_name, pack_contents in kw_packs_raw.items():
        kw_groups: list[KeywordGroup] = []
        for group in pack_contents:
            new = KeywordGroup(
                weight=group["weight"],
                colour=group["colour"],
                words=group["words"]
            )
            kw_groups.append(new)

        kw_packs[pack_name] = KeywordPack(
            name=pack_name,
            kw_groups=kw_groups
        )

    return kw_packs

@dataclass
class FlyingWord:
    text: str

    x: float
    y: int

    base_speed: float  # chars/s
    direction: Literal[-1, 1]
    colour: tuple[int, int, int]

    def update(self, dt_s: float, T: float) -> None:
        speed_mult = (T - ABS_ZERO) / (START_TEMP - ABS_ZERO)
        final_speed = self.base_speed * speed_mult

        self.x += final_speed * dt_s * self.direction

class FlyingWordsSim:
    def __init__(self) -> None:
        self.kb = KBInputManager()

        self.temperature = START_TEMP
        self.flying_words: list[FlyingWord] = []

        self.kw_packs = load_kw_packs()
        self.current_kw_pack: int = 0

        w, h = shutil.get_terminal_size()
        self.buffer: list[list[str]] = [[" " for _ in range(w)] for _ in range(h)]

    def cycle_kw_pack(self) -> None:
        self.current_kw_pack = (self.current_kw_pack + 1) % len(self.kw_packs)

    def cull_offscreen_words(self, term_w: int) -> None:
        for flying_word in self.flying_words[:]:
            if (
                flying_word.direction == -1 and flying_word.x < -len(flying_word.text)
                or flying_word.direction == 1 and flying_word.x > term_w
            ):
                self.flying_words.remove(flying_word)

    def spawn_flying_word(self, *, viewport_w: int, viewport_h: int) -> None:
        unoccupied_rows = set(range(viewport_h)) - {f.y for f in self.flying_words}

        # Skip drawing if all rows are occupied
        # This avoids a ValueError downstream
        if not unoccupied_rows:
            return

        text = "hello"
        direction = random.choice((-1, 1))

        if direction == -1:
            start_x = viewport_w
        else:
            start_x = -len(text)

        new = FlyingWord(
            x=start_x,
            y=random.choice(list(unoccupied_rows)),
            text=text,
            base_speed=random.uniform(MIN_SPEED, MAX_SPEED),
            direction=direction,
            colour=(255, 255, 255)
        )

        self.flying_words.append(new)

    def take_input(self, dt_s: float) -> None:
        # Change temperature at 80°C/s depending on key pressed
        if self.kb.is_down(Keys.W):
            self.temperature += 80 * dt_s
        if self.kb.is_down(Keys.S):
            self.temperature -= 80 * dt_s

        self.temperature = max(self.temperature, ABS_ZERO)

    def update(self, *, viewport_w: int, viewport_h: int) -> None:
        if chance(SPAWN_CHANCE):
            self.spawn_flying_word(viewport_w=viewport_w, viewport_h=viewport_h)

        for flying_word in self.flying_words:
            flying_word.update(1 / FPS, self.temperature)

        self.cull_offscreen_words(term_w=viewport_w)

    def draw(self, *, viewport_w: int, viewport_h: int) -> None:
        # Only reassign a new buffer if the terminal width and height has changed
        # since the last draw
        if len(self.buffer) != viewport_h or len(self.buffer[0]) != viewport_w:
            self.buffer = [[" " for _ in range(viewport_w)] for _ in range(viewport_h)]
        else:
            for y in range(viewport_h):
                for x in range(viewport_w):
                    self.buffer[y][x] = " "

        for flying_word in self.flying_words[:]:  # Create a shallow copy of the list to avoid modify-while-iterating bugs
            for i, char in enumerate(flying_word.text):
                x, y = int(flying_word.x + i), flying_word.y

                if not 0 <= x < viewport_w or not 0 <= y < viewport_h:
                    continue

                self.buffer[y][x] = char

        print("\n".join(["".join(row) for row in self.buffer]), flush=True)

def run():
    sim = FlyingWordsSim()

    print("\033[H\033[J", end="")
    while True:
        tw, th = shutil.get_terminal_size()

        visible_h = th - 1

        sim.take_input(1 / FPS)
        sim.update(viewport_w=tw, viewport_h=visible_h)

        if sim.temperature > MAX_TEMP:
            # Print a fake traceback before exiting
            print("\033[H\033[J", end='')
            traceback = (
                "Traceback (most recent call last)",
                "  File \"main.py\", line 123, in update",
                "    raise RuntimeError('system meltdown')",
                "RuntimeError: system meltdown"
            )

            print("\n".join(traceback) + "\n")

            time.sleep(2)

            # Flush any "ghost" keystrokes
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
            break

        sim.draw(viewport_w=tw, viewport_h=visible_h)

        hud_text = f"Temp: {sim.temperature:.1f}°C"
        print(f"{hud_text:<24} | Press Ctrl-C to exit.", flush=True)

        time.sleep(1 / FPS)
        termios.tcflush(sys.stdin, termios.TCIFLUSH)

def main():
    try:
        print("\033[H\033[J\033[?25l", end='', flush=True)
        run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[H\033[J\033[?25h", end='', flush=True)

if __name__ == "__main__":
    main()
