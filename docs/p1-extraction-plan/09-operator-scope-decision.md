# 9. Approved scope record (operator decisions)

## Decisions recorded

**OPTION B — APPROVED**

**ATOMIC ROUTE ONLY — APPROVED**

The operator accepted the Architect's recommendations on both scope questions. These decisions are final for the current planning baseline. The A/B/C comparison is not reopened and no further operator decision about V1 scope is requested. This page replaces the earlier decision request; the alternatives and exclusions are kept below as history.

Authorization status is unchanged: this record approves *scope*, not work. No implementation PR is authorized. Implementation authorization follows separately. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

## What V1 will provide (design intent; nothing is built)

Today the limits on what an agent runtime may do (which actions, adapters, units, institutions and authority domains) are written into each deployment by whoever builds it. V1 is designed to let those limits be set centrally, in signed records that can **only make the limits tighter, never looser**, and to let the Control Plane's freshness limits (how old a status or approval may be) be tightened the same way. Every configuration is versioned, authenticated, explicitly selected, narrowing only, bound to the component that enforces it, revocable, auditable, fail-closed when required, and independently qualifiable. Existing component evaluators stay authoritative, mandatory guardrails stay in code, and registry records never issue grants or approvals.

**The eight fields:** `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains` (Runtime) and `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds` (Control Plane). Field detail: [03](03-field-extraction-register.md).

**Execution scope:** V1 qualification covers the supported atomic effect route, Route B, only. Route A stays excluded from the registry-mediated effect-time guarantee; its existing behaviour and residual risk are documented in [08](08-exclusions-and-residual-risks.md), it is not weakened, and it is not claimed to be protected. Any later expansion to Route A needs separate scope approval and independent qualification.

## Explicit V1 exclusions (history preserved)

`max_amount` is **excluded** from V1 (ruling R7): its code-owned enforcement is retained unchanged and the D6 analysis is kept in [03](03-field-extraction-register.md) for a later profile; no monetary encoding decision is made now. Also deferred: F1d target prefixes, F6 agent permissions, F7 deduplication parameters, F3 resource budgets, F8 demo tool lists, F9 tenant-length parameters, F10 diagnostic thresholds, F11 configurable redaction. Deferral does not authorize weakening any existing control, and existing operation-identity and deduplication weaknesses remain independently tracked under their owning components. Deferred registry configuration is not absent OCS enforcement.

## History of the alternatives considered

| Option | Settings | Outcome |
|---|---|---|
| A | The five Runtime allow-lists | Not chosen. Smallest; freshness limits remain set per deployment |
| **B** | A plus three Control Plane freshness limits (status age, approval age, per-class status age) | **Approved.** Covers what a runtime may touch and how fresh the information behind a decision must be, without reopening spend-ceiling semantics |
| C | B plus the spend ceiling `max_amount`, single unit at a time | Not chosen. Needed an Architect ruling and a numeric-format decision first and could not support different ceilings per unit. Stays available as a later, separately approved extension |

| Route question | Outcome |
|---|---|
| Atomic route only | **Approved.** The registry-mediated check that the selected policy is still current at the moment of commit is designed for the atomic route only |
| Declare both routes in V1 | Not chosen. Route A's commit transaction reads no grant, claim, selection or epoch, so protecting it would need a larger redesign than this plan covers |

## Costs and dependencies (updated for mandatory claim-carried integration)

The Architect's ruling R11 makes the commit-time check **claim-carried and independently validated** by the Runtime under its own lock; the smaller keyword-argument option is rejected. The consequences, in plain terms:

- The Control Plane gains a successor claim carrying the policy identity, and the Runtime validates it against its own stored selection state at the commit. Both repositories change and are re-pinned; the Control Plane change lands first because the Runtime cannot run or test the new claim without it. This is mandatory work (`EXT-S4-4`, `EXT-S4-2`), and it, rather than the registry work, sets the critical path.
- A separate Control Plane source change (`EXT-S3-5`) is needed so a signed outage extension can never lift a freshness limit the registry narrowed (ruling R6).
- The registry gains a new strict-superset `r08-v2` contract in new files, with the existing `r08-v1` behaviour preserved byte for byte, a real signature-verifier adapter (synthetic keys only) and a snapshot-version floor.
- Effort (judgement, not measured): about 76 to 112 builder days across the four build sprints and about 68 to 77 independent-author days for qualification and closeout, which is about 144 to 189 in total; roughly 12 to 16 calendar weeks with three builders and one independent author. Details and uncertainties are in [06](06-pr-and-sprint-execution-plan.md). This replaces the earlier 58 to 93 days, which assumed the smaller carriage option; excluding `max_amount` removes the 4 to 7 days that option C would have added.
- No new spending, trust root, key ceremony, credentialed run or paid test is requested.

## What the operator is still asked for later (none needed to close P1)

Field formats, validation rules, numeric bounds, reason codes, adapter design, claim-binding mechanics, cryptographic details, test infrastructure and sequencing belong to the Architect and component owners and are settled in the plan or its ADRs. Only the following come to the operator, and only when they arise:

- **Mandatory-profile activation:** the capability to make a policy *mandatory* (refuse to act without it) is built inactive. Turning it on is the operator's to authorize.
- **Independent qualification:** no independent lead is designated. If none can be secured, the result will be reported as "NOT INDEPENDENTLY QUALIFIED"; that single fact, not any technical detail, would come to the operator.
- **Required status checks:** confirmation that the listed checks are required on the repositories (`EXT-S2-G`), because the branch-protection settings cannot be read from here.
- **Material departures** from the approved architecture, a major change to customer capability, new spending, and release, publication or production authorization.
