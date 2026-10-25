# 1. Executive implementation proposal

Status: planning only; nothing here authorizes implementation. See [README](README.md) for gate G-0 (the inventory baseline is unmerged).

## Proposal in one paragraph

Build a governed configuration capability for the **Execution Runtime** and the **Control Plane** by externalizing **nine** typed values, while leaving every existing evaluator, floor and guardrail in code. The registry holds typed, versioned, authenticated *narrowing* data. Each enforcing component owns activation and its high-water state; the selection issuer assigns epochs; the registry never activates and never issues grants (ADR-REG-TR01). Everything reuses the existing R08-S01 verification and decision layers and the existing Runtime atomic-destination extension seam. There is no universal interpreter and no second enforcement engine.

**Nine fields:** five mandatory (`allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`) and four conditional (`max_amount`, `status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`). The manifest holds 96 rows; the other 87 stay code, stay deferred or are not relevant to V1 (see [03](03-field-extraction-register.md)).

## Recommendation, stated plainly

1. **Adopt as V1 acceptance scope: the five mandatory fields plus the three Control Plane freshness ages (eight fields).** The ages are plain integer seconds in source, only ever tighten, and are low in cost (see [03](03-field-extraction-register.md)).
2. **Keep `max_amount` designed but not in V1 acceptance.** It needs a ruling that the caller's value stays authoritative (D6) and a numeric encoding, and it must stay single-unit. It is specified in [04](04-component-ownership-and-adapter-matrix.md) so that it can be added later without redesign; activation is a separate decision.
3. **Scope the integration to Route B (the atomic Runtime route).** Route A cannot be closed at the commit boundary with the available mechanism. Whether Route A is in the V1 profile is an operator decision ([09](09-operator-scope-decision.md)).
4. Everything produced would be developer-tested only and **not independently qualified** until an independent lead is designated (GAP-G4-13). Nothing described here is built yet.

## Answers to the ten integration questions

**1. Which existing components require changes?**

| Component | Change | Source edit constraint |
|---|---|---|
| Registry (`cognous-ocs-registry`) | Family dispatch, `r08-v2` five-set payload, integer/capped-min slots, identity object, snapshot-version floor, real Ed25519 verifier adapter, conformance kit, emulator integration gate | Frozen `registry_contract`, `registry_consumer`, `baseline/` stay byte-identical |
| Execution Runtime | Narrowing adapter (new file), characterization tests; later an additive in-transaction guard in `local_authority_effect.py` and a passthrough in `atomic_local_control_plane_executor.py`, plus a new destination module | **Zero edits to `engine/safe_executor.py`**: it is the pinned evaluator, and any edit invalidates every pin, record and S05 expectation |
| Control Plane | Test-only characterization, a pure `age_bounds` helper, host-side wiring for F4 then F5 | No edit to `bounded.py`; narrowing is applied before construction (Runtime copies the age attributes, so a new kwarg would silently revert) |
| Qualification repo | Predeclared independent oracle batteries (docs/data, then tests) | No expectation edits |
| Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest | None. They carry policy identity opaquely if at all | Not read; UNVERIFIED |

**2. What exact capabilities will V1 provide?** See [02](02-v1-capability-profile.md): authenticated, narrow-only central governance of the five Runtime allow-lists and the three Control Plane freshness ceilings; consumer-owned activation with anti-rollback; exact effective-policy identity in committed evidence; required-versus-optional participation with fail-closed refusal; revocation and expiry rechecked under the lock on Route B; durable negative evidence; documented restore behaviour.

**3. What is excluded?** See [02](02-v1-capability-profile.md) and [08](08-exclusions-and-residual-risks.md): no central spend ceiling (unless `max_amount` is added), no central target scoping, no agent permissions, no dedupe/TTL, redaction or lease tuning, no Route A commit-time guarantee, no operational trust root, no GCR integration, no release or production.

**4. Which existing contracts are reused?** R08-S01 `r08-v1` verification (ten layers), decision kinds, composition and `PolicyDecision`; `TrustSnapshot.min_epochs`; ADR-REG-TR01 ownership; P0 extractability test; the Runtime `operation_id` guard seam as precedent; `LocalExecutionPolicy.check` order and reason texts; Control Plane `_fresh`, the approval commitment and the single-effect gate. Detail in [04](04-component-ownership-and-adapter-matrix.md).

