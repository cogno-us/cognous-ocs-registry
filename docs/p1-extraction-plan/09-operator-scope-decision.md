# 9. Operator scope decision (recorded, plain language)

Status: **DECIDED.** The operator accepted the Architect's recommendations on 2026-10-25. This page records what was decided and what it does and does not mean. It authorizes no implementation: planning approval, implementation authorization and independent qualification stay separate, and the Architect issues the implementation authorization and builder handoff separately.

## What V1 lets your customers do

Today, the limits on what an agent runtime may do (which actions, adapters, units, institutions and authority domains) are written into each deployment by whoever builds it. V1 lets you set those limits centrally, in signed records that can **only make the limits tighter, never looser**. It also lets you tighten how old a status or approval may be before the Control Plane refuses to act on it. Every change is signed, versioned, revocable and recorded in the evidence with exact identity, and a missing or invalid required setting stops the action instead of falling back to something wider.

## Decision 1 (decided): which settings are in V1?

**Option B: eight configurable fields.**

| Owner | Fields |
|---|---|
| Runtime | `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains` |
| Control Plane | `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds` |

`max_amount` is **deferred**: it is not a V1 task, not a V1 release blocker, and the V1 profile is not expanded. Its design stays documented ([04](04-component-ownership-and-adapter-matrix.md), [08](08-exclusions-and-residual-risks.md)) so it can be authorized later. The Option A and Option C alternatives that were offered are not taken; the decision is not reopened here.

## Decision 2 (decided): does V1 cover both execution routes?

**No. V1 covers the atomic route only (Route B)**, and says so plainly in its status report. A registry-selected policy on the other route is not rechecked at the commit boundary.

## Consequences the operator was told about (no further decision needed)

- **Commit-time check is claim-carried** (Architect ruling, [10](10-architect-rulings-and-repin.md)). This adds a Control Plane change and requires re-pinning both repositories; it is planned as `EXT-S4-4`.
- **Built but off:** the capability to make a policy *mandatory* (refuse to act without it) is built inactive. Turning it on later is the operator's to authorize.
- **Independent qualification:** no independent qualification lead is designated. Until one is, qualification work is PREPARE-only and the result will be reported as "not independently qualified". Copilot review is technical review, not qualification.

Release, publication and production remain on HOLD. No trust root, key ceremony, credentialed run or paid test is requested.
