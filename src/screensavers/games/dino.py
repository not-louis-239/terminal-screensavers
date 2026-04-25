import sys
import random
import shutil

from screensavers.utils.utils import chance
from screensavers.utils.vectors import Vector2
from screensavers.utils.clock import Clock
from screensavers.utils.kb_input_manager import KBInputManager, Keys

FPS = 60

DINO_CHAR = "@"
HIGH_OBST_CHAR = ">"
LOW_OBST_CHAR = "#"
GRAVITY = -9.8  # m/s^2
JUMP_IMPULSE = 5  # m/s

def get_visible_area() -> tuple[int, int]:
    tw, th = shutil.get_terminal_size()
    return (tw, th - 1)

class Entity:
    def __init__(self, pos: Vector2, char: str) -> None:
        self.pos = pos
        self.char = char

    def update(self) -> None:
        pass

class Obstacle(Entity):
    def __init__(self, pos: Vector2, char: str) -> None:
        super().__init__(pos, char)

    def update(self, dt_s: float) -> None:
        pass

class Dino(Entity):
    def __init__(self, pos: Vector2, char: str) -> None:
        super().__init__(pos, char)
        self.vel = Vector2(0, 0)

    def update(self, dt_s: float) -> None:
        self.vel_y += GRAVITY * dt_s

        # Make sure he doesn't go through the ground
        self.pos.y = max(0, self.pos.y + self.vel_y * dt_s)

    def jump(self) -> None:
        self.vel_y = JUMP_IMPULSE

class DinoGame:
    def __init__(self) -> None:
        self.kb = KBInputManager()
        self.clock = Clock()

        self.score = 0

        self.dino = Dino(Vector2(0, 0), char=DINO_CHAR)
        self.obstacles: list[Obstacle] = []

    def spawn_obstacle(self, vis_area: tuple[int, int]) -> None:
        if chance(0.6):
            # Spawn ground obstacle
            char = LOW_OBST_CHAR
            y = 0
        else:
            # Spawn airborne obstacle
            char = HIGH_OBST_CHAR
            y = random.randint(4, 6)

        obstacle = Obstacle(Vector2(self.dino.pos.x + vis_area[0]), char=char)
        self.obstacles.append(obstacle)

    def update(self, dt_s: float) -> None:
        self.score += 100 * dt_s
        for obstacle in self.obstacles:
            obstacle.update(dt_s)

    def take_input(self, dt_s: float) -> None:
        if self.kb.went_down(Keys.SPACE):
            self.dino.jump()

    def draw(self, vis_area: tuple[int, int]) -> None:
        # We store entity positions internally as 2d vectors,
        # and adjust for that in the draw() method
        vis_w, vis_h = vis_area

        # the horiz and vert offsets for camera_pos are to make the dino roughly centred visually
        camera_pos = Vector2(self.dino.pos.x - vis_w * 0.25, -vis_h // 2)

        buf: list[list[str]] = [[" "] * vis_w for _ in range(vis_h)]

        # Draw entities
        for obs in self.obstacles:
            obs_screen_y: int = int(vis_h - (obs.pos.y - camera_pos.y))
            obs_screen_x: int = int(obs.pos.x - camera_pos.x)
            buf[obs_screen_y][obs_screen_x] = obs.char

        # Draw dino
        dino_screen_y: int = int(vis_h - (self.dino.pos.y - camera_pos.y))
        dino_screen_x: int = int(self.dino.pos.x - camera_pos.x)

        buf[dino_screen_y][dino_screen_x] = self.dino.char

        print("\n".join("".join(row) for row in buf))

    def run(self) -> None:
        while True:
            vis_area = get_visible_area()
            dt_s = self.clock.tick(FPS)
            self.update(dt_s)
            self.take_input(dt_s)
            self.draw(vis_area=vis_area)

def main() -> None:
    try:
        print("\033[H\033[J\033[?25l")
        DinoGame().run()
    except KeyboardInterrupt:
        pass

    print("\033[H\033[J\033[?25h", end='')
    sys.exit(0)

if __name__ == "__main__":
    main()
