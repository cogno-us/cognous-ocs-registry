# F4 ages-only increment: Registry-governed `status_max_age_seconds` and `approval_max_age_seconds` (2026-10-28)

Status: **IMPLEMENTED IN AN OPEN, UNMERGED PR; NOT ACCEPTED.** Builder-side, non-authorizing, documentation only. Tier 1 independent acceptance REQUIRED. Release, Publication, Production HOLD.

## 1. Mandatory references
- Static Migration Plan v1.1, adoption merge `6f600ab1150f00ef3d96834159b1807e866a78b6` (`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`).
- Independent Inventory Audit, PR #60, merge `6516446a4e551e50f2bb47c1d57fbf8ace27d7c5`.
- Engineering Plan v1.5 (`docs/plans/PROJECT_PLAN-v1.5.md`).
- Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; ADOPTION.md read at the same revision (non-authorizing; adoption is by exact revision and scope, and a merge is not an adoption decision).

## 2. Deliverables and exact pins
| Item | Where | Exact revision |
|---|---|---|
| A. F4 ages-only Control Plane implementation | Control Plane PR #88, branch `f4-ages-governed-consumption` (OPEN, UNMERGED) | head `9b71a1018eb630966a2b93c6e3bbfa36ebaeba7e` (reviewed head `ee8d51606fc33a0ee3d3784e2d05e55be4ce344e` preserved in branch history), based on Control Plane `d66ae07fa240510efdcc11ed4b3e1189dcefc822` |
| B. Registry compatibility change | **None required.** The existing r08-v2 F4 family (`f4-control-plane-age-bounds`) is consumed unchanged; no Registry slot, code or contract change | Registry pin `6f600ab1150f00ef3d96834159b1807e866a78b6` |
| C. Dependency manifest | Registry checkout at the pin above; PyNaCl 1.6.2 from Registry `requirements-ed25519.lock.txt` (hash-locked); Control Plane `.[dev]` (pydantic>=2.12, cryptography, pytest) | pin recorded in `tests/test_f4_age_governance.py` (`PIN`) and `.github/workflows/tests.yml` |
| Runtime | unchanged (source shows it does not consume these two values) | none |

Control Plane files: `src/agent_control_plane/registry_f4_age_governance.py` (new), `tests/test_f4_age_governance.py` (new, 73 tests), `docs/registry-f4-selection-source-custody.md` (new), `.github/workflows/tests.yml` (CI repair). `bounded.py` is byte-identical to `d66ae07` (test compares its sha256).

## 3. Design (source-backed)
- `GovernedAgeWorkflow` subclasses the existing `BoundedAuthorizationWorkflow`; the existing `_fresh` checks and reason codes enforce the narrowed values. The status scalar governs grant status (non-profile path), conflict status and policy status; the approval scalar governs approvals; both are read only inside `_resolve`, which only `decide` and `execute` call.
- Scope is host-fixed and never taken from a caller or record: consumer id (host configuration), tenant (must equal the proposal's `tenant_id`; tenant-aware proposals only), action (the workflow is bound to one action), Registry operation id (host mapping), institution and authority domain (the host manifest's declared authority context for the action). Out-of-scope proposals are refused before any Registry call.
- Source finding: Registry requires `operation` to match `[a-z0-9][a-z0-9._-]{2,63}`; a Control Plane action URN does not, so the operation id is a host-configured mapping rather than the action id.
- Required participation only; exact `Ed25519Verifier`; only `applied`; narrowing `min(host, registry)` with a defence-in-depth `<= host` re-check; r08-v2 F4 effective-policy digest recorded on the workflow (`registry_f4_policy_identity`).
- A `runtime_authority_profile` is refused: with it the grant-status bound comes from the F5 class bound, so F4 would silently not govern it (F5 is a different family and wave).

## 4. Lifecycle and atomicity evidence (Task 3 and the review correction)

**Execute-path trace (Control Plane `bounded.py` at `d66ae07`, unchanged).** `execute` = decision-record check; `_resolve` (authorization re-resolution, all freshness checks using the two scalars); `_record_check`; capability and adapter checks; `_observe_and_reconcile` (destination `observe`); reuse paths for an already-applied or partial effect; the "attempted" record (`records.append_attempt`); the freshness/0.1 expiry gate (only with a freshness profile, not used here); then `self.destination.apply(...)`, the single place an effect is committed; then the attempt record and a post-observation. `self.destination` is a host-supplied duck-typed object, and `DefinitiveDestinationRejection` is the existing, documented way for a trusted adapter to assert that nothing was dispatched (recorded as attempt `failed` with the given reason code). No hook exists inside the destination's own transaction.

