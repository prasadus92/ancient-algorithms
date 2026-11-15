"""Render the series charts as SVG and PNG, in light and dark, from the package's own results.

Run: uv run python charts/render.py [--out DIR]

Each chart highlights the series its post is about in the site's red and draws the rest in
1 gray, with a direct label on every line or bar. The palette was checked with the dataviz
validator: the red and the gray pass the lightness, color-vision deficiency, normal-vision and
contrast checks in both modes. The gray fails only the chroma floor, as a context color should.
Every number is deterministic, so on the same machine a re-render rewrites identical files.
The Euclid and chakravala charts use the same samples and ranges as their benchmarks.
"""

from __future__ import annotations

import argparse
import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import isqrt
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, LogLocator, NullLocator

from ancient_algorithms.chakravala import chakravala, pell_continued_fraction
from ancient_algorithms.euclid import division_count, subtraction_count
from ancient_algorithms.heron import correct_decimals, heron_sqrt
from ancient_algorithms.madhava import correct_digits, madhava_pi

RENDER_FONTS = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
"""Fonts matplotlib draws with; the first installed wins. The site font cannot be bundled."""

SVG_FONT_STACK = "'General Sans', system-ui, -apple-system, 'Helvetica Neue', Arial, sans-serif"
"""The site's body font stack, written into each SVG in place of the render fonts."""

SVG_HASH_SALT = "ancient-algorithms"
"""Fixed salt for matplotlib's SVG element ids, so re-renders do not change them."""

REPO_URL = "github.com/prasadus92/ancient-algorithms"

BAR_HEIGHT = 0.32
"""Bar thickness as a share of each band, about 24px at the rendered size."""

MAX_MARKED_POINTS = 10
"""Series up to this length get a marker on every point; longer ones only at the end."""

EUCLID_DIGITS = (3, 6, 12, 24)
"""Digit counts in the Euclid chart, as in benchmarks/euclid_steps.py."""

EUCLID_SAMPLES = 10_000
"""Random pairs per size in the Euclid chart, as in benchmarks/euclid_steps.py."""

EUCLID_SEED = 300
"""Random seed of benchmarks/euclid_steps.py."""

PELL_LIMIT = 1000
"""The chakravala chart covers N below this, as in the chakravala post."""


@dataclass(frozen=True)
class Theme:
    """Colors for 1 mode, taken from the site's design tokens."""

    name: str
    surface: str
    ink: str
    muted: str
    grid: str
    baseline: str
    accent: str
    context: str


LIGHT = Theme("light", "#FFFFFF", "#0C0C0C", "#5F5F5F", "#ECECEC", "#DBDBDB", "#E5241C", "#8F8F8B")
DARK = Theme("dark", "#0C0C0C", "#F2F2F0", "#A3A3A0", "#1D1D1D", "#2E2E2E", "#FC4C42", "#60605C")


@dataclass(frozen=True)
class Series:
    """1 line: its label, its points, and whether it is the highlighted series."""

    label: str
    xs: Sequence[float]
    ys: Sequence[float]
    highlight: bool = False


@dataclass(frozen=True)
class LineChart:
    """Everything needed to draw 1 line chart."""

    slug: str
    title: str
    subtitle: str
    x_label: str
    y_label: str
    series: Sequence[Series]
    source: str
    log_x: bool = False
    log_y: bool = False
    steps: bool = False


@dataclass(frozen=True)
class BarChart:
    """Everything needed to draw 1 horizontal bar chart, 1 bar per category."""

    slug: str
    title: str
    subtitle: str
    x_label: str
    labels: Sequence[str]
    values: Sequence[float]
    highlight: str
    source: str


Chart = LineChart | BarChart


def madhava_convergence() -> LineChart:
    """Correct decimal places of pi against terms, for the bare series and Madhava's corrections."""
    terms = list(range(1, 101))
    names = ["Bare series", "Correction 1", "Correction 2", "Correction 3"]
    series = [
        Series(
            name,
            terms,
            [correct_digits(madhava_pi(n, order, 120)) for n in terms],
            highlight=order == 3,
        )
        for order, name in enumerate(names)
    ]
    best = series[-1].ys[-1]
    return LineChart(
        slug="madhava-convergence",
        title=f"Madhava's third correction gets pi to {best:.0f} decimal places from 100 terms",
        subtitle="Correct decimal places after n terms of 1 - 1/3 + 1/5 - ..., by end correction",
        x_label="Terms of the series (log scale)",
        y_label="Correct decimal places",
        series=series,
        source=f"Source: ancient_algorithms.madhava at 120 significant digits. {REPO_URL}",
        log_x=True,
        steps=True,
    )


