"""Code-Talk: a reversible Pig Latin for whole sentences.

Classic Pig Latin moves a word's opening consonants to the end and adds
"ay" (nix -> ixnay). It can't be undone reliably: "away" could come from
"way" or from "a". Code-Talk marks the join with a hyphen, so every word
carries the instructions to put it back together:

    nix -> ix-nay      string -> ing-stray      apple -> apple-ay

Everything else in the text (spaces, punctuation, digits, real hyphens) is
left exactly where it was.
"""

import re

VOWELS = "aeiou"

# A word is letters, optionally joined by apostrophes: don't, rock'n'roll.
WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")

# A Code-Talk word: the rest of the word, a hyphen, the moved consonants
# (``qu`` counts as one), then "ay". The consonants match lazily so "ay" is
# found at the very end, and the \b stops us eating into the next word.
CODED = re.compile(
    r"([A-Za-z]+(?:'[A-Za-z]+)*)-((?:qu|[b-df-hj-np-tv-z])*?)ay\b",
    re.IGNORECASE,
)


def leading_cluster(word: str) -> int:
    """Return how many opening letters move to the end of ``word``.

    The whole consonant cluster moves (``string`` -> ``str``), ``qu`` moves as
    one sound (``queen`` -> ``qu``), and ``y`` is a consonant at the start
    (``yes``) but a vowel after that (``rhythm`` -> ``rh``).
    """
    lower = word.lower()
    i = 0
    while i < len(lower):
        letter = lower[i]
        if lower.startswith("qu", i):
            i += 2
        elif letter in VOWELS or (letter == "y" and i > 0) or letter == "'":
            break
        else:
            i += 1
    return i


def case_of(word: str) -> str:
    """Name a word's capitalisation: ``"upper"``, ``"title"`` or ``"lower"``.

    Single capital letters such as "I" or "A" count as title case.
    """
    letters = [char for char in word if char.isalpha()]
    if len(letters) > 1 and all(char.isupper() for char in letters):
        return "upper"
    if letters and letters[0].isupper():
        return "title"
    return "lower"


def apply_case(word: str, case: str) -> str:
    """Give an all-lowercase ``word`` the capitalisation named by ``case``."""
    if case == "upper":
        return word.upper()
    if case == "title":
        return word[:1].upper() + word[1:]
    return word


def encode_word(word: str) -> str:
    """Turn one plain word into Code-Talk, keeping its capitalisation.

    Words with no vowels at all ("hmm", "shh", "TV") are left alone.
    """
    split = leading_cluster(word)
    if split == len(word):
        return word
    lower = word.lower()
    coded = f"{lower[split:]}-{lower[:split]}ay"
    return apply_case(coded, case_of(word))


def encode(text: str) -> str:
    """Translate a whole text into Code-Talk."""
    return WORD.sub(lambda match: encode_word(match.group()), text)


def decode(text: str) -> str:
    """Translate Code-Talk back into plain text. Undoes ``encode`` exactly."""

    def restore(match: re.Match[str]) -> str:
        rest, cluster = match.group(1), match.group(2)
        plain = (cluster + rest).lower()
        return apply_case(plain, case_of(match.group()))

    return CODED.sub(restore, text)


def explain(word: str) -> dict[str, str]:
    """Break one word's translation into its parts, for teaching.

    Returns the word, the letters that move, the letters that stay, the
    result and which rule applied.
    """
    split = leading_cluster(word)
    if split == len(word):
        rule = "No vowels, so it stays as it is."
    elif split == 0:
        rule = "Starts with a vowel: nothing moves, add -ay."
    elif "qu" in word.lower()[:split]:
        rule = "The consonants, qu kept together, move to the end, then -ay."
    else:
        rule = "The opening consonants move to the end, then -ay."
    return {
        "word": word,
        "moves": word[:split] if split < len(word) else "",
        "stays": word[split:] if split < len(word) else word,
        "result": encode_word(word),
        "rule": rule,
    }


def words_explained(text: str, limit: int = 12) -> list[dict[str, str]]:
    """Explain the first ``limit`` words of a text."""
    return [explain(match.group()) for match in WORD.finditer(text)][:limit]
