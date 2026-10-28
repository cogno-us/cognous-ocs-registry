# M2 — Test matrix

Status: PROPOSAL. C = caller ceiling, R = Registry ceiling. "Source" = expected outcome is fixed by pinned evaluator/Registry source; "Decision" = depends on a ruling in `05` and must not be coded until ruled. Every scenario is asserted for both `max_amount` and `max_effects` unless noted. Rule: no test may show an effective value above C or a dispatched effect after a refusal.

## Required scenarios

| ID | Scenario | Expected outcome | Layer | Basis |
|---|---|---|---|---|
| T01 | R < C | effective = R; operations above R refused | Reg + RT | Source (min) |
| T02 | R = C | effective = C; no detail | Reg + RT | Source |
| T03 | R > C | effective = C; detail `registry_value_not_narrowing:<name>`; never above C | Reg + RT | Source (F4/F5 precedent) |
| T04 | Missing Registry field (`max_amount` or `max_effects`) | `field_missing`; record rejected whole; no policy; no effect | Reg + RT | Source (pattern) |
| T05 | Invalid Registry value (float, 5.0, bool, str, None, negative, > cap, int subclass, extra key) | `field_type_invalid` / `field_invalid` / `field_unknown`; no coercion | Reg | Source (pattern) |
| T06a | Zero `max_amount` (R=0 or C=0) | amount 0 passes (`0 > 0` false); any amount > 0 refused | RT | Source (evaluator `>`); R=0 meaning is [D-2] |
| T06b | Zero `max_effects` in record | deny-all: no policy built, no effect dispatched | Reg + RT | Decision [D-2] |
| T06c | Caller `max_effects` = 0 | `composition_caller_invalid` (evaluator needs ≥ 1) | Reg | Source |
| T07 | Exact boundary: amount = ceiling; effects = ceiling | allowed (comparison is `>`); ceiling + 1 refused; 2^53 and 2^53+1 | RT | Source |
| T08 | Multiple-effect attempts (`op.effects` ≠ 1; N+1-th effect under max_effects N; cumulative ledger) | refused; ledger count unchanged by the refused attempt | RT | Source (`effects` must equal 1; ledger) |
| T09 | Revoked selection | refusal/HOLD; no fallback to caller-only; no effect | RT | Decision [D-7] (match f1ab behaviour) |
| T10 | Ceiling changed after authorization (lowered; raised) | lowered: re-evaluated at effect time, refused if exceeded; raised: capped by C and grant/claim limits, never widens | RT | Source for the cap; staleness rule [D-7] |
| T11 | Restart and recovery | selection and ceilings reloaded from durable store; same `effective_policy_digest`; no effect replay beyond ledger | RT | Source (durable selection authority) |
| T12 | Cross-policy substitution (record bound to another policy digest) | containment refuses; no effect | RT | Source (policy-digest containment) |
| T13 | Cross-tenant substitution | refused; no effect | RT | Source (scope/tenant binding) |
| T14 | No effect dispatched after any refusal | dispatcher call count 0 and ledger/evidence unchanged for T04, T05, T06b, T09, T12, T13 | RT | Source |

## Additional negative vectors (Registry)

V01 bad signature; V02 v2 signature presented as v3 and v3 as v2 (domain separation); V03 wrong family id; V04 wrong contract token; V05 duplicate key; V06 non-canonical encoding; V07 non-dict payload; V08 float/NaN/Infinity in source JSON (`json_number_unsupported`); V09 str-subclass key; V10 operator other than `intersection`; V11 oversized caller mapping; V12 caller float (`5.0`, `1e3`) → `composition_caller_invalid` [D-3]; V13 `r08-v2` payload with a sixth key still refuses `field_unknown` (frozen behaviour).

## Properties

- Exhaustive grid over C, R in {0, 1, 2, 3, 2^53−1, 2^53} per member: `effective ≤ C`, `effective ≤ R` or `= C`, and idempotent re-composition.
- Differential: composed policy vs baseline `LocalExecutionPolicy` over the same operation set, for every grid point: the Registry path never allows what the baseline refuses.
- Regression: `r08-v1`/`r08-v2` vectors and the existing f1ab narrowing tests pass unchanged; `r08-v2` files byte-identical.

## Qualification

These are builder tests. Tier 1: independent qualification of the successor contract, the no-widening proofs and the Runtime integration is required before acceptance and is not performed by the builder, the lead or CI.
