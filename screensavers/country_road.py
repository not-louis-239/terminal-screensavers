"""
country_road.py

Experience a road trip, right from your terminal!
"""

import time
import shutil
import random

from noise import snoise2

from lib.dirs import DIRS
from lib.custom_types import Colour
from lib.colours import COL_RESET, lerp_colours
from lib.buffer import Buffer
from lib.utils import clamp, chance
from lib.dirs import DIRS
from lib.kb_input_manager import KBInputManager, Keys

FPS = 60
SKY_COLOUR_BOTTOM = (178, 192, 255)
SKY_COLOUR_TOP = (91, 96, 255)

GROUND_COLOUR = (70, 45, 15)
GROUND_HEIGHT = 12

ROAD_TOP_HEIGHT = GROUND_HEIGHT - 3
ROAD_BOTTOM_HEIGHT = GROUND_HEIGHT - 7

ROAD_STRIPE_HEIGHT = GROUND_HEIGHT - 5
ROAD_STRIPE_WIDTH = 5

ROAD_COLOUR = (30, 30, 30)
ROAD_STRIPE_COLOUR = (230, 230, 230)

STARTING_CAR_SPEED = 110 / 3.6  # metres per second, approx. 110 km/h

COL_SPEEDING = "\033[33m"
COL_NORMAL = "\033[32m"
SPEED_LIMIT = 110 / 3.6  # m/s
HARD_SPEED_LIMIT = 300 / 3.6

class Car:
    def __init__(self, x: int, y: int, image: Buffer):
        self.x = x
        self.y = y
        self.image = image

class MountainRange:
    DISCARD_DISTANCE = 250

    def __init__(self, y: int, colour: Colour, variance: float, scale: float, parallax: float):
        self.y = y
        self.colour = colour
        self.variance = variance
        self.scale = scale  # Scale = horizontal dilation (how "stretched out" the mountains are)

        # Parallax is the distance between the mountains and the camera.
        # It affects how far away mountains
        # appear relative to the camera.
        if parallax <= 0:
            raise ValueError("parallax value must be a positive real number")

        self.parallax = parallax  # 1 = base movement speed, higher values suppress horizontal movement
        # This makes mountains that are further away appear to move slower

        # Cached dictionary of objective heights (not influenced by parallax)
        self.heights: dict[int, float] = {}

    def get_height_at(self, x: float) -> float:
        """
        Samples the noise function at a specific world coordinate.
        snoise2 returns a value between -1.0 and 1.0.
        """
        # We multiply x by scale to move through the noise 'map' slowly
        val = self.heights.get(int(x), None)
        if val is not None:
            return val

        noise_val = snoise2(x * self.scale * self.parallax, self.y * 0.5)
        assert -1 <= noise_val <= 1

        val = noise_val * self.variance + self.y
        return val

    def update_heights(self, displacement: float, vp_w: int) -> None:
        """Update the heights, and discard heights that are very far away from the viewport.
        Discarding heights far away ensures that the memory footprint remains small,
        while caching close heights reduces CPU load from needing to recompute snoise2"""

        # Compute missing heights
        for x in range(int(displacement), int(displacement + vp_w + 1)):
            if x not in self.heights:
                self.heights[x] = self.get_height_at(x)

        # Discard heights that are very far away from the viewport
        for x in list(self.heights.keys()):
            dx = x - displacement

            if not -self.DISCARD_DISTANCE <= dx <= self.DISCARD_DISTANCE:
                del self.heights[x]

