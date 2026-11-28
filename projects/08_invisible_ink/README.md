# 08 · Vanishing Ink

Professor Pockett's Joke Shop on the pier sells vanishing ink, and somebody has left a letter
on the counter. It's a booking confirmation from The Gull's Rest guesthouse: breakfast times,
a warning about the gulls, nothing anybody would read twice. But its blank lines aren't
blank. They're written in ink the same colour as the paper, and under the shop's UV lamp they
glow: a plot to fix the pier's duck race, scrambled with a key word.

The trick is **steganography** at its simplest: set the text colour to the paper colour. A
glance sees the usual gaps between paragraphs, and a printout drops the ink entirely. In
case someone does look, the ink is also scrambled with the **Vigenère cipher**. The letter,
the plot, the typewriter card and the key are all written for this stall.

On the web page you:

- **shine the lamp:** move the mouse (or tap) to use a UV torch, or switch the whole lamp on;
- **crack the key:** type a word to unscramble the ink, with a strip showing the key over
  the ink over what it reads (wrong keys say so; there's a clue if you're stuck);
- **see how it gets caught:** *Select all* shows blank lines of different lengths,
  *Spellcheck* underlines words nobody can see, *Save as plain text* drops the colour;
- **write your own:** a letter, a secret and a key, with a live room check, a real Word file
  to download, and a link that carries the letter but never the key;
- **try the typewriter trick:** a white letter in place of each space on a typewritten line;
- **check any Word letter:** drop in a .docx and Python lists any white or hidden text.

## Play

```bash
uv run python projects/08_invisible_ink/main.py --demo --out letter.docx
uv run python projects/08_invisible_ink/main.py --find letter.docx --key PUFFIN
uv run python projects/08_invisible_ink/main.py --hide cover.txt secret.txt --key GULL --out mine.docx
uv run python projects/08_invisible_ink/main.py --room cover.txt secret.txt
uv run python projects/08_invisible_ink/main.py --typewriter "LOST PROPERTY: one umbrella and two buckets" --secret KEY
uv run pytest tests/08_invisible_ink
```

Open a saved letter in Word, press Ctrl+A (Cmd+A on a Mac) and set the highlight colour to
black: the printed words disappear into the black and the white ink shows up.

## Design first: the pseudocode

```
read the cover letter, keeping its blank lines
read the secret, dropping its blank lines (fewer hiding places needed)
spell out numbers and symbols in the secret, then scramble each line with the key
if the letter has fewer blank lines than the secret has lines:
    say how many blank lines to add, and stop
for each line of the cover letter:
    if it's blank and some secret is left: write the next secret line, in white
    otherwise: write the line as it is
set every paragraph's space before and after to 0, so no gap looks bigger
zip the parts into a .docx
```

## The Vigenère cipher

The key word is written over the message again and again, and each key letter says how far
to shift the letter under it: A by 0, B by 1, … Z by 25.

```
key    K I T E
plain  c r a b
ink    m z t f      c+10=m, r+8=z, a+19=t, b+4=f
```

`vigenere.py` does this with `ALPHABET.index` and `% 26` to wrap round from Z to A. Two
details matter for a letter:

- **The key only moves on over letters.** Spaces and punctuation pass straight through, so
  "Meet me, 12 o'clock!" keeps its shape and still unscrambles exactly.
- **Numbers don't shift**, so "Duck 42" would leave "42" in plain sight. `spell_out` writes
  numbers and symbols as words first ("forty two", "percent", "and"), the book's own
  advice, using a small `number_words` for anything under a million.

The same plain letter scrambles differently depending on where it falls under the key,
which is why the cipher went unbroken for three centuries, until someone noticed that a
short key over a long message repeats.

## A Word file without python-docx

The book uses the `python-docx` package. It isn't one the browser's Python (Pyodide)
ships with, and the stall doesn't need it: a .docx file is a zip of a few XML files.
`docx_writer.py` writes the smallest set Word accepts:

