---
title: "BIP: Witness Discount Cap"
subtitle: "Cap the witness discount at 350 bytes per input"
date: "2025-03-07"
tags: ["bitcoin", "bip", "witness-discount", "soft-fork"]
status: "draft"
description: "This proposal caps Bitcoin's witness discount at 350 bytes per input — the minimum that covers every standard signature construction. Witness data beyond the threshold pays full price, correcting a gap where the discount's cost-proportional pricing goal fails for large witness data."
type: "bip"
---

## Abstract

This proposal caps Bitcoin's witness discount at 350 bytes per input, the minimum that covers every standard signature construction. Witness data beyond the threshold pays full price (4 WU/byte), correcting a gap where the discount's cost-proportional pricing goal fails for large witness data while preserving both original design goals for all signature data. No small-witness transaction (≤350 witness bytes per input) is affected.

## Copyright

This BIP is licensed under the Creative Commons CC0 1.0 Universal license.

## Motivation

### The discount's purpose

Two design goals emerge from the rationale given by the architects of BIP-141 [1]:

**1. Price data in proportion to its cost on the network.** The architects identified two properties that make witness data cheaper for nodes than non-witness data. Non-witness data (outputs) creates UTXO entries that every full node must hold in memory until spent. Witness data does not enter the UTXO set, and it can be pruned after validation. Pieter Wuille, presenting the discount at Scaling Bitcoin Hong Kong [13]: "The reason for doing this discount is that it disincentivizes UTXO impact. A signature that doesn't go into the UTXO set, can be pruned." The Bitcoin Core project description [2]: "making signature data, which does not impact the UTXO set size, cost 75% less than data that does." The primary cost variable was UTXO set impact. Prunability reinforced the case: data that can be discarded after validation is cheaper to carry long-term than data that must be held in memory indefinitely.

**2. Make spending UTXOs more affordable to encourage and enable consolidation.** Spending a UTXO requires witness data (a signature). Creating a UTXO requires none. Before SegWit the create/spend cost ratio was approximately 1:4.5; spending was so much more expensive than creating that users had little reason to consolidate. The discount shifted the ratio to approximately 1:2 [12], halving the penalty. Andrew Chow [3]: "The primary idea behind the discounts are to incentivise wallets to manage change differently and clean up the UTXO set."

A 66-byte Schnorr signature meets both design goals. It does not enter the UTXO set and can be pruned after validation (goal 1). Discounting it makes spending more affordable, encouraging consolidation (goal 2).

### The incomplete variable

Goal 1 rests on two properties: UTXO set avoidance and prunability. Both are binary. Data is either in the UTXO set or it is not. Data is either prunable or it is not. Neither property scales with size. The discount does not account for size.

A 20,000-byte data payload and a 66-byte Schnorr signature both avoid the UTXO set. Both can be pruned after validation. But pruning only saves disk space after the fact. Every witness byte must be downloaded during initial block download, relayed on every block, and stored by archival nodes regardless of whether it is later pruned. The network cost of downloading, storing, and relaying 20,000 witness bytes is not 75% less than 20,000 non-witness bytes. No protocol mechanism maintains a minimum density of archival nodes, and as they decline, the network's ability to onboard new validators degrades.

Testing goal 1 against large witness data: UTXO set avoidance holds (large witness data does not enter the set), but the cost-proportionality claim fails. The discount gives 20,000 bytes the same 75% subsidy as 66 bytes, despite the network cost scaling linearly with size.

Goal 2 is unaffected. Every standard signature construction fits within the threshold. The cap corrects for the incomplete variable in goal 1 while preserving both original design goals for all signature data.

### The pricing distortion

A transaction imposes two kinds of cost on node operators. UTXO set growth is one: non-witness data creates entries that every full node must hold in RAM until spent. Storage is the other: every byte of a transaction, witness or not, must be downloaded during initial block download, relayed to peers, and written to disk. The discount accounts for the first cost but not the second. A 66-byte signature avoids the UTXO set and adds so little to storage that the 75% discount is a reasonable approximation of its reduced burden on nodes. A 20,000-byte witness payload also avoids the UTXO set, but it adds the same storage, bandwidth, and IBD burden as 20,000 non-witness bytes. The discount treats both the same because the only variable it checks, UTXO set impact, is binary. Size is not part of the formula.

