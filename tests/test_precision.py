from decimal import Decimal, localcontext

import pytest

from ancient_algorithms.madhava import PI_100
from ancient_algorithms.precision import correct_decimals


def test_places_of_3_14() -> None:
    assert correct_decimals(Decimal("3.14"), PI_100, 100) == 2


def test_equal_values_give_the_cap() -> None:
    assert correct_decimals(PI_100, PI_100, 100) == 100


def test_an_error_of_1_or_more_gives_0() -> None:
    assert correct_decimals(Decimal(5), PI_100, 100) == 0


def test_capped() -> None:
    with localcontext() as ctx:
        ctx.prec = 120
        close = PI_100 + Decimal("1e-90")
    assert correct_decimals(close, PI_100, 50) == 50
    assert correct_decimals(close, PI_100, 100) == 90


def test_rejects_negative_cap() -> None:
    with pytest.raises(ValueError, match="cap must be at least 0, got -1"):
        correct_decimals(Decimal(3), PI_100, -1)
