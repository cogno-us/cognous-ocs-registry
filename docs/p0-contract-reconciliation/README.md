# P0 — V0.2 contract reconciliation

Status: **DOCUMENTATION ONLY. CONDITIONALLY ACCEPTED by the OCS Architect; TR-01 remediation recorded (ADR-REG-TR01).** The findings are reconciliation findings, not independent qualification of any component implementation; P1 readiness is PASS for planning. No implementation, test, plan, component or pin is changed. Release, publication and production remain on HOLD. Nothing here activates, approves or qualifies anything.

Governing plan: `docs/plans/PROJECT_PLAN-v1.3-DRAFT.md` (operator-approved 2026-10-24; approval merge `ce00520f91bf3986a08b4d13a1fb062057babc71`), phase **P0**. Purpose: determine which cross-component governance and registry contracts V0.2 already established, reuse them, and isolate only genuine conflicts, missing contracts and unresolved authority boundaries.

## Artifacts

| # | File | Content |
|---|---|---|
| 1 | [`01-executive-findings.md`](01-executive-findings.md) | What is settled, reusable and genuinely open |
| 2 | [`02-contract-ledger.jsonl`](02-contract-ledger.jsonl) | Machine-readable ledger, 140 contracts (P0 review baseline 139 + 1 ADR row) (schema: [`02-contract-ledger.schema.json`](02-contract-ledger.schema.json); human index: [`02-contract-ledger-index.md`](02-contract-ledger-index.md)) |
| 3 | [`03-v0.2-to-v1.3-crosswalk.md`](03-v0.2-to-v1.3-crosswalk.md) | V0.2 R0 versus registry v1.2/R08/v1.3 semantics, eleven dimensions |
| 4 | [`04-authority-boundary-matrix.md`](04-authority-boundary-matrix.md) | Ownership and enforcement; R09/R10 established versus open |
| 5 | [`05-configuration-extraction-readiness.md`](05-configuration-extraction-readiness.md) | Reusable architecture and bounded technical prerequisites |
| 6 | [`06-targeted-conflict-register.md`](06-targeted-conflict-register.md) | The one genuine conflict, plus candidates examined and not counted |
| 7 | [`07-p1-handoff.md`](07-p1-handoff.md) | What P1 may rely on, and what it must not |
| 8 | [`../decisions/2026-10-25-adr-tr-01-activation-and-epoch-ownership.md`](../decisions/2026-10-25-adr-tr-01-activation-and-epoch-ownership.md) | Architect ADR-REG-TR01 (2026-10-25): architectural resolution of TR-01. Decision recorded; not implemented; not qualified |
| — | [`evidence/`](evidence/) | Raw lane outputs (A1–A3, B–E) and the status-resolution log, kept for audit |

## Source revisions (exact)

| Source | Revision | Note |
|---|---|---|
| `cogno-us/cognous-ocs-registry` | `ce00520f91bf3986a08b4d13a1fb062057babc71` | `main` at review time; PR #20 (plan v1.3 approval) merge |
| `cogno-us/cognous-open-control-stack` (hub) | `51c579a3208149922649a31a6eb041106a4121c3` | `main` at review time; V0.2 program in `docs/program-v0.2/` |
| `cogno-us/cognous-engineering-constitution` | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | Pinned reference only. Revision adoption for the stack is **not** established (ledger `CONSTITUTION-REVISION-1C2E920F`, UNVERIFIED) |
| `cogno-us/cognous-stack-qualification` | `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` | `main` at review time |
| Registry PR #19 (R08-S01) | merged 2026-10-25T05:07:45Z, head `f0765909b1aca44d149ec6bfe75966cb8a03c79b`, merge `783ff59f07d020d06e2ea9a32a257311527d9d82` | Verified through the GitHub REST API. `docs/sprint-status.md` still says "DRAFT PR" (stale). Merge is not approval or activation |

