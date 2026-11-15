from collections.abc import Callable
from fractions import Fraction
from math import gcd, isqrt

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.babylonian_sqrt import parse_sexagesimal
from ancient_algorithms.plimpton322 import (
    LARGEST_IGI,
    NEUGEBAUER_SACHS_GENERATORS,
    ROBSON_IGI,
    SMALLEST_IGI,
    TABLET,
    compare_with_tablet,
    diagnose,
    euclid_triples,
    floating_digits,
    generator_pairs,
    generator_triple,
    igibi,
    is_regular,
    plimpton_row,
    rebuild_table,
    reduce_triangle,
    robson_candidates,
    short_side_and_diagonal,
    takiltum,
    trailing_part_steps,
)


def digits(text: str) -> tuple[int, ...]:
    return tuple(int(d) for d in text.split())


# The 7 slips Robson lists in her Table 2 (2001, p. 175), plus row 11, which is not reduced.
ROBSON_DIFFERENCES = [
    (2, "I", digits("1 56 56 58 14 56 15"), digits("1 56 56 58 14 50 06 15"), "2 places added"),
    (2, "III", digits("3 12 01"), digits("1 20 25"), "unexplained"),
    (8, "I", digits("1 41 33 59 03 45"), digits("1 41 33 45 14 03 45"), "2 places added"),
    (9, "II", digits("9 01"), digits("8 01"), "digit miscopied"),
    (11, "II", digits("45"), digits("3"), "common factor kept"),
    (11, "III", digits("1 15"), digits("5"), "common factor kept"),
    (13, "I", digits("1 27 03 45"), digits("1 27 00 03 45"), "empty place left out"),
    (13, "II", digits("7 12 01"), digits("2 41"), "square"),
    (15, "II", digits("56"), digits("28"), "twice"),
]


def test_reciprocal_reading_rebuilds_the_tablet_except_its_slips() -> None:
    assert compare_with_tablet(rebuild_table()) == ROBSON_DIFFERENCES


def test_seven_scribal_errors() -> None:
    kinds = [kind for *_, kind in compare_with_tablet(rebuild_table())]
    assert len([k for k in kinds if k != "common factor kept"]) == 7


def test_generator_reading_moves_the_row_15_error_to_column_iii() -> None:
    rows = []
    for p, q in NEUGEBAUER_SACHS_GENERATORS:
        b, long_side, d = generator_triple(p, q)
        rows.append((Fraction(d, long_side) ** 2, b, d))
    row_15 = [diff for diff in compare_with_tablet(rows) if diff[0] == 15]
    assert row_15 == [(15, "III", digits("53"), digits("1 46"), "half")]


def test_igi_values_are_robsons_reciprocals() -> None:
    # Robson 2001, Table 6, column 1/x.
    expected = [
        "0;25",
        "0;25,18,45",
        "0;25,36",
        "0;25,55,12",
        "0;26,40",
        "0;27",
        "0;27,46,40",
        "0;28,07,30",
        "0;28,48",
        "0;29,37,46,40",
        "0;30",
        "0;31,15",
        "0;32",
        "0;32,24",
        "0;33,20",
    ]
    assert [igibi(x) for x in ROBSON_IGI] == [parse_sexagesimal(t) for t in expected]


def test_long_sides_match_robson_table_6() -> None:
    expected = ["2", "57 36", "1 20", "3 45", "1 12", "6", "45", "16", "10", "1 48"]
    expected += ["", "40", "4", "45", "45"]
    for number, (igi, text) in enumerate(zip(ROBSON_IGI, expected, strict=True), start=1):
        if number == 11:
            continue
        _, long_side, _ = reduce_triangle(*short_side_and_diagonal(igi))
        assert floating_digits(long_side) == digits(text)


def test_column_i_heading_take_away_1_and_the_short_side_comes_up() -> None:
    for igi in ROBSON_IGI:
        b, long_side, d = reduce_triangle(*short_side_and_diagonal(igi))
        assert takiltum(igi) == Fraction(d, long_side) ** 2
        assert takiltum(igi) - 1 == Fraction(b, long_side) ** 2


