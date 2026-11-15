from math import comb

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.pingala import (
    binary_pattern,
    binary_row,
    lagakriya,
    matra_count,
    matra_prastara,
    meru_prastara,
    modern_lagakriya,
    modern_prastara,
    nashta,
    prastara,
    sankhya,
    sankhya_marks,
    total_through,
    uddishta,
)


# Worked examples from Halayudha's Mrtasanjivani, 1874 Bibliotheca Indica edition, chapter 8.
def test_two_syllable_prastara_matches_halayudha() -> None:
    # On 8.21: "gau lgau glau lau".
    assert prastara(2) == ["gg", "lg", "gl", "ll"]


def test_three_syllable_rows_are_the_8_ganas_in_order() -> None:
    # On 8.23 vasavas trikah: the 8 triplets are the ganas ma, ya, ra, sa, ta, ja, bha, na.
    assert prastara(3) == ["ggg", "lgg", "glg", "llg", "ggl", "lgl", "gll", "lll"]


def test_halayudha_nashta_example_sixth_row_of_six() -> None:
    # On 8.24-8.25: the 6th 6-syllable pattern; halve 6 for l, 3 is odd so g, 2 gives l, then g.
    assert nashta(6, 6) == "lglggg"


def test_uddishta_inverts_the_nashta_example() -> None:
    assert uddishta("lglggg") == 6


def test_halayudha_count_for_six_syllables() -> None:
    # On 8.28-8.31: marks 2, 0, 2, 0; from the bottom 2, 4, 8, then 8 x 8 = 64.
    assert sankhya_marks(6) == [2, 0, 2, 0]
    assert sankhya(6) == 64


def test_halayudha_counts_for_the_named_meters() -> None:
    # On 8.31: gayatri 64, usnih 128, anustubh 256, brhati 512, pankti 1024, tristubh 2048,
    # jagati 4096.
    assert [sankhya(n) for n in range(6, 13)] == [64, 128, 256, 512, 1024, 2048, 4096]


def test_total_through_six_syllables() -> None:
    # 8.32: 64 doubled, less 2, counts every pattern of 1 to 6 syllables.
    assert total_through(6) == 126 == sum(sankhya(n) for n in range(1, 7))


def test_meru_rows_match_halayudha() -> None:
    # On 8.34: the 3-cell row gives 1 all-g, 2 with 1 l, 1 all-l; the 4-cell row 1, 3, 3, 1.
    meru = meru_prastara(3)
    assert meru == [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1]]
    assert lagakriya(2) == [1, 2, 1]
    assert lagakriya(3) == [1, 3, 3, 1]


def test_six_mora_patterns_match_singh_table_ii() -> None:
    # Singh (1985), Table II, with S as g and I as l; row 4 is the nashta example S I I S.
    table_ii = "SSS IISS ISIS SIIS IIIIS ISSI SISI IIISI SSII IISII ISIII SIIII IIIIII"
    expected = [row.replace("S", "g").replace("I", "l") for row in table_ii.split()]
    assert matra_prastara(6) == expected
    assert matra_prastara(6)[3] == "gllg"


def test_gopala_and_hemacandra_mora_counts() -> None:
    # Gopala works the counts up to 21, for 7 morae; Hemacandra lists 1, 2, 3, 5, 8, 13, 21, 34.
    assert [matra_count(m) for m in range(1, 9)] == [1, 2, 3, 5, 8, 13, 21, 34]


def test_bad_inputs_raise() -> None:
    with pytest.raises(ValueError):
        prastara(0)
    with pytest.raises(ValueError):
        nashta(0, 3)
    with pytest.raises(ValueError):
        nashta(9, 3)
    with pytest.raises(ValueError):
        uddishta("")
    with pytest.raises(ValueError):
        uddishta("gxl")
    with pytest.raises(ValueError):
        sankhya_marks(0)
    with pytest.raises(ValueError):
        meru_prastara(-1)
    with pytest.raises(ValueError):
        matra_prastara(0)
    with pytest.raises(ValueError):
        matra_count(0)
    with pytest.raises(ValueError):
        binary_pattern(0, 2)


syllables = st.integers(min_value=1, max_value=10)


@given(n=syllables)
def test_prastara_lists_every_pattern_once(n: int) -> None:
    rows = prastara(n)
    assert len(rows) == len(set(rows)) == sankhya(n) == 2**n
    assert rows == modern_prastara(n)


@given(n=syllables)
def test_nashta_and_uddishta_agree_with_the_written_prastara(n: int) -> None:
    for row, pattern in enumerate(prastara(n), start=1):
        assert nashta(row, n) == pattern
        assert uddishta(pattern) == row


@given(pattern=st.text(alphabet="gl", min_size=1, max_size=60))
def test_uddishta_is_binary_with_the_lowest_digit_first(pattern: str) -> None:
    row = uddishta(pattern)
    assert row == binary_row(pattern)
    assert nashta(row, len(pattern)) == pattern == binary_pattern(row, len(pattern))


@given(n=st.integers(min_value=1, max_value=2_000))
def test_sankhya_is_two_to_the_n_in_about_two_log_n_steps(n: int) -> None:
    assert sankhya(n) == 2**n
    assert len(sankhya_marks(n)) <= 2 * n.bit_length()


@given(n=syllables)
def test_lagakriya_counts_laghus_in_the_prastara(n: int) -> None:
    by_laghus = [sum(1 for row in prastara(n) if row.count("l") == k) for k in range(n + 1)]
    assert lagakriya(n) == by_laghus == modern_lagakriya(n)


@given(n=st.integers(min_value=0, max_value=40))
def test_meru_is_pascals_triangle(n: int) -> None:
    for k, row in enumerate(meru_prastara(n)):
        assert row == [comb(k, j) for j in range(k + 1)]


@given(m=st.integers(min_value=1, max_value=16))
def test_mora_patterns_sum_to_m_and_match_the_count(m: int) -> None:
    rows = matra_prastara(m)
    assert all(sum(2 if s == "g" else 1 for s in row) == m for row in rows)
    assert len(rows) == len(set(rows)) == matra_count(m)
