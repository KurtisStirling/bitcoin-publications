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
import scenarios as sc
from chart_style import (
    CEIL_LINE_BASE, CEIL_FILL_COLOR, CEIL_FILL_ALPHA,
    CEIL_LW_BASE,
    CHAIN_RAMP, CHAIN_LW,
    LABEL_CEIL_COLOR,
    FIGSIZE, TOTAL_YEARS, START_YEAR, GRID_ALPHA,
    save, smart_labels, group_legend, log_yaxis,
)

# ── Constants ─────────────────────────────────────────────────────────

CHAINSTATE_GB_2026 = sc.CHAINSTATE_GB_2025
BYTES_PER_ENTRY = sc.BYTES_PER_UTXO_ENTRY

RAM_TOTAL_GB = sc.RAM_GB
RAM_OVERHEAD_GB = 4
UPGRADE_INTERVAL = sc.HW_UPGRADE_INTERVAL

RAM_MULT_OPT = 3.0
RAM_MULT_BASE = 2.0
RAM_MULT_PESS = 1.5

UTXO_WORST_PER_YR = 20_000_000
UTXO_REAL_PER_YR = sc.UTXO_ENTRIES_PER_YEAR
UTXO_CURRENT_PER_YR = 5_000_000

# Top of the log axis. The base RAM ceiling reaches ~5,400 GB by 2110 and the
# optimistic one far more, so the cloud runs off the top as it does on the
# storage chart. The old 120 GB linear cap cut every ceiling line off before
# 2050 and left only the chainstate lines visible.
Y_TOP_LOG_GB = 1000


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

    # Growth scenarios: ordered by rate, so colour carries the severity and
    # every line is the same weight and solid. They were previously separated
    # by dash pattern and thickness, which the style spec bans.
    ax.plot(dates, cs_curr, color=CHAIN_RAMP[1], linewidth=CHAIN_LW,
            linestyle="-", zorder=5)
    ax.plot(dates, cs_real, color=CHAIN_RAMP[2], linewidth=CHAIN_LW,
            linestyle="-", zorder=5)
    ax.plot(dates, cs_worst, color=CHAIN_RAMP[3], linewidth=CHAIN_LW,
            linestyle="-", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Size (GB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    log_yaxis(ax, min(cs_curr.min(), ram_pess.min()), Y_TOP_LOG_GB)
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Labels are colour-matched to their own line, not to a shared orange.
    x_end = START_YEAR + TOTAL_YEARS
    y_top = ax.get_ylim()[1]
    smart_labels(ax, dates, [
        (cs_curr, f"Current\n({UTXO_CURRENT_PER_YR // 1_000_000}M/yr)",
         CHAIN_RAMP[1]),
        (cs_real, f"Organic rate\n({UTXO_REAL_PER_YR // 1_000_000}M/yr)",
         CHAIN_RAMP[2]),
        (cs_worst, f"2024 peak\n({UTXO_WORST_PER_YR // 1_000_000}M/yr)",
         CHAIN_RAMP[3]),
        (ram_opt, f"Optimistic\n({RAM_MULT_OPT:g}x/decade)", LABEL_CEIL_COLOR),
        (ram_base, f"Base\n({RAM_MULT_BASE:g}x/decade)", LABEL_CEIL_COLOR),
        (ram_pess, f"Pessimistic\n({RAM_MULT_PESS:g}x/decade)", LABEL_CEIL_COLOR),
    ], y_top, x_end, log=True)

    group_legend(ax, "Available RAM", "UTXO set size",
                 chain_color=CHAIN_RAMP[1])

    fig.subplots_adjust(right=0.78)
    save(fig, "fig-utxo")
    plt.close(fig)


if __name__ == "__main__":
    make_chart()
