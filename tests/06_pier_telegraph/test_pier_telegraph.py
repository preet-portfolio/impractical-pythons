import importlib.util
import itertools
import random
from datetime import date
from pathlib import Path

import pytest

import night_clerk
import rail_fence
import sniff
from challenge import ChallengeProblem, fingerprint, is_solved, make_challenge, read_challenge
from codebook import CODEBOOK, FILLER, TICKETS, decode, encode, grid_options, pad, snuggest
from dispatches import DISPATCHES, dispatch, plain_route_hits, telegram_number, todays_dispatch
from rail_fence import RailProblem
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
from word_gaps import coverage, split_words, word_set
from wordlist import read_words

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


# ---------------------------------------------------------------- rail fence

WORDS = word_set(read_words())


def test_rail_fence_worked_example():
    # L.T.S.R.S.T.E.I.R on top, .E.U.C.O.S.H.P.E. underneath
    assert rail_fence.encrypt("Let us cross the pier") == "LTSRSTEIREUCOSHPE"
    assert rail_fence.decrypt("LTSRS TEIRE UCOSH PE") == "LETUSCROSSTHEPIER"


def test_prepare_keeps_only_letters_without_accents():
    assert rail_fence.prepare("Café at 9, by the pier!") == "CAFEATBYTHEPIER"


def test_zigzag_rows_bounce_between_the_rails():
    assert rail_fence.zigzag_rows(6, 2) == [0, 1, 0, 1, 0, 1]
    assert rail_fence.zigzag_rows(9, 3) == [0, 1, 2, 1, 0, 1, 2, 1, 0]


@pytest.mark.parametrize("rails", range(2, 7))
@pytest.mark.parametrize("text", ["Bring two spades", "Bring two spades now"])
def test_rail_fence_round_trips(text, rails):
    assert rail_fence.decrypt(rail_fence.encrypt(text, rails), rails) == rail_fence.prepare(text)


@pytest.mark.parametrize("length", range(3, 12))
def test_two_rail_shortcut_matches_the_zigzag_walk(length):
    letters = "ABCDEFGHIJKLMNOP"[:length]
    assert rail_fence.two_rail_decrypt(letters) == rail_fence.zigzag_decrypt(letters, 2)


def test_in_fives():
    assert rail_fence.in_fives("ABCDEFGH") == "ABCDE FGH"


@pytest.mark.parametrize(
    ("text", "rails", "message"),
    [("!!", 2, "no letters"), ("Hi", 1, "two rails"), ("Hello", 5, "straight across")],
)
def test_rail_fence_explains_what_it_cant_carry(text, rails, message):
    with pytest.raises(RailProblem, match=message):
        rail_fence.encrypt(text, rails)


# ---------------------------------------------------------- putting gaps back


def test_split_words_puts_the_spaces_back():
    assert split_words("LETUSCROSSTHEPIERATLOWTIDE", WORDS) == [
        "let",
        "us",
        "cross",
        "the",
        "pier",
        "at",
        "low",
        "tide",
    ]
    assert split_words("BRINGTWOSPADESTHETREASUREISUNDER", WORDS)[-2:] == ["is", "under"]


def test_split_words_keeps_letters_it_cant_explain():
    parts = split_words("MEETQXZBYTHESEA", WORDS)
    assert "".join(parts).upper() == "MEETQXZBYTHESEA"
    assert "QXZ" in "".join(part for part in parts if part.isupper())
    assert coverage("MEETQXZBYTHESEA", WORDS) == pytest.approx(12 / 15)


# --------------------------------------------------------------- night clerk


@pytest.mark.parametrize("cols", range(1, 6))
def test_key_count_matches_the_keys_really_tried(cols):
    keys = list(night_clerk.all_keys(cols))
    assert night_clerk.key_count(cols) == len(keys)
    assert len({tuple(key) for key in keys}) == len(keys)


def test_key_counts_explode():
    counts = [night_clerk.key_count(cols) for cols in range(2, 8)]
    assert counts == [8, 48, 384, 3840, 46080, 645120]


def test_place_agrees_with_route_decrypt():
    cipher = encrypt(TICKETS["words"], 5, 3, TICKETS["key"])
    for key in itertools.islice(night_clerk.all_keys(5), 0, 3840, 97):
        assert night_clerk.place(cipher, 5, 3, key) == decrypt(cipher, 5, 3, key)


def test_readability_likes_filler_at_the_end_and_dislikes_the_and():
    good = ["meet", "me", "at", "BUCKET", "KITE"]
    assert night_clerk.readability(good) > night_clerk.readability(
        ["KITE", "meet", "me", "at", "BUCKET"]
    )
    assert night_clerk.readability(["the", "and", "pier"]) < night_clerk.readability(
        ["the", "pier", "and"]
    )


def test_a_real_sandcastle_is_not_filler():
    assert night_clerk.expand(["the", "sandcastle", "SANDCASTLE"]) == ["the", "sandcastle", "~"]


