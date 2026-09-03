"""
Storage, near term: chain size vs the usable space on one 2 TB SSD.

The 80-year chart (charts.py) answers the cross-generational question and
squeezes the first decade into its left margin. This one covers only the
first hardware cycle, where the headline finding lives: at what point does
each growth scenario exhaust the disk?
"""

import pathlib
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scenarios as sc
from chart_style import (
    CEIL_LINE_BASE, CHAIN_RAMP, CHAIN_LW, BOUND_COLOR, BOUND_LS,
    REF_COLOR, REF_LW,
    LABEL_FONTSIZE, LABEL_CEIL_COLOR, LABEL_CHAIN_COLOR,
    GRID_ALPHA, save,
)

START_YEAR = 2026
YEARS = 10

import model as storage_model

CHAIN_GB_2026 = sc.CHAIN_GB_2026
CHAINSTATE_GB_2026 = sc.CHAINSTATE_GB_2025
CHAINSTATE_GROWTH = 0.5      # GB/yr at organic monetary rates
USABLE_GB = float(sc.SSD_GB)  # 2 TB minus ext4 reserve, OS, swap, logs

CEILING_RATE = storage_model.max_growth_rate_disk(10)


def _lab(name, rate):
    return f"{name}\n{rate:.0f} GB/yr"


# Demand scenarios: same weight, coloured by severity along CHAIN_RAMP.
# Reference lines (a derived threshold and a hard bound) are grey and thinner
# so they read as the frame rather than as forecasts.
SCENARIOS = [
    (sc.RATE_MONETARY, _lab("Monetary only", sc.RATE_MONETARY),
     CHAIN_RAMP[0], CHAIN_LW, "-"),
    (sc.RATE_CURRENT, _lab("Current", sc.RATE_CURRENT),
     CHAIN_RAMP[1], CHAIN_LW, "-"),
    (sc.RATE_PEAK, _lab("March 2024 peak", sc.RATE_PEAK),
     CHAIN_RAMP[2], CHAIN_LW, "-"),
    (sc.RATE_REALISTIC_WORST, _lab("Realistic worst", sc.RATE_REALISTIC_WORST),
     CHAIN_RAMP[3], CHAIN_LW, "-"),
    (CEILING_RATE, _lab("Ceiling rate", CEILING_RATE),
     REF_COLOR, REF_LW, "--"),
    (sc.RATE_THEORETICAL_MAX, _lab("Theoretical max", sc.RATE_THEORETICAL_MAX),
     BOUND_COLOR, CHAIN_LW, BOUND_LS),
]


def disk_used_gb(t, growth):
    """Blockchain plus chainstate on disk after t years."""
    return (CHAIN_GB_2026 + growth * t) + (CHAINSTATE_GB_2026 + CHAINSTATE_GROWTH * t)


def exhaustion_year(growth):
    """Years until disk_used crosses USABLE_GB, or None inside the window."""
    denom = growth + CHAINSTATE_GROWTH
    t = (USABLE_GB - CHAIN_GB_2026 - CHAINSTATE_GB_2026) / denom
    return t if t <= YEARS else None


def main():
    t = np.linspace(0, YEARS, YEARS * 100 + 1)
    dates = START_YEAR + t

    fig, ax = plt.subplots(figsize=(8, 4.2))

    # Everything above the ceiling is disk the machine does not have.
    ax.axhspan(USABLE_GB, 2800, facecolor="#000000", alpha=0.045, zorder=1)
    ax.axhline(USABLE_GB, color=CEIL_LINE_BASE, linewidth=1.4, zorder=6)
    ax.text(START_YEAR + 0.15, USABLE_GB + 55,
            "Usable space on a 2 TB SSD: 1,850 GB",
            fontsize=7.5, color=CEIL_LINE_BASE, va="bottom", ha="left")

    label_points = []
    for growth, label, color, lw, ls in SCENARIOS:
        used = disk_used_gb(t, growth)
        ax.plot(dates, used, color=color, linewidth=lw, linestyle=ls, zorder=5)

        cross = exhaustion_year(growth)
        if cross is not None:
            ax.plot([START_YEAR + cross], [USABLE_GB], marker="o", markersize=4,
                    color=color, markeredgecolor="white", markeredgewidth=0.6,
                    zorder=7)
            ax.text(START_YEAR + cross, USABLE_GB - 70,
                    f"{START_YEAR + cross:.0f}", fontsize=6.5, color=color,
                    ha="center", va="top")

        label_points.append((min(used[-1], 2750), label, color))

    # Nudge right-edge labels apart so they stay readable.
    label_points.sort(key=lambda p: p[0])
    ys = [p[0] for p in label_points]
    min_gap = 165
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < min_gap:
            ys[i] = ys[i - 1] + min_gap
    for y, (_, label, color) in zip(ys, label_points):
        ax.text(START_YEAR + YEARS + 0.12, y, label, fontsize=6.5,
                color=color, va="center", ha="left", clip_on=False)

    ax.set_xlabel("Year", fontsize=8)
    ax.set_ylabel("On disk: blockchain + chainstate (GB)", fontsize=8)
    ax.set_xlim(START_YEAR, START_YEAR + YEARS)
    ax.set_ylim(600, 2800)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(250))
    ax.yaxis.grid(True, alpha=GRID_ALPHA, linewidth=0.4)

    fig.text(0.5, -0.03,
             "Markers show the year each scenario exhausts the disk. "
             "Hardware held constant. This is one machine, not an upgrade path.",
             ha="center", fontsize=6.5, color="#666666", style="italic")

    fig.subplots_adjust(right=0.80)
    save(fig, "fig-storage-nearterm")
    plt.close(fig)

    for growth, label, *_ in SCENARIOS:
        cross = exhaustion_year(growth)
        flat = label.replace("\n", " ")
        if cross is None:
            print(f"{flat:32s} survives the {YEARS}-year cycle")
        else:
            print(f"{flat:32s} exhausts disk after {cross:.1f} yr "
                  f"({START_YEAR + cross:.0f})")


if __name__ == "__main__":
    main()
