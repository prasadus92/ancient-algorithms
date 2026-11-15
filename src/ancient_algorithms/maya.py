"""Maya numerals, the Long Count, the 260-day and 365-day counts, and the Calendar Round.

Maya scribes wrote numbers with a dot for 1, a bar for 5 and a sign for 0 (in the
codices a lenticular sign, always painted red, in Morley's words), stacking places
from the bottom up. Each place is worth 20 of the place below, except in counts of
days: there the third place is worth 18 of the second, so the places are 1, 20,
360, 7,200 and 144,000 days (S. G. Morley, An Introduction to the Study of the Maya
Hieroglyphs, 1915, Table VIII). Those 5 places are the Long Count: k'in, winal,
tun, k'atun and bak'tun, written as 9.9.9.16.0.

A day also has a name in 2 cycles that run at the same time. The 260-day count (the
Tzolk'in) pairs a number from 1 to 13 with 1 of 20 day names. The 365-day count
(the Haab') has 18 months of 20 days, numbered 0 to 19, and 5 extra days (Wayeb').
A Tzolk'in and Haab' pair repeats every 18,980 days, the Calendar Round.

The day count starts at the era date 13.0.0.0.0 4 Ajaw 8 Kumk'u. Tying that day
to a Julian Day Number needs a correlation constant, which comes from colonial
sources and astronomy, not from Maya texts. Martin and Skidmore (The PARI Journal
13, 2012, p. 3) call 584285 and 584283 "the two most widely accepted", and argue
for 584286 themselves. This module uses 584283, the Goodman-Martinez-Thompson (GMT)
value used by Kennett et al. (Scientific Reports 3, 1597, 2013), and offers the
other 2 as constants.

The steps, for a Long Count date:

1. Multiply each place by its value (1, 20, 360, 7,200, 144,000) and add, to get
   the days since the era date.
2. Count that many days on from 4 Ajaw in the 260-day count and from 8 Kumk'u in
   the 365-day count.
3. Add the correlation constant to get the Julian Day Number, and convert that to
   a Julian or Gregorian calendar date.

Names use the modern spellings (Ajaw, Kumk'u). Morley writes the older forms
(Ahau, Cumhu).
"""

from __future__ import annotations

from datetime import date

from ancient_algorithms.kuttaka import crt
from ancient_algorithms.place_value import carry, from_digits, pad, to_digits

__all__ = [
    "TZOLKIN_NAMES",
    "HAAB_MONTHS",
    "LONG_COUNT_PLACES",
    "LONG_COUNT_LIMITS",
    "CALENDAR_ROUND",
    "GMT",
    "GMT_584285",
    "MARTIN_SKIDMORE_584286",
    "bars_and_dots",
    "to_vigesimal",
    "from_vigesimal",
    "add_bars_and_dots",
    "days_from_long_count",
    "long_count_from_days",
    "tzolkin",
    "haab",
    "calendar_round",
    "days_in_round",
    "jdn_from_long_count",
    "long_count_from_jdn",
    "jdn_from_gregorian",
    "gregorian_from_jdn",
    "jdn_from_julian",
    "julian_from_jdn",
    "jdn_from_date",
]

TZOLKIN_NAMES = (
    "Imix", "Ik'", "Ak'bal", "K'an", "Chikchan", "Kimi", "Manik'", "Lamat", "Muluk", "Ok",
    "Chuwen", "Eb", "Ben", "Ix", "Men", "Kib", "Kaban", "Etz'nab", "Kawak", "Ajaw",
)  # fmt: skip
"""The 20 day names of the 260-day count, in order."""

HAAB_MONTHS = (
    "Pop", "Wo", "Sip", "Sotz'", "Sek", "Xul", "Yaxk'in", "Mol", "Ch'en", "Yax",
    "Sak'", "Keh", "Mak", "K'ank'in", "Muwan", "Pax", "K'ayab", "Kumk'u", "Wayeb'",
)  # fmt: skip
"""The 18 months of 20 days and the closing 5 days of the 365-day count."""

LONG_COUNT_PLACES = (144_000, 7_200, 360, 20, 1)
"""Days in a bak'tun, k'atun, tun, winal and k'in."""

LONG_COUNT_LIMITS = (20, 20, 20, 18, 20)
"""How many of each period make 1 of the next: 18 winals make a tun, 20 of the rest."""

