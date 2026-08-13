# ScopeLock submission readiness

## Previous rejection

> The originality registry is substantive, but the submitted repository does not clear the current GenVM source checks: tracked test candidates were treated as contract source and failed semantic validation on unresolved pytest/conftest imports. Please separate contract source from files that trigger contract-candidate detection, confirm every detected candidate passes current GenVM validation, and resubmit matching source and deployment.

## Remediation

| Concern | Remediation | Evidence |
|---|---|---|
| Test files detected as source | Removed inherited Python test and example candidates from this submission tree | `scripts/check-contract-candidates.ps1` |
| Every candidate must validate | The guard enumerates tracked Python candidates, validates each, and requires exactly one | candidate audit output |
| Source/deployment mismatch | Frozen source SHA and deployment transaction recorded together | `DEPLOYMENT.json` |
| Stale deployment | Fresh ScopeLock deployment on StudioNet | address and tx below |

## Frozen deployment proof

```text
network: studionet
address: 0x00f0ba00fB0a6C12f9b6eFEc2CBEEDC78920BfCf
deployment tx: 0x3fd73ccec23a7fff4b4da4842c693d5821393da72fdd4251668bbc6c0eaf0ada
contract-source commit: e9c5ad71d875eaf71136cb4ab08c31dfdc3662a7
contract sha256: ffc84489c4e6f8b4b428443ea21bc51d8ae08c72de21fcad47f0967425ea4524
```

## Commands run on this release

```text
genvm-lint check contracts/scopelock.py --json: PASS
genvm-lint validate contracts/scopelock.py: PASS
scripts/check-contract-candidates.ps1: PASS
frontend npm run lint: PASS
frontend npx tsc --noEmit: PASS
frontend npm run build: PASS
Vercel production build: READY
```

`genvm-lint typecheck` remains blocked by a missing `pyright` executable in the local Python toolchain. Direct and live integration tests have not been recreated after the source-candidate remediation; they must not be represented as passing.
