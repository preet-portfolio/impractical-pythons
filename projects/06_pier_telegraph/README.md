# 06 · Pier Telegraph

At the end of the pier there's a little telegraph office: mahogany counter, brass fittings,
yellow telegram forms. Hand over a message and the clerk files each word in a wooden
pigeonhole rack, left to right, a row at a time. Then they send the words down the wire in a
different order: up one column, down the next, in a sequence only the office at the other end
knows.

This is a **route cipher**. It doesn't change any words; it only shuffles them. To make the
shuffled telegram harder to read, the clerks also swap the important words for code words from
the office code book (*the money* goes out as DONKEY) and fill the empty pigeonholes with
harmless filler like PEBBLE and KITE.

Every day a new telegram is waiting on the counter, and nobody wrote down its route. Crack it,
then send your own to a friend as a challenge link: they have to crack your route to read it.
Stuck? Wake the **night clerk**, who tries every route at once. Out on the promenade the field
clerks use a quicker cipher, the **rail fence**, which zigzags letters between two railings.

## Play

```bash
uv run python projects/06_pier_telegraph/main.py                     # decode the settings block
uv run python projects/06_pier_telegraph/main.py --key "-1 2 -3 4 -5"
uv run python projects/06_pier_telegraph/main.py --cipher "tell under BUCKET on ..." --cols 5 --key "1 -2 3 -4 5"
uv run python projects/06_pier_telegraph/main.py --encrypt "Meet the manager at midnight"
uv run python projects/06_pier_telegraph/main.py --encrypt "Meet the manager by the pier" --cols 2 --key "2 -1"
uv run python projects/06_pier_telegraph/main.py --today                 # today's puzzle
uv run python projects/06_pier_telegraph/main.py --night-clerk --hunch "gull won" --hunch "and nobody"
uv run python projects/06_pier_telegraph/main.py --rail "Let us cross the pier"
uv run python projects/06_pier_telegraph/main.py --unrail "LTSRS TEIRE UCOSH PE"
uv run python projects/06_pier_telegraph/main.py --unrail "..." --rails 3
uv run python projects/06_pier_telegraph/main.py --crack-rails           # the intercepted one
uv run python projects/06_pier_telegraph/main.py --sniff "LTSRS TEIRT OTDAD ..."
```

The easiest way of all: open `main.py`, find the block marked `YOUR TELEGRAM`, paste in the
telegram, the columns, the rows and the key, and run it with no options.

## Design first: the pseudocode

Sending:

```
swap code-book phrases for code words
pick a rack: columns × rows with room for every word, less than one row of filler
pad the empty pigeonholes with filler words
for each number in the key:
    column = the number, counting from 1
    read that column top to bottom if the number is positive, bottom to top if negative
the words in that order are the telegram
```

Receiving:

```
check columns × rows equals the number of words, and the key uses every column once
cut the telegram into runs of `rows` words: one run per column, in key order
put each run back in its column, the right way up
read the rack across the rows
swap code words back, drop the filler at the end
```

## Filling the rack and walking the route

Cells are numbered across the rows, the way a person writes:

```
key  -1   2  -3   4           0  1  2  3
      ^   |   ^   |           4  5  6  7
      |   v   |   v           8  9 10 11
```

`route_order(cols, rows, key)` lists the cells in the order the route visits them. For each
number in the key it makes a `range` down the column, or a reversed range up it, and turns
each row into a cell number with `row * cols + column`. For the 4 × 3 rack above with the key
`-1 2 -3 4` that's `8 4 0 1 5 9 10 6 2 3 7 11`. Encrypting is then one line:
`[words[cell] for cell in order]`. The web page uses the very same list to draw the route
through the rack.

## Decrypting: a matrix and `pop()`

The telegram is the columns laid end to end, `rows` words each, in key order. `build_matrix`
slices those runs back out (`cipher[i * rows:(i + 1) * rows]`) and puts each in its column's
slot, stored **bottom word first**. A column read upwards already arrived bottom first; one
read downwards is flipped with `run[::-1]`.

Why bottom first? Because `list.pop()` takes the **last** item. `decrypt_matrix` loops once
per row, and on each pass pops one word off every column: the top row comes out first, then
the next, until the matrix is empty and the message is back in order.

```python
>>> matrix = [["and", "on", "meet"], ["bring", "WHELK", "GULL"]]
>>> [column.pop() for column in matrix]
['meet', 'GULL']
```

A test checks this against a completely different method (putting each word straight back
in its cell using `route_order`), and another round-trips every possible key for a 4-column
rack.

## Designing for human error

Real telegraph clerks were tired, rushed and working by lamplight. So were the people who had
to decode their messages. This stall makes mistakes hard to make, in two different ways.

