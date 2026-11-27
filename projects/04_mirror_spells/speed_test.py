"""Race the slow (list) and fast (set) spell finders, then profile them.

Usage (from the repo root):
    uv run python projects/04_mirror_spells/speed_test.py
    uv run python projects/04_mirror_spells/speed_test.py --sample 1000

Both finders look up partners in the *whole* dictionary; they only
check a sample of core words, so the slow one finishes in seconds rather
than minutes. Because each core word costs about the same, the slow
time for the full list is the sample time scaled up.
"""

import argparse
import cProfile
import io
import pstats
import random
import time
from collections.abc import Callable

from palingrams import spells_from
from wordlist import clean_words, read_words


def timed(func: Callable, *args) -> tuple[object, float]:
    """Run ``func(*args)`` and return its result and how long it took.

    ``time.perf_counter()`` is a stopwatch made for this: the highest
    resolution clock available, unaffected by changes to the system time.
    """
    start = time.perf_counter()
    result = func(*args)
    return result, time.perf_counter() - start


def race(words: list[str], sample_size: int = 500, seed: int = 4) -> dict:
    """Time the list and set lookups on the same sample of core words."""
    sample = random.Random(seed).sample(words, min(sample_size, len(words)))
    vocab = set(words)
    slow_pairs, slow = timed(spells_from, sample, words)  # in a list
    fast_pairs, fast = timed(spells_from, sample, vocab)  # in a set
    if slow_pairs != fast_pairs:
        raise RuntimeError("the list and set finders disagree")
    _, full_fast = timed(spells_from, vocab, vocab)
    scale = len(words) / len(sample)
    return {
        "sample": len(sample),
        "words": len(words),
        "slow_seconds": slow,
        "fast_seconds": fast,
        "speedup": slow / fast if fast else float("inf"),
        "slow_full_estimate": slow * scale,
        "fast_full_seconds": full_fast,
    }


def profile_report(func: Callable, *args, lines: int = 8) -> str:
    """Profile one call with cProfile and return the busiest functions.

    ``pstats`` sorts the measurements; "tottime" is time spent inside a
    function itself, which points straight at the slow part.
    """
    profiler = cProfile.Profile()
    profiler.runcall(func, *args)
    out = io.StringIO()
    stats = pstats.Stats(profiler, stream=out).strip_dirs()
    stats.sort_stats("tottime").print_stats(lines)
    return out.getvalue()


def main(argv: list[str] | None = None) -> None:
    """Print the race result and a cProfile report for each finder."""
    parser = argparse.ArgumentParser(description="Race list vs set.")
    parser.add_argument("--sample", type=int, default=500)
    args = parser.parse_args(argv)

    words = clean_words(read_words())
    result = race(words, args.sample)
    print(f"Checking {result['sample']:,} core words against all")
    print(f"{result['words']:,} words:")
    print(f"  list lookups: {result['slow_seconds']:.3f} s")
    print(f"  set lookups:  {result['fast_seconds']:.4f} s")
    print(f"  the set is about {result['speedup']:,.0f} times faster")
    print(
        f"Whole dictionary: list ~{result['slow_full_estimate']:.0f} s "
        f"(estimated), set {result['fast_full_seconds']:.2f} s (measured)"
    )

    sample = words[:: max(1, len(words) // args.sample)]
    print("\ncProfile, list version on the sample:")
    print(profile_report(spells_from, sample, words))
    print("cProfile, set version on the whole dictionary:")
    vocab = set(words)
    print(profile_report(spells_from, vocab, vocab))


if __name__ == "__main__":
    main()
