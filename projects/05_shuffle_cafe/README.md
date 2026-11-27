# 05 · Shuffle Café

A seafront café has a black felt letterboard. Put your name up in white peg letters, and the
waiter pulls them out and pegs them back as other words made from exactly the same letters:
*listen* becomes *silent*, *Daniel* gets *nailed*, an *ocean* turns into a *canoe*.

These are anagrams. This stall finds every single-word anagram of a word or name in a
60,000-word dictionary, and shows the dictionary's biggest anagram families.

Most names won't shuffle into a single word, so part two builds a **phrase** instead, one word
at a time: *Ice Cream Van* becomes *caveman rice*, *Donkey Rides* become *kidneys rode*, and a
*Seaside Town* has a *seasoned wit*.

Then the kitchen takes over. **Chef's choice** invents whole phrases by itself and serves the
best five at a time, and **the kitchen sieve** turns a handful of letters into brand-new,
sayable words: *teacakes* can be strained into a *cateseak*.

## Play

```bash
uv run python projects/05_shuffle_cafe/main.py listen         # anagrams of one word
uv run python projects/05_shuffle_cafe/main.py                # asks you for a word
uv run python projects/05_shuffle_cafe/main.py --families 5   # the biggest families
uv run python projects/05_shuffle_cafe/main.py Daniel --words my_words.txt
uv run python projects/05_shuffle_cafe/main.py "Ice Cream Van" --phrase   # build a phrase
uv run python projects/05_shuffle_cafe/main.py emr --shuffle  # every order of some letters
uv run python projects/05_shuffle_cafe/main.py teacakes --strain      # the kitchen sieve
uv run python projects/05_shuffle_cafe/main.py doughnut --check       # would it get through?
uv run python projects/05_shuffle_cafe/main.py "Ice Cream Van" --chef # chef's choice
```

In a phrase session, type a word (or several) to add it, `-` to undo the last word, `?` to
shuffle the leftover letters, `!` to strain them, just Enter to start over, or `#` to quit.

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

## Shuffling the leftovers

Sometimes the last few letters won't make an English word. *Paddle Steamer* gives
*paddles ate* easily, and then *e, m, r* are left. No dictionary word fits, but shuffle them
and one ordering is *mer*, French for sea. A name doesn't have to be in the dictionary, so the
tray's **Shuffle the leftovers** button (and `?` on the command line) lists every ordering
for you to eyeball.

**How many orderings?** Six different letters can be put in 6! = 720 orders
(`math.factorial(6)`). Repeated letters cut that down, because swapping the two e's in
*teeth* changes nothing you can see, so divide by the factorial of each letter's count:
5! / (2! × 2!) = 30. `arrangement_count` does exactly that, before any orderings are made.

**Making them.** `itertools.permutations("emr")` yields tuples like `('m', 'e', 'r')`;
`"".join` turns each into a string, and a set drops the repeats that identical letters cause.

**Too many to read.** Thirteen leftover letters have 259,459,200 orderings: about eight years
of reading at one a second. Above 720, `shuffle_report` shows a random handful instead
(`random.Random(seed).sample`), and the page says how long the full list would take.

## The kitchen sieve: strain out the unsayable

Shuffling nine letters gives up to 362,880 orderings, nearly all mush. Nobody reads that many,
so the sieve throws most away without looking, using a code-breaker's idea: every language
leaves fingerprints, and English's are easy to count.

```
orderings = every different ordering of the letters
for each sieve (shape, three-letter, two-letter):
    keep only the orderings the sieve doesn't catch
    note how many are left
sort the survivors, most English-sounding first
```

**Counting the fingerprints ourselves.** Instead of copying a table of letter statistics from
somewhere, `ngrams.py` counts them from the dictionary the café already has. `ngrams(word, 2)`
slices out every overlapping pair, repeats included, so *banana* gives *ba an na an na* (the
practice-project trap: *an* and *na* each count twice). `count_ngrams` adds them up with a
`Counter` across all 60,388 words; the same goes for runs of three letters and for the pair
each word starts with. Because the numbers come from our own list, they work for any letters.

**The three sieves** live in `sieve.py`. Each is a small function that returns the *culprit*
it caught (or `None`), so the very same functions strain a batch and explain a single word:

| Sieve | Catches an ordering when… | Built from |
|---|---|---|
| Shape | its consonant/vowel pattern (`cv_map`: *riddle* → `cvcccv`) is one real words that long rarely have | `common_shapes`: shapes taken most common first until they cover 95% of words that length |
| Three-letter | it contains a run of three found fewer than 3 times in the dictionary | `count_ngrams(words, 3)` |
| Two-letter | it contains a pair below 0.05% of all pairs, or starts with a pair fewer than 10 words start with | `count_ngrams(words, 2)` and `count_starts` |

