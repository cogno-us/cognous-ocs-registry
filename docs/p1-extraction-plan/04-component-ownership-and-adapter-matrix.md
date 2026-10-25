# 4. Component ownership, adapters and claim-carried binding

Status: planning only; nothing here is built or tested. Ownership follows ADR-REG-TR01: the selection issuer assigns the selection epoch; the enforcing component owns activation and high-water state; the registry never activates and never issues grants or approvals. Authority to authorize stays with the Control Plane. Source line cites are at Runtime `c5e97e87`, Control Plane `7a4bcd40`, registry `d61ef729`. Mechanism descriptions are **source readings** (design intent), not tested results. Binding rulings R1 to R14 are applied, not reopened.

## Ownership matrix

| Concern | Registry | Runtime | Control Plane | Qualification |
|---|---|---|---|---|
| Typed record, manifest shape, strict loader, digest | **Owns** (`registry_successor`, `r08-v2` in new files) | consumes verified output only | consumes verified output only | none |
| Family dispatch and per-family payload validation | **Owns** (new table) | none | none | none |
| Authenticated selection (ten-layer verification), trust snapshot format | **Owns verification**; snapshot delivery is the host's | none | none | none |
| Selection epoch assignment | selection issuer (not the registry as activator) | none | none | none |
| Activation, high-water, activation epoch, revocation and withdrawal state | **Does not own** (stateless transition function and vectors only) | **Owns** for Runtime scope (destination tables, written only by a trusted activator) | **Owns** for Control Plane scope (host-side profile rebuild) | none |
| Evaluators and guardrails | none | **Owns** (`safe_executor.py`, frozen, R14) | **Owns** (`bounded.py`, `runtime_authority.py`) | none |
| Authorization authority, grants, approvals, single-effect gate | never | consumes | **Owns** | none |
| Claim-carried policy binding: definition and issuance | **Defines** the identity object (`EffectivePolicyIdentity`) | none | **Owns** the successor claim class and its commitment (`EXT-S4-4`, mandatory) | none |
| Effect-time validation under the lock | provides identity and verdict only | **Owns** the in-transaction validation (`EXT-S4-2`) | provides claim machinery only | independent oracle |
| Synthetic emulator integration host (R12) | **Owns** (`registry_integration/`) | none | none | consumes it as a system under test; does not author it |
| Independent oracle and verdicts | none | none | none | **Owns** (designated lead; the Architect may not self-certify Tier 1) |

## Adapter matrix (one typed adapter per enforcement owner)

| Family | Adapter owner | Input (already authenticated and decided) | Output | Narrowing rule | Code that stays | Refusal behaviour |
|---|---|---|---|---|---|---|
| F1a + F1b (five sets) | Runtime, new file `engine/local_policy_narrowing.py` (name indicative) | `PolicyDecision.effective` (dict of sorted tuples) from `verify_and_decide` | `dataclasses.replace(caller_policy, **sets)` so `__post_init__` re-runs | Intersection; Runtime re-verifies each set is a subset of the caller's; exactly the five keys; `type(caller) is LocalExecutionPolicy` | `check` order and reason texts, `__post_init__`, target fields, `max_amount`, `max_effects`, trusted-context binding | Optional: caller policy unchanged, marker `applied=false`. Required: no dispatch, never the caller's wider policy. Empty effective set: the adapter denies by contract (below) |
| F4 ages | Control Plane, host factory over a pure `age_bounds` helper (`host_age_policy`) | Typed F4 payload (two integers) from the registry decision | kwargs for `BoundedAuthorizationWorkflow` | `min(caller, registry)`, strict `int`, per-field code-owned bounds | `_fresh`, tolerance, approval-binding block, gate | Registry value not narrowing: use caller value, record `registry_value_not_narrowing`. Required but invalid: HOLD, never a looser value |
| F5 age | Control Plane, same module (`build_effective_profile`) | Typed F5 payload (per action class) | new `RuntimeAuthorityProfile` via `model_copy`/`model_validate` | Same, per class; unknown class refused | `ActionClass` model; profile dump and existing commitments byte-identical when no registry input | Same |