This produces a distortion in the fee market. A transaction fee should reflect what that transaction costs the nodes that carry it. Under current rules, 20,000 witness bytes cost 20,000 WU while 20,000 non-witness bytes cost 80,000 WU, even though both impose the same physical burden on every node that downloads, stores, and relays them. The fee signal is wrong by a factor of four, and because the cheapest way to consume block space is to place data in the witness, the discount acts as a subsidy on storage consumption for anyone willing to use witness space at scale.

The discount was calibrated for signatures. At signature scale the UTXO set cost dominates and the storage cost is negligible, so the 75% reduction is justified. At 20,000 bytes storage is the dominant cost and the UTXO set benefit is irrelevant to the price the network bears. Capping the discount at 350 bytes per input limits the subsidy to the range where the calibration holds and restores fee-market neutrality above that range. Signature data keeps its discount because the original cost rationale still applies. Data beyond any signature construction pays the same rate as every other byte on the network, because at that scale, the cost to nodes is the same.

### The consequence

Worst-case chain growth under current rules is ~196 GB per year (worst-case blocks average ~3.82 MB x 52,560 blocks/year) [11]. Higher chain growth forces more frequent hardware upgrades on node operators, shrinking the validator set over time. The ~3 MB worst case under this proposal remains three times the pre-SegWit 1 MB limit.

## Design

### Goal

Ensure worst-case chain growth remains within the capacity of commodity hardware to run a full node over multi-generational upgrade cycles, while preserving the incentive to consolidate UTXOs.

Constraint analysis across storage, bandwidth, IBD, and UTXO/RAM [11] identifies storage as the binding constraint, with a narrow margin between current trajectory and ceiling breach. This proposal reduces worst-case chain growth from ~196 GB/year to ~154 GB/year.

Bitcoin should also remain accessible to the widest possible population, including people for whom commodity hardware is already a stretch. That is a value judgment. The engineering case stands without it, but it informs the design: when the threshold can be set generously for small-witness transactions without conceding the rate-limiting effect, set it generously.

### Consensus vs policy

The witness discount is a consensus-level pricing rule. Policy-level corrections (mempool filtering, relay rules) cannot override it: any miner can include transactions that policy nodes reject. Correcting the formula requires a consensus change.

### Status quo projection

Blocks have been full by weight (~99.6% of the 4M WU limit) since January 2023. What fills them determines chain growth.

| Scenario | Chain growth | Avg block size |
|---|---|---|
| Small-witness only | ~55 GB/year | ~1.1 MB |
| Current trajectory | ~80 GB/year | ~1.69 MB |
| Observed peak (March 2024) | ~118 GB/year | ~2.29 MB |
| Worst case (current rules) | ~196 GB/year | ~3.82 MB |

Average block size grew 52% in two years (1.11 to 1.69 MB). The storage ceiling for a $300 node lasting a decade is ~111 GB/year [11]. The ceiling breaches at 2.16 MB average block size, 6% below the peak already observed.

With this proposal, worst-case chain growth drops to ~154 GB/year. The current trajectory (~80 GB/year) is unchanged. The ceiling can still be exceeded under sustained data pressure, but not by the margins current rules allow.

### The per-input threshold

For each transaction input, the first 350 bytes of witness data retain the existing BIP-141 discount (1 weight unit per byte). All witness data beyond 350 bytes per input pays full price (4 weight units per byte), the same cost as non-witness data. The block weight limit is unchanged at 4,000,000 WU.

Small-witness transactions fit within 350 bytes. The threshold prices data by size, not content. The fee market does the rest. One parameter (discount threshold per input), one consensus rule change. No new validation logic, no ongoing maintenance.

The threshold applies only to witness data. Non-witness data (inputs, outputs, amounts, scripts) is unaffected. It always costs 4 WU/byte, same as today. The two are priced independently. For example: a transaction input with 300 bytes of non-witness data and 300 bytes of witness data pays 300 × 4 = 1,200 WU for the non-witness portion and 300 × 1 = 300 WU for the witness portion (all within the 350-byte threshold). The non-witness data is never subject to the threshold and the witness data is never subject to the non-witness rate unless it exceeds 350 bytes.

Standard transaction types by witness size [6][7][8] and on-chain input share:

