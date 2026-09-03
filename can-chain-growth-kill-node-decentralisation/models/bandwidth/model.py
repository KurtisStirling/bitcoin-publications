"""
Bandwidth Ceiling Model — Node Viability Analysis

Answers: what sustained bandwidth does a full node require, and when (if ever)
does residential internet become the binding constraint on chain growth policy?

Three bandwidth components:
1. Block relay at tip — receiving new blocks as they're mined
2. Peer serving — uploading historical blocks to syncing peers
3. IBD download — downloading the full chain within 7 days

Key findings:
- Tip-following is trivial (~3 KB/s with compact blocks)
- IBD download needs ~9.6 Mbps for the current chain (724 GB in 7 days)
- Below ~27 Mbps, download is slower than processing — bandwidth
  becomes the IBD bottleneck instead of I/O
- For growth rate policy: at ≥27 Mbps (global median), the bandwidth
  ceiling exceeds the disk ceiling. Disk still binds.
- For developing nations (<10 Mbps): IBD is already download-bound
  at 13+ days. This is a current reality, not a growth problem.
  AssumeUTXO solves the usability issue.

Target hardware (from Q036): $300 N100 mini-PC, 2TB SSD, 16GB RAM
"""

# ── Constants ─────────────────────────────────────────────────────────

BLOCKS_PER_HOUR = 6
BLOCKS_PER_DAY = 144
SECONDS_PER_DAY = 86_400

# ── Baseline (2025) ──────────────────────────────────────────────────
# Baselines and scenarios live in models/scenarios.py. Do not redefine here.

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import scenarios as sc

# The IBD ceiling is the IBD model's result, not ours. Loaded by path because
# both files are called model.py and neither directory is a package.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "ibd_model", pathlib.Path(__file__).resolve().parent.parent / "ibd" / "model.py")
ibd_model = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(ibd_model)

BLOCKS_PER_YEAR = sc.BLOCKS_PER_YEAR
CHAIN_SIZE_GB_2026 = sc.CHAIN_GB_2026

# ── IBD processing rates (from ibd.py) ───────────────────────────────
# These are CPU/I/O rates — they set the FLOOR for when download stops
# being the bottleneck.

IBD_RATE_AV_GB_PER_HR = sc.IBD_RATE_GB_PER_HR   # I/O bound, observed N100 IBD
IBD_RATE_BLENDED_GB_PER_HR = sc.IBD_RATE_GB_PER_HR  # observed blended rate on N100

# Download speed needed to match processing rate. Decimal throughout:
# 1 GB = 10^9 bytes, 1 Mbps = 10^6 bit/s.
#   12 GB/hr: 12 * 1000 * 8 / 3600 ≈ 26.7 Mbps
# Below this speed, download is the IBD bottleneck.

# ── Block relay ──────────────────────────────────────────────────────
# BIP152 compact blocks: only short transaction IDs are sent (~6 bytes
# each), not full transactions. A node with a well-synced mempool
# receives ~10-30 KB per compact block instead of the full 1-4 MB.
#
# Compact block reconstruction fails when the node is missing txs from
# the mempool → falls back to full block download. Failure rate is low
# for well-connected nodes (<5% of blocks need full download).

COMPACT_BLOCK_KB = 25          # typical compact block (BIP152)
COMPACT_BLOCK_FAIL_RATE = 0.05 # fraction needing full block fallback

# Transaction relay: nodes relay individual transactions as they arrive.
# Average mempool throughput: ~3-7 tx/sec, ~250-500 bytes/tx average.

TX_RELAY_AVG_BYTES_PER_SEC = 2000  # ~2 KB/s average tx relay

# ── Peer serving (upload) ─────────────────────────────────────────────
# Each syncing peer effectively pulls at ~1 Mbps (limited by their own
# processing speed, not the serving node's upload).

SYNCING_PEERS_TYPICAL = 2
SYNCING_PEERS_WORST = 5
UPLOAD_PER_SYNCING_PEER_MBPS = 1.0

# ── IBD ───────────────────────────────────────────────────────────────

MAX_IBD_DAYS = 7

