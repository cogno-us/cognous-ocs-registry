# Unresolved architectural decisions

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

## 1. Decisions raised by the lead

### AUD-D01 — AD-07 is still recorded OPEN, but Registry narrowing of max_amount, max_effects, target prefixes and target_match is merged

The frozen G0 decision register (docs/family-migration/g0/unresolved-decisions.md, AD-07) asks whether the Registry may ever carry these four fields, given Amendment 3 records them as caller-owned residuals, and lists it OPEN. Registry PRs #54 (r08-v3, merge ba98dd26) and #56 (r08-v4, merge b7e6a173) and Runtime PRs #151, #152 and #153 (merge f7a55e2a) implement exactly that narrowing, and the M2 record treats it as authorized. This audit found no later repository record that closes AD-07, so the register and the merged code disagree. It is a governance-record inconsistency, not a safety defect: the Runtime narrowing adapter was read and enforces subset-of-caller sets and ceilings no higher than the caller's.

*Recommendation:* The Architect records an explicit disposition for AD-07 (ratify the merged M2/M3 narrowing, or direct a revert) so the register matches the code.

### AUD-D02 — Counting rule: represented in the Registry is not governed

G0 labelled RG-A-007, RG-A-008 (and, in the audit's view, RG-C-021) ALREADY-GOVERNED. The Registry composes the F4 status/approval scalars and the F5 per-class map (registry_successor/v2_age_bounds.py), but the Control Plane imports no Registry code and enforces only host-supplied values; policy_binding.py enforces a host-copied age_ceilings. Three facts are therefore kept separate throughout this audit: represented in the Registry, integrated at an enforcement boundary, independently accepted. Only rules with the first two are REGISTRY-GOVERNED.

*Recommendation:* Adopt the three-layer definition for backlog and PASS accounting; carry the F4/F5 age rules as eligible with the Registry half represented until the Control Plane consumer (waves M11/M12) is merged.

### AUD-D03 — RG-C-018 (freshness nonce toggle) is marginal

FreshnessProfile.nonce (default True) is host-settable. A Registry overlay could only force True, structurally the same as RG-C-020 (anchor_deadline_to_inputs). Two first-pass workers disagreed: the group audit rated it REGISTRY-ELIGIBLE, the row-level configurable-candidate review rated the same field host-owned. The audit keeps it ELIGIBLE with the disagreement recorded because a forcing-True overlay is monotone and the consumer is the same Control Plane freshness profile as RG-C-019/RG-C-020; it adds little protection unless a host disables the nonce.

*Recommendation:* Decide whether to migrate it at all; if the Architect prefers not to migrate safeguards that default to the safe value, reclassify RETAIN-IN-CODE. The eligible count falls by one.

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

## 2. Blocking decisions attached to individual rules

| Rule | Disposition | Blocking question |
|---|---|---|
| LR-F5-CLASS-STATUS-AGE | REGISTRY-ELIGIBLE | How does a Registry-narrowed class value enter approval_commitment and the approval-side age_ceilings check, given profile.model_dump is the preimage? |
| LR-RUNTIME-ADMISSION-SIZE-BUDGETS | UNRESOLVED | May the Registry narrow Runtime structural admission budgets (depth, node/entry count, byte size)? They are Tier 1 admission guards that bound the canonicalization domain; a narrow-only override only rejects more, but the value is low and the ceiling must sta… |
| NEW:operation-identity-enablement | UNRESOLVED | Is enabling operation-identity a governed policy narrowing, or a host protocol-profile/wiring choice that must be set jointly in Runtime ctor, CP profile and destination capability (and be one-way)? |
| RG-C-005 | BLOCKED | DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) excludes identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as host-owned and never registry-managed. Narrowing them would be monotone, but needs an Architect reversal of that… |
| RG-C-005 | BLOCKED | Is the omission of identity/mandate ages from F4 (DR-CP-AGE-1) a deliberate exclusion or a gap awaiting a new slot? |
| RG-C-006 | BLOCKED | DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) excludes identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as host-owned and never registry-managed. Narrowing them would be monotone, but needs an Architect reversal of that… |
| RG-C-009 | REGISTRY-ELIGIBLE | As RG-C-008: how a narrowed class enum enters the approval commitment. |
| RG-C-010 | REGISTRY-ELIGIBLE | Is a Registry-forced 'requires_revocation_assurance' meaningful when it holds the class until the host supplies a holder inventory (self-inflicted denial), and does it need profile-commitment handling? |
| RG-C-024 | UNRESOLVED | Is a host principal allow-list (funded merge authorities) a Registry-narrowable allow-set like F1a, given principal identity namespace and merge profile are host-owned and opt-in? |
| RG-C-032 | UNRESOLVED | Who may add custom action types to the effectful/high-risk/privileged floor sets, and who authorises that classification? Built-in membership is a fixed floor. |
| RG-D-012 | UNRESOLVED | Same minimum-redaction-floor ownership question as RG-F11-REDACTION-DEFAULTS; the replay-bundle library has no Registry consumer. |
| RG-D-025 | UNRESOLVED | Do wording/claim scanner term lists belong to the hub declarative-governance registry (OCS-DGR-ARCH) or to cognous-ocs-registry, and is lint-only wording in scope of this program? |
| RG-D-027 | BLOCKED | Project-owner confirmation of the tier ceilings and a consuming enforcement boundary for delay_limit. |
| RG-F11-REDACTION-DEFAULTS | UNRESOLVED | Is a minimum-redaction floor a Registry-owned operator control (a new privacy feature, plan wave M10), and who is the privacy owner? |
| RG-F7-DEDUPE | UNRESOLVED | Are the Control Plane DedupeProfile escalation_deadline and key TTL host policy or provider-declared facts? (G0 C-022) |

## 3. Observations that are not migration defects

Recorded for the Architect; none concerns an active migration and none was escalated as a material safety defect.

- Control Plane bounded.py:2085-2087 caps the `_mono_open` map at 4096 entries with FIFO eviction; eviction drops the secondary monotonic-clock guard (bounded.py:1426) for the oldest open check, while the wall-clock deadline (bounded.py:1421-1432) still applies (worker B).
- Control Plane cli_run.py:511 `allow_test_time=now is not None` lets the `--now` flag set the evaluation clock; the CLI flags it as a test override under a synthetic resolver (worker B).
- Runtime engine/local_authority_effect.py:631-645 `remove_authoritative_state` deletes authority state with no revocation record or authorization; its only callers are tests (worker H1; matches G0 finding G0-B-029).
- Runtime engine/local_authority_effect.py `_selection_guard` is opt-in by design: a claim with no binding and no configured store follows the legacy path unchanged, but a binding or an existing store with no verifiable authority refuses (store_unknown) and a successor claim without its binding refuses. Lead read of lines 815-831.
- evidence-registry app/core/config.py:28 holds a default JWT secret_key; create_access_token/verify_token have no callers, so it is not exposed today (worker I2). The module is a non-authoritative demo.
- Stack Orchestrator observer.py:91 defaults confirmations to 0 and observer.py:120-126 accepts http:// and userinfo URLs; its hard-coded upstream pins (admission.py:102-118, producer_evidence.py:10-11) are stale against the current hub lock. Documented, labelled historical (worker I3).
- Control Plane replay.py from_json uses non-strict json.loads for a fixed-format export (worker F2); not a defect.
