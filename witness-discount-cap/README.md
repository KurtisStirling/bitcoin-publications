# Witness Discount Cap (Cost-Reflective Fee Pricing)

| Field | Value |
|---|---|
| **BIP** | ? |
| **Layer** | Consensus (soft fork) |
| **Title** | Witness Discount Cap (Cost-Reflective Fee Pricing) |
| **Authors** | Kurtis Stirling <kurtis.stirling@proton.me> |
| **Status** | Draft |
| **Type** | Specification |
| **Assigned** | ? |
| **License** | CC0-1.0 |

## Abstract

BIP-141 assigns witness data one quarter of the weight of non-witness data. This proposal caps that discount at 350 witness bytes per transaction input: bytes within the cap retain the existing 1 WU/byte rate, while excess witness data costs 4 WU/byte.

This makes fees for large witness payloads more reflective of their network resource use while leaving common small-witness transactions unchanged.

## Motivation

BIP-141 introduced transaction weight, under which non-witness data costs 4 weight units (WU) per byte while witness data costs 1 WU per byte. This gives witness data a 75% discount and permits blocks of up to 4,000,000 WU.

The distinction has sound reasons. Witness data does not create entries in the UTXO set and can eventually be pruned by nodes that do not require historical witness data. The discount also avoids discouraging transactions that consolidate multiple UTXOs. These considerations remain valid. Pieter Wuille's original Segregated Witness presentation explicitly described the discount in terms of differences in resource cost, particularly UTXO-set impact and prunability.

The issue is not that witness data receives a discount, but that the same discount scales without limit. A small signature and a very large witness payload are both charged at 1 WU per byte.

Large volumes of witness data still contribute to permanent chain history. They increase:

- initial block download time and data transfer;
- archival storage requirements;
- block and transaction relay bandwidth;
- bandwidth costs for nodes on metered connections;
- the cost of synchronisation over constrained or privacy-preserving transports.

The benefits that justify treating witness data differently from base data therefore do not imply that an unlimited quantity of witness data should receive the same 4:1 weight treatment.

This proposal preserves the existing discount for the portion of each input's witness that covers ordinary transaction use, while charging additional witness data at the same weight as base data.

## Design

This BIP aims to rate-limit the contribution of large witnesses to Bitcoin's chain growth. It does so by capping the amount of witness data per input that receives the witness discount. Witness data within the allowance retains the existing discount; data beyond it is charged at the base-data rate.

### Objectives

The design aims to:

- preserve the witness discount for ordinary transaction use;
- limit how far that discount scales with unusually large witnesses;
- remain content agnostic and avoid passing judgement on how witness space is used;
- keep the consensus rule simple, deterministic and easy to reason about.

### Why rate limiting?

**Content agnostic.** Rate limiting avoids passing judgement on what witness data represents or what it is being used for. The rule cares only about size: the same number of bytes receives the same treatment regardless of content, purpose, application or encoding.

**Future-proof.** Filters depend on recognising particular forms of data and can be bypassed when that data is represented differently. A size-based rule does not. New encodings do not change their underlying byte cost, so the rule does not need to evolve alongside new ways of using witness space.

**A "one-time fix."** Rather than creating an ongoing cycle of monitoring new uses, identifying workarounds, agreeing responses and updating filters, rate limiting establishes a simple resource constraint that continues to apply without needing to know what comes next. This reduces implementation and maintenance costs, as well as the ongoing engineering attention, coordination and social capital consumed by a perpetual filtering arms race.

### Per-input discount cap

The discount is capped **per input**, rather than per transaction.

Each transaction input receives an allowance of 350 serialized witness bytes at the existing 1 WU/byte rate. Any witness bytes for that input beyond the allowance are charged at 4 WU/byte.

Applying the allowance per input preserves an important property of the existing witness discount: transactions that legitimately consume additional UTXOs receive additional discounted capacity for the witnesses required to spend them.

A transaction with many ordinary inputs therefore does not lose the economic incentive to consolidate UTXOs simply because its aggregate witness size exceeds 350 bytes.

### Choice of 350 bytes

The allowance is intended to cover the large majority of ordinary currently deployed witness constructions while remaining small relative to the large payloads this proposal is intended to affect.

Representative witness sizes considered during design include approximately:

| Spend type | Serialized witness size |
|---|---:|
| Taproot key-path | 65–66 bytes |
| P2WPKH | 107–109 bytes |
| Minimal Taproot script-path | ~135 bytes |
| Typical HTLC timeout | ~196 bytes |
| P2WSH 2-of-2 multisig | ~220 bytes |
| P2WSH 2-of-3 multisig | ~254 bytes |
| P2WSH HTLC | ~286–324 bytes |
| P2WSH 3-of-5 multisig | ~395 bytes |
| P2WSH 3-of-6 multisig | ~429 bytes |
| Deep Taproot script-path spend | ~385–450 bytes |

The threshold is therefore not intended to encompass every possible legitimate witness construction. Some unusually large multisig arrangements, deep Taproot trees and future constructions may exceed it.

