# Decision record — OriginalityBond

## Candidates generated (12, spanning 5 capabilities)

| # | Candidate | Capability | Value? |
|---|---|---|---|
| 1 | Semantic originality registry: stake a claim, embeddings flag near-duplicates, LLM judges derivation, loser's stake pays the other party | **embeddings/VecDB** | yes |
| 2 | Visual milestone escrow: screenshot-verified delivery releases payable escrow | images | yes |
| 3 | Cross-listing price-consistency oracle: fetch a price from N marketplaces, judge manipulation | web | no |
| 4 | EVM-state-gated payable release: pay out only if a named contract's on-chain state satisfies a judged condition | EVM interop, value | yes |
| 5 | Contract-factory-based bounty board: factory deploys one escrow per bounty, each independently resolved | factories, value | yes |
| 6 | Build-status badge oracle: screenshot a CI dashboard, judge green/red, gate a deploy-approval flag | images, web | no |
| 7 | Semantic API-changelog compatibility gate (already exists in this workspace as `interface-compatibility-oracle` — discard, collision) | web | no |
| 8 | Duplicate-bounty-claim detector: embeddings cluster near-identical bounty submissions across a marketplace to stop the same work being paid for twice | embeddings/VecDB | yes |
| 9 | Cross-contract escalation ladder: contract A's unresolved dispute triggers a payable appeal on contract B via composition | composition, value | yes |
| 10 | Upgrade-governance primitive: N-of-M judged sign-off before `root.upgraders` is allowed to swap contract code | upgradeability | no |
| 11 | Semantic license-compatibility checker: embed two license texts, judge compatibility for redistribution | embeddings/VecDB | no |
| 12 | Screenshot-based accessibility-compliance gate: render a page, judge WCAG-relevant visual issues, gate a listing | images, web | no |

## Self-audit

1. **Distinct capabilities represented:** 5 — embeddings/VecDB (1, 8, 11), images (2, 6, 12), EVM interop (4), factories (5), composition (9), upgradeability (10), web (3, 6, 7, 12). Six if web counts on its own. Well above the 3-capability floor.
2. **Most similar pair:** #1 and #8. Both use embeddings to catch semantic duplicates. #8 is a narrower special case of #1 (bounty submissions are just one kind of claim); #1 subsumes it as a general primitive, so #8 was folded in rather than discarded as noise.
3. **If web access did not exist:** #1 (embeddings-based originality) — it uses no web fetching at all. This was chosen anyway; web access was never the deciding factor.
4. **Strongest discarded candidate:** #4, EVM-state-gated payable release. It is a genuine primitive and passes every gate. Discarded because `calldata-approval-gateway`, already present in this workspace from a parallel session, sits close enough to the same EVM-interop-gating-a-payout territory that building it risked a collision I could not fully rule out without reading that session's contract. #1 had no such adjacency to anything already in the workspace.

## Chosen: OriginalityBond

**One sentence:** A staked originality registry — anyone can bond native GEN behind a claim that their submitted content is not derivative of anything already registered, and anyone can challenge that claim by pointing at a specific prior entry, with GenLayer consensus judging derivation and the loser's stake paying the winner.

**Why not existing workspace projects:** `interface-compatibility-oracle`, `dependency-drift-oracle`, `policy-gate`, `service-uptime-oracle`, `deliverable-acceptance-escrow`, `visual-claim-verifier`, `bonded-claim`, `calldata-approval-gateway`, `policy-bound-executor` — none use on-chain embeddings or vector similarity search. This is a different mechanism (deterministic ANN distance gating a nondet judgment round) applied to a different problem (derivation between two pieces of already-registered content, not an external fact or a delivered artifact).

### Gates

- **A — counterfactual:** delete GenLayer and a single admin (or the registry operator) decides whose claim of originality stands. Every registrant and every challenger must trust that party not to favour whoever pays them, or whoever registered first regardless of who actually copied whom.
- **B — trust problem:** the claimant and the challenger are directly financially adversarial — one of them is about to lose a stake to the other. Neither can be the judge.
- **C — judgement:** "is B a derivative reproduction of A, or an independently created work that happens to be topically similar" is not answerable by a similarity score alone. Two products can be 90% textually similar and be independent (a common industry template) or 40% similar and be a clear derivative (a substantially reworded copy). Only meaning settles it.
- **D — evidence fetched by the contract:** N/A in the web-fetch sense — the "evidence" here is the two pieces of content, both of which are already committed on-chain at registration time, before any dispute exists. Neither party can alter what the other is being compared against after the fact.
- **E — consequential decision:** money moves. A registrant who loses a review or a challenge forfeits their stake; a challenger who loses forfeits their bond.
- **F — originality:** no contract in the ecosystem wall or this workspace does embeddings-gated staked derivation adjudication.
