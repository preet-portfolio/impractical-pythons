import itertools
import math

from leftovers import (
    LIST_LIMIT,
    arrangement_count,
    arrangements,
    sample_arrangements,
    shuffle_report,
)
from phrase_session import run_session
from wordlist import clean_words, read_words


def test_count_divides_out_repeated_letters():
    assert arrangement_count("mer") == 6
    assert arrangement_count("teeth") == 30  # 5! / (2! * 2!)
    assert arrangement_count("aaaa") == 1
    assert arrangement_count("") == 1
    assert arrangement_count("abcdefghi") == math.factorial(9)


def test_count_matches_brute_force():
    for letters in ["pier", "steam", "paddle", "seesaw"]:
        brute = {"".join(p) for p in itertools.permutations(letters)}
        assert arrangement_count(letters) == len(brute)


def test_arrangements_are_sorted_and_different():
    assert arrangements("emr") == ["emr", "erm", "mer", "mre", "rem", "rme"]
    assert arrangements("eel") == ["eel", "ele", "lee"]


def test_sample_is_different_letters_reshuffled():
    sample = sample_arrangements("paddlesteamer", 24, seed=7)
    assert len(sample) == len(set(sample)) == 24
    assert all(sorted(guess) == sorted("paddlesteamer") for guess in sample)
    assert sample == sample_arrangements("paddlesteamer", 24, seed=7)
    assert sorted(sample_arrangements("aab", 24, seed=1)) == ["aab", "aba", "baa"]


def test_report_lists_everything_only_when_small():
    small = shuffle_report("meroa")
    assert small["complete"] and small["count"] == 120 == len(small["arrangements"])
    big = shuffle_report("lighthouse", sample=10, seed=3)
    assert not big["complete"] and big["count"] > LIST_LIMIT
    assert len(big["arrangements"]) == 10


def test_session_shuffles_and_accepts_a_made_up_word():
    said = []
    replies = iter(["paddles", "ate", "?", "mer"])
    words = clean_words(read_words())
    result = run_session("Paddle Steamer", words, ask=lambda _p: next(replies), say=said.append)
    assert result == "paddles ate mer"
    assert "emr can be arranged 6 ways." in said
