from __future__ import annotations

from typing import Iterator
from math import acos

from .utils import clamp, lerp

class Vector2:
    def __init__(self, x: float = 0, y: float = 0) -> None:
        self.x = x
        self.y = y

    def _is_zero(self) -> bool:
        return self.x == 0 and self.y == 0

    # Arithmetic overloads
    def __add__(self, other: Vector2) -> Vector2:
        # Using type(self) ensures that if an IntVector2 adds something,
        # it tries to stay an IntVector2 where possible.
        return type(self)(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2) -> Vector2:
        return type(self)(self.x - other.x, self.y - other.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2):
            return False
        return self.x == other.x and self.y == other.y

    def __neg__(self) -> Vector2:
        return type(self)(-self.x, -self.y)

    def __mul__(self, scalar: float) -> Vector2:
        return type(self)(
            self.x * scalar,
            self.y * scalar
        )

    def __truediv__(self, scalar: float) -> Vector2:
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide a vector by zero")
        return self * (1 / scalar)

    # Hashing, representation and copying
    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.x}, {self.y})"

    def __copy__(self) -> Vector2:
        return type(self)(self.x, self.y)
    copy = __copy__

    def __iter__(self) -> Iterator[float]:
        return iter((self.x, self.y))

    # Vector-specific operations
    def length_sq(self) -> float:
        return self.x ** 2 + self.y ** 2

    def length(self) -> float:
        return self.length_sq() ** 0.5

    def dist_to_sq(self, other: Vector2) -> float:
        dx_sq = (self.x - other.x) ** 2
        dy_sq = (self.y - other.y) ** 2
        return dx_sq + dy_sq

    def dist_to(self, other: Vector2) -> float:
        return self.dist_to_sq(other) ** 0.5

    def dot(self, other: Vector2) -> float:
        return self.x * other.x + self.y * other.y

    def normalise(self) -> Vector2:
        """Returns the unit vector of self."""
        length = self.length()
        if length == 0:
            raise ValueError("cannot normalise a zero vector")
        return self / length

    def angle_to(self, other: Vector2) -> float:
        """
        Returns the angle to another Vector2 in radians

        Uses the dot product formula

           v.u = |v||u| * cos(theta)
        => theta = arccos(v.u / |v||u|)
        """

        if self._is_zero() or other._is_zero():
            raise ValueError("angle_to is undefined for zero vectors")

        dot = self.dot(other)
        cos_theta = dot / (self.length_sq() * other.length_sq()) ** 0.5

        # Using length_sq then square-rooting once is more efficient
        return acos(clamp(cos_theta, (-1, 1)))  # clamping ensures that floating-point errors don't crash the script, e.g. 1.0000000001

    def wrap(self, env_w: float, env_h: float) -> Vector2:
        """Wraps the vector within the given environment bounds"""
        return Vector2(
            self.x % env_w,
            self.y % env_h
        )

class Vector3:
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    def _is_zero(self) -> bool:
        return self.x == 0 and self.y == 0 and self.z == 0

    def __add__(self, other: Vector3) -> Vector3:
        return Vector3(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __sub__(self, other: Vector3) -> Vector3:
        return Vector3(
            self.x - other.x,
            self.y - other.y,
            self.z - other.z
        )

    def __mul__(self, scalar: float) -> Vector3:
        return Vector3(
            self.x * scalar,
            self.y * scalar,
            self.z * scalar
        )

    def __truediv__(self, scalar: float) -> Vector3:
        return self * (1 / scalar)

    def __neg__(self) -> Vector3:
        return Vector3(-self.x, -self.y, -self.z)

    def length_sq(self) -> float:
        return (self.x ** 2 + self.y ** 2 + self.z ** 2)

    def length(self) -> float:
        return self.length_sq() ** 0.5

    def normalise(self) -> Vector3:
        length = self.length()
        if length == 0:
            raise ValueError("Cannot normalise a zero vector.")
        return self / length

    def lerp(self, other: Vector3, t: float) -> Vector3:
        return Vector3(
            lerp(self.x, other.x, t),
            lerp(self.y, other.y, t),
            lerp(self.z, other.z, t)
        )

class IntVector2(Vector2):
    def __init__(self, x: int = 0, y: int = 0) -> None:
        # Force cast to int to maintain "Integer Semantics"
        super().__init__(int(x), int(y))

    def __repr__(self) -> str:
        return f"IntVector2({self.x}, {self.y})"

    def __hash__(self) -> int:
        return hash((self.x, self.y))

DIRS_NEIGH4: tuple[Vector2, ...] = (
    Vector2(-1, 0),
    Vector2(1, 0),
    Vector2(0, 1),
    Vector2(0, -1)
)

DIRS_DIAG4: tuple[Vector2, ...] = tuple(Vector2(dx, dy) for dx in (-1, 1) for dy in (-1, 1))

DIRS_NEIGH8: tuple[Vector2, ...] = DIRS_NEIGH4 + DIRS_DIAG4

def test():
    v = Vector2(3, 4)  # 3i + 4j
    print(v.x, v.y)  # Output: 3 4

    u = Vector2(-1, -2)  # -1i - 2j
    print(u.x, u.y)  # Output: -1 -2

    print("Dot product:", v.dot(u))
    print(f"Angle to: {v.angle_to(u):.2f} rad ({v.angle_to(u) * 180 / 3.14159:.2f} deg)")
    print(f"|v| = {v.length():.2f}")
    print(f"|u| = {u.length():.2f}")
    print(f"Distance: {v.dist_to(u):.2f}")

if __name__ == "__main__":
    test()
