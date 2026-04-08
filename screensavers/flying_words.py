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

from lib.utils import chance
from lib.custom_types import Colour, T
from lib.colours import COL_RESET, rgb_to_str, lerp_colours
from lib.dirs import DIRS
from lib.kb_input_manager import KBInputManager, Keys

FPS = 60
SPAWN_CHANCE = 0.5
MIN_SPEED = 30
MAX_SPEED = 50

START_TEMP = 20
ABS_ZERO = -273.15
MAX_TEMP = 150

ABS_ZERO_COLOUR = (60, 60, 60)
MAX_TEMP_COLOUR = (255, 255, 255)

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
def load_kw_packs() -> list[KeywordPack]:
    with open((DIRS.assets.json.kw_packs / "kw_packs.json").path(), "r") as f:
        kw_packs_raw = json.load(f)["kw_packs"]
        print(kw_packs_raw)

    kw_packs: list[KeywordPack] = []

    for pack in kw_packs_raw:
        pack_name = pack["name"]
        pack_contents = pack["kw_groups"]

        assert isinstance(pack_name, str)

        kw_groups: list[KeywordGroup] = []

        for group in pack_contents:
            new = KeywordGroup(
                weight=group["weight"],
                colour=group["colour"],
                words=group["words"]
            )
            kw_groups.append(new)

        kw_packs.append(KeywordPack(
            name=pack_name,
            kw_groups=kw_groups
        ))

    return kw_packs

import random

def pick_opt_from_weighted_table(table: list[tuple[T, float]]) -> T:
    if not table:
        raise ValueError("Table is empty")

    # zip(*table) unpacks the tuples into two separate iterables
    objs, weights = zip(*table)

    if sum(weights) == 0:
        raise ValueError("Total of weights cannot be zero")
    if any((bad_weight := weight) < 0 for weight in weights):
        raise ValueError(f"No weight can be negative. Got {bad_weight}")

    # random.choices returns a list, so we take the first element [0]
    return random.choices(objs, weights=weights, k=1)[0]

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
        self.current_kw_pack_idx: int = 0

        self.temperature = START_TEMP
        self.flying_words: list[FlyingWord] = []

        self.kw_packs = load_kw_packs()
        self.current_kw_pack: int = 0

        w, h = shutil.get_terminal_size()
        self.buffer: list[list[str]] = [[" " for _ in range(w)] for _ in range(h)]

    def _pick_word_and_colour(self, kw_pack: KeywordPack) -> tuple[str, Colour]:
        if not kw_pack.kw_groups:
            raise ValueError("KeywordPack has no groups")

        # Build the weighted table: [(KeywordGroup, weight), ...]
        weighted_table = [(group, group.weight) for group in kw_pack.kw_groups]

        # 2. Pick the winning group
        chosen_group = pick_opt_from_weighted_table(weighted_table)

        # 3. Pick a random word from the chosen group
        # (Assuming words in a group are equally likely)
        chosen_word = random.choice(chosen_group.words)

        return chosen_word, chosen_group.colour

    def _adjust_colour_on_temp(self, base_colour: Colour) -> Colour:
        frac_of_normal = (self.temperature - ABS_ZERO) / (START_TEMP - ABS_ZERO)

        if frac_of_normal >= 1:
            # Hot
            heat_intensity = (self.temperature - START_TEMP) / (MAX_TEMP - START_TEMP)
            return lerp_colours(base_colour, MAX_TEMP_COLOUR, heat_intensity)
        else:
            # Cold
            return lerp_colours(ABS_ZERO_COLOUR, base_colour, frac_of_normal)

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

        word, colour = self._pick_word_and_colour(self.kw_packs[self.current_kw_pack_idx])
        direction = random.choice((-1, 1))

        if direction == -1:
            start_x = viewport_w
        else:
            start_x = -len(word)

        new = FlyingWord(
            x=start_x,
            y=random.choice(list(unoccupied_rows)),
            text=word,
            base_speed=random.uniform(MIN_SPEED, MAX_SPEED),
            direction=direction,
            colour=colour
        )

        self.flying_words.append(new)

    def take_input(self, dt_s: float) -> None:
        if self.kb.went_down(Keys.SPACE):
            self.current_kw_pack_idx += 1
            self.current_kw_pack_idx %= len(self.kw_packs)

            # Clear the flying words on screen when changing theme
            self.flying_words.clear()

        # Change temperature at 80°C/s depending on key pressed
        if self.kb.is_down(Keys.W):
            self.temperature += 80 * dt_s
        if self.kb.is_down(Keys.S):
            self.temperature -= 80 * dt_s

        self.temperature = max(self.temperature, ABS_ZERO)

    def update(self, *, viewport_w: int, viewport_h: int) -> None:
        self.kb.update()  # VERY IMPORTANT!

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
            colour_str = rgb_to_str(self._adjust_colour_on_temp(flying_word.colour))
            for i, char in enumerate(flying_word.text):
                x, y = int(flying_word.x + i), flying_word.y

                if not 0 <= x < viewport_w or not 0 <= y < viewport_h:
                    continue

                self.buffer[y][x] = f"{colour_str}{char}{COL_RESET}"

        print("\n".join(["".join(row) for row in self.buffer]), flush=True)

def run():
    sim = FlyingWordsSim()

    print("\033[H\033[J", end="")
    while True:
        tw, th = shutil.get_terminal_size()

        visible_h = th - 1

        sim.update(viewport_w=tw, viewport_h=visible_h)
        sim.take_input(1 / FPS)

        if sim.temperature > MAX_TEMP:
            # Print a fake traceback before exiting
            print("\033[H\033[J", end='')
            traceback = (
                "Traceback (most recent call last):",
                "  File \"main.py\", line 442, in <module>",
                "    sim.run()",
                "  File \"core/engine.py\", line 89, in run",
                "    self.update_physics(dt)",
                "  File \"core/physics.py\", line 156, in update_physics",
                "    self.processor.compute_thermal_load()",
                "  File \"hardware/drivers/cpu.py\", line 12, in compute_thermal_load",
                "    return __thermal_interface__.get_die_temp(core_id=0)",
                "  File \"hardware/drivers/thermal.py\", line 204, in get_die_temp",
                "    raise HardwareCriticalError(f\"Sensor overflow at {hex(id(self))}\")",
                "errors.HardwareCriticalError: Sensor overflow at 0x00007FFD2E41B090",
                "",
                "--- [ SYSTEM HALT: THERMAL_PROTECTION_FAULT ] ---",
                "Reason: Temperature exceeded MAX_TEMP threshold.",
                f"CPU_CORE_0: {sim.temperature:.1f}°C (CRITICAL)",
                "VOLTAGE_REG: FAILURE",
                "KERNEL_STATE: DUMPING MEMORY...",
            )

            print("\n".join(traceback) + "\n")

            time.sleep(2)

            # Flush any "ghost" keystrokes
            termios.tcflush(sys.stdin, termios.TCIFLUSH)
            break

        sim.draw(viewport_w=tw, viewport_h=visible_h)

        hud_text = f"{f"Temp: {sim.temperature:.1f}°C":<15} | {f"Theme: {sim.kw_packs[sim.current_kw_pack_idx].name.title()}":<15}"
        print(f"{hud_text:<32} | Press Ctrl-C to exit.", flush=True)

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
