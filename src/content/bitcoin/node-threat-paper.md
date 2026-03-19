---
title: "Quantifying Threats to Bitcoin Node Decentralisation"
subtitle: "Storage is the binding constraint"
date: "2025-03-09"
tags: ["bitcoin", "full-nodes", "decentralisation", "storage"]
status: "draft"
description: "Bitcoin's security model depends on ordinary users running full nodes. This paper quantifies four hardware constraints against a $300 computer lasting 10 years. Storage is the binding constraint, with a narrow margin between current trajectory and ceiling breach."
type: "paper"
---

## Abstract

Bitcoin's security model depends on ordinary users running full nodes to enforce consensus rules without trust. If the blockchain grows faster than commodity hardware improves, node operation becomes a privilege rather than a default, and this security model breaks down. This paper quantifies four hardware constraints (storage, UTXO/RAM, initial block download, and bandwidth) against a target of a $300 computer lasting 10 years: a minimum-viable hardware configuration. Storage is the binding constraint. The maximum chain growth rate that keeps a 2TB SSD viable within a decade is ~111 GB/year (after ext4 reserved blocks, OS overhead, and Bitcoin Core's disk safety margin). The current trajectory (~80 GB/year) passes. The worst case allowed by current consensus rules (~196 GB/year) does not. The peak already observed (118 GB/year, March 2024) exceeds the ceiling. The ceiling breaches at an average block size of 2.16 MB, 6% below the peak already observed. Block size grew 52% in the last two years. All models are standalone Python with no external dependencies and are published alongside this paper.

## 1. Introduction

At what point does chain growth make it impractical to run a Bitcoin full node?

Bitcoin operates as "a purely peer-to-peer version of electronic cash" [1] whose security depends on participants verifying transactions for themselves without trust. Satoshi understood the tension between chain growth and accessibility:

> "Bitcoin users might get increasingly tyrannical about limiting the size of the chain so it's easy for lots of users and small devices."
>
> Satoshi Nakamoto, December 10, 2010 [2]

The causal chain: chain growth > node cost growth > fewer nodes > centralisation > capture > (censorship, confiscation, debasement) > failure of Bitcoin's decentralised validation model.

This analysis measures four hardware constraints against a benchmark: a $300 computer lasting 10 years. The focus is archival full nodes on home hardware: the nodes that provide both bootstrapping capacity and the censorship resistance Bitcoin's security model requires.

The contributions of this work are:

1. Storage is the binding constraint, with a ceiling of ~111 GB/year.
2. The margin between current trajectory and ceiling breach is 28% of average block size.
3. Storage is the only constraint that is both operationally critical and irreversible.
4. The hardware improvement rates used (5-15%/year, decaying 2%/year) are conservative relative to Moore's Law (~41%/year) and Kryder's Law (~41-85%/year), anchored to observed post-2011 CAGR through two full shortage cycles.

This report does not prescribe protocol changes.

---

## 2. Background

This section defines the core concepts needed to follow the analysis. Readers familiar with Bitcoin's architecture can skip ahead.

**Full nodes.** A full node is software that independently validates every block and transaction against Bitcoin's consensus rules. It does not trust any other participant. Anyone running a full node can verify that no coins were created outside the issuance schedule, that no transaction spends coins it does not own, and that no rule has been broken. This independent verification is the mechanism by which Bitcoin's rules are enforced. A network where only miners validate is a network where miners set the rules.

**Archival vs pruned nodes.** An archival node stores the entire blockchain history (currently ~724 GB). A pruned node validates every block identically but discards old data after validation, keeping only ~10-15 GB. Pruned nodes depend on archival nodes for initial sync: without archival peers serving historical blocks, no new node (pruned or archival) can bootstrap. No protocol mechanism maintains a minimum density of archival nodes.

**The UTXO set.** The set of all unspent transaction outputs (UTXOs) is the database a node must consult for every transaction it validates. It currently contains ~169 million entries (~11 GB on disk). Performance depends on how much of this set the operating system can cache in RAM.

**Initial block download (IBD).** When a new node joins the network, it must download and validate the entire blockchain from genesis. This process, IBD, currently takes 2-3 days on mid-range hardware. As the chain grows, IBD takes longer, creating friction for new operators.

**Block weight and the witness discount.** Block size is measured in "weight units" (WU), capped at 4 million WU per block. Non-witness data (transaction structure, inputs, outputs) counts at 4 WU per byte. Witness data (signatures, proofs) counts at 1 WU per byte, a 75% discount. This discount means a block filled with witness-heavy data (like inscriptions) can reach ~4 MB, while a block of standard monetary transactions is typically 1.5-2 MB.

---

## 3. Methodology

### The metric: upgrade frequency

What matters is how often a node runner must replace hardware, not snapshot cost. Even if storage gets cheaper, if the blockchain grows faster, node runners face an upgrade treadmill: hardware purchased today becomes inadequate, requiring replacement. High upgrade frequency creates friction, and friction creates churn. Operators who face repeated upgrades stop running nodes.

Empirical anchor: the Raspberry Pi 4 lifecycle.

- 2022: The Pi 4 was the dominant budget node platform, recommended by nearly every community guide and pre-built node product.
- 2025: The Pi 4 is effectively disqualified [50] [51] [52]. IBD takes over a week, RAM is insufficient, and pre-built node products (Umbrel, RaspiBlitz) migrated to N100/N150 platforms [49].
- Observed cycle: ~3 years. The market rejected this upgrade frequency by abandoning the platform.

Consumer electronics reference points: smartphones last 3-4 years, PCs 5-7 years. A dedicated appliance should last longer. Working target: 10-year upgrade cycle.

### Target hardware: $300, grounded in what people actually buy

Rather than theorising about ideal price points, the analysis starts from what the market has converged on:

| Segment | Price range | Example |
|---|---|---|
| Pre-built (plug-and-play) | $399-599 | Umbrel Home, Start9, MyNode |
| DIY (technical hobbyist) | $200-270 | Pi 5 + NVMe, N100 mini-PC |
| Reuse (owns a PC) | $80-120 | Just add a 2TB SSD |

The market floor is $200-400. Below $200 is Pi 5 territory, already straining. Above $400 is comfortable pre-built territory.

$300 is already expensive globally. In developing nations it represents weeks to months of median income, and that's before import duties (20-30% in Nigeria, 30-40% in India, 50-65% in Argentina) push a $300 device to $375-465 locally. If running a node costs a month's income, those users default to trusting remote validators, the centralisation this analysis measures.

Independent measurement of Bitcoin's P2P network found Africa accounts for 0.3% of reachable nodes and South America for 1.0% [60]. The Global South is already largely absent from Bitcoin's validation infrastructure.

The reference machine: N100 mini-PC, 2TB NVMe SSD, 16 GB RAM. Currently available for ~$200-300. IBD rate: ~12 GB/hr (~2.5 days for the current 724 GB chain). Usable storage is modelled at 1,850 GB after ext4 reserved blocks (5%, 100 GB), OS/swap/logs (50 GB), and Bitcoin Core's low-disk shutdown margin (50 MB, acknowledged but too small to model).

Inflation is accounted for: all cost data in this study is nominal.

### Four constraints

Each constraint produces an independent ceiling: the maximum chain growth rate (GB/year) at which that constraint is not breached over the device's lifetime. The overall ceiling is the tightest.

| Constraint | What it limits | Checked against |
|---|---|---|
| Storage (disk) | Total chain size that fits on 2TB SSD | GB/year chain growth |
| IBD (processing) | Chain size processable in 7 days on target CPU | GB/year chain growth |
| Bandwidth | Chain downloadable in 7 days on residential internet | GB/year chain growth |
| UTXO/RAM | Chainstate that fits in available memory | Independent (entries/year) |

### Constraint taxonomy

Not all constraints threaten node viability equally.

| Constraint    | Category  | Urgency                        | Reversibility                                        | Priority                               |
| ------------- | --------- | ------------------------------ | ---------------------------------------------------- | -------------------------------------- |
| **Bandwidth** | Initiation | Not binding                    | Recoverable, internet growth dominates               | Low: permanently outpaced              |
| **IBD**       | Initiation | Adequate margin (base case)    | Recoverable via software gains                       | Monitor: structural tailwinds          |
| **UTXO/RAM**  | Initiation | Degrades IBD today, growing    | **Recoverable** via consolidation, hardware upgrades | Moderate: slows sync, does not stop it |
| **Storage**   | Operating  | Decade-scale, fills over years | **Irreversible**, the chain never shrinks            | Highest: act now, damage is permanent  |

The chain never shrinks; every byte on disk is permanent. Storage is the only constraint that can stop a node from working: the entire blockchain must fit on the machine to run Bitcoin.

This tension between block space cost and decentralisation is well recognised [53] [54] [55]. Money has always scaled in layers (gold to bank certificates to SWIFT to Visa). Bitcoin's scaling path is the same: a secure, trustless base layer with higher layers handling throughput [56].

---

## 4. Initiation time: factors that impact IBD time

