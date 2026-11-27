import importlib.util
from pathlib import Path

import pytest

from anagrams import (
    anagram_families,
    anagrams_from_families,
    biggest_families,
    find_anagrams,
    is_anagram,
    letter_key,
    letters_only,
    menu_stats,
)
from wordlist import clean_words, read_words

WORDS = clean_words(read_words())

# main.py shares its name with other projects' CLIs, so load it by path.
_spec = importlib.util.spec_from_file_location(
    "shuffle_cafe_main", Path(__file__).parents[2] / "projects" / "05_shuffle_cafe" / "main.py"
)
cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cli)


@pytest.fixture(scope="module")
def families():
    return anagram_families(WORDS)


def test_letters_only_and_key():
    assert letters_only("Mary-Jo O'Neil") == "maryjooneil"
    assert letter_key("Listen") == letter_key("SILENT") == "eilnst"


def test_is_anagram():
    assert is_anagram("listen", "silent")
    assert is_anagram("Dormitory", "dirty room")
    assert not is_anagram("listen", "listen")
    assert not is_anagram("listen", "lister")


def test_find_anagrams_known_words():
    assert find_anagrams("listen", WORDS) == ["enlist", "inlets", "silent", "tinsel"]
    assert find_anagrams("Daniel", WORDS) == ["denial", "nailed"]
    assert find_anagrams("petal", WORDS) == ["leapt", "plate", "pleat"]


def test_a_word_is_not_its_own_anagram():
    assert "ocean" not in find_anagrams("ocean", WORDS)
    assert find_anagrams("ocean", WORDS) == ["canoe"]


def test_no_anagrams():
    assert find_anagrams("amelia", WORDS) == []
    assert anagrams_from_families("amelia", anagram_families(WORDS[:500])) == []


def test_loop_and_index_agree(families):
    for word in WORDS[::3000]:
        assert anagrams_from_families(word, families) == find_anagrams(word, WORDS)


def test_every_family_shares_one_key(families):
    for key, family in families.items():
        assert len(family) > 1
        assert all(letter_key(word) == key for word in family)


def test_biggest_families_and_stats(families):
    top = biggest_families(families, 3)
    assert top[0] == ["pares", "parse", "pears", "rapes", "reaps", "spare", "spear"]
    assert [len(family) for family in top] == sorted((len(f) for f in top), reverse=True)
    stats = menu_stats(WORDS, families)
    assert stats["families"] == 3285
    assert stats["in_families"] == 7284
    assert stats["longest"] == ["dessertspoonfuls", "dessertspoonsful"]


def test_menu_stats_on_nothing():
    assert menu_stats([], {}) == {
        "words": 0,
        "families": 0,
        "in_families": 0,
        "biggest": [],
        "longest": [],
    }


def test_cli_with_a_word(capsys):
    cli.main(["listen"])
    assert capsys.readouterr().out.split() == [
        "Anagrams",
        "of",
        "listen:",
        "enlist",
        "inlets",
        "silent",
        "tinsel",
    ]


def test_cli_asks_when_no_word_is_given(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda prompt: "Daniel")
    cli.main([])
    out = capsys.readouterr().out
    assert "denial" in out and "nailed" in out


def test_cli_without_anagrams_and_families(capsys):
    cli.main(["Amelia"])
    assert "Try a nickname" in capsys.readouterr().out
    cli.main(["--families", "2"])
    assert capsys.readouterr().out.startswith("7: pares, parse")


def test_cli_exits_with_1_on_a_missing_file(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["listen", "--words", str(tmp_path / "nope.txt")])
    assert exit_info.value.code == 1
    assert "Couldn't open" in capsys.readouterr().err
