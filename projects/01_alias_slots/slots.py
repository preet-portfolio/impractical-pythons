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

# How often the wildcard middle-name reel shows up: about one spin in three.
MIDDLE_CHANCE = 1 / 3


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
        middle: Index of the wildcard middle name, or ``None`` if it didn't show.
        middle_word: The wildcard middle name itself, or ``None``.
        bonus: True when the middle name starts with the first name's letter.
    """

    theme: str
    indices: tuple[int, ...]
    words: tuple[str, ...]
    name: str
    prize: str | None
    code: str
    middle: int | None = None
    middle_word: str | None = None
    bonus: bool = False


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


def wildcard_bonus(first: str, middle: str | None) -> bool:
    """True when a middle name showed up and alliterates with the first name."""
    return middle is not None and key_letter(middle) == key_letter(first)


def from_indices(theme_key: str, indices: tuple[int, ...], middle: int | None = None) -> Spin:
    """Build the spin where each reel stopped at the given index.

    ``middle`` is the wildcard middle name's index, or ``None`` when it
    didn't show up.
    """
    theme = get_theme(theme_key)
    if len(indices) != len(theme.reels):
        raise ValueError(f"Expected {len(theme.reels)} reel positions, got {len(indices)}")
    for reel, index in zip(theme.reels, indices, strict=True):
        if not 0 <= index < len(reel):
            raise ValueError(f"Reel position {index} is off the reel (0-{len(reel) - 1})")
    if middle is not None and not 0 <= middle < len(theme.middles):
        raise ValueError(f"Middle name {middle} is off the wildcard reel")
    words = tuple(reel[i] for reel, i in zip(theme.reels, indices, strict=True))
    middle_word = None if middle is None else theme.middles[middle]
    return Spin(
        theme=theme.key,
        indices=tuple(indices),
        words=words,
        name=theme.render(words, middle_word),
        prize=prize_for(words),
        code=encode(theme.key, tuple(indices), middle),
        middle=middle,
        middle_word=middle_word,
        bonus=wildcard_bonus(words[0], middle_word),
    )


def spin(theme_key: str, seed: int | None = None, locked: dict[int, int] | None = None) -> Spin:
    """Pull the lever.

    Args:
        theme_key: Which machine to play.
        seed: Same seed, same spin. ``None`` means a fresh random spin.
        locked: ``{reel number: index}`` for reels that must not move.

    Every reel always draws a random number, even when locked, so locking a
    reel never changes what the *other* reels land on for a given seed. The
    wildcard reel draws its chance and its name on every spin for the same
    reason, then only shows up when the chance comes in.
    """
    theme = get_theme(theme_key)
    rng = random.Random(seed)
    locked = locked or {}
    indices = tuple(
        locked.get(reel_no, drawn)
        for reel_no, drawn in enumerate(rng.randrange(len(reel)) for reel in theme.reels)
    )
    shows = rng.random() < MIDDLE_CHANCE
    middle = rng.randrange(len(theme.middles)) if theme.middles else 0
    return from_indices(theme_key, indices, middle if shows and theme.middles else None)


def encode(theme_key: str, indices: tuple[int, ...], middle: int | None = None) -> str:
    """Pack a theme, reel positions and any middle name into a base-36 code.

    It's a mixed-radix number: each reel is a "digit" whose base is that
    reel's length. The wildcard is a digit with one extra value (0 means
    "no middle name"), and the theme is the last digit.
    """
    theme = get_theme(theme_key)
    number = 0
    for reel, index in zip(theme.reels, indices, strict=True):
        number = number * len(reel) + index
    number = number * (len(theme.middles) + 1) + (0 if middle is None else middle + 1)
    number = number * len(THEMES) + list(THEMES).index(theme_key)
    return to_base36(number)


def decode(code: str) -> Spin:
    """Turn a share code back into its spin. Raises ValueError for bad codes."""
    number = from_base36(code)
    theme_key = list(THEMES)[number % len(THEMES)]
    number //= len(THEMES)
    theme = THEMES[theme_key]
    number, wildcard = divmod(number, len(theme.middles) + 1)
    indices: list[int] = []
    for reel in reversed(theme.reels):
        number, index = divmod(number, len(reel))
        indices.append(index)
    if number:
        raise ValueError(f"Share code {code!r} is too big for any spin")
    middle = None if wildcard == 0 else wildcard - 1
    return from_indices(theme_key, tuple(reversed(indices)), middle)


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


def reel_combinations(theme_key: str) -> int:
    """How many ways the three main reels can stop (what prizes are scored on)."""
    total = 1
    for reel in get_theme(theme_key).reels:
        total *= len(reel)
    return total


def combinations(theme_key: str) -> int:
    """How many different aliases this machine can make, middle names included."""
    return reel_combinations(theme_key) * (len(get_theme(theme_key).middles) + 1)


def odds(theme_key: str) -> dict[str, int]:
    """Count how many of the main reels' stops win each prize.

    The reels are small (about 24**3 = 13,824 spins), so we can simply try
    every combination with ``itertools.product`` instead of doing the maths.
    """
    counts = Counter(prize_for(words) for words in product(*get_theme(theme_key).reels))
    return {prize: counts.get(prize, 0) for prize in PRIZES}


def bonus_chance(theme_key: str) -> float:
    """Chance that a spin earns the wildcard bonus.

    Two independent things must happen, so their chances multiply:
    the wildcard shows up (``MIDDLE_CHANCE``) *and* the middle name starts
    with the same letter as the first name.
    """
    theme = get_theme(theme_key)
    if not theme.middles:
        return 0.0
    pairs = product(theme.reels[0], theme.middles)
    matches = sum(key_letter(first) == key_letter(middle) for first, middle in pairs)
    return MIDDLE_CHANCE * matches / (len(theme.reels[0]) * len(theme.middles))


def catalogue() -> list[dict]:
    """Everything the web page needs to draw the machines, as plain data."""
    return [
        {
            "key": theme.key,
            "title": theme.title,
            "blurb": theme.blurb,
            "reel_names": list(theme.reel_names),
            "reels": [list(reel) for reel in theme.reels],
            "middles": list(theme.middles),
            "middle_chance": MIDDLE_CHANCE,
            "combinations": combinations(theme.key),
            "reel_combinations": reel_combinations(theme.key),
            "odds": odds(theme.key),
            "bonus_chance": bonus_chance(theme.key),
        }
        for theme in THEMES.values()
    ]
