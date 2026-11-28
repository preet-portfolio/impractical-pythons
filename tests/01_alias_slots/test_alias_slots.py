"""Tests for Alias Slots: the machine logic, the themes and the terminal loop."""

import io
import itertools
import math

import pytest

from main import play
from slots import (
    MIDDLE_CHANCE,
    PRIZES,
    bonus_chance,
    catalogue,
    combinations,
    decode,
    encode,
    from_base36,
    from_indices,
    key_letter,
    odds,
    prize_for,
    reel_combinations,
    spin,
    to_base36,
)
from themes import THEMES

THEME_KEYS = list(THEMES)


# --- themes -----------------------------------------------------------------


@pytest.mark.parametrize("key", THEME_KEYS)
def test_every_reel_is_clean(key):
    for reel in THEMES[key].reels:
        assert len(reel) >= 20
        assert len(set(reel)) == len(reel), "duplicate words on a reel"
        for word in reel:
            assert word and word == word.strip(), f"messy word {word!r}"


@pytest.mark.parametrize("key", THEME_KEYS)
def test_theme_key_matches_dict_key(key):
    assert THEMES[key].key == key


@pytest.mark.parametrize("key", THEME_KEYS)
def test_template_uses_every_reel(key):
    theme = THEMES[key]
    name = theme.render(("AAA", "BBB", "CCC"))
    assert all(part in name for part in ("AAA", "BBB", "CCC"))


# --- spinning ---------------------------------------------------------------


@pytest.mark.parametrize("key", THEME_KEYS)
def test_same_seed_same_spin(key):
    assert spin(key, seed=42) == spin(key, seed=42)


def test_different_seeds_usually_differ():
    names = {spin("sidekick", seed=s).name for s in range(50)}
    assert len(names) > 40


def test_locked_reel_never_moves():
    for seed in range(200):
        result = spin("space_pirate", seed=seed, locked={1: 5})
        assert result.indices[1] == 5
        assert result.words[1] == THEMES["space_pirate"].reels[1][5]


def test_locking_does_not_change_the_other_reels():
    free = spin("cozy_wizard", seed=9)
    held = spin("cozy_wizard", seed=9, locked={0: 3})
    assert held.indices[0] == 3
    assert held.indices[1:] == free.indices[1:]


def test_unknown_theme_is_a_friendly_error():
    with pytest.raises(ValueError, match="Choose one of"):
        spin("dinosaur_dentist")


def test_from_indices_rejects_positions_off_the_reel():
    with pytest.raises(ValueError, match="off the reel"):
        from_indices("sidekick", (0, 0, 999))
    with pytest.raises(ValueError, match="Expected 3"):
        from_indices("sidekick", (0, 0))


# --- prizes -----------------------------------------------------------------


def test_jackpot_is_alliteration():
    assert prize_for(("Barnaby", "Bumblesnoot", "Big Spoon")) == "jackpot"


def test_filler_words_are_skipped_for_alliteration():
    assert key_letter("of the Damp Crypt") == "d"
    assert prize_for(("Draven", "of the Damp Crypt", "Devourer of Socks")) == "jackpot"


def test_rhyme_beats_pair():
    assert prize_for(("Kettle", "Candlewick", "Slow Reader")) is None
    assert prize_for(("Sage", "Teacosy", "Porridge Prophet")) is None
    assert prize_for(("Hazel", "Gentlebrook", "Snooze Brook")) == "rhyme"
    assert prize_for(("Sage", "Snugglewood", "Barely Awake")) == "pair"


def test_same_word_is_not_a_rhyme():
    assert prize_for(("Moon", "Pie", "Moon")) == "pair"


@pytest.mark.parametrize("key", THEME_KEYS)
def test_odds_add_up(key):
    counts = odds(key)
    assert set(counts) == set(PRIZES)
    assert sum(counts.values()) <= reel_combinations(key)
    assert counts["jackpot"] > 0, "every machine should be able to pay out a jackpot"


@pytest.mark.parametrize("key", THEME_KEYS)
def test_combinations_count_reels_and_middles(key):
    theme = THEMES[key]
    assert reel_combinations(key) == math.prod(len(reel) for reel in theme.reels)
    assert combinations(key) == reel_combinations(key) * (len(theme.middles) + 1)


# --- share codes ------------------------------------------------------------


@pytest.mark.parametrize("key", THEME_KEYS)
def test_share_codes_round_trip(key):
    reels = THEMES[key].reels
    corners = itertools.product(*[(0, len(reel) - 1) for reel in reels])
    for indices in [*corners, *(spin(key, seed=s).indices for s in range(100))]:
        result = from_indices(key, indices)
        assert decode(result.code) == result


def test_codes_are_unique_across_themes():
    codes = {spin(key, seed=s).code: key for key in THEME_KEYS for s in range(200)}
    for code, key in codes.items():
        assert decode(code).theme == key


def test_codes_are_short():
    longest = max(
        len(encode(key, tuple(len(r) - 1 for r in THEMES[key].reels), len(THEMES[key].middles) - 1))
        for key in THEMES
    )
    assert longest <= 5


