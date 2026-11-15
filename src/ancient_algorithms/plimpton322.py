"""Plimpton 322, an Old Babylonian table of right triangles (Larsa, c. 1822 to 1762 BCE).

Source: the clay tablet Plimpton 322, Rare Book and Manuscript Library, Columbia
University (CDLI P254790), first published as text A of Neugebauer and Sachs,
Mathematical Cuneiform Texts (1945). Robson (Historia Mathematica 28, 2001, p. 172)
places it in Larsa and dates it to the 60 years or so before Hammurabi took Larsa in
1762 BCE, from its script and its table format. The date is an inference.

The surviving part has 4 columns and 15 rows. Column I is a squared ratio, columns
II and III are the short side ``b`` and the diagonal ``d`` of a right triangle, and
column IV numbers the rows. The long side ``l`` is not written. ``TABLET`` holds the
tablet's numbers, errors included, as transcribed in Robson 2001, Tables 1 and 2,
checked against Mansfield and Wildberger (Historia Mathematica 44, 2017), Table 1.

The code follows the reciprocal-pair reading of Bruins (1949, 1955) and Robson
(2001), because it accounts for column I, the order of the rows and the heading of
column I. The steps:

1. Take a regular number, the igi (``x``), between 1;48 and 2;24, and its
   reciprocal, the igibi (``1/x``). Regular numbers have only 2, 3 and 5 as prime
   factors, so both have a finite base-60 expansion.
2. Halve their difference and their sum. These are the short side and the
   diagonal of a right triangle whose long side is 1.
3. Square the diagonal. That is column I, which Robson reads as "the takiltum
   (holding square) of the diagonal from which 1 is torn out, so that the short
   side comes up".
4. Multiply the short side and the diagonal by regular factors, read off their
   last base-60 digits, until both are whole. These are columns II and III. The
   product of the factors is the long side.
5. Number the row. Sort the rows by column I, largest first.

Neugebauer and Sachs read the table as built from 2 regular numbers ``p > q``,
with ``b = p^2 - q^2``, ``l = 2pq`` and ``d = p^2 + q^2``. With ``x = p/q`` the
2 readings give the same triangles. Euclid's formula for all primitive
Pythagorean triples is at the end of the module, for comparison.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd, isqrt, prod

from ancient_algorithms.babylonian_sqrt import parse_sexagesimal, to_sexagesimal

__all__ = [
    "SMALLEST_IGI",
    "LARGEST_IGI",
    "ROBSON_IGI",
    "NEUGEBAUER_SACHS_GENERATORS",
    "TABLET",
    "is_regular",
    "igibi",
    "short_side_and_diagonal",
    "takiltum",
    "trailing_part_steps",
    "reduce_triangle",
    "plimpton_row",
    "rebuild_table",
    "robson_candidates",
    "generator_triple",
    "generator_pairs",
    "floating_digits",
    "diagnose",
    "compare_with_tablet",
    "euclid_triples",
]

SMALLEST_IGI = parse_sexagesimal("1;48")
"""The igi of row 15, the last row on the tablet."""

LARGEST_IGI = parse_sexagesimal("2;24")
"""The igi of row 1, the first row on the tablet."""

ROBSON_IGI = tuple(
    parse_sexagesimal(text)
    for text in (
        "2;24",
        "2;22,13,20",
        "2;20,37,30",
        "2;18,53,20",
        "2;15",
        "2;13,20",
        "2;09,36",
        "2;08",
        "2;05",
        "2;01,30",
        "2",
        "1;55,12",
        "1;52,30",
        "1;51,06,40",
        "1;48",
    )
)
"""The igi of each row, rows 1 to 15, as listed in Robson 2001, Table 6."""

NEUGEBAUER_SACHS_GENERATORS = (
    (12, 5),
    (64, 27),
    (75, 32),
    (125, 54),
    (9, 4),
    (20, 9),
    (54, 25),
    (32, 15),
    (25, 12),
    (81, 40),
    (2, 1),
    (48, 25),
    (15, 8),
    (50, 27),
    (9, 5),
)
"""The pairs ``(p, q)`` for rows 1 to 15, as listed in Robson 2001, Table 4."""

_TABLET_TEXT = (
    ("1 59 00 15", "1 59", "2 49"),
    ("1 56 56 58 14 56 15", "56 07", "3 12 01"),
    ("1 55 07 41 15 33 45", "1 16 41", "1 50 49"),
    ("1 53 10 29 32 52 16", "3 31 49", "5 09 01"),
    ("1 48 54 01 40", "1 05", "1 37"),
    ("1 47 06 41 40", "5 19", "8 01"),
    ("1 43 11 56 28 26 40", "38 11", "59 01"),
    ("1 41 33 59 03 45", "13 19", "20 49"),
    ("1 38 33 36 36", "9 01", "12 49"),
    ("1 35 10 02 28 27 24 26 40", "1 22 41", "2 16 01"),
    ("1 33 45", "45", "1 15"),
    ("1 29 21 54 02 15", "27 59", "48 49"),
    ("1 27 03 45", "7 12 01", "4 49"),
    ("1 25 48 51 35 06 40", "29 31", "53 49"),
    ("1 23 13 46 40", "56", "53"),
)

TABLET = tuple(
    tuple(tuple(int(digit) for digit in cell.split()) for cell in row) for row in _TABLET_TEXT
)
"""Columns I, II and III of rows 1 to 15 as written, base-60 digits with no point.

