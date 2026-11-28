"""Hide a secret in the blank lines of an innocent letter, in white ink.

The cover letter is the one anybody sees. Its blank lines (the gaps
between paragraphs) aren't wasted: each one can carry a line of the
secret, written in ink the same colour as the paper. On screen and on a
printout the letter looks exactly the same.

Two rules from the book keep the trick invisible:

* the secret's lines are packed tight (its own blank lines are dropped),
  so it needs as few hiding places as possible;
* every secret line must fit on one line of the page, or it wraps and
  the gap it sits in grows taller than the others.

The challenge version, ``between_words``, hides one character in each
space between the words of a typewritten line instead.
"""

import base64
import json

from decency import NOT_ON_THE_PIER, nothing_rude_inside

LONGEST_LINE = 70  # a secret line longer than this would wrap on the page
LONGEST_LETTER = 3000  # characters, for anything typed on the page or sent in a link
MOST_LINES = 60


class InkProblem(ValueError):
    """The letter or the secret can't be used as given."""


class NotEnoughRoom(InkProblem):
    """The cover letter has too few blank lines for the secret."""

    def __init__(self, add: int):
        """Remember how many blank lines are missing."""
        self.add = add
        lines = "line" if add == 1 else "lines"
        super().__init__(f"Not enough room: add {add} more blank {lines} to the letter.")


def letter_lines(text: str) -> list[str]:
    """Split a letter into lines, with blank space at the line ends tidied away.

    Blank lines at the very end are kept: like the book's tip of pressing
    Enter a few times under the signature, they're extra hiding places.
    """
    return [line.rstrip() for line in text.lstrip("\n").splitlines()]


def secret_lines(text: str) -> list[str]:
    """The secret's lines, with its own blank lines dropped (fewer hiding places needed)."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def blank_lines(cover: list[str]) -> int:
    """How many blank lines the cover letter has: each one is a hiding place."""
    return sum(1 for line in cover if not line.strip())


def room_check(cover: list[str], secret: list[str]) -> dict:
    """Is there room? The book's practice project, as numbers the page can say.

    Returns ``{"fits", "blanks", "needed", "add"}``: ``add`` is how many
    blank lines to put in the letter (0 if it fits).
    """
    blanks, needed = blank_lines(cover), len(secret)
    return {
        "fits": blanks >= needed,
        "blanks": blanks,
        "needed": needed,
        "add": max(0, needed - blanks),
    }


def interleave(cover: list[str], secret: list[str]) -> list[dict]:
    """Fill the cover letter's blank lines with the secret, in order.

    Returns one ``{"text", "hidden"}`` per line of the finished letter.
    Blank lines left over once the secret runs out stay blank. Raises
    ``NotEnoughRoom`` (saying how many lines to add) if it doesn't fit.
    """
    check = room_check(cover, secret)
    if not check["fits"]:
        raise NotEnoughRoom(check["add"])
    waiting = iter(secret)
    letter = []
    for line in cover:
        hidden = next(waiting, None) if not line.strip() else None
        letter.append(
            {"text": hidden, "hidden": True}
            if hidden is not None
            else {"text": line, "hidden": False}
        )
    return letter


def as_plain_text(letter: list[dict]) -> str:
    """The letter saved as plain text: colour is lost, so the ink shows."""
    return "\n".join(line["text"] for line in letter)


# ------------------------------------------------------------ checking input


def words_of(text: str) -> list[str]:
    """Lower-case words, for the "not on the pier" check."""
    return "".join(ch if ch.isalpha() else " " for ch in text.lower()).split()


def check_text(text: str, what: str) -> None:
    """Raise ``InkProblem`` if ``text`` is too long or not for the pier."""
    if len(text) > LONGEST_LETTER:
        raise InkProblem(f"The {what} is too long: {LONGEST_LETTER} characters at most.")
    if len(text.splitlines()) > MOST_LINES:
        raise InkProblem(f"The {what} is too long: {MOST_LINES} lines at most.")
    if NOT_ON_THE_PIER.intersection(words_of(text)) or not nothing_rude_inside([text.lower()]):
        raise InkProblem(f"The shop won't sell ink for that {what}. Try kinder words.")


def long_lines(secret: list[str]) -> list[int]:
    """Which secret lines (counting from 1) are long enough to wrap and give the game away."""
    return [n for n, line in enumerate(secret, 1) if len(line) > LONGEST_LINE]


# ------------------------------------------------------------- share a letter


def pack_letter(letter: list[dict], title: str) -> str:
    """Pack a finished letter into link-safe text: JSON, then URL-safe Base64.

    The ink lines travel scrambled; the key never goes in the link.
    """
    payload = {"t": title, "l": [[line["text"], int(line["hidden"])] for line in letter]}
    packed = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(packed).decode("ascii").rstrip("=")


def unpack_letter(token: str) -> dict:
    """Unpack a letter link into ``{"title", "letter"}``, checking every part."""
    try:
        padded = token + "=" * (-len(token) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        title, lines = payload["t"], payload["l"]
        letter = [{"text": str(text), "hidden": bool(hidden)} for text, hidden in lines]
    except (ValueError, KeyError, TypeError) as error:
        raise InkProblem("The letter got smudged on the way. Ask for the link again.") from error
    if not isinstance(title, str) or len(title) > 40 or not letter or len(letter) > MOST_LINES:
        raise InkProblem("That link doesn't hold a letter the shop can show.")
    check_text(title + "\n" + as_plain_text(letter), "letter")
    return {"title": title, "letter": letter}


# ------------------------------------------- the challenge: ink between words


def between_words(cover: str, secret: str) -> list[dict]:
    """Hide ``secret`` in the spaces between the words of a typewritten line.

    On a typewriter every character is the same width, so a white letter
    in place of a space looks exactly like the space. One secret
    character per gap; spaces in the secret are dropped, and gaps left
    over stay ordinary spaces. Returns ``{"text", "hidden"}`` pieces.
    """
    words = cover.split()
    ink = "".join(secret.split())
    gaps = len(words) - 1
    if len(ink) > gaps:
        more = len(ink) - gaps
        words_needed = "word" if more == 1 else "words"
        raise InkProblem(f"Not enough spaces: the line needs {more} more {words_needed}.")
    pieces = []
    for n, word in enumerate(words):
        pieces.append({"text": word, "hidden": False})
        if n < gaps:
            pieces.append(
                {"text": ink[n], "hidden": True} if n < len(ink) else {"text": " ", "hidden": False}
            )
    return pieces


def read_between_words(pieces: list[dict]) -> str:
    """The secret from a typewritten line: every hidden character, in order."""
    return "".join(piece["text"] for piece in pieces if piece["hidden"])
