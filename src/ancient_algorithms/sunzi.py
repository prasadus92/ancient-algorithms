"""The remainder problem of the Sunzi Suanjing (孫子算經, Master Sun's Mathematical Manual).

The text is usually dated to the 3rd to 5th century CE, and the date is uncertain. The problem
is in the third juan (卷下), usually cited as problem 26; it is the 25th in the edition read
here. The reading follows the Siku Quanshu copy, rebuilt from the Yongle dadian, as
transcribed on Chinese Wikisource, the edition available in full:

    今有物，不知其數。三三數之，賸二；五五數之，賸三；七七數之，賸二。問：物幾何？答曰：二十三。

The recipe (術), in the order the text gives it:

1. For each 1 left over when counting by 3s, set down 70; by 5s, set down 21; by 7s, set down 15.
2. Add what was set down. For remainders 2, 3 and 2 that is 140 + 63 + 30 = 233.
3. While the sum is 106 or more, take away 105. The worked line takes away 210 at once,
   leaving 23.

The text does not say where 70, 21 and 15 come from. Each is a multiple of the other 2
divisors that leaves 1 with its own divisor. ``sunzi_multipliers`` builds such numbers for any
pairwise coprime divisors, and ``sunzi_general`` adds remainder times multiplier: the
sum-of-products form of the Chinese remainder theorem, as Gauss stated it in 1801. The
incremental form, which folds in 1 congruence at a time, is ``crt`` in
``ancient_algorithms.kuttaka``, and the tests compare the 2.
"""

from __future__ import annotations

from math import gcd, prod

from ancient_algorithms.kuttaka import _check_remainders, mod_inverse_euclid

__all__ = [
    "SUNZI_DIVISORS",
    "SUNZI_MULTIPLIERS",
    "SUNZI_PERIOD",
    "sunzi_recipe",
    "sunzi_multipliers",
    "sunzi_general",
]

SUNZI_DIVISORS = (3, 5, 7)
"""The 3 counts of the problem: by 3s (三三數之), by 5s and by 7s."""

SUNZI_MULTIPLIERS = (70, 21, 15)
"""The numbers the recipe sets down for each 1 left over by 3s, 5s and 7s."""

SUNZI_PERIOD = 105
"""The number taken away (一百五), the product 3 * 5 * 7."""


def sunzi_recipe(by_threes: int, by_fives: int, by_sevens: int) -> int:
    """The number leaving the given remainders by 3s, 5s and 7s, by Sunzi's recipe as stated."""
    remainders = (by_threes, by_fives, by_sevens)
    _check_remainders(list(zip(remainders, SUNZI_DIVISORS, strict=True)))
    total = sum(r * m for r, m in zip(remainders, SUNZI_MULTIPLIERS, strict=True))
    # "一百六以上，以一百五減之": 106 or more, take away 105.
    while total >= SUNZI_PERIOD + 1:
        total -= SUNZI_PERIOD
    return total


def sunzi_multipliers(divisors: list[int] | tuple[int, ...]) -> list[int]:
    """For each divisor, the multiple of all the others that leaves 1 with it.

    For 3, 5 and 7 these are Sunzi's 70, 21 and 15. Raises ``ValueError`` unless every divisor
    is at least 2 and no 2 share a factor.
    """
    _check_pairwise_coprime(divisors)
    period = prod(divisors)
    multipliers = []
    for divisor in divisors:
        others = period // divisor
        multipliers.append(others * mod_inverse_euclid(others, divisor))
    return multipliers


def sunzi_general(pairs: list[tuple[int, int]]) -> int:
    """Smallest ``N >= 0`` leaving each ``remainder`` with its ``divisor``, by Sunzi's recipe.

    ``pairs`` holds ``(remainder, divisor)``. Each remainder is multiplied by its divisor's
    multiplier, the products are added, and the product of the divisors is taken away as often
    as it goes. Raises ``ValueError`` unless every divisor is at least 2, no 2 divisors share a
    factor, and each remainder is smaller than its divisor.
    """
    _check_remainders(pairs)
    divisors = [divisor for _, divisor in pairs]
    multipliers = sunzi_multipliers(divisors)
    total = sum(r * m for (r, _), m in zip(pairs, multipliers, strict=True))
    return total % prod(divisors)


def _shared_factor(divisors: list[int] | tuple[int, ...]) -> tuple[int, int] | None:
    """The first 2 divisors that share a factor, or ``None`` when they are pairwise coprime."""
    for i, a in enumerate(divisors):
        for b in divisors[i + 1 :]:
            if gcd(a, b) != 1:
                return a, b
    return None


def _check_pairwise_coprime(divisors: list[int] | tuple[int, ...]) -> None:
    """Raise ``ValueError`` unless every divisor is at least 2 and no 2 share a factor."""
    if any(d < 2 for d in divisors):
        raise ValueError(f"each divisor must be at least 2, got {list(divisors)}")
    pair = _shared_factor(divisors)
    if pair is not None:
        a, b = pair
        raise ValueError(f"the divisors {a} and {b} share the factor {gcd(a, b)}")
