import time
import random
import shutil

from src.screensavers.utils.vectors import Vector3, clamp
from src.screensavers.utils.colours import lerp_colours, rgb_to_str
from src.screensavers.utils.colours import COL_RESET

FPS = 60

FALL_SPEED: float = 10  # chars/s

WIND_STRENGTH: float = 0.2  # chars/s
WIND_CHANGE_TIME = 10

SNOW_SPAWN_RATE: float = 12
MAX_SNOWFLAKE_DISTANCE: float = 10
MIN_SNOWFLAKE_DISTANCE: float = 1
SNOWFLAKE_CHARS = "*.·+"

PARALLAX_FRONT_COLOUR = (153, 255, 255)
PARALLAX_BACK_COLOUR = (91, 91, 128)

class Snowflake:
    def __init__(self, x: float, y: float, z: float, char: str) -> None:
        self.pos = Vector3(x, y, z)
        self.char = char

    def update(self, dt_s: float, lateral_wind_rate: Vector3) -> None:
        self.pos.y += FALL_SPEED * dt_s
        self.pos += lateral_wind_rate * dt_s
        self.pos.z = clamp(self.pos.z, (MIN_SNOWFLAKE_DISTANCE, MAX_SNOWFLAKE_DISTANCE))

    def get_viewport_pos(self, vp_w: int, vp_h: int) -> tuple[float, float]:
        """Assuming (0, 0) is top-centre of viewport and +self.pos.y = downwards"""

        half_vp_w = vp_w // 2

        vp_x = (self.pos.x / self.pos.z) + half_vp_w
        vp_y = self.pos.y / self.pos.z

        return (vp_x, vp_y)

    def is_in_viewport(self, vp_w: int, vp_h: int) -> bool:
        vp_x, vp_y = self.get_viewport_pos(vp_w, vp_h)
        return (0 <= vp_x < vp_w) and (0 <= vp_y < vp_h)

class SnowflakesSim:
    def __init__(self) -> None:
        self.snowflakes: list[Snowflake] = []

        self._wind_old = Vector3(random.uniform(-WIND_STRENGTH, WIND_STRENGTH), 0, random.uniform(-WIND_STRENGTH, WIND_STRENGTH))
        self._wind_new = Vector3(random.uniform(-WIND_STRENGTH, WIND_STRENGTH), 0, random.uniform(-WIND_STRENGTH, WIND_STRENGTH))
        self.t_wind = 0

    def _generate_wind_dir(self) -> Vector3:
        return Vector3(random.uniform(-WIND_STRENGTH, WIND_STRENGTH), 0, random.uniform(-WIND_STRENGTH, WIND_STRENGTH))

    def get_current_wind(self) -> Vector3:
        return self._wind_old.lerp(self._wind_new, self.t_wind / WIND_CHANGE_TIME)

    def spawn_snowflake(self, vp_w: float) -> None:
        z = random.uniform(MIN_SNOWFLAKE_DISTANCE, MAX_SNOWFLAKE_DISTANCE)
        y = 0

        half_vp_w = vp_w / 2
        x = random.uniform(-half_vp_w * z, half_vp_w * z)

        self.snowflakes.append(Snowflake(x, y, z, random.choice(SNOWFLAKE_CHARS)))

    def update(self, dt_s: float, vp_w: int, vp_h: int) -> None:
        if random.random() < SNOW_SPAWN_RATE * dt_s:
            self.spawn_snowflake(vp_w)

        self.t_wind += dt_s
        if self.t_wind >= WIND_CHANGE_TIME:
            self.t_wind = 0
            self._wind_old = self._wind_new
            self._wind_new = self._generate_wind_dir()

        wind = self.get_current_wind()

        for snowflake in self.snowflakes[:]:
            snowflake.update(dt_s, wind)

            # Allow flakes to exist slightly outside the bounds before killing them
            _, vp_y = snowflake.get_viewport_pos(vp_w, vp_h)
            if vp_y > vp_h or snowflake.pos.z < 0.1: # Kill if below screen or behind camera
                self.snowflakes.remove(snowflake)

    def draw(self, vp_w: int, vp_h: int) -> None:
        buf: list[list[str]] = [[" " for _ in range(vp_w)] for _ in range(vp_h)]

        # higher z-coord = further behind the camera
        # furthest behind = first
        # that way the closest snowflakes are drawn last
        snowflakes = sorted(self.snowflakes, key=lambda sf: sf.pos.z, reverse=True)

        for sf in snowflakes[:]:
            visual_x, visual_y = sf.get_viewport_pos(vp_w, vp_h)
            visual_x, visual_y = int(visual_x), int(visual_y)

            if 0 <= visual_x < vp_w and 0 <= visual_y < vp_h:
                frac = (sf.pos.z - MIN_SNOWFLAKE_DISTANCE) / (MAX_SNOWFLAKE_DISTANCE - MIN_SNOWFLAKE_DISTANCE)
                colour = lerp_colours(PARALLAX_FRONT_COLOUR, PARALLAX_BACK_COLOUR, frac)

                buf[visual_y][visual_x] = f"{rgb_to_str(colour)}{sf.char}{COL_RESET}"

        print("\n".join(["".join(row) for row in buf]))

def run():
    sim = SnowflakesSim()

    while True:
        print("\033[H", end='')

        term_w, term_h = shutil.get_terminal_size()

        sim.update(1 / FPS, term_w, term_h)
        sim.draw(term_w, term_h)

        print("Press Ctrl-C to exit.", flush=True)

        time.sleep(1 / FPS)

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