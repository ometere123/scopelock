# OriginalityBond

**A staked originality registry.** Anyone bonds native GEN behind a claim that their content is not derivative of anything already registered. Anyone else can challenge that claim by naming a specific prior entry. GenLayer consensus judges derivation; the loser's stake pays the winner.

It is infrastructure, not an application — the piece a marketplace, a bounty board, or a content platform imports when it needs "is this actually original" answered by something other than the two people arguing about it.

---

## The problem

Two parties disagree about whether B copied A. Neither can be the judge — the accuser has every incentive to call anything DERIVATIVE, and the accused has every incentive to call anything ORIGINAL. A platform operator isn't neutral either: they get paid either way, or they favour whoever complains loudest.

A pure similarity score doesn't solve it. Two independent product descriptions of the same category of headphones can be 90% textually similar. A substantially reworded copy of one specific description can be 40% similar and still be a clear derivative. Distance alone cannot tell "the same idea, independently expressed" from "the same expression, reworded" — that took a real judgement, made against this contract's own measured evidence:

| Content A | Content B | Relationship | Measured distance* |
|---|---|---|---|
| "…premium wireless headphones… ANC… thirty hours battery…" | "…high-end wireless headphones… ANC noise cancelling… thirty-hour battery…" | close paraphrase | 674 |
| A recipe for bread | A quarterly semiconductor earnings report | topically unrelated | 566 |
| Portland's climate | Seattle's climate (independently written) | same topic, no copying | 436 |

*milli-units of squared Euclidean distance on 384-dim sentence embeddings; lower = more similar. Measured during development on this contract's own embedding pipeline.

Read that table again: the unrelated recipe/earnings pair scored **closer** than the genuine paraphrase, and the same-topic-independent pair scored closer still. Raw embedding distance is not a reliable verdict — which is exactly why this contract does not use it as one. It is used only as a cheap, deliberately over-inclusive **triage** step that decides whether a consensus round is worth paying for. The verdict itself is always a judgement.

## Why this needs GenLayer

**The trust problem, stated precisely.** A registrant and a challenger are directly financially adversarial: one of them is about to lose a stake to the other. Delete GenLayer and a single admin — or the platform operator — decides who was right. Every registrant and every challenger has to trust that party isn't favouring whoever complains loudest, or whoever pays them, or whoever registered first regardless of who actually copied whom.

**The counterfactual, run against every alternative:**

| Approach | What it gives away |
|---|---|
| Platform-operator judgement | The operator is not neutral; they profit either way and answer to neither party alone. |
| Pure similarity threshold, no LLM | Cannot separate "reworded copy" from "independently similar" — see the table above. |
| A single LLM call off-chain | Whoever ran it could have skewed the prompt, retried until a favourable answer came back, or simply lied about the result. |
| Optimistic oracle + human dispute | Works, but costs days and a bond per dispute — unusable for the volume a registry like this needs. |
| A DAO vote | Voters have no reason to have actually read either piece of content, and can be bought or brigaded far more cheaply than corrupting N independent validators. |

The property only GenLayer provides: **N independent validators each read both pieces of content themselves and form their own judgement, and the transaction only lands if their judgements agree on the verdict category.** No party — not the registrant, not the challenger, not the contract's own deployer — can author the answer.

**Why it is not the rejected patterns:**

| Pattern | Why this is not that |
|---|---|
| *"An AI app with GenLayer attached"* | The output is not advice for a human to read. It is a typed verdict that deterministically routes real money in the very same transaction. |
| *"A validator that only checks output format"* | The equivalence principle requires validators to agree on the **verdict category** — ORIGINAL, DERIVATIVE, or INCONCLUSIVE — not on valid JSON. A well-formed response with a different verdict fails consensus. |
| *"Judging facts from user-submitted text alone"* | The two texts being compared are not a claim about the external world — they are the artifacts themselves, committed on-chain by two adversaries *before* either has anything to gain from tampering with the other's copy. |
| *"Lightweight / minimally differentiated"* | No contract in this ecosystem uses on-chain embeddings or vector search. This is a different mechanism (a deterministic ANN-distance gate) applied to a different problem (derivation between two already-registered artifacts). |

