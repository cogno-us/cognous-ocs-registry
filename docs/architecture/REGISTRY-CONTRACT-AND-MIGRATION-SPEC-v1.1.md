# Cognous Registry Contract and Migration Specification v1.1 (2026-10-29)

Status: PROPOSED, NON-AUTHORIZING, BUILDER_TESTED where implemented. Companion to `REGISTRY-TARGET-ARCHITECTURE-v1.1.md`. v1.0 (PR #68) stays as written. Governing documents as in the architecture file.

## 1. Contract catalogue
| Contract | Families | Status |
|---|---|---|
| `r08-v1`..`r08-v5` | baseline, f1ab/f1abc/f1abcd, f4, f5 class age, f5 on_unreadable | frozen, merged; unchanged |
| `r08-v6` | `f5-action-class-revocation-assurance-policy`, `f5-terminal-revocation-enablement-policy` | transitional two-family contract; Registry #69 / CP #92 open, unmerged; NOT repurposed |
| `r08-v7` | `f5-action-class-irreversibility-policy` (schema revision 1) | proposed unified successor on ONE engine (Registry #71 / CP #93, stacked); conditional on version-allocation review; open until Architect freeze |

Envelope protocol version (`ContractProfile.version`) and family schema revision are separate. Signing inputs: `ocs-reg/r08-vN/selection\n` + canonical statement. Effective-policy identity: sha256 of `ocs-reg/r08-vN/effective-policy\n` + canonical preimage `{effective_policy_profile, contract_version, family, family_schema_revision (v7) | family_version (v6), deny_all, effective}`. Unknown versions and families refuse (`contract_unsupported`, `family_unsupported`); there is no fallback and no implicit upgrade.

## 2. v7 family `f5-action-class-irreversibility-policy`
Payload: exactly `class_irreversible`: non-empty class-id to `irreversible|no_change` map (frozen token rule, at most 256). Relation: `no_change` < `irreversible`; operator `intersection`; effective = stricter of caller and record per class; the vocabulary cannot say "reversible"; an unknown Registry class refuses `composition_record_invalid`. Consumer rules (Control Plane): flip false to true for every action of a class; refuse, never repair, when the HOST class has `reversibility`, `reversible_until`/`reversal_cost`, `on_unreadable != refuse`, `reads_protected_data` or non-default `counterparty_observable`; ambiguous class refuses.

## 3. Registered-family discipline
Adding a family to a profile requires: exact schema and bounds, a proved non-widening relation against a source-backed consumer, an existing enforcement boundary, a binding path with no approval-preimage or persisted-field change, a composer that only adds, a final-composition rule, tests including forged-result widening, and a mutation run. A family that fails any item is not registered (the three blocked parameters have no placeholder and a test proves they refuse `family_unsupported`).

## 4. 19-parameter mapping
See `docs/family-migration/unified/01-parameter-source-and-consumer-crosswalk-19-2026-10-29.md`.

## 5. Open blockers (unchanged by this package)
F4 scalar binding; ObservationPolicy binding, clock domain and 60/300 relationship; anchor residual; durable activation; atomic multi-selector snapshots; version allocation. This specification does not authorize any approval-format change, new trust root or issuer.