A new node must download and validate the entire blockchain before it can be used. Several factors determine how long this takes. This section measures each one: how much headroom exists today, what threatens it, and the impact on IBD time as limits are approached.

### 4.1 Bandwidth

![](/figures/node-threat-paper/fig-bandwidth.png)

*Required IBD bandwidth vs residential internet supply. Model: `models/bandwidth/model.py`.*

Of the three bandwidth components a full node uses, only IBD download scales with chain growth. Tip-following requires ~3 KB/s (compact blocks, BIP 152). Peer serving requires ~2 Mbps. Neither is a constraint. IBD download requires ~9.8 Mbps for the current 724 GB chain in 7 days, rising to ~30 Mbps at worst case by year 10.

The global median is ~104 Mbps (Ookla, 2025) and rising at ~19% CAGR. The bandwidth ceiling only binds below ~27 Mbps, affecting ~10-20% of global broadband connections. For the ~3-5% below 10 Mbps (conflict states and rural ADSL), IBD already exceeds 7 days today, a current infrastructure gap, not a chain growth problem. Internet growth (~19%/year globally, 24-50%/year in developing nations per Cisco/Ookla) outpaces chain growth under all scenarios [48] [59].

#### Bandwidth verdict

Bandwidth is not a constraint for most of the world. Internet speeds (~19%/year growth) outpace chain growth under all scenarios. The ceiling only binds below ~27 Mbps, affecting 10-20% of global broadband connections. For the 3-5% below 10 Mbps, IBD already exceeds 7 days today. That is a current infrastructure gap, not a chain growth problem.

### 4.2 Chain size

![](/figures/node-threat-paper/fig-ibd.png)

*Chain size vs 7-day processing limit. Model: `models/ibd/model.py`.*

A node must download and validate every block from genesis, so twice the chain means roughly twice the sync time. Chain size is the dominant factor in how long IBD takes. What fills those blocks matters far less than how many bytes they contain.

#### Why composition barely matters

IBD has two phases. The AssumeValid phase covers everything except the last ~6 months, skipping signature verification. Its bottleneck is disk I/O (UTXO lookups), running at ~12 GB/hr on the N100. The full validation phase covers the final ~6 months, verifying all signatures. AssumeValid dominates: ~97% of the chain by size, ~90%+ of total sync time.

Under AssumeValid, block composition has minimal effect on sync time:

| Block type | Volume | Signature density |
|---|---|---|
| Inscription-heavy | Large (~2.9 MB avg) | Very low (~256 sigs/GB) |
| Monetary-heavy | Smaller (~1.1 MB avg) | High (~5M sigs/GB) |

Inscription blocks are bigger but have fewer signatures. Monetary blocks are smaller but signature-dense. Under AssumeValid, neither matters. Total sync time tracks chain size.

At year 10 on static hardware:

| Scenario | Chain size | Sync time |
|---|---|---|
| Monetary only (55 GB/yr) | 1,274 GB | 4.7 days |
| Current trajectory (80 GB/yr) | 1,524 GB | 5.6 days |
| Worst case (196 GB/yr) | 2,684 GB | 9.9 days |

#### A note on the 7-day threshold

Abandonment during IBD is driven by the gap between expected and experienced duration, not by absolute time. Someone told "up to two weeks" tolerates 10 days; someone who assumed overnight quits on day 2. Seven days is a Schelling point ("a week" is naturally salient) that also sits near the empirical performance floor of target hardware with tuning. It represents where even well-informed operators on adequate hardware face unreasonable friction, not a population average.

#### Processing ceiling vs storage ceiling

| Signature density | Processing ceiling (10yr, static) | Processing ceiling (10yr, +5%/yr SW) | Storage ceiling |
|---|---|---|---|
| Inscription-heavy (256/GB) | 117 GB/yr | 236 GB/yr | 111 GB/yr |
| Current mix (2.1M/GB) | 117 GB/yr | 236 GB/yr | 111 GB/yr |
| Full monetary (5.0M/GB) | 116 GB/yr | 234 GB/yr | 111 GB/yr |

The processing ceiling exceeds the storage ceiling under every scenario. The disk fills before sync time becomes the constraint.

#### Mitigations

AssumeUTXO is available in Bitcoin Core but requires manual opt-in (`loadtxoutset`). Most node operators do traditional IBD. If used, it downloads a UTXO snapshot (~11 GB), validates at tip immediately, then backfills historical validation in the background. Time-to-usable drops from days to hours. Full validation still runs; it just doesn't block the operator.

SwiftSync (proposed) could deliver 5x+ IBD speedup via parallel validation and batch signature verification [43]. Not yet deployed; treated as upside, not baseline.

Independent benchmarks show Bitcoin Core 30.0 syncing in 12h 7m on mid-range 2018 hardware, but "most clients took more than the expected 34% longer to sync" relative to chain growth [42]. A longitudinal study concludes that without software optimisations, Bitcoin would be "essentially dead," but warns the "rate of software improvement has been reduced in recent years" [23].

#### Verdict

Chain size does not bind through sync time. The disk fills before sync becomes the constraint.

### 4.3 UTXO set size

![](/figures/node-threat-paper/fig-utxo.png)

*UTXO chainstate growth scenarios vs available RAM. Model: `models/utxo/charts.py`.*

#### Current state

The UTXO set is what a full node must look up every time it validates a transaction: does this coin exist, and has it already been spent? Bitcoin Core stores this set on disk using LevelDB, a key-value database. The on-disk representation is called the chainstate and currently occupies ~11 GB.

RAM matters because of how the operating system handles disk reads. When a program reads from disk, the OS automatically keeps a copy of that data in any RAM not being used for something else. If the same data is needed again, the OS serves it from RAM instead of going back to disk. On a 16 GB machine with ~12 GB available after OS and application overhead, most of the 11 GB chainstate fits in RAM this way, without any special configuration.

When the chainstate grows past what RAM can hold, some lookups will need to read from disk instead of RAM. This is a speed issue, not a functionality issue. It matters most during IBD, where the node is processing hundreds of millions of historical transactions and every one requires a UTXO lookup. Benchmarks on identical hardware show that IBD with ~0.45 GB of RAM available for caching takes ~32% longer than IBD with the full dataset in RAM [42]: a measurable slowdown, but a smooth gradient, not a wall. Once a node has finished syncing and is just validating new blocks as they arrive (one block every ~10 minutes, a few thousand lookups), available RAM has no meaningful effect on performance. A node with 12 GB of RAM and a 24 GB chainstate will sync slower, but once synced it runs the same as any other node.

#### Growth scenarios

UTXO set growth depends on the transaction mix, specifically how many new UTXOs are created versus spent per year:

| Scenario | Net growth | Basis |
|---|---|---|
| Current | 5M entries/yr | Below organic; consolidation era or inscription decline |
| Realistic | 8M entries/yr | Organic rate (7M/yr observed 2020-2022) plus margin |
| Sustained stress | 20M entries/yr | Sustained inscription/token pressure (2024 rate) |

At 63 bytes per entry (empirically measured across two independent `gettxoutsetinfo` snapshots), these translate to ~0.3-1.2 GB/year of additional chainstate.

All scenarios push the chainstate past available RAM within the first hardware cycle. Even 5M/year reaches ~14 GB by year 10. The result is not node failure but progressively slower IBD as more UTXO lookups have to read from disk rather than RAM.

#### Adversarial growth

The chart models realistic scenarios up to 20M entries/year. The consensus maximum is far higher. A single block-filling transaction (1 P2TR input, ~23,253 P2TR outputs, 4M weight units) creates ~23,253 net UTXOs. At 144 blocks/day, sustained production would add ~1.2 billion entries per year, roughly 70 GB of chainstate growth.

At 1 sat/vB this costs ~$900 per block, ~$47M per year. For context, this is well beyond what any individual or commercial actor would sustain, but nation-state defence budgets routinely exceed $10 billion per year. A state actor motivated to degrade Bitcoin's onboarding infrastructure could sustain this cost indefinitely.

UTXO-worst blocks and storage-worst blocks cannot occur simultaneously. A block maximising UTXO creation is small (~1 MB, dominated by outputs with minimal witness data). A block maximising chain growth is large (~3.82 MB witness-heavy, up to ~4 MB for single-inscription blocks). An attacker must choose which constraint to stress.

#### Hardware upgrades restore headroom

RAM on $300 hardware has doubled per decade: 8 GB in 2016 to 16 GB in 2026. This rate (the base case) uses the worst decade for DRAM density growth ever observed. At year 10, a new $300 machine provides ~28 GB available for caching. Realistic chainstate at year 10 (~16 GB) fits comfortably. Headroom is restored.

But by mid-cycle (~year 15-17), the squeeze returns. The first generation is tight. The second is less so. After ~25 years, RAM growth dominates and UTXO/RAM stops being a problem.

#### UTXO composition and reversibility

Nearly half the UTXO set is non-monetary dust: 85M UTXOs (49.1%) hold less than 1,000 sats, overwhelmingly inscription pointers and BRC-20 mints [24]. UTXO count already declined from a 187.5M peak (January 2025) to ~167M (October 2025), the first sustained decline in Bitcoin's history.

