# OriginalityBond

Register content by staking native GEN on the claim that it isn't derivative of anything already registered. Anyone can dispute that by naming a specific prior entry and staking their own money on being right. GenLayer consensus decides who was, and the loser's stake pays the winner.

Live on StudioNet: `0xF45259B199164952B7E855186B0f02e12a6DD16b` — [explorer](https://explorer-studio.genlayer.com/address/0xF45259B199164952B7E855186B0f02e12a6DD16b) · [open in Studio](https://studio.genlayer.com/?import-contract=0xF45259B199164952B7E855186B0f02e12a6DD16b)

---

## A number that shaped this design

Before writing the adjudication logic, I measured how well raw embedding distance alone tracks "is this a copy":

| Pair | Relationship | Distance* |
|---|---|---|
| "…premium wireless headphones… ANC… thirty hours battery…" vs "…high-end wireless headphones… ANC noise cancelling… thirty-hour battery…" | close paraphrase | 674 |
| A bread recipe vs a semiconductor earnings report | topically unrelated | 566 |
| Portland's climate vs Seattle's climate, written independently | same topic, no copying | 436 |

*milli-units of squared Euclidean distance on 384-dim sentence embeddings — lower means the model thinks the texts are more alike.

The unrelated pair scored **closer** than the actual paraphrase. The independently-written same-topic pair scored closer still. If this contract used distance as its verdict, it would have called two strangers who happened to both write about West Coast weather more suspicious than an actual reworded copy.

That number is why the architecture below exists: distance is a triage signal, cheap and deliberately trigger-happy, deciding only whether a real judgement is worth paying for. It never gets to render the verdict itself.

## What two people are actually fighting about

A registrant and a challenger are staking money against each other's claim. One of them is about to lose it. A platform operator judging between them isn't neutral — they profit either way. A pure similarity cutoff can't do it either, per the table above. A single off-chain LLM call can be re-rolled until it says what its caller wants. An optimistic-oracle-plus-human-dispute flow works but costs days per case, which kills it for a registry meant to process ordinary volume.

What actually settles it: several validators, independently, each reading both pieces of content and forming their own opinion — with the transaction only landing if their opinions agree on the category. Nobody involved, including whoever deployed this contract, gets to author that agreement.

This is also why it isn't the shape of thing that gets rejected. The output isn't advice for a human — it's a typed verdict that routes real money in the same transaction. The equivalence principle isn't checking that JSON parses — it requires the *category* (ORIGINAL / DERIVATIVE / INCONCLUSIVE) to match, so a well-formed response with the wrong verdict still fails consensus. And the two pieces of content being judged aren't a claim about the outside world submitted by one party and taken on faith — they're the artifacts themselves, both already committed on-chain before either side gains anything from tampering.

## The one thing that needs a model, and the fifteen things that don't

There is exactly one question in this contract with no deterministic answer: *does CANDIDATE derive from PRIOR, or was it created independently?* Both places that question gets asked — the automatic post-registration review, and a paid challenge — call the same single method, `_judge_derivation`, so there's one equivalence-principle block in the whole file to audit.

Everything else is code doing arithmetic on a stored integer:

- **The embedding itself is deterministic.** `SentenceTransformer` runs a fixed ONNX model with no sampling step — tokenise, run the network, done. It's called directly with no consensus wrapper for the same reason `Keccak256` is: nothing for validators to disagree about.
- **The nearest-neighbour search is deterministic** — cover-tree k-NN over vectors that were themselves produced deterministically.
- Threshold checks, bond minimums, timeout math, payout routing, every access check — ordinary Python.

**Money only moves as a function of a stored verdict integer, never the other way around.** `_settle_challenge` reads `outcome` and does exactly one of two things with it. Take away the consensus round and there's no `outcome` to read — the function has nothing to act on, the contract is inert. Take away the settlement code and `outcome` is just a number sitting in storage that never reaches anyone's balance. Neither half does anything alone.

The distance gate makes the same point in miniature: it's *entirely* deterministic, and its only power is to say "look at this one" — never "this is a copy." Only the round says that.

```
register(title, content)  payable, deterministic
   embed → knn(k=8) → skip dead hits → nearest live match, or none
   no match within threshold ─────────────────────────▶ ACTIVE, done
   match within threshold ────────────────────────────▶ PENDING_REVIEW
                                                              │
                            resolve_review(id)  permissionless, one round
                                    exec_prompt(candidate, prior)
                                    prompt_comparative(EQ_DERIVATION)
                          DERIVATIVE ──┬── ORIGINAL / INCONCLUSIVE
                    REJECTED, stake    │   ACTIVE — no adversary has
                    to prior's owner   │   staked anything on a system flag
                                       ▼
                          open_challenge(id, prior_id)  payable, deterministic
                          entry → CHALLENGE_PENDING
                                       │
                          resolve_challenge(id)  permissionless, one round
                              (same _judge_derivation, same principle)
                          DERIVATIVE ──┬── ORIGINAL / INCONCLUSIVE
                REJECTED, stake        │   ACTIVE again, challenger's
                to the challenger      │   bond to the entry's owner
```

Every deterministic gate sits *before* a round starts or *after* it lands — never inside. A caller who's never flagged never pays for a round at all. A flagged caller pays for the review in its own, separate, permissionless transaction, so `register()` itself always stays fast. A challenge nobody ever resolves doesn't strand the bond forever — `reclaim_stale_challenge` settles it on a plain clock check, with exactly the same economic outcome as a losing challenge.

The equivalence principle, verbatim:

> Both outputs judge whether the same CANDIDATE content is a derivative reproduction of the same PRIOR content, or an independently created work. They are equivalent if and only if they report the same verdict: ORIGINAL, DERIVATIVE, or INCONCLUSIVE. Differences in the wording of the reasoning, or in the confidence band, do not matter. A different verdict means they are NOT equivalent.

## What stops this from going wrong

- An unparseable verdict leaves the entry exactly where it was — `PENDING_REVIEW` or `CHALLENGE_PENDING` — so the next call can still resolve it. Nothing is ever inferred from a parse failure.
- An unreadable verdict string defaults to INCONCLUSIVE, never DERIVATIVE — guessing wrong in that direction takes someone's real money.
- The vector index never calls `.remove()`. `VecDB.insert()` reuses the integer ids of anything removed, so a stored reference to a removed id could silently point at a completely different later entry. This contract sidesteps that by never removing anything and keying every external reference on its own monotonic `entry_id` space instead of a VecDB id.
- Similarity search skips REJECTED and WITHDRAWN hits and keeps widening until it finds a live one — a dead claim is never mistaken for standing prior art.
- Withdrawal is open right up until a challenger has bonded money against the entry, and refused the instant they have — a challenger who paid to dispute a claim can't have the target vanish out from under them.
- A challenge nobody resolves settles deterministically once its timeout passes, with the same payout as a losing challenge — a bond can never be stuck waiting on a resolver who never shows up.
- A reactivated entry can be challenged again later — winning once doesn't grant permanent immunity from better evidence.
- Every payout coerces its recipient through `isinstance(x, Address)` before use. Calldata delivers addresses as hex strings, and assigning one straight into a payout call raises on a real network while passing quietly in a hand-built direct-mode test — the exact bug that shipped in a sibling primitive's example contract before it was caught.

## Building on it

The whole integration surface:

```python
@gl.contract_interface
class IOriginalityBond:
    class View:
        def get_entry(self, entry_id: u256) -> dict: ...

entry = IOriginalityBond(registry_address).view().get_entry(entry_id)
if int(entry["status"]) == 1:   # ACTIVE
    ...
```

[`examples/listing_gate.py`](examples/listing_gate.py) puts that to work: a marketplace that refuses to list anything whose backing claim isn't currently ACTIVE. It has no embeddings, no `exec_prompt`, no equivalence principle, and needs no special runner dependency — none of that is its problem to solve. It reads one status field twice: once to admit a new listing, once (`is_still_backed`) so a UI can notice a listing's backing claim getting overturned by a later challenge.

Everything downstream of that one read differs only by what the caller does with `status`:

| Consumer | Reads | Registry stays |
|---|---|---|
| Marketplace listing gate | `get_entry` before admitting a listing | unchanged |
| Bounty dedup | `get_entry` before paying out a submission | unchanged |
| Prior-art search | `preview_similarity` only, never registers | unchanged |
| Plagiarism bounty platform | the challenge bond *is* the bounty | unchanged |

The policy that actually differs between these — how eager the auto-flag threshold is, how large a challenge bond has to be, how long a challenge stays open — is a constructor argument, not a constant, so a stricter deployment for high-value claims and a looser one for casual use are two deployments of identical code, not two forks of it.

**Where this isn't the right tool:** the distance gate is noisy by the measurement at the top of this document — tune it generously wherever missing a real derivative would hurt. `MAX_ENTRIES` (5000) is a real cap that isn't exercised end to end here, since reaching it costs 5000 real embeddings. And `resolve_review`/`resolve_challenge` are retryable, not guaranteed to land first try — a round can come back `UNDETERMINED`, in which case nothing was written and the call needs repeating.

## Running it yourself

```bash
pip install genvm-linter genlayer-test
export GENVM_VERSION=v0.3.0-rc7   # embeddings only exist from this SDK version on

GENVM_VERSION=v0.3.0-rc7 genvm-lint check contracts/originality_bond.py --json
python -m pytest tests/direct/ -v
gltest tests/integration/ -v -s --network studionet
```

Windows: prefix lint/download commands with `PYTHONIOENCODING=utf-8`, or the ✓ glyph crashes the console.

**One CLI gap worth knowing before you hit it:** `genlayer write` (CLI v0.39.2) has no flag for sending native value — only `--fee-value`, which is the gas deposit, not `gl.message.value`. Every payable method here was exercised through `genlayer-js`'s `writeContract({..., value})`, not the bare CLI. Script against `genlayer-js` directly if you need to call `register` or `open_challenge` outside a dApp.

### What's tested and how

40 direct tests. Embedding generation and vector search run for real in every single one of them — they're deterministic contract logic, not something worth mocking — and only the derivation verdict itself is mocked. All 40 finish in under 5 seconds, after a one-time ~50-second runner extraction the first time this repo's tests run on a machine.

Coverage: every constructor guard; the fast-path/flagged-path split under both a forced-loose and a forced-strict policy, plus one test that registers identical content under the *default* policy and trusts real embedding behaviour rather than a forced threshold; every review outcome including unparseable and fenced-JSON model output; withdrawal's full access-and-state matrix; the challenge lifecycle including re-challenging a reactivated entry; and the stale-challenge timeout on both sides of its boundary using a `warp_to` helper documented in `conftest.py` that works around a real gap in `direct_vm.warp()`.

Three integration tests against live StudioNet consensus:

- **Convergence** — the same content, embedded independently by two separate transactions, produces a byte-identical distance both times, and genuinely different content measures a thousand times further away, not closer.
- **Full surface** — all 6 writes and all 5 views, in lifecycle order, against one deployment, with every refusal confirmed to actually refuse on-chain.
- **Timeout on the real clock** — a 3-second policy timeout, exceeded naturally by StudioNet's own round-trip time rather than by an artificial sleep.

**One of those tests initially passed for the wrong reason.** The convergence test's own registration call was missing `value=` and its receipt was never checked, so it silently reverted; `preview_similarity` then correctly reported "no neighbour" for every comparison — including the self-comparison, which at a glance looked exactly like a working deterministic result. The fix was two lines: check the receipt, pass the value. It's recorded here rather than quietly patched, because a convergence test that never actually registers anything will still say PASSED.

### On chain right now

Every write method has been run against the deployed address above: `register` twice, `resolve_review`, `open_challenge`, `resolve_challenge`, `withdraw`, plus refusals for a repeat review, a repeat withdrawal, and a self-referential challenge.

A real verdict from that deployment, verbatim:

> "The CANDIDATE ('Second') addresses a completely different subject (deep-sea hydrothermal vent ecosystems) from the PRIOR ('First,' which discusses a community garden rotation schedule). There is no overlap in specific expression, structure, phrasing, sequence of ideas, or distinguishing details. The works share no substantive similarities beyond being original content on unrelated topics."

`ORIGINAL`, confidence `HIGH` — reached independently twice on the same pair, once by the automatic review and once again by a paid challenge, the second time in different words but the same conclusion:

> "The two works share no commonality in subject matter, structure, or phrasing. PRIOR concerns community garden logistics, while CANDIDATE concerns deep-sea marine biology. There is no evidence of reproduction."

## API

**Writes** — `register(title, content) payable → u256` (deterministic unless flagged) · `resolve_review(entry_id)` (permissionless, one round) · `open_challenge(entry_id, prior_entry_id) payable` (deterministic) · `resolve_challenge(entry_id)` (permissionless, one round) · `reclaim_stale_challenge(entry_id)` (permissionless, deterministic) · `withdraw(entry_id)`

**Views** — `get_entry` · `get_challenge` · `preview_similarity` (no stake, no round) · `entry_count` · `is_challenge_stale`

**Constructor** — `OriginalityBond(auto_flag_distance_milli=550, min_challenge_bond_bps=2000, challenge_timeout_seconds=604800)`, every value a deployment-time policy choice, none hardcoded.

## In this repo

```
contracts/originality_bond.py   the primitive
examples/listing_gate.py        a consumer with no embeddings machinery of its own
tests/direct/                   40 tests, real embeddings, mocked verdicts
tests/integration/               3 tests against live StudioNet consensus
tests/conftest.py                Windows workarounds, the warp_to helper
DECISION_RECORD.md               how this idea was chosen over eleven others
```
