"""
Chain Growth Ceiling Model

Answers: what is the maximum chain growth rate (GB/year) that keeps a $300
node viable for 8-10 years?

Works backwards from hardware constraints:
1. For each bottleneck (disk, IBD time), solve for max growth rate
2. The ceiling = the lowest (binding constraint)
3. Check UTXO set growth as an independent time-bomb (not growth-rate dependent)
4. Then compare BIP block size options against the ceiling

Target hardware (from Q036): $300 N100 mini-PC, 2TB SSD, 16GB RAM
Target upgrade cycle (from Q038): 8-10 years
"""

# ── Baseline (2025) ──────────────────────────────────────────────────

# Baselines and scenarios live in models/scenarios.py so every model in this
# paper uses the same numbers. Do not redefine them here.

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scenarios as sc

CHAIN_SIZE_GB_2026 = sc.CHAIN_GB_2026
CHAINSTATE_GB_2025 = sc.CHAINSTATE_GB_2025
UTXO_SET_ENTRIES_2025 = sc.UTXO_SET_ENTRIES_2025
BYTES_PER_UTXO_ENTRY = sc.BYTES_PER_UTXO_ENTRY

# IBD: N100 mini-PC with NVMe SSD, Bitcoin Core defaults
IBD_RATE_GB_PER_HOUR_2025 = sc.IBD_RATE_GB_PER_HR

REALISTIC_WORST_MB = sc.SCENARIOS["realistic_worst"]["avg_block_mb"]
THEORETICAL_MAX_MB = sc.SCENARIOS["theoretical_max"]["avg_block_mb"]

# ── Target hardware ($300, static purchase) ──────────────────────────

# ── Usable disk capacity ─────────────────────────────────────────────
# A "2TB SSD" = 2,000 GB (marketed in decimal GB, no GiB conversion needed).
#
# Deductions:
#   ext4 reserved blocks (5%):  -100 GB  (default root reservation; tune2fs -m)
#   OS + swap + logs:            -50 GB  (Ubuntu/Debian minimal + 4 GB swap + journals)
#   Core low-disk shutdown:       ~0 GB  (50 MB floor, checked every 5 min in init.cpp;
#                                         too small to model)
#
# Total usable for Bitcoin data: 1,850 GB
SSD_GB = sc.SSD_GB

# Nominal capacity with the ext4 root reservation reclaimed (tune2fs -m 0).
SSD_GB_NO_FS_RESERVE = sc.SSD_GB + 100

RAM_GB = sc.RAM_GB
MAX_IBD_DAYS = sc.MAX_IBD_DAYS    # beyond this, new operators give up

# ── Upgrade cycle targets ────────────────────────────────────────────

CYCLE_YEARS = [7, 8, 10]

# ── Hardware improvement rates (annual, compounding) ─────────────────
# Used ONLY for IBD processing speed — the SSD and RAM are fixed at purchase.
# For a static purchase, the hardware doesn't get faster. But Bitcoin Core
# validation software improves (~5-8%/yr historically — assumecheck,
# signature batch validation, UTXO cache improvements, etc.).
#
# We model two cases:
#   - Static: no IBD speed improvement (pure hardware question)
#   - Software-adjusted: ~5% annual IBD speed improvement from Core optimisation

IBD_SOFTWARE_IMPROVEMENT_PCT = 5  # annual % improvement in validation speed

