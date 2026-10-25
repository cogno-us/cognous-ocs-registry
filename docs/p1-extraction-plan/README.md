# P1 — Configuration-extraction design and execution plan

Status: **DOCUMENTATION ONLY. SCOPE APPROVED (Option B, atomic Route B only). IMPLEMENTATION NOT AUTHORIZED.** This is one finite plan. It authorizes no sprint, no migration, no source change, no activation, and no change to any recorded test expectation. Implementation authorization follows separately. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

Governing plan: `docs/plans/PROJECT_PLAN-v1.3-DRAFT.md` (phase P1). Contract baseline: `docs/p0-contract-reconciliation/` and ADR-REG-TR01 (`docs/decisions/2026-10-25-adr-tr-01-activation-and-epoch-ownership.md`). Engineering constitution: pinned `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (formal adoption of that revision is not established; ledger `CONSTITUTION-REVISION-1C2E920F`).

## Approved scope and binding rulings (recorded, not reopened)

The operator accepted the Architect's recommendations: **V1 capability scope Option B (exactly eight fields)** and **V1 execution scope atomic Route B only**. Both are final for this planning baseline ([09](09-operator-scope-decision.md)). The Architect's rulings R1 to R14 and the empty-set rule are binding and are applied in documents 02 to 08; the most consequential are R11 (claim-carried policy binding is the authoritative effect-time mechanism; `EXT-S4-4` is mandatory; B-lite is rejected) and R14 (no edit to `engine/safe_executor.py`).

The eight fields: **F1a** `allowed_actions`, `allowed_adapters`, `allowed_units`; **F1b** `allowed_institutions`, `allowed_authority_domains`; **F4** `status_max_age_seconds`, `approval_max_age_seconds`; **F5** `ActionClass.max_status_age_seconds`. `max_amount` is outside V1 (R7).

## Inventory baseline: PR #227 is merged (gate G-0 closed)

`cogno-us/cognous-stack-qualification` PR #227 **merged**. Merge commit `be1994a961e4e40612d999972ede6547a3729887` (current `main`), final PR head `1b34db3442c70701d6ffad67db94a49492b1827b`. The baseline for this plan is the merge commit; provenance of the earlier analysis is preserved in [03](03-field-extraction-register.md): the plan's first draft was written against head `64b4942b4c3cd142db26482af85cbaec024aa043`, and the head moved through `a2718f30` to `1b34db34` before merge. The identities were not replaced silently: the 96-row manifest differs between `64b4942b` and the merge only by two empty columns on every row and one disposition change (`CP-F3-07` `CONDITIONAL_EXTRACTION` to `UNRESOLVED`, a duplicate of `CP-F4-13`). None of the eight V1 fields is affected. This workstream did not merge or modify PR #227.

## Deliverables

| # | File | Content |
|---|---|---|
| 1 | [`01-executive-implementation-proposal.md`](01-executive-implementation-proposal.md) | The approved proposal, the ten integration answers, stop gates, effort |
| 2 | [`02-v1-capability-profile.md`](02-v1-capability-profile.md) | Exact V1 capability profile: what V1 provides, what it does not |
| 3 | [`03-field-extraction-register.md`](03-field-extraction-register.md) | Eight-field register, deferred `max_amount` extension, errata, provenance |
| 4 | [`04-component-ownership-and-adapter-matrix.md`](04-component-ownership-and-adapter-matrix.md) | Ownership, adapters, claim-carried binding, three age-field contracts |
| 5 | [`05-contract-and-integration-dependency-graph.md`](05-contract-and-integration-dependency-graph.md) | Dependency graph, mandatory serial CP to Runtime edges, parallel lanes, critical path |
| 6 | [`06-pr-and-sprint-execution-plan.md`](06-pr-and-sprint-execution-plan.md) | Per-PR cards for S1 to S6, repo checks table, effort, critical path |
| 7 | [`07-independent-qualification-matrix.md`](07-independent-qualification-matrix.md) | Gates QG-01..16, negative controls NX-01..12, PREPARE-only rules |
| 8 | [`08-exclusions-and-residual-risks.md`](08-exclusions-and-residual-risks.md) | Exclusions as lost customer capability, Route A residual risk, residual risks |
| 9 | [`09-operator-scope-decision.md`](09-operator-scope-decision.md) | Approved scope record and history of alternatives |
| — | [`data/qualification-gate-matrix-v2.json`](data/qualification-gate-matrix-v2.json) | Machine-readable gate matrix (16 gates; supersedes the 14-gate draft) |
| — | [`data/ld02-outcome-map.json`](data/ld02-outcome-map.json) | LD-02 outcome map: 47 r08-v2 codes plus 4 decision kinds (proposal; ratified in the S1-1 ADR) |

## Source revisions (exact)

| Source | Revision | Use |
|---|---|---|
| `cogno-us/cognous-ocs-registry` | `d61ef729883c9c127cbd05b8f8a1a5944dc0e717` (`main`, merge of PR #21, P0) | Registry code, P0 ledger, ADR, R08/S03-S06 evidence |
| `cogno-us/cognous-execution-runtime` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | Runtime source (evaluator blob `engine/safe_executor.py` = `2fc880dae37eac76e5074533435740ce0684209d`, byte-identical to the S01/S03/S04 baseline; never edited, R14) |
| `cogno-us/cognous-control-plane` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | Control Plane source |
| `cogno-us/cognous-stack-qualification` | `main` `be1994a961e4e40612d999972ede6547a3729887` (merge of PR #227); the existing suites and the qualification-repo workflow pins were read at the earlier `main` `998d39c5ba1c9d537be8289f7658f2e9cde6cbba`, which is the parent of the merge on the first-parent line and differs from the merge only by the PR #227 package | Scenario catalog, existing tests; inventory package |
| Hub `cognous-open-control-stack` | `51c579a3` | V0.2 program documents (not re-read for this plan) |

Source was read, not executed: **no repository test was run for this plan.** Two throwaway read-only probes were executed, writing nothing to any repository (a pydantic coercion probe on `ActionClass`, and construction of a `LocalExecutionPolicy` with an empty set), plus read-only arithmetic probes on `timedelta`/`datetime` limits. Every statement about a test's pass state is taken from recorded documents and is labelled accordingly. Components not read (Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest) are UNVERIFIED here. Every implementation PR must re-pin against the heads current at its start ([06](06-pr-and-sprint-execution-plan.md)).

## Vocabulary and evidence rules

- "Qualified" is never used for builder-tested or Copilot-reviewed results. "Frozen" means byte-pinned or decision-recorded.
- Known-limit tests are not PASS. NOT RUN stays NOT RUN. Historical `PASS_RECORDED` cases are at the g8-r10 pins, not at the current heads, and the scenario rows stay INCONCLUSIVE.
- "Required/advisory" (rule status) is kept distinct from "required/optional" (operation participation).
- Sprint labels S1..S6 are the planning labels. They collide with the historical sprints S01..S06 of plan v1.1; PR identifiers use the prefix `EXT-` (for example `EXT-S1-3`).
- Statements of capability are written as design intent ("is designed to"), never as built or tested behaviour. The mechanism sections of [04](04-component-ownership-and-adapter-matrix.md) are source readings, not tested results.
- This directory duplicates neither the 696-scenario catalog nor the P0 ledger. Scenario IDs and ledger IDs are referenced, not restated.
