# G0 migration backlog (proposal; M1–M13 sequence unchanged)

G0: AUTHORIZED. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

This backlog maps eligible families onto the approved M1–M13 sequence. **Nothing here starts a wave.** The order is not redesigned; where source contradicts a plan premise the conflict is stated (family-eligibility-matrix.md section 3). Ten fields are given per wave: source ownership, Registry contract/version, evaluator integration, Control Plane/Runtime dependencies, authorization semantics, non-widening proof, tests (positive/negative/differential), independent qualification, proposed PR sequence, blocking decisions.

## Recommended first implementation increment (after Architect authorization)

**M1 re-scoped as negative-oracle closure for institutions and authority domains.** It needs no contract change, no source change in Runtime or Control Plane, and it builds the differential harness that M2, M3, M11 and M12 reuse. Everything else needs the contract-path decision AD-03 (new narrowing-only family id under r08-v2 vs r08-v3) first. This is a recommendation only; G1 is not authorized.

## Summary

| Wave | Family | G0 finding | Records |
|---|---|---|---|
| M1 | F1b allow-set completion (institutions, authority domains) | ALREADY-GOVERNED; evidence gap | A-002, B-010, B-012 |
| M2 | F1c numeric ceilings (max_amount, max_effects) | ELIGIBLE-NOT-MIGRATED (conditional) | A-003, A-004, B-007, B-008, D-001 |
| M3 | F1d target configuration | ELIGIBLE-NOT-MIGRATED (conditional) | A-005, A-006, B-004, B-006, D-002 |
| M4 | F6 agent permissions | OUT-OF-SCOPE (Runtime) / UNRESOLVED (action-manifest) | B-014, D-008 |
| M5 | F7 dedupe/replay TTL | OUT-OF-SCOPE / UNRESOLVED | B-015, C-022 |
| M6 | F3 budgets | RETAIN-IN-CODE (floors); UNRESOLVED (residual) | B-001..B-003, B-027, C-040, D-006, D-024 |
| M7 | F9 tenant-ID length | RETAIN-IN-CODE | B-003, C-035, C-036, D-004 |
| M8 | F10 diagnostic thresholds | ELIGIBLE-NOT-MIGRATED (low priority) | C-037 |
| M9 | F8 demo lists | OUT-OF-SCOPE / RETAIN-IN-CODE | C-025..C-030 |
| M10 | F11 redaction defaults | ELIGIBLE-NOT-MIGRATED (conditional) | C-038, D-007, D-012 |
| M11 | F4 freshness | PARTLY ALREADY-GOVERNED; remainder ELIGIBLE-NOT-MIGRATED | A-007, A-009, C-001..C-006, C-019, C-020, B-016, D-011 |
| M12 | F5 authority-profile declarations | PARTLY ALREADY-GOVERNED; remainder ELIGIBLE-NOT-MIGRATED | A-008, C-008..C-011, C-021, C-031 |
| M13 | Delta and residual closure | Closure item | S02 §3a rows W8-041, W8-042, W8-068, W8-072; the 32 UNRESOLVED rows |

## M1 — F1b allow-set completion (institutions, authority domains)

G0 finding: **ALREADY-GOVERNED; evidence gap**. Records: A-002, B-010, B-012.

