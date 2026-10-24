# OCS Registry — Mandatory Builder Handoff
**Every builder instruction, worker delegation, PR description and completion report must include both exact references:**

1. **Static plan:** https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/PROJECT_PLAN.md (OCS-REG-PLAN v1.0; until merged, cite the exact PR head/path).
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
Build → Test → Fix → Retest → Commit. Autonomous routine repairs; small PRs; max two workers; no bulk history/corpus import; no new multi-repo governance system. No paid calls/cloud/effects/releases. Historical evidence stays in old repos.

## Current authorization
**S01 ONLY — Historical baseline recovery.**
Use the existing S01 PR if suitable; add these governance docs there without widening its engineering objective. The g8-r10 tuple is a **proposed candidate**, not operator-approved simply because tests pass. Do not assert the narrow Runtime local-policy slice represents the entire historic OCS.
Stop after S01; submit evidence and ask for S01 disposition / S02 authorization. No automatic next sprint.

## Anti-drift check
Before any new PR or sprint, read the static plan and latest dated decisions. If work lies outside the authorized sprint, record it as a future candidate rather than silently implementing. Changes to the static plan require a new numbered revision and operator decision, never an in-place rewrite to match work already performed.
