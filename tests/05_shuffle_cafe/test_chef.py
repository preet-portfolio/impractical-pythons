import pytest

from chef import chefs_choice, is_phrase_anagram, tastiness
from wordlist import clean_words, read_words


@pytest.fixture(scope="module")
def words():
    return clean_words(read_words())


def test_tastiness_rewards_long_words():
    assert tastiness("caveman rice") == 49 + 16
    assert tastiness("caveman rice") > tastiness("a crave manic")


def test_every_phrase_is_an_exact_anagram(words):
    phrases = chefs_choice("Ice Cream Van", words)
    assert "caveman rice" in phrases
    assert all(is_phrase_anagram(p, "Ice Cream Van") for p in phrases)
    assert "ice cream van" not in phrases  # the name itself isn't news


def test_no_reordered_duplicates(words):
    phrases = chefs_choice("Donkey Rides", words)
    as_sets = [tuple(sorted(p.split())) for p in phrases]
    assert len(as_sets) == len(set(as_sets))


def test_ranked_tastiest_first_and_limited(words):
    phrases = chefs_choice("Penny Arcade", words, limit=50)
    assert len(phrases) == 50
    scores = [tastiness(p) for p in phrases]
    assert scores == sorted(scores, reverse=True)


def test_budget_stops_the_search(words):
    small = chefs_choice("Paddle Steamer", words, budget=500)
    assert len(small) < len(chefs_choice("Paddle Steamer", words))


def test_no_letters_no_phrases(words):
    assert chefs_choice("", words) == []
    assert chefs_choice("zzz", words) == []
