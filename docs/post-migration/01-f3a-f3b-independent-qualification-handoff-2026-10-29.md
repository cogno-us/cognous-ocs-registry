# F3-A / F3-B independent qualification handoff (prepared by the Lead Builder; NO verdict)

Status: handoff package for an **independent qualification owner**. Non-authorizing. The Lead Builder records no PASS/FAIL and must not qualify its own work. **F3-A: PENDING. F3-B: PENDING.** Developer tests, CI and mutation results are developer evidence, not qualification. No qualifier is yet designated (Architect decision, `04-...`). Date: 2026-10-29.

## 1. Frozen subject (bind to live main, never to feature-branch heads)

| Subject | Exact source |
|---|---|
| Control Plane `main` | `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (merge of #97) |
| Registry `main` | `2815643c3e15fbc6aadadbf88dc7596f10120992`; r08-v8 merge `188e90efc02e857928e857998231473c3f235b16` |
| F3-A sources | `src/agent_control_plane/effective_configuration_binding.py`, `registry_governed_lifecycle.py`, `registry_governed_policy.py`, `registry_f4_age_governance.py`, `registry_f5_class_age_governance.py`, `registry_f5_class_unreadable_governance.py`, `registry_final3_governance.py`, `registry_effective_policy.py` (blob/sha256/line count per file in annex A section 1) |
| F3-B source | `src/agent_control_plane/runtime_authority.py` sha256 prefix `45a27db8695f` (D-07; one hunk, lines 404-415 vs predecessor `a4b4ac36…` at `061a986`), plus the six other protected evaluators byte-identical to `b7eb11a`: `bounded.py`, `freshness.py`, `policy_binding.py`, `rule_revision.py`, `reversibility.py`, `holder_inventory.py` |
| Oracle expectations | `docs/family-migration/final-three/03-f3-qualification-expectations-F3A-F3B-2026-10-29.md` (written before the changes; minimum, never the ceiling) |
| Contract | Registry `docs/r08-v8-contract.md`; freeze record `final-three/02-...`; defect record `final-three/04-...` (out of scope) |

D-07 reached Control Plane `main` only through #97; #95 merged into the #94 feature branch (`fb9c7e0`, not an ancestor of `main`). Evidence produced at `5ffd0ae`, `4adb84b`, `b8fbe95`, `a1de48c` or `55488d2` is **not transferable** to `main` without a justified identity argument (the worker found that `a1de48c` src, tests and schemas are tree-identical to `main` with docs differing; that is a lead for the qualifier, not a transfer).

## 2. Archetype D governance (verbatim from `ENGINEERING_COMPLIANCE_ADDENDUM.md` at `dcdbe3b76843d672ca3cfb1f000124ecd78ed03c`, table cells unaltered; bindings are task-specific)

| Article | Required behavior — exact source | Prohibited shortcut — exact source | Binding |
|---|---|---|---|
| CA04 — Qualification Designed Before Acceptance | Distinguish implementation inspection, independent qualification, competent certification and final integration; preserve independence wherever required. | Fit an oracle to implementation or substitute developer tests. | The qualifier defines its own scope and oracle (the builder expectations in final-three record 03 are the minimum, never the ceiling) and does not inherit the builder test selection. |
| CA06 — Preserve Original Evidence | Retain consequential decision ancestry, rejected alternatives, objections, adverse findings and supersession where legitimately relevant, subject to privacy and retention limits. | Delete, relabel, overwrite or silently rescore failures. | Retain every adverse result with its original output, including the 41 known baseline failures with their causes; no rescoring, no edited frozen oracle. |
| CA07 — Exact-Source Reproducibility | Bind claims to exact source, configuration, governing context and transition evidence; reconstruct authoritative pathways when deterministic execution replay is impossible. | Transfer a pass across revisions. | Qualify only the exact frozen heads named in the assignment (Control Plane `main` 739efe7d…, Registry per the pin decision); no pass is transferred from the pre-merge branch heads. |
| CA08 — Independently Qualified Delivery | Optimize authorization-to-independently-qualified outcome; distinguish lifecycle evidence. | Treat PR counts, green CI or documents as delivery or qualification. | Report delivery state precisely: implemented and merged, developer-tested, independently qualified or not; green CI and documents are not qualification. |
| CA23 — Accountable Certification | Separate contribution, inspection, qualification, certification and integration according to risk and governing independence requirements. | Self-certify generated work or treat nominal human involvement as sufficient authority. | Separate contribution, inspection, qualification, certification and integration; the Lead Builder contributes handoff material only and issues no verdict. |

Assignment shape for the qualifier (to be compiled by the Architect/orchestrator, not dispatched by the Lead Builder): role `independent_qualification_owner`, archetype D, tier T4, repositories as in section 1, writable paths: the qualifier's own report location only; protected: everything else; acceptance: the qualifier's own oracle plus the minimum expectations; delivery: a verdict per package with raw outputs and original failures; boundaries: no paid testing or external effects without specific authorization.

## 3. What the builder delivers to the qualifier

* Coverage and source map of existing developer tests per expectation, with gaps: annex A (a read-only worker's factual record; unverified items are listed there).
* Original failing outputs and supersession records: Control Plane `tests/fixtures/d07_predecessor_outcomes_061a986.json`, `tests/test_freshness_purpose_residual.py` (superseded characterization, history at `061a986`), `docs/evidence/d06/`, `docs/evidence/d07/`, `docs/evidence/final3-consumers/` (including the reviewer's shallow-clone failure kept as evidence).
* Developer mutation evidence (64/64 consumer mutants; D-06 and D-07 harnesses) — developer evidence only.
* Environment: Python >=3.11 (Control Plane CI runs 3.11 and 3.12), `pydantic>=2.12`, PyNaCl; `OCS_REGISTRY_PIN_DIR` must point to a Registry checkout and `OCS_REQUIRE_REGISTRY_PIN=1`. The Control Plane tests hard-code the accepted Registry pins per suite (`ACCEPTED_PINS` includes `PIN_V8` = `a40fe755e2384a99c37016fa9ad59396f1835900`); a checkout at Registry `main` or at `188e90ef` is rejected at collection. For the r08-v8 suites (the F3-A and F3-B subjects: `test_final3_*`, the D-06 binding files, the D-07 successor tests) `a40fe755` is the working pin; it is code-identical to Registry `main` outside documentation (diff of all code and test directories). It is NOT sufficient for the whole Control Plane suite: the F4 and F5-age gates need a checkout at `6f600ab`, the `test_v02` vectors need `943ab18`, and the workflow uses five pins (`6f600ab`, `6c3e5e4`, `42a6663`, `b73c59e`, `a40fe755`). A reviewer reproduced a single-pin run as 2898 collected with 2 collection errors. The qualifier must follow the workflow's per-suite pins. Pin decision for the Architect: see `04-...` D3.
* The 41 known environmental baseline failures (pytest-asyncio absent; older Registry pins) are listed in `docs/evidence/final3-consumers/baseline-failures.txt` and must be retained, not hidden.

## 4. Known coverage gaps stated by the worker (developer evidence only, for the qualifier to test independently)

F3-A: pin-export refusal is not driven for every perturbed member; duplicate JSON keys in the persisted store are untested; only one crash point around `append_decision` is injected; no test asserts the limits text or fails an anti-rollback claim. F3-B: expectation 4 ("only adds a `min`") is exercised by a 124-case grid, not a property test; outage-extension tests cover the purpose observation only. Also: no CI step runs the three D-06 binding test files under the Registry pin with a skip-asserting junit gate (the Control Plane workflow gates other suites; the workflow's plain `pytest` step runs without the pin). These are recorded for transparency; they do not change the expectations.

## 5. Limitations to carry, verbatim in any qualification report (not promoted to guarantees)

Unsigned persistence store; no durable anti-rollback guarantee; `legacy_cutoff` provenance (host-supplied, no durable provenance); mixed-fleet legacy writer behavior; a host change fully masked by a stricter Registry value is not refused; the anchor guarantee depends on D-07 being present; `reconcile()` is not guarded against post-construction mutation of `observation_policy` (pre-existing). Out of scope and separate: DEF-OBS-TOL-OVERFLOW-1.

## 6. Documentation discrepancies found while preparing this handoff (for the owner of each document; not corrected here)

`docs/final3-consumers.md` section 6 (Control Plane) says `main` lacks D-07, which was true before #97 merged and is stale on `main`; `docs/r08-v8-contract.md` states that no Control Plane consumer exists (stale after #97); the D-07 doc's "Before" comment quotation is not verbatim; `family_schema_revision` accepts null in one record form; the D-06 mutation counts differ between the draft (65 killed, 2 survived) and `summary.json` (64 killed, 3 survived). Historical evidence files are not rewritten (CA06); corrections, if wanted, are new text.

## 7. Typed assignment packets

Schema-validated Archetype D packets for F3-A and F3-B are in `assignments/` (status: READY FOR ASSIGNMENT / OWNER BLOCKED; no execution authorized). Coverage notes in section 4 remain developer evidence.
