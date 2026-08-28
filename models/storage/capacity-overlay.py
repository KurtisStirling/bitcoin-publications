"""
fig-storage-capacity-probabilistic: probabilistic storage capacity fan chart
with chain growth.

Same AR(1) model and visual style as fig-storage-cost-probabilistic, but y-axis is
TB affordable instead of $/GB (flips the fan upward). Log y-axis (the
inverse of an exponential decline is exponential growth — log keeps it
smooth). Chain size overlaid to show the gap.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# ── Constants ────────────────────────────────────────────────────────

SSD_PRICE_2026 = 0.11       # $/GB, SSD anchor point
USABLE_TB_2026 = 1.85       # known: 2TB SSD minus OS overhead

CHAIN_GB_2026 = 724.0
RATE_CURRENT = 80            # GB/yr
RATE_PEAK = 118              # GB/yr
RATE_MAX = 196               # GB/yr

# Historical chain size (GB, end of year). Sources: Statista, Blockchain.com
CHAIN_HISTORY = {
    2009: 0.01, 2010: 0.06, 2011: 0.84, 2012: 4.5, 2013: 13.7,
    2014: 27.8, 2015: 53.2, 2016: 94.7, 2017: 146, 2018: 193,
    2019: 250, 2020: 311, 2021: 374, 2022: 435, 2023: 525,
    2024: 612, 2025: 674, 2026: CHAIN_GB_2026,
}

# ── Load data & fit AR(1) ────────────────────────────────────────────

data_path = Path(__file__).resolve().parent.parent.parent.parent.parent / \
    'models' / 'storage' / 'composite-storage-series.json'

with open(data_path) as f:
    raw = json.load(f)

years_all = np.array([d['year'] for d in raw])
prices_all = np.array([d['cheapest_per_gb'] for d in raw])

# Historical SSD prices → TB affordable (SSD data only, for consistency
# with SSD-anchored forecast. AR(1) is fit on full composite for trajectory.)
ssd_years = []
ssd_tb = []
for d in raw:
    if d.get('ssd_per_gb') is not None:
        ssd_years.append(d['year'])
        ssd_tb.append(USABLE_TB_2026 * (SSD_PRICE_2026 / d['ssd_per_gb']))
ssd_years = np.array(ssd_years)
ssd_tb = np.array(ssd_tb)

# Fit AR(1) in log space on 1985-2026
log_prices_all = np.log10(prices_all)
fit_mask = years_all >= 1985
fit_years = years_all[fit_mask]
fit_log = log_prices_all[fit_mask]

year_grid = np.arange(int(fit_years[0]), int(fit_years[-1]) + 1)
log_grid = np.interp(year_grid, fit_years, fit_log)

X_prev = log_grid[:-1]
X_curr = log_grid[1:]
n = len(X_curr)
A = np.column_stack([np.ones(n), X_prev])
params, _, _, _ = np.linalg.lstsq(A, X_curr, rcond=None)
kappa_hat, phi_hat = params[0], params[1]

eps = X_curr - (kappa_hat + phi_hat * X_prev)
sigma_e = np.std(eps, ddof=2)

mse = np.sum(eps**2) / (n - 2)
XtX_inv = np.linalg.inv(A.T @ A)
se_kappa = np.sqrt(mse * XtX_inv[0, 0])
se_phi = np.sqrt(mse * XtX_inv[1, 1])

print(f"AR(1) fit: phi={phi_hat:.4f}, kappa={kappa_hat:.4f}, sigma_e={sigma_e:.4f}")

# ── Monte Carlo forecast (SSD-anchored) ──────────────────────────────

n_sims = 10000
start_year = 2026
end_year = 2066
horizon = end_year - start_year
forecast_years = np.arange(start_year + 1, end_year + 1)

x0 = np.log10(SSD_PRICE_2026)

np.random.seed(42)
price_paths = np.zeros((n_sims, horizon))

for i in range(n_sims):
    phi_i = np.clip(np.random.normal(phi_hat, se_phi), 0.01, 0.999)
    kappa_i = np.random.normal(kappa_hat, se_kappa)
    x = x0
    for t in range(horizon):
        x = kappa_i + phi_i * x + np.random.normal(0, sigma_e)
        price_paths[i, t] = x

# Convert to TB affordable
capacity_paths = USABLE_TB_2026 * (SSD_PRICE_2026 / 10**price_paths)

cap_p2_5 = np.percentile(capacity_paths, 2.5, axis=0)
cap_p25 = np.percentile(capacity_paths, 25, axis=0)
cap_p50 = np.percentile(capacity_paths, 50, axis=0)
cap_p75 = np.percentile(capacity_paths, 75, axis=0)
cap_p97_5 = np.percentile(capacity_paths, 97.5, axis=0)

print(f"\nCapacity forecast (median [95% CI]):")
for yr_offset in [10, 20, 30, 40]:
    idx = yr_offset - 1
    print(f"  {start_year + yr_offset}: "
          f"{cap_p50[idx]:.1f} TB  "
          f"[{cap_p2_5[idx]:.1f} - {cap_p97_5[idx]:.1f}]")

# ── Chart (matching fig-storage-cost-probabilistic style) ────────────

fig, ax = plt.subplots(1, 1, figsize=(10, 6))

# Historical SSD capacity (dots)
ax.scatter(ssd_years, ssd_tb, c='black', s=12, zorder=5, label='Historical data (SSD)')

# Historical chain size (black line)
hist_years = sorted(CHAIN_HISTORY.keys())
hist_tb = [CHAIN_HISTORY[y] / 1000 for y in hist_years]
ax.plot(hist_years, hist_tb, color='black', linewidth=1.5, zorder=5,
        label='Historical chain size')

# 95% CI
ax.fill_between(forecast_years, cap_p2_5, cap_p97_5,
                alpha=0.15, color='#2171b5', label='95% Confidence Interval')

# 50% CI
ax.fill_between(forecast_years, cap_p25, cap_p75,
                alpha=0.35, color='#2171b5', label='50% Confidence Interval')

# Median
ax.plot(forecast_years, cap_p50, '--', color='#2171b5', linewidth=1.5,
        label='Forecast median')

# Future chain growth fan
t_future = np.arange(0, horizon + 1)
future_years = start_year + t_future

ch_current_tb = (CHAIN_GB_2026 + RATE_CURRENT * t_future) / 1000
ch_peak_tb = (CHAIN_GB_2026 + RATE_PEAK * t_future) / 1000
ch_max_tb = (CHAIN_GB_2026 + RATE_MAX * t_future) / 1000

# Outer band: current to max
ax.fill_between(future_years, ch_current_tb, ch_max_tb,
                alpha=0.15, color='#F7931A', label='Chain growth range')

# Inner band: current to peak
ax.fill_between(future_years, ch_current_tb, ch_peak_tb,
                alpha=0.35, color='#F7931A')

# Peak observed as median-style line
ax.plot(future_years, ch_peak_tb, '--', color='#F7931A', linewidth=1.5,
        zorder=5, label='Peak observed (118 GB/yr)')

# Log scale
ax.set_yscale('log')
ax.set_ylabel('Storage (TB, log scale)', fontsize=11)
ax.set_xlabel('Year', fontsize=11)
ax.set_title('Storage capacity outlook: AR(1) meta-trend vs chain growth',
             fontsize=13)

# Y-axis formatting
def fmt_tb(x, p):
    if x >= 1000:
        return f'{x:,.0f} TB'
    elif x >= 1:
        return f'{x:.0f} TB'
    elif x >= 0.1:
        return f'{x:.1f} TB'
    elif x >= 0.001:
        return f'{x*1000:.0f} GB'
    else:
        return f'{x*1e6:.0f} MB'

ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_tb))

# X range
ax.set_xlim(2008, end_year + 2)

# Y limits
ax.set_ylim(0.1 / 1000, None)  # 100 MB = 0.0001 TB

# Grid
ax.grid(True, alpha=0.3, which='major')

# Legend
ax.legend(loc='lower right', fontsize=9)

plt.tight_layout()

# Save
out_dir = Path(__file__).resolve().parent.parent.parent / 'figures'
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'fig-storage-capacity-probabilistic.png'
plt.savefig(out_path, dpi=200, bbox_inches='tight')
print(f"\nSaved to {out_path}")

plt.close()