- **Source ownership:** Registry owns the f1ab record (`registry_successor/v2_f1ab.py`, `families.py`); Runtime owns the policy fields and the effect-time guard (`registry_selection_authority.check_effect`).
- **Registry contract / version:** No change: existing r08-v2 `f1ab-local-execution-allowlist`. The plan premise ('carried unchanged') is contradicted by source.
- **Evaluator integration:** No change. `LocalExecutionPolicy.check` (protected evaluator) and the narrowing adapter already handle all five sets.
- **Control Plane / Runtime dependencies:** None for source. Optional Runtime/Stack Qualification differential against the baseline `LocalExecutionPolicy` for the two sets (S05 equivalence was 3-set).
- **Authorization semantics:** Unchanged: Registry narrows; absence is `field_missing`; deny-all is an explicit `[]`.
- **Non-widening proof:** Existing: intersection ⊆ caller and ⊆ Registry. To add: exhaustive small-grid and subset property for the two sets; effect-time subset test on the two sets.
- **Tests (positive / negative / differential):** Positive: narrowing of institutions. Negative: disjoint set → `applied_deny_all` naming the two fields; NFC/NFD and case-fold; decision-level selection crossing `scope.institution`/`scope.authority_domain`. Differential: five-set composed policy vs baseline policy. Missing today: all of these exist only for `allowed_units`.
- **Independent qualification:** Tier 1 subject: independent qualification required before acceptance, as for V08. Builder tests are not independent.
- **Proposed PR sequence:** PR-1 Registry tests-only closure; PR-2 optional Stack Qualification differential; no contract PR.
- **Blocking decisions:** AD-01 (reclassify M1 as evidence closure), AD-06 (equality vs subset for the two sets).

## M2 — F1c numeric ceilings (max_amount, max_effects)

G0 finding: **ELIGIBLE-NOT-MIGRATED (conditional)**. Records: A-003, A-004, B-007, B-008, D-001.

- **Source ownership:** Caller owns the ceilings today (Runtime `LocalExecutionPolicy`; action-manifest per-action ceiling). A Registry family would carry a narrowing ceiling only.
- **Registry contract / version:** New narrowing-only family (new family id under r08-v2, registered in both `FAMILIES_V2` and `IDENTITY_FAMILIES`) or r08-v3. The frozen contract states 'no max_amount slot'; Amendment 3 lists them as caller-owned residuals.
- **Evaluator integration:** Runtime guard extended to compare Registry ceiling ≥ effective ceiling inside the same atomic transaction; `safe_executor.py` evaluator unchanged.
- **Control Plane / Runtime dependencies:** Runtime: adapter + guard + selection store identity. Control Plane: canonical policy binding / authorization-pin export carry a new family identity. Action-manifest authored ceilings stay caller data.
- **Authorization semantics:** effective = min(caller, Registry); absent/unknown/corrupt record → existing refusal/HOLD, never a higher value. Numeric domain must be fixed first (int or finite float ≥ 0, magnitude ≤ 2^53).
- **Non-widening proof:** Property: effective ≤ caller and ≤ Registry for all values incl. boundary equality, 2^53, float/int mix; guard refuses any effective value above the record.
- **Tests (positive / negative / differential):** Positive: lower Registry ceiling applies. Negative: Registry above caller never raises; boundary equality; non-finite; NaN; bool-as-int. Differential: baseline policy with the ceiling set equal to the Registry value. Missing: no test names `test_amount_exactly_at_max_is_allowed` in the current Runtime tests (equivalents cited).
- **Independent qualification:** Tier 1 (admission to an effect): independent qualification required.
- **Proposed PR sequence:** PR-1 contract decision record/amendment; PR-2 Registry family + vectors; PR-3 Runtime adapter/guard; PR-4 Control Plane binding; PR-5 Stack Qualification differential; independent review.
- **Blocking decisions:** AD-03 (contract path), AD-07 (may the Registry ever carry these), numeric domain ruling.

## M3 — F1d target configuration

G0 finding: **ELIGIBLE-NOT-MIGRATED (conditional)**. Records: A-005, A-006, B-004, B-006, D-002.

- **Source ownership:** Caller owns prefixes and the mode choice. The mode vocabulary and separators (F2) stay in `safe_executor.py`.
- **Registry contract / version:** As M2. Prefix order relation (subset of prefixes vs prefix-extension) is non-trivial; mode narrowing order is not proven in source.
- **Evaluator integration:** Evaluator unchanged; only the effective policy values are narrowed. Segment-aware matching remains code.
- **Control Plane / Runtime dependencies:** Runtime guard and Control Plane binding as M2. Action-manifest `allowed_targets`/`allow_any_target` are a second authored home.
- **Authorization semantics:** Narrowing only; an unknown mode or malformed prefix refuses; a record can never turn `exact` into `legacy-prefix`.
- **Non-widening proof:** Define a partial order on (mode, prefix set) and prove effective ≤ both operands, including dot-segment and separator edge cases.
- **Tests (positive / negative / differential):** Existing S01 suite covers target modes and well-formedness (names `test_default_target_match_is_segment_aware_*` etc. NOT FOUND in the current Runtime tests; equivalents cited). Add disjoint/overlapping prefix negatives and mode-widening negatives.
- **Independent qualification:** Tier 1: independent qualification required.
- **Proposed PR sequence:** After M2 contract decision: Registry family PR, Runtime PR, Control Plane PR, qualification PR.
- **Blocking decisions:** AD-03, AD-07, order-relation ruling for prefixes and modes.