| Transaction type | Witness bytes/input | Input share | Cumulative | Within 350? |
|---|:-:|:-:|:-:|:-:|
| P2TR key-path (Schnorr single-sig) | 65–66 | ~60% | ~60% | Yes |
| P2WPKH (legacy SegWit single-sig) | 107–109 | ~30% | ~90% | Yes |
| P2WSH 2-of-2 (Lightning) | ~220 | ~5% | ~95% | Yes |
| P2WSH 2-of-3 multisig | ~254 | ~2% | ~97% | Yes |
| MuSig2 (n-of-n via Taproot) | 65–66 | ~1% | ~98% | Yes |
| P2TR script-path (minimal) | ~135 | <1% | >98% | Yes |
| P2TR HTLC-timeout (Taproot Lightning) | ~196 | <1% | >99% | Yes |
| P2WSH HTLC-success (legacy Lightning) | ~324 | <1% | >99% | Yes |
| **── 350-byte threshold ──** | | | **>99%** | |
| P2WSH 3-of-5 multisig | ~395 | <0.1% | >99.9% | 45 excess bytes |
| P2WSH 3-of-6 multisig | ~429 | <0.01% | >99.99% | 79 excess bytes |

The largest standard signature construction (P2WSH HTLC-success in legacy Lightning) is ~324 bytes. 350 covers it with margin. Lower (285) would partially reprice Lightning HTLCs, handing critics the objection that sinks consensus proposals. Higher (500) would extend the discount to data not serving the UTXO incentive. Constructions above 350 bytes pay full price, including large signature schemes, creating pressure toward Schnorr, MuSig2, and FROST.

![Threshold tradeoff chart](/figures/bip-witness-discount-cap/threshold_tradeoff.png)
*Coverage vs leakage at 350 bytes. Left: standard transaction types by input share. Right: percentage of a 20,000-byte witness payload that retains the discount at each threshold. The gap between the two is the design margin: every standard type is covered while large witness data retains less than 2% of its discount.*

### Effect on large witness data

Any witness data exceeding 350 bytes per input pays full price on the excess. The cost increase depends on size. A 500-byte witness sees a minor increase. A 20,000-byte witness payload sees ~4x:

| Threshold | Discounted bytes | Full-price bytes | Effective cost increase |
|---|:-:|:-:|:-:|
| 285 | 285 (1.4%) | 19,715 (98.6%) | 3.96x |
| 350 | 350 (1.8%) | 19,650 (98.2%) | 3.95x |
| 500 | 500 (2.5%) | 19,500 (97.5%) | 3.93x |

The threshold choice is insensitive to the rate-limiting effect: between 285 and 500, the cost increase varies by 0.03x. The threshold can be set generously for small-witness transactions without reducing the rate-limiting effect on large-witness transactions.

### Behaviour above the threshold

Transactions with witness data above 350 bytes per input have three options:

1. Stay in witness and pay full price. Same tooling, ~4x cost increase.
2. Split across many inputs. Each input gets 350 discounted bytes but requires pre-creating UTXOs (extra cost). Net effect: higher cost and a cleaner UTXO set.
3. Move to OP_RETURN. Provably unspendable, immediately prunable by nodes.

### Multi-input threshold exploitation

Splitting data across many inputs maximises discounted bytes: each input gets 350 bytes at the discounted rate. But each input requires a pre-existing UTXO, which must be created in a prior fan-out transaction. Mass splitting is mass UTXO consolidation.

Per-input witness overhead (signature, script structure, control block) consumes 70-133 bytes of the 350-byte threshold depending on the technique, leaving 210-280 bytes of data capacity per input. For a 20,000-byte witness payload:

| Strategy | Inputs | Total WU | vs. current |
|---|:-:|:-:|:-:|
| Single input (current rules) | 1 | ~20,164 | baseline |
| Single input (this proposal) | 1 | ~79,114 | 3.92x |
| Split, tapscript OP_IF (deployed) | ~96 | ~65,856 | 3.27x |
| Split, annex (most efficient, non-standard) | ~72 | ~49,392 | 2.45x |

Each split input costs ~686 WU: 350 WU witness (within discount, covering both data and overhead) + 164 WU non-witness input data + 172 WU UTXO creation in the prior fan-out. The tapscript OP_IF method (~133 bytes overhead, ~210 data bytes per input) is used by existing data-embedding protocols. The annex method (70 bytes overhead, ~280 data bytes per input) is more efficient but currently non-standard.

Multi-input splitting is cheaper per byte than OP_RETURN (the table above includes fan-out costs). But every split path requires pre-creating and then consuming all UTXOs across multiple transactions. If the UTXOs are created for this purpose, the net UTXO effect is neutral and the cost is 2.45-3.27x higher than today. If existing UTXOs are consumed, the result is mass consolidation, exactly what the discount exists to incentivise. There is no version of multi-input splitting that is both cheap and harmful to the network.

### OP_RETURN alignment