# ── UTXO set growth ─────────────────────────────────────────────────
# The UTXO set lives on-disk in LevelDB. Bitcoin Core's dbcache (default
# 450 MB) is primarily a WRITE BUFFER — it batches dirty UTXO entries and
# flushes to LevelDB periodically. It is NOT a read cache in the
# traditional sense.
#
# The hidden performance variable is the OS PAGE CACHE. On a 16 GB system
# with dbcache=4000 (~4 GB): ~6 GB to bitcoind, ~10 GB free for the OS to
# transparently cache LevelDB files. At 11 GB chainstate, most of it fits
# in OS cache. Going ABOVE ~4 GB dbcache actually hurts reads by stealing
# RAM from the OS page cache — explaining the steep diminishing returns in
# Lopp's benchmarks (Core v27.1, NVMe):
#
#   dbcache   IBD time   vs default
#   450 MB    10.0 hr    baseline
#   4 GB       8.9 hr    10% faster
#   28 GB      7.5 hr    24% faster
#
# IBD degradation from UTXO set growth (11 GB → 15 GB over 10 years):
# Analysed at ~5-15% slowdown on new blocks due to OS page cache no
# longer covering the full chainstate. On NVMe (~20-40μs random reads),
# this is a gradual degradation, not a cliff. At worst case (15%),
# the IBD ceiling would drop from ~129 to ~110 GB/yr for static hardware
# — near the disk ceiling (~111 GB/yr). With software improvement
# (+5%/yr), IBD stays at 230+ GB/yr regardless.
# Conclusion: UTXO degradation doesn't materially change the ceiling
# or which options pass/fail. Not modelled explicitly — disk remains
# the practical binding constraint.
#
# UTXO set growth affects:
#   1. Disk usage (adds to total SSD consumption, but trivial vs chain growth)
#   2. IBD speed (bounded ~5-15% degradation, absorbed by NVMe)
#
# Growth is LINEAR (entries/year), not compound percentage.
# The inscription-era spike (86M → 169M in 2023) is widely acknowledged
# as a problem with broad consensus to address (BRC-20 → Runes migration,
# dust cleanup proposals like "The Cat" and "Lynx", BIP anti-spam measures).
#
# Historical data:
#   2020-2022 (pre-inscription organic): ~7M entries/yr, ~0.4 GB/yr
#   2023 (inscription mania): ~74M entries/yr — 10x organic, anomalous
#   2025: net SHRINKAGE (-21.7M entries, from 187.5M peak to 165.8M)
#
# Three scenarios for post-inscription organic growth:

UTXO_SCENARIOS = {
    "optimistic": {
        "label": "Optimistic (dust solved, consolidation wins)",
        "entries_per_year": 5_000_000,
        "note": "Cleanup mechanisms deployed, inscription dust spent/expired. "
                "Organic monetary growth only.",
    },
    "realistic": {
        "label": "Realistic (organic monetary, no spam)",
        "entries_per_year": 8_000_000,
        "note": "Pre-inscription baseline (~7M/yr 2020-2022) with moderate "
                "adoption growth. Inscription spike addressed.",
    },
    "pessimistic": {
        "label": "Pessimistic (moderate inscription activity persists)",
        "entries_per_year": 20_000_000,
        "note": "Some data-storage demand survives at higher prices. "
                "Unlikely at current levels but models residual spam.",
    },
}


# ── Bottleneck 1: Disk ───────────────────────────────────────────────

def max_growth_rate_disk(cycle_years: int, utxo_entries_per_year: int = 8_000_000) -> float:
    """
    Max chain growth GB/year before 2TB SSD fills.

    Total disk = chain data + chainstate (UTXO set on disk).
    Chainstate growth is small but real — subtract it from available space.
    """
    # Chainstate growth over the cycle
    new_entries = utxo_entries_per_year * cycle_years
    chainstate_growth_gb = (new_entries * BYTES_PER_UTXO_ENTRY) / (1024 ** 3)
    chainstate_at_end = CHAINSTATE_GB_2025 + chainstate_growth_gb

    # Available for chain data = SSD - current chain - current chainstate - chainstate growth
    available_gb = SSD_GB - CHAIN_SIZE_GB_2026 - CHAINSTATE_GB_2025 - chainstate_growth_gb

    if available_gb <= 0:
        return 0.0

    return available_gb / cycle_years


def max_growth_rate_disk_no_fs_reserve(
    cycle_years: int, utxo_entries_per_year: int = 8_000_000
) -> float:
    """Disk ceiling if the ext4 root reservation is reclaimed (tune2fs -m 0)."""
    new_entries = utxo_entries_per_year * cycle_years
    chainstate_growth_gb = (new_entries * BYTES_PER_UTXO_ENTRY) / (1024 ** 3)
    available_gb = (SSD_GB_NO_FS_RESERVE - CHAIN_SIZE_GB_2026
                    - CHAINSTATE_GB_2025 - chainstate_growth_gb)
    return max(0.0, available_gb) / cycle_years


# ── Bottleneck 2: IBD time ───────────────────────────────────────────

def max_growth_rate_ibd(cycle_years: int, software_improvement: bool = False) -> float:
    """
    Max chain growth GB/year before IBD exceeds 7 days at end of cycle.

    IBD time = total_chain_size / processing_rate.
    Processing rate is fixed (static hardware) unless software_improvement=True.

    Solve for max growth_rate such that:
        (693 + growth_rate * cycle_years) / effective_rate <= 7 * 24
    """
    max_ibd_hours = MAX_IBD_DAYS * 24

    if software_improvement:
        effective_rate = IBD_RATE_GB_PER_HOUR_2025 * (
            (1 + IBD_SOFTWARE_IMPROVEMENT_PCT / 100) ** cycle_years
        )
    else:
        effective_rate = IBD_RATE_GB_PER_HOUR_2025

    max_chain_size = effective_rate * max_ibd_hours
    available_growth = max_chain_size - CHAIN_SIZE_GB_2026

    if available_growth <= 0:
        return 0.0

    return available_growth / cycle_years