This means the current chainstate size overstates the long-term problem. If inscription activity continues declining, the set shrinks on its own. Multiple mitigation paths exist beyond organic decline: Utreexo [45] would replace the full chainstate with a cryptographic accumulator under 1 KB [46] [47]; dust cleanup proposals would remove ~51M inscription UTXOs (~3 GB); hardware upgrades restore headroom each generation.

#### UTXO set verdict

UTXO set growth degrades IBD performance but does not prevent node operation. The chainstate sits near the edge of what $300 hardware can cache in RAM, and all growth scenarios push it past that point within a decade. The consequence is slower initial sync, not a broken node. The problem is real but recoverable, with multiple independent paths to resolution and no permanent damage to the network.

---

## 5. Storage: the binding constraint

![](/figures/node-threat-paper/fig-storage.png)

*Chain growth scenarios vs storage ceiling. Model: `models/storage/model.py`.*

### The ceiling: simple arithmetic

Given the target ($300 hardware, 10-year cycle), the ceiling is the maximum chain growth rate that keeps a 2TB SSD from filling up.

A "2TB SSD" provides 2,000 GB of raw capacity (SSDs are marketed in decimal GB, so no GiB conversion applies). Not all of it is available for Bitcoin data:

| Deduction | GB | Rationale |
|---|---|---|
| ext4 reserved blocks (5%) | -100 | Default root reservation (`tune2fs -m`); most users won't change it |
| OS + swap + logs | -50 | Ubuntu/Debian minimal + 4 GB swap + system journals |
| Bitcoin Core low-disk shutdown | ~0 | Core checks free space every 5 minutes and shuts down below 50 MB (`init.cpp`, `CheckDiskSpace`). Too small to model. |
| **Usable for Bitcoin data** | **1,850** | |

Current disk usage: 724 GB blockchain + 11 GB chainstate (UTXO set) = 735 GB total. Available: 1,115 GB.

The UTXO chainstate grows ~0.5 GB/year at organic monetary rates (8M entries/year). Small compared to chain growth, but subtracted from available space.

| Cycle | Available for chain growth | Chain growth ceiling |
|---|---|---|
| 10 years | ~1,110 GB | **~111 GB/year** |
| 8 years | ~1,115 GB | **~139 GB/year** |

This is the number the rest of the analysis checks against.

### Where current rules stand

Under current consensus rules (the block size limit is measured in "weight units" that give witness data a 75% discount, effectively capping blocks at ~4 MB for data-heavy content but ~1.5-2 MB for normal transactions), chain growth rate depends on the transaction mix:

| Scenario | Chain growth | Note |
|---|---|---|
| Monetary only | ~55 GB/year | No data-storage demand, just payments and settlement |
| Current trajectory | ~80 GB/year | Observed average since 2023 |
| Worst case | ~196 GB/year | Sustained inscription-heavy blocks (~3.82 MB avg, see derivation below) |

#### Block size depends on what fills the block

Every full block uses 4 million weight units. How many bytes that produces on disk depends on the content. Each inscription transaction carries 481 WU of fixed overhead: 94 bytes of non-witness structure (version, input, output, locktime) at 4 WU/byte, plus ~105 bytes of witness structure (Schnorr signature, Taproot control block, serialization flags) at 1 WU/byte. The rest is data payload at 1 WU/byte.

More transactions per block means more overhead, fewer bytes on disk per weight unit consumed. For N inscription transactions averaging D bytes of data: N = 3,999,108 / (481 + D), block size = 250 + N × (199 + D) bytes.

| Inscription mix | Avg data/tx | Txs/block | Block size |
|---|---|---|---|
| All BRC-20 text (~75 B) | 75 B | ~7,200 | ~2.0 MB |
| Observed peak (90% text, 10% images by count) | ~2.2 KB | ~1,500 | ~3.6 MB |
| Image-heavy (~73% text, ~27% images) | ~5.8 KB | ~635 | **~3.82 MB** |
| All images (21 KB mean) | 21 KB | ~186 | ~3.95 MB |
| Single inscription (Slipstream) | ~4 MB | 1 | ~4.0 MB |

Inscription size data: ~90% of inscriptions are BRC-20 text (~50-100 bytes); by bytes consumed, ~93% are images (~21 KB mean, up to 3.97 MB per inscription) [40].

BRC-20 mints cap out around 2 MB even at full weight because per-transaction overhead dominates at 75 bytes of payload. Images shift the balance. At the observed inscription peak, ~10% of inscriptions were images by count. Growing that share to ~27% gives ~3.82 MB, which produces 196 GB/yr of chain growth. This analysis uses 3.82 MB as the sustained worst case: a plausible escalation of observed demand. Individual blocks can approach 4 MB via Slipstream (3.97 MB observed), but sustained chain growth depends on the transaction mix across thousands of blocks.

A sustained wave of bulk data storage can push growth past the ceiling. Current consensus rules do not prevent this.

### The gap is narrow

The ceiling breaches at an average block size of 2.16 MB, just 6% below the peak already observed (March 2024, mempool.space). Block size went from 1.11 MB (pre-inscription, 2022) to 1.69 MB (current), a 52% increase in two years. Blocks have been full by weight (~99.6% of the 4M WU limit) since January 2023. What fills them determines how fast the average grows.

| Avg block size | Growth rate | Chain at year 10 | Disk margin | Context |
|---|---|---|---|---|
| 1.11 MB | 57 GB/yr | 1,294 GB | 540 GB | Pre-inscription baseline (2022) |
| 1.69 MB | 87 GB/yr | 1,591 GB | 243 GB | Current trajectory |
| **2.16 MB** | **111 GB/yr** | **1,834 GB** | **~0 GB** | **Ceiling breach** |
| 2.29 MB | 118 GB/yr | 1,899 GB | -65 GB | Observed peak (March 2024) |
| 2.75 MB | 141 GB/yr | 2,136 GB | -302 GB | Exceeds disk |
| 3.82 MB | 196 GB/yr | 2,680 GB | -892 GB | Sustained worst case (see derivation above) |

#### Findings (certain, given inputs)

The ceiling is 111 GB/yr. The current trajectory is ~80 GB/yr. Margin: 28% of average block size (from 1.69 MB to 2.16 MB). Block size grew 52% in two years (1.11 to 1.69 MB). Blocks have been full by weight since January 2023. Only the current trajectory survives the full 10-year cycle.

#### Risks (conditional on future behaviour)

A return to the March 2024 peak (2.29 MB average, 118 GB/yr) breaches the ceiling. This peak was observed once and lasted approximately one month. Whether it recurs depends on inscription demand, fee market dynamics, and out-of-band submission volume.

Sustained worst-case growth (~196 GB/yr, blocks filled with inscription data at ~3.82 MB average) would exhaust disk in ~5.7 years. This has never been observed for more than brief periods. The cost to an attacker is quantified in Section 5.1.

Multiple vectors of data demand are active. Each is a risk factor for sustained block size increase:

| Vector | Current status | Trend |
|---|---|---|
| Witness inscriptions (Ordinals) | Drove 1.1 → 1.7 MB avg block size [38] [39] [40] | Declining from peak but structurally enabled |
| OP_RETURN (Runes, etc.) | 4-6M/month, 80-byte limit removed in Core v30 [41] | Expanding |
| Out-of-band submission (Slipstream) | Bypasses 400 KB relay limit, single inscriptions up to 3.97 MB observed | Active |

The finding (ceiling exists, margin is narrow) is certain. Whether the margin is consumed depends on which of these vectors sustain or grow.

### Hardware trends: storage cost improvement rates

The model uses annual improvement rates of 5-15%, each decaying by 2% of itself per year. The optimistic scenario starts at 15% but falls to ~12.6% by year 10. These rates are well below Moore's Law (~41%/year for transistors) and Kryder's Law (~41-85%/year for disk density). Both of those broke. The model is anchored to observed SSD prices across two full shortage cycles, not theoretical scaling laws.

SSD cost history:

| Date     | $/GB                 | Source                            |
| -------- | -------------------- | --------------------------------- |
| 2011     | $2.00                | DigiPen University                |
| 2014     | $0.40                | DigiPen University                |
| 2019     | $0.15                | DigiPen University                |
| Jun 2023 | $0.05 (all-time low) | Tom's Hardware, StorageDiskPrices |
| Jan 2025 | $0.09                | StorageDiskPrices                 |
| Jan 2026 | $0.11                | Tom's Hardware SSD price index    |

NAND spot prices surged 5x from August 2025 to January 2026.

AI demand is driving the reversal. NAND wafer costs surged 246% in 2025 [3] as manufacturers shifted production to HBM and enterprise AI storage [4]. Phison's CEO confirmed all 2026 production is "already sold out," warned of a "pricing apocalypse throughout 2027" [31], and said the shortage could persist for a decade [32]. Price relief is not expected before 2027-2028 [34] [36] [37].

