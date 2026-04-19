import time

class Clock:
    def __init__(self):
        """
        Sleep for and then return a specified duration

        example usage:

        >>> running = True
        >>> clock = Clock()
        >>> while running:
        ...     dt_s = clock.tick(FPS)
        ...     game.update(dt_s)
        ...     game.take_input(dt_s)
        """

        self.last_time = time.perf_counter()

    def tick(self, fps: int) -> float:
        target_period = 1.0 / fps
        current_time = time.perf_counter()

        # How long did the actual logic take?
        work_time = current_time - self.last_time

        # Calculate how much of the frame is left to sleep
        sleep_time = target_period - work_time

        if sleep_time > 0:
            time.sleep(sleep_time)

        # Update trackers
        now = time.perf_counter()
        dt_s = now - self.last_time
        self.last_time = now
        return dt_s
