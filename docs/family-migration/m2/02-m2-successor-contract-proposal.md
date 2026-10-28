# M2 — Successor-contract proposal (corrected): composite `f1abc` with governed ceilings `max_amount`, `max_effects`

Status: PROPOSAL (corrected after Architect review of head `338325ca…`). Non-authorizing. Not adopted. Frozen `r08-v2` is unchanged: schemas, vectors, signing domains and reason vocabularies are not edited. The only values newly governed are `max_amount` and `max_effects`; the five f1ab allow-sets are carried unchanged. Evidence for each source claim is in `05-blocking-architectural-decisions.md` (D-1) and `03-m2-implementation-blueprint.md`.

## 0. Selected architecture (Correction 1): OPTION B, composite successor family

`f1abc-local-execution-limits`, family version 1, registered ONLY in the new `r08-v3` table. Standalone f1c was not selected because the existing architecture cannot bind and enforce two families atomically (D-1 evidence). The composite carries exactly seven payload members and binds all seven into one effective policy identity, one selection and one activation.

## 1. Family identity and version

- Contract `r08-v3`; family id `f1abc-local-execution-limits` (28 characters, passes the Control Plane identifier pattern `[A-Za-z0-9][A-Za-z0-9._:-]{0,127}`); family version `1`.
- `r08-v3` registers no other family. `families.table_for_contract_version` gains one entry; the v1/v2 tables are not edited.

## 2. Authenticated record format

Same envelope discipline as `r08-v2` (canonical JSON, integers only, exact `dict`/`str`, no duplicate keys, detached signature over domain-separated canonical bytes). New contract token `r08-v3` and a new signing domain derived by the `r08-v2` rule with the version token replaced (exact string fixed at implementation and pinned by a vector; a v2 signature must not verify as v3 and conversely). Payload is EXACTLY seven members:

```
allowed_actions, allowed_adapters, allowed_units, allowed_institutions, allowed_authority_domains   (each: sorted, duplicate-free list of valid tokens, <= 256 entries; explicit [] is the explicit deny-all, exactly as f1ab)
max_amount   (int)
max_effects  (int)
```

Absent member `field_missing`; extra member `field_unknown`; non-dict `field_type_invalid`. The five set members reuse the f1ab validators by import (no copy, no edit of `v2_f1ab.py`).

## 3. Exact numeric types

`type(v) is int` for both ceilings. Refused with `field_type_invalid`: bool, float (including `5.0`, `-0.0`), Decimal, str, None, bytes, list, int subclasses. In source JSON a float or non-finite number never reaches validation (`json_number_unsupported`). No coercion, rounding, truncation, clamping or defaulting anywhere.

## 4. Valid ranges and boundary behaviour (D-4)

| Input | Registry `max_amount` | Registry `max_effects` |
|---|---|---|
| 0 | valid ceiling (amount 0 passes, amount > 0 refused) | valid record; **explicit deny-all**; no policy is built; no effect dispatched |
| 1 | valid | valid (ops with `effective_max_effects` 1 pass) |
| maximum accepted | 2^53 (9007199254740992) | 2^53 − 1 (9007199254740991) |
| maximum + 1 | `field_invalid` | `field_invalid` |
| negative | `field_invalid` | `field_invalid` |
| bool | `field_type_invalid` | `field_type_invalid` |
| float / Decimal / str / None / int subclass | `field_type_invalid` | `field_type_invalid` |
| overflow (> 2^63 − 1, e.g. 10^30) | `field_invalid` | `field_invalid` |

