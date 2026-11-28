"""A new telegram on the counter every day, with no server to send it.

Everyone who opens the page on the same day should get the same puzzle,
so they can compare notes. Without a server, the date itself has to do
the choosing: turn the date into a number, use that number to pick a
message, and use it again as the seed for a ``random.Random``. The same
seed always rolls the same "random" route, on every computer.
"""

import random
from datetime import date

from codebook import encode, grid_options, pad, snuggest
from route import Key, Words, decrypt, encrypt

# The office's first day. Telegram No. 1 went out then.
OPENING_DAY = date(2026, 11, 1)

# Messages for the daily telegram. Code-book phrases ("the manager",
# "the money", "the lighthouse", "midnight", "Tuesday") turn into code
# words; nothing here uses a code word or a filler word on its own, or
# the decoder would mistake it for one.
DISPATCHES = [
    "Tell the manager the money is hidden under the lighthouse "
    + "collect it at midnight on Tuesday",
    "The manager is asleep in a deckchair so ice cream is free till midnight",
    "Someone painted the lighthouse pink and the manager is furious",
    "The money is buried under the third sandcastle from the pier",
    "Do not let the manager near the dodgems again on Tuesday",
    "The fortune teller says the money will arrive at midnight wearing a hat",
    "Abandon the crazy golf plan because the manager knows everything",
    "Meet me under the lighthouse at midnight and bring sun cream",
    "The seagulls have formed a union and want the money by Tuesday",
    "The pier organ only plays sea shanties after midnight so do not panic",
    "Count the money twice because the manager has learned a card trick",
    "Send more ice lollies the whole town is at the lighthouse for the sunset",
    "Hide the money in the candyfloss machine the manager never cleans it",
    "The manager won the sandcastle contest again and nobody knows how",
]

# Racks that make a fair puzzle: 3 to 5 columns (comfortable on a phone)
# and at least 3 rows, so every column has a top, a middle and a bottom.
COLUMNS = range(3, 6)
MIN_ROWS = 3


def telegram_number(day: date) -> int:
    """Count the days since the office opened: No. 1 on opening day."""
    return (day - OPENING_DAY).days + 1


def plain_route_hits(words: Words, cols: int, rows: int, key: Key) -> int:
    """How many words a lazy guess gets right.

    The lazy guess is the right rack read straight down every column, in
    order (``1 2 3 ...``). A good daily route should leave most words in
    the wrong pigeonhole for that guess, or the puzzle is over in a tap.
    """
    cipher = encrypt(words, cols, rows, key)
    guess = decrypt(cipher, cols, rows, list(range(1, cols + 1)))
    return sum(a == b for a, b in zip(guess, words, strict=True))


def scrambled_key(
    words: Words,
    cols: int,
    rows: int,
    rng: random.Random,
) -> Key:
    """A route that makes the lazy guess get at most a fifth of the words.

    Shuffle the columns and pick each direction at random, then try
    again if the lazy guess does too well. A ``for`` loop with a limit
    (rather than ``while True``) means it can never spin forever; after
    100 tries it settles for the best key it saw.
    """
    allowed = max(2, len(words) // 5)
    best, best_hits = [], len(words) + 1
    for _ in range(100):
        columns = list(range(1, cols + 1))
        rng.shuffle(columns)
        key = [column * rng.choice((1, -1)) for column in columns]
        hits = plain_route_hits(words, cols, rows, key)
        if hits < best_hits:
            best, best_hits = key, hits
        if hits <= allowed:
            break
    return best


def is_fair(option: dict) -> bool:
    """Whether a rack makes a fair daily puzzle (see ``COLUMNS``)."""
    return option["cols"] in COLUMNS and option["rows"] >= MIN_ROWS


def puzzle_rack(count: int) -> dict:
    """The tidiest rack for a daily puzzle of ``count`` words.

    Prefer the racks that make a fair puzzle; a message too short or
    too long for any of them just gets the tidiest rack there is.
    """
    options = grid_options(count, widest=max(COLUMNS))
    fair = [option for option in options if is_fair(option)]
    return snuggest(fair or options)


def dispatch(number: int) -> dict:
    """Telegram No. ``number``: its words, rack and route.

    Returns ``{"number", "words", "cols", "rows", "key"}``. ``words`` is
    the whole rack read across the rows, filler included, which is what
    the visitor has to get back.
    """
    rng = random.Random(number)  # same number, same telegram, everywhere
    coded = encode(DISPATCHES[(number - 1) % len(DISPATCHES)])
    option = puzzle_rack(len(coded))
    cols, rows = option["cols"], option["rows"]
    words = pad(coded, cols, rows, seed=number)
    key = scrambled_key(words, cols, rows, rng)
    return {
        "number": number,
        "words": words,
        "cols": cols,
        "rows": rows,
        "key": key,
    }


def todays_dispatch(day: date) -> dict:
    """The telegram on the counter on ``day``."""
    return dispatch(max(1, telegram_number(day)))
