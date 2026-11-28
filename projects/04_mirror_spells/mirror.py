"""Find palindromes: words and phrases that read the same both ways.

The whole test is one slice. ``text[::-1]`` means "start to end, taking
steps of -1", which walks the string backwards, so a palindrome is any
text equal to its own reverse. Everything else here is about deciding
*what* to compare (letters only, ignoring case) and presenting the
results.
"""

from collections import Counter


def letters_only(text: str) -> str:
    """Keep only the letters, lowercased: "No, Don!" -> "nodon"."""
    return "".join(char for char in text.lower() if char.isalpha())


def is_palindrome(text: str) -> bool:
    """Return True if the letters read the same forwards and backwards.

    Spaces, punctuation and capitals are ignored, so whole phrases count.
    Text with no letters at all isn't a palindrome: there's nothing to
    reflect.
    """
    letters = letters_only(text)
    return bool(letters) and letters == letters[::-1]


def find_palindromes(words: list[str], min_length: int = 2) -> list[str]:
    """Return the words that are palindromes, in their original order.

    One-letter "words" (a, I, and the letter headings some dictionaries
    include) are trivially palindromes, so ``min_length`` leaves them out.
    """
    long_enough = [word for word in words if len(word) >= min_length]
    return [word for word in long_enough if is_palindrome(word)]


def spellbook_stats(words: list[str]) -> dict[str, object]:
    """Summarise a dictionary's palindromes for the page and the CLI."""
    spells = find_palindromes(words)
    longest = max((len(spell) for spell in spells), default=0)
    by_length = Counter(len(spell) for spell in spells)
    return {
        "words": len(words),
        "spells": spells,
        "count": len(spells),
        "percent": 100 * len(spells) / len(words) if words else 0.0,
        "longest": [spell for spell in spells if len(spell) == longest],
        "by_length": dict(sorted(by_length.items())),
    }


def reflect(text: str) -> dict[str, object]:
    """Pair letters from both ends inward, for the magic mirror.

    The first letter is checked against the last, the second against the
    second-to-last, and so on to the middle. ``broken`` is the index of
    the first pair that doesn't match, or None if every pair does.
    """
    letters = letters_only(text)
    half = len(letters) // 2
    # In the reversed copy, position i holds letter i's mirror image.
    back = letters[::-1]
    pairs = [{"left": letters[i], "right": back[i]} for i in range(half)]
    broken = next(
        (i for i, pair in enumerate(pairs) if pair["left"] != pair["right"]),
        None,
    )
    return {
        "letters": letters,
        "reversed": back,
        "pairs": pairs,
        "middle": letters[half] if len(letters) % 2 else "",
        "broken": broken,
        "spell": is_palindrome(text),
    }
