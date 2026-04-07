from __future__ import annotations
from math import acos

from .utils import clamp

class IntVector2:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: IntVector2) -> IntVector2:
        return IntVector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: IntVector2) -> IntVector2:
        return IntVector2(self.x - other.x, self.y - other.y)

    def __eq__(self, other: IntVector2) -> bool:
        return self.x == other.x and self.y == other.y

    def __neg__(self) -> IntVector2:
        return IntVector2(-self.x, -self.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f"IntVector2({self.x}, {self.y})"

    def length_sq(self) -> int:
        return self.x ** 2 + self.y ** 2

    def length(self) -> float:
        return self.length_sq() ** 0.5

    def dist_to_sq(self, other: IntVector2) -> int:
        dx_sq = (self.x - other.x) ** 2
        dy_sq = (self.y - other.y) ** 2
        return dx_sq + dy_sq

    def dist_to(self, other: IntVector2) -> float:
        return self.dist_to_sq(other) ** 0.5

    def dot(self, other: IntVector2) -> int:
        return self.x * other.x + self.y * other.y

    def angle_to(self, other: IntVector2) -> float:
        """Returns the angle to another IntVector2 in radians"""

        dot = self.dot(other)
        cos_theta = dot / (self.length_sq() * other.length_sq()) ** 0.5

        # Using length_sq then square-rooting once is more efficient
        return acos(clamp(cos_theta, (-1, 1)))  # clamping ensures that floating-point errors don't crash the script, e.g. 1.0000000001

    def __copy__(self) -> IntVector2:
        return IntVector2(self.x, self.y)

    copy = __copy__

def test():
    v = IntVector2(3, 4)  # 3i + 4j
    print(v.x, v.y)  # Output: 3 4

    u = IntVector2(-1, -2)  # -1i - 2j
    print(u.x, u.y)  # Output: -1 -2

    print("Dot product:", v.dot(u))
    print(f"Angle to: {v.angle_to(u):.2f} rad ({v.angle_to(u) * 180 / 3.14159:.2f} deg)")
    print(f"|v| = {v.length():.2f}")
    print(f"|u| = {u.length():.2f}")
    print(f"Distance: {v.dist_to(u):.2f}")

if __name__ == "__main__":
    test()