**On the command line, mistakes get a plain explanation.** `route.py` defines its own
exceptions: `TelegramProblem` (a kind of `ValueError`), with `KeyProblem` and `GridProblem`
under it. Each check matches a slip a person might really make and says how to fix it:

```
The office can't do that: Columns count from 1, so the key can't use 0.
The office can't do that: Column 3 is in the key twice. Use each once.
The office can't do that: 4 columns × 4 rows is 16 pigeonholes, but the telegram has 15 words.
Column counts that fit: 3, 5.
```

`main.py` catches `TelegramProblem` (and only that), prints the message to `stderr` and exits
with code 1, so a script calling it can tell something went wrong. Anything else is a real bug
and still crashes loudly. The settings block at the top of `main.py` means you never have to
remember the options.

**On the web page, mistakes can't happen at all.** Rack sizes are buttons, and Python only
offers the ones that fit. The route is built from chips (tap to flip a column's arrow, nudge
to change its place), so every route you can make uses each column exactly once. The key is
still shown underneath (`-1 2 -3 4`) for anyone who wants to send it.

## The web page

Python does all the work: the page's small bridge calls `codebook.encode`, `grid_options`,
`pad`, `route_order`, `encrypt` and `decrypt`, and the page only draws what comes back. When you
press **Check the route**, Python compares your rack with the answer and says how many words are
in the right pigeonhole. When all of them are, the DELIVERED stamp comes down and the code words
are swapped back.

## A telegram a day, with no server

Everyone who opens the page on the same day should get the same puzzle, but the site has no
server to hand one out. So the date does the choosing (`dispatches.py`):

1. `telegram_number` counts the days since the office opened: No. 1, No. 2, and so on.
2. That number picks a message from `DISPATCHES` (looping round when they run out).
3. The same number seeds a `random.Random`, which rolls the route. A seeded generator gives the
   same "random" numbers every time, on every computer, so everybody's telegram matches.

A random route can be too easy: reading every column straight down might already get most
words right. `scrambled_key` checks that "lazy guess" with `plain_route_hits` and rolls again
until the guess gets at most a fifth of the words. It tries at most 100 times (a `for` loop with
a limit, never `while True`) and keeps the best route it saw. A test checks all 14 telegrams.

## Challenge links: sending the puzzle, not the answer

A challenge link (`challenge.py`) has to let a friend's browser say "you've cracked it" without
carrying the answer. It packs two things:

- the **scrambled telegram**, which the friend can see anyway, and
- a **fingerprint** of the right order: the first 12 characters of a SHA-256 hash of the words.

`hashlib.sha256` turns any text into a fixed-size string of hex digits. The same words always
give the same hash, a single word moved gives a completely different one, and there's no way to
run it backwards. So when the friend presses Check, their browser fingerprints *their* rack and
compares. The key never leaves the sender's screen.

To fit in a link, the two go through `json.dumps` (data to text) and then
`base64.urlsafe_b64encode` (text to just letters, digits, `-` and `_`). `read_challenge` undoes
that and checks everything, because anything can arrive in a link: a cut-off or edited link
raises `ChallengeProblem` with a plain message, and the page falls back to today's telegram.

Could someone cheat? They could try every possible route and compare fingerprints. That's a
brute-force attack, and the night clerk does exactly that (see below).

## The night clerk: trying every route

A route's key is an order of the columns plus an arrow for each one. `itertools.permutations`
gives every order and `itertools.product((1, -1), repeat=cols)` every set of arrows, so
`all_keys` is two nested loops over them. Both hand out one answer at a time (they're lazy),
so the clerk never builds a list of 46,080 keys in memory.

How many routes is that? `cols!` orders times `2 ** cols` arrows:

| Columns | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|
| Routes | 8 | 48 | 384 | 3,840 | 46,080 | 645,120 |

A 12-word telegram fits racks of 2, 3, 4 and 6 columns, so the clerk tries all four: 46,520
routes. In the browser that takes under a second. Seven columns would take about 14 times
longer, so the clerk stops at six (`WIDEST`) and says which racks it skipped.

**The catch: the clerk can't read.** `readability` scores each reading with rules a tired
clerk would notice: filler belongs at the end, "the" comes before a thing (not before "and"),
and a message doesn't end on "under". Those rules sort little words into jobs (`KINDS`) and
score neighbouring pairs. They can't tell "fortune teller says" from "teller says fortune",
because every ordinary word looks the same to them. On its own the clerk put the right answer
anywhere from 1st to 1,400th.

So the clerk takes **hunches**: pairs of words you're sure sit side by side ("ice cream",
"at BUCKET"). `fits` throws out every route that pulls a hunch apart. One hunch cuts thousands
of routes to hundreds; three usually leave a handful, and a test checks that three hunches put
the answer in the clerk's top five for all 14 daily telegrams. That's how real code-breakers
worked too: a computer to grind through the possibilities, a person to guess a likely word or
phrase (a *crib*).

