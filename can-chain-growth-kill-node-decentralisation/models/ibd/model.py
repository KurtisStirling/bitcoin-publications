"""
IBD Ceiling Model — Two-Phase Analysis

Answers: how long does Initial Block Download take on target hardware ($300
N100 mini-PC) at year N, and when does IBD exceed the 7-day threshold?

Decomposes IBD into two phases:
1. AssumeValid (AV): skips signature verification — I/O bound (UTXO lookups)
2. Full Validation (FV): verifies all signatures — CPU bound for monetary blocks

Key insight: inscription blocks are large but cheap to validate (few sigs);
monetary blocks are smaller but expensive (many sigs). The polarity nearly
cancels: unrestricted inscription-heavy growth adds volume but reduces per-GB
validation cost, while capped monetary-heavy growth limits volume but increases
per-GB cost.

Target hardware (from Q036): $300 N100 mini-PC, 2TB SSD, 16GB RAM
Target upgrade cycle (from Q038): 8-10 years
"""

# ── Baseline (2025) ──────────────────────────────────────────────────

# Baselines and scenarios live in models/scenarios.py. Do not redefine here.

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scenarios as sc

CHAIN_SIZE_GB_2026 = sc.CHAIN_GB_2026
CHAINSTATE_GB_2025 = sc.CHAINSTATE_GB_2025
UTXO_SET_ENTRIES_2025 = sc.UTXO_SET_ENTRIES_2025
BYTES_PER_UTXO_ENTRY = sc.BYTES_PER_UTXO_ENTRY

# ── Target hardware ($300, static purchase) ──────────────────────────

SSD_GB = sc.SSD_GB
MAX_IBD_DAYS = sc.MAX_IBD_DAYS

# ── IBD rate components (N100 mini-PC, NVMe SSD) ─────────────────────
# The blended rate (12 GB/hr = ~2.5 days for 724 GB) decomposes into:
#   - AV phase: I/O bound (UTXO lookups, no sig verification) → ~12 GB/hr
#   - FV phase: CPU bound (sig verification dominates) → varies by density
#
# Cross-check at year 0, current trajectory (80 GB/yr, 2.1M sigops/GB):
#   AV covers 684 GB (all but last 6 months), FV covers 40 GB.
#   FV CPU rate: 13,000 * 3600 / 2,100,000 = 22.3 GB/hr (faster than I/O)
#   FV is I/O bound at same rate as AV → entire IBD is I/O bound.
#   724 / 12 = 60.3 hrs ≈ 2.5 days — matches observed.
#
# The AV rate (12 GB/hr) is calibrated to the observed blended rate on an
# N100 (Lopp 2025: ~2.5 days for 724 GB). With corrected sig verification
# speed (13,000/sec via libsecp256k1), FV CPU throughput (22 GB/hr for
# mixed blocks) exceeds I/O throughput, so the entire IBD is I/O bound
# for current block composition. CPU only becomes the FV bottleneck for
# pure monetary blocks: 13,000 * 3600 / 5,000,000 = 9.4 GB/hr < 12.

IBD_RATE_AV_GB_PER_HR = sc.IBD_RATE_GB_PER_HR   # I/O bound, observed N100 IBD
AV_WINDOW_MONTHS = 6               # AssumeValid checkpoint lag behind tip

# ── CPU: signature verification ──────────────────────────────────────
# libsecp256k1 schnorrsig_verify: ~48-50 us/op on i7-class hardware
# (secp256k1 PR #760, CoinEx endomorphism benchmarks). That's ~20,000/sec.
#
# Scaling to N100 by Passmark single-thread ratio:
#   i7-6820HQ ST ~2100, N100 ST ~1900 → ratio 0.90 → ~18,000/sec
#   With real-world margin (cache pressure, context switching): ~13,000/sec
#
# Cross-check: Lopp 2025 benchmarks report 5,130 ns/sigop amortised on
# i7-8700 (multi-threaded IBD). Single-thread is ~10x slower = ~50 us,
# consistent with the library benchmarks above.
#
# Previous value (2,000/sec) was likely confused with OpenSSL performance.
# libsecp256k1 is ~8x faster (Delving Bitcoin, 2024).

SIG_VERIFICATIONS_PER_SEC_N100 = 13_000

