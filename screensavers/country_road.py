"""
country_road.py

Experience a road trip, right from your terminal!
"""

import time

from lib.custom_types import Colour

FPS = 60

class Car:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

class MountainRange:
    def __init__(self, height: int, colour: Colour):
        self.height = height
        self.colour = colour

class CountryRoad:
    def __init__(self, width: int, height: int):
        ...

    def update(self, dt_s: float) -> None:
        ...

def run():
    while True:
        print("Press Ctrl-C to exit.", flush=True)

        time.sleep(1 / FPS)

def main():
    try:
        print("\033[H\033[J\033[?25l", end="", flush=True)
        run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[H\033[J\033[?25l", end="", flush=True)

if __name__ == "__main__":
    main()
