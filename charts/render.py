"""Render the series charts as SVG and PNG, in light and dark, from the package's own results.

Run: uv run --group charts python charts/render.py [--out DIR]

Each chart highlights the series its post is about in the site's accent and draws the rest in
1 grey, with a direct label on every line. The palette was checked with the dataviz validator:
the accent and grey separate under color-vision deficiency in both modes, and the grey's low
contrast is relieved by the direct labels.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.ticker import FuncFormatter, NullLocator  # noqa: E402

from ancient_algorithms.madhava import correct_digits, madhava_pi  # noqa: E402

RENDER_FONTS = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
"""Fonts matplotlib draws the PNG with; the first one installed wins."""

SVG_FONT_STACK = "'Quicksand Variable', Quicksand, 'Helvetica Neue', Arial, sans-serif"
"""The site's body font stack, written into the SVG so the page renders it in Quicksand."""

REPO_URL = "github.com/prasadus92/ancient-algorithms"


@dataclass(frozen=True)
class Theme:
    """Colors for 1 mode, taken from the site's design tokens."""

    name: str
    surface: str
    ink: str
    muted: str
    grid: str
    accent: str
    context: str


LIGHT = Theme("light", "#f7f8fb", "#101522", "#3f4856", "#e3e6ec", "#d81b6e", "#9aa3b2")
DARK = Theme("dark", "#06080d", "#eef2f8", "#9ba5b6", "#1a1f2a", "#f63e8c", "#4a5263")


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
    steps: bool = False


def _style_axes(ax: Axes, theme: Theme) -> None:
    ax.set_facecolor(theme.surface)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(theme.grid)
    ax.grid(axis="y", color=theme.grid, linewidth=1)
    ax.set_axisbelow(True)
    ax.tick_params(colors=theme.muted, labelsize=10, length=0, pad=6)


def _draw(chart: LineChart, theme: Theme) -> Figure:
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=200)
    fig.patch.set_facecolor(theme.surface)
    _style_axes(ax, theme)
    ordered = sorted(chart.series, key=lambda s: s.highlight)
    for s in ordered:
        color = theme.accent if s.highlight else theme.context
        drawstyle = "steps-post" if chart.steps else "default"
        ax.plot(
            s.xs,
            s.ys,
            color=color,
            linewidth=2,
            solid_capstyle="round",
            drawstyle=drawstyle,
            zorder=3,
        )
        ax.scatter(
            [s.xs[-1]],
            [s.ys[-1]],
            s=40,
            color=color,
            edgecolors=theme.surface,
            linewidths=2,
            zorder=4,
        )
        ax.annotate(
            s.label,
            (s.xs[-1], s.ys[-1]),
            xytext=(8, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=theme.ink if s.highlight else theme.muted,
            fontweight="bold" if s.highlight else "normal",
        )
    if chart.log_x:
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xlabel(chart.x_label, color=theme.muted, fontsize=10, labelpad=8)
    ax.set_ylabel(chart.y_label, color=theme.muted, fontsize=10, labelpad=8)
    fig.text(0.06, 0.95, chart.title, color=theme.ink, fontsize=14, fontweight="bold", va="top")
    fig.text(0.06, 0.885, chart.subtitle, color=theme.muted, fontsize=10.5, va="top")
    fig.text(0.06, 0.025, chart.source, color=theme.muted, fontsize=8.5, va="bottom")
    fig.subplots_adjust(left=0.09, right=0.8, top=0.8, bottom=0.2)
    return fig


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
    return LineChart(
        slug="madhava-convergence",
        title="Madhava's third correction gets 14 digits of pi from 100 terms",
        subtitle="Correct decimal places after n terms of 1 - 1/3 + 1/5 - ..., by end correction",
        x_label="Terms of the series (log scale)",
        y_label="Correct decimal places",
        series=series,
        source=f"Source: ancient_algorithms.madhava at 120 significant digits. {REPO_URL}",
        log_x=True,
        steps=True,
    )


CHARTS: tuple[Callable[[], LineChart], ...] = (madhava_convergence,)


def render(out_dir: Path) -> list[Path]:
    """Render every chart in both modes as SVG and PNG; return the written paths."""
    plt.rcParams["font.family"] = RENDER_FONTS
    plt.rcParams["svg.fonttype"] = "none"
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


def _use_site_font(svg: Path) -> None:
    """Replace the render font family in the SVG's text with the site's font stack."""
    rendered = ", ".join(f"'{family}'" for family in RENDER_FONTS)
    svg.write_text(
        svg.read_text().replace(f"font-family: {rendered}", f"font-family: {SVG_FONT_STACK}")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "out")
    args = parser.parse_args()
    for path in render(args.out):
        print(path)


if __name__ == "__main__":
    main()
