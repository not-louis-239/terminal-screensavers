import shutil
import random
import time
import sys

from screensavers.utils.colours import col

CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()-=_+[]{}|:;'<>?,./"
BRIGHTNESS_COLOUR_MAP: dict[float, int] = {
    0.1: 22,
    0.2: 28,
    0.3: 34,
    0.4: 40,
    0.5: 46,
    0.6: 83,
    0.7: 120,
    0.8: 157,
    0.9: 194,
    1.0: 231
}

COL_RESET = "\033[0m"

class TrailParticle:
    def __init__(self, x: int, y: int, lifetime: int):
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.max_lifetime = lifetime

    def update(self):
        self.lifetime -= 1

    def alive(self):
        return self.lifetime > 0

    def brightness(self):
        return max(0.1, self.lifetime / self.max_lifetime)

class Projectile:
    def __init__(self, x: int, y: int, lifetime: int, trail_len: int = 12) -> None:
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.trail_len = trail_len
        self.trail: list[int] = []
        self.alive = True

    def update(self, term_h: int) -> None:
        if not self.alive:
            return

        self.trail.insert(0, self.y)  # record old position
        self.trail = self.trail[:self.trail_len]

        self.y += 1
        self.lifetime -= 1

        if self.lifetime <= 0 or self.y >= term_h:
            self.alive = False

class Screen:
    def __init__(self):
        self.projectiles: list[Projectile] = []
        self.trails: list[TrailParticle] = []

    def update(self, term_w: int, term_h: int):
        for _ in range(2):
            self.projectiles.append(
                Projectile(random.randint(0, term_w - 1), 0, random.randint(0, term_h))
            )

        for p in self.projectiles:
            # spawn trail BEFORE moving
            self.trails.append(TrailParticle(p.x, p.y, lifetime=12))
            p.update(term_h)

        self.projectiles = [p for p in self.projectiles if p.alive]

        for t in self.trails:
            t.update()

        self.trails = [t for t in self.trails if t.alive]

    def draw(self, term_w: int, term_h: int):
        contents = [[' ' for _ in range(term_w)] for _ in range(term_h)]

        for t in self.trails:
            if 0 <= t.y < term_h and 0 <= t.x < term_w:
                b = round(t.brightness(), 1)
                colour = BRIGHTNESS_COLOUR_MAP.get(b, 34)
                contents[t.y][t.x] = col(colour) + random.choice(CHARS)

        for p in self.projectiles:
            if 0 <= p.y < term_h and 0 <= p.x < term_w:
                contents[p.y][p.x] = col(231) + random.choice(CHARS)

        print('\n'.join(''.join(r) for r in contents) + COL_RESET)

def run():
    screen = Screen()
    while True:
        term_w, term_h = shutil.get_terminal_size()

        # viewport width, viewport height
        vp_w, vp_h = term_w, term_h - 1

        screen.update(vp_w, vp_h)

        print("\033[H\033[J", end='')
        screen.draw(vp_w, vp_h)
        print("Press Ctrl-C to exit.")

        time.sleep(0.03)

def main():
    print("\033[H\033[J\033[?25l", end='')
    try:
        run()
    except KeyboardInterrupt:
        pass
    finally:
        print("\033[H\033[J\033[?25h", end='')
    sys.exit(0)

if __name__ == "__main__":
    main()
