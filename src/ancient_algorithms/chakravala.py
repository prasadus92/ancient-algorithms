"""The chakravala (cyclic) method for x^2 - N*y^2 = 1, from Bhaskara II's Bijaganita (1150).

Source: Bhaskara II, Bijaganita, chapter 3 ("affected square", vargaprakriti),
section 1 (composition) and section 2 (the cyclic method), in H. T. Colebrooke,
"Algebra, with Arithmetic and Mensuration, from the Sanscrit of Brahmegupta and
Bhascara" (London, 1817), pp. 170 to 178, sections 75 to 87. Colebrooke dates
the Siddhantasiromani, of which the Bijaganita is a part, to Saka 1072, 1150 CE,
from Bhaskara's own statement.

The text calls a triple (kanistha, jyestha, ksepa) a solution when

    N * kanistha^2 + ksepa = jyestha^2

that is, kanistha is the "least" root y, jyestha the "greatest" root x, and ksepa
the additive k, in the modern form x^2 - N*y^2 = k. Triples here keep the text's
order, (kanistha, jyestha, ksepa).

The method, as Bhaskara II states it in sections 83 to 86:

1. Start from any triple. His examples take kanistha = 1 and jyestha = the
   whole number whose square is nearest N.
2. Find a multiplier m with (kanistha*m + jyestha) divisible by the ksepa, by
   the kuttaka ("making the least root, greatest root and additive a dividend,
   additive and divisor"). Among the m that work, take one whose square is
   close to N ("so that the remainder be small").
3. The new ksepa is (m^2 - N) / ksepa. The new kanistha is the quotient of that
   kuttaka, (kanistha*m + jyestha) / |ksepa|, and the new jyestha is
   (jyestha*m + N*kanistha) / |ksepa|, the rule Colebrooke's note gives from
   the commentator Krishna.
4. Repeat until the ksepa is 1, or stop at ksepa -1, 2, -2, 4 or -4 and finish
   with Brahmagupta's composition (bhavana), as Bhaskara II does in his
   2 worked examples, N = 67 and N = 61.

Bhavana ("composition") is Brahmagupta's rule (Brahmasphutasiddhanta, 628 CE,
chapter 18, Colebrooke pp. 363 to 364), which Bhaskara II repeats as his
sections 77 and 78: from 2 triples for the same N, cross-multiply the roots and
multiply the ksepas.

The textbook continued-fraction solution is at the end of the module, for
comparison.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from math import gcd, isqrt
from typing import TypeVar

from ancient_algorithms.kuttaka import pulverize

__all__ = [
    "Triple",
    "ChakravalaRecord",
    "bhavana",
    "starting_triple",
    "choose_multiplier",
    "chakravala_step",
    "chakravala",
    "complete_by_bhavana",
    "pell_continued_fraction",
]

Triple = tuple[int, int, int]
"""(kanistha, jyestha, ksepa) with N * kanistha^2 + ksepa == jyestha^2."""

Root = TypeVar("Root", int, Fraction)

SHORTCUT_KSEPAS = (-1, 2, -2, 4, -4)
"""Ksepas from which Bhaskara II finishes by composition instead of cycling on."""


@dataclass
class ChakravalaRecord:
    """One chakravala run, kept so each round of the cycle can be printed and checked.

    ``triples`` holds every triple from the start to the stop, and ``multipliers``
    the m chosen at each round, so ``len(multipliers) == len(triples) - 1``.
    ``solution`` is the final triple with ksepa 1.
    """

    n: int
    triples: list[Triple] = field(default_factory=list)
    multipliers: list[int] = field(default_factory=list)
    solution: Triple = (0, 1, 1)
    finished_by_bhavana: bool = False

    @property
    def rounds(self) -> int:
        """Number of rounds of the cycle, each needing 1 kuttaka."""
        return len(self.multipliers)


def bhavana(
    first: tuple[Root, Root, int],
    second: tuple[Root, Root, int],
    n: int,
    *,
    difference: bool = False,
) -> tuple[Root, Root, int]:
    """Brahmagupta's composition of 2 triples for the same ``n``.

    By the sum (Bijaganita section 77): kanistha = k1*j2 + k2*j1,
    jyestha = n*k1*k2 + j1*j2, ksepa = e1*e2. By the difference (section 78):
    kanistha = k1*j2 - k2*j1, jyestha = n*k1*k2 - j1*j2, and the same ksepa.
    Works on ints or Fractions alike.
    """
    k1, j1, e1 = first
    k2, j2, e2 = second
    if difference:
        return k1 * j2 - k2 * j1, n * k1 * k2 - j1 * j2, e1 * e2
    return k1 * j2 + k2 * j1, n * k1 * k2 + j1 * j2, e1 * e2


def starting_triple(n: int) -> Triple:
    """Bhaskara II's start: kanistha 1, jyestha the whole number whose square is nearest ``n``."""
    _check_n(n)
    root = isqrt(n)
    jyestha = root if n - root * root <= (root + 1) ** 2 - n else root + 1
    return 1, jyestha, jyestha * jyestha - n


def choose_multiplier(triple: Triple, n: int) -> int:
    """The m with ``(kanistha*m + jyestha) % ksepa == 0`` that makes ``|m^2 - n|`` least.

    The kuttaka gives the smallest such m; every m that works differs from it by a
    multiple of ``|ksepa|``. The text does not settle a tie; this takes the m below
    the square root of ``n``.
    """
    kanistha, jyestha, ksepa = triple
    step = abs(ksepa)
    base = pulverize(kanistha, step, jyestha).x
    root = isqrt(n)
    below = base + (root - base) // step * step
    above = below + step
    candidates = [m for m in (below, above) if m > 0]
    return min(candidates, key=lambda m: (abs(m * m - n), m))


