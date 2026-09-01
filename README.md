# Bitcoin Publications

Research and proposals on what threatens Bitcoin as sound money, and what to do about it.

Kurtis Stirling · [CC0-1.0](LICENSE)

---

## [Can Chain Growth Kill Node Decentralisation?](can-chain-growth-kill-node-decentralisation)

What does it cost to run a Bitcoin full node, and how much room is left before that cost pushes people out?

Four hardware constraints modelled against a deliberately cheap target: a $300 node expected to last ten years. Storage binds first, at roughly 111 GB of chain growth per year. The observed trajectory passes, but not by much. Today's average block size sits 28% below the break point, and March 2024 already exceeded it for a month.

Every modelled result reproduces from the standalone Python in [`models/`](can-chain-growth-kill-node-decentralisation/models).

## [Witness Discount Cap (Cost-Reflective Fee Pricing)](witness-discount-cap)

BIP draft. Consensus soft fork, status Draft.

BIP-141 charges witness data one quarter of the weight of everything else, and that discount scales without limit. A signature and a large arbitrary payload are priced the same per byte, even though only one of them is why the discount exists. This proposal caps the discount at 350 witness bytes per input. Bytes within the cap keep the current rate, and the excess costs the same as base data.
