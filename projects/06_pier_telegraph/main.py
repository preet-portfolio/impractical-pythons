"""Decode a route-cipher telegram, or send one, at the pier telegraph office.

Most people only need the settings block below: paste in the telegram,
say how many columns and rows the sender used, and type the route.
Then run:

    uv run python projects/06_pier_telegraph/main.py

The same settings can come from the command line instead:

    uv run python projects/06_pier_telegraph/main.py --key "-1 2 -3 4 -5"
    uv run python projects/06_pier_telegraph/main.py --encrypt "Meet me"
    uv run python projects/06_pier_telegraph/main.py --today
    uv run python projects/06_pier_telegraph/main.py --night-clerk --hunch "at BUCKET"
    uv run python projects/06_pier_telegraph/main.py --rail "Meet me at noon"
    uv run python projects/06_pier_telegraph/main.py --crack-rails

The route (the key) has one number per column, counting from 1. A
positive number reads that column top to bottom, a negative one bottom
to top::

    key  -1   2  -3        column 1 up, column 2 down, column 3 up
          ^   |   ^
          |   v   |
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# The word list and the English letter table are shared by several
# stalls, so they live in projects/common. Python only looks next to
# this file by default.
sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

# pylint: disable=wrong-import-position
import rail_fence  # noqa: E402
from codebook import decode, encode, grid_options, pad, snuggest  # noqa: E402
from dispatches import todays_dispatch  # noqa: E402
from night_clerk import crack_rails, crack_route  # noqa: E402
from route import (  # noqa: E402
    TelegramProblem,
    check_grid,
    decrypt,
    encrypt,
    factors,
    parse_key,
)
from sniff import verdict  # noqa: E402
from word_gaps import split_words, word_set  # noqa: E402
from wordlist import read_words  # noqa: E402

# pylint: enable=wrong-import-position

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
    if not options:  # 2 words: a 2 × 1 or 1 × 2 rack hides nothing
        raise TelegramProblem("A telegram needs at least three words.")
    if cols is None:  # the snuggest grid: least filler, then the squarest
        option = snuggest(options)
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


def show_today(day: date) -> None:
    """Print the telegram waiting on the counter today, ready to crack."""
    today = todays_dispatch(day)
    words, cols, rows = today["words"], today["cols"], today["rows"]
    cipher = encrypt(words, cols, rows, today["key"])
    print(f"Telegram No. {today['number']}: {' '.join(cipher)}")
    fit = ", ".join(map(str, factors(len(cipher))))
    print(f"{len(cipher)} words. Column counts that fit: {fit}")
    print('Crack it with --cipher "..." --cols N --key "..."')


def todays_cipher(day: date) -> list[str]:
    """Today's telegram as it arrives, scrambled."""
    today = todays_dispatch(day)
    return encrypt(today["words"], today["cols"], today["rows"], today["key"])


def show_night_clerk(cipher: list[str], hunches: list[str]) -> None:
    """Brute-force a route telegram and print the best five readings."""
    pairs = []
    for hunch in hunches:
        pair = hunch.split()
        if len(pair) != 2:
            message = (
                f'A hunch is two words that sit side by side, like "ice cream", not "{hunch}".'
            )
            raise TelegramProblem(message)
        pairs.append(pair)
    result = crack_route(cipher, pairs)
    print(f"The night clerk tried {result['tried']:,} routes.")
    if pairs:
        print(f"{result['fit']:,} of them fit your hunches.")
        if not result["fit"]:
            print("Check the spelling, or drop a hunch: one of them must be wrong.")
    for rank, best in enumerate(result["best"], 1):
        route = " ".join(map(str, best["key"]))
        print(f"{rank}. {best['cols']} × {best['rows']}, route {route} (score {best['score']})")
        print(f"   {' '.join(best['words'])}")
    if not pairs:
        print('Add a hunch or two (--hunch "ice cream") to narrow it down.')


def show_rails(cipher: str, rails: int) -> None:
    """Read a rail fence telegram and put the gaps back."""
    letters = rail_fence.decrypt(cipher, rails)
    print(f"Off the rails: {letters}")
    print(f"With the gaps back: {' '.join(split_words(letters, word_set(read_words())))}")


def show_crack_rails(cipher: str) -> None:
    """Try every rail count on a rail fence telegram."""
    result = crack_rails(cipher, word_set(read_words()))
    for reading in result["readings"]:
        star = "  <- reads best" if reading["rails"] == result["best"] else ""
        share = f"{reading['coverage']:.0%}"
        print(f"{reading['rails']} rails: {share:>4} real words  {reading['letters']}{star}")


def show_sniff(text: str) -> None:
    """Say whether a telegram looks shuffled or swapped, and why."""
    result = verdict(text)
    print(
        f"{result['verdict'].capitalize()} ({result['letters']} letters, score {result['score']})"
    )
    print(result["reason"])


def main(argv: list[str] | None = None) -> None:
    """Decode the settings block's telegram, or what the command line says."""
    parser = argparse.ArgumentParser(description="Route cipher telegrams.")
    parser.add_argument("--cipher", default=CIPHERTEXT, help="telegram")
    parser.add_argument("--cols", type=int, help="columns in the grid")
    parser.add_argument("--rows", type=int, help="rows in the grid")
    parser.add_argument("--key", help='route, like "-1 2 -3"')
    parser.add_argument("--encrypt", metavar="TEXT", help="send a message")
    parser.add_argument("--today", action="store_true", help="today's puzzle")
    parser.add_argument("--night-clerk", action="store_true", help="brute-force today's telegram")
    parser.add_argument(
        "--hunch", action="append", default=[], help='two words side by side, like "ice cream"'
    )
    parser.add_argument("--rail", metavar="TEXT", help="send a rail fence telegram")
    parser.add_argument("--unrail", metavar="CIPHER", help="read a rail fence telegram")
    parser.add_argument("--rails", type=int, default=2, help="rails (default 2)")
    parser.add_argument(
        "--crack-rails",
        nargs="?",
        const=rail_fence.intercepted(),
        metavar="CIPHER",
        help="try every rail count (default: the intercepted telegram)",
    )
    parser.add_argument("--sniff", metavar="TEXT", help="shuffled or swapped?")
    args = parser.parse_args(argv)

    try:
        if args.night_clerk:
            show_night_clerk(todays_cipher(date.today()), args.hunch)
        elif args.rail:
            print(rail_fence.in_fives(rail_fence.encrypt(args.rail, args.rails)))
        elif args.unrail:
            show_rails(args.unrail, args.rails)
        elif args.crack_rails:
            show_crack_rails(args.crack_rails)
        elif args.sniff:
            show_sniff(args.sniff)
        elif args.today:
            show_today(date.today())
        elif args.encrypt:
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
