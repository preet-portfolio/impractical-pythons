"""Spin silly secret-agent aliases in the terminal: the tidy version.

This is messy_slots.py after a style clinic. It behaves the same but
follows PEP 8 (code layout) and PEP 257 (docstrings), and Pylint rates it
10/10 even at PEP 8's strict 79-character line limit.
"""

import random
import sys

FIRST_WORDS = (
    "Waffle",
    "Socket",
    "Pebble",
    "Turnip",
    "Velcro",
    "Marzipan",
    "Gadget",
)
LAST_WORDS = (
    "McNoodle",
    "Featherstone",
    "Bumbercrumb",
    "Snorkelton",
    "Puddleby",
)
TAGS = (
    "the Unbreakable Teaspoon",
    "who Knows a Guy",
    "of the Overdue Library Book",
)


def make_alias(rng: random.Random) -> str:
    """Return one alias: a first word, a last word and a tag.

    Args:
        rng: Where the randomness comes from. Pass ``random.Random(seed)``
            to get the same alias every time, which keeps tests simple.
    """
    first = rng.choice(FIRST_WORDS)
    last = rng.choice(LAST_WORDS)
    tag = rng.choice(TAGS)
    return f"{first} {last} {tag}"


def main() -> None:
    """Spin aliases until the player types n (or input runs out)."""
    rng = random.Random()
    spins = 0
    print("\nWelcome to the Snack Agent alias spinner!")
    print("Press Enter to spin, or type n and Enter to stop.")
    while True:
        spins += 1
        # stderr shows red in IDLE and many terminals, so the name stands out.
        print(f"\n\n{make_alias(rng)}\n", file=sys.stderr)
        try:
            answer = input("Spin again? ")
        except EOFError:  # input closed, e.g. Ctrl-D or a piped file ran out
            break
        if answer.strip().lower() == "n":
            break
    print(f"You spun {spins} times. Bye!")


if __name__ == "__main__":
    main()