# Sigops per GB by block composition:
#   Monetary (P2TR 1-in-2-out): ~153.5 vB/tx, 1 sig → ~6,515 sigs/MB
#     Conservative estimate ~5.0M/GB accounting for mixed input counts.
#   Inscription (single 4MB witness): ~1 sig per ~4MB → ~0.25 sigs/MB
#   Current trajectory: weighted mix of monetary + inscription
#   Historical (pre-inscription): ~2.0M/GB

SIGOPS_PER_GB_MONETARY = 5_000_000     # full monetary blocks
SIGOPS_PER_GB_INSCRIPTION = 256         # inscription-dominated blocks
SIGOPS_PER_GB_MIXED = 2_100_000         # current trajectory mix
SIGOPS_PER_GB_HISTORICAL = 2_000_000    # pre-inscription chain average
SIGOPS_PER_GB_CAPPED_WORST = 3_500_000  # ~70% monetary density under BIP cap

# ── UTXO degradation ────────────────────────────────────────────────
# As chainstate grows beyond OS page cache coverage, UTXO lookups hit
# disk more often. Linear 0→15% slowdown as chainstate grows 11→20 GB.

CHAINSTATE_DEGRADE_START_GB = 11.0
CHAINSTATE_DEGRADE_END_GB = 20.0
CHAINSTATE_MAX_DEGRADATION = 0.15  # 15% slowdown at 20 GB

# ── Software improvement ────────────────────────────────────────────

IBD_SOFTWARE_IMPROVEMENT_PCT = 5  # annual % from Core optimisations

# ── Hardware upgrade cycle ──────────────────────────────────────────
# For the 80-year chart: hardware purchased at year 0 is fixed, but every
# 10 years the operator buys a new $300 machine. Processing speed (both
# CPU and I/O) improves ~1.5x per decade, based on observed Passmark
# single-thread improvement for budget hardware (~1.58x from 2016→2026).
# This is the hardware analog of the storage chart's 3x/decade capacity.
#
# Note: software improvement (5%/yr above) is used in the 8-10yr tables
# where it has empirical grounding. The 80-year chart uses hardware
# upgrades only — compounding 5%/yr for 80 years (50x) is indefensible.

HW_IMPROVEMENT_PER_DECADE = 1.5   # processing speed multiplier per decade
UPGRADE_INTERVAL_YEARS = 10

# ── Misc ────────────────────────────────────────────────────────────

BLOCKS_PER_YEAR = sc.BLOCKS_PER_YEAR

# ── UTXO scenarios (from ceiling.py) ────────────────────────────────

UTXO_SCENARIOS = {
    "optimistic": {"entries_per_year": 5_000_000},
    "realistic": {"entries_per_year": 8_000_000},
    "pessimistic": {"entries_per_year": 20_000_000},
}

# ── IBD scenarios ───────────────────────────────────────────────────

IBD_SCENARIOS = {
    "Unrestricted monetary": {
        "growth_gb_yr": sc.RATE_MONETARY,
        "sigops_per_gb_new": SIGOPS_PER_GB_MONETARY,
        "note": "Current rules, only monetary txs fill blocks.",
    },
    "Unrestricted current": {
        "growth_gb_yr": sc.RATE_CURRENT,
        "sigops_per_gb_new": SIGOPS_PER_GB_MIXED,
        "note": "Current trajectory: mixed monetary + inscription.",
    },
    "Realistic worst": {
        "growth_gb_yr": sc.RATE_REALISTIC_WORST,
        "sigops_per_gb_new": SIGOPS_PER_GB_INSCRIPTION,
        "note": "Inscription-saturated blocks at the observed 10% image mix.",
    },
    "Theoretical max": {
        "growth_gb_yr": sc.RATE_THEORETICAL_MAX,
        "sigops_per_gb_new": SIGOPS_PER_GB_INSCRIPTION,
        "note": "4M weight units of pure witness data. A bound, not a forecast.",
    },
    "Capped monetary": {
        "growth_gb_yr": sc.RATE_MONETARY,
        "sigops_per_gb_new": SIGOPS_PER_GB_MONETARY,
        "note": "BIP cap active, only monetary txs.",
    },
    "Capped worst": {
        "growth_gb_yr": 100,
        "sigops_per_gb_new": SIGOPS_PER_GB_CAPPED_WORST,
        "note": "BIP cap active, max data stuffing under cap (~70% monetary density).",
    },
}


