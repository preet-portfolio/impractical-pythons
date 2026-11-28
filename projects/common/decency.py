"""Words kept off the pier: the web page's family-friendly filter.

The dictionary is honest, so spell and anagram hunts find rude words,
swear words and slurs too. The Python, the command line and the tests
still find *everything*; only the web pages leave these out, and they
say so. The list is explicit on purpose, so anyone can see what's
hidden. Words about who people are ("gay", "lesbian", "queer") are not
rude and are not on it.
"""

# Strings split on spaces keep each group short enough to read at once.
# Exact words, not stems, so "constitution", "cocktail" and "scrape" stay.
RUDE = """
    anus arse arses bonk bonks boob boobs booby crap craps cum enema
    enemas fart farts fecal lewd nude nudes pee peed pees penis piss
    pisses poo poop poops sex sexed sexes sexing slut sluts smut smuts
    spank tit tits turd turds twat twats
    """
SWEARS = """
    arsed arsehole arseholes bastard bastards bitch bitched bitches
    bitchier bitchiest bitchiness bitching bitchy bollocking bollockings
    bollocks bugger buggered buggering buggers buggery bullshit bullshits
    bullshitted bullshitter bullshitters bullshitting chickenshit
    chickenshits crapped crapper crappers crappier crappiest crapping
    crappy cunt cunts dickhead dickheads fuck fucked fucker fuckers
    fuckhead fuckheads fucking fucks horseshit motherfucker motherfuckers
    pissed pisser pissers pissing shagged shagging shit shite shites
    shitfaced shithead shitheads shitload shits shitted shittier
    shittiest shitting shitty sluttish slutty sonofabitch sonsofbitches
    wank wanked wanker wankers wanking wanks whore whorehouse
    whorehouses whores
    """
SLURS = """
    chink chinks coon coons dago darkie darkies faggot faggots fag
    golliwog golliwogs gyp gypped gypping gyps kike kikes midget midgets
    mongol mongols negro negroid nigger niggers retard retarded retards
    spastic spastics spic spics spik spiks wog wogs wop wops yid yids
    """
GRIM = """
    boobed boobies boobing erotic erotica erotically eroticism incest
    incestuous incestuously molest molestation molested molester
    molesters molesting molests orgasm orgasmic orgasms paedophile
    paedophiles paedophilia pedophile pedophiles pedophilia porn porno
    pornographer pornographers pornographic pornography pussy rape raped
    rapes raping rapist rapists titties titty
    """
NOT_ON_THE_PIER = frozenset((RUDE + SWEARS + SLURS + GRIM).split())


# Made-up words can hide a rude word inside them, including some no
# dictionary lists. Checked as substrings, so only longer, unambiguous
# words go here (a short one like "tit" would hide "titanic").
NOT_INSIDE = frozenset(
    {word for word in NOT_ON_THE_PIER if len(word) >= 4}
    | {"cock", "cunt", "dick", "fuck", "shag", "shit", "wank"}
)


def nothing_rude_inside(made_up: list[str]) -> list[str]:
    """Drop made-up strings that contain a rude word anywhere inside."""

    def clean(text: str) -> bool:
        return not any(rude in text for rude in NOT_INSIDE)

    return [text for text in made_up if clean(text)]


def family_friendly(words: list[str]) -> list[str]:
    """Drop single words that are on the hidden list."""
    return [word for word in words if word not in NOT_ON_THE_PIER]


def family_friendly_pairs(
    pairs: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Drop two-word spells where either word is on the hidden list."""
    return [pair for pair in pairs if NOT_ON_THE_PIER.isdisjoint(pair)]
