"""The interactive phrase builder for the command line.

The talking happens here and the thinking in ``phrases.py``. ``ask`` and
``say`` default to ``input`` and ``print`` but can be swapped for test
doubles, so a whole session can be tested without a keyboard.

One loop runs the session. Starting over just empties the list of
chosen words; the function never calls itself or ``main`` again, so a
long evening of failed attempts doesn't pile up calls on the stack.
"""

import textwrap
from collections.abc import Callable

from phrases import phrase_status, remaining

HELP = "Type word(s) to add, '-' to undo, Enter to start over, '#' to quit."
SHOWN = 60  # options listed at once; the rest are counted


def show_options(options: list[str], say: Callable) -> None:
    """Print the words that still fit, wrapped, longest first."""
    listed = " ".join(options[:SHOWN])
    more = len(options) - SHOWN
    say(textwrap.fill(listed, width=72) if listed else "(no words fit)")
    if more > 0:
        say(f"...and {more} shorter words.")


def run_session(
    name: str,
    words: list[str],
    ask: Callable = input,
    say: Callable = print,
) -> str | None:
    """Build one phrase from ``name``; return it, or ``None`` on quit."""
    chosen: list[str] = []
    say(HELP)
    while True:
        status = phrase_status(name, chosen, words)
        if status["done"]:
            say(f"***** Order up! {name} = {status['phrase']} *****")
            return status["phrase"]
        say(f"\nLetters left: {status['left']}")
        show_options(status["options"], say)
        say(f"Phrase so far: {status['phrase'] or '(empty)'}")

        reply = ask("Your choice: ").strip()
        if reply == "#":
            return None
        if reply == "":
            chosen = []
            say("Starting over.")
        elif reply == "-":
            chosen = chosen[:-1]
        elif remaining(name, [*chosen, reply]) is None:
            say(f"{reply!r} needs letters you don't have left.")
        else:
            chosen.append(reply.lower())