# ── Residential internet trajectories ─────────────────────────────────
# Sources: Ookla Speedtest Global Index, ITU, Cisco Annual Internet Report.
#
# RESEARCH FINDINGS (26-03-03):
#
# 1. CAGR vs step-function: Year-to-year growth is lumpy (UK: +1% in 2020-21,
#    then +79% on fibre rollout; India: two step functions from Jio 4G and 5G).
#    But over a decade, smooth CAGR is a reasonable approximation because
#    countries' step functions are staggered. The model's 8-10% CAGR is very
#    conservative. Actual observed (Cisco 2018-2023):
#      - Global average: ~19% CAGR
#      - Developed nations: 20-22% CAGR (N. America 20%, W. Europe 22%)
#      - Developing nations: 24-50% CAGR (India 33%, Nigeria 35%, Philippines 50%)
#    Even stall cases (Germany 61% DSL, Australia FTTN debacle) sit well above
#    the ~27 Mbps crossover where bandwidth binds before disk.
#
# 2. Tier baselines: intentionally conservative stress-test floors, not medians.
#    Ookla 2025 medians: global ~104 Mbps, USA 303, UK 155, Germany 101 (worst
#    developed nation — 61% still DSL), India 60, Nigeria 44, Indonesia 32.
#    The 5 Mbps "developing nation" baseline = Afghanistan/Cuba/Syria only (3-4
#    countries). Representative developing nations with broadband are 30-60 Mbps.
#    These tiers are kept conservative deliberately — the conclusion (bandwidth
#    doesn't bind) holds even at these pessimistic floors.
#
# 3. Bitcoin Core P2P efficiency during IBD:
#    Below ~25 Mbps (download-bound): Core achieves ~80-90% of line speed.
#      Download IS the bottleneck. Protocol overhead ~10-20% (stalling timeouts,
#      round-trip overhead, peer quality variance).
#    Above ~50 Mbps (validation-bound): Core uses ~5-25% of line speed.
#      Download fills the 1024-block window (~1 GB buffer) in seconds, then idles
#      waiting for sequential block validation. CPU is the bottleneck, not download.
#    Lopp tested 48 peers + 10,000-block window: "negligible" improvement — confirms
#    validation, not download protocol, is the constraint.
#    Full-line-speed assumption is approximately correct in the download-bound
#    regime (where it matters) and irrelevant in the validation-bound regime.

BANDWIDTH_TRAJECTORIES = {
    "developing_nation": {
        "label": "Developing nation (5 Mbps / 2 Mbps)",
        "download_mbps_2025": 5.0,
        "upload_mbps_2025": 2.0,
        "annual_improvement_pct": 10,
        # Stress-test floor: only Afghanistan, Cuba, Syria at this level.
        # Representative developing nations (India 60, Nigeria 44, Indonesia 32).
        # 10%/yr is conservative — actual developing-nation CAGR is 24-50%.
    },
    "global_median": {
        "label": "Global median (50 Mbps / 10 Mbps)",
        "download_mbps_2025": 50.0,
        "upload_mbps_2025": 10.0,
        "annual_improvement_pct": 8,
        # Ookla 2025 global median is ~104 Mbps — this tier is conservative by 2x.
        # 8%/yr is conservative — actual global CAGR is ~19%.
    },
    "developed_nation": {
        "label": "Developed nation (100 Mbps / 20 Mbps)",
        "download_mbps_2025": 100.0,
        "upload_mbps_2025": 20.0,
        "annual_improvement_pct": 8,
        # 100 Mbps = Germany, the worst major developed nation (61% DSL).
        # Most developed nations: 150-300+ Mbps. Conservative floor.
        # 8%/yr is conservative — actual developed-nation CAGR is 20-22%.
    },
}

# ── Policy scenarios (from ceiling.py) ────────────────────────────────

def _policy(rate_gb_yr, note):
    """Rate and average block size can never disagree: one derives the other."""
    return {
        "growth_gb_yr": rate_gb_yr,
        "avg_block_mb": rate_gb_yr / sc.GB_PER_YEAR_PER_MB_BLOCK,
        "note": note,
    }


