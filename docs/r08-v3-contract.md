# `r08-v3` contract: composite family `f1abc-local-execution-limits` (M2 PR-1)

Status: IMPLEMENTED, NOT ACCEPTED. Non-authorizing. BUILDER_TESTED only; Tier 1 independent qualification is required before acceptance and has not been performed (not by the builder, the lead or CI). Frozen `r08-v1` and `r08-v2` are unchanged. Scope is the Registry producer/consumer contract only: no Runtime or Control Plane integration. Design record: PR #53 (`docs/family-migration/m2/`, approved head `66251b5d3337b27a76c8ca73ecc4da5e7ccaeaea`).

## 1. Identity

Contract `r08-v3`; family `f1abc-local-execution-limits` (version tag `v3`); the `r08-v3` table registers this family only. Every record and selection of any other family (including f1a, f1ab, F4, F5) refuses `family_unsupported`.

## 2. Record

Same envelope as `r08-v2` (canonical JSON, integers only, `payload_digest`, `record_digest`, exact shape, `non_authorizing: true`) with `contract_version` exactly `r08-v3`. Payload is EXACTLY seven members: `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains` (validated by the unmodified `v2_f1ab` validator, by import) and `max_amount`, `max_effects`. Missing member `field_missing`, extra member `field_unknown`, wrong type `field_type_invalid`, violated value rule `field_invalid` (types before values).

## 3. Numeric domains (exact `int` only; no bool, float, Decimal, str, None, bytes, int subclass; no coercion)

| Value | Registry record | Caller (governed path) |
|---|---|---|
| `max_amount` | 0 ..= 2^53; 0 is a valid ceiling | exact int 0 ..= 2^53; any float, including `5.0` and `-0.0`, is refused `composition_caller_invalid` |
| `max_effects` | 0 ..= 2^53 − 1; **0 is the explicit deny-all** | exact int ≥ 1, no upper bound |

Floats and non-finite numbers never reach validation from source JSON (`json_number_unsupported`). Integer literals of 20 or more digits are `field_invalid` in the identity module.

## 4. Composition (only operator `intersection`)

Sets: intersection per set (the f1ab semantics; an empty effective set is deny-all). Ceilings: `min(caller, registry)`; a Registry ceiling strictly above the caller yields the caller with `detail = registry_value_not_narrowing:<names>`. The result never exceeds the caller for any of the seven members. Deny-all (`deny_all = True`, `deny_all_fields` naming the dimensions, `max_effects` included) when any effective set is empty or the Registry `max_effects` is 0; the decision still carries the effective values but the consumer MUST build no policy and dispatch no effect. Every refusal carries no effective policy and never the caller policy under `required` participation.

## 5. Entry points (all new modules; no frozen file edited)

| Module | Purpose |
|---|---|
| `v3_f1abc.py` | payload validator, caller normalizer, `compose_f1abc` |
| `v3_families.py` | `FAMILIES_V3`, `table_for_contract_version_v3`, `compose_for_v3` |
| `v3_record.py` | `validate_record_text_v3` (accepts `r08-v3` documents only) |
| `v3_selection.py` | `parse_selection_envelope_v3`, `signing_input_v3` |
| `v3_verify.py` | `verify_selection_v3` (no `contract_version` parameter; hardwired `r08-v3`) |
| `v3_policy_identity.py` | `effective_policy_digest` over all seven members |
| `v3_decision.py` | `verify_and_decide_v3` |

## 6. Signing and identity (version-specific)

Selection signing input: `b"ocs-reg/r08-v3/selection\n" + canonical_bytes(statement)`; a v1 or v2 signature never verifies a v3 statement and the reverse. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v3/effective-policy\n"` + canonical bytes of the preimage `{effective_policy_profile, contract_version "r08-v3", family, family_version "v3", deny_all, effective}` with all seven members; `v2_policy_identity` refuses this family and `v3_policy_identity` refuses `r08-v2`/`r08-v1`. Reason codes: the existing `CODES_V2` (46 + 2); none added.

## 7. Compatibility limitations (explicit)

1. Governed caller `max_amount` must be an exact int; legacy float ceilings are refused only in this governed path (the Runtime evaluator and callers outside it are unchanged).
2. The frozen `families.table_for_contract_version` still refuses `r08-v3` (so no v1/v2 entry point can reach a v3 family). PR #53 proposed an entry there; to keep every frozen file byte-identical the v3 table lives in `v3_families.py`. This is a deliberate deviation from that blueprint line.
3. `v3_verify._verify_v3` repeats the layer orchestration of the frozen `verify._verify` because the latter hardwires `r08-v2` (statement shape, contract label and signing domain). All contract-agnostic helpers (private copies, trust normalization, key admission, record binding, snapshot floor) are imported, not copied. Two orchestrations is a drift risk for the independent qualifier to compare.
4. The binding and scope-key digest domains in `v2_policy_identity` (`ocs-reg/r08-v2/...`) are Control Plane/Runtime consumer concerns and are not given `r08-v3` variants here; whether the Control Plane may keep the v2 label for an `r08-v3` family is open item R-2 of PR #53.
5. Numeric enforcement is as exact as the unchanged evaluator: binary64 comparison `float(op.amount) > float(max_amount)`; Registry integers up to 2^53 convert exactly, no claim is made about the decimal form of an operation amount before it became binary64.
6. No Runtime selection, activation, transition (f1ab to f1abc), revocation handling or effect-time enforcement exists yet (M2 PR-2/PR-3, not authorized). The migration backlog stays at 23.

## 8. Evidence

Tests: `tests/test_r08v3_f1abc_family.py` (validation, boundaries, composition grid), `tests/test_r08v3_policy_identity.py` (identity, independent digest recomputation), `tests/test_r08v3_decision_path.py` (real synthetic Ed25519 decisions, cross-version/family/tenant, signature, digest, lifecycle), `tests/test_r08v3_frozen_baseline.py` (125 frozen files byte-identical). Vectors: `tests/vectors/r08v3/` (identity, signed selection, frozen manifest).
