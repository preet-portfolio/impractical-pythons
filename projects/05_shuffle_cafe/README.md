# 05 · Shuffle Café

A seafront café has a black felt letterboard. Put your name up in white peg letters, and the
waiter pulls them out and pegs them back as other words made from exactly the same letters:
*listen* becomes *silent*, *Daniel* gets *nailed*, an *ocean* turns into a *canoe*.

These are anagrams. This stall finds every single-word anagram of a word or name in a
60,000-word dictionary, and shows the dictionary's biggest anagram families.

Most names won't shuffle into a single word, so part two builds a **phrase** instead, one word
at a time: *Ice Cream Van* becomes *caveman rice*, *Donkey Rides* become *kidneys rode*, and a
*Seaside Town* has a *seasoned wit*.

## Play

```bash
uv run python projects/05_shuffle_cafe/main.py listen         # anagrams of one word
uv run python projects/05_shuffle_cafe/main.py                # asks you for a word
uv run python projects/05_shuffle_cafe/main.py --families 5   # the biggest families
uv run python projects/05_shuffle_cafe/main.py Daniel --words my_words.txt
uv run python projects/05_shuffle_cafe/main.py "Ice Cream Van" --phrase   # build a phrase
```

In a phrase session, type a word (or several) to add it, `-` to undo the last word, just Enter
to start over, or `#` to quit.

## Design first: the pseudocode

```
read the word list, or explain the problem and quit with code 1
take a word from the command line, or ask for one
key = the word's letters, lowercased and sorted
for every dictionary word:
    if it isn't the word itself and its sorted letters equal the key:
        it's an anagram
print the anagrams, or a friendly "none today"
```

## The sorted key

Comparing *listen* and *silent* letter by letter fails straight away (L isn't S). But
put both in alphabetical order and they're identical:

```python
>>> sorted("listen")
['e', 'i', 'l', 'n', 's', 't']
>>> "".join(sorted("silent"))
'eilnst'
```

`sorted` takes any iterable, a string included, and returns a list. Joining it back into a
string gives the word's **key**: every anagram in a family shares it. `letters_only` lowercases
first and drops spaces and hyphens, so *Mary-Jo* and *mary jo* behave the same.

## A loop, or a filing cabinet

`find_anagrams` follows the pseudocode: it walks all 60,000 words and sorts each one, every time
you ask. That's fine for one word on the command line.

The web page asks again on every keystroke, so it uses `anagram_families` instead. That walks
the dictionary **once**, filing each word in a `dict` under its key (a `defaultdict(list)`, so a
new key starts with an empty list). After that, finding anagrams is one lookup:
`families.get(letter_key(word), [])`. Same idea as the set in Mirror Spells: do the work once,
then jump straight to the answer. The tests check that both ways give identical results.

Some numbers from the dictionary: 3,285 families hold 7,284 words. The biggest has seven
members (*pares, parse, pears, reaps, spare, spear* and one rude one), and the longest pair is
*dessertspoonfuls* / *dessertspoonsful*.

## Building a phrase: the computer lists, the human chooses

A program could shuffle a name into thousands of phrases, nearly all nonsense. Picking the one
that *means* something is a job for a person. So the work is split: Python lists every word
that still fits, you choose one that makes sense, and Python works out what's left.

```
letters = count the letters in the name
chosen = []
while letters are left:
    show every word that fits in the letters, longest first
    ask for a word ("-" undoes, Enter starts over, "#" quits)
    if the word fits: add it to chosen, take its letters away
    else: say so and ask again
show the finished phrase
```

**Does a word fit?** `collections.Counter` counts things, and Counters can be subtracted.
Subtraction keeps only counts that stay above zero, so whatever survives is what the word is
missing:

```python
>>> from collections import Counter
>>> Counter("cook") - Counter("cork")     # cook needs two o's, cork has one
Counter({'o': 1})
>>> Counter("rock") - Counter("rockpool")  # nothing missing
Counter()
```

An empty Counter is falsy, so `fits` is just `not letter_count(word) - letters`. Before building
a Counter for every one of the 60,000 words, `words_that_fit` turns most of them away with two
cheaper questions: is the word too long, and does it use a letter we don't have at all
(`set(word) <= set(letters)`)?

**No recursion for starting over.** The phrase is just a list of chosen words. Starting over
empties it, undo drops the last one, and the letters left are always recalculated from the name
and that list (`phrases.remaining`). So the session is one plain loop that never calls itself,
and the web page uses the very same functions: it keeps the list, Python does the counting.

**Talking and thinking apart.** `phrase_session.run_session` takes `ask` and `say` arguments
that default to `input` and `print`. The tests pass in a list of scripted replies instead, so a
whole session (a bad word, an undo, a restart, a quit) runs without a keyboard.

## Shared with other stalls

The word list, its loader and the "not on the pier" filter now live in
[`projects/common/`](../common/), because Mirror Spells uses them too. `main.py` adds that
folder to `sys.path` before importing from it. The web page bundles the common files next to
this project's own, so the same `import wordlist` works there. Anagram families turn up a few
rude words, so the page leaves them off and says how many; the Python and the tests still see
everything.

## Files

| File | What's in it |
|---|---|
| `anagrams.py` | `letters_only`, `letter_key`, `is_anagram`, `find_anagrams`, `anagram_families`, `anagrams_from_families`, `biggest_families`, `menu_stats` |
| `phrases.py` | `letter_count`, `fits`, `remaining`, `words_that_fit`, `spell_out`, `phrase_status` |
| `phrase_session.py` | `run_session`: the interactive phrase builder, with `ask`/`say` you can swap |
| `main.py` | The command line: `argparse`, an `input()` fallback, `--families`, `--phrase`, `try`/`except OSError` |
| `../common/wordlist.py` | Shared: `read_words`, `clean_words` and the bundled dictionary |
| `../common/decency.py` | Shared: the short list of words kept off the web page |

## What's new here

- **`sorted()` on a string.** It returns a sorted list of characters; `"".join` turns it back
  into a string you can compare or use as a key.
- **A dict as an index.** Build it once, look things up instantly forever after.
- **`defaultdict(list)`** saves the "is this key here yet?" check when grouping things.
- **`dict.get(key, default)`** answers "nothing" without raising `KeyError`.
- **Sorting with a tuple key.** `(-len(family), family)` sorts biggest first and breaks ties
  the same way every time.
- **`input()` as a fallback.** `args.word or input(...)` asks only when nothing was given on the
  command line; the test swaps `input` out with `monkeypatch`.
- **Shared modules.** Code two projects need lives in one place, and each project adds it to
  `sys.path`.
- **`collections.Counter`** counts letters; subtracting Counters tells you what's missing.
  `Counter.total()` adds up the counts and `Counter.elements()` lists every letter again.
- **Cheap checks first.** A length test and a set test turn most words away before the
  slower Counter check runs.
- **Stateless steps.** Passing "the words chosen so far" in each time makes undo and restart
  free, and lets the command line and the web page share every function.
- **Dependency injection, lightly.** Giving `run_session` its `ask` and `say` makes an
  interactive program testable.

## Try this next

1. Is `Counter(a) == Counter(b)` faster than comparing sorted strings for single-word
   anagrams? Time both with `time.perf_counter()`.
2. Add a "finish it for me" button: when only a few letters are left, find every word (or
   pair of words) that uses all of them exactly.
3. Score phrases: give a bonus for long words, and list the best two-word phrases for a name
   automatically.
