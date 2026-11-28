"""Draw a letter bar chart in the terminal.

Usage (from the repo root):
    uv run python projects/03_letter_bars/main.py "Like a bad penny"
    uv run python projects/03_letter_bars/main.py --sample French
    uv run python projects/03_letter_bars/main.py --compare English Spanish
"""

import argparse
import sys
from pathlib import Path
from pprint import pprint

# The English letter table is shared with Pier Telegraph, so it lives in
# projects/common. Python only looks next to this file by default.
sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

# pylint: disable-next=wrong-import-position
from letter_bars import (  # noqa: E402
    SAMPLES,
    accents,
    bar_chart,
    compare,
    count_letters,
    top_letters,
)


def show_chart(text: str) -> None:
    """Print one text's bars, its top letters and any folded accents."""
    pprint(bar_chart(text), width=110)
    print("Top letters:", top_letters(count_letters(text)))
    found = accents(text)
    if found:
        listed = ", ".join(f"{char} x{n}" for char, n in found.items())
        print("Accents folded in:", listed)


def show_comparison(name_a: str, name_b: str) -> None:
    """Print two samples side by side as percentage bars, a to z."""
    print(f"   {name_a:<20}{name_b}   (one # per 1% of letters)")
    for row in compare(SAMPLES[name_a], SAMPLES[name_b]):
        bar_a = "#" * round(row["a"])
        bar_b = "#" * round(row["b"])
        print(f"{row['letter']}  {bar_a:<20}{bar_b}")


def main(argv: list[str] | None = None) -> None:
    """Chart the given text, a built-in sample, or two samples compared."""
    parser = argparse.ArgumentParser(description="Letter frequency bars.")
    parser.add_argument("text", nargs="*", help="text to chart")
    languages = sorted(SAMPLES)
    parser.add_argument("--sample", choices=languages)
    parser.add_argument("--compare", nargs=2, choices=languages)
    args = parser.parse_args(argv)

    if args.compare:
        show_comparison(*args.compare)
    elif args.sample:
        show_chart(SAMPLES[args.sample])
    elif args.text:
        show_chart(" ".join(args.text))
    else:
        show_chart(input("Type some text: "))


if __name__ == "__main__":
    main()
