"""Strain every ordering of some letters down to the ones that sound right.

Nine letters can be put in 362,880 orders, and almost all of them are
unpronounceable mush. Rather than read them, pour them through three
sieves, each one built from statistics counted in our own dictionary:

1. **Shape**: written as consonants and vowels (``cvccvc``), does the
   ordering look like real words that long? Rare shapes are caught.
2. **Triples**: does it contain a run of three letters that hardly
   any English word has?
3. **Pairs**: does it contain one of English's rarest letter pairs,
   or start with a pair that almost no word starts with?

Each sieve is a small function that returns the *culprit* (the shape,
triple or pair that got caught) or ``None`` if the ordering passes.
The same functions strain a whole batch and explain a single verdict.
"""

import math
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from leftovers import arrangement_count, arrangements
from ngrams import common_shapes, count_ngrams, count_starts, cv_map, ngrams

SIEVE_LIMIT = 9  # letters; ten would be 3,628,800 orderings
RARE_TRIPLE = 3  # a triple found fewer times than this is rare
RARE_PAIR = 0.0005  # a pair below this share of all pairs is rare
RARE_START = 10  # a pair starting fewer words than this can't start ours


@dataclass
class LetterStats:
    """Everything the sieves know about English, counted once.

    Counting takes a moment, so the web page builds this once and keeps
    it. Shapes are counted per word length, the first time that length
    is asked for, and remembered in ``_shapes``.
    """

    words: list[str]
    pairs: Counter = field(init=False)
    triples: Counter = field(init=False)
    starts: Counter = field(init=False)
    _shapes: dict = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        """Count pairs, triples and word starts across the dictionary."""
        self.words = [word for word in self.words if word.isalpha()]
        self.pairs = count_ngrams(self.words, 2)
        self.triples = count_ngrams(self.words, 3)
        self.starts = count_starts(self.words, 2)

    def shapes(self, length: int) -> set[str]:
        """The common consonant-vowel shapes for words this long."""
        if length not in self._shapes:
            self._shapes[length] = common_shapes(self.words, length)
        return self._shapes[length]

    def rare_pair(self, pair: str) -> bool:
        """Say whether a letter pair is among English's rarest."""
        return self.pairs[pair] < RARE_PAIR * self.pairs.total()


def catch_shape(candidate: str, stats: LetterStats) -> str | None:
    """Return the candidate's shape if few real words have it."""
    shape = cv_map(candidate)
    return None if shape in stats.shapes(len(candidate)) else shape


def catch_triple(candidate: str, stats: LetterStats) -> str | None:
    """Return the first rare three-letter run in the candidate."""
    for triple in ngrams(candidate, 3):
        if stats.triples[triple] < RARE_TRIPLE:
            return triple
    return None


def catch_pair(candidate: str, stats: LetterStats) -> str | None:
    """Return a rare pair, or ``"start:xy"`` for an unlikely first pair."""
    if len(candidate) >= 2 and stats.starts[candidate[:2]] < RARE_START:
        return "start:" + candidate[:2]
    for pair in ngrams(candidate, 2):
        if stats.rare_pair(pair):
            return pair
    return None


SIEVES: dict[str, Callable[[str, LetterStats], str | None]] = {
    "shape": catch_shape,
    "triples": catch_triple,
    "pairs": catch_pair,
}


def explain(sieve: str, culprit: str, stats: LetterStats) -> str:
    """Say in plain words why a sieve caught something."""
    if sieve == "shape":
        return (
            f"Its shape, {culprit.upper()} (C for consonant, V for vowel), "
            "is rare: hardly any English words that long are built like it."
        )
    if sieve == "triples":
        times = stats.triples[culprit]
        if not times:
            return f'No English word has "{culprit}" in it.'
        where = "1 place" if times == 1 else f"{times} places"
        return f'"{culprit}" turns up in only {where} in the dictionary.'
    if culprit.startswith("start:"):
        start = culprit.removeprefix("start:")
        times = stats.starts[start]
        if not times:
            return f'No English word starts with "{start}".'
        return f'Only {times} English words start with "{start}".'
    return f'"{culprit}" is one of the rarest letter pairs in English.'


def verdict(
    name: str,
    stats: LetterStats,
    active: tuple[str, ...] = tuple(SIEVES),
) -> dict:
    """Pour one made-up word through the sieves and report what happened."""
    for sieve in active:
        culprit = SIEVES[sieve](name, stats)
        if culprit is not None:
            return {
                "name": name,
                "passed": False,
                "caught_by": sieve,
                "reason": explain(sieve, culprit, stats),
            }
    return {"name": name, "passed": True, "caught_by": None, "reason": ""}


def wordiness(candidate: str, stats: LetterStats) -> float:
    """Score how English an ordering sounds: its triples' average log count.

    Logarithms stop one hugely common triple (like *ing*) from drowning
    out the rest: each tenfold jump in count adds the same amount.
    """
    triples = ngrams(candidate, 3)
    if not triples:
        return 0.0
    return sum(math.log1p(stats.triples[t]) for t in triples) / len(triples)


def strain(
    letters: str,
    stats: LetterStats,
    active: tuple[str, ...] = tuple(SIEVES),
) -> dict:
    """Make every ordering of the letters, then pour them through the sieves.

    Returns how many orderings were left after each sieve (a sieve that
    is switched off lets everything through), the survivors, most
    English-sounding first, and how many survivors start with each letter.
    Raises ``ValueError`` past ``SIEVE_LIMIT`` letters.
    """
    if len(letters) > SIEVE_LIMIT:
        raise ValueError(f"{len(letters)} letters is too many to strain")
    batch = arrangements(letters)
    stages = []
    for sieve, catch in SIEVES.items():
        on = sieve in active
        if on:
            batch = [c for c in batch if catch(c, stats) is None]
        stages.append({"sieve": sieve, "on": on, "left": len(batch)})
    survivors = sorted(batch, key=lambda c: (-wordiness(c, stats), c))
    by_letter: dict[str, int] = {}
    for survivor in survivors:
        by_letter[survivor[0]] = by_letter.get(survivor[0], 0) + 1
    return {
        "letters": letters,
        "start": arrangement_count(letters),
        "stages": stages,
        "survivors": survivors,
        "by_letter": dict(sorted(by_letter.items())),
    }
