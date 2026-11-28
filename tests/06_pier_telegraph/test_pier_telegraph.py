import importlib.util
import itertools
import random
from datetime import date
from pathlib import Path

import pytest

from challenge import ChallengeProblem, fingerprint, is_solved, make_challenge, read_challenge
from codebook import CODEBOOK, TICKETS, decode, encode, grid_options, pad, snuggest
from dispatches import DISPATCHES, dispatch, plain_route_hits, telegram_number, todays_dispatch
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


SAMPLE_MESSAGE = "Meet the manager by the lighthouse at midnight"


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


def test_snuggest_prefers_least_filler_then_square():
    assert snuggest(grid_options(11)) == {"cols": 4, "rows": 3, "filler": 1}


def test_telegram_numbers_count_from_opening_day():
    assert telegram_number(date(2026, 11, 1)) == 1
    assert telegram_number(date(2026, 11, 28)) == 28
    assert todays_dispatch(date(2026, 11, 28)) == dispatch(28)


@pytest.mark.parametrize("number", range(1, len(DISPATCHES) + 1))
def test_every_daily_telegram_is_a_fair_puzzle(number):
    today = dispatch(number)
    words, cols, rows, key = today["words"], today["cols"], today["rows"], today["key"]
    assert 3 <= cols <= 5 and rows >= 3 and len(words) == cols * rows
    # The lazy guess (straight down every column) gets almost nothing right.
    assert plain_route_hits(words, cols, rows, key) <= max(2, len(words) // 5)
    # Decoding gives back the message, code words swapped and filler gone.
    plain = " ".join(encode(DISPATCHES[number - 1])).lower()
    message = decode(decrypt(encrypt(words, cols, rows, key), cols, rows, key))
    assert message == decode(plain.split())


def test_daily_telegrams_are_the_same_everywhere():
    assert dispatch(40) == dispatch(40)  # seeded, so no randomness between visitors
    assert dispatch(40)["words"][:3] == dispatch(40 - len(DISPATCHES))["words"][:3]


def test_challenge_round_trip():
    words = pad(encode(SAMPLE_MESSAGE), 4, 3, seed=1)
    token = make_challenge(words, 4, 3, [-1, 2, -3, 4])
    assert set(token) <= set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")
    challenge = read_challenge(token)
    assert challenge["cipher"] == encrypt(words, 4, 3, [-1, 2, -3, 4])
    assert is_solved(words, challenge["fingerprint"])
    assert not is_solved(challenge["cipher"], challenge["fingerprint"])
    assert "manager" not in token and fingerprint(words) == challenge["fingerprint"]


@pytest.mark.parametrize(
    ("token", "message"),
    [
        ("not base64 at all!", "smudged"),
        ("e30", "smudged"),  # {} has no telegram in it
        (make_challenge(list("abcde"), 5, 1, [1, 2, 3, 4, 5]), "can read"),  # 5 is prime
    ],
)
def test_bad_challenge_links_are_explained(token, message):
    with pytest.raises(ChallengeProblem, match=message):
        read_challenge(token)


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


def test_cli_wants_three_words(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--encrypt", "Hello there"])
    assert "at least three words" in capsys.readouterr().err


def test_cli_shows_todays_telegram(capsys):
    cli.main(["--today"])
    out = capsys.readouterr().out
    assert out.startswith("Telegram No. ") and "Column counts that fit" in out


def test_cli_explains_a_bad_key_and_exits_1(capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main(["--key", "-1 2 0 4 -5"])
    assert exit_info.value.code == 1
    assert "can't use 0" in capsys.readouterr().err