# ── UTXO set projection ─────────────────────────────────────────────

def utxo_projection(entries_per_year: int, years: int) -> dict:
    """Project UTXO set size after N years of linear growth."""
    new_entries = entries_per_year * years
    total_entries = UTXO_SET_ENTRIES_2025 + new_entries
    chainstate_gb = (total_entries * BYTES_PER_UTXO_ENTRY) / (1024 ** 3)
    return {
        "total_entries": total_entries,
        "chainstate_gb": chainstate_gb,
        "growth_gb": chainstate_gb - CHAINSTATE_GB_2025,
    }


# ── Ceiling computation ──────────────────────────────────────────────

def compute_ceiling(
    cycle_years: int,
    utxo_scenario: str,
    software_improvement: bool = False,
) -> dict:
    """
    Compute the chain growth ceiling for given parameters.

    Returns the binding constraint and ceiling value.
    """
    entries_per_year = UTXO_SCENARIOS[utxo_scenario]["entries_per_year"]

    disk_max = max_growth_rate_disk(cycle_years, entries_per_year)
    ibd_max = max_growth_rate_ibd(cycle_years, software_improvement)
    utxo = utxo_projection(entries_per_year, cycle_years)

    ceiling_gb_yr = min(disk_max, ibd_max)
    binding = "disk" if disk_max < ibd_max else "IBD"

    return {
        "cycle_years": cycle_years,
        "utxo_scenario": utxo_scenario,
        "software_improvement": software_improvement,
        "disk_max_gb_yr": disk_max,
        "ibd_max_gb_yr": ibd_max,
        "ceiling_gb_yr": ceiling_gb_yr,
        "binding_constraint": binding,
        "utxo_entries_at_end": utxo["total_entries"],
        "chainstate_at_end_gb": utxo["chainstate_gb"],
        "chainstate_growth_gb": utxo["growth_gb"],
    }


# ── BIP option growth rates ─────────────────────────────────────────
# Derived from transaction mix analysis (hf-avoidance-options-analysis.md).
#
# Each option has a range: monetary-only (floor) to worst-case (ceiling).
# "Monetary-only" = no inscription/data-stuffing demand, just payments.
# "Worst-case" = blocks full of maximum-bloat transactions under that regime.

BIP_OPTIONS = {
    "Current 4MW": {
        "monetary_only_gb_yr": round(sc.RATE_MONETARY),
        "current_trajectory_gb_yr": round(sc.RATE_CURRENT),
        "worst_case_gb_yr": round(sc.RATE_REALISTIC_WORST),
        "note": f"Current rules. Realistic worst case: inscription-saturated "
                f"blocks (~{REALISTIC_WORST_MB:.2f} MB avg).",
    },
    "Option B/C/D (~1MB)": {
        "monetary_only_gb_yr": 55,
        "current_trajectory_gb_yr": 55,
        "worst_case_gb_yr": 100,
        "note": "Witness discount removed for excess data. ~1MB cap on arbitrary data.",
    },
    "Option A (599KB)": {
        "monetary_only_gb_yr": 31,
        "current_trajectory_gb_yr": 31,
        "worst_case_gb_yr": 63,
        "note": "Hard 599KB paid-byte limit. Monetary throughput reduced ~33%.",
    },
}


# ── Block size ↔ growth rate ────────────────────────────────────────

BLOCKS_PER_YEAR = sc.BLOCKS_PER_YEAR
GB_PER_YEAR_PER_MB_BLOCK = sc.GB_PER_YEAR_PER_MB_BLOCK  # 52.56 GB/yr per 1 MB block

# Observed data points (mempool.space block size report, Glassnode, Dune):
OBSERVED_AVG_BLOCK_MB_PRE_INSCRIPTION = 1.11   # pre-block 770,000 (before Jan 2023)
OBSERVED_AVG_BLOCK_MB_CURRENT = sc.SCENARIOS["current"]["avg_block_mb"]
OBSERVED_AVG_BLOCK_MB_PEAK = sc.SCENARIOS["peak"]["avg_block_mb"]


