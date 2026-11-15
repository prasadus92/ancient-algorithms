from collections.abc import Sequence
from fractions import Fraction
from math import isclose

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.completing_square import (
    Number,
    complete_the_square,
    quadratic_formula,
    roots_and_numbers_equal_squares,
    roots_equal_numbers,
    squares_and_numbers_equal_roots,
    squares_and_roots_equal_numbers,
    squares_equal_numbers,
    squares_equal_roots,
)

half, third = Fraction(1, 2), Fraction(1, 3)
positive = st.integers(1, 1000)


# Worked examples from Rosen's 1831 translation, pp. 6 to 13.
def test_squares_equal_roots_examples() -> None:
    assert squares_equal_roots(1, 5) == 5
    assert squares_equal_roots(third, 4) == 12
    assert squares_equal_roots(5, 10) == 2


def test_squares_equal_numbers_examples() -> None:
    assert squares_equal_numbers(1, 9) == 3
    assert squares_equal_numbers(5, 80) == 4
    assert squares_equal_numbers(half, 18) == 6


def test_roots_equal_numbers_examples() -> None:
    assert roots_equal_numbers(1, 3) == 3
    assert roots_equal_numbers(4, 20) == 5
    assert roots_equal_numbers(half, 10) == 20


def test_a_square_and_ten_roots_equal_thirty_nine() -> None:
    root = squares_and_roots_equal_numbers(1, 10, 39)
    assert isinstance(root, Fraction)
    assert root == 3


def test_two_squares_and_half_a_square_are_reduced_to_one() -> None:
    assert squares_and_roots_equal_numbers(2, 10, 48) == 3
    assert squares_and_roots_equal_numbers(half, 5, 28) == 4


def test_a_square_and_twenty_one_equal_ten_roots_has_two_answers() -> None:
    assert squares_and_numbers_equal_roots(1, 21, 10) == (3, 7)


def test_type_5_impossible_and_single_cases() -> None:
    assert squares_and_numbers_equal_roots(1, 26, 10) == ()
    assert squares_and_numbers_equal_roots(1, 25, 10) == (5,)


def test_three_roots_and_four_equal_a_square() -> None:
    assert roots_and_numbers_equal_squares(1, 3, 4) == 4


def test_the_figure_with_four_strips() -> None:
    # Rosen pp. 13 to 15: strips of 2 1/2, corners 25, great square 64, side 8, root 3.
    figure = complete_the_square(10, 39)
    assert figure.breadth == Fraction(5, 2)
    assert [figure.corners, figure.area, figure.side, figure.root] == [25, 64, 8, 3]


def test_the_figure_with_two_strips_gives_the_same_square() -> None:
    # Rosen pp. 15 to 16: strips of 5 on 2 sides and 1 corner of 5 by 5.
    figure = complete_the_square(10, 39, strips=2)
    assert [figure.breadth, figure.corners, figure.side, figure.root] == [5, 25, 8, 3]


def test_bm_13901_problem_1() -> None:
    # Old Babylonian: area plus side is 45 sixtieths; the side is 30 sixtieths (Hoyrup 2017).
    assert squares_and_roots_equal_numbers(1, 1, Fraction(45, 60)) == Fraction(30, 60)


def test_irrational_answers_fall_back_to_float() -> None:
    assert isclose(squares_and_roots_equal_numbers(1, 2, 1), 2**0.5 - 1)


def test_coefficients_must_be_positive() -> None:
    with pytest.raises(ValueError, match="number must be positive, got -39"):
        squares_and_roots_equal_numbers(1, 10, -39)
    with pytest.raises(ValueError, match="squares must be positive, got 0"):
        squares_equal_roots(0, 5)
    with pytest.raises(ValueError, match="4 strips or 2, got 3"):
        complete_the_square(10, 39, strips=3)


def _same(rule: Sequence[Number], formula: Sequence[float]) -> bool:
    return len(rule) == len(formula) and all(
        isclose(float(r), f, rel_tol=1e-9, abs_tol=1e-9) for r, f in zip(rule, formula, strict=True)
    )


@given(c=positive, b=positive, a=positive)
def test_type_4_matches_the_formula(c: int, b: int, a: int) -> None:
    root = squares_and_roots_equal_numbers(c, b, a)
    assert _same((root,), [r for r in quadratic_formula(c, b, -a) if r > 0])


@given(c=positive, b=positive, a=positive)
def test_type_5_matches_the_formula(c: int, b: int, a: int) -> None:
    roots = squares_and_numbers_equal_roots(c, a, b)
    expected = quadratic_formula(c, -b, a)
    if len(expected) == 2 and isclose(*expected, rel_tol=1e-12):
        return  # a double root the float formula splits in 2
    assert _same(roots, expected)


@given(c=positive, b=positive, a=positive)
def test_type_6_matches_the_formula(c: int, b: int, a: int) -> None:
    root = roots_and_numbers_equal_squares(c, b, a)
    assert _same((root,), [r for r in quadratic_formula(c, -b, -a) if r > 0])


@given(b=positive, a=positive)
def test_both_figures_agree_with_the_rule(b: int, a: int) -> None:
    four, two = complete_the_square(b, a), complete_the_square(b, a, strips=2)
    assert four.area == two.area
    assert four.root == two.root == squares_and_roots_equal_numbers(1, b, a)
