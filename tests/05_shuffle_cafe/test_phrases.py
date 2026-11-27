from collections import Counter

from phrase_session import run_session
from phrases import fits, letter_count, phrase_status, remaining, spell_out, words_that_fit
from wordlist import clean_words, read_words

WORDS = clean_words(read_words())


def test_letter_count_ignores_case_and_spaces():
    assert letter_count("Rock Pool") == Counter({"o": 3, "r": 1, "c": 1, "k": 1, "p": 1, "l": 1})


def test_fits_needs_enough_of_each_letter():
    letters = letter_count("rock pool")
    assert fits("pool", letters)
    assert fits("crook", letters)
    assert not fits("roof", letters)  # no f
    assert not fits("poorly", letters)  # no y
    assert not fits("cook", letter_count("cork"))  # one o, cook needs two


def test_remaining_after_choices():
    assert spell_out(remaining("Rock Pool", ["cork"])) == "loop"
    assert remaining("Rock Pool", ["cork", "loop"]).total() == 0
    assert remaining("Rock Pool", ["cork", "cork"]) is None
    assert remaining("Rock Pool", []) == letter_count("rock pool")


def test_words_that_fit_are_real_and_longest_first():
    options = words_that_fit(letter_count("Ice Cream Van"), WORDS)
    assert options[0] == "variance"
    assert {"caveman", "vaccine", "rice"} <= set(options)
    assert [len(w) for w in options] == sorted((len(w) for w in options), reverse=True)
    assert all(fits(word, letter_count("Ice Cream Van")) for word in options)


def test_every_fitting_word_is_found():
    letters = letter_count("Beach Hut")
    expected = sorted(w for w in WORDS if not Counter(w) - letters)
    assert sorted(words_that_fit(letters, WORDS)) == expected


def test_phrase_status_through_to_done():
    start = phrase_status("Donkey Rides", [], WORDS)
    assert start["left"] == "ddeeiknorsy" and not start["done"]
    middle = phrase_status("Donkey Rides", ["kidneys"], WORDS)
    assert middle["left"] == "deor" and middle["phrase"] == "kidneys"
    assert {"rode", "redo", "doer"} <= set(middle["options"])
    end = phrase_status("Donkey Rides", ["kidneys", "rode"], WORDS)
    assert end["done"] and end["phrase"] == "kidneys rode" and end["options"] == []
    assert phrase_status("Donkey Rides", ["zebra"], WORDS) is None


def session(name, replies):
    """Run a whole session with scripted replies; return (result, output)."""
    said = []
    answers = iter(replies)
    result = run_session(name, WORDS, ask=lambda _prompt: next(answers), say=said.append)
    return result, "\n".join(said)


def test_session_builds_a_phrase():
    result, out = session("Ice Cream Van", ["caveman", "rice"])
    assert result == "caveman rice"
    assert "Order up!" in out


def test_session_rejects_undoes_restarts_and_quits():
    result, out = session("Ice Cream Van", ["zebra", "vaccine", "-", "ceramic", "", "#"])
    assert result is None
    assert "'zebra' needs letters" in out
    assert "Phrase so far: vaccine" in out
    assert "Phrase so far: ceramic" in out
    assert "Starting over." in out