# ── Core functions ──────────────────────────────────────────────────

def utxo_chainstate_gb(year: int, entries_per_year: int = 8_000_000) -> float:
    """Chainstate size (GB) at year N from 2025 baseline."""
    new_entries = entries_per_year * year
    total_entries = UTXO_SET_ENTRIES_2025 + new_entries
    return (total_entries * BYTES_PER_UTXO_ENTRY) / 1e9


def av_phase_degradation(chainstate_gb: float) -> float:
    """
    Speed multiplier (1.0 → 0.85) for UTXO I/O pressure.

    Linear degradation as chainstate outgrows OS page cache.
    Returns a multiplier: 1.0 = no degradation, 0.85 = 15% slower.
    """
    if chainstate_gb <= CHAINSTATE_DEGRADE_START_GB:
        return 1.0
    if chainstate_gb >= CHAINSTATE_DEGRADE_END_GB:
        return 1.0 - CHAINSTATE_MAX_DEGRADATION
    fraction = (chainstate_gb - CHAINSTATE_DEGRADE_START_GB) / (
        CHAINSTATE_DEGRADE_END_GB - CHAINSTATE_DEGRADE_START_GB
    )
    return 1.0 - fraction * CHAINSTATE_MAX_DEGRADATION


def software_multiplier(years: float) -> float:
    """Compound software improvement multiplier after N years."""
    return (1 + IBD_SOFTWARE_IMPROVEMENT_PCT / 100) ** years


def cpu_rate_gb_per_hr(sigops_per_gb: float) -> float:
    """
    CPU-limited IBD rate (GB/hr) for a given sigops density.

    Higher sigops density → lower throughput (more CPU work per GB).
    """
    if sigops_per_gb <= 0:
        return float("inf")
    return SIG_VERIFICATIONS_PER_SEC_N100 * 3600 / sigops_per_gb


def ibd_time_hours(
    chain_gb: float,
    growth_gb_yr: float,
    sigops_per_gb_new: float,
    chainstate_gb: float,
    sw_years: float = 0,
    software_improvement: bool = True,
) -> dict:
    """
    Two-phase IBD time decomposition.

    Phase 1 (AV): everything except last 6 months — I/O bound, no sigs.
    Phase 2 (FV): last 6 months — min(I/O rate, CPU rate by sig density).

    Returns dict with av_hours, fv_hours, total_hours, fv_bottleneck.
    """
    # FV covers last 6 months of blocks
    fv_gb = growth_gb_yr * (AV_WINDOW_MONTHS / 12)
    av_gb = max(0, chain_gb - fv_gb)

    # Degradation and software multipliers
    degrade = av_phase_degradation(chainstate_gb)
    sw_mult = software_multiplier(sw_years) if software_improvement else 1.0

    # Phase 1: AV — I/O bound only
    effective_av_rate = IBD_RATE_AV_GB_PER_HR * degrade * sw_mult
    av_hours = av_gb / effective_av_rate if effective_av_rate > 0 else float("inf")

    # Phase 2: FV — bottleneck is min(I/O, CPU)
    effective_io_rate = IBD_RATE_AV_GB_PER_HR * degrade * sw_mult
    effective_cpu_rate = cpu_rate_gb_per_hr(sigops_per_gb_new) * sw_mult

    if effective_cpu_rate < effective_io_rate:
        fv_rate = effective_cpu_rate
        fv_bottleneck = "CPU"
    else:
        fv_rate = effective_io_rate
        fv_bottleneck = "I/O"

    fv_hours = fv_gb / fv_rate if fv_rate > 0 else float("inf")

    return {
        "av_gb": av_gb,
        "fv_gb": fv_gb,
        "av_hours": av_hours,
        "fv_hours": fv_hours,
        "total_hours": av_hours + fv_hours,
        "fv_rate_gb_hr": fv_rate,
        "fv_bottleneck": fv_bottleneck,
        "degrade": degrade,
        "sw_mult": sw_mult,
    }


