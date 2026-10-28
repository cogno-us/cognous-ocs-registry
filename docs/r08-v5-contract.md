# `r08-v5` contract: family `f4t-control-plane-clock-tolerance` (M11 PR-1)

Status: IMPLEMENTED (Registry side only), NOT ACCEPTED. Non-authorizing. BUILDER_TESTED only; Tier 1 independent qualification is required before acceptance and has not been performed. Frozen `r08-v1`, `r08-v2`, `r08-v3` and merged `r08-v4` are unchanged. Scope is the Registry producer/consumer contract only: no Control Plane or Runtime integration in this PR.

## 1. Identity and why a new contract

Contract `r08-v5`; family `f4t-control-plane-clock-tolerance` (version tag `v5`); the `r08-v5` table registers this family only. Source group RG-C-006 is the Control Plane `clock_tolerance_seconds` (default 5). The existing Registry family `f4-control-plane-age-bounds` (r08-v2) already governs `status_max_age_seconds` and `approval_max_age_seconds` (RG-C-003, RG-C-004) and is closed to exactly those two keys; frozen `r08-v2` is not modified and its fields are not duplicated here. Every record or selection of any other family refuses `family_unsupported`.

## 2. Record

Same envelope as `r08-v3`/`r08-v4` with `contract_version` exactly `r08-v5`. Payload is EXACTLY one member: `clock_tolerance_seconds`, an `int` (not bool) in `0..2147483647` (the same technical ceiling as the age bounds). `0` is the strictest valid value (no tolerance) and is NOT a deny-all; there is no deny-all dimension. Missing `field_missing`, extra `field_unknown`, wrong type `field_type_invalid` (floats fail earlier at the canonical-JSON layer as `json_number_unsupported`), out of range `field_invalid`.

## 3. Composition (only operator `intersection`)

`effective = min(caller, registry)`. A Registry value above the caller reports `registry_value_not_narrowing:clock_tolerance_seconds` in `detail` and the caller value stands; the result is never above the caller. The caller must supply exactly `{clock_tolerance_seconds: int in range}`; otherwise `composition_caller_invalid` (no default, no fallback).

## 4. Entry points (new modules only)

`v5_f4t.py` (validator, normalizer, `compose_f4t`), `v5_families.py`, `v5_record.py`, `v5_selection.py`, `v5_verify.py` (`verify_selection_v5`, hardwired `r08-v5`), `v5_policy_identity.py`, `v5_decision.py` (`verify_and_decide_v5`). Enforcing component of the family is `control-plane`.

## 5. Signing and identity (version-specific)

Selection signing input `b"ocs-reg/r08-v5/selection\n" + canonical_bytes(statement)`; effective-policy digest over `b"ocs-reg/r08-v5/effective-policy\n"` + canonical preimage `{effective_policy_profile, contract_version "r08-v5", family, family_version "v5", deny_all [], effective}`. Earlier-version signatures and digests never validate here and the reverse. `v2_policy_identity` refuses this family. Reason codes: existing `CODES_V2`; none added.

## 6. Limitations

1. The frozen dispatch tables refuse `r08-v5`; `v5_verify._verify_v5` repeats the layer orchestration (drift risk), guarded by a test that asserts equality with `r08-v4` modulo version names.
2. `f4t` and `f4` are independent families. A consumer that wants both must hold two selections; the coexistence rule applies per family. The Control Plane adapter (M11 PR-2) must refuse when only one of the two governed inputs is satisfied.
3. No Control Plane consumption exists in this PR; nothing is counted IMPLEMENTED until the consumer PR lands.

## 7. Evidence

`tests/test_r08v5_f4t_family.py`, `tests/test_r08v5_frozen_baseline.py` (frozen files byte-identical), vectors in `tests/vectors/r08v5/`.