# ── Escalation scenarios ───────────────────────────────────────────
# The constant-rate analysis (§5) uses worst-case from day 1. But the
# real question is: how much does data demand need to grow from TODAY
# before the ceiling becomes a problem?
#
# Blocks have been essentially full (99.6% at 3.8-4.0 MWU) since
# January 2023. The question is not WHETHER blocks fill but WHAT
# fills them — and how that shifts average block size.
#
# Two approaches:
#   1. Block size sensitivity: what avg block size breaches the ceiling?
#   2. Ramp model: linear ramp from current rate to target, then sustained.

def _ramp(name, avg_mb, ramp_years, note):
    """Build a ramp scenario so its label can never disagree with its rate."""
    return {
        "label": f"{name} ({avg_mb:.2f} MB avg)",
        "start_gb_yr": sc.RATE_CURRENT,
        "end_gb_yr": sc.mb_to_gb_per_year(avg_mb),
        "ramp_years": ramp_years,
        "note": note,
    }


_MODERATE_MB = OBSERVED_AVG_BLOCK_MB_PEAK * 1.10

RAMP_SCENARIOS = {
    "observed_peak": _ramp(
        "Return to observed peak", OBSERVED_AVG_BLOCK_MB_PEAK, 3,
        "March 2024 monthly average, sustained. Already happened once."),
    "moderate": _ramp(
        "Moderate growth", _MODERATE_MB, 5,
        "10% above observed peak. New data protocols + OP_RETURN growth."),
    "aggressive": _ramp(
        "Realistic worst", REALISTIC_WORST_MB, 3,
        "Inscription-saturated blocks at the observed 10% image mix."),
}


def escalation_total_growth(
    start_gb_yr: float,
    end_gb_yr: float,
    ramp_years: int,
    cycle_years: int,
) -> float:
    """
    Total chain growth (GB) under a linear ramp + plateau.

    Ramps linearly from start_gb_yr to end_gb_yr over ramp_years,
    then holds at end_gb_yr for the remaining cycle.
    """
    ramp = min(ramp_years, cycle_years)
    plateau = max(0, cycle_years - ramp)
    ramp_total = ramp * (start_gb_yr + end_gb_yr) / 2
    plateau_total = plateau * end_gb_yr
    return ramp_total + plateau_total


