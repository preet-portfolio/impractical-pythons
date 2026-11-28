"""Find anagrams: words made from exactly the same letters, shuffled.

Two words are anagrams when they use the same letters the same number
of times. Sorting makes that easy to check: *listen* and *silent* both
sort to ``eilnst``. That sorted string is the word's *key*, a fingerprint
every anagram of it shares.

There are two ways to use the key here, on purpose:

* ``find_anagrams`` walks the whole dictionary every time you ask,
  comparing keys one word at a time. Simple, and fine for one word.
* ``anagram_families`` does that walk once, filing every word under its
  key in a dictionary. After that, looking up a word's anagrams is a
  single jump, however big the word list is.
"""

from collections import defaultdict

Families = dict[str, list[str]]


def letters_only(text: str) -> str:
    """Lowercase the text and keep only its letters.

    Names arrive with capitals, spaces and hyphens ("Mary-Jo"), but only
    the letters matter for an anagram.
    """
    return "".join(char for char in text.lower() if char.isalpha())


def letter_key(text: str) -> str:
    """Return the text's letters in alphabetical order: its anagram key.

    ``sorted`` happily takes a string and hands back a list of its
    characters in order; ``"".join`` glues them back into one string, which
    (unlike a list) can be a dictionary key.
    """
    return "".join(sorted(letters_only(text)))


def is_anagram(first: str, second: str) -> bool:
    """Say whether two different words share exactly the same letters."""
    if letters_only(first) == letters_only(second):
        return False  # a word isn't an anagram of itself
    return letter_key(first) == letter_key(second)


def find_anagrams(word: str, words: list[str]) -> list[str]:
    """Search the whole word list for anagrams of ``word``, one at a time.

    The key of ``word`` is worked out once, before the loop, so each
    dictionary word costs one sort and one comparison.
    """
    target = letters_only(word)
    key = letter_key(word)
    matches = []
    for other in words:
        if other != target and letter_key(other) == key:
            matches.append(other)
    return matches


def anagram_families(words: list[str]) -> Families:
    """File every word under its key, so any lookup is instant later.

    ``defaultdict(list)`` makes an empty list the first time a key is
    used, which saves an "is this key here yet?" check for every word.
    Only keys with two or more words are kept: a family needs relatives.
    """
    index: defaultdict[str, list[str]] = defaultdict(list)
    for word in words:
        index[letter_key(word)].append(word)
    return {key: family for key, family in index.items() if len(family) > 1}


def anagrams_from_families(word: str, families: Families) -> list[str]:
    """Look up ``word``'s anagrams in a ready-made index.

    ``dict.get`` returns the default (an empty list) when the key isn't
    there, rather than raising ``KeyError``.
    """
    target = letters_only(word)
    family = families.get(letter_key(word), [])
    return [member for member in family if member != target]


def biggest_families(families: Families, count: int = 8) -> list[list[str]]:
    """Return the largest families, biggest first.

    The sort key is a tuple: ``-len(fam)`` puts big families first, then
    the family's own words break ties, so the result never changes.
    """
    ranked = sorted(families.values(), key=lambda fam: (-len(fam), fam))
    return ranked[:count]


def menu_stats(words: list[str], families: Families) -> dict:
    """Fun facts about the dictionary's anagrams, for the café board."""
    in_families = sum(len(family) for family in families.values())
    longest = max(families.values(), key=lambda fam: len(fam[0]), default=[])
    return {
        "words": len(words),
        "families": len(families),
        "in_families": in_families,
        "biggest": biggest_families(families, 1)[0] if families else [],
        "longest": longest,
    }
