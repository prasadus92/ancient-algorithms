"""Pingala's rules for listing and counting metrical patterns, Chandahshastra 8.20-8.34.

Pingala's Chandahshastra (date debated: Shah gives the 2nd century BCE, Plofker
perhaps the 3rd, as reported by Mumford) ends with short rules on patterns of guru
(heavy, written ``g``) and laghu (light, written ``l``) syllables. The sutra text
and numbering follow the 1874 Bibliotheca Indica edition by Visvanatha Sastri, which
prints them with Halayudha's 10th-century commentary, the Mrtasanjivani. Every rule
here follows Halayudha's reading, because the sutras alone do not fix the
procedures. The edition Kulkarni (2017) uses numbers the last sutras 8.34 and 8.35.

1. Prastara, the spread (8.20-8.23): write g over l. For each further syllable,
   write the list so far twice, and add g after each row of the first copy and l
   after each row of the second.
2. Nashta, the lost pattern (8.24-8.25): from a row number, halve it if even and
   write l; if odd, add 1, halve, and write g. Repeat once per syllable.
3. Uddishta, the pointed-out pattern (8.26-8.27): from the last l, moving left,
   start at 1 and double at each syllable, subtracting 1 at each g. The result is
   the row number.
4. Sankhya, the count (8.28-8.31): mark 2 and halve when the syllable count is
   even, mark 0 and subtract 1 when it is odd. From the last mark back, double at
   each 0 and square at each 2, starting from 1.
5. The total for all meters of 1 to n syllables is the count for n, doubled, less 2
   (8.32). The count for n + 1 is the count for n doubled in full (8.33).
6. Meru prastara (Halayudha on 8.34): a triangle of cells whose end cells hold 1
   and whose inner cells hold the sum of the 2 cells above. Row n counts the
   n-syllable patterns with 0, 1, ..., n laghus.

Read with g as 0 and l as 1, the leftmost syllable as the lowest digit, row k of
the prastara is the binary form of k - 1.

The matra (mora-counted) patterns, where g counts 2 and l counts 1, come from later
authors: Virahanka (between 600 and 800 CE) gives the rule that each count is the
sum of the 2 before, and Gopala (before 1135) and Hemacandra (c. 1150) list the
numbers. Dates follow P. Singh, Historia Mathematica 12 (1985).

The binary reading and ``math.comb`` are at the end of the module, for comparison.
"""

from __future__ import annotations

from itertools import pairwise, product
from math import comb

__all__ = [
    "GURU",
    "LAGHU",
    "prastara",
    "nashta",
    "uddishta",
    "sankhya_marks",
    "sankhya",
    "total_through",
    "meru_prastara",
    "lagakriya",
    "matra_prastara",
    "matra_count",
    "binary_row",
    "binary_pattern",
    "modern_prastara",
    "modern_lagakriya",
]

GURU = "g"
"""A heavy syllable, Pingala's ``g`` (guru)."""

LAGHU = "l"
"""A light syllable, Pingala's ``l`` (laghu)."""

HALVED = 2
"""Halayudha's mark for a halving step in the count: "dvir ardhe", 2 when halved."""

LESS_ONE = 0
"""Halayudha's mark for a subtraction step in the count: "rupe shunyam", 0 when 1 is taken off."""


def prastara(n: int) -> list[str]:
    """All ``n``-syllable patterns, in Pingala's order: row 1 is all g, the last row all l."""
    _check_syllables(n)
    rows = [GURU, LAGHU]  # 8.20 dvikau glau: g over l
    # 8.21-8.22: write the list twice, g after each row of the first copy, l after the second.
    for _ in range(n - 1):
        rows = [row + GURU for row in rows] + [row + LAGHU for row in rows]
    return rows


def nashta(row: int, n: int) -> str:
    """The pattern in row ``row`` of the ``n``-syllable prastara, found without writing it out."""
    _check_row(row, n)
    pattern = []
    for _ in range(n):
        if row % 2 == 0:  # 8.24 l ardhe: even, halve and write l
            pattern.append(LAGHU)
            row //= 2
        else:  # 8.25 saike g: odd, add 1, halve and write g
            pattern.append(GURU)
            row = (row + 1) // 2
    return "".join(pattern)


def uddishta(pattern: str) -> int:
    """The row number of ``pattern`` in its prastara, found without writing the prastara out."""
    _check_pattern(pattern)
    last_laghu = pattern.rfind(LAGHU)
    if last_laghu == -1:
        return 1
    row = 1
    # 8.26-8.27 as Halayudha reads them: from the last l, move left, double, 1 off at each g.
    # Syllables after the last l are all g, and 2*1 - 1 leaves 1, so they can be skipped.
    for syllable in reversed(pattern[: last_laghu + 1]):
        row *= 2
        if syllable == GURU:
            row -= 1
    return row


