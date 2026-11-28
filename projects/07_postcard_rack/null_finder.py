"""Find a message hidden in plain sight: a null cipher.

A null cipher doesn't scramble anything. The real message sits inside
an ordinary-looking letter, one letter at a time, at places only the
sender and reader agreed on. Everything else is padding (the "nulls").
Hiding that a message exists at all is called **steganography**.

The classic rule counts from punctuation: after each mark, skip to the
Nth letter and write it down. Three rules decide the awkward cases:

1. every punctuation mark starts the count again from zero;
2. so a second mark before you reach N restarts it;
3. punctuation itself is never part of the message.

Spaces don't count at all. Nothing is counted before the first mark.

The other rules here are simpler: the Nth letter of every word, or the
Nth letter of every word that starts with a capital.
"""

import re
import string
from collections.abc import Callable

from word_gaps import split_words

LETTER_WORD = re.compile(r"[A-Za-z]+")
SHORTEST = 6  # fewer picked letters than this could read as words by luck
# A reading counts as a message when nearly all of it is real words and
# those words average at least this many letters. Chance makes plenty of
# "a", "at" and "me", but rarely "under" or "gnome".
READS_COVERAGE = 0.95
READS_WORD_LENGTH = 3.0


def strip_spaces(text: str) -> str:
    """Join the text up with every space, tab and newline taken out."""
    return "".join(text.split())


def after_punctuation(text: str, offset: int) -> list[int]:
    """Where the letters are that sit ``offset`` places after punctuation.

    This is the book's loop, but it returns *positions* in the original
    text rather than letters, so a page can light up the exact letters.
    Spaces are stepped over without counting, which is the same as
    stripping them first.
    """
    picked, count, found_first = [], 0, False
    for i, char in enumerate(text):
        if char.isspace():
            continue
        if char in string.punctuation:
            count, found_first = 0, True
        elif found_first:
            count += 1
            if count == offset:
                picked.append(i)
    return picked


def word_letters(text: str, offset: int, capitals_only: bool = False) -> list[int]:
    """Where the ``offset``-th letter of each word is (words too short have none)."""
    picked = []
    for word in LETTER_WORD.finditer(text):
        if capitals_only and not word.group()[0].isupper():
            continue
        if len(word.group()) >= offset:
            picked.append(word.start() + offset - 1)
    return picked


def of_each_word(text: str, offset: int) -> list[int]:
    """The ``offset``-th letter of every word."""
    return word_letters(text, offset)


def of_capital_words(text: str, offset: int) -> list[int]:
    """The ``offset``-th letter of every word that starts with a capital."""
    return word_letters(text, offset, capitals_only=True)


# Each rule: a name the page shows, and the function that finds positions.
RULES: dict[str, Callable[[str, int], list[int]]] = {
    "punctuation": after_punctuation,
    "words": of_each_word,
    "capitals": of_capital_words,
}

DESCRIBE = {
    "punctuation": "letter after each punctuation mark",
    "words": "letter of every word",
    "capitals": "letter of every capitalised word",
}


def check_setting(rule: str, offset: int) -> None:
    """Raise ``ValueError`` with a plain reason for a setting that can't work."""
    if rule not in RULES:
        raise ValueError(f"There's no rule called {rule!r}. Try {', '.join(RULES)}.")
    if offset < 1:
        raise ValueError("Count from 1: the first letter is 1.")


def picked_positions(text: str, rule: str, offset: int) -> list[int]:
    """Where the hidden letters are, for one rule and offset."""
    check_setting(rule, offset)
    return RULES[rule](text, offset)


def hidden_letters(text: str, rule: str, offset: int) -> str:
    """The hidden letters themselves, in lower case."""
    return "".join(text[i] for i in picked_positions(text, rule, offset)).lower()


def describe(rule: str, offset: int) -> str:
    """A setting in plain words: "3rd letter after each punctuation mark"."""
    ordinal = {1: "1st", 2: "2nd", 3: "3rd"}.get(offset, f"{offset}th")
    return f"{ordinal} {DESCRIBE[rule]}"


def read_reading(letters: str, words: set[str]) -> dict:
    """Split picked letters into words and say how well they read.

    Returns ``{"words", "coverage", "word_length", "reads"}``:
    ``coverage`` is the share of letters inside real words, and
    ``word_length`` the average length of those words.
    """
    parts = split_words(letters, words)
    real = [part for part in parts if not part.isupper()]
    covered = sum(len(part) for part in real)
    coverage = covered / len(letters) if letters else 0.0
    word_length = covered / len(real) if real else 0.0
    reads = (
        len(letters) >= SHORTEST and coverage >= READS_COVERAGE and word_length >= READS_WORD_LENGTH
    )
    return {"words": parts, "coverage": coverage, "word_length": word_length, "reads": reads}


def scan(text: str, words: set[str], most: int = 6) -> list[dict]:
    """Try every rule and offset up to ``most``, best reading first.

    This is the book's "lookahead" loop, widened to every rule. Each
    reading is scored by how much of it splits into real words, then by
    how long those words are: the right setting reads "key under gnome",
    a wrong one reads alphabet soup or a string of little words ("at men
    a"). Readings shorter than ``SHORTEST`` letters are left out.

    Returns a list of ``{"rule", "offset", "setting", "letters",
    "words", "coverage", "word_length", "reads"}``.
    """
    readings = []
    for rule in RULES:
        for offset in range(1, most + 1):
            letters = hidden_letters(text, rule, offset)
            if len(letters) < SHORTEST:
                continue
            reading = {"rule": rule, "offset": offset, "setting": describe(rule, offset)}
            reading |= {"letters": letters} | read_reading(letters, words)
            readings.append(reading)
    return sorted(readings, key=lambda r: (-r["reads"], -r["coverage"], -r["word_length"]))
