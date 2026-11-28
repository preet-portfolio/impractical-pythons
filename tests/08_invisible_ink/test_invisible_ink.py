"""Tests for the joke shop's vanishing ink: the cipher, the hiding, the Word file."""

import io
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from docx_reader import NotALetter, find_white_ink, read_paragraphs
from docx_writer import WHITE, make_docx
from invisible_ink import (
    InkProblem,
    NotEnoughRoom,
    as_plain_text,
    between_words,
    blank_lines,
    check_text,
    interleave,
    letter_lines,
    long_lines,
    pack_letter,
    read_between_words,
    room_check,
    secret_lines,
    unpack_letter,
)
from letters import COVER, KEY, SECRET, TYPEWRITER_COVER, TYPEWRITER_SECRET, demo_letter
from vigenere import (
    KeyProblem,
    clean_key,
    decrypt,
    encrypt,
    key_over,
    number_words,
    spell_out,
    tableau_row,
)

MAIN = Path(__file__).resolve().parents[2] / "projects" / "08_invisible_ink" / "main.py"

# ---------------------------------------------------------------- Vigenère


def test_a_worked_example_by_hand():
    """KITE over "crab": c+K=m, r+I=z, a+T=t, b+E=f."""
    assert encrypt("crab", "KITE") == "mztf"
    assert decrypt("mztf", "kite") == "crab"


def test_the_key_moves_on_over_letters_only():
    assert encrypt("ab cd!", "BC") == "bd df!"
    assert key_over("ab cd!", "BC") == "BC BC "


def test_capitals_and_punctuation_are_kept():
    text = "Meet Me, 12 o'clock!"
    scrambled = encrypt(text, "puffin")
    assert scrambled[4] == " " and scrambled[7] == "," and "12" in scrambled
    assert scrambled[0].isupper() and scrambled[1].islower()
    assert decrypt(scrambled, "PUFFIN") == text


@pytest.mark.parametrize("key", ["PUFFIN", "a", "Gull's Rest", "z"])
def test_every_secret_line_comes_back(key):
    for line in secret_lines(SECRET):
        assert decrypt(encrypt(line, key), key) == line


def test_a_key_needs_letters():
    assert clean_key("gull's rest 2") == "GULLSREST"
    with pytest.raises(KeyProblem):
        clean_key("1234 !")


def test_the_table_rows_shift_left():
    assert tableau_row("A").startswith("ABC")
    assert tableau_row("c") == "CDEFGHIJKLMNOPQRSTUVWXYZAB"


def test_numbers_and_symbols_are_spelled_out():
    assert number_words(42) == "forty two"
    assert number_words(105) == "one hundred and five"
    assert number_words(3000) == "three thousand"
    assert spell_out("Duck 42 wins 60% of races & 3 cups") == (
        "Duck forty two wins sixty percent of races and three cups"
    )
    assert not any(ch.isdigit() for ch in encrypt(spell_out("room 7"), "puffin"))


# -------------------------------------------------- hiding in the blank lines


def test_the_secret_fills_the_blank_lines_in_order():
    cover = ["Dear Kit,", "", "Lovely weather.", "", "", "Love, Sam"]
    letter = interleave(cover, ["first", "second"])
    assert [line["text"] for line in letter] == [
        "Dear Kit,",
        "first",
        "Lovely weather.",
        "second",
        "",
        "Love, Sam",
    ]
    assert [line["hidden"] for line in letter] == [False, True, False, True, False, False]


def test_the_room_check_says_how_many_lines_to_add():
    cover = ["Hi", "", "Bye"]
    assert room_check(cover, ["a"]) == {"fits": True, "blanks": 1, "needed": 1, "add": 0}
    assert room_check(cover, ["a", "b", "c"])["add"] == 2
    with pytest.raises(NotEnoughRoom, match="add 2 more blank lines") as caught:
        interleave(cover, ["a", "b", "c"])
    assert caught.value.add == 2


def test_the_secret_drops_its_own_blank_lines():
    assert secret_lines("one\n\n  two  \n\n") == ["one", "two"]
    assert letter_lines("\nDear Kit,   \n\nLove\n") == ["Dear Kit,", "", "Love"]
    # Blank lines under the signature are extra hiding places, as in the book.
    assert letter_lines("Love\n\n\n") == ["Love", "", ""]


def test_the_demo_letter_hides_the_whole_plot():
    letter = demo_letter()
    hidden = [line["text"] for line in letter if line["hidden"]]
    assert [decrypt(line, KEY) for line in hidden] == secret_lines(SECRET)
    assert blank_lines(letter_lines(COVER)) >= len(hidden)
    # What the reader sees is exactly the cover letter, blank lines and all.
    seen = ["" if line["hidden"] else line["text"] for line in letter]
    assert seen == letter_lines(COVER)
    assert not long_lines(hidden)


def test_plain_text_shows_the_ink():
    letter = demo_letter()
    assert letter[1]["text"] in as_plain_text(letter)