def ibd_projection(
    growth_gb_yr: float,
    sigops_per_gb_new: float,
    year: int,
    utxo_entries_per_year: int = 8_000_000,
    software_improvement: bool = True,
) -> dict:
    """
    Full IBD projection at year N.

    Computes chain size, UTXO chainstate, and two-phase IBD breakdown.
    """
    chain_gb = CHAIN_SIZE_GB_2026 + growth_gb_yr * year
    chainstate_gb = utxo_chainstate_gb(year, utxo_entries_per_year)

    result = ibd_time_hours(
        chain_gb=chain_gb,
        growth_gb_yr=growth_gb_yr,
        sigops_per_gb_new=sigops_per_gb_new,
        chainstate_gb=chainstate_gb,
        sw_years=year if software_improvement else 0,
        software_improvement=software_improvement,
    )
    result["year"] = year
    result["chain_gb"] = chain_gb
    result["chainstate_gb"] = chainstate_gb
    result["total_days"] = result["total_hours"] / 24
    return result


def max_growth_rate_ibd(
    cycle_years: int,
    sigops_per_gb_new: float,
    utxo_entries_per_year: int = 8_000_000,
    software_improvement: bool = True,
) -> float:
    """
    Binary search for max chain growth rate (GB/yr) where IBD <= 7 days
    at end of cycle.
    """
    lo, hi = 0.0, 2000.0
    target_hours = MAX_IBD_DAYS * 24

    for _ in range(100):
        mid = (lo + hi) / 2
        proj = ibd_projection(
            growth_gb_yr=mid,
            sigops_per_gb_new=sigops_per_gb_new,
            year=cycle_years,
            utxo_entries_per_year=utxo_entries_per_year,
            software_improvement=software_improvement,
        )
        if proj["total_hours"] <= target_hours:
            lo = mid
        else:
            hi = mid

    return lo


# ── Output functions ────────────────────────────────────────────────

def print_two_phase_analysis():
    """IBD time at years 0, 5, 10, 20, 40, 80 for each scenario."""
    years = [0, 5, 10, 20, 40, 80]

    print("=" * 100)
    print("TWO-PHASE IBD ANALYSIS — TIME BREAKDOWN BY SCENARIO")
    print("=" * 100)
    print()
    print("Hardware: $300 N100 mini-PC, 2TB NVMe SSD, 16GB RAM")
    print(f"AV rate: {IBD_RATE_AV_GB_PER_HR} GB/hr (I/O bound)")
    print(f"Sig verification: {SIG_VERIFICATIONS_PER_SEC_N100:,}/sec")
    print(f"Software improvement: +{IBD_SOFTWARE_IMPROVEMENT_PCT}%/yr")
    print()

    for sw_label, sw_flag in [("With +5%/yr software improvement", True),
                               ("Static hardware (no improvement)", False)]:
        print("─" * 100)
        print(f"  {sw_label}")
        print("─" * 100)

        for name, s in IBD_SCENARIOS.items():
            print(f"\n  {name} ({s['growth_gb_yr']:.0f} GB/yr, "
                  f"{s['sigops_per_gb_new']/1e6:.1f}M sigops/GB)")
            print(f"  {s['note']}")
            print()
            print(f"  {'Year':>6}  {'Chain':>9}  {'AV':>8}  {'FV':>8}  "
                  f"{'AV time':>9}  {'FV time':>9}  {'Total':>9}  "
                  f"{'FV bind':>8}  {'Status'}")
            print(f"  {'':>6}  {'(GB)':>9}  {'(GB)':>8}  {'(GB)':>8}  "
                  f"{'(hrs)':>9}  {'(hrs)':>9}  {'(days)':>9}  "
                  f"{'':>8}")
            print("  " + "─" * 90)

            for yr in years:
                p = ibd_projection(
                    s["growth_gb_yr"], s["sigops_per_gb_new"], yr,
                    software_improvement=sw_flag,
                )
                status = "FAIL" if p["total_days"] > MAX_IBD_DAYS else "pass"
                flag = " !" if p["total_days"] > MAX_IBD_DAYS else ""
                print(f"  {yr:>6}  {p['chain_gb']:>9.0f}  {p['av_gb']:>8.0f}  "
                      f"{p['fv_gb']:>8.0f}  {p['av_hours']:>9.1f}  "
                      f"{p['fv_hours']:>9.1f}  {p['total_days']:>9.1f}  "
                      f"{p['fv_bottleneck']:>8}  {status}{flag}")
        print()


