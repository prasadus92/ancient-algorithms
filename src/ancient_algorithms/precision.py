"""Correct decimal places of an approximation, shared by the Madhava and Heron modules.

1. Take the absolute error between the approximation and the exact value.
2. The correct decimal places are floor(-log10 of the error), at least 0.
3. Stop at a cap, the number of places the exact value is known to.
"""

from __future__ import annotations

from decimal import ROUND_FLOOR, Decimal, localcontext

from ancient_algorithms._checks import check_at_least

__all__ = ["GUARD_DIGITS", "correct_decimals"]

GUARD_DIGITS = 10
"""Extra significant digits carried so the error is not lost to rounding."""


def correct_decimals(approx: Decimal, exact: Decimal, cap: int) -> int:
    """``floor(-log10 |approx - exact|)``, from 0 up to ``cap``; ``cap`` when the 2 are equal."""
    check_at_least("cap", cap, 0)
    with localcontext() as ctx:
        ctx.prec = cap + GUARD_DIGITS
        error = abs(approx - exact)
        if error == 0:
            return cap
        places = int((-error.log10()).to_integral_value(rounding=ROUND_FLOOR))
    return min(cap, max(0, places))
