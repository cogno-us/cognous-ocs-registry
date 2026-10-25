# ADR EXT-S1-1: canonical V1 contract for governed configuration extraction

- Status: **PROPOSED for Architect acceptance (gate G-3).** Documentation only. Authorizes no implementation PR after `EXT-S1-1`, no source edit anywhere, no activation, no qualification. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.
- Work package: `EXT-S1-1` of the merged P1 plan ([`docs/p1-extraction-plan/`](../p1-extraction-plan/README.md), registry PR #22, merge `d2c472e4a09543228bad62235e07a0dedfd7f48b`). Companion contract: [`docs/r08-v2-contract.md`](../r08-v2-contract.md) (families, dispatch, codes, identity, snapshot floor, wire shapes).
- Primary source for the rulings recorded here: the Architect's final rulings of 2026-10-25 (the directive supplied to the registry contract owner; quoted by content, not reopened) and the Architect's round-2 rulings of 2026-10-25 (also quoted by content; section 6 lists each ruling and where it is recorded). Ownership baseline: [ADR-REG-TR01](2026-10-25-adr-tr-01-activation-and-epoch-ownership.md).
- Evidence rule: every statement about Runtime and Control Plane behaviour is a **source reading** at the heads in section 4, not a tested result. No repository test was run for this ADR. Nothing here is "qualified".

## 1. How to read this ADR

Each decision has a number (`D-nn`), a rationale, a source basis and, where it applies, the owning `EXT` PR. Decisions D-01 to D-06 record the schema-readiness items A1 to A4. The P1 plan is not restated; where a decision supersedes plan wording, section 3 says so explicitly. Section 6 is the provenance note for the Architect's round-2 rulings (each ruling and where it is recorded) and lists the few items that remain open, marked **proposed**.

## 2. Decisions

### A. Selection, withdrawal and activation (A1 to A4)

**D-01 Selection carries an explicit disposition (A1).**
Decision: an `r08-v2` selection statement carries `disposition` in `{select, withdraw}`. A withdrawal pins no record, names its predecessor exactly (selection id, strictly lower epoch, statement digest, `decision_ref`) and is signed under the `r08-v2` domain. Epoch ordering and authenticated supersession are preserved: a higher epoch alone never supersedes. Supersession requires a fresh authenticated statement with a strictly higher applicable selection epoch that names its predecessor; replay, restoration, withdrawal or stale selection state never reactivates or supersedes implicitly (round-2 R3). Withdrawal never erases historical evidence: the withdrawn statement, its digest and every log entry stay, and every rejected transition leaves preserved negative evidence (contract 7.1).
Rationale: the P1 plan had no withdrawal vocabulary; a UI or operator "disable" must be a signed, ordered statement, never an unsigned write.
Basis: Architect ruling A1 and round-2 R3; plan doc 04 A1; `registry_successor/selection.py` (supersession shape and `selection_supersession_invalid`, which a bad withdrawal reuses).
Owner: this ADR; implemented in `EXT-S1-2` (dispatch) and `EXT-S1-5`.

**D-02 `selection_withdrawn` is added to `CODES_V2`.**
Decision: `CODES_V2` is the 46 `r08-v1` codes plus exactly `trust_snapshot_version_stale` and `selection_withdrawn` (48). `CODES` stays 46 and byte-identical. `selection_withdrawn` is reached only after all ten v1 layers pass, through a final `disposition` layer, so an invalid statement can never read as an intentional withdrawal. For a required scope effect a withdrawal is a REFUSE (D-21), returns no policy and is never success. Optional participation returns the unchanged caller policy as `overlay_not_applied` only through the authenticated optional-state determination of D-17 (never as compliance or protection).
Rationale: absent, withdrawn, revoked, expired and superseded must each keep a distinct cause.
Basis: Architect ruling A1; `common.CODES` at the candidate (46 keys); LD-02 map `meta.code_count_note`.
Owner: declared in `EXT-S1-2`; mapped in `EXT-S1-5` (completeness test iterates all 48).

**D-03 Activation state and append-only transition evidence live in the enforcing component (A2).**
Decision: the enforcing component persists `activation_state` in `{active, withdrawn, revoked}` per scope key and an append-only, hash-chained transition log with `entry_type` in `{activate, withdraw, revoke, sync}`. State and history are separate stores: state is the current value, history is how it became so. No row means not activated. `activation_state` has no writer other than the four transitions, takes no input from a caller or UI, and is never stored in the registry.
Rationale: ADR-REG-TR01 decision 2 gives activation to the enforcing component; a state without history cannot be audited, and history without state cannot be read at the lock.
Basis: Architect ruling A2; ADR-REG-TR01; contract section 7.
Owner: schema frozen in `EXT-S4-0`; implemented in `EXT-S4-2`.

**D-04 Sync cannot manufacture authorization or reverse a revocation (A2 condition).**
Decision: `sync` records snapshot high-water and may append `revoke` entries. It never activates or withdraws, never clears a revoked pair, never changes a revoked state and never supplies authorization. The revoked set is grow-only; a newer snapshot that omits an earlier revocation is refused. An `activate` or `withdraw` at an epoch not strictly above the high-water, or without exact supersession of the current row, is refused (`revoke` and `sync` follow their own preconditions in contract 7.1: revoking the current epoch and redelivering the current snapshot are permitted); a revoked epoch is not resurrected by reactivation, lineage or restore. There is no implicit reactivation (round-2 R3): replay, restoration, withdrawal and stale selection state never reactivate a scope; reactivation is only a fresh authenticated `select` at a strictly higher applicable selection epoch that names the current row, and each rejected transition leaves preserved negative evidence (contract 7.1). A supersession gap is closed by a fresh higher-epoch statement naming the current row, not by processing unactivated ancestors.
Rationale: a lagging or hostile sync channel must not widen authority; the revocation source today has no rollback check (`TrustSnapshot.version` is only checked `>= 1`).
Basis: Architect ruling A2 and round-2 R3; `verify.py` `_normalize_trust`; plan doc 08 risks 8 and 9.
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

**D-07 Required and optional participation (round-2 R1).**
Decision: `participation` in the signed statement stays the only required/optional source; rule status (required/advisory) is a different thing. An omitted policy binding is **not** automatically equivalent to an intentionally absent optional policy. Required: a missing binding refuses; an invalid binding refuses; a withdrawal cannot silently downgrade the scope; a required scope never falls back to a wider caller policy, never returns success, and refuses or holds (D-21). The durable `scope_required` ratchet is authoritative for required participation (D-06). Optional: fallback to the caller policy requires an authenticated and valid optional-state determination (D-17); an omitted binding cannot bypass a previously activated or required policy; any other refusal is reported as "not applied", never as compliance or protection; the fallback reason is preserved in evidence. A statement whose participation differs from the operation class refuses `participation_mismatch`.
Basis: Architect round-2 R1; `decision.py` (`_refusal`, kinds); ADR-REG-TR01 reading rules; plan doc 02 CAP-7.
Owner: `EXT-S1-5` (map), `EXT-S4-2` (ratchet and guard).

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
Decision: Runtime `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`; Control Plane `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`. `max_amount` stays deferred (not a V1 task, slot or release blocker). No field beyond these eight. Composition only narrows. Confirmed out of V1 extraction (round-2): `identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds` and the evidence-obligation age limits are not added to the eight-field profile and their existing Control Plane enforcement is not disabled.
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
`activation_ref` (round-2 ruling, accepted): an **immutable reference to the specific consumer-owned activation transition governing the effect**. It is the entry hash of the enforcing component's `activate` log entry that made this selection active; the hashed entry content includes the scope key, the selection epoch, the selection digest and the event type, so it identifies the applicable scope, selection epoch and activation event and prevents substitution across scopes, epochs or events and reuse of stale state. It is **not** a Registry-issued authorization token: the registry never produces it and never treats it as authority. There is **one canonical representation** across Registry, Runtime, Control Plane and evidence: the string `sha256:` followed by 64 lowercase hexadecimal characters (the registry `valid_sha_ref` shape), never re-encoded, abbreviated or wrapped, and no component keeps a second form. It is stable across `sync` entries; a new activation yields a new value. `EXT-S4-0` may refine the entry layout but must keep these properties and add no competing member.
Rationale: the P1 plan listed "selection, epoch, record digest, evaluator build, trust snapshot, caller and effective policy digests" across three documents; those overlap, and a claim member that duplicates another can disagree with it.
Basis: `selection.py` statement fields; `verify.py` `TrustSnapshot`; `local_authority_effect.py` existing claim members (`institution_id`, `authority_domain`, `tenant_id` already ride in the claim; `consumer_id` and `operation` do not).
Owner: `EXT-S1-5`; checked by `EXT-S4-0` ("diverges: stop").

**D-15 Serialization profile for the binding (round-2 ruling).**
Decision: `binding_digest` over `canonical_bytes` (registry profile, `ensure_ascii=True`) with domain prefix `ocs-reg/r08-v2/policy-binding\n`. **V1 policy-binding identifiers are ASCII-only**, drawn from a formally specified restricted character set for the canonical identity fields (contract 4.1). Unsupported Unicode is rejected (`field_invalid`), never normalized (no NFC or NFKC, no case folding, no transcoding), so no two components can normalize inconsistently. This is a V1 interoperability restriction on canonical identity fields only; it is **not** a restriction on human-readable policy metadata, which is never a binding member. The Control Plane `commitment` serializer uses `ensure_ascii=False`, so the two differ for non-ASCII strings; ASCII-only members make them byte-identical. Exact serialization, byte encoding, field ordering and digest rules are recorded in contract 4.1. Cross-language golden vectors (at least the registry and Control Plane serializers and one non-Python implementation) and malformed-input tests (non-ASCII, out-of-set characters, over-length, wrong type, missing and extra members, non-canonical integers) are required. No Runtime or Control Plane code imports registry code.
Rationale: a digest that two components compute differently is an authority hole at the lock.
Basis: source reading `common.canonical_bytes` (registry) against `bounded._canonical_bytes` and `decision_input_profile.canonical_bytes` (Control Plane `7a4bcd40`); Architect round-2 ruling on policy-binding serialization.
Owner: `EXT-S1-5` (vectors incl. malformed-input refusals), `EXT-S4-4`.

**D-16 No automatic approval revival (ruled; mechanism ruled in round 2).**
Decision: there is no automatic approval revival. Withdrawing a narrowed configuration must not reactivate an older approval that is no longer valid under the current effective policy generation. A fresh approval, or explicitly authorized new issuance, under the new effective profile is required, and an old commitment is never reused as evidence of a new authorization. The mechanism is an **additive approval-generation or policy-binding mechanism with explicit generation continuity**, preferably carried in authenticated, approval-bound context. A detached mutable generation that could be substituted independently of the approval is not permitted. The candidate is an approver-bound generation or policy-identity key in the `runtime_authority_context` allow-list (`runtime_authority.py:262-267`), which is hashed into `approval_commitment` and absent-key-compatible (Worker D finding). Generation continuity means the generation is issued from the authoritative policy state (D-03, D-14), is monotone, and a withdrawal of a narrowing yields a new, higher generation, never a return to an earlier one; the exact derivation is the `EXT-S3-4` design note's to specify. This is a **Control Plane source change and requires a bounded implementation PR with additional tests** and exact re-pins; nothing in this ADR authorizes that edit. Terminal revocation of incompatible approvals through the Runtime destination's approval status (`set_approval_status`, `engine/local_authority_effect.py:523`, a source reading) was the earlier alternative (a); it is not the ruled mechanism. Narrowing the F4 scalars alone does not change the commitment and invalidates no approval.
**Mandatory negative sequence** (all six steps, in order): (1) an approval is issued; (2) the profile is narrowed; (3) the approval is invalidated; (4) the narrowing is withdrawn; (5) the original approval remains invalid; (6) a fresh approval succeeds only under the current authoritative policy generation. No generalized approval-history migration in V1.
Rationale: `approval_commitment` hashes the profile dump, so withdrawal returns the profile to P0 and an old P0 approval would match its commitment again unless generation continuity breaks the match.
Basis: Architect rulings (round 1 and round 2); `runtime_authority.py` `approval_commitment` (`:186`) and the `runtime_authority_approval_mismatch` check (`:268-271`) at Control Plane `7a4bcd40`: no generation or policy-identity member exists and the commitment is a pure function of content, so revival is automatic today (inferred, not run).
Owner: `EXT-S3-4` (design note, bounded Control Plane PR, six-step negative sequence), QG-04 (supersession in section 3).

**D-17 Optional-scope fallback and omitted binding (round-2 R1).**
Decision: optional participation may fall back to the caller policy only on an **authenticated and valid optional-state determination**; this is not a monotonic-tightening guarantee and V1 adds no universal tightening guarantee for optional policies. An omitted binding is not an intentionally absent optional policy: it cannot bypass a previously activated or required policy. Required participation never silently downgrades and stays fail-closed (missing or invalid binding refuses; withdrawal cannot downgrade). The determination is read from trusted durable state at the guard, never from the claim or the executor (contract 7.4, line 8): never activated (no row and no history, store not `unknown`), an authenticated `withdraw` of an optional selection, or an optional row past its verified `valid_until`. An active in-window row, a revoked row, an `unknown` store or a set `scope_required` ratchet never admits a no-binding claim. The fallback reason (`never_activated`, `withdrawn`, `expired`) is preserved in evidence with `applied=false`, the original `registry_code` and `fallback=caller_policy`. An invalid selection is reported under its own code and must not be relabelled `selection_withdrawn` (D-02). Previously committed effects stay governed by their original effective-policy evidence. A current claim must not reuse a stale policy identity: a claim minted under identity X is refused at the guard if the state row no longer matches X (never downgraded to a fallback there). The durable `scope_required` ratchet is authoritative for required participation, and a scope that must be fail-closed at commit must have the ratchet set (D-06).
Basis: Architect rulings (round 1 optional-scope fallback; round 2 R1); `decision.py` optional path; plan doc 04 acceptance criterion 8.
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

**D-21 Stale or rolled-back epoch and withdrawal are REFUSE (OPEN-Q12; `selection_withdrawn` ruled in round 2).**
Decision: for effects a stale or rolled-back epoch is a REFUSE with a specific stale-epoch cause (`selection_epoch_stale` carried structurally). HOLD is only for authority state that is genuinely unavailable or indeterminate with effect execution prohibited. Neither is ever a retryable success. This changes the merged map row `selection_epoch_stale` from HOLD to REFUSE (section 3, related disposition change). `selection_withdrawn` follows the same rule (round-2 ruling): **REFUSE** when the withdrawal is authenticated, current and definitively applies to the attempted effect; **HOLD** only when the authoritative state is unavailable or indeterminate and execution is prohibited; withdrawal is never translated into success. This changes the merged map row for `selection_withdrawn` from HOLD to REFUSE for required-scope effects; an optional scope falls back only through the authenticated optional-state determination of D-17.
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

**D-27 Control Plane owns safety bounds (O-4; AGE bounds ruled in round 2).**
Decision: the Control Plane contract owns the safety bounds for the three ages; the registry F4/F5 validator carries no private constant and reads a table copied from that contract with a citation and a test that fails if the two differ. **`AGE_MIN = 1` is adopted** (accepted in round 2; the Control Plane models admit 0, which only accepts an observation at exactly `now`; the floor validates the registry value and never clamps the effective output, so a caller value of 0 still yields 0). **`AGE_MAX = 2678400` is NOT adopted.** The maximum is an evidence-supported value selected by the Control Plane owner after source characterization; no production requirement is inferred from fixture values and no universal bound is invented. The evidence in hand supports no value: the largest value in any Control Plane or Runtime fixture is 3600 s, every observed value is synthetic, and neither repository has an upper bound or operational host data. **Interim position:** the supported range is `1 <= value <= MAX`, with `MAX` **pending**; no numeric maximum is stated here because none is justified yet. Until `MAX` is recorded the schema stays bounded and refuses invalid values: non-integers (including `bool`, floats, strings), nonfinite values, zero and negative values, and any integer that is unrepresentable in the Control Plane arithmetic (it would raise `OverflowError` or otherwise fail when added to a datetime). Worker D's reading is that with the freshness profile on, a base near 2.5e11 s overflows date arithmetic and raises an unhandled `OverflowError` outside the journal's exception tuple, and that with it off there is no technical ceiling; this approximate figure is a failure point for the owner to characterize exactly, not a supported maximum. A "caller value" is valid only as a strict integer with `0 <= value <= MAX` (the Control Plane models admit 0, so the caller range differs from the registry-input range `1 <= value <= MAX` only at 0); an invalid caller refuses and is never replaced, and a caller value of 0 stays 0. The precise supported range, with its evidence, is documented in the Control Plane contract **before `EXT-S1-4` or `EXT-S3-2` merges**; neither merges with a placeholder bound.
Rationale: a bound set by the registry would be a second owner of Control Plane safety semantics; an arbitrary universal constant is what the Architect ruled out.
Basis: Architect ruling O-4 and round-2 AGE BOUNDS; source readings at Control Plane `7a4bcd40` (section 5): `runtime_authority.py:87` (`ActionClass.max_status_age_seconds`, `ge=0`, no upper bound), `bounded.py:1271-1275, 1295-1299` (unvalidated kwargs), `freshness.py:68` (`max_age_extension_seconds`, no upper bound), `bounded.py:2081-2089` (`opened + timedelta(seconds=bound)`).
Owner: Control Plane owner (records the maximum and its evidence before `EXT-S1-4` and `EXT-S3-2`); referenced from the registry family validator in `EXT-S1-4`.

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

**D-29 R6: the effective freshness ceiling is enforced at the dispatch and authorization boundary (ruled in round 2).**
Decision: the effective freshness ceiling is enforced at the applicable dispatch/authorization boundary, and the effective registry-narrowed limit must remain binding throughout the supported Route B operation. **Host-factory composition is necessary but insufficient** where a later dispatch can act on an observation beyond the effective ceiling. The smallest compatible implementation is adopted, using existing deadline anchoring where supported. Binding constraints:
- `anchor_deadline_to_inputs` is investigated. Worker D found that setting it to true adds a key to the profile dump and therefore changes `approval_commitment`. **Commitments must not change silently**: any use of it needs an explicit, tested and re-pinned change in a bounded Control Plane PR with Architect review.
- The previously observed 2x dispatch window (an observation at the ceiling when read can still be dispatched until `opened + bound`, a pinned pre-existing behaviour, `tests/test_freshness.py:805`) is **NOT accepted as a V1 freshness guarantee**.
- Existing behaviour is preserved when no registry configuration is applied (default path byte-identical, commitments unchanged).
- The implementation must demonstrate that outage extensions cannot widen a registry-narrowed ceiling.
- If the mechanism changes Control Plane enforcement source: isolate it in a bounded PR, characterize existing behaviour first, add targeted negative and compatibility tests, re-pin the affected contracts and source revisions, and obtain Architect review before merge. This ADR authorizes no such edit.
Source reading that motivates the ruling: **profile narrowing alone does not meet the invariant**. If only `ActionClass.max_status_age_seconds` is narrowed, a validly signed extension is measured from the narrowed base and still lifts the grant-status window by up to `max_age_extension_seconds` (a probe with base 60 narrowed to 30 and the extension limit left at 300 authorized a status ten times the narrowed ceiling; the check deadline became opened plus 330 s). The extension applies to grant status, cached grant, cached purpose and the dispatch deadline only; conflict, policy, identity, mandate, approval, direct purpose reads and destination observation are not on the extension path.
- **Necessary component, factory composition (no Control Plane source edit):** the `EXT-S3-4` host factory composes the ceiling into the existing evaluation. For a validated integer ceiling `C_c` per class: `base_c = min(current_c, C_c)`, `headroom = min over classes of max(0, C_c - base_c)`, `extension limit = 0 if no freshness profile else min(current limit, headroom)`. Every internal call site passes the trusted base, so the extension is then bounded by the ceiling on every extension-aware path. Proof obligation: a property test over the unchanged public pure functions `effective_age_bound` and `extension_defects` and through `BoundedAuthorizationWorkflow`, including store rows rewritten to a higher `to` or the old base; plus the negative cases (extension to ceiling+1 refused with `age_extension_exceeds_limit`; extension to the ceiling allowed and a status at ceiling+1 held; rows recorded at the old base invalid with `age_extension_invalid`; cached purpose and cached grant refuse at ceiling+1; irreversible class never extended; default path byte-identical).
- **Dispatch-boundary enforcement (required, not optional):** the Control Plane owner characterizes the dispatch path and selects the smallest compatible mechanism that holds the ceiling at dispatch. Affected functions to characterize first: `freshness.effective_age_bound` (`freshness.py:182`), `BoundedAuthorizationWorkflow._class_age_bound` (`bounded.py:1358`), `record_age_extension` (`bounded.py:1376`), `BoundedRecordStore.record_age_extension` (`bounded.py:982`) and the dispatch-deadline computation (`bounded.py:2081-2089`), and `runtime_authority.py` only if the carrier is a profile field. A default of `None` for any new optional parameter keeps output byte-identical; a profile-field carrier uses the repository's `exclude_if` omission so default-path commitments stay identical; a constructor-keyword carrier changes no commitment but leaves the ceiling unbound from approvals. Exact re-pins: the Control Plane head, the `freshness.py`/`bounded.py`/`runtime_authority.py` blobs, the freshness, reversibility, runtime-authority and holder-inventory tests, and the adversarial mutation script. `engine/safe_executor.py` is never modified.
- **Characterization findings carried forward:** R-b, the public `extension_defects(..., base_seconds=None)` trusts a row's own base (no internal caller omits it). R-c, the extension limit is one profile-wide scalar, so the safe composition is the minimum headroom across classes (it may refuse an extension a roomier class could have had). R-d, the ceiling is recorded nowhere in the profile, so a later host that rebuilds a profile without composing it would pass undetected unless enforcement holds at dispatch.
Rationale: the ceiling is a safety invariant at the point where an effect is authorized; composing it only at profile construction leaves a window.
Basis: Architect ruling R6 (round 2); Control Plane `7a4bcd40` source readings: `freshness.py:155-201`, `bounded.py:1358-1396, 2078-2090, 2105-2143, 2163, 2393-2400`, `runtime_authority.py:339-342`; Worker D probes S2, S3, S3b, S3c, S4 (read-only, unmodified source; not repository tests).
Owner: `EXT-S3-4` (factory composition and proof); Control Plane owner (dispatch-boundary mechanism, bounded PR, Architect review before merge).

**D-30 Naming map: selection epoch versus record succession counter (DT-03).**
Decision: "selection epoch" is the `epoch` of an `r08` selection statement, assigned by the selection issuer and enforced against the consumer's high-water; "record succession counter" is the `epoch` of `ocs-registry-record/0` (hub `tools/registry_records.py`), which is never used as a selection epoch. In `r08-v2` the wire field stays `epoch`; the binding member is `selection_epoch`; r08 records carry `record_version`, not an epoch. No adapter is needed because the two contracts never share a document.
Basis: ADR-REG-TR01 decision 6 and DT-03; `selection.py` `STATEMENT_FIELDS`.
Owner: `EXT-S1-5`.

### F. CI baseline

**D-31 Registry CI baseline and green-CI requirement (EXT-S1-0 accepted; round-2).**
Decision: EXT-S1-0 is accepted. The registry `Registry tests` workflow (job `pytest`, merged in registry PR #23, merge `c6d82e18337496dda2b73df6122867e5d9378d58`, file `.github/workflows/registry-tests.yml` at registry `main` `fac15c795dbaa2504af196eec271f69e1aaabc15`) is the baseline for subsequent registry PRs. This work makes **no** branch-protection, ruleset or settings change. The absence of configured required checks does not remove the requirement of green applicable CI: every applicable check must be green on the exact head regardless of what is configured as required. For the Runtime, Control Plane and qualification repositories the access limitation is recorded accurately in section 4 (the GitHub API refused those repositories for this session, HTTP 403; heads were read with `git ls-remote`; branch protection and required-ness there are not determinable with available access). No required-check name is invented; check names are taken only from files or check-runs actually observed.
Basis: Architect round-2 CI ruling; registry `docs/ext-implementation/ext-s2-g-check-inventory.md` (EXT-S2-G, PR #24, merge `fac15c795dbaa2504af196eec271f69e1aaabc15`).
Owner: every registry PR (green exact-head CI); `EXT-S2-G` inventory for exact names.

## 3. EXPLICIT SUPERSESSION

The Architect's later rulings supersede the earlier wording in merged PR #22 (registry `d2c472e4a09543228bad62235e07a0dedfd7f48b`) as follows. The merged files are not edited; this ADR is the record, and the owning PR cards are read through it.

**(1) Approval revival.** Merged docs 07 (row "Outage extension and approval revival"), the QG-04 gate JSON (`docs/p1-extraction-plan/data/qualification-gate-matrix.json`, `new_tests_needed`) and the `EXT-S3-4` card (element 5 of `docs/p1-extraction-plan/11-ext-pr-execution-cards.md`) say that revival of an older P0 approval is "not guaranteed" by V1 and is "disclosed". **Superseded by**: no automatic approval revival; a fresh approval under the new profile is required; the mechanism is an additive approval-generation or policy-binding mechanism with explicit generation continuity, preferably carried in authenticated approval-bound context (no detached mutable generation), as a Control Plane source change in a bounded implementation PR with additional tests; the six-step mandatory negative sequence is required (D-16). The earlier "(a) versus (b)" question is ruled (section 6).

**(2) Control Plane R6 enforcement-file exception.** Merged docs say the S3 header is "no edit to `bounded.py`" (docs 06 and 11) and that `EXT-S3-4` stops if it needs any existing Control Plane source edit (doc 11, O-1). **Superseded by** the round-2 R6 ruling: the effective freshness ceiling is enforced at the applicable dispatch/authorization boundary; factory composition is necessary but insufficient; the smallest compatible implementation is adopted using existing deadline anchoring where supported; `anchor_deadline_to_inputs` changes `approval_commitment` and must not be used silently (any use is an explicit, tested, re-pinned change in a bounded Control Plane PR with Architect review); the 2x dispatch window is not an accepted V1 guarantee; default behaviour is preserved when no registry configuration is applied; and outage extensions must be demonstrated unable to widen a registry-narrowed ceiling. If the mechanism changes Control Plane enforcement source it is isolated in its **own** bounded PR (characterize first, targeted negative and compatibility tests, re-pin, Architect review before merge). The earlier "conditional exception, planning only" wording is replaced by this ruling. **This ADR itself authorizes no edit**; `engine/safe_executor.py` is never modified (D-29).

**CODES_V2 language.** Wherever merged wording counts the `r08-v2` code set as 46, 47 or as one set, it is read as: **46 `r08-v1` codes plus `trust_snapshot_version_stale` plus `selection_withdrawn` = 48** (D-02). This includes the LD-02 map `meta.vetting.completeness_test_rule` ("CODES plus trust_snapshot_version_stale (47)").

**Related disposition change (a consequence of OPEN-Q12, not a PR #22 prose change).** The LD-02 map row `selection_epoch_stale` (HOLD, OPEN-Q12 unresolved) is read as REFUSE with a specific stale-epoch cause, and the row `selection_withdrawn` (HOLD) is read as REFUSE for required-scope effects, with HOLD only for unavailable or indeterminate authoritative state (D-21). Its `runtime_route_b_commit.cause_requirement` ("mapped only if the destination PermissionError text carries structured detail") is read through D-19.

## 4. Exact source candidates (R10-F-03)

Verified on 2026-10-25. Registry head was read through the GitHub API (`gh api repos/cogno-us/cognous-ocs-registry/commits/main`). The GitHub API refused the Runtime, Control Plane and qualification repositories for this session (HTTP 403, repository access not enabled), so their heads were read from the live remote with `git ls-remote origin refs/heads/main` in the local clones. Same repositories, same refs; the method differs from the one the work order named.

| Source | Historical pin (P1 plan) | Current `main` head | Proposed candidate | Moved? |
|---|---|---|---|---|
| Registry `cogno-us/cognous-ocs-registry` | `d61ef729883c9c127cbd05b8f8a1a5944dc0e717` (merge of P0 PR #21) | `d2c472e4a09543228bad62235e07a0dedfd7f48b` (merge of PR #22; PR head `b34fa6613f225f944ca839d521a4f8a972b89cec`) | `d2c472e4a09543228bad62235e07a0dedfd7f48b` | **Yes**, by PR #22 only |
| Runtime `cogno-us/cognous-execution-runtime` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | No |
| Control Plane `cogno-us/cognous-control-plane` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | No |
| Runtime evaluator blob `engine/safe_executor.py` | `2fc880dae37eac76e5074533435740ce0684209d` | `2fc880dae37eac76e5074533435740ce0684209d` (`git rev-parse origin/main:engine/safe_executor.py`) | unchanged | No |
| Inventory `cogno-us/cognous-stack-qualification` | merge `be1994a961e4e40612d999972ede6547a3729887` (PR #227; final PR head `1b34db3442c70701d6ffad67db94a49492b1827b`) | `be1994a961e4e40612d999972ede6547a3729887` | merge `be1994a961e4e40612d999972ede6547a3729887` | No |

Registry movement `d61ef729` to `d2c472e4`: `git diff --name-only d61ef729 d2c472e4` lists only files under `docs/p1-extraction-plan/` (fourteen documentation files); no code, test, lock or frozen path changed. The registry source tree the later PRs refactor (`registry_successor/`, `registry_contract/`, `registry_consumer/`, `baseline/`, `tests/`) is therefore the same as the P1 pin. This ADR's own merge moves registry `main` again by documentation only; later PRs record the head they start from (D-23). The CI workflow (PR #23) and the CI inventory (PR #24) have since merged; Worker B's implementation docs, if any, are separate PRs and are not part of the candidate until merged.

Update at round-2 (recorded, not substituted): registry `main` has since advanced to `fac15c795dbaa2504af196eec271f69e1aaabc15` (merge of PR #24; PR #23 merge `c6d82e18337496dda2b73df6122867e5d9378d58`). `git diff --name-only d2c472e4 fac15c79` lists only `.github/workflows/registry-tests.yml` and `docs/ext-implementation/ext-s2-g-check-inventory.md`; no code, test, lock or frozen path changed. The candidate registry entry above is the historical tuple of this ADR's first revision; later PRs record the head they start from (D-23).

The candidate selects the tuple against which `EXT-S1-2` onward are built. It is **proposed**: the Architect accepts it by accepting this ADR (G-3). `EXT-S4-5` replaces the Runtime and Control Plane entries after the claim change.

## 5. Control Plane characterization (Worker D findings)

Worker D produced a read-only characterization of the Control Plane at `7a4bcd40` (functions, signatures and locations; behaviour per path; probes that imported the unmodified source in scratch directories). These are **source readings, not repository test results, and not qualification**. Findings used above:

| Finding | Where used |
|---|---|
| Profile narrowing of the class base alone lets a valid outage extension exceed the narrowed ceiling; composing `FreshnessProfile.max_age_extension_seconds` in the host factory bounds the extension with no source edit but is not sufficient at dispatch (round-2 R6); `anchor_deadline_to_inputs=True` adds a profile dump key and changes `approval_commitment` | D-29 |
| Extensions affect only grant status, cached grant, cached purpose and the dispatch deadline; not conflict, policy, identity, mandate, approval, direct purpose or observation | D-29 |
| `approval_commitment` hashes the full profile dump; narrowing a class base or the extension limit changes it, while narrowing the F4 scalars (constructor keywords outside the profile dump) does not; no generation, epoch or registry-identity member exists; re-widening to P0 recomputes the same commitment, so an older P0 approval **revives automatically** (inferred from determinism plus the equal-profiles-equal-commitments probe). The merged wording "revival is not guaranteed" understates this | D-16, section 3 |
| No existing maximum for any age in either repository; largest observed value 3600 s in synthetic fixtures; overflow of date arithmetic near 2.5e11 s on the freshness path; pydantic lax coercion accepts `"60"`, `60.0`, `True` and 10**30 on the profile model; constructor keywords are unvalidated | D-27 |
| Claim function names, signatures and locations; the declared-field requirement for a carrier | D-28 |
| Scalars outside the eight V1 fields (`identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds`, observation and evidence-obligation ages) have no narrowing path and are not added: the eight-field profile is unchanged | D-11 |
| Plan citations for `bounded.py:1271, 1274, 2398-2400, 2445, 2469, 2505, 2082-2088, 2163` and `runtime_authority.py:87, 341` verified exact at `7a4bcd40` | evidence |

Head-advance check: Control Plane and Runtime heads did not move; Worker D, like this ADR's author, could not read those repositories through `gh api` (HTTP 403) and used `git ls-remote`.

## 6. Architect round-2 rulings: provenance, and items still open

The Architect's round-2 rulings of 2026-10-25 are recorded as decisions; none is reopened here. Each ruling and where it is recorded:

| Ruling | Recorded in |
|---|---|
| R1 optional fallback and omitted binding | D-07, D-17, D-06; contract 4.3, 7.4 (guard line 8) |
| R2 commit-time state comparison | contract 7.4 (atomicity preface, comparison lines 1 to 8); D-13 |
| R3 supersession | D-01, D-04; contract 3, 7.1 |
| R6 freshness ceiling at dispatch/authorization | D-29; contract 2.2; section 3 (2) |
| AGE_MIN adopted; AGE_MAX not adopted; interim bounded schema | D-27; contract 2, 2.1 |
| `selection_withdrawn` REFUSE or HOLD | D-02, D-21; contract 3.2; section 3 (related disposition change) |
| `activation_ref` definition | D-14; contract 4, 4.2 |
| Policy-binding serialization (ASCII-only, vectors) | D-15; contract 4.1 |
| Approval revival mechanism and six-step negative sequence | D-16; contract 7.5; section 3 (1) |
| Out-of-scope scalars confirmed | D-11; section 5 |
| CI baseline | D-31; section 4 |

Items still open (**proposed**, not decided here):

1. **AGE_MAX value** (D-27): the Control Plane owner records the evidence-supported maximum and the precise supported range before `EXT-S1-4` or `EXT-S3-2` merges. Until then the range upper bound is pending.
2. **Approval-generation derivation** (D-16): the exact generation continuity rule and carrier field name are specified in the `EXT-S3-4` design note and reviewed by the Architect with the bounded Control Plane PR.
3. **Dispatch-boundary mechanism** (D-29): the Control Plane owner's characterization selects the smallest compatible mechanism; Architect review precedes merge of any Control Plane source change.
4. **Binding identifier character set** (contract 4.1): fixed here as the V1 set for the Architect's acceptance with this ADR; any change is an ADR amendment.
5. **Review-driven clarifications to confirm** (added after the first Copilot review; they apply existing rulings and add no field to the eight-field profile): the state columns the guard needs (contract 7); the `last_accepted_snapshot` input and bootstrap rule and the fingerprint encoding with a vector (contract 5, D-25); the supersession-gap closure by a fresh higher-epoch statement (contract 7.1, D-04).

## 7. Review checklist (card element 5)

- No `max_amount` slot, reserved key or task; no ninth field; eight fields exactly (D-11).
- No five-second floor; no cross-bound among the distinct ages (contract 2).
- V0.2 contracts not reopened; ADR-REG-TR01 unchanged and cited.
- Registry never activates, issues a grant or authorizes an effect (D-22).
- Required scope never falls back to a wider caller policy (D-07, D-17).
- `r08-v1` behaviour and serialized outputs unchanged; `CODES` is still 46 (D-02, D-09).
- Nothing is called qualified; GAP-G4-13 open; S5 PREPARE-only (D-26).
- No edit to `engine/safe_executor.py`; no Control Plane edit authorized by this ADR (D-16, D-29).
- Round-2 rulings recorded and not softened (section 6); no ninth field and no out-of-scope scalar added (D-11).
- `AGE_MAX` not adopted; upper bound pending with an interim bounded schema (D-27).
- No qualification claim (D-26); no branch-protection or settings change (D-31).
- All links in this ADR and the contract resolve (checked mechanically before the PR).

## 8. Evidence and limits

Read for this ADR: the merged P1 plan (documents 01 to 11 and both data files), ADR-REG-TR01, `docs/r08-s01-contract.md`, `registry_successor/{common,selection,verify,decision,compose}.py` at `d2c472e4`, and Runtime and Control Plane source at the section 4 heads for the named functions. The JSON in the contract parses and its digests (unchanged by the round-2 corrections, which add no example input) were computed with the stated profile using the registry `common.digest`; signatures in the examples are placeholders. The Control Plane findings in section 5 are source readings by a separate worker; they are not test results. Not read: Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest (UNVERIFIED).
