# OCS Registry — Mandatory Builder Handoff
**Every builder instruction, worker delegation, PR description and completion report must include both exact references:**

1. **Static plan:** https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (OCS-REG-PLAN v1.1; until merged, cite the PR branch and exact head). Earlier v1.0 remains at docs/PROJECT_PLAN.md.
2. **Engineering Constitution (pinned):** https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md

Also read pinned `ADOPTION.md` and `ORCHESTRATION.md`. The Constitution governs engineering conduct, not release authority; do not infer project adoption from publication. If plan or Constitution is unreachable, report this and use the actual fetched canonical text before claiming conformance.

## Required instruction header
- **Plan:** exact link and version; authorized sprint and section.
- **Constitution:** exact pinned link; materially applicable CA articles.
- **Authorization:** source and scope of operator/Architect decision; no inferred expansion.
- **Objective and allowed files:** one bounded deliverable.
- **Source baseline:** exact refs, licenses and retained historical provenance.
- **Tests/acceptance:** reproducible commands, positive and negative controls.
- **Exclusions/no claims:** what remains unimplemented, deferred, or unqualified.
- **Completion:** exact commit/PR, PASS/FAIL/SKIP, limitations and next action.

## Execution
Build → Test → Fix → Retest → Commit. Autonomous routine repairs; small PRs; maximum productive parallelism for disjoint tasks within authorized S01, with one integration owner for shared files; no bulk history/corpus import; no new multi-repo governance system. No paid calls/cloud/effects/releases. Historical evidence stays in old repos.

## Current authorization
**No work beyond S06 is authorized.** S01 to S05 are complete; the state of S06 (consolidation) is whatever [sprint-status.md](sprint-status.md), the only live status document, records. Each sprint was authorized by its own dated decision under `docs/decisions/` (the plan's "NOT AUTHORIZED" headings are static text). A new rule family, shared ISS/OCS registry work, dynamic activation, approval of a manifest selection pin, publication, production and formal independent qualification need a new operator decision. Read [trust-limitations.md](trust-limitations.md) before any new work. Historical note: this section previously read "S01 ONLY"; the g8-r10 tuple was operator-selected under D1 (see [decisions](decisions/2026-10-24-operator-decisions-D1-D5.md)).

## Anti-drift check
Before any new PR or sprint, read the static plan and latest dated decisions. If work lies outside the authorized sprint, record it as a future candidate rather than silently implementing. Changes to the static plan require a new numbered revision and operator decision, never an in-place rewrite to match work already performed.
