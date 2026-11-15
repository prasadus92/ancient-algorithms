"""The kuttaka ("pulverizer") of Aryabhata, Aryabhatiya, Ganitapada 32-33 (499 CE).

The verses state a rule for the remainder problem: find a number that leaves
remainder ``r1`` when divided by ``d1`` and remainder ``r2`` when divided by ``d2``.
The steps below follow the reading of Bhaskara I's commentary (629 CE), as printed
in K. S. Shukla's 1976 critical edition:

1. Divide the divisor of the greater remainder by the divisor of the smaller one.
   Keep only the remainder (Bhaskara I: "there is no use for the quotient").
2. Divide that remainder and the smaller divisor by each other in turn, writing
   the quotients one under another. This column is the valli, the "creeper".
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
verse), solves ``a*x + c = 0 (mod b)``. That is the form used for modular inverses.

The modern counterparts sit at the end of this module for comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd

__all__ = [
    "Valli",
    "pulverize",
    "two_remainders",
    "remainder_problem",
    "mod_inverse_kuttaka",
    "extended_gcd",
    "mod_inverse_euclid",
    "crt",
]


@dataclass
class Valli:
    """A record of one kuttaka run, kept so each step can be printed and checked."""

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
        """Number of divisions performed in the reciprocal division."""
        return len(self.quotients)


def _choose_mati(upper: int, lower: int, c: int, add: bool) -> tuple[int, int]:
    """Smallest positive mati with ``upper*mati +/- c`` divisible by ``lower``.

    With the full division the latest residue is 1 and the mati can be read off.
    After an early stop it is found by trial, as a person would, so keep the
    residues small when using ``stop_after``.
    """
    sign = 1 if add else -1
    if upper == 1:
        mati = (-sign * c) % lower or lower
        return mati, (mati + sign * c) // lower
    for mati in range(1, lower + 1):
        total = upper * mati + sign * c
        if total % lower == 0:
            return mati, total // lower
    raise ValueError(f"no mati exists for {upper}*m {'+' if add else '-'} {c} (mod {lower})")


def pulverize(a: int, b: int, c: int, *, stop_after: int | None = None) -> Valli:
    """Find ``x`` with ``(a*x + c) % b == 0`` by the kuttaka.

    ``stop_after`` limits the number of reciprocal divisions, which the mati makes
    possible. ``None`` divides until the latest residue is 1 or 0, so the mati can
    be read off at once.

    Raises ``ValueError`` when ``gcd(a, b)`` does not divide ``c``, the case the
    texts set aside as having no solution.
    """
    if b <= 0:
        raise ValueError("b must be positive")
    g = gcd(a, b)
    if c % g:
        raise ValueError(f"no solution: gcd({a}, {b}) = {g} does not divide {c}")
    # Bhaskara I's niragra reading first removes the common factor (apavartana).
    a, b, c = a // g, b // g, c // g
    record = Valli(a=a, b=b, c=c)
    if b == 1:
        record.x = 0
        return record

    # residues[0] is the lower divisor b, residues[1] the first remainder a mod b.
    residues = [b, a % b]
    quotients: list[int] = []
    while residues[-1] > 1 and (stop_after is None or len(quotients) < stop_after):
        q, r = divmod(residues[-2], residues[-1])
        quotients.append(q)
        residues.append(r)

    n = len(quotients)
    # Each division swaps the roles of the two rows and flips the sign of c.
    upper, lower = residues[n + 1], residues[n]
    added = n % 2 == 0
    mati, mq = _choose_mati(upper, lower, c, added)

    column = quotients + [mati, mq]
    reduced = [column[:]]
    work = column[:]
    # "Multiply the upper by the lower and add the last", from the bottom up.
    for i in range(n - 1, -1, -1):
        work[i] = work[i] * work[i + 1] + work[i + 2]
        work = work[: i + 2]
        reduced.append(work[:])

    record.quotients = quotients
    record.residues = residues
    record.mati = mati
    record.mati_quotient = mq
    record.added = added
    record.column = column
    record.reduced = reduced
    record.x = work[0] % b
    return record


def two_remainders(r1: int, d1: int, r2: int, d2: int) -> int:
    """Aryabhata's dvicchedagra: smallest ``N >= 0`` with ``N % d1 == r1`` and ``N % d2 == r2``.

    Follows Ganitapada 32-33 as read by Bhaskara I. The divisor with the greater
    remainder is the one that gets divided first.
    """
    if not (0 <= r1 < d1 and 0 <= r2 < d2):
        raise ValueError("each remainder must be smaller than its divisor")
    if r1 >= r2:
        big_r, big_d, small_r, small_d = r1, d1, r2, d2
    else:
        big_r, big_d, small_r, small_d = r2, d2, r1, d1
    # N = big_d * x + big_r must leave small_r with small_d, so
    # big_d * x + (big_r - small_r) is divisible by small_d.
    valli = pulverize(big_d, small_d, big_r - small_r)
    step = small_d // gcd(big_d, small_d)
    n = big_d * (valli.x % step) + big_r
    return n % (big_d * step)


def remainder_problem(pairs: list[tuple[int, int]]) -> int:
    """Fold several ``(remainder, divisor)`` pairs, as Bhaskara I does in his third example.

    Each solved pair becomes a new remainder whose divisor is the product (here the
    least common multiple) of the two divisors.
    """
    if not pairs:
        raise ValueError("need at least one (remainder, divisor) pair")
    r, d = pairs[0]
    r %= d
    for r2, d2 in pairs[1:]:
        r = two_remainders(r, d, r2 % d2, d2)
        d = d * d2 // gcd(d, d2)
    return r


def mod_inverse_kuttaka(a: int, m: int) -> int:
    """Inverse of ``a`` modulo ``m``: the ``x`` with ``a*x - 1`` divisible by ``m``."""
    if gcd(a, m) != 1:
        raise ValueError(f"{a} has no inverse modulo {m}")
    if m == 1:
        return 0
    return pulverize(a, m, -1).x


# Modern counterparts, for comparison.


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    """Return ``(g, s, t)`` with ``a*s + b*t == g == gcd(a, b)``, iteratively."""
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r:
        q = old_r // r
        old_r, r = r, old_r - q * r
        old_s, s = s, old_s - q * s
        old_t, t = t, old_t - q * t
    return old_r, old_s, old_t


def mod_inverse_euclid(a: int, m: int) -> int:
    """Inverse of ``a`` modulo ``m`` from the extended Euclidean algorithm."""
    g, s, _ = extended_gcd(a % m, m)
    if g != 1:
        raise ValueError(f"{a} has no inverse modulo {m}")
    return s % m


def crt(pairs: list[tuple[int, int]]) -> int:
    """Chinese remainder theorem by the textbook construction, for comparison."""
    r, d = 0, 1
    for r2, d2 in pairs:
        g, s, _ = extended_gcd(d, d2)
        if (r2 - r) % g:
            raise ValueError("inconsistent congruences")
        lcm = d // g * d2
        r = (r + (r2 - r) // g * s % (d2 // g) * d) % lcm
        d = lcm
    return r
