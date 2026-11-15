# Working in this repo

Instructions for anyone changing this repo, human or coding agent. `CLAUDE.md` points here.

This repo implements algorithms from dated historical sources in Python. Each module is checked against the worked examples in its source, where the source gives any. The write-ups are at https://prasad.tech/ancient-algorithms/.

## Setup and checks

Python 3.11 or newer, with [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest
uv build
uv run python benchmarks/kuttaka_vs_euclid.py
uv run python benchmarks/madhava_convergence.py
uv run python benchmarks/qiuyi_vs_euclid.py
uv run python benchmarks/euclid_steps.py
uv run python benchmarks/sieve_compare.py
uv run python benchmarks/chakravala_vs_continued_fraction.py
```

CI runs these steps on Python 3.11 to 3.15, and `main` accepts changes only through a pull request with all 5 jobs green. `uv run ruff format .` fixes formatting, and `uv run pytest tests/test_kuttaka.py -k example_2` runs a single test.

## Layout

- `src/ancient_algorithms/<algorithm>.py`: one module per algorithm. Comparisons with the modern method go in the same module.
- `tests/test_<algorithm>.py`: one test file per module.
- `charts/render.py`: draws the series charts from the package's results (SVG and PNG, light and dark) into `charts/out/`. Each chart has a title that states the finding, the highlighted series in the accent, every other series in gray, a direct label on each line or bar and a source line. Every number is deterministic, so a re-render with no code change rewrites identical files. The `dev` group includes the `charts` group, because mypy checks `charts/`.
- `benchmarks/`: scripts that print step counts or convergence tables. CI runs each one by name, so they must stay fast.
- `CITATION.cff`, `LICENSE` (MIT, for code) and `LICENSE-PROSE.md` (CC BY 4.0, for prose).

## Adding an algorithm

1. **Read the primary source in a named edition.** Note the text, chapter or verse, the edition and the date. Do not rely on a summary.
2. **Write the module docstring.** It names the source and the reading you follow. Where scholars read the text differently, say which reading the code follows and why.
3. **Write the functions.** Each docstring says what the function computes. Use type hints, clear names and small functions.
4. **Write the tests.**
   - Run every worked example the source gives, with its numbers.
   - Add property tests with Hypothesis against brute force or a modern method, as in `tests/test_kuttaka.py`.
   - Test that each `ValueError` is raised.
5. **Add a benchmark** only when the comparison with the modern method is the point, for example step counts or rates of convergence. Add a step that runs it to `.github/workflows/ci.yml` and to the README's "Run it" block.
6. **Update the metadata:** `README.md` (the module table and "What the tests check"), `CITATION.cff` (keywords, abstract and references) and the `keywords` in `pyproject.toml`.

The write-ups on prasad.tech live in a separate site repo. A change here does not need one.

## Accuracy

- Never invent a quotation, a page number, a verse number or a date. Leave out what you cannot confirm from a source.
- Mark an approximate date with "c.", and say what it rests on when it is an inference.
- State a lineage or a parallel between traditions only when a source supports it, and name that source.
- Where the source does not say how a value was computed, the code and docs say so and do not claim a method.

## Code style

- Write each function the way a textbook would present the algorithm: plain loops, standard-library types, and names taken from the source where it has them (for example `mati`).
- Comments: keep one only when it gives a source reference, explains a step that is not obvious from the code, or says why a choice was made. Delete any comment that restates the code. Each comment fits on 1 line.
- Use `ValueError` with a message that names the bad input.
- `ruff` and `mypy` settings live in `pyproject.toml`: ruff rules E, F, W, I, UP and B, lines of at most 100 characters, and mypy in strict mode over `src`, `tests` and `benchmarks`.

## Docs and commit messages

- Use American English: normalize, color, behavior, center, meter.
- Write plain, short sentences. Use digits for counts, and sentence case for headings.
- No em dashes, no middle dots, no emoji.
- No filler words (just, really, actually, simply), no hype adjectives, no "X, not Y" framing.
- A pull request description says what changed, why, how it was verified, and what was refactored.
- Commit messages and pull requests carry no AI attribution lines or trailers.
