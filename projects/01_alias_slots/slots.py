"""The Alias Slots machine: spin reels, score the result, share it.

Everything here is a pure function of its inputs (no printing, no input()), so
the same code runs in the terminal, in pytest and in the browser via Pyodide.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from itertools import product

from themes import THEMES, Theme

# Small words that don't count for alliteration: "the Unwashed" starts with U.
FILLER_WORDS = frozenset({"the", "of", "a", "an"})

# Best prize first. A spin wins the highest prize it qualifies for.
PRIZES = ("jackpot", "rhyme", "pair")

BASE36 = "0123456789abcdefghijklmnopqrstuvwxyz"


@dataclass(frozen=True)
class Spin:
    """The result of one pull of the lever.

    Attributes:
        theme: Key of the theme that was spun.
        indices: Where each reel stopped (one index per reel).
        words: The words at those positions.
        name: The finished alias, built from the theme's template.
        prize: ``"jackpot"``, ``"rhyme"``, ``"pair"`` or ``None``.
        code: Short share code that brings back exactly this spin.
    """

    theme: str
    indices: tuple[int, ...]
    words: tuple[str, ...]
    name: str
    prize: str | None
    code: str


def get_theme(key: str) -> Theme:
    """Look up a theme by key, with a helpful error for typos."""
    try:
        return THEMES[key]
    except KeyError:
        choices = ", ".join(THEMES)
        raise ValueError(f"Unknown theme {key!r}. Choose one of: {choices}") from None


def key_letter(word: str) -> str:
    """Return the letter a word 'starts with' for alliteration.

    Filler words are skipped, so ``"of the Damp Crypt"`` counts as D.
    """
    for part in word.split():
        if part.lower() not in FILLER_WORDS:
            return part[0].lower()
    return word[0].lower()


def last_word(word: str) -> str:
    """Return the final word, lower-cased and stripped of punctuation."""
    return word.split()[-1].lower().strip(".,!?'\"-")


def rhymes(a: str, b: str) -> bool:
    """Cheap rhyme test: two different words sharing their last three letters."""
    a_end, b_end = last_word(a), last_word(b)
    return a_end != b_end and len(a_end) >= 3 and len(b_end) >= 3 and a_end[-3:] == b_end[-3:]


def prize_for(words: tuple[str, ...]) -> str | None:
    """Score a spin.

    * ``jackpot``: every reel starts with the same letter (alliteration).
    * ``rhyme``: any two reels end with the same three letters.
    * ``pair``: two reels start with the same letter.
    """
    letters = Counter(key_letter(word) for word in words)
    most_common = letters.most_common(1)[0][1]
    if most_common == len(words):
        return "jackpot"
    if any(rhymes(a, b) for i, a in enumerate(words) for b in words[i + 1 :]):
        return "rhyme"
    if most_common >= 2:
        return "pair"
    return None


def from_indices(theme_key: str, indices: tuple[int, ...]) -> Spin:
    """Build the spin where each reel stopped at the given index."""
    theme = get_theme(theme_key)
    if len(indices) != len(theme.reels):
        raise ValueError(f"Expected {len(theme.reels)} reel positions, got {len(indices)}")
    for reel, index in zip(theme.reels, indices, strict=True):
        if not 0 <= index < len(reel):
            raise ValueError(f"Reel position {index} is off the reel (0-{len(reel) - 1})")
    words = tuple(reel[i] for reel, i in zip(theme.reels, indices, strict=True))
    return Spin(
        theme=theme.key,
        indices=tuple(indices),
        words=words,
        name=theme.render(words),
        prize=prize_for(words),
        code=encode(theme.key, tuple(indices)),
    )


def spin(theme_key: str, seed: int | None = None, locked: dict[int, int] | None = None) -> Spin:
    """Pull the lever.

    Args:
        theme_key: Which machine to play.
        seed: Same seed, same spin. ``None`` means a fresh random spin.
        locked: ``{reel number: index}`` for reels that must not move.

    Every reel always draws a random number, even when locked, so locking a
    reel never changes what the *other* reels land on for a given seed.
    """
    theme = get_theme(theme_key)
    rng = random.Random(seed)
    locked = locked or {}
    indices = tuple(
        locked.get(reel_no, drawn)
        for reel_no, drawn in enumerate(rng.randrange(len(reel)) for reel in theme.reels)
    )
    return from_indices(theme_key, indices)


def encode(theme_key: str, indices: tuple[int, ...]) -> str:
    """Pack a theme and reel positions into a short base-36 share code.

    It's a mixed-radix number: each reel is a "digit" whose base is that
    reel's length, and the theme is the last digit.
    """
    theme = get_theme(theme_key)
    number = 0
    for reel, index in zip(theme.reels, indices, strict=True):
        number = number * len(reel) + index
    number = number * len(THEMES) + list(THEMES).index(theme_key)
    return to_base36(number)


def decode(code: str) -> Spin:
    """Turn a share code back into its spin. Raises ValueError for bad codes."""
    number = from_base36(code)
    theme_key = list(THEMES)[number % len(THEMES)]
    number //= len(THEMES)
    theme = THEMES[theme_key]
    indices: list[int] = []
    for reel in reversed(theme.reels):
        number, index = divmod(number, len(reel))
        indices.append(index)
    if number:
        raise ValueError(f"Share code {code!r} is too big for any spin")
    return from_indices(theme_key, tuple(reversed(indices)))


def to_base36(number: int) -> str:
    """Write a non-negative integer in base 36 (0-9 then a-z)."""
    if number < 0:
        raise ValueError("Only non-negative numbers can be encoded")
    digits = ""
    while True:
        number, remainder = divmod(number, 36)
        digits = BASE36[remainder] + digits
        if number == 0:
            return digits


def from_base36(code: str) -> int:
    """Read a base-36 string. ``int(code, 36)`` with a friendlier error."""
    cleaned = code.strip().lower()
    if not cleaned or any(char not in BASE36 for char in cleaned):
        raise ValueError(f"Share code {code!r} isn't valid")
    return int(cleaned, 36)


def combinations(theme_key: str) -> int:
    """How many different aliases this machine can make."""
    total = 1
    for reel in get_theme(theme_key).reels:
        total *= len(reel)
    return total


def odds(theme_key: str) -> dict[str, int]:
    """Count how many of all possible spins win each prize.

    The reels are small (about 24**3 = 13,824 spins), so we can simply try
    every combination with ``itertools.product`` instead of doing the maths.
    """
    counts = Counter(prize_for(words) for words in product(*get_theme(theme_key).reels))
    return {prize: counts.get(prize, 0) for prize in PRIZES}


def catalogue() -> list[dict]:
    """Everything the web page needs to draw the machines, as plain data."""
    return [
        {
            "key": theme.key,
            "title": theme.title,
            "blurb": theme.blurb,
            "reel_names": list(theme.reel_names),
            "reels": [list(reel) for reel in theme.reels],
            "combinations": combinations(theme.key),
            "odds": odds(theme.key),
        }
        for theme in THEMES.values()
    ]