| Part | What it says |
|---|---|
| `[Content_Types].xml` | what each file in the zip is |
| `_rels/.rels` | where the document is |
| `word/_rels/document.xml.rels` | where the styles are |
| `word/styles.xml` | one font (Georgia) and size for everything |
| `word/document.xml` | the letterhead, then one paragraph (`<w:p>`) per line |

A hidden line is a run (`<w:r>`) with `<w:color w:val="FFFFFF"/>`. Every paragraph gets
`<w:spacing w:before="0" w:after="0"/>`, the book's `set_spacing`, so the gaps that hold
ink are exactly as tall as empty ones. `xml.sax.saxutils.escape` keeps "Fish & chips" from
breaking the XML, and `zipfile.ZipFile(io.BytesIO(), "w")` builds the file in memory, so
the page can hand it straight to the browser as a download.

`docx_reader.py` goes the other way for the detector: unzip, parse `word/document.xml` with
`xml.etree.ElementTree`, and report every run that's white (or uses Word's own "hidden"
text, `<w:vanish/>`). Files come from visitors, so it refuses anything with a DOCTYPE (Word
never writes one, and that's where XML entity tricks live) and anything that unzips to more
than 5 MB.

## The practice project: is there room?

`room_check(cover, secret)` counts the cover's blank lines against the secret's lines and
says how many to add. On the page it runs as you type, and *Add the blank lines for me*
does the book's tip: press Enter a few more times under the signature. That's why
`letter_lines` keeps blank lines at the very end of a letter.

`long_lines` flags secret lines over 70 characters. A line that wraps makes its gap taller
than the others, which is the easiest way to give the game away. (On a very narrow phone
screen even short ink lines wrap: try the demo letter there to see exactly the tell the book
warns about.)

## The challenge project: ink between words

On a typewriter every character is the same width, so a white letter where a space should
be looks exactly like the space. `between_words(cover, secret)` puts one secret character
in each gap of a typewritten line and returns pieces marked hidden or not;
`read_between_words` reads them back. In a normal (proportional) font this fails: an "m" is
wider than a space, and the words would drift apart.

## Files

| File | What it does |
|---|---|
| `vigenere.py` | The cipher, the key-over-message strip, table rows, spelling out numbers |
| `invisible_ink.py` | Interleaving, the room check, input checks, share links, the typewriter trick |
| `docx_writer.py` | Builds a .docx with `zipfile` and XML strings |
| `docx_reader.py` | Finds white or hidden text in any .docx |
| `letters.py` | The shop's demonstration letter, plot and typewriter card |
| `main.py` | The command line: `--demo`, `--hide`, `--room`, `--find`, `--typewriter` |

## What's new here

- **The Vigenère cipher**: shifting by a repeating key with `index` and `% 26`, keeping case
  with `isupper`, and a key that only advances over letters.
- **Office files are zips of XML**: `zipfile` with `io.BytesIO` to build one in memory,
  `xml.sax.saxutils.escape` to write XML safely, and `xml.etree.ElementTree` with namespaces
  (`{uri}tag`) to read one.
- **Bytes across the bridge**: `base64.b64encode` to carry a Word file from Python to the
  page as text, and back again for the detector.
- **Treating uploads with suspicion**: size limits before unzipping and refusing DOCTYPEs.
- **`next(iterator, None)`** to take the next secret line only when a blank line comes up.
- **Spelling out numbers** with `divmod` and recursion in `number_words`.
- **A custom exception that carries data**: `NotEnoughRoom.add` says how many lines are
  missing.

## Try this next

1. Hide the secret in the letter's *metadata* instead (`docProps/core.xml` has a
   "description" nobody reads), and teach the detector to look there too.
2. Use the cipher's weakness: with a long scrambled message, find repeated chunks and the
   distances between them, and guess the key's length (Babbage's and Kasiski's attack).
3. Make the ink *nearly* white (`FEFEFE`) and see which word processors and email previews
   still reveal it. The detector already counts that as ink.

Inspired by the invisible ink project in *Impractical Python Projects* by Lee Vaughan
(No Starch Press). The shop, letters, examples and code are new.