def test_rows_are_in_descending_order_of_column_i() -> None:
    column_i = [takiltum(x) for x in ROBSON_IGI]
    assert column_i == sorted(column_i, reverse=True)
    assert ROBSON_IGI[0] == LARGEST_IGI and ROBSON_IGI[-1] == SMALLEST_IGI


def test_row_2_trailing_part_steps_match_mansfield_wildberger_table_7() -> None:
    steps = trailing_part_steps(*short_side_and_diagonal(ROBSON_IGI[1]))
    assert steps == [
        (2, parse_sexagesimal("1;56,54,35"), parse_sexagesimal("2;47,32,05")),
        (12, parse_sexagesimal("23;22,55"), parse_sexagesimal("33;30,25")),
        (12, parse_sexagesimal("280;35"), parse_sexagesimal("402;05")),
        (12, Fraction(3367), Fraction(4825)),
    ]


def test_trailing_part_reads_only_the_numbers_still_fractional() -> None:
    assert trailing_part_steps(Fraction(1, 2), Fraction(3)) == [(2, Fraction(1), Fraction(6))]


def test_row_15_reduces_to_28_45_53() -> None:
    assert short_side_and_diagonal(parse_sexagesimal("1;48")) == (
        parse_sexagesimal("0;37,20"),
        parse_sexagesimal("1;10,40"),
    )
    assert reduce_triangle(*short_side_and_diagonal(parse_sexagesimal("1;48"))) == (28, 45, 53)


def test_robsons_worked_examples_from_ybc_6967() -> None:
    # Robson 2001, pp. 184-185: the reciprocal pair 12 and 0;05, then 5 and 0;12.
    assert short_side_and_diagonal(Fraction(12)) == (
        parse_sexagesimal("5;57,30"),
        parse_sexagesimal("6;02,30"),
    )
    assert reduce_triangle(*short_side_and_diagonal(Fraction(12))) == (143, 24, 145)
    assert reduce_triangle(*short_side_and_diagonal(Fraction(5))) == (12, 5, 13)


def test_robson_limits_admit_her_3_missing_lines() -> None:
    extra = {parse_sexagesimal(t) for t in ("2;18,14,24", "2;06,33,45", "1;57,11,15")}
    assert set(robson_candidates()) == set(ROBSON_IGI) | extra
    assert len(robson_candidates()) == 18


def test_missing_lines_match_robson_table_8() -> None:
    expected = {
        "2;18,14,24": ("18 41 59", "20", "27 22 49"),
        "2;06,33,45": ("3 55 29", "4 48", "6 12 01"),
        "1;57,11,15": ("3 12 09", "4 26 40", "5 28 41"),
    }
    for igi, sides in expected.items():
        triangle = reduce_triangle(*short_side_and_diagonal(parse_sexagesimal(igi)))
        assert tuple(floating_digits(v) for v in triangle) == tuple(digits(s) for s in sides)


def test_generator_bound_on_q_excludes_robsons_missing_lines() -> None:
    extra = set(robson_candidates()) - set(ROBSON_IGI)
    assert sorted(x.denominator for x in extra) == [64, 64, 125]
    assert all(Fraction(p, q) not in extra for p, q in generator_pairs())


def test_four_places_each_admit_3_more_lines() -> None:
    # Robson 2001, note 34: lines 6a, 9a and 12a.
    extra = {parse_sexagesimal(t) for t in ("2;10,12,30", "2;02,52,48", "1;53,46,40")}
    assert set(robson_candidates(max_total_places=8)) - set(robson_candidates()) == extra


def test_generator_pairs_give_the_tablet_rows_first() -> None:
    pairs = generator_pairs()
    assert len(pairs) == 38
    assert pairs[:15] == list(NEUGEBAUER_SACHS_GENERATORS)
    assert [Fraction(p, q) for p, q in pairs[:15]] == list(ROBSON_IGI)


def test_mansfield_wildberger_row_16() -> None:
    # Mansfield and Wildberger 2017, Table 9: the first row after the tablet's 15.
    p, q = generator_pairs()[15]
    assert plimpton_row(Fraction(p, q))[1:] == (175, 337)
    assert floating_digits(175) == (2, 55) and floating_digits(337) == (5, 37)


