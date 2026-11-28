"""The rail fence: a field cipher that shuffles letters, not words.

Write the message's letters in a zigzag, down and up between two
"rails", then send the top rail followed by the bottom rail::

    L T S R S T E I R       top rail:    LTSRSTEIR
     E U C O S H P E        bottom rail: EUCOSHPE

"Let us cross the pier" goes out as LTSRS TEIRE UCOSH PE.

Nothing is swapped for anything else, so every letter of the message is
still there: it's a *transposition*, like the route cipher, only
letter by letter. Spaces, capitals and punctuation are dropped first
(they'd give the game away), and the result goes out in groups of five.

Senders on the pier always use two rails. The functions take any number
of rails, though, because whoever intercepts a rail telegram doesn't
know how many were used and has to try them all.
"""

import math
import string
import unicodedata
from itertools import zip_longest

from route import TelegramProblem

# Our own messages to send down the rails.
RAIL_SAMPLES = [
    "Let us cross the pier at low tide and meet by the carousel",
    "Bring two spades the treasure is under the bandstand",
    "The seagulls are watching so act natural",
]

# A telegram the office intercepted. Nobody knows how many rails it used.
# (It was three. The page lets visitors find that out for themselves.)
INTERCEPT_RAILS = 3
INTERCEPT = "The penguins have escaped from the aquarium and are waiting in line for chips"


class RailProblem(TelegramProblem):
    """A message the rail fence can't carry (no letters, or too few)."""


def prepare(text: str) -> str:
    """Keep only the letters, in capitals, with accents taken off.

    ``unicodedata.normalize("NFKD", ...)`` splits é into e plus a
    separate accent mark, so the mark can be dropped and the e kept.
    """
    plain = unicodedata.normalize("NFKD", text).upper()
    return "".join(char for char in plain if char in string.ascii_uppercase)


def check_rails(length: int, rails: int) -> None:
    """Raise ``RailProblem`` unless ``rails`` can really scramble ``length`` letters."""
    if length == 0:
        raise RailProblem("There are no letters in that message to send.")
    if rails < 2:
        raise RailProblem("A rail fence needs at least two rails.")
    if rails >= length:
        message = f"{length} letters on {rails} rails would just read straight across."
        raise RailProblem(message + " Use fewer rails or a longer message.")


def zigzag_rows(length: int, rails: int) -> list[int]:
    """Which rail each letter sits on: 0 1 0 1... or 0 1 2 1 0 1 2...

    The pattern down and back up repeats every ``2 * (rails - 1)``
    letters, so ``%`` (the remainder) finds each letter's place in it.
    """
    pattern = list(range(rails)) + list(range(rails - 2, 0, -1))
    return [pattern[i % len(pattern)] for i in range(length)]


def encrypt(text: str, rails: int = 2) -> str:
    """Read the zigzag one rail at a time, top rail first."""
    letters = prepare(text)
    check_rails(len(letters), rails)
    rows = zigzag_rows(len(letters), rails)
    return "".join(
        letter
        for rail in range(rails)
        for letter, row in zip(letters, rows, strict=True)
        if row == rail
    )


def in_fives(letters: str) -> str:
    """Space letters into groups of five, the way telegraph clerks sent them."""
    return " ".join(letters[i : i + 5] for i in range(0, len(letters), 5))


def two_rail_decrypt(cipher: str) -> str:
    """Undo a two-rail fence: split in half, then stitch the halves together.

    The top rail holds the 1st, 3rd, 5th... letters, so with an odd
    number of letters it has the extra one: ``math.ceil`` rounds the
    half up. ``zip_longest`` pairs top and bottom letters and pads the
    short bottom rail with ``""`` instead of stopping early like ``zip``.
    """
    half = math.ceil(len(cipher) / 2)
    top, bottom = cipher[:half], cipher[half:]
    return "".join(a + b for a, b in zip_longest(top, bottom, fillvalue=""))


def zigzag_decrypt(cipher: str, rails: int) -> str:
    """Undo a fence with any number of rails by walking the zigzag again.

    First count how many letters landed on each rail, and cut the cipher
    into those runs. Then walk the zigzag and take the next letter from
    whichever rail the walk is on.
    """
    rows = zigzag_rows(len(cipher), rails)
    runs, start = [], 0
    for rail in range(rails):
        size = rows.count(rail)
        runs.append(iter(cipher[start : start + size]))
        start += size
    return "".join(next(runs[row]) for row in rows)


def decrypt(cipher: str, rails: int = 2) -> str:
    """Read a rail fence telegram (spaces in the groups of five are ignored)."""
    letters = prepare(cipher)
    check_rails(len(letters), rails)
    if rails == 2:
        return two_rail_decrypt(letters)
    return zigzag_decrypt(letters, rails)


def intercepted() -> str:
    """The intercepted telegram, as it came off the wire."""
    return in_fives(encrypt(INTERCEPT, INTERCEPT_RAILS))
