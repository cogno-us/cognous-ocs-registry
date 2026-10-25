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
| Effect-time revalidation | provides identity and verdict | **Owns** the in-transaction guard | **Owns the claim-carried binding** (`EXT-S4-4`) | independent oracle |
| Effective-policy identity object | **Owns** definition | carries into receipt/failure rows | carries in the claim (mandatory) | verifies |
| Independent oracle and verdicts | none | none | none | **Owns** (designated lead; architect may not self-certify Tier 1) |

## Adapter matrix (one typed adapter per enforcement owner)

| Family | Adapter owner | Input (already authenticated, decided) | Output | Narrowing rule | Code that stays | Refusal behaviour |
|---|---|---|---|---|---|---|
| F1a + F1b (five sets) | Runtime, new file `engine/local_policy_narrowing.py` (name indicative) | `PolicyDecision.effective` from `verify_and_decide` | `dataclasses.replace(caller_policy, **sets)` so `__post_init__` re-runs | Intersection; Runtime re-verifies each set is a subset of the caller's; exactly the five keys; `type(caller) is LocalExecutionPolicy` | `check` order and reason texts, `__post_init__`, target fields, `max_effects`, trusted-context binding | Optional: caller policy unchanged, receipt marker `applied=false`. Required: no dispatch, never the caller's wider policy. Empty effective set: deny without constructing a policy |
| F4 ages | Control Plane, host factory over a pure `age_bounds` helper | Typed F4 payload (two integers) from the registry decision | kwargs for `BoundedAuthorizationWorkflow` | `min(caller, registry)`, strict `int`, floor >= 1 | `_fresh`, tolerance, approval-binding block, gate | Registry value not narrowing: use caller value and record `registry_value_not_narrowing`. Required but invalid: HOLD, never a looser value |
| F5 age | Control Plane, same helper | Typed F5 payload (per action class) | per-class `min` applied to the profile before `model_validate`/`snapshot` | Same, per class; unknown class refused | `ActionClass` model untouched; profile dump and existing commitments byte-identical when no registry input | Same |
| `max_amount` (**DEFERRED, not V1; design note only**) | Runtime, same adapter module (not built) | Typed payload `{unit, scale, value}` | ceiling converted to binary64 rounding **down** | Apply only when effective `allowed_units` after intersection is exactly the one declared unit, else refuse | `check` unchanged, `_strict_finite_number`, inclusive unit-less comparison, `ValueError`-before-institution behaviour | Cannot represent exactly: refuse. Zero ceiling: ruled in the D6 ADR |

Constraints on every adapter: pure function, no I/O, no import of registry code into the Runtime (the dependency points registry to engine today), no change to any frozen evaluator file, the Ed25519 verifier stays an adapter outside the core, and the Runtime keeps the last non-widening gate.

## Reused contracts and mechanisms (nothing new where something exists)

| Need | Reused | Reference |
|---|---|---|
| Authenticated selection | Ten-layer `verify_selection`, injected `SignatureVerifier`, domain-separated signing input, snapshot expiry, issuer/key revocation | `registry_successor/verify.py:17-20, 60, 256, 322`; ledger `AUTHENTICATED-SELECTION-STATE` (IMPLEMENTED_NOT_QUALIFIED) |
| Required versus optional, deny-all versus refusal | `verify_and_decide` kinds `applied`, `applied_deny_all`, `overlay_not_applied`, `required_policy_unavailable`; participation equality | `decision.py:35-55, 83`; ledger `FAILURE-REFUSAL-SEMANTICS` |
| Anti-rollback floor | `TrustSnapshot.min_epochs` (stateless) | `verify.py:303`; test `test_a2_rollback_attempts_refused` (builder) |
| Revocation, expiry evaluation | Interval `[valid_from, valid_until)`, `selection_revoked`, key revocation | `verify.py:287-302` |
| Effect-boundary seam (guard location only; the binding itself is claim-carried) | The Runtime `operation_id` guard under `BEGIN IMMEDIATE` and the `OperationIdentityAtomicAuthorityEffectDestination` pattern (own table, no profile URN, no claim change) | `local_authority_effect.py:790, 860, 919`; `operation_identity_atomic_destination.py:23-39`; `atomic_local_control_plane_executor.py:84-87` |
| Claim expiry clamp (defence in depth) | `provision_claim(expires_at=selection.valid_until)` | `atomic_local_control_plane_executor.py:61-63` |
| Ownership assignment | ADR-REG-TR01 decisions 2 to 5 | ADR |
| Extractability test | P0 clauses (a) caller/constructor data, (b) code-owned bound remains, (c) narrow-only, (d) deterministic non-widening refusal | `docs/p0-contract-reconciliation/05-configuration-extraction-readiness.md` |
| Reference path | S03 allow-list contract, S04 overlay consumer, S05 differential equivalence (F1a, builder oracle, frozen) | `docs/s03-contract.md`, `registry_consumer`, `tests/test_s05_equivalence.py` |

