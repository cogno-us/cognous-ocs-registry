# P1 — Configuration-extraction design and execution plan

Status: **DOCUMENTATION ONLY. ARCHITECT-FINALIZED PLANNING BASELINE; OPERATOR SCOPE APPROVED (Option B, eight fields, atomic Route B only).** Planning approval, implementation authorization and independent qualification are three separate things: this plan is the first only. It is not an authorization to implement anything. It authorizes no sprint, no migration, no source change, no activation, and no change to any recorded test expectation. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

Governing plan: `docs/plans/PROJECT_PLAN-v1.3-DRAFT.md` (phase P1). Contract baseline: `docs/p0-contract-reconciliation/` and ADR-REG-TR01 (`docs/decisions/2026-10-25-adr-tr-01-activation-and-epoch-ownership.md`). Engineering constitution: pinned `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (formal adoption of that revision is not established; ledger `CONSTITUTION-REVISION-1C2E920F`).

## Stop gate G-0: closed. The inventory baseline is MERGED and ACCEPTED

`cogno-us/cognous-stack-qualification` PR #227 merged with merge commit `be1994a961e4e40612d999972ede6547a3729887` (final PR head `1b34db3442c70701d6ffad67db94a49492b1827b`). The Architect formally closed and accepted the inventory. **This plan now cites the merge commit as the authoritative inventory pin.** The earlier provisional pin, PR #227 head `64b4942b4c3cd142db26482af85cbaec024aa043` (earlier still `947db3d2`), is retained only as provenance of what the first draft of this plan was read against.

The merged inventory is analytical evidence, not independent operational qualification. Its canonical files for P1 are `docs/registry-v1-scope-assessment/09-configuration-extraction-handoff.md` and `docs/registry-v1-scope-assessment/data/configuration-extraction-manifest.{jsonl,csv}`.

Reconciled figures (merged inventory): 696 canonical scenarios and 162 suite-local claims recorded separately; 96 manifest rows representing **95 distinct underlying fields** (CP-F3-07 and CP-F4-13 are two rows for `FreshnessProfile.lease_acquire_timeout_seconds`, both UNRESOLVED, counted once); DIRECT 5, CONDITIONAL 17, UNRESOLVED 16, CODE_OWNED_GUARDRAIL 47, NOT_RELEVANT_TO_V1 11; Model A 9, Model B 22, Model B-only 13 (eligible-field counts, not qualification results). Nothing here re-runs the inventory.

## Deliverables (the nine required items)

| # | File | Content |
|---|---|---|
| 1 | [`01-executive-implementation-proposal.md`](01-executive-implementation-proposal.md) | The proposal, the ten integration answers, stop gates, effort |
| 2 | [`02-v1-capability-profile.md`](02-v1-capability-profile.md) | Exact V1 capability profile: what V1 provides, what it does not |
| 3 | [`03-field-extraction-register.md`](03-field-extraction-register.md) | Field-by-field register (8 V1 fields; `max_amount` deferred), deferred-family assessment, manifest corrections |
| 4 | [`04-component-ownership-and-adapter-matrix.md`](04-component-ownership-and-adapter-matrix.md) | Component ownership, adapters, reused contracts |
| 5 | [`05-contract-and-integration-dependency-graph.md`](05-contract-and-integration-dependency-graph.md) | Dependency graph, serial edges, parallel lanes, critical path |
| 6 | [`06-pr-and-sprint-execution-plan.md`](06-pr-and-sprint-execution-plan.md) | Ordered PR and sprint plan S1 to S6 with gates |
| 7 | [`07-independent-qualification-matrix.md`](07-independent-qualification-matrix.md) | Gates QG-01..14, test mapping, independence rules |
| 8 | [`08-exclusions-and-residual-risks.md`](08-exclusions-and-residual-risks.md) | Exclusions as lost customer capability, residual risks |
| 9 | [`09-operator-scope-decision.md`](09-operator-scope-decision.md) | The operator scope decision (approved: Option B, Route B only) in plain language |
| 10 | [`10-architect-rulings-and-repin.md`](10-architect-rulings-and-repin.md) | Architect rulings in force, re-pin record, inventory reconciliation, seven errata, EXT PR sequence summary |
| — | [`data/qualification-gate-matrix.json`](data/qualification-gate-matrix.json) | Machine-readable gate matrix (14 gates) |

## Source revisions (exact)

| Source | Revision | Use |
|---|---|---|
| `cogno-us/cognous-ocs-registry` | `d61ef729883c9c127cbd05b8f8a1a5944dc0e717` (`main`, merge of PR #21, P0) | Registry code, P0 ledger, ADR, R08/S03-S06 evidence |
| `cogno-us/cognous-execution-runtime` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | Runtime source (evaluator blob `engine/safe_executor.py` = `2fc880dae37eac76e5074533435740ce0684209d`, byte-identical to the S01/S03/S04 baseline) |
| `cogno-us/cognous-control-plane` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | Control Plane source |
| `cogno-us/cognous-stack-qualification` | merge commit `be1994a961e4e40612d999972ede6547a3729887` (inventory PR #227, accepted); base `main` before merge `998d39c5ba1c9d537be8289f7658f2e9cde6cbba`; historical provisional pin PR #227 head `64b4942b` (provenance only) | Scenario catalog, existing tests; merged inventory package |
| Hub `cognous-open-control-stack` | `51c579a3` | V0.2 program documents (not re-read for this plan) |

Source was read, not executed: **no repository test was run for this plan.** Two throwaway read-only probes were executed, writing nothing to any repository: a pydantic coercion probe on `ActionClass`, and construction of a `LocalExecutionPolicy` with an empty set. Every statement about a test's pass state is taken from recorded documents and is labelled accordingly. Components not read (Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest) are UNVERIFIED here.

## Vocabulary and evidence rules

- "Qualified" is never used for builder-tested or Copilot-reviewed results. "Frozen" means byte-pinned or decision-recorded.
- Known-limit tests are not PASS. NOT RUN stays NOT RUN. Historical `PASS_RECORDED` cases are at the g8-r10 pins, not at the current heads, and the scenario rows stay INCONCLUSIVE.
- "Required/advisory" (rule status) is kept distinct from "required/optional" (operation participation).
- Sprint labels S1..S6 are the planning labels the brief proposes. They collide with the historical sprints S01..S06 of plan v1.1; PR identifiers below use the prefix `EXT-` (for example `EXT-S1-3`) to avoid confusion.
- This directory duplicates neither the 696-scenario catalog nor the P0 ledger. Scenario IDs and ledger IDs are referenced, not restated.
