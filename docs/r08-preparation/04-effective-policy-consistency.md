# R08-PREP Lane D: Effective-policy consistency at the authority-to-effect boundary

Purpose: define a candidate policy-consistency tuple and the changed-condition behavior for a future operational registry, grounded in how the real OCS Control Plane and Runtime already revalidate authority at the effect boundary, and state exactly what OCS owns versus what GCR owns.

Architectural preparation only. Candidate models, not normative. No implementation, approval, activation or qualification.

## 1. Sources and revisions examined
- Registry repo `eb850c8` (rev-parse verified). Plan v1.2 §3.3-binding "Atomic effective-policy binding and non-forgetting" and §3.2 floors bullet; crosswalk rows A5, A6 (`PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md`).
- ISS review `gcr-registry-transaction-binding.md` (PR #12 head `547b9052`; it cites v1.2 PR #16 head `100aa407` and ISS main `f6723d54`; reference only).
- Control Plane clone head `7a4bcd40`: `local_authority_effect.py`, `runtime_authority.py`, `freshness.py`, `schemas/runtime_authority_reasons_0_1.json` / `_0_2.json`. Runtime clone head `c5e97e87`: `engine/local_authority_effect.py`, `atomic_local_control_plane_executor.py`, `effective_grant.py`, `local_authority_effect_recovery.py`.
- S01/S02 pins fetched and compared: Runtime `ec728da6`, Control Plane `0a41faa9`. Differences relevant here: Runtime head adds terminal approval revocation (`authority_approval_revocations_v1`, `_approval_revoked`, checked at provisioning and at commit); Control Plane head differs from the pin by one small change in `local_authority_effect.py` (10 lines, content not analysed). All other cited behavior I saw only at the clone heads. Assume nothing about the pin beyond the diff checked.
- Constitution `1c2e920f` text read: CA03, CA05, CA06, CA07, CA12, CA16, CA18, CA20, CA21, CA22, plus the CA table intro. No formal adoption inferred.
- PR #13 `unresolved.md` rows W8-091, W3-063, W9-027; PR #17 §08 D1–D13 (read, not restated). Both PRs are now merged (PR #13 `e20504df8d2c8ddf8b3944c0dabb0dcf5f1009b6`, PR #17 `e3f5bbc32f957a10822a15a1b642e48c63d428e9`): **MERGED SOURCE EVIDENCE, WITH PROVISIONAL CLASSIFICATIONS**; not adopted requirements.
- Baselines kept separate (Architect LD-06): HISTORICAL = S01/S02 pins; CURRENT CANDIDATE = Runtime `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`, Control Plane `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (re-verified). No integration baseline is selected; R10 selects one; see `10-source-revision-reconciliation-and-review-closure.md`.
- NOT inspected: COG-REG-SHARED-ADD-01 (unavailable); `revocation_closeout.py` internals beyond its header; Control Plane `dedupe.py`/`merge.py` semantic bodies; the Control Plane decision/approval resolution path beyond claim materialization; any registry-consumer code path (registry S04 overlay) for effect-time use; GCR/ISS Core code (access-limited); the older Control Plane pin diff beyond stat.

## 2. Findings from source
1. [EXISTING] The OCS effect boundary is the atomic local authority/effect profile (`urn:cognous:profiles:local-authority-effect:0.1.0-proposed`). `execute_claim_atomic` opens `BEGIN IMMEDIATE`, reads trusted time after lock acquisition, loads the claim row (must be state `issued`), calls `_validate_claim_state`, checks budget, runs the optional operation-identity guard, rejects a repeated `attempt_id`, then inserts attempt, consumes the claim, increments the budget, inserts the effect and receipt, and `COMMIT`s. Authority writers (`set_grant_status`, `set_approval_status`, `set_policy_state`, `set_evidence_state`) also use `BEGIN IMMEDIATE`, so they serialize with the effect transaction. Scope: one SQLite database; the source states "no remote atomicity".
2. [EXISTING] `_validate_claim_state` rechecks at commit: exact match of ~24 operation fields against the claim; claim validity interval; authoritative grant row (revision equal, status `active`, institution/domain/tenant, revision not in the retained revoked set, grant validity interval); each approval row (status `active`, not retained-revoked, grant/revision/proposal commitment/`policy_versions` equal); each policy row (`ref`, `version`, status `active`, tenant); each evidence row (source unchanged, `current` when required or `hold_effect`, not future, age within `max_age_seconds`). Failure raises `PermissionError` with a free-text message.
3. [EXISTING] The only "policy" the boundary revalidates today is the claim's `policy_state` list of `{ref, version, status}` rows (`PolicyProjection`), taken from the approval's `policy_versions`. It has no digest, no selection identity, no evaluator identity and no epoch. The receipt records `grant_state_commitment`, `checked_at`, `claim_id`, `attempt_id` but no policy or approval state commitment, although the claim carries `policy_state_commitment`, `approval_state_commitment`, `authority_state_commitment`.
4. [EXISTING] Revocation is terminal per `(grant_id, revision)` and per `approval_ref` on the Runtime destination; re-provisioning a stale claim cannot revive it (`provision_claim`). Terminal approval revocation is not in the S01 pin `ec728da6`.
5. [EXISTING] Claim materialization (Control Plane `_validate_issuance_snapshot`) requires a fresh resolution of the same trusted workflow and refuses unavailable or non-`active` policy/evidence snapshots; the claim "is not authority by itself" and must be consumed in the destination's transaction.
6. [EXISTING] `AtomicLocalControlPlaneExecutor.execute` maps outcomes: policy-check failure -> `denied` (`local_policy_rejected` / `local_policy_evaluation_error`); operation-identity or `PermissionError` at commit -> `denied`, failure_class `authority_hold`, reason_code `current_authority_rejected`; `TimeoutError` or any other exception after possible commit -> `unknown` with reconciliation, never a refusal and never `retry_eligible`; `PostCommitObservationUnavailable` keeps a durable effect from reading as refusal. `reconcile_claim_exact` returns `hold` with `retry_eligible: False` for binding mismatch or `no_durable_effect_for_claim`.
7. [EXISTING] `effective_grant.py` is a separate optional profile (`sqlite-effective-grant/0.1`) that digests principal/grant/revision/permissions/status and re-reads the row under the effect transaction; its source says the digest proves only that the caller read the row, so permissions are rechecked. The two profiles refuse to share a database.
8. [EXISTING] Freshness profile (`freshness/0.1`, opt-in): a deadline checked immediately before `destination.apply` "narrows the window... It does not close it"; the lease is same-host `flock`; the record store is a plain JSON file with no keyed integrity; signer fields are asserted names. This limits any claim that a pre-dispatch check equals commit-time authority outside the atomic destination.
9. [EXISTING] Closed vocabularies: `runtime-authority-reasons/0.1` (121 codes) and `/0.2` (164 codes, superset). Relevant codes present: `policy_missing`, `policy_stale_or_changed`, `policy_superseded`, `policy_version_changed`, `policy_status_unknown`, `policy_status_stale_or_future`, `policy_binding_mismatch`, `policy_tenant_mismatch`, `grant_revoked`, `grant_suspended`, `grant_revision_stale`, `grant_revocation_recorded`, `approval_not_active`, `required_approval_missing`, `required_evidence_not_current`, `required_evidence_stale_or_future`, `evidence_binding_mismatch`, `status_unreadable`, `context_unknown_requires_hold`, `check_expired_before_dispatch`, `check_overdue`, `check_lease_unavailable`, `dedupe_unresolved_attempt_blocks_new_key`, `attempt_unresolved_past_horizon`, `operation_not_admitted`. No code names a selection, epoch, record digest or evaluator build. The destination's commit-time `PermissionError` strings (e.g. "authoritative policy state invalid") are free text, not these codes.
10. [DEV-TESTED, not re-run by this lane] Control Plane `freshness.py` cites `tests/test_freshness.py` for the 2x age window. Not otherwise verified; no tests were executed.
11. [EXISTING] S04 registry consumer is an optional overlay; a refused overlay returns caller policy unchanged (brief; frozen). It has no effect-time path. Not established: any existing registry-to-effect-boundary binding. [EXISTING] ISS review itself states S04's `policy_reference` has no authenticated selection epoch, revocation check or atomic binding.

## 3. OCS-owned versus GCR-owned (v1.2 §3.3-binding, A5/A6, ISS transaction-binding)
| Item | OCS | GCR | Registry |
|---|---|---|---|
| Effect-time recheck of grant, approval, revocation, evidence, freshness, budget, dedupe | Owns (component code; plan §3.2 keeps these in component code) | No | None |
| Cognitive admission, StateDelta/Governor commit, output/reliance eligibility | No | Owns | None |
| Source preservation, negative-record continuity (A6) | Preserves own effect evidence only | Owns | Must not erase or reinterpret history |
| Exact selection, record, evaluator identity as data | Consumes via adapter | Consumes via adapter | Supplies and custodies (once defined by Lanes A, B) |
| Same authorized selection bound to admission and commit | Must bind in its own transaction | Must bind in its own transaction | Cannot do it for either |
| Cross-domain atomicity | Not claimed | Not claimed | Not claimed |
OCS must not reuse GCR cognitive admission as a grant, and a registry selection is not an OCS execution grant (plan §3.3-binding; ISS table row "Cross-system OCS effect"). A5 scope clarification: no global atomic commit; ISS S04 pin does not qualify transaction-time revalidation. A6 legal erasure/retention is a later explicit domain ruling; this lane does not decide it.

## 4. Candidate design [PROPOSAL]
### 4.1 Policy-consistency tuple (candidate, OCS-domain view)
| # | Member | Notes |
|---|---|---|
| 1 | `selection_id` | From Lane B authenticated selection; not derived from record status |
| 2 | `selection_epoch` (or revision) | Monotonic per selection scope; semantics from Lane A |
| 3 | `record_id`, `record_version` | Exact; never `latest` |
| 4 | `record_digest` | Integrity only (D2 open); never read as authority |
| 5 | `evaluator_id`, `evaluator_revision`, build identity | Registered code evaluator; loaded-code integrity is a separate open threat-model item |
| 6 | `consumer_id` | Named Control Plane/Runtime consumer instance (MSOP §3.4) |
| 7 | `governing_context` | Institution, authority domain, tenant, operation family/context |
| 8 | `admission_evaluation` | Evaluation time (`evaluated_at`), inputs commitment, result; admission is not commit |
| 9 | `observed_authority_conditions` (not the ISS-review record field `effective_conditions`; see 08 §2 R-03) | Grant id/revision/status, approval refs/status, evidence state, freshness bounds, as observed |
| 10 | `commit_effect_ref` | claim_id, attempt_id, effect_id, decision_id, receipt id, `checked_at`/`linearized_at` |
| 11 | `evidence_commitment` | Commitment over members 1-10 as recorded, written with the effect |
The tuple is two distinct things: (a) an **admission-time pin** frozen with the claim, and (b) a **commit-time observation** written by the destination under its lock. Equality of (a) and (b) members 1-6 is checked at commit; member 9 is re-read, not copied.

### 4.2 Binding point without a competing check (amended; F1 guarantee UNQUALIFIED)
- A registry selection is **not an OCS execution grant** (Architect C-03/LD-01). The earlier proposal to extend the claim's grant-derived `policy_state` row with selection fields is withdrawn as a preferred design: the grant policy row is grant authority, and modelling a selection as a grant policy merely because that path revalidates atomically would blur two authorities.
- Required instead (R10, OCS Architect with Runtime and Control Plane owners): an explicit integration design that keeps six things distinct: A selection authentication, B effective policy evaluation, C OCS grant authorization, D pre-commit policy applicability, E effect commitment, F evidence recording (ownership table: document 03 section 4.1). It must show **either** re-evaluation of the effective policy within a supported atomic boundary, **or** an independently defensible binding protocol that prevents a policy change from widening the executable operation between check and effect.
- **UNQUALIFIED:** `LocalExecutionPolicy.check` runs before the atomic claim transaction (`atomic_local_control_plane_executor.py:69`; transaction at `local_authority_effect.py:782`, revision `c5e97e87`). Selection identifiers compared at commit would detect a changed identity; they would not by themselves establish that every F1 restriction was atomically revalidated. Until the design above exists, the F1 authority-to-effect guarantee is UNQUALIFIED. An evidence-only reference does not prove the selected policy remained authorized at commit, and a recorded policy digest does not prove atomic evaluation.
- Candidate tuple members 1-6 of 4.1 remain the exact-match data a future binding would compare; where they would be compared is the open design (LD-01).
- [PROPOSAL] Record the commit-time policy and approval state commitment in the authority receipt (today only the grant state commitment is recorded, finding 3) so evidence shows what was actually checked.
- **Open binding gap (selection validity):** selection validity at initial admission is insufficient if it changes before effect commitment. A selection can expire between evaluation and commit without changing its epoch, digests or any policy row, so identity equality alone does not enforce document 01 section 3.4's commit-time validity requirement. Closing it needs a lock-held validity check against trusted time in the destination, or constraining the claim's validity interval to the authenticated selection interval. Neither exists; registered as LD-09, not solved here.
- Not recommended: a separate registry check before dispatch (a competing check with a window, finding 8, at risk of being read as authorization); a second OCS authority engine. Any claim, destination schema or receipt change belongs to the Control Plane/Runtime owners and needs a successor profile; not authorized here.

### 4.3 Outcome semantics and crosswalk to existing components (controlling candidate for documents 03, 06)

**Conceptual outcomes** (Architect LD-02; candidate wording, independent of any component's codes):
- **REFUSE:** a registry input, selection, authentication, composition or evaluator contract cannot be accepted.
- **DENY:** a valid, applicable policy prohibits the requested action.
- **HOLD:** execution cannot safely proceed because authority, evidence, required policy or current applicability is unavailable or unresolved.
- **RETRY:** a new, independently evaluated attempt may be made after a transient or changed condition. RETRY is never permission to reuse a stale approval, selection, evidence or authorization, is never automatic for an in-doubt effect, and needs a new attempt identity.

**Crosswalk to existing component classes** (descriptive of source at `c5e97e87` / `7a4bcd40`; not a new vocabulary, not approved, and component-specific distinctions are preserved):

| Conceptual | Runtime (local / atomic executor) | Control Plane | S04 overlay (frozen) |
|---|---|---|---|
| REFUSE | Registry-side input rejection has no Runtime code today; construction refusals (`ValueError` without policy) | Reason codes for unknown/unadopted status (`policy_status_unknown`, `policy_binding_mismatch`) apply to grant policy refs, not registry inputs | any refusal: caller policy unchanged, `overlay_applied False` ("not applied", NOT denial) |
| DENY | `denied` with `failure_class="policy_denial"`, `reason_code="local_policy_rejected"` when `LocalExecutionPolicy.check` rejects | `deny` outcome is declared, emitted only by one adapter (document 06 finding 9) | not applicable |
| HOLD | `denied` + `authority_hold` + `current_authority_rejected` on commit-time `PermissionError` (name says hold, outcome field says denied: mapping unsettled); `unknown` with reconciliation when commit is in doubt; reconcile `hold` with `retry_eligible: False` | `hold` with reason codes (`policy_status_unknown`, `status_unreadable`, `policy_stale_or_changed`, `context_unknown_requires_hold`) and `EffectTimeRefusal` rows | not applicable (optional profile never holds) |
| RETRY | `retry_eligible: False` on unknown outcomes; retry rules depend on W3-063 and W9-027 (open) | new decision under freshly resolved inputs; dedupe rules open | not applicable |

Rules: an uncertain authority state is not classified as ordinary policy DENY where the existing component requires HOLD or another bounded refusal; commit-time `PermissionError` free text is not a closed reason code; mapping REFUSE/DENY/HOLD/RETRY onto these classes is decision LD-02 for the OCS Architect with the Runtime and Control Plane owners (R10, qualified in R17); no universal reason vocabulary and no change to existing Runtime or Control Plane outcomes is proposed; any selection/epoch/evaluator reason code needs the separately versioned vocabulary process (D8; R07 ruling keeps 0.1 and 0.2 distinct). Mandatory profile: merged R07 ruling D7 permits it as a design capability, not for activation; required-policy failure must not fall back to a broader caller policy. Optional profile: truthful "overlay not applied" record only.

### 4.4 Prohibited behaviors
- Treating a matching record digest, PR merge, record status or repository presence as current authorization.
- Silent hot-swap of selection, record or evaluator between admission and commit; selecting `latest`; automatic fallback to prior or newer selection.
- A registry-side check that substitutes for, or runs instead of, the OCS commit-time recheck; any registry-minted grant, approval, revocation bypass or reactivation.
- Replay or restore reactivating withdrawn authority; re-provisioning a claim over revoked state.
- Reporting a possibly committed effect as refusal or retryable (existing rule, finding 6); reporting commit failure as admission success.
- Claiming atomicity across OCS and GCR, across remote effect destinations, or across the registry store and the effect database.

## 5. Race / changed-condition table [PROPOSAL, built on findings]
| Condition | Detection point | Required behavior | Evidence recorded | Remains unproven |
|---|---|---|---|---|
| Mid-execution selection withdrawal | Commit-time applicability check (design open, 4.2; F1 UNQUALIFIED); [EXISTING] only for grant-policy `policy_state` status/version | REFUSE/DENY before commit (mandatory); if effect already committed, no rollback claim (CA22): record as completed-before-withdrawal | Failure record with closed code; receipt with commit-time commitment | Withdrawal ordering vs commit across the registry store and effect DB; selection withdrawal feed to destination is not built |
| Selection expires mid-flight (interval ends between evaluation and commit; epoch and digests unchanged) | Not detected by identity comparison; needs a lock-held validity check or interval-constrained claim (4.2 gap) | REFUSE before commit if the check exists; otherwise not detected and must be stated, not assumed | Expected interval end, trusted `checked_at` | Trusted time source (F-06); no such check exists |
| Concurrent selection update (epoch bump) | Epoch inequality at commit | REFUSE; RETRY only as new operation under new pin | Old pin, observed epoch, refusal | Epoch semantics (Lane A); who writes the destination row |
| Revoked grant | [EXISTING] grant row + retained revoked set under lock | DENY (`grant_revoked` class codes) | [EXISTING] failure record; receipt only on success | Cross-host revocation propagation; holder-inventory scope |
| Withdrawn approval | [EXISTING] approval row + terminal revocation set (head `c5e97e87`; not in S01 pin) | DENY | Failure record | Behavior at S01 pin lacks terminal approval revocation; independent qualification absent |
| Expired evidence | [EXISTING] evidence age/state check under lock | HOLD or REFUSE per `unknown_behavior`/required flag (mapping unsettled) | Failure record | Evidence authenticity; clock trust (`_trusted_now`) |
| Changed policy revision (same ref) | [EXISTING] version compare; registry digest compare [PROPOSAL] | REFUSE (`policy_version_changed`/`policy_stale_or_changed` class) | Both revisions in failure detail | Whether digest change with same version is possible depends on Lane A immutability |
| Changed evaluator build | [PROPOSAL] evaluator id/revision/build compare at commit | REFUSE required profile as unsupported; optional: no-overlay record | Expected vs loaded identity | Loaded-code integrity; hashing a file on disk is insufficient (plan §3.2) |
| Stale cache | [EXISTING] purpose cache and status age checks in opt-in profiles; destination re-reads rows | Cache is never authority; commit-time row wins | Cache age and basis | Cache coverage outside the atomic profile; freshness window is narrowed, not closed (finding 8) |
| Failed write (authority row or effect) | Transaction rollback; executor reconcile | Pre-commit failure: REFUSE, claim stays `issued`. Ambiguous: HOLD, reconcile, never retry blindly | Failure record or `unknown` with reconcile status | Failed-failure-record case is flagged `failure_record_unavailable` only |
| Restore / replay | Claim state `consumed`; attempt identity unique; historical pin kept | Replay never re-authorizes; restored authority rows must not revive revoked state | Historical pin retained read-only | Backup restore of authority tables is not shown to preserve retained revocation sets; not inspected |
| Authority-to-effect race (writer vs effect) | `BEGIN IMMEDIATE` serialization in one SQLite database | Whoever commits first wins; effect after revocation committed is impossible in this profile | Receipt `checked_at` vs row state | Any non-SQLite or remote destination: no atomicity claimed |
| Duplicate / retried operation | [EXISTING] attempt-id uniqueness, claim consumption, operation-identity guard (opt-in) | REFUSE duplicate; RETRY only per definition | Attempt rows | W3-063 (key-forgetting TTL) and W9-027 (applied/unresolved definitions) open; effect cap origin W8-091 open |

## 6. Constitutional and v1.2 mapping
- Plan: R09/R10/R16 (§3.3-binding, crosswalk A5); R07/R08 MSOP (§3.4); A6 non-forgetting; floors in component code (§3.2). Constitution: CA05 (fail closed without inventing policy: no invented codes), CA07 (bind to exact source and governing context), CA12/CA21 (mandatory floors and boundary semantics), CA18 (authenticated governance policy), CA20 (scoped delegation, revocation), CA22 (rollback is not reversal of committed effect), CA06, CA16 (no label promotion).

## 7. Decisions raised
| ID | Decision | Owner | Blocking consequence | PR #17 overlap |
|---|---|---|---|---|
| LD-01 | **Architect: amended.** Selection is not a grant; design a separate applicability binding with re-evaluation in an atomic boundary or a no-widening binding protocol; F1 guarantee UNQUALIFIED until then | OCS Architect with Runtime and Control Plane owners (R10) | No effect-time registry binding can exist; F1 stays UNQUALIFIED | D7, V2 |
| LD-02 | **Architect: accepted with amendments.** Conceptual outcomes separate from component mapping (4.3); no universal vocabulary | OCS Architect / Runtime and Control Plane owners (R10; qualified R17) | Evidence cannot be machine-compared; no new code may be assumed | D8 |
| LD-03 | Mandatory vs optional participation for the F1 effect profile (participation is per operation, v1.2; D7 permits mandatory as design capability, not activation) | Operator | Fail-closed behavior cannot be claimed | D7 |
| LD-04 | Selection withdrawal propagation to the destination's authority table (writer, trust, ordering) | OCS Architect, Operator | Withdrawal detection point has no source | D2 |
| LD-05 | Receipt content: add policy/approval state commitment and selection tuple | OCS Architect | Evidence cannot show what was checked | none |
| LD-06 | Compatibility of terminal approval revocation with S01 pin consumers | Operator | Pin-vs-head behavior differs | none |
| LD-07 | Independent qualifier for the effect-time path (S05 limits do not qualify) | Independent qualifier | No QUALIFIED label possible | D13 |
| LD-09 | Close the selection-expiry binding gap: lock-held validity check, interval-constrained claim, or accepted limitation | OCS Architect | Mid-flight expiry undetected at commit; document 01 §3.4 not enforceable | V1 |
| LD-08 | Dependency: W8-091, W3-063, W9-027 classification | Operator/OCS Architect | Retry/dedupe and cap semantics stay open | D1, D6, D12 |

## 8. Interfaces expected from other lanes (stated, not designed)
- Lane A: lifecycle states and the definition of selection epoch/revision (monotonic, scope, supersession, withdrawal states) and record immutability per version/digest.
- Lane B: the authenticated selection object (issuer identity, trust root, custody) and how a consumer verifies it; out of this lane.
- Lane C: integration points where the Control Plane/Runtime adapters obtain the tuple and where the OCS authority writer receives selection state.

## 9. Risks and unresolved constraints
- F1 authority-to-effect guarantee: UNQUALIFIED (4.2).
- Decision IDs in this document are written `LD-nn` so they cannot be confused with PR #17 D1-D13.
- Binding limit for F1 (integration note): the registry-derived `LocalExecutionPolicy` values are evaluated by `policy.check` before the claim, outside the atomic transaction (lane C 03 §3.4). A tuple member compared at commit detects a changed selection/record/evaluator identity; it does not re-evaluate the narrowed allow-lists inside the transaction, and it exists only if the selection is modelled as a policy row the destination reads (03 C-03). Neither is a source fact today.
- The effect boundary today does not know the registry; every "bind" here is a proposal needing OCS source change and approval.
- Atomicity holds only inside one SQLite database with trusted writers; SQLite does not separate a caller holding the file from the authority writer (Runtime source). Not a defense against compromised host or runtime.
- Commit-time errors are free text; closed-code mapping unsettled; vocabulary change goes through its own process.
- Recording the tuple in a receipt proves what was recorded, not that authorization was valid at that instant; only the lock-held recheck does, and only for rows the destination actually reads.
- W8-091 (where `max_effects` originates), W3-063 and W9-027 remain open; the duplicate/retry row depends on them.
- No QUALIFIED or PRODUCTION evidence was found; no tests were run by this lane.
- Clone heads differ from the S01 pin (approval revocation); statements on pin behavior are limited to the diff checked.
