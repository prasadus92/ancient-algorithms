"""The square root of 2 on YBC 7289, in base 60.

YBC 7289 is an Old Babylonian school tablet (c. 1800 to 1600 BCE) in the Yale
Babylonian Collection. It shows a square with the number 30 on one side and 2
numbers along the diagonal:

    1;24,51,10   = 1 + 24/60 + 51/60^2 + 10/60^3, close to sqrt(2)
    42;25,35     = 30 times that number

Base-60 numbers on the tablet carry no mark for where the whole part ends. Read
the side as 30, and 42;25,35 is the length of the diagonal. Read it as 0;30, and
the third number is 0;42,25,35, close to 1/sqrt(2). Both readings fit the digits.

The tablet records the values and does not say how they were computed. Fowler and
Robson (Historia Mathematica 25, 1998) discuss which methods could produce them.
The averaging iteration

    x_next = (x + N / x) / 2

is written out in Heron of Alexandria's Metrica (1st century CE) and is commonly
called the Babylonian method. The tablet's 1;24,51,10 is sqrt(2) truncated to 3
sexagesimal places. 2 steps of the iteration from 3/2 give 577/408, which also
truncates to 1;24,51,10, so the iteration is a way to reach the tablet's value.
Agreement of the digits does not show which method the scribe used.
"""

from __future__ import annotations

from fractions import Fraction

__all__ = [
    "Sexagesimal",
    "to_sexagesimal",
    "from_sexagesimal",
    "parse_sexagesimal",
    "heron_steps",
    "YBC7289_ROOT2",
    "YBC7289_SIDE",
    "YBC7289_DIAGONAL",
    "format_sexagesimal",
]

Sexagesimal = tuple[int, tuple[int, ...]]


def to_sexagesimal(x: Fraction | int, places: int) -> Sexagesimal:
    """Truncate a non-negative number to ``places`` base-60 fractional digits."""
    x = Fraction(x)
    if x < 0:
        raise ValueError("only non-negative values")
    whole = x.numerator // x.denominator
    fraction = x - whole
    digits = []
    for _ in range(places):
        fraction *= 60
        digit = fraction.numerator // fraction.denominator
        digits.append(digit)
        fraction -= digit
    return whole, tuple(digits)


def from_sexagesimal(value: Sexagesimal) -> Fraction:
    """Exact value of ``(whole, (d1, d2, ...))``."""
    whole, digits = value
    total = Fraction(whole)
    place = Fraction(1)
    for digit in digits:
        if not 0 <= digit < 60:
            raise ValueError(f"sexagesimal digit out of range: {digit}")
        place /= 60
        total += digit * place
    return total


def parse_sexagesimal(text: str) -> Fraction:
    """Parse the modern notation ``"1;24,51,10"`` into an exact fraction."""
    if text.strip().startswith("-"):
        raise ValueError("only non-negative values")
    whole, _, fraction = text.partition(";")
    digits = tuple(int(d) for d in fraction.split(",")) if fraction else ()
    return from_sexagesimal((int(whole), digits))


def format_sexagesimal(value: Sexagesimal) -> str:
    """Modern notation, for example ``1;24,51,10``."""
    whole, digits = value
    return f"{whole};" + ",".join(str(d) for d in digits) if digits else str(whole)


def heron_steps(square: int | Fraction, start: Fraction, steps: int) -> list[Fraction]:
    """Exact approximations of sqrt(square) by x -> (x + square/x) / 2, starting at ``start``."""
    square = Fraction(square)
    approximations = [Fraction(start)]
    for _ in range(steps):
        x = approximations[-1]
        approximations.append((x + square / x) / 2)
    return approximations


YBC7289_ROOT2 = parse_sexagesimal("1;24,51,10")
YBC7289_SIDE = Fraction(30)
YBC7289_DIAGONAL = parse_sexagesimal("42;25,35")
