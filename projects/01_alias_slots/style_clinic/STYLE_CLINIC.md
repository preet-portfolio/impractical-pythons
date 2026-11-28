# Style clinic: from 3.10 to 10.00

Code that works isn't finished: other people (and you, five years from now) have to read it.
Python's shared rules for readable code are **PEP 8** (layout, naming, line length) and
**PEP 257** (docstrings). Tools check them for you, so you don't have to memorise them.

This folder holds two versions of the same tiny program, a spinner for silly secret-agent
aliases:

| File | What it is |
|---|---|
| [`messy_slots.py`](messy_slots.py) | Works, but breaks the rules **on purpose** |
| [`tidy_slots.py`](tidy_slots.py) | Same behaviour, fixed |

Run either one with `uv run python projects/01_alias_slots/style_clinic/tidy_slots.py`.
Press Enter to spin, and type `n` to stop.

## 1. Run the checkers

```bash
cd projects/01_alias_slots/style_clinic
uv run pylint --max-line-length=79 messy_slots.py   # PEP 8 + likely bugs, with a score
uv run pydocstyle messy_slots.py                    # PEP 257 docstrings only
```

`--max-line-length=79` is PEP 8's strict limit. Pylint's default is 100, which is also what
this repo uses (see section 5). The score line appears at the bottom of Pylint's output.
Modern Pylint prints it even with `-rn`, which only turns off the long statistics tables.

## 2. Before: 3.10/10

Pylint 4.1.4 on `messy_slots.py`:

```
messy_slots.py:2:0: C0301: Line too long (88/79) (line-too-long)
messy_slots.py:6:0: C0301: Line too long (85/79) (line-too-long)
messy_slots.py:7:0: C0301: Line too long (81/79) (line-too-long)
messy_slots.py:8:0: C0301: Line too long (85/79) (line-too-long)
messy_slots.py:16:0: C0301: Line too long (99/79) (line-too-long)
messy_slots.py:1:0: C0114: Missing module docstring (missing-module-docstring)
messy_slots.py:3:0: C0410: Multiple imports on one line (sys, random) (multiple-imports)
messy_slots.py:5:0: C0103: Constant name "spinCount" doesn't conform to UPPER_CASE naming style (invalid-name)
messy_slots.py:6:0: C0103: Constant name "FirstWords" doesn't conform to UPPER_CASE naming style (invalid-name)
messy_slots.py:7:0: C0103: Constant name "LastWords" doesn't conform to UPPER_CASE naming style (invalid-name)
messy_slots.py:9:0: C0116: Missing function or method docstring (missing-function-docstring)
messy_slots.py:9:0: C0103: Function name "SpinOnce" doesn't conform to snake_case naming style (invalid-name)
messy_slots.py:10:4: W0603: Using the global statement (global-statement)
messy_slots.py:12:35: C0321: More than one statement on a single line (multiple-statements)
messy_slots.py:14:11: C0209: Formatting a regular string which could be an f-string (consider-using-f-string)
messy_slots.py:22:4: W0702: No exception type(s) specified (bare-except)
messy_slots.py:24:7: C0121: Comparison 'answer.lower() == 'n' == True' should be ... (singleton-comparison)
messy_slots.py:26:6: C0209: Formatting a regular string which could be an f-string (consider-using-f-string)
messy_slots.py:29:0: W0702: No exception type(s) specified (bare-except)
messy_slots.py:4:0: W0611: Unused import os (unused-import)
Your code has been rated at 3.10/10
```

pydocstyle on the same file:

```
messy_slots.py:1 at module level:
        D100: Missing docstring in public module
messy_slots.py:9 in public function `SpinOnce`:
        D103: Missing docstring in public function
```

The letter in each Pylint code tells you how serious it is: **C** is convention (style),
**R** is refactor, **W** is warning (a likely bug), **E** is error and **F** is fatal.

## 3. The fixes