CALENDAR_ROUND = 18_980
"""Days before a Tzolk'in and Haab' pair repeats: the least common multiple of 260 and 365."""

GMT = 584_283
"""Julian Day Number of the era date 13.0.0.0.0 under the GMT correlation."""

GMT_584285 = 584_285
"""The other widely accepted GMT value, 2 days later (Martin and Skidmore 2012, p. 3)."""

MARTIN_SKIDMORE_584286 = 584_286
"""The constant Martin and Skidmore (2012) argue for, 3 days later than 584283."""

MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
"""Days in each month of a common year, in both the Julian and Gregorian calendars."""

ERA_TZOLKIN = (4, TZOLKIN_NAMES.index("Ajaw"))
"""The era date falls on 4 Ajaw."""

ERA_HAAB = (8, HAAB_MONTHS.index("Kumk'u"))
"""The era date falls on 8 Kumk'u."""


def bars_and_dots(digit: int) -> tuple[int, int]:
    """The bars (5 each) and dots (1 each) that write a digit from 0 to 19; 0 is ``(0, 0)``."""
    if not 0 <= digit < 20:
        raise ValueError(f"a Maya digit is from 0 to 19, got {digit}")
    return divmod(digit, 5)


def to_vigesimal(n: int) -> list[int]:
    """Base-20 digits of ``n``, highest first, as a scribe stacks them from the top."""
    return to_digits(n, 20)


def from_vigesimal(digits: list[int]) -> int:
    """The number written by base-20 ``digits``, highest first."""
    return from_digits(digits, 20)


def add_bars_and_dots(upper: list[int], lower: list[int]) -> list[int]:
    """Sum of 2 base-20 numbers, highest digit first, by pooling bars and dots.

    In each place, put the bars and dots of both numbers together. Then, from the
    bottom, every 5 dots make a bar and every 4 bars make 1 dot in the place above,
    which is carrying 20 in base 20.
    """
    width = max(len(upper), len(lower))
    pooled = []
    for a, b in zip(pad(upper, width), pad(lower, width), strict=True):
        bars_a, dots_a = bars_and_dots(a)
        bars_b, dots_b = bars_and_dots(b)
        pooled.append(5 * (bars_a + bars_b) + dots_a + dots_b)
    return carry(pooled, 20)


def days_from_long_count(long_count: tuple[int, ...]) -> int:
    """Days since the era date for a Long Count ``(bak'tun, k'atun, tun, winal, k'in)``."""
    if len(long_count) != len(LONG_COUNT_PLACES):
        raise ValueError(f"a Long Count has 5 places, got {long_count}")
    for place, (value, limit) in enumerate(zip(long_count, LONG_COUNT_LIMITS, strict=True)):
        if not 0 <= value < limit:
            raise ValueError(f"place {place} of {long_count} must be from 0 to {limit - 1}")
    return sum(value * days for value, days in zip(long_count, LONG_COUNT_PLACES, strict=True))


def long_count_from_days(days: int) -> tuple[int, ...]:
    """The Long Count of a day ``days`` after the era date, below 20 bak'tuns."""
    if not 0 <= days < 20 * LONG_COUNT_PLACES[0]:
        raise ValueError(f"days must be from 0 to {20 * LONG_COUNT_PLACES[0] - 1}, got {days}")
    places = []
    for size in LONG_COUNT_PLACES:
        value, days = divmod(days, size)
        places.append(value)
    return tuple(places)


def tzolkin(days: int) -> tuple[int, str]:
    """Number (1 to 13) and day name of the day ``days`` after the era date, 4 Ajaw."""
    number, name = ERA_TZOLKIN
    return (number - 1 + days) % 13 + 1, TZOLKIN_NAMES[(name + days) % 20]


