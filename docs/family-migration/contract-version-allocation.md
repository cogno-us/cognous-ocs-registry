# Registry successor contract-version allocation and compatibility ledger

Status: documentation only; non-authorizing; append-only. Created 2026-10-28 in the `on_unreadable` accounting PR. Governing documents: Static Migration Plan v1.1, Engineering Plan v1.5, audit #60, Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`.

| Contract id | Family / families | Status | Source |
|---|---|---|---|
| `r08-v1` | baseline | frozen | Registry main |
| `r08-v2` | f1ab allow-sets; f4 `status_max_age_seconds` + `approval_max_age_seconds`; f5 `class_status_max_age_seconds` | frozen (Amendments 1-4) | Registry main |
| `r08-v3` | f1abc `max_amount`, `max_effects` | frozen, merged | Registry main (`b7e6a17` lineage) |
| `r08-v4` | f1abcd (adds `allowed_target_prefixes`, `target_match`) | frozen, merged | Registry main |
| **`r08-v5`** | **f5 `f5-action-class-unreadable-policy` (`class_on_unreadable`) — RESERVED to `on_unreadable` by Architect decision 2026-10-28** | OPEN in Registry PR #64 (head `6c3e5e4037d34bd2b31371461bfc872c762026b9`), not merged | PR #64 |
| `r08-v6` | next free id | unallocated | n/a |

## Collision record (do not rewrite)
- Registry PR #58 (head `1a67d539`, HELD, constructor clock tolerance `f4t-control-plane-clock-tolerance`) also claims `r08-v5` and the same file names (`registry_successor/v5_*.py`, `docs/r08-v5-contract.md`, `tests/r08v5_support.py`). The two cannot both merge.
- Architect decision (2026-10-28): `r08-v5` belongs to `on_unreadable`. PR #58 must not merge under that contract version or those file names and is not modified by this program step. If constructor clock tolerance is later authorized, its implementation must be rebased onto the then-current Registry baseline and given a distinct successor version (next free: `r08-v6`) or be reconciled explicitly by the Architect. The two proposals are never combined into one composite record. PR #58's historical evidence stays as written.
- Consumer-side effect: the Control Plane pins for the F4 age and F5 class-age governance remain Registry `6f600ab1150f00ef3d96834159b1807e866a78b6`; the `on_unreadable` consumer (Control Plane PR #90) pins Registry #64's exact head in a second checkout.

## Update 2026-10-28 (consolidation increment; append-only)
- `r08-v5` (on_unreadable) is MERGED: Registry PR #64 merge `94e8652725ec34e29fc9b91ed132bb8b5a4b381a`; Control Plane consumer PR #90 merge `ae47a040ecfa7d22fb2d98932318d4770f1d3709`. The reservation stands: PR #58 (held) may not use `r08-v5` or the `v5_*` file names.
- `r08-v6` remains the next free identifier and is NOT introduced or authorized by the consolidation increment. The Registry shared-orchestration extraction was reviewed and is DOCUMENT-ONLY (`docs/family-migration/consolidation/01-registry-shared-orchestration-review-2026-10-28.md`): v3/v4 are hash-frozen and parity-tested, so any shared implementation belongs to a future version and must leave v3/v4/v5 byte-identical.
- Open allocation-policy question (assessment P1-4, DEC-5): single-family versions (the v3/v4/v5 pattern) versus one multi-family version (the v2 pattern). Not decided here.
