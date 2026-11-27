import pytest

from sieve import SIEVE_LIMIT, LetterStats, strain, verdict, wordiness
from wordlist import clean_words, read_words


@pytest.fixture(scope="module")
def stats():
    return LetterStats(clean_words(read_words()))


def test_each_stage_only_removes(stats):
    report = strain("teacakes", stats)
    counts = [report["start"]] + [stage["left"] for stage in report["stages"]]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] == 10_080  # 8! / (2! * 2! * 2!)
    assert counts[-1] == len(report["survivors"]) > 0


def test_real_word_survives_and_mush_does_not(stats):
    report = strain("teacakes", stats)
    assert "teacakes" in report["survivors"]
    assert "kcstaeea" not in report["survivors"]


def test_survivors_are_ranked_and_grouped(stats):
    report = strain("crumpets", stats)
    survivors = report["survivors"]
    scores = [wordiness(s, stats) for s in survivors]
    assert scores == sorted(scores, reverse=True)
    assert sum(report["by_letter"].values()) == len(survivors)
    assert list(report["by_letter"]) == sorted(report["by_letter"])


def test_switching_a_sieve_off_lets_more_through(stats):
    full = strain("crumpets", stats)
    no_pairs = strain("crumpets", stats, active=("shape", "triples"))
    assert no_pairs["stages"][2] == {"sieve": "pairs", "on": False, "left": 2234}
    assert len(no_pairs["survivors"]) > len(full["survivors"])


def test_too_many_letters_is_refused(stats):
    with pytest.raises(ValueError):
        strain("a" * (SIEVE_LIMIT + 1), stats)


def test_verdicts_explain_themselves(stats):
    assert verdict("biscuit", stats)["passed"]
    caught = verdict("doughnut", stats)  # real, but "hnu" is very rare
    assert caught["caught_by"] == "triples" and '"hnu"' in caught["reason"]
    assert verdict("zzyzx", stats)["caught_by"] == "shape"
    start = verdict("ngarb", stats)
    assert start["caught_by"] == "pairs" and start["reason"] == 'No English word starts with "ng".'
    assert verdict("doughnut", stats, active=("shape",))["passed"]


def test_session_strains_the_leftovers():
    from phrase_session import run_session

    said = []
    replies = iter(["kidneys", "!", "rode"])
    words = clean_words(read_words())
    result = run_session("Donkey Rides", words, ask=lambda _p: next(replies), say=said.append)
    assert result == "kidneys rode"
    assert "24 orderings -> 16 after shape -> 16 after triples -> 16 after pairs" in said