## M4 — F6 agent permissions

G0 finding: **OUT-OF-SCOPE (Runtime) / UNRESOLVED (action-manifest)**. Records: B-014, D-008.

- **Source ownership:** Runtime `permissions.json` is a legacy sample data file. The action-manifest `authority_required`/`tools.allowed` declarations are the live authored home.
- **Registry contract / version:** N/A: no implementation is proposed for this wave on current evidence.
- **Evaluator integration:** Control Plane re-declares its own checks and does not import the manifest.
- **Control Plane / Runtime dependencies:** Both sides would need to change for a Registry narrowing (CD-10).
- **Authorization semantics:** N/A: no implementation is proposed for this wave on current evidence.
- **Non-widening proof:** N/A: no implementation is proposed for this wave on current evidence.
- **Tests (positive / negative / differential):** N/A: no implementation is proposed for this wave on current evidence.
- **Independent qualification:** N/A: no implementation is proposed for this wave on current evidence.
- **Proposed PR sequence:** N/A: no implementation is proposed for this wave on current evidence.
- **Blocking decisions:** AD-10 (confirm F6 scope), AD-19 (are non-core repositories in scope).

## M5 — F7 dedupe/replay TTL

G0 finding: **OUT-OF-SCOPE / UNRESOLVED**. Records: B-015, C-022.

- **Source ownership:** Runtime TTL models a provider horizon; Control Plane `DedupeProfile` has three required ints with an invariant.
- **Registry contract / version:** N/A: no implementation is proposed for this wave on current evidence.
- **Evaluator integration:** N/A: no implementation is proposed for this wave on current evidence.
- **Control Plane / Runtime dependencies:** N/A: no implementation is proposed for this wave on current evidence.
- **Authorization semantics:** N/A: no implementation is proposed for this wave on current evidence.
- **Non-widening proof:** N/A: no implementation is proposed for this wave on current evidence.
- **Tests (positive / negative / differential):** N/A: no implementation is proposed for this wave on current evidence.
- **Independent qualification:** N/A: no implementation is proposed for this wave on current evidence.
- **Proposed PR sequence:** N/A: no implementation is proposed for this wave on current evidence.
- **Blocking decisions:** AD-13 (policy or provider fact).

## M6 — F3 budgets

G0 finding: **RETAIN-IN-CODE (floors); UNRESOLVED (residual)**. Records: B-001..B-003, B-027, C-040, D-006, D-024.

- **Source ownership:** Admission and parsing floors are mandatory and stay in code. The residual host-owned budgets (OpenShell timeout 1..30, CLI input cap, manifest cap, bounded-json defaults) have no authority effect.
- **Registry contract / version:** N/A: no implementation is proposed for this wave on current evidence.
- **Evaluator integration:** Floors are in the protected evaluator path.
- **Control Plane / Runtime dependencies:** N/A: no implementation is proposed for this wave on current evidence.
- **Authorization semantics:** A budget may only be lowered, never raised above the floor.
- **Non-widening proof:** N/A: no implementation is proposed for this wave on current evidence.
- **Tests (positive / negative / differential):** N/A: no implementation is proposed for this wave on current evidence.
- **Independent qualification:** N/A: no implementation is proposed for this wave on current evidence.
- **Proposed PR sequence:** N/A: no implementation is proposed for this wave on current evidence.
- **Blocking decisions:** AD-08 (floors stay floors), AD-09 (low-risk lowering candidates), scope: should the Registry carry resource budgets at all.

