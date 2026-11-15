"""Place-value digits in any base, shared by the algorism (base 10) and Maya (base 20) modules.

A number in base ``b`` is a list of digits, each from 0 to ``b - 1``, worth
``d[0] * b^(k-1) + ... + d[k-1] * b^0``. Lists here are most significant digit
first, the order a number is written in our script.

1. Write a number: divide by the base again and again; the remainders, read
   backwards, are the digits.
2. Read a number: multiply the running value by the base and add the next digit.
3. Add column by column: sum each column, then carry every ``b`` in a column as 1
   into the column to its left, starting from the right.
"""

from __future__ import annotations

from collections.abc import Sequence

from ancient_algorithms._checks import check_at_least

__all__ = ["check_digits", "to_digits", "from_digits", "pad", "trim", "carry"]


def check_digits(digits: Sequence[int], base: int) -> None:
    """Raise ``ValueError`` unless ``base >= 2`` and ``digits`` is a non-empty digit list in it."""
    check_at_least("base", base, 2)
    if not digits:
        raise ValueError("a number needs at least 1 digit, got []")
    for digit in digits:
        if not 0 <= digit < base:
            raise ValueError(f"digits in base {base} are 0 to {base - 1}, got {digit}")


def to_digits(n: int, base: int) -> list[int]:
    """Digits of ``n`` in ``base``, most significant first; 0 is ``[0]``."""
    check_at_least("base", base, 2)
    check_at_least("n", n, 0)
    digits = []
    while True:
        n, digit = divmod(n, base)
        digits.append(digit)
        if n == 0:
            return digits[::-1]


def from_digits(digits: Sequence[int], base: int) -> int:
    """The number written by ``digits`` in ``base``, most significant first."""
    check_digits(digits, base)
    value = 0
    for digit in digits:
        value = value * base + digit
    return value


def pad(digits: Sequence[int], width: int) -> list[int]:
    """``digits`` with zeros added on the left up to ``width`` digits."""
    return [0] * (width - len(digits)) + list(digits)


def trim(digits: Sequence[int]) -> list[int]:
    """``digits`` without leading zeros, keeping at least 1 digit."""
    if not digits:
        raise ValueError("need at least 1 digit")
    start = 0
    while start < len(digits) - 1 and digits[start] == 0:
        start += 1
    return list(digits[start:])


def carry(columns: Sequence[int], base: int) -> list[int]:
    """Digits of a number given as column totals of any size, most significant first.

    Works from the right, passing ``total // base`` to the next column left.
    """
    check_at_least("base", base, 2)
    digits, carried = [], 0
    for total in reversed(columns):
        check_at_least("a column total", total, 0)
        carried, digit = divmod(total + carried, base)
        digits.append(digit)
    while carried:
        carried, digit = divmod(carried, base)
        digits.append(digit)
    return trim(digits[::-1] or [0])