Constraints on every adapter: pure function, no I/O, no import of registry code into the Runtime or Control Plane, no change to any frozen evaluator file, and the Runtime keeps the last non-widening gate. There is **no `max_amount` adapter, slot or task in V1** (R7).

### Empty-set semantics (binding)

`LocalExecutionPolicy.__post_init__` rejects non-frozensets and empty-string members, **not empty sets**; an empty frozenset is accepted and denies every operation on that dimension at `check`. The registry composition contract (`registry_successor/compose.py:3-6`) tells consumers not to build a policy from empty sets; that convention is an **adapter contract, not constructor validation**. The Runtime adapter therefore: detects any empty effective dimension itself (it never trusts `deny_all_fields`), records the registry deny-all cause **first** (`policy_denial` / `registry_deny_all`) so the cause is not hidden behind the generic `local_policy_rejected`, and still returns a policy carrying the empty frozenset so a host that ignores the outcome is denied by `check`. It never substitutes the caller policy and never relies on construction failing.

## Claim-carried policy binding (R11; authoritative; `EXT-S4-4` mandatory)

The B-lite keyword-argument approach is **rejected as the authoritative mechanism**. An executor-supplied string alone is never authority. The binding is carried in the **claim** and independently validated under the destination lock against Runtime-held trusted state. Rationale from source: the Runtime loads the claim from its own stored, commitment-verified `claim_json` row (`local_authority_effect.py:808-824`), never from the caller, which can only name a `claim_id`; so a claim-carried value cannot be swapped or omitted by an executor, whereas a keyword argument could be. Also: the operation cannot change between the pre-claim check (`atomic_local_control_plane_executor.py:69`) and the commit (action, adapter, unit and `operation_commitment` must equal the claim, `:690-698`); only *which policy was in force* can drift, and that drift is what the binding closes.

### What the claim carries

A new claim member `policy_binding`, in a **successor claim class with its own profile URN** (name fixed in `EXT-S4-0`). A new optional field on the base claim would add `"field": null` to every baseline commitment preimage (`verify_local_execution_claim` hashes `model_dump(exclude_none=False)`, `:538`) and break byte identity, so the successor has its own class; an old Runtime refuses a successor claim (`_claim_model` requires `model.profile == PROFILE`, `:242`), a fail-closed property made explicit.

| Group | Members |
|---|---|
| format | `binding_version`, `contract_version` (`r08-v2`), `family` |
| selection | `selection_id`, `selection_epoch` (named apart from the record-succession `epoch`, DT-03), `statement_digest` |
| record | `record_id`, `record_version`, `record_digest`, `payload_digest` |
| evaluator pin | `evaluator_id`, `binding`, `source_blob_id` (`2fc880da`), `source_sha256` |
| scope key | `consumer_id`, `tenant`, `institution`, `authority_domain`, `operation` |
| participation | `required` or `optional` |
| validity | `valid_from`, `valid_until` |
| trust snapshot | `snapshot_id`, `version` (and fingerprint where `EXT-S1-5` supplies one) |
| policy digests | `caller_policy_digest`, `effective_policy_digest` over the five sets |
| commitments | `policy_binding_commitment`, also a claim-level member covered by `claim_commitment` |

It sits at the top level of the claim, **not** in `policy_state` (grant policy rows) and **not** in `authority_state`. The Control Plane issues it inside the trusted handoff with the grant and approval snapshot (one coherent instant): it validates shape and the binding commitment, requires `valid_until > now`, and clamps the claim interval itself (`not_before = max(.., valid_from)`, `expires_at = min(.., valid_until)`). The Control Plane imports no registry code and verifies no signature; claim carriage is only the route to the commit. Authenticity of the selection stays with the registry verifier and the Runtime-held row. Stated limit: `claim_commitment` is an unkeyed hash, so claim authenticity rests on the trusted provisioning path exactly as for every existing claim member; the independent anchor is the Runtime row, which a claim can never create.

### Validation under the lock (Runtime; no registry call inside the transaction)

