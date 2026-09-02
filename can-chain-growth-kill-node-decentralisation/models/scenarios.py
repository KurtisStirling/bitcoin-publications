"""
Canonical baselines and chain-growth scenarios, shared by every model here.

Single source of truth. Before this file existed the storage model used a
196 GB/yr data-heavy case while the IBD and bandwidth models used 150 GB/yr
for the scenario of the same name, and three print statements carried numbers
their own code contradicted.

UNITS
-----
Decimal throughout: 1 GB = 1,000 MB = 10^9 bytes.

Drives are sold in decimal GB and the reference machine is specified as a
2 TB SSD = 2,000 GB, so every disk figure in this paper was already decimal.
The old block-size conversion (MB x 52,560 / 1024) applied a binary divisor to
a decimal numerator, mixing both conventions inside the same tables and running
2.4% low on every block-derived number. Nothing here uses 1024.
"""

# ── Reference hardware and current chain state ───────────────────────

CHAIN_GB_2026 = 724.0            # on-chain measurement, March 2026
CHAINSTATE_GB_2025 = 11.0        # UTXO set on-disk (LevelDB)
UTXO_SET_ENTRIES_2025 = 169_000_000
BYTES_PER_UTXO_ENTRY = 63        # measured: 11 GB / 173M entries (Apr 2025)

SSD_NOMINAL_GB = 2000            # "2 TB SSD", decimal as sold
SSD_GB = 1850                    # usable: minus ext4 reserve (100) and OS/swap/logs (50)
USABLE_TB_2026 = SSD_GB / 1000   # 1.85 TB, for the capacity charts

RAM_GB = 16
IBD_RATE_GB_PER_HR = 12.0        # I/O bound, calibrated to observed N100 IBD
MAX_IBD_DAYS = 7

# ── Block cadence ────────────────────────────────────────────────────
# 52,560 is the difficulty-TARGETED cadence (144 blocks/day), not an enforced
# rate. Actual production runs slightly above target while hashrate grows, so
# every rate below is an envelope at target cadence rather than a hard cap.

BLOCKS_PER_YEAR = 144 * 365      # 52,560
GB_PER_YEAR_PER_MB_BLOCK = BLOCKS_PER_YEAR / 1000  # 52.56 GB/yr per 1 MB block


def mb_to_gb_per_year(avg_block_mb: float) -> float:
    """Average block size (decimal MB) -> chain growth (decimal GB/year)."""
    return avg_block_mb * GB_PER_YEAR_PER_MB_BLOCK


# ── Inscription block construction ───────────────────────────────────
# What average block size results from blocks filled with inscription
# transactions carrying a given payload?
#
# Every full block spends the same 4,000,000 weight units, but bytes written to
# disk depend on composition. Witness bytes cost 1 WU; non-witness bytes cost 4.
#
# Per inscription reveal transaction, with payload D bytes in the witness:
#     weight         = 481 + D WU
#     serialized size = 199 + D bytes
# These two are consistent with ~94 non-witness bytes and ~105 + D witness
# bytes, which is what a taproot reveal actually looks like.
#
# BLOCK_OVERHEAD_WU / _BYTES cover the header and coinbase. Both are carried
# forward from the original derivation and are approximate; they move the
# result by ~27 bytes in 3.8 MB, so precision here does not matter.

WEIGHT_LIMIT = 4_000_000
BLOCK_OVERHEAD_WU = 892
BLOCK_OVERHEAD_BYTES = 250
TX_OVERHEAD_WU = 481
TX_OVERHEAD_BYTES = 199

# Observed inscription payload sizes.
BRC20_TEXT_PAYLOAD_B = 75
IMAGE_PAYLOAD_B = 21_000

# Share of inscriptions that were images, by count, at the observed peak.
# Source: ref [40]. This is the one empirical input to the data-heavy case.
OBSERVED_IMAGE_SHARE = 0.10


def inscription_block_mb(payload_bytes: float) -> float:
    """Average block size (decimal MB) for a block full of inscription txs."""
    usable_wu = WEIGHT_LIMIT - BLOCK_OVERHEAD_WU
    n_tx = usable_wu / (TX_OVERHEAD_WU + payload_bytes)
    size_bytes = BLOCK_OVERHEAD_BYTES + n_tx * (TX_OVERHEAD_BYTES + payload_bytes)
    return size_bytes / 1e6


