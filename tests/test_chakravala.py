from fractions import Fraction
from math import gcd, isqrt

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from ancient_algorithms.chakravala import (
    bhavana,
    chakravala,
    chakravala_step,
    choose_multiplier,
    complete_by_bhavana,
    pell_continued_fraction,
    starting_triple,
)

non_squares = st.integers(min_value=2, max_value=200).filter(lambda n: isqrt(n) ** 2 != n)


def smallest_solution_by_search(n: int, limit: int) -> tuple[int, int]:
    """Smallest y >= 1 with n*y^2 + 1 a square, by trying y = 1, 2, 3, ..."""
    for y in range(1, limit + 1):
        x = isqrt(n * y * y + 1)
        if x * x == n * y * y + 1:
            return y, x
    raise AssertionError(f"no solution with y <= {limit}")


# Bhaskara II, Bijaganita section 87, as translated by Colebrooke (1817), pp. 176 to 178.
def test_bhaskara_n67_rounds_match_the_text() -> None:
    record = chakravala(67)
    assert record.triples == [(1, 8, -3), (5, 41, 6), (11, 90, -7), (27, 221, -2)]
    assert record.multipliers == [7, 5, 9]


def test_bhaskara_n67_composition_and_halving() -> None:
    # Composing (27, 221, -2) with itself gives ksepa 4, then halving gives ksepa 1.
    assert bhavana((27, 221, -2), (27, 221, -2), 67) == (11934, 97684, 4)
    assert chakravala(67).solution == (5967, 48842, 1)


def test_bhaskara_n61_rounds_match_the_text() -> None:
    record = chakravala(61)
    assert record.triples == [(1, 8, 3), (5, 39, -4)]
    assert record.multipliers == [7]
    assert record.finished_by_bhavana


def test_bhaskara_n61_route_through_minus_one() -> None:
    # Halve to (5/2, 39/2, -1), compose twice to reach (3805, 29718, -1), then square.
    half = (Fraction(5, 2), Fraction(39, 2), -1)
    twice = bhavana(half, half, 61)
    thrice = bhavana(twice, half, 61)
    assert thrice == (Fraction(3805), Fraction(29718), -1)
    assert bhavana((3805, 29718, -1), (3805, 29718, -1), 61) == (226153980, 1766319049, 1)


def test_bhaskara_n61_answer() -> None:
    assert chakravala(61).solution == (226153980, 1766319049, 1)
    assert chakravala(61, shortcut=False).solution == (226153980, 1766319049, 1)


# Bijaganita section 82, Colebrooke pp. 173 to 174: N = 8 and N = 11 by composition alone.
def test_bhaskara_section_82_compositions() -> None:
    assert bhavana((1, 3, 1), (1, 3, 1), 8) == (6, 17, 1)
    assert bhavana((1, 3, 1), (6, 17, 1), 8) == (35, 99, 1)
    assert bhavana((1, 3, -2), (1, 3, -2), 11) == (6, 20, 4)
    assert bhavana((3, 10, 1), (3, 10, 1), 11) == (60, 199, 1)


def test_bhavana_by_difference() -> None:
    assert bhavana((6, 17, 1), (1, 3, 1), 8, difference=True) == (1, -3, 1)


def test_starting_triple_takes_the_nearest_square() -> None:
    assert starting_triple(61) == (1, 8, 3)
    assert starting_triple(67) == (1, 8, -3)
    assert starting_triple(2) == (1, 1, -1)


def test_choose_multiplier_keeps_the_remainder_small() -> None:
    # For (1, 8, -3) and N = 67, m can be 1, 4, 7, 10, ...; 7 gives |49 - 67| = 18.
    assert choose_multiplier((1, 8, -3), 67) == 7


def test_choose_multiplier_breaks_a_tie_below_the_root() -> None:
    # For (1, 8, 6) and N = 58, m = 4 and m = 10 both leave 42; the text does not choose.
    assert choose_multiplier((1, 8, 6), 58) == 4


def test_pell_continued_fraction_known_values() -> None:
    assert pell_continued_fraction(61)[:2] == (1766319049, 226153980)
    assert pell_continued_fraction(67)[:2] == (48842, 5967)
    assert pell_continued_fraction(2) == (3, 2, 1)