`expand` also fixed a quiet bug in waiting: a message about a real sandcastle used to look like
SANDCASTLE the filler. The office writes code words and filler in capitals, so the clerk
compares words exactly, capitals and all.

## Breaking the seal

A challenge link's seal needs no hunches. `crack_seal` tries routes until one has the same
SHA-256 fingerprint, and stops there. A 12-word telegram falls in a few hundred tries. A
fingerprint is only as safe as the number of answers it could stand for: 46,520 is nothing to
a computer. Real passwords and keys have so many possibilities that trying them all would take
longer than the age of the universe. That's the whole trick.

## The rail fence

The field cipher in `rail_fence.py` works on letters, not words. `prepare` keeps only the
letters, in capitals (`unicodedata.normalize("NFKD", ...)` splits é into e plus an accent mark
first, so the e survives). Then the letters zigzag between two rails:

```
L T S R S T E I R       top rail
 E U C O S H P E        bottom rail
```

The telegram is the top rail then the bottom one, in groups of five: "Let us cross the pier"
goes out as `LTSRS TEIRE UCOSH PE`.

`zigzag_rows(length, rails)` says which rail each letter sits on. The pattern down and back up
(`0 1 2 1` for three rails) repeats, so `pattern[i % len(pattern)]` finds any letter's place.
Encrypting reads the letters rail by rail.

Decrypting two rails is a neat trick: the top rail holds the 1st, 3rd, 5th... letters, so it
has the extra one when the count is odd. `math.ceil(len(cipher) / 2)` finds where to cut, and
`itertools.zip_longest` stitches the halves back together, filling the short bottom rail with
`""` instead of stopping early as `zip` would. `zigzag_decrypt` does any number of rails: count
how many letters landed on each rail, slice the cipher into those runs, then walk the zigzag
taking the next letter from whichever rail the walk is on. A test checks the two agree.

Senders on the pier always use two rails. The intercepted telegram used three, and nobody
knows that until they try. `crack_rails` tries 2 to 8 rails: just 7 tries, against 3,840 for a
five-column route.

## Putting the gaps back

Rail fence letters arrive with no spaces. `word_gaps.split_words` (in `projects/common`, shared with the Postcard Rack) puts them back using the
shared 60,000-word dictionary, with **dynamic programming**: work left to right, and for every
position remember only the best way to split the letters up to there. Each answer is built
from a shorter one plus one more word, so nothing is worked out twice. "Best" is a tuple,
`(letters covered, -pieces, everyday words)`, which Python compares item by item, so `max`
tries each rule in turn:

1. cover as many letters with real words as possible;
2. then use the fewest pieces ("seagulls", not "sea gulls");
3. then prefer everyday words ("pier at", not "pie rat"; "is under", not "i sunder").

Letters no word explains stay in capitals, so nothing is lost. `coverage` (the share of
letters inside real words) is how the cracker scores each rail count: the right one is 100%,
the wrong ones about 50%.

## Shuffled or swapped?

A rail fence **shuffles** letters; a substitution cipher **swaps** each letter for another.
`sniff.py` tells them apart before trying to crack anything. A shuffled telegram still has
English's letters, so E, T and A still turn up most. A swapped one has the same shape on the
wrong letters.

`english_likeness` is a **chi-squared** score: for each letter, the difference between its
count and what English would give (from `common/english.py`, shared with Letter Bars),
squared, divided by what English would give, all added up and divided by the number of
letters. Shuffled pier telegrams score under 0.7; swapped ones mostly 2 to 40. In between, a
swap that happened to land on look-alike letters can pass for English, so `verdict` says
"hard to say" there, and "too short" under 30 letters.

## Files

| File | What's in it |
|---|---|
| `route.py` | `factors`, `check_grid`, `check_key`, `parse_key`, `route_order`, `encrypt`, `build_matrix`, `decrypt_matrix`, `decrypt`, and the `TelegramProblem` exceptions |
| `codebook.py` | `CODEBOOK`, `FILLER`, `SAMPLE`, `TICKETS`, `plain_words`, `encode`, `decode`, `grid_options`, `snuggest`, `pad` |
| `dispatches.py` | `DISPATCHES`, `telegram_number`, `plain_route_hits`, `scrambled_key`, `is_fair`, `puzzle_rack`, `dispatch`, `todays_dispatch` |
| `challenge.py` | `fingerprint`, `make_challenge`, `looks_like_telegram`, `read_challenge`, `is_solved`, `ChallengeProblem` |
| `night_clerk.py` | `key_count`, `all_keys`, `place`, `expand`, `readability`, `fits`, `racks`, `crack_route`, `crack_seal`, `crack_rails` |
| `rail_fence.py` | `prepare`, `zigzag_rows`, `encrypt`, `in_fives`, `two_rail_decrypt`, `zigzag_decrypt`, `decrypt`, `intercepted`, `RailProblem`, the sample messages |
| `../common/word_gaps.py` | `word_set`, `split_words`, `join_strays`, `coverage`. Shared, because the Postcard Rack uses it too |
| `sniff.py` | `letter_shares`, `english_likeness`, `verdict`, `decide`, `explain`, `swap_letters` |
| `main.py` | The settings block, `receive`, `send`, `show_today`, the night clerk, rail fence and sniff commands, `argparse` options, friendly errors on `stderr` with exit code 1 |