def three_hunches(words):
    """Three pairs a person might spot: the start, the middle and the end."""
    message = [word for word in words if word not in FILLER]
    middle = len(message) // 2
    return [message[:2], message[middle : middle + 2], message[-2:]]


@pytest.mark.parametrize("number", range(1, len(DISPATCHES) + 1))
def test_night_clerk_cracks_every_daily_telegram_with_three_hunches(number):
    today = dispatch(number)
    cipher = encrypt(today["words"], today["cols"], today["rows"], today["key"])
    result = night_clerk.crack_route(cipher, three_hunches(today["words"]))
    assert today["words"] in [best["words"] for best in result["best"]]
    assert result["tried"] >= night_clerk.key_count(today["cols"])
    assert result["fit"] < result["tried"] / 10


def test_hunches_ignore_capitals_and_impossible_ones_leave_nothing():
    today = dispatch(14)
    cipher = encrypt(today["words"], today["cols"], today["rows"], today["key"])
    assert night_clerk.crack_route(cipher, [["gull", "won"]])["fit"] > 0
    assert night_clerk.crack_route(cipher, [["gull", "pancake"]])["fit"] == 0


def test_too_wide_racks_are_skipped_not_tried():
    result = night_clerk.crack_route([str(n) for n in range(14)], top=1)
    assert result["racks"] == [(2, 7)]
    assert result["too_wide"] == [7]
    assert result["tried"] == 8


def test_night_clerk_breaks_a_challenge_seal():
    today = dispatch(3)
    token = make_challenge(today["words"], today["cols"], today["rows"], today["key"])
    link = read_challenge(token)
    broken = night_clerk.crack_seal(link["cipher"], link["fingerprint"])
    assert broken["words"] == today["words"]
    assert is_solved(broken["words"], link["fingerprint"])


def test_a_seal_with_no_route_stays_shut():
    assert night_clerk.crack_seal(["a", "b", "c", "d"], "0" * 12) is None


def test_crack_rails_finds_the_intercepted_rail_count():
    result = night_clerk.crack_rails(rail_fence.intercepted(), WORDS)
    assert result["best"] == rail_fence.INTERCEPT_RAILS
    assert [reading["rails"] for reading in result["readings"]] == list(range(2, 9))
    best = next(r for r in result["readings"] if r["rails"] == result["best"])
    assert best["coverage"] == 1


# ------------------------------------------------------- shuffled or swapped


@pytest.mark.parametrize("text", [*rail_fence.RAIL_SAMPLES, *DISPATCHES])
def test_rail_fence_telegrams_sniff_shuffled(text):
    assert sniff.verdict(rail_fence.encrypt(text))["verdict"] == "shuffled"


@pytest.mark.parametrize("text", [*rail_fence.RAIL_SAMPLES, *DISPATCHES])
def test_swapped_telegrams_sniff_swapped(text):
    result = sniff.verdict(sniff.swap_letters(text))
    assert result["verdict"] == "swapped"
    assert result["reason"]


def test_short_telegrams_are_too_short_to_tell():
    assert sniff.verdict("Meet me at noon")["verdict"] == "too short"


def test_swap_letters_swaps_every_letter_the_same_way():
    swapped = sniff.swap_letters("aa bb")
    assert len(swapped) == 4
    assert swapped[0] == swapped[1] and swapped[2] == swapped[3] and swapped[0] != swapped[2]


def test_letter_shares_add_up_to_100():
    assert sum(sniff.letter_shares("The pier at night").values()) == pytest.approx(100)


# ------------------------------------------------------------- the new flags


def test_cli_rail_and_unrail(capsys):
    cli.main(["--rail", "Let us cross the pier"])
    assert capsys.readouterr().out.strip() == "LTSRS TEIRE UCOSH PE"
    cli.main(["--unrail", "LTSRS TEIRE UCOSH PE"])
    assert "let us cross the pier" in capsys.readouterr().out


def test_cli_crack_rails_marks_three(capsys):
    cli.main(["--crack-rails"])
    out = capsys.readouterr().out
    assert "3 rails: 100% real words" in out and "reads best" in out


def test_cli_night_clerk_with_hunches(capsys):
    cli.main(["--night-clerk", "--hunch", "gull won"])
    assert "tried" in capsys.readouterr().out


def test_cli_sniff(capsys):
    cli.main(["--sniff", sniff.swap_letters(DISPATCHES[0])])
    assert capsys.readouterr().out.startswith("Swapped")


@pytest.mark.parametrize(
    "argv",
    [["--rail", "!!"], ["--unrail", "ABC", "--rails", "5"], ["--night-clerk", "--hunch", "x"]],
)
def test_cli_new_flags_explain_mistakes_and_exit_1(argv, capsys):
    with pytest.raises(SystemExit) as stop:
        cli.main(argv)
    assert stop.value.code == 1
    assert "can't do that" in capsys.readouterr().err
