"""The sieve of Eratosthenes, as Nicomachus of Gerasa describes it (c. 100 CE).

No work of Eratosthenes (c. 276 to 194 BCE) on the sieve survives. The earliest
description is in Nicomachus, Introduction to Arithmetic I.13.2 to 13.6, in
R. Hoche's Greek edition (Teubner, 1866), p. 29, and M. L. D'Ooge's English
translation (Macmillan, 1926), pp. 204 to 205. Nicomachus says the method "is
called by Eratosthenes the sieve" (koskinon, κόσκινον), and gives it as a way to
sort the odd numbers into primes, composites, and composites that are prime to
one another.

The code follows the text literally: every odd number in the series takes its
turn as a measure, composites included. D'Ooge's note on I.13.6 reads the text
the same way and adds that the primes alone would do. The text has no stopping
rule, so each number measures to the end of the series.

1. Set out the odd numbers in order from 3, as far as you like.
2. Take the first, 3. It measures every term that stands 2 places after the
   last one it measured: 9, 15, 21, ..., measuring them 3, 5, 7, ... times.
3. Take the second, 5. It measures every term 4 places on: 15, 25, 35, ...,
   again 3, 5, 7, ... times.
4. The term in position k measures every term 2k places on, starting with 3
   times itself.
5. The terms no number measures are the primes. The rest are composite.

In Nicomachus the primes are a class of odd numbers, so 2 is outside the series
and his sieve gives the odd primes. The standard sieve, a segmented sieve and a
mod-30 wheel sieve follow for comparison, with trial division as the reference.
"""

from __future__ import annotations

from math import isqrt

from ancient_algorithms._checks import check_at_least

__all__ = [
    "koskinon",
    "odd_primes",
    "mark_count",
    "trial_division",
    "sieve_of_eratosthenes",
    "crossing_count",
    "segmented_sieve",
    "wheel_sieve",
]

SEGMENT_SIZE = 1 << 15
"""Numbers per segment in ``segmented_sieve``, held as 1 byte each."""

WHEEL = 30
"""The wheel modulus, 2 * 3 * 5."""

WHEEL_RESIDUES = (1, 7, 11, 13, 17, 19, 23, 29)
"""The residues mod 30 that share no factor with 30, so the only places a prime above 5 can be."""


def koskinon(limit: int) -> dict[int, list[int]]:
    """Nicomachus's sieve on the odd numbers 3 to ``limit``: each one and what measures it."""
    check_at_least("limit", limit, 0)
    marks: dict[int, list[int]] = {n: [] for n in range(3, limit + 1, 2)}
    for measure in marks:
        for n in range(3 * measure, limit + 1, 2 * measure):
            marks[n].append(measure)
    return marks


def odd_primes(limit: int) -> list[int]:
    """The odd numbers up to ``limit`` that nothing measures in Nicomachus's sieve."""
    return [n for n, measures in koskinon(limit).items() if not measures]


def mark_count(limit: int) -> int:
    """Number of marks Nicomachus's sieve makes up to ``limit``."""
    return sum(len(measures) for measures in koskinon(limit).values())


def _position(n: int) -> int:
    """Index of ``n`` among the numbers prime to 30."""
    return 8 * (n // WHEEL) + WHEEL_RESIDUES.index(n % WHEEL)


def _wheel_value(i: int) -> int:
    """The ``i``-th number prime to 30, counting 1 as the 0-th."""
    return WHEEL * (i // 8) + WHEEL_RESIDUES[i % 8]


def trial_division(limit: int) -> list[int]:
    """Primes up to ``limit``, each tested by division by the primes up to its square root."""
    check_at_least("limit", limit, 0)
    primes: list[int] = []
    for n in range(2, limit + 1):
        if not _has_prime_factor_up_to_root(n, primes):
            primes.append(n)
    return primes


def _has_prime_factor_up_to_root(n: int, primes: list[int]) -> bool:
    """Whether a prime in ``primes`` no larger than sqrt(n) divides ``n``."""
    for p in primes:
        if p * p > n:
            return False
        if n % p == 0:
            return True
    return False


def sieve_of_eratosthenes(limit: int) -> list[int]:
    """Primes up to ``limit`` by the standard sieve: cross out from ``p*p`` for each prime ``p``."""
    check_at_least("limit", limit, 0)
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[: min(2, limit + 1)] = bytes(min(2, limit + 1))
    for p in range(2, isqrt(limit) + 1):
        if is_prime[p]:
            is_prime[p * p :: p] = bytes(len(range(p * p, limit + 1, p)))
    return [n for n in range(limit + 1) if is_prime[n]]


def crossing_count(limit: int, start_at_square: bool = True) -> int:
    """Crossings the standard sieve makes up to ``limit``, starting at ``p*p`` or at ``2*p``."""
    total = 0
    for p in sieve_of_eratosthenes(isqrt(limit)):
        first = p * p if start_at_square else 2 * p
        total += len(range(first, limit + 1, p))
    return total


def segmented_sieve(limit: int, segment_size: int = SEGMENT_SIZE) -> list[int]:
    """Primes up to ``limit``, sieving 1 segment of ``segment_size`` numbers at a time."""
    check_at_least("limit", limit, 0)
    check_at_least("segment_size", segment_size, 1)
    base = sieve_of_eratosthenes(isqrt(limit))
    primes: list[int] = []
    for low in range(2, limit + 1, segment_size):
        high = min(low + segment_size, limit + 1)
        is_prime = bytearray([1]) * (high - low)
        for p in base:
            first = max(p * p, -(-low // p) * p)
            if first >= high:
                continue
            is_prime[first - low :: p] = bytes(len(range(first, high, p)))
        primes.extend(low + i for i, flag in enumerate(is_prime) if flag)
    return primes


def wheel_sieve(limit: int) -> list[int]:
    """Primes up to ``limit``, storing and sieving only the numbers prime to 30."""
    check_at_least("limit", limit, 0)
    small = [p for p in (2, 3, 5) if p <= limit]
    size = 8 * (limit // WHEEL + 1)
    is_prime = bytearray([1]) * size
    is_prime[0] = 0
    for i in range(1, size):
        p = _wheel_value(i)
        if p * p > limit:
            break
        if not is_prime[i]:
            continue
        for j in range(i, size):
            multiple = p * _wheel_value(j)
            if multiple > limit:
                break
            is_prime[_position(multiple)] = 0
    rest = (_wheel_value(i) for i in range(size) if is_prime[i])
    return small + [n for n in rest if n <= limit]