def chakravala_step(triple: Triple, n: int, m: int) -> Triple:
    """One round of the cycle: the triple that multiplier ``m`` leads to (sections 84 to 85)."""
    kanistha, jyestha, ksepa = triple
    step = abs(ksepa)
    if (kanistha * m + jyestha) % step:
        raise ValueError(f"multiplier {m} does not divide out for triple {triple}")
    return (
        (kanistha * m + jyestha) // step,
        (jyestha * m + n * kanistha) // step,
        (m * m - n) // ksepa,
    )


def chakravala(n: int, *, shortcut: bool = True, start: Triple | None = None) -> ChakravalaRecord:
    """Solve ``x^2 - n*y^2 = 1`` by the cyclic method; the solution is ``(y, x, 1)``.

    With ``shortcut=True`` the cycle stops at a ksepa of -1, 2, -2, 4 or -4 and the
    answer is completed by composition, as in Bhaskara II's examples. With
    ``shortcut=False`` the cycle runs until the ksepa is 1.

    A ``start`` triple needs positive roots with no common factor, as in Bhaskara
    II's starts, so that every round divides out exactly.

    Raises ``ValueError`` when ``n`` is not a positive non-square, the cases with
    no solution in positive whole numbers, or when ``start`` breaks the rule above.
    """
    _check_n(n)
    triple = start if start is not None else starting_triple(n)
    _check_triple(triple, n)
    if triple[0] < 1 or triple[1] < 1 or gcd(triple[0], triple[1]) != 1:
        raise ValueError(f"start roots must be positive and coprime, got {triple}")
    record = ChakravalaRecord(n=n, triples=[triple])
    while triple[2] != 1 and not (shortcut and triple[2] in SHORTCUT_KSEPAS):
        m = choose_multiplier(triple, n)
        triple = chakravala_step(triple, n, m)
        record.multipliers.append(m)
        record.triples.append(triple)
    record.finished_by_bhavana = triple[2] != 1
    record.solution = complete_by_bhavana(triple, n)
    return record


def complete_by_bhavana(triple: Triple, n: int) -> Triple:
    """Turn a triple with ksepa 1, -1, 2, -2, 4 or -4 into one with ksepa 1 (section 86).

    Ksepa -1: compose the triple with itself. Ksepa 2 or -2: compose with itself
    to get ksepa 4, then divide both roots by 2 (section 79). Ksepa 4 or -4:
    divide both roots by 2 and, when that leaves fractions, keep composing with
    the halved triple until the roots are whole and the ksepa is 1, the route
    Bhaskara II takes for N = 61.
    """
    _check_triple(triple, n)
    ksepa = triple[2]
    if ksepa == 1:
        return triple
    if ksepa == -1:
        return bhavana(triple, triple, n)
    if abs(ksepa) == 2:
        k, j, _ = bhavana(triple, triple, n)
        return k // 2, j // 2, 1
    if abs(ksepa) == 4:
        return _complete_from_four(triple, n)
    raise ValueError(f"composition completes only ksepa 1, -1, 2, -2, 4 or -4, got {ksepa}")


def _complete_from_four(triple: Triple, n: int) -> Triple:
    """Halve a ksepa-4 triple and compose with the half until the roots are whole with ksepa 1."""
    kanistha, jyestha, ksepa = triple
    half = (Fraction(kanistha, 2), Fraction(jyestha, 2), ksepa // 4)
    power = half
    # A power of the halved triple always has whole roots; for N = 61 it is the sixth.
    while not (power[2] == 1 and power[0].denominator == 1 and power[1].denominator == 1):
        power = bhavana(power, half, n)
    return int(power[0]), int(power[1]), 1


def _check_n(n: int) -> None:
    """Raise ``ValueError`` unless ``n`` is a positive whole number that is not a square."""
    if n < 2 or isqrt(n) ** 2 == n:
        raise ValueError(f"n must be a positive non-square, got {n}")


def _check_triple(triple: Triple, n: int) -> None:
    """Raise ``ValueError`` unless ``n * kanistha^2 + ksepa == jyestha^2`` and ksepa is not 0."""
    kanistha, jyestha, ksepa = triple
    if ksepa == 0 or n * kanistha * kanistha + ksepa != jyestha * jyestha:
        raise ValueError(f"{triple} is not a triple for n = {n}")


def pell_continued_fraction(n: int) -> tuple[int, int, int]:
    """Fundamental solution of ``x^2 - n*y^2 = 1`` from the continued fraction of sqrt(n).

    Returns ``(x, y, steps)``, where ``steps`` counts the partial quotients
    computed after the first, until a convergent satisfies the equation.
    """
    _check_n(n)
    a0 = isqrt(n)
    m, d, a = 0, 1, a0
    p_prev, p = 1, a0
    q_prev, q = 0, 1
    steps = 0
    while p * p - n * q * q != 1:
        m = d * a - m
        d = (n - m * m) // d
        a = (a0 + m) // d
        p_prev, p = p, a * p + p_prev
        q_prev, q = q, a * q + q_prev
        steps += 1
    return p, q, steps
