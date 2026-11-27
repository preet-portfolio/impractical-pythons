# 04 · Mirror Spells

Some words read the same backwards: *kayak*, *level*, *deified*. Whole sentences can do it too
(*Step on no pets*). In this stall they're spells: type one into the magic mirror and it checks
every letter against its reflection. The spellbook holds every one-word spell in a
60,000-word dictionary. There are only 56 of them, about one word in a thousand.

Part two pairs words up: *nurses run*, *stir grits*, *stack cats*. Say them together and the
mirror still agrees. The dictionary hides 2,230 of these two-word spells, and finding them
quickly is a lesson in picking the right container.

## Play

```bash
uv run python projects/04_mirror_spells/main.py                       # the whole spellbook
uv run python projects/04_mirror_spells/main.py "Step on no pets"     # test a phrase
uv run python projects/04_mirror_spells/main.py --words my_words.txt  # use your own list
uv run python projects/04_mirror_spells/main.py --pairs               # every two-word spell
uv run python projects/04_mirror_spells/speed_test.py                 # list vs set, plus cProfile
```

Point `--words` at a file that isn't there and the program explains the problem in red (on
standard error) and quits with exit code 1. Check it with `echo $?`.

## Design first: the pseudocode

```
read the word list (one word per line), or explain the problem and quit with code 1
spells = every word with at least 2 letters that equals itself reversed
print the spells, one per line
print how many there are, what share of the dictionary that is, and the longest
```

## Reading backwards with a slice

A slice is `text[start:stop:step]`. Leave out start and stop and you get the whole string;
make the step `-1` and Python walks it from the end to the beginning:

```python
>>> word = "stressed"
>>> word[::-1]
'desserts'
>>> word[2:6]        # positions 2, 3, 4 and 5
'ress'
```

So a palindrome is any text where `letters == letters[::-1]`. The mirror on the web page does
the same check one letter at a time, so you can see exactly where a near-miss breaks.

## Two-word spells

A two-word spell is built around a **core word**. Cut the core somewhere. If one side of the
cut is a palindrome on its own (a *run*), and the other side backwards is a real word, that
word is the core's partner:

```
core first: "nurses" + partner              core second: partner + "grits"

   n u r s e s                                  g r i t s
   ───┬─── ─┬─                                  ┬ ───┬───
   head    run ("ses" reads the same            run  tail ("rits" backwards
   backwards = "run", a real word)            ("g")  = "stir", a real word)

   → nurses run                                 → stir grits
```

`palingrams.spells_from` tries every cut of every word, both ways round. An empty run is
allowed, which catches word pairs that are each other's reflection (*stab bats*). Pairs go
into a `set` of tuples so the same spell found twice is only kept once, then get sorted.

## Making it fast

Each core word asks "is this a real word?" for every cut, about a million questions for the
whole dictionary. `two_word_spells_slow` asks a **list**; `two_word_spells` asks a **set**.
Same logic, same answers (the tests check), very different speeds. From one run on a laptop:

```
Checking 500 core words against all 60,388 words:
  list lookups: 0.761 s
  set lookups:  0.0016 s
  the set is about 466 times faster
Whole dictionary: list ~92 s (estimated), set 0.18 s (measured)
```

`speed_test.py` times both with `time.perf_counter()` (a clock made for measuring short
gaps, not telling the time), then runs each under `cProfile` and prints the top lines with
`pstats`, sorted by `tottime`:

```
   ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        1    0.778    0.778    0.779    0.779 palingrams.py:29(spells_from)
     8340    0.001    0.000    0.001    0.000 palingrams.py:24(_is_run)
```

Almost all the time sits *inside* `spells_from` itself. That's a clue: `word in some_list` is
an operator, not a function call, so cProfile can't list it on its own line. The cost hides in
whoever does the asking.

**Why the set wins.** A list check reads the words one by one until it finds a match, so a
miss costs 60,000 comparisons. A set works out a *hash* of the word (a number computed from
its letters) and jumps straight to the slot where that word would live. One look, whatever
the size. That's why the list version gets slower as the dictionary grows and the set
version barely notices.

