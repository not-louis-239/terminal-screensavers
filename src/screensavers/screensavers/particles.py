from __future__ import annotations

import sys
import math
import shutil
import random
from math import sin, cos
from typing import Literal

from src.screensavers.utils.clock import Clock
from src.screensavers.utils.buffer import Buffer
from src.screensavers.utils.utils import chance
from src.screensavers.utils.vectors import Vector2

FPS = 60
PARTICLE_SPAWN_RATE = 5  # rate per second
PARTICLE_SPEED = 40  # pix/s
FLASH_LIFETIME = 0.3

class ParticleColours:
    # Pure data storage, because apparently Pylance hates when you
    # use an Enum without .value, and I don't want .value cluttering
    # the file.
    POS = (100, 230, 255)
    NEG = (255, 200, 100)
    WHITE = (255, 255, 255)

class Particle:
    def __init__(
            self, x: float, y: float,
            bearing_rad: float, charge: Literal[-1, 1],
            invicibility: float = 0.5, lifetime: float = 0.5
        ) -> None:
        self.pos = Vector2(x, y)
        self.bearing_rad = bearing_rad
        self.charge = charge
        self.invicibility = invicibility

    def is_close_to(self, other: Particle) -> bool:
        dist = self.pos.dist_to(other.pos)
        return dist < 1  # 1 unit (square in terminal)

    def update(self, dt_s: float, env_w: float, env_h: float) -> None:
        vel = Vector2(
            x=cos(self.bearing_rad) * PARTICLE_SPEED,
            y=-sin(self.bearing_rad) * PARTICLE_SPEED
        )

        self.pos += vel * dt_s
        self.bearing_rad += random.uniform(-2, 2) * dt_s  # 2π rad/s, random turning

        # Particles wrap around the screen edges
        self.pos = self.pos.wrap(env_w=env_w, env_h=env_h)

        # Decrement invincibility
        self.invicibility = max(0, self.invicibility - dt_s)

class Environment:
    def __init__(self, w: int, h: int) -> None:
        self.clock = Clock()
        self.buf = Buffer(width=w, height=h)

        self.particles: list[Particle] = []
        self.flashes: list[tuple[Vector2, float]] = []  # position, lifetime
        self.w = w
        self.h = h

    def spawn_particle_pair(self) -> None:
        orig_pos = Vector2(
            random.uniform(0, self.w),
            random.uniform(0, self.h)
        )
        base_bearing = random.uniform(0, 2 * math.pi)

        # First, spawn the positive particle
        self.particles.append(
            Particle(
                *orig_pos, bearing_rad=base_bearing, charge=1
            )
        )

        # Then, spawn the negative particle
        self.particles.append(
            Particle(
                *orig_pos, bearing_rad=-base_bearing, charge=-1
            )
        )

    def update(self, dt_s: float) -> None:
        antiparticles = [p for p in self.particles if p.charge == -1]
        particles = [p for p in self.particles if p.charge == 1]

        # Add particles to a "death row" instead of removing instantly
        # This prevents ValueError: list.remove(x): x not in list
        collided: set[Particle] = set()
        collided_pairs: list[tuple[Particle, Particle]] = []

        # Check for collisions and destroy particle-antiparticle pairs if they collide
        for particle in particles:
            for antiparticle in antiparticles:
                if (
                    particle in collided
                    or antiparticle in collided
                ):
                    continue

                if (
                    particle.is_close_to(antiparticle)  # particles are close
                    and particle.invicibility == 0      # particle not invincible
                    and antiparticle.invicibility == 0  # antiparticle not invincible
                ):
                    collided.add(particle)
                    collided.add(antiparticle)
                    collided_pairs.append((particle, antiparticle))

        for particle, antiparticle in collided_pairs:
            collision_pos = (particle.pos + antiparticle.pos) / 2
            self.flashes.append((collision_pos, 0))

        # Remove collided particles from self.particles
        self.particles = [p for p in self.particles if p not in collided]

        # Remove expired flashes
        self.flashes = [(pos, dur + dt_s) for (pos, dur) in self.flashes if dur < FLASH_LIFETIME]

        # Update particles
        for p in self.particles:
            p.update(dt_s=dt_s, env_w=self.w, env_h=self.h)

        # Spawn particles
        num_to_spawn = PARTICLE_SPAWN_RATE * dt_s
        for _ in range(int(num_to_spawn)):
            self.spawn_particle_pair()
        if chance(num_to_spawn % 1):
            self.spawn_particle_pair()

        self.update_buf()

    def update_buf(self) -> None:
        self.buf.clear()
        # Keep track of which pixels we've touched this frame
        occupied: dict[tuple[int, int], int] = {}

        for p in self.particles:
            pos = (int(p.pos.x), int(p.pos.y))

            # Check for overlap and set colours
            if pos in occupied and occupied[pos] != p.charge:
                # This pixel is already taken! Set it to WHITE,
                # only if it is occupied by a pixel of opposite charge
                self.buf.set_pix(*pos, ParticleColours.WHITE)
            else:
                # New pixel, draw normal charge colour
                occupied[pos] = p.charge
                col = ParticleColours.POS if p.charge == 1 else ParticleColours.NEG
                self.buf.set_pix(*pos, col)

        for cpos, _ in self.flashes:
            cx, cy = int(cpos.x), int(cpos.y)
            self.buf.set_pix(cx, cy, ParticleColours.WHITE)

def get_visible_size():
    term_w, term_h = shutil.get_terminal_size()
    return (term_w, 2 * (term_h - 1))

def run():
    env = Environment(*get_visible_size())

    while True:
        dt_s = env.clock.tick(FPS)
        env.update(dt_s=dt_s)

        print("\033[H", end='')
        print(env.buf.render())

        print(f"Press Ctrl-C to exit.", end='', flush=True)

def main():
    try:
        print("\033[H\033[J\033[?25l")
        run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h")
    sys.exit(0)

if __name__ == "__main__":
    main()
