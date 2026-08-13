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

- `/` — concise index and network proof
- `/programs`, `/programs/new`, `/programs/[id]` — live program ledger, creation, and dossier
- `/programs/[id]/submit` — exact bond read from contract and shared injected-wallet write
- `/disclosures`, `/disclosures/[id]` — public ledger and Scope Rail dossier
- `/precedent` — settled-valid possible precedents (semantic distance is not duplicate)
- `/settlements` — final on-chain payout/refund/slash ledger

The persistent application shell owns the sole production wallet identity. Browser-generated/local-storage wallets are absent. Every payable action uses the connected injected wallet, waits for finalization, and fails clearly when `NEXT_PUBLIC_SCOPELOCK_CONTRACT` is missing.

## Contract API

Writes: `create_program`, `top_up`, `pause_program`, `close_program`, `submit_report`, `adjudicate`, `add_supplementary_evidence`, `expire_needs_evidence`.

Views: full bounded `get_program`, `get_report`, `preview_precedents`, counts, and paginated `list_program_ids`, `list_report_ids`, and `list_program_report_ids`.

## Release proof

- Network: StudioNet
- Contract: `0x6114bcC2eAeFbD4f83dB9EC35693cde067a60bfB`
- Deploy tx: `0xaa374c3bbae62accae0bb69215c7ed7284c657e532a15e0ea183ee73c4d6e245`
- Source SHA-256: `a3ff06a24cb6b13e26029c8457da42a7cae51f4455430986287e42747cc02165`

The deployed source was retrieved after deployment and matched the evidence-fetch/deadline implementation markers. `DEPLOYMENT.json` is the machine-readable binding; `scripts/verify-deployment-source.ps1` validates the local frozen hash.

## Verification

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\Scripts\genvm-lint.exe" check contracts/scopelock.py
./scripts/check-contract-candidates.ps1
python -m pytest tests/direct -v
cd frontend; npm run lint; npx tsc --noEmit; npm run build
```

The candidate audit finds exactly one candidate: `contracts/scopelock.py`. The prior rejection came from tracked pytest helper imports being interpreted as contract candidates; the test compatibility shim now avoids runtime SDK imports, while the audit enforces the single-candidate invariant.

Current direct suite: 4 passing lifecycle/read tests. This repository does not yet claim a live report-adjudication transaction with public web retrieval, so it does not claim that a validator-fetch lifecycle proof has been completed.