class Simulation:
    def __init__(self) -> None:
        tw, th = shutil.get_terminal_size()
        self.buf = Buffer(tw, 2 * (th - 1))
        self.kb = KBInputManager()

        self.car = Car(15, GROUND_HEIGHT + 1, Buffer.load_from_img((DIRS.assets.images / "car.png").path()))
        self.displacement = 0
        self.car_speed = STARTING_CAR_SPEED

        self.mountain_ranges: list[MountainRange] = [
            MountainRange(y=GROUND_HEIGHT + 8, colour=(122, 101, 86), variance=5, scale=0.03, parallax=1.4),
            MountainRange(y=GROUND_HEIGHT + 15, colour=(145, 133, 125), variance=4, scale=0.03, parallax=1.8),
            MountainRange(y=GROUND_HEIGHT + 21, colour=(191, 186, 182), variance=3, scale=0.03, parallax=2.3)
        ]

        # sort by y-coordinate in descending order so that the lowest ones are drawn last
        self.mountain_ranges.sort(key=lambda mountain_range: -mountain_range.y)

    def update(self, dt_s: float, vp_w: int, vp_h: int) -> None:
        self.kb.update()
        for mountain_range in self.mountain_ranges:
            mountain_range.update_heights(self.displacement, vp_w)
        self.displacement += self.car_speed * dt_s

        if (vp_w, vp_h) != self.buf.get_size():
            self.buf.resize_and_clear(vp_w, vp_h)

    def take_input(self, dt_s: float) -> None:
        ACCELERATION = 40  # m s^-2

        if self.kb.is_down(Keys.W):
            self.car_speed += ACCELERATION * dt_s
        elif self.kb.is_down(Keys.S):
            self.car_speed -= ACCELERATION * dt_s

        self.car_speed = clamp(self.car_speed, (-HARD_SPEED_LIMIT, HARD_SPEED_LIMIT))  # Hard speed limit

    def draw(self) -> str:
        self.buf.clear()

        road_phase = -self.displacement % (ROAD_STRIPE_WIDTH * 2)

        buf_width, buf_height = self.buf.get_size()

        vis_road_top = buf_height - ROAD_TOP_HEIGHT
        vis_road_bottom = buf_height - ROAD_BOTTOM_HEIGHT
        assert vis_road_top < vis_road_bottom

        # Draw sky
        for y in range(buf_height):
            row_colour = (*lerp_colours(SKY_COLOUR_TOP, SKY_COLOUR_BOTTOM, y / buf_height), 1)
            self.buf.draw_rect(0, y, buf_width, 1, row_colour)

        # Draw mountains before ground so that they appear behind the ground
        for mountain_range in self.mountain_ranges:
            for screen_x in range(buf_width):
                camera_x = self.displacement / mountain_range.parallax
                world_x = screen_x + camera_x

                h = mountain_range.get_height_at(world_x)
                hL = mountain_range.heights.get(int(world_x - 1), h)
                hR = mountain_range.heights.get(int(world_x + 1), h)

                slope = hR - hL
                shade = clamp(0.5 + slope * 0.1, (0, 1))

                if shade > 0.5:
                    light_strength = (shade - 0.5)
                    base_colour = lerp_colours(mountain_range.colour, tuple(c + 10 for c in mountain_range.colour), light_strength)  # type: ignore
                else:
                    dark_strength = (0.5 - shade)
                    base_colour = lerp_colours(mountain_range.colour, tuple(c - 10 for c in mountain_range.colour), dark_strength)  # type: ignore

                alpha = (1 / mountain_range.parallax) ** 0.5  # **0.5 makes the transparency effect slightly less harsh

                for y in range(int(buf_height - h), buf_height):
                    dark_strength = 4 * (y - (buf_height - h))

                    colour = tuple(c - int(dark_strength) for c in base_colour)
                    assert len(colour) == 3
                    colour = lerp_colours(SKY_COLOUR_TOP, colour, alpha)

                    self.buf.set_pix(screen_x, y, colour)

        # Draw ground and road
        for y in range(buf_height):
            if vis_road_top <= y <= vis_road_bottom:
                row_colour = ROAD_COLOUR
            elif y > buf_height - GROUND_HEIGHT:
                row_colour = GROUND_COLOUR
            else:
                continue
            self.buf.draw_rect(0, y, buf_width, 1, row_colour)

        # Draw road stripes
        for x in range(int(road_phase - ROAD_STRIPE_WIDTH), buf_width + 1, ROAD_STRIPE_WIDTH * 2):
            self.buf.draw_rect(x, buf_height - ROAD_STRIPE_HEIGHT, ROAD_STRIPE_WIDTH, 1, ROAD_STRIPE_COLOUR)

        # Draw car
        self.buf.blit(self.car.image, self.car.x, buf_height - self.car.y)

        return self.buf.render()

