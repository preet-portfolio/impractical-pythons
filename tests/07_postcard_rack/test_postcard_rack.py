import importlib.util
from datetime import date, timedelta
from pathlib import Path

import pytest

from decency import family_friendly
from null_finder import (
    after_punctuation,
    describe,
    hidden_letters,
    of_capital_words,
    of_each_word,
    picked_positions,
    read_reading,
    scan,
    strip_spaces,
)
from postcards import OPENING_DAY, POSTCARDS, postcard_number, todays_postcard, with_notes
from word_gaps import word_set
from wordlist import clean_words, read_words

spec = importlib.util.spec_from_file_location(
    "postcard_rack_main", Path(__file__).parents[2] / "projects" / "07_postcard_rack" / "main.py"
)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

WORDS = word_set(family_friendly(clean_words(read_words())))


# ------------------------------------------------------- the punctuation rule


def test_strip_spaces():
    assert strip_spaces(" a b\n c\t") == "abc"


def test_nothing_counts_before_the_first_mark():
    assert hidden_letters("Hello there, pal", "punctuation", 1) == "p"


def test_a_second_mark_restarts_the_count():
    # "ab" after the comma, then the full stop restarts: "cd" counts from 1 again
    assert hidden_letters("x, ab. cd", "punctuation", 2) == "bd"
    assert hidden_letters("x, a.bcd", "punctuation", 2) == "c"


def test_punctuation_is_never_part_of_the_message():
    assert hidden_letters("x, a!b?c", "punctuation", 2) == ""
    assert hidden_letters("x, 'tis", "punctuation", 1) == "t"


def test_spaces_never_count():
    assert hidden_letters("x,   a  b   c", "punctuation", 3) == "c"


def test_positions_point_into_the_original_text():
    text = "Hi, ab cd. ef"
    positions = after_punctuation(text, 2)
    assert [text[i] for i in positions] == ["b", "f"]


# ------------------------------------------------------------- the word rules


def test_letter_of_each_word():
    text = "Big umbrella, a kite"
    assert "".join(text[i] for i in of_each_word(text, 1)) == "Buak"
    assert "".join(text[i] for i in of_each_word(text, 2)) == "imi"  # "a" has no 2nd letter


def test_letter_of_capital_words():
    text = "Brilliant day, Rain held off"
    assert "".join(text[i] for i in of_capital_words(text, 1)) == "BR"


def test_settings_are_described_plainly():
    assert describe("punctuation", 3) == "3 letters after each punctuation mark"
    assert describe("punctuation", 1) == "1 letter after each punctuation mark"
    assert describe("words", 2) == "2nd letter of every word"
    assert describe("capitals", 1) == "1st letter of every capitalised word"


@pytest.mark.parametrize(("rule", "offset"), [("moon", 1), ("words", 0)])
def test_impossible_settings_are_explained(rule, offset):
    with pytest.raises(ValueError):
        picked_positions("Some text.", rule, offset)


# -------------------------------------------------------------- the postcards


@pytest.mark.parametrize("card", with_notes(), ids=lambda card: card["id"])
def test_every_postcard_hides_its_note(card):
    found = hidden_letters(card["text"], card["rule"], card["offset"])
    assert found == card["note"].replace(" ", "")


@pytest.mark.parametrize("card", with_notes(), ids=lambda card: card["id"])
def test_scanning_finds_each_postcards_setting_first(card):
    best = scan(card["text"], WORDS)[0]
    assert (best["rule"], best["offset"]) == (card["rule"], card["offset"])
    assert best["reads"]
    assert " ".join(best["words"]) == card["note"]


def test_the_plain_postcard_hides_nothing():
    plain = [card for card in POSTCARDS if not card["note"]]
    assert plain
    for card in plain:
        assert not any(reading["reads"] for reading in scan(card["text"], WORDS))


def test_little_words_by_luck_dont_count_as_a_message():
    reading = read_reading("atmena", WORDS)
    assert reading["coverage"] == 1
    assert not reading["reads"]


def test_postcard_ids_are_unique():
    assert len({card["id"] for card in POSTCARDS}) == len(POSTCARDS)


def test_the_daily_postcard_comes_round_in_turn():
    cards = with_notes()
    days = [OPENING_DAY + timedelta(days=n) for n in range(len(cards))]
    assert [todays_postcard(day)["id"] for day in days] == [card["id"] for card in cards]
    assert todays_postcard(OPENING_DAY + timedelta(days=len(cards))) == cards[0]
    assert postcard_number(date(2026, 11, 28)) == 28
    assert postcard_number(date(2020, 1, 1)) == 1


# ---------------------------------------------------------------- the command


def test_cli_lookahead_finds_the_offset(capsys, tmp_path):
    card = next(card for card in POSTCARDS if card["id"] == "lighthouse")
    letter = tmp_path / "letter.txt"
    letter.write_text(card["text"] + "\n", encoding="utf-8")
    cli.main(["--file", str(letter), "--lookahead", "4"])
    out = capsys.readouterr().out
    assert "3 letters after each punctuation mark: seagullstolemyhat" in out
    assert out.count("\n") == 4


def test_cli_scan_splits_the_note(capsys):
    card = next(card for card in POSTCARDS if card["id"] == "donkeys")
    cli.main(["--text", card["text"], "--scan"])
    assert "1st letter of every capitalised word: bring a spade" in capsys.readouterr().out


def test_cli_scan_says_when_its_just_a_postcard(capsys):
    plain = next(card for card in POSTCARDS if not card["note"])
    cli.main(["--text", plain["text"], "--scan"])
    assert "just be a postcard" in capsys.readouterr().out


def test_cli_today(capsys):
    cli.main(["--today"])
    assert capsys.readouterr().out.startswith("Postcard No.")


@pytest.mark.parametrize(
    "argv", [["--file", "no-such-letter.txt"], ["--lookahead", "0"], ["--rule", "moon"]]
)
def test_cli_explains_mistakes_and_exits_1(argv, capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(argv)
    assert stop.value.code == 1
    assert capsys.readouterr().err
