# 4. Component ownership and adapter matrix

Status: planning only. Ownership follows ADR-REG-TR01: the selection issuer assigns the selection epoch; the enforcing component owns activation and high-water state; the registry never activates and never issues grants. Authority to authorize stays with the Control Plane. Source line cites are at Runtime `c5e97e87`, Control Plane `7a4bcd40`, registry `d61ef729`.

## Ownership matrix

| Concern | Registry | Runtime | Control Plane | Qualification |
|---|---|---|---|---|
| Typed record, manifest shape, strict loader, digest | **Owns** (`registry_successor`) | consumes verified output only | consumes verified output only | none |
| Family dispatch and per-family payload validation | **Owns** (new table) | none | none | none |
| Authenticated selection (ten-layer `verify_selection`), trust snapshot format | **Owns verification**; snapshot delivery is the host's | none | none | none |
| Selection epoch assignment | selection issuer (not the registry as activator) | none | none | none |
| Activation, high-water, anti-rollback, revoked set | **Does not own** (stateless transition function and vectors only) | **Owns** for Runtime scope (destination state) | **Owns** for Control Plane scope (host-side rebuild) | none |
| Evaluators and guardrails | none | **Owns** (`safe_executor.py`, frozen) | **Owns** (`bounded.py`, `runtime_authority.py`) | none |
| Authorization authority, grants, approvals, single-effect gate | never | consumes | **Owns** | none |
| Effect-time revalidation | provides identity and verdict | **Owns** the in-transaction guard | provides claim machinery only | independent oracle |
| Effective-policy identity object | **Owns** definition | carries into receipt/failure rows | evidence option decided in S4 | verifies |
| Independent oracle and verdicts | none | none | none | **Owns** (designated lead; architect may not self-certify Tier 1) |

## Adapter matrix (one typed adapter per enforcement owner)

| Family | Adapter owner | Input (already authenticated, decided) | Output | Narrowing rule | Code that stays | Refusal behaviour |
|---|---|---|---|---|---|---|
| F1a + F1b (five sets) | Runtime, new file `engine/local_policy_narrowing.py` (name indicative) | `PolicyDecision.effective` from `verify_and_decide` | `dataclasses.replace(caller_policy, **sets)` so `__post_init__` re-runs | Intersection; Runtime re-verifies each set is a subset of the caller's; exactly the five keys; `type(caller) is LocalExecutionPolicy` | `check` order and reason texts, `__post_init__`, target fields, `max_effects`, trusted-context binding | Optional: caller policy unchanged, receipt marker `applied=false`. Required: no dispatch, never the caller's wider policy. Empty effective set: deny without constructing a policy |
| F4 ages | Control Plane, host factory over a pure `age_bounds` helper | Typed F4 payload (two integers) from the registry decision | kwargs for `BoundedAuthorizationWorkflow` | `min(caller, registry)`, strict `int`, floor >= 1 | `_fresh`, tolerance, approval-binding block, gate | Registry value not narrowing: use caller value and record `registry_value_not_narrowing`. Required but invalid: HOLD, never a looser value |
| F5 age | Control Plane, same helper | Typed F5 payload (per action class) | per-class `min` applied to the profile before `model_validate`/`snapshot` | Same, per class; unknown class refused | `ActionClass` model untouched; profile dump and existing commitments byte-identical when no registry input | Same |
| `max_amount` (conditional) | Runtime, same adapter module | Typed payload `{unit, scale, value}` | ceiling converted to binary64 rounding **down** | Apply only when effective `allowed_units` after intersection is exactly the one declared unit, else refuse | `check` unchanged, `_strict_finite_number`, inclusive unit-less comparison, `ValueError`-before-institution behaviour | Cannot represent exactly: refuse. Zero ceiling: ruled in the D6 ADR |

Constraints on every adapter: pure function, no I/O, no import of registry code into the Runtime (the dependency points registry to engine today), no change to any frozen evaluator file, and the Runtime keeps the last non-widening gate.

## Reused contracts and mechanisms (nothing new where something exists)