def print_escalation_analysis():
    """Show how close we already are to the ceiling."""

    ceiling_10yr = max_growth_rate_disk(10)
    ceiling_block_mb = ceiling_10yr / GB_PER_YEAR_PER_MB_BLOCK
    chainstate_buffer = 16  # GB, conservative chainstate at year 10
    available_10yr = SSD_GB - CHAIN_SIZE_GB_2026 - chainstate_buffer

    print("=" * 80)
    print("ESCALATION ANALYSIS — THE GAP IS NARROW")
    print("=" * 80)

    print(f"""
  Blocks per year:            {BLOCKS_PER_YEAR:,}
  Conversion:                 1 MB avg block ≈ {GB_PER_YEAR_PER_MB_BLOCK:.1f} GB/yr

  Ceiling (10yr, disk):       {ceiling_10yr:.0f} GB/yr
  Ceiling breach at avg block: {ceiling_block_mb:.2f} MB
  Observed peak (Mar 2024):   {OBSERVED_AVG_BLOCK_MB_PEAK} MB → {OBSERVED_AVG_BLOCK_MB_PEAK * GB_PER_YEAR_PER_MB_BLOCK:.0f} GB/yr

  Headroom from today:        {(ceiling_block_mb / OBSERVED_AVG_BLOCK_MB_CURRENT - 1) * 100:.0f}% above the current {OBSERVED_AVG_BLOCK_MB_CURRENT} MB average
  Headroom from peak:         {(ceiling_block_mb / OBSERVED_AVG_BLOCK_MB_PEAK - 1) * 100:.0f}% (negative = March 2024 already breached it)
""")

    # ── Block size sensitivity ──
    print("  BLOCK SIZE → GROWTH RATE → CEILING CHECK (10-year cycle)")
    print()
    print(f"  {'Avg block':>10}  {'GB/yr':>8}  {'10yr total':>10}  "
          f"{'Chain yr 10':>12}  {'Margin':>8}  {'Status'}")
    print(f"  {'─' * 10}  {'─' * 8}  {'─' * 10}  "
          f"{'─' * 12}  {'─' * 8}  {'─' * 25}")

    block_sizes = [
        (OBSERVED_AVG_BLOCK_MB_PRE_INSCRIPTION, "Pre-inscription"),
        (OBSERVED_AVG_BLOCK_MB_CURRENT, "Current trajectory"),
        (2.00, None),
        (OBSERVED_AVG_BLOCK_MB_PEAK, "Observed peak (Mar 2024)"),
        (ceiling_block_mb, "CEILING BREACH"),
        (2.75, None),
        (3.00, None),
        (REALISTIC_WORST_MB, "Realistic worst case"),
        (THEORETICAL_MAX_MB, "Theoretical max (bound)"),
    ]
    block_sizes.sort(key=lambda r: r[0])

    for mb, label in block_sizes:
        rate = mb * GB_PER_YEAR_PER_MB_BLOCK
        total = rate * 10
        chain = CHAIN_SIZE_GB_2026 + total
        margin = available_10yr - total

        if rate <= ceiling_10yr:
            status = label or "Below ceiling"
        else:
            status = label or "EXCEEDS CEILING"

        flag = "  !" if margin < 0 else ""
        print(f"  {mb:>8.2f} MB  {rate:>7.0f}  {total:>8.0f} GB  "
              f"{chain:>10.0f} GB  {margin:>6.0f} GB{flag}  {status}")

    print("  (! = exceeds available disk)")
    print()

    # ── Ramp scenarios ──
    print("  RAMP SCENARIOS (linear ramp from current → target, then sustained)")
    print()
    print(f"  {'Scenario':<42}  {'Ramp':>6}  {'Rate yr10':>10}  "
          f"{'Total 10yr':>10}  {'Chain yr10':>11}  {'Margin':>8}")
    print(f"  {'─' * 42}  {'─' * 6}  {'─' * 10}  "
          f"{'─' * 10}  {'─' * 11}  {'─' * 8}")

    # Baseline: current sustained
    baseline_total = sc.RATE_CURRENT * 10
    baseline_chain = CHAIN_SIZE_GB_2026 + baseline_total
    baseline_margin = available_10yr - baseline_total
    _base_mb = sc.RATE_CURRENT / GB_PER_YEAR_PER_MB_BLOCK
    _base_lbl = f"Current sustained ({_base_mb:.2f} MB avg)"
    _base_rate = f"{sc.RATE_CURRENT:.0f} GB/yr"
    print(f"  {_base_lbl:<42}  {'—':>6}  {_base_rate:>10}  "
          f"{baseline_total:>8.0f} GB  {baseline_chain:>9.0f} GB  {baseline_margin:>6.0f} GB")

    for name, s in RAMP_SCENARIOS.items():
        total = escalation_total_growth(
            s["start_gb_yr"], s["end_gb_yr"], s["ramp_years"], 10
        )
        chain = CHAIN_SIZE_GB_2026 + total
        margin = available_10yr - total
        ramp_str = f"{s['ramp_years']}yr"
        rate_str = f"{s['end_gb_yr']:.0f} GB/yr"
        flag = " !" if margin < 0 else ""

        print(f"  {s['label']:<42}  {ramp_str:>6}  {rate_str:>10}  "
              f"{total:>8.0f} GB  {chain:>9.0f} GB  {margin:>6.0f} GB{flag}")

    print(f"  (! = exceeds available disk, available = {available_10yr:.0f} GB)")
    print()

    # ── The punchline ──
    pct_increase = (OBSERVED_AVG_BLOCK_MB_PEAK / OBSERVED_AVG_BLOCK_MB_PRE_INSCRIPTION - 1) * 100
    print(f"""  KEY FINDING:
  Average block size went from {OBSERVED_AVG_BLOCK_MB_PRE_INSCRIPTION} MB to {OBSERVED_AVG_BLOCK_MB_CURRENT} MB in 2 years (+{pct_increase:.0f}%).
  The ceiling breaches at {ceiling_block_mb:.2f} MB — only {(ceiling_block_mb - OBSERVED_AVG_BLOCK_MB_PEAK) / OBSERVED_AVG_BLOCK_MB_PEAK * 100:.0f}% above the peak already observed.
  Under current rules, nothing prevents sustained operation at or above this level.
""")


# ── Main output ──────────────────────────────────────────────────────

