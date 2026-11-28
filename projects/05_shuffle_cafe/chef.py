"""Chef's choice: invent whole-phrase anagrams of a name automatically.

The phrase builder lets a person pick words one at a time. Here the
kitchen does all the picking itself: it tries word after word, backs up
when it gets stuck, and writes down every phrase that uses each letter
exactly once.

The search is a **depth-first search** with an explicit stack instead of
recursion. Each entry on the stack is a half-built phrase: the words so
far and the letters still left. Pop one, try every word that fits the
leftovers, and push each longer phrase back on. A phrase with no letters
left is finished.

Two rules keep it sane:

- Words are only ever taken in list order (never going back to an
  earlier word), so *caveman rice* is found but *rice caveman* isn't:
  the same words in another order are the same anagram.
- A ``budget`` of steps stops the search, so a long name can never make
  the page hang, and each first word gets only a share of it, so the
  results don't all begin the same way. The best phrases then come
  first, ranked by ``tastiness``.
"""

from collections import Counter

from anagrams import letters_only
from phrases import fits, letter_count, words_that_fit

MAX_WORDS = 4  # longer "phrases" are mostly little words strung together


def tastiness(phrase: str) -> int:
    """Score a phrase: each word earns its length squared.

    Squaring rewards long words: one 8-letter word (64) beats two
    4-letter words (16 + 16), so *caveman rice* outranks *a crave manic*.
    """
    return sum(len(word) ** 2 for word in phrase.split())


def _search(
    menu: list[str],
    first: int,
    left: Counter,
    cap: int,
) -> tuple[list[tuple[str, ...]], int]:
    """Depth-first search for phrases that start with ``menu[first]``.

    Returns the finished phrases (as tuples of words) and the number of
    steps used, never more than ``cap``.
    """
    finished: list[tuple[str, ...]] = []
    stack = [(first, left - letter_count(menu[first]), (menu[first],))]
    steps = 0
    while stack and steps < cap:
        start, rest, chosen = stack.pop()
        if not rest.total():
            finished.append(chosen)
            continue
        if len(chosen) == MAX_WORDS:
            continue
        # Push in reverse so the longest words are popped (tried) first.
        for index in range(len(menu) - 1, start - 1, -1):
            steps += 1
            word = menu[index]
            if fits(word, rest):
                after = rest - letter_count(word)
                stack.append((index, after, (*chosen, word)))
    return finished, steps


def chefs_choice(
    name: str,
    words: list[str],
    limit: int = 500,
    budget: int = 200_000,
) -> list[str]:
    """Return up to ``limit`` phrase anagrams of ``name``, tastiest first.

    Every possible first word gets its own small share of the ``budget``
    (taken longest first), so one long word can't hog the whole search
    and the results start with many different words.
    """
    letters = letter_count(name)
    menu = words_that_fit(letters, words)  # longest first
    own = sorted(name.lower().split())
    share = max(budget // 40, 1)
    found: set[str] = set()
    spent = 0
    for first in range(len(menu)):
        if spent >= budget:
            break
        cap = min(share, budget - spent)
        finished, steps = _search(menu, first, letters, cap)
        spent += steps + 1
        found.update(" ".join(p) for p in finished if sorted(p) != own)
    ranked = sorted(found, key=lambda phrase: (-tastiness(phrase), phrase))
    return ranked[:limit]


def is_phrase_anagram(phrase: str, name: str) -> bool:
    """Check a phrase uses exactly the letters of the name."""
    return sorted(letters_only(phrase)) == sorted(letters_only(name))
