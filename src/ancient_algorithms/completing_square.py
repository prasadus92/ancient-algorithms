"""Al-Khwarizmi's 6 types of equation and his completion of the square (c. 820 CE).

Source: Muhammad ibn Musa al-Khwarizmi, al-Kitab al-mukhtasar fi hisab al-jabr
wa'l-muqabala ("The compendious book on calculating by completion and
reduction"), written in Baghdad for the caliph al-Ma'mun (reigned 813 to 833).
Page numbers refer to F. Rosen, The Algebra of Mohammed ben Musa (London, 1831),
the English translation with the Arabic text.

The date c. 820 is an inference. The preface addresses al-Ma'mun as caliph, which
places the book in his reign, 813 to 833 (Folkerts, Science in Context 14, 2001).
Al-Khwarizmi's arithmetic, c. 825 by Folkerts's dating, cites the Algebra, so the
Algebra came first. No source gives a year.

Al-Khwarizmi works with 3 kinds of number: roots (the unknown, x), squares (x^2)
and simple numbers. Every coefficient is positive, so an equation is one of 6
types (Rosen pp. 5 to 13):

1. squares equal roots          c x^2 = b x
2. squares equal numbers        c x^2 = a
3. roots equal numbers          b x = a
4. squares and roots equal numbers   c x^2 + b x = a
5. squares and numbers equal roots   c x^2 + a = b x
6. roots and numbers equal squares   c x^2 = b x + a

His rule for the 3 compound types, after reducing to 1 square:

1. Divide everything by the number of squares: "reduce them to one single square".
2. Halve the number of roots and multiply the half by itself.
3. Type 4: add the number, take the root, subtract the half. Type 6: add the
   number, take the root, add the half. Type 5: subtract the number; if nothing
   is left over the half is the answer, if the product is the smaller the problem
   is "impossible", otherwise take the root and subtract it from the half or add
   it to the half: both answers serve.

The geometric proof for type 4 (Rosen pp. 13 to 16) puts a strip of breadth b/4 on
each of the 4 sides of the square and fills the 4 corners with squares of side
b/4. He gives a second figure with 2 strips of breadth b/2 and 1 corner square.
Al-Khwarizmi gives positive answers only and never x = 0.

Every function takes keyword arguments named after his 3 kinds of number
(``squares``, ``roots``, ``number``), so that a coefficient cannot land in the
wrong place and solve a different equation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt, sqrt

__all__ = [
    "Number",
    "GreatSquare",
    "one_square",
    "squares_equal_roots",
    "squares_equal_numbers",
    "roots_equal_numbers",
    "squares_and_roots_equal_numbers",
    "squares_and_numbers_equal_roots",
    "roots_and_numbers_equal_squares",
    "complete_the_square",
    "quadratic_formula",
]

Number = Fraction | float
"""A value al-Khwarizmi can name exactly (a fraction), or a float when the root is irrational."""


@dataclass
class GreatSquare:
    """The figure for "a square and ``roots`` roots equal ``number``", step by step."""

    roots: Fraction
    number: Fraction
    strips: int
    breadth: Fraction
    corners: Fraction
    area: Fraction
    side: Number
    root: Number


def one_square(*, squares: Number, roots: Number, number: Number) -> tuple[Fraction, Fraction]:
    """Roots and number after dividing through by the number of squares."""
    squares = _positive(squares, "squares")
    return Fraction(roots) / squares, Fraction(number) / squares


def squares_equal_roots(*, squares: Number, roots: Number) -> Fraction:
    """Root of ``squares * x^2 = roots * x``, for example 5 for "a square equals 5 roots"."""
    return _positive(roots, "roots") / _positive(squares, "squares")


def squares_equal_numbers(*, squares: Number, number: Number) -> Number:
    """Root of ``squares * x^2 = number``."""
    return _root(_positive(number, "number") / _positive(squares, "squares"))


def roots_equal_numbers(*, roots: Number, number: Number) -> Fraction:
    """Root of ``roots * x = number``."""
    return _positive(number, "number") / _positive(roots, "roots")


def squares_and_roots_equal_numbers(*, squares: Number, roots: Number, number: Number) -> Number:
    """Root of ``squares * x^2 + roots * x = number``: halve, square, add, take root, subtract."""
    b, a = one_square(
        squares=squares, roots=_positive(roots, "roots"), number=_positive(number, "number")
    )
    half = b / 2
    return _root(half * half + a) - half


def squares_and_numbers_equal_roots(
    *, squares: Number, roots: Number, number: Number
) -> tuple[Number, ...]:
    """Roots of ``squares * x^2 + number = roots * x``: 0, 1 or 2 positive answers.

    Halve the roots and square the half. If that is less than the number, the
    problem is impossible and the result is empty. If it equals the number, the
    half is the 1 answer. Otherwise the half minus and plus the root of the
    difference are both answers.
    """
    b, a = one_square(
        squares=squares, roots=_positive(roots, "roots"), number=_positive(number, "number")
    )
    half = b / 2
    excess = half * half - a
    if excess < 0:
        return ()
    if excess == 0:
        return (half,)
    gap = _root(excess)
    return (half - gap, half + gap)


def roots_and_numbers_equal_squares(*, squares: Number, roots: Number, number: Number) -> Number:
    """Root of ``squares * x^2 = roots * x + number``: halve, square, add, take root, add."""
    b, a = one_square(
        squares=squares, roots=_positive(roots, "roots"), number=_positive(number, "number")
    )
    half = b / 2
    return _root(half * half + a) + half


def complete_the_square(*, roots: Number, number: Number, strips: int = 4) -> GreatSquare:
    """Al-Khwarizmi's figure for ``x^2 + roots * x = number``, with 4 strips or 2.

    Each strip is ``roots / strips`` wide and as long as the unknown side. The
    corners left empty are filled with squares of side equal to the strip's
    breadth: 4 of them for 4 strips, 1 for 2 strips. Both fills add (roots/2)^2.
    """
    if strips not in (2, 4):
        raise ValueError(f"al-Khwarizmi uses 4 strips or 2, got {strips}")
    b, a = _positive(roots, "roots"), _positive(number, "number")
    breadth = b / strips
    corner_count = 4 if strips == 4 else 1
    corners = corner_count * breadth * breadth
    area = a + corners
    side = _root(area)
    cut_off = b / 2  # 2 breadths of b/4 from the 2 ends, or 1 breadth of b/2
    return GreatSquare(b, a, strips, breadth, corners, area, side, side - cut_off)


def _positive(value: Number, name: str) -> Fraction:
    """``value`` as a Fraction, or ``ValueError`` if it is not positive."""
    value = Fraction(value)
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _root(value: Fraction) -> Number:
    """Square root, exact when ``value`` is the square of a fraction."""
    top, bottom = isqrt(value.numerator), isqrt(value.denominator)
    if top * top == value.numerator and bottom * bottom == value.denominator:
        return Fraction(top, bottom)
    return sqrt(value)


def quadratic_formula(a: float, b: float, c: float) -> tuple[float, ...]:
    """Real roots of ``a*x^2 + b*x + c = 0``, ascending, by the modern formula."""
    if a == 0:
        raise ValueError("a must not be 0")
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return ()
    if discriminant == 0:
        return (-b / (2 * a),)
    return tuple(sorted(((-b - sqrt(discriminant)) / (2 * a), (-b + sqrt(discriminant)) / (2 * a))))