Instead, 350 bytes provides headroom above common signatures, multisig spends and script paths while limiting how far the discounted region extends into large witness payloads.

There is also little sensitivity to the precise threshold once witness payloads become very large. For a 20,000-byte single-input witness, the witness-only weight increase relative to BIP-141 is approximately:

| Allowance | Relative witness weight |
|---|---:|
| 285 bytes | ~3.96× |
| **350 bytes** | **~3.95×** |
| 500 bytes | ~3.93× |

The threshold therefore primarily determines where ordinary transaction use stops receiving the discount. It has relatively little effect on the treatment of genuinely large payloads.

### Economic effect

Under BIP-141, a 20,000-byte witness contributes approximately 20,000 WU.

Under this proposal:

- the first 350 bytes contribute 350 WU;
- the remaining 19,650 bytes contribute 78,600 WU;
- total witness contribution is therefore 78,950 WU.

The large witness consequently approaches the base-data cost of 4 WU per byte while retaining a small discounted allowance for the witness required to spend the input.

The proposal does not make large witnesses invalid. It changes how much scarce block weight they consume.

Input splitting can multiply the number of 350-byte allowances. This means the proposal is not an absolute cap on discounted witness data per transaction. Splitting has costs, however: each additional input requires a spendable UTXO and adds non-witness transaction overhead.

Modelling of a 20,000-byte payload under currently available constructions gives approximate total transaction weights of:

| Construction | Approx. weight | Increase vs current |
|---|---:|---:|
| Single input | ~79,114 WU | ~3.92× |
| Optimised tapscript input splitting | ~65,856 WU | ~3.27× |
| Optimised annex input splitting | ~49,392 WU | ~2.45× |

The ability to split data across inputs therefore reduces the maximum economic effect, but does not recreate the existing unlimited 1 WU/byte treatment.

## Specification

For each transaction input `i`, define:

```text
witness_size_i = serialized size in bytes of that input's witness

discounted_i = min(witness_size_i, 350)

excess_i = max(witness_size_i - 350, 0)
```

The witness contribution of input `i` to transaction weight is:

```text
discounted_i + 4 * excess_i
```

For a transaction using witness serialization, transaction weight becomes:

```text
weight =
    base_size * 4
    + marker_and_flag_weight
    + sum(discounted_i)
    + 4 * sum(excess_i)
```

where:

```text
marker_and_flag_weight = 2
```

The marker and flag therefore retain their existing BIP-141 treatment.

Transactions without witness serialization are unaffected.

Virtual transaction size remains:

```text
vsize = ceil(weight / 4)
```

The maximum block weight remains:

```text
MAX_BLOCK_WEIGHT = 4,000,000
```

Only the weight assigned to witness bytes beyond the per-input allowance changes. BIP-141's existing block-weight limit itself is not increased or decreased.

## Reference Implementation

Illustrative pseudocode:

```text
WITNESS_DISCOUNT_ALLOWANCE = 350

function input_witness_weight(witness):
    size = serialized_size(witness)

    discounted = min(size, WITNESS_DISCOUNT_ALLOWANCE)
    excess = size - discounted

    return discounted + (4 * excess)

function transaction_weight(tx):
    weight = base_size(tx) * 4

    if tx.has_witness():
        weight += 2  // marker + flag

        for input in tx.inputs:
            weight += input_witness_weight(input.witness)

    return weight
```

Block validation continues to require:

```text
sum(transaction_weight(tx) for tx in block.transactions)
    <= MAX_BLOCK_WEIGHT
```

This pseudocode is explanatory rather than a production implementation. A complete implementation and consensus test suite would be required before the proposal could progress beyond Draft status.

## Security Considerations

### Input splitting

Because the allowance applies per input, users can obtain additional discounted witness capacity by spending additional inputs.

This is intentional to the extent necessary to preserve the incentive to consolidate UTXOs, but it also provides a way to reduce the cost increase for large witness payloads.

This should not be described as making the rule fully "unbypassable". The narrower property is that it cannot be bypassed merely by inventing a new representation for the same quantity of data. Input splitting changes the transaction's resource structure and incurs additional UTXO and transaction overhead.

### Taproot annex

Annex data is part of the serialized witness and is therefore included in `witness_size_i`.

A Taproot key-path witness consumes approximately 66 bytes before annex data, leaving approximately 284 bytes of the 350-byte allowance available at the discounted rate.

Annex data beyond the remaining allowance is charged at 4 WU/byte.

### Large legitimate witnesses

Some legitimate current constructions can exceed 350 bytes, including larger P2WSH multisig arrangements and sufficiently deep Taproot script paths.

This proposal deliberately does not attempt to identify those constructions and provide exemptions. Doing so would undermine the content-agnostic property of the rule and introduce additional consensus complexity.

The excess remains valid. It simply does not receive the witness discount.

### Future soft forks

Future witness versions or script upgrades may introduce legitimate constructions with larger witnesses.