The reversal is structural, not cyclical. Every storage technology follows an S-curve, not an exponential. HDD areal density improvement slowed from ~39%/year (2000s) to ~7.6%/year (2009-2018) to effectively zero by 2015-2022 [8] [9] [10] [11]. NAND is earlier on its curve, but per-generation cost improvement is already decelerating: 10-15% at the 96-layer transition, dropping to ~5% at 128 layers [12]. 3D NAND is progressing toward 500+ layers [5] [6] [7], but per-generation cost reduction is diminishing.

Kryder's Law [13], the storage equivalent of Moore's Law, predicted HDD areal density would double every ~13 months. It broke around 2010-2014 [14]. By 2017, disk was 7x more expensive than the Kryder rate predicted; by 2020, the gap was 100-300x [15] [16]. The headline figure often cited for storage improvement (41%/year average since 1956) is dominated by two anomalous decades (1990s-2000s) that are over. The post-golden-era rate across storage paradigms converges to 7-15%/year [8], consistent with the three SSD-specific rates used here.

Satoshi's whitepaper invoked Moore's Law for block headers in RAM (Section 7) [1]. Moore's Law describes transistor density; Kryder's Law describes storage density. They are different phenomena, and Kryder's broke first. Neither is a physical law. Both are empirical trends bounded by the physics of their respective substrates.

Forward projection (from 2028, after current shortage). All rates decay 2%/year:

| Scenario    | Annual improvement | Anchored to                                          | Rationale                                                                          |
| ----------- | ------------------ | ---------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Optimistic  | 15%/year           | 2011-2026 compound annual growth rate / CAGR (17.6%) | AI shortage normalises, NAND scaling continues, but golden era (20%+) is over      |
| Base case   | 10%/year           | 2014-2026 CAGR (10.2%)                               | 12-year observed rate through two full shortage cycles; Wright's Law steady state  |
| Pessimistic | 5%/year            | 2019-2026 CAGR (4.3%)                                | Structural AI demand + NAND scaling diminishing returns + oligopoly margin capture |

*Price data compiled from DigiPen University SSD archive [17] (2010-2022) and StorageDiskPrices [18] (2020-2026), cross-validated against howmuch.one 1TB NVMe tracker [19].*

### The structural test: chain growth vs storage improvement

Chain growth is linear: a fixed number of GB added each year, permanently. Storage capacity per dollar compounds. As long as improvement rates stay positive, compound growth eventually outpaces linear growth, and each hardware generation starts with more headroom than the last. The chart above shows this across all three improvement scenarios.

The first hardware cycle is the tightest. At the base case (10%/yr), headroom roughly doubles by the second cycle. Even the pessimistic case (5%/yr) widens, just slowly enough that a sustained demand spike could force an upgrade before the 10-year target. The confidence behind these rates, and the scenarios that could break them, is examined in Section 6.

### Storage verdict

Current trajectory (~80 GB/yr) fits within a 10-year cycle on a 2 TB SSD. The risk is not that the disk fills under normal conditions, but that a sustained increase in block size (like the 118 GB/yr peak observed in March 2024) forces operators to upgrade sooner than the 10-year target. Current consensus rules permit block sizes that would shorten the cycle to ~5-6 years at worst case. The ceiling breaches at an average block size of 2.16 MB, 6% below the peak already observed.

### Pruned nodes don't relax the ceiling

The storage ceiling does not directly apply to pruned nodes. They validate every block but discard old data, keeping only ~10-15 GB on disk. IBD still hits them the same: a pruned node downloads and validates the entire chain from archival peers before discarding anything. No archival peers, no new pruned nodes. That is why this analysis focuses on archival.

### Potential mitigations

SeF (Secure Fountain architecture) [62] could reduce archival storage by ~1,000x using fountain codes, allowing nodes to store coded fragments instead of full blocks while preserving the ability to reconstruct any block on demand. SeF is not deployed. Unlike UTXO/RAM (where consolidation and hardware upgrades provide relief today) and IBD (where AssumeUTXO is already shipped), no shipping mechanism reduces chain size. The analysis is based on current implementations.

### 5.1 Attack surface: chain growth vectors

What does it cost to push chain growth past the 111 GB/yr ceiling?

The attacker's goal: sustain average block size above 2.16 MB. Three independent paths exist under current consensus rules. A fourth requires miner cooperation.

```
ROOT: Sustain avg block > 2.16 MB
├── [OR] Path 1: Witness inscription flooding
│   ├── Fill blocks with witness-heavy data (~3.82 MB sustained, ~4 MB single-tx max)
│   ├── Cost: ~1 sat/vB minimum relay fee
│   └── Requires: fee rate above competing monetary transactions
├── [OR] Path 2: OP_RETURN flooding
│   ├── Fill OP_RETURN outputs (no size limit post-Core v30)
│   ├── Cost: same fee market as Path 1
│   └── Note: OP_RETURN data is non-witness, counts 4x by weight.
│         Less efficient for chain bloat per sat spent.
├── [OR] Path 3: Out-of-band submission (Slipstream)
│   ├── Submit oversized transactions directly to cooperating miners
│   ├── Cost: mining fee + relationship/payment to pool operator
│   └── Bypasses: 400 KB relay limit, any mempool policy filter
└── [OR] Path 4: Miner self-stuffing
    ├── Miners fill their own blocks with junk witness data
    ├── Cost: opportunity cost of displaced fee-paying transactions
    └── Requires: miner willingness to sacrifice fee revenue
```

Cost to sustain each path (fee rates in sat/vB; USD at $100K/BTC for illustration):

| Path | Cost to fill one block | Cost per year (144 blk/day) | Chain growth if sustained | Damage |
|---|---|---|---|---|
| Witness inscription (~3.82 MB sustained) | 0.05 BTC at 5 sat/vB ($5,000) | ~2,628 BTC (~$263M) | ~196 GB/yr | Disk full in ~5.7 yr |
| Witness inscription (2.16 MB avg) | ~0.029 BTC at 5 sat/vB (~$2,900) | ~1,500 BTC (~$150M) | 111 GB/yr | Ceiling hit at year 10 |
| OP_RETURN (non-witness, 4x weight) | 0.05 BTC at 5 sat/vB ($5,000) | ~2,628 BTC (~$263M) | ~51 GB/yr | Below ceiling; 4x less efficient than witness |
| Out-of-band (max block) | Negotiated | Unknown | Up to 196 GB/yr | Bypasses all policy filters |
| Miner self-stuff | Opportunity cost only | Variable | Up to 196 GB/yr | No out-of-pocket cost |

At 5 sat/vB (low by 2024-2025 standards), sustaining the ceiling breach via witness inscriptions costs ~1,500 BTC/year (~$150M at $100K/BTC). Sustaining worst-case growth costs ~2,628 BTC/year (~$263M). These costs are within nation-state budgets but not trivial. They are orders of magnitude beyond commercial spam economics. The March 2024 spike was driven by commercial demand (BRC-20, image inscriptions), not an attacker, and still produced 118 GB/yr.

Paths 3 and 4 are harder to price but harder to mitigate. No relay policy stops a miner from including whatever they want in their own blocks. No standardness rule stops a transaction submitted directly to a pool via private API.

What the tree shows: the cheapest sustained attack on storage costs ~1,500 BTC/year (~$150M at $100K/BTC) and is fully permitted by current consensus rules. Policy-level filters (Knots defaults, relay limits) only block Paths 1-2. Paths 3-4 are unblockable without consensus changes. The ceiling is an economic question (is there enough demand or motivation to sustain 2.16 MB+ blocks?), not a technical one.

---

## 6. Stress-testing the storage outlook

Section 5 identifies storage as the binding constraint and models it as arithmetic: given a $300 budget, a 2TB SSD, and a 10-year cycle, the ceiling is 111 GB/year. That arithmetic is correct given its inputs. The inputs are not certain.

Three assumptions carry the weight of the analysis:

1. SSD technology is the relevant technology for the full forecast horizon. No successor arrives at consumer pricing.
2. The 2014-2026 observed improvement rate (~10%/year) is a reasonable predictor of the next decade and beyond.
3. Structural headwinds (AI demand competition, NAND oligopoly production control) are already reflected in the observed data.

If the paper is going to argue that storage is the bottleneck, and stake a position on how severe it is, these assumptions need stress-testing. This section attacks them from both directions.

### The optimist case

#### What about breakthroughs we can't predict?

The strongest version of the optimist argument goes beyond any specific technology. Kurzweil's Law of Accelerating Returns [66] explicitly covers storage and argues that paradigm shifts (tape to disk to flash) reset the improvement curve each time, maintaining a meta-exponential across all storage technologies. The McCallum dataset [67], tracking storage prices from 1956 to 2024, shows a ~41%/year average decline across 68 years and multiple paradigm shifts.

The argument is real. Each past transition delivered a discontinuous jump that the prior S-curve could not have predicted. But the 41% average is misleading. Two anomalous decades (the 1990s and 2000s) dominate it. Post-golden-era rates converge to 7-15%/year. Kurzweil's framework is not peer-reviewed and has no error bounds.

