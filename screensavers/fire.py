from dataclasses import dataclass
import time
import json
import shutil

from lib.buffer import Buffer
from lib.custom_types import Colour
from lib.dirs import DIRS
from lib.kb_input_manager import KBInputManager, Keys

FPS = 60

@dataclass
class Material:
    name: str
    flame_colour: Colour

def load_materials() -> list[Material]:
    materials: list[Material] = []

    with open((DIRS.assets.json.flame_materials / "flame_materials.json").path(), "r") as f:
        materials_raw = json.load(f)["materials"]

    assert isinstance(materials_raw, list)

    for obj in materials_raw:
        materials.append(Material(obj["name"], obj["flame_colour"]))

    return materials

class SmokeBubble:
    def __init__(self) -> None:
        pass

    def update(self, dt_s: float) -> None:
        pass

class FireSim:
    def __init__(self) -> None:
        self.kb = KBInputManager()

        vp_w, vp_h = shutil.get_terminal_size()
        self.buf = Buffer(vp_w, vp_h)

        self.materials = load_materials()
        self.material_idx = 0

    def update(self, dt_s: float, vp_w: int, vp_h: int) -> None:
        if (vp_w, vp_h) != self.buf.get_size():
            self.buf.resize_and_clear(vp_w, vp_h)

    def take_input(self, dt_s: float) -> None:
        if self.kb.went_down(Keys.SPACE):
            self.material_idx += 1
            self.material_idx %= len(self.materials)

    def render(self) -> str:
        self.buf.clear()

        return self.buf.render()

def run():
    sim = FireSim()

    dt_s = 1 / FPS

    while True:
        print("\033[H", end='')

        term_w, term_h = shutil.get_terminal_size()
        vp_w, vp_h = term_w, 2 * (term_h) - 1

        sim.update(dt_s, vp_w, vp_h)
        sim.take_input(dt_s)
        print(sim.render())

        print("Press Ctrl-C to exit.", flush=True)
        time.sleep(dt_s)

def main():
    try:
        print("\033[H\033[J\033[?25l", end='', flush=True)
        run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[H\033[J\033[?25h", end='', flush=True)
