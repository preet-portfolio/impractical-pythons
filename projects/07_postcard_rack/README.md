# 07 · The Postcard Rack

Outside the pier's gift shop there's a wire rack of postcards. Every one says the usual
things: the weather's lovely, Nan fell asleep in a deckchair, wish you were here. Some of
them say something else as well, and the postman never notices.

The trick is a **null cipher**. The hidden note isn't scrambled at all: its letters sit
inside an ordinary message at places the sender and reader agreed on (one letter after
every comma and full stop, say, or the first letter of every capitalised word). Every other
letter is padding, a "null". Hiding the fact that a message exists at all is called
**steganography**, from the Greek for "covered writing".

The famous case comes from the English Civil War. In 1642 a Royalist prisoner was sent a
letter his jailers read and passed as harmless. Counting three letters on from each
punctuation mark spelled out where to find the way out of the chapel, and by morning he
was gone. Every postcard on this rack was written for this stall; none of them copy that
letter.

On the web page you hold a **reading glass** over a card: pick what to count from, turn
the dial for how many letters along, and the letters it lands on light up in the
handwriting. On the right setting the hidden note appears on a luggage tag and the shop
stamps the card "Read between the lines". **Try every setting** does what a suspicious
jailer could have done, and there's a blank card for any text you want to test.

## Play

```bash
uv run python projects/07_postcard_rack/main.py --today                  # today's card
uv run python projects/07_postcard_rack/main.py --lookahead 4            # the book's loop
uv run python projects/07_postcard_rack/main.py --rule capitals --lookahead 2
uv run python projects/07_postcard_rack/main.py --file letter.txt --lookahead 4
uv run python projects/07_postcard_rack/main.py --text "..." --rule words --lookahead 3
uv run python projects/07_postcard_rack/main.py --scan                   # let the dictionary pick
```

With no text given it uses today's postcard. Bad input (an unknown rule, `--lookahead 0`, a
missing file) prints one plain line to `stderr` and exits with code 1.

## Design first: the pseudocode

Reading a message hidden after punctuation:

```
take out every space
count = 0, found_first = false
for each character:
    if it's punctuation:
        count = 0, found_first = true        # every mark starts the count again
    else if found_first:
        count += 1
        if count == lookahead: write this letter down
the letters written down are the message
```

Three small rules carry the whole cipher. **Every mark resets the count**, so a second
mark before you reach the Nth letter starts it again. **Punctuation never counts** as one
of the letters. **Nothing counts before the first mark**, which is what the `found_first`
flag is for. Writing these cards by hand showed how fragile that makes it: one stray
apostrophe in "it's" restarts the count and the note falls apart. A test checks every card.

## Positions, not letters

The book's version returns the hidden letters. `after_punctuation(text, offset)` returns
their **positions** in the original text instead, and `hidden_letters` builds the letters
from those. That one change is what lets the web page light up the exact letters on the
card: the page asks Python where the glass lands, then wraps each of those characters in a
`<mark>`.

Stepping over spaces with `continue` gives the same count as stripping them first (the
book's `"".join(text.split())`), but keeps every position pointing into the real text.

## Three rules in one table

```python
RULES = {
    "punctuation": after_punctuation,
    "words": of_each_word,
    "capitals": of_capital_words,
}
```

A dict of functions means the CLI, the scan and the web page all pick a rule by name, and
adding a fourth rule is one line. The two word rules share `word_letters`, which uses
`re.finditer(r"[A-Za-z]+")` to find each word and its start position.

`string.punctuation` decides what counts as a mark: ``!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~``.
Note the apostrophe and the hyphen are in there.

## Trying every setting

The book's lookahead loop prints a reading for every offset up to N and leaves you to spot
the one that makes sense. `scan(text, words)` goes further: it tries every rule and every
offset up to 6, then asks the dictionary how well each one reads.

`read_reading` uses `split_words` from `projects/common/word_gaps.py` (the same
dynamic-programming word splitter the Pier Telegraph uses to crack a rail fence, moved into
`common/` now that two stalls need it) to put the gaps back. Then:

- **coverage** is the share of letters that land inside real words;
- **word length** is the average length of those words.

Coverage alone isn't enough. Chance is very good at making "a", "at", "me" and "men", so a
wrong setting can score 100% with "at men a". A reading only **reads** if it's at least 6
letters, at least 95% words, and those words average 3 letters or more. The scan sorts by
that, then coverage, then word length, with a tuple sort key. The tests check that every
postcard's own setting comes out first, and that the decoy card (the one with nothing to
hide) has no reading at all.

## Today's postcard

`todays_postcard(day)` counts days since the rack went up and cycles through the cards that
hide something, so everyone who visits on the same day gets the same card with no server
deciding. The web page passes the visitor's own date.

## Files

| File | What's in it |
|---|---|
| `null_finder.py` | The three rules, `picked_positions`, `describe`, `read_reading` and `scan` |
| `postcards.py` | The seven postcards (six notes and one decoy) and the daily pick |
| `main.py` | The command line: `--lookahead`, `--rule`, `--scan`, `--today`, `--file`, `--text` |
| `../common/word_gaps.py` | Puts the gaps back between words (shared with the Pier Telegraph) |

The web page is `web/postcard-rack/index.html` with `web/src/postcard-rack-page.ts`; it runs
these exact modules in the browser with Pyodide.

## What's new here

- **Steganography and null ciphers**: hiding that a message exists, not what it says.
- **`string.punctuation`** as a ready-made set of marks.
- **A state flag** (`found_first`) alongside a counter that resets.
- **Returning positions instead of values**, so a UI can point at the answer.
- **A dict of functions** to pick behaviour by name.
- **`re.finditer`** for words *and* where they start (`match.start()`).
- **Scoring with more than one number**: coverage alone is fooled by short words, so word
  length breaks the tie, sorted with a tuple key.
- **Moving shared code into `common/`** once a second project needs it.

## Try this next

1. **Write a null cipher** (the book's next project): given a note and a rule, pick words
   from a list so the right letters land in the right places, then make it read like a real
   postcard.
2. **A fourth rule**: the last letter of every line, or the letter after every capital.
   Add one function to `RULES` and the page, scan and CLI pick it up.
3. **Scan something famous**: run `--scan --file` on a poem or a song you like and see
   whether chance hides anything readable. How long a lucky reading can you find?

---

Inspired by the Trevanion cipher project in
[*Impractical Python Projects*](https://nostarch.com/impracticalpython) by Lee Vaughan. The
postcards, rules beyond punctuation, scoring and web page are new.
