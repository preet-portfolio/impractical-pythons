# 01 · Alias Slots

A fruit machine for ridiculous aliases. Pick a machine (Detective's Sidekick, Space
Pirate, Fantasy Villain, Bollywood Baddie or Cozy Wizard), pull the lever, hold the
reels you like and spin the rest.

- **Jackpot:** every reel starts with the same letter (*Gingersnap Gentlebrook the Gently Glowing*).
- **Rhyme:** two reels end with the same three letters.
- **Pair:** two reels share a first letter.
- **Wildcard:** about one spin in three, a middle name sneaks in between the first and last
  names. If it starts with the same letter as the first name, that's a wildcard bonus.

Every alias has a short share code, so a link brings back exactly that name.

## Play

```bash
uv run python projects/01_alias_slots/main.py                      # spin, l1/l2/l3 to hold, t to switch, q to quit
uv run python projects/01_alias_slots/main.py --theme space_pirate --seed 7
uv run python projects/01_alias_slots/main.py --code dwy           # show a shared alias
uv run python projects/01_alias_slots/main.py --list-themes
```

The alias prints to standard error, which most terminals show in red, so it stands out
from the prompts. Or play it on the web, where the same Python runs in your browser.

## Design first: the pseudocode

```
load the machines: each one is three reels (tuples of words) plus a template
pick a machine
repeat:
    for each reel:
        draw a random stop                 # always draw, so holding one reel never
        if the reel is held: keep its stop #   changes where the others land
    read the words at the stops and fill in the template
    score it: same first letter on all reels -> jackpot
              two reels end in the same 3 letters -> rhyme
              two reels share a first letter -> pair
    pack the machine and stops into a base-36 share code
    show the alias (in red), the prize and the code
    ask: spin, hold a reel, switch machine or quit
until the player quits
```

## Files

| File | What's in it |
|---|---|
| `themes.py` | The `Theme` dataclass and the five machines' word reels |
| `slots.py` | Pure functions: `spin`, `prize_for`, `encode`/`decode`, `odds`, `catalogue` |
| `main.py` | The terminal game (`argparse`, the spin/hold/quit loop) |

## What's new here

- **Tuples for data that never changes.** The reels are tuples, so the code itself
  promises nobody will append to them mid-game.
- **`random.Random(seed)`**: its own random number generator. The same seed gives the
  same spins, which makes tests and shared sessions reproducible.
- **Frozen `dataclasses`**: `Theme` and `Spin` are small read-only records with free
  `__eq__` and `__repr__`.
- **Counting instead of calculating.** `odds()` tries all 13,824 spins with
  `itertools.product` and tallies prizes with `collections.Counter`.
- **Mixed-radix numbers.** A share code treats each reel as a digit whose base is that
  reel's length, then writes the number in base 36.
- **Printing to `sys.stderr`** with `print(..., file=sys.stderr)` to colour the output red.
- **Style guides as tools.** PEP 8 (code style) and PEP 257 (docstrings) are checked by
  `ruff`, which does the job of `pylint` and `pydocstyle` in one fast tool.
- **A style clinic.** [`style_clinic/`](style_clinic/STYLE_CLINIC.md) takes a deliberately
  messy spinner from a Pylint score of 3.10 to 10.00, fix by fix, and shows why passing
  pydocstyle doesn't make a docstring good.
- **Testable I/O.** `play()` takes its input and output streams as parameters, so tests
  type keys with `io.StringIO` and read what came out.

## Try this next

1. Add your own machine to `themes.py`, for example "Cricket Commentator" or "Startup Founder".
   The tests check that its reels are clean.
2. Add a fourth reel, such as a title ("Dr.", "Sir", "Auntie"). What has to change in
   `encode`/`decode`, and why do the old share codes break?
3. Make a "near miss" prize when two reels alliterate and the third is one letter away
   in the alphabet. How does it change the odds?
