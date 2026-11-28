"""Send a telegram to a friend as one link, without giving the answer away.

The link carries the scrambled telegram and a *fingerprint* of the
right answer, but not the key and not the message in order. The
friend's browser can tell them when they've got it right by
fingerprinting their own attempt and comparing, without ever knowing
the answer in advance.

A fingerprint here is the start of a SHA-256 hash: the same words always
give the same fingerprint, and you can't run it backwards to get the
words. (Someone determined could still try every route and compare
fingerprints. That's the brute-force attack later in this chapter.)
"""

import base64
import hashlib
import json

from route import Key, TelegramProblem, Words, encrypt, factors

MAX_WORDS = 64  # a telegram, not a novel
MAX_WORD_LENGTH = 30


class ChallengeProblem(TelegramProblem):
    """A challenge link that can't be read (cut short, or tampered with)."""


def fingerprint(words: Words) -> str:
    """A short, one-way summary of the words in their right order."""
    digest = hashlib.sha256(" ".join(words).encode("utf-8")).hexdigest()
    return digest[:12]


def make_challenge(words: Words, cols: int, rows: int, key: Key) -> str:
    """Pack a telegram into text that's safe to put in a link.

    JSON turns the data into text; URL-safe Base64 turns that text into
    letters, digits, ``-`` and ``_`` only, so nothing in it can break a
    link. The ``=`` padding Base64 adds at the end isn't needed, so it's
    dropped to keep links short.
    """
    payload = {"t": encrypt(words, cols, rows, key), "f": fingerprint(words)}
    packed = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(packed).decode("ascii").rstrip("=")


def looks_like_telegram(cipher: object) -> bool:
    """Whether a link's contents are a list of short words that fit a rack.

    The word count must have a factor, or no rack (other than one row or
    one column, which hide nothing) could have held it.
    """
    if not isinstance(cipher, list) or not 4 <= len(cipher) <= MAX_WORDS:
        return False
    for word in cipher:
        if not isinstance(word, str) or not 0 < len(word) <= MAX_WORD_LENGTH:
            return False
    return bool(factors(len(cipher)))


def read_challenge(token: str) -> dict:
    """Unpack a challenge link's text into ``{"cipher", "fingerprint"}``.

    Anything can arrive in a link, so check everything and raise
    ``ChallengeProblem`` with a plain reason instead of crashing.
    """
    try:
        padded = token + "=" * (-len(token) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        cipher, check = payload["t"], payload["f"]
    except (ValueError, KeyError, TypeError) as error:
        message = "The link got smudged on the way. Ask for it again."
        raise ChallengeProblem(message) from error
    if not looks_like_telegram(cipher):
        message = "That link doesn't hold a telegram the office can read."
        raise ChallengeProblem(message)
    if not isinstance(check, str) or len(check) != 12:
        message = "That link is missing its seal. Ask for it again."
        raise ChallengeProblem(message)
    return {"cipher": cipher, "fingerprint": check}


def is_solved(words: Words, check: str) -> bool:
    """Whether these words, in this order, are the sender's message."""
    return fingerprint(words) == check
