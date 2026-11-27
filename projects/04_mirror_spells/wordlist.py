"""Read a word list: one word per line, in a plain text file.

Loading is kept apart from the palindrome hunting so either can change
on its own. This module never calls ``sys.exit``: if the file is missing
it lets the ``OSError`` travel up to whoever asked, and *they* decide
what to do (the command line prints a message and quits; a test checks
that the error happened). A library that quits the program for you is
rude.
"""

from pathlib import Path

DEFAULT_WORDS = Path(__file__).resolve().parent / "data" / "2of4brif.txt"


def words_from_text(text: str) -> list[str]:
    """Split text into lowercase words, one per non-blank line.

    A list comprehension builds the new list in one readable line:
    "for each line, keep it stripped and lowercased, if anything's left".
    """
    return [line.strip().lower() for line in text.splitlines() if line.strip()]


def read_words(path: str | Path = DEFAULT_WORDS) -> list[str]:
    """Read a word-per-line file into a list of lowercase words.

    ``with`` closes the file as soon as the block ends, even if reading
    fails halfway. Raises ``OSError`` (such as ``FileNotFoundError``) when
    the file can't be opened.
    """
    with open(path, encoding="utf-8") as word_file:
        return words_from_text(word_file.read())
