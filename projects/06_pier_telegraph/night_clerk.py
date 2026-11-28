"""The night clerk: try every route, then let a person's hunches narrow them down.

A route cipher's key is an order of the columns plus a direction for
each, so a rack with ``c`` columns has ``c!`` orders (``c`` choices for
the first column, ``c - 1`` for the next...) times ``2 ** c`` sets of
arrows. Four columns give 384 routes; seven give 645,120. Trying every
key like this is called a **brute-force attack**, and a computer
doesn't mind doing it.

The hard part is *recognising* the right reading. The clerk can't read:
it only knows a few rules about little words ("the" comes before a
thing, not before "and") and that filler goes at the end. Those rules
can't tell "fortune teller says" from "teller says fortune". A person
can, so the clerk takes **hunches**: pairs of words you're sure sit
side by side. Each hunch throws out most of the routes, and three
are usually enough to leave the answer in the clerk's top five.

The same brute force breaks a challenge link's seal without any
hunches at all: try routes until one has the right fingerprint.
"""

import itertools
import math
from collections.abc import Iterator

from challenge import is_solved
from codebook import CODEBOOK, FILLER
from rail_fence import check_rails, prepare, zigzag_decrypt
from route import Key, Words, factors, route_order
from word_gaps import coverage

WIDEST = 6  # 46,080 routes; seven columns would be 645,120

# A hunch: two words the person is sure sit side by side, in that order.
type Hunch = tuple[str, str] | list[str]

# Little words sorted into the jobs they do in a sentence. Everything
# else counts as a "word" (nouns, verbs, describing words...).
KINDS = {
    "pointer": "the a an this that these those my your our their his her its every",
    "place": "in on at under from by for of to with near into after before till over past",
    "joiner": "and but or so because if when than",
    "helper": "is are was were will has have had do does can be been",
    "person": "it he she they we you i me us them nobody someone everyone everything",
}
KIND = {word: kind for kind, words in KINDS.items() for word in words.split()}

# What usually comes next. Each pair that fits is +1; a pair that almost
# never happens in English ("the and", "under of") is -2.
GOOD = {
    ("pointer", "word"), ("place", "pointer"), ("place", "word"), ("place", "person"),
    ("person", "helper"), ("helper", "pointer"), ("helper", "word"), ("joiner", "pointer"),
    ("joiner", "person"), ("word", "place"), ("word", "joiner"), ("word", "pointer"),
}  # fmt: skip
BAD = {
    ("pointer", "pointer"), ("pointer", "place"), ("pointer", "joiner"),
    ("pointer", "helper"), ("pointer", "person"), ("place", "place"),
    ("place", "joiner"), ("place", "helper"), ("joiner", "joiner"),
    ("joiner", "helper"), ("helper", "joiner"),
}  # fmt: skip
# A sentence rarely ends on these, or starts with a joiner.
NO_END = {"pointer", "place", "joiner"}


def key_count(cols: int) -> int:
    """How many routes a rack with ``cols`` columns has: ``cols! * 2 ** cols``."""
    return math.factorial(cols) * 2**cols


def all_keys(cols: int) -> Iterator[Key]:
    """Every route for a rack, one at a time.

    ``itertools.permutations`` gives every order of the columns, and
    ``itertools.product((1, -1), repeat=cols)`` every set of arrows (up
    or down for each column). Both are lazy: they hand out one answer at
    a time instead of building a list of 46,080 keys first.
    """
    for order in itertools.permutations(range(1, cols + 1)):
        for signs in itertools.product((1, -1), repeat=cols):
            yield [column * sign for column, sign in zip(order, signs, strict=True)]


def place(cipher: Words, cols: int, rows: int, key: Key) -> Words:
    """Decrypt by putting each word back in the cell its route came from.

    The same answer as ``route.decrypt``, but a little quicker, which
    counts when it runs 46,080 times.
    """
    words = [""] * len(cipher)
    for word, cell in zip(cipher, route_order(cols, rows, key), strict=True):
        words[cell] = word
    return words


def expand(words: Words) -> Words:
    """Swap code words back for their phrases, and filler for a marker.

    The office writes code words and filler in capitals and everything
    else in small letters, so a message about a real sandcastle isn't
    mistaken for SANDCASTLE the filler.
    """
    plain: Words = []
    for word in words:
        if word in FILLER:
            plain.append("~")
        else:
            plain.extend(CODEBOOK.get(word, word).lower().split())
    return plain


