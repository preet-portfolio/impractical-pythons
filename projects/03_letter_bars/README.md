# 03 · Letter Bars

Every language leaves a fingerprint in how often it uses each letter. English leans on
E, T and A; Spanish piles up A, E and O; French loves E and S. Letter Bars counts the
letters in anything you type and draws them as bars, all 26 of them, so two texts (or two
languages) line up side by side.

On the web it's a seaside rock shop: every letter is a stick of striped candy rock as long
as its share of your letters, with chocolate notches marking ordinary English.

## Play

```bash
uv run python projects/03_letter_bars/main.py "Like a bad penny"
uv run python projects/03_letter_bars/main.py --sample French
uv run python projects/03_letter_bars/main.py --compare English Spanish
```

A single text prints with `pprint`, where each letter's bar is made of the letter itself
(`'e': 'eeeeeeee'`). `--compare` prints two samples side by side, one `#` per 1% of letters.

## Design first: the pseudocode

```
count_letters(text):
    counts = a dictionary that starts every letter at 0
    for each character:
        fold it to plain a-z (é -> e, ñ -> n, ß -> ss; digits and spaces -> nothing)
        add one to each letter it folds to
compare(a, b):
    turn each text's counts into percentages
    for each letter from a to z: pair up the two percentages
top letters: sort by (biggest count first, then alphabetical) and take six
```

## Files

| File | What's in it |
|---|---|
| `letter_bars.py` | `fold`, `count_letters`, `accents`, `shares`, `top_letters`, `bar_chart`, `compare`, `chart_data` and three sample postcards |
| `main.py` | The terminal chart (`argparse`, `pprint`) |
| `../common/english.py` | `ENGLISH`, the usual English letter shares. It's shared, because Pier Telegraph uses it too to tell a shuffled telegram from a swapped one |

The sample postcard (a summer evening on a pier) and its Spanish and French versions were
written for this project. The "usual English" figures are Robert Lewand's widely quoted
letter frequencies (*Cryptological Mathematics*, 2000), the table Wikipedia's "Letter
frequency" article uses.

## What's new here

- **`collections.defaultdict(int)`**: a dictionary that hands back 0 for a missing key, so
  counting is just `counts[letter] += 1`.
- **`unicodedata.normalize("NFD", ...)`** splits *é* into *e* plus a combining accent, which
  is how accents get folded. A small table handles letters Unicode doesn't split (*ß*, *æ*).
- **Sorting with a key**: `sorted(letters, key=lambda l: (-counts[l], l))` ranks by count
  and breaks ties alphabetically, so the answer never depends on the order letters arrived.
- **`pprint`** prints a dictionary one key per line, which turns `bar_chart()` into a
  sideways bar chart for free.
- **Shares, not counts**: dividing by the total lets a postcard and a novel be compared.

## Try this next

1. Add a German or Italian postcard. Which letters give each language away fastest?
2. Write `guess_language(text)` that picks the sample whose shares are closest to the
   text's (try summing the absolute differences). How short can a text be before it fails?
3. Count pairs of letters (*th*, *he*, *in*) instead of single ones. Which pair is most
   common in each language?
