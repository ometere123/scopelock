# ScopeLock

Public findings. Bound scope. Consensus settlement.

ScopeLock is a GenLayer-native public vulnerability disclosure bounty system. A sponsor locks GEN against an immutable public program scope; a researcher bonds GEN with a public disclosure; permissionless adjudication uses GenLayer consensus to inspect evidence; deterministic contract code applies the fixed payout matrix.

## What validators decide

ScopeLock uses embeddings only to discover candidate precedent. No similarity score can pay, slash, reject, or mark a disclosure duplicate. The final security outcome comes from GenLayer consensus over independently fetched public evidence, and deterministic contract code alone maps the agreed outcome to GEN settlement.

`VALID`, `DUPLICATE`, `KNOWN_ISSUE`, `OUT_OF_SCOPE`, `EXPLOITABILITY_NOT_ESTABLISHED`, and `NEEDS_EVIDENCE` are the only adjudication outcomes. A valid result additionally requires consensus on severity. A duplicate must reference a settled report from the same program.

## Architecture

- `contracts/scopelock.py` is the only GenVM contract candidate.
- `frontend/` is a Next.js App Router application. It has no backend authority or production fixtures.
- `scripts/check-contract-candidates.ps1` prevents the rejection caused by tracked pytest files being interpreted as source.

## Run and verify

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\Scripts\genvm-lint.exe" check contracts/scopelock.py --json
./scripts/check-contract-candidates.ps1
cd frontend; npm run lint; npx tsc --noEmit; npm run build
```

## Deployment

StudioNet contract: `0x00f0ba00fB0a6C12f9b6eFEc2CBEEDC78920BfCf`

Deployment transaction: `0x3fd73ccec23a7fff4b4da4842c693d5821393da72fdd4251668bbc6c0eaf0ada`

Live frontend: https://frontend-five-omega-50.vercel.app

The frontend’s default configuration points to that StudioNet address and supports read-only browsing, injected-wallet connection, a local browser wallet, live count reads, and payable report submission. Browser-wallet keys stay in local storage; export is not yet implemented, so this path is demonstrative rather than custody-grade.

`DEPLOYMENT.json` binds the deployed source to commit `e9c5ad71d875eaf71136cb4ab08c31dfdc3662a7`. Verify the executable source fingerprint with `./scripts/verify-deployment-source.ps1`.