OP_RETURN exists as the designated location for arbitrary data: provably unspendable, immediately prunable, no UTXO bloat. But with the witness discount uncapped, the incentive structure favours embedding data in witness space at a 75% discount over using OP_RETURN at full price. Capping the discount closes most of that gap. A single large-witness input pays within 1.3% of OP_RETURN. Multi-input splitting is cheaper per byte but requires fan-out transactions and mass UTXO management. OP_RETURN is simpler for the same result.

### Parameter adjustability

The threshold is a consensus parameter. Lowering it (350 to 200) is a soft fork: more restrictive, every old-rule-valid block remains valid. This provides a mechanism to tighten the discount as subsidy diminishes. Raising it (350 to 500) is a hard fork relative to the activated rule, since blocks valid under the higher threshold may exceed weight limits under the lower one.

Raising is unlikely to be needed. Future signature schemes or protocol extensions that require larger witnesses will arrive via new SegWit versions, whose activation can define version-specific thresholds. The industry trend runs the other direction anyway: Schnorr < ECDSA, MuSig2 collapses n-of-n to 66 bytes, FROST compresses k-of-n to single signatures, CISA aggregates across inputs.

### Witness stuffing breakeven

The per-input discount creates a fixed savings of 1,050 WU (350 bytes x 3 WU saved) per input. For a single input with a 20,000-byte witness payload, this is a 1.3% advantage over OP_RETURN. Multi-input splitting multiplies this savings (see multi-input threshold exploitation above), but every split path either creates and consumes UTXOs (net neutral) or consolidates existing ones (net positive). The discount preserves enough subsidy to cover signatures and nothing more.

### Discounted, not free

An earlier design made the first N witness bytes completely free (0 WU). Three problems:

1. **Hard fork trap.** 0 WU witness bytes create a weight formula mismatch. A block of standard P2TR transactions at a 1,000,000 paid-byte limit produces ~4.4M WU, exceeding BIP-141's 4M limit. Resolving this requires either a 33% capacity reduction (a one-way door) or a new block limit formula.
2. **Capacity preservation.** Keeping the discount at 1 WU means small-witness transactions are priced identically to BIP-141. No capacity loss, no block size controversy.
3. **CISA makes weight elimination premature.** Cross-Input Signature Aggregation (DahLIAS, proven secure April 2025) will restructure the witness model. Weight elimination now would be redesigned during CISA deployment.

### Full discount removal

Removing the discount entirely (all witness at 4 WU) makes spending UTXOs more expensive while creating them stays the same cost, inverting the spend/create incentive. Large-data transactions could shift to encoding data in dust UTXOs: permanent UTXO set bloat stored in RAM by every full node, strictly worse than witness-embedded data.

### Lower weight limit (1 MWU)

| | 1 MWU limit | Per-input threshold |
|---|---|---|
| P2TR txs/block | ~1,623 | ~6,494 |
| Small-witness capacity vs today | **-75%** | **0%** |
| Max large-witness data/block | ~1 MB | ~1 MB |
| Large-witness discount per byte | 75% (preserved) | 0% (eliminated) |

Same cap on large witness data, 75% less small-witness capacity, and large witness data keeps its 75% subsidy.

### Content filtering

Content filtering identifies and rejects transactions matching data patterns at the consensus layer. Consensus rules are static; encoding methods are dynamic. Each new encoding technique requires a new filter rule and a new round of coordination to deploy. A pricing change is structural: one consensus change, and every current and future encoding technique hits the same cost wall.

Structural limits create perverse outcomes. Reducing push size limits forces data into more fragments, each with its own opcode and length prefix. The cost increase to the data creator is negligible (less than 0.4%), but the network stores the original data plus the fragmentation overhead. Analysis of seven bypass techniques shows that for most methods, the network burden increases more than the data creator's cost, a damage factor above 1 [10]. A per-input witness discount cap meters total witness volume per input, so no structural rearrangement reduces the cost.

Content-based filters also risk blocking protocol upgrade paths. Restricting opcodes or witness structures that double as soft fork delivery mechanisms adds coordination overhead and delay to upgrades that are already difficult to ship. A pricing cap achieves the same economic pressure without touching any upgrade path. A fixed pricing rule is also a stable foundation. Developers can reason about witness costs without accounting for filter rules that change with each new encoding method.

### Network-layer solutions