def euclid_steps() -> LineChart:
    """Median subtraction and division counts on random pairs of growing size."""
    rng = random.Random(EUCLID_SEED)
    sizes = list(EUCLID_DIGITS)
    subtractions, divisions = [], []
    for digits in sizes:
        pairs = [_random_pair(rng, digits) for _ in range(EUCLID_SAMPLES)]
        subtractions.append(median(subtraction_count(a, b) for a, b in pairs))
        divisions.append(median(division_count(a, b) for a, b in pairs))
    return LineChart(
        slug="euclid-steps",
        title=(
            f"On {sizes[-1]}-digit numbers, division needs {divisions[-1]:.0f} steps "
            f"and subtraction {subtractions[-1]:.0f}"
        ),
        subtitle=(
            f"Median steps to the greatest common divisor, {EUCLID_SAMPLES:,} random pairs per size"
        ),
        x_label="Digits in each number",
        y_label="Steps (log scale)",
        series=[
            Series("Subtraction (Euclid VII.1)", sizes, subtractions),
            Series("Division (modern form)", sizes, divisions, highlight=True),
        ],
        source=f"Source: ancient_algorithms.euclid, random seed {EUCLID_SEED}. {REPO_URL}",
        log_y=True,
    )


def heron_convergence() -> LineChart:
    """Correct decimal places of the square root of 720 after each step of Heron's rule."""
    approximations = heron_sqrt(720, 5)
    steps = list(range(len(approximations)))
    digits = [correct_decimals(720, x) for x in approximations]
    return LineChart(
        slug="heron-convergence",
        title=f"5 steps of Heron's rule give the square root of 720 to {digits[-1]} places",
        subtitle="Correct decimal places after each step, starting from the nearest square, 27",
        x_label="Steps of the rule",
        y_label="Correct decimal places",
        series=[Series("Heron's rule", steps, digits, highlight=True)],
        source=f"Source: ancient_algorithms.heron, exact fractions. {REPO_URL}",
    )


def chakravala_steps() -> BarChart:
    """Total rounds over every non-square N up to PELL_LIMIT, for each method."""
    ns = [n for n in range(2, PELL_LIMIT) if isqrt(n) ** 2 != n]
    shortcut = sum(chakravala(n).rounds for n in ns)
    cycle = sum(chakravala(n, shortcut=False).rounds for n in ns)
    fraction = sum(pell_continued_fraction(n)[2] for n in ns)
    return BarChart(
        slug="chakravala-steps",
        title=(f"With the shortcut, the chakravala needs {shortcut / fraction:.0%} of the steps"),
        subtitle=(
            f"Against continued fractions, for the {len(ns):,} non-square N below {PELL_LIMIT:,}; "
            "closing compositions not counted"
        ),
        x_label="Total rounds or steps",
        labels=["Continued fractions", "Chakravala", "With the shortcut"],
        values=[fraction, cycle, shortcut],
        highlight="With the shortcut",
        source=f"Source: ancient_algorithms.chakravala. {REPO_URL}",
    )


def _random_pair(rng: random.Random, digits: int) -> tuple[int, int]:
    low, high = 10 ** (digits - 1), 10**digits - 1
    return rng.randint(low, high), rng.randint(low, high)


CHARTS: tuple[Callable[[], Chart], ...] = (
    madhava_convergence,
    euclid_steps,
    heron_convergence,
    chakravala_steps,
)


def render(out_dir: Path) -> list[Path]:
    """Render every chart in both modes as SVG and PNG; return the written paths."""
    plt.rcParams["font.family"] = RENDER_FONTS
    plt.rcParams["svg.fonttype"] = "none"
    plt.rcParams["svg.hashsalt"] = SVG_HASH_SALT
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for build in CHARTS:
        chart = build()
        for theme in (LIGHT, DARK):
            fig = _draw(chart, theme)
            png = out_dir / f"{chart.slug}-{theme.name}.png"
            fig.savefig(png, facecolor=theme.surface)
            svg = out_dir / f"{chart.slug}-{theme.name}.svg"
            fig.savefig(svg, facecolor=theme.surface, metadata={"Date": None})
            _use_site_font(svg)
            written += [png, svg]
            plt.close(fig)
    return written


def _draw(chart: Chart, theme: Theme) -> Figure:
    if isinstance(chart, BarChart):
        return _draw_bars(chart, theme)
    return _draw_lines(chart, theme)