Runs inside `execute_claim_atomic` after `_validate_claim_state`, before any insert, on the same connection and with the same lock-time `now`. SQLite reads only. Failures raise a `PermissionError` subclass with a closed code; the existing `authority_hold` / `current_authority_rejected` / `denied` mapping is unchanged and the closed code goes into structured detail (the carrier is an Architect item, Q3).

| R11 item | Check | Closed code (proposal) |
|---|---|---|
| authorized claim identity | stored `claim_json` re-verified; recomputed commitment equals the stored column; claim `state='issued'`; successor profile accepted | `policy_binding_claim_invalid` |
| scope | binding scope equals the destination's configured scope and the claim's tenant, institution, domain | `policy_scope_mismatch` |
| selected record and selection identity | active row exists for scope; `(selection_id, epoch, statement_digest)` equal; participation equal; `(record_id, version, digest, payload_digest)` and evaluator pin equal | `policy_activation_unavailable`, `policy_selection_mismatch`, `policy_participation_mismatch`, `policy_record_mismatch`, `policy_evaluator_mismatch` |
| effective policy identity | claim `effective_policy_digest` and `caller_policy_digest` equal the row; the executor-derived digest of its own policy equals both (an executor string is necessary, never sufficient) | `policy_effective_digest_mismatch`, `policy_enforced_digest_missing` |
| applicable activation epoch | claim epoch equals the row epoch and the scope's retained high-water for the selection | `policy_epoch_stale` |
| policy expiry | `row.valid_from <= now < row.valid_until` on the lock-time clock; binding validity equals the row | `policy_not_yet_valid`, `policy_expired` |
| withdrawal and revocation | row `status='active'`; `(selection_id, epoch)` not in the terminal revocation table | `policy_selection_withdrawn`, `policy_selection_revoked` |
| trust snapshot | binding snapshot id equals the row's, version at least the accepted floor | `policy_trust_snapshot_stale` |
| required policy | a claim without a binding where a `required` requirement exists for the scope | `policy_binding_required` |
| applicable grant and approval validity | **unchanged**: the existing `_validate_claim_state` (`:710-758`) runs first in the same transaction; no second grant lookup, and a selection is never read from grant rows | existing |
| capability | executor mode on but destination lacks the capability | `policy_binding_capability_unavailable` |

The executor passes the digest of its own policy (default off, as `operation_identity` today) only as one more value that must equal the claim's and the row's. A successor claim executed without it is refused; a baseline claim executed with it is refused. `provision_claim` seeds missing grant, approval, policy and evidence rows from the claim (`:262-442`); **selection state must never follow that pattern**: provisioning only compares against the existing row under its own `BEGIN IMMEDIATE` and writes nothing into any policy table.

### State, writer, restore (R13)

New tables created `IF NOT EXISTS` by a destination subclass (the pattern of `operation_identity_atomic_destination.py:26-33`; the DB profile marker is unchanged): `authority_policy_activation_v1` (one row per scope key), `authority_policy_high_water_v1` (maximum epoch ever seen per selection and scope, plus a `scope_required` ratchet; never decreases), `authority_policy_revocations_v1` (terminal `(selection_id, epoch)`), `authority_policy_log_v1` (append-only, hash-chained). Written only by a trusted activator through Runtime-side writers with an already verified identity; the Runtime verifies no signature and imports no registry code, and the writer API is the trust boundary. Rules: strictly greater epoch accepted; equal epoch with equal statement digest idempotent; equal epoch with a different digest, a lower epoch, a revoked epoch, or a different selection for an occupied scope refused. A required selection sets `scope_required`; clearing it is an explicit logged call (an operator item, built inactive).

Restore and rollback: a policy rollback is a new higher epoch naming the older record, never a lower epoch. A whole-database restore reverts high-water, revocations and the log together and the in-database state cannot detect it (the same class as the known Runtime limit); mitigations, none a cure: the effective floor is `max(DB high-water, operator floor held outside the DB)`, the exported log-chain head and a per-scope high-water digest are compared at start-up, and the gate refuses required scopes until its first successful post-start sync. Durability is a test, not an assumption: the connection sets WAL only and `PRAGMA synchronous` is unset. Custody, restore and rollback are exercised by `EXT-S4-2` tests and gate QG-16 (R13).