Network improvements (SeF/Erlay, better compression, pruning defaults) reduce the cost of carrying large blocks. They address the symptom: nodes struggling under load. They do not address the cause: a pricing rule that subsidises large witness data at 25% of its actual cost to the network. SeF compresses historical data after the fact. The discount lets new data enter at 75% subsidy every block. Fixing both is better than fixing either alone, but neither exists yet. SeF has no deployment timeline. The pricing error exists now and can be fixed now.

### Deployment scope

SegWit (BIP-141) introduced a new transaction serialization format, a new fee metric (weight units and vbytes, which did not exist before), new address formats (P2SH-P2WPKH, bech32), and a new block structure. Every wallet, block explorer, fee estimator, and miner had to understand all of it from scratch.

This proposal changes one coefficient in the existing weight formula. The serialization format, fee metric (sat/vB), address formats, and block structure are all unchanged. For any transaction where every input has ≤ 350 witness bytes, the weight calculation produces the same result as BIP-141.

| Who | What changes | Effort |
|---|---|---|
| Node implementations | Weight calculation, block validation | Small: the formula is 4 lines |
| Miners | Block template uses new weight formula | Included in node upgrade, same as any soft fork |
| Wallets building standard txs | Nothing | None: weight is identical for ≤ 350 bytes/input |
| Large-witness tooling | Weight calculation for >350 byte witnesses | Required: excess witness data pays full price |
| Block explorers | Display updated weight for affected txs | Small |
| Non-upgraded nodes | Nothing: blocks are valid under old rules | None (soft fork) |

## Specification

### Definitions

For each transaction input *i*, the **discounted witness bytes** and **excess witness bytes** are:

```
discounted_i = min(witness_size_i, WITNESS_DISCOUNT_THRESHOLD)
excess_i     = max(witness_size_i - WITNESS_DISCOUNT_THRESHOLD, 0)
```

Where `witness_size_i` is the total serialised witness data for input *i* (including stack item count, item lengths, and item data).

The **weight** of a transaction is:

```
weight = non_witness_size × 4 + marker_flag × 1 + sum(discounted_i) × 1 + sum(excess_i) × 4
```

Where:

- `non_witness_size` = transaction size excluding witness marker, flag, and all witness data (BIP-141 `base_size`)
- `marker_flag` = 2 bytes (witness marker 0x00 + flag 0x01), present in all SegWit transactions

### Block validation

A block is valid under this proposal if:

```
block_weight ≤ MAX_BLOCK_WEIGHT
```

Where `block_weight` is the sum of `weight` across all transactions in the block. This is the same validation rule as BIP-141. The only change is how individual transaction weights are calculated.

### Constants

```
WITNESS_DISCOUNT_THRESHOLD = 350
MAX_BLOCK_WEIGHT           = 4,000,000  (unchanged from BIP-141)
```

### Fee calculation

Transaction fees continue to be denominated in sat/vB, where `vbytes = weight / 4`. Unchanged from BIP-141. Wallets, block explorers, and fee estimators require no changes for small-witness transactions.

### Reference implementation

```python
WITNESS_DISCOUNT_THRESHOLD = 350
MAX_BLOCK_WEIGHT = 4_000_000

def tx_weight(tx):
    non_witness = tx.base_size * 4
    marker_flag = 2 if tx.has_witness else 0
    witness = sum(
        min(witness_size(tx, i), WITNESS_DISCOUNT_THRESHOLD) * 1
        + max(witness_size(tx, i) - WITNESS_DISCOUNT_THRESHOLD, 0) * 4
        for i in range(tx.input_count)
    )
    return non_witness + marker_flag + witness

def validate_block_weight(block):
    return sum(tx_weight(tx) for tx in block.transactions) <= MAX_BLOCK_WEIGHT
```

### Activation

This proposal is suitable for inclusion in the next consensus soft fork bundle. The change is one coefficient in the weight formula and is compatible with any activation mechanism. No rush is necessary, but I would want it in the next one as there is no reason I can think of to delay further than that.

### Soft fork proof

Every byte's cost either stays the same or increases:

| Data type | BIP-141 cost | This proposal | Change |
|---|:-:|:-:|---|
| Non-witness | 4 WU/byte | 4 WU/byte | Unchanged |
| Witness ≤ 350 bytes/input | 1 WU/byte | 1 WU/byte | Unchanged |
| Witness > 350 bytes/input | 1 WU/byte | **4 WU/byte** | Increased |

Since every byte costs the same or more, the weight of any transaction under this proposal is ≥ its weight under BIP-141. Any block valid under the new rules necessarily satisfies the old 4,000,000 WU limit. No block valid under the new rules can be invalid under the old rules.

