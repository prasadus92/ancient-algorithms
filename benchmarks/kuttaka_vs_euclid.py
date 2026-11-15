"""Kuttaka against the extended Euclidean algorithm and Python's pow(a, -1, m).

For each modulus size, prints the mean number of divisions over 100 random
moduli, and the time per modular inverse for 1 of them. The kuttaka count is 1
lower because it stops when a residue reaches 1 and solves the last step with
the mati, where the Euclidean loop does 1 more division to reach 0.

Run: python benchmarks/kuttaka_vs_euclid.py
"""

import random
import timeit

from old_algorithms.kuttaka import extended_gcd, mod_inverse_euclid, mod_inverse_kuttaka, pulverize

SAMPLES = 100


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
        if extended_gcd(a, m)[0] == 1:
            return a, m


def main() -> None:
    rng = random.Random(499)
    print(
        f"{'bits':>5} {'kuttaka divs':>13} {'euclid divs':>12} {'kuttaka us':>11} "
        f"{'euclid us':>10} {'pow us':>8}"
    )
    for bits in (16, 64, 256, 1024, 2048):
        pairs = [random_pair(rng, bits) for _ in range(SAMPLES)]
        k_divs = sum(pulverize(a, m, -1).divisions for a, m in pairs) / SAMPLES
        e_divs = sum(euclid_divisions(a, m) for a, m in pairs) / SAMPLES
        a, m = pairs[0]
        assert mod_inverse_kuttaka(a, m) == mod_inverse_euclid(a, m) == pow(a, -1, m)
        n = 200
        k_us = timeit.timeit(lambda a=a, m=m: mod_inverse_kuttaka(a, m), number=n) / n * 1e6
        e_us = timeit.timeit(lambda a=a, m=m: mod_inverse_euclid(a, m), number=n) / n * 1e6
        p_us = timeit.timeit(lambda a=a, m=m: pow(a, -1, m), number=n) / n * 1e6
        print(f"{bits:>5} {k_divs:>13.1f} {e_divs:>12.1f} {k_us:>11.1f} {e_us:>10.1f} {p_us:>8.2f}")


if __name__ == "__main__":
    main()
