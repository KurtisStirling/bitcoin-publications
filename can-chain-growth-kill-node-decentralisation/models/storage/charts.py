"""
Storage: node capacity ceiling vs chain growth, 80-year outlook.

1 grey ceiling line + cloud (HW growth rates).
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
    LABEL_FONTSIZE, LABEL_CEIL_COLOR, LABEL_CHAIN_COLOR,
    FIGSIZE, TOTAL_YEARS, START_YEAR, GRID_ALPHA,
    save, smart_labels, group_legend, label_along_curve,
)

# ── Constants ─────────────────────────────────────────────────────────

CHAIN_GB_2026 = 724.0
DEVICE_0_TB = 1.85  # 2 TB NVMe minus ext4 reserved (5%, 100 GB) minus OS/swap/logs (50 GB)
UPGRADE_INTERVAL = 10
Y_MAX_TB = 18

HW_RATE_OPTIMISTIC = 0.15
HW_RATE_BASE = 0.10
HW_RATE_PESSIMISTIC = 0.05

RATE_WORST = 196
RATE_PEAK = 118
RATE_CURRENT = 80


# ── Helpers ───────────────────────────────────────────────────────────

def hw_cap_tb_stepped(t, rate):
    upgrades = int(t) // UPGRADE_INTERVAL
    return DEVICE_0_TB * (1 + rate) ** (upgrades * UPGRADE_INTERVAL)


def hw_cap_tb_smooth(t, rate):
    return DEVICE_0_TB * (1 + rate) ** t


DECAY_RATE = 0.02  # rate shrinks by 2% of itself each year


def hw_cap_tb_stepped_decay(t, rate, decay=DECAY_RATE):
    """Decaying-rate stepped: rate shrinks each year, upgrade every interval."""
    upgrades = int(t) // UPGRADE_INTERVAL
    effective_years = upgrades * UPGRADE_INTERVAL
    cap = DEVICE_0_TB
    for y in range(effective_years):
        cap *= (1 + rate * (1 - decay) ** y)
    return cap


def chain_tb(t, growth):
    return (CHAIN_GB_2026 + growth * t) / 1000


# ── Chart ─────────────────────────────────────────────────────────────

def make_chart(hw_cap_fn, suffix, footnote=None, label_min_gap=None):
    t = np.linspace(0, TOTAL_YEARS, TOTAL_YEARS * 100 + 1)
    dates = START_YEAR + t

    hw_opt = np.array([hw_cap_fn(y, HW_RATE_OPTIMISTIC) for y in t])
    hw_base = np.array([hw_cap_fn(y, HW_RATE_BASE) for y in t])
    hw_pess = np.array([hw_cap_fn(y, HW_RATE_PESSIMISTIC) for y in t])

    ch_worst = np.array([chain_tb(y, RATE_WORST) for y in t])
    ch_peak = np.array([chain_tb(y, RATE_PEAK) for y in t])
    ch_cur = np.array([chain_tb(y, RATE_CURRENT) for y in t])

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Ceiling fill between bounds
    ax.fill_between(dates, hw_pess, hw_opt,
                    facecolor=CEIL_FILL_COLOR, edgecolor="none",
                    alpha=CEIL_FILL_ALPHA, zorder=2)

    # Ceiling base line only
    ax.plot(dates, hw_base, color=CEIL_LINE_BASE, linewidth=CEIL_LW_BASE,
            linestyle="-", zorder=5)

    # Chain growth lines (no fill)
    ax.plot(dates, ch_cur, color=CHAIN_COLOR, linewidth=CHAIN_LW_CONS,
            linestyle=":", zorder=5)
    ax.plot(dates, ch_peak, color=CHAIN_COLOR, linewidth=CHAIN_LW_BASE,
            linestyle="--", zorder=5)
    ax.plot(dates, ch_worst, color=CHAIN_COLOR_MAX, linewidth=CHAIN_LW_MAX,
            linestyle=":", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Storage (TB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.set_ylim(0, Y_MAX_TB)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Ceiling labels — placed manually inside the grey fill
    for x, y, label, rot in [
        (2045, 13, "Optimistic (15%/yr)", 90),
        (2062, 15.8, "Base (10%/yr)", 0),
        (2098, 12.5, "Pessimistic (5%/yr)", 0),
    ]:
        ax.text(x, y, label, fontsize=LABEL_FONTSIZE, color=LABEL_CEIL_COLOR,
                ha="center", va="center", rotation=rot)

    # Chain labels — right edge
    x_end = START_YEAR + TOTAL_YEARS
    smart_labels(ax, dates, [
        (ch_cur, "Current\n(80 GB/yr)", LABEL_CHAIN_COLOR),
        (ch_peak, "March 2024 peak\n(118 GB/yr)", LABEL_CHAIN_COLOR),
        (ch_worst, "Sustained data-heavy\n(196 GB/yr)", LABEL_CHAIN_COLOR),
    ], Y_MAX_TB, x_end, min_gap=label_min_gap)

    group_legend(ax, "Node storage capacity", "Chain growth")

    if footnote:
        fig.text(0.5, -0.02, footnote, ha="center", fontsize=6.5,
                 color="#666666", style="italic")

    fig.subplots_adjust(right=0.78)
    save(fig, f"fig-storage{suffix}")
    plt.close(fig)


if __name__ == "__main__":
    make_chart(
        hw_cap_tb_stepped_decay, "",
        footnote=(
            "Storage improvement rates decay at 2%/yr.  "
            "Steps represent a 10-year hardware upgrade cycle."
        ),
        label_min_gap=1.5,
    )