POLICY_SCENARIOS = {
    "Unrestricted monetary": _policy(
        sc.RATE_MONETARY, "Current rules, only monetary txs fill blocks."),
    "Unrestricted current": _policy(
        sc.RATE_CURRENT, "Current trajectory: today's 1.69 MB average block."),
    "Realistic worst": _policy(
        sc.RATE_REALISTIC_WORST,
        "Inscription-saturated blocks at the observed 10% image mix."),
    "Theoretical max": _policy(
        sc.RATE_THEORETICAL_MAX,
        "4M weight units of pure witness data. A bound, not a forecast."),
    "Capped (Option D)": _policy(
        sc.RATE_MONETARY, "BIP cap active, only monetary txs."),
    "Capped worst": {
        "growth_gb_yr": 100,
        "avg_block_mb": 1.95,
        "note": "BIP cap active, max data stuffing under cap.",
    },
}


# ── Helper functions ──────────────────────────────────────────────────

def mbps_to_gb_per_hr(mbps: float) -> float:
    """Convert Mbps (megabits/sec) to GB/hr."""
    return mbps / 8 * 3600 / 1000


def mbps_to_gb_per_day(mbps: float) -> float:
    """Convert Mbps (megabits/sec) to GB/day."""
    return mbps * SECONDS_PER_DAY / 8 / 1000


def gb_per_day_to_kbps(gb_per_day: float) -> float:
    """Convert GB/day to KB/s."""
    return gb_per_day * 1_000_000 / SECONDS_PER_DAY


def bandwidth_at_year(base_mbps: float, improvement_pct: float, year: int) -> float:
    """Bandwidth (Mbps) at year N with annual improvement."""
    return base_mbps * (1 + improvement_pct / 100) ** year


# ── Component 1: Block relay bandwidth ────────────────────────────────

def block_relay_kbps(avg_block_mb: float) -> dict:
    """
    Steady-state bandwidth for receiving new blocks at tip.

    Two modes:
    - Compact blocks (BIP152): ~25 KB per block + rare full fallback
    - Full blocks (no compact): full block every ~10 min (worst case)
    """
    compact_kb_per_block = COMPACT_BLOCK_KB
    full_kb_per_block = avg_block_mb * 1000
    effective_kb_per_block = (
        compact_kb_per_block * (1 - COMPACT_BLOCK_FAIL_RATE) +
        full_kb_per_block * COMPACT_BLOCK_FAIL_RATE
    )
    compact_kbps = effective_kb_per_block * BLOCKS_PER_DAY / SECONDS_PER_DAY
    full_kbps = full_kb_per_block * BLOCKS_PER_DAY / SECONDS_PER_DAY
    tx_relay_kbps = TX_RELAY_AVG_BYTES_PER_SEC / 1000

    return {
        "compact_kbps": compact_kbps,
        "full_kbps": full_kbps,
        "tx_relay_kbps": tx_relay_kbps,
        "total_compact_kbps": compact_kbps + tx_relay_kbps,
        "total_full_kbps": full_kbps + tx_relay_kbps,
    }


# ── Component 2: Peer serving bandwidth (upload) ─────────────────────

def peer_serving_kbps(syncing_peers: int = SYNCING_PEERS_TYPICAL) -> dict:
    """Upload bandwidth consumed serving historical blocks to syncing peers."""
    total_mbps = syncing_peers * UPLOAD_PER_SYNCING_PEER_MBPS
    total_kbps = total_mbps * 1000 / 8

    return {
        "syncing_peers": syncing_peers,
        "per_peer_kbps": UPLOAD_PER_SYNCING_PEER_MBPS * 1000 / 8,
        "total_kbps": total_kbps,
        "total_mbps": total_mbps,
    }


# ── Component 3: IBD download ────────────────────────────────────────

def ibd_download_requirement(chain_gb: float, max_days: int = MAX_IBD_DAYS) -> dict:
    """
    Minimum download bandwidth to complete IBD download within max_days.

    Note: this is the DOWNLOAD requirement only. Actual IBD time is
    max(download_time, processing_time). Below ~27 Mbps, download is
    the bottleneck; above, I/O is.
    """
    gb_per_day = chain_gb / max_days
    kbps = gb_per_day_to_kbps(gb_per_day)
    mbps = kbps * 8 / 1000

    return {
        "chain_gb": chain_gb,
        "max_days": max_days,
        "gb_per_day": gb_per_day,
        "required_kbps": kbps,
        "required_mbps": mbps,
    }


