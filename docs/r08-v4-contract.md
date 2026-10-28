# `r08-v4` contract: composite family `f1abcd-local-execution-limits` (M3 PR-1)

Status: IMPLEMENTED (Registry side only), NOT ACCEPTED. Non-authorizing. BUILDER_TESTED only; Tier 1 independent qualification is required before acceptance and has not been performed (not by the builder, the lead or CI). Frozen `r08-v1`, `r08-v2` and merged `r08-v3` are unchanged. Scope is the Registry producer/consumer contract only: no Runtime or Control Plane integration in this PR.

## 1. Identity

Contract `r08-v4`; family `f1abcd-local-execution-limits` (version tag `v4`); the `r08-v4` table registers this family only. Every record and selection of any other family (including `f1abc-local-execution-limits`) refuses `family_unsupported`. `f1abcd` carries all seven `f1abc` restrictions unchanged plus the two M3 values, in ONE signed selection, so the two target members can never be activated independently of the seven (single-binding atomicity).

## 2. Record

Same envelope as `r08-v3` (canonical JSON, integers only, `payload_digest`, `record_digest`, exact shape, `non_authorizing: true`) with `contract_version` exactly `r08-v4`. Payload is EXACTLY nine members: the seven `f1abc` members (validated by the unmodified `v3_f1abc`/`v2_f1ab` validators, by import) plus
- `allowed_target_prefixes`: list of tokens, sorted by code point, duplicate-free, at most 256, each valid under the frozen token rule `frozen_token_valid` (1..128 characters; no control, separator-category, unassigned or `*` characters; `/`, `:` and `\` are allowed). `[]` is the explicit deny-all.
- `target_match`: exact `str`, one of `exact`, `segment`, `legacy-prefix`. There is no default: the Runtime default `segment` is never applied by the Registry.

Missing member `field_missing`, extra `field_unknown`, wrong type `field_type_invalid`, violated value rule `field_invalid` (types before values).

## 3. Source semantics of target matching (engine/safe_executor.py, protected, unchanged)

With SEP = `/:` the accepted set of a policy is a UNION over its entries, per entry:
- `exact(e) = {e}`
- `segment(e) = {t : t startswith e and (t == e or e[-1] in SEP or t[len(e)] in SEP)}`
- `legacy-prefix(e) = {t : t startswith e}`

`exact(e) ⊆ segment(e) ⊆ legacy-prefix(e)` holds PER ENTRY only. It is NOT a global order between two (list, mode) pairs: caller `(["a/b"], legacy-prefix)` and Registry `(["a"], exact)` are not comparable. A rule that compared mode names alone would widen, so none is used. Accepted targets are not exactly representable as a single (list, mode) intersection of two arbitrary pairs, so composition uses the sound rule below.

## 4. Composition (only operator `intersection`)

Seven `f1abc` members: exactly as `r08-v3` section 4. Targets:
1. `m' =` the stricter mode (`exact` > `segment` > `legacy-prefix`).
2. `P' =` every entry `e` in `P_caller ∪ P_registry` such that `accepted(m', e)` is contained in `accepted(caller_mode, c)` for SOME caller entry `c` AND in `accepted(registry_mode, r)` for SOME Registry entry `r`. `contained` is an exact string predicate (`v4_f1abcd.contained`) verified exhaustively against the evaluator rule on a bounded universe.
3. Empty `P'` is deny-all (`deny_all_fields` includes `allowed_target_prefixes`); the consumer MUST build no policy and dispatch no effect.

Guarantee: the effective accepted set is a subset of the caller's AND of the Registry's, for every mode pair. The rule is not always complete (it may narrow below the exact set intersection, for example caller `(["a"], segment)` with Registry `(["a/b"], legacy-prefix)` yields `(["a/b"], segment)`); this is documented and never widens. A Registry mode weaker than the caller's reports `registry_value_not_narrowing:target_match` in `detail`. Caller prefixes must be a non-empty collection of valid tokens and the mode a valid str; otherwise `composition_caller_invalid` (no default, no fallback; a seven-member caller is refused).

## 5. Entry points (all new modules; no frozen file edited)

| Module | Purpose |
|---|---|
| `v4_f1abcd.py` | payload validator, caller normalizer, `matches`, `contained`, `compose_targets`, `compose_f1abcd` |
| `v4_families.py` | `FAMILIES_V4`, `table_for_contract_version_v4`, `compose_for_v4` |
| `v4_record.py` | `validate_record_text_v4` (accepts `r08-v4` documents only) |
| `v4_selection.py` | `parse_selection_envelope_v4`, `signing_input_v4` |
| `v4_verify.py` | `verify_selection_v4` (no `contract_version` parameter; hardwired `r08-v4`) |
| `v4_policy_identity.py` | `effective_policy_digest` over all nine members |
| `v4_decision.py` | `verify_and_decide_v4` |

## 6. Signing and identity (version-specific)

Selection signing input: `b"ocs-reg/r08-v4/selection\n" + canonical_bytes(statement)`; a v1, v2 or v3 signature never verifies a v4 statement and the reverse. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v4/effective-policy\n"` + canonical bytes of the preimage `{effective_policy_profile, contract_version "r08-v4", family, family_version "v4", deny_all, effective}` with all nine members; `deny_all` includes `allowed_target_prefixes` when empty. `v2_policy_identity` and `v3_policy_identity` refuse this family; `v4_policy_identity` refuses `r08-v3`/`r08-v2`/`r08-v1`. Reason codes: the existing `CODES_V2`; none added.

## 7. Compatibility limitations (explicit)

1. Registry tokens exclude spaces and other characters: a target prefix containing them cannot be governed (it is refused, never loosened).
2. Governed callers must supply a non-empty prefix list and an explicit `target_match` (the Runtime policy default `segment` is not applied implicitly).
3. The composition rule can be narrower than the exact set intersection (section 4); it is never wider.
4. As with `r08-v3`, the frozen dispatch tables still refuse `r08-v4`; `v4_verify._verify_v4` repeats the layer orchestration (a drift risk). A test asserts it equals the `r08-v3` orchestration modulo version names.
5. No Runtime selection, activation, transition (`f1abc` to `f1abcd`), revocation handling or effect-time target enforcement exists in this PR (M3 Runtime PR). Registry configuration reaches no enforcement boundary yet, so nothing is counted IMPLEMENTED in the migration ledger until the Runtime PR lands.

## 8. Evidence

Tests: `tests/test_r08v4_f1abcd_family.py` (exhaustive containment and soundness against the evaluator rule, validation, composition), `tests/test_r08v4_policy_identity.py` (identity, independent digest recomputation), `tests/test_r08v4_decision_path.py` (real synthetic Ed25519 decisions), `tests/test_r08v4_targets_and_versions.py` (target narrowing, cross-version/family, orchestration parity), `tests/test_r08v4_frozen_baseline.py` (141 frozen files byte-identical). Vectors: `tests/vectors/r08v4/`.
