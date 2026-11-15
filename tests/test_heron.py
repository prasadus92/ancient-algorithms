from fractions import Fraction
from itertools import pairwise
from math import isqrt

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ancient_algorithms.babylonian_sqrt import heron_steps
from ancient_algorithms.heron import (
    METRICA_NUMBER,
    correct_decimals,
    difference,
    heron_sqrt,
    nearest_square_side,
    newton_step,
    unit_fractions,
)

numbers = st.integers(min_value=1, max_value=10**12)
sides = st.fractions(min_value=Fraction(1, 1000), max_value=10**6, max_denominator=10**6)
# Greedy unit-fraction denominators grow fast, so this test keeps denominators small.
small_fractions = st.fractions(min_value=0, max_value=1000, max_denominator=100)


# Metrica I.8 (Schöne 1903, pp. 18.22 to 20.5; Heath 1921, vol. 2, p. 324).
def test_metrica_720_from_the_triangle_7_8_9() -> None:
    s = Fraction(7 + 8 + 9, 2)
    assert s * (s - 7) * (s - 8) * (s - 9) == METRICA_NUMBER


def test_metrica_first_step() -> None:
    assert nearest_square_side(720) == 27
    start, first = heron_sqrt(720, 1)
    assert (start, first) == (Fraction(27), Fraction(161, 6))
    assert unit_fractions(first) == (26, (2, 3))  # 26 1/2 1/3


def test_metrica_difference_is_1_36() -> None:
    first = heron_sqrt(720, 1)[1]
    assert first * first == 720 + Fraction(1, 36)
    assert difference(720, first) == Fraction(1, 36)


def test_metrica_second_step_starts_from_720_1_36() -> None:
    # Heron: put 720 1/36 in place of 729, so the side 26 1/2 1/3 replaces 27.
    second = heron_sqrt(720, 2)[2]
    assert second == heron_steps(720, Fraction(161, 6), 1)[1] == Fraction(51841, 1932)
    assert difference(720, second) == Fraction(1, 3_732_624)
    assert difference(720, second) < Fraction(1, 36)


def test_correct_decimals_on_720() -> None:
    assert [correct_decimals(720, x) for x in heron_sqrt(720, 4)] == [0, 3, 8, 18, 38]


def test_correct_decimals_from_below() -> None:
    assert correct_decimals(720, Fraction(26)) == 0
    assert correct_decimals(2, Fraction(141, 100)) == 2
    assert correct_decimals(2, Fraction(1)) == 0
    assert correct_decimals(10**6, Fraction(1)) == 0


def test_archimedes_upper_bound_for_root_3() -> None:
    # Measurement of a Circle uses 1351/780 > sqrt(3); 2 rounds from 5/3 reach it.
    assert heron_steps(3, Fraction(5, 3), 2)[-1] == Fraction(1351, 780)


def test_ybc_7289_route() -> None:
    assert heron_sqrt(2, 3) == [1, Fraction(3, 2), Fraction(17, 12), Fraction(577, 408)]


@pytest.mark.parametrize(
    "n, side", [(1, 1), (2, 1), (3, 2), (12, 3), (13, 4), (720, 27), (729, 27)]
)
def test_nearest_square_side(n: int, side: int) -> None:
    assert nearest_square_side(n) == side


def test_a_square_number_stays_put() -> None:
    assert heron_sqrt(729, 3) == [27, 27, 27, 27]


def test_unit_fractions() -> None:
    assert unit_fractions(Fraction(1, 36)) == (0, (36,))
    assert unit_fractions(Fraction(7)) == (7, ())
    assert unit_fractions(Fraction(5, 121)) == (
        0,
        (25, 757, 763309, 873960180913, 1527612795642093418846225),
    )
    with pytest.raises(ValueError, match="x must be at least 0"):
        unit_fractions(Fraction(-1, 2))


@pytest.mark.parametrize("n, steps", [(0, 1), (-4, 1), (2, -1)])
def test_rejects_bad_input(n: int, steps: int) -> None:
    with pytest.raises(ValueError, match="must be at least"):
        heron_sqrt(n, steps)


def test_correct_decimals_rejects_bad_n() -> None:
    with pytest.raises(ValueError, match="n must be at least 1, got 0"):
        correct_decimals(0, Fraction(1))


@given(numbers, sides)
def test_heron_is_newton_on_x_squared_less_n(n: int, x: Fraction) -> None:
    assert heron_steps(n, x, 1)[1] == newton_step(n, x)


@given(numbers, sides)
def test_difference_after_a_step_is_the_old_one_squared_over_4x2(n: int, x: Fraction) -> None:
    # (x' * x' - n) = (x * x - n)**2 / (4 * x * x): the error in the square is squared.
    new = heron_steps(n, x, 1)[1]
    assert difference(n, new) == difference(n, x) ** 2 / (4 * x * x)


@given(numbers, sides)
def test_after_1_step_the_side_is_never_too_small(n: int, x: Fraction) -> None:
    assert difference(n, heron_steps(n, x, 1)[1]) >= 0


@settings(max_examples=50)
@given(st.integers(min_value=2, max_value=10**8).filter(lambda n: isqrt(n) ** 2 != n))
def test_correct_decimals_at_least_double(n: int) -> None:
    xs = heron_sqrt(n, 4)
    decimals = [correct_decimals(n, x, limit=100) for x in xs]
    for before, after in pairwise(decimals[1:]):
        if before >= 1 and after < 100:
            assert after >= 2 * before


@given(small_fractions)
def test_unit_fractions_add_back_up(x: Fraction) -> None:
    whole, denominators = unit_fractions(x)
    assert whole + sum(Fraction(1, d) for d in denominators) == x
    assert list(denominators) == sorted(set(denominators))
