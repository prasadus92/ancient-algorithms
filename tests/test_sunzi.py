from itertools import product
from math import prod

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms._checks import shared_factor
from ancient_algorithms.kuttaka import crt, remainder_problem
from ancient_algorithms.sunzi import (
    SUNZI_DIVISORS,
    SUNZI_MULTIPLIERS,
    SUNZI_PERIOD,
    sunzi_general,
    sunzi_multipliers,
    sunzi_recipe,
)


def test_sunzi_problem_answer_is_23() -> None:
    assert sunzi_recipe(2, 3, 2) == 23


def test_sunzi_worked_line() -> None:
    # "置一百四十 ... 置六十三 ... 置三十。并之，得二百三十三，以二百一十減之".
    terms = [r * m for r, m in zip((2, 3, 2), SUNZI_MULTIPLIERS, strict=True)]
    assert terms == [140, 63, 30]
    assert sum(terms) == 233
    assert sum(terms) - 210 == 23


def test_multipliers_leave_1_with_own_divisor_and_0_with_the_others() -> None:
    for i, (m, d) in enumerate(zip(SUNZI_MULTIPLIERS, SUNZI_DIVISORS, strict=True)):
        assert m % d == 1
        assert all(m % other == 0 for j, other in enumerate(SUNZI_DIVISORS) if j != i)


def test_multipliers_are_rebuilt_from_the_divisors() -> None:
    assert sunzi_multipliers(SUNZI_DIVISORS) == list(SUNZI_MULTIPLIERS)
    assert prod(SUNZI_DIVISORS) == SUNZI_PERIOD


def test_general_recipe_on_sunzi_problem() -> None:
    assert sunzi_general([(2, 3), (3, 5), (2, 7)]) == 23


def test_qin_rice_problem_by_sunzi_recipe() -> None:
    # Qin Jiushao's rice problem: containers of 19, 17 and 12 ge, leftovers 1, 14 and 1.
    assert sunzi_general([(1, 19), (14, 17), (1, 12)]) == 3193


def test_all_zero_remainders_give_0() -> None:
    assert sunzi_recipe(0, 0, 0) == 0


def test_bad_inputs_raise() -> None:
    with pytest.raises(ValueError):
        sunzi_recipe(3, 0, 0)
    with pytest.raises(ValueError):
        sunzi_recipe(0, -1, 0)
    with pytest.raises(ValueError):
        sunzi_general([])
    with pytest.raises(ValueError):
        sunzi_general([(5, 3), (1, 5)])
    with pytest.raises(ValueError, match="divisors 4 and 6 share the factor 2"):
        sunzi_general([(0, 4), (1, 6)])
    with pytest.raises(ValueError):
        sunzi_multipliers([4, 6])
    with pytest.raises(ValueError):
        sunzi_multipliers([1, 5])


def test_recipe_on_all_105_remainder_triples() -> None:
    for r3, r5, r7 in product(range(3), range(5), range(7)):
        n = sunzi_recipe(r3, r5, r7)
        assert (n % 3, n % 5, n % 7) == (r3, r5, r7)
        assert 0 <= n < 105
        assert n == crt([(r3, 3), (r5, 5), (r7, 7)])
        assert n == remainder_problem([(r3, 3), (r5, 5), (r7, 7)])


coprime_divisors = st.lists(st.integers(2, 10_000), min_size=1, max_size=6).filter(
    lambda divisors: shared_factor(divisors) is None
)


@given(coprime_divisors, st.data())
def test_general_recipe_matches_crt(divisors: list[int], data: st.DataObject) -> None:
    pairs = [(data.draw(st.integers(0, d - 1)), d) for d in divisors]
    n = sunzi_general(pairs)
    assert 0 <= n < prod(divisors)
    assert all(n % d == r for r, d in pairs)
    assert n == crt(pairs)


@given(coprime_divisors)
def test_multipliers_have_sunzis_property(divisors: list[int]) -> None:
    for i, m in enumerate(sunzi_multipliers(divisors)):
        assert m % divisors[i] == 1
        assert all(m % d == 0 for j, d in enumerate(divisors) if j != i)
