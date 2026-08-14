# ScopeLock resubmission verification

Fresh local verification was run from a shallow, blob-filtered, sparse checkout of public GitHub `main`. GitHub Actions and other CI were intentionally not used.

| Item | Result |
|---|---|
| Run timestamp | `2026-08-15T00:04:59.7703613+01:00` (Africa/Lagos) |
| Public GitHub commit tested | `5dbc38c1626425049f555d0651fe59213b5c6aab` |
| Working-tree scope during frontend checks | Evidence-expiry timer fix only; contract unchanged |
| Direct Mode command | `python -m pytest tests/direct -v` |
| Python | `3.12.13` |
| genlayer-test / gltest | `0.29.2` |
| Direct Mode result | `14 passed in 6.09s` |
| Candidate audit | PASS: `candidate_count: 1`, `validated_count: 1`, `unexpected_candidates: 0` |
| GenVM lint | PASS: `Lint passed (3 checks)` |
| Frontend install | PASS: `npm ci`; 373 packages, 0 vulnerabilities |
| Frontend lint | PASS: `npm run lint` |
| Frontend typecheck | PASS: `npx tsc --noEmit` |
| Frontend production build | PASS: `npm run build`; 10 routes generated |
| Contract diff | Empty |
| Contract SHA-256 | `ecd525571e8e79fc309388bf5730fba2cbe3a5825c7f2568891f72340e13f067` |

The Direct Mode suite executed `contracts/scopelock.py` through gltest with mocked nondeterministic inputs. No contract source change or redeployment was performed.

## Reproduction

```powershell
python -m pytest tests/direct -v
./scripts/check-contract-candidates.ps1
genvm-lint lint contracts/scopelock.py
cd frontend
npm ci
npm run lint
npx tsc --noEmit
npm run build
```
