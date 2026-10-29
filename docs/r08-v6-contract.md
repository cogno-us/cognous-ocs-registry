# `r08-v6` contract: families `f5-action-class-revocation-assurance-policy` (audit parameter `P-RG-C-010-requires_revocation_assurance`) and `f5-terminal-revocation-enablement-policy` (audit parameter `P-RG-C-TERMINAL-REVOCATION-enabled`)

Status: IMPLEMENTED (Registry side only), NOT ACCEPTED. Non-authorizing. BUILDER_TESTED only; Tier 1 independent qualification is required before acceptance and has not been performed (not by the builder, the lead or CI). Frozen `r08-v1`, `r08-v2` (including its F5 class-age family `f5-action-class-age-bounds`), merged `r08-v3`, `r08-v4` and `r08-v5` (family `f5-action-class-unreadable-policy`) are unchanged. Scope is the Registry producer/consumer contract only; the Control Plane consumer is a separate change. Nothing here claims certification, security clearance or production readiness.

Governing documents: Static Migration Plan v1.1 (`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`), Engineering Plan v1.5, adopted audit (Registry PR #60), Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` with `ADOPTION.md` at the same revision.

## 1. Why a successor contract, and what sharing it does NOT mean

`r08-v5` is frozen and registers exactly one family; no earlier table carries a revocation-related family. The smallest versioned successor is a new contract with a separate table, a version-specific signing domain and a version-specific effective-policy identity, following the `r08-v3`/`r08-v4`/`r08-v5` pattern: new modules only. The `r08-v6` table registers TWO independent families, because both are enforced by the same consumer (the Control Plane) and both can only ADD a refusal or hold:

| Family | Audit parameter | Control Plane field | Payload member |
|---|---|---|---|
| `f5-action-class-revocation-assurance-policy` | `P-RG-C-010-requires_revocation_assurance` | `ActionClass.requires_revocation_assurance` (bool) | `class_requires_revocation_assurance`: map `action_class -> "required" \| "not_required"` |
| `f5-terminal-revocation-enablement-policy` | `P-RG-C-TERMINAL-REVOCATION-enabled` | `RuntimeAuthorityProfile.terminal_revocation` (absent = off, present = on) | `terminal_revocation`: scalar `"off" \| "on"` |

Sharing a contract version does NOT make the two atomically applicable. Each record and each selection is for exactly one family, under its own operation id, with its own epoch, validity interval, signature and revocation. The Registry never combines two records, never applies one because the other was applied, and a verdict about one family says nothing about the other. A consumer that governs both must decide, verify and bind them separately (and may apply one while the other is refused). A record of any other family refuses `family_unsupported`.

## 2. Identity and record

Contract `r08-v6`; family version tag `v6` for both families. Same envelope as `r08-v5` (canonical JSON, `payload_digest`, `record_digest`, exact shape, `non_authorizing: true`) with `contract_version` exactly `r08-v6`. Each record's payload is EXACTLY one member:

- Family 1, `class_requires_revocation_assurance`: object `action_class -> value`. Value: exact `str`, one of `required`, `not_required`. JSON booleans are NOT accepted (`field_type_invalid`): the Control Plane field is a bool, but the Registry vocabulary is a closed two-string set, and the consumer maps the exact strings; there is no coercion. Class keys follow the frozen opaque-token rule of the `r08-v2` F5 family (`frozen_token_valid`, 1..128, no `*`), sorted, at most 256, non-empty map.
- Family 2, `terminal_revocation`: exact `str`, one of `off`, `on` (a scalar, never a map).

Missing member `field_missing`, extra `field_unknown`, wrong type `field_type_invalid`, violated value rule `field_invalid` (types before values). No default, no case folding, no coercion, no str subclass. Reason codes: the existing `CODES_V2`; none added.

## 3. Order and composition (only operator `intersection`)

Family 1. The only relation asserted is `required` (stricter) < `not_required` (looser). Effective per class = the stricter of (caller, Registry). A Registry `not_required` over a caller `required` yields the caller value, reported in `detail` as `registry_value_not_narrowing:<classes>` (sorted, only the looser Registry classes). A Registry class the caller does not define refuses `composition_record_invalid` (a class is never created); a caller class the record does not name keeps the caller value.

Family 2. The only relation asserted is `on` (stricter) < `off` (looser). Effective = `on` if EITHER side is `on`, else `off`. Registry `off` over caller `on` yields `on` with `detail` `registry_value_not_narrowing:terminal_revocation`; Registry `off` over caller `off` yields `off` with no detail; Registry `on` yields `on`. The caller policy is the scalar `{"terminal_revocation": "off"|"on"}`; any other shape (a map, a bool, a missing or extra member, a subclass) is invalid.

For both: an invalid caller refuses `composition_caller_invalid` and is never replaced or defaulted. Every refusal carries no effective policy. `deny_all` is never set (neither value is a deny-all dimension).

| Matrix (family 2) | Registry `off` | Registry `on` |
|---|---|---|
| caller `off` | `off` | `on` |
| caller `on` | `on` (not-narrowing detail) | `on` |

## 4. What the Registry cannot know (consumer-owned)

- Family 1: the Registry cannot see whether a holder inventory exists. `required` makes the class hold `holder_inventory_missing` unless the host profile carries a holder inventory, so it can only ADD a hold. It never creates a holder inventory. Honest limitation: `required` demands only the PRESENCE of a host-declared inventory, and that presence is an unverified host claim; the Registry does not verify the inventory's contents, completeness or truth, and `required` is not assurance that any grant can actually be revoked.
- Family 2: the Registry cannot see which grants were revoked, nor irreversibility. `on` adds a refusal `grant_revocation_recorded` for a grant revision whose revocation a retained check already observed. It grants nothing, never revokes anything and does not decide who may revoke; revocation authority stays entirely with the host.
- Neither family can widen what the host allows: a looser Registry value never loosens the caller (section 3), and a Registry class unknown to the host is refused rather than created.
- Interaction with other class attributes (for example irreversibility, `r08-v5` `on_unreadable`) belongs to the consumer.

## 5. Entry points (all new modules; no frozen file edited)

| Module | Purpose |
|---|---|
| `v6_class_revocation_assurance.py` | family 1: payload validator, caller normalizer, `stricter`, `compose_f5ra` |
| `v6_terminal_revocation.py` | family 2: payload validator, caller normalizer, `stricter`, `compose_tr` |
| `v6_families.py` | `FAMILIES_V6` (two families), `lookup_v6`, `table_for_contract_version_v6`, `compose_for_v6` |
| `v6_record.py` | `validate_record_text_v6` (accepts `r08-v6` documents only) |
| `v6_selection.py` | `parse_selection_envelope_v6`, `signing_input_v6` |
| `v6_verify.py` | `verify_selection_v6` (no `contract_version` parameter; hardwired `r08-v6`) |
| `v6_policy_identity.py` | `effective_policy_digest(family, effective, contract_version="r08-v6")` |
| `v6_decision.py` | `verify_and_decide_v6` (dispatches on the verified record's family; never combines families) |

## 6. Signing and identity (version-specific)

Selection signing input: `b"ocs-reg/r08-v6/selection\n" + canonical_bytes(statement)`; a v1..v5 signature never verifies a v6 statement and the reverse. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v6/effective-policy\n"` + canonical bytes of the preimage `{effective_policy_profile, contract_version "r08-v6", family, family_version "v6", deny_all [], effective}`; family 1 binds every class and value, family 2 binds the scalar, so no class and no value can be replaced independently and the two families can never share a digest. Identity row kinds: `classmap-enum` (family 1) and `scalar-enum` (family 2), in the module's own table. `v2_policy_identity`..`v5_policy_identity` refuse these families `family_unsupported`; `v6_policy_identity` refuses `r08-v5`..`r08-v1` as `contract_unsupported`. No new trust root: signing keys, trust snapshots, key admission, withdrawal, revocation and epoch floors are the existing mechanisms, unchanged.

## 7. Compatibility limitations (explicit)

1. Records of both families pin the same registered evaluator reference (`engine.safe_executor.LocalExecutionPolicy.check`, `registered-code-reference`); the enforcing Control Plane evaluator is named by `FamilySpec.enforcing_component` only (as for `r08-v2` F4/F5 and `r08-v5`).
2. Registry tokens exclude spaces and other characters: a class id containing them cannot be governed (refused, never loosened).
3. As with `r08-v3`..`r08-v5`, the frozen dispatch tables refuse `r08-v6`; `v6_verify._verify_v6` and `v6_decision` repeat the layer orchestration (a drift risk). Tests assert they equal the `r08-v5` orchestration modulo version names. The only intended difference in `v6_decision` is the optional-participation refusal, which normalizes the caller with whichever `r08-v6` family normalizer accepts its shape (the two caller shapes are disjoint) and otherwise returns the caller unchanged.
4. Whether `required`/`on` has any operational effect depends entirely on the consumer wiring the field; a consumer that ignores the effective policy is not governed by it.
5. No Control Plane activation exists in this change; nothing is counted IMPLEMENTED in the migration ledger until the Control Plane change lands.

## 8. Evidence

Tests: `tests/test_r08v6_revocation_assurance_family.py` and `tests/test_r08v6_terminal_revocation_family.py` (validation, hostile inputs, exhaustive composition matrices), `tests/test_r08v6_policy_identity.py` (identity, independent digest recomputation), `tests/test_r08v6_decision_path.py` (real synthetic Ed25519 decisions for both families: key revocation, withdrawal, expiry, wrong scope/operation/family), `tests/test_r08v6_lifecycle_boundaries.py` (exact boundaries, exact-type dispatch), `tests/test_r08v6_frozen_baseline.py` (174 frozen r08-v1..v5 files byte-identical from Registry `e8b572cc`, cross-version and cross-family refusal, orchestration parity). Builders: `tests/r08v6_support.py`. Vectors: `tests/vectors/r08v6/`. Mutation harness, generators and raw logs: `docs/family-migration/revocation-families/evidence/`.