def test_long_lines_are_flagged():
    assert long_lines(["short", "x" * 71]) == [2]


def test_unkind_or_huge_text_is_refused():
    check_text("Meet me by the pier", "secret")
    with pytest.raises(InkProblem):
        check_text("you are a twat", "secret")
    with pytest.raises(InkProblem):
        check_text("a" * 3001, "letter")


def test_a_letter_link_round_trips_without_the_key():
    letter = demo_letter()
    token = pack_letter(letter, "The Gull's Rest")
    assert "PUFFIN" not in token
    back = unpack_letter(token)
    assert back == {"title": "The Gull's Rest", "letter": letter}


@pytest.mark.parametrize("token", ["!!!", "e30", "eyJ0IjoxfQ"])
def test_a_smudged_link_says_so(token):
    with pytest.raises(InkProblem):
        unpack_letter(token)


# ------------------------------------------------------------- the Word file


def test_the_word_file_is_a_real_zip_with_white_ink():
    data = make_docx(demo_letter(), "The Gull's Rest", "Sea Front", "14th August")
    with zipfile.ZipFile(io.BytesIO(data)) as docx:
        assert docx.testzip() is None
        assert {
            "[Content_Types].xml",
            "_rels/.rels",
            "word/document.xml",
            "word/styles.xml",
        } <= set(docx.namelist())
        body = docx.read("word/document.xml").decode()
    assert f'w:val="{WHITE}"' in body
    assert 'w:before="0" w:after="0"' in body  # no tell-tale gaps around the ink


def test_the_reader_finds_what_the_writer_hid():
    letter = demo_letter()
    data = make_docx(letter, "The Gull's Rest")
    ink = find_white_ink(data)
    assert ink == [line["text"] for line in letter if line["hidden"]]
    assert [decrypt(line, KEY) for line in ink] == secret_lines(SECRET)
    words = [p["text"] for p in read_paragraphs(data)]
    assert "Dear Mr Finch," in words and "The Gull's Rest" in words


def test_awkward_characters_survive_the_trip():
    letter = [{"text": 'Fish & chips <for two> "please"', "hidden": True}]
    assert find_white_ink(make_docx(letter, "A & B")) == ['Fish & chips <for two> "please"']


def test_a_letter_with_no_ink_has_nothing_to_find():
    assert find_white_ink(make_docx([{"text": "Hello", "hidden": False}], "Hi")) == []


def test_strange_files_are_turned_away():
    with pytest.raises(NotALetter):
        find_white_ink(b"not a zip at all")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as fake:
        fake.writestr(
            "word/document.xml", '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaa">]><x>&a;</x>'
        )
    with pytest.raises(NotALetter, match="odd"):
        find_white_ink(buffer.getvalue())


# ---------------------------------------------- the challenge: between words


def test_ink_between_words_round_trips():
    pieces = between_words(TYPEWRITER_COVER, TYPEWRITER_SECRET)
    assert read_between_words(pieces) == TYPEWRITER_SECRET
    # With the ink hidden, the line reads as the cover, every gap one character wide.
    seen = "".join(" " if p["hidden"] else p["text"] for p in pieces)
    assert seen == " ".join(TYPEWRITER_COVER.split())
    assert len("".join(p["text"] for p in pieces)) == len(seen)


def test_spaces_in_the_secret_are_dropped():
    assert read_between_words(between_words("a b c d", "x y")) == "xy"


def test_too_few_gaps_says_how_many_words_to_add():
    with pytest.raises(InkProblem, match="2 more words"):
        between_words("one two", "abc")


# ---------------------------------------------------------------- the CLI


def test_the_cli_hides_and_finds(tmp_path):
    cover = tmp_path / "cover.txt"
    secret = tmp_path / "secret.txt"
    out = tmp_path / "letter.docx"
    cover.write_text(COVER)
    secret.write_text("Meet at 7 by the pier.\n\nBring 2 buckets.")
    run = [sys.executable, str(MAIN)]
    subprocess.run(
        [*run, "--hide", str(cover), str(secret), "--key", "gull", "--out", str(out)], check=True
    )
    found = subprocess.run(
        [*run, "--find", str(out), "--key", "gull"], check=True, capture_output=True, text=True
    )
    assert found.stdout.splitlines() == ["Meet at seven by the pier.", "Bring two buckets."]


def test_the_cli_room_check_fails_politely(tmp_path):
    cover = tmp_path / "cover.txt"
    secret = tmp_path / "secret.txt"
    cover.write_text("Hi\n\nBye")
    secret.write_text("a\nb\nc")
    run = [sys.executable, str(MAIN)]
    said = subprocess.run(
        [*run, "--room", str(cover), str(secret)], check=True, capture_output=True, text=True
    )
    assert "add 2 blank lines" in said.stdout
    bad = subprocess.run(
        [*run, "--typewriter", "one two", "--secret", "xyz"], capture_output=True, text=True
    )
    assert bad.returncode == 1 and "more word" in bad.stderr