## What's new here

- **`str.split()` with no argument** splits on any run of spaces, tabs or newlines, so a
  pasted telegram with odd spacing still works.
- **A list of lists** as a matrix: one inner list per column.
- **Slicing with a negative step.** `run[::-1]` flips a list; `range(rows - 1, -1, -1)` counts
  down.
- **`list.pop()`** takes (and removes) the last item, which is why the columns are stored
  bottom first.
- **`abs()`** turns a signed key number into a column, while its sign gives the direction.
- **Your own exception classes.** Subclassing `ValueError` lets callers catch just your
  problems, and the class names say what went wrong.
- **`raise ... from None`** hides the less helpful error underneath (`int("two")` failing)
  when you raise a clearer one.
- **`for` ... `else`** in `encode`: the `else` runs only when the loop finished without a
  `break`, meaning no code-book phrase started at that word.
- **Type aliases.** `Words = list[str]` and `Key = list[int]` make signatures read like the
  problem.
- **`sys.exit(1)` and `stderr`** for errors, so the shell (and other programs) can tell.
- **A settings block** at the top of a script, for people who'd rather edit than type options.
- **`datetime.date` arithmetic.** Subtracting two dates gives a `timedelta`; `.days` turns
  it into a number.
- **Seeded randomness as a shared secret.** `random.Random(number)` rolls the same route for
  everyone, which is how a static site can have a daily puzzle.
- **A retry loop with a limit.** `for _ in range(100)` plus `break`, keeping the best so far.
- **`hashlib.sha256`** for a one-way fingerprint: check an answer without storing it.
- **`json` plus `base64.urlsafe_b64encode`** to pack data into a link, and validating
  everything that comes back out.
- **Rounding up with `-(-a // b)`**: floor division of a negative number rounds the other
  way. (`math.ceil` does the same, as the rail fence shows.)
- **`itertools.permutations` and `itertools.product`** to list every key, lazily.
- **`math.factorial`** and the key-count explosion behind brute-force attacks.
- **`itertools.pairwise`** for looking at neighbouring words.
- **`itertools.zip_longest`** for pairing lists of different lengths.
- **The `%` remainder** to repeat a pattern (the zigzag) forever.
- **`unicodedata.normalize("NFKD")`** to take accents off letters.
- **Dynamic programming** to split letters into words without trying every split.
- **Tuples as scores**: `max` compares them item by item, so one tuple holds several rules.
- **Chi-squared** to compare letter counts with English.
- **`str.maketrans` and `str.translate`** to swap every letter at once.
- **A `type` alias statement** (`type Hunch = ...`), Python 3.12's way to name a type.

## Try this next

1. Add a **spiral route**: round the outside of the rack and inwards. Write
   `spiral_order(cols, rows)` that returns cell numbers like `route_order` does, and check that
   decrypting by inverting it gets the message back.
2. Make the code book **two-way safe**: warn when a message already contains a code word
   (someone writing about an actual gull), and pick a different one for that telegram.
3. Let a challenge link carry a **hint**: how many columns the rack had, or which column
   comes first, chosen by the sender. What would you add to the payload, and does it give
   anything else away?
4. Teach the night clerk more English: give `readability` a list of word pairs counted from a
   long text (a book from Project Gutenberg) and see how many hunches it still needs.
5. A **three-rail** sender: add a rails picker to the page, and check `crack_rails` still finds
   the count. What happens with a message shorter than the zigzag?
6. Make `sniff` spot a **Caesar shift** (every letter moved the same distance) and say how far,
   by trying all 25 shifts and keeping the one with the lowest chi-squared score.

## Further reading

The idea comes from the route cipher and rail fence cipher projects in chapter 4 of
[*Impractical Python Projects*](https://nostarch.com/impracticalpython) by Lee Vaughan, which
looks at how both were used on the American Civil War telegraph. The code book, telegrams,
racks, hunches, intercepted telegram and code here are new.
