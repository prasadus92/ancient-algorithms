# Working in this repo

Instructions for anyone changing this repo, human or coding agent. `CLAUDE.md` points here.

This repo implements algorithms from dated historical sources in Python. Each module is checked against the worked examples in its source, where the source gives any. The write-ups are at https://prasad.tech/ancient-algorithms/.

## Setup and checks

Python 3.10 or newer, with [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked --group dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv build
```

CI runs these steps on Python 3.10 to 3.14, and `main` accepts changes only through a pull request with all 5 jobs green.

## Layout

- `src/ancient_algorithms/<algorithm>.py`: one module per algorithm. Comparisons with the modern method go in the same module.
- `tests/test_<algorithm>.py`: one test file per module.
- `benchmarks/`: scripts that print step counts or convergence tables. CI runs them, so they must stay fast.
- `CITATION.cff`, `LICENSE` (MIT, for code) and `LICENSE-PROSE.md` (CC BY 4.0, for prose).

## Adding an algorithm

1. **Read the primary source in a named edition.** Use the edition itself, not a summary of it, and note the text, chapter or verse, the edition and the date.
2. **Write the module docstring.** It names the source and the reading you follow. Where scholars read the text differently, say which reading the code follows and why.
3. **Write the functions.** Each docstring says what the function computes. Use type hints, clear names and small functions.
4. **Write the tests.**
   - Run every worked example the source gives, with its numbers.
   - Add property tests with Hypothesis against brute force or a modern method.
   - Test each input check.
5. **Add a benchmark** only when the comparison with the modern method is the point, for example step counts or rates of convergence.
6. **Update `README.md`** (the module table and "What the tests check") and the keywords in `CITATION.cff`.

## Accuracy

- Never invent a quotation, a page number, a verse number or a date. Leave out what you cannot confirm from a source.
- Mark an approximate date with "c.", and say what it rests on when it is an inference.
- State a lineage or a parallel between traditions only when a source supports it, and name that source.
- Where the source does not say how a value was computed, the code and docs say so and do not claim a method.

## Code style

- Code reads like a clean textbook implementation.
- Comments: keep one only when it gives a source reference, explains a step that is not obvious from the code, or says why a choice was made. Delete any comment that restates the code. Each comment fits on 1 line.
- Use `ValueError` with a message that names the bad input.
- `ruff` settings live in `pyproject.toml`. Lines are at most 100 characters.

## Docs and commit messages

- Write plain, short sentences. Use digits for counts, and sentence case for headings.
- No em dashes, no middle dots, no emoji.
- No filler words (just, really, actually, simply), no hype adjectives, no "X, not Y" framing.
- A pull request description says what changed, why, how it was verified, and what was refactored.
- Commit messages and pull requests carry no AI attribution lines or trailers.