Source basis. `max_amount` 2^53: `safe_executor.MAX_EXACT_INTEGER_AMOUNT`. `max_effects` 2^53 − 1: derived, not chosen for symmetry. The evaluator requires only an exact int ≥ 1 and has no upper bound; the Control Plane derives `effective_max_effects = min(requirement, grant, action effect_limits)` over `_exact_int` values with no cap; the only hard storage limit is SQLite's signed 64-bit INTEGER (2^63 − 1) for `effect_budgets_v1.max_effects`. No Runtime or Control Plane limit forces a value below 2^63 − 1, so the bound is set by the Registry's own canonical-integer representation convention, 2^53 − 1 (`verify.MAX_SNAPSHOT_VERSION`; the Control Plane binding uses the same 9007199254740991 for `trust_snapshot_version`). A Registry ceiling larger than any real budget is harmless because composition only narrows. Alternative for the Architect: 2147483647 (`MAX_INT`, the F4/F5 convention).

## 5. Caller baseline (what the Registry narrows)

| Member | Caller value accepted in the governed path | Otherwise |
|---|---|---|
| `max_amount` | exact `int`, 0 ≤ v ≤ 2^53 | `composition_caller_invalid` |
| `max_effects` | exact `int`, v ≥ 1 (any size; the evaluator has no upper bound, and `min(caller, registry)` is bounded by the record) | `composition_caller_invalid` |
| five sets | frozenset of non-empty str (as f1ab) | `composition_caller_invalid` |

## 6. Float compatibility (D-3, Correction 2): decision B, explicit refusal

Characterization of the existing evaluator (`LocalExecutionPolicy.check` via `_strict_finite_number`): `max_amount` is accepted if `type is int` with |v| ≤ 2^53, or `type is float` and finite and not `< 0`. That admits non-integral floats (99.5), integral floats (5.0), very large floats (1e300, all integral and above 2^53), subnormals and `-0.0` (not `< 0`, compares equal to 0). The value is converted with `float()` and compared as `float(op.amount) > max_amount`.

Option A (accommodate) is rejected: a caller float below the Registry value would be the effective ceiling, but the effective-policy digest preimage is canonical JSON, which refuses floats; carrying it would need a new float encoding in the identity preimage, weakening or complicating digest binding. Therefore **in the governed path a caller float `max_amount` (any float, including `5.0` and `-0.0`) is refused** with `composition_caller_invalid` (Runtime evidence code `registry_caller_ceiling_unsupported`). This is a documented compatibility limitation: the operator expresses the ceiling as an exact int. No rounding, truncation, coercion or ungoverned fallback occurs, and the legacy evaluator and callers outside the governed path (no governed binding) are unchanged.

## 7. Numeric comparison semantics (Correction 2)

The evaluator is preserved. What source demonstrates, and what this contract does not claim:

- Comparison is binary64: `float(op.amount) > float(max_amount)`. Registry integers ≤ 2^53 convert exactly, so for them the comparison is exact between two binary64 values; boundary equality passes (`>` is strict), ceiling + 1 refuses.
- Operation amounts: `validate_snapshot` admits exact ints with |v| ≤ 2^53 or finite floats ≥ 0 (including `-0.0`, equal to 0). An int operation amount above 2^53 is refused before comparison; a float above 2^53 is accepted as a binary64 value and compared normally.
- Non-integral amounts are compared as their binary64 value (0.5 > 0 refuses at ceiling 0). A decimal amount whose binary64 value rounds to an integer (for example 5.0000000000000001 parses to 5.0) is compared as 5.0; precision lost before the evaluator is outside this contract.
- Registry ceilings make NO claim about mathematical comparison of the original decimal amount, and no claim about exactness beyond binary64 values that reach the evaluator. The Control Plane's own `proposal.amount > permission["max_amount"]` is a separate Python mixed int/float comparison and is not changed.
- `max_effects` is integer-only: `op.effective_max_effects > max_effects`, no conversion.

## 8. Missing-value, deny-all and refusal semantics

