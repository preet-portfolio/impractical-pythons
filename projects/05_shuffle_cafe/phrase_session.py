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

from leftovers import shuffle_report
from phrases import phrase_status, remaining

HELP = (
    "Type word(s) to add, '-' to undo, '?' to shuffle the leftovers,\n"
    "Enter to start over, '#' to quit. Any letters count, even made-up words."
)
SHOWN = 60  # options listed at once; the rest are counted


def show_options(options: list[str], say: Callable) -> None:
    """Print the words that still fit, wrapped, longest first."""
    listed = " ".join(options[:SHOWN])
    more = len(options) - SHOWN
    say(textwrap.fill(listed, width=72) if listed else "(no words fit)")
    if more > 0:
        say(f"...and {more} shorter words.")


def show_shuffle(letters: str, say: Callable) -> None:
    """Print every arrangement of the leftovers, or a sample if too many."""
    report = shuffle_report(letters)
    say(f"{letters} can be arranged {report['count']:,} ways.")
    if not report["complete"]:
        say("Far too many to read, so here are a few at random:")
    say(textwrap.fill(" ".join(report["arrangements"]), width=72))


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
        elif reply == "?":
            show_shuffle(status["left"], say)
        elif remaining(name, [*chosen, reply]) is None:
            say(f"{reply!r} needs letters you don't have left.")
        else:
            chosen.append(reply.lower())
