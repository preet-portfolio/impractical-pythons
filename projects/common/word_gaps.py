"""Put the spaces back into a run of letters, using a dictionary.

Shared by Pier Telegraph (rail fence letters) and the Postcard Rack
(letters hidden in a postcard).

A rail fence telegram arrives as one long string, LETUSCROSSTHEPIER,
because the spaces were thrown away before sending. A person reads
"let us cross the pier" without thinking; a program has to search.

Trying every way to cut the letters into pieces is hopeless (a
40-letter message has over 500 billion ways). **Dynamic programming**
saves the day: work left to right, and for every position remember only
the *best* way to split the letters up to there. The best split of the
first 10 letters is built from the best split of some shorter start plus
one more word, so each answer is worked out once and reused.
"""

from collections.abc import Iterable

# The shared word list leaves out single letters, so add the two real
# one-letter words back in.
ONE_LETTER_WORDS = {"a", "i"}
LONGEST_WORD = 20

# Little words that turn up in almost every sentence. When two splits are
# otherwise as good, the one using more of these usually reads right:
# "pier at" beats "pie rat", "is under" beats "i sunder".
EVERYDAY = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "do", "for", "from", "has",
    "have", "he", "her", "his", "if", "in", "is", "it", "its", "me", "my", "no", "not",
    "of", "on", "or", "our", "she", "so", "than", "that", "the", "their", "them",
    "there", "they", "this", "to", "too", "up", "us", "was", "we", "were", "what",
    "when", "who", "will", "with", "you", "your",
}  # fmt: skip


def word_set(words: Iterable[str]) -> set[str]:
    """A set of lowercase dictionary words, for fast ``in`` checks."""
    return {word.lower() for word in words} | ONE_LETTER_WORDS


def split_words(letters: str, words: set[str]) -> list[str]:
    """Split ``letters`` into dictionary words where it can.

    The best split covers the most letters with real words, then uses
    the fewest pieces (so "seagulls" beats "sea gulls"), then the most
    everyday words. Letters no word explains are kept, in capitals, so
    nothing is ever lost.

    ``best[i]`` holds the score and pieces for the first ``i`` letters.
    Scores are tuples ``(letters covered, -pieces, everyday words)``:
    Python compares tuples item by item, so ``max`` tries each rule in
    turn and only looks at the next one to break a tie.
    """
    text = letters.lower()
    best: list[tuple[tuple[int, int, int], list[str]]] = [((0, 0, 0), [])]
    for end in range(1, len(text) + 1):
        (covered, pieces, everyday), parts = best[end - 1]  # one stray letter
        stray = text[end - 1].upper()
        options = [((covered, pieces - 1, everyday), [*parts, stray])]
        for start in range(max(0, end - LONGEST_WORD), end):
            word = text[start:end]
            if word in words:
                (covered, pieces, everyday), parts = best[start]
                score = (covered + len(word), pieces - 1, everyday + (word in EVERYDAY))
                options.append((score, [*parts, word]))
        best.append(max(options, key=lambda option: option[0]))
    return join_strays(best[-1][1])


def join_strays(parts: list[str]) -> list[str]:
    """Glue neighbouring unexplained letters (capitals) into one piece."""
    joined: list[str] = []
    for part in parts:
        if joined and part.isupper() and joined[-1].isupper():
            joined[-1] += part
        else:
            joined.append(part)
    return joined


def coverage(letters: str, words: set[str]) -> float:
    """The share of the letters (0 to 1) that fall inside real words."""
    if not letters:
        return 0.0
    parts = split_words(letters, words)
    inside = sum(len(part) for part in parts if not part.isupper())
    return inside / len(letters)
