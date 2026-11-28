"""Tests for Code-Talk: the rules, the edge cases and the round trip."""

import random
import string

import pytest

from code_talk import case_of, decode, encode, encode_word, explain, words_explained


@pytest.mark.parametrize(
    ("plain", "coded"),
    [
        ("nix", "ix-nay"),
        ("string", "ing-stray"),
        ("apple", "apple-ay"),
        ("queen", "een-quay"),
        ("squid", "id-squay"),
        ("yes", "es-yay"),
        ("rhythm", "ythm-rhay"),
        ("don't", "on't-day"),
        ("Hello", "Ello-hay"),
        ("NASA", "ASA-NAY"),
        ("I", "I-ay"),
        ("hmm", "hmm"),
        ("TV", "TV"),
    ],
)
def test_word_rules(plain, coded):
    assert encode_word(plain) == coded


def test_sentence_keeps_spacing_punctuation_and_numbers():
    assert encode("Meet me at 7, okay?") == "Eet-may e-may at-ay 7, okay-ay?"


def test_real_hyphens_survive():
    assert encode("a well-known spy") == "a-ay ell-way-own-knay y-spay"
    assert decode("a-ay ell-way-own-knay y-spay") == "a well-known spy"


def test_decode_leaves_plain_text_alone():
    assert decode("Nothing coded here.") == "Nothing coded here."


@pytest.mark.parametrize(
    "text",
    [
        "Meet me by the old fountain at noon.",
        "The QUICK brown fox can't find its well-worn hat!",
        "Yes, I squeezed thirty-three quiet yellow lemons.",
        "Rhythm and blues, rock'n'roll, and a lot of NOISE.",
        "Operation Snack Attack begins at 0600 sharp.",
        "",
        "   spaced   out   ",
    ],
)
def test_round_trip(text):
    assert decode(encode(text)) == text


def test_round_trip_on_random_words():
    rng = random.Random(1)
    for _ in range(500):
        words = []
        for _ in range(rng.randint(1, 6)):
            word = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(1, 8)))
            words.append(rng.choice([word, word.title(), word.upper()]))
        text = " ".join(words) + rng.choice([".", "!", "?", ""])
        assert decode(encode(text)) == text, text


def test_case_names():
    assert case_of("NASA") == "upper"
    assert case_of("Hello") == "title"
    assert case_of("I") == "title"
    assert case_of("quiet") == "lower"


def test_explain_shows_what_moves():
    assert explain("string") == {
        "word": "string",
        "moves": "str",
        "stays": "ing",
        "result": "ing-stray",
        "rule": "The opening consonants move to the end, then -ay.",
    }
    assert explain("apple")["moves"] == ""
    assert explain("hmm")["stays"] == "hmm"


def test_words_explained_limits_the_list():
    assert len(words_explained("one two three four", limit=2)) == 2
