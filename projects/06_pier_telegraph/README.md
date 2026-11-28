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

## Play

```bash
uv run python projects/06_pier_telegraph/main.py                     # decode the settings block
uv run python projects/06_pier_telegraph/main.py --key "-1 2 -3 4 -5"
uv run python projects/06_pier_telegraph/main.py --cipher "tell under BUCKET on ..." --cols 5 --key "1 -2 3 -4 5"
uv run python projects/06_pier_telegraph/main.py --encrypt "Meet the manager at midnight"
uv run python projects/06_pier_telegraph/main.py --encrypt "Meet the manager by the pier" --cols 2 --key "2 -1"
uv run python projects/06_pier_telegraph/main.py --today                 # today's puzzle
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
brute-force attack, and it's coming to this stall later in the chapter.

## Files

| File | What's in it |
|---|---|
| `route.py` | `factors`, `check_grid`, `check_key`, `parse_key`, `route_order`, `encrypt`, `build_matrix`, `decrypt_matrix`, `decrypt`, and the `TelegramProblem` exceptions |
| `codebook.py` | `CODEBOOK`, `FILLER`, `SAMPLE`, `TICKETS`, `plain_words`, `encode`, `decode`, `grid_options`, `snuggest`, `pad` |
| `dispatches.py` | `DISPATCHES`, `telegram_number`, `plain_route_hits`, `scrambled_key`, `is_fair`, `puzzle_rack`, `dispatch`, `todays_dispatch` |
| `challenge.py` | `fingerprint`, `make_challenge`, `looks_like_telegram`, `read_challenge`, `is_solved`, `ChallengeProblem` |
| `main.py` | The settings block, `receive`, `send`, `show_today`, `argparse` options, friendly errors on `stderr` with exit code 1 |

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
  way.

## Try this next

1. Add a **spiral route**: round the outside of the rack and inwards. Write
   `spiral_order(cols, rows)` that returns cell numbers like `route_order` does, and check that
   decrypting by inverting it gets the message back.
2. Make the code book **two-way safe**: warn when a message already contains a code word
   (someone writing about an actual gull), and pick a different one for that telegram.
3. Let a challenge link carry a **hint**: how many columns the rack had, or which column
   comes first, chosen by the sender. What would you add to the payload, and does it give
   anything else away?
4. Write `crack(cipher, cols, rows)` that tries **every** key for a rack and scores each result
   by how many neighbouring word pairs appear in the sample messages. How many keys are there
   for 5 columns? (Hint: orderings times directions.)

## Further reading

The idea comes from the route cipher project in chapter 4 of
[*Impractical Python Projects*](https://nostarch.com/impracticalpython) by Lee Vaughan, which
looks at how route ciphers were used on the American Civil War telegraph. The code book,
telegrams, racks and code here are new.
