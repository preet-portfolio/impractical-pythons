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


def clean_words(words: list[str], keep: tuple = ("a", "i")) -> list[str]:
    """Tidy a loaded word list without editing the file by hand.

    Some dictionaries list every letter of the alphabet as a "word"
    (a heading for that letter's section). This drops one-letter entries
    except the real words in ``keep``, and removes repeats. ``dict.fromkeys``
    remembers the order keys arrive in, so it de-duplicates while
    keeping the list in its original order.
    """
    wanted = [word for word in words if len(word) > 1 or word in keep]
    return list(dict.fromkeys(wanted))