## M7 — F9 tenant-ID length

G0 finding: **RETAIN-IN-CODE**. Records: B-003, C-035, C-036, D-004.

- **Source ownership:** The 128 bound is repeated at 8 sites in 3 repositories with no shared source; the canonical binding additionally restricts the pattern.
- **Registry contract / version:** N/A: no implementation is proposed for this wave on current evidence.
- **Evaluator integration:** N/A: no implementation is proposed for this wave on current evidence.
- **Control Plane / Runtime dependencies:** A narrowing config would desynchronize sites and could make valid tenants unrepresentable.
- **Authorization semantics:** N/A: no implementation is proposed for this wave on current evidence.
- **Non-widening proof:** N/A: no implementation is proposed for this wave on current evidence.
- **Tests (positive / negative / differential):** N/A: no implementation is proposed for this wave on current evidence.
- **Independent qualification:** N/A: no implementation is proposed for this wave on current evidence.
- **Proposed PR sequence:** N/A: no implementation is proposed for this wave on current evidence.
- **Blocking decisions:** AD-18.

## M8 — F10 diagnostic thresholds

G0 finding: **ELIGIBLE-NOT-MIGRATED (low priority)**. Records: C-037.

- **Source ownership:** Control Plane `reason_vocabulary` keyword defaults (5, 1); non-gating report.
- **Registry contract / version:** A Registry diagnostic profile with no authority semantics, if wanted.
- **Evaluator integration:** Report generator reads the value; no gate.
- **Control Plane / Runtime dependencies:** Control Plane only.
- **Authorization semantics:** No authority semantics: a change alters a report, never an effect.
- **Non-widening proof:** A value change cannot alter any gate outcome (no consumer influences an authority decision).
- **Tests (positive / negative / differential):** Positive/negative threshold behaviour; differential vs literal defaults. `test_rule_revision.py:118-120` (by name).
- **Independent qualification:** Not required if Tier 3 is ratified; otherwise Tier 2 review.
- **Proposed PR sequence:** One Registry family PR + one Control Plane PR.
- **Blocking decisions:** AD-23 (tier ruling).

## M9 — F8 demo lists

G0 finding: **OUT-OF-SCOPE / RETAIN-IN-CODE**. Records: C-025..C-030.

- **Source ownership:** Demo-only defaults; helpers that grant read/write authority; the legacy `PolicyGate` evaluator.
- **Registry contract / version:** N/A: no implementation is proposed for this wave on current evidence.
- **Evaluator integration:** N/A: no implementation is proposed for this wave on current evidence.
- **Control Plane / Runtime dependencies:** N/A: no implementation is proposed for this wave on current evidence.
- **Authorization semantics:** Demo grants confer authority and are not tunables.
- **Non-widening proof:** N/A: no implementation is proposed for this wave on current evidence.
- **Tests (positive / negative / differential):** N/A: no implementation is proposed for this wave on current evidence.
- **Independent qualification:** N/A: no implementation is proposed for this wave on current evidence.
- **Proposed PR sequence:** N/A: no implementation is proposed for this wave on current evidence.
- **Blocking decisions:** AD-12 (retire or guard inert `policy_config.default_action` and demo helpers).

## M10 — F11 redaction defaults

G0 finding: **ELIGIBLE-NOT-MIGRATED (conditional)**. Records: C-038, D-007, D-012.

- **Source ownership:** Defaults in action-manifest (`[REDACTED]`), replay-bundle keyword defaults and the Control Plane `RedactionConfig`; the redaction mechanism and truncation stay in code.
- **Registry contract / version:** New narrowing-only family where narrowing means *more* redaction.
- **Evaluator integration:** Redaction mechanism (`redaction.py`) unchanged.
- **Control Plane / Runtime dependencies:** Action-manifest, replay-bundle and Control Plane keep separate copies today (CD-06).
- **Authorization semantics:** A record may only add redaction; it can never turn payload redaction off.
- **Non-widening proof:** Effective redaction set ⊇ code default set for every input.
- **Tests (positive / negative / differential):** Negative: attempt to disable payload redaction or fingerprint blanking must refuse.
- **Independent qualification:** Confidentiality controls are treated as Tier 1 until reviewed (S02 section 3).
- **Proposed PR sequence:** Registry family PR, per-component consumer PRs.
- **Blocking decisions:** AD-03, AD-19.

