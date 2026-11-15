from math import gcd, lcm, prod

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms._checks import shared_factor
from ancient_algorithms.dayan import dayan, definite_numbers, qiuyi, qiuyi_board
from ancient_algorithms.kuttaka import crt, extended_gcd, mod_inverse_kuttaka
from ancient_algorithms.sunzi import sunzi_multipliers


# Qin Jiushao, Shushu jiuzhang, chapter 1, as in the Siku Quanshu copy (數學九章 卷一).
def test_qiuyi_board_for_remainder_3_and_definite_4() -> None:
    # Divination problem (蓍卦發微): 4 by 3 gives quotient 1, lower left 1; then quotient 2
    # leaves 1 upper right, and 2 times 1 plus 1 gives the multiplier 3.
    assert qiuyi_board(3, 4) == [(1, 3, 0, 4), (1, 3, 1, 1), (3, 1, 1, 1)]
    assert qiuyi(3, 4) == 3


def test_divination_problem() -> None:
    assert definite_numbers([1, 2, 3, 4]) == [1, 1, 3, 4]
    r = dayan([(0, 1), (1, 2), (0, 3), (1, 4)])
    assert r.extension_mother == 12
    assert r.extension_numbers == [12, 12, 4, 3]
    assert r.qi == [1, 1, 1, 3]
    assert r.multipliers == [1, 1, 1, 3]
    # Qin's 泛用. He then adds the extension mother to the 2nd (定用 12, 24, 4, 9), a step left out.
    assert r.use_numbers == [12, 12, 4, 9]


def test_rice_problem() -> None:
    # 餘米推數: containers of 1 sheng 9 ge, 1 sheng 7 ge and 1 sheng 2 ge; leftovers 1, 14, 1 ge.
    r = dayan([(1, 19), (14, 17), (1, 12)])
    assert r.definite == [19, 17, 12]
    assert r.extension_mother == 3876
    assert r.extension_numbers == [204, 228, 323]
    assert r.qi == [14, 7, 11]
    assert r.multipliers == [15, 5, 11]
    assert r.use_numbers == [3060, 1140, 3553]
    assert r.total == 22573
    assert r.answer == 3193


def test_dike_problem() -> None:
    # 推計土功: daily lengths 54, 57, 75, 72 zhang; counties C and D have 51 and 18 zhang left.
    r = dayan([(0, 54), (0, 57), (51, 75), (18, 72)])
    assert r.definite == [27, 19, 25, 8]
    assert r.extension_mother == 102600
    assert r.extension_numbers == [3800, 5400, 4104, 12825]
    assert r.qi == [20, 4, 4, 1]
    assert r.multipliers == [23, 5, 19, 1]
    assert r.use_numbers == [87400, 27000, 77976, 12825]
    assert r.total == 4207626
    assert r.answer == 1026


def test_couriers_problem() -> None:
    # 程行計地: 300, 240 and 180 li a day; the last part-day covers 180 li, 60 short of a full day.
    r = dayan([(0, 300), (180, 240), (60, 180)])
    assert r.definite == [25, 16, 9]
    assert r.extension_mother == 3600
    assert r.extension_numbers == [144, 225, 400]
    assert r.qi == [19, 1, 4]
    assert r.multipliers == [4, 1, 7]
    assert r.use_numbers == [576, 225, 2800]
    assert r.total == 208500
    assert r.answer == 3300


def test_pursuit_problem_gives_the_siku_editors_definite_numbers() -> None:
    # 程行相及: Qin's text has 3, 125, 16 with product 6000; the Siku editors correct it to
    # 3, 125, 8, whose product 3000 is the lcm of 300, 250 and 200.
    assert definite_numbers([300, 250, 200]) == [3, 125, 8]


def test_divide_out_of_the_number_with_odd_quotient() -> None:
    # 約奇弗約偶, in Wylie's reading: 12 and 6 share 6; 12/6 is even, 6/6 is odd, so 6 is reduced.
    assert definite_numbers([12, 6]) == [12, 1]


def test_sunzi_problem_by_dayan() -> None:
    r = dayan([(2, 3), (3, 5), (2, 7)])
    assert r.use_numbers == [70, 21, 15]
    assert r.answer == 23


def test_bad_inputs_raise() -> None:
    with pytest.raises(ValueError):
        dayan([])
    with pytest.raises(ValueError, match=r"remainder < divisor, got \(3, 3\)"):
        dayan([(3, 3)])
    with pytest.raises(ValueError):
        dayan([(1, 0)])
    with pytest.raises(ValueError):
        dayan([(0, 4), (1, 6)])
    with pytest.raises(ValueError):
        definite_numbers([0, 3])
    with pytest.raises(ValueError):
        qiuyi(2, 4)
    with pytest.raises(ValueError):
        qiuyi(5, 4)
    with pytest.raises(ValueError):
        qiuyi(0, 4)
    with pytest.raises(ValueError):
        qiuyi(1, 0)


coprime_pair = st.integers(2, 10**12).flatmap(
    lambda m: st.tuples(st.integers(1, m - 1).filter(lambda a: gcd(a, m) == 1), st.just(m))
)


@given(coprime_pair)
def test_qiuyi_is_the_least_inverse(pair: tuple[int, int]) -> None:
    qi, m = pair
    k = qiuyi(qi, m)
    assert 1 <= k < m or m == 2
    assert qi * k % m == 1
    assert k == pow(qi, -1, m)
    assert k == mod_inverse_kuttaka(qi, m)
    g, s, _ = extended_gcd(qi, m)
    assert g == 1 and k == s % m


@given(coprime_pair)
def test_qiuyi_board_keeps_its_invariants(pair: tuple[int, int]) -> None:
    qi, m = pair
    for upper_left, upper_right, lower_left, lower_right in qiuyi_board(qi, m):
        assert upper_left > 0 and lower_left >= 0
        assert upper_left * qi % m == upper_right % m
        assert (lower_left * qi + lower_right) % m == 0


divisor_lists = st.lists(st.integers(1, 400), min_size=1, max_size=6)


@given(divisor_lists)
def test_definite_numbers_are_coprime_divisors_with_lcm_product(original: list[int]) -> None:
    definite = definite_numbers(original)
    assert all(m % d == 0 for d, m in zip(definite, original, strict=True))
    assert shared_factor(definite) is None
    assert prod(definite) == lcm(*original)


@given(divisor_lists, st.integers(0, 10**9))
def test_dayan_matches_crt_and_brute_force(original: list[int], n: int) -> None:
    pairs = [(n % d, d) for d in original]
    r = dayan(pairs)
    assert r.answer == n % lcm(*original)
    assert r.answer == crt(pairs)


@given(divisor_lists)
def test_use_numbers_add_to_1_more_than_a_multiple_of_the_mother(original: list[int]) -> None:
    # Qin's check (併泛課衍母多一者為正用): the use numbers add to 1 more than a multiple.
    r = dayan([(0, d) for d in original])
    assert sum(r.use_numbers) % r.extension_mother == 1 % r.extension_mother


@given(divisor_lists)
def test_use_numbers_are_sunzis_multipliers_for_the_definite_numbers(original: list[int]) -> None:
    definite = [d for d in definite_numbers(original) if d > 1]
    if not definite:
        return
    r = dayan([(0, d) for d in definite])
    assert r.use_numbers == sunzi_multipliers(definite)
