"""
fig-storage-outlook: probabilistic fan chart for storage cost per GB.

Methodology adapted from Way et al. (2022, Joule), S.I. 5.1.
Uses the AR(1) model — same model Way et al. use for technologies with
volatile/mean-reverting costs (fossil fuels). Storage post-2010 fits this
pattern: bouncing within an order of magnitude, boom-bust cycles, no clear
exponential decline.

AR(1) model in log space (Way et al. Eq. 35-36):

    X_t = phi * X_{t-1} + epsilon_t + kappa

    where X_t = log10($/GB), phi in (0,1] is the autoregression parameter,
    epsilon_t ~ N(0, sigma_e^2) are IID shocks, and kappa is the drift constant.

Equivalently in Ornstein-Uhlenbeck form:

    X_t = X_{t-1} + (1-phi)(mu - X_{t-1}) + epsilon_t

    where mu = kappa/(1-phi) is the long-run equilibrium (mean-reversion target).

Key properties:
- phi close to 1: slow mean reversion, behaves like random walk with drift
- phi close to 0: fast mean reversion, stays near mu
- The long-run mean mu captures the secular trend direction
- sigma_e captures year-to-year volatility (boom-bust cycles, demand shocks)
- Mean reversion prevents the golden-era decline rate from dominating the forecast

Fit window: 1985-2026 (consumer hard drive era through SSD).
Plot: all data from 1955 for visual context.
Fan: median + 50% CI (dark) + 95% CI (light).
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from pathlib import Path

# --- Load data ---
data_path = Path(__file__).parent / 'composite-storage-series.json'
with open(data_path) as f:
    raw = json.load(f)

years_all = np.array([d['year'] for d in raw])
prices_all = np.array([d['cheapest_per_gb'] for d in raw])
log_prices_all = np.log10(prices_all)

# --- Fit window: 1985-2026 ---
fit_mask = years_all >= 1985
fit_years = years_all[fit_mask]
fit_log = log_prices_all[fit_mask]

# Need evenly-spaced annual data for AR(1). Some years have gaps.
# Interpolate to annual grid.
year_grid = np.arange(int(fit_years[0]), int(fit_years[-1]) + 1)
log_grid = np.interp(year_grid, fit_years, fit_log)

print(f"Fit window: {year_grid[0]}-{year_grid[-1]} ({len(year_grid)} annual points)")

# --- Fit AR(1) via OLS ---
# X_t = phi * X_{t-1} + kappa + epsilon_t
# Regress X_t on X_{t-1} (with intercept)
X_prev = log_grid[:-1]
X_curr = log_grid[1:]

# OLS: X_curr = kappa + phi * X_prev + epsilon
n = len(X_curr)
A = np.column_stack([np.ones(n), X_prev])
params, residuals_ols, rank, sv = np.linalg.lstsq(A, X_curr, rcond=None)
kappa_hat, phi_hat = params[0], params[1]

# Residuals
eps = X_curr - (kappa_hat + phi_hat * X_prev)
sigma_e = np.std(eps, ddof=2)  # 2 params estimated

# Long-run mean
mu = kappa_hat / (1 - phi_hat)

print(f"\nAR(1) parameters:")
print(f"  phi (autoregression):  {phi_hat:.4f}")
print(f"  kappa (drift):         {kappa_hat:.4f}")
print(f"  sigma_e (noise std):   {sigma_e:.4f}")
print(f"  mu (long-run mean):    {mu:.4f}  (=${10**mu:.4f}/GB)")
print(f"  Mean reversion half-life: {-np.log(2)/np.log(phi_hat):.1f} years")

# Parameter standard errors (for uncertainty sampling)
# Var(phi_hat) and Var(kappa_hat) from OLS
mse = np.sum(eps**2) / (n - 2)
XtX_inv = np.linalg.inv(A.T @ A)
se_kappa = np.sqrt(mse * XtX_inv[0, 0])
se_phi = np.sqrt(mse * XtX_inv[1, 1])
print(f"  SE(phi):   {se_phi:.4f}")
print(f"  SE(kappa): {se_kappa:.4f}")

# --- Monte Carlo forecast ---
n_sims = 10000
start_year = 2026
end_year = 2066  # 40-year horizon
horizon = end_year - start_year
forecast_years = np.arange(start_year + 1, end_year + 1)

# Start from the last observed log price
x0 = log_grid[-1]
print(f"\nStarting price ({start_year}): ${10**x0:.4f}/GB")

np.random.seed(42)
paths = np.zeros((n_sims, horizon))

for i in range(n_sims):
    # Sample parameters with uncertainty (Way et al. approach)
    phi_i = np.random.normal(phi_hat, se_phi)
    kappa_i = np.random.normal(kappa_hat, se_kappa)

    # Clamp phi to (0, 1) to keep process stationary
    phi_i = np.clip(phi_i, 0.01, 0.999)

    x = x0
    for t in range(horizon):
        e = np.random.normal(0, sigma_e)
        x = kappa_i + phi_i * x + e
        paths[i, t] = x

# Percentiles at each year
p2_5 = np.percentile(paths, 2.5, axis=0)
p25 = np.percentile(paths, 25, axis=0)
p50 = np.percentile(paths, 50, axis=0)
p75 = np.percentile(paths, 75, axis=0)
p97_5 = np.percentile(paths, 97.5, axis=0)

# Convert back to $/GB for reporting
print(f"\nForecast $/GB (median [95% CI]):")
for yr_offset in [5, 10, 20, 30, 40]:
    if yr_offset <= horizon:
        idx = yr_offset - 1
        print(f"  {start_year + yr_offset}: "
              f"${10**p50[idx]:.4f}  "
              f"[${10**p2_5[idx]:.4f} - ${10**p97_5[idx]:.4f}]")

# Implied annual rate at median
if horizon >= 10:
    median_10yr = 10**p50[9]
    start_price = 10**x0
    implied_rate = (median_10yr / start_price) ** (1/10) - 1
    print(f"\nImplied 10-year median annual change: {implied_rate*100:.1f}%/yr")

# --- Plot ---
fig, ax = plt.subplots(1, 1, figsize=(10, 6))

# All historical data (dots)
ax.scatter(years_all, prices_all, c='black', s=12, zorder=5, label='Historical data')

# Mark fit window start
fit_start_idx = np.argmin(np.abs(years_all - 1985))

# 95% confidence interval (light band)
ax.fill_between(forecast_years, 10**p2_5, 10**p97_5,
                alpha=0.15, color='#2171b5', label='95% Confidence Interval')

# 50% confidence interval (dark band)
ax.fill_between(forecast_years, 10**p25, 10**p75,
                alpha=0.35, color='#2171b5', label='50% Confidence Interval')

# Median line
ax.plot(forecast_years, 10**p50, '--', color='#2171b5', linewidth=1.5,
        label='Forecast median')


# Log scale
ax.set_yscale('log')
ax.set_ylabel('Cost per GB, USD (log scale)', fontsize=11)
ax.set_xlabel('Year', fontsize=11)
ax.set_title('Storage cost outlook: all-technology meta-trend', fontsize=13)

# Format y-axis with cleaner labels
def fmt_price(x, p):
    if x >= 1000:
        return f'${x:,.0f}'
    elif x >= 1:
        return f'${x:.0f}'
    elif x >= 0.01:
        return f'${x:.2f}'
    elif x >= 0.001:
        return f'${x:.3f}'
    else:
        return f'${x:.4f}'

ax.yaxis.set_major_formatter(ticker.FuncFormatter(fmt_price))

# X range
ax.set_xlim(1953, end_year + 2)

# Grid
ax.grid(True, alpha=0.3, which='major')
ax.grid(True, alpha=0.1, which='minor')

# Legend
ax.legend(loc='upper right', fontsize=9)

plt.tight_layout()

# Save
out_dir = Path(__file__).resolve().parents[2] / 'figures'
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'fig-storage-outlook.png'
plt.savefig(out_path, dpi=200, bbox_inches='tight')
print(f"\nSaved to {out_path}")

plt.close()