Nagy, Farmer, Bui, and Trancik [63] provide the missing piece. Testing six forecasting models against 62 technologies over decades, they found that forecasting error grows at ~2.5%/year (root of log error), regardless of whether paradigm shifts occurred. Over an 80-year horizon, this produces enormous uncertainty bands. Paradigm shifts have happened and will probably happen again. When and how much they deliver is not predictable. The uncertainty is the finding, not a limitation of it.

#### Could a new storage technology make current limits irrelevant?

Three candidates have serious institutional backing.

DNA storage has the densest theoretical ceiling: ~455 exabytes per gram, hundreds of millions of times denser than current SSDs by mass. The DNA Data Storage Alliance (a consortium including Microsoft, IBM, Dell, Samsung, and Lenovo) projects pilot systems within 3-5 years [69]. The market is growing at 78-88% CAGR. But Rosenthal's 2025 assessment [71] is blunt: "not within five years of market entry." A 2019 demonstration cost ~$10,000 to write and read 5 bytes over 21 hours. DNA storage is archival. It is not random-access.

Glass and ceramic storage are further along. Microsoft's Project Silica published a complete end-to-end system in Nature in February 2026 [70], writing terabytes per glass wafer with a lifespan exceeding 10,000 years. Rosenthal [71] calls it "probably having the best chance" among alternatives. The constraint is cost: femtosecond lasers start at ~$50,000, with limited scope for price reduction absent a mass-market laser application. Cerabyte's ceramic nano-memory targets 1 PB per rack at $1/TB, but that is rack-scale enterprise hardware, not a consumer drive.

The IEEE IRDS 2023 Mass Data Storage Roadmap [68] covers all emerging technologies. Its assessment: alternative memories (ReRAM, MRAM) remain niche, with no near-term NAND replacement anticipated.

None of these technologies targets a $50 consumer NVMe drive. A Bitcoin node needs cheap, fast, random-access storage. DNA is archival. Glass is archival. Ceramic is rack-scale. Denser does not mean cheaper. Archival does not mean random-access. Every emerging technology is designed for data centres first. Consumer trickle-down is not guaranteed and historically takes 8-20 years where it happens at all.

#### How often do paradigm shifts happen?

Counting all of computing history: tape, floppy, hard drive, optical, solid-state. Five or six transitions in roughly 60 years. Major shifts in consumer storage happen every 10-20 years, suggesting 4-8 more over an 80-year horizon. But the sample size is too small to model statistically.

Lafond et al. [64] resolve this. Their distributional forecasting method does not try to predict individual paradigm shifts. Instead, prediction intervals widen with the forecast horizon at a rate calibrated from the historical error distribution across 51 technologies. The possibility of paradigm shifts is captured in the widening error bands rather than predicted as discrete events. Acknowledge that transitions will probably happen, accept that timing is unpredictable, and let the uncertainty distribution do the work.

#### Does SSD technology still have room to improve on its own?

Yes. The path to 1,000 NAND layers exists via string-stacking [5], [6]. SK Hynix targets 400 layers by 2029-2031 [7]. The IEEE IRDS [68] projects die capacity from 2 TB (2025) to 8 TB (2029). Wikibon's Wright's Law analysis [65] found that flash production already exceeded HDD by volume (435 EB vs 310 EB in 2020), driving cost decline through manufacturing scale.

But more layers does not automatically mean cheaper storage. Per-layer cost improvement is already decelerating: 10-15% per additional layer at 96 layers, falling to ~5% at 128 layers [12]. The IEEE IRDS itself states that "SSD cost/bit will not become equal to or go below HDD cost/bit" [68]. IDC projects 13% CAGR for NAND bit price erosion through 2029 [34], consistent with the paper's base case but below the optimistic scenario.

Headroom in layers exists. Headroom in dollars-per-gigabyte is a different question, and the cost curve is flattening even as the technology advances.

### The pessimist case

#### Are we approaching physical limits?

No.

![](/figures/node-threat-paper/fig-bekenstein.png)

*Distance from fundamental physics limits on information density. Current commercial storage sits ~26 orders of magnitude below the Bekenstein bound.*

| Technology | Bits per cm3 | Distance from Bekenstein bound |
|---|---|---|
| Current HDD/SSD | ~10^9 to 10^12 | ~10^26x below |
| DNA storage (practical) | ~10^18 to 10^21 | ~10^17 to 10^20x below |
| Perfect atomic storage | ~10^22 to 10^25 | ~10^13 to 10^16x below |
| Bekenstein bound (1g, 1cm3) | ~10^38 | Theoretical maximum |

Twenty-six orders of magnitude of headroom. Current technology is at the starting line, not the finish.

The pessimist case does not rest on physics limits being close. It rests on economic and engineering constraints biting long before physics does. Every transition from one storage paradigm to the next requires a new manufacturing ecosystem, and those ecosystems take decades and billions of dollars to build. The gap between "physically possible" and "available at $50 retail" is where the real risk lives.

#### Will SSDs stall like hard drives did?

Maybe. This is the strongest pessimist argument, and it has precedent.

Rosenthal has spent 13 years modelling this scenario [72], [15], [16], [71]. Kryder's Law broke for hard drives around 2010-2014. By 2017, disk was 7x more expensive than the Kryder rate predicted. By 2020, 100-300x. HAMR has been "imminent for a decade" without reaching the volume market. Rosenthal's 2025 assessment [71]: "Technologies progress on S-curves and the only one that still has a lot of runway on the steep part is tape."

Where is NAND on that trajectory? The evidence is mixed. Layer counts are climbing rapidly (276 to 500+ projected by 2029). But per-layer cost improvement is decelerating, which is exactly the pattern that preceded the HDD plateau. Backblaze fleet data [11] shows what the S-curve flattening looks like in practice for HDD. If NAND follows with a 10-15 year lag, the SSD plateau arrives between 2025 and 2035.

Rosenthal's endowment model [72] uses a default "Kryder rate" of 10%/year for long-term storage cost decline. His central finding: "the effects of the unknowable future KryderRate are so large" that other model parameters are irrelevant. The entire long-term cost question reduces to one number. This matches our analysis: the storage verdict is insensitive to hardware budget, upgrade cycle, or usable space assumptions. It is almost entirely sensitive to the improvement rate.

#### Will AI demand keep driving prices up?

Consumer SSD prices doubled from $0.05/GB (June 2023) to $0.11/GB (January 2026) [4], [18], [31]. A demand shock, not a gradual trend correction.

AI training and inference infrastructure consumes NAND at accelerating rates. Demand is growing at ~40%/year while supply grows at 14-17% [33]. New fabrication capacity begins coming online in 2027-2028 [3], but the gap may not close quickly. The NAND oligopoly (Samsung, SK Hynix, Kioxia/WD, Micron) has demonstrated willingness to coordinate production cuts when prices fall [22].

No academic paper models the AI-demand-on-storage-cost interaction over multi-decade horizons. The data is too recent for peer-reviewed work to exist.

Within the Wright's Law framework [63], demand shocks are temporary. Higher demand increases cumulative production, which eventually drives costs down. But "eventually" can mean years, and during the transition consumer storage gets deprioritised when enterprise and AI buyers pay more per gigabyte. The question is whether this resembles the 2016-2017 NAND shortage (cyclical, resolved in 18 months) or a structural reallocation of manufacturing away from consumer price tiers.

The evidence so far looks more structural than cyclical. The 2016-2017 shortage was supply-driven (earthquake, factory conversion). The current one is demand-driven (AI) with simultaneous supply discipline (coordinated production cuts). That combination is harder to resolve.

#### What if better technology never reaches consumer pricing?

Rosenthal [71]: "The economics of archival storage only work at data-center scale." Project Silica requires $50,000+ lasers. DNA cost $10,000 for 5 bytes in 2019. Sony's OD-3 optical archival standard (1 TB per disk) was cancelled in 2023 for lack of a large enough market.

Lab-to-consumer timelines vary. Hard drives took roughly 10 years from mainframe to PC. SSDs took roughly 10 years from enterprise to consumer boot drive. Both transitions had mass-market pull: personal computers needed storage. A Bitcoin node operator buying a $50-100 NVMe drive sits at the bottom of every emerging technology's priority stack. Governments and enterprises buy first. Consumers get the surplus capacity years later, if at all.

Lafond et al. [64] quantify the uncertainty: forecast error grows with horizon. Confidence that any specific technology reaches consumer pricing decades out is inherently low. A technology can be physically demonstrated, institutionally backed, and commercially viable at enterprise scale, and still never reach the price point that matters for a home node operator.

### Revised base case

The stress test does not resolve the uncertainty. It maps it.

The optimist case is grounded in real evidence: paradigm shifts have happened, 26 orders of magnitude of physics headroom exist, and institutional R&D is active across multiple fronts. The pessimist case is equally grounded: HDD improvement did permanently stall, NAND shows early deceleration signs, AI demand is structural, and no emerging technology targets consumer pricing.

