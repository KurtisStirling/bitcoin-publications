"""
Bandwidth: required IBD download speed vs residential internet, 80-year outlook.

1 grey ceiling line + cloud (internet tiers).
3 orange chain lines (growth scenarios). Smart labels at exit points.
"""

import pathlib
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from chart_style import (
    CEIL_LINE_BASE, CEIL_FILL_COLOR, CEIL_FILL_ALPHA,
    CEIL_LW_BASE,
    CHAIN_COLOR, CHAIN_COLOR_MAX, CHAIN_LW_CONS, CHAIN_LW_BASE, CHAIN_LW_MAX,
    LABEL_CEIL_COLOR, LABEL_CHAIN_COLOR,
    FIGSIZE, TOTAL_YEARS, START_YEAR, GRID_ALPHA,
    save, smart_labels, group_legend, label_along_curve,
)

from model import (
    CHAIN_SIZE_GB_2026,
    MAX_IBD_DAYS,
)

# ── Constants ─────────────────────────────────────────────────────────

SECONDS_PER_DAY = 86_400
Y_MAX = 250

RATE_WORST = 196
RATE_PEAK = 118
RATE_CURRENT = 80

# Pessimistic internet trajectories (deliberately 2-5x below observed)
INET_DEV_BASE = 5.0      # Mbps (actual India: 60)
INET_DEV_CAGR = 0.05
INET_GLOBAL_BASE = 25.0  # Mbps (actual Ookla median: 104)
INET_GLOBAL_CAGR = 0.04
INET_RICH_BASE = 50.0    # Mbps (actual USA: 303)
INET_RICH_CAGR = 0.04


# ── Helpers ───────────────────────────────────────────────────────────

def chain_ibd_mbps(growth_gb_yr, year):
    chain_gb = CHAIN_SIZE_GB_2026 + growth_gb_yr * year
    gb_per_day = chain_gb / MAX_IBD_DAYS
    return gb_per_day * 1024 * 8 / SECONDS_PER_DAY


def inet_mbps(base, cagr, year):
    return base * (1 + cagr) ** year


# ── Chart ─────────────────────────────────────────────────────────────

def make_chart():
    years = np.arange(0, TOTAL_YEARS + 1)
    dates = START_YEAR + years

    # Ceiling: internet supply (developing = pessimistic, developed = optimistic)
    inet_pess = np.array([inet_mbps(INET_DEV_BASE, INET_DEV_CAGR, yr) for yr in years])
    inet_base = np.array([inet_mbps(INET_GLOBAL_BASE, INET_GLOBAL_CAGR, yr) for yr in years])
    inet_opt = np.array([inet_mbps(INET_RICH_BASE, INET_RICH_CAGR, yr) for yr in years])

    # Demand: required download speed
    req_worst = np.array([chain_ibd_mbps(RATE_WORST, yr) for yr in years])
    req_peak = np.array([chain_ibd_mbps(RATE_PEAK, yr) for yr in years])
    req_cur = np.array([chain_ibd_mbps(RATE_CURRENT, yr) for yr in years])

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Ceiling fill between bounds (axes clip handles y_max)
    ax.fill_between(dates, inet_pess, inet_opt,
                    facecolor=CEIL_FILL_COLOR, edgecolor="none",
                    alpha=CEIL_FILL_ALPHA, zorder=2)

    # Ceiling base line only
    ax.plot(dates, inet_base, color=CEIL_LINE_BASE, linewidth=CEIL_LW_BASE,
            linestyle="-", zorder=5)

    # Chain growth lines (no fill)
    ax.plot(dates, req_cur, color=CHAIN_COLOR, linewidth=CHAIN_LW_CONS,
            linestyle=":", zorder=5)
    ax.plot(dates, req_peak, color=CHAIN_COLOR, linewidth=CHAIN_LW_BASE,
            linestyle="--", zorder=5)
    ax.plot(dates, req_worst, color=CHAIN_COLOR_MAX, linewidth=CHAIN_LW_MAX,
            linestyle=":", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Download speed (Mbps)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.set_ylim(0, Y_MAX)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(50))
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Ceiling labels — curved along their lines, right-aligned to exit point
    label_along_curve(ax, dates, inet_opt, "Optimistic (developed)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX)
    label_along_curve(ax, dates, inet_base, "Base (global)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX)
    label_along_curve(ax, dates, inet_pess, "Pessimistic (developing)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX)

    # Chain labels — right edge
    x_end = START_YEAR + TOTAL_YEARS
    smart_labels(ax, dates, [
        (req_cur, "Current growth\n(80 GB/yr)", LABEL_CHAIN_COLOR),
        (req_peak, "March 2024 peak\n(118 GB/yr)", LABEL_CHAIN_COLOR),
        (req_worst, "Sustained data-heavy\n(196 GB/yr)", LABEL_CHAIN_COLOR),
    ], Y_MAX, x_end)

    group_legend(ax, "Internet speed", "7-day IBD requires")

    fig.subplots_adjust(right=0.78)
    save(fig, "fig-bandwidth")
    plt.close(fig)


if __name__ == "__main__":
    make_chart()
