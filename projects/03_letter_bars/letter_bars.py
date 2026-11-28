"""Letter Bars: count the letters in a text and line them up as bars.

Every language leaves a fingerprint in how often it uses each letter.
English leans on E, T and A; Spanish piles up A, E and O; French loves
E and S. Counting is the easy part (a ``defaultdict`` does it). The
interesting decisions are about *what counts as a letter*: here é, à and
ñ are folded into e, a and n with ``unicodedata``, and the accents we
folded are reported separately so nothing disappears silently.
"""

import string
import unicodedata
from collections import defaultdict

from english import ENGLISH

ALPHABET = string.ascii_lowercase

# ENGLISH (typical letter shares, in percent) lives in projects/common,
# because Pier Telegraph needs it too.

# Letters that don't split into "base letter + accent" in Unicode.
LIGATURES = {"æ": "ae", "œ": "oe", "ß": "ss", "ø": "o", "đ": "d", "ł": "l"}

# Our own short scene, with our own Spanish and French versions of it.
SAMPLES = {
    "English": (
        "On summer evenings the old pier fills with music. Children chase "
        "gulls past the ice cream kiosk, fishermen trade stories about the "
        "one that got away, and the lights along the railing come on one by "
        "one. When the tide turns, everyone stops to watch the sun slide "
        "quietly into the sea."
    ),
    "Spanish": (
        "En las tardes de verano, el viejo muelle se llena de música. Los "
        "niños persiguen a las gaviotas junto al quiosco de helados, los "
        "pescadores cuentan historias sobre el pez que se les escapó, y las "
        "luces de la barandilla se encienden una a una. Cuando cambia la "
        "marea, todos se detienen para ver cómo el sol se hunde despacio en "
        "el mar."
    ),
    "French": (
        "Les soirs d'été, la vieille jetée se remplit de musique. Les "
        "enfants poursuivent les mouettes devant le kiosque à glaces, les "
        "pêcheurs racontent l'histoire du poisson qui s'est échappé, et les "
        "lumières le long de la rambarde s'allument une à une. Quand la "
        "marée tourne, tout le monde s'arrête pour regarder le soleil "
        "glisser doucement dans la mer."
    ),
}


def fold(char: str) -> str:
    """Return the plain a-z letter(s) a character stands for, or "".

    NFD normalisation splits "é" into "e" plus a combining accent, so the
    first piece is the base letter. Anything that isn't a Latin letter
    (digits, spaces, Greek, emoji) folds to "" and isn't counted.
    """
    lower = char.lower()
    if lower in LIGATURES:
        return LIGATURES[lower]
    base = unicodedata.normalize("NFD", lower)[:1]
    return base if base in ALPHABET else ""


def count_letters(text: str, all_letters: bool = False) -> dict[str, int]:
    """Count each a-z letter in ``text``, with accents folded in.

    ``defaultdict(int)`` starts every new key at 0, so there is no "is
    it there yet?" check. With ``all_letters`` the zeros are filled in
    too, which keeps two charts the same shape for comparing.
    """
    counts: defaultdict[str, int] = defaultdict(int)
    for char in text:
        for letter in fold(char):
            counts[letter] += 1
    if all_letters:
        return {letter: counts[letter] for letter in ALPHABET}
    return dict(sorted(counts.items()))


def accents(text: str) -> dict[str, int]:
    """Count the accented letters that were folded into plain ones."""
    found: defaultdict[str, int] = defaultdict(int)
    for char in text:
        lower = char.lower()
        if lower not in ALPHABET and fold(lower):
            found[lower] += 1
    return dict(sorted(found.items(), key=lambda item: (-item[1], item[0])))


def shares(counts: dict[str, int]) -> dict[str, float]:
    """Turn counts into percentages of all the letters counted."""
    total = sum(counts.values()) or 1  # an empty text gives all zeros
    return {letter: 100 * n / total for letter, n in counts.items()}


def top_letters(counts: dict[str, int], n: int = 6) -> str:
    """Return the ``n`` most common letters, most common first.

    Sorting on the key ``(-count, letter)`` puts big counts first and
    breaks ties alphabetically, so the answer never depends on the order
    the letters were seen in.
    """
    used = [letter for letter, count in counts.items() if count]
    ranked = sorted(used, key=lambda letter: (-counts[letter], letter))
    return "".join(ranked[:n])


def bar_chart(text: str) -> dict[str, str]:
    """Map each letter used to a bar made of that letter, e.g. "eeee".

    Printed with ``pprint`` this is already a sideways bar chart.
    """
    return {letter: letter * n for letter, n in count_letters(text).items()}


def compare(text_a: str, text_b: str) -> list[dict[str, float | str]]:
    """Line up two texts' letter shares, all 26 letters, a to z."""
    share_a = shares(count_letters(text_a, all_letters=True))
    share_b = shares(count_letters(text_b, all_letters=True))
    rows = []
    for char in ALPHABET:
        rows.append({"letter": char, "a": share_a[char], "b": share_b[char]})
    return rows


def summary(text: str) -> dict[str, object]:
    """Everything the page shows about one text, in plain types."""
    counts = count_letters(text, all_letters=True)
    return {
        "total": sum(counts.values()),
        "counts": counts,
        "shares": shares(counts),
        "top": top_letters(counts),
        "accents": accents(text),
    }


def chart_data(text_a: str, text_b: str | None = None) -> dict[str, object]:
    """Build the page's chart: one or two texts plus typical English."""
    return {
        "letters": list(ALPHABET),
        "english": ENGLISH,
        "english_top": top_letters(
            {letter: round(share * 1000) for letter, share in ENGLISH.items()}
        ),
        "a": summary(text_a),
        "b": None if text_b is None else summary(text_b),
    }
