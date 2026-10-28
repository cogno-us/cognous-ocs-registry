# Unresolved architectural decisions

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

## 1. Decisions raised by the lead

### AUD-D01 — AD-07 is still recorded OPEN, but Registry narrowing of max_amount, max_effects, target prefixes and target_match is merged

The frozen G0 decision register (docs/family-migration/g0/unresolved-decisions.md, AD-07) asks whether the Registry may ever carry these four fields, given Amendment 3 records them as caller-owned residuals, and lists it OPEN. Registry PRs #54 (r08-v3, merge ba98dd26) and #56 (r08-v4, merge b7e6a173) and Runtime PRs #151, #152 and #153 (merge f7a55e2a) implement exactly that narrowing, and the M2 record treats it as authorized. This audit found no later repository record that closes AD-07, so the register and the merged code disagree. It is a governance-record inconsistency, not a safety defect: the Runtime narrowing adapter was read and enforces subset-of-caller sets and ceilings no higher than the caller's.

*Recommendation:* The Architect records an explicit disposition for AD-07 (ratify the merged M2/M3 narrowing, or direct a revert) so the register matches the code.

### AUD-D02 — Counting rule: represented in the Registry is not governed

G0 labelled RG-A-007, RG-A-008 (and, in the audit's view, RG-C-021) ALREADY-GOVERNED. The Registry composes the F4 status/approval scalars and the F5 per-class map (registry_successor/v2_age_bounds.py), but the Control Plane imports no Registry code and enforces only host-supplied values; policy_binding.py enforces a host-copied age_ceilings. Three facts are therefore kept separate throughout this audit: represented in the Registry, integrated at an enforcement boundary, independently accepted. Only rules with the first two are REGISTRY-GOVERNED.

*Recommendation:* Adopt the three-layer definition for backlog and PASS accounting; carry the F4/F5 age rules as eligible with the Registry half represented until the Control Plane consumer (waves M11/M12) is merged.

### AUD-D03 — RG-C-018 (freshness nonce toggle) is not Registry-enforceable (superseded finding)

FreshnessProfile.nonce (default True) is host-settable and a forcing-True overlay would be monotone, but the resolver silently falls back to a plain read when it lacks nonce support (bounded.py:2208-2223), so a Registry cannot enforce it. Pass 1 first kept it ELIGIBLE (marginal); cross-check J2 and pass-2 Worker E reclassified it PROVIDER-OR-HOST-OWNED, which is the final disposition.

*Recommendation:* None needed; recorded so the earlier ELIGIBLE reading is not relied on.

### AUD-D04 — Two ocs-registry-record/0 formats exist

Repository-coverage worker I2 found the hub's tools/registry_records.py (lines 18-31) defines a second ocs-registry-record/0 format beside the Registry's r08-v2 record. Which one is the migration target, and whether the hub vocabulary must be reconciled with the Registry successor contracts, is not decidable from source.

*Recommendation:* Architect names the authoritative record format; until then the rule NEW:hub-registry-record-profile-vocabulary stays UNRESOLVED.

### AUD-D05 — Redaction defaults: floor or presentation choice?

The audit rates the Control Plane, Action Manifest and Replay Bundle redaction defaults CALLER-OR-ISSUER-OWNED (caller-overridable presentation defaults; no redaction floor exists in code), which removes the G0 eligible group RG-F11. A Registry 'minimum redaction' would be a new confidentiality control, not the migration of an existing one.

*Recommendation:* If a minimum-redaction floor is wanted, treat it as a new privacy-owned feature (plan wave M10) with its own decision, not as a rule migration.

### AUD-D06 — How a Registry-narrowed Control Plane class value enters approval_commitment

The whole ActionClass is hashed into approval_commitment (runtime_authority.py:236-247). Narrowing a per-class age, unreadable posture or revocation-assurance flag through a Registry record changes a committed value, so the commitment coupling must be defined before RG-C-008/C-009/C-010 (and the merged F5 class age rule) can be implemented.

*Recommendation:* Decide the coupling in the M12 design before any F5 Control Plane consumer is authorized.

### AUD-D07 — Coverage gaps the Architect may want closed

Not reviewed in full: Stack Qualification (about 10 of 28,961 files read), Action Manifest and Governed Exchange schemas/examples/docs/tests, parts of the Stack Orchestrator (store.py, machine.py, observer.py, preserve.py, observations.py, refund_runtime.py and about 20 scenario modules were grepped only), and S02-covered Runtime/Control Plane files that were grep-scanned rather than re-read.

*Recommendation:* If an exhaustive denominator is required, commission a second bounded sweep of those areas; the present result should not be described as exhaustive.

### AUD-D08 — Nothing is independently accepted

All five governed rules are builder-integrated; the program's own accounting (m2/01-migration-backlog.md) states 0 accepted. V09 independent Tier 1 qualification is open and Ed25519 #26/#34 are security-held. Builder CI and AI review do not establish acceptance.

*Recommendation:* Keep acceptance percentages at 0% until an independent Tier 1 qualifier is designated and passes the integrated path.

## 1b. DR-CP-AGE-1 and AD-07 decision reconciliation (pass 2, Worker C; no decision is reversed here)

**What DR-CP-AGE-1 prohibits:**

- Clamping, coercing, defaulting or replacing any age value; non-exact-int, bool, float, str, None, zero or negative registry input, and anything above 2147483647 (Decision 1, lines 19).
- Letting a Registry value widen: effective = min(caller, registry); a Registry value above the caller is a no-op (Decision 2, line 20).
- Replacing an invalid caller value with the registry value (line 20).
- Reading AGE_MAX as an operational freshness setting or safety certificate (Decision 3, line 21; line 40).
- Registry values replacing, relaxing or widening any component-owned bound (Obligations 2-3, lines 45-46; Amendment 1 s2 rule 6, A:62).
- Implementing the freshness-profile outage-extension composition in this decision; it belongs to the later host factory EXT-S3-4 (Decision 5, line 23).
- Nothing in DR-CP-AGE-1 expressly forbids Registry governance of identity_max_age_seconds, mandate_max_age_seconds or clock_tolerance_seconds; it declares them out of scope (line 8).

**What it permits:**

- Registry-managed domain 1..2147483647 strict int for status_max_age_seconds, approval_max_age_seconds, ActionClass.max_status_age_seconds (line 8, 12, 15).
- Caller domain 0..2147483647; caller 0 stays 0 (line 13, 20).
- A Registry-hosted canonical V1 age table without a Control Plane mirror (line 3, 5; Batch 6 ruling 4.2 as reported).
- Control Plane consumption is neither authorized nor barred by the text: line 22 says the decision 'validates and composes the registry side only' and CP 'must enforce corresponding bounds through its established S3 implementation' (line 5).

| Field | Rule | Registry slot | Decision status | Touched by PR #58/#87 | Conflict | Needs reversal | Could proceed without reversal |
|---|---|---|---|---|---|---|---|
| status_max_age_seconds | RG-C-003 | yes: F4 f4-control-plane-age-bounds (r08-v2), merged | AUTHORIZED at Registry level: r08-v2 + Amendment 1 s2 (A:49-55) + DR-CP-AGE-1 (ACCEPTED, Batch 3 + Batch 6 4.2); V1 Option B and F4 age fields accept… | PR87 consumes via verify_and_decide_v2 (registry_freshness_narrowing.py:111-124); PR58 none | No conflict with DR-CP-AGE-1 text: min(caller,registry) at :117 and :123, registry domain 1..MAX preserved (test_m11 line 134 refuses 0). Adjacent tensions: (a) SCALAR_MAX=2147483647 hard-coded in CP… | no (DR-CP-AGE-1 not reversed) | yes as a decision-conflict matter, if split from tolerance; still needs explicit Architect M11 authorization (PR59 handoff s9.1), ruling on plan v1.5:13 deferral, AD-11 and 6.E |
| approval_max_age_seconds | RG-C-004 | yes: F4 (same family, same record) | same as RG-C-003 | PR87 :111-124 (same call, inseparable from status in one F4 record) | Same as RG-C-003; no DR conflict. | no | yes, same conditions as RG-C-003 |
| identity_max_age_seconds, mandate_max_age_seconds | RG-C-005 | no: F4 closed to two keys (v2_age_bounds.py:6) | OUT OF SCOPE by DR-CP-AGE-1:8 and Amendment 1 s2 rule 7 (A:63); G0 rated CONDITIONAL needing a Registry contract change (g0 ledger RG-C-005). Not aut… | none (PR87 docstring :10 says they stay host-owned; PR59 handoff :32 same) | none | n/a (untouched); any future migration requires an explicit Architect scope ruling plus F4 contract change | n/a: remain host-owned |
| clock_tolerance_seconds | RG-C-006 | no on main; PR58 adds new r08-v5 family f4t-control-plane-clock-tolerance (unmerged) | NOT authorized. Out of scope (R:8, A:63); behaviour 'untouched and host-owned' (R:22). PR59 handoff 6.B itself says 'Needs Architect adoption or chan… | PR58: v5_f4t.py:26-31,90-91, docs/r08-v5-contract.md:7,11,15; PR87: :9,:126-139; PR59: H:32,38,50 | Not a violation of an express prohibition; a scope breach. (1) PR58 contract s1 line 7 and v5_f4t.py:10-12 take the field DR-CP-AGE-1:8 / A:63 declare out of scope and create Registry-governed config… | YES (explicit Architect ruling): adopting the field, its domain and its basis amends the scope exclusions in DR-CP-AGE-1:8,:22 and Amendment 1 s2 rule 7; treat as reversal of those exclusions for this field | no for PR58; PR87 tolerance branch no; PR87 ages-only branch and PR59 docs yes (see matrix rows 1-2 and findings) |
| class_status_max_age_seconds (ActionClass.max_status_age_seconds) | RG-C-008 | yes: F5 f5-action-class-age-bounds (r08-v2), merged | AUTHORIZED at Registry level: DR-CP-AGE-1:8,12; Amendment 1 s2; V1 Option B F5 class status age (account memory 2026-10-25). CP consumption is M12, n… | none (PR87 module has no F5 or freshness-profile handling) | none from M11. Note DR Decision 5 (R:23): outage-extension composition deferred to EXT-S3-4; PR87 builds the workflow from **workflow_kwargs (:143-156) without composing extension limits; if a host p… | no | n/a for M11; M12 separate |
| evidence-obligation ages; ObservationPolicy.max_age_seconds / clock_tolerance_seconds | RG-F4-OBSERVATION-POLICY (and evidence ages) | no | evidence-obligation ages: host-owned, never registry-managed (R:8). ObservationPolicy (bounded.py:411-415) is stated not an F4/F5 field (R:13); G0 CO… | none (G0 ledger RG-C-006 notes it is NOT the ObservationPolicy tolerance) | none | n/a | n/a |

**AD-07.** AD-07 | May the Registry ever carry `max_amount`, `max_effects`, `allowed_target_prefixes`, `target_match`, given Amendment 3 records them as caller-owned residuals? | A/B/C | OPEN  (docs/family-migration/g0/unresolved-decisions.md:58; same OPEN in g1-preparation/g0-freeze-record.md:62 and open-decisions-and-prerequisites.md:32; backlog g0/migration-backlog.md:65,80 'Blocking decisions: AD-07 (open)').

Superseded in substance: YES in substance for all four fields (Registry may carry them, narrow-only, caller value remains the ceiling so Amendment 3 caller-ownership is preserved), evidenced by merged r08-v3/r08-v4 and Runtime enforcement. NO in form: the register row still reads OPEN, no ratification document is in the repository, and M3 authorization text is unverified by this worker.

Recommended additive correction (a new dated decision file; the old row and the frozen G0 records are not edited): Add a new dated file (e.g. docs/decisions/2026-10-28-ad-07-disposition-addendum.md); do not edit g0/unresolved-decisions.md or the frozen G0 or G1 records. Content: (1) quote AD-07 verbatim with its original OPEN status and location; (2) record 'Disposition: ANSWERED, option A (yes, narrow-only: effective = min(caller, registry) / sound accepted-set containment for target pair; caller value is the ceiling; absent or invalid Registry input never adds permission)'; (3) cite Architect M2 directive (date 2026-10-27, text to be supplied by the Architect), M3 approval (date/text to be supplied), Registry PRs #54 #56, Runtime #151-#153, backlog m2/01:75; (4) state it answers AD-07 only, does not accept M2/M3 (independent Tier 1 acceptance still required) and does not change Amendment 3; (5) state it does not extend to any other field. Mark ratification by the Architect; the builder or auditor must not self-ratify.

**Minimum Architect rulings** (from Worker C; recommendations are the worker's, adopted by the lead where stated in `pass2_resolutions`):

- **AR-1** Is clock_tolerance_seconds (RG-C-006) to become Registry-governed, which amends the scope exclusions in DR-CP-AGE-1 lines 8 and 22 and Amendment 1 s2 rule 7? If yes, under which new decision record (not an edit of DR-CP-AGE-1)? Options: A: No. Remain host-owned; close or park Registry PR #58 and drop the tolerance branch of CP PR #87. B: Yes, adopt as a new narrow-only F4T family via a new decision record that explicitly scopes it, names its owner and domain. C: Defer until atomicity (handoff 6.A) and revocation (6.E) are ruled. *Recommendation:* C now, B only after a new scoped decision. Narrowing is sound (all uses fail closed when smaller) so B is eligible in principle, but nothing adopts the field today and PR59 6.B already says it needs adoption. Keep PR #58 unmerged until AR-1 and AR-2 are answered.
- **AR-2** If AR-1 is B: what registry domain and basis for the tolerance (PR58 proposes 0..2147483647 reusing the age ceiling)? Options: A: 0..2147483647 as a technical representation ceiling, with a new probe measuring this scalar (the DR-CP-AGE-1 measurement covered the class base only). B: A lower operational cap (e.g. a small seconds ceiling) set by the Architect, since tolerance of years has no operational meaning. C: Registry domain 1..MAX like ages. *Recommendation:* B or A with a fresh probe; do not rely on DR-CP-AGE-1 for the tolerance ceiling. Correct v5_f4t.py:10-12 wording either way.
- **AR-3** May a Control Plane consumer of the existing F4 ages (RG-C-003/004) proceed as a stand-alone, tolerance-free adapter, given plan v1.5:13 defers F4/F5 and CP EXT-S3-1..3 absent an operator-approved amendment, AD-11 is OPEN, and handoff 6.E (no revocation observation) is unresolved? Also: does the Architect acknowledge the DR-CP-AGE-1 Decision 7 availability trade-off now realised in CP (PR87:87)? Options: A: Authorize ages-only PR-2 after 6.E ruling. B: Hold all CP consumption until AD-11, 6.A, 6.E, 6.C are closed. C: Authorize with a documented requirement that the adapter also compose freshness-profile extensions (EXT-S3-4). *Recommendation:* A conditional on 6.E and AD-11 rulings; split tolerance out of PR #87. This needs no reversal of DR-CP-AGE-1.
- **AR-4** Confirm identity_max_age_seconds and mandate_max_age_seconds (RG-C-005) stay host-owned and out of the Registry for this program. Options: A: Confirm retained host-owned (no action). B: Open a scoped decision to add them to F4 via a successor contract. *Recommendation:* A. No benefit evidenced; both would need a Registry contract change and an AD-11-style mapping.
- **AR-5** Ratify the disposition of AD-07 as answered by the merged M2/M3 narrowing, via an additive addendum. Options: A: Ratify as option A (narrow-only) with the addendum described under ad07. B: Direct a revert or further restriction. *Recommendation:* A. Architect supplies the M2 and M3 ruling texts and dates; no code change.
- **AR-6** Counting rule: may RG-C-006 be counted as implemented in the progress ledger (PR59 H:38, m2 backlog appended text) before AR-1/AR-2? Options: A: No, show M11 as 2 groups implemented plus 1 pending ruling. B: Yes. *Recommendation:* A.

Limits: Batch 3, Batch 4, Batch 6 ruling texts, the M2/M3/M11 Architect authorization texts and Project docs (claude/*) are NOT in the repo and were not readable by this worker; account memory records M2 PR-1 authorization (2026-10-27) and V1 Option B (2026-10-25) only, nothing for M3 or M11 authorization. PR #87 tests not run (brief forbids); CP code read from the ref only. AD-07 supersession is inferred from merged code and Architect-approved notes, not from a recorded ruling. Whether the Architect already authorized M11 (including tolerance) outside the repository is unknown to this worker; if such a ruling exists, AR-1/AR-3 may already be answered and the conflict reduces to documentation. Grammar of R:8 parenthetical read two ways; the stricter reading (all four are host-owned and never registry-managed) would make PR58 a direct conflict; this worker took the narrower, text-faithful reading and flagged it. Confidence: medium-high on quoted text and PR line evidence; medium on AD-07 substance (memory-sourced for M2, inferred for M3).

## 2. Blocking decisions attached to individual rules

| Rule | Disposition | Blocking question |
|---|---|---|
| LR-F5-CLASS-STATUS-AGE | REGISTRY-ELIGIBLE | How does a Registry-narrowed class value enter approval_commitment and the approval-side age_ceilings check, given profile.model_dump is the preimage? |
| NEW:terminal-revocation-marker | REGISTRY-ELIGIBLE | How does a Registry-forced profile section enter the approval commitment (the AUD-D06 question shared with RG-C-010)? |
| RG-C-005 | BLOCKED | Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'out of scope and not covered'; it does not expressly prohibit them, but noth… |
| RG-C-005 | BLOCKED | Is the omission of identity/mandate ages from F4 (DR-CP-AGE-1) a deliberate exclusion or a gap awaiting a new slot? |
| RG-C-006 | BLOCKED | Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'out of scope and not covered'; it does not expressly prohibit them, but noth… |
| RG-C-009 | REGISTRY-ELIGIBLE | As RG-C-008: how a narrowed class enum enters the approval commitment. |
| RG-C-010 | REGISTRY-ELIGIBLE | Is a Registry-forced 'requires_revocation_assurance' meaningful when it holds the class until the host supplies a holder inventory (self-inflicted denial), and does it need profile-commitment handling? |
| RG-C-024 | UNRESOLVED | Is a host principal allow-list (funded merge authorities) a Registry-narrowable allow-set like F1a, given principal identity namespace and merge profile are host-owned and opt-in? |
| RG-D-025 | UNRESOLVED | Do wording/claim scanner term lists belong to the hub declarative-governance registry (OCS-DGR-ARCH) or to cognous-ocs-registry, and is lint-only wording in scope of this program? |

## 3. Observations that are not migration defects

Recorded for the Architect; none concerns an active migration and none was escalated as a material safety defect.

- Control Plane bounded.py:2085-2087 caps the `_mono_open` map at 4096 entries with FIFO eviction; eviction drops the secondary monotonic-clock guard (bounded.py:1426) for the oldest open check, while the wall-clock deadline (bounded.py:1421-1432) still applies (worker B).
- Control Plane cli_run.py:511 `allow_test_time=now is not None` lets the `--now` flag set the evaluation clock; the CLI flags it as a test override under a synthetic resolver (worker B).
- Runtime engine/local_authority_effect.py:631-645 `remove_authoritative_state` deletes authority state with no revocation record or authorization; its only callers are tests (worker H1; matches G0 finding G0-B-029).
- Runtime engine/local_authority_effect.py `_selection_guard` is opt-in by design: a claim with no binding and no configured store follows the legacy path unchanged, but a binding or an existing store with no verifiable authority refuses (store_unknown) and a successor claim without its binding refuses. Lead read of lines 815-831.
- evidence-registry app/core/config.py:28 holds a default JWT secret_key; create_access_token/verify_token have no callers, so it is not exposed today (worker I2). The module is a non-authoritative demo.
- Stack Orchestrator observer.py:91 defaults confirmations to 0 and observer.py:120-126 accepts http:// and userinfo URLs; its hard-coded upstream pins (admission.py:102-118, producer_evidence.py:10-11) are stale against the current hub lock. Documented, labelled historical (worker I3).
- Control Plane replay.py from_json uses non-strict json.loads for a fixed-format export (worker F2); not a defect.
- RG-B-016, RG-D-014 and RG-D-015 are OUT-OF-SCOPE on the strength of README and docstring labels ('experimental', 'no executor imports this module'); like RG-D-022, designating any of them production would reopen the question (pass 2, Worker H U-07).
- Worker F recorded a lockstep note: replay-bundle recovery_inspection.py:172 (0..86400 cap) mirrors RG-B-016, and uncounted members restart_quorum (RG-D-022 family) and governance_quadratic_scaling (evidence-registry quorum family); all non-manageable. The hub collateral_evidence_snapshot.py:73-84 claim-scanner vocabulary is not catalogued as its own rule.
