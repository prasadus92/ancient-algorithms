# Old algorithms, implemented

Python implementations of algorithms from dated historical sources, each checked against the worked examples in the source or its oldest commentary. The write-ups, with the source text, translation and derivation, are at [prasad.tech/old-algorithms](https://prasad.tech/old-algorithms/).

| Module | Algorithm | Source |
|---|---|---|
| `kuttaka.py` | The kuttaka ("pulverizer") for `a*x + c = b*y` and the remainder problem, with the extended Euclidean algorithm and modular inverse for comparison | Aryabhata, *Aryabhatiya*, Ganitapada 32 and 33 (499 CE), read with Bhaskara I's commentary (629 CE) |
| `madhava.py` | The series for pi with Madhava's 3 end corrections, the sqrt(12) series, and Machin's formula for comparison | Kerala texts of c. 1500 to 1530 that credit Madhava of Sangamagrama (c. 1340 to 1425) |
| `babylonian_sqrt.py` | Base-60 arithmetic, the square root of 2 on YBC 7289, and the averaging iteration | YBC 7289, Old Babylonian (c. 1800 to 1600 BCE); Heron of Alexandria, *Metrica* (1st century CE) |

## Run it

Python 3.10 or newer. With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --group dev
uv run pytest
uv run python benchmarks/kuttaka_vs_euclid.py
uv run python benchmarks/madhava_convergence.py
```

With pip: `pip install -e . pytest hypothesis`, then `pytest`.

```python
>>> from old_algorithms.kuttaka import two_remainders, mod_inverse_kuttaka
>>> two_remainders(5, 12, 7, 31)   # leaves 5 with 12 and 7 with 31
317
>>> mod_inverse_kuttaka(17, 3120)  # the RSA textbook private exponent
2753
```

## What the tests check

- **The sources' own examples.** All 4 of Bhaskara I's kuttaka examples (16, 317, 85 and 301), his day-count example from astronomy (199,066 days), and the example Clark (1930) works from Parameshvara's commentary (1001). The column for the 317 example is checked step by step against the commentary.
- **Properties on random inputs**, with Hypothesis. The kuttaka's answer satisfies its equation and is the smallest one, stopping the divisions early gives the same answer, and the results match the textbook Chinese remainder construction and Python's `pow(a, -1, m)`.
- **Convergence rates.** Each of Madhava's corrections cuts the error by the expected power of n (n^-3, n^-5, n^-7).
- **The tablet.** 30 times 1;24,51,10 is 42;25,35, and 1;24,51,10 is the square root of 2 truncated to 3 base-60 places.

## How readings are chosen

Old texts are terse, and translators disagree. Each module's docstring says which reading it follows and why, and names the edition of the text. Where the source does not say how a value was computed (YBC 7289 is the clearest case), the code says so and does not claim a method.

## Citing

The repo has a `CITATION.cff`, which GitHub shows as "Cite this repository". A Zenodo DOI will be added with the first tagged release.

## License

Code under the MIT License. Quotations from editions and translations are short and credited in the docstrings and on the site.
