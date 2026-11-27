"""Count letter pairs, triples and word shapes in a dictionary.

Code-breakers have long known that a language leaves fingerprints:
English is full of *th*, *er* and *ing*, and almost never writes *vq*.
Rather than copy a table of those statistics from somewhere, we count
them ourselves from the word list we already ship. That way they match
our dictionary exactly, and they work for any letters at all.

Three kinds of fingerprint are counted:

- **n-grams**: runs of ``n`` letters next to each other (pairs are
  2-grams, triples are 3-grams);
- **starts**: the pair a word begins with;
- **shapes**: a word written as consonants and vowels, ``cvccvc``.
"""

from collections import Counter

VOWELS = frozenset("aeiou")  # y counts as a consonant: "yes", "yak"


def ngrams(word: str, size: int) -> list[str]:
    """Every run of ``size`` letters in the word, overlapping, repeats kept.

    ``"banana"`` has the pairs ``ba an na an na``: *an* and *na* each
    turn up twice, and both times count. Slicing ``word[i:i + size]``
    at every starting position gets them all.
    """
    return [word[i : i + size] for i in range(len(word) - size + 1)]


def count_ngrams(words: list[str], size: int) -> Counter:
    """Count every ``size``-letter run across all the words."""
    counts: Counter = Counter()
    for word in words:
        counts.update(ngrams(word, size))
    return counts


def count_starts(words: list[str], size: int = 2) -> Counter:
    """Count how often each ``size``-letter run begins a word."""
    return Counter(word[:size] for word in words if len(word) >= size)


def cv_map(text: str) -> str:
    """Write the text as consonants and vowels: ``"riddle"`` → ``"cvcccv"``."""
    return "".join("v" if letter in VOWELS else "c" for letter in text)


def common_shapes(
    words: list[str],
    length: int,
    coverage: float = 0.95,
) -> set[str]:
    """The consonant-vowel shapes that most words of this length have.

    Shapes are taken most common first, until together they cover
    ``coverage`` of the dictionary's words that long. The rare shapes
    left over (like ``ccccvvvv``) are the ones a made-up word shouldn't
    have either.
    """
    shapes = Counter(cv_map(word) for word in words if len(word) == length)
    wanted = coverage * shapes.total()
    kept: set[str] = set()
    covered = 0
    for shape, count in shapes.most_common():
        if covered >= wanted:
            break
        kept.add(shape)
        covered += count
    return kept


def pair_table(letters: str, pair_counts: Counter) -> dict[str, float]:
    """Share of each pair you could make from ``letters``, as a percentage.

    Only pairs built from the given letters are included (a letter pairs
    with itself only if it appears twice), and the shares add up to 100:
    it's the chart of "which of *these* pairs does English like?".
    """
    available = Counter(letters)
    pairs = [
        first + second
        for first in sorted(available)
        for second in sorted(available)
        if first != second or available[first] > 1
    ]
    total = sum(pair_counts[pair] for pair in pairs) or 1
    return {pair: 100 * pair_counts[pair] / total for pair in pairs}
