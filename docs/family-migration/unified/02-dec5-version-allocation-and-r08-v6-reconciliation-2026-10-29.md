# DEC-5 and the `r08-v6` / `r08-v7` reconciliation (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (independent Tier 1 qualification is DEFERRED, NOT WAIVED). Governing documents: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ENGINEERING_CONSTITUTION.md`, `ADOPTION.md`), Static Migration Plan v1.1 (section 12), Engineering Plan v1.5, audit #60, assessments #65/#67, target architecture and contract specification v1.0 (Registry PR #68, merge `d7eb6be2ccc5614fcfb2be68422c04d9c8a11037`).

## 1. What changed relative to the #68 target architecture

#68 (v1.0) described "candidate r08-v6" as the unified successor and said no successor id was allocated. Since then the `r08-v6` identifier was used, for real, by the two-family revocation contract (Registry PR #69, head `42a666328b974a7581013358bcf8bc7b9eac7761`; Control Plane PR #92, head `a62ca8d8e4088c95407c2000dcca081383d8dd4d`; records PR #70, head `f309ae20a194786a45a708118b93603ee4670096`). All three are OPEN and unmerged; nothing here rebases, rewrites or supersedes them.

| #68 statement | Implemented reality | Reconciliation |
|---|---|---|
| "Candidate r08-v6 is a proposed unified successor" | `r08-v6` carries exactly two families (`f5-action-class-revocation-assurance-policy`, `f5-terminal-revocation-enablement-policy`), hard-wired per-version modules | `r08-v6` is the COMPATIBLE TRANSITIONAL contract. It is not repurposed and its records are not rewritten. |
| "Separate envelope protocol version from family schema revision" | v6 has one family-version tag ("v6") for both families and no schema revision | Introduced in `r08-v7`: `ContractProfile.version` (envelope) versus a per-family `family_schema_revision` that enters the effective-policy preimage. |
| "Reuse parsing and verification mechanics" | v3..v6 each carry a near-identical copy of selection, record, verify, decision and identity code (v5_verify.py and v6_verify.py are the same 244-line routine differing only in constants) | `r08-v7` implements those mechanics ONCE in `registry_successor/engine/`, parameterised by an immutable `ContractProfile`. Frozen v1..v6 modules are untouched. |
| "Compatibility adapters for frozen contracts where support can be added without changing semantics" | none | The engine ships a `V6_COMPAT` profile built from the existing v6 family specs; a differential test proves byte-identical results with the frozen v6 entry points. It is an adapter for verification reuse, not a re-signing or translation of v6 records. |

## 2. DEC-5 (single-family versus multi-family contract versions) - resolved as the Architect's preferred design
- `r08-v6` preserved for the two existing revocation families, subject to final merge approval.
- `r08-v7` is the next unified successor, **conditional on final version-allocation review**: it is allocated by this proposal only if Registry PR for `r08-v7` is merged. Until then `r08-v7` is a proposed identifier, `r08-v8` is next free, and nothing is in force.
- One contract may carry multiple qualified families. Sharing a contract version does NOT make families atomically applicable: each family has its own record, selection, operation id and effective-policy identity, and the consumer declares the mandatory set (see `06-applicability-activation-durable-model-2026-10-29.md`).
- `r08-v7` currently registers ONE family (irreversibility). It does not re-register the `r08-v6` families, and no family is registered for a BLOCKED parameter. Because v7 is unmerged and unfrozen, qualified families may be added to its table before the Architect freezes it; after freeze a new family needs a new contract id (never a mutation of v7).
- No version identifier is reused or overwritten; v1..v6 signing and identity domains stay disjoint from the v7 domains (`ocs-reg/r08-v7/selection\n`, `ocs-reg/r08-v7/effective-policy\n`).

## 3. Unresolved authority decisions (not assumed)
See `07-commitment-binding-decisions-2026-10-29.md`: D-06 (F4 scalar and ObservationPolicy binding), D-07 (temporal relationship), anchor-deadline residual window, durable activation, and the final freeze/allocation of `r08-v7`.
