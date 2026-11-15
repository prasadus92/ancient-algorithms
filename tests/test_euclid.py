import time
import tracemalloc
from fractions import Fraction
from math import gcd

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ancient_algorithms.euclid import (
    anthyphairesis,
    division_count,
    division_quotients,
    fibonacci_pair,
    greatest_common_measure,
    lame_bound,
    prime_to_one_another,
    subtraction_count,
)

numbers = st.integers(min_value=1, max_value=10**6)
# Subtraction is linear in the quotients, so its inputs stay small.
small_numbers = st.integers(min_value=1, max_value=10**4)


def test_subtraction_in_turn_for_54_and_15() -> None:
    assert list(anthyphairesis(54, 15)) == [
        (54, 15),
        (39, 15),
        (24, 15),
        (9, 15),
        (9, 6),
        (3, 6),
        (3, 3),
    ]
    assert greatest_common_measure(54, 15) == 3
    assert subtraction_count(54, 15) == 6


def test_vii_1_ends_on_a_unit() -> None:
    # Granville (2024) works 41 and 12: 41 - 3*12 = 5, 12 - 2*5 = 2, 5 - 2*2 = 1.
    assert list(anthyphairesis(41, 12))[-1] == (1, 1)
    assert prime_to_one_another(41, 12)
    assert division_quotients(41, 12) == [3, 2, 2, 2]


def test_vii_2_when_the_less_measures_the_greater() -> None:
    # VII.2 opens with this case: CD measures AB, so CD is the greatest common measure.
    assert greatest_common_measure(36, 12) == 12
    assert not prime_to_one_another(36, 12)


def test_order_of_arguments_does_not_matter() -> None:
    assert greatest_common_measure(15, 54) == greatest_common_measure(54, 15) == 3


def test_unit_and_equal_numbers() -> None:
    assert list(anthyphairesis(7, 7)) == [(7, 7)]
    assert subtraction_count(10_000, 1) == 9_999


def test_a_long_run_is_counted_in_constant_memory() -> None:
    tracemalloc.start()
    start = time.perf_counter()
    count = subtraction_count(10**12, 1)
    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert count == 10**12 - 1
    assert greatest_common_measure(10**12, 1) == 1
    assert elapsed < 1
    assert peak < 100_000


def test_anthyphairesis_yields_lazily() -> None:
    pairs = anthyphairesis(10**12, 1)
    assert next(pairs) == (10**12, 1)
    assert next(pairs) == (10**12 - 1, 1)


@pytest.mark.parametrize("a, b", [(0, 5), (5, 0), (-3, 4)])
def test_rejects_non_numbers(a: int, b: int) -> None:
    with pytest.raises(ValueError, match="must be at least 1"):
        anthyphairesis(a, b)
    with pytest.raises(ValueError, match="must be at least 1"):
        division_quotients(a, b)


def test_lame_example_1597_and_987() -> None:
    # Lamé counts 14 divisions to the remainder 1; the 15th leaves 0. His bound is 15.
    assert division_count(1597, 987) == 15
    assert lame_bound(1597, 987) == 15


def test_lame_bound_above_python_str_digit_limit() -> None:
    big = 10**5000
    assert lame_bound(big + 1, big) == 5 * 5001


def test_fibonacci_pairs() -> None:
    assert [fibonacci_pair(n) for n in range(1, 6)] == [(2, 1), (3, 2), (5, 3), (8, 5), (13, 8)]
    with pytest.raises(ValueError, match="n must be at least 1"):
        fibonacci_pair(0)


@given(small_numbers, small_numbers)
def test_subtraction_matches_math_gcd(a: int, b: int) -> None:
    assert greatest_common_measure(a, b) == gcd(a, b)
    assert prime_to_one_another(a, b) == (gcd(a, b) == 1)


@given(small_numbers, small_numbers)
def test_a_common_measure_measures_the_greatest(a: int, b: int) -> None:
    # The porism to VII.2.
    g = greatest_common_measure(a, b)
    for d in range(1, 50):
        if a % d == 0 and b % d == 0:
            assert g % d == 0


@given(small_numbers, small_numbers)
def test_subtractions_are_the_quotients_summed_less_1(a: int, b: int) -> None:
    assert subtraction_count(a, b) == sum(division_quotients(a, b)) - 1


@given(numbers, numbers)
def test_quotients_rebuild_the_ratio(a: int, b: int) -> None:
    *head, last = division_quotients(a, b)
    value = Fraction(last)
    for q in reversed(head):
        value = q + 1 / value
    assert value == Fraction(max(a, b), min(a, b))


@settings(max_examples=50)
@given(st.integers(min_value=1, max_value=10**60), st.integers(min_value=1, max_value=10**60))
def test_lame_bound_holds(a: int, b: int) -> None:
    assert division_count(a, b) <= lame_bound(a, b)


@given(numbers, numbers)
def test_fibonacci_pair_is_the_worst_case(a: int, b: int) -> None:
    a, b = max(a, b), min(a, b)
    if a == b:
        return
    n = division_count(a, b)
    big, small = fibonacci_pair(n)
    assert a >= big and b >= small


@pytest.mark.parametrize("n", range(1, 40))
def test_fibonacci_pair_needs_exactly_n_divisions(n: int) -> None:
    big, small = fibonacci_pair(n)
    assert division_count(big, small) == n
    assert set(division_quotients(big, small)[:-1]) <= {1}


def test_smallest_pairs_by_brute_force() -> None:
    # For each n, the smallest a > b needing n divisions is a Fibonacci pair.
    smallest: dict[int, tuple[int, int]] = {}
    for a in range(2, 200):
        for b in range(1, a):
            smallest.setdefault(division_count(a, b), (a, b))
    for n, pair in smallest.items():
        assert pair == fibonacci_pair(n)