The leading 1 of each column I entry sits on the broken edge. Robson (2001,
pp. 190-191) restores it, and so does this table.
"""


def is_regular(value: int | Fraction) -> bool:
    """Whether a positive number has no prime factors other than 2, 3 and 5."""
    value = Fraction(value)
    if value <= 0:
        raise ValueError(f"value must be positive, got {value}")
    return _strip_regular(value.numerator) == 1 and _strip_regular(value.denominator) == 1


def igibi(igi: Fraction) -> Fraction:
    """The reciprocal of a regular number, which has a finite base-60 expansion."""
    if not is_regular(igi):
        raise ValueError(f"{igi} is not regular, so it has no finite reciprocal")
    return 1 / Fraction(igi)


def short_side_and_diagonal(igi: Fraction) -> tuple[Fraction, Fraction]:
    """Half the difference and half the sum of ``igi`` and its reciprocal.

    They are the short side and the diagonal of a right triangle with long side 1,
    because ``((x + 1/x)/2)^2 - ((x - 1/x)/2)^2 = x * (1/x) = 1``.
    """
    if igi <= 1:
        raise ValueError(f"igi must be greater than 1, got {igi}")
    reciprocal = igibi(igi)
    return (igi - reciprocal) / 2, (igi + reciprocal) / 2


def takiltum(igi: Fraction) -> Fraction:
    """Column I: the square of the diagonal of the triangle with long side 1."""
    _, diagonal = short_side_and_diagonal(igi)
    return diagonal * diagonal


def trailing_part_steps(
    short: Fraction, diagonal: Fraction
) -> list[tuple[int, Fraction, Fraction]]:
    """Clear the fractional digits of both sides by regular factors read off their last digits.

    Each step multiplies both numbers by ``60 // g``, where ``g`` is the largest
    divisor of 60 that divides the last base-60 digit of every number still
    fractional. A factor of 60 only moves the point, which a scribe did not write.
    Returns ``(factor, short, diagonal)`` after each step. This is the trailing-part
    algorithm of Friberg (2007), as Mansfield and Wildberger (2017, Table 7) apply
    it to row 2.
    """
    steps: list[tuple[int, Fraction, Fraction]] = []
    while short.denominator > 1 or diagonal.denominator > 1:
        common = 60
        for side in (short, diagonal):
            if side.denominator > 1:
                common = gcd(common, _last_digit(side))
        factor = 60 // common
        short, diagonal = short * factor, diagonal * factor
        steps.append((factor, short, diagonal))
    return steps


def reduce_triangle(short: Fraction, diagonal: Fraction) -> tuple[int, int, int]:
    """Whole-number sides ``(b, l, d)`` of the triangle with sides ``(short, 1, diagonal)``."""
    steps = trailing_part_steps(short, diagonal)
    _, b, d = steps[-1] if steps else (1, short, diagonal)
    return int(b), prod(factor for factor, _, _ in steps), int(d)


def plimpton_row(igi: Fraction) -> tuple[Fraction, int, int]:
    """Columns I, II and III of the row built from ``igi``."""
    short, diagonal = short_side_and_diagonal(igi)
    b, _, d = reduce_triangle(short, diagonal)
    return diagonal * diagonal, b, d


def rebuild_table(igis: tuple[Fraction, ...] = ROBSON_IGI) -> list[tuple[Fraction, int, int]]:
    """The rows built from each igi, sorted by column I from largest to smallest."""
    return sorted((plimpton_row(igi) for igi in igis), reverse=True)


def robson_candidates(max_places: int = 4, max_total_places: int = 7) -> list[Fraction]:
    """Every regular igi from 1;48 to 2;24 with short enough digits, largest first.

    The igi and its reciprocal may each have at most ``max_places`` base-60
    digits, and at most ``max_total_places`` between them. Robson (2001, p. 196)
    finds that these limits admit the 15 rows of the tablet and 3 more, her
    lines 4a, 8a and 11a.
    """
    if max_places < 1:
        raise ValueError(f"max_places must be at least 1, got {max_places}")
    scale = 60 ** (max_places - 1)
    candidates = []
    for n in range(int(SMALLEST_IGI * scale), int(LARGEST_IGI * scale) + 1):
        igi = Fraction(n, scale)
        if not is_regular(n) or not SMALLEST_IGI <= igi <= LARGEST_IGI:
            continue
        places, reciprocal_places = len(floating_digits(igi)), len(floating_digits(1 / igi))
        if reciprocal_places <= max_places and places + reciprocal_places <= max_total_places:
            candidates.append(igi)
    return sorted(candidates, reverse=True)


def generator_triple(p: int, q: int) -> tuple[int, int, int]:
    """Neugebauer and Sachs's reading: ``(b, l, d) = (p^2 - q^2, 2pq, p^2 + q^2)``."""
    if not p > q > 0:
        raise ValueError(f"need p > q > 0, got p={p}, q={q}")
    return p * p - q * q, 2 * p * q, p * p + q * q


