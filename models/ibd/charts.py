"""
IBD: processing ceiling vs chain growth, 80-year outlook.

1 grey ceiling line + cloud (HW improvement rates).
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
    HW_IMPROVEMENT_PER_DECADE,
    UPGRADE_INTERVAL_YEARS,
    SIGOPS_PER_GB_MIXED,
    ibd_time_hours,
    utxo_chainstate_gb,
)

# ── Constants ─────────────────────────────────────────────────────────

Y_MAX_TB = 18
FV_GROWTH_REF = 80

HW_OPT = 2.0
HW_BASE = HW_IMPROVEMENT_PER_DECADE  # 1.5
HW_PESS = 1.2

RATE_WORST = 196
RATE_PEAK = 118
RATE_CUR = 80

CEIL_SIGOPS = SIGOPS_PER_GB_MIXED


# ── Chart ─────────────────────────────────────────────────────────────

def make_chart():
    years = np.arange(0, TOTAL_YEARS + 1)
    dates = START_YEAR + years

    def ceiling_tb(hw_rate):
        out = []
        for yr in years:
            yr_int = int(yr)
            hw_mult = hw_rate ** (yr_int / UPGRADE_INTERVAL_YEARS)
            chainstate = utxo_chainstate_gb(yr_int)
            target_hours = MAX_IBD_DAYS * 24 * hw_mult

            lo, hi = 0.0, 50_000.0
            for _ in range(100):
                mid = (lo + hi) / 2
                result = ibd_time_hours(
                    mid, FV_GROWTH_REF, CEIL_SIGOPS, chainstate,
                    software_improvement=False,
                )
                if result["total_hours"] <= target_hours:
                    lo = mid
                else:
                    hi = mid
            out.append(lo / 1000)
        return np.array(out)

    def chain_tb(rate):
        return (CHAIN_SIZE_GB_2026 + rate * years) / 1000

    ceil_opt = ceiling_tb(HW_OPT)
    ceil_base = ceiling_tb(HW_BASE)
    ceil_pess = ceiling_tb(HW_PESS)

    ch_worst = chain_tb(RATE_WORST)
    ch_peak = chain_tb(RATE_PEAK)
    ch_cur = chain_tb(RATE_CUR)

    fig, ax = plt.subplots(figsize=FIGSIZE)

    # Ceiling fill between bounds
    ax.fill_between(dates, ceil_pess, ceil_opt,
                    facecolor=CEIL_FILL_COLOR, edgecolor="none",
                    alpha=CEIL_FILL_ALPHA, zorder=2)

    # Ceiling base line only
    ax.plot(dates, ceil_base, color=CEIL_LINE_BASE, linewidth=CEIL_LW_BASE,
            linestyle="-", zorder=5)

    # Chain growth lines (no fill)
    ax.plot(dates, ch_cur, color=CHAIN_COLOR, linewidth=CHAIN_LW_CONS,
            linestyle=":", zorder=5)
    ax.plot(dates, ch_peak, color=CHAIN_COLOR, linewidth=CHAIN_LW_BASE,
            linestyle="--", zorder=5)
    ax.plot(dates, ch_worst, color=CHAIN_COLOR_MAX, linewidth=CHAIN_LW_MAX,
            linestyle=":", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Chain size (TB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.set_ylim(0, Y_MAX_TB)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Ceiling labels — curved along their lines
    label_along_curve(ax, dates, ceil_opt, "Optimistic (2x/decade)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX_TB)
    label_along_curve(ax, dates, ceil_base, "Base (1.5x/decade)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX_TB)
    label_along_curve(ax, dates, ceil_pess, "Pessimistic (1.2x/decade)",
                      LABEL_CEIL_COLOR, y_max=Y_MAX_TB)

    # Chain labels — right edge
    x_end = START_YEAR + TOTAL_YEARS
    smart_labels(ax, dates, [
        (ch_cur, "Current\n(80 GB/yr)", LABEL_CHAIN_COLOR),
        (ch_peak, "March 2024 peak\n(118 GB/yr)", LABEL_CHAIN_COLOR),
        (ch_worst, "Sustained data-heavy\n(196 GB/yr)", LABEL_CHAIN_COLOR),
    ], Y_MAX_TB, x_end)

    group_legend(ax, "7-day processing limit", "Chain size")

    fig.subplots_adjust(right=0.78)
    save(fig, "fig-ibd")
    plt.close(fig)


if __name__ == "__main__":
    make_chart()
