import pytest
from hypothesis import given
from hypothesis import strategies as st

from ancient_algorithms.place_value import carry, check_digits, from_digits, pad, to_digits, trim


def test_digits_are_written_most_significant_first() -> None:
    assert to_digits(401, 20) == [1, 0, 1]
    assert to_digits(2026, 10) == [2, 0, 2, 6]
    assert to_digits(0, 7) == [0]
    assert from_digits([1, 0, 1], 20) == 401


def test_pad_and_trim() -> None:
    assert pad([5, 3], 4) == [0, 0, 5, 3]
    assert pad([5, 3], 1) == [5, 3]
    assert trim([0, 0, 5, 3]) == [5, 3]
    assert trim([0, 0]) == [0]


def test_carry_turns_column_totals_into_digits() -> None:
    assert carry([1, 18, 19], 10) == [2, 9, 9]
    assert carry([0, 25], 20) == [1, 5]
    assert carry([], 10) == [0]


def test_bad_input_names_the_value() -> None:
    with pytest.raises(ValueError, match="base must be at least 2, got 1"):
        to_digits(5, 1)
    with pytest.raises(ValueError, match="base must be at least 2, got 0"):
        from_digits([1], 0)
    with pytest.raises(ValueError, match="at least 1 digit, got"):
        from_digits([], 10)
    with pytest.raises(ValueError, match="digits in base 20 are 0 to 19, got 20"):
        check_digits([1, 20], 20)
    with pytest.raises(ValueError, match="n must be at least 0, got -3"):
        to_digits(-3, 10)
    with pytest.raises(ValueError, match="a column total must be at least 0, got -1"):
        carry([1, -1], 10)
    with pytest.raises(ValueError, match="base must be at least 2, got 1"):
        carry([1], 1)


@given(n=st.integers(0, 10**40), base=st.integers(2, 36))
def test_round_trip_and_python_int(n: int, base: int) -> None:
    digits = to_digits(n, base)
    assert from_digits(digits, base) == n
    assert int("".join("0123456789abcdefghijklmnopqrstuvwxyz"[d] for d in digits), base) == n


@given(columns=st.lists(st.integers(0, 500), max_size=12), base=st.integers(2, 60))
def test_carry_keeps_the_value(columns: list[int], base: int) -> None:
    value = sum(total * base**place for place, total in enumerate(reversed(columns)))
    assert from_digits(carry(columns, base), base) == value


@given(digits=st.lists(st.integers(0, 9), min_size=1, max_size=12), width=st.integers(0, 15))
def test_pad_and_trim_keep_the_value(digits: list[int], width: int) -> None:
    assert from_digits(pad(digits, width), 10) == from_digits(digits, 10)
    assert from_digits(trim(digits), 10) == from_digits(digits, 10)


def test_trim_needs_a_digit() -> None:
    with pytest.raises(ValueError):
        trim([])
