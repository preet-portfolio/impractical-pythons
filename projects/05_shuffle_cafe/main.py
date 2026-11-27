"""Find anagrams of a word or name, or build an anagram phrase.

Usage (from the repo root):
    uv run python projects/05_shuffle_cafe/main.py listen
    uv run python projects/05_shuffle_cafe/main.py          # asks you
    uv run python projects/05_shuffle_cafe/main.py "Donkey Rides" --phrase
    uv run python projects/05_shuffle_cafe/main.py emr --shuffle
    uv run python projects/05_shuffle_cafe/main.py --families 5
    uv run python projects/05_shuffle_cafe/main.py Daniel --words my_words.txt
"""

import argparse
import sys
from pathlib import Path

import anagrams
from phrase_session import run_session, show_shuffle

# The word list is shared by several stalls, so it lives in
# projects/common. Python only looks next to this file by default.
sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

# pylint: disable-next=wrong-import-position
from wordlist import DEFAULT_WORDS, clean_words, read_words  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    """Print anagrams, families or shuffles, or build a phrase."""
    parser = argparse.ArgumentParser(description="Find anagrams.")
    parser.add_argument("word", nargs="?", help="a word or name")
    parser.add_argument("--words", default=DEFAULT_WORDS, help="word list")
    parser.add_argument("--families", type=int, metavar="N", help="top N")
    parser.add_argument("--phrase", action="store_true", help="build a phrase")
    parser.add_argument("--shuffle", action="store_true", help="every order")
    args = parser.parse_args(argv)

    try:
        words = clean_words(read_words(args.words))
    except OSError as error:
        print(f"{error}\nCouldn't open the word list.", file=sys.stderr)
        sys.exit(1)

    if args.families:
        families = anagrams.anagram_families(words)
        for family in anagrams.biggest_families(families, args.families):
            print(f"{len(family)}: {', '.join(family)}")
        return

    # No word on the command line? Ask for one, like a café counter would.
    word = args.word or input("Your word or name: ")
    if not anagrams.letters_only(word):
        print("That has no letters to shuffle.")
        return

    if args.shuffle:
        show_shuffle(anagrams.letters_only(word), print)
        return

    if args.phrase:
        run_session(word, words)
        return

    found = anagrams.find_anagrams(word, words)
    if found:
        print(f"Anagrams of {word}:", *found, sep="\n  ")
    else:
        print(f"No anagrams of {word} in this dictionary. Try a nickname?")


if __name__ == "__main__":
    main()
