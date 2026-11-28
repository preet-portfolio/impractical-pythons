"""Tests for the code shared between stalls: the word list and the filter."""

import pytest

from decency import (
    NOT_ON_THE_PIER,
    family_friendly,
    family_friendly_pairs,
    nothing_rude_inside,
)
from wordlist import DEFAULT_WORDS, clean_words, read_words, words_from_text


def test_words_from_text_cleans_lines():
    assert words_from_text("Apple\r\n\n  Kayak \nnoon") == ["apple", "kayak", "noon"]


def test_read_words(tmp_path):
    path = tmp_path / "words.txt"
    path.write_text("Level\nboat\n", encoding="utf-8")
    assert read_words(path) == ["level", "boat"]


def test_missing_file_raises(tmp_path):
    with pytest.raises(OSError):
        read_words(tmp_path / "nope.txt")


def test_clean_words_drops_letter_headings():
    words = ["a", "aardvark", "b", "c", "i", "cat", "cat", "dog"]
    assert clean_words(words) == ["a", "aardvark", "i", "cat", "dog"]
    assert clean_words(words, keep=()) == ["aardvark", "cat", "dog"]


def test_bundled_word_list_loads():
    words = read_words(DEFAULT_WORDS)
    assert len(words) == 60_388
    assert {"kayak", "listen", "silent"} <= set(words)


def test_family_friendly_drops_listed_words():
    assert family_friendly(["kayak", "tit", "level"]) == ["kayak", "level"]
    assert family_friendly_pairs([("go", "dog"), ("pee", "p")]) == [("go", "dog")]
    assert all(word == word.lower() for word in NOT_ON_THE_PIER)


def test_swear_words_and_slurs_stay_off_the_pier():
    # The rude-word lists live in decency.py; spot-check a few from each group here.
    assert family_friendly(["shit", "fuck", "wanker", "incest", "raping"]) == []


@pytest.mark.parametrize(
    "word", ["ginger", "this", "insect", "constitution", "cocktail", "scrape", "titanic"]
)
def test_innocent_neighbours_of_rude_words_stay(word):
    assert family_friendly([word]) == [word]


@pytest.mark.parametrize("word", ["gay", "lesbian", "queer"])
def test_words_about_who_people_are_are_not_rude(word):
    assert family_friendly([word]) == [word]


def test_nothing_rude_inside_checks_substrings():
    assert nothing_rude_inside(["latorment", "brashite", "pennarse"]) == ["latorment"]
    assert nothing_rude_inside(["titanic"]) == ["titanic"]  # short words aren't checked inside
