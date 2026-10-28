# Registry Family Migration: controlled pause and handoff (2026-10-28)

Status: **PAUSED, AWAITING INVENTORY AUDIT.** Documentation only. Non-authorizing. Nothing here is an acceptance, certification or readiness claim. Written by the Lead Builder; the Architect decides everything marked OPEN.

## 1. Objective
Migrate eligible hard-coded policy rule groups into Registry-governed configuration. Registry configuration may only narrow authority, never widen it. Priority was working code; the program is now paused (not cancelled) until the independent 620-record historical inventory and Registry eligibility audit is reviewed.

## 2. Governing documents and immutable pins
- Static Family Migration Plan v1.0: `docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.0.md`
- Engineering Plan v1.5: `docs/plans/PROJECT_PLAN-v1.5.md`
- Engineering Constitution, pinned `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (ENGINEERING_CONSTITUTION.md and ADOPTION.md at that revision; ADOPTION is non-authorizing).
- Original frozen G0 inventory (`docs/family-migration/g0/`): unmodified.
- Control Plane source baseline for M11 reads: `d66ae07`.

## 3. Completed and merged
| Item | Repo | Full SHA | Final CI |
|---|---|---|---|
| M3 Registry r08-v4, PR #56 (reviewed head `7cd8042696ac1d692c2f325095e194ed4f23c72c`) | Registry | `b7e6a173877c731273858b01b26214147dd0736c` | pytest, CodeQL, Analyze: success |
| M3 Runtime enforcement, PR #153 (head `e8323f1d790829d0e1353f436c6a60e787eddefe`, re-pinned to the Registry #56 merge) | Runtime | `f7a55e2a8494801e49193f9f46935f0a971c248d` | Component-local, cross-component (3.11, 3.12, safety-tests), no-tabs, Analyze: success |
| M3 tracking PR #57 (head `b81a2a2ff62f9a2cf0b439aacc332c2ef5a22dde`) | Registry | `2668094dd6caac1a397dce7f6d6c3b5a194e9d8e` | success |
| M2 (r08-v3): Registry `ba98dd26`, Runtime PR-2 `99f5f053`, Runtime PR-3 #152 `dabaa770` | | | merged earlier |
M2 and M3 are IMPLEMENTED AND MERGED, NOT independently accepted. Runtime pinned-profile result at the M3 merge: 1023 passed, 1 skipped (pin-dependent tests are NOT RUN without the pin).

## 4. Open M11 PRs (all OPEN, UNMERGED, implementation frozen)
| PR | Branch | Head | Depends on |
|---|---|---|---|
| Registry #58 (r08-v5 `f4t-control-plane-clock-tolerance`) https://github.com/cogno-us/cognous-ocs-registry/pull/58 | `m11-pr1-r08-v5` | `1a67d5396a3cf81512fdfa98c5cea9c6db70aede` (based on Registry main `2668094d`) | none |
| Control Plane #87 (adapter `registry_freshness_narrowing`) https://github.com/cogno-us/cognous-control-plane/pull/87 | `m11-pr2-registry-freshness-governance` | `56ddb5f5cabab5c8c37155ae3a0ad1b586d0c354` (based on CP main `d66ae07`) | Registry #58: its test pin `PIN` is #58's unmerged head; re-pin to the merge commit if #58 merges |
| Registry #59 (accounting + this handoff) https://github.com/cogno-us/cognous-ocs-registry/pull/59 | `m11-progress-accounting` | see the PR (amended by an added commit, no force-push; earlier head `259766e6a07724f35a01be968477842c7e4ab8cc`) | none |
Runtime: unchanged by M11 (source shows it does not consume these values). CI on all three was green at their reported heads; Control Plane CI does NOT run the new tests (section 7).

M11 values: RG-C-003 `status_max_age_seconds` and RG-C-004 `approval_max_age_seconds` use the existing Registry F4 fields (r08-v2) with new Control Plane consumption only; RG-C-006 `clock_tolerance_seconds` is the new r08-v5 F4T field. `identity_max_age_seconds` and `mandate_max_age_seconds` stay host-owned.

## 5. Counts (PROVISIONAL G0 counts; the audit may revise the denominator)
| | Count |
|---|---|
| Already Registry-governed before this program | 5 |
| G0 eligible-not-migrated (PROVISIONAL; 23 + 5 = 28 PROVISIONAL total) | 23 |
| M2 implemented and merged | 2 |
| M3 implemented and merged | 2 |
| M11 implemented in open PRs, not merged | 3 |
| Remaining, merged basis | 19 |
| Remaining if M11 merges | 16 |
| Independently accepted (new migrations) | 0 |
The current migration inventory does NOT exhaust the 620 historical rule-site records; do not read these counts as covering them. IMPLEMENTED is not ACCEPTED.

## 6. Open architectural issues (recorded, not resolved)
**A. Family atomicity (OPEN).** F4 (r08-v2) and F4T (r08-v5) are separate Registry families with separate selections, signing domains and digests. Evidence: the adapter requires every *supplied* input to apply and returns no workflow otherwise, with no fallback; a group left out (`None`) is simply ungoverned, so a host can omit one family; each family's coexistence rule applies only within itself; the Control Plane has no durable activation record, so there is no cross-family binding or ratchet. Unresolved: whether the architecture can force both to be active together without partial activation, stale authority or silent fallback, or whether that needs a composite family or a Control Plane activation record. Not implemented during closeout.

**B. Clock-tolerance range (OPEN, unchanged).** Proposed `0..2147483647`. Basis: `2147483647` is the adopted V1 technical representation ceiling for AGE values (DR-CP-AGE-1, `docs/r08-v2-contract-amendment-1.md` section 2). For `clock_tolerance_seconds` it is an implementation constraint the builder reused (the Control Plane adds the value with `timedelta`, which overflows far above this, so the ceiling is safe); it is NOT an adopted Registry limit for tolerance. `0` is valid and strictest, not deny-all. Source `bounded.py` does not validate the caller's tolerance at all. Needs Architect adoption or change.

**C. Control Plane CI coverage (OPEN).** New tests: `tests/test_m11_registry_freshness.py` (81 tests; module is skipped, i.e. NOT RUN, when the pin or PyNaCl is absent). Needs: `OCS_REGISTRY_PIN_DIR` set to a Registry checkout whose `git rev-parse HEAD` equals the test's `PIN` constant (`1a67d539...` now); PyNaCl from Registry `requirements-ed25519.lock.txt` (hash-locked); pydantic>=2.12 and cryptography (already in `.[dev]`). Local command: `OCS_REGISTRY_PIN_DIR=<registry checkout> PYTHONPATH=src:. python -m pytest -q tests/test_m11_registry_freshness.py` gives 81 passed; without the env var: 1 skipped. Recommended minimal CI correction (not applied): in the existing `tests.yml`, add a step that checks out `cogno-us/cognous-ocs-registry` at the pinned SHA, installs its `requirements-ed25519.lock.txt`, and exports `OCS_REGISTRY_PIN_DIR`, the same way other pin-dependent tests already work. No new framework. Note: running the whole Control Plane suite under that pin also turns on other pin-dependent modules, which assert other pins (e.g. `test_v02_claim_policy_binding.py` expects `943ab183`), so the step may need to be limited to this module.

**D. Existing Control Plane failures (OPEN, undiagnosed).** 41 failures with the pin set, identical on untouched base `d66ae07` (1325 passed, 90 skipped) and on PR #87 (1406 passed, 90 skipped); 35 on the base without the pin. Distribution: `test_microsoft_agt.py` 14, `test_scan6_agt_exact.py` 16, `test_v02_claim_policy_binding.py` 6, `test_wave7_agt_binding_equality.py` 5. Identities: `evidence/cp-local-failures-41.txt`. Builder environment: Python 3.13.17, pydantic 2.14.1, pytest 9.1.1, PyNaCl present (CI uses Python 3.11 and 3.12 and is green). Not classified as M11 regressions; no unrelated repair undertaken.

**E. Revocation observation (OPEN).** The adapter verifies Registry selections once, at workflow construction. A later revocation, withdrawal or expiry is not observed until the host rebuilds the workflow. This is NOT effect-time revocation enforcement (the Runtime has a durable ratchet and lock-time guard for its values; the Control Plane has none). **Do not merge Control Plane #87 while A and E remain unresolved.**

## 7. Reproducible test environments
- Registry: `python -m pytest -q tests` with PyNaCl from `requirements-ed25519.lock.txt`; last full run on the #58 tree: 7351 passed, 2 skipped (about 6 minutes).
- Runtime pinned profile: `OCS_REGISTRY_PIN_DIR=<registry at b7e6a173> PYTHONPATH=".:src:<cp>/src:<cp>" python -m pytest -q tests --ignore=tests/test_producer_status_matrix.py --ignore=tests/test_scan_remediation_profiles.py` (pydantic 2.12): 1023 passed, 1 skipped. Without the pin (Profile X): 561 passed, 52 skipped (NOT RUN).
- Control Plane: as in 6.C and 6.D.

## 8. Inventory-audit dependency
The independent 620-record historical inventory and Registry eligibility audit is an ACTIVE, separate workstream and is not touched here. The backlog (`m2/01-migration-backlog.md`) and the G0 inventory are not revised on preliminary findings. The Architect reconciles audit findings with the backlog before any further wave.

## 9. Restart prerequisites
1. Explicit Architect authorization after the audit is reviewed.
2. Architect decisions on 6.A, 6.B, 6.E (and the CI approach in 6.C).
3. Verify heads: Registry main `2668094d` (or later), PR #58 `1a67d539`, CP PR #87 `56ddb5f5`; branches `m11-pr1-r08-v5`, `m11-pr2-registry-freshness-governance`, `m11-progress-accounting` on GitHub.
4. If #58 merges, re-pin #87 (and any dependent tests) to its merge commit before merging #87.
5. Independent Tier 1 acceptance of M2, M3 (and M11 if merged) is still REQUIRED and has not been performed.

## 10. Recommended next increment (after audit review; NOT automatically M12)
First close the M11 decisions (6.A atomicity, 6.E lifecycle, 6.C CI) because they decide whether the Control Plane consumer pattern is sound for later Control Plane waves. Then choose the next wave from the audit-reconciled inventory. G0's default order (M12, M10, M8, M13) is only a default.

## Standing holds
Independent Tier 1 acceptance: REQUIRED. V09 assurance: separate workstream. Ed25519 #26/#34: SECURITY-HELD. Release, Publication, Production: HOLD. M12 and later waves: NOT AUTHORIZED.
