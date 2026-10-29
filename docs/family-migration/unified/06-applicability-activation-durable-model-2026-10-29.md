# Applicability and the required host-owned durable activation model (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (independent Tier 1 qualification is DEFERRED, NOT WAIVED). Governing documents: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ENGINEERING_CONSTITUTION.md`, `ADOPTION.md`), Static Migration Plan v1.1 (section 12), Engineering Plan v1.5, audit #60, assessments #65/#67, target architecture and contract specification v1.0 (Registry PR #68, merge `d7eb6be2ccc5614fcfb2be68422c04d9c8a11037`).

**Honest status: DESIGN ONLY.** Nothing below is implemented or operational. The only implemented control is `GovernedActivationLedger`, which is local, in-process and **advisory**. It stays advisory until a durable boundary is implemented AND qualified. No statement in this repository claims deployment-wide enforcement.

## 1. Effective-configuration identity (implemented, per workflow)
For a workflow the identity covers: the host profile digest; each declared family's contract version, family id, family schema revision, Registry record digest, selection id and epoch, and effective-policy digest; the constructor scalars where a family governs them; and the final effective-profile digest. The set of declared families is itself part of the identity, so removing a family changes it. The claim is made last and atomically. (Implemented for F4/F5/r08-v6 families; r08-v7 irreversibility joins the same identity.)

## 2. Required host-owned durable model (REQUIRED BEFORE any deployment-wide claim)
| Requirement | Required behaviour | Status |
|---|---|---|
| Scope key | One authoritative governed configuration per `(consumer_id, tenant_id, institution_id, authority_domain, operation_id)` plus host action/action-class mapping | NOT IMPLEMENTED |
| Single writer | Compare-and-set activation record in a host durable store, keyed by scope; activation binds the configuration identity above | NOT IMPLEMENTED |
| Cross-process conflict | Two processes activating different identities for one scope: the second is refused (`activation_conflict`), never merged | NOT IMPLEMENTED (advisory ledger is per-process) |
| Supersession | A new identity replaces the old only by an authenticated higher epoch for every declared family; downgrade refused | NOT IMPLEMENTED (epoch floors are a selection-source duty) |
| Withdrawal and revocation | A withdrawn/revoked mandatory selection deactivates the whole configuration (all-or-nothing); the workflow refuses until a new complete configuration is activated | Per-boundary refusal IMPLEMENTED; durable deactivation NOT |
| Restart and recovery | On start, the process loads the durable record, rebuilds the workflow from the SAME declared families and compares identities; any mismatch refuses; no fallback to a weaker configuration | NOT IMPLEMENTED |
| Partial-family activation | Refused: the declared family set is part of the identity and every declared family is mandatory | IMPLEMENTED per workflow |
| Bypass | A plain `BoundedAuthorizationWorkflow` built without Registry cannot be detected by this adapter | OPEN host duty |

The activation store must not become a new authority: it records what the host chose; it never approves, issues, revokes or executes. The decision of WHERE it lives (host database, not Registry) and who may write it is an Architect decision (D-09/D-10 below).
