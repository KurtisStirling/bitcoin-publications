# Can Chain Growth Kill Node Decentralisation?

**Quantifying the hardware cost of running a Bitcoin full node, and how much room is left.**

Kurtis Stirling · March 2026 · [CC0-1.0](../LICENSE)

All models are standalone Python and live in [`models/`](models). Every modelled result in this paper can be reproduced.

---

## Summary

Bitcoin's security depends on people independently verifying the chain. If doing that requires increasingly expensive or frequently replaced hardware, fewer people will run nodes and the validator set becomes easier to concentrate or coerce.

I modelled four hardware constraints against a deliberately cheap target: a **$300 node with a ten-year service life**. Storage is the constraint that binds.

A 2 TB SSD in the reference machine has room for about **111 GB of chain growth per year** over ten years. The observed trajectory since 2023 is about **80 GB/year**, so it passes. The current average block size of 1.69 MB corresponds to about **87 GB/year**. The ceiling breaks at **2.16 MB average blocks**, only 28% above today's average, and Bitcoin has already briefly exceeded it: March 2024 averaged 2.29 MB, equivalent to **118 GB/year**.

A sustained data-heavy mix averaging 3.82 MB per block would grow the chain by about **196 GB/year** and fill the reference disk in roughly **5.7 years**.

The longer-term picture is less alarming. Chain growth is linear while storage capacity per dollar can compound, so later hardware generations gain headroom if consumer storage keeps improving at anything close to its historical post-2014 rate. That is the main uncertainty in the paper. The first ten-year ceiling is arithmetic; the multi-generation forecast is not.

This paper does not propose a protocol change.

---

## Contents