*Teacakes* goes 10,080 → 3,168 → 957 → 518, and *teacakes* itself survives, so the sieves
aren't cutting too close. They aren't perfect either: *doughnut* is caught, because only two
words in the dictionary contain *hnu*. That's a good thing to show people, not hide.

**Ranking the survivors.** `wordiness` averages `math.log1p` of each triple's count. Logs stop
one enormously common triple (*ing*) from drowning out the rest: every tenfold jump in count
adds the same amount.

**Nine letters at most.** Ten letters are 3,628,800 orderings, too many to make in a browser
tab, so `strain` refuses (with a `ValueError`) and the page asks for fewer.

## Chef's choice: the computer picks the words too

The challenge from the book: generate phrase anagrams automatically and show a few hundred.
`chef.py` does it with a **depth-first search** and an explicit stack, like packing a suitcase:
try the longest word that fits, then the longest that fits what's left, and back up when
nothing fits the gap.

```
menu = every word that fits the name, longest first
for each first word on the menu (until the budget runs out):
    stack = [(that word, the letters it leaves)]
    while the stack isn't empty and this word's share of the budget lasts:
        pop a half-built phrase
        no letters left? it's finished
        otherwise push it plus each later menu word that still fits
rank the finished phrases, best first
```

- **No duplicates in a different order.** Words are only taken from the menu at or after the
  last one used, so *caveman rice* is found and *rice caveman* never is.
- **A budget, shared out.** Every first word gets a slice of 200,000 steps. Without that, a long
  word like *bowdlerizes* would swallow the whole search and every phrase would start with it.
- **Tastiness.** Each word scores its length squared, so one long word beats several short
  ones: *caveman rice* (49 + 16) outranks *a crave manic*.

**What the research said.** Before building it we looked at the anagram sites the book lists
(see `docs/ux-research.md`). They hand you settings forms and lists of thousands, and leave
the hard part, spotting the funny one, to you. So the page serves five at a time to keep or
send back, collects the keepers on a card you can copy, and keeps the full list one tap away.
Computers are good at finding phrases; people are good at judging them.

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
| `ngrams.py` | `ngrams`, `count_ngrams`, `count_starts`, `cv_map`, `common_shapes`, `pair_table` |
| `sieve.py` | `LetterStats`, the three `catch_*` sieves, `explain`, `verdict`, `wordiness`, `strain` |
| `chef.py` | `chefs_choice` (depth-first search with a budget), `tastiness`, `is_phrase_anagram` |
| `leftovers.py` | `arrangement_count`, `arrangements`, `sample_arrangements`, `shuffle_report` |
| `phrase_session.py` | `run_session`: the interactive phrase builder, with `ask`/`say` you can swap |
| `main.py` | The command line: `argparse`, an `input()` fallback, `--families`, `--phrase`, `--shuffle`, `--strain`, `--check`, `--chef`, `try`/`except OSError` |
| `../common/wordlist.py` | Shared: `read_words`, `clean_words` and the bundled dictionary |
| `../common/decency.py` | Shared: the short list of words kept off the web page, also checked inside made-up words |

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
- **`itertools.permutations`** makes every ordering; **`math.factorial`** says how many
  there will be first, so you know whether to ask.
- **Random samples** with `random.Random(seed)`, repeatable in tests and fresh on the page.
- **Overlapping slices.** `word[i:i + n]` for every `i` gives every n-gram, repeats and all.
- **`Counter.update` and `Counter.most_common`** count a whole dictionary's pairs, then walk
  them from most to least common.
- **Filtering in stages.** Each sieve is a list comprehension over the last one's survivors,
  so the count after every stage is just `len()`.
- **Functions in a dict.** `SIEVES = {"shape": catch_shape, ...}` lets a loop run whichever
  sieves are switched on.
- **`@dataclass` with `__post_init__`** holds the counted statistics, counted once.
- **`math.log1p`** for scores where ten times more should count as one step more.
- **Depth-first search with an explicit stack and a budget**, so a search always stops.
- **Dependency injection, lightly.** Giving `run_session` its `ask` and `say` makes an
  interactive program testable.

## Try this next

1. Is `Counter(a) == Counter(b)` faster than comparing sorted strings for single-word
   anagrams? Time both with `time.perf_counter()`.
2. Make the sieve smarter about *endings*: count the pair each word ends with, and catch
   orderings that end like no English word (*-gh* is fine, *-hg* isn't).
3. Give the chef a theme: pass a list of seaside words and give phrases a bonus for each one
   they use, so *Brighton Pier* prefers phrases about the beach.

## Further reading

- [Jumble](https://www.jumble.com/), the newspaper anagram puzzle.
- Online anagram makers: the [Internet Anagram Server](https://wordsmith.org/anagram/) and
  [dCode](https://www.dcode.fr/anagram-generator).
- *Think Python* by Allen Downey has more anagram exercises; *Cracking Codes with Python* by
  Al Sweigart has more on word patterns like the consonant/vowel shapes here.
