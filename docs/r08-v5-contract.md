# `r08-v5` contract: family `f5-action-class-unreadable-policy` (audit parameter `P-RG-C-009-on_unreadable`)

Status: IMPLEMENTED (Registry side only), NOT ACCEPTED. Non-authorizing. BUILDER_TESTED only; Tier 1 independent qualification is required before acceptance and has not been performed (not by the builder, the lead or CI). Frozen `r08-v1`, `r08-v2` (including its F5 class-age family `f5-action-class-age-bounds`), merged `r08-v3` and merged `r08-v4` are unchanged. Scope is the Registry producer/consumer contract only; the Control Plane consumer is a separate PR.

Governing documents: Static Migration Plan v1.1 (`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`), Engineering Plan v1.5, adopted audit (Registry PR #60), Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` with `ADOPTION.md` at the same revision.

## 1. Why a successor contract

The `r08-v2` F5 payload is EXACTLY `class_status_max_age_seconds` (`v2_age_bounds.F5_FIELDS`); a second key refuses `field_unknown`. `r08-v2` is frozen, so `on_unreadable` cannot be added to it, and no earlier table carries a class-attribute family. The smallest versioned successor is a new contract with one single-parameter family, following the `r08-v3`/`r08-v4` pattern: new modules only, a separate table, a version-specific signing domain and a version-specific effective-policy identity. The class-age parameter stays where it is (`r08-v2` F5); the two are NOT merged into one family (decision record, alternative R2).

## 2. Identity and record

Contract `r08-v5`; family `f5-action-class-unreadable-policy` (version tag `v5`); the `r08-v5` table registers this family only. Every record and selection of any other family refuses `family_unsupported`. Same envelope as `r08-v4` (canonical JSON, `payload_digest`, `record_digest`, exact shape, `non_authorizing: true`) with `contract_version` exactly `r08-v5`. Payload is EXACTLY one member:

- `class_on_unreadable`: object `action_class -> value`. Value: exact `str`, one of `refuse`, `bounded_tolerance` (the closed vocabulary of the Control Plane `ActionClass.on_unreadable`, `runtime_authority.py:132`). Class keys follow the frozen opaque-token rule of the `r08-v2` F5 family (`frozen_token_valid`, 1..128, no `*`), sorted, at most 256, non-empty map.

Missing member `field_missing`, extra `field_unknown`, wrong type `field_type_invalid`, violated value rule `field_invalid` (types before values). No default, no case folding, no coercion, no str subclass. Reason codes: the existing `CODES_V2`; none added.

## 3. Order and composition (only operator `intersection`)

The only relation asserted is `refuse` (stricter) < `bounded_tolerance` (looser). Source support: Control Plane `bounded.py:2189` is the only branch that reads the value to admit something (`bounded_tolerance` lets an unreadable grant status be replaced by a cached positive; `refuse` never does). Effective value per class = the stricter of (caller, Registry). A Registry value looser than the caller yields the caller value, reported in `detail` as `registry_value_not_narrowing:<classes>`. A Registry class the caller does not define refuses `composition_record_invalid` (never created); a caller class the record does not name keeps the caller value. An invalid caller refuses `composition_caller_invalid` and is never replaced. Every refusal carries no policy. `deny_all` is never set (`refuse` is a value, not a deny-all dimension).

## 4. What the Registry cannot know (consumer-owned)

The Registry has no view of irreversibility. The Control Plane additionally refuses an irreversible class whose value is not `refuse` (`bounded.py:2111`, `action_class_invalid`): a host class that is irreversible AND `bounded_tolerance` is an invalid host configuration that already refuses every action of the class. A Registry `refuse` composed into it would turn an always-refused class into an operational one. That is a widening in effect, so the consumer MUST refuse it (the Control Plane workflow refuses `registry_would_heal_invalid_class`). The Registry composer is correct in isolation; the guard lives where irreversibility is known.

## 5. Entry points (all new modules; no frozen file edited)

| Module | Purpose |
|---|---|
| `v5_class_unreadable.py` | payload validator, caller normalizer, `stricter`, `compose_f5u` |
| `v5_families.py` | `FAMILIES_V5`, `table_for_contract_version_v5`, `compose_for_v5` |
| `v5_record.py` | `validate_record_text_v5` (accepts `r08-v5` documents only) |
| `v5_selection.py` | `parse_selection_envelope_v5`, `signing_input_v5` |
| `v5_verify.py` | `verify_selection_v5` (no `contract_version` parameter; hardwired `r08-v5`) |
| `v5_policy_identity.py` | `effective_policy_digest` over the whole class map |
| `v5_decision.py` | `verify_and_decide_v5` |

## 6. Signing and identity (version-specific)

Selection signing input: `b"ocs-reg/r08-v5/selection\n" + canonical_bytes(statement)`; a v1, v2, v3 or v4 signature never verifies a v5 statement and the reverse. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v5/effective-policy\n"` + canonical bytes of the preimage `{effective_policy_profile, contract_version "r08-v5", family, family_version "v5", deny_all [], effective}` with every class and value, so no class can be replaced independently. `v2_policy_identity`, `v3_policy_identity` and `v4_policy_identity` refuse this family; `v5_policy_identity` refuses `r08-v4`/`r08-v3`/`r08-v2`/`r08-v1`.

## 7. Compatibility limitations (explicit)

1. Records of every family pin the same registered evaluator reference (`engine.safe_executor.LocalExecutionPolicy.check`, `registered-code-reference`); the enforcing Control Plane evaluator is named by `FamilySpec.enforcing_component` only (as for `r08-v2` F4/F5).
2. Registry tokens exclude spaces and other characters: a class id containing them cannot be governed (refused, never loosened).
3. As with `r08-v3`/`r08-v4`, the frozen dispatch tables refuse `r08-v5`; `v5_verify._verify_v5` repeats the layer orchestration (a drift risk). A test asserts it equals the `r08-v4` orchestration modulo version names.
4. The parameter only governs the cached-grant branch (`bounded.py:2189`). The cached-purpose-snapshot path (reversibility/0.1, `_cached_purpose`) never reads `on_unreadable`: a Registry `refuse` does not disable it (excluded: reversibility; protected evaluator unchanged).
5. No Control Plane activation exists in this PR; nothing is counted IMPLEMENTED in the migration ledger until the Control Plane PR lands.

## 8. Evidence

Tests: `tests/test_r08v5_unreadable_family.py` (validation, exhaustive 2x2 composition matrix, hostile inputs), `tests/test_r08v5_policy_identity.py` (identity, independent digest recomputation), `tests/test_r08v5_decision_path.py` (real synthetic Ed25519 decisions), `tests/test_r08v5_frozen_baseline.py` (158 frozen files byte-identical, cross-version and cross-family refusal, orchestration parity). Vectors: `tests/vectors/r08v5/`.
