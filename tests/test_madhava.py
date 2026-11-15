from decimal import Decimal

import pytest

from ancient_algorithms.madhava import (
    PI_100,
    correct_digits,
    correction,
    machin_pi,
    madhava_pi,
    madhava_sqrt12_pi,
    partial_sum,
)


def test_reference_pi_digits() -> None:
    assert str(PI_100).startswith("3.14159265358979323846")


def test_partial_sum_small_cases() -> None:
    assert partial_sum(0) == 0
    assert partial_sum(1) == 1
    assert abs(partial_sum(2) - Decimal(2) / 3) < Decimal("1e-25")


def test_bare_series_converges_slowly() -> None:
    assert correct_digits(madhava_pi(50)) == 1


@pytest.mark.parametrize("n", [10, 20, 40, 80])
def test_each_correction_beats_the_previous(n: int) -> None:
    errors = [abs(madhava_pi(n, order) - PI_100) for order in range(4)]
    assert errors[0] > errors[1] > errors[2] > errors[3]


@pytest.mark.parametrize("order,exponent", [(1, 3), (2, 5), (3, 7)])
def test_error_falls_as_a_power_of_n(order: int, exponent: int) -> None:
    # Doubling n should divide the error by about 2**exponent.
    e1 = abs(madhava_pi(40, order) - PI_100)
    e2 = abs(madhava_pi(80, order) - PI_100)
    ratio = float(e1 / e2)
    assert 2 ** (exponent - 0.5) < ratio < 2 ** (exponent + 0.5)


def test_third_correction_with_50_terms() -> None:
    assert correct_digits(madhava_pi(50, 3)) >= 12


def test_sqrt12_series_and_machin() -> None:
    assert correct_digits(madhava_sqrt12_pi(21)) >= 10
    assert correct_digits(machin_pi(10)) >= 14


def test_machin_values_match_term_by_term_rounding() -> None:
    assert str(machin_pi(41)) == "3.14159265358979323846264338327950288419716939937510582097494"
    assert str(machin_pi(3, 5)) == "3.1415"


def test_invalid_inputs() -> None:
    with pytest.raises(ValueError):
        correction(5, 4)
    with pytest.raises(ValueError):
        madhava_pi(0)
