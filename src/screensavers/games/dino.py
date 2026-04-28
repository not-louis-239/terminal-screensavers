import sys
import random
import shutil

from screensavers.utils.utils import chance
from screensavers.utils.vectors import Vector2
from screensavers.utils.clock import Clock
from screensavers.utils.kb_input_manager import KBInputManager, Keys

FPS = 60

OBS_SPAWN_RATE = 1.2  # per second
OBS_SPAWN_COOLDOWN = 0.25  # for this many seconds after an obstacle spawns, no more obstacles can spawn

DINO_CHAR = "@"
HIGH_OBST_CHAR = ">"
LOW_OBST_CHAR = "#"

GRAVITY = -200  # m/s^2
JUMP_IMPULSE = 35  # m/s

BASE_SPEED = 10
MAX_SPEED = 150
SPEED_PER_SCORE = 0.08  # m s^-1 score^-1

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
        # Obstacles don't move
        pass

class Dino(Entity):
    def __init__(self, pos: Vector2, char: str) -> None:
        super().__init__(pos, char)
        self.vel = Vector2(0, 0)

    def update(self, dt_s: float) -> None:
        self.vel.y += GRAVITY * dt_s

        # Apply movement
        self.pos.y += self.vel.y * dt_s
        self.pos.x += self.vel.x * dt_s

        # Clamp to ground
        if self.pos.y <= 0:
            self.pos.y = 0
            if self.vel.y < 0:
                self.vel.y = 0

    def jump(self) -> None:
        self.vel.y = JUMP_IMPULSE

class DinoGame:
    def __init__(self) -> None:
        self.kb = KBInputManager()
        self.clock = Clock()

        self.score = 0
        self.game_over = False

        self.dino = Dino(Vector2(0, 0), char=DINO_CHAR)
        self.obstacles: list[Obstacle] = []
        self.obs_spawn_cooldown: float = 0

    def _draw_text_to_buf(self, buf: list[list[str]], text: str, pos:tuple[int, int]) -> None:
        start_x, start_y = pos
        buf_w, buf_h = len(buf[0]), len(buf)

        for i, c in enumerate(text):
            x, y = start_x + i, start_y
            if 0 <= x < buf_w and 0 <= y < buf_h:
                buf[y][x] = c

    def reset(self) -> None:
        self.game_over = False
        self.score = 0
        self.obs_spawn_cooldown = 0
        self.dino.pos.clear()
        self.dino.vel.clear()
        self.obstacles.clear()

    def spawn_obstacle(self, vis_area: tuple[int, int]) -> None:
        if chance(0.6):
            # Spawn ground obstacle
            char = LOW_OBST_CHAR
            y = 0
        else:
            # Spawn airborne obstacle
            char = HIGH_OBST_CHAR
            y = random.randint(1, 4)

        obstacle = Obstacle(Vector2(self.dino.pos.x + vis_area[0], y), char=char)
        self.obstacles.append(obstacle)

    def update(self, dt_s: float, vis_area: tuple[int, int]) -> None:
        self.kb.update()

        if self.game_over:
            return

        self.score += 10 * dt_s
        self.dino.update(dt_s)
        self.dino.vel.x = min(MAX_SPEED, BASE_SPEED + SPEED_PER_SCORE * self.score)

        self.obs_spawn_cooldown -= dt_s
        if self.obs_spawn_cooldown <= 0 and chance(OBS_SPAWN_RATE * dt_s):
            self.spawn_obstacle(vis_area=vis_area)
            self.obs_spawn_cooldown = OBS_SPAWN_COOLDOWN

        for obstacle in self.obstacles:
            obstacle.update(dt_s)
            obstacle_hitbox_r_sq = 0.5 ** 2  # m
            if obstacle.pos.dist_to_sq(self.dino.pos) < obstacle_hitbox_r_sq:
                self.game_over = True

    def take_input(self, dt_s: float) -> None:
        if self.kb.went_down(Keys.SPACE):
            if not self.game_over:
                if self.dino.pos.y <= 0:
                   self.dino.jump()

        if self.kb.went_down(Keys.ENTER) and self.game_over:
            self.reset()

    def draw(self, vis_area: tuple[int, int]) -> None:
        # We store entity positions internally as 2d vectors,
        # and adjust for that in the draw() method
        vis_w, vis_h = vis_area

        buf: list[list[str]] = [[" "] * vis_w for _ in range(vis_h)]

        # the horiz and vert offsets for camera_pos are to make the dino roughly centred visually
        camera_pos = Vector2(self.dino.pos.x - vis_w * 0.25, -vis_h // 2)

        # Draw ground
        ground_screen_y = int(vis_h + camera_pos.y) + 1
        for x in range(vis_w):
            buf[ground_screen_y][x] = "-"

        # Draw entities
        for obs in self.obstacles:
            obs_screen_y: int = int(vis_h - (obs.pos.y - camera_pos.y))
            obs_screen_x: int = int(obs.pos.x - camera_pos.x)

            if 0 <= obs_screen_x < vis_w and 0 <= obs_screen_y < vis_h:
                # Draw obstacle
                buf[obs_screen_y][obs_screen_x] = obs.char

        # Draw dino
        dino_screen_y: int = int(vis_h - (self.dino.pos.y - camera_pos.y))
        dino_screen_x: int = int(self.dino.pos.x - camera_pos.x)

        buf[dino_screen_y][dino_screen_x] = self.dino.char

        # Show score
        score_str = f"{int(self.score):07d}"
        self._draw_text_to_buf(buf=buf, text=score_str, pos=(vis_w // 2, 3))

        # Game over
        if self.game_over:
            self._draw_text_to_buf(buf=buf, text="GAME   OVER", pos=(vis_w // 2 - 2, 2))
            self._draw_text_to_buf(buf=buf, text="Press Enter to restart", pos=(vis_w // 2 - 7, 5))

        print("\n".join(""     .join(row) for row in buf))

    def run(self) -> None:
        while True:
            vis_area = get_visible_area()
            dt_s = self.clock.tick(FPS)
            self.take_input(dt_s)
            self.update(dt_s, vis_area=vis_area)

            try:
                self.draw(vis_area=vis_area)
                print(f"Press Ctrl+C to quit.", end='', flush=True)
            except IndexError:
                print("\033[H\033[J")
                print("Your screen is too small to render right now. Please increase your screen size.", end='', flush=True)

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
