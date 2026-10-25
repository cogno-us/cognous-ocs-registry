# 1. Executive implementation proposal

Status: planning only; nothing here authorizes implementation. Planning approval, implementation authorization and independent qualification are separate. The inventory baseline is merged and accepted (README, gate G-0 closed; inventory merge commit `be1994a961e4e40612d999972ede6547a3729887`). The operator has approved the V1 scope below; the Architect rulings that settle the earlier open decisions are recorded in [10](10-architect-rulings-and-repin.md).

## Proposal in one paragraph

Build a governed configuration capability for the **Execution Runtime** and the **Control Plane** by externalizing **eight** typed values, while leaving every existing evaluator, floor and guardrail in code. The registry holds typed, versioned, authenticated *narrowing* data. Each enforcing component owns activation and its high-water state; the selection issuer assigns epochs; the registry never activates and never issues grants (ADR-REG-TR01). Everything reuses the existing R08-S01 verification and decision layers and the existing Runtime atomic-destination extension seam. There is no universal interpreter and no second enforcement engine.

**Eight fields (operator-approved, Option B):** five Runtime allow-lists (`allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`) and three Control Plane freshness ages (`status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`). **`max_amount` is DEFERRED**: it is not a V1 task, not a V1 release blocker, and no inactive slot for it is built. The merged manifest holds 96 rows for 95 distinct fields; the other rows stay code, stay deferred or are not relevant to V1 (see [03](03-field-extraction-register.md)).

## Approved scope and plain statements

1. **V1 scope: Option B, eight configurable fields, atomic Route B only** (operator-approved; not reopened here).
2. **`max_amount` is deferred.** Its design notes remain in [04](04-component-ownership-and-adapter-matrix.md) and [08](08-exclusions-and-residual-risks.md) so it can be authorized later without redesign. Deferred functionality is documented and never a release blocker.
3. **Route B (the atomic Runtime route) only.** Route A cannot be closed at the commit boundary with the available mechanism and is outside V1; the status report says so plainly.
4. **Commit-time binding is claim-carried** (Architect ruling): B-lite keyword-argument carriage is rejected and `EXT-S4-4` (Control Plane claim-carried binding and successor profile, with re-pinning of both repositories) is mandatory. See [10](10-architect-rulings-and-repin.md).
5. Everything produced would be developer-tested only and **not independently qualified** until an independent lead is designated (GAP-G4-13). Until then qualification work is PREPARE-only. Nothing described here is built yet.

## Answers to the ten integration questions

**1. Which existing components require changes?**

| Component | Change | Source edit constraint |
|---|---|---|
| Registry (`cognous-ocs-registry`) | Family dispatch, `r08-v2` five-set payload, integer/capped-min slots, identity object, snapshot-version floor, real Ed25519 verifier adapter, conformance kit, emulator integration gate | Frozen `registry_contract`, `registry_consumer`, `baseline/` stay byte-identical |
| Execution Runtime | Narrowing adapter (new file), characterization tests; later a new destination module with an additive in-transaction guard that reads the claim-carried binding, and a passthrough in `atomic_local_control_plane_executor.py` | **Zero edits to `engine/safe_executor.py`**: it is the pinned evaluator, and any edit invalidates every pin, record and S05 expectation |
| Control Plane | Test-only characterization, a pure `age_bounds` helper, host-side wiring for F4 then F5, **and claim-carried effective-policy binding with a successor claim profile (`EXT-S4-4`, mandatory)**; both repositories re-pin | No edit to `bounded.py`; narrowing is applied before construction (Runtime copies the age attributes, so a new kwarg would silently revert); the claim-carried binding is additive and must not alter the existing claim for callers that do not use it |
| Qualification repo | Predeclared independent oracle batteries (docs/data, then tests) | No expectation edits |
| Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest | None. They carry policy identity opaquely if at all | Not read; UNVERIFIED |

**2. What exact capabilities will V1 provide?** See [02](02-v1-capability-profile.md): authenticated, narrow-only central governance of the five Runtime allow-lists and the three Control Plane freshness ceilings (status age, approval age, per-class status age; strict integer seconds, per-scalar `min`, no universal floor and no cross-bound); consumer-owned activation with anti-rollback; exact effective-policy identity in committed evidence; required-versus-optional participation with fail-closed refusal; revocation and expiry rechecked under the lock on Route B; durable negative evidence; documented restore behaviour.

**3. What is excluded?** See [02](02-v1-capability-profile.md) and [08](08-exclusions-and-residual-risks.md): no central spend ceiling (`max_amount` deferred), no central target scoping, no agent permissions, no dedupe/TTL, redaction or lease tuning, no Route A commit-time guarantee, no operational trust root, no GCR integration, no release or production.

**4. Which existing contracts are reused?** R08-S01 `r08-v1` verification (ten layers), decision kinds, composition and `PolicyDecision`; `TrustSnapshot.min_epochs`; ADR-REG-TR01 ownership; P0 extractability test; the Runtime `operation_id` guard seam as precedent; `LocalExecutionPolicy.check` order and reason texts; Control Plane `_fresh`, the approval commitment and the single-effect gate. Detail in [04](04-component-ownership-and-adapter-matrix.md).

