"""Madhava's series for pi with the end corrections, and a convergence benchmark.

Later Kerala texts attribute to Madhava of Sangamagrama (c. 1340 to 1425) the series

    pi/4 = 1 - 1/3 + 1/5 - 1/7 + ...

together with corrections that estimate the tail left after stopping at term n.
No surviving work by Madhava contains these series. They reach us through 16th-century
Kerala works: Jyesthadeva's Yuktibhasa derives them, and Shankara Variyar's
commentaries Yuktidipika and Kriyakramakari quote verses that they credit to Madhava.

With S_n the sum of the first n terms (last denominator 2n - 1), the 3
corrections, written in n, are

    f1(n) = 1 / (4n)
    f2(n) = n / (4n^2 + 1)
    f3(n) = (n^2 + 1) / (4n^3 + 5n)

and pi/4 is approximated by S_n + (-1)^n f(n). The error falls roughly as n^-3,
n^-5 and n^-7 for the 3 corrections, against n^-1 for the bare series.

All arithmetic uses ``decimal.Decimal`` at a caller-chosen precision.
"""

from __future__ import annotations

from decimal import Decimal, localcontext

__all__ = [
    "PI_100",
    "partial_sum",
    "correction",
    "madhava_pi",
    "madhava_sqrt12_pi",
    "machin_pi",
    "correct_digits",
]

# 100 decimal places of pi, used as the reference for error and digit counts.
PI_100 = Decimal(
    "3.14159265358979323846264338327950288419716939937510"
    "58209749445923078164062862089986280348253421170679"
)


def partial_sum(n: int, prec: int = 60) -> Decimal:
    """1 - 1/3 + ... with n terms, the last one being +/- 1/(2n - 1)."""
    if n < 0:
        raise ValueError("n must be non-negative")
    with localcontext() as ctx:
        ctx.prec = prec
        total = Decimal(0)
        for k in range(n):
            term = Decimal(1) / (2 * k + 1)
            total += term if k % 2 == 0 else -term
        return +total


def correction(n: int, order: int, prec: int = 60) -> Decimal:
    """Madhava's end correction of the given order (0, 1, 2 or 3) after n terms."""
    if n < 1 and order:
        raise ValueError("corrections need n >= 1")
    with localcontext() as ctx:
        ctx.prec = prec
        d = Decimal(n)
        if order == 0:
            return Decimal(0)
        if order == 1:
            return 1 / (4 * d)
        if order == 2:
            return d / (4 * d * d + 1)
        if order == 3:
            return (d * d + 1) / (4 * d**3 + 5 * d)
    raise ValueError("order must be 0, 1, 2 or 3")


def madhava_pi(n: int, order: int = 0, prec: int = 60) -> Decimal:
    """Approximate pi from n terms of the series plus the chosen end correction."""
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n}")
    with localcontext() as ctx:
        ctx.prec = prec
        sign = 1 if n % 2 == 0 else -1
        return 4 * (partial_sum(n, prec) + sign * correction(n, order, prec))


def madhava_sqrt12_pi(n: int, prec: int = 60) -> Decimal:
    """pi = sqrt(12) * (1 - 1/(3*3) + 1/(5*3^2) - ...), also credited to Madhava."""
    with localcontext() as ctx:
        ctx.prec = prec
        total = Decimal(0)
        power = Decimal(1)
        for k in range(n):
            term = 1 / ((2 * k + 1) * power)
            total += term if k % 2 == 0 else -term
            power *= 3
        return Decimal(12).sqrt() * total


def _arctan_inverse(x: int, terms: int) -> Decimal:
    """arctan(1/x) by its Taylor series, ``terms`` terms."""
    total = Decimal(0)
    power = Decimal(x)
    x2 = x * x
    for k in range(terms):
        term = 1 / ((2 * k + 1) * power)
        total += term if k % 2 == 0 else -term
        power *= x2
    return total


def machin_pi(n: int, prec: int = 60) -> Decimal:
    """Machin (1706): pi/4 = 4 arctan(1/5) - arctan(1/239), n terms of each series."""
    with localcontext() as ctx:
        ctx.prec = prec
        return 4 * (4 * _arctan_inverse(5, n) - _arctan_inverse(239, n))


def correct_digits(approx: Decimal) -> int:
    """Number of correct decimal places, measured as floor(-log10 |error|)."""
    with localcontext() as ctx:
        ctx.prec = 110
        err = abs(approx - PI_100)
        if err == 0:
            return 100
        return max(0, int((-err.log10()).to_integral_value(rounding="ROUND_FLOOR")))
