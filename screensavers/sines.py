import sys
import shutil

from lib.custom_types import Colour
from lib.kb_input_manager import KBInputManager
from lib.colours import lerp_colours, rgb_to_str
from lib.utils import clamp
from lib.buffer import Buffer
from lib.clock import Clock

FPS = 60
SPAWN_RATE = 0.6  # chance to spawn a wave per second
DARK_BG = (20, 20, 20)  # used to control the colour that the edges of a wave blend into

class SineWave:
    def __init__(
            self,
            colour: Colour,
            lifetime: float,
            amplitude: float,
            frequency: float,
        ) -> None:
        self.colour = colour
        self.lifetime = lifetime
        self.amplitude = amplitude
        self.frequency = frequency

        self.age = 0

    def update(self, dt_s: float) -> None:
        self.age += dt_s

    def alive(self) -> bool:
        return self.age < self.lifetime

    def draw(self, buf: Buffer) -> None:
        ...

def get_visible_area() -> tuple[int, int]:
    term_w, term_h = shutil.get_terminal_size()
    return (term_w, 2 * (term_h - 1))

class Simulation:
    def __init__(self) -> None:
        self.waves: list[SineWave] = []
        self.kb = KBInputManager()
        self.clock = Clock()
        self.buf = Buffer(*get_visible_area())

    def spawn_sine_wave(self) -> None:
        ...

    def update(self) -> None:
        self.update_buf()

    def update_buf(self) -> None:
        ...

def run():
    sim = Simulation()
    while True:
        sim.clock.tick(FPS)
        sim.update()

        print(sim.buf.render())
        print("Press Ctrl-C to exit.", end='', flush=True)

def main():
    try:
        print("\033[H\033[J\033[?25l")
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[25h", end='', flush=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