## New work that has no existing counterpart

Family dispatch table and `r08-v2` five-set payload; integer-second and capped-min slots; `EffectivePolicyIdentity` and trust-snapshot fingerprint; snapshot-version floor and builder; Ed25519 verifier adapter (outside the core, hash-locked, synthetic keys only); conformance kit for the consumer high-water function; Runtime narrowing adapter; Runtime destination with selection-state, revoked-set and activation-log tables plus the in-transaction guard; Control Plane `age_bounds` helper and wiring; emulator integration gate (DT-01); independent oracle batteries.

## Key design decisions recorded here (Architect to confirm)

1. **Zero edits to `engine/safe_executor.py`.** The consumer re-hashes the evaluator file against `TrustConfig`, records bind its blob id and S05 Z2 pins it; any edit forces a re-pin of S01, every record and the S05 expectations. All new Runtime code goes in new files and two additive seams.
2. **Claim-carried binding (Architect ruling; B-lite rejected).** The authorization claim carries the effective-policy identity; the Control Plane claim machinery (`provision_claim`/`verify_local_execution_claim`) gains an additive successor profile (`EXT-S4-4`), the Runtime destination guard compares the claim-carried identity under the lock and the lock-time clock against a trusted selection row, and both repositories re-pin (`EXT-S4-5`). Keyword-argument carriage is rejected. Commit-time revocation, expiry and epoch checks remain essential, and EXT-S4-4 is mandatory. The mechanism rests on a source reading and has not been tested.
3. **Control Plane narrowing is host-side** and applied before construction, because Runtime forwards the profile snapshot and the four age attributes but no new kwarg.
4. **Deny-all is decided by the gate before a policy object is built.** The registry's composition contract says consumers must not build a `LocalExecutionPolicy` from empty sets (`registry_successor/compose.py:3-6`), so the gate denies without constructing one. Note the lanes disagreed on the Runtime side; this was checked directly at the pin: `LocalExecutionPolicy.__post_init__` **accepts** an empty `frozenset` (constructed an instance with an empty `allowed_institutions` at `c5e97e87`), where an empty set means deny-all for that dimension. The rule is therefore a registry-side convention, not a Runtime refusal, and the adapter must not rely on construction failing.
5. **Runtime guard is `EXT-S4-2`, built after the re-pin.** The destination guard and the executor passthrough touch `atomic_local_control_plane_executor.py`; they are one PR and one owner and read the claim-carried identity.
6. **`r08-v2` preserves `r08-v1` behaviour** (strict superset; golden outputs byte-identical) and all 46 registry outcomes require safe mappings (REFUSE, DENY, HOLD or RETRY), enforced by a completeness test.
7. **Emulator host belongs to the registry, not the qualification repo**, so the independent oracle never tests its own fixture.
8. **Durable selection state needs custody and anti-rollback qualification**; it is never seeded from a claim.

## Schema-readiness for policy on/off management (acceptance criterion for future Ergonomics integration)

Status: documentation-level requirement. It adds **no UI, no V1 field, no per-field toggle and no operator decision**; the approved eight fields and atomic Route B scope are unchanged. It makes sure the typed contracts already planned can later back a management surface (`cognous-open-control-stack-ergonomics`) without a second authorization mechanism. Verified against `registry_successor/` at `258a165`: `r08-v1` has no activation and no withdrawal vocabulary (record `status` is deliberately absent; `operationally_authorized` is always `False`; only the frozen legacy `r08-s03` record has `status`).

### The four distinctions: owner, field, and what is already there

