import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.algorism import (
    add,
    divide,
    division_steps,
    double,
    from_places,
    halve,
    multiply,
    nines_check,
    schoolbook_add,
    subtract,
    to_places,
)

P = to_places
F = from_places
whole = st.integers(0, 10**40)


# Worked examples in the Cambridge text, Boncompagni 1857 edition.
def test_subtraction_example_6422_minus_3211() -> None:
    assert F(subtract(P(6422), P(3211))) == 3211


def test_subtraction_example_1144_minus_144() -> None:
    # C states the problem without working; N has 1444 - 144 (Folkerts 2001).
    assert F(subtract(P(1144), P(144))) == 1000
    assert F(subtract(P(1444), P(144))) == 1300


def test_multiplication_example_2326_times_214() -> None:
    product = multiply(P(2326), P(214))
    assert F(product) == 497764
    assert nines_check(P(2326), P(214), product)


def test_division_example_46468_by_324_step_by_step() -> None:
    # The text: quotient digits 1, 4, 3, leaving 14068, then 1108, then 136.
    steps = division_steps(P(46468), P(324))
    assert [(digit, F(rest)) for digit, rest in steps] == [(1, 14068), (4, 1108), (3, 136)]
    quotient, remainder = divide(P(46468), P(324))
    assert (F(quotient), F(remainder)) == (143, 136)


def test_division_example_1800_by_9() -> None:
    # 1 is smaller than 9, so the 9 goes under the 8.
    steps = division_steps(P(1800), P(9))
    assert [digit for digit, _ in steps] == [2, 0, 0]
    assert [F(x) for x in divide(P(1800), P(9))] == [200, 0]


def test_halving_odd_units_gives_thirty_sixtieths() -> None:
    assert halve(P(7)) == ([3], 30)
    assert halve(P(10)) == ([5], 0)
    assert halve(P(35)) == ([7, 1], 30)


def test_odd_digit_above_units_sends_five_down() -> None:
    whole_part, sixtieths = halve(P(1144))
    assert (F(whole_part), sixtieths) == (572, 0)


def test_doubling_carries_upward_through_nines() -> None:
    assert F(double(P(4999))) == 9998
    assert F(double(P(5))) == 10


def test_addition_from_the_top_cascades_carries() -> None:
    assert F(add(P(999), P(1))) == 1000
    assert F(add(P(5), P(995))) == 1000


def test_division_digit_from_top_digit_can_overshoot() -> None:
    # 1980 / 199: the top digits say 1, but 199 does not go into 198.
    steps = division_steps(P(1980), P(199))
    assert [digit for digit, _ in steps] == [0, 9]
    assert [F(x) for x in divide(P(1980), P(199))] == [9, 189]


def test_nines_check_misses_errors_by_multiples_of_nine() -> None:
    assert not nines_check(P(2326), P(214), P(497765))
    assert nines_check(P(2326), P(214), P(497764 + 9))


def test_bad_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot subtract"):
        subtract(P(5), P(7))
    with pytest.raises(ValueError, match="divisor must not be 0"):
        divide(P(5), [0])
    with pytest.raises(ValueError, match="digits must be from 0 to 9, got 12"):
        add([12], [1])
    with pytest.raises(ValueError, match="n must be at least 0, got -1"):
        to_places(-1)


@given(a=whole, b=whole)
def test_add_matches_python(a: int, b: int) -> None:
    assert F(add(P(a), P(b))) == a + b
    assert schoolbook_add(P(a), P(b)) == add(P(a), P(b))


@given(a=whole, b=whole)
def test_subtract_matches_python(a: int, b: int) -> None:
    a, b = max(a, b), min(a, b)
    assert F(subtract(P(a), P(b))) == a - b


@given(a=whole)
def test_halve_and_double_match_python(a: int) -> None:
    whole_part, sixtieths = halve(P(a))
    assert F(whole_part) * 60 + sixtieths == a * 30
    assert F(double(P(a))) == 2 * a


@given(a=whole, b=whole)
def test_multiply_matches_python(a: int, b: int) -> None:
    assert F(multiply(P(a), P(b))) == a * b


@given(a=whole, b=st.integers(1, 10**20))
def test_divide_matches_divmod(a: int, b: int) -> None:
    quotient, remainder = divide(P(a), P(b))
    assert (F(quotient), F(remainder)) == divmod(a, b)


@given(n=whole, base=st.integers(2, 60))
def test_places_round_trip(n: int, base: int) -> None:
    assert F(P(n, base), base) == n