def ibd_actual_time_days(chain_gb: float, download_mbps: float) -> dict:
    """
    Actual IBD time considering both download and processing constraints.

    IBD time = max(download_time, processing_time) because download and
    processing overlap (Core downloads ahead, processes sequentially).

    Below ~27 Mbps: download-bound (download slower than processing)
    Above ~27 Mbps: processing-bound (I/O is the bottleneck)
    """
    download_gb_hr = mbps_to_gb_per_hr(download_mbps)
    download_days = chain_gb / download_gb_hr / 24 if download_gb_hr > 0 else float("inf")
    processing_days = chain_gb / IBD_RATE_BLENDED_GB_PER_HR / 24

    if download_days > processing_days:
        bottleneck = "download"
        total_days = download_days
    else:
        bottleneck = "CPU/I/O"
        total_days = processing_days

    return {
        "download_days": download_days,
        "processing_days": processing_days,
        "total_days": total_days,
        "bottleneck": bottleneck,
        "download_gb_hr": download_gb_hr,
    }


# ── Ceiling computation ──────────────────────────────────────────────

def bandwidth_ceiling_gb_yr(
    download_mbps: float,
    cycle_years: int = 10,
) -> float:
    """
    Max chain growth rate (GB/yr) where IBD download completes in 7 days.

    This is the bandwidth-limited ceiling: the chain must be downloadable
    in 7 days at the given speed. Returns negative if the CURRENT chain
    already can't be downloaded in 7 days (already exceeded).
    """
    download_gb_per_day = mbps_to_gb_per_day(download_mbps)
    max_chain_gb = download_gb_per_day * MAX_IBD_DAYS
    return (max_chain_gb - CHAIN_SIZE_GB_2026) / cycle_years


# ── Output functions ──────────────────────────────────────────────────

def print_component_breakdown():
    """Bandwidth requirements by component for each policy scenario."""

    print("=" * 95)
    print("BANDWIDTH REQUIREMENTS BY COMPONENT")
    print("=" * 95)
    print()
    print("Target hardware: $300 N100 mini-PC, residential internet")
    print()

    print("  COMPONENT 1: BLOCK RELAY AT TIP (download)")
    print()
    print(f"  {'Scenario':<30}  {'Avg block':>10}  {'Compact':>10}  "
          f"{'Full blk':>10}  {'+ tx relay':>10}")
    print(f"  {'':>30}  {'(MB)':>10}  {'(KB/s)':>10}  "
          f"{'(KB/s)':>10}  {'(KB/s)':>10}")
    print("  " + "─" * 75)

    for name, s in POLICY_SCENARIOS.items():
        r = block_relay_kbps(s["avg_block_mb"])
        print(f"  {name:<30}  {s['avg_block_mb']:>10.2f}  "
              f"{r['compact_kbps']:>10.2f}  {r['full_kbps']:>10.2f}  "
              f"{r['total_compact_kbps']:>10.2f}")

    print()
    print(f"  Transaction relay background: ~{TX_RELAY_AVG_BYTES_PER_SEC/1000:.1f} KB/s")
    print(f"  Compact block (BIP152): ~{COMPACT_BLOCK_KB} KB/block, "
          f"{COMPACT_BLOCK_FAIL_RATE*100:.0f}% fallback to full")
    print()
    print("  Verdict: tip-following needs ~3 KB/s. Trivial on any connection.")
    print()

    print("  COMPONENT 2: PEER SERVING (upload)")
    print()
    for peers in [1, SYNCING_PEERS_TYPICAL, SYNCING_PEERS_WORST]:
        s = peer_serving_kbps(peers)
        print(f"    Serving {peers} syncing peer{'s' if peers > 1 else ' '}: "
              f"{s['total_kbps']:.0f} KB/s ({s['total_mbps']:.1f} Mbps upload)")
    print()

    print("  COMPONENT 3: IBD DOWNLOAD")
    print()
    print(f"  {'Scenario':<30}  {'Chain yr 10':>12}  {'DL needed':>10}  "
          f"{'DL needed':>10}")
    print(f"  {'':>30}  {'(GB)':>12}  {'(KB/s)':>10}  {'(Mbps)':>10}")
    print("  " + "─" * 65)

    for name, s in POLICY_SCENARIOS.items():
        chain_10 = CHAIN_SIZE_GB_2026 + s["growth_gb_yr"] * 10
        ibd = ibd_download_requirement(chain_10)
        print(f"  {name:<30}  {chain_10:>12.0f}  "
              f"{ibd['required_kbps']:>10.0f}  {ibd['required_mbps']:>10.1f}")

    print()
    # Current chain requirement
    ibd_now = ibd_download_requirement(CHAIN_SIZE_GB_2026)
    print(f"  Current chain (724 GB): needs {ibd_now['required_mbps']:.1f} Mbps "
          f"to download in 7 days.")
    print()