def sankhya_marks(n: int) -> list[int]:
    """Halayudha's marks for counting ``n``-syllable patterns: 2 for a halving, 0 for 1 off."""
    _check_syllables(n)
    marks = []
    while n:
        if n % 2 == 0:
            marks.append(HALVED)
            n //= 2
        else:
            marks.append(LESS_ONE)
            n -= 1
    return marks


def sankhya(n: int) -> int:
    """The number of ``n``-syllable patterns, by Pingala's halving rule (8.28-8.31)."""
    count = 1
    for mark in reversed(sankhya_marks(n)):
        # 8.30 dvih shunye: double at a 0; 8.31 tavad ardhe tad gunitam: square at a 2.
        count = count * 2 if mark == LESS_ONE else count * count
    return count


def total_through(n: int) -> int:
    """The number of patterns of every length from 1 to ``n`` syllables (8.32)."""
    return 2 * sankhya(n) - 2  # dvir dvyunam tadantanam: doubled, less 2


def meru_prastara(n: int) -> list[list[int]]:
    """Halayudha's meru, rows 0 to ``n``: row k counts k-syllable patterns by number of laghus."""
    _check_at_least(n, 0, "n")
    rows = [[1]]
    for _ in range(n):
        above = rows[-1]
        rows.append([1] + [left + right for left, right in pairwise(above)] + [1])
    return rows


def lagakriya(n: int) -> list[int]:
    """How many ``n``-syllable patterns have 0, 1, ..., ``n`` laghus, read from the meru."""
    _check_syllables(n)
    return meru_prastara(n)[n]


def matra_prastara(morae: int) -> list[str]:
    """All patterns worth ``morae`` morae (g = 2, l = 1), in the order Singh (1985) describes."""
    _check_at_least(morae, 1, "morae")
    two_back, one_back = [""], [LAGHU]
    for _ in range(morae - 1):
        two_back, one_back = one_back, [p + GURU for p in two_back] + [p + LAGHU for p in one_back]
    return one_back


def matra_count(morae: int) -> int:
    """The number of patterns worth ``morae`` morae: each count is the sum of the 2 before it."""
    _check_at_least(morae, 1, "morae")
    two_back, one_back = 1, 1
    for _ in range(morae - 1):
        two_back, one_back = one_back, two_back + one_back
    return one_back


def _check_at_least(value: int, minimum: int, name: str) -> None:
    """Raise ``ValueError`` unless ``value`` is at least ``minimum``."""
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")


def _check_syllables(n: int) -> None:
    """Raise ``ValueError`` unless ``n`` is a positive syllable count."""
    _check_at_least(n, 1, "n")


def _check_row(row: int, n: int) -> None:
    """Raise ``ValueError`` unless ``row`` is a row of the ``n``-syllable prastara."""
    _check_syllables(n)
    if not 1 <= row <= 2**n:
        raise ValueError(f"row must be between 1 and {2**n}, got {row}")


def _check_pattern(pattern: str) -> None:
    """Raise ``ValueError`` unless ``pattern`` is a non-empty string of g and l."""
    if not pattern or set(pattern) - {GURU, LAGHU}:
        raise ValueError(f"pattern must be a non-empty string of 'g' and 'l', got {pattern!r}")


def binary_row(pattern: str) -> int:
    """Row number of ``pattern`` read as binary: g = 0, l = 1, leftmost syllable lowest, plus 1."""
    _check_pattern(pattern)
    return int(pattern[::-1].replace(GURU, "0").replace(LAGHU, "1"), 2) + 1


def binary_pattern(row: int, n: int) -> str:
    """The ``n``-syllable pattern whose binary row number is ``row``."""
    _check_row(row, n)
    bits = format(row - 1, f"0{n}b")[::-1]
    return bits.replace("0", GURU).replace("1", LAGHU)


def modern_prastara(n: int) -> list[str]:
    """The same list from ``itertools.product``, which varies the rightmost place fastest."""
    _check_syllables(n)
    return ["".join(reversed(p)) for p in product((GURU, LAGHU), repeat=n)]


def modern_lagakriya(n: int) -> list[int]:
    """Binomial coefficients ``C(n, k)`` for ``k`` from 0 to ``n``."""
    _check_syllables(n)
    return [comb(n, k) for k in range(n + 1)]
