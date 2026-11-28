import base64
import importlib.util
import json
from pathlib import Path

import pytest

from decency import family_friendly
from null_finder import describe, every_nth_word, hidden_letters, scan
from null_writer import (
    COVER,
    LONGEST_NAME,
    NOT_ON_A_POSTCARD,
    NoteProblem,
    check_note,
    hide_note,
    note_letters,
    pack_card,
    postcard_words,
    unpack_card,
    words_by_letter,
    write_card,
    write_postcard,
)
from word_gaps import word_set
from wordlist import clean_words, read_words

spec = importlib.util.spec_from_file_location(
    "postcard_writer_main", Path(__file__).parents[2] / "projects" / "07_postcard_rack" / "main.py"
)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)

WORDS = word_set(family_friendly(clean_words(read_words())))
NOTES = ["meet me by the pier", "bring more sun cream", "the donkey ate my chips", "quiz at six"]


# ---------------------------------------------------------------- writing


@pytest.mark.parametrize("note", NOTES)
@pytest.mark.parametrize("position", [2, 3, 4])
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_the_glass_reads_back_every_note_it_writes(note, position, seed):
    card = write_postcard(note, WORDS, position, seed)
    assert hidden_letters(card, "punctuation", position) == note_letters(note)
    best = scan(card, WORDS)[0]
    assert (best["rule"], best["offset"], best["reads"]) == ("punctuation", position, True)


def test_each_word_carries_one_letter_and_none_repeats():
    chosen = hide_note("seagulls seagulls", WORDS, 3, seed=7)
    assert "".join(word[2] for word in chosen) == "seagullsseagulls"
    assert len(set(chosen)) == len(chosen)


def test_the_same_seed_writes_the_same_card_and_another_seed_a_new_one():
    first = write_postcard("chips at noon", WORDS, 3, seed=1)
    assert write_postcard("chips at noon", WORDS, 3, seed=1) == first
    assert write_postcard("chips at noon", WORDS, 3, seed=2) != first


def test_the_cover_line_has_no_marks_to_start_the_count_early():
    card = write_card(["alpaca", "sherbet"])
    assert card == f"{COVER}: alpaca, sherbet."
    assert not any(char in "!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~" for char in COVER)


def test_only_letters_of_the_note_are_hidden():
    assert note_letters("Pier at 6, OK?") == "pieratok"


@pytest.mark.parametrize(
    ("note", "reason"),
    [
        ("hi there", None),  # 7 letters is fine
        ("hello", "at least"),
        ("a" * 41, "Keep it to"),
        ("you smell of wee and farts", "family-friendly"),
        ("go shoot the moon", "family-friendly"),
    ],
)
def test_notes_are_checked(note, reason):
    if reason is None:
        assert check_note(note) == note_letters(note)
    else:
        with pytest.raises(NoteProblem, match=reason):
            check_note(note)


def test_only_three_positions_are_allowed():
    with pytest.raises(NoteProblem, match="letter 2, 3, 4"):
        words_by_letter(WORDS, 5)


def test_nans_words_are_scrabble_sized_and_kind():
    pool = postcard_words(WORDS)
    assert len(pool) > 20_000
    assert all(5 <= len(word) <= 8 for word in pool)
    assert not [word for word in pool if any(stem in word for stem in NOT_ON_A_POSTCARD)]
    assert "dickens" not in pool  # a swear word hiding inside is enough to leave it out


def test_running_out_of_words_is_explained():
    tiny = {"apple", "maple"}
    with pytest.raises(NoteProblem, match="no words"):
        hide_note("pppppp", tiny, 3)


# ------------------------------------------------------------------ links


def test_a_postcard_survives_the_post():
    token = pack_card("Nan won: alpaca, sherbet.", "Kit", "Sam")
    assert set(token) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    assert unpack_card(token) == {"text": "Nan won: alpaca, sherbet.", "to": "Kit", "sender": "Sam"}


def test_names_are_tidied_or_filled_in():
    token = pack_card("Some card text.", "  Kit   " + "x" * 40, "")
    card = unpack_card(token)
    assert card["to"].startswith("Kit x") and len(card["to"]) == LONGEST_NAME
    assert card["sender"] == "a friend"


def _token(payload: object) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")


@pytest.mark.parametrize(
    "token",
    [
        "not*base64",
        _token(["a", "list"]),
        _token({"to": "Kit"}),
        _token({"t": 42}),
        _token({"t": ""}),
        _token({"t": "x" * 601}),
        _token({"t": "what a load of crap"}),
    ],
)
def test_smudged_or_unkind_links_are_turned_away(token):
    with pytest.raises(NoteProblem):
        unpack_card(token)


# ----------------------------------------------------- every Nth word's Nth letter


def test_nth_letter_of_every_nth_word():
    assert hidden_letters("one two three four five six", "nth", 2) == "woi"
    assert hidden_letters("aa bb cc dd ee ff", "nth", 2) == "bdf"


def test_words_with_marks_inside_count_once():
    text = "We didn't nap, honestly"
    # word 2 is "didn't" (2nd letter i), word 4 is "honestly" (2nd letter o)
    assert hidden_letters(text, "nth", 2) == "io"
    assert [text[i] for i in every_nth_word(text, 2)] == ["i", "o"]


def test_the_nth_rule_is_described_plainly():
    assert describe("nth", 2) == "2nd letter of every 2nd word"
    assert describe("nth", 3) == "3rd letter of every 3rd word"


def test_scan_shows_each_reading_once():
    readings = scan("Apple banana cherry damson elder fig grape", WORDS)
    letters = [reading["letters"] for reading in readings]
    assert len(letters) == len(set(letters))


# -------------------------------------------------------------------- CLI


def test_cli_writes_a_card_the_scan_can_read(capsys):
    cli.main(["--write", "meet me by the pier", "--position", "3", "--seed", "1"])
    card = capsys.readouterr().out.splitlines()[0]
    assert card.startswith(COVER)
    assert hidden_letters(card, "punctuation", 3) == "meetmebythepier"


def test_cli_turns_away_a_short_note(capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(["--write", "hi"])
    assert stop.value.code == 1
    assert "at least" in capsys.readouterr().err
