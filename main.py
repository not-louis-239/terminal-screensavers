"""
main.py

Used for routing the arg passed in to the correct executable screensaver
"""

import runpy
import sys
from pathlib import Path

SCREENSAVERS_DIR = Path(__file__).parent / "screensavers"
screensaver_files: dict[str, Path] = {}
for fp in SCREENSAVERS_DIR.rglob("*.py"):
    screensaver_files[fp.stem] = fp

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <screensaver_name>")
        print("\nAvailable screensavers: ")
        for name in screensaver_files.keys():
            print(name)
        sys.exit(1)
    else:
        screensaver_name = sys.argv[1]
        if screensaver_name not in screensaver_files:
            print(f"No screensaver named '{screensaver_name}'.")
            sys.exit(1)
        else:
            fp = screensaver_files[screensaver_name]
            runpy.run_path(str(fp), run_name="__main__")

if __name__ == "__main__":
    main()