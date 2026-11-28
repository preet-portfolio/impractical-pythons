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

On the web page you pick a card from the rack and it lands on the desk, painted like its
front (its picture, paper and ink). Read it closely, then press **Reveal the secret**: the
hidden letters light up in the handwriting, the note appears in plain words on a luggage
tag with where it was hiding, and the shop stamps the card "Read between the lines". On a
card from a friend or your own pasted words, Reveal does what a suspicious jailer could
have done: Python tries every rule and count and keeps the one that reads as real words.
(An earlier version had a reading glass with rule buttons and a dial; it was cut because
a line of raw letters like "absw" meant nothing to visitors.)

At the **writing desk** you go the other way: type a secret note and Nan hides it in a list
of her Scrabble words, one letter per word. Or ask for **a proper postcard** from one of eight
seaside themes, with one letter hidden at the start of each sentence. Send the
postcard to a friend as a link, and all they see is a gran showing off (or a nice day
out), until they press Reveal.

## Play

```bash
uv run python projects/07_postcard_rack/main.py --today                  # today's card
uv run python projects/07_postcard_rack/main.py --lookahead 4            # the book's loop
uv run python projects/07_postcard_rack/main.py --rule capitals --lookahead 2
uv run python projects/07_postcard_rack/main.py --file letter.txt --lookahead 4
uv run python projects/07_postcard_rack/main.py --text "..." --rule words --lookahead 3
uv run python projects/07_postcard_rack/main.py --scan                   # let the dictionary pick
uv run python projects/07_postcard_rack/main.py --rule nth --lookahead 3 # every Nth word
uv run python projects/07_postcard_rack/main.py --write "meet me by the pier" --position 3
uv run python projects/07_postcard_rack/main.py --write "..." --position 2 --seed 7
```

With no text given it uses today's postcard. Bad input (an unknown rule, `--lookahead 0`, a
missing file, a note that's too short) prints one plain line to `stderr` and exits with
code 1.

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
card: the page asks Python where the secret letters are, then wraps each of those characters in a
`<mark>`.