For the first hardware cycle (2026-2036), all sources converge. Our evidence base, Rosenthal's endowment model, the IEEE IRDS roadmap, and Wikibon's Wright's Law analysis all point to 8-12%/year SSD cost improvement. The paper's base case of 10%/year sits in the middle. This is the finding we are most confident in.

Beyond a single cycle, confidence drops fast. Lafond et al. [64] show that forecasting error in technology costs grows as a power law of the horizon. At 10 years, the prediction interval is manageable. At 30 years, it spans an order of magnitude. At 80, several.

| Scenario | Annual rate | 10-year multiplier | Probability | Basis |
|---|---|---|---|---|
| Stall | 0-2%/yr | 1.0-1.2x | ~10% | HDD precedent. NAND follows HDD S-curve to plateau, no successor at consumer pricing. |
| Pessimistic | ~5%/yr | 1.6x | ~25% | Current short-term trend (2019-2026 CAGR 4.3%). AI demand structural, per-layer deceleration continues. |
| Base | ~10%/yr | 2.6x | ~35% | Full-cycle CAGR (2014-2026, 10.2%). Near-term consensus across all sources. |
| Optimistic | ~15%/yr | 4.0x | ~20% | Secular CAGR (2011-2026, 17.6%). Requires return to pre-2020 manufacturing expansion. |
| Paradigm shift | 20%+/yr | 6.2x+ | ~10% | New storage technology reaches consumer pricing. Probable over 80 years, unpredictable over 10. |

These probabilities are informed estimates, not outputs of a statistical model. The Lafond distributional framework [64] produces continuous probability distributions rather than discrete scenarios. The table is a simplified communication tool. Probability mass clusters around the base case for the first cycle but spreads dramatically over longer horizons.

The cross-generational question remains open. If the base case holds, compound improvement outpaces linear chain growth and headroom widens each cycle. If the pessimistic or stall scenarios materialise, current trajectory becomes unsustainable after 2-3 hardware generations. Over an 80-year horizon, at least one paradigm shift is probable, but its timing and magnitude are not predictable.

The Section 5 verdict stands for a single hardware cycle: current trajectory fits on a 2TB SSD with margin. Whether storage is a long-term threat depends on a single variable (the annual improvement rate) that nobody can forecast with confidence beyond a decade.

---

## 7. Synthesis

Current trajectory (~80 GB/year) stays within all four resilience thresholds for a single hardware cycle. But the margin is narrow: a 28% increase in average block size breaches the storage ceiling, and block size already grew 52% in two years. Across hardware generations, compound storage improvement outpaces linear chain growth at all three modelled rates, and headroom widens each cycle. The risk is not gradual erosion but demand spikes: current consensus rules permit sustained block sizes that would force upgrades every 5-6 years instead of 10.

UTXO set growth degrades IBD performance progressively as less of the chainstate fits in RAM cache. This is a slowdown, not a wall: operators with less RAM take longer to sync but still complete it. Storage is the only constraint where the ceiling is absolute.

### What would change these findings

The storage ceiling (111 GB/yr) is arithmetic given the inputs. It breaks if any input is wrong:

- The target hardware is wrong. A $400 budget buys 4TB today. The ceiling doubles to ~222 GB/yr. Current worst case (196 GB/yr) passes.
- The upgrade cycle is wrong. At 8 years instead of 10, the ceiling rises to ~139 GB/yr. Current trajectory clears with margin. The March 2024 peak still breaches.
- Usable space is wrong. If users reclaim the 5% ext4 reservation (`tune2fs -m 1`), usable space rises to ~1,930 GB, ceiling to ~119 GB/yr. Small difference.

The cross-generational finding (chain growth outpaces storage improvement) breaks if SSD cost improvement sustains above ~15%/yr. This requires NAND scaling to return to pre-2020 rates despite the shift to AI/HBM production. Observable evidence against: NAND spot prices rising, manufacturer roadmaps prioritising HBM, per-layer cost improvement declining at higher layer counts.

The claim that storage is the binding constraint (not IBD or bandwidth) breaks if software optimisation stalls. The IBD ceiling exceeds the storage ceiling because of AssumeValid and expected software gains. If Bitcoin Core IBD performance degrades (benchmark: Lopp's annual tests [42]), IBD could bind first. Current trend is improvement, not degradation.

The claim about UTXO/RAM breaks if the current consolidation trend reverses and UTXO creation returns to 2024 rates (20M+/yr) indefinitely. Observable on-chain.

---

## 8. Discussion

### Limitations

This analysis models a single hardware configuration at a single price point. Operators willing to spend more ($500-1,000) gain years of additional headroom. The $300 target captures the minimum viable configuration, not the median operator. Results are sensitive to the assumed upgrade cycle: an 8-year cycle raises the storage ceiling to ~139 GB/year, which current trajectory clears with margin.

The models assume constant chain growth rates within each scenario. In practice, growth is episodic: inscription waves produce spikes (March 2024) followed by partial reversion. The realistic ramp scenarios partially address this, but sustained worst-case growth has not been observed.

UTXO/RAM projections depend on future transaction mix, which is driven by market behaviour and protocol changes that cannot be predicted. The analysis presents scenarios rather than forecasts.

### What this analysis does not cover

This paper measures the hardware burden of running a full node. It does not address:

- **Lightning Network capacity** and its effect on base-layer transaction demand
- **Fee market dynamics** and whether fee revenue can sustain mining security
- **Mining centralisation** and its implications for consensus capture
- **Software optimisation trajectories** beyond the IBD improvements already noted

Each of these interacts with chain growth but requires its own analysis.

### Implications

The narrow gap between current trajectory and ceiling breach means Bitcoin's node accessibility is sensitive to demand shocks. A sustained increase in data-heavy transactions, which current consensus rules permit, could push average block size past the 2.16 MB threshold. The March 2024 episode demonstrated this is not hypothetical.

The cross-generational finding (that chain growth outpaces storage improvement at base-case rates) suggests the problem does not resolve itself through hardware progress alone. Each successive hardware generation inherits a larger chain and starts with proportionally less margin.

### Future work

Empirical measurement of archival node density over time would test whether the modelled thresholds correlate with observed node attrition. The interaction between pruned node prevalence and archival node requirements warrants formal analysis. Extension of the storage model to incorporate periodic demand shocks (rather than constant rates) would improve predictive accuracy.

---

## 9. Related Work

The largest empirical study of Bitcoin's network decentralisation, Gencer et al. [59], measured bandwidth, latency, geography, and mining concentration across the P2P network. It established the measurement methodology for blockchain decentralisation research but did not measure the resource burden of running a full node: storage, RAM, IBD time, or their trajectories. The present work addresses that gap.

Wu [arXiv:2602.14372] examined Bitcoin infrastructure resilience from 2014 to 2025, focusing on network-level metrics (connectivity, latency, peer diversity). The two analyses are complementary: Wu measures the health of the network as it exists; this paper measures the conditions under which nodes cease to join it.

Croman et al. [FC 2016] identified throughput and bootstrap time as fundamental bottlenecks in decentralised blockchains. Their framework informs the constraint-based approach used here, though their analysis predated the inscription era and the NAND price reversal that makes storage the binding constraint.

Kiffer et al. [arXiv:2511.15388] measured P2P infrastructure across 36 cryptocurrencies, providing the node geographic distribution data cited in Section 3. Their finding that Africa and South America account for 1.3% of Bitcoin's reachable nodes supports the argument that $300 hardware is already exclusionary for much of the world.

Voskuil [56] formalises the theoretical basis: Bitcoin is "perfectly non-scalable" by design, and any increase in validation cost is a direct reduction in decentralisation. The present work quantifies what Voskuil describes in principle.

---

## 10. Contrary Positions

Two external sources challenge aspects of this analysis.

A graph-theory analysis argues that home full nodes are "neither critical nor operationally relevant for consensus propagation"; miners dominate the core relay graph [57]. This conflates consensus *propagation* (routing blocks through the network) with consensus *enforcement* (rejecting blocks that violate rules). Nodes enforce rules by refusing invalid blocks and transactions, not by routing them. A network where only miners validate is a network where miners set the rules.

Multiple sources note that pruned nodes reduce storage to ~1-5 GB while still validating all blocks [58]. Section 5 addresses this: pruned nodes still require archival peers for initial sync, no protocol mechanism maintains archival density, and the storage ceiling therefore binds the whole network [61].

### Objections to the target configuration

**"$300 is too low. Most node operators spend $400-600."**

Pre-built node products (Umbrel Home, Start9) sell for $399-599. At $500, current hardware buys a 4TB SSD. The ceiling doubles. The single-cycle finding disappears; the cross-generational finding (chain growth vs storage improvement) still holds at base-case rates.

But "raise the budget" is not an answer to the problem. It moves the line on the chart. It does not change the rate at which the chain fills the disk. Increasing required spend is the problem this paper measures. It cannot also be the solution.

The $300 target is deliberately conservative. $300 is already expensive globally: weeks to months of median income in developing nations, before import duties (20-30% in Nigeria, 30-40% in India, 50-65% in Argentina) push it to $375-465 locally. Africa accounts for 0.3% of reachable nodes and South America for 1.0% [60]. The Global South is already largely absent from Bitcoin's validation infrastructure. Raising the target to $500 answers "is there a problem for comfortable Western hobbyists?" No. It does not answer "is there a problem for the global network?"

**"10 years is too long. Nobody expects a dedicated appliance to last that."**

The Pi 4 cycle was ~3 years. The market rejected it. Consumer PCs last 5-7 years. A dedicated appliance with no moving parts and a single function should last longer. At 8 years, the ceiling rises to ~139 GB/yr and current trajectory passes with margin. At 7 years, ~159 GB/yr. The single-cycle finding is sensitive to this assumption. The cross-generational finding is not: even at 7-year cycles, each replacement machine inherits a larger chain.

**"Why archival? Pruned nodes validate identically."**

Pruned nodes depend on archival nodes to bootstrap. A new pruned node downloads the entire chain from archival peers, validates it, then discards history. Zero archival nodes means zero new nodes of any kind. No protocol mechanism maintains a minimum archival density. The storage ceiling binds archival nodes, and archival nodes are the bottleneck for network regeneration.

---

## 11. Conclusion

Storage is the binding constraint on Bitcoin full node viability. The maximum chain growth rate compatible with a $300 node lasting 10 years is ~111 GB/year. The current trajectory (~80 GB/year) fits within a single hardware cycle, but the margin is narrow (a 28% increase in average block size exhausts it) and the peak already observed exceeds it. Across hardware generations, compound storage improvement outpaces linear chain growth, and headroom widens each cycle. The threat is not gradual erosion but demand spikes: current consensus rules permit sustained block sizes that would shorten the upgrade cycle from 10 years to 5-6. The three other constraints examined (IBD, bandwidth, UTXO/RAM) are either not binding or recoverable through hardware upgrades and software improvement. Storage is the only constraint that is both operationally critical and irreversible.

---

## Appendix A: Evidence Chain

Evidence is ranked by type: (1) on-chain measurement, (2) controlled benchmark, (3) observed market data, (4) model output, (5) industry forecast/expert opinion. Claims resting on weaker evidence are flagged.

| Input | Evidence type | Refs | Status |
|---|---|---|---|
| Chain size (724 GB, March 2026) | On-chain measurement | [25], [61] | Established |
| Chainstate (11 GB, 169M entries) | On-chain measurement | [24] | Established |
| Bytes per UTXO entry (63) | On-chain measurement | [24] | Established |
| Block size and inscription impact | On-chain measurement | [38], [39], [40] | Established |
| OP_RETURN data trends | On-chain measurement | [41] | Established |
| UTXO composition and growth | On-chain measurement | [24], [45], [46], [47] | Established |
| IBD rate (12 GB/hr, N100) | Controlled benchmark | [42] | Established |
| Node density (archival vs pruned) | Network observation | [58], [61] | Established |
| Target hardware ($300) | Observed market data | [49], [60] | Contested (medium) |
| Upgrade cycle (10 years) | Observed market data + inference | [50], [51], [52] | Contested (medium) |
| SSD cost trend and improvement rates | Observed market data | [17], [18], [19], [34] | Established |
| SSD price reversal (2023-2026) | Observed market data | [4], [18], [31] | Established |
| Residential bandwidth trends | Observed market data | [48] | Established |
| HDD S-curve deceleration | Observed market data (historical) | [8], [9], [10], [11] | Established |
| Kryder's Law breakdown | Observed market data (historical) | [13], [14], [15], [16] | Established |
| NAND oligopoly coordination | Observed market data | [20], [21], [22] | Established |
| NAND scaling outlook | Industry forecast | [5], [6], [7], [12] | Established (trend), contested (timeline) |
| AI NAND shortage (2025-2028) | Industry forecast | [3], [31], [32], [34], [36], [37] | Established (current), contested (duration) |

The storage ceiling calculation (111 GB/yr) rests entirely on on-chain measurement and arithmetic. The claim that storage improvement will not outpace chain growth rests partly on industry forecasts about NAND scaling and AI demand. If those forecasts are wrong (NAND improvement returns to 20%+/yr), the cross-generational finding weakens but the single-cycle ceiling holds.

## Appendix B: Models

All models are standalone Python. No external dependencies except numpy/matplotlib for chart generation.

| Model | File | Constraint |
|---|---|---|
| Storage ceiling | `models/storage/model.py` | Storage (disk) |
| IBD two-phase | `models/ibd/model.py` | IBD (processing) |
| Bandwidth | `models/bandwidth/model.py` | Bandwidth |
| UTXO/RAM | `models/utxo/charts.py` | UTXO set / RAM |

---

## References

[1] Nakamoto, S. "Bitcoin: A Peer-to-Peer Electronic Cash System." 2008. https://bitcoin.org/bitcoin.pdf

2] Nakamoto, S. "Re: BitDNS and Generalizing Bitcoin." BitcoinTalk, December 10, 2010. https://satoshi.nakamotoinstitute.org/posts/bitcointalk/threads/244/#246