def haab(days: int) -> tuple[int, str]:
    """Day (0 to 19) and month of the day ``days`` after the era date, 8 Kumk'u."""
    day, month = ERA_HAAB
    position = (20 * month + day + days) % 365
    return position % 20, HAAB_MONTHS[position // 20]


def calendar_round(days: int) -> tuple[int, str, int, str]:
    """Tzolk'in and Haab' of the day ``days`` after the era date.

    The 2 counts run at the same time, so the pair repeats every 18,980 days.
    """
    return tzolkin(days) + haab(days)


def days_in_round(number: int, name: str, day: int, month: str) -> int:
    """Days after the era date, from 0 to 18,979, of a Calendar Round date.

    A Calendar Round date fixes the day count in 3 cycles: modulo 13 (the number),
    modulo 20 (the day name) and modulo 365 (the Haab'). Solving the 3 remainders is
    the Chinese remainder problem, so this uses ``kuttaka.crt``. Only 1 in 5 pairs of
    a 260-day and a 365-day name exists, because 20 and 365 share the factor 5.
    """
    if not 1 <= number <= 13:
        raise ValueError(f"a Tzolk'in number is from 1 to 13, got {number}")
    if name not in TZOLKIN_NAMES or month not in HAAB_MONTHS:
        raise ValueError(f"unknown day name or month: {name!r}, {month!r}")
    limit = 5 if month == "Wayeb'" else 20
    if not 0 <= day < limit:
        raise ValueError(f"{month} has days 0 to {limit - 1}, got {day}")
    in_13 = (number - ERA_TZOLKIN[0]) % 13
    in_20 = (TZOLKIN_NAMES.index(name) - ERA_TZOLKIN[1]) % 20
    in_365 = (20 * HAAB_MONTHS.index(month) + day - 20 * ERA_HAAB[1] - ERA_HAAB[0]) % 365
    try:
        return crt([(in_13, 13), (in_20, 20), (in_365, 365)])
    except ValueError:
        raise ValueError(f"{number} {name} {day} {month} never occurs") from None


def jdn_from_long_count(long_count: tuple[int, ...], correlation: int = GMT) -> int:
    """Julian Day Number of a Long Count date under ``correlation``."""
    return days_from_long_count(long_count) + correlation


def long_count_from_jdn(jdn: int, correlation: int = GMT) -> tuple[int, ...]:
    """Long Count of a Julian Day Number under ``correlation``."""
    return long_count_from_days(jdn - correlation)


def jdn_from_gregorian(year: int, month: int, day: int) -> int:
    """Julian Day Number of a proleptic Gregorian date; year 0 is 1 BCE, -3113 is 3114 BCE."""
    _check_day(year, month, day, _gregorian_leap(year))
    y, m = _march_based(year, month)
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045


def gregorian_from_jdn(jdn: int) -> tuple[int, int, int]:
    """Proleptic Gregorian ``(year, month, day)`` of a Julian Day Number, astronomical years."""
    a = jdn + 32044
    centuries = (4 * a + 3) // 146097
    return _from_march_based(a - 146097 * centuries // 4, 100 * centuries)


def jdn_from_julian(year: int, month: int, day: int) -> int:
    """Julian Day Number of a proleptic Julian calendar date, astronomical years."""
    _check_day(year, month, day, year % 4 == 0)
    y, m = _march_based(year, month)
    return day + (153 * m + 2) // 5 + 365 * y + y // 4 - 32083


def julian_from_jdn(jdn: int) -> tuple[int, int, int]:
    """Proleptic Julian calendar ``(year, month, day)`` of a Julian Day Number."""
    return _from_march_based(jdn + 32082, 0)


def _gregorian_leap(year: int) -> bool:
    """Whether a proleptic Gregorian year, astronomical numbering, has a 29 February."""
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _check_day(year: int, month: int, day: int, leap: bool) -> None:
    """Raise ``ValueError`` unless ``month`` is 1 to 12 and ``day`` exists in that month."""
    if not 1 <= month <= 12:
        raise ValueError(f"month must be from 1 to 12, got {month}")
    length = MONTH_DAYS[month - 1] + (1 if leap and month == 2 else 0)
    if not 1 <= day <= length:
        raise ValueError(f"{year}-{month:02d} has days 1 to {length}, got {day}")


def _march_based(year: int, month: int) -> tuple[int, int]:
    """Shift to a year that starts in March and counts from 4800 BCE, so leap days fall last."""
    shift = (14 - month) // 12
    return year + 4800 - shift, month + 12 * shift - 3


def _from_march_based(days: int, century_years: int) -> tuple[int, int, int]:
    """Year, month and day from days into a 4-year Julian cycle count, March-based."""
    four_years = (4 * days + 3) // 1461
    day_of_year = days - 1461 * four_years // 4
    m = (5 * day_of_year + 2) // 153
    day = day_of_year - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = century_years + four_years - 4800 + m // 10
    return year, month, day


def jdn_from_date(year: int, month: int, day: int) -> int:
    """Julian Day Number from Python's own proleptic Gregorian calendar, years 1 to 9999."""
    return date(year, month, day).toordinal() + 1_721_425
