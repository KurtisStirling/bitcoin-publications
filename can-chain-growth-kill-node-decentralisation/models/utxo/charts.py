"""
UTXO: RAM ceiling vs chainstate size, 80-year outlook.

1 grey ceiling line + cloud (RAM growth rates).
3 orange chain lines (UTXO growth scenarios). Smart labels at exit points.
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

# ── Constants ─────────────────────────────────────────────────────────

CHAINSTATE_GB_2026 = 11.0
BYTES_PER_ENTRY = 63

RAM_TOTAL_GB = 16
RAM_OVERHEAD_GB = 4
UPGRADE_INTERVAL = 10

RAM_MULT_OPT = 3.0
RAM_MULT_BASE = 2.0
RAM_MULT_PESS = 1.5

UTXO_WORST_PER_YR = 20_000_000
UTXO_REAL_PER_YR = 8_000_000
UTXO_CURRENT_PER_YR = 5_000_000

Y_MAX_GB = 120


# ── Helpers ───────────────────────────────────────────────────────────

def ram_ceil_gb(t, mult):
    total = RAM_TOTAL_GB * mult ** (t / UPGRADE_INTERVAL)
    return total - RAM_OVERHEAD_GB


def chainstate_gb(t, entries_per_yr):
    growth_gb = (entries_per_yr * t * BYTES_PER_ENTRY) / 1e9
    return CHAINSTATE_GB_2026 + growth_gb


# ── Chart ─────────────────────────────────────────────────────────────

def make_chart():
    t = np.linspace(0, TOTAL_YEARS, TOTAL_YEARS * 100 + 1)
    dates = START_YEAR + t

    ram_opt = np.array([ram_ceil_gb(y, RAM_MULT_OPT) for y in t])
    ram_base = np.array([ram_ceil_gb(y, RAM_MULT_BASE) for y in t])
    ram_pess = np.array([ram_ceil_gb(y, RAM_MULT_PESS) for y in t])

    cs_worst = np.array([chainstate_gb(y, UTXO_WORST_PER_YR) for y in t])
    cs_real = np.array([chainstate_gb(y, UTXO_REAL_PER_YR) for y in t])
    cs_curr = np.array([chainstate_gb(y, UTXO_CURRENT_PER_YR) for y in t])

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Ceiling fill between bounds (axes clip handles y_max)
    ax.fill_between(dates, ram_pess, ram_opt,
                    facecolor=CEIL_FILL_COLOR, edgecolor="none",
                    alpha=CEIL_FILL_ALPHA, zorder=2)

    # Ceiling base line only
    ax.plot(dates, ram_base, color=CEIL_LINE_BASE, linewidth=CEIL_LW_BASE,
            linestyle="-", zorder=5)

    # Chain growth lines (no fill)
    ax.plot(dates, cs_curr, color=CHAIN_COLOR, linewidth=CHAIN_LW_CONS,
            linestyle=":", zorder=5)
    ax.plot(dates, cs_real, color=CHAIN_COLOR, linewidth=CHAIN_LW_BASE,
            linestyle="--", zorder=5)
    ax.plot(dates, cs_worst, color=CHAIN_COLOR_MAX, linewidth=CHAIN_LW_MAX,
            linestyle=":", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Size (GB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.set_ylim(0, Y_MAX_GB)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(20))
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Ceiling labels — curved along their lines
    label_along_curve(ax, dates, ram_opt, "Optimistic (3x/decade)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX_GB)
    label_along_curve(ax, dates, ram_base, "Base (2x/decade)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX_GB)
    label_along_curve(ax, dates, ram_pess, "Pessimistic (1.5x/decade)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX_GB)

    # Chain labels — right edge
    x_end = START_YEAR + TOTAL_YEARS
    smart_labels(ax, dates, [
        (cs_curr, "Current\n(5M/yr)", LABEL_CHAIN_COLOR),
        (cs_real, "Organic rate\n(8M/yr)", LABEL_CHAIN_COLOR),
        (cs_worst, "2024 peak\n(20M/yr)", LABEL_CHAIN_COLOR),
    ], Y_MAX_GB, x_end)

    group_legend(ax, "Available RAM", "UTXO set size")

    fig.subplots_adjust(right=0.78)
    save(fig, "fig-utxo")
    plt.close(fig)


if __name__ == "__main__":
    make_chart()