def test_cycle_uses_fewer_rounds_than_the_continued_fraction() -> None:
    assert chakravala(61, shortcut=False).rounds < pell_continued_fraction(61)[2]
    assert chakravala(67, shortcut=False).rounds < pell_continued_fraction(67)[2]


@pytest.mark.parametrize("n", [n for n in range(2, 61) if isqrt(n) ** 2 != n])
def test_matches_brute_force_search(n: int) -> None:
    y, x = smallest_solution_by_search(n, 10_000)
    assert chakravala(n).solution == (y, x, 1)
    assert chakravala(n, shortcut=False).solution == (y, x, 1)


@given(non_squares)
def test_cycle_matches_continued_fraction(n: int) -> None:
    x, y, _ = pell_continued_fraction(n)
    assert chakravala(n, shortcut=False).solution == (y, x, 1)


@given(non_squares)
def test_shortcut_gives_the_same_fundamental_solution(n: int) -> None:
    assert chakravala(n).solution == chakravala(n, shortcut=False).solution


@given(non_squares)
def test_every_round_keeps_the_identity(n: int) -> None:
    for kanistha, jyestha, ksepa in chakravala(n, shortcut=False).triples:
        assert n * kanistha * kanistha + ksepa == jyestha * jyestha


@given(
    non_squares,
    st.integers(min_value=-50, max_value=50),
    st.integers(min_value=-50, max_value=50),
    st.integers(min_value=-50, max_value=50),
    st.integers(min_value=-50, max_value=50),
    st.booleans(),
)
def test_bhavana_preserves_the_identity(
    n: int, k1: int, j1: int, k2: int, j2: int, difference: bool
) -> None:
    e1 = j1 * j1 - n * k1 * k1
    e2 = j2 * j2 - n * k2 * k2
    k, j, e = bhavana((k1, j1, e1), (k2, j2, e2), n, difference=difference)
    assert n * k * k + e == j * j


@given(non_squares, st.integers(min_value=1, max_value=200))
def test_cycle_from_another_start(n: int, kanistha: int) -> None:
    jyestha = isqrt(n * kanistha * kanistha) + 1
    ksepa = jyestha * jyestha - n * kanistha * kanistha
    assume(gcd(kanistha, jyestha) == 1)
    solution = chakravala(n, start=(kanistha, jyestha, ksepa)).solution
    assert n * solution[0] ** 2 + 1 == solution[1] ** 2


@pytest.mark.parametrize("n", [0, 1, -3])
def test_rejects_n_below_2(n: int) -> None:
    with pytest.raises(ValueError, match="n must be at least 2"):
        chakravala(n)


@pytest.mark.parametrize("n", [0, 1, 4, 49, -3])
def test_rejects_squares_and_small_n(n: int) -> None:
    with pytest.raises(ValueError):
        chakravala(n)
    with pytest.raises(ValueError):
        pell_continued_fraction(n)


def test_another_start_can_give_a_larger_solution() -> None:
    assert chakravala(2, start=(5, 7, -1)).solution == (70, 99, 1)
    assert chakravala(2).solution == (2, 3, 1)


@pytest.mark.parametrize("n", [n for n in range(2, 201) if isqrt(n) ** 2 != n])
def test_every_ksepa_four_triple_completes(n: int) -> None:
    for triple in chakravala(n, shortcut=False).triples:
        if abs(triple[2]) == 4:
            k, j, e = complete_by_bhavana(triple, n)
            assert e == 1 and n * k * k + 1 == j * j


def test_rejects_a_bad_triple() -> None:
    with pytest.raises(ValueError):
        chakravala(61, start=(1, 8, 4))
    with pytest.raises(ValueError):
        chakravala(61, start=(1, 8, 1))
    with pytest.raises(ValueError):
        chakravala(2, start=(6, 9, 9))
    with pytest.raises(ValueError):
        chakravala(2, start=(0, 1, 1))
    with pytest.raises(ValueError):
        complete_by_bhavana((1, 9, 20), 61)


def test_rejects_a_multiplier_that_does_not_divide() -> None:
    with pytest.raises(ValueError):
        chakravala_step((1, 8, 3), 61, 5)