**Supported correction (implemented).** The workflow wraps the supplied destination in a transparent proxy; its `apply` first re-verifies the selection and, if it is no longer valid, raises `DefinitiveDestinationRejection("registry_f4_selection_invalid")` without calling the real destination. The gate therefore runs after authorization re-resolution, observation, reconciliation and the "attempted" record, immediately before the commit call. All other destination attributes and methods are forwarded unchanged (tested). No evaluator, record schema or reason vocabulary was changed. Cost, stated honestly: a gate refusal leaves a persisted `failed` attempt, and under existing semantics a prior attempt blocks an automatic retry of the same effect ("observed absence does not establish retry eligibility after a prior attempt"), so a revoked-at-commit effect needs a new decision path after the host rebuilds the workflow.

**Residual TOCTOU (not closed).** The gate runs immediately before `destination.apply` is entered, not inside the destination's transaction. A revocation landing during the delegated call itself is seen at the next boundary only. Minimum architectural options for the Architect: (A) accept this bound as sufficient for the Control Plane's role (the destination remains the final atomic authority for its own state); (B) authorize an optional destination-transaction hook (e.g. a `pre_commit_check` callable that a destination invokes inside its own lock) in a successor Control Plane/destination contract; (C) move effect-time enforcement of Registry-governed values to the destination or Runtime, which already has a lock-time guard for its own values, and treat the Control Plane check as advisory. A rollback guard for `selection_source` is a separate option set (custody document section 4): (D) persisted high-water mark in the source (host duty, no change), or (E) an Architect-authorized Control Plane ratchet (a new mechanism, not built).

**Boundaries now checked.** Construction; start of `decide`; start of `execute`; effect commit gate (four `selection_source` calls per effect). Each must reproduce the bound values and effective-policy digest; withdrawn, revoked, expired, stale-trust, superseded, widened or otherwise changed selections are refused (entry boundaries: raise before any write; commit gate: destination untouched, attempt `failed`). Edits to the bound scalars or the manifest authority after construction are refused.

**Deterministic TOCTOU test (C01).** Source calls: 1 construction, 2 decision, 3 execute entry (valid), 4 commit gate, where the source now serves a revoked selection. Asserts: exactly four calls (entry passed, the gate refused), attempt `failed` with `registry_f4_selection_invalid`, Registry code `selection_revoked`, destination effects empty, no acknowledged attempt. C02 covers late stale-trust, superseded, bad-signature and wrong-scope material and C03 a failing source at the gate. C04 asserts gate-then-apply ordering and destination transparency; C06 asserts every boundary is judged at the execute-entry time even when the wall clock differs.

**Mutation evidence.** Removing the commit gate fails 9 tests; replacing the definitive rejection with a plain exception (which the workflow would record as an unknown outcome) fails 7; ignoring the execute-entry clock fails 1; earlier mutations (effect-entry check 2, decision check 9, narrowing 15, change detection 1) still fail tests; the widening re-check has its own test (D01).

**Atomicity.** Both ages are one F4 record and one selection, so a partial selection of one age is impossible. Different families are never combined by this module: an r08-v5 (clock tolerance), F5 or F1 selection supplied in place of the F4 record is refused at every boundary, and the module contains no tolerance code (S01). F4 and F4T stay separate; the F4/F4T question is not resolved here (RG-C-006 excluded; AR-1/AR-2).

**`selection_source` custody.** Requirements for freshness, revocation visibility, epoch, rollback, authenticity, scope, availability and thread safety are in [selection-source-custody.md](selection-source-custody.md) (copy of the Control Plane document). The Control Plane keeps no durable selection state; a source that rolls back to an older, unexpired, consistent set predating a revocation is NOT detected.