**5. What is the minimum PR sequence?** About thirty bounded PRs across six sprints (S1 to S6); the first, `EXT-S1-1`, is a docs-only contract-delta ADR; `EXT-S4-4` is mandatory. The final sequence and its critical path are in [06](06-pr-and-sprint-execution-plan.md) and [05](05-contract-and-integration-dependency-graph.md).

**6. Which workstreams can execute in parallel?** Runtime characterization tests (`EXT-S2-1`), Control Plane characterization and helper (`EXT-S3-1`, `EXT-S3-2`), the Ed25519 adapter, the conformance kit, S4 drafting, and the independent oracle predeclaration all start without waiting for registry code. See [05](05-contract-and-integration-dependency-graph.md).

**7. Which dependencies force serialization?** The contract freeze; shared registry core files (`common.py` CODES, `decision.py`, `verify.py`); the two shared Runtime files; the exact-source-candidate selection (R10-F-03); the F4-then-F5 order; any head change, which invalidates evidence at the old tuple.

**8. What are the independent acceptance gates?** QG-01..QG-14 in [07](07-independent-qualification-matrix.md), derived from the existing 13-gate inventory matrix; all 14 are retained (QG-02 is retained but inactive while `max_amount` is deferred). None is met today.

**9. What existing tests establish each gate?** Mapped in [07](07-independent-qualification-matrix.md) and `data/qualification-gate-matrix.json`, with their true statuses. For gates QG-05, 08, 09 and 10 there is nothing to execute until R09/R10-class code exists.

**10. What are the remaining residual risks?** [08](08-exclusions-and-residual-risks.md): no operational trust root or independent lead, Route A open, new durable mutable state, restore rolls back high-water and revocations together, builder-only oracles, and several unruled decisions.

## Gates (nothing proceeds past a gate that is not recorded)

| Gate | Condition | Status | Opens |
|---|---|---|---|
| G-0 | Inventory baseline merged | **CLOSED**: PR #227 merged, `be1994a961e4e40612d999972ede6547a3729887` | Acceptance of this plan |
| G-1 | Architect accepts this integrated plan | Architect finalizing in this revision; acceptance is recorded by the PR #22 merge | Operator scope decision |
| G-2 | Operator approves the V1 capability scope | **CLOSED**: Option B, eight fields, Route B only ([09](09-operator-scope-decision.md)) | Planning of implementation PRs |
| G-3 | `EXT-S1-1` ADR accepted by the Architect; it records the exact source candidate (R10-F-03) | OPEN | Every source edit in S1, S2 and S3 (test-only PRs merge after it) |
| G-4 | R10-F-01/02/03 disposition (carriage mechanism and exact source candidate) | **Carriage RULED**: claim-carried, B-lite rejected, `EXT-S4-4` mandatory. The exact source candidate (R10-F-03) is recorded earlier, in `EXT-S1-1` (G-3) | `EXT-S4-2` |
| G-5 | Rulings D4, MC-06 G2/G3, W8-014 | **Recorded in [10](10-architect-rulings-and-repin.md)** (per-scalar min; strict integer seconds; no universal floor; no cross-bound; approval binds to the effective narrowed profile; outage extensions cannot widen). `max_amount` rulings (D6, encoding) are deferred with the field | The conditional PRs that depend on them |
| G-6 | Independent qualification lead designated in writing | OPEN; qualification is PREPARE-only until closed | S5 in non-PREPARE mode |
| G-7 | Release, publication, production: HOLD stays until the operator lifts it | HOLD | Never inferred |

**Implementation authorization is a separate act.** Merging this plan authorizes no EXT PR. The Architect issues the implementation authorization and builder handoff separately.

## Estimated effort and major uncertainties

Planning estimates in engineer-days (judgement, not measured; ranges are wide on purpose). They exclude operator and independent-lead scheduling latency.

| Sprint | Estimate | Main uncertainty |
|---|---|---|
| S1 registry foundation | 14 to 22 | Real Ed25519 adapter and hash-lock change; `r08-v2` surface; outcome map for all 46 codes |
| S2 Runtime adapter | 5 to 8 | Characterization coverage for institution/domain/adapter that does not exist at the pin |
| S3 Control Plane adapter | 6 to 10 | F5 approval-commitment coupling; validated per-scalar `min` helper |
| S4 integration | 18 to 28 | New durable state and its custody review; claim-carried binding across two repositories (`EXT-S4-4`) with re-pinning |
| S5 independent qualification | 15 to 25 | No lead designated (PREPARE-only until then); oracle independence; race/clock gates need repetition |
| S6 release-candidate evidence | 4 to 6 | Any head change reopens gates |
| **Total (8-field V1)** | **62 to 99** | `max_amount` (deferred) would add 4 to 7 later |

With three builders in parallel and one independent author, the critical path is roughly 10 to 14 calendar weeks. The path is set by serialized registry core edits and the S4 integration chain (`EXT-S4-0` to `EXT-S4-4` to `EXT-S4-3`), not by Runtime or Control Plane adapter work.

## Items still open for the Architect (not the operator)

`r08-v2` versioning details (additive; `r08-v1` behaviour preserved); B-10 verifier and dependency; LD-02 mapping; R10-F-03 exact source candidate (recorded in `EXT-S1-1`); DT-01 emulator host placement (ruled: Registry, not Qualification); custody review of the new mutable destination state. Settled rulings are in [10](10-architect-rulings-and-repin.md) and are not reopened. See [05](05-contract-and-integration-dependency-graph.md).
