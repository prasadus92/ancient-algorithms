"""Rounds of the chakravala against steps of the continued-fraction method for Pell's equation.

Each chakravala round needs 1 kuttaka; each continued-fraction step computes 1
partial quotient and 1 convergent. Both are counted until x^2 - N*y^2 = 1.

Run: python benchmarks/chakravala_vs_continued_fraction.py
"""

from math import isqrt

from ancient_algorithms.chakravala import chakravala, pell_continued_fraction

EXAMPLES = (13, 61, 67, 94, 109, 181, 991)
RANGES = ((2, 100), (2, 1_000), (2, 10_000))


def counts(n: int) -> tuple[int, int, int]:
    """Rounds with Bhaskara II's shortcut, rounds without it, and continued-fraction steps."""
    return (
        chakravala(n).rounds,
        chakravala(n, shortcut=False).rounds,
        pell_continued_fraction(n)[2],
    )


def main() -> None:
    print(f"{'N':>6} {'shortcut':>9} {'cycle':>6} {'cont. fr.':>10}  y")
    for n in EXAMPLES:
        shortcut, cycle, cf = counts(n)
        print(f"{n:>6} {shortcut:>9} {cycle:>6} {cf:>10}  {chakravala(n).solution[0]}")
    print()
    print(f"{'N up to':>8} {'shortcut':>9} {'cycle':>8} {'cont. fr.':>10} {'ratio':>6}")
    for low, high in RANGES:
        totals = [0, 0, 0]
        for n in range(low, high):
            if isqrt(n) ** 2 == n:
                continue
            for i, value in enumerate(counts(n)):
                totals[i] += value
        ratio = totals[1] / totals[2]
        print(f"{high:>8} {totals[0]:>9} {totals[1]:>8} {totals[2]:>10} {ratio:>6.3f}")


if __name__ == "__main__":
    main()
