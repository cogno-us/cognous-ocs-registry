# OCS Registry — Static Engineering Program
**Plan:** OCS-REG-PLAN v1.1 | **Issued:** 2026-10-24 | **Status:** Architect-directed plan, operator-selected program; exact baseline selection pending
**Plan authority:** Cognous operator. **Plan custodian:** Architect (ChatGPT). **Implementation:** authorized builder.
**Engineering Constitution:** https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
**Adoption:** This plan does not itself adopt the Constitution. Follow its ADOPTION.md; identify any formal adoption separately.
**Scope:** One clean, non-fork registry engineering workspace; not a replacement OCS stack.
**Release / publication / production:** HOLD. No paid calls, cloud, credentialed effects or deployment.

## Mission and no-drift rule
Return to an exact source-backed historical OCS behavioral baseline, then migrate genuinely configurable hardcoded governance rules **one family at a time** into authenticated versioned data consumed by registered deterministic evaluators. Constitutional and mandatory authority/effect-time invariants remain enforced in code. Do not import the 3,190-rule historical catalogue, broad scenario inventory, old execution logs, orchestration machinery, or the former v0.2 project-management system. Historical records remain accessible by exact references in the old repositories.

**This plan is static.** Never edit this version in place to accommodate builder discoveries or status. A material change needs an operator/Architect decision and a new versioned successor plan with a crosswalk. Routine findings update only `docs/sprint-status.md`; decisions retain dated, source-backed records under `docs/decisions/`. A proposed change is not authorization.

## Work rules
- One sprint = one primary deliverable and normally one small PR; target 1–3 working days, planned maximum 5; split rather than sprawl. Size guidance ~100–400 substantive changed lines when practical, excluding carefully selected upstream source.
- Use maximum practical parallelism for disjoint tasks within the **currently authorized sprint**. Delegate exact source pins, file ownership and nonoverlapping deliverables. One designated integration owner serializes changes to shared code, schemas, authority boundaries and canonical state. Multiple independent reviewers may work concurrently. No overlapping implementation sprints without separate operator authorization.
- Build → test → fix → retest → commit; routine repairs autonomous within the approved sprint.
- No new engines, databases, orchestration, cloud environments, PR control planes, bulk migration pipelines, generalized policy interpreters or broad adapters.
- Preserve exact source revision, licenses, hashes, results and adverse findings. Developer tests do not constitute independent qualification.
- No new sprint begins until explicitly authorized by the operator. S01 ONLY is authorized initially.
- At each sprint exit, compare the PR against the applicable static plan section; record PASS/BLOCKED and scope differences in PR and live status, not in this plan.
- Constitution references: CA01, CA02, CA04, CA07, CA09–CA12, CA14, CA16, CA18–CA20, CA23, and any additionally applicable articles.

## v1.1 amendment — parallelism authorization
The operator rescinds the v1.0 two-worker limit. S01 research, source verification, tests, provenance and independent review may run concurrently with disjoint ownership. There is no numeric worker cap; use only productive, nonconflicting workers. Workers cannot expand authorized sprint scope. v1.0 remains preserved at its historical Git blob.

## S01 — Historical baseline recovery (AUTHORIZED)
**Objective:** Recover and reproduce the minimum source-backed historical behavioral slice necessary to compare a first registry migration.
**Tasks:** Examine historical locks and revision lineage; distinguish g8-r10, earlier W7/V1 selections and MVP candidates; propose exact source tuple and confirm provenance; curate minimal files, dependencies, license notices, minimal fixtures, clean-clone reproduction; list (do not import) later valuable safety corrections. No rule extraction or registry migration.
**Exit:** Source identity and baseline candidate stated without pretending it is an adopted release; reproducible bounded smoke tests with commands and PASS/FAIL/SKIP, exclusions and limits; one reviewable PR. If multiple plausible baselines exist, do not choose silently: request operator's exact selection.
**Stop:** After S01 PR. No S02 without operator authorization.

## S02 — Hardcoded-rule inventory (PLANNED; NOT AUTHORIZED)
**Objective:** Source-based list of configurable logic in the *selected* baseline, distinct from constitutional floors, intrinsic admission/effect checks, refusal/reason codes, serialization, incidental conditionals and historical test ideas.
**Exit:** Small source-to-rule-family crosswalk (file/line/ref/evaluator/boundary), risk classification, explicit non-migratable invariants; one proposed low-risk first family. No bulk catalogue import, no production behavior change.

## S03 — Minimal registry contract (PLANNED; NOT AUTHORIZED)
**Objective:** One-family data schema and deterministic validation: stable identity/version/hash, provenance, applicability, registered evaluator reference, required inputs and missing/invalid/unsupported behavior, non-authorizing semantics and supersession.
**Exit:** Focused schema, validator, tests and fail-closed outcomes. Reuse existing qualified OCS concepts. No general-purpose interpreter, arbitrary scripts or new enforcement authority.

## S04 — One rule-family migration (PLANNED; NOT AUTHORIZED)
**Objective:** Move exactly one selected configurable policy-data family to versioned registry records, while preserving deterministic evaluator/enforcement code.
**Exit:** Narrow implementation PR, source lineage, no changes to grant/approval authority, effect-time admission, negative evidence or mandatory safety floors. Do not migrate neighboring families opportunistically.

## S05 — Behavioral equivalence (PLANNED; NOT AUTHORIZED)
**Objective:** Compare original hardcoded and registry-backed behavior with identical pinned inputs/configuration; test positive, refusal, boundary, missing/invalid inputs and relevant negative/changed-condition cases.
**Exit:** Raw and summarized differential results; exact hashes; no unexplained materially different output; independent assessment where risk requires it. Developer PASS is not qualification.

## S06 — Consolidate and propose next increment (PLANNED; NOT AUTHORIZED)
**Objective:** Remove only demonstrated redundancy of the first migration; retain invariants and source provenance; recommend the next family from evidence.
**Exit:** One bounded cleanup PR and concise next-increment proposal. S07/next migration not automatically authorized.

## Source and operational custody
- Static plan: `docs/PROJECT_PLAN.md` (this file; v1.0).
- Mandatory builder handoff: `docs/BUILDER_HANDOFF.md`.
- Live status only: `docs/sprint-status.md`.
- Dated decisions: `docs/decisions/` (verbatim decision where available, scope, source, effective point, exceptions, authority; no fabricated retrospective approvals).
- PR evidence: exact heads, local commands, PASS/FAIL/SKIP, limitations, next requested decision. Avoid copying old result archives.
- Other OCS repos are read-only provenance sources for this program unless the operator separately authorizes changes.

## Change control
The Architect maintains plan alignment and proposes exact-version changes; the operator alone authorizes material scope/sprint transitions. Builder may correct routine implementation failures within a sprint, not expand its mandate. Material security/authority/acceptance differences require decision before canonical promotion. Preserve old plan revisions as history; never rewrite S01–S06 outcomes to claim broader scope.