def test_written_sides_fail_the_diagonal_rule_where_the_tablet_is_wrong() -> None:
    failing = []
    for number, (_, b_digits, d_digits) in enumerate(TABLET, start=1):
        b = _value(b_digits)
        d = _value(d_digits)
        long_squared = d * d - b * b
        if long_squared <= 0 or isqrt(long_squared) ** 2 != long_squared:
            failing.append(number)
    assert failing == [2, 9, 13, 15]


def _value(ds: tuple[int, ...]) -> int:
    total = 0
    for d in ds:
        total = total * 60 + d
    return total


def test_diagnose_each_kind() -> None:
    assert diagnose((8, 1), (8, 1)) == "match"
    assert diagnose((7, 12, 1), (2, 41)) == "square"
    assert diagnose((56,), (28,)) == "twice"
    assert diagnose((53,), (1, 46)) == "half"
    assert diagnose((1, 27, 3, 45), (1, 27, 0, 3, 45)) == "empty place left out"
    assert diagnose((41, 33, 59), (41, 33, 45, 14)) == "2 places added"
    assert diagnose((9, 1), (8, 1)) == "digit miscopied"
    assert diagnose((3, 12, 1), (1, 20, 25)) == "unexplained"


def test_is_regular() -> None:
    assert is_regular(1) and is_regular(60**5) and is_regular(Fraction(1, 405))
    assert not is_regular(7) and not is_regular(Fraction(5, 14))


def test_floating_digits_drop_the_point_and_outer_zeros() -> None:
    assert floating_digits(Fraction(3, 4)) == (45,)
    assert floating_digits(45) == (45,)
    assert floating_digits(3600) == (1,)
    assert floating_digits(parse_sexagesimal("1;27,00,03,45")) == (1, 27, 0, 3, 45)


@pytest.mark.parametrize(
    "call",
    [
        lambda: is_regular(0),
        lambda: igibi(Fraction(7)),
        lambda: short_side_and_diagonal(Fraction(1)),
        lambda: generator_triple(2, 2),
        lambda: floating_digits(0),
        lambda: floating_digits(Fraction(1, 7)),
        lambda: robson_candidates(max_places=0),
        lambda: generator_pairs(max_q=0),
        lambda: compare_with_tablet([]),
        lambda: euclid_triples(0),
        lambda: diagnose((60,), (1,)),
    ],
)
def test_bad_input_raises(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError):
        call()


regular_igi = st.builds(
    lambda a, b, c: Fraction(2) ** a * Fraction(3) ** b * Fraction(5) ** c,
    st.integers(-6, 6),
    st.integers(-4, 4),
    st.integers(-3, 3),
).filter(lambda x: x > 1)


@given(regular_igi)
def test_every_regular_igi_gives_a_primitive_triple(igi: Fraction) -> None:
    b, long_side, d = reduce_triangle(*short_side_and_diagonal(igi))
    assert b * b + long_side * long_side == d * d
    assert gcd(gcd(b, long_side), d) == 1
    assert is_regular(long_side)
    assert takiltum(igi) == Fraction(d, long_side) ** 2


@given(regular_igi)
def test_reciprocal_and_generator_readings_agree(igi: Fraction) -> None:
    b, long_side, d = generator_triple(igi.numerator, igi.denominator)
    common = gcd(gcd(b, long_side), d)
    assert reduce_triangle(*short_side_and_diagonal(igi)) == (
        b // common,
        long_side // common,
        d // common,
    )


def brute_force_triples(max_diagonal: int) -> list[tuple[int, int, int]]:
    found = []
    for c in range(1, max_diagonal + 1):
        for a in range(1, c):
            b = isqrt(c * c - a * a)
            if a % 2 and b * b == c * c - a * a and gcd(a, b) == 1:
                found.append((a, b, c))
    return found


@given(st.integers(1, 400))
def test_euclid_formula_finds_every_primitive_triple(limit: int) -> None:
    assert euclid_triples(limit) == brute_force_triples(limit)


def test_euclid_first_triples() -> None:
    assert euclid_triples(30) == [(3, 4, 5), (5, 12, 13), (15, 8, 17), (7, 24, 25), (21, 20, 29)]
