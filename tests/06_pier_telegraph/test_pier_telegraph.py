import importlib.util
import itertools
import random
from pathlib import Path

import pytest

from codebook import CODEBOOK, MYSTERY, TICKETS, decode, encode, grid_options, pad
from route import (
    GridProblem,
    KeyProblem,
    build_matrix,
    check_grid,
    decrypt,
    decrypt_matrix,
    encrypt,
    factors,
    parse_key,
    route_order,
)

spec = importlib.util.spec_from_file_location(
    "pier_telegraph_main", Path(__file__).parents[2] / "projects" / "06_pier_telegraph" / "main.py"
)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def all_keys(cols):
    """Every route: any column order, each column up or down."""
    for order in itertools.permutations(range(1, cols + 1)):
        for signs in itertools.product((1, -1), repeat=cols):
            yield [n * s for n, s in zip(order, signs, strict=True)]


def test_route_order_walks_up_and_down():
    # 3 columns, 2 rows: cells 0 1 2 / 3 4 5
    assert route_order(3, 2, [-1, 2, -3]) == [3, 0, 1, 4, 5, 2]
    assert route_order(3, 2, [2, 1, 3]) == [1, 4, 0, 3, 2, 5]


def test_practice_tickets():
    t = TICKETS
    cipher = encrypt(t["words"], t["cols"], t["rows"], t["key"])
    assert cipher == [
        "11",
        "6",
        "1",
        "2",
        "7",
        "12",
        "13",
        "8",
        "3",
        "4",
        "9",
        "14",
        "15",
        "10",
        "5",
    ]
    assert decrypt(cipher, t["cols"], t["rows"], t["key"]) == t["words"]


def test_every_key_round_trips():
    words = [str(n) for n in range(12)]
    for key in all_keys(4):
        assert decrypt(encrypt(words, 4, 3, key), 4, 3, key) == words


def test_pop_matrix_matches_inverting_the_route():
    rng = random.Random(4)
    words = [f"w{n}" for n in range(15)]
    for _ in range(50):
        key = rng.choice(list(all_keys(3)))
        cipher = encrypt(words, 3, 5, key)
        inverse = [""] * 15
        for position, cell in enumerate(route_order(3, 5, key)):
            inverse[cell] = cipher[position]
        assert decrypt_matrix(build_matrix(cipher, 5, key)) == inverse == words


def test_factors():
    assert factors(15) == [3, 5]
    assert factors(20) == [2, 4, 5, 10]
    assert factors(13) == []


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("-1 0 3", "count from 1"),
        ("-1 2 4", "no column 4"),
        ("1 2", "needs 3 numbers"),
        ("1 -1 3", "Column 1 is in the key twice"),
        ("1 two 3", '"two" isn\'t a column number'),
    ],
)
def test_key_problems_say_what_to_fix(text, message):
    with pytest.raises(KeyProblem, match=message):
        parse_key(text, 3)


def test_keys_can_use_commas():
    assert parse_key("-1, 2, -3", 3) == [-1, 2, -3]


def test_grid_problem_suggests_sizes():
    with pytest.raises(GridProblem, match="fit: 3, 5"):
        check_grid(15, 4, 4)


def test_codebook_round_trip():
    coded = encode("Meet THE MANAGER at midnight!")
    assert coded == ["meet", "GULL", "at", "BUCKET"]
    assert decode([*coded, "PEBBLE", "KITE"]) == "meet the manager at midnight"
    assert all(code.isupper() for code in CODEBOOK)


def test_grid_options_and_padding():
    options = grid_options(11)
    assert {"cols": 4, "rows": 3, "filler": 1} in options
    assert all(o["filler"] < o["cols"] and o["rows"] >= 2 for o in options)
    padded = pad(["a"] * 11, 4, 3, seed=1)
    assert len(padded) == 12 and padded == pad(["a"] * 11, 4, 3, seed=1)
    with pytest.raises(ValueError):
        pad(["a"] * 13, 4, 3)


def test_mystery_telegram_is_solvable():
    m = MYSTERY
    words = pad(encode(m["text"]), m["cols"], m["rows"], m["seed"])
    cipher = encrypt(words, m["cols"], m["rows"], m["key"])
    assert decode(decrypt(cipher, m["cols"], m["rows"], m["key"])).startswith("tell the manager")


def test_cli_decodes_the_settings_block(capsys):
    cli.main([])
    assert "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15" in capsys.readouterr().out


def test_cli_sends_a_telegram_that_comes_back(capsys):
    cli.main(["--encrypt", "Meet the manager at midnight by the pier"])
    lines = capsys.readouterr().out.splitlines()
    assert lines[1] == "Grid: 4 columns × 2 rows, route -1 2 -3 4"  # 7 words + 1 filler
    telegram = lines[2].removeprefix("Telegram: ")
    cli.main(["--cipher", telegram, "--cols", "4", "--key", "-1 2 -3 4"])
    assert "meet the manager at midnight by the pier" in capsys.readouterr().out


def test_cli_explains_a_bad_key_and_exits_1(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--key", "-1 2 0 4 -5"])
    assert exit_info.value.code == 1
    assert "can't use 0" in capsys.readouterr().err