def mixed_payload_bytes(image_share: float) -> float:
    """Mean payload for a text/image inscription mix, by transaction count."""
    return ((1 - image_share) * BRC20_TEXT_PAYLOAD_B
            + image_share * IMAGE_PAYLOAD_B)


def inscription_regime_mb(image_share: float = OBSERVED_IMAGE_SHARE) -> float:
    """Average block size for an inscription-saturated regime at a given mix."""
    return inscription_block_mb(mixed_payload_bytes(image_share))


# The result saturates hard. Going from the observed 10% image share to 100%
# moves the block only 3.57 -> 3.95 MB, because per-transaction overhead stops
# mattering once payloads are large. So the data-heavy scenario does not depend
# on guessing a mix, and there is no room between it and the theoretical
# maximum for a further scenario.

# ── Maximum block size ───────────────────────────────────────────────
# A block approaches 4,000,000 serialized bytes as its contents approach pure
# witness data (one ~4 MB witness-stuffed transaction). Observed maxima sit
# just under 3.99 MB.

MAX_BLOCK_MB = 3.99


# ── The five scenarios ───────────────────────────────────────────────
# Three demand scenarios, one adversarial construction, one hard bound.
# Nothing else. 150, 196, 201 and 207 GB/yr were all either undocumented or
# reverse-engineered and have been removed.

SCENARIOS = {
    "monetary": {
        "label": "Monetary only",
        "avg_block_mb": 1.07,
        "basis": "No data-storage demand. Payments and settlement only.",
        "kind": "demand",
    },
    "current": {
        "label": "Current",
        "avg_block_mb": 1.69,
        "basis": "Current average block size. Observed.",
        "kind": "demand",
    },
    "peak": {
        "label": "March 2024 peak",
        "avg_block_mb": 2.29,
        "basis": "Highest monthly average on record. Observed, and it did not persist.",
        "kind": "demand",
    },
    "realistic_worst": {
        "label": "Realistic worst",
        "avg_block_mb": inscription_regime_mb(OBSERVED_IMAGE_SHARE),
        "basis": ("Blocks saturated with inscriptions at the observed 10% image "
                  "share. The composition is observed; the saturation is not. "
                  "No month has averaged above 2.29 MB."),
        "kind": "adversarial",
    },
    "theoretical_max": {
        "label": "Theoretical max",
        "avg_block_mb": MAX_BLOCK_MB,
        "basis": ("4,000,000 weight units of pure witness data at target block "
                  "cadence. A bound, not a demand forecast."),
        "kind": "bound",
    },
}

for _s in SCENARIOS.values():
    _s["gb_per_year"] = mb_to_gb_per_year(_s["avg_block_mb"])

# Convenience handles for models that want a bare number.
RATE_MONETARY = SCENARIOS["monetary"]["gb_per_year"]
RATE_CURRENT = SCENARIOS["current"]["gb_per_year"]
RATE_PEAK = SCENARIOS["peak"]["gb_per_year"]
RATE_REALISTIC_WORST = SCENARIOS["realistic_worst"]["gb_per_year"]
RATE_THEORETICAL_MAX = SCENARIOS["theoretical_max"]["gb_per_year"]

# Observed trajectory, measured directly from chain size rather than inferred
# from average block size. Kept separate from RATE_CURRENT because they answer
# different questions: this is what happened, RATE_CURRENT is what today's
# average block size implies going forward.
RATE_OBSERVED_SINCE_2023 = 80.0


def chart_label(key: str) -> str:
    """Two-line chart label. Fits the 15-char budget at 6.5pt."""
    s = SCENARIOS[key]
    return f"{s['label']}\n({s['gb_per_year']:.0f} GB/yr)"


if __name__ == "__main__":
    print(f"1 MB average block = {GB_PER_YEAR_PER_MB_BLOCK:.2f} GB/yr (decimal)\n")
    print(f"{'Scenario':<18} {'kind':<12} {'avg block':>10} {'GB/yr':>8}")
    print("-" * 52)
    for k, s in SCENARIOS.items():
        print(f"{s['label']:<18} {s['kind']:<12} "
              f"{s['avg_block_mb']:>7.2f} MB {s['gb_per_year']:>8.1f}")

    print(f"\nInscription regime saturates with image share:")
    for f in (0.0, 0.05, 0.10, 0.25, 0.50, 1.0):
        mb = inscription_regime_mb(f)
        print(f"  {f:>5.0%} images -> {mb:.2f} MB -> {mb_to_gb_per_year(mb):6.1f} GB/yr")