@pytest.mark.parametrize("bad", ["", "  ", "no!", "zzzzzzzzzz"])
def test_bad_codes_raise_value_error(bad):
    with pytest.raises(ValueError):
        decode(bad)


def test_base36_round_trip():
    for number in [0, 1, 35, 36, 1295, 1296, 10**9]:
        assert from_base36(to_base36(number)) == number
    assert to_base36(35) == "z"
    with pytest.raises(ValueError):
        to_base36(-1)


def test_codes_ignore_case_and_spaces():
    result = spin("bollywood_baddie", seed=3)
    assert decode(f"  {result.code.upper()} ") == result


# --- web data ---------------------------------------------------------------


def test_catalogue_is_plain_data_for_the_browser():
    import json

    data = catalogue()
    assert [entry["key"] for entry in data] == THEME_KEYS
    json.dumps(data)  # must be JSON-serialisable to cross into JavaScript


# --- terminal loop ----------------------------------------------------------


def run(keys: str, seed: int = 1) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    spins = play("sidekick", seed, io.StringIO(keys), out, err)
    return spins, out.getvalue(), err.getvalue()


def test_quit_right_away():
    spins, out, err = run("q\n")
    assert spins == 1
    assert "Bye!" in out
    assert err.strip(), "the alias goes to stderr so it shows in red"


def test_enter_spins_again_and_end_of_input_quits():
    spins, _, err = run("\n\n")
    assert spins == 3
    assert len([line for line in err.splitlines() if line.strip()]) == 3


def test_lock_keeps_the_word_in_the_terminal():
    _, out, err = run("l2\n\n\n\nq\n")
    surnames = [line for line in out.splitlines() if "[locked]" in line]
    assert len(surnames) == 3
    assert len({line.split("|")[1] for line in surnames}) == 1


def test_session_is_reproducible_from_seed():
    assert run("\n\nq\n", seed=5) == run("\n\nq\n", seed=5)


def test_unknown_command_shows_help_without_spinning():
    spins, out, _ = run("dance\nq\n")
    assert spins == 1
    assert "lock or unlock" in out


# --- style clinic -----------------------------------------------------------


def test_tidy_slots_makes_three_part_aliases():
    import random

    from tidy_slots import FIRST_WORDS, TAGS, make_alias

    alias = make_alias(random.Random(3))
    assert alias == make_alias(random.Random(3))
    assert alias.split()[0] in FIRST_WORDS
    assert any(alias.endswith(tag) for tag in TAGS)


# --- wildcard middle name ---------------------------------------------------


@pytest.mark.parametrize("key", THEME_KEYS)
def test_every_theme_has_clean_middles(key):
    middles = THEMES[key].middles
    assert len(middles) >= 10
    assert len(set(middles)) == len(middles)
    assert all(word and word == word.strip() for word in middles)


def test_middle_shows_about_one_spin_in_three():
    shown = sum(spin("sidekick", seed=s).middle is not None for s in range(3000))
    assert abs(shown / 3000 - MIDDLE_CHANCE) < 0.03


def test_middle_goes_after_the_first_name():
    result = next(r for s in range(100) if (r := spin("cozy_wizard", seed=s)).middle_word)
    first, middle = result.words[0], result.middle_word
    assert result.name.startswith(f"{first} {middle} ")


def test_same_seed_same_middle():
    assert [spin("space_pirate", seed=s) for s in range(50)] == [
        spin("space_pirate", seed=s) for s in range(50)
    ]


def test_holding_a_reel_keeps_the_middle_the_same():
    for seed in range(100):
        free = spin("fantasy_villain", seed=seed)
        held = spin("fantasy_villain", seed=seed, locked={2: 0})
        assert held.middle == free.middle


@pytest.mark.parametrize("key", THEME_KEYS)
def test_codes_round_trip_with_every_middle(key):
    theme = THEMES[key]
    for middle in [None, *range(len(theme.middles))]:
        result = from_indices(key, (1, 2, 3), middle)
        assert decode(result.code) == result


def test_middle_off_the_reel_is_rejected():
    with pytest.raises(ValueError, match="wildcard"):
        from_indices("sidekick", (0, 0, 0), 99)


def test_bonus_needs_matching_letters():
    theme = THEMES["sidekick"]
    first = theme.reels[0].index("Pudding")
    pockets = theme.middles.index("Pockets")
    noodle = theme.middles.index("Noodle")
    assert from_indices("sidekick", (first, 0, 0), pockets).bonus
    assert not from_indices("sidekick", (first, 0, 0), noodle).bonus
    assert not from_indices("sidekick", (first, 0, 0), None).bonus


@pytest.mark.parametrize("key", THEME_KEYS)
def test_bonus_chance_matches_a_brute_force_count(key):
    theme = THEMES[key]
    hits = sum(
        from_indices(key, (f, 0, 0), m).bonus
        for f in range(len(theme.reels[0]))
        for m in range(len(theme.middles))
    )
    expected = MIDDLE_CHANCE * hits / (len(theme.reels[0]) * len(theme.middles))
    assert bonus_chance(key) == pytest.approx(expected)
