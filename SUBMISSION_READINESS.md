# ScopeLock submission readiness

## Candidate remediation

The earlier repository was rejected because tracked pytest helpers were detected as GenVM candidates. The audit now permits exactly one tracked candidate, `contracts/scopelock.py`, and validates it. The Windows-only direct-test shim avoids contract-runtime imports so it cannot become an additional candidate.

## Frozen deployment

```text
network: studionet
address: 0x6114bcC2eAeFbD4f83dB9EC35693cde067a60bfB
deployment tx: 0xaa374c3bbae62accae0bb69215c7ed7284c657e532a15e0ea183ee73c4d6e245
contract sha256: a3ff06a24cb6b13e26029c8457da42a7cae51f4455430986287e42747cc02165
```

The deployed code was retrieved and contains the bounded `gl.nondet.web.render` evidence path, pinned-target resolution, and seven-day evidence-deadline path.

## Release gates

| Gate | Result |
|---|---|
| Candidate audit | PASS — one candidate |
| GenVM lint / semantic validation | PASS |
| Direct contract tests | PASS — 4 tests |
| Frontend lint | PASS |
| Typecheck | PASS |
| Production build | PASS |

Honest remaining evidence: StudioNet deployment itself succeeded, but a separate real public-disclosure adjudication transaction has not yet been recorded. It must be performed before claiming an end-to-end live validator-fetch lifecycle proof.
