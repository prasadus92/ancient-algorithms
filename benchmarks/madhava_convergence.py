"""Correct decimal places of pi against the number of terms, for each method.

Run: python benchmarks/madhava_convergence.py
"""

from old_algorithms.madhava import correct_digits, machin_pi, madhava_pi, madhava_sqrt12_pi

TERMS = (1, 2, 5, 10, 20, 50, 100)
METHODS = {
    "bare series": lambda n: madhava_pi(n, 0),
    "+ correction 1": lambda n: madhava_pi(n, 1),
    "+ correction 2": lambda n: madhava_pi(n, 2),
    "+ correction 3": lambda n: madhava_pi(n, 3),
    "sqrt(12) series": madhava_sqrt12_pi,
    "Machin (1706)": machin_pi,
}


def main() -> None:
    print(f"{'terms':<16}" + "".join(f"{n:>6}" for n in TERMS))
    for name, fn in METHODS.items():
        print(f"{name:<16}" + "".join(f"{correct_digits(fn(n)):>6}" for n in TERMS))


if __name__ == "__main__":
    main()