def generator_pairs(max_q: int = 60) -> list[tuple[int, int]]:
    """Coprime regular ``p > q`` with ``q <= max_q`` and ``p/q`` up to 2;24, by column I.

    Sorted from largest column I to smallest. With ``max_q = 60`` the list has 38
    pairs, and the first 15 are the rows of the tablet: Price's observation (1964),
    as Mansfield and Wildberger (2017, pp. 405-406) report and extend it.
    """
    if max_q < 1:
        raise ValueError(f"max_q must be at least 1, got {max_q}")
    pairs = [
        (p, q)
        for q in range(1, max_q + 1)
        if is_regular(q)
        for p in range(q + 1, int(LARGEST_IGI * q) + 1)
        if gcd(p, q) == 1 and is_regular(p)
    ]
    return sorted(pairs, key=lambda pair: takiltum(Fraction(*pair)), reverse=True)


def floating_digits(value: int | Fraction) -> tuple[int, ...]:
    """The base-60 digits of a regular number as a scribe wrote them, with no point.

    Leading and trailing zeros drop out, because the tablet marks neither the
    place of the units nor an empty last place. Inner zeros stay.
    """
    value = Fraction(value)
    if value <= 0:
        raise ValueError(f"value must be positive, got {value}")
    whole, fraction = to_sexagesimal(value, _fractional_places(value))
    digits = _base60_digits(whole) + fraction
    start = next(i for i, digit in enumerate(digits) if digit)
    end = max(i for i, digit in enumerate(digits) if digit)
    return digits[start : end + 1]


def diagnose(written: tuple[int, ...], computed: tuple[int, ...]) -> str:
    """Name the slip that turns the computed digits into the written ones.

    Returns ``"match"``, ``"square"`` (the square of the right value),
    ``"twice"``, ``"half"``, ``"empty place left out"``, ``"2 places added"``,
    ``"digit miscopied"`` or ``"unexplained"``. Values compare as the scribe saw
    them, with no point, so twice 28 and half of 1 52 are both 56.
    """
    _from_digits(written)
    value = _from_digits(computed)
    if written == computed:
        return "match"
    for kind, candidate in (("square", value * value), ("twice", 2 * value), ("half", 30 * value)):
        if floating_digits(candidate) == written:
            return kind
    if any(computed[:i] + computed[i + 1 :] == written for i, d in enumerate(computed) if d == 0):
        return "empty place left out"
    for i in range(len(computed) - 1):
        merged = computed[:i] + (computed[i] + computed[i + 1],) + computed[i + 2 :]
        if merged == written:
            return "2 places added"
    if (
        len(written) == len(computed)
        and sum(w != c for w, c in zip(written, computed, strict=True)) == 1
    ):
        return "digit miscopied"
    return "unexplained"


