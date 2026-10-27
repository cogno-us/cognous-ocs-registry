# G0 exit report — Registry family migration inventory reconciliation

Builder-side, non-authorizing. This report recommends; the Architect decides. G0: AUTHORIZED. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## 1. Result

**Recommendation: G0 PASS (inventory complete) with 24 named Architect decisions; G1 remains blocked on AD-01 and AD-03.** The recommendation depends on the verification in section 7. PASS here means the inventory is complete and source-backed within the stated limits; it does not mean any family is approved, qualified or ready.

## 2. Historical reconciliation (S02, 620 rows)

| Item | Count |
|---|---|
| Rows reconciled | 620 |
| CONFIGURABLE-CANDIDATE | 43 |
| INCIDENTAL-CONDITIONAL | 51 |
| MANDATORY-INVARIANT | 354 |
| REFUSAL-OR-REASON-VOCABULARY | 50 |
| SERIALIZATION-OR-EVIDENCE | 90 |
| UNRESOLVED | 32 |
| Crosswalk status: UNCHANGED | 482 |
| Crosswalk status: MOVED (line coordinates shifted; 31 of these are cumulative W8 coordinates with an unchanged file) | 124 |
| Crosswalk status: CHANGED (additive; class retained) | 14 |
| Crosswalk status: DELETED | 0 |
| Rows resolved by workers (43 candidates + 32 unresolved) | 75 |
| UNRESOLVED rows individually tracked | 32 |

Historical ids and classifications are copied unchanged. No row was silently reclassified: the 20 worker reclassification proposals are listed in `unresolved-decisions.md` and not applied. The four S02 §3a rows are dispositioned: W8-041 → G0-C-017 (RETAIN-IN-CODE; liveness reaper interval), W8-042 → G0-C-018 (RETAIN-IN-CODE; safeguard toggle), W8-068 → G0-C-014 (RETAIN-IN-CODE; host trust data), W8-072 → G0-C-015 (OUT-OF-SCOPE; labels).

## 3. Current candidate counts

Definitions: a *record* is one source site; a *rule group* is a unique rule (ten merges across components). Dispositions are proposals.

| Measure | Rule groups | Records |
|---|---|---|
| Current configurable candidates (ALREADY-GOVERNED + ELIGIBLE-NOT-MIGRATED + UNRESOLVED + BLOCKED) | 33 | 46 |
| Already Registry-governed | 5 | 10 |
| Eligible, not migrated | 23 | 30 |
| Retained in code | 56 | 60 |
| Out of scope | 8 | 10 |
| Unresolved | 4 | 5 |
| Blocked | 1 | 1 |
| Total | 97 | 116 |

Records by eligibility: {'CONDITIONAL': 36, 'ELIGIBLE': 5, 'NOT_ELIGIBLE': 69, 'UNRESOLVED': 6}. New families discovered: 20 (five with a non-retain disposition). 

## 4. The 60-versus-300 relationship

The 60 s value governs the age of **authority-input reads** (grant status, identity, mandate, approval, conflict, policy): `BoundedAuthorizationWorkflow.__init__` defaults (`bounded.py:1271-1275`), `_fresh` at decision and effect time. The 300 s value (with 5 s tolerance) governs the age of the **destination observation** used before first dispatch, after dispatch and in `reconcile()` (`cli_run.py:510`; `ObservationPolicy.max_age_seconds` has no default). Nothing in code compares or orders them; an observation may be older than an authority input is allowed to be. Two distinct 5 s clock tolerances exist. The Registry f4 record carries only the 60-type status and approval scalars. Lead spot-check: `cli_run.py:510` and `bounded.py:1271-1275` read as stated; `bounded.py` is byte-identical to the S02 pin. A hub scenario placing 300 and 60 side by side is consistent with two concepts but is not evidence about the Control Plane.

## 5. Security-boundary check (Phase 5)

No record whose kind is IMMUTABLE_CONTROL is proposed ELIGIBLE-NOT-MIGRATED (checked by the integrity test). Constitutional safeguards, authentication/provenance, grant/approval authority, atomic effect/evidence transactions, revocation enforcement, fail-closed validation, mandatory floors, serialization integrity, replay/rollback protection, the closed refusal vocabulary and `engine/safe_executor.py` evaluator semantics all appear only as RETAIN-IN-CODE. Every eligible row is monotone narrowing: Registry configuration may only narrow, unknown/absent/corrupt input never adds permission. `immutable_controls_seen.json` (A 26, B 25, C 44, D 32) lists what was deliberately left alone. Notable: the effect-time guard compares only the five allow-sets with a Registry record; `max_amount`, `max_effects`, `allowed_target_prefixes` and `target_match` are never compared.

## 6. Findings that need attention outside the migration program

Downstream importers pin older producer revisions (AD-16); the verifier lacks reasons 0.3 (AD-17); the hub component lock and Stack Qualification effective pins are the old generation (7 of 11 locked components moved); the Constitution checkout is ahead of the pin with inverted tier numbering (AD-15); `remove_authoritative_state` deletes grant rows without a retained-revocation record while approvals gained `authority_approval_revocations_v1` (G0-B-029; an authority-surface question, not a config value).

## 7. Verification

| Check | Result |
|---|---|
| `tests/test_g0_family_inventory_integrity.py` (620/620 rows, 75 resolutions, 32 unresolved tracked, 116 records source-backed, families dispositioned, no immutable control migrated, historical blobs unchanged, holds, sprint status) | PASS locally, 10 of 10 |
| Mutation checks of that test (change a historical class; change a historical evidence file) | PASS: each mutation made the expected tests fail; both restored |
| Full Registry suite, local | 6214 passed, 2 skipped, **1 FAILED**: `test_adapter_ed25519.py::test_installed_cryptography_matches_the_test_only_lock` (local environment has `cryptography` 50.0.2, the test-only lock says 50.0.1). The same test fails identically on the baseline without any G0 file, so it is environmental and not caused by G0. Exact-head CI on the PR is the authority. |
| Exact-head CI on the G0 PR | NOT YET OBSERVED at the time this file was written; see the PR |
| Component test suites (Runtime, Control Plane, Stack Qualification) | NOT RUN: G0 is a read-only inventory and changed no component source |
| Worker-cited test names | NOT RUN: cited by name only |
| Independent review | NOT RUN: none is claimed; AI workers and CI are not independent assessors |

Lead spot-checks (executed by the lead against the checkouts): f1ab field set; zero Registry code hits for `max_amount|max_effects|allowed_target_prefixes|target_match`; Runtime `tenant_id` 128 bound; Control Plane `cli_run.py:510` and `bounded.py:1271-1275`; `bounded.py` identical to the S02 pin; Control Plane and Runtime churn since the S02 pins (file lists in `source-baseline.md`). Worker claims not spot-checked are labelled worker findings in the ledger.

## 8. Limits

AI workers and CI are not independent assessors. Dispositions are proposals. Test bodies were not read and no component test suite was executed. The inventory is as complete as the grep-plus-read method allows; it is not proven exhaustive. Not read: see `source-baseline.md` section 4 and each worker's `notes.md`.

## 9. Holds unchanged

G0: AUTHORIZED. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD. The V09 candidate manifest and all historical evidence files are unchanged; no component source was changed; no workflow pin moved.
