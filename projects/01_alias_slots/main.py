"""Play Alias Slots in the terminal.

Usage:
    uv run python projects/01_alias_slots/main.py
    uv run python projects/01_alias_slots/main.py --theme space_pirate --seed 7
    uv run python projects/01_alias_slots/main.py --code 3k9

The alias is printed to standard error, which most terminals (and IDLE) show
in red, so it stands out from the prompts.
"""

from __future__ import annotations

import argparse
import random
import sys
from typing import TextIO

from slots import THEMES, Spin, combinations, decode, spin

PRIZE_LINES = {
    "jackpot": "*** JACKPOT! Every reel starts with the same letter! ***",
    "rhyme": "~ Rhyme bonus! ~",
    "pair": "Pair! Two reels match.",
}

HELP = "[Enter] spin   l1/l2/l3 lock or unlock a reel   t switch theme   q quit"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Read the command-line options."""
    parser = argparse.ArgumentParser(description="A slot machine for ridiculous aliases.")
    parser.add_argument("--theme", choices=list(THEMES), default="sidekick")
    parser.add_argument("--seed", type=int, help="same seed, same names")
    parser.add_argument("--code", help="show the alias behind a share code and exit")
    parser.add_argument("--list-themes", action="store_true", help="list themes and exit")
    return parser.parse_args(argv)


def show(result: Spin, locked: dict[int, int], out: TextIO, err: TextIO) -> None:
    """Print one spin: the alias in red (stderr), the details in normal text."""
    print(f"\n  {result.name}", file=err)
    shown = [f"{word} [locked]" if i in locked else word for i, word in enumerate(result.words)]
    reels = "  |  ".join(shown)
    print(f"  {reels}", file=out)
    if result.prize:
        print(f"  {PRIZE_LINES[result.prize]}", file=out)
    print(f"  share code: {result.code}", file=out)


def play(
    theme_key: str,
    seed: int | None = None,
    stdin: TextIO = sys.stdin,
    out: TextIO = sys.stdout,
    err: TextIO = sys.stderr,
) -> int:
    """Run the spin / lock / quit loop. Returns how many spins were played.

    Streams are parameters so tests can feed in keystrokes and read the output.
    """
    # One master generator hands out a seed per spin: the whole session is
    # reproducible from --seed, but every spin is still different.
    master = random.Random(seed)
    locked: dict[int, int] = {}
    themes = list(THEMES)
    print(f"Alias Slots: {THEMES[theme_key].title} ({combinations(theme_key):,} aliases)", file=out)
    print(HELP, file=out)
    result = spin(theme_key, master.randrange(2**32))
    show(result, locked, out, err)
    spins = 1

    while True:
        print("> ", end="", file=out, flush=True)
        line = stdin.readline()
        command = line.strip().lower()
        if not line or command in {"q", "quit", "exit"}:
            print("Bye!", file=out)
            return spins
        if command in {"l1", "l2", "l3"}:
            reel = int(command[1]) - 1
            if reel in locked:
                del locked[reel]
                print(f"  Reel {reel + 1} unlocked.", file=out)
            else:
                locked[reel] = result.indices[reel]
                print(f"  Reel {reel + 1} locked on {result.words[reel]!r}.", file=out)
            continue
        if command == "t":
            theme_key = themes[(themes.index(theme_key) + 1) % len(themes)]
            locked.clear()
            print(f"  Switched to {THEMES[theme_key].title}.", file=out)
        elif command:
            print(f"  ?  {HELP}", file=out)
            continue
        result = spin(theme_key, master.randrange(2**32), locked)
        show(result, locked, out, err)
        spins += 1


def main(argv: list[str] | None = None) -> None:
    """Entry point for the command line."""
    args = parse_args(argv)
    if args.list_themes:
        for theme in THEMES.values():
            print(f"{theme.key:18} {theme.title}: {theme.blurb}")
        return
    if args.code:
        try:
            print(decode(args.code).name, file=sys.stderr)
        except ValueError as error:
            sys.exit(str(error))
        return
    play(args.theme, args.seed)


if __name__ == "__main__":
    main()