| Distinction | Owner | Typed field and closed values | Status today |
|---|---|---|---|
| SELECTED / NOT_SELECTED (per scope: tenant, institution, authority domain, operation, family) | Selection issuer, signed in the `r08-v2` selection statement | Selected = a verified, in-window, head-of-chain selection with `disposition = select`. Not selected = none verified for the scope (`selection_missing`) or the head is `disposition = withdraw` (`selection_withdrawn`) | Positive selection exists (`selection.py` statement). **Withdrawal is missing: smallest additive change below (A1)** |
| REQUIRED / OPTIONAL | Selection statement and the caller, per operation | `participation` in `{required, optional}` (`common.PARTICIPATION`); mismatch is `participation_mismatch`; decision kinds `applied`, `applied_deny_all`, `overlay_not_applied` (optional only, caller unchanged), `required_policy_unavailable` (required only, never the caller policy). **Planned** consumer-owned ratchet `scope_required` (never cleared by selection or UI; not in `r08-v1`, where `decision.py` takes participation anew on every call) | `participation` present, no change. **The `scope_required` ratchet is planned, not present: persistence is specified below (A4)** |
| ACTIVE / INACTIVE | Enforcing component only (ADR-REG-TR01); never stored in the registry | Activation-state row per scope key with closed `activation_state` in `{active, withdrawn, revoked}`; no row = not activated; closed log `entry_type` in `{activate, withdraw, revoke, sync}` in the hash-chained activation log | Activation is planned (`EXT-S4-0`, `EXT-S4-2`) but the **state vocabulary is unspecified: smallest additive change below (A2)** |
| ENABLED / DISABLED (future UI) | Presentation only | **No stored field.** A pure mapping from the derived `policy_state` below | Absent by design; mapping fixed here (A3) |

### Distinct lifecycle states (disabled, absent, revoked, expired, superseded)

| State | Where it comes from | Distinguishing code or field |
|---|---|---|
| absent / not selected | no verified selection for the scope | `selection_missing` (registry); no activation row |
| selected, not activated | verified selection, no consumer activation row | no row; the guard refuses with the consumer's activation-unavailable code and never evaluates the selection |
| active | row `activation_state = active`, in window, epoch equals the row and is at or above the high-water | none (success path; identity recorded in evidence) |
| withdrawn (the "disabled" state) | authenticated `disposition = withdraw` selection at a strictly higher epoch, applied by the consumer | `selection_withdrawn` (registry), `activation_state = withdrawn` (consumer) |
| revoked | terminal revocation entry for `(selection_id, epoch)`; never resurrected by reactivation or lineage | `selection_revoked`, `issuer_key_revoked`; `activation_state = revoked` mirrors the terminal table |
| expired / not yet valid | `effective.valid_until` / `valid_from` against the lock-time clock | `selection_expired`, `selection_not_yet_effective`, `trust_snapshot_expired` |
| superseded | a higher epoch exists for the scope; derived, never stored | `selection_epoch_stale`, `selection_conflict`, `selection_supersession_invalid` |
| unknown | state unreadable, restored from an older copy, or publication unacknowledged (DT-04) | fail closed; never rendered as active |

### Derived read model: `policy_state`

`policy_state` is a closed enum **computed on read and never stored, never accepted as input and never authoritative**: `not_selected`, `selected_not_activated`, `active`, `withdrawn`, `revoked`, `expired`, `not_yet_valid`, `superseded`, `unknown`. Precedence when several apply: `unknown`, `revoked`, `withdrawn`, `superseded`, `expired` / `not_yet_valid`, `active`. Each value carries the closed reason code from the table above. A conformance function (pure, in the `EXT-S1-8` kit) defines it once so that every consumer and the UI derive the same value.

### Smallest additive changes (no new booleans, no per-field toggle)

