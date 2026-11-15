from math import gcd

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.kuttaka import (
    crt,
    extended_gcd,
    mod_inverse_euclid,
    mod_inverse_kuttaka,
    pulverize,
    remainder_problem,
    two_remainders,
)


# Bhaskara I's worked examples on Ganitapada 32-33 (Shukla 1976 edition).
def test_bhaskara_example_1():
    assert two_remainders(1, 5, 2, 7) == 16


def test_bhaskara_example_2():
    assert two_remainders(5, 12, 7, 31) == 317


def test_bhaskara_example_2_column_matches_commentary():
    # Bhaskara I stops after 2 quotients (1, 1), picks mati 4, gets 10, then 310 and 317.
    v = pulverize(31, 12, 2, stop_after=2, trace=True)
    assert v.quotients == [1, 1]
    assert v.residues[-2:] == [5, 2]
    assert v.added is True
    assert (v.mati, v.mati_quotient) == (4, 2)
    assert v.column == [1, 1, 4, 2]
    assert v.reduced[-1] == [10, 6]
    assert v.x == 10
    assert 31 * (v.x % 12) == 310


def test_bhaskara_example_1_column_matches_commentary():
    # The numbers are small, so Bhaskara I picks the mati before any division: mati 2, quotient 1.
    v = pulverize(7, 5, 1, stop_after=0)
    assert v.column == [2, 1]
    assert v.x == 2
    assert 7 * v.x + 2 == 16


def test_bhaskara_example_3_three_divisors():
    # Bhaskara I folds the first 2 pairs into 13 with divisor 72, then adds the third.
    assert two_remainders(5, 8, 4, 9) == 13
    assert two_remainders(13, 72, 1, 7) == 85
    assert remainder_problem([(5, 8), (4, 9), (1, 7)]) == 85


def test_bhaskara_example_5_without_remainders():
    # The column and fold as printed in the commentary.
    v = pulverize(8, 13, 6, trace=True)
    assert v.column == [1, 1, 1, 1, 2, 4]
    assert v.reduced[-1] == [22, 14]
    assert v.x == 9
    assert (8 * v.x + 6) // 13 == 6


def test_bhaskara_example_6_without_remainders():
    v = pulverize(11, 23, -3)
    assert v.x == 17
    assert (11 * v.x - 3) // 23 == 8


def test_bhaskara_example_4_non_coprime_divisors():
    assert remainder_problem([(1, d) for d in range(2, 7)] + [(0, 7)]) == 301


def test_paramesvara_example_from_clark():
    # Clark (1930), p. 47: agras 15 and 11 with divisors 29 and 45 give 1001.
    assert two_remainders(15, 29, 11, 45) == 1001


def test_rsa_textbook_private_exponent():
    # p = 61, q = 53, phi = 3120, e = 17 gives d = 2753.
    assert mod_inverse_kuttaka(17, 3120) == 2753
    assert mod_inverse_euclid(17, 3120) == 2753
    assert pow(17, -1, 3120) == 2753


def test_bad_inputs_raise():
    with pytest.raises(ValueError):
        pulverize(3, 0, 1)
    with pytest.raises(ValueError):
        pulverize(3, 7, 1, stop_after=-1)
    with pytest.raises(ValueError):
        remainder_problem([(7, 5), (2, 7)])
    with pytest.raises(ValueError):
        remainder_problem([(1, 0)])
    with pytest.raises(ValueError):
        remainder_problem([(7, 5)])
    with pytest.raises(ValueError):
        mod_inverse_kuttaka(1, 0)
    with pytest.raises(ValueError):
        mod_inverse_euclid(3, 0)


def test_early_stop_with_a_large_divisor_is_fast():
    # Past TRIAL_LIMIT the mati is solved directly, so this returns at once.
    m = 2**61 - 1
    assert pulverize(3, m, 1, stop_after=0).x == (-pow(3, -1, m)) % m


def test_no_solution_raises():
    with pytest.raises(ValueError):
        pulverize(6, 9, 4)
    with pytest.raises(ValueError):
        two_remainders(0, 4, 1, 6)
    with pytest.raises(ValueError):
        mod_inverse_kuttaka(6, 9)


small = st.integers(min_value=-10_000, max_value=10_000)
modulus = st.integers(min_value=1, max_value=10_000)


@given(a=small, b=modulus, c=small, stop=st.one_of(st.none(), st.integers(0, 12)))
def test_pulverize_solves_whenever_a_solution_exists(a, b, c, stop):
    if c % gcd(a, b):
        with pytest.raises(ValueError):
            pulverize(a, b, c, stop_after=stop)
        return
    v = pulverize(a, b, c, stop_after=stop, trace=True)
    x = v.x
    assert (a * x + c) % b == 0
    assert 0 <= x < b // gcd(a, b)
    if v.b > 1:
        n = v.divisions
        sign = 1 if v.added else -1
        upper, lower = v.residues[n + 1], v.residues[n]
        assert upper * v.mati + sign * v.c == lower * v.mati_quotient
        assert v.reduced[-1][0] % v.b == x


def test_common_factor_is_removed_first():
    # Bhaskara I's apavartana: 6x + 3 = 0 (mod 9) becomes 2x + 1 = 0 (mod 3).
    v = pulverize(6, 9, 3)
    assert (v.a, v.b, v.c) == (2, 3, 1)
    assert v.x == 1


@given(a=small, b=modulus, c=small, stop=st.integers(0, 12))
def test_stopping_early_gives_the_same_answer(a, b, c, stop):
    if c % gcd(a, b):
        return
    g = gcd(a, b)
    assert pulverize(a, b, c, stop_after=stop).x % (b // g) == pulverize(a, b, c).x % (b // g)


@given(d1=st.integers(1, 500), d2=st.integers(1, 500), data=st.data())
def test_two_remainders_matches_crt(d1, d2, data):
    r1 = data.draw(st.integers(0, d1 - 1))
    r2 = data.draw(st.integers(0, d2 - 1))
    if (r1 - r2) % gcd(d1, d2):
        with pytest.raises(ValueError):
            two_remainders(r1, d1, r2, d2)
        return
    n = two_remainders(r1, d1, r2, d2)
    assert n % d1 == r1 and n % d2 == r2
    assert n == crt([(r1, d1), (r2, d2)])


@given(a=st.integers(1, 10**30), m=st.integers(2, 10**30))
def test_inverse_agrees_with_euclid_and_pow(a, m):
    if gcd(a, m) != 1:
        return
    inv = mod_inverse_kuttaka(a, m)
    assert inv == mod_inverse_euclid(a, m) == pow(a, -1, m)


@given(a=small, b=small)
def test_extended_gcd_bezout(a, b):
    g, s, t = extended_gcd(a, b)
    assert a * s + b * t == g
    assert g == gcd(a, b)


def test_bhaskara_example_22_day_count():
    # Example 22 on Ganitapada 32-33; Bhaskara I divides by 7,500 first, as pulverize does.
    v = pulverize(4_320_000, 1_577_917_500, -82_500)
    assert (v.a, v.b) == (576, 210_389)
    assert v.x == 199_066
    assert (4_320_000 * v.x - 82_500) // 1_577_917_500 == 545
