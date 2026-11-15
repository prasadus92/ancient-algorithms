"""Al-Khwarizmi's arithmetic with Indian numerals, from the Latin "Dixit Algorizmi".

Al-Khwarizmi wrote a book on calculating with the 9 Indian digits and the zero in
Baghdad, c. 825 CE (Folkerts, Science in Context 14, 2001). No Arabic manuscript of
it is known. It survives in a Latin reworking of a lost 12th-century translation,
called DA from its opening words "Dixit Algorizmi" ("al-Khwarizmi said"), in 2
manuscripts: Cambridge, University Library Ii.6.5 (apparently 13th century, missing
its last folios) and New York, Hispanic Society of America HC 397/726 (complete,
edited by Folkerts in 1997).

This module follows the Cambridge text as printed by B. Boncompagni, "Algoritmi de
numero indorum", Trattati d'aritmetica I (Rome, 1857), from p. 1, read against
Folkerts's 2001 chapter summary. A number is written in places (differentiae),
counted from the right, and an empty place holds a small circle (circulus), 0:

1. Add or subtract place by place, starting from the highest place. When a place
   reaches 10, write 1 in the next place up. When a place is too small to subtract
   from, take 1 from the next place up and make it 10.
2. Halve starting from the lowest place. The half of an odd unit is written as 30
   sixtieths; an odd 1 in a higher place goes down to the place below as 5.
3. Double starting from the highest place, carrying 10 as 1 to the place above.
4. Multiply by writing the lower number with its units under the highest digit of
   the upper. That digit multiplies each digit of the lower number from the left,
   the products are written above, and the last product replaces the digit. Then
   the lower number moves 1 place right and the next digit does the same.
5. Check a doubling or a product by casting out nines.
6. Divide by setting the divisor under the dividend, highest place under highest
   place, 1 place further right when the dividend's top digit is the smaller. Find
   the digit that times the divisor's top digit comes closest to what is above it,
   write it above the divisor's units, multiply and subtract digit by digit, move
   the divisor 1 place right, and repeat. The quotient is "what is owed to 1".

Numbers go in and come out as digit lists in written order, most significant
first, as ``place_value`` writes them. Inside each procedure the digits are turned
round into places counted from the right, as the text counts them, so
``places[0]`` is the first place.
"""

from __future__ import annotations

from ancient_algorithms.place_value import carry, check_digits, from_digits, pad, to_digits, trim

__all__ = [
    "add",
    "subtract",
    "halve",
    "double",
    "multiply",
    "nines_check",
    "division_steps",
    "divide",
    "schoolbook_add",
]

BASE = 10
"""The Indian numerals are decimal."""

HALF_UNIT_SIXTIETHS = 30
"""DA writes the half of an odd unit as 30 parts of 60."""


def add(upper: list[int], lower: list[int]) -> list[int]:
    """Add ``lower`` into ``upper`` from the highest place down (DA chapter 2)."""
    places, other = _places(upper, lower)
    for place in reversed(range(len(other))):
        places[place] += other[place]
        _carry_up(places, place)
    return _written(places)


def subtract(upper: list[int], lower: list[int]) -> list[int]:
    """Take ``lower`` from ``upper`` from the highest place down, borrowing from above."""
    if from_digits(upper, BASE) < from_digits(lower, BASE):
        raise ValueError(
            f"cannot subtract {from_digits(lower, BASE)} from {from_digits(upper, BASE)}"
        )
    places, other = _places(upper, lower)
    for place in reversed(range(len(other))):
        if places[place] < other[place]:
            _borrow(places, place)
        places[place] -= other[place]
    return _written(places)


def halve(digits: list[int]) -> tuple[list[int], int]:
    """Half of a number as ``(whole digits, sixtieths)``, working up from the units.

    The sixtieths are 30 when the number is odd and 0 otherwise.
    """
    (places,) = _places(digits)
    halves = [0] * len(places)
    sixtieths = 0
    for place, digit in enumerate(places):
        halves[place] = digit // 2
        if digit % 2 == 0:
            continue
        if place == 0:
            sixtieths = HALF_UNIT_SIXTIETHS
        else:
            halves[place - 1] += 5  # the odd 1 here is 10 of the place below
    return _written(halves), sixtieths


def double(digits: list[int]) -> list[int]:
    """Twice a number, from the highest place down (DA chapter 3)."""
    (places,) = _places(digits)
    for place in reversed(range(len(places))):
        places[place] *= 2
        _carry_up(places, place)
    return _written(places)


