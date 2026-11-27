# 04 · Mirror Spells

Some words read the same backwards: *kayak*, *level*, *deified*. Whole sentences can do it too
(*Step on no pets*). In this stall they're spells: type one into the magic mirror and it checks
every letter against its reflection. The spellbook holds every one-word spell in a
60,000-word dictionary. There are only 56 of them, about one word in a thousand.

## Play

```bash
uv run python projects/04_mirror_spells/main.py                       # the whole spellbook
uv run python projects/04_mirror_spells/main.py "Step on no pets"     # test a phrase
uv run python projects/04_mirror_spells/main.py --words my_words.txt  # use your own list
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

## Files

| File | What's in it |
|---|---|
| `wordlist.py` | `read_words(path)` and `words_from_text(text)`: loading, with errors left to the caller |
| `mirror.py` | `letters_only`, `is_palindrome`, `find_palindromes`, `spellbook_stats`, `reflect` |
| `main.py` | The command line: `argparse`, `try`/`except OSError`, `sys.exit(1)` |
| `data/2of4brif.txt` | 60,388 common English words (see [data/SOURCE.md](data/SOURCE.md)) |

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

## Try this next

1. Find the "near-spells": words that become a *different* real word backwards (*stressed*
   and *desserts*, *drawer* and *reward*). Hint: put the words in a `set` first.
2. Try another word list from the 12dicts download. Does a bigger dictionary find a longer
   spell than *deified*?
3. Make the mirror forgiving: allow one mismatched pair and call it a "wobbly spell".