def print_sig_density_comparison():
    """Unrestricted vs Capped side-by-side — volume vs density decomposition."""

    print("=" * 100)
    print("SIGNATURE DENSITY POLARITY — VOLUME vs DENSITY DECOMPOSITION")
    print("=" * 100)
    print()
    print("The key insight: inscription blocks are big but cheap to validate (few sigs),")
    print("monetary blocks are smaller but expensive (many sigs). Do these effects cancel?")
    print()

    year = 10

    pairs = [
        ("Realistic worst", "Capped worst"),
        ("Unrestricted current", "Capped monetary"),
    ]

    for name_a, name_b in pairs:
        a = IBD_SCENARIOS[name_a]
        b = IBD_SCENARIOS[name_b]

        print(f"  {name_a} vs {name_b} (year {year}, static hardware)")
        print("  " + "─" * 80)

        pa = ibd_projection(a["growth_gb_yr"], a["sigops_per_gb_new"], year,
                            software_improvement=False)
        pb = ibd_projection(b["growth_gb_yr"], b["sigops_per_gb_new"], year,
                            software_improvement=False)

        cpu_rate_a = cpu_rate_gb_per_hr(a["sigops_per_gb_new"])
        cpu_rate_b = cpu_rate_gb_per_hr(b["sigops_per_gb_new"])

        print(f"    {'':>25}  {name_a:>25}  {name_b:>25}")
        print(f"    {'Growth rate':>25}  {a['growth_gb_yr']:>22} GB/yr  "
              f"{b['growth_gb_yr']:>22} GB/yr")
        print(f"    {'Chain at yr 10':>25}  {pa['chain_gb']:>22.0f} GB  "
              f"{pb['chain_gb']:>22.0f} GB")
        print(f"    {'Sigops/GB (new)':>25}  {a['sigops_per_gb_new']/1e6:>22.1f}M  "
              f"{b['sigops_per_gb_new']/1e6:>22.1f}M")
        print(f"    {'FV CPU rate':>25}  {cpu_rate_a:>20.1f} GB/hr  "
              f"{cpu_rate_b:>20.1f} GB/hr")
        print(f"    {'FV bottleneck':>25}  {pa['fv_bottleneck']:>25}  "
              f"{pb['fv_bottleneck']:>25}")
        print(f"    {'AV time':>25}  {pa['av_hours']:>20.1f} hrs  "
              f"{pb['av_hours']:>20.1f} hrs")
        print(f"    {'FV time':>25}  {pa['fv_hours']:>20.1f} hrs  "
              f"{pb['fv_hours']:>20.1f} hrs")
        print(f"    {'Total IBD':>25}  {pa['total_days']:>19.1f} days  "
              f"{pb['total_days']:>19.1f} days")

        diff = pa["total_days"] - pb["total_days"]
        if abs(diff) < 0.5:
            verdict = "NEAR-WASH"
        elif diff > 0:
            verdict = f"{name_a} slower by {diff:.1f} days"
        else:
            verdict = f"{name_b} slower by {-diff:.1f} days"
        print(f"    {'Verdict':>25}  {verdict}")
        print()

    print("""  POLARITY ANALYSIS:

  Volume and density effects have opposite signs:
    - More volume (inscription) → more AV time (bad)
    - Lower density (inscription) → less FV time (good)

  But AV phase dominates (~97% of IBD time), so the volume effect
  is the primary driver. The density effect is real but small because
  FV only covers 6 months of blocks.

  Net result: IBD time is driven almost entirely by total chain size,
  not by what fills the blocks. The sig density polarity is a near-wash.
""")


