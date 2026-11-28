"""Write a postcard that hides a note: a null cipher, the other way round.

Hiding letters inside a letter that still makes sense is very hard: every
sentence has to stay on topic *and* put the right letter in the right
place. A list gets round that, because nobody expects a list to make
sense. So these postcards are a list of Nan's Scrabble words:

    Nan won at Scrabble again with these words: alpaca, sherbet, ...

The note's letters sit at one agreed place in each word (the 3rd letter,
say). The colon and every comma restart the count, so the reading glass
in ``null_finder`` can read the note back with its punctuation rule: the
3rd letter after each punctuation mark.

The cover line has no punctuation of its own before the colon on
purpose: a mark there would start the count early and add stray letters.

A postcard can travel as a link. The link holds the card's text and
names, packed with JSON and URL-safe Base64, and never the note itself:
the friend has to find it.
"""

import base64
import json
import random
import string

from decency import NOT_ON_THE_PIER, nothing_rude_inside
from null_finder import SHORTEST

COVER = "Nan won at Scrabble again with these words"
POSITIONS = (2, 3, 4)  # which letter of each word carries the note
SHORTEST_WORD, LONGEST_WORD = 5, 8  # long enough to look like a good Scrabble word
LONGEST_NOTE = 40  # letters: a postcard, not a novel
LONGEST_CARD = 600  # characters a link may carry
LONGEST_NAME = 20


# Nan's list goes on a public postcard, so it is stricter than the pier's
# filter: any word containing one of these stems is left in the bag. It
# throws out some innocent words too ("niggle", "begun"), which is fine:
# the list only needs enough words, not every word.
NOT_ON_A_POSTCARD = frozenset(
    """
    abort bastard bitch bomb bosom breast butt corpse crap cripple damn
    drug erotic fatso fetish gay genocid gun gypsy idiot incest insan
    kill lesbian lunatic massacr midget molest moron murder naked negro
    nigg nude obese orgasm pervert porn psycho pussy queer rape raping
    retard rifle sex shoot slave stab strangl suicid terror testic
    toerag tortur vagin whore
    """.split()  # noqa: SIM905
)


class NoteProblem(ValueError):
    """A note that can't be hidden, or a link that can't be read."""


def note_letters(note: str) -> str:
    """Just the letters of a note, lower case (the book's ``ascii_letters`` filter)."""
    return "".join(char for char in note if char in string.ascii_letters).lower()


def words_of(text: str) -> set[str]:
    """The words of a text, lower case and letters only, for the decency check."""
    return {note_letters(word) for word in text.split()}


def postcard_words_ok(text: str) -> bool:
    """Whether no word of ``text`` contains one of the postcard's banned stems."""
    return not any(stem in word for word in words_of(text) for stem in NOT_ON_A_POSTCARD)


def check_note(note: str) -> str:
    """Return the note's letters, or raise ``NoteProblem`` with a plain reason."""
    letters = note_letters(note)
    if len(letters) < SHORTEST:
        reason = f"Hide at least {SHORTEST} letters, or the glass can't tell it from luck."
        raise NoteProblem(reason)
    if len(letters) > LONGEST_NOTE:
        raise NoteProblem(f"That's {len(letters)} letters. Keep it to {LONGEST_NOTE} or fewer.")
    rude = NOT_ON_THE_PIER.intersection(words_of(note)) or not postcard_words_ok(note)
    if rude or not nothing_rude_inside([letters]):
        raise NoteProblem("Let's keep the rack family-friendly. Try another note.")
    return letters


def postcard_words(words: set[str] | list[str]) -> list[str]:
    """The words Nan is allowed to play: Scrabble-sized, and nothing unkind.

    ``nothing_rude_inside`` catches swear words hiding inside longer ones;
    ``NOT_ON_A_POSTCARD`` catches slurs and grim words the pier's
    shorter list lets through.
    """
    sized = [
        word
        for word in sorted(words)
        if SHORTEST_WORD <= len(word) <= LONGEST_WORD and word.isalpha() and word.islower()
    ]
    gentle = [word for word in sized if not any(stem in word for stem in NOT_ON_A_POSTCARD)]
    return nothing_rude_inside(gentle)


def words_by_letter(words: set[str] | list[str], position: int) -> dict[str, list[str]]:
    """Group Scrabble-sized words by the letter at ``position`` (counting from 1).

    Sorted, so a seeded ``random.Random`` picks the same words every time.
    """
    if position not in POSITIONS:
        raise NoteProblem(f"Hide the note in letter {', '.join(map(str, POSITIONS))} of each word.")
    groups: dict[str, list[str]] = {}
    for word in postcard_words(words):
        groups.setdefault(word[position - 1], []).append(word)
    return groups


def choose_words(
    letters: str, groups: dict[str, list[str]], position: int, seed: int | None = None
) -> list[str]:
    """Pick one word per letter from ``groups`` (made by ``words_by_letter``).

    No word is used twice. ``seed`` makes the choice repeatable; a new
    seed writes the same note into a different list. Kept apart from
    ``hide_note`` so a web page can group the dictionary once and reuse it.
    """
    rng = random.Random(seed)
    chosen: list[str] = []
    for letter in letters:
        options = [word for word in groups.get(letter, []) if word not in chosen]
        if not options:
            raise NoteProblem(f"Nan has no words with {letter!r} as letter {position}.")
        chosen.append(rng.choice(options))
    return chosen


def hide_note(
    note: str, words: set[str] | list[str], position: int = 3, seed: int | None = None
) -> list[str]:
    """Pick one word per letter of the note, each with that letter at ``position``."""
    return choose_words(check_note(note), words_by_letter(words, position), position, seed)


def write_card(chosen: list[str]) -> str:
    """The postcard's message: the cover line, then the list."""
    return f"{COVER}: {', '.join(chosen)}."


def write_postcard(
    note: str, words: set[str] | list[str], position: int = 3, seed: int | None = None
) -> str:
    """Hide ``note`` in a postcard of Scrabble words, ready to send."""
    return write_card(hide_note(note, words, position, seed))


def clean_name(name: object, fallback: str) -> str:
    """A short, tidy name for the card, or ``fallback`` if there isn't one."""
    if not isinstance(name, str):
        return fallback
    tidy = " ".join(name.split())[:LONGEST_NAME]
    return tidy or fallback


def pack_card(text: str, to: str, sender: str) -> str:
    """Pack a postcard into link-safe text: JSON, then URL-safe Base64."""
    payload = {"t": text, "to": to, "from": sender}
    packed = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(packed).decode("ascii").rstrip("=")


def unpack_card(token: str) -> dict:
    """Unpack a postcard link into ``{"text", "to", "sender"}``.

    Anything can arrive in a link, so every part is checked, and a
    problem comes back as ``NoteProblem`` with a plain reason.
    """
    try:
        padded = token + "=" * (-len(token) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
        text = payload["t"]
    except (ValueError, KeyError, TypeError) as error:
        reason = "The postcard got smudged in the post. Ask for the link again."
        raise NoteProblem(reason) from error
    if not isinstance(text, str) or not 0 < len(text) <= LONGEST_CARD:
        raise NoteProblem("That link doesn't hold a postcard the rack can show.")
    if NOT_ON_THE_PIER.intersection(words_of(text)) or not nothing_rude_inside([text.lower()]):
        raise NoteProblem("That postcard isn't one for the rack.")
    return {
        "text": text,
        "to": clean_name(payload.get("to"), "you"),
        "sender": clean_name(payload.get("from"), "a friend"),
    }
