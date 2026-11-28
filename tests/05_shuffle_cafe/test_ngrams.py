from collections import Counter

import pytest

from ngrams import (
    common_shapes,
    count_ngrams,
    count_starts,
    cv_map,
    ngrams,
    pair_table,
)


def test_ngrams_overlap_and_keep_repeats():
    assert ngrams("banana", 2) == ["ba", "an", "na", "an", "na"]
    assert ngrams("banana", 3) == ["ban", "ana", "nan", "ana"]
    assert ngrams("a", 2) == []


def test_count_ngrams_counts_every_occurrence():
    pairs = count_ngrams(["banana", "mississippi"], 2)
    assert pairs["an"] == 2 and pairs["na"] == 2
    assert pairs["ss"] == 2 and pairs["is"] == 2 and pairs["pp"] == 1


def test_count_starts():
    assert count_starts(["tea", "teacake", "toast", "a"]) == Counter({"te": 2, "to": 1})


def test_cv_map():
    assert cv_map("riddle") == "cvcccv"
    assert cv_map("yummy") == "cvccc"  # y counts as a consonant


def test_common_shapes_cover_most_words():
    words = ["cat", "dog", "pig", "hen", "owl", "eel"]
    assert common_shapes(words, 3, coverage=0.6) == {"cvc"}
    assert common_shapes(words, 3, coverage=1.0) == {"cvc", "vcc", "vvc"}
    assert common_shapes(words, 4) == set()


def test_pair_table_shares_add_to_100():
    counts = Counter({"te": 30, "et": 10, "ea": 60})
    table = pair_table("tea", counts)
    assert "tt" not in table  # one t can't pair with itself
    assert table["ea"] == pytest.approx(60)
    assert sum(table.values()) == pytest.approx(100)
    assert "ee" in pair_table("tee", counts)