def print_download_vs_cpu():
    """Show when download becomes the IBD bottleneck vs CPU/I/O."""

    print("=" * 95)
    print("DOWNLOAD vs CPU — WHEN IS BANDWIDTH THE IBD BOTTLENECK?")
    print("=" * 95)
    print()
    print("  During IBD, download and processing overlap. The slower one")
    print("  determines total time. At what speed does download become the")
    print("  bottleneck?")
    print()

    processing_mbps = IBD_RATE_BLENDED_GB_PER_HR * 1000 * 8 / 3600

    print(f"  Processing rate (N100):  {IBD_RATE_BLENDED_GB_PER_HR:.0f} GB/hr "
          f"→ need {processing_mbps:.0f} Mbps to keep up")
    print()
    print(f"  Below ~{processing_mbps:.0f} Mbps: download is slower than processing "
          f"→ download-bound")
    print(f"  Above ~{processing_mbps:.0f} Mbps: processing is slower than download "
          f"→ CPU/I/O-bound")
    print()

    # IBD time at various speeds for current chain
    print("  IBD TIME vs DOWNLOAD SPEED (current chain, 724 GB)")
    print()
    print(f"  {'Download':>10}  {'DL rate':>10}  {'DL time':>10}  "
          f"{'CPU time':>10}  {'Actual':>10}  {'Bottleneck'}")
    print(f"  {'(Mbps)':>10}  {'(GB/hr)':>10}  {'(days)':>10}  "
          f"{'(days)':>10}  {'(days)':>10}")
    print("  " + "─" * 65)

    for mbps in [5, 10, 15, 25, 35, 50, 100]:
        r = ibd_actual_time_days(CHAIN_SIZE_GB_2026, mbps)
        print(f"  {mbps:>10}  {r['download_gb_hr']:>10.1f}  "
              f"{r['download_days']:>10.1f}  {r['processing_days']:>10.1f}  "
              f"{r['total_days']:>10.1f}  {r['bottleneck']}")

    print()
    for _mbps, _tail in [
        (5, "bandwidth is the bottleneck"),
        (10, "against the 7-day window"),
        (25, "just above processing rate"),
    ]:
        _days = CHAIN_SIZE_GB_2026 / mbps_to_gb_per_hr(_mbps) / 24
        print(f"  At {_mbps} Mbps: download takes {_days:.1f} days — {_tail}.")
    print(f"  At {processing_mbps:.0f}+ Mbps: download faster than processing "
          f"— I/O dominates.")
    print()


def print_trajectory_comparison():
    """Compare bandwidth requirements against residential trajectories."""

    print("=" * 95)
    print("BANDWIDTH vs RESIDENTIAL INTERNET — TRAJECTORY COMPARISON")
    print("=" * 95)
    print()

    years = [0, 5, 10, 20, 40]

    for traj_name, traj in BANDWIDTH_TRAJECTORIES.items():
        print(f"  {traj['label']}")
        print(f"  Improvement: +{traj['annual_improvement_pct']}%/yr")
        print()
        print(f"  {'Year':>6}  {'DL speed':>10}  {'Chain':>10}  "
              f"{'IBD DL time':>12}  {'IBD actual':>12}  {'Bottleneck'}")
        print(f"  {'':>6}  {'(Mbps)':>10}  {'(GB)':>10}  "
              f"{'(days)':>12}  {'(days)':>12}")
        print("  " + "─" * 70)

        for yr in years:
            dl = bandwidth_at_year(traj["download_mbps_2025"],
                                   traj["annual_improvement_pct"], yr)

            # Use worst-case growth for stress test
            worst = POLICY_SCENARIOS["Realistic worst"]
            chain_gb = CHAIN_SIZE_GB_2026 + worst["growth_gb_yr"] * yr

            r = ibd_actual_time_days(chain_gb, dl)

            status = ""
            if r["total_days"] > MAX_IBD_DAYS:
                status = " !"

            print(f"  {yr:>6}  {dl:>10.1f}  {chain_gb:>10.0f}  "
                  f"{r['download_days']:>12.1f}  {r['total_days']:>12.1f}  "
                  f"{r['bottleneck']}{status}")

        print(f"  (! = exceeds 7-day threshold, "
              f"{sc.RATE_REALISTIC_WORST:.0f} GB/yr realistic-worst growth)")
        print()