import random
from datetime import datetime

def make_speeding_fine(speed_kmh: float, limit_kmh: float) -> str:
    # Load the template
    with open((DIRS.assets / "texts" / "speeding_fine.txt").path(), "r") as f:
        # Filter out lines starting with '#'
        template = "".join(line for line in f if not line.strip().startswith("#"))  # allow comments to be ignored

    # Calculate the variables
    now = datetime.now()
    diff = speed_kmh - limit_kmh

    # Logic for offence and fines based on WA 2026 guidelines (make it realistic!)
    offence_len = 57
    if diff > 40:
        offence = "Exceed speed limit by more than 40 km/h".ljust(offence_len)
        fine_amount = 1200
        demerits = 7
    elif diff > 30:
        offence = "Exceed speed limit by 30 to 40 km/h".ljust(offence_len)
        fine_amount = 800
        demerits = 6
    else:
        offence = "Speeding in a high-speed zone".ljust(offence_len)
        fine_amount = 400
        demerits = 3

    # Create the data dictionary
    # The keys must match the {names} inside the .txt file
    data = {
        "random_ac_segment_0": random.randint(10, 99),
        "random_ac_segment_1": random.randint(100, 999),
        "random_ac_segment_2": random.randint(10, 99),
        "year": now.year,
        "month": f"{now.month:02}",
        "day": f"{now.day:02}",
        "offence": offence,
        "camera_no": random.randint(100, 999),
        "speed": abs(int(speed_kmh)),
        "limit": int(limit_kmh),
        "fine_amount": f"{fine_amount:,.2f}",
        "demerit_points": demerits
    }

    # Finally, perform the substitution
    try:
        return template.format(**data)
    except KeyError as e:
        raise ValueError(f"Error: Missing variable in template: {e}") from e

def run():
    sim = Simulation()
    police_aggro = 0

    # Only activate the "Speeding Ticket" Easter egg once per run, or else it would get annoying
    speeding_ticket_issued = False

    while True:
        dt_s = 1 / FPS

        term_w, term_h = shutil.get_terminal_size()
        vp_w, vp_h = term_w, 2 * (term_h - 1)

        sim.update(dt_s, vp_w, vp_h)
        sim.take_input(dt_s)

        buf_str = sim.draw()

        speed_colour = COL_SPEEDING if abs(sim.car_speed) > SPEED_LIMIT else COL_NORMAL

        speed_diff_km_h = (abs(sim.car_speed) * 3.6) - (SPEED_LIMIT * 3.6)

        if speed_diff_km_h > 20:
            # Rapid flicker if 20km/h over
            if int(time.time() * 10) % 2 == 0:
                speed_colour = "\033[31m"

            # Increment police aggro depending on how much over the limit the user is
            aggro_factor = 0.04  # percentage of full aggro per km/h over

            # Active the "Speeding Ticket" Easter egg if the user goes too fast
            police_aggro += speed_diff_km_h * aggro_factor * dt_s
            police_aggro = clamp(police_aggro, (0, 1))

            if police_aggro >= 1 and not speeding_ticket_issued:
                if chance(0.1):  # 10% chance per frame
                    speeding_ticket_issued = True
                    print("\033[H\033[J", end="")
                    print("You got a speeding fine!", flush=True)
                    time.sleep(2)

                    print("\033[H\033[J", end="")
                    speeding_fine = make_speeding_fine(sim.car_speed * 3.6, SPEED_LIMIT * 3.6)
                    print(speeding_fine)

                    time.sleep(5)
                    continue

        print("\033[H", end='')
        print(buf_str)
        hud_str = f"Distance: {f"{sim.displacement / 1000:.2f}":>7} km | Speed: {speed_colour}{f"{sim.car_speed * 3.6:.0f}":>4}{COL_RESET} km/h"
        print(f"{hud_str} | Press Ctrl-C to conclude your journey.", flush=True)

        time.sleep(dt_s)

def main():
    try:
        print("\033[H\033[J\033[?25l", end="", flush=True)
        run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[H\033[J\033[?25h", end="", flush=True)

if __name__ == "__main__":
    main()
