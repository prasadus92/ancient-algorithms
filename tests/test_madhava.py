from decimal import Decimal

import pytest

from old_algorithms.madhava import (
    PI_100,
    correct_digits,
    correction,
    machin_pi,
    madhava_pi,
    madhava_sqrt12_pi,
    partial_sum,
)


def test_reference_pi_digits():
    assert str(PI_100).startswith("3.14159265358979323846")


def test_partial_sum_small_cases():
    assert partial_sum(0) == 0
    assert partial_sum(1) == 1
    assert abs(partial_sum(2) - Decimal(2) / 3) < Decimal("1e-25")


def test_bare_series_converges_slowly():
    # 50 terms of the bare series give only 1 correct decimal place.
    assert correct_digits(madhava_pi(50)) == 1


@pytest.mark.parametrize("n", [10, 20, 40, 80])
def test_each_correction_beats_the_previous(n):
    errors = [abs(madhava_pi(n, order) - PI_100) for order in range(4)]
    assert errors[0] > errors[1] > errors[2] > errors[3]


@pytest.mark.parametrize("order,exponent", [(1, 3), (2, 5), (3, 7)])
def test_error_falls_as_a_power_of_n(order, exponent):
    # Doubling n should divide the error by about 2**exponent.
    e1 = abs(madhava_pi(40, order) - PI_100)
    e2 = abs(madhava_pi(80, order) - PI_100)
    ratio = float(e1 / e2)
    assert 2 ** (exponent - 0.5) < ratio < 2 ** (exponent + 0.5)


def test_third_correction_with_50_terms():
    assert correct_digits(madhava_pi(50, 3)) >= 12


def test_sqrt12_series_and_machin():
    assert correct_digits(madhava_sqrt12_pi(21)) >= 10
    assert correct_digits(machin_pi(10)) >= 14


def test_invalid_inputs():
    with pytest.raises(ValueError):
        correction(5, 4)
    with pytest.raises(ValueError):
        madhava_pi(0)