[3] TrendForce. "NAND Flash Q1 2026 price forecast." January 2026. https://www.trendforce.com/presscenter/news/20260105-12860.html

[4] Tom's Hardware. "Perfect storm of demand and supply driving up storage costs." 2025. https://www.tomshardware.com/pc-components/storage/perfect-storm-of-demand-and-supply-driving-up-storage-costs

[5] Semi Engineering. "NAND Flash Targets 1,000 Layers." https://semiengineering.com/nand-flash-targets-1000-layers/

[6] Lam Research. "1,000 Layers NAND Etch." https://newsroom.lamresearch.com/1000-layers-NAND-etch

[7] TrendForce. "SK Hynix Unveils 2029-2031 Roadmap Featuring HBM5, GDDR7 Next, and 400-Layer NAND." November 2025. https://www.trendforce.com/news/2025/11/04/news-sk-hynix-unveils-2029-2031-roadmap-featuring-hbm5-gddr7-next-and-400-layer-nand/

[8] National Academies of Sciences, Engineering, and Medicine. "Decadal Survey of Astronomy and Astrophysics 2020 (Astro2020): Data, Computing, and the Evolving Cyberinfrastructure." National Academies Press, 2024. https://www.nationalacademies.org/read/27445/chapter/3

[9] StorageNewsletter. "Has HDD Areal Density Stalled?" April 2022. https://www.storagenewsletter.com/2022/04/19/has-hdd-areal-density-stalled/

[10] Computer History Museum. "HDD Areal Density Reaches 1 Terabit/sq. in." https://www.computerhistory.org/storageengine/hdd-areal-density-reaches-1-terabit-sq-in/

[11] Backblaze. "Hard Drive Cost Per Gigabyte." https://www.backblaze.com/blog/hard-drive-cost-per-gigabyte/

[12] Semi Engineering. "3D NAND Race Faces Huge Tech and Cost Challenges." https://semiengineering.com/3d-nand-race-faces-huge-tech-and-cost-challenges/

[13] Scientific American. "Kryder's Law." https://www.scientificamerican.com/article/kryders-law/

[14] The Register. "Kryder's Law of Ever-Cheaper Storage Disproven." November 2014. https://www.theregister.com/2014/11/10/kryders_law_of_ever_cheaper_storage_disproven/

[15] Rosenthal, D. "Patting Myself on the Back." DSHR's Blog, July 2017. https://blog.dshr.org/2017/07/patting-myself-on-back.html

[16] Rosenthal, D. "Storage Media Update." DSHR's Blog, November 2020. https://blog.dshr.org/2020/11/storage-media-update.html

[17] Mead, M. "RAM/HDD/SSD Prices." DigiPen Institute of Technology. https://azrael.digipen.edu/~mmead/www/Courses/CS180/ram-hd-ssd-prices.html

[18] StorageDiskPrices. "SSD Price History." https://storagediskprices.com/ssd-price-history/

[19] howmuch.one. "Average SSD 1TB NVMe Price History." https://howmuch.one/product/average-ssd-1tb-nvme/price-history

[20] TrendForce. "NAND Flash Revenue, Q3 2025." December 2025. https://www.trendforce.com/presscenter/news/20251203-12813.html

[21] Mordor Intelligence. "NAND Flash Memory Market." https://www.mordorintelligence.com/industry-reports/nand-flash-memory-market

[22] TrendForce. "NAND Giants Reportedly Cut Output in 2H25 as Prices Surge." November 2025. https://www.trendforce.com/news/2025/11/13/news-nand-giants-reportedly-cut-output-in-2h25-as-prices-surge-samsung-mulls-20-30-hike-in-2026/

[23] BitMEX Research. "Bitcoin's Initial Block Download." https://www.bitmex.com/blog/bitcoins-initial-block-download

[24] Mempool Research. "UTXO Set Report." April 2025, block 892,385. https://research.mempool.space/utxo-set-report/

[25] CoinLedger. "Bitcoin Blockchain Size and Growth Over Time." 2025. https://coinledger.io/research/bitcoin-blockchain-size-and-growth-over-time