def compare_with_tablet(
    rows: list[tuple[Fraction, int, int]],
) -> list[tuple[int, str, tuple[int, ...], tuple[int, ...], str]]:
    """Every cell where the tablet differs from ``rows``, with the likely slip.

    Returns ``(row, column, written, computed, kind)``. Where both sides of a
    row are the same regular multiple of the computed ones, ``kind`` is
    ``"common factor kept"``: the scribe did not reduce that triangle.
    """
    if len(rows) != len(TABLET):
        raise ValueError(f"need {len(TABLET)} rows, got {len(rows)}")
    differences = []
    for number, (row, written) in enumerate(zip(rows, TABLET, strict=True), start=1):
        computed = tuple(floating_digits(value) for value in row)
        kept = _common_factor_kept(written[1:], row[1:])
        for column, (w, c) in enumerate(zip(written, computed, strict=True)):
            if w != c:
                kind = "common factor kept" if kept and column else diagnose(w, c)
                differences.append((number, ("I", "II", "III")[column], w, c, kind))
    return differences


def _strip_regular(n: int) -> int:
    """``n`` with every factor 2, 3 and 5 divided out."""
    for prime in (2, 3, 5):
        while n % prime == 0:
            n //= prime
    return n


def _fractional_places(value: Fraction) -> int:
    """The number of base-60 places after the point in a regular number."""
    if not is_regular(value.denominator):
        raise ValueError(f"{value} has no finite base-60 expansion")
    places = 0
    while value.denominator > 1:
        value *= 60
        places += 1
    return places


def _last_digit(value: Fraction) -> int:
    """The last nonzero base-60 digit after the point."""
    return to_sexagesimal(value, _fractional_places(value))[1][-1]


def _base60_digits(n: int) -> tuple[int, ...]:
    """The base-60 digits of a whole number, most significant first."""
    digits = []
    while n:
        n, digit = divmod(n, 60)
        digits.append(digit)
    return tuple(reversed(digits)) or (0,)


def _from_digits(digits: tuple[int, ...]) -> int:
    """Read base-60 digits as a whole number."""
    total = 0
    for digit in digits:
        if not 0 <= digit < 60:
            raise ValueError(f"base-60 digit out of range: {digit}")
        total = total * 60 + digit
    return total


def _common_factor_kept(written: tuple[tuple[int, ...], ...], sides: tuple[int, int]) -> bool:
    """Whether both written sides are the same regular multiple of ``sides``."""
    ratios = [Fraction(_from_digits(w), side) for w, side in zip(written, sides, strict=True)]
    if not all(is_regular(ratio) for ratio in ratios):
        return False
    shapes = {floating_digits(ratio) for ratio in ratios}
    return len(shapes) == 1


def euclid_triples(max_diagonal: int) -> list[tuple[int, int, int]]:
    """Every primitive triple ``(a, b, c)``, ``a^2 + b^2 = c^2``, with ``c <= max_diagonal``.

    Euclid's formula: ``m > n > 0`` coprime and of opposite parity give
    ``(m^2 - n^2, 2mn, m^2 + n^2)``, each primitive triple once. Sorted by ``c``,
    then by ``a``.
    """
    if max_diagonal < 1:
        raise ValueError(f"max_diagonal must be at least 1, got {max_diagonal}")
    triples = []
    for m in range(2, isqrt(max_diagonal) + 1):
        for n in range(1, m):
            if (m - n) % 2 and gcd(m, n) == 1 and m * m + n * n <= max_diagonal:
                triples.append((m * m - n * n, 2 * m * n, m * m + n * n))
    return sorted(triples, key=lambda t: (t[2], t[0]))