### Compatibility, order, re-pin

- **No binding means byte-identical baseline.** The Control Plane path with no binding keeps today's code path and preimage; Runtime hooks default to inert no-ops; the base destination has no tables or capability.
- **Negotiation is explicit and two-sided.** A successor claim is accepted only by a destination declaring the capability; a baseline destination refuses it. A policy-bound destination accepts baseline claims only when no `scope_required` exists for the claim's tenant, institution and domain.
- **Serial order (mandatory):** `EXT-S4-0` ADR freezes the binding schema, digest profile and closed codes; **`EXT-S4-4` (Control Plane) lands first** (inert by default, baseline byte-identical); **`EXT-S4-2` (Runtime) lands second at the new Control Plane pin**, because the Runtime imports Control Plane claim classes at call time (`:226`, `:791`) and cannot run a successor claim until a Control Plane carrying it is on the path; the registry identity object (absorbed into `EXT-S1-5`, retiring `EXT-S4-1`) follows the ADR; `EXT-S4-3` (gate) lands last. If the Runtime merged without the Control Plane, its successor tests would skip silently (the atomic tests skip when `agent_control_plane` is absent); so the Runtime PR must fail its own check when the Control Plane pin is absent.
- **Re-pin.** `safe_executor.py` is untouched, so selections and records that pin only the evaluator blob stay valid; Runtime and Control Plane heads change, so every artifact bound to `c5e97e87`/`7a4bcd40` as an integration tuple is re-issued at the new tuple.
- **Digest profile.** The registry canonical digest uses `ensure_ascii=True` while the Control Plane `commitment` uses `ensure_ascii=False`; they differ for non-ASCII tokens, which `valid_token` permits. The ADR names one digest profile with a non-ASCII test vector.

