# 02 · Code-Talk

Pig Latin with a secret handshake. Classic Pig Latin moves a word's opening consonants to
the end and adds *ay*, but you can't always undo it: does *away* come from *way* or from
*a*? Code-Talk puts a hyphen where the word was snipped, so every word carries the
instructions to put it back.

| Plain | Code-Talk | Rule |
|---|---|---|
| nix | ix-nay | the opening consonants move, then *-ay* |
| string | ing-stray | the whole cluster moves |
| apple | apple-ay | a vowel start moves nothing |
| queen | een-quay | *qu* stays together |
| yes / rhythm | es-yay / ythm-rhay | *y* is a consonant at the start, a vowel inside |
| Hello, NASA | Ello-hay, ASA-NAY | capitals follow the word's shape |
| hmm | hmm | no vowels, nothing to do |

Punctuation, numbers, apostrophes (*on't-day*) and real hyphens (*ell-way-own-knay*) all
survive the round trip.

## Play

```bash
uv run python projects/02_code_talk/main.py "Meet me at noon"
uv run python projects/02_code_talk/main.py --decode "Eet-may e-may at-ay oon-nay"
uv run python projects/02_code_talk/main.py      # type lines, Ctrl-D to stop
```

On the web it's a spy's case file: type on either sheet and the other keeps up, and a
ticker-tape "decoder strip" shows which letters moved in each word.

## Design first: the pseudocode

```
encode(text):
    for every word the regular expression finds:
        find where the leading consonants end (qu counts as one, y only at the start)
        if the word has no vowel: leave it alone
        rebuild it as  rest + "-" + leading + "ay"
        give the result the original word's capitals (lower, Title or UPPER)
decode(text):
    for every "word-<consonants>ay" the regular expression finds:
        put the consonants back in front and restore the capitals
```

## Files

| File | What's in it |
|---|---|
| `code_talk.py` | Pure functions: `encode_word`, `encode`, `decode`, `explain`, `words_explained` |
| `main.py` | The terminal translator (`argparse`, or line by line from standard input) |

## What's new here

- **String slicing** does the real work: `word[split:] + "-" + word[:split] + "ay"`.
- **Regular expressions** find the words (`[A-Za-z]+(?:'[A-Za-z]+)*`) and, for decoding, the
  coded pattern. A *lazy* `*?` and a consonants-only class make sure `ell-way-own-knay`
  decodes as two words, not one.
- **`re.sub` with a function**: instead of a replacement string, pass a function that gets
  each match and returns its replacement, so every word can be rebuilt with real logic.
- **Round-trip testing**: the strongest test of an encoder is `decode(encode(s)) == s`,
  checked here on hand-picked sentences and 500 random ones.
- **Case as data**: `case_of` names a word's shape ("upper", "title", "lower") so it can be
  put back on a different word.

## Try this next

1. Add a `--classic` flag for old-school Pig Latin (no hyphen) and write a test that shows
   why it can't always round-trip.
2. Make a "Ubbi Dubbi" mode, which inserts *ub* before every vowel sound. Does it reverse?
3. Teach Code-Talk about words with no vowels but a *y* (*myth*, *gym*). What should
   happen, and what do the tests need to say?
