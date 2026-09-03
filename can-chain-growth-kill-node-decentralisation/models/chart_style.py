"""
Shared chart style for publication figures.

Greyscale ceiling lines, bitcoin orange chain growth lines. Academic layout
(Tufte L-shaped axes, no title, detail in LaTeX caption). Three lines per
group with direct right-edge labels — no legend, no fill on chain lines.

Output: PNG at 400 DPI.
"""

import pathlib
import matplotlib as mpl

# ── Apply academic rcParams on import ──────────────────────────────────

_RC = {
    "font.family":           "sans-serif",
    "font.sans-serif":       ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size":             9,

    "axes.labelsize":        10,
    "axes.titlesize":        11,
    "axes.linewidth":        0.6,
    "axes.spines.top":       False,
    "axes.spines.right":     False,
    "axes.grid":             False,

    "xtick.labelsize":       8,
    "ytick.labelsize":       8,
    "xtick.direction":       "in",
    "ytick.direction":       "in",
    "xtick.major.size":      4,
    "xtick.major.width":     0.6,
    "xtick.minor.size":      2,
    "xtick.minor.width":     0.4,
    "ytick.major.size":      4,
    "ytick.major.width":     0.6,
    "ytick.minor.size":      2,
    "ytick.minor.width":     0.4,

    "legend.frameon":        False,
    "legend.fontsize":       8,

    "lines.linewidth":       1.0,
    "lines.markersize":      4,

    "savefig.dpi":           400,
    "savefig.bbox":          "tight",
    "savefig.pad_inches":    0.03,
}

mpl.rcParams.update(_RC)

# ── Ceiling: greyscale ─────────────────────────────────────────────────

CEIL_LINE_BASE  = "#444444"
CEIL_LINE_BOUND = "#888888"
CEIL_FILL_COLOR = "#AAAAAA"
CEIL_FILL_ALPHA = 0.20
CEIL_LW_BASE    = 1.2
CEIL_LW_BOUND   = 0.7

# ── Chain growth: sequential heat ramp, mild → severe ─────────────────
# The demand scenarios are ordered by growth rate, so colour encodes
# magnitude rather than identity: one ramp, light → dark, never cycled.
# All four carry the same line weight — colour does the work, not thickness.
#
# Lightness is monotonic across the ramp. The lightest step sits below 3:1
# against white; the required relief is the direct right-edge label every
# line already carries.

CHAIN_RAMP = ["#E3A008", "#D1600A", "#A8300C", "#6E1206"]
CHAIN_LW = 1.0

# The theoretical maximum sits at the top of the same severity scale, so it
# keeps the darkest step. Dotted marks it as a bound rather than a forecast.
BOUND_COLOR = CHAIN_RAMP[3]
BOUND_LS    = ":"

# A derived hardware threshold is not a chain-growth scenario at all: grey.
REF_COLOR = "#8A8A8A"
REF_LW    = 0.8

# Retained for the bandwidth and IBD charts.
CHAIN_COLOR     = "#F7931A"
CHAIN_COLOR_MAX = "#D4600A"
CHAIN_LW_CONS   = 0.8
CHAIN_LW_BASE   = 1.2
CHAIN_LW_MAX    = 0.6

# ── Label styling ─────────────────────────────────────────────────────

LABEL_FONTSIZE    = 6.5
LABEL_CEIL_COLOR  = "#555555"
LABEL_CHAIN_COLOR = "#C05000"

# ── Layout ─────────────────────────────────────────────────────────────

FIGSIZE = (8, 3.5)
DPI = 400
TOTAL_YEARS = 84   # 2026-2110, so the axis ends on a decade tick
START_YEAR = 2026

GRID_ALPHA = 0.12

# ── Output path ────────────────────────────────────────────────────────

FIGURES_DIR = pathlib.Path(__file__).resolve().parent.parent / "figures"


def save(fig, name):
    """Save figure as PNG to the publication figures dir."""
    png = FIGURES_DIR / f"{name}.png"
    kw = dict(facecolor="white", bbox_inches="tight", pad_inches=0.15)
    fig.savefig(png, dpi=DPI, **kw)
    print(f"Saved: {png}")


