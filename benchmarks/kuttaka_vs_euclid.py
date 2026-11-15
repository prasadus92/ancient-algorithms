"""Kuttaka against the extended Euclidean algorithm and Python's pow(a, -1, m).

Prints, for moduli of growing size, the number of divisions each method performs
and the time per modular inverse. Run: python benchmarks/kuttaka_vs_euclid.py
"""

import random
import timeit

from old_algorithms.kuttaka import extended_gcd, mod_inverse_euclid, mod_inverse_kuttaka, pulverize


def euclid_divisions(a: int, m: int) -> int:
    count, r0, r1 = 0, m, a % m
    while r1:
        r0, r1 = r1, r0 % r1
        count += 1
    return count


def main() -> None:
    rng = random.Random(499)
    print(
        f"{'bits':>5} {'kuttaka divs':>13} {'euclid divs':>12} {'kuttaka us':>11} "
        f"{'euclid us':>10} {'pow us':>8}"
    )
    for bits in (16, 64, 256, 1024, 2048):
        m = rng.getrandbits(bits) | (1 << (bits - 1)) | 1
        a = rng.getrandbits(bits) % m
        while extended_gcd(a, m)[0] != 1:
            a = rng.getrandbits(bits) % m
        assert mod_inverse_kuttaka(a, m) == mod_inverse_euclid(a, m) == pow(a, -1, m)
        k_divs = pulverize(a, m, -1).divisions
        e_divs = euclid_divisions(a, m)
        n = 200
        k_us = timeit.timeit(lambda a=a, m=m: mod_inverse_kuttaka(a, m), number=n) / n * 1e6
        e_us = timeit.timeit(lambda a=a, m=m: mod_inverse_euclid(a, m), number=n) / n * 1e6
        p_us = timeit.timeit(lambda a=a, m=m: pow(a, -1, m), number=n) / n * 1e6
        print(f"{bits:>5} {k_divs:>13} {e_divs:>12} {k_us:>11.1f} {e_us:>10.1f} {p_us:>8.2f}")


if __name__ == "__main__":
    main()
