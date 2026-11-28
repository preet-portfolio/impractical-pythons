"""The joke shop's demonstration letter, and its typewriter card.

All written for this stall. The letter is a booking confirmation from a
seaside guesthouse: dull enough that nobody reads it twice. Its blank
lines hold a plot to fix the pier's duck race, scrambled with the key
PUFFIN.
"""

from invisible_ink import interleave, letter_lines, secret_lines
from vigenere import encrypt

TITLE = "The Gull's Rest"
SUBTITLE = "Guest House · Sea Front · Bramble Bay"
DATE = "14th August"

COVER = """\
Dear Mr Finch,

Thank you for booking a room at The Gull's Rest for Regatta Week.

Your room is the blue one at the top of the stairs, with a view of the pier.

Breakfast is served from half past seven until nine.
Kippers must be ordered the night before.

Please do not feed the gulls from the window. They remember.

Kindly rinse the sand from your shoes before coming in.

We look forward to seeing you.

Yours sincerely,

Doreen Pebble
Proprietor"""

KEY = "PUFFIN"

SECRET = """\
The duck race is fixed for Saturday at noon.
Duck number forty two has a magnet in its tail.
The judge hides the spare ducks under the tea urn.
Swap them while the brass band plays.
Meet me by the coconut shy after.
Bring a towel and say nothing to the gulls."""

# The typewriter card (the challenge project): a lost property notice
# with a short note in the spaces between its words.
TYPEWRITER_COVER = (
    "LOST PROPERTY: one umbrella, two buckets, a single flip flop and a very cross crab."
)
TYPEWRITER_SECRET = "KEYINBOOT"


def demo_letter() -> list[dict]:
    """The finished demonstration letter, its ink already scrambled."""
    secret = [encrypt(line, KEY) for line in secret_lines(SECRET)]
    return interleave(letter_lines(COVER), secret)