def group_legend(ax, ceil_label, chain_label, loc="upper left",
                 chain_color=None):
    """Add a minimal 2-entry legend identifying the ceiling and chain groups."""
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color=CEIL_LINE_BASE, linewidth=CEIL_LW_BASE,
               linestyle="-", label=ceil_label),
        Line2D([0], [0], color=chain_color or CHAIN_COLOR, linewidth=CHAIN_LW,
               linestyle="-", label=chain_label),
    ]
    ax.legend(handles=handles, loc=loc, fontsize=7)


def label_right(ax, x, y, text, color, fontsize=LABEL_FONTSIZE):
    """Place a text label just right of a line's endpoint, outside the axes."""
    ax.text(x + 0.5, y, text, fontsize=fontsize, color=color,
            va="center", ha="left", clip_on=False)


def label_top(ax, x, y, text, color, fontsize=LABEL_FONTSIZE, ha="left"):
    """Place a text label just above a line's exit point at the top edge."""
    ax.text(x, y, text, fontsize=fontsize, color=color,
            va="bottom", ha=ha, clip_on=False, rotation=0)


def labels_right(ax, x, items, min_gap=None, log=False):
    """Place multiple right-edge labels, nudging apart to avoid collisions.

    items: list of (y, text, color) tuples.
    min_gap: minimum vertical distance between labels (in data units, or in
             decades when log=True). If None, uses 4% of the y-axis range.
    log: spacing is done in log10 space, so labels stay evenly separated on
         screen when the axis is logarithmic.
    """
    import math

    if not items:
        return

    fwd = (lambda v: math.log10(v)) if log else (lambda v: v)
    inv = (lambda v: 10 ** v) if log else (lambda v: v)

    if min_gap is None:
        y0, y1 = ax.get_ylim()
        min_gap = (fwd(y1) - fwd(y0)) * 0.04

    # Sort by y position
    sorted_items = sorted(items, key=lambda t: t[0])

    # Nudge apart from bottom up, in whatever space the axis is drawn in
    ys = [fwd(item[0]) for item in sorted_items]
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < min_gap:
            ys[i] = ys[i - 1] + min_gap

    for y, (_, text, color) in zip(ys, sorted_items):
        label_right(ax, x, inv(y), text, color)