Stepping over spaces with `continue` gives the same count as stripping them first (the
book's `"".join(text.split())`), but keeps every position pointing into the real text.

## Four rules in one table

```python
RULES = {
    "punctuation": after_punctuation,
    "words": of_each_word,
    "capitals": of_capital_words,
    "nth": every_nth_word,
}
```

A dict of functions means the CLI, the scan and the web page all pick a rule by name, and
adding a rule is one line. The two word rules share `word_letters`, which uses
`re.finditer(r"[A-Za-z]+")` to find each word and its start position.

`every_nth_word` is the book's "Colchester Catch" practice project: the Nth letter of every
Nth word. Here a word is anything between spaces (`re.finditer(r"\S+")`), so "didn't" counts
as one word, and only its letters are counted inside it. The caravan-park card hides "ghost
train" in the 2nd letter of every 2nd word. With N = 1 this rule picks the same letters as
"1st letter of every word", so `scan` keeps a `seen` set and shows each reading once.

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

## Writing a note: Nan's Scrabble words

Writing a null cipher is much harder than finding one. Every sentence has to make sense
*and* put the right letter in the right place. The book's answer is a **list**: nobody
expects a list to make sense, so any word will do. Ours is Nan bragging about her Scrabble
words, because any odd word can be a great Scrabble word.

```
keep only the note's letters (string.ascii_letters), lower case
check it: 6 to 40 letters, nothing rude
group Nan's words by the letter at the chosen position (2nd, 3rd or 4th)
for each letter of the note:
    pick a word from that letter's group that isn't already on the card
card = "Nan won at Scrabble again with these words: " + the words joined by ", " + "."
```

`null_writer.py` does this, and three choices make it work with the glass:

- **The commas are the cipher.** Each comma restarts the count, so the glass's punctuation
  rule reads "the 3rd letter after each punctuation mark" straight back. A test writes
  dozens of cards and checks that `scan` ranks the right setting first every time.
- **The cover line has no marks of its own.** "Nan won at Scrabble again with these words"
  has no apostrophe or comma, so the count starts at the colon and no stray letters creep in.
- **A seeded `random.Random(seed)`** picks among the words, from a *sorted* list, so the
  same note and seed always give the same card (that's what makes it testable) and "Write
  it again" just tries the next seed. `choose_words` is kept apart from `hide_note` so the
  web page can group the dictionary once and reuse it for every card.

**Keeping the card kind.** The dictionary is honest, and the pier's family-friendly list
turned out to let some slurs and grim words through. Nan's words go out on a public
postcard, so `postcard_words` is stricter: it drops any word containing a stem from
`NOT_ON_A_POSTCARD`, plus anything `nothing_rude_inside` catches. That throws out some
innocent words too ("peacock", "begun"), which is fine: the card only needs enough words,
and there are still nearly 30,000.

**Sending it.** `pack_card` turns the card's text and names into a link: JSON, then
URL-safe Base64 (the same trick as the Pier Telegraph's challenge links). The note itself
is never in the link; your friend has to find it. `unpack_card` checks every field of
whatever arrives and raises `NoteProblem` with a plain reason, so a smudged link gets a
friendly message instead of a crash.

## A proper postcard, from eight themes

A list is easy to hide in but looks like a list. A postcard that reads naturally is the
hard version: every sentence has to make sense *and* carry the right letter. The trick is
to make every sentence the same shape, "Somebody did something.":

```
check the note: 6 to 16 letters (one sentence each), nothing rude
shuffle the theme's 20 ready-written endings ("found a crab under a rock")
for each letter:
    pick a person whose name has that letter at the chosen position (Ezra, Max, Nan...)
    sentence = person + ending + "."
card = the theme's opening line ("Wish you were here!") + the sentences
```

`postcard_themes.py` holds the eight themes, one for each picture on the rack (Beach day, On the pier, Rainy day, Caravan
holiday, Fish and chips, Lighthouse walk, Donkey rides, Arcade night), each with its own opening line, postmark, picture and 20 endings,
plus about 210 first names and family words. `write_story` in `null_writer.py` does the rest.

- **The opening line's "!" starts the count** and every full stop restarts it, so the note
  sits in the Nth letter of each sentence's first word: the glass's punctuation rule.
- **Every ending names nobody and is past tense**, so it fits any subject: "Ezra lost a
  flip flop", "Grandad lost a flip flop", "Cousins lost a flip flop".
- **Plenty of names** means every letter has someone at every position, even q, x, z and
  j (Iqbal, Axel, Liza, Benji). A test checks all 26 letters × 3 positions, and another
  checks that no ending or opening has a stray punctuation mark.
- **A seeded `random.Random`** shuffles the endings and picks the people, so "Write it
  again" gives a new card, and nobody turns up twice unless a rare letter runs out.
- **The postmark travels with the card.** A link only carries the text, so `theme_of`
  recognises the theme from the opening line and the friend sees the right picture.

Short notes are honest. "go to the pub" is all real words, but tiny ones, and the glass's
strict test (words averaging 3 letters or more) was written to stop chance passing off "at
men a" as a message. On a card from the writing desk, the writer's own settings (2nd, 3rd
or 4th letter after punctuation) skip that test and go first in "Try every setting". The
sender's own note always counts, even with words the dictionary lacks ("ok"), and a friend
who gets "mostly real words" is told to look for themselves.

## Today's postcard

`todays_postcard(day)` counts days since the rack went up and cycles through the cards that
hide something, so everyone who visits on the same day gets the same card with no server
deciding. The web page passes the visitor's own date.

## Files

| File | What's in it |
|---|---|
| `null_finder.py` | The four rules, `picked_positions`, `describe`, `read_reading` and `scan` |
| `null_writer.py` | Hides a note in Nan's Scrabble words or a themed postcard, and packs and unpacks postcard links |
| `postcard_themes.py` | The eight postcard themes and the names that carry the letters |
| `postcards.py` | The eight postcards (seven notes and one decoy) and the daily pick |
| `main.py` | The command line: `--lookahead`, `--rule`, `--scan`, `--today`, `--write`, `--file`, `--text` |
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
- **`string.ascii_letters`** to keep only the letters of a note.
- **A seeded `random.Random`** choosing from a sorted list, for repeatable output.
- **Hiding in a list**: why a list beats a letter for a null cipher.
- **JSON + URL-safe Base64** to carry data in a link, checked on the way back in.
- **A round-trip test**: write a card, then check the finder reads it back.
- **Templates that always fit**: one sentence shape ("Somebody did something.") makes
  any subject work with any ending.
- **Data-driven tests**: every letter at every position, and every ending checked for
  stray marks, so new themes can't quietly break the cipher.

## Try this next

1. **Saving Mary** (the book's other practice project): alternate the note between the 2nd
   and 3rd letters, and slip in decoy words that carry nothing. Then teach the glass to
   read it.
2. **A fourth rule**: the last letter of every line, or the letter after every capital.
   Add one function to `RULES` and the page, scan and CLI pick it up.
3. **Scan something famous**: run `--scan --file` on a poem or a song you like and see
   whether chance hides anything readable. How long a lucky reading can you find?

---

Inspired by the Trevanion cipher and list cipher projects (and the Colchester Catch practice
project) in [*Impractical Python Projects*](https://nostarch.com/impracticalpython) by Lee
Vaughan. The postcards, Nan's Scrabble cover, the eight themes, scoring, links and web
page are new.
