# ScopeLock

Public findings. Bound scope. Consensus settlement.

ScopeLock is a GenLayer-native public vulnerability-disclosure bounty protocol. A sponsor funds a time-bound, immutable target and scope in GEN. A researcher posts a public disclosure and exact bond. GenLayer validators independently retrieve bounded public evidence, reach a comparative consensus verdict, and deterministic code applies the payout/refund/slash rule.

## Why GenLayer

A conventional deterministic contract can escrow money, but it cannot inspect a changing public disclosure, a pinned source component, or whether two security reports describe the same root cause. Removing GenLayer from ScopeLock would leave an administrator or oracle deciding those facts. ScopeLock instead asks validators to fetch the supplied disclosure, a pinned GitHub component when applicable, supplementary evidence, and selected same-program precedent disclosures inside the consensus block.

All fetched material is treated as untrusted evidence: the adjudication prompt explicitly ignores instructions, credentials, and policy-changing text found in it. Fetch failures, empty content, malformed model output, and consensus transport failures revert as transient errors; they never settle a report or move GEN.

## Precedent and settlement

Embeddings perform bounded deterministic retrieval only. `preview_precedents` and adjudication select at most three settled VALID reports from the same program and persist their IDs, semantic distances, URLs, components, and metadata. Semantic distance is never a confidence score and can never decide `DUPLICATE`. Validators compare fetched evidence; a duplicate is accepted only when its referenced ID is among those selected candidates and is a settled same-program valid finding.

Deterministic code alone enforces program date windows, exact bonds, sponsor permissions, payout matrix, pool sufficiency, no double settlement, and close/reclaim rules. `NEEDS_EVIDENCE` creates a seven-day future deadline. The researcher may append one public HTTPS URL; after expiry anyone can return the full bond through the explicit safe expiry path. A sponsor cannot close while reports are unresolved and only receives unused bounty pool, never researcher bonds.

## Product surface

- `/`: concise index and network proof
- `/programs`, `/programs/new`, `/programs/[id]`: live program ledger, creation, and dossier
- `/programs/[id]/submit`: exact bond read from contract and shared injected-wallet write
- `/disclosures`, `/disclosures/[id]`: public ledger and state-aware Scope Rail dossier with adjudication, researcher-only supplementary-evidence recovery, post-deadline expiry/refund, and finalized settlement state
- `/precedent`: settled-valid possible precedents (semantic distance is not duplicate)
- `/settlements`: final on-chain payout/refund/slash ledger

The persistent application shell owns the sole production wallet identity. Browser-generated/local-storage wallets are absent. Production writes use the connected injected wallet, wait for finalization, verify `FINISHED_WITH_RETURN` GenVM execution, refresh chain state, and fail clearly when `NEXT_PUBLIC_SCOPELOCK_CONTRACT` is missing. A finalized transaction with failed GenVM execution is never presented as application success.

### Application lifecycle

```text
create program -> submit bonded disclosure -> RUN ADJUDICATION
  -> terminal verdict -> deterministic settlement
  -> NEEDS_EVIDENCE -> researcher adds supplementary public HTTPS evidence
       -> SUBMITTED -> RUN ADJUDICATION -> settlement
  OR deadline passes -> any account expires request -> full bond refund
```

The dossier matches contract authorization exactly: any connected account may adjudicate; only the recorded researcher may supplement evidence before the deadline; and any connected account may expire a request after the deadline. Terminal reports expose no further lifecycle write.

## Contract API

Writes: `create_program`, `top_up`, `pause_program`, `close_program`, `submit_report`, `adjudicate`, `add_supplementary_evidence`, `expire_needs_evidence`.

Views: full bounded `get_program`, `get_report`, `preview_precedents`, counts, and paginated `list_program_ids`, `list_report_ids`, and `list_program_report_ids`.

## Release proof

- Network: StudioNet
- Contract: `0xCCc5f1B4589FF468c300B417f46F782110487a9D`
- Deploy tx: `0xad49482466c2393bb6123cb2b7fef3b81443f75c79a0a40d6ab2529f8ca06c54`
- Source SHA-256: `ecd525571e8e79fc309388bf5730fba2cbe3a5825c7f2568891f72340e13f067`

The deployed source was retrieved after deployment and matched the evidence-fetch/deadline implementation markers. `DEPLOYMENT.json` is the machine-readable binding; `scripts/verify-deployment-source.ps1` validates the local frozen hash.

## Verification

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\Scripts\genvm-lint.exe" check contracts/scopelock.py
./scripts/check-contract-candidates.ps1
python -m pytest tests/direct -v
cd frontend; npm run lint; npx tsc --noEmit; npm run build
```

The candidate audit finds exactly one candidate: `contracts/scopelock.py`. The prior rejection came from tracked pytest helper imports being interpreted as contract candidates; the test compatibility shim now avoids runtime SDK imports, while the audit enforces the single-candidate invariant.

The Direct Mode suite contains 14 tests and passes 14/14. It covers the four original invariants plus VALID/HIGH settlement, KNOWN_ISSUE, exact OUT_OF_SCOPE slashing, EXPLOITABILITY_NOT_ESTABLISHED, NEEDS_EVIDENCE without premature money movement, researcher-only supplementation, re-adjudication after supplementation, premature and post-deadline expiry, invalid duplicate-reference rejection, and terminal re-adjudication protection.

## On-chain proof

Program 1 locked 10 GEN against Express `<4.20.0` `response.redirect()` XSS at immutable commit `04bc62787be974874bc1467b23606c36bc9779ba`, component `lib/response.js`. The evidence preflight verified both the advisory API and raw source with HTTP 200.

| Step | Method | Transaction | Execution / resulting state |
|---|---|---|---|
| Fund program | `create_program` | `0xa7c31068b59fe2e36945841fe370477444431c1cc239512466eb324c6aa2c6a4` | GenVM SUCCESS; Program 1 funded 10 GEN |
| Bond disclosure | `submit_report` | `0x621cf8463429f71088e0eebf8c7d22007a2f3f95cdd7d54f4f97e9a65b6080b9` | GenVM SUCCESS; Report 1 bonded 1 GEN |
| Validator adjudication | `adjudicate` | `0xa305e878583d13e147111d4af8021734891ce0645811938e3573d291fc41babd` | FINALIZED / Accepted / GenVM SUCCESS / empty stderr; `KNOWN_ISSUE`, `NONE` |
| Settlement | finalized transfer | `0x30dc5ed880bc5bd04c7d65620d428f665a19a5287aa6928476e869c58fea8855` | 1 GEN refund to researcher |

The stored evidence summary identifies GHSA-qw6h-vgh9-j6wx / CVE-2024-43796 and the pinned component; reasoning classifies it as a documented known issue. Payout is 0 GEN, refund 1 GEN, slash 0 GEN, and remaining sponsor pool is 10 GEN. The historical 404 attempt `0x9ca276b21f753cc8ff122db38b1fa354f16140488697e9166841273f87630be0` finalized a rollback with no money movement, proving the fail-closed evidence path.