Reviews were read-only from shallow clones. Control Plane and Execution Runtime source trees were **not** read; line-level claims about them are second-hand from registry R08/R10 documents and are marked as such. No test was executed. See the source-verification limitation below.

## Vocabulary used in the ledger

Statuses (exact set from the P0 mission):

| Status | Meaning in this ledger |
|---|---|
| `ADOPTED_FROZEN` | A **decision record** exists (operator decision, M0 row, operator-approved plan, or recorded operator decision in this repository) that adopts the contract or principle. It does **not** mean the wire format is frozen byte-for-byte, and it does **not** mean qualified. Frozen registry sources (S03/S04) are byte-pinned by blob hash. |
| `IMPLEMENTED_NOT_QUALIFIED` | Code or data exists and is builder-tested. Builder tests and Copilot code review are not independent qualification. |
| `PROPOSED_ONLY` | A draft, candidate or architect default without an adopting decision record. Appearing in the V0.2 program is not adoption. |
| `SUPERSEDED` | Replaced by a later adopted record or withdrawn by a documented correction. |
| `CONFLICTING` | Source statements disagree in a way that matters for use of the contract. A conflicting *status label* is not necessarily a conflicting *contract* (see register). |
| `UNVERIFIED` | Evidence is missing or lives outside custody. Nothing is assumed. |

Dispositions: `REUSE_UNCHANGED`, `REUSE_WITH_ADAPTER`, `TARGETED_RECONCILIATION` (only these may create architecture work), `SUPERSEDED_BY_ADOPTED_CONTRACT`, `DEFER`.

Optional narrow field `architectural_resolution` (added in the TR-01 remediation) records an architectural resolution alongside a row's original historical `current_status` and `disposition`, which are not rewritten. It is set on `ACTIVATION-EPOCH-AUTHORITY-OWNER` and `REGISTRY-ACTIVATION-2.4-V02`. The new row `ADR-TR-01-ACTIVATION-EPOCH-OWNERSHIP` is `ADOPTED_FROZEN` meaning decision recorded; not implemented; not qualified.

`qualification_reference` is a free-text note, not a pointer to a qualification verdict. It is null or "None" where no qualification evidence exists, and otherwise records what was searched for or found (for example "No qualification record found", builder tests, Copilot review, or a bounded controller run). **No independent qualification of any registry contract exists** in the three repositories; a non-empty note is never evidence of independent qualification.

## Method

Seven short-lived read-only agents worked non-overlapping lanes: A1–A3 (V0.2 inventory: program top level and S01/S02; S03–S05 and AOI; repository-level contracts and the Constitution), B (registry R0 versus R08), C (authority and effect boundaries), D (configuration and guardrail partition), E (claim and evidence verification). The lead architect deduplicated 223 lane rows into 139 canonical contracts, resolved every status disagreement against the decision records (log: `evidence/status-resolution-log.json`; the rules were: a decision record must be cited for `ADOPTED_FROZEN`; on disagreement the lower-assurance reading wins unless a record is cited; a lane's own cited evidence overrides its label) and verified the final ledger mechanically (schema, closed vocabularies, non-null source repository/path/commit, decision reference present on every adopted row).

## Source-verification limitation

The P0 worker did **not** inspect Control Plane or Execution Runtime source. Claims about them are second-hand from registry R08/R10 documents. P0 establishes contract and decision reconciliation, not independent verification of implementation claims. P1 **must** directly inspect exact source revisions before accepting each configurable-field extraction mapping. No broad 15-component source audit is launched. No additional source was needed to establish TR-01 (a written-requirement conflict resolved by an ownership assignment).

## Revision history

1. `711a09ccbdd4757edc260248c5f6d7c7633c9c2d`: initial P0 reconciliation (139 contracts).
2. Remediation (2026-10-25): ADR-REG-TR01 recorded; ledger `architectural_resolution` field and ADR row added (140 contracts); P0 documents updated to reflect the Architect's conditional acceptance. Nothing implemented, activated or qualified.