- **A1 (selection withdrawal), owner `EXT-S1-1` ADR, implemented in `EXT-S1-2`/`S1-5`:** the new `r08-v2` selection statement carries a closed `disposition` in `{select, withdraw}`. A `withdraw` statement must name a prior selection (`supersedes` required and strictly lower epoch), carries no record pin, and signs under the same `r08-v2` domain. It resolves to the new code `selection_withdrawn`, whose decision is the ordinary one for the participation: `overlay_not_applied` for optional (caller policy unchanged) and `required_policy_unavailable` for required (refuse or hold, never the caller policy, never success). `CODES_V2` is therefore the 46 `r08-v1` codes plus the additions the ADR enumerates: `trust_snapshot_version_stale` and `selection_withdrawn`. `r08-v1` bytes and behaviour are untouched (additive successor, R8).
- **A2 (activation vocabulary), owner `EXT-S4-0` ADR, implemented in `EXT-S4-2`:** the activation-state row carries `activation_state` in `{active, withdrawn, revoked}` and the activation log carries `entry_type` in `{activate, withdraw, revoke, sync}`. A transition is written only by the existing `activate_selection` or `sync` writers from an authenticated selection, withdrawal or revocation; there is **no local-only writer and no UI-writable column**. Withdrawal or activation at an epoch not strictly greater than the row is refused; reactivation of a revoked epoch is refused. The ADR also reconciles the table names to one set and records the high-water table (the plan names high-water state in `EXT-S1-8` and the residual risks).
- **A3 (presentation mapping), owner `EXT-S4-0` ADR (doc only):** ENABLED = `active`. DISABLED = `withdrawn` or `not_selected`. Revoked, expired, superseded, not-yet-valid and unknown render with their own reason and are never shown as a plain toggle state. For a **required** scope a withdrawn, revoked or expired policy is shown as "REQUIRED, UNAVAILABLE: operations refuse", never as "disabled".
- **A4 (required-scope ratchet), owner `EXT-S4-0` ADR, implemented in `EXT-S4-2`:** the enforcing component persists `scope_required` per scope key in its own durable state (one trusted writer; never seeded from a claim; included in the hash-chained log and in restore and anti-rollback custody). Once set, a call, selection or UI request that presents `optional` for that scope is refused (`participation_mismatch`) and clearing is only an explicit, authorized, versioned, logged operation that is not built in V1. Until `EXT-S4-2` exists nothing prevents a required scope being presented as optional per call; this is disclosed, not claimed. Tests: downgrade attempts (claim, selection, caller, restore of an older store) refuse; the ratchet survives restart; a restored older store fails closed until re-baselined.
- **Not changed:** `participation` stays the only required/optional source; `EffectivePolicyIdentity` stays immutable and carries no state; `scope_required` stays a ratchet; no new family; `max_amount` has no slot.

### Acceptance criteria (documentation-level; checked by `EXT-S1-1`, `EXT-S4-0` and the QG-05, 06, 08, 09, 12 batteries)

1. Selection, participation and activation are three separate typed fields with closed values; no duplicate boolean carries the same meaning.
2. Absent, withdrawn, revoked, expired and superseded each have a distinct code or derivation (table above); none collapses into another or into success.
3. A UI toggle is a request, not a write: ENABLE and DISABLE are submitted as signed, versioned selection or withdrawal statements by the authorized issuer, then applied by the consumer. No UI action changes `activation_state`, `participation` or `scope_required` directly.
4. A toggle can never bypass required-policy enforcement: a required scope that becomes withdrawn, revoked, expired or unavailable refuses; it is never a way to run with the caller policy.
5. Code-owned guardrails (evaluator order and reasons, floors, `safe_executor.py` blob `2fc880da`, approval binding) are not toggleable and are not represented in any state.
6. Activation and anti-rollback stay consumer-owned; the registry holds no activation state and issues no grant or effect authority.
7. Every transition is attributable and recorded: an authenticated statement (issuer key, selection id, epoch, supersedes), a hash-chained log entry, and the effective-policy identity in evidence. Reversal is only a new, strictly higher-epoch authenticated statement; nothing is edited in place.
8. A deliberate transition cannot silently widen authority. Composition stays `min(caller, registry)`, so no state can exceed the caller's own policy or a code bound. Relaxing from a previously narrowed registry state through a deliberate selection or withdrawal change is possible only through an authenticated higher-epoch statement, is recorded as such, and is visible in evidence. **Failure-driven fallback is separate and is disclosed, not prevented:** for an optional scope, an expired, unavailable, revoked or withdrawn selection returns `overlay_not_applied` and the unchanged caller policy (`decision.py` optional path), which can be wider than the previous narrowing and needs no new signed statement. Only a required scope refuses. A scope that must not relax on failure must be marked required.
9. Tests that must exist (predeclared in `S5-1`): withdrawn versus absent versus revoked versus expired versus superseded each produce their own code for required and optional participation; a withdraw statement without `supersedes`, at a lower or equal epoch, or with a record pin is refused; a revoked epoch is not resurrected by a later `activate`; no code path writes `activation_state` without an authenticated statement; `policy_state` precedence cases; a required scope never returns the caller policy under any state; the `scope_required` downgrade negatives of A4.
