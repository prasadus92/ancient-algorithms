from datetime import date

import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.maya import (
    CALENDAR_ROUND,
    GMT,
    GMT_PLUS_2,
    add_bars_and_dots,
    bars_and_dots,
    calendar_round,
    days_from_long_count,
    days_in_round,
    from_vigesimal,
    gregorian_from_jdn,
    haab,
    jdn_from_date,
    jdn_from_gregorian,
    jdn_from_julian,
    jdn_from_long_count,
    julian_from_jdn,
    long_count_from_days,
    long_count_from_jdn,
    to_vigesimal,
    tzolkin,
)

ERA_END = days_from_long_count((13, 0, 0, 0, 0))
any_day = st.integers(0, 20 * 144_000 - 1)


def test_era_date_is_4_ajaw_8_kumku() -> None:
    assert calendar_round(0) == (4, "Ajaw", 8, "Kumk'u")


def test_era_date_under_gmt() -> None:
    # 11 August 3114 BCE proleptic Gregorian, 6 September 3114 BCE Julian.
    assert jdn_from_long_count((0, 0, 0, 0, 0)) == 584_283
    assert gregorian_from_jdn(GMT) == (-3113, 8, 11)
    assert julian_from_jdn(GMT) == (-3113, 9, 6)


def test_13_baktun_ends_on_21_december_2012() -> None:
    assert ERA_END == 1_872_000
    assert calendar_round(ERA_END) == (4, "Ajaw", 3, "K'ank'in")
    assert gregorian_from_jdn(jdn_from_long_count((13, 0, 0, 0, 0))) == (2012, 12, 21)
    assert gregorian_from_jdn(jdn_from_long_count((13, 0, 0, 0, 0), GMT_PLUS_2)) == (2012, 12, 23)


def test_tikal_lintel_3_date_from_kennett_2013() -> None:
    # 9.13.3.7.18 is 1,390,838 days, 6 August 695 in Kennett et al.'s reckoning.
    days = days_from_long_count((9, 13, 3, 7, 18))
    assert days == 1_390_838
    assert calendar_round(days) == (11, "Etz'nab", 11, "Ch'en")
    assert gregorian_from_jdn(days + GMT) == (695, 8, 6)
    assert julian_from_jdn(days + GMT) == (695, 8, 3)


def test_dresden_page_24_initial_series() -> None:
    # Morley 1915, pp. 266 to 268: 9.9.16.0.0 4 Ahau 8 Cumhu and 9.9.9.16.0 1 Ahau 18 Kayab.
    first = days_from_long_count((9, 9, 16, 0, 0))
    assert first == 1_366_560 == 72 * CALENDAR_ROUND
    assert calendar_round(first) == (4, "Ajaw", 8, "Kumk'u")
    second = days_from_long_count((9, 9, 9, 16, 0))
    assert second == 1_364_360
    assert calendar_round(second) == (1, "Ajaw", 18, "K'ayab")


def test_dresden_page_24_multiples_of_2920_from_1_ajaw() -> None:
    # Morley 1915, p. 276: the 12 lower terms and the day each reaches from 1 Ahau.
    numbers = [9, 4, 12, 7, 2, 10, 5, 13, 8, 3, 11, 6]
    start = days_in_round(1, "Ajaw", 18, "K'ayab")
    for k, number in enumerate(numbers, start=1):
        assert tzolkin(start + k * 2920) == (number, "Ajaw")
    assert tzolkin(start + 13 * 2920) == (1, "Ajaw")


def test_venus_table_period_counts() -> None:
    # Morley 1915, p. 278: 113,880 days in whole tzolk'ins, years, Venus years and rounds.
    assert 2920 == 5 * 584 == 8 * 365
    assert 113_880 == 438 * 260 == 312 * 365 == 195 * 584 == 39 * 2920 == 6 * CALENDAR_ROUND


