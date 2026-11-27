"""Words kept off the pier: the web page's family-friendly filter.

The dictionary is honest, so the spell hunt finds some rude words and a
few slurs too. The Python, the command line and the tests still find
*everything*; only the web page leaves these out, and it says so. The
list is short and explicit on purpose, so anyone can see what's hidden.
"""

# One string split on spaces keeps the list short enough to read at once.
NOT_ON_THE_PIER = frozenset(
    """
    anus bonk bonks boob boobs booby crap craps cum dago enema enemas fag
    farts fecal gyps lewd nude nudes pee peed pees penis piss pisses poo
    poop poops rape raped sex sexed sexes sexing smut smuts spank spik
    spiks tit tits turd turds wog wop wops
    """.split()  # noqa: SIM905
)


def family_friendly(words: list[str]) -> list[str]:
    """Drop single words that are on the hidden list."""
    return [word for word in words if word not in NOT_ON_THE_PIER]


def family_friendly_pairs(
    pairs: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Drop two-word spells where either word is on the hidden list."""
    return [pair for pair in pairs if NOT_ON_THE_PIER.isdisjoint(pair)]
