# M2 — Blocking architectural decisions

Status: for Architect ruling. Each item blocks only the stated part; none blocks this proposal. The recommendation lets implementation start without further preparation.

| ID | Decision | Options | Recommendation | Blocks |
|---|---|---|---|---|
| D-1 | Family architecture (policy binding carries one family) | (a) standalone `f1c-local-execution-ceilings` plus consumer support for two bindings; (b) composite `f1abc-…` carrying the five f1ab sets and both ceilings, one binding | (a) if Control Plane and Runtime accept two bindings at no new grant authority; otherwise (b). Ceiling members are identical in both | PR-1 family id, PR-4 |
| D-2 | Zero semantics | `max_effects` record 0 = explicit deny-all, `max_amount` 0 = valid ceiling (zero-amount operations pass); or both zero = deny-all | Proposed in `02`: effects 0 = deny-all, amount 0 = ceiling | PR-1 ranges, T06 |
| D-3 | Caller float ceilings in the governed path | refuse (`composition_caller_invalid`); or accept finite floats and fall back to a non-governed digest | Refuse; the identity preimage is integer-only and canonical JSON refuses floats | PR-1 composer, V12 |
| D-4 | Registry upper bound for `max_effects` (and confirmation of 2^53 for `max_amount`) | 2^53; or 2147483647 (F4/F5 `AGE_MAX` precedent) | 2^53 for `max_amount` (source); 2^53 for `max_effects` for symmetry | PR-1 ranges |
| D-5 | Successor mechanism | new `r08-v3` table and signing domain; or additive family in `r08-v2` (excluded by v2 text) | `r08-v3` (Architect-preferred; v2 stays frozen) | PR-1 |
| D-6 | Control Plane treats family and digest as opaque | confirm; or identify a family allow-list | Confirm opaque (no family constants found in its source) | PR-4 |
| D-7 | Activation, staleness and revocation | new scope key and fresh ratchet; revoked or withdrawn selection fails closed (refusal) as for f1ab; changed ceiling re-evaluated at effect time | As stated; no silent fallback to caller-only after a revocation | PR-2/3, T09, T10 |

## Implementation authorization recommendation

Authorize PR-1 (Registry `r08-v3` family, validation, composition, vectors) once D-1 to D-5 are ruled; PR-2/PR-3 (Runtime) follow without further design once D-7 is ruled. Do not authorize release or production use; Tier 1 independent qualification remains required before acceptance.

## Standing holds (unchanged)

M2 proposal: AUTHORIZED. M2 implementation: NOT YET AUTHORIZED. V09 independent assurance: separate workstream. Ed25519: SECURITY-HELD. Release/publication/production: HOLD.