def print_bandwidth_ceiling():
    """Bandwidth ceiling vs disk ceiling for each trajectory."""

    print("=" * 95)
    print("BANDWIDTH CEILING — MAX GROWTH RATE (GB/yr) FOR 7-DAY IBD DOWNLOAD")
    print("=" * 95)
    print()
    print("  'Bandwidth ceiling' = max growth rate where the chain can be")
    print("  DOWNLOADED in 7 days. Negative means the current chain already")
    print("  can't be downloaded in 7 days at that speed.")
    print()

    print(f"  {'Trajectory':<45}  {'DL (Mbps)':>10}  "
          f"{'BW ceil':>10}  {'Disk ceil':>10}  {'BW binds?'}")
    print(f"  {'':>45}  {'':>10}  "
          f"{'(GB/yr)':>10}  {'(GB/yr)':>10}")
    print("  " + "─" * 90)

    for traj_name, traj in BANDWIDTH_TRAJECTORIES.items():
        dl = traj["download_mbps_2025"]
        bw_ceil = bandwidth_ceiling_gb_yr(dl, cycle_years=10)
        disk_ceil = round(sc.disk_ceiling_gb_per_year(10))
        binds = "YES" if bw_ceil < disk_ceil else "no"
        bw_str = f"{bw_ceil:.0f}" if bw_ceil > 0 else f"{bw_ceil:.0f} (already exceeded)"

        print(f"  {traj['label']:<45}  {dl:>10.0f}  "
              f"{bw_str:>10}  {disk_ceil:>10}  {binds}")

    print()

    # What speed is needed for the bandwidth ceiling to match the disk ceiling?
    disk_ceiling = sc.disk_ceiling_gb_per_year(10)
    needed_chain = CHAIN_SIZE_GB_2026 + disk_ceiling * 10
    needed_gbday = needed_chain / MAX_IBD_DAYS
    needed_mbps = needed_gbday * 1000 * 8 / SECONDS_PER_DAY
    print(f"  Crossover: need {needed_mbps:.0f} Mbps for bandwidth ceiling "
          f"to match disk ceiling ({disk_ceiling:.0f} GB/yr).")
    print(f"  At that speed, chain at year 10 = {needed_chain:.0f} GB, "
          f"downloadable in 7 days.")
    print()

    ibd_ceiling = ibd_model.max_growth_rate_ibd(
        10, ibd_model.SIGOPS_PER_GB_MIXED, software_improvement=False)
    print("  For reference:")
    print(f"  Disk ceiling (10yr, realistic UTXO):  {disk_ceiling:.0f} GB/yr")
    print(f"  IBD ceiling (10yr, static, mixed):    {ibd_ceiling:.0f} GB/yr")
    print()