def kind(word: str) -> str:
    """Which job a word does: a ``KINDS`` name, or "word" for the rest."""
    return KIND.get(word, "word")


def readability(words: Words) -> int:
    """Score how much a reading looks like a real telegram.

    Each rule is something a tired clerk would notice too:

    - filler belongs at the very end, so it's worth +2 there and -4
      anywhere else;
    - each neighbouring pair that fits English ("at the", "the pier")
      is +1, and each one that hardly ever happens ("the and") is -2;
    - a message doesn't end on "the", "under" or "and" (-2), or start
      with "and" (-2).
    """
    plain = expand(words)
    message = list(plain)
    while message and message[-1] == "~":
        message.pop()
    score = 2 * (len(plain) - len(message)) - 4 * message.count("~")
    kinds = [kind(word) for word in message if word != "~"]
    for pair in itertools.pairwise(kinds):
        if pair in GOOD:
            score += 1
        elif pair in BAD:
            score -= 2
    if kinds and kinds[-1] in NO_END:
        score -= 2
    if kinds and kinds[0] == "joiner":
        score -= 2
    return score


def racks(count: int, widest: int = WIDEST) -> list[tuple[int, int]]:
    """Every (columns, rows) rack a telegram of ``count`` words could fill."""
    return [(cols, count // cols) for cols in factors(count) if cols <= widest]


def fits(words: Words, hunches: list[Hunch]) -> bool:
    """Whether every hunch (a word, then the word right after it) is in ``words``.

    Capitals don't matter, so a hunch of "gull won" finds "GULL won".
    """
    if not hunches:
        return True
    pairs = {(first.lower(), second.lower()) for first, second in itertools.pairwise(words)}
    return all((first.lower(), second.lower()) in pairs for first, second in hunches)


def crack_route(
    cipher: Words,
    hunches: list[Hunch] | None = None,
    widest: int = WIDEST,
    top: int = 5,
) -> dict:
    """Try every route on every rack that fits, and keep the best readings.

    ``hunches`` are pairs of words the person is sure sit side by side
    ("ice", "cream"). Routes that break a hunch are thrown out, which is
    how a little human knowledge turns thousands of routes into a few.

    Returns ``{"tried", "fit", "racks", "too_wide", "best"}``, where
    ``best`` is a list of ``{"cols", "rows", "key", "words", "score"}``,
    best first. Racks wider than ``widest`` are skipped (and listed in
    ``too_wide``), because their routes run into the millions.
    """
    hunches = hunches or []
    tried, readings = 0, []
    for cols, rows in racks(len(cipher), widest):
        for key in all_keys(cols):
            tried += 1
            words = place(cipher, cols, rows, key)
            if fits(words, hunches):
                readings.append((readability(words), tried, cols, rows, key, words))
    readings.sort(key=lambda reading: (-reading[0], reading[1]))
    best = [
        {"cols": cols, "rows": rows, "key": key, "words": words, "score": score}
        for score, _, cols, rows, key, words in readings[:top]
    ]
    return {
        "tried": tried,
        "fit": len(readings),
        "racks": racks(len(cipher), widest),
        "too_wide": [cols for cols in factors(len(cipher)) if cols > widest],
        "best": best,
    }


def crack_seal(cipher: Words, check: str, widest: int = WIDEST) -> dict | None:
    """Break a challenge link: try routes until one matches its fingerprint.

    Returns ``{"cols", "rows", "key", "words", "tried"}``, or ``None`` if
    no route on a rack up to ``widest`` columns fits.
    """
    tried = 0
    for cols, rows in racks(len(cipher), widest):
        for key in all_keys(cols):
            tried += 1
            words = place(cipher, cols, rows, key)
            if is_solved(words, check):
                return {"cols": cols, "rows": rows, "key": key, "words": words, "tried": tried}
    return None


def crack_rails(cipher: str, words: set[str], most: int = 8) -> dict:
    """Try every rail count from 2 to ``most`` and score each by real words.

    Returns ``{"readings", "best"}``: one ``{"rails", "letters",
    "coverage"}`` per rail count, and the rail count that reads best.
    """
    letters = prepare(cipher)
    check_rails(len(letters), 2)
    readings = []
    for rails in range(2, min(most, len(letters) - 1) + 1):
        plain = zigzag_decrypt(letters, rails)
        readings.append({"rails": rails, "letters": plain, "coverage": coverage(plain, words)})
    best = max(readings, key=lambda reading: reading["coverage"])
    return {"readings": readings, "best": best["rails"]}
