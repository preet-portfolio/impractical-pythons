"""The Vigenère cipher: scramble a message with a keyword, and unscramble it.

The keyword is written over the message again and again, one key letter
above each message letter. Each key letter says how far along the
alphabet to shift the letter under it: A shifts by 0, B by 1, ... Z by
25. That's the same as reading across the key letter's row of the
Vigenère table (the "tableau").

Only letters are shifted, and the key only moves on over letters, so
spaces, numbers and punctuation pass straight through. That's why
``spell_out`` exists: "42" would otherwise give the game away.
"""

import string

ALPHABET = string.ascii_uppercase


class KeyProblem(ValueError):
    """The keyword can't be used (no letters in it)."""


def clean_key(key: str) -> str:
    """The keyword's letters, in capitals. Raise ``KeyProblem`` if there are none."""
    letters = "".join(ch for ch in key.upper() if ch in ALPHABET)
    if not letters:
        raise KeyProblem("The key needs at least one letter, like PUFFIN.")
    return letters


def _shift(text: str, key: str, direction: int) -> str:
    """Shift each letter by its key letter: forwards to scramble, backwards to read."""
    key = clean_key(key)
    out = []
    k = 0  # which key letter is next: it moves on over letters only
    for ch in text:
        upper = ch.upper()
        if upper not in ALPHABET:
            out.append(ch)
            continue
        shift = ALPHABET.index(key[k % len(key)]) * direction
        moved = ALPHABET[(ALPHABET.index(upper) + shift) % 26]
        out.append(moved if ch.isupper() else moved.lower())
        k += 1
    return "".join(out)


def encrypt(text: str, key: str) -> str:
    """Scramble ``text`` with ``key``, keeping capitals and everything that isn't a letter."""
    return _shift(text, key, 1)


def decrypt(text: str, key: str) -> str:
    """Unscramble ``text`` that was scrambled with ``key``."""
    return _shift(text, key, -1)


def key_over(text: str, key: str) -> str:
    """The key written over the message, one key letter above each letter (spaces elsewhere)."""
    key = clean_key(key)
    out, k = [], 0
    for ch in text:
        if ch.upper() in ALPHABET:
            out.append(key[k % len(key)])
            k += 1
        else:
            out.append(" ")
    return "".join(out)


def tableau_row(key_letter: str) -> str:
    """The table row for one key letter: the alphabet, starting at that letter."""
    start = ALPHABET.index(clean_key(key_letter)[0])
    return ALPHABET[start:] + ALPHABET[:start]


# ------------------------------------------------- numbers give the game away

ONES = "zero one two three four five six seven eight nine".split()  # noqa: SIM905
TEENS = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()  # noqa: SIM905
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()  # noqa: SIM905
SYMBOLS = {"%": "percent", "&": "and", "£": "pounds", "$": "dollars", "@": "at"}


def number_words(n: int) -> str:
    """Spell out a whole number below a million: 42 -> "forty two"."""
    if n < 10:
        return ONES[n]
    if n < 20:
        return TEENS[n - 10]
    if n < 100:
        tens, ones = divmod(n, 10)
        return TENS[tens] + ("" if ones == 0 else " " + ONES[ones])
    if n < 1000:
        hundreds, rest = divmod(n, 100)
        return ONES[hundreds] + " hundred" + ("" if rest == 0 else " and " + number_words(rest))
    if n < 1_000_000:
        thousands, rest = divmod(n, 1000)
        tail = "" if rest == 0 else (" and " if rest < 100 else " ") + number_words(rest)
        return number_words(thousands) + " thousand" + tail
    return " ".join(ONES[int(d)] for d in str(n))  # too big to say: read it digit by digit


def spell_out(text: str) -> str:
    """Write numbers and symbols as words, so the scramble hides them too."""
    out, digits = [], ""
    for ch in text + " ":  # the extra space flushes a number at the very end
        if ch.isdigit() and ch in string.digits:
            digits += ch
            continue
        if digits:
            out.append(number_words(int(digits)))
            digits = ""
        if ch in SYMBOLS:
            out.append(" " + SYMBOLS[ch] if out and not out[-1].endswith(" ") else SYMBOLS[ch])
        else:
            out.append(ch)
    return "".join(out)[:-1]