def print_developing_nation_focus():
    """Deep dive on developing nation — the only case where bandwidth matters."""

    print("=" * 95)
    print("DEVELOPING NATION DEEP DIVE — THE TIGHTEST CASE")
    print("=" * 95)
    print()

    traj = BANDWIDTH_TRAJECTORIES["developing_nation"]
    dl_2025 = traj["download_mbps_2025"]
    ul_2025 = traj["upload_mbps_2025"]
    imp = traj["annual_improvement_pct"]

    print(f"  Baseline: {dl_2025} Mbps down / {ul_2025} Mbps up, +{imp}%/yr")
    print()

    # IBD reality check
    print("  IBD REALITY CHECK (current trajectory, 80 GB/yr)")
    print()
    print(f"  {'Year':>6}  {'DL speed':>10}  {'Chain':>10}  "
          f"{'DL time':>10}  {'CPU time':>10}  {'Actual':>10}  {'Bottleneck'}")
    print(f"  {'':>6}  {'(Mbps)':>10}  {'(GB)':>10}  "
          f"{'(days)':>10}  {'(days)':>10}  {'(days)':>10}")
    print("  " + "─" * 70)

    for yr in [0, 5, 10, 20]:
        dl = bandwidth_at_year(dl_2025, imp, yr)
        chain = CHAIN_SIZE_GB_2026 + 80 * yr  # current trajectory

        r = ibd_actual_time_days(chain, dl)
        flag = " !" if r["total_days"] > MAX_IBD_DAYS else ""

        print(f"  {yr:>6}  {dl:>10.1f}  {chain:>10.0f}  "
              f"{r['download_days']:>10.1f}  {r['processing_days']:>10.1f}  "
              f"{r['total_days']:>10.1f}  {r['bottleneck']}{flag}")

    print()
    print(f"  At 5 Mbps, IBD is download-bound at "
          f"{CHAIN_SIZE_GB_2026 / mbps_to_gb_per_hr(5) / 24:.0f} days. This is the current")
    print("  reality — not caused by future chain growth. A developing-nation")
    print("  operator already needs ~10 Mbps to IBD within 7 days.")
    print()

    # AssumeUTXO changes the picture
    print("  ASSUMEUTXO CHANGES EVERYTHING")
    print()
    print("  AssumeUTXO downloads a UTXO snapshot (~11 GB), validates at tip")
    print("  immediately, then backfills historical validation in background.")
    print()
    print(f"  At 5 Mbps:  11 GB snapshot = {11 / mbps_to_gb_per_hr(5):.1f} hours → usable")
    print(f"  At 10 Mbps: 11 GB snapshot = {11 / mbps_to_gb_per_hr(10):.1f} hours → usable")
    print(f"  At 50 Mbps: 11 GB snapshot = {11 / mbps_to_gb_per_hr(50):.1f} hours → usable")
    print()
    print("  With AssumeUTXO, time-to-usable is hours (not days) on any")
    print("  connection. Full historical validation still runs in background")
    print("  but doesn't block the user.")
    print()

    # Upload check
    print("  PEER SERVING (upload)")
    print()
    serving_2 = peer_serving_kbps(2)
    serving_1 = peer_serving_kbps(1)
    headroom_2 = ul_2025 / serving_2["total_mbps"]
    headroom_1 = ul_2025 / serving_1["total_mbps"]
    print(f"  Upload available:    {ul_2025} Mbps ({ul_2025 * 1000 / 8:.0f} KB/s)")
    print(f"  1 syncing peer:      {serving_1['total_mbps']:.1f} Mbps → "
          f"{headroom_1:.0f}x headroom")
    print(f"  2 syncing peers:     {serving_2['total_mbps']:.1f} Mbps → "
          f"{headroom_2:.0f}x headroom (tight)")
    print()

    # Summary
    print("  DEVELOPING NATION SUMMARY")
    print()
    print("  A 5 Mbps / 2 Mbps node can:")
    print("    - Follow the tip:      YES (~3 KB/s with compact blocks)")
    print("    - AssumeUTXO sync:     YES (~5 hours to usable)")
    print(f"    - Full IBD (<7 days):  NO (takes "
          f"~{CHAIN_SIZE_GB_2026 / mbps_to_gb_per_hr(5) / 24:.0f} days, download-bound)")
    print("    - Serve 2 peers:       YES (barely — 1x headroom)")
    print()
    print("  Bandwidth IS a real limitation for developing nations, but:")
    print("    1. It's a current reality (not caused by chain growth policy)")
    print("    2. AssumeUTXO makes it a non-issue for usability")
    print("    3. Internet speeds improve faster than chain grows (~10%/yr vs linear)")
    print("    4. Disk fills up before bandwidth becomes the policy constraint")
    print()