def label_along_curve(ax, dates, values, text, color,
                      offset_pts=6, fontsize=LABEL_FONTSIZE, y_max=None,
                      center_x=None):
    """Place text curving along a data line, each character following the tangent.

    By default, right-aligned so the last character sits at the line's exit.
    If center_x is given, the label is centered at that x-coordinate instead.
    offset_pts: perpendicular offset above the line in display points.
    y_max: clip line at this value so text stays inside the chart.
    """
    import numpy as np

    fig = ax.get_figure()
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    dates = np.asarray(dates, dtype=float)
    values = np.asarray(values, dtype=float)

    if y_max is not None:
        # The last character sits on the line but its top (rotated height
        # + perpendicular offset) must not exceed y_max.  Compute how far
        # below y_max the line anchor needs to be so the visible text
        # stays inside the chart.
        y0_disp = ax.transData.transform([0, ax.get_ylim()[0]])[1]
        ymax_disp = ax.transData.transform([0, y_max])[1]
        pts_per_data = (ymax_disp - y0_disp) / (y_max - ax.get_ylim()[0])
        # Vertical extent above line: offset + char ascent, projected
        # through cos(angle).  Angle varies but ~50-70 deg typical for
        # these exponentials; cos(60)=0.5 is a reasonable average.
        vert_pts = (offset_pts + fontsize * 1.2) * 0.55
        ceiling = y_max - vert_pts / pts_per_data

        cross_idx = None
        for i in range(len(values) - 1):
            if values[i] <= ceiling < values[i + 1]:
                cross_idx = i
                break

        if cross_idx is not None:
            frac = (ceiling - values[cross_idx]) / (
                values[cross_idx + 1] - values[cross_idx])
            cross_x = dates[cross_idx] + frac * (
                dates[cross_idx + 1] - dates[cross_idx])
            dates = np.append(dates[:cross_idx + 1], cross_x)
            values = np.append(values[:cross_idx + 1], ceiling)

    # Display coordinates and arc length
    xy_disp = ax.transData.transform(np.column_stack([dates, values]))
    diffs = np.diff(xy_disp, axis=0)
    seg_len = np.hypot(diffs[:, 0], diffs[:, 1])
    arc = np.concatenate([[0], np.cumsum(seg_len)])

    # Measure character widths
    gap = 0.6
    widths = []
    for ch in text:
        t = fig.text(0, 0, ch, fontsize=fontsize)
        widths.append(t.get_window_extent(renderer).width)
        t.remove()

    total_w = sum(widths) + (len(text) - 1) * gap

    if center_x is not None:
        # Center the label at center_x
        center_arc = np.interp(center_x, dates, arc)
        cursor = center_arc - total_w / 2
    else:
        # Right-align: last character ends at the end of the visible line
        cursor = arc[-1] - total_w

    for ch, w in zip(text, widths):
        mid = cursor + w / 2
        if mid < 0 or mid > arc[-1]:
            cursor += w + gap
            continue

        idx = np.searchsorted(arc, mid) - 1
        idx = np.clip(idx, 0, len(seg_len) - 1)

        frac = (mid - arc[idx]) / seg_len[idx] if seg_len[idx] > 0 else 0
        frac = np.clip(frac, 0, 1)
        pos = xy_disp[idx] + frac * diffs[idx]

        angle = np.arctan2(diffs[idx, 1], diffs[idx, 0])
        perp = np.array([-np.sin(angle), np.cos(angle)])
        pos = pos + perp * offset_pts

        dp = ax.transData.inverted().transform(pos)
        ax.text(dp[0], dp[1], ch,
                fontsize=fontsize, color=color,
                rotation=np.degrees(angle), rotation_mode='anchor',
                ha='center', va='baseline',
                clip_on=False, transform=ax.transData)

        cursor += w + gap


def _find_crossing_x(dates, values, threshold):
    """Find x-coordinate where values first exceed threshold."""
    for i in range(len(values) - 1):
        if values[i] <= threshold < values[i + 1]:
            frac = (threshold - values[i]) / (values[i + 1] - values[i])
            return dates[i] + frac * (dates[i + 1] - dates[i])
    return None


def smart_labels(ax, dates, lines, y_max, x_end, min_gap=None, log=False):
    """Route labels to top edge or right edge based on where each line exits.

    lines: list of (values_array, text, color) tuples.
    Lines exceeding y_max get labeled at the top where they cross.
    Lines that exit the top late (past 80% of x-range) get right-edge labels
    at y_max to avoid collision with the right-label zone.
    Lines within y_max get labeled at the right edge.
    """
    x0, x1 = ax.get_xlim()
    late_threshold = x0 + (x1 - x0) * 0.80

    right_items = []
    top_items = []

    for values, text, color in lines:
        if values[-1] > y_max:
            x_cross = _find_crossing_x(dates, values, y_max)
            if x_cross is not None and x_cross < late_threshold:
                top_items.append((x_cross, text, color))
            else:
                # Exits top too late — treat as right-edge label at y_max
                right_items.append((y_max, text, color))
        else:
            right_items.append((values[-1], text, color))

    # Place right-edge labels with collision avoidance
    if right_items:
        labels_right(ax, x_end, right_items, min_gap=min_gap, log=log)

    # Place top-edge labels with position-based alignment
    if top_items:
        sorted_top = sorted(top_items, key=lambda t: t[0])
        n = len(sorted_top)
        for i, (x, text, color) in enumerate(sorted_top):
            if n == 1:
                ha = "center"
            elif i == 0:
                ha = "right"
            elif i == n - 1:
                ha = "left"
            else:
                ha = "center"
            label_top(ax, x, y_max, text, color, ha=ha)
