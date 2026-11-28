"""Hide a scrambled secret in white ink between the lines of a Word letter.

Usage (from the repo root):

    uv run python projects/08_invisible_ink/main.py --demo --out letter.docx
    uv run python projects/08_invisible_ink/main.py --hide cover.txt secret.txt \
        --key PUFFIN --out letter.docx
    uv run python projects/08_invisible_ink/main.py --room cover.txt secret.txt
    uv run python projects/08_invisible_ink/main.py --find letter.docx --key PUFFIN
    uv run python projects/08_invisible_ink/main.py --typewriter "a line of words" --secret KEY

``--hide`` scrambles each secret line with the key (Vigenère), tucks the
lines into the cover letter's blank lines in white ink, and saves a .docx.
``--find`` reads any .docx and prints its white ink, unscrambled if you
give the key. ``--room`` is the book's practice project: is there space?
"""

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "common"))

# pylint: disable=wrong-import-position
from docx_reader import find_white_ink  # noqa: E402
from docx_writer import make_docx  # noqa: E402
from invisible_ink import (  # noqa: E402
    between_words,
    interleave,
    letter_lines,
    long_lines,
    room_check,
    secret_lines,
)
from letters import DATE, SUBTITLE, TITLE, demo_letter  # noqa: E402
from vigenere import decrypt, encrypt, spell_out  # noqa: E402

# pylint: enable=wrong-import-position


def read_lines(path: str, secret: bool) -> list[str]:
    """Read a cover letter (blank lines kept) or a secret (blank lines dropped)."""
    text = Path(path).read_text(encoding="utf-8")
    return secret_lines(text) if secret else letter_lines(text)


def hide(cover_path: str, secret_path: str, key: str, out: str) -> None:
    """Scramble the secret, hide it in the letter and save the Word file."""
    cover = read_lines(cover_path, secret=False)
    secret = [encrypt(spell_out(line), key) for line in read_lines(secret_path, secret=True)]
    for n in long_lines(secret):
        print(f"Careful: secret line {n} is long and may wrap. Press Enter earlier.")
    Path(out).write_bytes(make_docx(interleave(cover, secret), TITLE, SUBTITLE, DATE))
    print(f"Saved {out}. Select all and highlight it in black to see the ink.")


def main() -> None:
    """Parse the options and run one of the jobs."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    jobs = parser.add_mutually_exclusive_group(required=True)
    jobs.add_argument("--demo", action="store_true", help="save the joke shop's own letter")
    jobs.add_argument(
        "--hide", nargs=2, metavar=("COVER", "SECRET"), help="hide a secret in a letter"
    )
    jobs.add_argument("--room", nargs=2, metavar=("COVER", "SECRET"), help="check there's room")
    jobs.add_argument("--find", metavar="DOCX", help="look for white ink in a Word file")
    jobs.add_argument("--typewriter", metavar="LINE", help="hide --secret between the words")
    parser.add_argument("--key", default="PUFFIN", help="the scrambling keyword")
    parser.add_argument("--secret", default="", help="the secret for --typewriter")
    parser.add_argument("--out", default="letter.docx", help="where to save the Word file")
    args = parser.parse_args()

    try:
        if args.demo:
            Path(args.out).write_bytes(make_docx(demo_letter(), TITLE, SUBTITLE, DATE))
            print(f"Saved {args.out}. The key is PUFFIN.")
        elif args.hide:
            hide(*args.hide, args.key, args.out)
        elif args.room:
            check = room_check(read_lines(args.room[0], False), read_lines(args.room[1], True))
            if check["fits"]:
                blanks, needed = check["blanks"], check["needed"]
                print(f"Plenty of room: {blanks} blank lines for {needed} secret lines.")
            else:
                print(f"Not enough room: add {check['add']} blank lines to the letter.")
        elif args.find:
            ink = find_white_ink(Path(args.find).read_bytes())
            for line in ink:
                print(decrypt(line, args.key) if args.key else line)
            if not ink:
                print("No white ink in that letter.")
        else:
            pieces = between_words(args.typewriter, args.secret)
            print("".join(p["text"] if not p["hidden"] else " " for p in pieces))
            print("With the ink showing:")
            print("".join(p["text"] for p in pieces))
    except ValueError as problem:
        print(problem, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
