"""Hunt for palindromes ("mirror spells") in a word list.

Usage (from the repo root):
    uv run python projects/04_mirror_spells/main.py
    uv run python projects/04_mirror_spells/main.py "Step on no pets"
    uv run python projects/04_mirror_spells/main.py --pairs
    uv run python projects/04_mirror_spells/main.py --words my_words.txt
"""

import argparse
import sys
from pathlib import Path

from mirror import is_palindrome, spellbook_stats
from palingrams import two_word_spells

# The word list and the filter are shared by several stalls, so they live
# in projects/common. Python only looks next to this file by default.
sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

# pylint: disable-next=wrong-import-position
from wordlist import DEFAULT_WORDS, clean_words, read_words  # noqa: E402


def main(argv: list[str] | None = None) -> None:
    """Test a phrase, or list every palindrome in the word list."""
    parser = argparse.ArgumentParser(description="Find palindromes.")
    parser.add_argument("phrase", nargs="*", help="a word or phrase to test")
    parser.add_argument("--words", default=DEFAULT_WORDS, help="word list")
    parser.add_argument("--pairs", action="store_true", help="two-word spells")
    args = parser.parse_args(argv)

    if args.phrase:
        phrase = " ".join(args.phrase)
        verdict = "is" if is_palindrome(phrase) else "is not"
        print(f'"{phrase}" {verdict} a mirror spell.')
        return

    # Loading can fail (a typo in the path, a missing file), so the
    # problem is caught here, explained on stderr, and the program quits
    # with exit code 1, which tells the shell "this went wrong".
    try:
        words = clean_words(read_words(args.words))
    except OSError as error:
        print(f"{error}\nCouldn't open the word list.", file=sys.stderr)
        sys.exit(1)

    if args.pairs:
        pairs = two_word_spells(words)
        print(*(f"{first} {second}" for first, second in pairs), sep="\n")
        print(f"\n{len(pairs):,} two-word spells in {len(words):,} words.")
        return

    stats = spellbook_stats(words)
    # The * "splats" the list into separate arguments, and sep puts
    # each one on its own line: one print call instead of a loop.
    print(*stats["spells"], sep="\n")
    print(
        f"\n{stats['count']} spells in {stats['words']:,} words "
        f"({stats['percent']:.2f}%). Longest: {', '.join(stats['longest'])}"
    )


if __name__ == "__main__":
    main()
