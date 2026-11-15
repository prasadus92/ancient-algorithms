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

Places are stored least significant first, so ``places[0]`` is the first place.
"""

from __future__ import annotations

__all__ = [
    "to_places",
    "from_places",
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


def to_places(n: int, base: int = BASE) -> list[int]:
    """Digits of ``n`` in ``base``, least significant first; 0 is ``[0]``."""
    if n < 0:
        raise ValueError(f"n must be at least 0, got {n}")
    if base < 2:
        raise ValueError(f"base must be at least 2, got {base}")
    places = []
    while True:
        n, digit = divmod(n, base)
        places.append(digit)
        if n == 0:
            return places


def from_places(places: list[int], base: int = BASE) -> int:
    """The number whose digits in ``base`` are ``places``, least significant first."""
    _check_places(places, base)
    return sum(digit * base**place for place, digit in enumerate(places))


def add(upper: list[int], lower: list[int]) -> list[int]:
    """Add ``lower`` into ``upper`` from the highest place down (DA chapter 2)."""
    _check_places(upper)
    _check_places(lower)
    result = _padded(upper, len(lower))
    for place in reversed(range(len(lower))):
        result[place] += lower[place]
        _carry_up(result, place)
    return _trimmed(result)


def subtract(upper: list[int], lower: list[int]) -> list[int]:
    """Take ``lower`` from ``upper`` from the highest place down, borrowing from above."""
    if from_places(upper) < from_places(lower):
        raise ValueError(f"cannot subtract {from_places(lower)} from {from_places(upper)}")
    result = _padded(upper, len(lower))
    for place in reversed(range(len(lower))):
        if result[place] < lower[place]:
            _borrow(result, place)
        result[place] -= lower[place]
    return _trimmed(result)


def halve(places: list[int]) -> tuple[list[int], int]:
    """Half of a number as ``(whole places, sixtieths)``, working up from the units.

    The sixtieths are 30 when the number is odd and 0 otherwise.
    """
    _check_places(places)
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
    return _trimmed(halves), sixtieths


def double(places: list[int]) -> list[int]:
    """Twice a number, from the highest place down (DA chapter 3)."""
    _check_places(places)
    result = list(places)
    for place in reversed(range(len(result))):
        result[place] *= 2
        _carry_up(result, place)
    return _trimmed(result)


def multiply(upper: list[int], lower: list[int]) -> list[int]:
    """Product of 2 numbers, built in place over the upper number (DA chapter 4).

    The units of ``lower`` start under the highest digit of ``upper``. Each digit
    of ``upper``, from the highest, multiplies the digits of ``lower`` from the
    highest, and its last product replaces it.
    """
    _check_places(upper)
    _check_places(lower)
    result = _padded(upper, len(upper) + len(lower))
    for place in reversed(range(len(upper))):
        digit = result[place]
        for shift in reversed(range(len(lower))):
            product = digit * lower[shift]
            if shift == 0:
                result[place] = product  # erase the digit and write the product in its place
            else:
                result[place + shift] += product
            _carry_up(result, place + shift)
    return _trimmed(result)


def nines_check(upper: list[int], lower: list[int], product: list[int]) -> bool:
    """DA's probatio: the excesses over 9 of the factors, multiplied, match the product's.

    The test catches most slips. A wrong product that differs by a multiple of 9 passes.
    """
    excess = from_places(upper) % 9 * (from_places(lower) % 9) % 9
    return excess == from_places(product) % 9


def division_steps(dividend: list[int], divisor: list[int]) -> list[tuple[int, list[int]]]:
    """Each quotient digit of DA's division, from the highest, with the dividend left after it."""
    _check_places(dividend)
    _check_places(divisor)
    divisor = _trimmed(divisor)
    if divisor == [0]:
        raise ValueError("divisor must not be 0")
    remainder = _trimmed(dividend)
    top = len(divisor) - 1
    start = len(remainder) - len(divisor)
    if remainder[-1] < divisor[-1]:
        start -= 1  # move the divisor 1 place right
    steps = []
    for shift in range(start, -1, -1):
        above = from_places(remainder[shift + top :])
        digit = min(above // divisor[-1], BASE - 1)
        while digit and not _fits(remainder, divisor, digit, shift):
            digit -= 1  # "or close to it, below it"
        for place in reversed(range(len(divisor))):
            amount = [0] * (shift + place) + to_places(digit * divisor[place])
            remainder = _padded(subtract(remainder, amount), len(remainder))
        steps.append((digit, _trimmed(remainder)))
    return steps


def divide(dividend: list[int], divisor: list[int]) -> tuple[list[int], list[int]]:
    """Quotient and remainder, as places, by DA's division (chapters 6 and 7).

    The quotient is what DA calls "what is owed to 1"; the remainder is "parts of 1".
    """
    steps = division_steps(dividend, divisor)
    if not steps:
        return [0], _trimmed(dividend)
    quotient = [digit for digit, _ in reversed(steps)]
    return _trimmed(quotient), steps[-1][1]


def _check_places(places: list[int], base: int = BASE) -> None:
    """Raise ``ValueError`` unless ``places`` is a non-empty list of digits in ``base``."""
    if not places:
        raise ValueError("a number needs at least 1 place")
    for digit in places:
        if not 0 <= digit < base:
            raise ValueError(f"digits must be from 0 to {base - 1}, got {digit}")


def _padded(places: list[int], length: int) -> list[int]:
    """Copy of ``places`` with zeros added on the left up to ``length`` places."""
    return list(places) + [0] * (length - len(places))


def _trimmed(places: list[int]) -> list[int]:
    """``places`` without empty high places, keeping at least 1 place."""
    end = len(places)
    while end > 1 and places[end - 1] == 0:
        end -= 1
    return places[:end]


def _carry_up(places: list[int], place: int) -> None:
    """Turn each 10 at ``place`` into 1 in the place above, and keep going while needed."""
    while places[place] >= BASE:
        carry, places[place] = divmod(places[place], BASE)
        if place + 1 == len(places):
            places.append(0)
        places[place + 1] += carry
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
    return digit * from_places([0] * shift + divisor) <= from_places(remainder)


def schoolbook_add(upper: list[int], lower: list[int]) -> list[int]:
    """Modern column addition: right to left, 1 carry passed along, no place revisited."""
    _check_places(upper)
    _check_places(lower)
    width = max(len(upper), len(lower))
    a, b = _padded(upper, width), _padded(lower, width)
    total, carry = [], 0
    for place in range(width):
        carry, digit = divmod(a[place] + b[place] + carry, BASE)
        total.append(digit)
    if carry:
        total.append(carry)
    return total
