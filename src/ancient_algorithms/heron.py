"""Heron's method for square roots, Metrica I.8 (Heron of Alexandria, c. 1st century CE).

The date rests on O. Neugebauer's 1938 match of an eclipse in Heron's Dioptra
with the eclipse of 62 CE; T. L. Heath (1921), before that, placed Heron in the
3rd century CE. The text follows H. Schöne's Greek edition, Heronis Alexandrini
opera, vol. 3 (Teubner, 1903), pp. 18.22 to 20.5, from a Constantinople manuscript,
and T. L. Heath's English, A History of Greek Mathematics, vol. 2 (Oxford, 1921),
p. 324. Heron needs the side of 720 for the area of a triangle with sides 7, 8
and 9. Heron calls the square root the side (pleura, πλευρά) and the error the
difference (diaphoron, διάφορον), measured on the square.

1. Take the square number nearest to the given number (Heron: "the square that
   comes close to 720 is 729") and its side, 27.
2. Divide the given number by that side: 720 / 27 = 26 2/3.
3. Add the side and halve: (27 + 26 2/3) / 2 = 26 1/2 1/3.
4. Square the result to check it: 720 1/36, so the difference is 1/36.
5. For a smaller difference, put the square just found, 720 1/36, in place of
   729, and do the same again.

Heron writes 26 2/3 as "26 and 2 thirds" and 26 5/6 as a sum of unit fractions,
26 1/2 1/3. Steps 2 and 3 are ``heron_steps`` from ``babylonian_sqrt``, reused
here. The modern counterpart, Newton's method on ``x*x - n``, is at the end.
"""

from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from math import isqrt

from ancient_algorithms import precision
from ancient_algorithms._checks import check_at_least
from ancient_algorithms.babylonian_sqrt import heron_steps
from ancient_algorithms.place_value import to_digits

__all__ = [
    "nearest_square_side",
    "heron_sqrt",
    "difference",
    "unit_fractions",
    "correct_decimals",
    "newton_step",
]

METRICA_NUMBER = 720
"""The number whose side Heron finds in Metrica I.8: the squared area of the 7, 8, 9 triangle."""


def nearest_square_side(n: int) -> int:
    """Side of the square number nearest to ``n``, Heron's starting value."""
    check_at_least("n", n, 1)
    below = isqrt(n)
    above = below + 1
    return below if n - below * below < above * above - n else above


def heron_sqrt(n: int, steps: int) -> list[Fraction]:
    """Heron's approximations to the side of ``n``: the starting side, then ``steps`` rounds."""
    check_at_least("steps", steps, 0)
    return heron_steps(n, Fraction(nearest_square_side(n)), steps)


def difference(n: int, side: Fraction) -> Fraction:
    """Heron's check: the square of ``side`` less ``n``."""
    return side * side - n


def unit_fractions(x: Fraction) -> tuple[int, tuple[int, ...]]:
    """``x`` as a whole number and distinct unit fractions, greedily: 26 5/6 is 26 1/2 1/3."""
    if x < 0:
        raise ValueError(f"x must be at least 0, got {x}")
    whole = x.numerator // x.denominator
    rest = x - whole
    denominators: list[int] = []
    while rest:
        d = -(-rest.denominator // rest.numerator)  # the largest unit fraction that fits
        denominators.append(d)
        rest -= Fraction(1, d)
    return whole, tuple(denominators)


def correct_decimals(n: int, side: Fraction, limit: int = 1000) -> int:
    """Correct decimal places of ``side`` as the side of ``n``, from 0 up to ``limit``."""
    check_at_least("n", n, 1)
    check_at_least("limit", limit, 0)
    with localcontext() as ctx:
        ctx.prec = limit + len(to_digits(isqrt(n), 10)) + precision.GUARD_DIGITS
        exact = Decimal(n).sqrt()
        approx = Decimal(side.numerator) / Decimal(side.denominator)
    return precision.correct_decimals(approx, exact, limit)


def newton_step(n: int, x: Fraction) -> Fraction:
    """1 step of Newton's method on ``f(x) = x*x - n``: ``x - f(x) / f'(x)``."""
    return x - (x * x - n) / (2 * x)