**5. What is the minimum PR sequence?** Thirty-odd bounded PRs across six sprints; the first, `EXT-S1-1`, is a docs-only contract-delta ADR. See [06](06-pr-and-sprint-execution-plan.md).

**6. Which workstreams can execute in parallel?** Runtime characterization tests (`EXT-S2-1`), Control Plane characterization and helper (`EXT-S3-1`, `EXT-S3-2`), the Ed25519 adapter, the conformance kit, S4 drafting, and the independent oracle predeclaration all start without waiting for registry code. See [05](05-contract-and-integration-dependency-graph.md).

**7. Which dependencies force serialization?** The contract freeze; shared registry core files (`common.py` CODES, `decision.py`, `verify.py`); the two shared Runtime files; the exact-source-candidate selection (R10-F-03); the F4-then-F5 order; any head change, which invalidates evidence at the old tuple.

**8. What are the independent acceptance gates?** QG-01..QG-14 in [07](07-independent-qualification-matrix.md), derived from the existing 13-gate inventory matrix. None is met today.

**9. What existing tests establish each gate?** Mapped in [07](07-independent-qualification-matrix.md) and `data/qualification-gate-matrix.json`, with their true statuses. For gates QG-05, 08, 09 and 10 there is nothing to execute until R09/R10-class code exists.

**10. What are the remaining residual risks?** [08](08-exclusions-and-residual-risks.md): no operational trust root or independent lead, Route A open, new durable mutable state, restore rolls back high-water and revocations together, builder-only oracles, and several unruled decisions.

## Stop gates (nothing proceeds past a gate that is not recorded)

| Gate | Condition | Opens |
|---|---|---|
| G-0 | PR #227 merged, or Architect accepts head `64b4942b`; re-pin if the head moves | Acceptance of this plan |
| G-1 | Architect accepts this integrated plan | Operator scope decision |
| G-2 | Operator approves the V1 capability scope ([09](09-operator-scope-decision.md)) | Any implementation PR |
| G-3 | `EXT-S1-1` ADR accepted by the Architect | S1 code PRs and S2/S3 merges |
| G-4 | Architect disposition of R10-F-01/02/03 (carriage mechanism and exact source candidate) | `EXT-S4-2` |
| G-5 | Rulings D4, MC-06 G2/G3, W8-014 recorded (and D6 plus encoding for `max_amount`) | The conditional PRs that depend on them |
| G-6 | Independent qualification lead designated in writing | S5 in non-PREPARE mode |
| G-7 | Release, publication, production: HOLD stays until the operator lifts it | Never inferred |

## Estimated effort and major uncertainties

Planning estimates in engineer-days (judgement, not measured; ranges are wide on purpose). They exclude operator and independent-lead scheduling latency.

| Sprint | Estimate | Main uncertainty |
|---|---|---|
| S1 registry foundation | 14 to 22 | Real Ed25519 adapter and hash-lock change; `r08-v2` surface |
| S2 Runtime adapter | 5 to 8 | Characterization coverage for institution/domain/adapter that does not exist at the pin |
| S3 Control Plane adapter | 6 to 10 | F5 approval-commitment coupling; floor value; extension override ruling |
| S4 integration | 14 to 22 | New durable state, kwarg-carriage not yet tested, source-candidate churn |
| S5 independent qualification | 15 to 25 | No lead designated; oracle independence; race/clock gates need repetition |
| S6 release-candidate evidence | 4 to 6 | Any head change reopens gates |
| **Total (8-field V1)** | **58 to 93** | Add 4 to 7 if `max_amount` is added |

With three builders in parallel and one independent author, the critical path is roughly 9 to 13 calendar weeks. The path is set by serialized registry core edits and the S4 integration gate, not by Runtime or Control Plane work.

## Items for the Architect, not the operator

D4 per-scalar minimum; MC-06 G2 ("no cross-bound required") and G3 (integer seconds for ages); the age floor value; W6-042 (the 300 is `ObservationPolicy`, not these fields); W8-014; whether a signed outage extension may lift a registry-narrowed bound; `r08-v2` versioning; B-10 verifier and dependency; LD-02 mapping; R10-F-01/02/03, including the B-lite kwarg-carriage departure from R10's wording; DT-01 emulator host placement; custody review of the new mutable destination state. See [05](05-contract-and-integration-dependency-graph.md).
