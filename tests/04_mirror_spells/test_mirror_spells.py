"""Tests for Mirror Spells: slicing, palindromes, loading and the CLI."""

import importlib.util
from pathlib import Path

import pytest

from decency import NOT_ON_THE_PIER, family_friendly_pairs
from mirror import find_palindromes, is_palindrome, letters_only, reflect, spellbook_stats
from palingrams import is_palindrome_recursive, two_word_spells, two_word_spells_slow
from speed_test import profile_report, race
from wordlist import read_words

# Every project has a main.py, so "import main" would grab whichever one
# another test file loaded first. Load this one by path, under its own name.
_SPEC = importlib.util.spec_from_file_location(
    "mirror_spells_main", Path(__file__).parents[2] / "projects" / "04_mirror_spells" / "main.py"
)
_CLI = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_CLI)
run_cli = _CLI.main


def test_reverse_slice():
    word = "stressed"
    assert word[::-1] == "desserts"
    assert word[:] == word


@pytest.mark.parametrize(
    "text", ["level", "Kayak", "noon", "Step on no pets!", "Was it a car or a cat I saw?"]
)
def test_palindromes(text):
    assert is_palindrome(text)


@pytest.mark.parametrize("text", ["levels", "kayaks", "palindrome", "", "123 321", "!!"])
def test_not_palindromes(text):
    assert not is_palindrome(text)


def test_letters_only():
    assert letters_only("Don't nod.") == "dontnod"


def test_one_letter_words_are_left_out():
    words = ["a", "i", "aha", "bob", "cat", "deed"]
    assert find_palindromes(words) == ["aha", "bob", "deed"]
    assert find_palindromes(words, min_length=1) == ["a", "i", "aha", "bob", "deed"]


def test_spellbook_stats():
    stats = spellbook_stats(["noon", "racecar", "civic", "radar", "pirate", "boat", "pop", "x"])
    assert stats["count"] == 5
    assert stats["percent"] == pytest.approx(62.5)
    assert stats["longest"] == ["racecar"]
    assert stats["by_length"] == {3: 1, 4: 1, 5: 2, 7: 1}


def test_spellbook_stats_on_nothing():
    assert spellbook_stats([])["percent"] == 0.0


def test_reflect_finds_the_first_broken_pair():
    good = reflect("Racecar")
    assert good["spell"] and good["broken"] is None and good["middle"] == "e"
    bad = reflect("racecars")
    assert not bad["spell"]
    assert bad["pairs"][0] == {"left": "r", "right": "s"}
    assert bad["broken"] == 0


def test_cli_exits_with_1_on_a_missing_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run_cli(["--words", str(tmp_path / "nope.txt")])
    assert exit_info.value.code == 1
    assert "Couldn't open the word list" in capsys.readouterr().err


def test_bundled_word_list_has_familiar_spells():
    spells = find_palindromes(read_words())
    for word in ["kayak", "level", "radar", "rotor", "deified"]:
        assert word in spells
    assert 40 < len(spells) < 120


# ---- two-word spells -------------------------------------------------------------------


WORDS = read_words()


@pytest.fixture(scope="module")
def all_pairs():
    return two_word_spells(WORDS)


def test_known_two_word_spells(all_pairs):
    for pair in [("nurses", "run"), ("stir", "grits"), ("stack", "cats"), ("stab", "bats")]:
        assert pair in all_pairs


def test_every_pair_reads_the_same_backwards(all_pairs):
    assert all(is_palindrome(first + second) for first, second in all_pairs)


def test_pairs_are_sorted_unique_and_use_real_words(all_pairs):
    vocab = set(WORDS)
    assert all_pairs == sorted(set(all_pairs))
    assert all(first in vocab and second in vocab for first, second in all_pairs)


def test_the_full_list_finds_2230_spells(all_pairs):
    assert len(all_pairs) == 2230


def test_small_hand_made_list():
    assert two_word_spells(["nurses", "run", "stir", "grits", "cat", "x"]) == [
        ("nurses", "run"),
        ("stir", "grits"),
    ]


def test_slow_and_fast_agree_on_a_sample():
    sample = WORDS[::40]  # every 40th word: about 1,500 words
    assert two_word_spells_slow(sample) == two_word_spells(sample)


def test_recursive_check_matches_the_slice():
    for word in WORDS[::7] + ["", "a", "abba", "abca"]:
        assert is_palindrome_recursive(word) == (word == word[::-1])
    assert is_palindrome_recursive(letters_only("Step on no pets"))


def test_decency_filter(all_pairs):
    kept = family_friendly_pairs(all_pairs)
    assert 0 < len(all_pairs) - len(kept) < 150
    assert all(NOT_ON_THE_PIER.isdisjoint(pair) for pair in kept)
    assert ("nurses", "run") in kept


def test_race_reports_both_timings():
    result = race(WORDS[:3000], sample_size=50)
    assert result["sample"] == 50
    assert result["slow_seconds"] > 0 and result["fast_seconds"] > 0
    assert result["slow_full_estimate"] == pytest.approx(result["slow_seconds"] * 60)


def test_profile_report_names_the_busy_function():
    report = profile_report(two_word_spells, ["nurses", "run"])
    assert "spells_from" in report
