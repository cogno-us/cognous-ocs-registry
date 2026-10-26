# Operator adoption — Static Engineering Plan v1.5
Date: 2026-10-26
Status: **OPERATOR-APPROVED; effective upon merge**.

The operator directed: "create new static project plan, merge it, then give me prompt for fresh builder session", following the Architect finding that the original Registry objective was displaced by integration-contract work. This decision adopts the [v1.5 working-vertical-slice-first plan](../plans/PROJECT_PLAN-v1.5.md) with developer-only M1 first and secure, independently qualified M2 after. It supersedes **schedule and priority**, not contracts or historical evidence, of [v1.4](../plans/PROJECT_PLAN-v1.4.md) and [G0 Amendment 1](2026-10-26-amendment-1-plan-v1.4-g0-schedule.md).

**Source baseline:** Registry S01 merge `d1dedf79dfb82a25acdcd590c7d39830fa74ef17`; G0 `ea7fe24eb3fd2c310efc6a39f8dcc404fb4a1333`. Preserve adopted `r08-v2`/Amendment 1, TR-01, DR-CP-AGE-1, EXT-S4-0, MSOP-F1a-C11, Engineering Constitution pinned `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`. Old plans remain intact.

**Authorization boundary:** The instruction authorizes static plan authoring/adoption/merge and fresh-session handoff. It does not specifically authorize V01 implementation or any V02–V09 source changes, tests that cause effects, production, publication or release. V01 needs an explicit operator sprint authorization. Developer M1 is non-effecting and cannot be represented as operational or independently qualified enforcement.

**Holds:** Security review of Ed25519 #26/#34 OPEN; Tier 1 NOT STARTED; RELEASE / PUBLICATION / PRODUCTION HOLD. No new architectural grants or waived authority invariants.