| Pylint | What it means | How `tidy_slots.py` fixes it | Same rule in ruff |
|---|---|---|---|
| C0114, C0116 | No docstring for the module or function | One-line summary, then detail where it helps | D100, D103 |
| C0301 | Line over 79 characters | Long tuples broken one item per line, and long messages shortened | E501 |
| C0410 | `import sys, random` | One import per line, standard library sorted | E401, I001 |
| W0611 | `os` imported but never used | Deleted | F401 |
| C0103 | `spinCount`, `FirstWords`, `SpinOnce` | Constants in `UPPER_CASE`, functions in `snake_case` | N802, N816 (pep8-naming) |
| W0603 | `global spinCount` mutates shared state | The counter lives inside `main()` | (Pylint only) |
| C0321 | `a = ...; b = ...` on one line | One statement per line | E702 |
| C0209 | `"%s %s" % (a, b)` | f-strings: `f"{first} {last} {tag}"` | UP031 |
| W0702 | Bare `except:` also swallows Ctrl-C and real bugs | `except EOFError:`, the one error we expect | E722 |
| C0121 | `(... == "n") == True` | Just `if answer.strip().lower() == "n":` | E712 |
| (no code) | Script code runs at import time | Wrapped in `main()` behind `if __name__ == "__main__":` | (neither) |

The last row isn't flagged by either tool, but it matters. With the guard in place, tests can
`import tidy_slots` and call `make_alias()` without starting the game. That's what
`tests/01_alias_slots/test_alias_slots.py` does.

The fix also made the program **easier to test**. `make_alias(rng)` takes its random
generator as a parameter, so `random.Random(3)` gives the same alias every time.

## 4. After: 10.00/10, and why that isn't the whole story

```
$ uv run pylint --max-line-length=79 tidy_slots.py
Your code has been rated at 10.00/10
$ uv run pydocstyle tidy_slots.py
$                                  # silence means no problems
```

**Passing isn't the same as good.** pydocstyle checks the *shape* of a docstring, not
whether it says anything. This passes every rule:

```python
def make_alias(rng):
    """Qwfp arst zxcv neio mklj."""
```

So does this, which is worse, because it's confidently unhelpful:

```python
def make_alias(rng):
    """Make alias."""
```

The real one says what comes back and why the parameter exists, which is the part a
reader can't guess from the name:

```python
def make_alias(rng: random.Random) -> str:
    """Return one alias: a first word, a last word and a tag.

    Args:
        rng: Where the randomness comes from. Pass ``random.Random(seed)``
            to get the same alias every time, which keeps tests simple.
    """
```

**Comments** follow the same idea. `tidy_slots.py` has only two, and each explains
something the code can't say for itself:

- `# stderr shows red in IDLE and many terminals, so the name stands out.` This explains
  *why* the alias is printed to the error stream. Without it, the line looks like a mistake.
- `# input closed, e.g. Ctrl-D or a piped file ran out` This says *when* `EOFError` actually
  happens.

Good reasons to write a comment are intent, surprises, units ("seconds, not ms") and the
input format you expect. Bad reasons are repeating the code (`spins += 1  # add one to spins`)
or leaving old code commented out.

## 5. Keep the settings in a file

Instead of typing options every time (the book uses a `.pylintrc`), this repo keeps every
tool's settings in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100

[tool.pylint.format]
max-line-length = 100
```

That's why plain `uv run pylint projects/01_alias_slots/*.py` gives 10.00/10 with no flags.
We picked 100 over PEP 8's 79 on purpose. PEP 8 allows a team to agree on up to 99–100,
and it's Pylint's own default. The `--max-line-length=79` runs above show the strict version.

Day to day this repo uses **ruff**, which covers the same ground as pycodestyle, pydocstyle
and most of Pylint's style checks in one very fast pass (`uv run ruff check .`). Pylint is
still worth running sometimes: it catches design smells such as `global` that ruff doesn't.
