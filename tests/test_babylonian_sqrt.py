from fractions import Fraction

import pytest

from ancient_algorithms.babylonian_sqrt import (
    YBC7289_DIAGONAL,
    YBC7289_ROOT2,
    YBC7289_SIDE,
    format_sexagesimal,
    from_sexagesimal,
    heron_steps,
    parse_sexagesimal,
    to_sexagesimal,
)


def test_tablet_value():
    assert YBC7289_ROOT2 == 1 + Fraction(24, 60) + Fraction(51, 60**2) + Fraction(10, 60**3)
    assert YBC7289_ROOT2 == Fraction(30547, 21600)


def test_diagonal_is_side_times_root2():
    assert YBC7289_SIDE * YBC7289_ROOT2 == YBC7289_DIAGONAL


def test_tablet_is_sqrt2_truncated_to_three_places():
    # sqrt(2) = 1;24,51,10,7,46,... and the tablet keeps 3 places.
    x = YBC7289_ROOT2
    step = Fraction(1, 60**3)
    assert x * x < 2 < (x + step) * (x + step)


def test_other_reading_gives_inverse_root2():
    # Read the side as 0;30 and the third number is 0;42,25,35, 1/sqrt(2) to 3 places.
    assert to_sexagesimal(1 / YBC7289_ROOT2, 3) == (0, (42, 25, 35))
    x = parse_sexagesimal("0;42,25,35")
    step = Fraction(1, 60**3)
    assert x * x < Fraction(1, 2) < (x + step) * (x + step)


def test_negative_input_is_rejected():
    with pytest.raises(ValueError):
        parse_sexagesimal("-1;30")


def test_tablet_accuracy():
    err = 2**0.5 - float(YBC7289_ROOT2)
    assert 5.9e-7 < err < 6.0e-7


def test_heron_from_three_halves():
    xs = heron_steps(2, Fraction(3, 2), 2)
    assert xs == [Fraction(3, 2), Fraction(17, 12), Fraction(577, 408)]
    assert to_sexagesimal(xs[-1], 3) == (1, (24, 51, 10))


def test_round_trip_and_format():
    v = (42, (25, 35))
    assert to_sexagesimal(from_sexagesimal(v), 2) == v
    assert format_sexagesimal(v) == "42;25,35"
    assert parse_sexagesimal("42;25,35") == YBC7289_DIAGONAL
    assert format_sexagesimal((7, ())) == "7"
