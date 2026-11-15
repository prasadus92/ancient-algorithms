"""Input checks shared across modules."""

from __future__ import annotations

from collections.abc import Sequence
from math import gcd

__all__ = ["check_at_least", "check_remainders", "shared_factor"]


def check_at_least(name: str, value: int, minimum: int) -> None:
    """Raise ``ValueError`` naming ``name`` unless ``value`` is at least ``minimum``."""
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}, got {value}")


def check_remainders(pairs: Sequence[tuple[int, int]]) -> None:
    """Raise ``ValueError`` unless there is a pair and each has ``0 <= remainder < divisor``."""
    if not pairs:
        raise ValueError("need at least one (remainder, divisor) pair")
    for remainder, divisor in pairs:
        if divisor < 1 or not 0 <= remainder < divisor:
            raise ValueError(f"need 0 <= remainder < divisor, got ({remainder}, {divisor})")


def shared_factor(divisors: Sequence[int]) -> tuple[int, int] | None:
    """The first 2 divisors that share a factor, or ``None`` when they are pairwise coprime."""
    for i, a in enumerate(divisors):
        for b in divisors[i + 1 :]:
            if gcd(a, b) != 1:
                return a, b
    return None
