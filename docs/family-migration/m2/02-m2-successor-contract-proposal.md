# M2 — Successor-contract proposal: F1c numeric ceilings (`max_amount`, `max_effects`)

Status: PROPOSAL. Non-authorizing. Not adopted. Frozen `r08-v2` is unchanged. Scope is `max_amount` and `max_effects` only; nothing else is added. Open choices are marked **[D-n]** and listed in `05-blocking-architectural-decisions.md`.

Source facts this design follows (all read from pinned source): Registry canonical JSON refuses floats and non-finite numbers (`json_number_unsupported`), so records carry integers only. The Runtime evaluator `LocalExecutionPolicy.check` (unchanged) takes `max_amount` as an exact int or finite float, ≥ 0, int ≤ 2^53, compared `float(op.amount) > max_amount`; and `max_effects` as an exact int ≥ 1, compared `op.effective_max_effects > max_effects`; `op.effects` must equal 1. The numeric-narrowing precedent is F4/F5 (`registry_successor/v2_age_bounds.py`): exact ints, `min(caller, registry)`, a registry value above the caller yields the caller with detail `registry_value_not_narrowing:<names>`.

## 1. Family identity and version

- Contract version: `r08-v3` (new, additive successor; `r08-v1` and `r08-v2` tables, codes, vectors and signing domain untouched). Dispatch through `families.table_for_contract_version`, which gains one entry.
- Family id: `f1c-local-execution-ceilings`, family version `1`. **[D-1]**: whether this ships standalone (binding carries one family, so a second binding is needed) or as the payload-superset composite `f1abc-…` (five f1ab sets + the two ceilings). The payload rules for the two ceiling members below hold in either case.
- `r08-v3` registers only this family. It does not re-register f1ab, F4, F5.

## 2. Authenticated record format

Same envelope as `r08-v2` (canonical JSON, integers only, detached signature over domain-separated canonical bytes, exact `dict`/`str` types, no duplicate keys). Differences: contract token `r08-v3` and a new signing domain string derived by the `r08-v2` rule with the version token replaced (exact string fixed at implementation and pinned by a signature vector; a v2 signature must not verify under v3 and conversely). Payload is EXACTLY:

```
{"max_amount": <int>, "max_effects": <int>}
```

## 3. Exact numeric types

`type(v) is int` for both members. Refused with `field_type_invalid`: bool, float (including 5.0), Decimal, str, None, bytes, list, int subclasses. No coercion, rounding, clamping, defaulting or float-to-int conversion anywhere (record, caller, effective).

## 4. Valid ranges

| Member | Registry record range | Caller (baseline) range | Source |
|---|---|---|---|
| `max_amount` | 0 ..= 2^53 | exact int 0 ..= 2^53 | evaluator: ≥ 0, int ≤ `MAX_EXACT_INTEGER_AMOUNT` = 2^53 |
| `max_effects` | 0 ..= B | exact int 1 ..= B | evaluator: ≥ 1 for the caller; record 0 is the explicit deny-all (§6) **[D-2]**; B proposed 2^53 **[D-4]** |

Out of range → `field_invalid`. Negative → `field_invalid`. No NaN/infinity can occur (canonical JSON refuses them).

## 5. Missing-value semantics

- Absent member → `field_missing`; extra member → `field_unknown`; non-dict payload → `field_type_invalid`. The record is rejected whole; no partial application, no default.
- No selection/record for the scope: behaviour is unchanged from today (the caller policy governs, Registry not consulted). A selection that names this family but whose record is absent, unverifiable, stale or revoked → existing refusal/HOLD, never a higher or default value **[D-7]**.

## 6. Explicit deny-all

Only an explicit record `max_effects = 0` is deny-all. Composition returns `deny_all = True` with no policy construction; consumers must not build a `LocalExecutionPolicy` (the evaluator would raise on 0) and must dispatch no effect. Absence of a value is never deny-all or allow-all; it is `field_missing`. `max_amount = 0` is a valid ceiling, not deny-all (evaluator semantics: only an amount > 0 is refused) **[D-2]**.

## 7. Narrowing operation

Operator `intersection` (frozen dispatch name; any other → `composition_operator_unsupported`). Per member: `effective = min(caller, registry)`. Registry ≥ caller → effective = caller, detail `registry_value_not_narrowing:<names>`. The result is never greater than the caller value for either member.

## 8. Baseline / caller precedence

The caller `LocalExecutionPolicy` values are the baseline authority and are never replaced. Invalid caller (wrong key set, float, bool, out of range, > cap) → `composition_caller_invalid`; the Registry value never substitutes for it **[D-3]** (floats refused in the governed path because the identity digest preimage is integer-only). Grant/claim limits (`claim.max_effects`, effect-budget ledger, per-action amount) continue to apply independently: the effective ceiling for an operation is the minimum of all applicable authorized limits.

## 9. Invalid / unsupported refusal

Reuses existing codes: `composition_record_invalid`, `composition_family_unsupported`, `composition_operator_unsupported`, `composition_caller_invalid`, `field_*`. A refusal carries no effective policy. No new reason code is anticipated; if one is found necessary it is a contract amendment, not an implementation detail.

## 10. Digest and signature binding

`effective_policy_digest` is computed over canonical JSON of {contract `r08-v3`, family, family version, effective `{max_amount, max_effects}`} using the `v2_policy_identity` pattern with a v3 identity row. The record digest and family id are bound into the signed selection, so a record for another family, policy digest, scope or tenant cannot be substituted. Exact preimage layouts are pinned by vectors.

## 11. Consumer compatibility

`r08-v2` consumers are unchanged and refuse `r08-v3` records (unregistered contract version; existing refusal). `r08-v3` consumers refuse `r08-v2` records for this family. The Control Plane is expected to treat the family as opaque (no family constants found in its source) **[D-6]**.

## 12. Version transition

A new family is a new scope key: no prior epoch exists, so activation starts the ratchet fresh and does not touch f1ab epochs. Rollback is by revocation/withdrawal, which fails closed (refusal), not by falling back to caller-only silently **[D-7]**. `r08-v2` stays frozen and valid for f1ab.

## 13. No-widening proof obligations

- P1 `effective_amount ≤ caller.max_amount` and `effective_effects ≤ caller.max_effects` for every valid input (exhaustive small grid plus boundary values 0, 1, 2^53−1, 2^53).
- P2 `effective ≤ registry` for each member, except where the registry is above the caller (then = caller).
- P3 No refusal returns an effective policy; no error path returns a default or the caller value as if governed.
- P4 No type coercion: every non-exact-int input is refused (vector per type).
- P5 At effect time the guard compares the operation against the record directly (not only the composed policy), so the operation value is bounded by the record and by the caller ceiling.
- P6 Substitution of record (policy, tenant, family, version, scope) is refused by identity binding.
- P7 `r08-v2` frozen files and vectors are byte-identical after the change.
- P8 Independent qualification of the above (Tier 1) is required; builder tests are not independent.
