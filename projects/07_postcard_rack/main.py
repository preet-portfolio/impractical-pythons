"""Look for a message hidden between the lines of a postcard (or any text).

Usage (from the repo root):

    uv run python projects/07_postcard_rack/main.py --today
    uv run python projects/07_postcard_rack/main.py --lookahead 4
    uv run python projects/07_postcard_rack/main.py --file letter.txt --lookahead 4
    uv run python projects/07_postcard_rack/main.py --text "..." --rule words --lookahead 3
    uv run python projects/07_postcard_rack/main.py --scan
    uv run python projects/07_postcard_rack/main.py --write "meet me by the pier" --position 3

``--lookahead N`` is the book's loop: try 1, 2, ... N letters along and
print every reading, so you can spot the one that makes sense.
``--scan`` tries every rule as well and lets the dictionary pick.
``--write`` goes the other way: it hides a note in a list of Nan's
Scrabble words, one letter per word.
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# The dictionary and the word splitter are shared with other stalls, so
# they live in projects/common. Python only looks next to this file.
sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

# pylint: disable=wrong-import-position
from decency import family_friendly  # noqa: E402
from null_finder import RULES, check_setting, describe, hidden_letters, scan  # noqa: E402
from null_writer import POSITIONS, write_postcard  # noqa: E402
from postcards import postcard_number, todays_postcard  # noqa: E402
from word_gaps import word_set  # noqa: E402
from wordlist import clean_words, read_words  # noqa: E402

# pylint: enable=wrong-import-position


def load_text(path: str) -> str:
    """Read a text file, trimmed of blank space at either end."""
    with open(path, encoding="utf-8") as text_file:
        return text_file.read().strip()


def dictionary() -> set[str]:
    """The shared word list, tidied and with nothing rude in it."""
    return word_set(family_friendly(clean_words(read_words())))


def show_lookahead(text: str, rule: str, lookahead: int) -> None:
    """Print the hidden letters for every offset from 1 to ``lookahead``."""
    check_setting(rule, lookahead)
    for offset in range(1, lookahead + 1):
        print(f"{describe(rule, offset)}: {hidden_letters(text, rule, offset)}")


def show_scan(text: str) -> None:
    """Try every rule and offset and print the readings that make sense."""
    words = dictionary()
    readings = scan(text, words)
    found = [reading for reading in readings if reading["reads"]]
    for reading in found:
        print(f"{reading['setting']}: {' '.join(reading['words'])}")
    if not found:
        best = readings[0] if readings else None
        print("Nothing reads as a message. It may just be a postcard.")
        if best:
            print(f"Closest: {best['setting']}: {' '.join(best['words'])}")


def show_written(note: str, position: int, seed: int | None) -> None:
    """Print a postcard that hides ``note``, and how to find it again."""
    card = write_postcard(note, dictionary(), position, seed)
    print(card)
    print()
    print(f"Hidden in the {describe('punctuation', position)}.")
    print('Check it with --scan --text "..." (paste the card in).')


def show_today(day: date) -> None:
    """Print the postcard at the front of the rack today."""
    card = todays_postcard(day)
    print(f"Postcard No. {postcard_number(day)}, from {card['place']}")
    print(f"To {card['to']}: {card['text']}. From {card['sender']}")
    print("Hunt with --lookahead 4 --rule punctuation (or words, or capitals),")
    print("or let --scan try every setting.")


def main(argv: list[str] | None = None) -> None:
    """Read the text to search, then look ahead or scan it."""
    parser = argparse.ArgumentParser(description="Find a message hidden in a text.")
    parser.add_argument("--file", help="a text file to search")
    parser.add_argument("--text", help="text to search")
    parser.add_argument(
        "--rule", default="punctuation", help=f"where to count from: {', '.join(RULES)}"
    )
    parser.add_argument("--lookahead", type=int, help="try 1 up to this many letters along")
    parser.add_argument("--scan", action="store_true", help="try every rule and offset")
    parser.add_argument("--today", action="store_true", help="today's postcard")
    parser.add_argument("--write", metavar="NOTE", help="hide a note in a postcard")
    parser.add_argument(
        "--position", type=int, default=3, choices=POSITIONS, help="which letter carries the note"
    )
    parser.add_argument("--seed", type=int, help="pick the same words every time")
    args = parser.parse_args(argv)

    try:
        if args.write:
            show_written(args.write, args.position, args.seed)
            return
        if args.file:
            text = load_text(args.file)
        else:
            text = args.text or todays_postcard(date.today())["text"]
        if args.today:
            show_today(date.today())
        elif args.scan:
            show_scan(text)
        else:
            lookahead = 4 if args.lookahead is None else args.lookahead
            show_lookahead(text, args.rule, lookahead)
    except OSError as error:
        print(f"{error}. Check the file name and try again.", file=sys.stderr)
        sys.exit(1)
    except ValueError as problem:
        print(f"The glass can't do that: {problem}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
