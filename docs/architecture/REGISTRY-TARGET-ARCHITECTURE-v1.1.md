# Cognous Registry Target Architecture v1.1 (2026-10-29)

Status: PROPOSED, NON-AUTHORIZING, BUILDER_TESTED where implemented. Supersedes nothing: v1.0 (Registry PR #68, `d7eb6be2ccc5614fcfb2be68422c04d9c8a11037`) stays as written; this file records what changed after the implementation work. Governing: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ADOPTION.md`), Static Plan v1.1 s.12, Engineering Plan v1.5, audit #60, #65/#67. Independent Tier 1 qualification DEFERRED, NOT WAIVED.

## 1. Principles carried over unchanged
Registry stores and authenticates restrictions, never originating authority, approvals or execution. A verified overlay narrows a valid host policy; it never widens or repairs an invalid host. Existing evaluators keep their semantics. Host policy owner, signed selector, deployment activator, approval issuer and executor stay separate.

## 2. Architecture as built (and as proposed)
| Layer | v1.0 target | State now |
|---|---|---|
| A. Canonical record and selection parsing | common | Implemented ONCE in `registry_successor/engine/{record,selection}.py` for `r08-v7` (open PR). v2..v6 keep their frozen per-version copies. |
| B. Cryptographic verification orchestration | stable verifier | `engine/verify.py`: the layered verification of `v6_verify` as a function of a frozen `ContractProfile`. |
| C. Typed registered families | typed catalogue | `ContractProfile.families`: immutable table, each entry a typed `FamilySpec` plus `family_schema_revision`. One family registered in v7. |
| D. Family-specific admissibility and narrowing | per family | Each family owns its schema, validator, caller normalizer, composer. Shared mechanics never share semantics. |
| E. Shared composition and cross-field validation | resolver | Control Plane `GovernedPolicyWorkflow` (merged, `#91`) composes F4, class age, unreadable, then (open PRs) assurance, irreversibility, terminal; `final_composition_defect` validates the final profile. |
| F. Explicit mandatory-family applicability | host-declared | `GovernedFamilies`: every declared family is mandatory at every boundary; the declared set is part of the configuration identity. |
| G. One immutable effective-policy snapshot | snapshot | `EffectivePolicySnapshot` / `workflow.effective_policy_snapshot` (open PR): frozen tuples and scalars with an identity digest. |
| H. Version-specific signing and identity domains | domains | `ocs-reg/r08-vN/{selection,effective-policy}\n`, disjoint per version. |
| I. Typed deterministic refusals | codes | Closed code vocabulary (`CODES_V2`); no new Registry code for v6/v7. |
| J. Compatibility adapters | adapters | `V6_COMPAT` engine profile, proved byte-identical to the frozen v6 entry points by a differential test; frozen files untouched. |

## 3. The resolver
`resolve_effective_policy(host, mandatory selections, scope, trust, time)` is realised in the Control Plane as `resolve_effective_policy(...)` over the existing `derive_policy` path (open PR #93). Sequence: validate original host (before any source read); authenticate every required selection through the Registry decision; verify exact scope and trust; apply only proven non-widening transformations (add-only composers); validate the final composition; refuse any missing or invalid mandatory family; bind the final profile digest and each family's effective-policy identity; revalidate at construction, decision entry, execute entry and the pre-dispatch commit gate; never fall back to a weaker configuration. It is NOT a general interpreter; ownership of authorization, revocation issuance, durable state and execution stays with the original components.

## 4. What is NOT achieved (stated plainly)
- Three of the remaining four parameters are BLOCKED by decision records (anchor deadline residual window; ObservationPolicy max age and clock tolerance have no commitment/persistence binding). See `docs/family-migration/unified/07-...`.
- F4 constructor scalars remain workflow-local (D-06).
- Activation is advisory; the durable host-owned model is design only (`06-...`).
- A single signed snapshot across multiple selectors, rollback/high-water custody and revocation visibility remain host duties (D-09).
- Merged accounting does not change until the open PRs merge.

## 5. Decisions still required of the Architect
D-06 (binding option A/B/C), D-07 (anchor residual and temporal relationship), AR-1 and range ruling for ObservationPolicy tolerance, durable activation ownership, `r08-v7` allocation/freeze, and merge order.