## Backwards Compatibility

### Effect on existing transaction types

| Transaction type | Witness/input | Excess | Effect |
|---|:-:|:-:|---|
| P2TR key-path (single-sig) | 65–66 | 0 | **Unchanged** |
| MuSig2 (n-of-n multisig) | 65–66 | 0 | **Unchanged** |
| P2WPKH (legacy SegWit) | 107–109 | 0 | **Unchanged** |
| P2TR script-path (minimal) | ~135 | 0 | **Unchanged** |
| P2TR HTLC-timeout (Taproot LN) | ~196 | 0 | **Unchanged** |
| P2WSH 2-of-2 (LN cooperative close) | ~220 | 0 | **Unchanged** |
| P2WSH 2-of-3 multisig | ~254 | 0 | **Unchanged** |
| P2WSH HTLC (legacy Lightning) | 286–324 | 0 | **Unchanged** |
| P2WSH 3-of-5 multisig | ~395 | ~45 | ~8.5% cost increase |
| P2WSH 3-of-6 multisig | ~429 | ~79 | More expensive |
| P2TR script-path (depth 4) | ~290 | 0 | **Unchanged** |
| P2TR script-path (depth 7) | ~385–450 | ~35–100 | ~8–37% cost increase |
| Large witness data (20,000 bytes) | ~20,000 | ~19,650 | 3.95x cost increase |

### Wallet and tooling

Wallets and fee estimators require no changes for small-witness transactions (≤ 350 witness bytes per input). Tooling for transactions with large witness data would need to account for the higher weight of excess witness bytes. The sat/vB fee unit is unchanged.

### Migration path

Taproot-native replacements exist for all legacy patterns exceeding the threshold:

- **n-of-n multisig** → MuSig2 key-path (66 bytes)
- **k-of-n multisig** → FROST or Taproot script-path
- **Legacy Lightning** → Taproot Lightning (smaller witnesses)

### Pre-signed transactions

Transactions signed before activation carry witness data sized under the old weight formula. All standard pre-signed transaction types (Lightning commitment/HTLC, vault covenants, DLCs) use witness data well under 350 bytes per input. They are unaffected. Non-standard pre-signed transactions with witness data above 350 bytes per input would pay higher fees than originally estimated. No known deployed protocol produces such transactions.

## Security Considerations

**Chain growth.** Realistic full-block size drops from ~2.3 MB (observed peak monthly average, March 2024) toward ~1.3 MB (small-witness use) as large-witness transactions are repriced. Worst-case block size drops from ~4 MB to ~3 MB. Large blocks under this proposal necessarily are mass UTXO consolidation; it is impossible to create large blocks without consuming mass UTXOs. Where a large block under current rules can be a net burden on nodes, large blocks under this proposal are always a net positive. Long-term storage, bandwidth, and IBD requirements are reduced in all scenarios.

**Fee market.** Large-witness transactions produce higher weight per byte of useful content, naturally pricing them behind small-witness transactions when blocks are full.

**Attack paths.** Five strategies for embedding large data in blocks, compared under current and proposed rules.

| Strategy | Cost (current) | Cost (proposed) | Notes |
|---|---|---|---|
| Single large witness input | ~20,164 WU | ~79,114 WU (3.92x) | Direct path. Repriced. |
| Split across inputs (tapscript) | ~20,164 WU | ~65,856 WU (3.27x) | Requires fan-out tx. Consumes all created UTXOs. |
| Split across inputs (annex) | ~20,164 WU | ~49,392 WU (2.45x) | Non-standard. Best-case evasion. |
| OP_RETURN | ~80,000 WU | ~80,000 WU | Already full price. Prunable. |
| Dust UTXO encoding | ~80,000 WU | ~80,000 WU | Permanent UTXO bloat. More expensive than witness even pre-proposal. |

Every witness-based path costs more under the proposal. Non-witness paths are unchanged but were already 4x more expensive. The cheapest evasion (annex splitting) still costs 2.45x more than today, requires thousands of pre-created UTXOs, and consumes all of them in the data transaction. No path increases UTXO set burden: witness paths are repriced, OP_RETURN is prunable, and dust encoding remains more expensive than both.

**Taproot annex.** The annex counts toward `witness_size_i` and the threshold. A P2TR key-path spend (66 bytes) leaves 284 bytes of annex space within the threshold. Any annex-defining soft fork should consider threshold interaction.