- [1. The question](#1-the-question)
- [2. What running a node actually costs](#2-what-running-a-node-actually-costs)
- [3. Method](#3-method)
- [4. Storage is the binding constraint](#4-storage-is-the-binding-constraint)
- [5. How much to trust the storage forecast](#5-how-much-to-trust-the-storage-forecast)
- [6. The other constraints do not bind](#6-the-other-constraints-do-not-bind)
- [7. Affordability and decentralisation are different questions](#7-affordability-and-decentralisation-are-different-questions)
- [8. What would change the findings](#8-what-would-change-the-findings)
- [9. Objections](#9-objections)
- [10. Related work](#10-related-work)
- [11. Conclusion](#11-conclusion)
- [Appendix A: evidence chain](#appendix-a-evidence-chain)
- [Appendix B: models](#appendix-b-models)
- [Appendix C: supplementary calculations](#appendix-c-supplementary-calculations)
- [References](#references)

---

## 1. The question

A bigger blockchain needs more storage and takes longer to download and validate. The useful question is not whether those costs rise, but whether they rise fast enough to force enough operators out that Bitcoin's validator set becomes easier to enumerate, target or coerce.

I do not try to determine how many nodes are "enough". This paper measures the other half of the problem: how quickly the hardware burden is changing, which resource becomes limiting first, and whether chain growth is on a trajectory that repeatedly forces operators to upgrade.

The answer is more reassuring over decades than it is over the next hardware cycle. Storage capacity per dollar can compound while the blockchain adds a roughly fixed number of gigabytes each year. If storage keeps improving, each replacement machine starts with more headroom than the one before it. But a ten-year device can still hit its limit before that compounding benefit arrives.

That failure can be quiet. An operator whose disk fills can prune rather than upgrade. Their node continues validating, but it stops retaining and serving the historical chain. Nothing visibly breaks, yet the network loses an archival peer that future nodes can bootstrap from.

### What this paper measures

The decentralisation claim here is about the validator population, not universal access to node ownership. A network can be expensive to join and still be difficult to coerce if enough validators remain across enough jurisdictions. It can also be cheap to join but concentrated in a small number of places.

The causal chain tested here is:

**chain growth → node cost and upgrade pressure → fewer nodes → greater concentration → easier capture or coercion**

Section 7 deals separately with affordability in regions where the $300 hardware target or flat-rate broadband assumption does not hold.

Satoshi identified the underlying tension early:

> "Bitcoin users might get increasingly tyrannical about limiting the size of the chain so it's easy for lots of users and small devices."
>
> – Satoshi Nakamoto, 10 December 2010 [\[2\]](#ref-2)

The central result is that **storage is the only constraint examined that is both operationally critical and irreversible**. The chain never shrinks, and no deployed protocol mechanism substantially reduces the archival storage requirement.

---

## 2. What running a node actually costs

Bitcoin was specified as "a purely peer-to-peer version of electronic cash" whose security rests on participants verifying transactions themselves rather than trusting an intermediary [\[1\]](#ref-1). A full node does that by validating every block and transaction against the consensus rules.

An **archival node** keeps the entire blockchain, currently about 724 GB. A **pruned node** validates the same history but discards old block data afterwards, usually keeping around 10–15 GB. Pruning reduces the operator's storage requirement, but it does not remove the network's need for archival peers: a new node still needs to obtain the full history before it can validate and discard it. Nothing in the protocol guarantees a minimum archival population.

The **UTXO set** is the set of currently spendable outputs. It contains about 169 million entries and occupies about 11 GB. Keeping more of it in RAM speeds validation, especially during initial sync, but it does not need to fit entirely in memory for a node to function.

**Initial block download (IBD)** is the first sync from genesis. On the class of hardware used here it currently takes days, not hours.

One detail matters particularly for storage. Bitcoin limits blocks by **weight**, not simply by bytes. Non-witness data costs four weight units per byte, while witness data costs one. A full block of ordinary monetary transactions is therefore much smaller on disk than a full block dominated by witness-heavy data such as inscriptions. Once blocks are full by weight, transaction mix becomes the main lever on chain growth.

---

## 3. Method

### Upgrade frequency is the metric

A node being affordable today says little about decentralisation if it has to be replaced every few years. Repeated forced upgrades create churn, so I use **service life** rather than snapshot purchase price as the main test.

The Raspberry Pi 4 is a useful empirical anchor. It was widely recommended for budget nodes around 2022, but by 2025 the platform was effectively being abandoned for Bitcoin workloads as IBD times stretched beyond a week, RAM became restrictive, and pre-built vendors moved to N100/N150 hardware [\[49\]](#ref-49)[\[50\]](#ref-50)[\[51\]](#ref-51)[\[52\]](#ref-52).

I use a **ten-year target**. That is deliberately demanding: consumer PCs are commonly replaced sooner, but a single-purpose appliance with no moving parts should not need the same replacement cycle as a general-purpose computer. Section 8 shows how the result changes at seven and eight years.

### Reference hardware: $300

Current node hardware spans roughly $200–400 at the low end. DIY systems can sit near $200–270, while pre-built products commonly cost $399–599. I use **$300** as a conservative minimum viable configuration rather than as the median operator budget.

The reference machine is an N100 mini-PC with:

- 2 TB NVMe SSD
- 16 GB RAM
- roughly 12 GB/hour observed IBD processing
- about 1,850 GB of usable storage after filesystem reservation, OS, swap and logs

A higher budget substantially relaxes the storage result. That is intentional: if the analysis finds adequate headroom at $300, more expensive configurations have more.

### Four constraints

Each model asks how quickly the chain can grow before one resource breaches the target service life.

| Constraint | What it limits | Result |
|---|---|---|
| **Storage** | Chain size that fits on the 2 TB SSD | **Binding** |
| IBD processing | Chain processable within seven days | ~117 GB/year ceiling on static hardware |
| Bandwidth speed | Chain downloadable within seven days | Not binding for most current residential broadband |
| UTXO / RAM | Chainstate that can be cached in memory | Slows IBD as pressure rises, but does not stop operation |

The distinction is important. Bandwidth and IBD mainly make it harder to **start** a node. UTXO pressure mainly changes performance. All three have credible paths to improvement through faster networks, software optimisation, more RAM or alternative chainstate designs.

Storage accumulates while the node is already operating, and every byte added to the archival chain is permanent. That makes it the hardest constraint to recover from once the disk fills.

---

## 4. Storage is the binding constraint

![Chain size against usable space on a 2 TB SSD, 2026–2036, for five growth scenarios](figures/fig-storage-nearterm.png)

*The first hardware cycle. Markers show the year each scenario exhausts the disk. Model: [`models/storage/`](models/storage).*

### 4.1 The ten-year ceiling is 111 GB/year

A nominal 2 TB SSD provides 2,000 GB. After the deductions above, the reference machine has about 1,850 GB available. The blockchain and chainstate currently use roughly 735 GB, leaving about 1,115 GB. Allowing for modest chainstate growth leaves around 1,110 GB for additional blockchain data.

Spread across ten years, that produces a ceiling of **111 GB/year**. At eight years, the ceiling rises to about 139 GB/year.

This is not a forecast. It is arithmetic from the chosen hardware, current chain size and service-life target. The uncertainty begins when we ask how quickly blocks will grow and what a replacement machine will cost later.

### 4.2 The current margin is real, but small

The observed trajectory since 2023 is roughly **80 GB/year**, below the ceiling. At today's 1.69 MB average block size, the implied annual rate is about **87 GB/year**.

The ceiling is crossed at **2.16 MB average blocks**. That is only 28% above today's average. Bitcoin has already crossed that level temporarily: March 2024 averaged 2.29 MB, equivalent to about **118 GB/year**.

Blocks have been effectively full by weight since January 2023, so future storage growth depends largely on what fills that weight. Average block size rose from 1.11 MB in 2022 to 1.69 MB, a 52% increase. Witness inscriptions drove much of that move [\[38\]](#ref-38)[\[39\]](#ref-39)[\[40\]](#ref-40). OP_RETURN use and direct submission to miners provide other routes for data-heavy transactions [\[41\]](#ref-41).

A sustained inscription-heavy mix averaging **3.82 MB** would grow the chain by about **196 GB/year**, filling the reference disk in roughly **5.7 years**. I use that as a plausible high-demand scenario rather than a theoretical maximum. Individual blocks can approach 4 MB, but sustaining an extreme across years is a different claim.

The detailed transaction-mix calculation and sensitivity table are in [Appendix C](#appendix-c-supplementary-calculations).

### 4.3 Deliberately filling the chain is expensive, not impossible

At an illustrative 5 sat/vB and $100,000/BTC, sustaining just enough witness-heavy demand to hold average blocks at the 2.16 MB ceiling costs roughly **1,500 BTC, or $150 million per year**. Sustaining the 3.82 MB scenario costs roughly **2,628 BTC, or $263 million per year**.

Those numbers are far outside ordinary spam economics, but they are not outside a state budget. More importantly, the March 2024 breach did not require an attacker. Commercial inscription demand alone briefly produced 118 GB/year.

Relay and mempool policy can make some forms of flooding harder, but policy does not prevent miners from placing their own data in blocks or accepting transactions out of band. The full path and cost comparison is retained in Appendix C.

### 4.4 Pruning does not remove the archival problem

Pruned nodes are not directly constrained by a 2 TB archival disk because they keep only a small rolling window of block data. They still need the historical chain during IBD, and they need archival peers to supply it. A network made entirely of pruned nodes cannot bootstrap a new node from genesis.

There is also no deployed storage equivalent of the mitigations available elsewhere. SeF proposes a coded archival architecture that could reduce per-node historical storage dramatically [\[62\]](#ref-62), but it is not deployed. For the period modelled here, archival chain storage remains cumulative.

---

## 5. How much to trust the storage forecast

The first-cycle result does not need a storage-price forecast. The multi-generation result does.

![Storage cost per gigabyte, 1956–2026, with a distributional forecast to 2066](figures/fig-storage-outlook.png)

*Historical storage cost with forecast confidence intervals. Model: [`models/storage/`](models/storage).*

The model uses three annual improvement rates: **5%, 10% and 15%**, each decaying by 2% of itself per year. The 10% base case is anchored to the 2014–2026 observed CAGR of about 10.2%. The pessimistic case is close to the much weaker 2019–2026 period, while 15% assumes a return toward stronger pre-2020 improvement.

These rates are intentionally far below the historical headline versions of Moore's Law or Kryder's Law. That matters because Kryder's Law already failed as a practical price forecast. HDD cost improvement slowed sharply after roughly 2010, and by 2020 actual storage costs were orders of magnitude above the old extrapolated curve [\[13\]](#ref-13)[\[14\]](#ref-14)[\[15\]](#ref-15)[\[16\]](#ref-16).

### The near-term evidence is mixed

Consumer SSD prices bottomed around $0.05/GB in mid-2023 and had risen to about $0.11/GB by January 2026. NAND input prices also rose sharply through 2025 as AI-related demand competed for manufacturing capacity [\[3\]](#ref-3)[\[4\]](#ref-4). Industry sources describe demand growth materially ahead of supply growth, with new fabrication capacity arriving only gradually [\[31\]](#ref-31)[\[32\]](#ref-32)[\[33\]](#ref-33).

That makes a rapid return to very high consumer storage improvement rates hard to assume. It does not prove a permanent plateau.

NAND still has technical room to scale. Manufacturers are moving toward much higher layer counts [\[5\]](#ref-5)[\[6\]](#ref-6)[\[7\]](#ref-7), and new storage paradigms may eventually reset the curve. But denser storage is not automatically cheap consumer storage. DNA, glass and ceramic systems are currently aimed at archival or data-centre use, not $300 home nodes [\[68\]](#ref-68)[\[69\]](#ref-69)[\[70\]](#ref-70)[\[71\]](#ref-71).

The opposite error is possible too. Long technological forecasts routinely miss paradigm shifts. Historical datasets spanning tape, disk and flash show much faster improvement than any single technology curve [\[66\]](#ref-66)[\[67\]](#ref-67), and forecasting research finds uncertainty widening rapidly with horizon [\[63\]](#ref-63)[\[64\]](#ref-64).

### The long-term result depends on one uncertain variable

![Node storage capacity against chain growth across eight decades and three improvement rates](figures/fig-storage.png)

*The cross-generational view: stepped capacity, one purchase every ten years, against linear chain growth. Model: [`models/storage/charts.py`](models/storage/charts.py).*

At roughly **10% annual storage improvement**, capacity growth eventually pulls away from linear blockchain growth and each replacement cycle gains headroom. At 5% or below, that separation weakens and the current chain-growth trajectory can become unsustainable after a small number of hardware generations.

For the first cycle the sources converge. Rosenthal's long-term storage model [\[72\]](#ref-72), the IEEE roadmap [\[68\]](#ref-68) and Wikibon's Wright's Law analysis [\[65\]](#ref-65) all land in the 8 to 12% range, with the 10% base case in the middle.

This is the cleanest way to state the forecast:

- **First ten years:** relatively high confidence, because the 111 GB/year ceiling is dominated by current measurements and arithmetic.
- **Later generations:** increasingly uncertain, because the result becomes dominated by the future improvement rate of cheap consumer storage.

The detailed forecast scenarios and probability estimates are in Appendix C. They are informed estimates rather than model-generated probabilities.

---

## 6. The other constraints do not bind

### 6.1 Bandwidth speed

![Required IBD bandwidth against residential internet supply](figures/fig-bandwidth.png)

*Model: [`models/bandwidth/`](models/bandwidth).*

Only the IBD download scales strongly with chain size. Following the tip needs roughly 3 KB/s with compact blocks, and ordinary peer serving is around 2 Mbps. Downloading the current 724 GB chain inside seven days requires about **9.8 Mbps**. Even the data-heavy year-10 scenario needs only around **30 Mbps**.

Global median residential broadband is roughly 104 Mbps and has been improving much faster than chain growth [\[48\]](#ref-48)[\[59\]](#ref-59). Very slow connections already struggle with IBD today, but for most existing node-hosting regions, bandwidth speed is not the first constraint to fail.

Bandwidth **cost** is a different problem and is treated separately in Section 7.

### 6.2 IBD processing time

![Chain size against the seven-day processing limit](figures/fig-ibd.png)

*Model: [`models/ibd/`](models/ibd).*

On the N100 reference machine, IBD processing is dominated by the historical AssumeValid phase and tracks chain size more closely than transaction composition. Under the current trajectory, year-10 sync time is about **5.6 days**. The data-heavy scenario reaches about **9.9 days**.

The processing ceiling lands around **116–117 GB/year** on static hardware, only slightly above the 111 GB/year storage ceiling. With modest software improvement it moves much further out. In either case, the reference disk fills before processing time becomes the binding problem.

This constraint also has active mitigations. AssumeUTXO is already in Bitcoin Core and can reduce time-to-usable to hours by loading a validated chainstate snapshot before historical validation finishes [\[44\]](#ref-44). SwiftSync is proposed and could improve IBD further [\[43\]](#ref-43). I treat those as upside rather than as requirements for the storage result. Past software optimisation has been essential to keeping IBD tractable, and the rate of that improvement has slowed [\[23\]](#ref-23).

### 6.3 UTXO set and RAM

![UTXO chainstate growth scenarios against available RAM](figures/fig-utxo.png)

*Model: [`models/utxo/`](models/utxo).*

The current chainstate is about 11 GB, close to the amount a 16 GB machine can cache after the operating system takes its share. Once it grows beyond available RAM, more UTXO lookups hit disk. Benchmarks show that can make IBD materially slower, but it is a performance gradient rather than a functional cutoff [\[42\]](#ref-42).

Even ordinary growth pushes the chainstate beyond current free RAM within a ten-year cycle. That still does not make the node unusable. Once synced, lookup demand is much lower, and each hardware generation brings more memory.

The UTXO set also has relief mechanisms that archival storage does not. The count has already fallen from its January 2025 peak, large numbers of low-value inscription outputs could potentially be consolidated or cleaned up, and Utreexo proposes replacing the conventional chainstate with a compact accumulator [\[24\]](#ref-24)[\[45\]](#ref-45)[\[46\]](#ref-46)[\[47\]](#ref-47).

An adversary can create UTXOs far faster than the organic scenarios, but a UTXO-maximising block and a chain-storage-maximising block are different constructions. The attacker cannot maximise both pressures with the same block.

---

## 7. Affordability and decentralisation are different questions

The $300 machine and seven-day sync target describe a population with access to cheap hardware and reasonably priced broadband. That is not the whole world.

> **Not modelled.** The figures in this section are sourced, but I have not built a chain-growth model for affordability. Treat this as a scope argument, not a fifth hardware result.

In some metered markets, downloading the chain can cost more than the node itself. Using the source data in Appendix C, the estimated one-time IBD cost is about **$2,540 at the Sub-Saharan African regional average**, about **$514 in Nigeria**, and about **$65 in India**. Those figures vary enormously by country and tariff, but the direction is clear: chain growth hurts most where data is already expensive.

That is a serious access problem. It does not automatically overturn the aggregate decentralisation result.

Independent P2P measurement attributes about **0.3% of reachable Bitcoin nodes to Africa and 1.0% to South America**, or 1.3% combined [\[60\]](#ref-60). The low share predates the inscription-driven increase in block size and is tied to broader differences in income, hardware imports and connectivity. Chain growth can worsen that exclusion, but it did not create it.

There is an important limitation to using node share this way. Coercion resistance depends on geographic and jurisdictional spread as well as raw count. A region with few nodes can still add meaningful jurisdictional diversity. Reachable-node measurements also omit nodes behind NAT or firewalls, and that undercount is unlikely to be geographically uniform.

So the bounded conclusion is narrower than "affordability does not matter". It is that **metered bandwidth does not currently explain enough of the observed node population for it to replace storage as the binding aggregate constraint in this model**.

---

## 8. What would change the findings

The 111 GB/year ceiling moves directly when its inputs move:

- **Higher budget.** Around $400–500 can buy substantially more storage. With 4 TB, the ten-year storage ceiling roughly doubles and the single-cycle problem largely disappears.
- **Shorter service life.** At eight years the ceiling rises to about 139 GB/year. At seven years it is about 159 GB/year.
- **More usable disk space.** Reducing the ext4 reservation moves the ten-year ceiling only modestly, to roughly 119 GB/year.

The multi-generation result is more sensitive. If cheap consumer storage returns to sustained improvement above roughly 15% per year, later hardware generations gain headroom much faster than the base case. If improvement stalls near 0–5%, the long-run result worsens.

The ordering between storage and IBD could also change if Bitcoin Core's sync performance stops improving or regresses. The UTXO result worsens if high UTXO creation returns and persists.

### The operator may prune instead of upgrade

The model treats a full disk as an upgrade event, but real operators have easier options. They can stop running the node or enable pruning at no hardware cost.

That makes the model potentially optimistic. Better storage value in 2040 does not mean an operator wants to open the box, migrate data, spend more money or maintain a machine they expected to leave alone. The Pi 4 transition is a warning: the ecosystem largely moved on from the platform rather than continually upgrading it.

About 89% of reachable nodes currently advertise archival service and about 11% are pruned [\[61\]](#ref-61). If pruning becomes the dominant response to storage pressure, archival density can fall even while the total number of validating nodes looks healthy.

### Limitations

This paper models one deliberately cheap configuration rather than the median node. It holds growth constant inside each scenario even though actual demand arrives in waves. The sustained data-heavy case has not been observed for years at a time.

The UTXO scenarios depend on future transaction mix. Long-range storage forecasts depend on technologies and manufacturing economics that are inherently hard to forecast.

The paper also does not model Lightning capacity, fee-market sustainability, mining centralisation, or long-run software optimisation. Each interacts with Bitcoin's scaling trade-offs, but none is needed to calculate the first-cycle storage ceiling.

---

## 9. Objections

### "Home nodes do not matter because miners dominate consensus propagation"

Propagation and enforcement are different functions. A home node does not need to be central to block propagation to enforce consensus rules for its operator. Full nodes enforce by rejecting invalid blocks, not by being important routers [\[57\]](#ref-57).

### "Pruned nodes validate identically, so storage is not a decentralisation problem"

Pruned nodes do validate identically. They still need the historical chain to bootstrap, and they rely on archival peers to supply it. The protocol does not enforce a minimum archival population [\[58\]](#ref-58)[\[61\]](#ref-61).

### "$300 is too low; most serious operators spend more"

A larger budget materially improves the result. That is why $300 is useful as a stress test rather than a claim about the median operator. At roughly $500, 4 TB storage can remove the first-cycle ceiling under the scenarios modelled here.

But increasing the minimum spend is itself part of the decentralisation question. "More expensive hardware solves it" cannot by itself answer whether chain growth raises the participation floor.

### "Ten years is too long for consumer hardware"

It may be. At eight years the storage ceiling rises from 111 to about 139 GB/year, and at seven years to about 159 GB/year. The current trajectory then passes comfortably.

That objection weakens the first-cycle result but not the broader method. Whatever replacement interval is chosen, the question remains whether chain growth forces upgrades faster than cheap hardware improves.

---

## 10. Related work

The tension between block space cost and decentralisation is well recognised [\[53\]](#ref-53)[\[54\]](#ref-54)[\[55\]](#ref-55). This paper tries to put numbers on where it starts to bind.

Gencer et al. [\[59\]](#ref-59) measured Bitcoin and Ethereum decentralisation through bandwidth, latency, geography and mining concentration. This paper focuses on a different layer of the problem: the resource burden on the individual node operator and how that burden changes over time.

Wu's 2014–2025 infrastructure-resilience work [arXiv:2602.14372] looks at network-level health, while this analysis asks what hardware conditions would cause nodes to stop joining or remaining archival.

Croman et al. [FC 2016] identified throughput and bootstrap time as fundamental resource constraints in decentralised blockchains. Their constraint-based framing is close to the approach here, but predates both inscriptions and the recent reversal in NAND pricing.

Kiffer et al. [\[60\]](#ref-60) provide the geographic node measurements used to bound the metered-bandwidth argument in Section 7.

Voskuil [\[56\]](#ref-56) states the theoretical trade-off directly: higher validation cost reduces decentralisation. This paper attempts to put numbers around where that pressure becomes operationally binding.

---

## 11. Conclusion

For a $300 archival node expected to last ten years, **storage is the first hardware constraint to bind**. The reference 2 TB SSD can absorb about **111 GB of new chain data per year**. The observed trajectory is below that level, but not by much: today's average block size is only 28% below the break point, and March 2024 already produced a monthly average above it.

The other constraints are less severe. Bandwidth speed improves faster than chain growth for most current node-hosting regions. IBD processing reaches its limit slightly after storage and has active software mitigations. UTXO growth can slow validation but does not create the same hard operating cutoff and has several independent paths to relief.

Over multiple hardware generations, the outlook is better if consumer storage continues improving near the base-case rate. Compound capacity growth then outpaces linear chain growth and headroom expands. The confidence in that statement falls rapidly beyond the first decade because future storage economics dominate the result.

The near-term risk is therefore not a slow, inevitable collapse in node decentralisation. It is a period of sustained data-heavy demand, fully compatible with current consensus rules, that shortens the life of cheap archival hardware from roughly ten years to five or six. If operators respond by pruning rather than upgrading, the loss appears first in archival capacity rather than in headline validating-node counts.

---

## Appendix A: evidence chain

Ranked by evidence type: on-chain measurement, controlled benchmark, observed market data, model output, industry forecast.

| Input | Evidence type | Refs | Status |
|---|---|---|---|
| Chain size (724 GB, March 2026) | On-chain measurement | [\[25\]](#ref-25), [\[61\]](#ref-61) | Established |
| Chainstate (11 GB, 169M entries) | On-chain measurement | [\[24\]](#ref-24) | Established |
| Bytes per UTXO entry (63) | On-chain measurement | [\[24\]](#ref-24) | Established |
| Block size and inscription impact | On-chain measurement | [\[38\]](#ref-38), [\[39\]](#ref-39), [\[40\]](#ref-40) | Established |
| OP_RETURN data trends | On-chain measurement | [\[41\]](#ref-41) | Established |
| UTXO composition and growth | On-chain measurement | [\[24\]](#ref-24), [\[45\]](#ref-45), [\[46\]](#ref-46), [\[47\]](#ref-47) | Established |
| IBD rate (12 GB/hr, N100) | Controlled benchmark | [\[42\]](#ref-42) | Established |
| Node density (archival vs pruned) | Network observation | [\[58\]](#ref-58), [\[61\]](#ref-61) | Established |
| Target hardware ($300) | Observed market data | [\[49\]](#ref-49), [\[50\]](#ref-50) | **Contested (medium)** |
| Upgrade cycle (10 years) | Market data + inference | [\[50\]](#ref-50), [\[51\]](#ref-51), [\[52\]](#ref-52) | **Contested (medium)** |
| SSD cost trend and improvement rates | Observed market data | [\[17\]](#ref-17), [\[18\]](#ref-18), [\[19\]](#ref-19), [\[34\]](#ref-34) | Established |
| SSD price reversal (2023–2026) | Observed market data | [\[4\]](#ref-4), [\[18\]](#ref-18), [\[31\]](#ref-31) | Established |
| Residential bandwidth trends | Observed market data | [\[48\]](#ref-48) | Established |
| HDD S-curve deceleration | Market data (historical) | [\[8\]](#ref-8), [\[9\]](#ref-9), [\[10\]](#ref-10), [\[11\]](#ref-11) | Established |
| Kryder's Law breakdown | Market data (historical) | [\[13\]](#ref-13), [\[14\]](#ref-14), [\[15\]](#ref-15), [\[16\]](#ref-16) | Established |
| NAND oligopoly coordination | Observed market data | [\[20\]](#ref-20), [\[21\]](#ref-21), [\[22\]](#ref-22) | Established |
| NAND scaling outlook | Industry forecast | [\[5\]](#ref-5), [\[6\]](#ref-6), [\[7\]](#ref-7), [\[12\]](#ref-12) | Established trend, contested timeline |
| AI NAND shortage (2025–2028) | Industry forecast | [\[3\]](#ref-3), [\[31\]](#ref-31), [\[32\]](#ref-32), [\[34\]](#ref-34), [\[36\]](#ref-36), [\[37\]](#ref-37) | Established now, contested duration |
| Metered bandwidth costs | Observed market data | ITU 2024, Cable.co.uk | **Not modelled** |

The 111 GB/year ceiling rests on current measurements and arithmetic. The claim that later hardware generations gain headroom depends much more heavily on future storage improvement. If the storage forecast is wrong, the multi-generation conclusion moves while the first-cycle ceiling remains.

---

## Appendix B: models

Standalone Python, no dependencies beyond numpy and matplotlib for chart generation.

```text
models/
├── chart_style.py              shared figure styling
├── storage/
│   ├── model.py                storage ceiling
│   ├── charts.py               80-year cross-generational view
│   ├── charts_nearterm.py      first-cycle view (fig-storage-nearterm)
│   └── capacity-overlay.py     probabilistic capacity overlay
├── ibd/       model.py, charts.py
├── bandwidth/ model.py, charts.py
└── utxo/      charts.py
```

Run any chart script directly to regenerate its figure into `figures/`. `capacity-overlay.py` produces `fig-storage-capacity-probabilistic.png`, supplementary to the charts embedded above.

---

## Appendix C: supplementary calculations

This appendix keeps the detailed scenario tables and derivations out of the main reading path without removing them from the paper.

### C.1 Chain-growth scenarios

| Scenario | Chain growth | What it assumes |
|---|---|---|
| Monetary only | ~55 GB/year | No data-storage demand, payments and settlement only |
| Current trajectory | ~80 GB/year | Observed average since 2023 |
| Sustained data-heavy | ~196 GB/year | Inscription-heavy blocks, ~3.82 MB average |

Every full block uses the same 4 million weight-unit budget, but the number of bytes written to disk depends on transaction composition. For the inscription model, each transaction carries 481 weight units of fixed overhead and the remaining weight is payload.

For *N* inscription transactions averaging *D* bytes of payload:

*N* = 3,999,108 / (481 + *D*)

block size = 250 + *N* × (199 + *D*) bytes

| Inscription mix | Avg payload | Txs/block | Block size |
|---|---|---|---|
| All BRC-20 text | 75 B | ~7,200 | ~2.0 MB |
| Observed peak (90% text, 10% images by count) | ~2.2 KB | ~1,500 | ~3.6 MB |
| Image-heavy (~73% text, ~27% images) | ~5.8 KB | ~635 | **~3.82 MB** |
| All images | 21 KB | ~186 | ~3.95 MB |
| Single inscription (Slipstream) | ~4 MB | 1 | ~4.0 MB |

BRC-20 mints remain relatively small even when a block is full by weight because transaction overhead is large relative to their payload. Images use the weight budget more efficiently as stored bytes. At the observed inscription peak, roughly 10% of inscriptions were images by count. Raising that mix to about 27% produces the 3.82 MB sustained data-heavy scenario. Inscription-size evidence is in [\[40\]](#ref-40).

### C.2 Storage sensitivity to average block size

| Avg block size | Growth rate | Chain at year 10 | Disk margin | Context |
|---|---|---|---|---|
| 1.11 MB | 57 GB/yr | 1,294 GB | 540 GB | Pre-inscription baseline, 2022 |
| 1.69 MB | 87 GB/yr | 1,591 GB | 243 GB | Current |
| **2.16 MB** | **111 GB/yr** | **1,834 GB** | **~0 GB** | **Ceiling breach** |
| 2.29 MB | 118 GB/yr | 1,899 GB | −65 GB | Observed peak, March 2024 |
| 2.75 MB | 141 GB/yr | 2,136 GB | −302 GB |  |
| 3.82 MB | 196 GB/yr | 2,680 GB | −892 GB | Sustained data-heavy |

### C.3 Deliberate chain-filling paths

```text
ROOT: Sustain avg block > 2.16 MB
├── [OR] Witness inscription flooding
│     Fill blocks with witness-heavy data (~3.82 MB sustained)
│     Requires: outbidding competing monetary transactions
├── [OR] OP_RETURN flooding
│     Non-witness data counts 4x by weight, so this is less storage-efficient
├── [OR] Out-of-band submission
│     Submit oversized transactions directly to cooperating miners
│     Bypasses relay and mempool policy
└── [OR] Miner self-stuffing
      Miners fill their own blocks with witness-heavy data
      Cost is the opportunity cost of displaced fee-paying transactions
```

Illustrative pricing at 5 sat/vB and $100,000/BTC:

| Path | Cost per year | Chain growth | Effect |
|---|---|---|---|
| Witness inscription, 3.82 MB avg | ~2,628 BTC (~$263M) | ~196 GB/yr | Disk full in ~5.7 years |
| Witness inscription, 2.16 MB avg | ~1,500 BTC (~$150M) | 111 GB/yr | Ceiling reached at year 10 |
| OP_RETURN | ~2,628 BTC (~$263M) | ~51 GB/yr | Below ceiling, about 4x less storage-efficient |
| Out-of-band | Negotiated | Up to 196 GB/yr | Bypasses policy filters |
| Miner self-stuffing | Opportunity cost only | Up to 196 GB/yr | No direct fee payment |

### C.4 Storage-improvement assumptions

| Scenario | Initial rate | Anchor | Rationale |
|---|---|---|---|
| Optimistic | 15%/yr | 2011–2026 CAGR (17.6%) | Shortage normalises and NAND scaling continues, but not at earlier peak rates |
| Base | 10%/yr | 2014–2026 CAGR (10.2%) | Twelve observed years through two shortage cycles |
| Pessimistic | 5%/yr | 2019–2026 CAGR (4.3%) | Structural AI demand and weaker NAND cost improvement persist |

The model decays each annual improvement rate by 2% of itself per year.

The original forecast communication scenarios are retained below. The probabilities are informed estimates, not model output.

| Scenario | Rate | 10-year multiplier | Probability | Basis |
|---|---|---|---|---|
| Stall | 0–2%/yr | 1.0–1.2x | ~10% | NAND follows HDD to plateau, no consumer-priced successor |
| Pessimistic | ~5%/yr | 1.6x | ~25% | Current short-term trend continues |
| Base | ~10%/yr | 2.6x | ~35% | Full-cycle CAGR, near-term evidence |
| Optimistic | ~15%/yr | 4.0x | ~20% | Requires stronger manufacturing expansion |
| Paradigm shift | 20%+/yr | 6.2x+ | ~10% | New storage technology reaches consumer pricing |

### C.5 Metered-bandwidth examples

| Region | Cost/GB | One-time IBD cost | Min sync (4.5 GB/mo) | Serving peers (~30 GB/mo) |
|---|---|---|---|---|
| Sub-Saharan Africa (avg) | $3.51 | ~$2,540 | ~$16/mo | ~$105/mo |
| Zimbabwe | $43.75 | ~$31,675 | ~$197/mo | ~$1,313/mo |
| Kenya | $0.84 | ~$608 | ~$3.80/mo | ~$25/mo |
| Nigeria | $0.71 | ~$514 | ~$3.20/mo | ~$21/mo |
| Bangladesh | ~$0.32 | ~$232 | ~$1.44/mo | ~$10/mo |
| India | ~$0.09 | ~$65 | ~$0.41/mo | ~$2.70/mo |

These figures are not part of the four-constraint model. They illustrate why adequate connection **speed** and affordable connection **cost** are separate questions.

### C.6 Operator response when storage fills

| Response | Effort | Cost | Network effect |
|---|---|---|---|
| Stop running a node | None | None | One fewer node |
| Prune | One configuration change | None | Keeps validating, stops retaining full history |
| Upgrade | Money, time, physical access | $200–400 | Keeps validating and serving history |

---

## References

<a id="ref-1"></a>[1] Nakamoto, S. "Bitcoin: A Peer-to-Peer Electronic Cash System." 2008. https://bitcoin.org/bitcoin.pdf

<a id="ref-2"></a>[2] Nakamoto, S. "Re: BitDNS and Generalizing Bitcoin." BitcoinTalk, 10 December 2010. https://satoshi.nakamotoinstitute.org/posts/bitcointalk/threads/244/#246

<a id="ref-3"></a>[3] TrendForce. "NAND Flash Q1 2026 price forecast." January 2026. https://www.trendforce.com/presscenter/news/20260105-12860.html

<a id="ref-4"></a>[4] Tom's Hardware. "Perfect storm of demand and supply driving up storage costs." 2025. https://www.tomshardware.com/pc-components/storage/perfect-storm-of-demand-and-supply-driving-up-storage-costs

<a id="ref-5"></a>[5] Semi Engineering. "NAND Flash Targets 1,000 Layers." https://semiengineering.com/nand-flash-targets-1000-layers/

<a id="ref-6"></a>[6] Lam Research. "1,000 Layers NAND Etch." https://newsroom.lamresearch.com/1000-layers-NAND-etch

<a id="ref-7"></a>[7] TrendForce. "SK Hynix Unveils 2029-2031 Roadmap Featuring HBM5, GDDR7 Next, and 400-Layer NAND." November 2025. https://www.trendforce.com/news/2025/11/04/news-sk-hynix-unveils-2029-2031-roadmap-featuring-hbm5-gddr7-next-and-400-layer-nand/

<a id="ref-8"></a>[8] National Academies of Sciences, Engineering, and Medicine. "Decadal Survey of Astronomy and Astrophysics 2020: Data, Computing, and the Evolving Cyberinfrastructure." National Academies Press, 2024. https://www.nationalacademies.org/read/27445/chapter/3

<a id="ref-9"></a>[9] StorageNewsletter. "Has HDD Areal Density Stalled?" April 2022. https://www.storagenewsletter.com/2022/04/19/has-hdd-areal-density-stalled/

<a id="ref-10"></a>[10] Computer History Museum. "HDD Areal Density Reaches 1 Terabit/sq. in." https://www.computerhistory.org/storageengine/hdd-areal-density-reaches-1-terabit-sq-in/

<a id="ref-11"></a>[11] Backblaze. "Hard Drive Cost Per Gigabyte." https://www.backblaze.com/blog/hard-drive-cost-per-gigabyte/

<a id="ref-12"></a>[12] Semi Engineering. "3D NAND Race Faces Huge Tech and Cost Challenges." https://semiengineering.com/3d-nand-race-faces-huge-tech-and-cost-challenges/

<a id="ref-13"></a>[13] Scientific American. "Kryder's Law." https://www.scientificamerican.com/article/kryders-law/

<a id="ref-14"></a>[14] The Register. "Kryder's Law of Ever-Cheaper Storage Disproven." November 2014. https://www.theregister.com/2014/11/10/kryders_law_of_ever_cheaper_storage_disproven/

<a id="ref-15"></a>[15] Rosenthal, D. "Patting Myself on the Back." DSHR's Blog, July 2017. https://blog.dshr.org/2017/07/patting-myself-on-back.html

<a id="ref-16"></a>[16] Rosenthal, D. "Storage Media Update." DSHR's Blog, November 2020. https://blog.dshr.org/2020/11/storage-media-update.html

<a id="ref-17"></a>[17] Mead, M. "RAM/HDD/SSD Prices." DigiPen Institute of Technology. https://azrael.digipen.edu/~mmead/www/Courses/CS180/ram-hd-ssd-prices.html

<a id="ref-18"></a>[18] StorageDiskPrices. "SSD Price History." https://storagediskprices.com/ssd-price-history/

<a id="ref-19"></a>[19] howmuch.one. "Average SSD 1TB NVMe Price History." https://howmuch.one/product/average-ssd-1tb-nvme/price-history

<a id="ref-20"></a>[20] TrendForce. "NAND Flash Revenue, Q3 2025." December 2025. https://www.trendforce.com/presscenter/news/20251203-12813.html

<a id="ref-21"></a>[21] Mordor Intelligence. "NAND Flash Memory Market." https://www.mordorintelligence.com/industry-reports/nand-flash-memory-market

<a id="ref-22"></a>[22] TrendForce. "NAND Giants Reportedly Cut Output in 2H25 as Prices Surge." November 2025. https://www.trendforce.com/news/2025/11/13/news-nand-giants-reportedly-cut-output-in-2h25-as-prices-surge-samsung-mulls-20-30-hike-in-2026/

<a id="ref-23"></a>[23] BitMEX Research. "Bitcoin's Initial Block Download." https://www.bitmex.com/blog/bitcoins-initial-block-download

<a id="ref-24"></a>[24] Mempool Research. "UTXO Set Report." April 2025, block 892,385. https://research.mempool.space/utxo-set-report/

<a id="ref-25"></a>[25] CoinLedger. "Bitcoin Blockchain Size and Growth Over Time." 2025. https://coinledger.io/research/bitcoin-blockchain-size-and-growth-over-time

<a id="ref-31"></a>[31] Tom's Hardware. "Phison CEO confirms NAND prices have more than doubled." January 2026. https://www.tomshardware.com/pc-components/ssds/phison-ceo-confirms-nand-prices-have-more-than-doubled-and-will-continue-to-rise-all-2026-production-already-sold-out-ssds-facing-pricing-apocalypse-throughout-2027

<a id="ref-32"></a>[32] Tom's Hardware. "Phison CEO claims NAND shortage could last a staggering 10 years." https://www.tomshardware.com/pc-components/ssds/phison-ceo-claims-nand-shortage-could-last-a-staggering-10-years-says-memory-supercycle-imminent-and-severe-2026-shortages-are-at-hand

<a id="ref-33"></a>[33] Oreton Storage. "Global NAND Supply Update Q4 2025." https://oretonstorage.com/blog/global-nand-supply-update-q4-2025-whats-shaping-ssd-prices-ahead

<a id="ref-34"></a>[34] IDC. "Global Memory Shortage Crisis: Market Analysis." 2026. https://www.idc.com/resource-center/blog/global-memory-shortage-crisis-market-analysis-and-the-potential-impact-on-the-smartphone-and-pc-markets-in-2026/

<a id="ref-36"></a>[36] OSCOO. "Will SSD Prices Drop in 2026?" https://www.oscoo.com/news/will-ssd-prices-drop-in-2026/

<a id="ref-37"></a>[37] NAND Research. "Memory Flash Crisis Update, March 2026." https://nand-research.com/memory-flash-crisisc-update-march-2026/

<a id="ref-38"></a>[38] JBBA. "Bitcoin Ordinals and Inscriptions: An Analysis of Bitcoin's Evolving Network Dynamics." 2024. https://jbba.scholasticahq.com/api/v1/articles/153840-bitcoin-ordinals-and-inscriptions-an-analysis-of-bitcoin-s-evolving-network-dynamics.pdf

<a id="ref-39"></a>[39] ScienceDirect. "Bitcoin Ordinals: Determinants and impact on total transaction fees." 2024. https://www.sciencedirect.com/science/article/abs/pii/S0275531924001314

<a id="ref-40"></a>[40] CryptoSlate. "Data on Taproot Ordinals points to higher Bitcoin fees, chain bloat." 2023. https://cryptoslate.com/data-on-taproot-ordinals-points-to-higher-bitcoin-fees-chain-bloat/

<a id="ref-41"></a>[41] CoinDesk. "Bitcoin Core 30 to Increase OP_RETURN Data Limit." 2025. https://www.coindesk.com/tech/2025/06/10/bitcoin-core-30-to-increase-op_return-data-limit-after-developer-debate-concludes

<a id="ref-42"></a>[42] Lopp, J. "2025 Bitcoin Node Performance Tests." https://blog.lopp.net/2025-bitcoin-node-performance-tests/

<a id="ref-43"></a>[43] Somsen, R. "SwiftSync: Speeding Up IBD with Pre-generated Hints." Delving Bitcoin, 2025. https://delvingbitcoin.org/t/swiftsync-speeding-up-ibd-with-pre-generated-hints-poc/1562

<a id="ref-44"></a>[44] Bitcoin Optech. "AssumeUTXO." https://bitcoinops.org/en/topics/assumeutxo/

<a id="ref-45"></a>[45] Dryja, T. "Utreexo: A dynamic hash-based accumulator optimized for the Bitcoin UTXO set." ePrint 2019/611. https://eprint.iacr.org/2019/611.pdf

<a id="ref-46"></a>[46] Bitcoin Magazine. "Bitcoin's Growing UTXO Problem and How Utreexo Can Help Solve It." https://bitcoinmagazine.com/technical/bitcoins-growing-utxo-problem-and-how-utreexo-can-help-solve-it

<a id="ref-47"></a>[47] IEEE GLOBECOM. "Prediction-based UTXO Cache Optimization for Bitcoin Lightweight Full Nodes." 2021. https://ieeexplore.ieee.org/document/9685843/

<a id="ref-48"></a>[48] Lopp, J. "Revisiting Bitcoin Network Bandwidth Issues." 2023. https://blog.lopp.net/revisiting-bitcoin-network-bandwidth-issues/

<a id="ref-49"></a>[49] Athena Alpha. "Best Bitcoin Node Hardware." 2024. https://www.athena-alpha.com/bitcoin-node-hardware/

<a id="ref-50"></a>[50] Start9 Community. "Raspberry Pi no longer recommended for use with Bitcoin stack." https://community.start9.com/t/raspberry-pi-no-longer-recommended-for-use-with-bitcoin-stack/779

<a id="ref-51"></a>[51] Stacker News. "Nobody should suggest using a Raspberry Pi for running a Bitcoin node in 2023." https://stacker.news/items/186832

<a id="ref-52"></a>[52] The Bitcoin Manual. "Migrating BTC Pi Node." https://thebitcoinmanual.com/articles/migrating-btc-pi-node/

<a id="ref-53"></a>[53] Lopp, J. "A Treatise on Bitcoin Block Space Economics." 2024. https://blog.lopp.net/treatise-bitcoin-block-space-economics/

<a id="ref-54"></a>[54] Buterin, V. "Some reflections on the Bitcoin block size war." May 2024. https://vitalik.eth.limo/general/2024/05/31/blocksize.html

<a id="ref-55"></a>[55] Blockonomi. "Full Nodes & Block Size: Keeping Validation Costs Low." https://blockonomi.com/full-nodes-block-size-keeping-validation-costs-low-in-bitcoin/

<a id="ref-56"></a>[56] Voskuil, E. "Scalability Principle." Cryptoeconomics, libbitcoin wiki. https://github.com/libbitcoin/libbitcoin-system/wiki/Scalability-Principle

<a id="ref-57"></a>[57] "The Redundancy of Full Nodes in Bitcoin." arXiv:2506.14197. June 2025. https://arxiv.org/abs/2506.14197

<a id="ref-58"></a>[58] D-Central. "Understanding the Role of Archival and Pruned Nodes in the Decentralization of Bitcoin." https://d-central.tech/understanding-the-role-of-archival-and-pruned-nodes-in-the-decentralization-of-bitcoin/

<a id="ref-59"></a>[59] Gencer, A.E., Basu, S., Eyal, I., van Renesse, R., Sirer, E.G. "Decentralization in Bitcoin and Ethereum Networks." FC 2018. arXiv:1801.03998. https://arxiv.org/abs/1801.03998

<a id="ref-60"></a>[60] Kiffer, L., Salman, A., Levin, D., Mislove, A., Nita-Rotaru, C. "36 Coins: Measuring P2P Network Structure and Health." SIGMETRICS 2026. arXiv:2511.15388. https://arxiv.org/abs/2511.15388

<a id="ref-61"></a>[61] Bitnodes. "Reachable Bitcoin Nodes." Snapshot March 2026. https://bitnodes.io/nodes/

<a id="ref-62"></a>[62] Kadhe, S., Chung, J., Ramchandran, K. "SeF: A Secure Fountain Architecture for Slashing Storage Costs in Blockchains." arXiv:1906.12140. 2019. https://arxiv.org/abs/1906.12140

<a id="ref-63"></a>[63] Nagy, J.B., Farmer, J.D., Bui, Q.M., Trancik, J.E. "Statistical Basis for Predicting Technological Progress." PLoS ONE 8(2): e52669, 2013. https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0052669

<a id="ref-64"></a>[64] Lafond, F., Bailey, A.G., Bakker, J.D., Rebois, D., Zadourian, R., McSharry, P., Farmer, J.D. "How Well Do Experience Curves Predict Technological Progress? A Method for Making Distributional Forecasts." Technological Forecasting and Social Change 128: 104-117, 2018. https://arxiv.org/abs/1703.05979

<a id="ref-65"></a>[65] Floyer, D. "SSDs Will Crush Hard Drives." Wikibon / Blocks & Files, January 2021. https://blocksandfiles.com/2021/01/25/wikibon-ssds-vs-hard-drives-wrights-law/

<a id="ref-66"></a>[66] Kurzweil, R. "The Singularity Is Near: When Humans Transcend Biology." Viking, 2005.

<a id="ref-67"></a>[67] McCallum, J.C. "Disk Drive Prices (1955-2024)." https://jcmit.net/diskprice.htm

<a id="ref-68"></a>[68] IEEE International Roadmap for Devices and Systems. "Mass Data Storage." 2023. https://irds.ieee.org/images/files/pdf/2023/2023IRDS_MDS.pdf

<a id="ref-69"></a>[69] DNA Data Storage Alliance (SNIA). "DNA Data Storage Technology Landscape." 2025.

<a id="ref-70"></a>[70] Microsoft Research. "Project Silica: Storing Data in Glass." Nature, February 2026. doi: 10.1038/s41586-025-10042-w

<a id="ref-71"></a>[71] Rosenthal, D. "Archival Storage." DSHR's Blog, March 2025. https://blog.dshr.org/2025/03/archival-storage.html

<a id="ref-72"></a>[72] Rosenthal, D. "An Economic Model of Long-Term Digital Storage." UNESCO Memory of the World Conference, 2012. https://www.fsl.cs.sunysb.edu/docs/unesco12/UNESCO2012-storage-econ.pdf