def test_401_in_base_20_and_as_days() -> None:
    assert to_vigesimal(401) == [1, 0, 1]
    assert long_count_from_days(401) == (0, 0, 1, 2, 1)


def test_bars_and_dots() -> None:
    assert bars_and_dots(0) == (0, 0)
    assert bars_and_dots(19) == (3, 4)
    with pytest.raises(ValueError, match="got 20"):
        bars_and_dots(20)


def test_adding_carries_four_bars_up_as_a_dot() -> None:
    assert add_bars_and_dots([19], [1]) == [1, 0]
    assert add_bars_and_dots([1, 0, 1], [19]) == [1, 1, 0]


def test_calendar_round_lookup() -> None:
    assert days_in_round(4, "Ajaw", 8, "Kumk'u") == 0
    assert days_in_round(4, "Ajaw", 3, "K'ank'in") == ERA_END % CALENDAR_ROUND
    with pytest.raises(ValueError, match="never occurs"):
        days_in_round(1, "Imix", 1, "Pop")
    with pytest.raises(ValueError, match="Wayeb' has days 0 to 4, got 7"):
        days_in_round(4, "Ajaw", 7, "Wayeb'")


def test_haab_wayeb_has_5_days() -> None:
    # 8 Kumk'u + 12 days is the first day after Kumk'u's 19th.
    assert haab(11) == (19, "Kumk'u")
    assert haab(12) == (0, "Wayeb'")
    assert haab(16) == (4, "Wayeb'")
    assert haab(17) == (0, "Pop")


def test_long_count_place_limits() -> None:
    with pytest.raises(ValueError, match="from 0 to 17"):
        days_from_long_count((9, 9, 9, 18, 0))
    with pytest.raises(ValueError, match="days must be"):
        long_count_from_days(-1)


def test_jdn_anchors() -> None:
    assert jdn_from_gregorian(2000, 1, 1) == 2_451_545
    assert gregorian_from_jdn(2_299_161) == (1582, 10, 15)
    assert julian_from_jdn(2_299_161) == (1582, 10, 5)
    assert julian_from_jdn(0) == (-4712, 1, 1)
    assert gregorian_from_jdn(0) == (-4713, 11, 24)


@given(n=st.integers(0, 10**30))
def test_vigesimal_round_trip(n: int) -> None:
    assert from_vigesimal(to_vigesimal(n)) == n


@given(a=st.integers(0, 10**30), b=st.integers(0, 10**30))
def test_bar_and_dot_addition_matches_python(a: int, b: int) -> None:
    assert from_vigesimal(add_bars_and_dots(to_vigesimal(a), to_vigesimal(b))) == a + b


@given(days=any_day)
def test_long_count_round_trip(days: int) -> None:
    assert days_from_long_count(long_count_from_days(days)) == days
    assert long_count_from_jdn(days + GMT) == long_count_from_days(days)


@given(days=any_day)
def test_round_repeats_and_lookup_finds_it(days: int) -> None:
    assert calendar_round(days) == calendar_round(days + CALENDAR_ROUND)
    assert days_in_round(*calendar_round(days)) == days % CALENDAR_ROUND


def test_round_is_18980_days_and_no_shorter() -> None:
    first = calendar_round(0)
    assert [d for d in range(1, CALENDAR_ROUND + 1) if calendar_round(d) == first] == [18_980]


@given(day=st.dates(min_value=date(1, 1, 1)))
def test_gregorian_matches_datetime(day: date) -> None:
    jdn = jdn_from_gregorian(day.year, day.month, day.day)
    assert jdn == jdn_from_date(day.year, day.month, day.day)
    assert gregorian_from_jdn(jdn) == (day.year, day.month, day.day)


@given(jdn=st.integers(0, 5_000_000))
def test_julian_round_trip(jdn: int) -> None:
    assert jdn_from_julian(*julian_from_jdn(jdn)) == jdn
    assert jdn_from_gregorian(*gregorian_from_jdn(jdn)) == jdn
