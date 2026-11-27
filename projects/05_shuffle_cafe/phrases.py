"""Build an anagram *phrase* from a name, one word at a time.

A computer can list every word hiding in a name, but only a person can
tell which ones make a phrase worth keeping. So the work is split: the
code offers the words that still fit, a human picks one, and the code
works out what's left. Repeat until every letter is used.

The tool for "does this word fit?" is ``collections.Counter``, a dict
that counts things. Count the letters of the word and of the name, take
one from the other, and see if anything is left over.

Everything here is stateless: the phrase so far is just a list of the
words chosen, passed in each time. That makes undo trivial (drop the
last word) and lets the command line and the web page share the code.
"""

from collections import Counter

from anagrams import letters_only


def letter_count(text: str) -> Counter:
    """Count each letter in the text, ignoring case, spaces and hyphens.

    ``Counter("banana")`` gives ``{"a": 3, "n": 2, "b": 1}``.
    """
    return Counter(letters_only(text))


def fits(word: str, letters: Counter) -> bool:
    """Say whether ``word`` can be made from ``letters``.

    Subtracting one Counter from another keeps only the counts that stay
    above zero. Whatever survives ``word - letters`` is a letter the word
    needs more of than we have. An empty Counter is falsy, so ``not``
    reads as "nothing missing".
    """
    return not letter_count(word) - letters


def remaining(name: str, chosen: list[str]) -> Counter | None:
    """Return the letters of ``name`` left after spelling the chosen words.

    Returns ``None`` if the chosen words need a letter the name doesn't
    have (or has too few of). That's how a typed choice gets checked.
    """
    left = letter_count(name)
    for word in chosen:
        needed = letter_count(word)
        if needed - left:
            return None
        left -= needed
    return left


def words_that_fit(letters: Counter, words: list[str]) -> list[str]:
    """List the dictionary words that can be made from ``letters``.

    Two cheap checks go first, so most words are turned away before a
    Counter is ever built: a word can't be longer than the letters we
    have, and can't use a letter we don't have at all. Longest words come
    first, because long words make the most interesting phrases.
    """
    size = letters.total()
    have = set(letters)

    def could_fit(word: str) -> bool:
        return len(word) <= size and set(word) <= have and fits(word, letters)

    found = [word for word in words if could_fit(word)]
    return sorted(found, key=lambda word: (-len(word), word))


def spell_out(letters: Counter) -> str:
    """Write the remaining letters as one alphabetical string, for display.

    ``Counter.elements()`` repeats each letter as many times as it's
    counted, so ``{"b": 2, "o": 1}`` becomes ``"bbo"``.
    """
    return "".join(sorted(letters.elements()))


def phrase_status(
    name: str,
    chosen: list[str],
    words: list[str],
) -> dict | None:
    """Everything a screen needs to show the next step of the phrase.

    Returns ``None`` when ``chosen`` doesn't fit in the name.
    """
    left = remaining(name, chosen)
    if left is None:
        return None
    return {
        "name": name,
        "phrase": " ".join(chosen),
        "left": spell_out(left),
        "done": left.total() == 0,
        "options": words_that_fit(left, words) if left else [],
    }