What this does and does not prove: the claim-authorized policy identity equals the Runtime-held current identity at the lock. It does not prove that `effective = caller INTERSECT record` was computed honestly (a compromised gate that activates wrong sets is outside it), it does not cover Route A, and it assumes a trusted host clock and no same-host tampering. Optional hardening H-1 (the Runtime re-checks that its policy sets are a subset of the row's sets) is not in V1 unless the Architect decides.

## The three age-field contracts (R1 to R6)

All three fields are `int` seconds with monotone consumers, so `min(caller, registry)` after strict validation is safe (R1). There is no cross-bound between the status and approval ages and none with identity or mandate ages (R2). `ObservationPolicy.max_age_seconds` governs a different observed object; nothing is checked against it (R4).

**Strict validation (R3), common to all three.** A value `v` is accepted only if `type(v) is int` and `AGE_MIN <= v <= AGE_MAX`.

- `AGE_MIN = 1`, derived and **not a universal 5 s floor**: 0 is degenerate (the check accepts only an age at or before the evaluation instant, a de facto deny-all dependent on clock coincidence), and `ObservationPolicy.max_age_seconds` already uses `gt=0`. The workflow clock tolerance acts only on the future side (`_fresh`, `bounded.py:2022`) and never relaxes the age ceiling, so no tolerance-relative floor is derivable. A host that measures its own check latency may pass a higher host floor (proposal; default 1; it can never lower the bound).
- `AGE_MAX` is a code-owned ceiling proposed at `2_678_400` (31 days). The hard structural limit is far higher (a `timedelta` addition overflows above about 2.5e11 s) but a bound that large silently disables staleness; the value must exceed every value in repo defaults and tests and must be confirmed by a Control Plane owner survey of in-use configurations before it is fixed.
- Rejected without coercion or clamping: `bool`, `float` (including `60.0`, `nan`, `inf`), `None`, `str`, `Decimal`, `int` subclasses, other numeric types, `0` and negatives, and values above `AGE_MAX` (including `10**30`, `2**53`). The registry loader rejects floats at load, so the loader and the helper agree.
- The clock context is validated separately and **before** any workflow is constructed: `clock_tolerance_seconds` must be a strict `int >= 0`; no cap is invented. Clock interactions analysed separately (each in the `EXT-S3-1` characterization): tolerance (future side only), `ObservationPolicy` (not coupled), bound 0, inclusive comparison (`<=`; bound B accepts age == B), the dispatch deadline and the up-to-2x window, cached-purpose bound, the unrelated `RA:341` purpose read (no tolerance), `anchor_deadline_to_inputs`, and `timedelta`/`datetime` overflow (pre-existing, fixed only in the optional hardening card).

**Composition order (host side, before construction).** (1) Validate the caller value; failure refuses and never falls back. (2) Validate the clock context. (3) No registry participation: effective = caller, byte-identical run records. (4) Validate the registry value; invalid and optional: effective = caller, recorded `registry_value_invalid`; invalid and required: HOLD, caller value not used. (5) `effective = min(caller, registry)`, recording `narrowed`, `registry_value_equal` or `registry_value_not_narrowing`. Outcome strings are host outcomes, not Control Plane reason codes; the existing stale-refusal codes are unchanged.

| Field | Lands in | Bounds | Notes |
|---|---|---|---|
| F4 `status_max_age_seconds` | workflow kwarg (`bounded.py:1271`) | strict int, `[1, AGE_MAX]` | Governs conflict and policy status always, grant status only with no profile. Not extendable |
| F4 `approval_max_age_seconds` | workflow kwarg (`:1274`) | strict int, `[1, AGE_MAX]` | One consumer (`:2505`); not hashed into any commitment. Not extendable |
| F5 `ActionClass.max_status_age_seconds` | per-class value inside the host `RuntimeAuthorityProfile` | strict int, `[1, AGE_MAX]`; the pydantic `ge=0` stays untouched for existing profiles | Hashed into `approval_commitment`. Extendable per class unless capped (R6) |

A new workflow kwarg would not reach the Runtime per-call view (it copies the five age and tolerance attributes verbatim and forwards the profile snapshot, `control_plane_adapter.py:340-345`), so narrowing lives in those attributes or in the profile object.

**R5, approvals bind to the effective profile.** `approval_commitment` hashes the profile dump, so an approval is valid only if its commitment equals `approval_commitment(effective_profile, context)`; any other approval (issued against the caller profile, an earlier registry value, or a profile with the R6 flag in a different state) fails closed with `runtime_authority_approval_mismatch`, with no change to `runtime_authority.py`'s commitment or check. F4 ages are in no commitment, so F4 narrowing never invalidates approvals. Ordering: registry decision, effective profile built once, approver computes the commitment from that object, workflow built from the same object. A read-only host pre-flight lists the incompatible approvals before dispatch.

**R6, a signed outage extension cannot widen a registry-narrowed ceiling: a Control Plane source change is required.** Today a validly signed row `from=N, to=N+k` (valid when `k` is within the profile's extension limit) lifts a narrowed base `N` above `N` and, if the limit exceeds `C-N`, above the caller's own ceiling `C`. The required semantics is `effective = min(extended, registry_ceiling)`, which for a narrowed class means the class is non-extendable. The change (`EXT-S3-5`) is opt-in and rides in the **profile**, not a kwarg: a new `ActionClass` flag (default false and omitted from dumps while unset, so default dumps and commitments stay byte-identical; when set it enters `approval_commitment`), an `extension_forbidden` input to the extension-defect logic with a new reason code (versioned vocabulary change), a branch in `_class_age_bound` mirroring the irreversible-class branch, and a persisted refusal row for a signed attempt. The host builder sets the flag only for classes whose outcome is `narrowed`. Un-narrowed classes keep today's extension behaviour byte-for-byte. This replaces the earlier plan header "no edit to `bounded.py`" for S3. The no-source alternatives (disable extensions for the whole profile; refuse narrowing while extensions are enabled) over-block and are not recommended.

## Reused contracts and mechanisms (nothing new where something exists)

| Need | Reused | Reference |
|---|---|---|
| Authenticated selection | Ten-layer verification, injected `SignatureVerifier`, domain-separated signing input, snapshot expiry, issuer/key revocation | `registry_successor/verify.py:17-20, 60, 256, 322`; ledger `AUTHENTICATED-SELECTION-STATE` (IMPLEMENTED_NOT_QUALIFIED) |
| Required versus optional, deny-all versus refusal | Decision kinds `applied`, `applied_deny_all`, `overlay_not_applied`, `required_policy_unavailable`; participation equality | `decision.py:35-55, 83`; ledger `FAILURE-REFUSAL-SEMANTICS` |
| Anti-rollback floor | `TrustSnapshot.min_epochs` (stateless) plus the new snapshot-version floor | `verify.py:303`; `EXT-S1-6` |
| Revocation and expiry evaluation | Interval `[valid_from, valid_until)`, `selection_revoked`, key revocation | `verify.py:287-302` |
| Effect-boundary seam | The Runtime `BEGIN IMMEDIATE` path and the `OperationIdentityAtomicAuthorityEffectDestination` pattern (own table, no profile change) | `local_authority_effect.py:790, 860, 919`; `operation_identity_atomic_destination.py:23-39` |
| Claim expiry clamp | Claim `expires_at` clamped to the selection's `valid_until`, now inside the Control Plane handoff | `EXT-S4-4` |
| Ownership assignment | ADR-REG-TR01 decisions 2 to 5 | ADR |
| Extractability test | P0 clauses (a) caller/constructor data, (b) code-owned bound remains, (c) narrow-only, (d) deterministic non-widening refusal | `docs/p0-contract-reconciliation/05-configuration-extraction-readiness.md` |
| Reference path | S03 allow-list contract, S04 overlay consumer, S05 differential equivalence (F1a, builder oracle, frozen) | `docs/s03-contract.md`, `registry_consumer`, `tests/test_s05_equivalence.py` |

## New work that has no existing counterpart

`r08-v2` (new files only, `r08-v1` byte-preserved) with the F1, F4 and F5 families; `EffectivePolicyIdentity` and trust-snapshot fingerprint; snapshot-version floor and builder; Ed25519 verifier adapter outside the core (hash-locked, synthetic keys only, R9); conformance kit; the Runtime narrowing adapter; the policy-bound Runtime destination with its four state tables; the Control Plane successor claim with `policy_binding`; the Control Plane `age_bounds` helper, host age policy and the R6 extension cap; the emulator integration host in the registry repository (R12); the independent oracle batteries.

## Key design decisions recorded here (approved rulings, not open)

1. **Zero edits to `engine/safe_executor.py` (R14).** The consumer re-hashes the evaluator file, records bind its blob id and S05 Z2 pins it; any edit forces a re-pin of S01, every record and S05. Any proposed evaluator change is a separate architectural and qualification issue.
2. **Claim-carried binding is authoritative (R11); B-lite is rejected.** Mandatory `EXT-S4-4`; both repositories re-pin; no untrusted registry call inside the atomic transaction; existing authorization and atomicity guarantees retained.
3. **Control Plane narrowing is host-side** and applied before construction, plus one source change for R6 (`EXT-S3-5`).
4. **Deny-all is an adapter contract** (above); the Runtime keeps the last non-widening gate.
5. **One owner per shared enforcement boundary.** `local_authority_effect.py` and `atomic_local_control_plane_executor.py` belong to `EXT-S4-2`; Control Plane `local_authority_effect.py` belongs to `EXT-S4-4`; `bounded.py` and `runtime_authority.py` are queued serially across `EXT-S3-5`, `EXT-S4-4` (if it adds a profile member) and `EXT-S3-6`; the registry `v2_*` files are queued by the card table in [06](06-pr-and-sprint-execution-plan.md).
6. **Route A is unchanged and excluded** from the registry-mediated effect-time guarantee ([08](08-exclusions-and-residual-risks.md)). No Route A file is edited and no Route A control is weakened.
