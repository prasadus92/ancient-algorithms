"""Nicomachus's sieve against the standard, segmented and wheel sieves, and trial division.

For each limit, prints the best of 3 timings in milliseconds. Every result is
checked against the standard sieve first. Trial division and Nicomachus's
literal sieve take over a second at 1,000,000, so they run there only with
``--full``.

Run: python benchmarks/sieve_compare.py [--full]
"""

from __future__ import annotations

import sys
import timeit
from collections.abc import Callable

from ancient_algorithms.sieve import (
    odd_primes,
    segmented_sieve,
    sieve_of_eratosthenes,
    trial_division,
    wheel_sieve,
)

LIMITS = (10**4, 10**5, 10**6)
SLOW_LIMIT = 10**5


def nicomachus(limit: int) -> list[int]:
    return [2, *odd_primes(limit)] if limit >= 2 else []


METHODS: dict[str, tuple[Callable[[int], list[int]], bool]] = {
    "trial division": (trial_division, True),
    "Nicomachus": (nicomachus, True),
    "standard": (sieve_of_eratosthenes, False),
    "segmented": (segmented_sieve, False),
    "wheel 30": (wheel_sieve, False),
}


def best_ms(method: Callable[[int], list[int]], limit: int) -> float:
    return min(timeit.repeat(lambda: method(limit), number=1, repeat=3)) * 1000


def main(full: bool) -> None:
    expected = {limit: sieve_of_eratosthenes(limit) for limit in LIMITS}
    print(f"{'method':>15} " + " ".join(f"{limit:>12,}" for limit in LIMITS))
    for name, (method, slow) in METHODS.items():
        cells = []
        for limit in LIMITS:
            if slow and limit > SLOW_LIMIT and not full:
                cells.append(f"{'--full':>12}")
                continue
            assert method(limit) == expected[limit]
            cells.append(f"{best_ms(method, limit):>10.1f}ms")
        print(f"{name:>15} " + " ".join(cells))
    print("primes:", [len(expected[limit]) for limit in LIMITS])


if __name__ == "__main__":
    main(full="--full" in sys.argv[1:])
