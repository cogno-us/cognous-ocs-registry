# M2 — Test matrix (corrected)

Status: PROPOSAL. C = caller ceiling, R = Registry ceiling. "Source" = outcome fixed by pinned evaluator/Registry/Runtime source; "Decision" = fixed by an Architect ruling in `05`. Each ceiling scenario applies to both `max_amount` and `max_effects` unless noted; set behaviour is covered by the existing f1ab tests, which must pass unchanged on the composite. Invariant for every row: no effective value above C, and no effect dispatched after a refusal.

## Required scenarios

| ID | Scenario | Expected outcome | Layer | Basis |
|---|---|---|---|---|
| T01 | R < C | effective = R; operations above R refused | Reg + RT | Source (min) |
| T02 | R = C | effective = C; no detail | Reg + RT | Source |
| T03 | R > C | effective = C; detail `registry_value_not_narrowing:<name>` | Reg + RT | Source (F4/F5 precedent) |
| T04 | Missing Registry member (any of the seven) | `field_missing`; record rejected whole | Reg + RT | Source (pattern) |
| T05 | Invalid Registry value: float (`5.0`, `1e3`), bool, str, None, Decimal, int subclass, negative, max+1, 10^30, extra key | `field_type_invalid` / `field_invalid` / `field_unknown`; no coercion | Reg | Decision (D-4) |
| T06a | `max_amount` 0 (R=0 or C=0) | amount 0 passes (`0.0 > 0.0` false); amount > 0 refused | RT | Source (evaluator) + Decision (D-2) |
| T06b | Record `max_effects` = 0 | deny-all: `LocalExecutionPolicy` not constructed, no effect dispatched | Reg + RT | Decision (D-2) |
| T06c | Caller `max_effects` = 0 or negative | `composition_caller_invalid` | Reg | Source (`_strict_positive_int`) |
| T07 | Exact boundary: amount = ceiling passes, ceiling + 1 refused; `effective_max_effects` = ceiling passes, +1 refused; ceilings 2^53 (amount) and 2^53 − 1 (effects); 2^53 + 1 (amount) refused | per `>` semantics | RT | Source |
| T08 | Multiple-effect attempts: `op.effects` ≠ 1 refused; N + 1-th effect under budget N refused; refused attempt leaves `used_effects` unchanged | exactly-one semantics unchanged; no double counting | RT | Source |
| T09 | Revoked / withdrawn / stale / absent selection (bound claim; unbound claim with ratchet) | refusal/HOLD; no fallback to caller policy | RT | Decision (D-7) |
| T10 | Ceiling changed after authorization: lowered by a new activation; raised | lowered: effect-time guard refuses if exceeded; raised: capped by C and by the grant budget, never widens | RT | Source (guard) + Decision (D-7) |
| T11 | Restart and recovery | selection and ceilings reload from the durable store; identical seven-member digest; ledger unchanged | RT | Source |
| T12 | Cross-policy substitution (record or digest of another policy; one member swapped) | `policy_identity_mismatch` / containment refusal | RT | Source |
| T13 | Cross-tenant substitution | refused | RT | Source |
| T14 | No effect after refusal (T04, T05, T06b, T06c, T09, T12, T13) | dispatcher count 0; `used_effects` and effects rows unchanged | RT | Source |

## Added scenarios from the correction

| ID | Scenario | Expected outcome | Basis |
|---|---|---|---|
| T15 | Caller float `max_amount` in the governed path (`5.0`, `99.5`, `1e300`, `-0.0`) | `composition_caller_invalid` / `registry_caller_ceiling_unsupported`; no rounding or coercion | Decision (D-3 B) |
| T16 | Legacy caller float, no governed binding | unchanged evaluator behaviour (accepted) | Source |
| T17 | Operation amount int 2^53 + 1 | refused by `validate_snapshot`; float 2^53 + 2 accepted and compared as binary64 | Source |
| T18 | Operation amount `-0.0`, non-integral amount 0.5 at ceiling 0 | `-0.0` passes, 0.5 refused | Source |
| T19 | Coexistence: activate f1abc while f1ab `active` for the same five scope fields; reverse; f1ab-bound claim after withdrawal; unbound claim | activation refused `selection_conflict`; after withdrawal f1ab-bound refuses `selection_withdrawn`; unbound refuses by ratchet | Decision (D-1) |
| T20 | f1abc with participation `optional` | activation refused | Decision (D-7) |
| T21 | Effect-time: executor reports a ceiling above the record; `claim.amount` above record; `claim.max_effects` above record | `policy_not_subset` / refusal inside the lock before the effect insert | Source (F-01 pattern) |
| T22 | Composite does not widen f1ab: record set above caller; disjoint sets; empty set | intersection / `applied_deny_all` exactly as f1ab | Source |
| T23 | One identity: changing any one of the seven members changes the digest | digests differ | Source |

## Negative vectors (Registry)

V01 bad signature; V02 v2 signature as v3 and v3 as v2; V03 wrong family id; V04 wrong contract token; V05 duplicate key; V06 non-canonical encoding; V07 non-dict payload; V08 float/NaN/Infinity in source JSON (`json_number_unsupported`); V09 str-subclass key; V10 operator other than `intersection`; V11 oversized caller mapping; V12 f1ab-only payload (five members) presented as f1abc → `field_missing`; V13 `r08-v2` sixth-key refusal (`field_unknown`) unchanged.

## Properties

Exhaustive grid for C, R in {0, 1, 2, 3, 2^53 − 1, 2^53} (effects: from 1) checks `effective ≤ C`, `effective ≤ R` or `= C`, idempotent re-composition. Differential: composed policy vs baseline `LocalExecutionPolicy` over the same operations. Regression: v1/v2 vectors and f1ab narrowing tests unchanged.

## Qualification

These are builder tests, not independent qualification. Tier 1: independent qualification of the contract, the no-widening proofs, the effect-time guard and the Runtime integration is required before acceptance and is not performed by the builder, the lead or CI.
