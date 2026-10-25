# ADR EXT-S1-1: canonical V1 contract for governed configuration extraction

- Status: **PROPOSED for Architect acceptance (gate G-3).** Documentation only. Authorizes no implementation PR after `EXT-S1-1`, no source edit anywhere, no activation, no qualification. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.
- Work package: `EXT-S1-1` of the merged P1 plan ([`docs/p1-extraction-plan/`](../p1-extraction-plan/README.md), registry PR #22, merge `d2c472e4a09543228bad62235e07a0dedfd7f48b`). Companion contract: [`docs/r08-v2-contract.md`](../r08-v2-contract.md) (families, dispatch, codes, identity, snapshot floor, wire shapes).
- Primary source for the rulings recorded here: the Architect's final rulings of 2026-10-25 (the directive supplied to the registry contract owner; quoted by content, not reopened). Ownership baseline: [ADR-REG-TR01](2026-10-25-adr-tr-01-activation-and-epoch-ownership.md).
- Evidence rule: every statement about Runtime and Control Plane behaviour is a **source reading** at the heads in section 4, not a tested result. No repository test was run for this ADR. Nothing here is "qualified".

## 1. How to read this ADR

Each decision has a number (`D-nn`), a rationale, a source basis and, where it applies, the owning `EXT` PR. Decisions D-01 to D-06 record the schema-readiness items A1 to A4. The P1 plan is not restated; where a decision supersedes plan wording, section 3 says so explicitly. Items that need an Architect decision this ADR cannot make are collected in section 6 and marked **proposed**.

## 2. Decisions

### A. Selection, withdrawal and activation (A1 to A4)

**D-01 Selection carries an explicit disposition (A1).**
Decision: an `r08-v2` selection statement carries `disposition` in `{select, withdraw}`. A withdrawal pins no record, names its predecessor exactly (selection id, strictly lower epoch, statement digest, `decision_ref`) and is signed under the `r08-v2` domain. Epoch ordering and authenticated supersession are preserved: a higher epoch alone never supersedes. Withdrawal never erases historical evidence: the withdrawn statement, its digest and every log entry stay.
Rationale: the P1 plan had no withdrawal vocabulary; a UI or operator "disable" must be a signed, ordered statement, never an unsigned write.
Basis: Architect ruling A1; plan doc 04 A1; `registry_successor/selection.py` (supersession shape and `selection_supersession_invalid`, which a bad withdrawal reuses).
Owner: this ADR; implemented in `EXT-S1-2` (dispatch) and `EXT-S1-5`.

**D-02 `selection_withdrawn` is added to `CODES_V2`.**
Decision: `CODES_V2` is the 46 `r08-v1` codes plus exactly `trust_snapshot_version_stale` and `selection_withdrawn` (48). `CODES` stays 46 and byte-identical. `selection_withdrawn` is reached only after all ten v1 layers pass, through a final `disposition` layer, so an invalid statement can never read as an intentional withdrawal. Optional participation returns the unchanged caller policy as `overlay_not_applied`; required returns no policy.
Rationale: absent, withdrawn, revoked, expired and superseded must each keep a distinct cause.
Basis: Architect ruling A1; `common.CODES` at the candidate (46 keys); LD-02 map `meta.code_count_note`.
Owner: declared in `EXT-S1-2`; mapped in `EXT-S1-5` (completeness test iterates all 48).

**D-03 Activation state and append-only transition evidence live in the enforcing component (A2).**
Decision: the enforcing component persists `activation_state` in `{active, withdrawn, revoked}` per scope key and an append-only, hash-chained transition log with `entry_type` in `{activate, withdraw, revoke, sync}`. State and history are separate stores: state is the current value, history is how it became so. No row means not activated. `activation_state` has no writer other than the four transitions, takes no input from a caller or UI, and is never stored in the registry.
Rationale: ADR-REG-TR01 decision 2 gives activation to the enforcing component; a state without history cannot be audited, and history without state cannot be read at the lock.
Basis: Architect ruling A2; ADR-REG-TR01; contract section 7.
Owner: schema frozen in `EXT-S4-0`; implemented in `EXT-S4-2`.

**D-04 Sync cannot manufacture authorization or reverse a revocation (A2 condition).**
Decision: `sync` records snapshot high-water and may append `revoke` entries. It never activates or withdraws, never clears a revoked pair, never changes a revoked state and never supplies authorization. The revoked set is grow-only; a newer snapshot that omits an earlier revocation is refused. An `activate` or `withdraw` at an epoch not strictly above the high-water, or without exact supersession of the current row, is refused (`revoke` and `sync` follow their own preconditions in contract 7.1: revoking the current epoch and redelivering the current snapshot are permitted); a revoked epoch is not resurrected by reactivation, lineage or restore. A supersession gap is closed by a fresh higher-epoch statement naming the current row, not by processing unactivated ancestors.
Rationale: a lagging or hostile sync channel must not widen authority; the revocation source today has no rollback check (`TrustSnapshot.version` is only checked `>= 1`).
Basis: Architect ruling A2; `verify.py` `_normalize_trust`; plan doc 08 risks 8 and 9.
Owner: contract in `EXT-S1-1`; floor in `EXT-S1-6`; consumer writers in `EXT-S4-2`; vectors in `EXT-S1-8`.

**D-05 ENABLED and DISABLED are presentation only (A3).**
Decision: no stored or authorizing boolean. `policy_state` is derived on read from the closed enum in contract 7.2 and is never input. ENABLED = `active`; DISABLED = `withdrawn` or `not_selected`; a required scope that is withdrawn, revoked, expired or unavailable displays `REQUIRED — UNAVAILABLE`, never silently "disabled". A toggle is a request that becomes a signed select or withdraw statement.
Rationale: a second switch would create a second authority; "disabled" on a required scope would hide a refusal behind a benign word.
Basis: Architect ruling A3; plan doc 04 acceptance criteria 1 to 9.
Owner: mapping fixed here; conformance function in `EXT-S1-8`; ADR detail in `EXT-S4-0`.

**D-06 Durable `scope_required` ratchet with a defined, unauthorized relaxation (A4).**
Decision: the enforcing component persists a one-way `scope_required` per scope key. It cannot be downgraded by an optional selection, a withdrawal, a restore of an older store or a replayed older statement; each refuses `participation_mismatch` or fails the restore fence closed. The only future relaxation is the administrative transition `relax_scope_required` (separate relax grant, scope key and current ratchet digest named, strictly higher ratchet generation, operator-approved `decision_ref`, own log entry). **No relaxation is authorized in V1**: the `entry_type` vocabulary is not extended and no writer or code path is built.
Rationale: only a persisted ratchet gives continuous non-relaxation; per-call participation cannot.
Basis: Architect ruling A4; plan doc 04 A4 and risk 25; `decision.py` (v1 takes participation anew on every call).
Owner: schema in `EXT-S4-0`; implementation and downgrade negatives in `EXT-S4-2`.

### B. Participation, activation ownership, structure

**D-07 Required and optional participation.**
Decision: `participation` in the signed statement stays the only required/optional source; rule status (required/advisory) is a different thing. Required: missing or invalid policy never falls back to a wider caller policy, never returns success, and refuses or holds (D-21). Optional: any refusal leaves the caller policy, reported as "not applied", never as compliance or protection. A statement whose participation differs from the operation class refuses `participation_mismatch`.
Basis: `decision.py` (`_refusal`, kinds); ADR-REG-TR01 reading rules; plan doc 02 CAP-7.
Owner: `EXT-S1-5` (map), `EXT-S4-2` (ratchet).

**D-08 Activation is consumer-owned; anti-rollback is the consumer's floor (ADR-REG-TR01).**
Decision: the selection issuer assigns the selection epoch; the enforcing component owns activation and its high-water state; the Control Plane keeps activation for Control Plane-enforced policy; Runtime-enforced policy is activated by the designated host/Runtime integration gate subject to existing Control Plane authority. Publication is not activation; a selection is never a grant. The stateless `TrustSnapshot.min_epochs` stays a floor input, not the state.
Basis: ADR-REG-TR01 decisions 1 to 10; `verify.py` epoch layer.
Owner: `EXT-S1-8` (pure transition vectors), `EXT-S4-0`, `EXT-S4-2`.

**D-09 `r08-v2` is strictly additive (O-2).**
Decision: a behaviour-preserving refactor with a small family dispatch table; prefer the existing public interfaces; v2-specific modules only where reuse would alter frozen v1 behaviour; no duplicate registry implementation. `r08-v1` behaviour, codes, signing input, serialized outputs, goldens and tests stay unchanged (source-byte identity is reserved for the frozen legacy directories `registry_contract/`, `registry_consumer/` and `baseline/`; shared `registry_successor/` files may be refactored only under the golden-replay proof); v1 and v2 documents and signatures do not cross-verify. The P1 alternative of v2 in new files only for every module is not taken (it would duplicate the loader, digest, layers and decision function); the P1 alternative of an unrestricted core refactor is bounded by the golden-replay proof.
Rationale: duplication creates two parsers that can disagree; unrestricted edits risk v1.
Basis: Architect ruling O-2; plan doc 11 reconciliation row 5; frozen sets FS-R.
Owner: `EXT-S1-2` (goldens captured from the unrefactored head in its first commit).

**D-10 Family dispatch and the V1 families.**
Decision: one table `family -> (payload validator, composer, evaluator binding, caller normalizer, enforcing component)`; unknown or case/whitespace-varied family refuses. V1 registers `f1ab-local-execution-allowlist` (five sets), `f4-control-plane-age-bounds` and `f5-action-class-age-bounds` beside the unchanged `f1a-...`. Payload and composition rules are in contract section 2. No `max_amount` key, slot or placeholder; no cross-bound among ages; no five-second floor.
Basis: plan docs 03 and 04; `common.py` family constants; `compose.py`.
Owner: `EXT-S1-2`, `EXT-S1-3`, `EXT-S1-4`.

**D-11 Eight-field Option B profile; nothing more.**
Decision: Runtime `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`; Control Plane `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`. `max_amount` stays deferred (not a V1 task, slot or release blocker). No field beyond these eight. Composition only narrows.
Basis: operator Option B ([09](../p1-extraction-plan/09-operator-scope-decision.md)); Architect ruling.
Owner: all S1 to S3 PRs.

**D-12 Atomic Route B only.**
Decision: V1 covers the atomic Runtime route. Route A is not rechecked at the commit boundary and every status report says so.
Basis: operator decision 2; GAP-G3-03.
Owner: disclosure in `EXT-S6-4`.

**D-13 Claim-carried policy identity; B-lite is rejected.**
Decision: the effective-policy identity is carried inside the Control Plane authorization claim as a declared optional claim field (omitted when absent) under an additive successor claim profile; the claim commitment covers it; the Runtime destination compares it with the trusted state row under the lock and the lock-time clock. Keyword-argument carriage is rejected. A claim with no binding stays byte-identical and is valid only where no registry policy governs the operation.
Basis: Architect ruling (items 9 to 11); `local_authority_effect.py` claim model (`LocalExecutionClaim`, `claim_commitment`); D-28.
Owner: `EXT-S4-4` (claim path, sole owner), `EXT-S4-5` (re-pin), `EXT-S4-2` (guard).

**D-14 One canonical policy-binding contract (O-3).**
Decision: one typed object owned by `EXT-S1-5`; `EXT-S4-0` consumes it and specializes only effect-boundary requirements; no competing member list. Members (contract section 4): `binding_profile`; `record_id`, `record_version`, `record_digest` (governing record and version); `selection_id`, `selection_epoch`, `selection_digest` (selected policy and epoch); `family`, `consumer_id`, `scope`, `operation` (enforcing scope); `effective_policy_digest` (effective configuration); `activation_ref` (applicable activation identity); `trust_snapshot_version`, `trust_snapshot_fingerprint` (relevant trust snapshot). From existing registry fields: the record pin, selection id, epoch, statement digest, family, consumer, scope, operation and snapshot version. New: `effective_policy_digest`, `trust_snapshot_fingerprint`, `activation_ref` (the last is produced by the enforcing gate, not the registry) and the profile constant. Not members: `snapshot_id`, evaluator hash, participation, caller policy digest, validity window, any state value, because each is already covered by a member or belongs to consumer state.
Rationale: the P1 plan listed "selection, epoch, record digest, evaluator build, trust snapshot, caller and effective policy digests" across three documents; those overlap, and a claim member that duplicates another can disagree with it.
Basis: `selection.py` statement fields; `verify.py` `TrustSnapshot`; `local_authority_effect.py` existing claim members (`institution_id`, `authority_domain`, `tenant_id` already ride in the claim; `consumer_id` and `operation` do not).
Owner: `EXT-S1-5`; checked by `EXT-S4-0` ("diverges: stop").

**D-15 Serialization profile for the binding.**
Decision: `binding_digest` over `canonical_bytes` (registry profile, `ensure_ascii=True`) with domain prefix `ocs-reg/r08-v2/policy-binding\n`. The Control Plane `commitment` serializer uses `ensure_ascii=False`, so the two differ for non-ASCII strings; the binding therefore admits ASCII strings only (`r08-v2` refuses a non-ASCII scope token with `field_invalid`). The two serializers are proved equal on shared vectors, and no Runtime or Control Plane code imports registry code.
Rationale: a digest that two components compute differently is an authority hole at the lock.
Basis: source reading `common.canonical_bytes` (registry) against `bounded._canonical_bytes` and `decision_input_profile.canonical_bytes` (Control Plane `7a4bcd40`). This restriction is **proposed to the Architect** (section 6).
Owner: `EXT-S1-5` (vectors incl. a non-ASCII refusal), `EXT-S4-4`.

**D-16 No automatic approval revival.**
Decision: withdrawing a narrowed configuration must not reactivate an older approval that is no longer valid under the current effective policy generation. A fresh approval, or explicitly authorized new issuance, under the new effective profile is required. Approval generation and policy identity are preserved enough to block stale reuse. Required negative case: narrowed profile P1 invalidates the older approval; the narrowing is withdrawn; the old approval **remains invalid**. Positive control: an approval bound to the narrowed profile passes while P1 is in force. No generalized approval-history migration in V1.
Rationale: `approval_commitment` hashes the profile dump, so withdrawal returns the profile to P0 and an old P0 approval would match its commitment again unless invalidation is durable.
Basis: Architect ruling; `runtime_authority.py` `approval_commitment` (`:186`) and the `runtime_authority_approval_mismatch` check (`:268-271`) at Control Plane `7a4bcd40`: no generation or policy-identity member exists and the commitment is a pure function of content, so revival is automatic today (inferred, not run). Candidate mechanisms for the `EXT-S3-4` owner to evaluate in its design note (this ADR does not choose): (a) terminal revocation of the incompatible approvals when a narrowing activates, using the Runtime destination's existing terminal approval status (`set_approval_status`, `engine/local_authority_effect.py:523`, a source reading; it needs no Control Plane edit); (b) an additive approver-signed generation or policy-identity key in the `runtime_authority_context` allow-list (`runtime_authority.py:262-267`), which is hashed into the commitment and absent-key-compatible but **is a Control Plane source edit that nothing here authorizes**. Narrowing the F4 scalars alone does not change the commitment and invalidates no approval.
Owner: `EXT-S3-4` (design note and negative case), QG-04 (supersession in section 3).

**D-17 Optional-scope fallback semantics.**
Decision: optional participation may fall back to the caller policy when no valid optional selection applies; this is not a monotonic-tightening guarantee and V1 adds no universal tightening guarantee for optional policies. Required participation never silently downgrades and stays fail-closed. Fallback is visible in evidence (`applied=false`, the original `registry_code`, `fallback=caller_policy`). An invalid selection is reported under its own code and must not be relabelled `selection_withdrawn` (D-02). Previously committed effects stay governed by their original effective-policy evidence. A current claim must not reuse a stale policy identity: a claim minted under identity X is refused at the guard if the state row no longer matches X (it is never downgraded to a fallback there), and a fallback claim carries no binding. The guard tells an optional fallback from a binding omitted on a required scope by the persisted `scope_required` ratchet (contract 7.4); a scope that must be fail-closed at commit must have the ratchet set. For continuous non-relaxation use `scope_required` (D-06).
Basis: Architect ruling; `decision.py` optional path; plan doc 04 acceptance criterion 8.
Owner: `EXT-S1-5` (evidence fields), `EXT-S4-2`.

### C. LD-02 typed reasons

**D-18 Structured registry code carriage (OPEN-Q5).**
Decision: the original registry failure code is kept as structured negative evidence (`ocs-registry-failure-detail/1`) and mapped to existing component refusal categories without collapsing causes. Distinct codes keep distinct cause fields. No policy authority lives in a message string.
Basis: Architect ruling; LD-02 map `meta.detail_schema_fields`.
Owner: `EXT-S1-5` (registry half), `EXT-S4-0` (component half).

**D-19 No string-based security decisions (OPEN-Q3).**
Decision: no code parses `PermissionError` text to infer authorization or policy state. Cross-component reasons use typed reason codes or a typed boundary adapter; historical text is retained for diagnostics only. Source reading that motivates this: the Runtime atomic executor maps **every** `PermissionError` from `execute_claim_atomic` to `authority_hold` / `current_authority_rejected` and carries only `str(exc)` (`atomic_local_control_plane_executor.py`, `except PermissionError`), and `destination_error_text` returns that text; the P1 map's phrase "mapped only if the PermissionError text carries structured detail" is therefore **not** adopted as a mechanism.
Owner: `EXT-S4-0` (typed boundary design), `EXT-S4-2`.

**D-20 Preconstruction deny-all is a different path from `check` denial (OPEN-Q6).**
Decision: the gate denies before building a policy when an effective set is empty (`registry_deny_all`); `LocalExecutionPolicy.__post_init__` accepts empty frozensets and `check` would deny with its own text (source reading, `safe_executor.py` at Runtime `c5e97e87`). Evidence preserves the distinction. QG-01 exact reason and check-order equivalence applies only to representable non-empty effective policies. Both negative paths are tested independently: the deny-all path (denial, zero effects, claim unconsumed, budget unchanged) and the `check` path.
Owner: `EXT-S2-1`, `EXT-S2-2`, QG-01.

**D-21 Stale or rolled-back epoch is REFUSE (OPEN-Q12).**
Decision: for effects a stale or rolled-back epoch is a REFUSE with a specific stale-epoch cause (`selection_epoch_stale` carried structurally). HOLD is only for authority state that is genuinely unavailable or indeterminate with effect execution prohibited. Neither is ever a retryable success. This changes the merged map row `selection_epoch_stale` from HOLD to REFUSE (section 3, related disposition change). `selection_withdrawn` stays as the map proposes (HOLD) pending section 6.
Basis: Architect ruling; map `selection_epoch_stale.open_question`.
Owner: `EXT-S1-5`, `EXT-S4-2`.

### D. Ownership, pins, restore, qualification

**D-22 Registry, Runtime and Control Plane ownership.**
Decision: the **registry** owns the typed record and manifest shape, strict loader, family dispatch, ten-layer verification, the identity object definition and the snapshot floor input; it never activates, never issues a grant and never authorizes execution. The **Runtime** owns the evaluator (`safe_executor.py`, frozen), the narrowing adapter, and for Runtime scope the state, ratchet, revoked set, log and in-transaction guard. The **Control Plane** owns grants, approvals, the single-effect gate, the claim path, freshness evaluation and its safety bounds, and activation state for Control Plane scope. Qualification owns independent oracles and verdicts only.
Basis: ADR-REG-TR01; plan doc 04 ownership matrix.
Owner: all.

**D-23 Source-pin and candidate selection rules (R10-F-03).**
Decision: (1) the candidate is the tuple of exact full SHAs in section 4; (2) a PR records the exact head of every repository it reads at its start and re-reads the affected lines; (3) a head that differs from the candidate is never absorbed silently: the author documents both the historical pin and the proposed new candidate, stops on any changed pinned fact and asks the Architect; (4) the candidate changes only through a documented amendment or `EXT-S4-5`, which lists old and new; (5) evidence at an old tuple is superseded, never reused; (6) `engine/safe_executor.py` blob `2fc880dae37eac76e5074533435740ce0684209d` is verified in every Runtime-touching PR; (7) a test-only PR may be prepared against the candidate and merges after G-3.
Owner: `EXT-S1-1`, `EXT-S4-5`.

**D-24 Restore, rollback and custody requirements.**
Decision: eight requirements in contract section 8: one trusted writer, never seeded from a claim; state and log commit in one transaction; external floor and log-head anchor; a restored or older store is `unknown` and required scopes refuse until a logged re-baseline; lost state is unknown, not zero; revoked set and high-water roll back together (disclosed limit, never claimed as restore safety); unacknowledged publication reads `UNKNOWN`; no network I/O inside a destination transaction. Key, trust-root and snapshot-channel custody stays operator-gated.
Basis: plan doc 08 risks 6 and 7; ADR-REG-TR01 DT-02, DT-04.
Owner: `EXT-S1-8` vectors, `EXT-S4-0` ADR, `EXT-S4-2`, QG-05/08/09/13.

**D-25 Snapshot-version floor, fingerprint, builder and snapshot-borne revocation.**
Decision: contract section 5. `TrustSnapshot` is unchanged; floor and `last_accepted_snapshot` inputs default off; equal version is idempotent redelivery only (compared with the consumer-supplied last accepted fingerprint; bootstrap is floor-only); fingerprint defined over the normalized snapshot; revocation rides the snapshot; the builder requires an explicit maximum lifetime and this ADR adopts none (operator cadence B-08).
Basis: `verify.py` (`TrustSnapshot`, `_normalize_trust`); plan doc 08 risks 8 and 9.
Owner: `EXT-S1-6`.

**D-26 Independent qualification boundary.**
Decision: GAP-G4-13 stays **open**. The independent qualification owner appoints an independent Tier 1 lead (never the builder, the Architect, Copilot or a dependent worker). S5 is **PREPARE-only**; no independent verdict exists or is written; criteria are not weakened. Copilot review is technical review, not qualification. Nothing produced by `EXT-S1-1` is called qualified, independently reviewed evidence or a verdict, and the `r08-v1` and v2 builder tests stay "developer-tested, not independently qualified".
Basis: Architect ruling; plan doc 07.
Owner: `EXT-S5-*`, `EXT-S6-4` wording.

### E. Control Plane bounds, function names, outage extension

**D-27 Control Plane owns safety bounds (O-4).**
Decision: the Control Plane contract owns the safety bounds for the three ages; the registry F4/F5 validator carries no private constant and reads a table copied from that contract with a citation and a test that fails if the two differ. **`AGE_MIN = 1` is adopted for the registry input** (the Control Plane models admit 0, which only accepts an observation at exactly `now`; the floor validates the registry value and never clamps the effective output, so a caller value of 0 still yields 0). **`AGE_MAX = 2678400` is a proposal and is not adopted.** The evidence does not support any value as "the smallest compatible safe bound": the largest value in any Control Plane or Runtime fixture is 3600 s; every observed value is synthetic; neither repository has an upper bound or operational host data. Until the Control Plane owner records an adopted maximum with its evidence, `EXT-S1-4` and `EXT-S3-2` do not merge (no placeholder bound merges). Hard technical ceiling to carry into that contract: with the freshness profile on, a base near 2.5e11 s overflows date arithmetic and raises an unhandled `OverflowError` outside the journal's exception tuple; with it off there is no technical ceiling. The registry input is therefore refused far below that. A "caller value" is valid only as a strict integer within the same technical range; an invalid caller refuses and is never replaced.
Rationale: a bound set by the registry would be a second owner of Control Plane safety semantics; an arbitrary universal constant is what the Architect ruled out.
Basis: Architect ruling O-4; source readings at Control Plane `7a4bcd40` (section 5 and its probe results): `runtime_authority.py:87` (`ActionClass.max_status_age_seconds`, `ge=0`, no upper bound), `bounded.py:1271-1275, 1295-1299` (unvalidated kwargs), `freshness.py:68` (`max_age_extension_seconds`, no upper bound), `bounded.py:2081-2089` (`opened + timedelta(seconds=bound)`).
Owner: Control Plane contract (recorded by the Control Plane owner before `EXT-S1-4` and `EXT-S3-2`); referenced from the registry family validator in `EXT-S1-4`. Proposed to the Architect (section 6, item 2).

**D-28 Claim function names source-verified at the selected head (O-5).**
Decision: names and signatures are source-verified at Control Plane `7a4bcd40` and Runtime `c5e97e87` (section 4 candidate). The merged plan's shorthand "`provision_claim`/`verify_local_execution_claim`" mixes two repositories and is **corrected** here (it corrects doc 11 reconciliation row 10 and the `EXT-S4-4` card wording):

| Role | Name and signature | Location |
|---|---|---|
| Control Plane claim issue and provision | `provision_local_execution_claim(workflow, proposal, decision, *, provision, now, claim_id=None, budget_id=None, expires_at=None, decision_input_commitment=None, decision_input_profile_version=None) -> LocalExecutionClaim` | `src/agent_control_plane/local_authority_effect.py:502` |
| Control Plane claim issue, no provisioning | `materialize_local_execution_claim(...)` (same minus `provision`) | `:475` |
| Control Plane claim core | `_materialize_under_handoff(...)` | `:329` |
| Control Plane claim verification | `verify_local_execution_claim(claim) -> bool` | `:534` |
| Claim models | `LocalExecutionClaim`, `TenantLocalExecutionClaim` (pydantic, default extra-ignore) | `local_authority_effect.py` (model definitions before `_utc`) |
| Runtime executor pass-through | `AtomicLocalControlPlaneExecutor.provision_claim(self, *, proposal, decision, now, claim_id=None, budget_id=None, expires_at=None, decision_input_commitment=None, decision_input_profile_version=None)` | Runtime `engine/atomic_local_control_plane_executor.py:61` |
| Runtime destination | `provision_claim(self, claim)`; `execute_claim_atomic(self, claim_id, snapshot, *, attempt_id, simulate=None, operation_id=None)` | Runtime `engine/local_authority_effect.py:262`, `:782` |
| Approval commitment and check | `approval_commitment(profile, context) -> str`; `validate_extensions(...)` | `src/agent_control_plane/runtime_authority.py:186`, `:251` |

Structural constraint for the carrier (source reading, not run): `LocalExecutionClaim` has no `extra` configuration, so a bare extra dictionary key is dropped when the model path re-dumps the claim, the recomputed `claim_commitment` no longer matches and `verify_local_execution_claim` returns False (claims would be refused, fail closed). The binding must therefore be a declared optional model field omitted when `None` (the repository's `exclude_if` pattern), which also keeps claims without a binding byte-identical. The binding must stay out of `authority_state` and `policy_state`, which `verify_local_execution_claim` recomputes. The claim already carries `decision_input_commitment` and `decision_input_profile_version`; they are not policy identity and are not reused or duplicated in the binding.
Rationale: an implementation edit against a wrong function name or a bare-key carrier would fail at the first test and invite a workaround.
Basis: Architect ruling O-5; Worker D source reading (section 5); my own read of the same functions.
Owner: recorded here before any implementation edit; re-confirmed at the `EXT-S4-5` re-pin.

**D-29 R6: outage extension never outlives the registry-narrowed deadline.**
Decision (**the mechanism is proposed to the Architect; no edit is authorized**): the invariant is that an outage extension never makes an observation acceptable after the effective registry-narrowed freshness deadline. The source reading shows that **profile narrowing alone does not meet it**: if only `ActionClass.max_status_age_seconds` is narrowed, a validly signed extension is measured from the narrowed base and still lifts the grant-status window by up to `max_age_extension_seconds` (a probe with base 60 narrowed to 30 and the extension limit left at 300 authorized a status ten times the narrowed ceiling; the check deadline became opened plus 330 s). The extension applies to grant status, cached grant, cached purpose and the dispatch deadline only; conflict, policy, identity, mandate, approval, direct purpose reads and destination observation are not on the extension path.
- **First mechanism (the smallest, no Control Plane source edit):** the `EXT-S3-4` host factory composes the ceiling into the existing evaluation. For a validated integer ceiling `C_c` per class: `base_c = min(current_c, C_c)`, `headroom = min over classes of max(0, C_c - base_c)`, `extension limit = 0 if no freshness profile else min(current limit, headroom)`. Every internal call site passes the trusted base, so the extension is then bounded by the ceiling on every extension-aware path. Proof obligation for that PR: a property test over the unchanged public pure functions `effective_age_bound` and `extension_defects` and through `BoundedAuthorizationWorkflow`, including store rows rewritten to a higher `to` or the old base; plus the listed negative cases (extension to ceiling+1 refused with `age_extension_exceeds_limit`; extension to the ceiling allowed and a status at ceiling+1 held; rows recorded at the old base invalid with `age_extension_invalid`; cached purpose and cached grant refuse at ceiling+1; irreversible class never extended; default path byte-identical).
- **Conditional bounded repair (planning only):** a source repair is warranted only if the owner concludes factory composition is insufficient, for example because the ceiling is recorded nowhere in the profile and a later host that rebuilds a profile without composing it would pass undetected (residual R-d), or because the Architect reads the invariant at dispatch time (residual R-a below). Affected functions if so: `freshness.effective_age_bound` (`freshness.py:182`, optional keyword-only ceiling defaulting to `None`), `BoundedAuthorizationWorkflow._class_age_bound` (`bounded.py:1358`), `record_age_extension` (`bounded.py:1376`) and `BoundedRecordStore.record_age_extension` (`bounded.py:982`), and `runtime_authority.py` only if the carrier is a profile field. A default of `None` keeps output byte-identical; a profile-field carrier uses the repository's `exclude_if` omission so default-path commitments stay identical, a constructor-keyword carrier changes no commitment but leaves the ceiling unbound from approvals. It would need its own implementation PR, independent review, and exact re-pins of the Control Plane head, the `freshness.py`/`bounded.py`/`runtime_authority.py` blobs, the freshness, reversibility, runtime-authority and holder-inventory tests, and the adversarial mutation script. `engine/safe_executor.py` is never modified.
- **Residuals for the Architect's reading:** R-a, by default the deadline is not anchored to `observed_at`, so an observation at the ceiling when read can still be dispatched until `opened + bound` (a pinned pre-existing behaviour, `tests/test_freshness.py:805`); if the invariant is read at dispatch time `anchor_deadline_to_inputs=True` is also required, which adds a key to the profile dump and changes the approval commitment. R-b, the public `extension_defects(..., base_seconds=None)` trusts a row's own base (no internal caller omits it). R-c, the extension limit is one profile-wide scalar, so the safe composition is the minimum headroom across classes (it may refuse an extension a roomier class could have had). R-d as above.
- **Exception status:** the narrow zero-edit exception for Control Plane enforcement files remains conditionally authorized for planning only. The findings above do not trigger it. The owner must still identify affected functions, minimum change, preserved behaviour, negative regressions, approval-commitment impact and exact re-pins before any edit is authorized.
Rationale: composing the ceiling uses existing, tested extension logic and keeps the Control Plane source zero-edit; a source repair is a larger authority-adjacent change that needs its own review.
Basis: Architect ruling R6; Control Plane `7a4bcd40` source readings: `freshness.py:155-201`, `bounded.py:1358-1396, 2078-2090, 2105-2143, 2163, 2393-2400`, `runtime_authority.py:339-342`; Worker D probes S2, S3, S3b, S3c, S4 (read-only, unmodified source; not repository tests).
Owner: `EXT-S3-4` (factory mechanism and proof); any repair is a separate PR after Architect authorization.

**D-30 Naming map: selection epoch versus record succession counter (DT-03).**
Decision: "selection epoch" is the `epoch` of an `r08` selection statement, assigned by the selection issuer and enforced against the consumer's high-water; "record succession counter" is the `epoch` of `ocs-registry-record/0` (hub `tools/registry_records.py`), which is never used as a selection epoch. In `r08-v2` the wire field stays `epoch`; the binding member is `selection_epoch`; r08 records carry `record_version`, not an epoch. No adapter is needed because the two contracts never share a document.
Basis: ADR-REG-TR01 decision 6 and DT-03; `selection.py` `STATEMENT_FIELDS`.
Owner: `EXT-S1-5`.

## 3. EXPLICIT SUPERSESSION

The Architect's later rulings supersede the earlier wording in merged PR #22 (registry `d2c472e4a09543228bad62235e07a0dedfd7f48b`) as follows. The merged files are not edited; this ADR is the record, and the owning PR cards are read through it.

**(1) Approval revival.** Merged docs 07 (row "Outage extension and approval revival"), the QG-04 gate JSON (`docs/p1-extraction-plan/data/qualification-gate-matrix.json`, `new_tests_needed`) and the `EXT-S3-4` card (element 5 of `docs/p1-extraction-plan/11-ext-pr-execution-cards.md`) say that revival of an older P0 approval is "not guaranteed" by V1 and is "disclosed". **Superseded by**: no automatic approval revival; a fresh approval under the new profile is required; approval generation and policy identity are preserved enough to block stale reuse; the negative case (narrowed profile, approval invalidated, narrowing withdrawn, old approval remains invalid) is required (D-16).

**(2) Control Plane R6 enforcement-file exception.** Merged docs say the S3 header is "no edit to `bounded.py`" (docs 06 and 11) and that `EXT-S3-4` stops if it needs any existing Control Plane source edit (doc 11, O-1). **Superseded by**: profile narrowing alone is not sufficient without an enforcement proof. The invariant is that an outage extension never makes an observation acceptable after the effective registry-narrowed freshness deadline. First the smallest mechanism that composes the effective age ceiling into existing evaluation is attempted. Only if source characterization shows the extension logic can exceed the ceiling, a bounded enforcement repair is made in its **own** implementation PR with independent review. A narrow exception to the zero-edit rule for Control Plane enforcement files is conditionally authorized **for planning only; it is NOT an authorization to edit now**. The component owner must identify the affected functions, the minimum change, preserved behaviour, negative regressions, approval-commitment impact and the exact re-pins. `engine/safe_executor.py` is never modified (D-29).

**CODES_V2 language.** Wherever merged wording counts the `r08-v2` code set as 46, 47 or as one set, it is read as: **46 `r08-v1` codes plus `trust_snapshot_version_stale` plus `selection_withdrawn` = 48** (D-02). This includes the LD-02 map `meta.vetting.completeness_test_rule` ("CODES plus trust_snapshot_version_stale (47)").

**Related disposition change (a consequence of OPEN-Q12, not a PR #22 prose change).** The LD-02 map row `selection_epoch_stale` (HOLD, OPEN-Q12 unresolved) is read as REFUSE with a specific stale-epoch cause (D-21). Its `runtime_route_b_commit.cause_requirement` ("mapped only if the destination PermissionError text carries structured detail") is read through D-19.

## 4. Exact source candidates (R10-F-03)

Verified on 2026-10-25. Registry head was read through the GitHub API (`gh api repos/cogno-us/cognous-ocs-registry/commits/main`). The GitHub API refused the Runtime, Control Plane and qualification repositories for this session (HTTP 403, repository access not enabled), so their heads were read from the live remote with `git ls-remote origin refs/heads/main` in the local clones. Same repositories, same refs; the method differs from the one the work order named.

| Source | Historical pin (P1 plan) | Current `main` head | Proposed candidate | Moved? |
|---|---|---|---|---|
| Registry `cogno-us/cognous-ocs-registry` | `d61ef729883c9c127cbd05b8f8a1a5944dc0e717` (merge of P0 PR #21) | `d2c472e4a09543228bad62235e07a0dedfd7f48b` (merge of PR #22; PR head `b34fa6613f225f944ca839d521a4f8a972b89cec`) | `d2c472e4a09543228bad62235e07a0dedfd7f48b` | **Yes**, by PR #22 only |
| Runtime `cogno-us/cognous-execution-runtime` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | No |
| Control Plane `cogno-us/cognous-control-plane` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | No |
| Runtime evaluator blob `engine/safe_executor.py` | `2fc880dae37eac76e5074533435740ce0684209d` | `2fc880dae37eac76e5074533435740ce0684209d` (`git rev-parse origin/main:engine/safe_executor.py`) | unchanged | No |
| Inventory `cogno-us/cognous-stack-qualification` | merge `be1994a961e4e40612d999972ede6547a3729887` (PR #227; final PR head `1b34db3442c70701d6ffad67db94a49492b1827b`) | `be1994a961e4e40612d999972ede6547a3729887` | merge `be1994a961e4e40612d999972ede6547a3729887` | No |

Registry movement `d61ef729` to `d2c472e4`: `git diff --name-only d61ef729 d2c472e4` lists only files under `docs/p1-extraction-plan/` (fourteen documentation files); no code, test, lock or frozen path changed. The registry source tree the later PRs refactor (`registry_successor/`, `registry_contract/`, `registry_consumer/`, `baseline/`, `tests/`) is therefore the same as the P1 pin. This ADR's own merge moves registry `main` again by documentation only; later PRs record the head they start from (D-23). Worker A's CI workflow and Worker B's implementation docs are separate PRs and are not part of the candidate until merged.

The candidate selects the tuple against which `EXT-S1-2` onward are built. It is **proposed**: the Architect accepts it by accepting this ADR (G-3). `EXT-S4-5` replaces the Runtime and Control Plane entries after the claim change.

## 5. Control Plane characterization (Worker D findings)

Worker D produced a read-only characterization of the Control Plane at `7a4bcd40` (functions, signatures and locations; behaviour per path; probes that imported the unmodified source in scratch directories). These are **source readings, not repository test results, and not qualification**. Findings used above:

| Finding | Where used |
|---|---|
| Profile narrowing of the class base alone lets a valid outage extension exceed the narrowed ceiling; composing `FreshnessProfile.max_age_extension_seconds` in the host factory enforces it with no source edit | D-29 |
| Extensions affect only grant status, cached grant, cached purpose and the dispatch deadline; not conflict, policy, identity, mandate, approval, direct purpose or observation | D-29 |
| `approval_commitment` hashes the full profile dump; narrowing a class base or the extension limit changes it, while narrowing the F4 scalars (constructor keywords outside the profile dump) does not; no generation, epoch or registry-identity member exists; re-widening to P0 recomputes the same commitment, so an older P0 approval **revives automatically** (inferred from determinism plus the equal-profiles-equal-commitments probe). The merged wording "revival is not guaranteed" understates this | D-16, section 3 |
| No existing maximum for any age in either repository; largest observed value 3600 s in synthetic fixtures; overflow of date arithmetic near 2.5e11 s on the freshness path; pydantic lax coercion accepts `"60"`, `60.0`, `True` and 10**30 on the profile model; constructor keywords are unvalidated | D-27 |
| Claim function names, signatures and locations; the declared-field requirement for a carrier | D-28 |
| Scalars outside the eight V1 fields (`identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds`, observation and evidence-obligation ages) have no narrowing path and are not added: the eight-field profile is unchanged | D-11 |
| Plan citations for `bounded.py:1271, 1274, 2398-2400, 2445, 2469, 2505, 2082-2088, 2163` and `runtime_authority.py:87, 341` verified exact at `7a4bcd40` | evidence |

Head-advance check: Control Plane and Runtime heads did not move; Worker D, like this ADR's author, could not read those repositories through `gh api` (HTTP 403) and used `git ls-remote`.

## 6. Items proposed to the Architect (not decided here)

1. **R6 mechanism** (D-29): the factory-composition mechanism needs no Control Plane source edit and is proposed as the first mechanism. Two readings are needed from the Architect: whether the invariant is read at acceptance time (composition suffices) or at dispatch time (then `anchor_deadline_to_inputs` is also required, residual R-a), and whether residual R-d (the ceiling is recorded nowhere in the profile) is enough to trigger the conditional repair. No edit is authorized.
2. **AGE_MAX** (D-27): `AGE_MIN = 1` is evidence-supported; no evidence supports adopting any maximum, and `2678400` stays a proposal. The Control Plane owner records a bound (or the Architect rules a population-based method) before `EXT-S1-4` and `EXT-S3-2` can merge. Also confirm that the floor validates the registry input and never clamps a caller value of 0.
3. **ASCII-only binding strings** (D-15): confirms a v2-only restriction on scope tokens so registry and Control Plane serializers agree. Alternative: a registry-defined digest with a Control Plane-side re-implementation that escapes non-ASCII identically; rejected here as a second implementation of the same rule.
4. **`selection_withdrawn` disposition**: the merged map says HOLD. Because an authenticated withdrawal is a determinate state (OPEN-Q12 principle), REFUSE may be the consistent mapping. This ADR does not change the map row; the Architect confirms in `EXT-S1-5`.
5. **`activation_ref` definition** (D-14): the entry hash of the enforcing component's `activate` log entry, stable across `sync` entries. `EXT-S4-0` may refine the entry layout but not add a competing member.
6. **Approval-revival mechanism** (D-16): mechanism (b) would be a Control Plane source edit and is not authorized; the Architect may prefer (a) (no Control Plane edit) or authorize a (b)-type exception under the same conditions as R6.
7. **Review-driven clarifications to confirm** (added after the first Copilot review; they apply the existing rulings and add no new field to the eight-field profile): the guard comparison table and the state columns it needs (contract 7.4, 7); the `last_accepted_snapshot` input and bootstrap rule and the fingerprint encoding with a vector (contract 5, D-25); the supersession-gap closure by a fresh higher-epoch statement (contract 7.1, D-04); the optional-fallback guard rule keyed on the ratchet (D-17).

## 7. Review checklist (card element 5)

- No `max_amount` slot, reserved key or task; no ninth field; eight fields exactly (D-11).
- No five-second floor; no cross-bound among the distinct ages (contract 2).
- V0.2 contracts not reopened; ADR-REG-TR01 unchanged and cited.
- Registry never activates, issues a grant or authorizes an effect (D-22).
- Required scope never falls back to a wider caller policy (D-07, D-17).
- `r08-v1` behaviour and serialized outputs unchanged; `CODES` is still 46 (D-02, D-09).
- Nothing is called qualified; GAP-G4-13 open; S5 PREPARE-only (D-26).
- No edit to `engine/safe_executor.py`; no Control Plane edit authorized (D-29).
- All links in this ADR and the contract resolve (checked mechanically before the PR).

## 8. Evidence and limits

Read for this ADR: the merged P1 plan (documents 01 to 11 and both data files), ADR-REG-TR01, `docs/r08-s01-contract.md`, `registry_successor/{common,selection,verify,decision,compose}.py` at `d2c472e4`, and Runtime and Control Plane source at the section 4 heads for the named functions. The JSON in the contract parses and its digests were computed with the stated profile using the registry `common.digest`; signatures in the examples are placeholders. The Control Plane findings in section 5 are source readings by a separate worker; they are not test results. Not read: Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest (UNVERIFIED).