- Absent selection for the pin scope: unchanged legacy behaviour (caller policy) only where the pin scope has never been activated; a governed activation uses participation `required`, so an unbound claim refuses (`selection_missing`) and there is no fallback (D-7).
- Revoked, withdrawn, stale, absent, invalid or mismatched governed selection → refusal/HOLD with no effect; never the ungoverned caller policy.
- Explicit deny-all = any set intersecting to empty, or record `max_effects = 0`. Composition returns `deny_all = True`; the Runtime builds no `LocalExecutionPolicy` (the evaluator raises on `max_effects` < 1) and dispatches no effect. `max_amount = 0` is a valid ceiling, not deny-all.
- Refusal codes reuse existing sets (`composition_*`, `field_*`); no new reason code is anticipated. A refusal carries no effective policy.

## 9. Narrowing operation and f1ab preservation

Operator `intersection` only. Five sets: exactly the f1ab composition (intersection; disjoint → `applied_deny_all` naming the fields; caller sets never exceeded). Ceilings: `effective = min(caller, registry)`; registry ≥ caller yields the caller with detail `registry_value_not_narrowing:<names>`. Result ≤ caller for all seven members. A composite record can widen no f1ab restriction: the set semantics are the f1ab functions, and a record set above the caller is cut to the caller by intersection.

## 10. Digest and signature binding (one identity)

`effective_policy_digest(FAMILY, effective)` over canonical JSON with family `f1abc-local-execution-limits`, version, and all seven members (sets sorted, ceilings ints) using the `v2_policy_identity` pattern with a v3 identity row. The record digest, family id and this digest are bound into the one signed selection, so no subset of the seven members can be replaced independently.

## 11. Consumer compatibility

`r08-v2` consumers are unchanged and refuse `r08-v3` records. `r08-v3` consumers refuse a v2 record for this family. The Control Plane treats `family` as an identifier string and `effective_policy_digest` as an opaque sha256 (D-6); the binding profile `ocs-policy-binding/1` is reused. Residual: its digest-domain constant names `r08-v2` (a Control Plane label); confirm that reuse is acceptable, otherwise the minimum Control Plane change is a new profile/domain constant (D-6).

## 12. Version transition and coexistence with an active f1ab selection

- `f1abc` is a new governed scope key (the scope includes `family`): fresh lineage, epoch and ratchet; it does not touch f1ab epochs.
- A claim carries exactly one binding, so a claim bound to f1ab would skip the ceilings. Rule: activation of an `f1abc` scope is refused (`selection_conflict`) while an `active` f1ab row exists for the same consumer, tenant, institution, authority domain and operation; the f1ab selection is withdrawn first (existing `withdraw` entry). After withdrawal, an f1ab-bound claim refuses `selection_withdrawn` and an unbound claim refuses by the f1ab ratchet; neither widens. The gap between withdrawal and f1abc activation fails closed (availability only).
- The symmetric rule applies: f1ab cannot be (re)activated while an f1abc row is active for the same pin scope.
- Control Plane issues bindings with the new family only after cutover. No restriction is dropped silently: the seven members replace the five-member f1ab record only through this explicit sequence.

## 13. No-widening proof obligations

- P1 effective ≤ caller for all seven members (exhaustive small grids + boundaries 0, 1, 2^53−1, 2^53).
- P2 each ceiling ≤ its record value unless the record is above the caller (then = caller); sets ⊆ record sets.
- P3 no refusal returns an effective policy; no default or caller value is returned as governed.
- P4 no coercion: every non-exact-int ceiling and every caller float is refused.
- P5 effect-time: executor-reported ceilings, `claim.amount` and `claim.max_effects` are checked against the authenticated record inside the lock; sets keep the F-01 subset check.
- P6 substitution of record, family, policy digest, tenant or scope is refused by identity binding.
- P7 `r08-v1`/`r08-v2` files, vectors and the f1ab narrowing behaviour are byte-identical.
- P8 no additional effect authority: the Registry ceiling never adds to, replaces or modifies the grant budget or ledger accounting (§ Effect-count mapping in `03`).
- P9 Tier 1: independent qualification is required and is not performed by the builder, the lead or CI.