**Deep taptree spends.** Script-path spends at taptree depth 5+ may exceed 350 bytes. No standard protocol uses depths beyond 4 for routine on-chain spends. Protocols building deep trees (BitVM2, large multisig via script leaves) use key-path for the happy path and rarely exercise the taptree.

**Future SegWit versions.** The threshold applies to all witness data regardless of SegWit version. Future soft forks that define new witness versions (v2 through v16) can set version-specific thresholds as part of their activation. For example, a CISA-enabled witness version where per-input signatures shrink could activate with a lower threshold for that version, while leaving the 350-byte threshold intact for v0 and v1. This is a soft fork in both directions: the new version's activation defines its own rules, and the existing threshold remains unchanged for existing versions.

**Template construction.** Miners select transactions by fee rate (sat/vB). Small-witness transactions have the same weight as under BIP-141, so their fee rate and template priority are unchanged. Only transactions with witness data exceeding 350 bytes per input see a weight increase, which lowers their fee rate and pushes them down the priority queue. No new sorting logic is required.

**Size-based pricing only.** The proposal contains no content-based rules. All witness data is priced by size and position (within or beyond the per-input threshold). The rate-limiting effect on large data emerges from pricing, not classification.

## Costs and Risks

Following Bitcoin Core's SegWit costs and risks analysis [12], this section separates certain costs from probabilistic risks. It does not conclude whether the change should be made.

### Incentive analysis

| Actor | Impact | Deviation incentive |
|---|---|---|
| Standard users (>99% of inputs) | None. Weight identical for ≤350 byte witnesses. | None. |
| Lightning operators | None. All constructions (cooperative close ~220B, HTLC-success ~324B) within threshold. | None. |
| Multisig (2-of-3 and below) | None. P2WSH 2-of-3 (~254B) within threshold. | None. |
| Multisig (3-of-5 and above) | ~8.5% cost increase (3-of-5), more for larger. | Migrate to MuSig2/FROST. Aligned with protocol direction. |
| Node operators | Worst-case chain growth drops ~196 to ~154 GB/year. | None. Strictly better. |
| Protocol developers | Threshold applies to existing witness versions only. Future versions define their own. | None. No constraint on roadmap. |
| Miners | Template construction unchanged. Standard tx fee rates identical. | See below. |
| Large arbitrary data | 2.45-3.95x cost increase depending on strategy. | See below. |

**Miners.** Sort by fee rate, fill to weight limit. That logic is unchanged. Small-witness transactions occupy the same template positions at the same fee rates. Large-witness transactions pay more per byte but there may be fewer of them. If data demand is inelastic, miners collect more per data transaction. If elastic, freed space fills with small-witness transactions at prevailing rates. In both cases miners have no incentive to deviate from honest template construction. A block violating the new weight formula is invalid, not just non-standard.

**Large arbitrary data.** The rational response to repricing is OP_RETURN: same cost, simpler tooling, prunable by nodes. The one structural evasion is input splitting (spreading data across many inputs to maximise discounted bytes). This is self-limiting: it requires mass UTXO creation in a prior fan-out transaction, and the data transaction consumes all of them. The net effect is mass UTXO consolidation, which is what the discount exists to incentivise. Even the most efficient split (annex method) costs 2.45x more than today.

**Unintended equilibria.** No path restores the current 75% subsidy on large witness data. Input splitting is the closest, but it is more expensive than OP_RETURN for the same data, and it produces UTXO consolidation as a side effect. No stable state exists where rational actors exploit the threshold to achieve current-rule economics.

### Costs

These occur if the proposal activates. They are not speculative.

**Higher fees for large witness data.** Any witness data exceeding 350 bytes per input pays ~4x more. This is the intended effect. Affected constructions include 3-of-5 multisig (~8.5% increase), deep taptree spends at depth 5+ (8-37%), and bulk data payloads (3.95x).

**Reduced worst-case block size.** Maximum block size drops from ~4 MB to ~3 MB. Small-witness capacity (transactions with ≤350 witness bytes per input) is unchanged.

**Migration pressure on legacy multisig.** Wallets using P2WSH 3-of-5 or larger see cost increases. Taproot-native replacements (MuSig2, FROST) exist but require wallet upgrades.

### Risks

These may or may not occur. Each includes avoidance (reduce probability) and mitigation (reduce impact).

**Miner revenue impact.** See incentive analysis above for full breakdown.

- *Avoidance:* Not avoidable. Inherent to any repricing.
- *Mitigation:* Small-witness transactions (>99% of inputs) are priced identically. If data demand drops, freed block space fills with small-witness transactions at prevailing rates.

