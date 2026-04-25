# The Pyway - Short for the "Python Highway"
# You just got up and need to cross the street.
# But the street has been invaded by Python exceptions.
# Be careful not to get run over by the ModuleNotFoundErrors!

from dataclasses import dataclass
from typing import Literal
import random
import sys

from screensavers.utils.vectors import Vector2
from screensavers.utils.utils import chance
from screensavers.utils.clock import Clock
from screensavers.utils.kb_input_manager import KBInputManager, Keys

FPS = 60

# Behaviour functions for behaviour dispatch

class Behaviour:
    def update(self, entity: PywayExceptionEntity, dt_s: float) -> None:
        pass

class LinearBehaviour(Behaviour):
    def update(self, entity: PywayExceptionEntity, dt_s: float) -> None:
        entity.pos.x += entity.base_speed * entity.direction * dt_s

class JitterBehaviour(LinearBehaviour):
    JITTER_FACTOR = 0.2
    def update(self, entity: PywayExceptionEntity, dt_s: float) -> None:
        super().update(entity, dt_s)
        entity.pos.y += self.JITTER_FACTOR * dt_s * random.uniform(-entity.base_speed, entity.base_speed)

class DashBehaviour(LinearBehaviour):
    DASH_CHANCE_PER_SECOND = 0.1
    DASH_SPEED_BOOST_FACTOR = 5

    def update(self, entity: PywayExceptionEntity, dt_s: float) -> None:
        super().update(entity, dt_s)
        if chance(dt_s * self.DASH_CHANCE_PER_SECOND):
            entity.speed *= self.DASH_SPEED_BOOST_FACTOR
        entity.speed = max(entity.speed * (0.5 ** dt_s), entity.base_speed)

# Exception types

@dataclass(kw_only=True)
class PywayExceptionType:
    name: str
    speed_range: tuple[float, float]  # percentage of terminal screen per second
    behaviour: Behaviour

class PywayExceptionEntity:
    def __init__(self, pos: Vector2, typ: PywayExceptionType, base_speed: float, direction: Literal[-1, 1]) -> None:
        self.pos = pos
        self.typ = typ
        self.base_speed = base_speed
        self.direction = direction
        self.speed = base_speed

    def clone(self) -> PywayExceptionEntity:
        assert self.direction in (-1, 1)
        return PywayExceptionEntity(
            pos=self.pos.copy(),
            typ=self.typ,
            base_speed=self.base_speed,
            direction=self.direction
        )

EXCEPTION_TYPES = [
    PywayExceptionType(
        name="ModuleNotFoundError",
        speed_range=(0.1, 0.3),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="ZeroDivisionError",
        speed_range=(0.5, 1.0),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="SyntaxError",
        speed_range=(0.2, 0.4),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="IndexError",
        speed_range=(0.3, 0.8),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="TypeError",
        speed_range=(0.4, 0.9),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="AttributeError",
        speed_range=(0.2, 0.6),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="KeyError",
        speed_range=(0.3, 0.7),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="NameError",
        speed_range=(0.1, 0.5),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="RecursionError",
        speed_range=(0.05, 0.2),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="MemoryError",
        speed_range=(0.6, 1.2),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="OverflowError",
        speed_range=(0.7, 1.3),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="KeyboardInterrupt",
        speed_range=(0.8, 1.6),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="AssertionError",
        speed_range=(0.4, 1.0),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="IndentationError",
        speed_range=(0.2, 0.5),
        behaviour=LinearBehaviour()
    ),
    PywayExceptionType(
        name="FloatingPointError",
        speed_range=(0.6, 1.4),
        behaviour=LinearBehaviour()
    )
]

class Player:
    def __init__(self, pos: Vector2) -> None:
        self.pos = pos

class Pyway:
    def __init__(self) -> None:
        self.kb = KBInputManager()
        self.clock = Clock()

    def update(self, dt_s: float) -> None:
        self.kb.update()

    def take_input(self, dt_s: float) -> None:
        if self.kb.is_down(Keys.W):
            ...
        if self.kb.is_down(Keys.S):
            ...
        if self.kb.is_down(Keys.A):
            ...
        if self.kb.is_down(Keys.D):
            ...

    def render(self) -> str:
        ...

def main():
    try:
        print("\033[H\033[J\033[?25l")
        pyway = Pyway()

        while True:
            dt_s = pyway.clock.tick(FPS)
            pyway.update(dt_s)
            pyway.take_input(dt_s)
            print(pyway.render())
            print("Press Ctrl-C to exit.", end="", flush=True)
    except KeyboardInterrupt:
        pass

    print("\033[?25h\033[H\033[J", end='')
    sys.exit(0)

if __name__ == "__main__":
    main()