def print_bottleneck_analysis():
    """Print the independent bottleneck analysis."""

    print("=" * 80)
    print("CHAIN GROWTH CEILING — TWO-BOTTLENECK ANALYSIS")
    print("=" * 80)
    print(f"""
Target hardware:  $300 N100 mini-PC, {SSD_GB/1000:.0f}TB SSD, {RAM_GB}GB RAM
Baseline (2025):  {CHAIN_SIZE_GB_2026:.0f} GB chain, {CHAINSTATE_GB_2025:.0f} GB chainstate
IBD rate (2025):  {IBD_RATE_GB_PER_HOUR_2025:.0f} GB/hr ({CHAIN_SIZE_GB_2026/IBD_RATE_GB_PER_HOUR_2025/24:.1f} days for current chain)
""")

    # ── Bottleneck 1: Disk ──
    print("─" * 80)
    print("BOTTLENECK 1: DISK (2TB SSD)")
    print("─" * 80)
    available = SSD_GB - CHAIN_SIZE_GB_2026 - CHAINSTATE_GB_2025
    print(f"  Total used: {CHAIN_SIZE_GB_2026:.0f} GB chain + {CHAINSTATE_GB_2025:.0f} GB chainstate "
          f"= {CHAIN_SIZE_GB_2026 + CHAINSTATE_GB_2025:.0f} GB")
    print(f"  Available:  {available:.0f} GB (before chainstate growth)\n")

    for cy in CYCLE_YEARS:
        print(f"  {cy}-year cycle:")
        for name, scenario in UTXO_SCENARIOS.items():
            rate = max_growth_rate_disk(cy, scenario["entries_per_year"])
            utxo = utxo_projection(scenario["entries_per_year"], cy)
            print(f"    {scenario['label'][:50]:<50}  "
                  f"chainstate +{utxo['growth_gb']:.1f} GB → "
                  f"max chain growth {rate:.1f} GB/yr")
        print()

    # ── UTXO set context ──
    print("─" * 80)
    print("UTXO SET CONTEXT")
    print("─" * 80)
    print(f"""
  The UTXO set lives on-disk in LevelDB. dbcache (default 450 MB) is
  primarily a write buffer, not a read cache. The OS page cache is the
  real read accelerator — on 16 GB RAM with dbcache=4000, ~10 GB free
  for OS to transparently cache LevelDB files.

  UTXO growth from {CHAINSTATE_GB_2025:.0f} GB to ~15 GB (yr 10) causes ~5-15% IBD
  degradation as the OS page cache can no longer cover the full chainstate.
  Analysed but not modelled — doesn't change binding constraint (disk).

  Current: {UTXO_SET_ENTRIES_2025/1e6:.0f}M entries, {CHAINSTATE_GB_2025:.0f} GB on disk

  Historical growth:
    2020-2022 (organic):     ~7M entries/yr  (~0.4 GB/yr)
    2023 (inscription era):  ~74M entries/yr (~4.4 GB/yr) — anomalous, 10x organic
    2025:                    net shrinkage (-21.7M entries from Jan peak)
""")

    for name, scenario in UTXO_SCENARIOS.items():
        print(f"  {scenario['label']}:")
        print(f"    {scenario['entries_per_year']/1e6:.0f}M entries/yr "
              f"(~{scenario['entries_per_year'] * BYTES_PER_UTXO_ENTRY / (1024**3):.2f} GB/yr)")
        for cy in CYCLE_YEARS:
            p = utxo_projection(scenario["entries_per_year"], cy)
            print(f"    At year {cy}: {p['total_entries']/1e6:.0f}M entries, "
                  f"{p['chainstate_gb']:.1f} GB on disk")
        print(f"    {scenario['note']}")
        print()

    # ── Bottleneck 2: IBD ──
    print("─" * 80)
    print("BOTTLENECK 2: IBD TIME (7-day max)")
    print("─" * 80)

    for cy in CYCLE_YEARS:
        rate_static = max_growth_rate_ibd(cy, software_improvement=False)
        rate_sw = max_growth_rate_ibd(cy, software_improvement=True)
        chain_at_static = CHAIN_SIZE_GB_2026 + rate_static * cy
        chain_at_sw = CHAIN_SIZE_GB_2026 + rate_sw * cy
        print(f"  {cy}-year cycle:")
        print(f"    Static hardware:      max {rate_static:.1f} GB/yr "
              f"(chain reaches {chain_at_static:.0f} GB, IBD = {MAX_IBD_DAYS}d)")
        print(f"    +{IBD_SOFTWARE_IMPROVEMENT_PCT}%/yr SW optimisation: max {rate_sw:.1f} GB/yr "
              f"(chain reaches {chain_at_sw:.0f} GB, IBD = {MAX_IBD_DAYS}d)")
    print()

    # ── IBD at specific growth rates ──
    print("  IBD time at specific growth rates (static hardware):")
    print(f"  {'Growth rate':<15}  {'Chain at yr 8':>14}  {'IBD at yr 8':>12}  "
          f"{'Chain at yr 10':>15}  {'IBD at yr 10':>13}")
    print("  " + "─" * 75)
    for growth in [31, 55, 80, 100, 130, round(sc.RATE_REALISTIC_WORST)]:
        for cy in CYCLE_YEARS:
            chain = CHAIN_SIZE_GB_2026 + growth * cy
            ibd_days = chain / IBD_RATE_GB_PER_HOUR_2025 / 24
        chain_8 = CHAIN_SIZE_GB_2026 + growth * 8
        chain_10 = CHAIN_SIZE_GB_2026 + growth * 10
        ibd_8 = chain_8 / IBD_RATE_GB_PER_HOUR_2025 / 24
        ibd_10 = chain_10 / IBD_RATE_GB_PER_HOUR_2025 / 24
        flag_8 = " !" if ibd_8 > MAX_IBD_DAYS else ""
        flag_10 = " !" if ibd_10 > MAX_IBD_DAYS else ""
        print(f"  {growth:>3} GB/yr        {chain_8:>12.0f} GB  {ibd_8:>10.1f}d{flag_8:<2} "
              f"{chain_10:>13.0f} GB  {ibd_10:>10.1f}d{flag_10}")
    print("  (! = exceeds 7-day threshold)")
    print()