## 5. Tests and CI (PASS / FAIL / SKIP / NOT RUN kept distinct)
- Local, exact pin, `OCS_REQUIRE_REGISTRY_PIN=1`: `tests/test_f4_age_governance.py` 73 PASS (was 64 at the reviewed head). Matrix covered: existing-behaviour equivalence across status/approval/policy ages; narrower, equal, wider Registry values; boundary equality (inclusive, 1 s off); missing/malformed/invalid records; wrong contract/family/domain/signature; wrong consumer/tenant/institution/domain/operation; expired, stale-trust, revoked, withdrawn; change after construction; revoked between decision and effect; cross-family; refusal without state mutation; no widening.
- **CI (Control Plane PR #88, corrected head `9b71a10`; the reviewed head `ee8d516` was also green): `test (3.11)`, `test (3.12)`, `manifest-validator-parity`, CodeQL, Analyze (python), Analyze (actions): all success.** The new `tests.yml` steps check out Registry at the pin, install the hash-locked PyNaCl set, run the module with `OCS_REQUIRE_REGISTRY_PIN=1` (a missing/wrong pin or missing PyNaCl FAILS) and fail the job unless 0 skipped, 0 failed and \>=70 ran (floor raised from 60 with the new tests). A first push (`32309ca3`) FAILED this guard because one test was skipped in the shallow CI checkout (it read git history); the test was changed to a sha256 pin and the guard then passed. CI job logs are not retrievable from the builder's network; the guard's printed counts were seen only through failure annotations, so the passing runs are evidenced by the job conclusion plus the in-step assertion, not by a log excerpt.
- Full Control Plane suite, builder environment (Python 3.13.17, pydantic 2.14.1): base `d66ae07` pinned: 41 failed, 1325 passed, 90 skipped; change pinned: 41 failed, 1398 passed, 90 skipped (corrected head `9b71a10`; 1389 at `ee8d516`); failure sets IDENTICAL. Unpinned: 35 failed on both (identical), the new module NOT RUN (skipped). Failure identities and raw output: `evidence/`. The 6 extra pinned failures are `test_v02_claim_policy_binding.py`, which asserts a different Registry pin (`943ab183`). These failures are pre-existing in this environment, undiagnosed, and not classified as regressions of this change.

## 6. Disposition of the old M11 PRs (nothing deleted, closed, force-pushed or merged)
- Control Plane #87 (head `56ddb5f5`): HELD, OPEN. Its F4 ages portion is re-implemented in #88 with lifecycle revalidation; its F4T adapter is not imported. Branch and evidence preserved as the historical reference. Superseded in part, not by merge.
- Registry #58 (r08-v5 clock tolerance, head `1a67d539`): HELD, OPEN, pending Architect decisions AR-1/AR-2.
- Registry #59 (M11 accounting + pause handoff, head `e716eb78`): OPEN, retained as the evidence record.

## 7. Parameter-level accounting (denominator unchanged: 19)
| Parameter | Represented | Enforcement-integrated | Accepted |
|---|---|---|---|
| `status_max_age_seconds` (RG-C-003) | yes (F4 r08-v2) | **in open PR #88, not merged** | no |
| `approval_max_age_seconds` (RG-C-004) | yes (F4 r08-v2) | **in open PR #88, not merged** | no |
Merged basis: 9 integrated, 10 eligible-not-integrated, 0 accepted (unchanged). If #88 merges: 11 integrated, 8 eligible-not-integrated. Excluded and unchanged: constructor clock tolerance (blocked AR-1/AR-2), identity/mandate ages (blocked AR-4), funded merge authorities (unresolved).

## 8. Outstanding defects and decisions
1. Merge decision for #88 (Architect). Suggested review focus: the scope derivation (one workflow per tenant/action), the host-mapped Registry operation id, the commit-gate wrapper and its retry consequence, and the CI change.
2. Choose among options A-C for the residual TOCTOU inside the destination call (section 4); and D/E for selection-source rollback protection.
3. The 41/35 pre-existing local Control Plane failures remain undiagnosed (CI is green on 3.11/3.12).
4. If #58 is ever merged, the CI pin and `PIN` constant need an explicit decision whether to move.

## 9. Recommended next eligible parameter
`class_status_max_age_seconds` (RG-C-008, F5 `f5-action-class-age-bounds`): already represented and the natural pair of this increment, but the plan requires first deciding how narrowed class data enters `approval_commitment`. Not started; not authorized.