def _frame(chart: Chart, theme: Theme) -> tuple[Figure, Axes]:
    """A figure with the title, subtitle and source line placed; the plot goes in the axes."""
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    fig.patch.set_facecolor(theme.surface)
    ax.set_facecolor(theme.surface)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(theme.baseline)
    ax.set_axisbelow(True)
    ax.tick_params(colors=theme.muted, labelsize=10, length=0, pad=6)
    fig.text(0.06, 0.95, chart.title, color=theme.ink, fontsize=14, fontweight="bold", va="top")
    fig.text(0.06, 0.885, chart.subtitle, color=theme.muted, fontsize=10.5, va="top")
    fig.text(0.06, 0.025, chart.source, color=theme.muted, fontsize=8.5, va="bottom")
    return fig, ax


def _draw_lines(chart: LineChart, theme: Theme) -> Figure:
    fig, ax = _frame(chart, theme)
    ax.grid(axis="y", color=theme.grid, linewidth=1)
    for s in sorted(chart.series, key=lambda s: s.highlight):
        color = theme.accent if s.highlight else theme.context
        ax.plot(
            s.xs,
            s.ys,
            color=color,
            linewidth=2,
            solid_capstyle="round",
            drawstyle="steps-post" if chart.steps else "default",
            zorder=3,
        )
        marked = range(len(s.xs)) if len(s.xs) <= MAX_MARKED_POINTS else [len(s.xs) - 1]
        ax.scatter(
            [s.xs[i] for i in marked],
            [s.ys[i] for i in marked],
            s=40,
            color=color,
            edgecolors=theme.surface,
            linewidths=2,
            zorder=4,
        )
        _label(ax, s.label, (s.xs[-1], s.ys[-1]), s.highlight, theme)
    if len(chart.series[0].xs) <= MAX_MARKED_POINTS:
        ax.set_xticks(list(chart.series[0].xs))
    if chart.log_x:
        ax.set_xscale("log")
        _plain_log_ticks(ax.xaxis)
    if chart.log_y:
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(subs=(1, 2, 5)))
        _plain_log_ticks(ax.yaxis)
    ax.set_xlabel(chart.x_label, color=theme.muted, fontsize=10, labelpad=8)
    ax.set_ylabel(chart.y_label, color=theme.muted, fontsize=10, labelpad=8)
    fig.subplots_adjust(left=0.09, right=0.76, top=0.8, bottom=0.2)
    return fig


def _draw_bars(chart: BarChart, theme: Theme) -> Figure:
    fig, ax = _frame(chart, theme)
    ax.grid(axis="x", color=theme.grid, linewidth=1)
    positions = list(range(len(chart.labels)))
    colors = [theme.accent if label == chart.highlight else theme.context for label in chart.labels]
    ax.barh(positions, chart.values, height=BAR_HEIGHT, color=colors, zorder=3)
    ax.xaxis.set_major_formatter(FuncFormatter(_thousands))
    ax.set_yticks(positions, chart.labels)
    ax.invert_yaxis()
    for y, (label, value) in enumerate(zip(chart.labels, chart.values, strict=True)):
        _label(ax, _thousands(value), (value, y), label == chart.highlight, theme)
    ax.set_xlabel(chart.x_label, color=theme.muted, fontsize=10, labelpad=8)
    ax.margins(x=0.15)
    fig.subplots_adjust(left=0.24, right=0.94, top=0.8, bottom=0.2)
    return fig


def _label(ax: Axes, text: str, at: tuple[float, float], highlight: bool, theme: Theme) -> None:
    """A direct label just right of a point, in ink and bold when it is the highlight."""
    ax.annotate(
        text,
        at,
        xytext=(8, 0),
        textcoords="offset points",
        va="center",
        fontsize=10,
        color=theme.ink if highlight else theme.muted,
        fontweight="bold" if highlight else "normal",
    )


def _plain_log_ticks(axis: Axis) -> None:
    """Label a log axis with plain numbers and no minor ticks."""
    axis.set_major_formatter(FuncFormatter(_thousands))
    axis.set_minor_locator(NullLocator())


def _thousands(value: float, _position: int | None = None) -> str:
    return f"{value:,.0f}"


def _use_site_font(svg: Path) -> None:
    """Replace the render font family in the SVG's text with the site's font stack."""
    rendered = ", ".join(f"'{family}'" for family in RENDER_FONTS)
    text = svg.read_text()
    if f"font-family: {rendered}" not in text:
        raise RuntimeError(f"{svg} has no font-family {rendered!r} to replace")
    svg.write_text(text.replace(f"font-family: {rendered}", f"font-family: {SVG_FONT_STACK}"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "out")
    args = parser.parse_args()
    for path in render(args.out):
        print(path)


if __name__ == "__main__":
    main()
