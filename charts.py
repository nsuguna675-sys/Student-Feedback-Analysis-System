import io
import textwrap

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from analysis import MIN_GROUP_SIZE, RATING_MAX, RATING_MIN

# Colours: one blue for single-series charts, a light-to-dark blue ramp for ratings 1 to 5
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
RAMP = ["#86b6ef", "#5598e7", "#2a78d6", "#184f95", "#0d366b"]   # rating 1 (light) to 5 (dark)


def to_png(fig):
    """Turn a Matplotlib figure into PNG bytes that Flask can send to the browser."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, facecolor=SURFACE)
    return buffer.getvalue()


def new_figure(width, height):
    # We use Figure directly (not pyplot) because pyplot can crash inside a web server on a Mac.
    return Figure(figsize=(width, height), facecolor=SURFACE, layout="constrained")


def style(ax, grid_axis=None):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(axis="x", colors=MUTED, labelsize=9, length=0)
    ax.tick_params(axis="y", colors=INK_SECONDARY, labelsize=9, length=0)
    ax.xaxis.label.set_color(INK_SECONDARY)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)


def wrap(text, width=28):
    return textwrap.fill(text, width=width)


def hidden_note(hidden_names):
    return f"Not shown (fewer than {MIN_GROUP_SIZE} responses): " + ", ".join(hidden_names) + "."


def placeholder(title, message):
    fig = new_figure(7, 3)
    ax = fig.subplots()
    ax.axis("off")
    ax.text(0.5, 0.62, title, ha="center", va="center", fontsize=13, fontweight="bold",
            color=INK, transform=ax.transAxes)
    ax.text(0.5, 0.38, message, ha="center", va="center", fontsize=10,
            color=INK_SECONDARY, transform=ax.transAxes)
    return fig


def course_comparison_png(summary):
    """Bar chart: average rating of each course (only courses with enough responses)."""
    shown = sorted([c for c in summary if c["shown"]], key=lambda c: c["average"])
    hidden = [c["course_name"] for c in summary if not c["shown"]]
    if not shown:
        return to_png(placeholder("Average rating by course",
                                  f"No course has {MIN_GROUP_SIZE} or more responses yet."))

    fig = new_figure(9, max(3.4, 0.7 * len(shown) + 2.2))
    ax = fig.subplots()
    style(ax, grid_axis="x")
    y = np.arange(len(shown))
    ax.barh(y, [c["average"] for c in shown], height=0.55, color=BLUE)
    ax.set_yticks(y, labels=[wrap(c["course_name"]) for c in shown])
    ax.set_xlim(0, RATING_MAX * 1.25)
    ax.set_xticks(range(0, RATING_MAX + 1))
    ax.spines["bottom"].set_bounds(0, RATING_MAX)
    for yi, c in zip(y, shown):
        ax.text(c["average"] + 0.06, yi, f"{c['average']:.2f}  (n = {c['students']})",
                va="center", fontsize=9, color=INK_SECONDARY)
    ax.set_xlabel(f"Average rating (scale {RATING_MIN} to {RATING_MAX}, higher is better)")
    ax.set_title("Average rating by course", loc="left", fontsize=13, fontweight="bold", color=INK)
    if hidden:
        fig.supxlabel(hidden_note(hidden), x=0.01, ha="left", fontsize=8, color=MUTED)
    return to_png(fig)


def distribution_png(rows):
    """100% stacked bars: what share of ratings were 1, 2, 3, 4 or 5 in each course."""
    if not rows:
        return to_png(placeholder("Rating distribution by course",
                                  f"No course has {MIN_GROUP_SIZE} or more responses yet."))

    levels = list(range(RATING_MIN, RATING_MAX + 1))
    # sort so the lowest-rated course is at the bottom
    rows = sorted(rows, key=lambda r: sum(p * level for p, level in zip(r["percents"], levels)))
    fig = new_figure(9, max(3.8, 0.7 * len(rows) + 2.6))
    ax = fig.subplots()
    style(ax)
    y = np.arange(len(rows))
    left = np.zeros(len(rows))
    for position, level in enumerate(levels):
        widths = np.array([r["percents"][position] for r in rows])
        ax.barh(y, widths, left=left, height=0.62, color=RAMP[position],
                edgecolor=SURFACE, linewidth=1.5)
        for yi, (start, width) in enumerate(zip(left, widths)):
            if width >= 6:
                ax.text(start + width / 2, yi, f"{width:.0f}%", ha="center", va="center",
                        fontsize=8, color="#ffffff" if position >= 2 else INK)
        left = left + widths
    ax.set_yticks(y, labels=[f"{wrap(r['course_name'])}\n(n = {r['students']})" for r in rows])
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 20), labels=[f"{v}%" for v in range(0, 101, 20)])
    ax.set_xlabel("Share of ratings given to the course (%)")
    names = [str(level) for level in levels]
    names[0] += " (lowest)"
    names[-1] += " (highest)"
    legend = ax.legend([Patch(facecolor=c, edgecolor=SURFACE) for c in RAMP], names, title="Rating",
                       ncol=len(levels), loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False,
                       fontsize=8, title_fontsize=8, labelcolor=INK_SECONDARY, alignment="left")
    legend.get_title().set_color(INK_SECONDARY)
    ax.set_title("Rating distribution by course", loc="left", fontsize=13, fontweight="bold",
                 color=INK, pad=34)
    return to_png(fig)