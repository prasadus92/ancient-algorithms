"""Euclid's algorithm, Elements Book VII, propositions 1 and 2 (c. 300 BCE).

The Greek follows J. L. Heiberg's edition (Teubner, 1883 to 1888) and the English
follows T. L. Heath, The Thirteen Books of Euclid's Elements, vol. 2 (Cambridge,
1908), pp. 296 to 299. Euclid states the method as anthyphairesis
(ἀνθυφαίρεσις), "subtraction in turn": "the less being continually subtracted
in turn from the greater". He never divides. Each stage, "let CD, measuring BF,
leave FA less than itself", lays the smaller number off along the greater as
many times as it fits, which is repeated subtraction.

Euclid stops when the number left measures the one before it. Testing "measures"
by subtraction alone means subtracting until the 2 numbers are equal, so the code
stops there, at the pair ``(g, g)``.

1. Set out 2 numbers. Subtract the less from the greater, again and again, while
   the greater is still the greater.
2. Subtract what is left from the number before it in the same way, and go on
   in turn.
3. If a unit (monas, μονάς) is left, the numbers are prime to one another
   (VII.1).
4. Otherwise the number left that measures the one before it is their greatest
   common measure (megiston koinon metron, μέγιστον κοινὸν μέτρον) (VII.2).

Euclid's numbers are multitudes of units (VII, Def. 2), so they start at 2. The
code also accepts 1, the unit, so that VII.1 can end on it.

The division form used today, and G. Lamé's 1844 bound on its number of
divisions (Comptes rendus 19, pp. 867 to 870), are at the end of the module.
"""

from __future__ import annotations

from ancient_algorithms._checks import check_at_least

__all__ = [
    "anthyphairesis",
    "prime_to_one_another",
    "greatest_common_measure",
    "subtraction_count",
    "division_quotients",
    "division_count",
    "lame_bound",
    "fibonacci_pair",
]

LAME_FACTOR = 5
"""Lamé: the divisions number at most 5 times the decimal digits of the smaller number."""


def anthyphairesis(a: int, b: int) -> list[tuple[int, int]]:
    """Every pair Euclid's subtraction in turn passes through, from ``(a, b)`` to ``(g, g)``."""
    check_at_least("a", a, 1)
    check_at_least("b", b, 1)
    pairs = [(a, b)]
    while a != b:
        if a > b:
            a -= b
        else:
            b -= a
        pairs.append((a, b))
    return pairs


def prime_to_one_another(a: int, b: int) -> bool:
    """VII.1: whether subtraction in turn leaves a unit, so only the unit measures both."""
    return greatest_common_measure(a, b) == 1


def greatest_common_measure(a: int, b: int) -> int:
    """VII.2: the greatest common measure of ``a`` and ``b``, by subtraction in turn."""
    last, _ = anthyphairesis(a, b)[-1]
    return last


def subtraction_count(a: int, b: int) -> int:
    """Number of subtractions Euclid's method makes before the 2 numbers are equal."""
    return len(anthyphairesis(a, b)) - 1


def _fibonacci(n: int) -> int:
    """F(n) with F(1) = F(2) = 1."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def division_quotients(a: int, b: int) -> list[int]:
    """Quotients of the division form, larger number first; they are the continued fraction."""
    check_at_least("a", a, 1)
    check_at_least("b", b, 1)
    a, b = max(a, b), min(a, b)
    quotients = []
    while b:
        q, r = divmod(a, b)
        quotients.append(q)
        a, b = b, r
    return quotients


def division_count(a: int, b: int) -> int:
    """Number of divisions the division form makes, the last one leaving remainder 0."""
    return len(division_quotients(a, b))


def lame_bound(a: int, b: int) -> int:
    """Lamé's 1844 bound on ``division_count(a, b)``: 5 times the digits of the smaller number."""
    check_at_least("a", a, 1)
    check_at_least("b", b, 1)
    return LAME_FACTOR * len(str(min(a, b)))


def fibonacci_pair(n: int) -> tuple[int, int]:
    """``(F(n+2), F(n+1))``, the smallest pair that needs ``n`` divisions."""
    check_at_least("n", n, 1)
    return _fibonacci(n + 2), _fibonacci(n + 1)