def multiply(upper: list[int], lower: list[int]) -> list[int]:
    """Product of 2 numbers, built in place over the upper number (DA chapter 4).

    The units of ``lower`` start under the highest digit of ``upper``. Each digit
    of ``upper``, from the highest, multiplies the digits of ``lower`` from the
    highest, and its last product replaces it.
    """
    work, other = _places(upper, lower)
    work += [0] * len(other)
    for place in reversed(range(len(upper))):
        digit = work[place]
        for shift in reversed(range(len(other))):
            product = digit * other[shift]
            if shift == 0:
                work[place] = product  # erase the digit and write the product in its place
            else:
                work[place + shift] += product
            _carry_up(work, place + shift)
    return _written(work)


def nines_check(upper: list[int], lower: list[int], product: list[int]) -> bool:
    """DA's probatio: the excesses over 9 of the factors, multiplied, match the product's.

    The test catches most slips. A wrong product that differs by a multiple of 9 passes.
    """
    excess = from_digits(upper, BASE) % 9 * (from_digits(lower, BASE) % 9) % 9
    return excess == from_digits(product, BASE) % 9


def division_steps(dividend: list[int], divisor: list[int]) -> list[tuple[int, list[int]]]:
    """Each quotient digit of DA's division, from the highest, with the dividend left after it."""
    check_digits(dividend, BASE)
    check_digits(divisor, BASE)
    remainder, divisor_places = trim(dividend)[::-1], trim(divisor)[::-1]
    if divisor_places == [0]:
        raise ValueError("divisor must not be 0")
    top = len(divisor_places) - 1
    start = len(remainder) - len(divisor_places)
    if remainder[-1] < divisor_places[-1]:
        start -= 1  # move the divisor 1 place right
    steps = []
    for shift in range(start, -1, -1):
        above = from_digits(remainder[shift + top :][::-1], BASE)
        digit = min(above // divisor_places[-1], BASE - 1)
        while digit and not _fits(remainder, divisor_places, digit, shift):
            digit -= 1  # "or close to it, below it"
        for place in reversed(range(len(divisor_places))):
            amount = to_digits(digit * divisor_places[place], BASE) + [0] * (shift + place)
            remainder = pad(subtract(_written(remainder), amount), len(remainder))[::-1]
        steps.append((digit, _written(remainder)))
    return steps


def divide(dividend: list[int], divisor: list[int]) -> tuple[list[int], list[int]]:
    """Quotient and remainder digits by DA's division (chapters 6 and 7).

    The quotient is what DA calls "what is owed to 1"; the remainder is "parts of 1".
    """
    steps = division_steps(dividend, divisor)
    if not steps:
        return [0], trim(dividend)
    return trim([digit for digit, _ in steps]), steps[-1][1]


def _places(*numbers: list[int]) -> list[list[int]]:
    """Check each number, pad all to one width, and turn each into places from the right."""
    for digits in numbers:
        check_digits(digits, BASE)
    width = max(len(digits) for digits in numbers)
    return [pad(digits, width)[::-1] for digits in numbers]


def _written(places: list[int]) -> list[int]:
    """Places from the right back into written digits, without leading zeros."""
    return trim(places[::-1])


def _carry_up(places: list[int], place: int) -> None:
    """Turn each 10 at ``place`` into 1 in the place above, and keep going while needed."""
    while places[place] >= BASE:
        carried, places[place] = divmod(places[place], BASE)
        if place + 1 == len(places):
            places.append(0)
        places[place + 1] += carried
        place += 1


def _borrow(places: list[int], place: int) -> None:
    """Take 1 from the nearest non-empty place above and make it 10 at ``place``."""
    source = place + 1
    while places[source] == 0:
        source += 1
    places[source] -= 1
    for between in range(place + 1, source):
        places[between] = BASE - 1  # "and 9 will remain in the second"
    places[place] += BASE


def _fits(remainder: list[int], divisor: list[int], digit: int, shift: int) -> bool:
    """Whether ``digit`` times the divisor, moved ``shift`` places, can be taken away."""
    moved = from_digits(divisor[::-1] + [0] * shift, BASE)
    return digit * moved <= from_digits(remainder[::-1], BASE)


def schoolbook_add(upper: list[int], lower: list[int]) -> list[int]:
    """Modern column addition: right to left, 1 carry passed along, no place revisited."""
    check_digits(upper, BASE)
    check_digits(lower, BASE)
    width = max(len(upper), len(lower))
    return carry([a + b for a, b in zip(pad(upper, width), pad(lower, width), strict=True)], BASE)
