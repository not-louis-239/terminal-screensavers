import sys
import json
import shutil
import random
from dataclasses import dataclass

from screensavers.utils.utils import collapse
from screensavers.utils.colours import add_colours, scale_brightness
from screensavers.utils.vectors import Vector2
from screensavers.utils.clock import Clock
from screensavers.utils.buffer import Buffer
from screensavers.utils.custom_types import Colour
from screensavers.utils.dirs import DIRS
from screensavers.utils.kb_input_manager import KBInputManager, Keys

FPS = 60

SMOKE_COLOUR = (30, 30, 50)
SMOKE_BUBBLE_RADIUS = 5
FLAME_RADIUS = 2
EMBER_SPAWN_RATE = 30  # embers/s
EMBER_LIFETIME = 1.8
EMBER_DRIFT_FACTOR = 1.0  # pix/s max
EMBER_DRIFT_CHANGE_FACTOR = 0.1  # pix/s^2 max
EMBER_RISE_SPEED = 40  # pix/s

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

def get_viewport_size() -> tuple[int, int]:
    term_w, term_h = shutil.get_terminal_size()
    return (term_w, 2 * (term_h - 1))

class Ember:
    def __init__(self, pos: Vector2) -> None:
        self.pos: Vector2 = pos
        self.life: float = 1.0
        self.drift_vel = random.uniform(-EMBER_DRIFT_FACTOR, EMBER_DRIFT_FACTOR)

    def update(self, dt_s: float) -> None:
        self.life -= dt_s / EMBER_LIFETIME
        self.pos.y -= EMBER_RISE_SPEED * dt_s
        self.pos.x += self.drift_vel * dt_s
        self.drift_vel += random.uniform(-EMBER_DRIFT_CHANGE_FACTOR, EMBER_DRIFT_CHANGE_FACTOR) * dt_s

    def alive(self) -> bool:
        return self.life > 0 and self.pos.y > -SMOKE_BUBBLE_RADIUS  # on screen AND life > 0

    def draw(self, buf: Buffer, material: Material) -> None:
        px, py = int(self.pos.x), int(self.pos.y)

        flame_rad_sq = FLAME_RADIUS * FLAME_RADIUS
        smoke_bubble_rad_sq = SMOKE_BUBBLE_RADIUS * SMOKE_BUBBLE_RADIUS

        ymin = max(py - SMOKE_BUBBLE_RADIUS, 0)
        ymax = min(py + SMOKE_BUBBLE_RADIUS, buf.get_height())
        xmin = max(px - SMOKE_BUBBLE_RADIUS, 0)
        xmax = min(px + SMOKE_BUBBLE_RADIUS, buf.get_width())

        for y in range(ymin, ymax + 1):
            for x in range(xmin, xmax + 1):
                dx, dy = x - px, y - py
                dist_sq = dx*dx + dy*dy

                # Radius checking (bounds checking isn't used here because buf.set_pix simply does nothing if the target pixel is out of bounds)
                if dist_sq > smoke_bubble_rad_sq:
                    continue

                dist = dist_sq ** 0.5

                brightness = 1 - dist / SMOKE_BUBBLE_RADIUS

                pix_init = buf.get_pix(x, y)[:3]
                pix_subt = add_colours(pix_init, scale_brightness(SMOKE_COLOUR, brightness * self.life))

                if dist_sq < flame_rad_sq:
                    pix_fin = add_colours(pix_subt, scale_brightness(material.flame_colour, self.life * (1 - dist / FLAME_RADIUS)))
                else:
                    pix_fin = pix_subt

                buf.set_pix(x, y, (pix_fin[0], pix_fin[1], pix_fin[2], 255))

class FireSim:
    def __init__(self) -> None:
        self.buf = Buffer(*get_viewport_size())
        self.clock = Clock()
        self.kb = KBInputManager()

        self.embers: list[Ember] = []
        self.materials = load_materials()
        self.material_idx = 0

    def spawn_ember(self, vp_w: float, vp_h: float) -> None:
        ember_x = random.uniform(0, vp_w)
        self.embers.append(Ember(pos=Vector2(ember_x, vp_h + SMOKE_BUBBLE_RADIUS)))

    def take_input(self, dt_s: float) -> None:
        if self.kb.went_down(Keys.SPACE):
            self.material_idx = (self.material_idx + 1) % len(self.materials)

    def update(self, dt_s: float, vp_w: int, vp_h: int) -> None:
        self.kb.update()

        for ember in self.embers:
            ember.update(dt_s=dt_s)

        if (vp_w, vp_h) != self.buf.get_size():
            self.buf.resize_and_clear(vp_w, vp_h)

        for _ in range(collapse(EMBER_SPAWN_RATE * dt_s)):
            self.spawn_ember(vp_w=vp_w, vp_h=vp_h)

        self.embers = [ember for ember in self.embers if ember.alive()]

    def update_buf(self) -> None:
        self.buf.clear()

        for ember in self.embers:
            ember.draw(buf=self.buf, material=self.materials[self.material_idx])

def run():
    sim = FireSim()

    while True:
        dt_s = sim.clock.tick(FPS)

        sim.update(dt_s, *get_viewport_size())
        sim.update_buf()
        sim.take_input(dt_s)

        print("\033[H", end='')
        print(sim.buf.render())

        theme_text = f"Theme: {sim.materials[sim.material_idx].name}"
        print(f"{theme_text:<30} | Press Ctrl-C to exit.", end='', flush=True)

def main():
    try:
        print("\033[H\033[J\033[?25l", end='', flush=True)
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h", end='', flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
