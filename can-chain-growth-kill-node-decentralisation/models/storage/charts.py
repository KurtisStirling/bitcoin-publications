"""
Storage: node capacity ceiling vs chain growth, 80-year outlook.

Grey capacity cloud with a base line and a labelled pessimistic bound,
against three chain-growth scenarios.

Log vertical axis. On a linear axis capped at 18 TB the optimistic ceiling
left the plot in 2046 and the base ceiling in 2056, so two of the three
improvement rates the caption promised were invisible for most of the chart.
"""

import pathlib
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scenarios as sc
from chart_style import (
    CEIL_LINE_BASE, CEIL_FILL_COLOR, CEIL_FILL_ALPHA,
    CEIL_LW_BASE,
    CHAIN_RAMP, CHAIN_LW,
    LABEL_FONTSIZE, LABEL_CEIL_COLOR,
    FIGSIZE, TOTAL_YEARS, START_YEAR, GRID_ALPHA,
    save, smart_labels, group_legend, log_yaxis,
)

# ── Constants ─────────────────────────────────────────────────────────

CHAIN_GB_2026 = sc.CHAIN_GB_2026
Y_MAX_TB = 18       # linear variant only

# Top of the log axis. True auto-scaling now reaches ~32,000 TB, which pushes
# every chain line and the pessimistic ceiling into the bottom fifth of the
# plot. 1,000 TB keeps the cloud running off the top without crushing the part
# anyone reads.
Y_TOP_LOG_TB = 1000

# Demand scenarios, mild to severe, paired with steps of the severity ramp.
# The theoretical maximum is not drawn: on a log axis it sits within 10% of
# the realistic worst case, so it costs a line and a label to show nothing.
# Section 4 states the 210 GB/year envelope in prose with its BIP-141 cite.
DEMAND = [
    ("monetary", CHAIN_RAMP[1]),
    ("current", CHAIN_RAMP[2]),
    ("realistic_worst", CHAIN_RAMP[3]),
]

CEILINGS = ["optimistic", "base", "pessimistic"]


def chain_tb(t, growth):
    return (CHAIN_GB_2026 + growth * t) / 1000


# ── Chart ─────────────────────────────────────────────────────────────

def make_chart(suffix="", footnote=None, label_min_gap=None, log=False,
               log_top=Y_TOP_LOG_TB):
    t = np.linspace(0, TOTAL_YEARS, TOTAL_YEARS * 100 + 1)
    dates = START_YEAR + t

    ceil = {c: np.array([sc.hw_capacity_tb(c, y) for y in t])
            for c in CEILINGS}
    demand = [(np.array([chain_tb(y, sc.SCENARIOS[key]["gb_per_year"])
                         for y in t]), key, colour)
              for key, colour in DEMAND]

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Ceiling fill between bounds
    ax.fill_between(dates, ceil["pessimistic"], ceil["optimistic"],
                    facecolor=CEIL_FILL_COLOR, edgecolor="none",
                    alpha=CEIL_FILL_ALPHA, zorder=2)

    ax.plot(dates, ceil["base"], color=CEIL_LINE_BASE, linewidth=CEIL_LW_BASE,
            linestyle="-", zorder=5)

    for series, _, colour in demand:
        ax.plot(dates, series, color=colour, linewidth=CHAIN_LW,
                linestyle="-", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Storage (TB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))

    if log:
        floor = min(ceil["pessimistic"].min(),
                    min(s.min() for s, _, _ in demand))
        log_yaxis(ax, floor, log_top or ceil["optimistic"].max() * 1.4)
        label_ceiling = ax.get_ylim()[1]
    else:
        ax.set_ylim(0, Y_MAX_TB)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
        label_ceiling = Y_MAX_TB
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Labels. Every rate in a label is derived from the rate it names, so a
    # label can never disagree with its own line.
    x_end = START_YEAR + TOTAL_YEARS
    items = [(series, sc.chart_label(key), colour)
             for series, key, colour in demand]

    if log:
        # Everything fits, so all labels go to the right edge and are spaced
        # there in one pass.
        items += [(ceil[c], sc.hw_label(c), LABEL_CEIL_COLOR)
                  for c in CEILINGS]
    else:
        for x, y, case, rot in [(2045, 13, "optimistic", 90),
                                (2062, 15.8, "base", 0),
                                (2098, 12.5, "pessimistic", 0)]:
            ax.text(x, y, sc.hw_label(case).replace("\n", " "),
                    fontsize=LABEL_FONTSIZE, color=LABEL_CEIL_COLOR,
                    ha="center", va="center", rotation=rot)

    smart_labels(ax, dates, items, label_ceiling, x_end,
                 min_gap=label_min_gap, log=log)

    group_legend(ax, "Node storage capacity", "Chain growth",
                 chain_color=CHAIN_RAMP[1])

    if footnote:
        fig.text(0.5, -0.02, footnote, ha="center", fontsize=6.5,
                 color="#666666", style="italic")

    fig.subplots_adjust(right=0.76)
    save(fig, f"fig-storage{suffix}")
    plt.close(fig)


if __name__ == "__main__":
    # No on-figure footnote. The style spec puts detail in the caption, and
    # the decay rule, the upgrade cycle and the log axis are all stated in
    # section 4, appendix C.4 and the figure caption respectively.
    make_chart(log=True)