## M11 — F4 freshness

G0 finding: **PARTLY ALREADY-GOVERNED; remainder ELIGIBLE-NOT-MIGRATED**. Records: A-007, A-009, C-001..C-006, C-019, C-020, B-016, D-011.

- **Source ownership:** Registry f4 already carries `status_max_age_seconds` and `approval_max_age_seconds`. Control Plane constructor defaults (60/60/60/60/5), the observation policy (300/5 literal in `acp run`) and the Runtime recovery window (86400) are uncovered.
- **Registry contract / version:** Extend by a new family id or r08-v3; f4 is a closed two-int record.
- **Evaluator integration:** `bounded._fresh` and `_reconcile_observation` unchanged; values narrowed at construction.
- **Control Plane / Runtime dependencies:** Mapping ruling: under a runtime-authority profile the class bound replaces the global status bound only for grant status (conflict and policy status keep the ctor bound). 60 and 300 govern different decisions; nothing relates them.
- **Authorization semantics:** min(host, Registry); a Registry age can only shorten the window; absent record keeps the host value.
- **Non-widening proof:** Property: accepted age ≤ min of both operands; clock tolerance cannot exceed the host value.
- **Tests (positive / negative / differential):** Existing: `test_bounded_authorization.py`, `test_freshness.py` (by name). Add decision-time and effect-time differential, and the 60-vs-300 independence test.
- **Independent qualification:** Tier 1: independent qualification required.
- **Proposed PR sequence:** Registry family PR, Control Plane PR, Runtime PR (recovery window), qualification PR.
- **Blocking decisions:** AD-02, AD-03, AD-11.

## M12 — F5 authority-profile declarations

G0 finding: **PARTLY ALREADY-GOVERNED; remainder ELIGIBLE-NOT-MIGRATED**. Records: A-008, C-008..C-011, C-021, C-031.

- **Source ownership:** Registry f5 carries the class→age map; policy-binding/0.1 already carries host ceilings. `on_unreadable`, revocation assurance, reversibility and class declarations remain host profile values.
- **Registry contract / version:** New family id or r08-v3.
- **Evaluator integration:** `validate_extensions` (protected) unchanged.
- **Control Plane / Runtime dependencies:** Trust anchors (producer keys, catalogue, signer sets) are never externalized.
- **Authorization semantics:** Only stricter directions: `refuse` over `bounded_tolerance`; longer assurance never allowed.
- **Non-widening proof:** Order relation per field (enum strictness order) with refusal on unknown values.
- **Tests (positive / negative / differential):** `test_runtime_authority.py`, `test_reversibility.py` (by name). Add per-field narrowing negatives; note UNKNOWN_BEHAVIORS has one gate branch.
- **Independent qualification:** Tier 1: independent qualification required.
- **Proposed PR sequence:** After M11 contract decision.
- **Blocking decisions:** AD-02, AD-03.

## M13 — Delta and residual closure

G0 finding: **Closure item**. Records: S02 §3a rows W8-041, W8-042, W8-068, W8-072; the 32 UNRESOLVED rows.

- **Source ownership:** Lead and Architect.
- **Registry contract / version:** None.
- **Evaluator integration:** None.
- **Control Plane / Runtime dependencies:** Importer pins, verifier reasons registry and hub component lock lag the current mains (AD-16, AD-17).
- **Authorization semantics:** None.
- **Non-widening proof:** None.
- **Tests (positive / negative / differential):** Integrity tests of this G0 package.
- **Independent qualification:** Not applicable.
- **Proposed PR sequence:** Per ratified resolution; no source changes in G0.
- **Blocking decisions:** All AD entries; see `unresolved-decisions.md`.
