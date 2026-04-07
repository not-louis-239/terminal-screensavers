def col(code: int, bg: bool = False) -> str:
    return f"\033[{48 if bg else 38};5;{code}m"

# Colourless formatting options
FAINT = "\033[2m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
INVERTED = "\033[7m"
STRIKE = "\033[9m"

COL_RESET = "\033[0m"

def show_palette() -> None:
    for i in range(16):
        for j in range(16):
            idx = i * 16 + j
            print(f"{col(idx)}{idx:03}", end=" ")
        print()

if __name__ == "__main__":
    show_palette()