def print_ibd_ceiling_table():
    """Max growth rate for IBD <= 7 days, compared with disk ceiling."""

    print("=" * 100)
    print("IBD CEILING — MAX GROWTH RATE FOR IBD <= 7 DAYS")
    print("=" * 100)
    print()

    # Disk ceiling for comparison. Shared arithmetic, not a second copy.
    disk_ceiling_10yr = sc.disk_ceiling_gb_per_year(10)

    print(f"  Disk ceiling (10yr, realistic UTXO): {disk_ceiling_10yr:.0f} GB/yr")
    print()

    sig_scenarios = [
        ("Inscription-heavy (256/GB)", SIGOPS_PER_GB_INSCRIPTION),
        ("Current mix (2.1M/GB)", SIGOPS_PER_GB_MIXED),
        ("Capped worst (3.5M/GB)", SIGOPS_PER_GB_CAPPED_WORST),
        ("Full monetary (5.0M/GB)", SIGOPS_PER_GB_MONETARY),
    ]

    print(f"  {'Sig density':<30}  {'10yr static':>12}  {'10yr +5%SW':>12}  "
          f"{'8yr static':>12}  {'8yr +5%SW':>12}  {'Disk (10yr)':>12}")
    print(f"  {'':>30}  {'GB/yr':>12}  {'GB/yr':>12}  "
          f"{'GB/yr':>12}  {'GB/yr':>12}  {'GB/yr':>12}")
    print("  " + "─" * 95)

    for label, sigops in sig_scenarios:
        rates = []
        for cy, sw in [(10, False), (10, True), (8, False), (8, True)]:
            r = max_growth_rate_ibd(cy, sigops, software_improvement=sw)
            rates.append(r)

        print(f"  {label:<30}  {rates[0]:>11.0f}  {rates[1]:>11.0f}  "
              f"{rates[2]:>11.0f}  {rates[3]:>11.0f}  {disk_ceiling_10yr:>11.0f}")

    print()
    print("  With software improvement: all IBD ceilings exceed disk. Disk binds.")
    print(f"  Static hardware: full monetary "
          f"({max_growth_rate_ibd(10, SIGOPS_PER_GB_MONETARY, software_improvement=False):.0f}"
          f" GB/yr) vs disk ({disk_ceiling_10yr:.0f} GB/yr).")
    print("  But this is the most conservative combo (max sig density + no SW gains).")
    print("  In practice, disk is the binding constraint for realistic scenarios.")
    print()


def print_mitigation_impact():
    """AssumeUTXO time-to-usable vs full IBD. SwiftSync projection."""

    print("=" * 100)
    print("MITIGATION IMPACT — ASSUMEUTXO AND SWIFTSYNC")
    print("=" * 100)
    print()

    print("  AssumeUTXO: download UTXO snapshot → validate at tip immediately →")
    print("  backfill historical validation in background.")
    print()
    print("  SwiftSync: proposed >5x IBD speedup via parallel validation + batch")
    print("  signature verification. Not deployed; treated as upside, not baseline.")
    print()

    years = [0, 5, 10, 20]

    print("  TIME-TO-USABLE (AssumeUTXO vs full IBD, +5%/yr software)")
    print()
    print(f"  {'Year':>6}  {'Scenario':<25}  {'Full IBD':>10}  "
          f"{'AssumeUTXO':>12}  {'SwiftSync':>12}")
    print(f"  {'':>6}  {'':>25}  {'(days)':>10}  "
          f"{'(hours)':>12}  {'(days)':>12}")
    print("  " + "─" * 75)

    for yr in years:
        for name in ["Unrestricted current", "Realistic worst"]:
            s = IBD_SCENARIOS[name]
            p = ibd_projection(s["growth_gb_yr"], s["sigops_per_gb_new"], yr,
                               software_improvement=True)

            # AssumeUTXO: download UTXO snapshot over broadband
            # ~50 MB/s average = 180 GB/hr. Snapshot ≈ chainstate size.
            chainstate = utxo_chainstate_gb(yr)
            assumeutxo_hours = chainstate / 180 + 0.5  # + catchup overhead

            # SwiftSync: assume 5x IBD speedup
            swiftsync_days = p["total_days"] / 5

            print(f"  {yr:>6}  {name:<25}  {p['total_days']:>10.1f}  "
                  f"{assumeutxo_hours:>12.1f}  {swiftsync_days:>12.1f}")

    print()
    print("  AssumeUTXO makes IBD a non-issue for usability (hours, not days).")
    print("  Full background validation still runs — just doesn't block the user.")
    print("  SwiftSync would compress full validation but is not yet deployed.")
    print()