A future soft fork may further restrict how block resources are consumed, but it cannot in general restore the 1 WU/byte treatment to bytes that this rule already counts at 4 WU without relaxing an existing consensus restriction.

The 350-byte allowance should therefore be treated as a long-lived consensus parameter rather than a policy default that can be adjusted casually.

## Test Vectors

The following examples show the witness contribution to transaction weight. Base transaction weight and, where applicable, the 2 WU marker/flag contribution are omitted for clarity.

### 1. No witness

```text
witness_size = 0

old witness weight = 0 WU
new witness weight = 0 WU
```

No change.

### 2. Witness below the allowance

```text
witness_size = 200

discounted = 200
excess = 0

new witness weight = 200 WU
```

No change from BIP-141.

### 3. Witness exactly at the allowance

```text
witness_size = 350

discounted = 350
excess = 0

new witness weight = 350 WU
```

No change from BIP-141.

### 4. Witness one byte above the allowance

```text
witness_size = 351

discounted = 350
excess = 1

new witness weight =
    350 + (1 * 4)
    = 354 WU
```

Under BIP-141 the same witness contributes 351 WU.

### 5. Large witness

```text
witness_size = 20,000

discounted = 350
excess = 19,650

new witness weight =
    350 + (19,650 * 4)
    = 78,950 WU
```

Under BIP-141 the same witness contributes 20,000 WU.

### 6. Multiple inputs

For two inputs containing 500 witness bytes each:

```text
input 1:
    350 + (150 * 4) = 950 WU

input 2:
    350 + (150 * 4) = 950 WU

total witness weight = 1,900 WU
```

Under BIP-141 the same 1,000 witness bytes contribute 1,000 WU.

This confirms that the allowance is independently applied to each input rather than once per transaction.

## Backward Compatibility

This proposal is a consensus tightening.

Non-upgraded nodes continue to calculate transaction and block weight according to BIP-141. They may therefore accept a block whose weight is at or below 4,000,000 WU under BIP-141 but exceeds 4,000,000 WU under the rules defined here.

Upgraded nodes reject such a block.

Any block accepted by upgraded nodes remains within the existing BIP-141 block-weight limit and is therefore valid to non-upgraded nodes. This gives the proposal the compatibility characteristics of a soft fork.

Transactions whose inputs contain no more than 350 witness bytes are unaffected.

Wallets, fee estimators, miners and other software constructing transactions with larger witnesses must use the revised weight calculation after activation. A pre-signed transaction containing above-cap witness data may consequently have a lower effective fee rate under the new rules than its creator expected.

## Deployment

TBD.

Deployment parameters and activation mechanism should be determined through community discussion after the proposal and its implementation have received sufficient review.

## Prior Work

The witness discount itself originated with Segregated Witness. Pieter Wuille described the 75% witness discount as a pragmatic approximation of differing resource costs and discussed moving toward a more general cost-based metric in the future.

Jonas Nick presented a validation-cost metric at Scaling Bitcoin Hong Kong in 2015, representing a broader approach in which transaction cost could reflect measured validation resources rather than serialized size alone.

Matt Corallo later proposed, as part of a broader hard-fork design, reducing the witness discount from 75% to 50%.

Other scaling discussions have considered maintaining multiple independent resource limits rather than collapsing every cost into a single scalar, and the complications that multidimensional limits create for transaction selection and block construction.

This proposal deliberately takes a narrower approach. It does not attempt to construct a complete model of node resource consumption or redesign Bitcoin's block-resource accounting. It modifies one property of BIP-141: how far the existing witness discount is allowed to scale.

There is also historical precedent in Bitcoin Core for applying a resource-accounting adjustment on a per-input basis rather than uniformly across the whole transaction. The former `CalculateModifiedSize()` priority calculation reduced the effective size attributed to an input in order to avoid disincentivising UTXO cleanup. The mechanism and purpose differ from this proposal, but the underlying pattern, preserving a bounded per-input allowance for desirable spending behaviour rather than granting an unbounded transaction-wide benefit, is related.

## Acknowledgements

Thanks to Gregory Maxwell, Luke Dashjr and Faye O'Connor for discussion, criticism and historical context that informed development of this proposal.

The witness-size estimates used during design also benefited from existing public analysis of Bitcoin transaction and witness serialization.

This proposal builds on the design and implementation work of BIP-141 and the broader body of Bitcoin scaling research concerning block-resource accounting.

## References

- **BIP-141: Segregated Witness (Consensus layer)**, Eric Lombrozo, Johnson Lau and Pieter Wuille.
- **Segregated Witness and its Impact on Scalability**, Pieter Wuille, Scaling Bitcoin Hong Kong 2015.
- **Validation-cost metric**, Jonas Nick, Scaling Bitcoin Hong Kong 2015.
- **On Hardforks in the Context of SegWit**, Matt Corallo, bitcoin-dev, 2016.

## Copyright

This BIP is licensed under the Creative Commons CC0 1.0 Universal license.