| Need | Reused | Reference |
|---|---|---|
| Authenticated selection | Ten-layer `verify_selection`, injected `SignatureVerifier`, domain-separated signing input, snapshot expiry, issuer/key revocation | `registry_successor/verify.py:17-20, 60, 256, 322`; ledger `AUTHENTICATED-SELECTION-STATE` (IMPLEMENTED_NOT_QUALIFIED) |
| Required versus optional, deny-all versus refusal | `verify_and_decide` kinds `applied`, `applied_deny_all`, `overlay_not_applied`, `required_policy_unavailable`; participation equality | `decision.py:35-55, 83`; ledger `FAILURE-REFUSAL-SEMANTICS` |
| Anti-rollback floor | `TrustSnapshot.min_epochs` (stateless) | `verify.py:303`; test `test_a2_rollback_attempts_refused` (builder) |
| Revocation, expiry evaluation | Interval `[valid_from, valid_until)`, `selection_revoked`, key revocation | `verify.py:287-302` |
| Effect-boundary seam | The Runtime `operation_id` guard under `BEGIN IMMEDIATE` and the `OperationIdentityAtomicAuthorityEffectDestination` pattern (own table, no profile URN, no claim change) | `local_authority_effect.py:790, 860, 919`; `operation_identity_atomic_destination.py:23-39`; `atomic_local_control_plane_executor.py:84-87` |
| Claim expiry clamp (defence in depth) | `provision_claim(expires_at=selection.valid_until)` | `atomic_local_control_plane_executor.py:61-63` |
| Ownership assignment | ADR-REG-TR01 decisions 2 to 5 | ADR |
| Extractability test | P0 clauses (a) caller/constructor data, (b) code-owned bound remains, (c) narrow-only, (d) deterministic non-widening refusal | `docs/p0-contract-reconciliation/05-configuration-extraction-readiness.md` |
| Reference path | S03 allow-list contract, S04 overlay consumer, S05 differential equivalence (F1a, builder oracle, frozen) | `docs/s03-contract.md`, `registry_consumer`, `tests/test_s05_equivalence.py` |

## New work that has no existing counterpart

Family dispatch table and `r08-v2` five-set payload; integer-second and capped-min slots; `EffectivePolicyIdentity` and trust-snapshot fingerprint; snapshot-version floor and builder; Ed25519 verifier adapter (outside the core, hash-locked, synthetic keys only); conformance kit for the consumer high-water function; Runtime narrowing adapter; Runtime destination with selection-state, revoked-set and activation-log tables plus the in-transaction guard; Control Plane `age_bounds` helper and wiring; emulator integration gate (DT-01); independent oracle batteries.

## Key design decisions recorded here (Architect to confirm)

1. **Zero edits to `engine/safe_executor.py`.** The consumer re-hashes the evaluator file against `TrustConfig`, records bind its blob id and S05 Z2 pins it; any edit forces a re-pin of S01, every record and the S05 expectations. All new Runtime code goes in new files and two additive seams.
2. **B-lite carriage** for the commit-time check: the executor passes an immutable policy binding by keyword argument (as it passes `operation_id` today), and a destination subclass compares it under the lock and the lock-time clock against a trusted selection row. This needs no Control Plane change and no successor profile. It departs from the wording of R10 Option B ("the claim carries the binding"; both repositories change). The mechanism rests on a source reading and has not been tested; it is an Architect disposition (R10-F-01/02), and if the Architect chooses claim-carried binding instead, `EXT-S4-4` (Control Plane) becomes mandatory.
3. **Control Plane narrowing is host-side** and applied before construction, because Runtime forwards the profile snapshot and the four age attributes but no new kwarg.
4. **Deny-all is decided by the gate before a policy object is built.** The registry's composition contract says consumers must not build a `LocalExecutionPolicy` from empty sets (`registry_successor/compose.py:3-6`), so the gate denies without constructing one. Note the lanes disagreed on the Runtime side; this was checked directly at the pin: `LocalExecutionPolicy.__post_init__` **accepts** an empty `frozenset` (constructed an instance with an empty `allowed_institutions` at `c5e97e87`), where an empty set means deny-all for that dimension. The rule is therefore a registry-side convention, not a Runtime refusal, and the adapter must not rely on construction failing.
5. **Runtime policy-provider seam is folded into `EXT-S4-2`.** Lane B proposed an opt-in seam (RT-PR-3) and lane D proposed the destination guard; both touch `atomic_local_control_plane_executor.py`. They are one PR and one owner.