[26] Bacloud. "Running Bitcoin Full Node Requirements 2025 (Updated)." https://www.bacloud.com/en/knowledgebase/204/running-bitcoin-full-node-requirements-2025-updated.html

[27] MDPI Applied Sciences. "Comprehensive review of blockchain scalability bottlenecks." 2025. https://www.mdpi.com/2076-3417/15/1/243

[28] ACM Computing Surveys. "Blockchain storage optimisation techniques." 2024. https://dl.acm.org/doi/10.1145/3645104

[29] 101 Blockchains. "Blockchain Size." https://101blockchains.com/blockchain-size/

[30] Traders Union. "Bitcoin Growing Block Size." 2025. https://tradersunion.com/news/editors-picks/show/79597-bitcoin-growing-block-size/

[31] Tom's Hardware. "Phison CEO confirms NAND prices have more than doubled." January 2026. https://www.tomshardware.com/pc-components/ssds/phison-ceo-confirms-nand-prices-have-more-than-doubled-and-will-continue-to-rise-all-2026-production-already-sold-out-ssds-facing-pricing-apocalypse-throughout-2027

[32] Tom's Hardware. "Phison CEO claims NAND shortage could last a staggering 10 years." https://www.tomshardware.com/pc-components/ssds/phison-ceo-claims-nand-shortage-could-last-a-staggering-10-years-says-memory-supercycle-imminent-and-severe-2026-shortages-are-at-hand

[33] Oreton Storage. "Global NAND Supply Update Q4 2025." https://oretonstorage.com/blog/global-nand-supply-update-q4-2025-whats-shaping-ssd-prices-ahead

[34] IDC. "Global Memory Shortage Crisis: Market Analysis." 2026. https://www.idc.com/resource-center/blog/global-memory-shortage-crisis-market-analysis-and-the-potential-impact-on-the-smartphone-and-pc-markets-in-2026/

[35] Yahoo Finance. "NAND Flash Memory Market Outlook." https://finance.yahoo.com/news/nand-flash-memory-market-outlook-095700880.html

[36] OSCOO. "Will SSD Prices Drop in 2026?" https://www.oscoo.com/news/will-ssd-prices-drop-in-2026/

[37] NAND Research. "Memory Flash Crisis Update, March 2026." https://nand-research.com/memory-flash-crisisc-update-march-2026/

[38] JBBA. "Bitcoin Ordinals and Inscriptions: An Analysis of Bitcoin's Evolving Network Dynamics." 2024. https://jbba.scholasticahq.com/api/v1/articles/153840-bitcoin-ordinals-and-inscriptions-an-analysis-of-bitcoin-s-evolving-network-dynamics.pdf

[39] ScienceDirect. "Bitcoin Ordinals: Determinants and impact on total transaction fees." 2024. https://www.sciencedirect.com/science/article/abs/pii/S0275531924001314

[40] CryptoSlate. "Data on Taproot Ordinals points to higher Bitcoin fees, chain bloat." 2023. https://cryptoslate.com/data-on-taproot-ordinals-points-to-higher-bitcoin-fees-chain-bloat/

[41] CoinDesk. "Bitcoin Core 30 to Increase OP_RETURN Data Limit." 2025. https://www.coindesk.com/tech/2025/06/10/bitcoin-core-30-to-increase-op_return-data-limit-after-developer-debate-concludes

[42] Lopp, J. "2025 Bitcoin Node Performance Tests." https://blog.lopp.net/2025-bitcoin-node-performance-tests/

[43] Somsen, R. "SwiftSync: Speeding Up IBD with Pre-generated Hints." Delving Bitcoin, 2025. https://delvingbitcoin.org/t/swiftsync-speeding-up-ibd-with-pre-generated-hints-poc/1562

[44] Bitcoin Optech. "AssumeUTXO." https://bitcoinops.org/en/topics/assumeutxo/

[45] Dryja, T. "Utreexo: A dynamic hash-based accumulator optimized for the Bitcoin UTXO set." ePrint 2019/611. https://eprint.iacr.org/2019/611.pdf

[46] Bitcoin Magazine. "Bitcoin's Growing UTXO Problem and How Utreexo Can Help Solve It." https://bitcoinmagazine.com/technical/bitcoins-growing-utxo-problem-and-how-utreexo-can-help-solve-it

[47] IEEE GLOBECOM. "Prediction-based UTXO Cache Optimization for Bitcoin Lightweight Full Nodes." 2021. https://ieeexplore.ieee.org/document/9685843/

[48] Lopp, J. "Revisiting Bitcoin Network Bandwidth Issues." 2023. https://blog.lopp.net/revisiting-bitcoin-network-bandwidth-issues/

[49] Athena Alpha. "Best Bitcoin Node Hardware." 2024. https://www.athena-alpha.com/bitcoin-node-hardware/

[50] Start9 Community. "Raspberry Pi no longer recommended for use with Bitcoin stack." https://community.start9.com/t/raspberry-pi-no-longer-recommended-for-use-with-bitcoin-stack/779

[51] Stacker News. "Nobody should suggest using a Raspberry Pi for running a Bitcoin node in 2023." https://stacker.news/items/186832

[52] The Bitcoin Manual. "Migrating BTC Pi Node." https://thebitcoinmanual.com/articles/migrating-btc-pi-node/

[53] Lopp, J. "A Treatise on Bitcoin Block Space Economics." 2024. https://blog.lopp.net/treatise-bitcoin-block-space-economics/

[54] Buterin, V. "Some reflections on the Bitcoin block size war." May 2024. https://vitalik.eth.limo/general/2024/05/31/blocksize.html

[55] Blockonomi. "Full Nodes & Block Size: Keeping Validation Costs Low." https://blockonomi.com/full-nodes-block-size-keeping-validation-costs-low-in-bitcoin/

[56] Voskuil, E. "Scalability Principle." Cryptoeconomics, libbitcoin wiki. https://github.com/libbitcoin/libbitcoin-system/wiki/Scalability-Principle

[57] "The Redundancy of Full Nodes in Bitcoin." arXiv:2506.14197. June 2025. https://arxiv.org/abs/2506.14197

[58] D-Central. "Understanding the Role of Archival and Pruned Nodes in the Decentralization of Bitcoin." https://d-central.tech/understanding-the-role-of-archival-and-pruned-nodes-in-the-decentralization-of-bitcoin/

[59] Gencer, A.E., Basu, S., Eyal, I., van Renesse, R., Sirer, E.G. "Decentralization in Bitcoin and Ethereum Networks." FC 2018. arXiv:1801.03998. https://arxiv.org/abs/1801.03998

[60] Kiffer, L., Salman, A., Levin, D., Mislove, A., Nita-Rotaru, C. "36 Coins: Measuring P2P Network Structure and Health." SIGMETRICS 2026. arXiv:2511.15388. https://arxiv.org/abs/2511.15388

[61] Bitnodes. "Reachable Bitcoin Nodes." Snapshot March 2026. https://bitnodes.io/nodes/

[62] Kadhe, S., Chung, J., Ramchandran, K. "SeF: A Secure Fountain Architecture for Slashing Storage Costs in Blockchains." arXiv:1906.12140. 2019. https://arxiv.org/abs/1906.12140

[63] Nagy, J.B., Farmer, J.D., Bui, Q.M., Trancik, J.E. "Statistical Basis for Predicting Technological Progress." PLoS ONE 8(2): e52669, 2013. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0052669

[64] Lafond, F., Bailey, A.G., Bakker, J.D., Rebois, D., Zadourian, R., McSharry, P., Farmer, J.D. "How Well Do Experience Curves Predict Technological Progress? A Method for Making Distributional Forecasts." Technological Forecasting and Social Change 128: 104-117, 2018. https://arxiv.org/abs/1703.05979

[65] Floyer, D. "SSDs Will Crush Hard Drives." Wikibon / Blocks & Files, January 2021. https://blocksandfiles.com/2021/01/25/wikibon-ssds-vs-hard-drives-wrights-law/

[66] Kurzweil, R. "The Singularity Is Near: When Humans Transcend Biology." Viking, 2005.

[67] McCallum, J.C. "Disk Drive Prices (1955-2024)." https://jcmit.net/diskprice.htm

[68] IEEE International Roadmap for Devices and Systems. "Mass Data Storage." 2023. https://irds.ieee.org/images/files/pdf/2023/2023IRDS_MDS.pdf

[69] DNA Data Storage Alliance (SNIA). "DNA Data Storage Technology Landscape." 2025.

[70] Microsoft Research. "Project Silica: Storing Data in Glass." Nature, February 2026. doi: 10.1038/s41586-025-10042-w

[71] Rosenthal, D. "Archival Storage." DSHR's Blog, March 2025. https://blog.dshr.org/2025/03/archival-storage.html

[72] Rosenthal, D. "An Economic Model of Long-Term Digital Storage." UNESCO Memory of the World Conference, 2012. https://www.fsl.cs.sunysb.edu/docs/unesco12/UNESCO2012-storage-econ.pdf
