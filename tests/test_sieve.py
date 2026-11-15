from collections.abc import Callable
from itertools import pairwise

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from ancient_algorithms.euclid import prime_to_one_another
from ancient_algorithms.sieve import (
    crossing_count,
    koskinon,
    mark_count,
    odd_primes,
    segmented_sieve,
    sieve_of_eratosthenes,
    trial_division,
    wheel_sieve,
)

PRIMES_TO_100 = [
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
    53, 59, 61, 67, 71, 73, 79, 83, 89, 97,
]  # fmt: skip

limits = st.integers(min_value=0, max_value=2000)


# Nicomachus, Introduction to Arithmetic I.13.3 to 13.5 (D'Ooge 1926, p. 204).
def test_3_measures_every_term_2_places_on() -> None:
    marked = [n for n, measures in koskinon(99).items() if 3 in measures]
    assert marked[:4] == [9, 15, 21, 27]
    assert [n // 3 for n in marked[:4]] == [3, 5, 7, 9]


def test_5_measures_every_term_4_places_on() -> None:
    marked = [n for n, measures in koskinon(99).items() if 5 in measures]
    assert marked[:3] == [15, 25, 35]
    assert [n // 5 for n in marked[:3]] == [3, 5, 7]


def test_7_measures_every_term_6_places_on() -> None:
    marked = [n for n, measures in koskinon(99).items() if 7 in measures]
    assert marked[:3] == [21, 35, 49]


@settings(max_examples=20)
@given(st.integers(min_value=1, max_value=40))
def test_the_term_in_position_k_skips_2k_terms(k: int) -> None:
    marks = koskinon(2000)
    series = list(marks)
    measure = series[k - 1]
    marked = [k - 1] + [i for i, n in enumerate(series) if measure in marks[n]]
    assert all(later - earlier - 1 == 2 * k for earlier, later in pairwise(marked))


def test_composites_take_a_turn_as_measures() -> None:
    # The literal reading: 9 and 15 also measure, so 45 carries 4 marks.
    assert koskinon(45)[45] == [3, 5, 9, 15]


def test_nicomachus_example_9_and_25() -> None:
    # I.13.1: each is composite, and they are prime to one another.
    marks = koskinon(25)
    assert marks[9] and marks[25]
    assert prime_to_one_another(9, 25)


def test_odd_primes_to_100() -> None:
    assert odd_primes(100) == PRIMES_TO_100[1:]


def test_sieve_to_100() -> None:
    assert sieve_of_eratosthenes(100) == PRIMES_TO_100
    assert len(PRIMES_TO_100) == 25


def test_crossings_to_100() -> None:
    assert crossing_count(100) == 104
    assert crossing_count(100, start_at_square=False) == 113
    assert mark_count(100) == 56


def test_crossing_out_from_the_square_misses_nothing() -> None:
    for limit in range(0, 500):
        assert sieve_of_eratosthenes(limit) == trial_division(limit)


@pytest.mark.parametrize("limit", [0, 1, 2, 3, 4, 5, 6, 7, 29, 30, 31])
def test_small_limits(limit: int) -> None:
    expected = [p for p in PRIMES_TO_100 if p <= limit]
    assert sieve_of_eratosthenes(limit) == expected
    assert segmented_sieve(limit) == expected
    assert wheel_sieve(limit) == expected
    assert odd_primes(limit) == [p for p in expected if p > 2]


@given(limits)
def test_nicomachus_matches_trial_division(limit: int) -> None:
    assert odd_primes(limit) == [p for p in trial_division(limit) if p > 2]


@given(limits)
def test_standard_sieve_matches_trial_division(limit: int) -> None:
    assert sieve_of_eratosthenes(limit) == trial_division(limit)


@given(limits, st.integers(min_value=1, max_value=200))
def test_segmented_sieve_matches_trial_division(limit: int, segment_size: int) -> None:
    assert segmented_sieve(limit, segment_size) == trial_division(limit)


@given(limits)
def test_wheel_sieve_matches_trial_division(limit: int) -> None:
    assert wheel_sieve(limit) == trial_division(limit)


def test_sieves_agree_at_100_000() -> None:
    expected = sieve_of_eratosthenes(10**5)
    assert len(expected) == 9_592
    assert segmented_sieve(10**5) == expected
    assert wheel_sieve(10**5) == expected
    assert [2, *odd_primes(10**5)] == expected


@pytest.mark.parametrize(
    "call",
    [koskinon, trial_division, sieve_of_eratosthenes, crossing_count, segmented_sieve, wheel_sieve],
)
def test_rejects_negative_limit(call: Callable[[int], object]) -> None:
    with pytest.raises(ValueError, match="limit must be at least 0, got -1"):
        call(-1)


def test_rejects_empty_segment() -> None:
    with pytest.raises(ValueError, match="segment_size must be at least 1, got 0"):
        segmented_sieve(100, 0)