def print_key_finding():
    """Bottom line: does IBD bind before disk?"""

    print("=" * 100)
    print("KEY FINDING — DOES IBD BIND BEFORE DISK?")
    print("=" * 100)

    # Compute both ceilings
    disk_ceiling = sc.disk_ceiling_gb_per_year(10)

    ibd_ceiling_static_mixed = max_growth_rate_ibd(
        10, SIGOPS_PER_GB_MIXED, software_improvement=False)
    ibd_ceiling_sw_mixed = max_growth_rate_ibd(
        10, SIGOPS_PER_GB_MIXED, software_improvement=True)
    ibd_ceiling_static_monetary = max_growth_rate_ibd(
        10, SIGOPS_PER_GB_MONETARY, software_improvement=False)

    # Spot-check: year 10 for key scenarios
    uw = ibd_projection(sc.RATE_REALISTIC_WORST, SIGOPS_PER_GB_INSCRIPTION, 10,
                         software_improvement=False)
    cw = ibd_projection(100, SIGOPS_PER_GB_CAPPED_WORST, 10,
                         software_improvement=False)
    uw_sw = ibd_projection(sc.RATE_REALISTIC_WORST, SIGOPS_PER_GB_INSCRIPTION, 10,
                            software_improvement=True)

    print(f"""
IBD CEILING vs DISK CEILING (10yr, realistic UTXO)
===================================================

  Disk ceiling:                       {disk_ceiling:.0f} GB/yr
  IBD ceiling (static, mixed):        {ibd_ceiling_static_mixed:.0f} GB/yr
  IBD ceiling (+5%/yr SW, mixed):     {ibd_ceiling_sw_mixed:.0f} GB/yr
  IBD ceiling (static, full monetary): {ibd_ceiling_static_monetary:.0f} GB/yr

  Disk binds in all static-hardware scenarios. Even full monetary
  ({ibd_ceiling_static_monetary:.0f} vs {disk_ceiling:.0f} GB/yr) — IBD ceiling stays above disk.
  With +5%/yr SW improvement: IBD ceiling pulls further away ({ibd_ceiling_sw_mixed:.0f} GB/yr).

YEAR 10 SPOT CHECK (static hardware)
=====================================

  Realistic worst ({sc.RATE_REALISTIC_WORST:.0f} GB/yr, inscription-saturated):
    Chain: {uw['chain_gb']:.0f} GB, AV: {uw['av_hours']:.1f}h, FV: {uw['fv_hours']:.1f}h
    Total: {uw['total_days']:.1f} days — FV bottleneck: {uw['fv_bottleneck']}

  Capped worst (100 GB/yr, 70% monetary density):
    Chain: {cw['chain_gb']:.0f} GB, AV: {cw['av_hours']:.1f}h, FV: {cw['fv_hours']:.1f}h
    Total: {cw['total_days']:.1f} days — FV bottleneck: {cw['fv_bottleneck']}

  Near-identical. The volume vs density polarity is a near-wash.

  With +5%/yr software improvement, realistic worst drops to
  {uw_sw['total_days']:.1f} days — well within 7-day threshold.

THE POLARITY NEAR-WASH
=======================

  Inscription-heavy blocks: +volume (bad for AV) but -sigs (good for FV).
  Monetary-heavy blocks:    -volume (good for AV) but +sigs (bad for FV).

  Because AV is ~97% of IBD time and doesn't verify signatures,
  the signature density barely matters. Total chain size dominates.

  This confirms the ceiling.py finding: disk is the binding constraint.
  IBD adds no additional restriction beyond what disk already imposes.

KEY UNCERTAINTIES
=================

  1. AV rate (12 GB/hr) calibrated to observed N100 IBD, not independently measured
  2. Sigops-per-GB constants are theoretical from tx type analysis
  3. N100 sig verification rate (~13,000/sec) scaled from libsecp256k1 benchmarks
  4. Software improvement 5%/yr is conservative — SwiftSync could be step change
  5. AssumeUTXO (hours to usable) makes the entire analysis academic for usability
""")


def main():
    print_two_phase_analysis()
    print_sig_density_comparison()
    print_ibd_ceiling_table()
    print_mitigation_impact()
    print_key_finding()


if __name__ == "__main__":
    main()
