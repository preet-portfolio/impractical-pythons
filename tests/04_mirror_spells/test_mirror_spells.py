"""Tests for Mirror Spells: slicing, palindromes, loading and the CLI."""

import importlib.util
from pathlib import Path

import pytest

from mirror import find_palindromes, is_palindrome, letters_only, reflect, spellbook_stats
from wordlist import read_words, words_from_text

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


def test_words_from_text_cleans_lines():
    assert words_from_text("Apple\r\n\n  Kayak \nnoon") == ["apple", "kayak", "noon"]


def test_read_words(tmp_path):
    path = tmp_path / "words.txt"
    path.write_text("Level\nboat\n", encoding="utf-8")
    assert read_words(path) == ["level", "boat"]


def test_missing_file_raises(tmp_path):
    with pytest.raises(OSError):
        read_words(tmp_path / "nope.txt")


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