def print_ceiling_table():
    """Print the ceiling for all parameter combinations."""

    print("=" * 80)
    print("CEILING RESULTS")
    print("=" * 80)
    print()
    print(f"{'Cycle':>6}  {'UTXO scenario':<50}  {'Disk':>8}  {'IBD':>8}  "
          f"{'Ceiling':>8}  {'Binding'}")
    print(f"{'(yr)':>6}  {'':<50}  {'GB/yr':>8}  {'GB/yr':>8}  "
          f"{'GB/yr':>8}  {''}")
    print("─" * 110)

    ceilings = []

    # Primary table: software improvement ON (realistic)
    for cy in CYCLE_YEARS:
        for utxo_name in UTXO_SCENARIOS:
            r = compute_ceiling(cy, utxo_name, software_improvement=True)
            ceilings.append(r)

            print(f"{cy:>6}  {UTXO_SCENARIOS[utxo_name]['label']:<50}  "
                  f"{r['disk_max_gb_yr']:>7.1f}  {r['ibd_max_gb_yr']:>7.1f}  "
                  f"{r['ceiling_gb_yr']:>7.1f}  {r['binding_constraint']}")
        print()

    # Secondary: static hardware (conservative)
    print("(Conservative — static hardware, no software improvement:)")
    print("─" * 110)
    for cy in CYCLE_YEARS:
        for utxo_name in UTXO_SCENARIOS:
            r = compute_ceiling(cy, utxo_name, software_improvement=False)
            print(f"{cy:>6}  {UTXO_SCENARIOS[utxo_name]['label']:<50}  "
                  f"{r['disk_max_gb_yr']:>7.1f}  {r['ibd_max_gb_yr']:>7.1f}  "
                  f"{r['ceiling_gb_yr']:>7.1f}  {r['binding_constraint']}")
        print()

    return ceilings


def print_bip_comparison(ceilings: list[dict]):
    """Compare BIP options against the ceiling."""

    print("=" * 80)
    print("BIP OPTIONS vs. CEILING")
    print("=" * 80)
    print()

    # Reference: most conservative defensible ceiling (10yr, realistic UTXO, static HW)
    ref_conservative = compute_ceiling(10, "realistic", software_improvement=False)
    ref_moderate = compute_ceiling(10, "realistic", software_improvement=True)

    for label, ref in [
        ("Conservative (10yr, static HW)", ref_conservative),
        ("Moderate (10yr, +5%/yr SW)", ref_moderate),
    ]:
        ceiling = ref["ceiling_gb_yr"]
        print(f"  {label}: ceiling = {ceiling:.0f} GB/yr (binding: {ref['binding_constraint']})")
        print()
        print(f"  {'Option':<25}  {'Monetary':>10}  {'Current':>10}  {'Worst':>10}  "
              f"{'Status'}")
        print(f"  {'':<25}  {'GB/yr':>10}  {'GB/yr':>10}  {'GB/yr':>10}")
        print("  " + "─" * 80)

        for name, opt in BIP_OPTIONS.items():
            worst = opt["worst_case_gb_yr"]
            curr = opt["current_trajectory_gb_yr"]
            if worst <= ceiling:
                status = "ALL PASS"
            elif curr <= ceiling:
                status = f"current PASS, worst FAIL ({worst} > {ceiling:.0f})"
            else:
                status = f"FAIL (current {curr} > {ceiling:.0f})"

            print(f"  {name:<25}  {opt['monetary_only_gb_yr']:>9.0f}  "
                  f"{curr:>9.0f}  {worst:>9.0f}  {status}")
        print()


