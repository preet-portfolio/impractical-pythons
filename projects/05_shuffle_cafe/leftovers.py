"""Shuffle leftover letters that no English word will take.

Sometimes the last few letters of a name don't spell anything in the
dictionary. They might still spell a word from another language, or a
name nobody has invented yet. The only way to find out is to look at
every arrangement, which is fine for five letters and hopeless for ten.

``itertools.permutations`` produces the arrangements; ``math.factorial``
says how many there will be before you ask for them.
"""

import itertools
import math
import random
from collections import Counter

LIST_LIMIT = 720  # 6 different letters: about as many as a person will read


def arrangement_count(letters: str) -> int:
    """Count the *different* ways to order the letters.

    Six letters can be ordered 6! = 720 ways. But swapping two identical
    letters gives the same string, so divide by the factorial of each
    letter's count: "teeth" has 5! / (2! * 2!) = 30 arrangements, not 120.
    """
    total = math.factorial(len(letters))
    for repeats in Counter(letters).values():
        total //= math.factorial(repeats)
    return total


def arrangements(letters: str) -> list[str]:
    """Every different arrangement of the letters, alphabetical.

    ``permutations`` yields tuples like ``('m', 'e', 'r')``; ``"".join``
    turns each into a string, and a set drops the repeats that
    identical letters cause.
    """
    every = {"".join(order) for order in itertools.permutations(letters)}
    return sorted(every)


def sample_arrangements(
    letters: str,
    size: int,
    seed: int | None = None,
) -> list[str]:
    """Pick random arrangements, for when there are far too many to list.

    ``random.sample(letters, len(letters))`` is a shuffled copy of the
    letters. Seen-before results are skipped, and the loop gives up after
    plenty of tries in case there aren't ``size`` different ones at all.
    """
    rng = random.Random(seed)
    wanted = min(size, arrangement_count(letters))
    found: list[str] = []
    for _ in range(wanted * 20):
        if len(found) == wanted:
            break
        guess = "".join(rng.sample(letters, len(letters)))
        if guess not in found:
            found.append(guess)
    return found


def shuffle_report(
    letters: str,
    sample: int = 24,
    seed: int | None = None,
) -> dict:
    """Everything the shuffle screen needs: the count, and the arrangements.

    Lists every arrangement when there are at most ``LIST_LIMIT``;
    otherwise a random sample, because nobody reads 40,000 lines.
    """
    count = arrangement_count(letters)
    report = {
        "letters": letters,
        "count": count,
        "complete": count <= LIST_LIMIT,
    }
    if report["complete"]:
        report["arrangements"] = arrangements(letters)
    else:
        report["arrangements"] = sample_arrangements(letters, sample, seed)
    return report