## Practice and challenge

- **Dictionary cleanup** (`wordlist.clean_words`): some word lists start each letter's
  section with a lone heading like `b` or `c`. Those aren't words, and they'd make silly
  spells. `clean_words` drops single letters except the real ones (*a* and *I*) and removes
  duplicates with `dict.fromkeys`, which keeps the first one of each and the original order.
- **Recursive check** (`palingrams.is_palindrome_recursive`): a palindrome is something whose
  first and last letters match *and* whose middle is a palindrome. That definition calls
  itself, so the code can too. Zero or one letter is the base case. The tests check it
  agrees with the slice version on every word in the dictionary.

## Not on the pier

`common/decency.py` holds a short list of crude words. The web page uses it to keep a handful of
spells (4 single words and 87 pairs) out of sight. The Python, the command line and the
tests still find everything, so nothing about the algorithm is hidden.

## Files

| File | What's in it |
|---|---|
| `mirror.py` | `letters_only`, `is_palindrome`, `find_palindromes`, `spellbook_stats`, `reflect` |
| `palingrams.py` | `two_word_spells` (set), `two_word_spells_slow` (list), `is_palindrome_recursive` |
| `speed_test.py` | `timed`, `race` and `profile_report`: the stopwatch and cProfile |
| `main.py` | The command line: `argparse`, `try`/`except OSError`, `sys.exit(1)`, `--pairs` |
| `../common/wordlist.py` | Shared: `read_words`, `words_from_text` and `clean_words` |
| `../common/decency.py` | Shared: `NOT_ON_THE_PIER`, `family_friendly`, `family_friendly_pairs` (web only) |
| `../common/data/2of4brif.txt` | 60,388 common English words (see [SOURCE.md](../common/data/SOURCE.md)) |

The word list is `2of4brif.txt` from Alan Beale's **12dicts**
(<http://wordlist.aspell.net/12dicts/>), which he released to the public domain. Thank you, Alan.

## What's new here

- **Slicing with a step.** `[::-1]` reverses any sequence: strings, lists, tuples.
- **`try` / `except`.** Opening a file can fail. `main.py` tries, and if an `OSError`
  (like `FileNotFoundError`) happens, it prints the reason to `sys.stderr` and stops.
- **Exit codes.** `sys.exit(1)` tells the shell (and any script that ran this one) that
  something went wrong; finishing normally means `0`.
- **Where errors get handled.** `read_words` doesn't catch anything: a module that quits the
  whole program is hard to reuse and test. The CLI decides what a missing file means.
- **`with open(...)`** closes the file the moment the block ends, even if something fails.
- **List comprehensions** turn "loop, check, append" into one readable line.
- **The splat operator.** `print(*spells, sep="\n")` unpacks a list into separate arguments,
  so one call prints every spell on its own line.
- **Testing failures.** `pytest.raises(OSError)` and `pytest.raises(SystemExit)` check that
  things go wrong in exactly the right way.
- **Sets and hashing.** `word in a_set` takes about the same time for 10 words or 10 million;
  `word in a_list` doesn't.
- **Tuples in sets.** A tuple can't change, so it can be hashed and stored in a set. That's
  how duplicate pairs vanish for free.
- **`cProfile` and `pstats`.** Find where the time goes before guessing.
- **`time.perf_counter()`.** The right clock for timing code.
- **Recursion.** A function that solves a smaller copy of the same problem, with a base case
  so it stops.

## Try this next

1. Find the "near-spells": words that become a *different* real word backwards (*stressed*
   and *desserts*, *drawer* and *reward*). Hint: put the words in a `set` first.
2. Try another word list from the 12dicts download. Does a bigger dictionary find a longer
   spell than *deified*?
3. Make the mirror forgiving: allow one mismatched pair and call it a "wobbly spell".
4. Hunt for three-word spells. How many questions would the list version need now?
5. Race a `frozenset` and a `dict` against the set. Are they any faster?