def print_key_finding():
    """Bottom line verdict."""

    bw_dev = bandwidth_ceiling_gb_yr(5.0)
    bw_med = bandwidth_ceiling_gb_yr(50.0)
    bw_27 = bandwidth_ceiling_gb_yr(27.0)

    disk_ceiling = sc.disk_ceiling_gb_per_year(10)
    ibd_ceiling = ibd_model.max_growth_rate_ibd(
        10, ibd_model.SIGOPS_PER_GB_MIXED, software_improvement=False)
    ibd_mbps_now = ibd_download_requirement(CHAIN_SIZE_GB_2026)["required_mbps"]
    bw_ratio = bw_med / disk_ceiling
    # Speed at which the bandwidth ceiling equals the disk ceiling. Distinct
    # from the ~27 Mbps processing crossover: that one is where download stops
    # being slower than the N100 can validate.
    xover_mbps = ((CHAIN_SIZE_GB_2026 + disk_ceiling * 10) / MAX_IBD_DAYS
                  * 1000 * 8 / SECONDS_PER_DAY)

    print("=" * 95)
    print("KEY FINDING — BANDWIDTH DOES NOT CHANGE THE GROWTH RATE CEILING")
    print("=" * 95)

    print(f"""
BANDWIDTH CEILING vs OTHER CEILINGS (10yr cycle)
=================================================

  Disk ceiling:                       {disk_ceiling:.0f} GB/yr
  IBD ceiling (static, mixed):        {ibd_ceiling:.0f} GB/yr
  Bandwidth ceiling (5 Mbps):         {bw_dev:.0f} GB/yr  (already exceeded)
  Bandwidth ceiling (27 Mbps):        {bw_27:.0f} GB/yr  (above disk ceiling)
  Bandwidth ceiling (50 Mbps):        {bw_med:.0f} GB/yr  ({bw_ratio:.1f}x disk)

THREE COMPONENTS, THREE VERDICTS
=================================

  1. TIP-FOLLOWING: ~3 KB/s with compact blocks (BIP152).
     Trivial. Not a factor at any connection speed.

  2. IBD DOWNLOAD: {ibd_mbps_now:.1f} Mbps needed for current chain (724 GB / 7 days).
     - Below ~10 Mbps: IBD is download-bound (>7 days). Affects ~3-5%
       of global fixed broadband connections (conflict states, rural
       ADSL). Core achieves ~80-90% of line speed in this regime.
     - Below ~{xover_mbps:.0f} Mbps: bandwidth ceiling tighter than the disk
       ceiling. ~10-20% of global connections (DSL tail in developed
       countries, rural areas, poorer developing nations).
     - Above ~{xover_mbps:.0f} Mbps: bandwidth ceiling exceeds the disk
       ceiling. Disk binds first, and above ~27 Mbps download is also
       faster than the N100 can process. Bandwidth irrelevant for policy.

  3. PEER SERVING (upload): ~2 Mbps for 2 syncing peers.
     Tight for developing nations (2 Mbps up). Not a node viability
     issue — the node works fine, it just serves fewer peers.
     Network-level concern, not individual-node ceiling.

WHY BANDWIDTH DOESN'T CONSTRAIN GROWTH RATE POLICY
====================================================

  For any connection ≥27 Mbps (global median is ~104 Mbps and rising at
  ~19% CAGR), the bandwidth ceiling is above the disk ceiling. Disk
  fills the SSD before bandwidth becomes the limiting factor.

  For connections <27 Mbps (~10-20% of global fixed broadband), IBD is
  already download-bound TODAY (before any chain growth). This is a
  fixed infrastructure gap that:
  (a) Shrinks every year as internet improves (actual CAGR 24-50% in
      developing nations — much faster than the model's conservative 10%)
  (b) Is solved by AssumeUTXO (hours to usable, not days)
  (c) Doesn't change what growth rate is sustainable — disk binds first

  The bandwidth ceiling concept doesn't constrain policy because the
  disk fills up before the connection speed matters. To change this,
  you'd need SSD capacity to grow much faster than internet speeds —
  the opposite of the actual trend.

VERDICT
=======

  Bandwidth is dismissed as a binding constraint on chain growth policy.
  Order of binding:  1. Disk / IBD (I/O)  2. Bandwidth (distant)

  Caveat: connections below ~27 Mbps (~10-20% of global fixed broadband,
  including DSL tail in developed nations and rural developing areas)
  are download-bound for IBD. Below ~10 Mbps (~3-5%, conflict states
  and rural ADSL), IBD exceeds 7 days. AssumeUTXO is the solution —
  already implemented, just needs adoption. This is a deployment
  concern, not a policy concern.
""")


def main():
    print_component_breakdown()
    print_download_vs_cpu()
    print_trajectory_comparison()
    print_bandwidth_ceiling()
    print_developing_nation_focus()
    print_key_finding()


if __name__ == "__main__":
    main()
