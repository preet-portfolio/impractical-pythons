"""Tests for Letter Bars: counting, folding, ranking and comparing."""

import pytest

from letter_bars import (
    ALPHABET,
    ENGLISH,
    SAMPLES,
    accents,
    bar_chart,
    chart_data,
    compare,
    count_letters,
    fold,
    shares,
    top_letters,
)


def test_counts_ignore_case_digits_and_punctuation():
    assert count_letters("Banana! 42 bananas?") == {"a": 6, "b": 2, "n": 4, "s": 1}


def test_all_letters_fills_in_zeros_in_order():
    counts = count_letters("zebra", all_letters=True)
    assert list(counts) == list(ALPHABET)
    assert counts["z"] == 1
    assert counts["q"] == 0


@pytest.mark.parametrize(
    ("char", "letters"),
    [
        ("é", "e"),
        ("Ñ", "n"),
        ("ç", "c"),
        ("ü", "u"),
        ("ß", "ss"),
        ("Œ", "oe"),
        ("7", ""),
        ("λ", ""),
    ],
)
def test_fold(char, letters):
    assert fold(char) == letters


def test_accents_are_counted_and_reported():
    text = "Crème brûlée"
    assert count_letters(text)["e"] == 4
    assert accents(text) == {"è": 1, "é": 1, "û": 1}


def test_shares_add_up_to_a_hundred():
    assert sum(shares(count_letters(SAMPLES["French"])).values()) == pytest.approx(100)
    assert shares({"a": 0}) == {"a": 0.0}


def test_top_letters_breaks_ties_alphabetically():
    assert top_letters({"b": 2, "a": 2, "c": 5, "d": 0}) == "cab"
    assert top_letters(count_letters("aaabbc"), n=2) == "ab"


def test_bar_chart_is_made_of_the_letters():
    assert bar_chart("Tattoo") == {"a": "a", "o": "oo", "t": "ttt"}


def test_compare_covers_all_26_letters():
    rows = compare("abc", "xyz")
    assert [row["letter"] for row in rows] == list(ALPHABET)
    assert rows[0]["a"] == pytest.approx(100 / 3)
    assert rows[0]["b"] == 0


def test_english_table_is_complete_and_sums_to_about_100():
    assert set(ENGLISH) == set(ALPHABET)
    assert sum(ENGLISH.values()) == pytest.approx(100, abs=0.5)


def test_samples_have_their_language_fingerprints():
    assert top_letters(count_letters(SAMPLES["English"]), 1) == "e"
    assert count_letters(SAMPLES["Spanish"])["a"] > count_letters(SAMPLES["English"])["a"]
    assert accents(SAMPLES["French"])


def test_chart_data_shape():
    data = chart_data("hello", None)
    assert data["b"] is None
    assert data["a"]["total"] == 5
    assert data["english_top"] == "etaoin"
    assert chart_data("a", "b")["b"]["top"] == "b"