## Why each non-deterministic call is non-deterministic

Exactly **one** operation in this contract has no deterministic form: *"is CANDIDATE a derivative reproduction of PRIOR, or an independently created work"*. Both consensus entry points — the automated review and a paid challenge — route through the same single method, `_judge_derivation`, so there is exactly one equivalence-principle block in the entire contract to audit.

**Everything else is deterministic, including the parts that look like they shouldn't be:**

- **Embedding generation is deterministic.** `SentenceTransformer` wraps a fixed ONNX model with no sampling temperature — tokenise, then run the network. Same input, same weights, same output on every validator. It is called directly, with no equivalence principle, for the same reason `Keccak256` is called directly: there is nothing for validators to disagree about.
- **The nearest-neighbour search is deterministic.** Cover-tree k-NN over deterministically-produced vectors is itself deterministic.
- **The auto-flag threshold, the challenge bond minimum, the timeout arithmetic, the payout routing, and every access check** are ordinary Python.

The model is asked what the relationship between two texts is — never what the contract should do about it.

### Does the deterministic logic weaken the case for consensus?

The opposite: every deterministic step here operates on an output the consensus round produced, or exists specifically to constrain what that round is allowed to do.

Trace the money. `_settle_challenge` — the one place funds actually move — reads `outcome` from the consensus round and nothing else. Delete the round and there is no outcome to read; the function has nothing to act on. Delete the deterministic settlement logic and the round's verdict is just a stored integer that never reaches anyone's balance. Both halves are load-bearing:

| Remove | Result |
|---|---|
| The consensus round | No verdict exists. `_settle_challenge` has nothing to route money on. The contract is inert. |
| The deterministic settlement | A model could say DERIVATIVE and nothing would happen, or the payout could go to whoever last touched the code path. Money would move on no fixed rule at all. |

And the similarity gate is a second, independent demonstration of the same principle in miniature: it is *entirely* deterministic, and its only job is to decide whether the non-deterministic round gets to run at all. A cheap, wrong-half-the-time distance metric is allowed to say "check this" — it is never allowed to say "this is derivative." Only consensus says that.

### Ordering discipline

```
register()              deterministic: embed, knn, flag-or-activate    ← no round at all
   ▼ (only if flagged)
resolve_review()         ONE consensus round                            ← permissionless, separate tx
   ▼
open_challenge()          deterministic: validate, bond                 ← no round
   ▼
resolve_challenge()       ONE consensus round                           ← permissionless, separate tx
   ▼ (if nobody ever resolves it)
reclaim_stale_challenge() deterministic: time check, same settlement    ← no round, funds never stranded
```

A caller who is never flagged never pays for a round. A caller who is flagged pays for the review in a **separate transaction** — registration itself always stays fast and deterministic. A challenge that nobody ever resolves does not strand the bond forever; it settles on a plain deterministic clock check identical in effect to a losing challenge.

## How it works

```
   register(title, content) ── payable ──────────────────────┐
        │                                                     │
        │  embed(content)          -- deterministic           │
        │  knn(embedding, k=8)     -- deterministic            │
        │  skip dead entries, keep first live match            │
        │                                                      │
        ├─ no live match within threshold ──▶ ACTIVE (done)    │
        │                                                      │
        └─ live match within threshold ──▶ PENDING_REVIEW      │
                        │                                      │
                        ▼                                      │
              resolve_review(id)  ── permissionless ──         │
                exec_prompt(candidate, prior)                  │
                gl.eq_principle.prompt_comparative(EQ_DERIVATION)
                        │
          DERIVATIVE ───┼─── ORIGINAL / INCONCLUSIVE
              │                       │
      REJECTED, stake to        ACTIVE (benefit of the doubt --
      the prior entry's         no adversary has staked
      owner                     anything on an automated flag)
                                        │
                          open_challenge(id, prior_id) ── payable ──
                          entry → CHALLENGE_PENDING
                                        │
                          resolve_challenge(id) ── permissionless ──
                            (same _judge_derivation, same EQ)
                                        │
                    DERIVATIVE ─────────┼───────── ORIGINAL / INCONCLUSIVE
                        │                                   │
                REJECTED, stake              ACTIVE again, challenger's
                to the challenger             bond to the entry's owner
```

