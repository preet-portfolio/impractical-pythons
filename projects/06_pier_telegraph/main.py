"""Decode a route-cipher telegram, or send one, at the pier telegraph office.

Most people only need the settings block below: paste in the telegram,
say how many columns and rows the sender used, and type the route.
Then run:

    uv run python projects/06_pier_telegraph/main.py

The same settings can come from the command line instead:

    uv run python projects/06_pier_telegraph/main.py --key "-1 2 -3 4 -5"
    uv run python projects/06_pier_telegraph/main.py --encrypt "Meet me"

The route (the key) has one number per column, counting from 1. A
positive number reads that column top to bottom, a negative one bottom
to top::

    key  -1   2  -3        column 1 up, column 2 down, column 3 up
          ^   |   ^
          |   v   |
"""

import argparse
import sys

from codebook import decode, encode, grid_options, pad
from route import (
    TelegramProblem,
    check_grid,
    decrypt,
    encrypt,
    factors,
    parse_key,
)

# ============================ YOUR TELEGRAM ============================
# The telegram exactly as it arrived: words separated by spaces.
CIPHERTEXT = "11 6 1 2 7 12 13 8 3 4 9 14 15 10 5"

# The grid the sender used. Columns × rows must equal the number of words.
COLS = 5
ROWS = 3

# The route: one number per column, from 1 up. Negative means "read upwards".
KEY = "-1 2 -3 4 -5"
# ======================= End of settings. That's all! ===================


def alternating_key(cols: int) -> list[int]:
    """The classic route: up the first column, down the next, and so on."""
    return [-(n + 1) if n % 2 == 0 else n + 1 for n in range(cols)]


def snugness(option: dict) -> tuple:
    """Sort key for grids: least filler, then the squarest, then widest."""
    cols, rows = option["cols"], option["rows"]
    return option["filler"], abs(cols - rows), -cols


def receive(cipher_text: str, cols: int, rows: int, key_text: str) -> None:
    """Decode a telegram and print what it says, or explain what's wrong."""
    cipher = cipher_text.split()
    print(f"Telegram: {len(cipher)} words")
    fit = ", ".join(map(str, factors(len(cipher)))) or "none"
    print(f"Column counts that fit: {fit}")
    check_grid(len(cipher), cols, rows)
    key = parse_key(key_text, cols)
    words = decrypt(cipher, cols, rows, key)
    print(f"Reading {cols} columns × {rows} rows along route {key}:")
    print(f"  {' '.join(words)}")
    meaning = decode(words)
    if meaning != " ".join(words):
        print(f"With the code book: {meaning}")


def send(text: str, cols: int | None, key_text: str | None) -> None:
    """Code, pad and scramble a message, and print the telegram."""
    coded = encode(text)
    options = grid_options(len(coded))
    if cols is None:  # the snuggest grid: least filler, then the squarest
        option = min(options, key=snugness)
    else:
        option = next((o for o in options if o["cols"] == cols), None)
        if option is None:
            fit = ", ".join(str(o["cols"]) for o in options)
            words = len(coded)
            message = f"{words} words don't fit {cols} columns. Try {fit}."
            raise TelegramProblem(message)
    cols, rows = option["cols"], option["rows"]
    key = parse_key(key_text, cols) if key_text else alternating_key(cols)
    words = pad(coded, cols, rows)
    print(f"Coded: {' '.join(coded)}")
    route = " ".join(map(str, key))
    print(f"Grid: {cols} columns × {rows} rows, route {route}")
    print(f"Telegram: {' '.join(encrypt(words, cols, rows, key))}")


def main(argv: list[str] | None = None) -> None:
    """Decode the settings block's telegram, or what the command line says."""
    parser = argparse.ArgumentParser(description="Route cipher telegrams.")
    parser.add_argument("--cipher", default=CIPHERTEXT, help="telegram")
    parser.add_argument("--cols", type=int, help="columns in the grid")
    parser.add_argument("--rows", type=int, help="rows in the grid")
    parser.add_argument("--key", help='route, like "-1 2 -3"')
    parser.add_argument("--encrypt", metavar="TEXT", help="send a message")
    args = parser.parse_args(argv)

    try:
        if args.encrypt:
            send(args.encrypt, args.cols, args.key)
        else:
            cols = args.cols or COLS
            # Given only the columns, the rows follow from the word count.
            count = len(args.cipher.split())
            rows = args.rows or (ROWS if cols == COLS else count // cols)
            receive(args.cipher, cols, rows, args.key or KEY)
    except TelegramProblem as problem:
        print(f"\nThe office can't do that: {problem}", file=sys.stderr)
        sys.exit(1)  # 1 tells the shell something went wrong


if __name__ == "__main__":
    main()
