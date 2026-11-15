"""The kuttaka ("pulverizer") of Aryabhata, Aryabhatiya, Ganitapada 32-33 (c. 499 CE).

The verses state a rule for the remainder problem: find a number that leaves
remainder ``r1`` when divided by ``d1`` and remainder ``r2`` when divided by ``d2``.
The steps below follow the reading of Bhaskara I's commentary (629 CE), as printed
in K. S. Shukla's 1976 critical edition:

1. Divide the divisor of the greater remainder by the divisor of the smaller one.
   Keep only the remainder (Bhaskara I: "there is no use for the quotient").
2. Divide that remainder and the smaller divisor by each other in turn, writing
   the quotients one under another, as a column.
3. Stop at any point. Choose a number, the mati, such that the latest residue
   times the mati, plus or minus the difference of the remainders, divides
   exactly by the residue before it. Bhaskara I adds the difference when the
   count of quotients is even and subtracts it when the count is odd ("sameshu
   kshiptam vishameshu shodhyam"), a rule he says comes from tradition. Write the
   mati and the quotient of that exact division under the column.
4. From the bottom up, replace each number with itself times the number below it,
   plus the number below that ("multiply the upper by the lower, add the last").
5. Divide the top number by the divisor of the smaller remainder, multiply the
   remainder by the divisor of the greater remainder, and add the greater
   remainder. The result satisfies both divisors.

The same column, read without remainders (Bhaskara I's niragra reading of the same
verses), solves ``a*x + c = 0 (mod b)``. That is the form used for modular inverses.

The extended Euclidean algorithm and the textbook Chinese remainder construction
are at the end of the module, for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd

__all__ = [
    "KuttakaRecord",
    "pulverize",
    "two_remainders",
    "remainder_problem",
    "mod_inverse_kuttaka",
    "extended_gcd",
    "mod_inverse_euclid",
    "crt",
]

TRIAL_LIMIT = 10_000
"""Largest last divisor for which the mati is found by trial, as a person would."""


@dataclass
class KuttakaRecord:
    """One kuttaka run, kept so each step can be printed and checked.

    ``a``, ``b`` and ``c`` are the values after the common factor is removed.
    ``reduced`` holds every fold of the column only when ``trace=True``.
    """

    a: int
    b: int
    c: int
    quotients: list[int] = field(default_factory=list)
    residues: list[int] = field(default_factory=list)
    mati: int = 0
    mati_quotient: int = 0
    added: bool = True
    column: list[int] = field(default_factory=list)
    reduced: list[list[int]] = field(default_factory=list)
    x: int = 0

    @property
    def divisions(self) -> int:
        """Number of divisions in the reciprocal division."""
        return len(self.quotients)


def pulverize(
    a: int, b: int, c: int, *, stop_after: int | None = None, trace: bool = False
) -> KuttakaRecord:
    """Find the smallest ``x >= 0`` with ``(a*x + c) % b == 0`` by the kuttaka.

    ``stop_after`` limits the number of reciprocal divisions, which the mati makes
    possible. ``None`` divides until the latest residue is 1, so the mati can be
    read off at once.

    ``trace=True`` keeps every fold of the column in ``reduced``. Its memory grows
    with the square of the number of divisions, so it is off by default.

    Raises ``ValueError`` when ``gcd(a, b)`` does not divide ``c``, the case the
    texts set aside as having no solution.
    """
    if b <= 0:
        raise ValueError(f"the divisor must be positive, got {b}")
    if stop_after is not None and stop_after < 0:
        raise ValueError(f"stop_after must be at least 0, got {stop_after}")
    g = gcd(a, b)
    if c % g:
        raise ValueError(f"no solution: gcd({a}, {b}) = {g} does not divide {c}")
    # Bhaskara I removes the common factor first (apavartana).
    a, b, c = a // g, b // g, c // g
    record = KuttakaRecord(a=a, b=b, c=c)
    if b == 1:
        return record

    quotients, residues = _reciprocal_division(a % b, b, stop_after)
    n = len(quotients)
    # Each division swaps the 2 rows and flips the sign of c, hence add when n is even.
    added = n % 2 == 0
    mati, mati_quotient = _choose_mati(residues[n + 1], residues[n], c, added)
    column = quotients + [mati, mati_quotient]
    top, reduced = _fold(column, trace)

    record.quotients = quotients
    record.residues = residues
    record.mati = mati
    record.mati_quotient = mati_quotient
    record.added = added
    record.column = column
    record.reduced = reduced
    record.x = top % b
    return record


def _reciprocal_division(
    first_remainder: int, divisor: int, stop_after: int | None
) -> tuple[list[int], list[int]]:
    """Divide the 2 numbers by each other in turn until a residue is 1, or ``stop_after`` times."""
    residues = [divisor, first_remainder]
    quotients: list[int] = []
    while residues[-1] > 1 and (stop_after is None or len(quotients) < stop_after):
        q, r = divmod(residues[-2], residues[-1])
        quotients.append(q)
        residues.append(r)
    return quotients, residues


def _choose_mati(residue: int, previous: int, c: int, add: bool) -> tuple[int, int]:
    """Smallest positive mati with ``residue*mati +/- c`` divisible by ``previous``.

    Returns the mati and the quotient of that exact division.
    """
    sign = 1 if add else -1
    if residue == 1 or previous > TRIAL_LIMIT:
        mati = (-sign * c) * pow(residue, -1, previous) % previous or previous
        return mati, (residue * mati + sign * c) // previous
    for mati in range(1, previous + 1):
        total = residue * mati + sign * c
        if total % previous == 0:
            return mati, total // previous
    raise ValueError(f"no mati exists for {residue}*m {'+' if add else '-'} {c} (mod {previous})")


def _fold(column: list[int], trace: bool) -> tuple[int, list[list[int]]]:
    """Fold the column from the bottom: "multiply the upper by the lower, add the last"."""
    work = column[:]
    reduced = [column[:]] if trace else []
    for i in range(len(column) - 3, -1, -1):
        work[i] = work[i] * work[i + 1] + work[i + 2]
        if trace:
            reduced.append(work[: i + 2])
    return work[0], reduced


def two_remainders(r1: int, d1: int, r2: int, d2: int) -> int:
    """Aryabhata's dvicchedagra: smallest ``N >= 0`` with ``N % d1 == r1`` and ``N % d2 == r2``.

    Follows Ganitapada 32-33 as read by Bhaskara I. The divisor with the greater
    remainder is the one that gets divided first. When the divisors share a
    factor, the common factor is removed first, a step Bhaskara I gives in his
    niragra reading of the same verses.
    """
    if not (0 <= r1 < d1 and 0 <= r2 < d2):
        raise ValueError("each remainder must be smaller than its divisor")
    if r1 >= r2:
        greater_r, greater_d, lesser_r, lesser_d = r1, d1, r2, d2
    else:
        greater_r, greater_d, lesser_r, lesser_d = r2, d2, r1, d1
    # N = greater_d*x + greater_r must also leave lesser_r when divided by lesser_d.
    x = pulverize(greater_d, lesser_d, greater_r - lesser_r).x
    return greater_d * x + greater_r


def remainder_problem(pairs: list[tuple[int, int]]) -> int:
    """Smallest ``N >= 0`` leaving each ``remainder`` with its ``divisor``.

    Folds the pairs 2 at a time, as Bhaskara I does in his third example: each
    solved pair becomes 1 remainder whose divisor is the least common multiple of
    the 2 divisors.
    """
    if not pairs:
        raise ValueError("need at least one (remainder, divisor) pair")
    for remainder, divisor in pairs:
        if divisor < 1 or not 0 <= remainder < divisor:
            raise ValueError(f"need 0 <= remainder < divisor, got ({remainder}, {divisor})")
    n, modulus = pairs[0]
    for remainder, divisor in pairs[1:]:
        n = two_remainders(n, modulus, remainder, divisor)
        modulus = modulus * divisor // gcd(modulus, divisor)
    return n


def mod_inverse_kuttaka(a: int, m: int) -> int:
    """Inverse of ``a`` modulo ``m``: the ``x`` with ``a*x - 1`` divisible by ``m``."""
    _check_invertible(a, m)
    return pulverize(a, m, -1).x if m > 1 else 0


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return ``(g, s, t)`` with ``a*s + b*t == g == gcd(a, b)`` and ``g >= 0``."""
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    if old_r < 0:
        return -old_r, -old_s, -old_t
    return old_r, old_s, old_t


def mod_inverse_euclid(a: int, m: int) -> int:
    """Inverse of ``a`` modulo ``m`` from the extended Euclidean algorithm."""
    _check_invertible(a, m)
    return extended_gcd(a % m, m)[1] % m


def crt(pairs: list[tuple[int, int]]) -> int:
    """Chinese remainder theorem by the textbook construction."""
    n, modulus = 0, 1
    for remainder, divisor in pairs:
        g, s, _ = extended_gcd(modulus, divisor)
        if (remainder - n) % g:
            raise ValueError("inconsistent congruences")
        lcm = modulus // g * divisor
        n = (n + (remainder - n) // g * s % (divisor // g) * modulus) % lcm
        modulus = lcm
    return n


def _check_invertible(a: int, m: int) -> None:
    """Raise ``ValueError`` unless ``m`` is positive and ``a`` is coprime to it."""
    if m < 1:
        raise ValueError(f"the modulus must be positive, got {m}")
    if gcd(a, m) != 1:
        raise ValueError(f"{a} has no inverse modulo {m}")
