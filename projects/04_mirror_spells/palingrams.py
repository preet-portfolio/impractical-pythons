"""Two-word spells: word pairs that read the same backwards (palingrams).

Take *nurses run*. All its letters, "nursesrun", reversed are the same
letters again. Look at the longer word, the "core", and it splits in two:

    n u r | s e s      the front, read backwards, is a real word: "run"
    ^^^^^   ^^^^^      the rest is a palindromic run of its own: "ses"

So "nurses" plus "run" is a spell. The partner can also go *first*:
in *stir grits* the core is "grits" = "g" (a palindromic run) + "rits"
(which is "stir" backwards). The run can even be empty, which gives
pairs like *stab bats*, where one word is simply the other reversed.

Every cut of every word is tried, and each try asks "is this piece a
real word?" That question is asked about a million times, so the kind
of container holding the words decides the speed: see ``speed_test.py``.
"""

from collections.abc import Collection, Iterable

Pair = tuple[str, str]


def _is_run(letters: str) -> bool:
    """Return True for a palindromic run; an empty run counts too."""
    return letters == letters[::-1]


def _spells(words: Iterable[str], vocab: Collection[str]) -> list[Pair]:
    """Find every two-word spell, checking partners with ``in vocab``.

    The logic is written once; only the container passed as ``vocab``
    changes between the fast and the slow version.
    """
    found: set[Pair] = set()  # a set drops duplicate pairs
    for core in words:
        if len(core) < 2:
            continue
        for cut in range(len(core) + 1):
            head, tail = core[:cut], core[cut:]
            # Core first ("nurses run"): head backwards + palindromic tail.
            partner = head[::-1]
            if partner and _is_run(tail) and partner in vocab:
                found.add((core, partner))
            # Core second ("stir grits"): palindromic head + tail backwards.
            partner = tail[::-1]
            if partner and _is_run(head) and partner in vocab:
                found.add((partner, core))
    return sorted(found)


def two_word_spells(words: Iterable[str]) -> list[Pair]:
    """Find every two-word spell in a word list, quickly.

    ``set(words)`` builds a hash table once; after that, ``partner in
    vocab`` jumps straight to the right slot instead of reading the
    whole list.
    """
    vocab = set(words)
    return _spells(vocab, vocab)


def two_word_spells_slow(words: list[str]) -> list[Pair]:
    """Find the same spells the slow way, looking partners up in a list.

    ``partner in words`` on a list compares against every word until it
    finds a match (or reaches the end). Kept on purpose, to profile it.
    """
    return _spells(words, words)


def is_palindrome_recursive(letters: str) -> bool:
    """Check a palindrome by peeling off the outer letters, recursively.

    A string of 0 or 1 letters is a palindrome. Otherwise the first and
    last letters must match *and* the middle must be a palindrome, which
    is the same question again on a smaller string.
    """
    if len(letters) < 2:
        return True
    if letters[0] != letters[-1]:
        return False
    return is_palindrome_recursive(letters[1:-1])
