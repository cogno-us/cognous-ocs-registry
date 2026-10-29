# Final integrated test and qualification plan (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (DEFERRED, NOT WAIVED). Governing: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Plan v1.1 s.12, Engineering Plan v1.5, audit #60, #65/#67, architecture v1.0 (#68, `d7eb6be`).

## Rule
Intermediate development ran schema/canonicalisation, frozen-vector, import, differential, small negative-path suites and required GitHub CI on every PR head. No known failing CI is deferred. After exact-head engineering freeze there is ONE coordinated campaign, and it retains every failure and the baseline delta.

## Campaign scope (all must be exercised against frozen exact heads)
| Area | Evidence required |
|---|---|
| All 19 parameters | per-row result from the crosswalk; BLOCKED rows get negative tests proving they are NOT reachable through any family |
| Cross-family composition | every subset of the six Control Plane families incl. irreversibility, on the real workflow with real signed selections |
| Missing/invalid mandatory policy; host invalidity; attempted widening | forged Registry results, host-invalid classes, flip conflicts |
| Approval and decision commitment | cross-profile approvals and persisted decisions refused; F4/ObservationPolicy limits stated, not hidden |
| Revocation and withdrawal | at construction, decision, execute entry, pre-dispatch |
| Cross-process activation and recovery | the durable model is DESIGN ONLY: the campaign must record these as NOT TESTABLE, not pass them |
| Replay, rollback, stale selections, concurrent source changes | per-boundary revalidation tests; epoch floor/rollback is a host duty and is recorded as such |
| Effect-boundary refusal | no effect after definitive refusal |
| Frozen v1-v6 compatibility | frozen manifests plus the engine V6_COMPAT differential |
| Runtime and Control Plane regressions | full suites on Python 3.11 and 3.12 versus unchanged-main baselines with identical pinned dependencies |
| Mutation and adversarial | harnesses recorded with raw logs; survivors proven equivalent or fixed |
| Security and independent Tier 1 | **DEFERRED, NOT WAIVED**; Ed25519 #26/#34 SECURITY-HELD; this campaign is builder-run only and is not independent acceptance |

## Evidence rules
Raw logs and JSON are committed; no summary replaces them. A failure is "pre-existing" only after the same test fails on the unchanged base with the same interpreter and pins. No paid provider calls.
