# Ancient algorithms, implemented

[![CI](https://github.com/prasadus92/ancient-algorithms/actions/workflows/ci.yml/badge.svg)](https://github.com/prasadus92/ancient-algorithms/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Python implementations of algorithms from dated historical sources. Where the source or its oldest commentary has worked examples, the tests run them. The write-ups, with the source text, translation and derivation, are at [prasad.tech/ancient-algorithms](https://prasad.tech/ancient-algorithms/).

| Module | Algorithm | Source |
|---|---|---|
| `kuttaka.py` | The kuttaka ("pulverizer") for `a*x + c = b*y` and the remainder problem, with the extended Euclidean algorithm and modular inverse for comparison | Aryabhata, *Aryabhatiya*, Ganitapada 32 and 33 (c. 499 CE), read with Bhaskara I's commentary (629 CE) |
| `madhava.py` | The series for pi with Madhava's 3 end corrections, the sqrt(12) series, and Machin's formula for comparison | 16th-century Kerala texts that credit Madhava of Sangamagrama (c. 1340 to 1425) |
| `babylonian_sqrt.py` | Base-60 arithmetic, the square root of 2 on YBC 7289, and the averaging iteration | YBC 7289, Old Babylonian (c. 1800 to 1600 BCE); Heron of Alexandria, *Metrica* (1st century CE) |
| `sunzi.py` | The remainder problem and its recipe with the multipliers 70, 21 and 15, generalized to any pairwise coprime divisors | *Sunzi Suanjing* (c. 3rd to 5th century CE), the remainder problem in the third juan |
| `dayan.py` | Qin Jiushao's dayan method: reducing the divisors to definite numbers, and the qiuyi procedure for each multiplier | Qin Jiushao, *Shushu jiuzhang* (preface 1247), chapter 1 |

## Run it

Python 3.11 or newer. With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --locked --group dev
uv run pytest
uv run python benchmarks/kuttaka_vs_euclid.py
uv run python benchmarks/madhava_convergence.py
uv run python benchmarks/qiuyi_vs_euclid.py
```

With pip: `pip install -e . pytest hypothesis`, then `pytest`.

```python
>>> from ancient_algorithms.kuttaka import two_remainders, mod_inverse_kuttaka
>>> two_remainders(5, 12, 7, 31)   # leaves 5 with 12 and 7 with 31
317
>>> mod_inverse_kuttaka(17, 3120)  # the RSA textbook private exponent
2753
```

## What the tests check

- **The sources' own examples.** From Bhaskara I's commentary on Ganitapada 32 and 33: his 4 examples of the remainder problem (16, 317, 85 and 301), his 2 examples without remainders (9 and 17), and 1 of his astronomical examples (number 22, 199,066 days). Also the example Clark (1930) works from Parameshvara's commentary (1001). The columns for 3 of these are checked step by step against the commentary.
- **Properties on random inputs**, with Hypothesis. The kuttaka's answer satisfies its equation and is the smallest one, stopping the divisions early gives the same answer, and the results match the textbook Chinese remainder construction and Python's `pow(a, -1, m)`.
- **Sunzi and Qin Jiushao.** Sunzi's answer 23 for all 105 remainder triples, and every number in Qin's rice, dike and couriers problems. The divination problem matches up to the adjustment step the code leaves out.
- **Convergence rates.** Each of Madhava's corrections cuts the error by the expected power of n (n^-3, n^-5, n^-7).
- **The tablet.** 30 times 1;24,51,10 is 42;25,35, 1;24,51,10 is the square root of 2 truncated to 3 base-60 places, and 0;42,25,35 is 1/sqrt(2) truncated the same way.

## How readings are chosen

Old texts are terse, and translators disagree. Each module's docstring says which reading or attribution it follows. Where a source does not say how a value was computed, as on YBC 7289, the code says so and does not claim a method.

## Contributing

Corrections to translations and readings are welcome, with the edition and page that support them. [AGENTS.md](AGENTS.md) has the setup, checks and rules for adding an algorithm.

## Citing

The repo has a `CITATION.cff`, which GitHub shows as "Cite this repository". A Zenodo DOI will be added with the first tagged release.

## License

The code is under the [MIT License](LICENSE). The prose in this repo (this README, the docstrings' explanations and translations) is under [CC BY 4.0](LICENSE-PROSE.md). You can reuse both, with credit.

Copyright Prasad Subrahmanya ([prasad.tech](https://prasad.tech)).
