"""Translate to and from Code-Talk in the terminal.

Usage (from the repo root):
    uv run python projects/02_code_talk/main.py "Meet me at noon"
    uv run python projects/02_code_talk/main.py --decode "Eet-may oon-nay"
    uv run python projects/02_code_talk/main.py   # type lines, Ctrl-D stops
"""

import argparse
import sys

from code_talk import decode, encode


def main(argv: list[str] | None = None) -> None:
    """Translate the text on the command line, or each line typed in."""
    parser = argparse.ArgumentParser(description="Reversible Pig Latin.")
    parser.add_argument("text", nargs="*", help="text to translate")
    parser.add_argument("--decode", action="store_true", help="undo Code-Talk")
    args = parser.parse_args(argv)
    translate = decode if args.decode else encode

    if args.text:
        print(translate(" ".join(args.text)))
        return
    print("Type a line and press Enter. Ctrl-D (or Ctrl-Z, Enter) to stop.")
    for line in sys.stdin:
        print(translate(line.rstrip("\n")))


if __name__ == "__main__":
    main()
