"""Shuffled or swapped? Tell two kinds of cipher apart by their letters.

There are two basic ways to hide a message:

- **shuffle** its letters into a new order (a *transposition*, like the
  rail fence), or
- **swap** each letter for a different one (a *substitution*: every E
  becomes Q, every T becomes M...).

A shuffled telegram still has English's letters, just in a different
order, so E, T and A still turn up most. A swapped one keeps the
pattern but on the wrong letters: Q might be the commonest. Count the
letters, compare them with ordinary English, and you can tell which
kind of cipher you're facing before trying to break it.

The comparison is a **chi-squared** score: for each letter, how far is
the count from what English would give, squared, and divided by what
English would give? Add those up. Small means "looks like English".
"""

import random
import string
from collections import Counter

from english import ENGLISH
from rail_fence import prepare

SHORTEST = 30  # fewer letters than this and chance swamps the pattern

# Scores per letter of text. Shuffled English telegrams on the pier score
# well under 1; swapped ones mostly score 2 to 10. In between, a swap
# that happened to land on similar letters can pass for English, so the
# office admits it can't be sure.
LOOKS_ENGLISH = 1.0
LOOKS_SWAPPED = 1.75


def letter_shares(text: str) -> dict[str, float]:
    """Each letter's share of the text's letters, in percent (a to z)."""
    letters = prepare(text).lower()
    counts = Counter(letters)
    total = len(letters) or 1
    return {letter: 100 * counts[letter] / total for letter in string.ascii_lowercase}


def english_likeness(text: str) -> float:
    """Chi-squared distance from English, per letter of text (0 is a perfect match).

    Dividing by the number of letters lets short and long telegrams be
    judged on the same scale.
    """
    letters = prepare(text).lower()
    if not letters:
        return 0.0
    counts = Counter(letters)
    total = len(letters)
    score = 0.0
    for letter, share in ENGLISH.items():
        expected = total * share / 100
        score += (counts[letter] - expected) ** 2 / expected
    return score / total


def verdict(text: str) -> dict:
    """Decide "shuffled", "swapped" or "too short", with a reason in plain words.

    Returns ``{"verdict", "reason", "score", "letters", "shares", "english"}``.
    """
    letters = prepare(text)
    shares = letter_shares(text)
    result = {
        "letters": len(letters),
        "shares": shares,
        "english": ENGLISH,
        "score": round(english_likeness(text), 2),
    }
    if len(letters) < SHORTEST:
        reason = f"Only {len(letters)} letters. Chance could make almost any pattern."
        return result | {"verdict": "too short", "reason": reason + " Try 30 or more."}
    kind = decide(result["score"])
    return result | {"verdict": kind, "reason": explain(shares, kind)}


def decide(score: float) -> str:
    """Turn a chi-squared score into "shuffled", "swapped" or "hard to say"."""
    if score <= LOOKS_ENGLISH:
        return "shuffled"
    if score >= LOOKS_SWAPPED:
        return "swapped"
    return "hard to say"


def explain(shares: dict[str, float], kind: str) -> str:
    """One plain sentence about the letters behind the verdict."""
    top = max(shares, key=lambda letter: shares[letter]).upper()
    if kind == "shuffled":
        if top in "ETAO":
            return f"{top} is the commonest letter, just like English."
        return "Every letter turns up about as often as it does in English."
    if kind == "hard to say":
        return "Nearly English-shaped, but not quite. A swap can land on look-alike letters."
    rare = [letter.upper() for letter in "jqxz" if shares[letter] >= 3]
    if rare:
        names = rare[0] if len(rare) == 1 else ", ".join(rare[:-1]) + " and " + rare[-1]
        verb = "turns" if len(rare) == 1 else "turn"
        return f"{names} {verb} up far more often than English would allow."
    if top not in "ETAOINSHR":
        return f"{top} is the commonest letter. In English it hardly ever would be."
    return "The right shape, but the wrong letters are doing the work."


def swap_letters(text: str, seed: int = 7) -> str:
    """Swap every letter for another, using a shuffled alphabet.

    ``str.maketrans`` builds a letter-for-letter table and
    ``str.translate`` applies it in one go. The seed makes the same
    shuffled alphabet every time.
    """
    alphabet = list(string.ascii_uppercase)
    random.Random(seed).shuffle(alphabet)
    table = str.maketrans(string.ascii_uppercase, "".join(alphabet))
    return prepare(text).translate(table)
