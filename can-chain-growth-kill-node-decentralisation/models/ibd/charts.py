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
import scenarios as sc
from chart_style import (
    CEIL_LINE_BASE, CEIL_FILL_COLOR, CEIL_FILL_ALPHA,
    CEIL_LW_BASE,
    CHAIN_RAMP, CHAIN_LW,
    LABEL_CEIL_COLOR, LABEL_CHAIN_COLOR,
    FIGSIZE, TOTAL_YEARS, START_YEAR, GRID_ALPHA,
    save, smart_labels, group_legend, log_yaxis,
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

# Top of the log axis. The optimistic ceiling reaches ~580 TB by 2110, which
# would push every chain line into the bottom of the plot. 100 TB keeps the
# cloud running off the top, as on the storage chart.
Y_TOP_LOG_TB = 100
FV_GROWTH_REF = 80

# Upper bracket for the bisection below, in GB. It was 50,000 (50 TB), which
# is smaller than the optimistic ceiling from about 2100 on, so both the
# optimistic and base ceiling lines flattened onto the bracket itself rather
# than onto anything the model says. On the old 18 TB linear axis both lines
# had left the plot long before, so the artefact never showed.
CEIL_SEARCH_MAX_GB = 5_000_000

HW_OPT = 2.0
HW_BASE = HW_IMPROVEMENT_PER_DECADE  # 1.5
HW_PESS = 1.2

RATE_WORST = sc.RATE_REALISTIC_WORST
RATE_PEAK = sc.RATE_PEAK
RATE_CUR = sc.RATE_CURRENT

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

            lo, hi = 0.0, CEIL_SEARCH_MAX_GB
            for _ in range(200):
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
    ax.plot(dates, ch_cur, color=CHAIN_RAMP[1], linewidth=CHAIN_LW,
            linestyle="-", zorder=5)
    ax.plot(dates, ch_peak, color=CHAIN_RAMP[2], linewidth=CHAIN_LW,
            linestyle="-", zorder=5)
    ax.plot(dates, ch_worst, color=CHAIN_RAMP[3], linewidth=CHAIN_LW,
            linestyle="-", zorder=5)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("Chain size (TB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + TOTAL_YEARS)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(10))
    log_yaxis(ax, min(ch_cur.min(), ceil_pess.min()), Y_TOP_LOG_TB)
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    # Every label goes to the right edge and is spaced there in one pass,
    # in log space so the gaps stay even on screen.
    x_end = START_YEAR + TOTAL_YEARS
    y_top = ax.get_ylim()[1]
    smart_labels(ax, dates, [
        (ch_cur, sc.chart_label("current"), CHAIN_RAMP[1]),
        (ch_peak, sc.chart_label("peak"), CHAIN_RAMP[2]),
        (ch_worst, sc.chart_label("realistic_worst"), CHAIN_RAMP[3]),
        (ceil_opt, "Optimistic\n(2x/decade)", LABEL_CEIL_COLOR),
        (ceil_base, "Base\n(1.5x/decade)", LABEL_CEIL_COLOR),
        (ceil_pess, "Pessimistic\n(1.2x/decade)", LABEL_CEIL_COLOR),
    ], y_top, x_end, log=True)

    group_legend(ax, "7-day processing limit", "Chain size", chain_color=CHAIN_RAMP[1])

    fig.subplots_adjust(right=0.78)
    save(fig, "fig-ibd")
    plt.close(fig)


if __name__ == "__main__":
    make_chart()
