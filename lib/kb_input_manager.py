from pynput import keyboard
from enum import StrEnum
import time

class KBInputManager:
    """
    A non-blocking keyboard state tracker using a background thread listener.

    This manager tracks the real-time state of keyboard keys (pressed vs. released)
    to allow for continuous input detection in simulations or games without
    blocking the main execution loop. It handles OS-level key-repeat issues
    by using a set-based architecture.
    Use with Keys.* for checking keys.

    Attributes:
        pressed_keys (set[str]): A collection of currently held keys,
            stored as lowercase strings or normalized special key names.
        listener (pynput.keyboard.Listener): The background thread monitoring
            hardware input events.

    Example:
        >>> # Initialize the manager
        >>> kb = KBInputManager()
        >>>
        >>> # In your main loop
        >>> while True:
        ...     if kb.is_pressed('w'):
        ...         print("Moving forward...")
        ...     if kb.is_pressed(' '): # SPACE key
        ...         print("Jump!")
        ...     if kb.is_pressed('esc'):
        ...         break
    """

    def __init__(self) -> None:
        # Use a set to automatically handle duplicates from key-repeat
        self.pressed_keys: set[str] = set()

        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()

    def on_press(self, key):
        # XXX: .lower() ignores shift for simplicity
        k = self._get_key_str(key)
        if k is not None:
            self.pressed_keys.add(k.lower())

    def on_release(self, key):
        # XXX: .lower() ignores shift for simplicity
        k = self._get_key_str(key)
        if k in self.pressed_keys:
            self.pressed_keys.remove(k.lower())

    def _get_key_str(self, key) -> str | None:
        """Helper to normalize character keys and special keys."""

        # Normal keys, e.g. A-Z, 0-9
        if hasattr(key, 'char') and key.char is not None:
            return key.char

        if key == keyboard.Key.space:
            return "space"
        if key == keyboard.Key.enter:
            return "enter"

        # Fallback for other keys
        return str(key).replace("Key.", "")

    def is_pressed(self, key: Keys) -> bool:
        return key in self.pressed_keys

class Keys(StrEnum):
    # Letters
    A = "a"
    B = "b"
    C = "c"
    D = "d"
    E = "e"
    F = "f"
    G = "g"
    H = "h"
    I = "i"
    J = "j"
    K = "k"
    L = "l"
    M = "m"
    N = "n"
    O = "o"
    P = "p"
    Q = "q"
    R = "r"
    S = "s"
    T = "t"
    U = "u"
    V = "v"
    W = "w"
    X = "x"
    Y = "y"
    Z = "z"

    # Numbers
    k0 = "0"
    k1 = "1"
    k2 = "2"
    k3 = "3"
    k4 = "4"
    k5 = "5"
    k6 = "6"
    k7 = "7"
    k8 = "8"
    k9 = "9"

    # Special-case keys
    SPACE = "space"
    ENTER = "enter"

    # Arrow keys
    UP    = "up"
    DOWN  = "down"
    LEFT  = "left"
    RIGHT = "right"

def _test_kb():
    kb = KBInputManager()

    try:
        while True:
            if kb.is_pressed(Keys.k0):
                print("Key 0 is pressed")
            elif kb.is_pressed(Keys.k1):
                print("Key 1 is pressed")
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received. Exiting now.")

if __name__ == "__main__":
    _test_kb()