"""The pier telegraph office's code book, filler words and sample telegrams.

A route cipher only shuffles words; anyone who unshuffles it can read
the message. So the clerks also swap the words that matter most for
harmless-looking code words, and pad the grid with filler. Unshuffle a
coded telegram and you get "meet GULL by BANDSTAND", which still gives
nothing away without the code book.
"""

import random

CODEBOOK = {
    "GULL": "the manager",
    "WHELK": "tuesday",
    "BANDSTAND": "the lighthouse",
    "BUCKET": "midnight",
    "DONKEY": "the money",
}

# Harmless words to fill the last pigeonholes.
FILLER = [
    "PEBBLE",
    "DECKCHAIR",
    "SANDCASTLE",
    "FLAG",
    "SPADE",
    "KITE",
    "ROCKPOOL",
]

SAMPLE = " ".join(
    (
        "Meet the manager by the lighthouse",
        "on Tuesday at midnight and bring the money",
    ),
)

# The telegram on the counter waiting to be cracked: its words, grid and route.
MYSTERY = {
    "text": "Tell the manager the money is hidden under the lighthouse "
    "collect it at midnight on Tuesday",
    "cols": 5,
    "rows": 3,
    "key": [1, -2, 3, -4, 5],
    "seed": 6,
}

# Practice: deckchair tickets 1 to 15 make it obvious when the route is right.
TICKETS = {
    "words": [str(n) for n in range(1, 16)],
    "cols": 5,
    "rows": 3,
    "key": [-1, 2, -3, 4, -5],
}


def plain_words(text: str) -> list[str]:
    """Split text into lowercase words, dropping punctuation around them."""
    words = (word.strip(".,;:!?\"'()").lower() for word in text.split())
    return [word for word in words if word]


def encode(text: str) -> list[str]:
    """Swap the code book's phrases for code words, longest phrase first.

    Longest first, so that "the manager" becomes GULL before a shorter
    phrase could claim its "the".
    """
    words = plain_words(text)
    phrases = sorted(CODEBOOK.items(), key=lambda item: -len(item[1].split()))
    coded = []
    i = 0
    while i < len(words):
        for code, phrase in phrases:
            size = len(phrase.split())
            if words[i : i + size] == phrase.split():
                coded.append(code)
                i += size
                break
        else:  # no phrase starts here: keep the word as it is
            coded.append(words[i])
            i += 1
    return coded


def decode(words: list[str]) -> str:
    """Turn code words back into what they mean, and drop trailing filler."""
    kept = list(words)
    while kept and kept[-1].upper() in FILLER:
        kept.pop()
    return " ".join(CODEBOOK.get(word.upper(), word) for word in kept)


def grid_options(count: int, widest: int = 8) -> list[dict]:
    """Every grid that holds ``count`` words with less than a row of filler.

    Each option is ``{"cols", "rows", "filler"}``: a 4 × 3 grid for 11
    words needs 1 filler word. Grids one column wide or one row tall are
    left out, because they don't scramble anything.
    """
    options = []
    for cols in range(2, widest + 1):
        rows = -(-count // cols)  # dividing and rounding up
        if rows >= 2:
            filler = cols * rows - count
            options.append({"cols": cols, "rows": rows, "filler": filler})
    return [option for option in options if option["filler"] < option["cols"]]


def pad(
    words: list[str],
    cols: int,
    rows: int,
    seed: int | None = None,
) -> list[str]:
    """Fill the grid's empty pigeonholes with filler words."""
    missing = cols * rows - len(words)
    if missing < 0:
        holes = cols * rows
        raise ValueError(f"{len(words)} words won't fit in {holes} holes")
    rng = random.Random(seed)
    if missing <= len(FILLER):
        extra = rng.sample(FILLER, missing)  # all different words
    else:
        extra = rng.choices(FILLER, k=missing)
    return words + extra
