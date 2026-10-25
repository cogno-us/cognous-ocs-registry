# Architect direction — post-S06 architectural direction (2026-10-24)

- Decision date: 2026-10-24 (as issued). GitHub recording time: this file's first commit; the direction was issued before it was recorded, and no retrospective approval date is claimed.
- Authority: **Architect direction**, relayed by the operator (André de Lima), who instructed the builder on 2026-10-24 to "just record the decision for now". This file is a builder transcription of text pasted into the Claude Code session, not independently countersigned. It is **not an operator authorization of any work**: it authorizes no implementation, and the builder was asked only to record it.
- Plan: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`, unchanged). Constitution pin: https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
- Context: follows the S06 closeout ([sprint-status.md](../sprint-status.md); PR #12 merge `03b4db319c2af03e883126448af89a0b77b3ea37`, closeout PR #14 merge `1870f3a62ee16cdea53c4c23a8df8c9be3c2f2cf`).

## Verbatim text

> OCS REGISTRY — POST-S06 ARCHITECTURAL DIRECTION
> Decision: Accept S06 closeout and record the six-sprint development program as complete within its bounded scope.
>
> 1. Retain S01–S06 results and frozen evidence without amendment.
> 2. Complete the historical rule-family classification and schema-fitness analysis in the separate, documentation-only workstream.
> 3. Evaluate F1 remaining allow-lists against F6 agent permissions and other justified candidates before selecting the next migration family.
> 4. Require a versioned successor contract for any material change to S03 representation or activation semantics.
> 5. Define explicit deny-all, optional-versus-mandatory refusal, record-selection authority, applicability and authentication requirements before introducing operational registry dependencies.
> 6. Preserve ISS and OCS canonical authority boundaries. Shared registry conventions do not transfer authority.
> 7. Do not approve a manifest pin, activate a registry record, wire Runtime, or implement a new rule family under this decision.
> 8. Return the proposed schema, migration scope, qualification requirements and operator decisions for separate authorization.
>
> S07 implementation: NOT AUTHORIZED.
> RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## Builder notes (recorded, not an expansion)

- Nothing in this file starts a workstream. Items 2, 3, 5 and 8 describe a separate documentation-only workstream that has not been assigned to this builder, with no scope, deliverable or file allowlist. It begins only on a separate authorization.
- Item 1 is honored: no S01–S06 result, frozen artifact or recorded evidence is amended by this file.
- Item 4 is consistent with [s06-representation-and-e05.md](../s06-representation-and-e05.md) section A, which recommends contract changes only as a separate, versioned decision.
- The "separate, documentation-only workstream" and COG-REG-SHARED-ADD-01 were not provided to this session. Nothing here relies on their content.
- No manifest pin is approved, no record is activated, the Runtime is not wired, and no rule family is implemented.
