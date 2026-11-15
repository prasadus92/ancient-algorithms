"""Qin Jiushao's qiuyi against Euclid's algorithm: divisions per modular inverse.

For each modulus size, prints the mean number of divisions over 1,000 random coprime pairs,
and how often qiuyi needs the same number as Euclid or 1 fewer. Qiuyi saves the last
division when the 1 first appears in the upper right of its board, because Euclid's loop
goes on to divide by 1 to reach 0.

Run: python benchmarks/qiuyi_vs_euclid.py
"""

import random

from ancient_algorithms.dayan import qiuyi, qiuyi_board
from ancient_algorithms.kuttaka import extended_gcd

SAMPLES = 1_000


def euclid_divisions(a: int, m: int) -> int:
    count, r0, r1 = 0, m, a % m
    while r1:
        r0, r1 = r1, r0 % r1
        count += 1
    return count


def random_pair(rng: random.Random, bits: int) -> tuple[int, int]:
    m = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
    while True:
        a = rng.getrandbits(bits) % m
        if a > 0 and extended_gcd(a, m)[0] == 1:
            return a, m


def main() -> None:
    rng = random.Random(1247)
    print(f"{'bits':>5} {'qiuyi divs':>11} {'euclid divs':>12} {'same':>6} {'1 fewer':>8}")
    for bits in (16, 64, 256, 1024):
        pairs = [random_pair(rng, bits) for _ in range(SAMPLES)]
        q_counts = [len(qiuyi_board(a, m)) - 1 for a, m in pairs]
        e_counts = [euclid_divisions(a, m) for a, m in pairs]
        same = sum(q == e for q, e in zip(q_counts, e_counts, strict=True))
        fewer = sum(q == e - 1 for q, e in zip(q_counts, e_counts, strict=True))
        assert same + fewer == SAMPLES
        a, m = pairs[0]
        assert qiuyi(a, m) == pow(a, -1, m)
        print(
            f"{bits:>5} {sum(q_counts) / SAMPLES:>11.2f} {sum(e_counts) / SAMPLES:>12.2f} "
            f"{same:>6} {fewer:>8}"
        )


if __name__ == "__main__":
    main()
