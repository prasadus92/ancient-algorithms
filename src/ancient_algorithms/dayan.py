"""Qin Jiushao's dayan method (大衍總數術), Shushu jiuzhang (數書九章), preface dated 1247.

The general rule and the procedure for the multiplier, the dayan qiuyi shu (大衍求一術, "great
extension method of finding one"), open chapter 1. The reading follows the Siku Quanshu copy
(titled 數學九章, rebuilt from the Yongle dadian, 1784) as transcribed on Chinese Wikisource,
checked against Alexander Wylie's 1852 English account. Qin's own worked problems in that
chapter are the tests: the divination problem (蓍卦發微), the dyke problem (推計土功), the
rice problem (餘米推數) and the couriers problem (程行計地).

The method, with Qin's names:

1. Original numbers (元數): the moduli as given.
2. Definite numbers (定數 or 定母): take the original numbers 2 at a time (連環求等). Divide
   their common measure out of one of them, the one whose quotient is odd (約奇弗約偶, as
   Wylie reads it). If the reduced number still shares a factor with the other, move that
   factor across (續等) until the 2 are coprime. The definite numbers are pairwise coprime,
   each divides its original number, and their product is the least common multiple.
3. Extension mother (衍母): the product of the definite numbers.
4. Extension numbers (衍數): the extension mother divided by each definite number.
5. Remainders (奇): each extension number reduced by its definite number.
6. Multipliers (乘率): for each remainder and definite number, the qiuyi procedure finds the
   number that, times the remainder, leaves 1.
7. Use numbers (用數): each extension number times its multiplier.
8. Total (總數): each given remainder times its use number, added; take away the extension
   mother as often as it goes (滿衍母去之). What is left is the answer.

Qin's text has further steps this module leaves out: a common divisor taken from all the
numbers first (總等), an adjustment of the use numbers (泛用 to 正用), and rules for numbers
with fractions or decimal places. They change neither the definite numbers' product nor the
answer in the problems tested here.

The modern counterpart is ``crt`` in ``ancient_algorithms.kuttaka``, built on ``extended_gcd``.
The tests compare the dayan answers and multipliers with both.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import gcd, prod

__all__ = [
    "QiuyiBoard",
    "DayanRecord",
    "definite_numbers",
    "qiuyi_board",
    "qiuyi",
    "dayan",
]

QiuyiBoard = tuple[int, int, int, int]
"""1 state of the counting board for qiuyi: (upper left, upper right, lower left, lower right)."""


@dataclass
class DayanRecord:
    """1 dayan run, with every intermediate number Qin writes down in his worked solutions."""

    remainders: list[int]
    original: list[int]
    definite: list[int] = field(default_factory=list)
    extension_mother: int = 1
    extension_numbers: list[int] = field(default_factory=list)
    qi: list[int] = field(default_factory=list)
    multipliers: list[int] = field(default_factory=list)
    use_numbers: list[int] = field(default_factory=list)
    total: int = 0
    answer: int = 0


def definite_numbers(original: list[int]) -> list[int]:
    """Qin's definite numbers (定數): coprime divisors of ``original`` whose product is the lcm."""
    if any(m < 1 for m in original):
        raise ValueError(f"each modulus must be at least 1, got {original}")
    numbers = list(original)
    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            numbers[i], numbers[j] = _make_coprime(numbers[i], numbers[j])
    return numbers


def qiuyi_board(qi: int, definite: int) -> list[QiuyiBoard]:
    """Every state of the qiuyi board, from the set-up to the state whose upper right is 1.

    Qin's set-up: the remainder upper right, the definite number lower right, 1 (天元一) upper
    left, the lower left empty. Divide the larger right-hand number by the smaller, in turn;
    each quotient times the left number in the divisor's row is added to the left number in
    the dividend's row. Stop when the upper right is 1; the upper left is the multiplier.
    """
    if definite < 1:
        raise ValueError(f"the definite number must be at least 1, got {definite}")
    if not 1 <= qi <= max(definite - 1, 1):
        raise ValueError(f"the remainder must be 1 to {max(definite - 1, 1)}, got {qi}")
    if gcd(qi, definite) != 1:
        raise ValueError(f"{qi} and {definite} share the factor {gcd(qi, definite)}")
    upper_left, upper_right, lower_left, lower_right = 1, qi, 0, definite
    boards = [(upper_left, upper_right, lower_left, lower_right)]
    while upper_right > 1:
        if lower_right > upper_right:
            q = lower_right // upper_right
            lower_right -= q * upper_right
            lower_left += q * upper_left
        else:
            # "須使右上末後奇一而止": the last quotient leaves 1 in the upper right.
            q = (upper_right - 1) // lower_right
            upper_right -= q * lower_right
            upper_left += q * lower_left
        boards.append((upper_left, upper_right, lower_left, lower_right))
    return boards


def qiuyi(qi: int, definite: int) -> int:
    """Qin's multiplier (乘率): the ``k`` with ``qi * k`` leaving 1 when divided by ``definite``."""
    return qiuyi_board(qi, definite)[-1][0]


def dayan(pairs: list[tuple[int, int]]) -> DayanRecord:
    """Smallest ``N >= 0`` leaving each ``remainder`` with its ``modulus``, by the dayan method.

    ``pairs`` holds ``(remainder, modulus)``. The moduli may share factors. Raises
    ``ValueError`` when the remainders contradict each other on a shared factor.
    """
    if not pairs:
        raise ValueError("need at least one (remainder, modulus) pair")
    for remainder, modulus in pairs:
        if modulus < 1 or not 0 <= remainder < modulus:
            raise ValueError(f"need 0 <= remainder < modulus, got ({remainder}, {modulus})")
    record = DayanRecord(
        remainders=[r for r, _ in pairs],
        original=[m for _, m in pairs],
    )
    record.definite = definite_numbers(record.original)
    record.extension_mother = prod(record.definite)
    record.extension_numbers = [record.extension_mother // d for d in record.definite]
    # A definite number 1 leaves remainder 1 in Qin's divination problem (其一母去衍一十二竒一).
    record.qi = [e % d or d for e, d in zip(record.extension_numbers, record.definite, strict=True)]
    record.multipliers = [qiuyi(q, d) for q, d in zip(record.qi, record.definite, strict=True)]
    record.use_numbers = [
        e * k for e, k in zip(record.extension_numbers, record.multipliers, strict=True)
    ]
    record.total = sum(r * u for r, u in zip(record.remainders, record.use_numbers, strict=True))
    record.answer = record.total % record.extension_mother
    for remainder, modulus in pairs:
        if record.answer % modulus != remainder:
            raise ValueError(
                f"no solution: the remainders disagree on a factor shared with {modulus}"
            )
    return record


def _make_coprime(a: int, b: int) -> tuple[int, int]:
    """Split ``a`` and ``b`` into coprime divisors of each with the same product as their lcm."""
    g = gcd(a, b)
    if g == 1:
        return a, b
    if (a // g) % 2 == 1:
        return _divide_out(a, b, g)
    reduced_b, other_a = _divide_out(b, a, g)
    return other_a, reduced_b


def _divide_out(x: int, y: int, g: int) -> tuple[int, int]:
    """Divide ``g`` out of ``x``, then move each further shared factor (續等) into ``x``."""
    x //= g
    while (k := gcd(x, y)) > 1:
        x, y = x * k, y // k
    return x, y
