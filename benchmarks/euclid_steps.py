"""Steps taken by Euclid's subtraction in turn and by the division form.

For random pairs of each size, prints the median and the largest number of
subtractions and of divisions, and Lamé's bound for the largest pair. Subtractions
are counted as the sum of the division quotients less 1, which the tests check
against the literal subtraction on smaller numbers.

Run: python benchmarks/euclid_steps.py
"""

from __future__ import annotations

import random
from statistics import median

from ancient_algorithms.euclid import division_count, division_quotients, lame_bound

SAMPLES = 10_000


def random_pair(rng: random.Random, digits: int) -> tuple[int, int]:
    low, high = 10 ** (digits - 1), 10**digits - 1
    return rng.randint(low, high), rng.randint(low, high)


def main() -> None:
    rng = random.Random(300)
    print(f"{'digits':>6} {'divisions':>18} {'subtractions':>26} {'Lame bound':>11}")
    for digits in (3, 6, 12, 24):
        pairs = [random_pair(rng, digits) for _ in range(SAMPLES)]
        divisions = [division_count(a, b) for a, b in pairs]
        subtractions = [sum(division_quotients(a, b)) - 1 for a, b in pairs]
        print(
            f"{digits:>6} {median(divisions):>8} (max {max(divisions):>4}) "
            f"{median(subtractions):>12} (max {max(subtractions):>9}) {5 * digits:>11}"
        )
    worst = max(range(1, 1000), key=lambda b: division_count(1597, b))
    print("most divisions for 1597 and b < 1000:", worst, division_count(1597, worst))
    print("1597, 987:", division_count(1597, 987), "divisions, bound", lame_bound(1597, 987))


if __name__ == "__main__":
    main()