def print_key_finding():
    """Print the bottom-line answer."""

    print("=" * 80)
    print("KEY FINDING")
    print("=" * 80)

    conservative = compute_ceiling(10, "realistic", software_improvement=False)
    moderate = compute_ceiling(10, "realistic", software_improvement=True)
    relaxed = compute_ceiling(8, "optimistic", software_improvement=True)

    print(f"""
THE CHAIN GROWTH CEILING
========================

For a $300 node (2TB SSD, 16GB RAM, N100) to last 8-10 years:

  Conservative (10yr, static HW, realistic UTXO): {conservative['ceiling_gb_yr']:.0f} GB/yr  [{conservative['binding_constraint']}]
  Moderate (10yr, +5%/yr SW, realistic UTXO):     {moderate['ceiling_gb_yr']:.0f} GB/yr  [{moderate['binding_constraint']}]
  Relaxed (8yr, +5%/yr SW, optimistic UTXO):      {relaxed['ceiling_gb_yr']:.0f} GB/yr  [{relaxed['binding_constraint']}]

WHAT THIS MEANS
===============

The ceiling is {conservative['ceiling_gb_yr']:.0f}-{relaxed['ceiling_gb_yr']:.0f} GB/year depending on assumptions.
Disk is the binding constraint — IBD is comfortably looser.

  Current 4MW rules:
    Monetary-only ({sc.RATE_MONETARY:.0f} GB/yr):  well below ceiling — SAFE
    Current trajectory ({sc.RATE_CURRENT:.0f} GB/yr): below ceiling — PASSES
    Realistic worst ({sc.RATE_REALISTIC_WORST:.0f} GB/yr): FAILS the 10yr ceiling ({conservative['ceiling_gb_yr']:.0f} GB/yr)
    Theoretical max ({sc.RATE_THEORETICAL_MAX:.0f} GB/yr): FAILS — this is the bound, not a forecast

  Options B/C/D (1MB paid-byte):
    Current trajectory (55 GB/yr): well below ceiling — SAFE
    Worst case (100 GB/yr): PASSES even conservative ceiling

  Option A (599KB):
    ALL scenarios PASS with huge margin (31-63 GB/yr vs {conservative['ceiling_gb_yr']:.0f})
    But pays 33% throughput reduction that the ceiling doesn't require

THE DECISIVE QUESTION
=====================

Current rules PASS at current trajectory. The ceiling doesn't bite today.
But the ceiling analysis reveals something else:

  1. Without the BIP, realistic-worst 4MW ({sc.RATE_REALISTIC_WORST:.0f} GB/yr) FAILS the 10yr ceiling.
     This means the protocol is not ROBUST to abuse — one sustained
     inscription wave can push growth past the ceiling.

  2. Options B/C/D guarantee growth stays below ceiling even at worst case.
     This is the defensive argument: not "current growth is too high"
     but "current rules allow growth that COULD be too high."

  3. Option A is overkill for the ceiling. The additional 33% throughput
     reduction buys margin the ceiling doesn't need.

UTXO SET: ANALYSED, NOT A CEILING-CHANGER
==========================================

The UTXO set lives on disk in LevelDB. Core's dbcache is a write buffer;
the OS page cache is the real read accelerator. At organic growth (~8M/yr):
  Year 10: {conservative['utxo_entries_at_end']/1e6:.0f}M entries, ~{conservative['chainstate_at_end_gb']:.0f} GB on disk
  Disk contribution: ~{conservative['chainstate_growth_gb']:.1f} GB over {conservative['cycle_years']} years — trivial vs chain growth

UTXO growth from 11 to ~15 GB causes ~5-15% IBD degradation as the OS
page cache (on 16 GB RAM) can no longer cover the full chainstate.
At worst case (15%), IBD ceiling drops from ~129 to ~110 GB/yr — near
disk ceiling (~111). With software improvement, irrelevant.
Conclusion: doesn't change which options pass/fail. Not modelled explicitly.
""")


def main():
    print_bottleneck_analysis()
    ceilings = print_ceiling_table()
    print_bip_comparison(ceilings)
    print_escalation_analysis()
    print_key_finding()


if __name__ == "__main__":
    main()