**Pre-signed transactions above threshold.** Transactions signed before activation with witness data above 350 bytes per input would pay higher fees than estimated at signing time.

- *Avoidance:* All known pre-signed transaction protocols (Lightning commitment/HTLC, vault covenants, DLCs) use witness data well under 350 bytes.
- *Mitigation:* Activation timeline provides lead time for any affected protocol to adapt.

**Future protocol interactions.** The Taproot annex, CISA, or future SegWit versions may alter witness structure in ways that interact with the threshold.

- *Avoidance:* Future soft forks can define version-specific thresholds as part of their activation. The 350-byte threshold applies only to existing witness versions unless explicitly extended.
- *Mitigation:* Lowering the threshold is a soft fork. Raising it for a new witness version is part of that version's activation. The threshold is adjustable without disrupting existing rules.

**Data migration to worse locations.** See incentive analysis above for rational responses to repricing. The risk is that large arbitrary data shifts from witness to dust UTXOs, creating permanent UTXO set bloat.

- *Avoidance:* OP_RETURN is cheaper and simpler than dust UTXOs. Capping the discount makes OP_RETURN price-competitive with witness embedding for the first time.
- *Mitigation:* Dust UTXOs cost 4 WU/byte even under current rules. The proposal prices excess witness data at the same rate, removing the incentive to use witness over OP_RETURN without creating any new incentive toward dust.

## Deployment

[TBD. To be determined through community discussion.]

## Test Vectors

[TBD. To be added before Proposed status.]

## Acknowledgements

The per-input deduction concept originates from Gregory Maxwell (commit [`d6eb259`](https://github.com/bitcoin/bitcoin/commit/d6eb259), August 2013). Witness discount analysis builds on observations by Giacomo Zucco regarding static consensus fixes versus dynamic filtering. The per-input witness discount threshold as a consensus proposal was first described by Luke Dashjr. Faye O'Connor contributed economic breakeven analysis and soft fork directionality analysis. Standard witness size data from on-chain analysis by Antoine Le Calvez and custody provider documentation. Lightning witness sizes from BOLT #3.

## References

[1] [BIP-141: Segregated Witness](https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki). Witness data serialisation, weight formula, WITNESS_SCALE_FACTOR.

[2] [Bitcoin Core: SegWit Benefits](https://bitcoincore.org/en/2016/01/26/segwit-benefits/). Original witness discount rationale: "making signature data, which does not impact the UTXO set size, cost 75% less than data that does."

[3] [Andrew Chow: Segwit FUD Clearup](https://achow101.com/2016/04/Segwit-FUD-Clearup). Discount designed to incentivise UTXO set cleanup.

[4] [Mastering Bitcoin (Saylor Academy)](https://learn.saylor.org/mod/book/view.php?id=36376&chapterid=19021). Witness data validated once, never stored in UTXO set.

[5] [River Learn: What is SegWit?](https://river.com/learn/what-is-segwit/). Discount balances cost of creating vs spending outputs.

[6] [BIP-341: Taproot](https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki). Schnorr signatures, key-path spends.

[7] [BIP-342: Tapscript](https://github.com/bitcoin/bips/blob/master/bip-0342.mediawiki). Witness structure for Taproot script-path.

[8] [BOLT #3: Transactions](https://github.com/lightning/bolts/blob/master/03-transactions.md). Lightning HTLC witness sizes.

[9] [Bitcoin Core commit d6eb259](https://github.com/bitcoin/bitcoin/commit/d6eb259). Gregory Maxwell, CalculateModifiedSize().

[10] [knotslies.com: Damage Factor Calculator](https://knotslies.com/calculator.html). Analysis of seven bypass techniques for structural push-size limits.

[11] Stirling, K. "Quantifying Threats to Bitcoin Node Decentralisation." 2026. Storage, IBD, bandwidth, and UTXO/RAM constraints against a $300 hardware target over a 10-year upgrade cycle.

[12] [Bitcoin Core: Segregated Witness Costs and Risks](https://bitcoincore.org/en/2016/10/28/segwit-costs/). Costs vs risks framework for consensus changes. UTXO lifecycle cost rebalancing: create/spend ratio from ~1:4.5 to ~1:2.

[13] Wuille, P. "Segregated Witness and its Impact on Scalability." Scaling Bitcoin Hong Kong, December 2015. [Transcript](https://btctranscripts.com/scalingbitcoin/hong-kong-2015/segregated-witness-and-its-impact-on-scalability). Witness discount rationale from the primary BIP-141 author.
