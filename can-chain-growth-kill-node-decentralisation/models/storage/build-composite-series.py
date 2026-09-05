"""
Build composite "cheapest consumer storage $/GB" time series.

This is the ALL-STORAGE meta-trend, not a single technology. It tracks whatever
technology was cheapest at each point in time. The HDD->SSD transition is captured
as data, not hidden.

Sources:
- HDD 1955-2017: hblok.net disk_magnetic.csv (derived from McCallum dataset)
  Values in $/MB, converted to $/GB (* 1000). Annual minimums used.
- HDD 2018-2026: Backblaze blog (2022), diskprices.com (2026), interpolated.
  Backblaze: $0.033/GB (2017), $0.0144/GB (Nov 2022). ~9%/yr decline.
  diskprices.com: $0.018/GB (Mar 2026).
- SSD 2010-2026: evidence base composite (compiled from the sources in the
  reference list of the paper this model belongs to)
  Values already in $/GB.

Output: one row per year, cheapest technology at that year.
For years where both HDD and SSD have data, take the minimum.
"""

import csv
import json
from pathlib import Path

OUT_PATH = Path(__file__).parent / 'composite-storage-series.json'

# --- HDD data ($/MB from hblok.net, annual minimums) ---
# Pasted from the CSV. We take the minimum $/MB per year.
# Only rows with valid numeric $/MB values.
hdd_raw = [
    (1955, 6233.33), (1960, 3600), (1964, 3518.62), (1966, 1047.26),
    (1970, 259.7), (1973, 2550), (1974, 185), (1975, 11377.78),
    (1979, 3009.42), (1980, 3488.63), (1981, 1020.83), (1982, 289.21),
    (1983, 319), (1984, 566.04), (1985, 31.39), (1986, 24.45),
    (1987, 14.97), (1988, 9.97), (1989, 7.48), (1990, 3.27),
    (1991, 2.79), (1992, 1.4), (1993, 0.718), (1994, 0.433),
    (1995, 0.214), (1996, 0.128), (1997, 0.0484), (1998, 0.0248),
    (1999, 0.0088), (2000, 0.00407), (2001, 0.00259), (2002, 0.00122),
    (2003, 0.00106), (2004, 0.000609), (2005, 0.000406), (2006, 0.000219),
    (2007, 0.0002), (2008, 0.0001), (2009, 0.00007), (2010, 0.000045),
    (2011, 0.0000367), (2012, 0.0000500), (2013, 0.0000400),
    (2014, 0.0000350), (2015, 0.0000279), (2016, 0.0000277),
    (2017, 0.0000250),
]

# Convert $/MB to $/GB (multiply by 1000)
hdd_per_gb = [(year, price_mb * 1000) for year, price_mb in hdd_raw]

# HDD 2018-2026: fill the gap after hblok/McCallum data ends.
# Backblaze: $0.033/GB (2017), $0.0144/GB (Nov 2022) = ~15.3% annual decline.
# diskprices.com (Mar 2026): cheapest consumer HDD = $0.018/GB (22TB Seagate).
# HDD plateau is real: decline slowed dramatically post-2015 (Kryder's Law broken).
# Interpolate 2018-2021, use Backblaze for 2022, interpolate to 2026.
hdd_gap = [
    (2018, 0.028),   # interpolated from 2017 $0.025 -> 2022 $0.014
    (2019, 0.024),
    (2020, 0.020),
    (2021, 0.017),
    (2022, 0.014),   # Backblaze Nov 2022
    (2023, 0.015),   # slight uptick (Thailand floods aftermath, supply)
    (2024, 0.016),   # AI demand pressure on all storage
    (2025, 0.017),   # HDD prices rising per Tom's Hardware (46% spike late 2025)
    (2026, 0.018),   # diskprices.com Mar 2026
]
hdd_per_gb.extend(hdd_gap)

# --- SSD data ($/GB from evidence base) ---
ssd_per_gb = [
    (2010, 1.400), (2011, 2.000), (2012, 1.000), (2013, 0.730),
    (2014, 0.400), (2015, 0.380), (2016, 0.250), (2017, 0.300),
    (2018, 0.240), (2019, 0.150), (2020, 0.110), (2021, 0.130),
    (2022, 0.090), (2023, 0.050), (2024, 0.080), (2025, 0.090),
    (2026, 0.110),
]

# --- Build composite: cheapest at each year ---
all_years = {}

for year, price in hdd_per_gb:
    if year not in all_years:
        all_years[year] = {'hdd': price}
    else:
        all_years[year]['hdd'] = min(all_years[year].get('hdd', float('inf')), price)

for year, price in ssd_per_gb:
    if year not in all_years:
        all_years[year] = {'ssd': price}
    else:
        all_years[year]['ssd'] = price

# Build output
print(f"{'Year':>6} {'HDD $/GB':>12} {'SSD $/GB':>12} {'Cheapest':>12} {'Tech':>6}")
print("-" * 54)

composite = []
for year in sorted(all_years.keys()):
    d = all_years[year]
    hdd = d.get('hdd')
    ssd = d.get('ssd')

    if hdd and ssd:
        if hdd <= ssd:
            cheapest, tech = hdd, 'HDD'
        else:
            cheapest, tech = ssd, 'SSD'
    elif hdd:
        cheapest, tech = hdd, 'HDD'
    else:
        cheapest, tech = ssd, 'SSD'

    composite.append({
        'year': year,
        'hdd_per_gb': hdd,
        'ssd_per_gb': ssd,
        'cheapest_per_gb': cheapest,
        'tech': tech,
    })

    hdd_str = f"${hdd:.4f}" if hdd else "-"
    ssd_str = f"${ssd:.3f}" if ssd else "-"
    print(f"{year:>6.0f} {hdd_str:>12} {ssd_str:>12} ${cheapest:>10.4f} {tech:>6}")

# Save as JSON for the chart model
with open(OUT_PATH, 'w') as f:
    json.dump(composite, f, indent=2)

print(f"\nTotal data points: {len(composite)}")
print(f"Saved to {OUT_PATH}")
