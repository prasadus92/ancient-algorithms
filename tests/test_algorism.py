import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.algorism import (
    add,
    divide,
    division_steps,
    double,
    halve,
    multiply,
    nines_check,
    schoolbook_add,
    subtract,
)
from ancient_algorithms.place_value import from_digits, to_digits


def dec(n: int) -> list[int]:
    """Decimal digits of ``n``, written order."""
    return to_digits(n, 10)


def val(digits: list[int]) -> int:
    """The number written by decimal ``digits``."""
    return from_digits(digits, 10)


whole = st.integers(0, 10**40)


# Worked examples in the Cambridge text, Boncompagni 1857 edition.
def test_subtraction_example_6422_minus_3211() -> None:
    assert subtract(dec(6422), dec(3211)) == [3, 2, 1, 1]


def test_subtraction_example_1144_minus_144() -> None:
    # C states the problem without working; N has 1444 - 144 (Folkerts 2001).
    assert val(subtract(dec(1144), dec(144))) == 1000
    assert val(subtract(dec(1444), dec(144))) == 1300


def test_multiplication_example_2326_times_214() -> None:
    product = multiply(dec(2326), dec(214))
    assert val(product) == 497764
    assert nines_check(dec(2326), dec(214), product)


def test_division_example_46468_by_324_step_by_step() -> None:
    # The text: quotient digits 1, 4, 3, leaving 14068, then 1108, then 136.
    steps = division_steps(dec(46468), dec(324))
    assert [(digit, val(rest)) for digit, rest in steps] == [(1, 14068), (4, 1108), (3, 136)]
    quotient, remainder = divide(dec(46468), dec(324))
    assert (val(quotient), val(remainder)) == (143, 136)


def test_division_example_1800_by_9() -> None:
    # 1 is smaller than 9, so the 9 goes under the 8.
    steps = division_steps(dec(1800), dec(9))
    assert [digit for digit, _ in steps] == [2, 0, 0]
    assert [val(x) for x in divide(dec(1800), dec(9))] == [200, 0]


def test_halving_odd_units_gives_thirty_sixtieths() -> None:
    assert halve(dec(7)) == ([3], 30)
    assert halve(dec(10)) == ([5], 0)
    assert halve(dec(35)) == ([1, 7], 30)


def test_odd_digit_above_units_sends_five_down() -> None:
    whole_part, sixtieths = halve(dec(1144))
    assert (val(whole_part), sixtieths) == (572, 0)


def test_doubling_carries_upward_through_nines() -> None:
    assert val(double(dec(4999))) == 9998
    assert val(double(dec(5))) == 10


def test_addition_from_the_top_cascades_carries() -> None:
    assert val(add(dec(999), dec(1))) == 1000
    assert val(add(dec(5), dec(995))) == 1000


def test_leading_zeros_are_dropped_by_both_additions() -> None:
    assert add([0, 0, 5], [0, 7]) == [1, 2]
    assert schoolbook_add([0, 0, 5], [0, 7]) == [1, 2]
    assert add([0], [0, 0]) == schoolbook_add([0], [0, 0]) == [0]


def test_division_digit_from_top_digit_can_overshoot() -> None:
    # 1980 / 199: the top digits say 1, but 199 does not go into 198.
    steps = division_steps(dec(1980), dec(199))
    assert [digit for digit, _ in steps] == [0, 9]
    assert [val(x) for x in divide(dec(1980), dec(199))] == [9, 189]


def test_dividend_smaller_than_divisor() -> None:
    assert divide(dec(5), dec(7)) == ([0], [5])


def test_nines_check_misses_errors_by_multiples_of_nine() -> None:
    assert not nines_check(dec(2326), dec(214), dec(497765))
    assert nines_check(dec(2326), dec(214), dec(497764 + 9))


def test_bad_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot subtract 7 from 5"):
        subtract(dec(5), dec(7))
    with pytest.raises(ValueError, match="divisor must not be 0"):
        divide(dec(5), [0])
    with pytest.raises(ValueError, match="digits in base 10 are 0 to 9, got 12"):
        add([12], [1])
    with pytest.raises(ValueError, match="at least 1 digit"):
        double([])


@given(a=whole, b=whole)
def test_add_matches_python(a: int, b: int) -> None:
    assert val(add(dec(a), dec(b))) == a + b
    assert schoolbook_add(dec(a), dec(b)) == add(dec(a), dec(b))


@given(a=whole, b=whole, zeros=st.integers(0, 3))
def test_additions_agree_with_leading_zeros(a: int, b: int, zeros: int) -> None:
    upper = [0] * zeros + dec(a)
    assert add(upper, dec(b)) == schoolbook_add(upper, dec(b)) == dec(a + b)


@given(a=whole, b=whole)
def test_subtract_matches_python(a: int, b: int) -> None:
    a, b = max(a, b), min(a, b)
    assert val(subtract(dec(a), dec(b))) == a - b


@given(a=whole)
def test_halve_and_double_match_python(a: int) -> None:
    whole_part, sixtieths = halve(dec(a))
    assert val(whole_part) * 60 + sixtieths == a * 30
    assert val(double(dec(a))) == 2 * a


@given(a=whole, b=whole)
def test_multiply_matches_python(a: int, b: int) -> None:
    assert val(multiply(dec(a), dec(b))) == a * b


@given(a=whole, b=st.integers(1, 10**20))
def test_divide_matches_divmod(a: int, b: int) -> None:
    quotient, remainder = divide(dec(a), dec(b))
    assert (val(quotient), val(remainder)) == divmod(a, b)
