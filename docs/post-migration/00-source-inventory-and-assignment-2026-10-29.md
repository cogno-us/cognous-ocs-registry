# OCS-REG-R1-START — post-migration source inventory and assignment record

Status: BUILDER_TESTED planning/inspection record. **Non-authorizing.** No behavior is changed. Nothing here is independent qualification, acceptance, release or a security clearance. Independent acceptance count: **0**. Migration implementation: CLOSED (see `docs/family-migration/IMPLEMENTATION-CLOSEOUT-2026-10-29.md`). Date: 2026-10-29.

## 1. Assignment (eight fields, condensed)

* **Identity:** work package `OCS-REG-R1-START`; role `implementation_owner` (Lead Builder); primary archetype **A** — contract, schema and architecture design: reconcile the completed implementation and establish the frozen architecture, contracts, acceptance criteria and dependency sequence for later bounded work; repositories `cogno-us/cognous-ocs-registry` (base `2815643c3e15fbc6aadadbf88dc7596f10120992`) and `cogno-us/cognous-control-plane` (base `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`). Risk tier: **T0** for this work package (documentation/inspection only; no reachable effect); the changes it plans are classified per package in `03-...`; prescribed independent qualification and final freeze are **T4**.
* **Authority:** Architect directive "POST-MIGRATION QUALIFICATION AND R1 CONSOLIDATION", 2026-10-29: verify closeout; prepare F3-A/F3-B handoffs; read-only R1 inventory; reconcile the R1 plan with merged code; rank candidates; prepare sequenced packages; GitHub-native planning and evidence PRs. **Not authorized:** R1 production-code refactoring before the entry gates; changing frozen Registry contracts, protected evaluators or authority semantics; modifying independent oracles; paid testing or external effects; automatic merges; publication, release, deployment.
* **Ownership:** Lead Builder writes this documentation set (one designated writer). The independent qualification owner owns F3-A/F3-B oracles, execution and verdicts. The Lead Builder does not self-certify. Read-only workers produced inventories; their output is developer evidence.
* **Inputs / Acceptance / Delivery / Boundaries:** as in the directive; deliverables are `00`–`04` in this directory and the PRs that carry them.
* **Governance baseline:** prompt-engineering policy revision `cogno-us/cognous-engineering-constitution@dcdbe3b76843d672ca3cfb1f000124ecd78ed03c` (read at that exact revision: ENGINEERING_CONSTITUTION.md, ORCHESTRATION.md, ORCHESTRATOR_PROMPT_ENGINEERING_ADDENDUM.md, ENGINEERING_COMPLIANCE_ADDENDUM.md, TESTING_POLICY.md, ADOPTION.md, `schemas/orchestrator-assignment-v1.schema.json`). That revision adds, relative to `230c0aff1c2d1e054652cfc1be175147260b8aae`, only the LICENSE, the Orchestrator Prompt Engineering Addendum (which states it is not adopted by publication or merge), a README change and the assignment schema. **Existing OCS project adoption records (which pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` or `230c0af…`) are not changed or superseded by this record.**

### Archetype A clauses, verbatim from `ENGINEERING_COMPLIANCE_ADDENDUM.md` at `dcdbe3b…` (table cells unaltered) with task-specific bindings

| Article | Required behavior — exact source | Prohibited shortcut — exact source | Binding for OCS-REG-R1-START |
|---|---|---|---|
| CA01 — Reuse Before Build | Inspect and reuse qualified, versioned components. | Duplicate an owned capability for convenience. | Inventory is built on the merged r08-v8 unified engine (`registry_successor/engine/`), Registry verification machinery and the Control Plane effective-policy infrastructure; no new abstraction is proposed where an existing shared helper or module is not demonstrably present. |
| CA03 — Contract Before Code | Identify the controlling source, external reliance boundary, duties, expected acceptance and the authority by which a proposed change may acquire canonical standing. | Start against an unnamed or mutable contract. | All contracts and source heads are pinned in section 2 before any consolidation is proposed; every package in `03-...` names its pins and its Architect gate. |
| CA04 — Qualification Designed Before Acceptance | Distinguish implementation inspection, independent qualification, competent certification and final integration; preserve independence wherever required. | Fit an oracle to implementation or substitute developer tests. | F3-A/F3-B expectations were written before the binding and temporal changes (final-three record 03); the handoff in `01-...` is prepared for an independent owner and contains no verdict. |
| CA18 — Governed Policy and Protected Invariants | Version, authenticate and review governance-critical policy and rule changes; protect established mandatory invariants against configuration override. | Treat unreviewed settings or evaluator changes as governing authority, weaken mandatory checks or introduce an unaccountable decision path. | Authority, revocation, authentication and enforcement checks are classified as deliberate security redundancy where they repeat; no package may remove one. |
| CA21 — Boundary Commitments | Preserve relied-upon external semantics or obtain an explicit authorized compatibility transition. | Introduce silent contract, rights, evidence or interface regressions through internal refactoring. | Frozen r08-v1..v8 contracts, signature domains, identities, approval commitments, catalogue digest, persisted decision bindings, reason vocabulary and historical records are preserved; any change is STOP-ARCHITECT. |

## 2. Verified current source (live, read from GitHub at the time of this record)

| Repository | Ref | Exact SHA | Evidence |
|---|---|---|---|
| cognous-ocs-registry | `main` | `2815643c3e15fbc6aadadbf88dc7596f10120992` | merge of closeout PR #78; GitHub check runs on that head: CodeQL, both Analyze jobs, pytest — success |
| cognous-control-plane | `main` | `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` | merge of PR #97; check runs on that head: both `test` jobs, manifest-validator-parity, both Analyze jobs — success |

Merged chain (matches the closeout): Registry #75 `7cfeca8098a2151a94763ca2d71271c4ab8d0524`; Registry #77 (r08-v8) `188e90efc02e857928e857998231473c3f235b16` (head `a40fe755e2384a99c37016fa9ad59396f1835900` is an ancestor); Registry #78 `2815643c…`; CP #94 `19aeb9397e161dd8876eff7d79733832ff8b6ab0`; CP #95 `fb9c7e06075d18f518f0d2e8782b167e368c0512` (merged into the #94 feature branch, **not** main); CP #96 `e9214718fd8cb89763a8663fa1d69f879f740e3e`; CP #97 `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`.

Verified facts on Control Plane `main` (sha256 of the working file): `src/agent_control_plane/runtime_authority.py` = `45a27db8695ff9d2…` (the D-07 corrected file, **present on main through #97**; the predecessor, still in `061a986`, is `a4b4ac36cca6e75d…`). The six other protected evaluators on `main` are `bounded.py` `c219f8825a8d…`, `freshness.py` `3f146ee11a34…`, `policy_binding.py` `defdfac5fd60…`, `rule_revision.py` `a3833f49e96d…`, `reversibility.py` `5edbadebb3aa…`, `holder_inventory.py` `76f5aaa63f49…` — identical to the pre-final-three baseline. Accounting: 19/19 implementation integrated, 0 independently accepted (closeout).

**Qualification must bind to these `main` sources, not to #95's feature-branch merge or to the earlier branch heads (`5ffd0ae`, `4adb84b`, `b8fbe95`, `a1de48c`, `55488d2`).**

## 3. Open items observed (no action taken on them)

* Registry #58, #59 (M11 constructor-tolerance work), Control Plane #87: open, **HELD**. Constructor tolerance NOT AUTHORIZED. Registry #52 and #7 (dependency bump) are open and outside this work package.
* Registry #76 — **R1-E Ergonomics Integration Addendum v1.0** (head `138e222998345e021c7f5adf68bf2d2aa719c8a9`, file `docs/plans/REGISTRY-R1-E-ERGONOMICS-INTEGRATION-ADDENDUM-v1.0.md`): **open, unmerged, status "PROPOSED STATIC PLAN AMENDMENT, NON-AUTHORIZING"**. It is therefore not an adopted revision; the only verifiable revision is that PR head. Its governance line pins `1c2e920…`. It places Ergonomics work as a named package between the core refactor and the freeze and does not authorize implementation. This record treats it as proposed; merging it is an Architect decision.
* Ed25519 #26/#34: HELD. In this Registry repository they are merged PRs titled `[SECURITY-HELD] EXT-S1-7: Ed25519 SignatureVerifier adapter (synthetic keys only)` (#26) and `[SECURITY-HELD] core verifier: canonical base64 signatures and trust-boundary key admission` (#34); their own records state NOT INDEPENDENTLY SECURITY-ASSESSED and NOT TIER 1 QUALIFIED. The merge does not lift the security hold; any R1 package touching them is STOP-ARCHITECT.
* DEF-OBS-TOL-OVERFLOW-1 (extreme ObservationPolicy tolerance `OverflowError` in `bounded.py`): unresolved and separate; **excluded from every R1 candidate**. Record: `docs/family-migration/final-three/04-defect-record-extreme-tolerance-overflow-2026-10-29.md`.

## 4. Known limitations carried unchanged (not promoted to guarantees)

Unsigned persistence store; no durable anti-rollback guarantee; `legacy_cutoff` has no durable provenance; mixed-fleet legacy writers; a host change fully masked by a narrower Registry value is not refused; the anchor guarantee depends on the D-07 correction; `reconcile()` is not guarded against post-construction mutation of `observation_policy` (pre-existing); the 41 Control Plane test failures in the baseline are environmental (pytest-asyncio absent, older Registry pins) and unchanged by the final three.

## 5. Holds (verbatim, unchanged)

Registry #58/#59: HELD. Control Plane #87: HELD. Constructor tolerance: NOT AUTHORIZED. Ed25519 #26/#34: HELD. V09: SEPARATE. Tier 1 final qualification: DEFERRED, NOT WAIVED. Publication, release, production: HOLD.