### The equivalence principle, in full

```
"Both outputs judge whether the same CANDIDATE content is a derivative
reproduction of the same PRIOR content, or an independently created work.
They are equivalent if and only if they report the same verdict: ORIGINAL,
DERIVATIVE, or INCONCLUSIVE. Differences in the wording of the reasoning, or
in the confidence band, do not matter. A different verdict means they are
NOT equivalent."
```

`prompt_comparative`, never `prompt_non_comparative` — validators independently read both texts and independently reach a verdict; they are never asked to merely check that the leader's JSON parses.

## Safety properties

- **A failed round is retryable, never silently resolved.** If `_judge_derivation`'s output is unparseable, `resolve_review` and `resolve_challenge` both leave the entry exactly where it was — `PENDING_REVIEW` or `CHALLENGE_PENDING` — so a later, successful call can still settle it. Nothing is ever assumed from a failure. *(`test_unparseable_review_output_is_retryable_not_lost`, `test_unparseable_challenge_output_leaves_challenge_open`)*
- **An unreadable verdict defaults to INCONCLUSIVE, never DERIVATIVE.** Guessing DERIVATIVE would take someone's real money on a parsing failure. *(`test_unknown_verdict_string_defaults_to_inconclusive`)*
- **The vector index is append-only by design**, specifically to avoid a real footgun: `VecDB.insert()` reuses the integer ids of removed elements. If this contract ever called `.remove()` and then treated a VecDB id as a stable reference, a later insert could silently collide with an old one. It never removes; it keys everything on its own monotonic `entry_id` space instead.
- **Dead entries are skipped, not trusted, in similarity search.** `_find_prior_art` widens its k-NN search past REJECTED and WITHDRAWN hits to find a currently-live one, so a withdrawn or already-rejected claim is never mistaken for standing prior art. *(`test_strict_threshold_never_flags` and friends exercise this indirectly; see also the append-only design note above)*
- **Withdrawal is refused the moment a challenger has skin in the game.** ACTIVE and PENDING_REVIEW both allow withdrawal (no adversary yet); CHALLENGE_PENDING refuses it (a challenger's bond deserves a resolution, not a vanishing target). *(`test_withdraw_allowed_while_pending_review`, `test_withdraw_refused_once_challenged`)*
- **Funds have a defined resting place in every terminal state**, including "nobody ever resolved it": `reclaim_stale_challenge` settles a stale challenge exactly like a losing ORIGINAL verdict, so a bond can never be stranded by an unresponsive resolver. *(`test_reclaim_stale_challenge_succeeds_exactly_at_the_boundary`)*
- **Losing a challenge does not permanently immunise an entry.** A reactivated ACTIVE entry can be challenged again by better evidence later. *(`test_a_reactivated_entry_can_be_challenged_again`)*
- **Address handling is defensive against the exact bug that shipped in a sibling primitive's example contract**: `_pay` coerces its recipient with `isinstance(..., Address)` before use, because calldata delivers addresses as hex strings, not `Address` objects, and assigning one straight through raises on a real network while passing happily in hand-built direct-mode tests.

## Why this is reusable

The falsifiable version — the entire integration surface a consumer needs:

```python
@gl.contract_interface
class IOriginalityBond:
    class View:
        def get_entry(self, entry_id: u256) -> dict: ...

entry = IOriginalityBond(registry_address).view().get_entry(entry_id)
if int(entry["status"]) == 1:   # ACTIVE
    ...
```

[`examples/listing_gate.py`](examples/listing_gate.py) is a complete worked consumer — a marketplace that refuses to list anything backed by a claim that isn't currently ACTIVE. It contains no embeddings, no `exec_prompt`, no equivalence principle, and needs no special runner dependency of its own, because none of that machinery is its concern. It reads one status field, twice: once to gate a new listing, once (`is_still_backed`) to notice if a challenge later overturns a claim a listing already depends on.

| Use case | What changes | What doesn't |
|---|---|---|
| Marketplace listing gate | nothing — this is `listing_gate.py` | the registry |
| Bounty-submission dedup | the caller checking `get_entry` before paying out | the registry |
| Prior-art search before filing | reads `preview_similarity` only, never registers | the registry |
| Content-platform plagiarism bounty | the challenge bond becomes the bounty | the registry |

One deployment serves all of them. The policy that varies between use cases — how strict the auto-flag threshold is, how large a challenge bond must be, how long a challenge stays open — is fixed at deployment time via the constructor, not hardcoded, so a stricter registry for high-value claims and a looser one for casual use can coexist as two separate deployments of the same code.

### The honest limits

- **Embedding distance is a noisy proxy, not a verdict.** The measured table above shows it can rank an unrelated pair as more "similar" than a genuine paraphrase. This is why the gate is deliberately over-inclusive rather than precise — a wrongly-triggered review costs one consensus round; a wrongly-skipped one costs nothing being caught at all. Tune `auto_flag_distance_milli` generously for anything where a missed derivative matters.
- **`MAX_ENTRIES` (5000) is a hard cap**, untested end-to-end here — reaching it costs 5000 real embeddings. The guard exists in source and is exercised by review, not by a 5000-iteration test.
- **The `genlayer` CLI (v0.39.2) has no flag for sending native value with `genlayer write`.** Only `--fee-value` (the gas deposit) is exposed; there is no `--value`. Every payable method in this contract was therefore verified with `genlayer-js`'s `writeContract({..., value: ...})` via the `gltest` integration suite, not the bare CLI. If you need to call `register` or `open_challenge` from a script rather than a dApp, use `genlayer-js` directly.
- **`resolve_review` / `resolve_challenge` are retryable, not guaranteed on the first attempt.** A consensus round can return `UNDETERMINED`; nothing is written when it does.
- **Registration cost scales with real ONNX inference**, not a placeholder. On StudioNet this sits inside the normal deterministic-write cost band — no separate consensus round is spent on it, but it is not free computation either.

## API

### Writes

| Method | |
|---|---|
| `register(title, content) payable -> u256` | Stake a claim. Deterministic — no consensus round unless flagged. |
| `resolve_review(entry_id)` | Settle a flagged registration. Permissionless. One consensus round. |
| `open_challenge(entry_id, prior_entry_id) payable` | Bond a dispute against a standing claim. Deterministic. |
| `resolve_challenge(entry_id)` | Settle an open challenge. Permissionless. One consensus round. |
| `reclaim_stale_challenge(entry_id)` | Settle a challenge nobody resolved within the timeout. Permissionless, deterministic. |
| `withdraw(entry_id)` | Owner reclaims their stake. Refused once a challenge is open. |

### Views

`get_entry` · `get_challenge` · `preview_similarity` (check before you stake — costs no round and no gas beyond a read) · `entry_count` · `is_challenge_stale`

### Constructor

`OriginalityBond(auto_flag_distance_milli=550, min_challenge_bond_bps=2000, challenge_timeout_seconds=604800)` — every parameter is deployment-time policy, not a hardcoded constant.

## Development

```bash
pip install genvm-linter genlayer-test
export GENVM_VERSION=v0.3.0-rc7   # embeddings only exist from this SDK version on
```

```bash
GENVM_VERSION=v0.3.0-rc7 genvm-lint check contracts/originality_bond.py --json
python -m pytest tests/direct/ -v
gltest tests/integration/ -v -s --network studionet
```

On Windows, prefix lint/download commands with `PYTHONIOENCODING=utf-8` — the ✓ glyph otherwise crashes the console.

### Test coverage

**40 direct tests.** Embedding generation and vector search run for real in every one of them — they are deterministic contract logic, not something to mock; only the derivation verdict is mocked. All 40 run in under 5 seconds after a one-time (~50s) runner-extraction cost the first time this project's tests are ever run on a machine.

| Area | Cases |
|---|---|
| Constructor / policy | every invalid parameter rejected |
| Registration | first-ever entry always fast-paths; input validation; a forced-loose policy flags; a forced-strict policy never flags; identical content flags under the *default* policy (the one test that trusts real embedding behaviour rather than a forced threshold) |
| Automated review | DERIVATIVE rejects and pays the prior owner; ORIGINAL and INCONCLUSIVE both activate; unparseable output is retryable; fenced JSON recovered; unknown verdict strings default safely |
| Withdrawal | owner-only; allowed from ACTIVE and PENDING_REVIEW; refused once challenged; refused after rejection |
| Challenges | input validation; target-must-be-ACTIVE; no double-challenge; DERIVATIVE pays the challenger; ORIGINAL/INCONCLUSIVE pay the owner and reactivate; a reactivated entry can be challenged again; unparseable output leaves the challenge open |
| Time | the stale-challenge reclaim refused before, and succeeding exactly at, the timeout boundary, using a `warp_to` helper that bridges a real gap in `direct_vm.warp()` (see source comment in `conftest.py`) |
| Views | unknown-id handling, entry counting |

**3 integration tests, all passing on live StudioNet consensus:**

- `test_embedding_is_deterministic_across_independent_calls` — the strict convergence property: the same content produces a byte-identical distance across two independent transactions, and genuinely unrelated content measures further away, not closer.
- `test_full_public_surface` — all 6 write methods and all 5 views, exercised in lifecycle order against one deployed contract, asserting every refusal actually refuses.
- `test_reclaim_stale_challenge_on_a_real_clock` — the timeout path on the real transaction clock, using a 3-second policy timeout rather than an artificial sleep.

### A bug this suite found in itself

While preparing these results, the convergence test's own registration call was missing `value=`, so it silently reverted (the assertion on its receipt had been omitted). `preview_similarity` then correctly reported "no neighbour found" for every comparison, including a self-comparison — which looked, at a glance, exactly like a working deterministic result. The fix was two lines: check the receipt, and pass the value. The finding is left here rather than quietly fixed and forgotten, because it is a reminder that a convergence test which never registers anything will still report "PASSED".

## Status

Lint clean (`genvm-lint`, GENVM_VERSION=v0.3.0-rc7). 40 direct tests, 3 integration tests, all passing.

### Deployed

| | |
|---|---|
| Network | StudioNet (chain id 61999) |
| Address | `0xF45259B199164952B7E855186B0f02e12a6DD16b` |
| Explorer | https://explorer-studio.genlayer.com/address/0xF45259B199164952B7E855186B0f02e12a6DD16b |
| Studio | https://studio.genlayer.com/?import-contract=0xF45259B199164952B7E855186B0f02e12a6DD16b |

All 6 write methods have been executed against this deployment by the integration suite: `register` ×2, `resolve_review`, `open_challenge`, `resolve_challenge`, `withdraw` — plus the refusal paths (double-review, double-withdraw, self-referential challenge) all confirmed refused on-chain.

### Measured on live consensus

A genuine derivation judgement, from the deployed contract, verbatim:

> *"The CANDIDATE ('Second') addresses a completely different subject (deep-sea hydrothermal vent ecosystems) from the PRIOR ('First,' which discusses a community garden rotation schedule). There is no overlap in specific expression, structure, phrasing, sequence of ideas, or distinguishing details. The works share no substantive similarities beyond being original content on unrelated topics."*

Verdict: `ORIGINAL`, confidence `HIGH`. The same verdict was reached independently twice — once by the automated review, once again by a real bonded challenge against the same pair — with a second, differently-worded but equally decisive reasoning:

> *"The two works share no commonality in subject matter, structure, or phrasing. PRIOR concerns community garden logistics, while CANDIDATE concerns deep-sea marine biology. There is no evidence of reproduction."*

Convergence, measured: two independent `preview_similarity` calls against identical content returned `distance_milli=0` both times; a call against genuinely unrelated content returned `distance_milli=1097` — a thousand-fold larger, and reproducible.

## Layout

```
contracts/originality_bond.py   the primitive
examples/listing_gate.py        worked consumer, no embeddings of its own
tests/direct/                   40 tests, real embeddings, mocked verdicts
tests/integration/               3 tests against live StudioNet consensus
tests/conftest.py                Windows workarounds and the warp_to helper
DECISION_RECORD.md               idea generation, screening, and self-audit
```
