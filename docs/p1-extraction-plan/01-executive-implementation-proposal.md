# 1. Executive implementation proposal

Status: planning only; scope approved (eight fields, atomic Route B only, rulings R1 to R14); nothing here authorizes implementation. See [README](README.md) and [09](09-operator-scope-decision.md).

## Proposal in one paragraph

Build a governed configuration capability for the **Execution Runtime** and the **Control Plane** by externalizing **eight** typed values, while leaving every existing evaluator, floor and guardrail in code. The registry holds typed, versioned, authenticated *narrowing* data. Each enforcing component owns activation and its high-water state; the selection issuer assigns epochs; the registry never activates and never issues grants or approvals (ADR-REG-TR01). Everything reuses the existing R08-S01 verification and decision layers as a strict additive `r08-v2` successor and the existing Runtime atomic-destination extension seam. The effect-time guarantee is **claim-carried**: the Control Plane issues a successor claim carrying the effective policy identity and the Runtime independently validates it against Runtime-held state under its own lock (R11). There is no universal interpreter and no second enforcement engine.

**Eight fields (approved):** five Runtime allow-lists (`allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`) and three Control Plane freshness bounds (`status_max_age_seconds`, `approval_max_age_seconds`, `ActionClass.max_status_age_seconds`). The manifest holds 96 rows; the other 88 stay code, stay deferred or are not relevant to V1, including `max_amount` (deferred extension, R7); see [03](03-field-extraction-register.md).

## Approved scope, stated plainly

1. **V1 capability scope is Option B (eight fields).** The ages are plain integer seconds in source, only ever tighten, and are validated strictly with code-owned bounds (R1 to R3).
2. **`max_amount` is outside V1.** Its code-owned enforcement is retained and the D6 analysis is preserved for a later profile; no monetary encoding decision is made now (R7).
3. **V1 execution scope is the atomic Route B only.** Route A is excluded from the registry-mediated effect-time guarantee; its existing behaviour and residual risk are documented, not weakened and not claimed protected ([08](08-exclusions-and-residual-risks.md)).
4. Everything produced is developer-tested only and **not independently qualified** until an independent lead is designated (GAP-G4-13). Nothing described here is built yet.

## Answers to the ten integration questions

**1. Which existing components require changes?**

| Component | Change | Source edit constraint |
|---|---|---|
| Registry (`cognous-ocs-registry`) | `r08-v2` in new files (dispatch, F1/F4/F5 families, identity object, snapshot-version floor), Ed25519 verifier adapter, conformance kit, emulator integration host (R12), registry test CI | `r08-v1` files, frozen `registry_contract`, `registry_consumer`, `baseline/` stay byte-identical |
| Execution Runtime | Narrowing adapter (new file), characterization tests; **mandatory** policy-bound atomic destination with selection-state tables and in-transaction validation (`local_authority_effect.py` inert hooks, executor opt-in passthrough) | **Zero edits to `engine/safe_executor.py`** (R14): it is the pinned evaluator |
| Control Plane | **Mandatory** successor claim carrying `policy_binding` (`EXT-S4-4`); R6 extension-cap source change (`EXT-S3-5`); a pure `age_bounds` helper and host wiring for F4 then F5 | Narrowing is applied before construction (Runtime copies the age attributes, so a new kwarg would silently revert); the only `bounded.py` edit is the R6 cap |
| Qualification repo | Predeclared independent oracle batteries (docs and data, then tests) | No expectation edits |
| Exchange, Replay, Evidence Pack, ODES, Verifier, BitRep, Index, Action Manifest | None. They carry policy identity opaquely if at all | Not read; UNVERIFIED |

**2. What exact capabilities will V1 provide?** See [02](02-v1-capability-profile.md): authenticated, narrow-only central governance of the five Runtime allow-lists and the three Control Plane freshness ceilings; consumer-owned activation with anti-rollback; exact effective-policy identity in committed evidence; required-versus-optional participation with fail-closed refusal; revocation, expiry, epoch and identity independently validated under the lock on Route B; durable negative evidence; documented restore behaviour.

**3. What is excluded?** See [02](02-v1-capability-profile.md) and [08](08-exclusions-and-residual-risks.md): no central spend ceiling, no central target scoping, no agent permissions, no dedupe/TTL, redaction or lease tuning, no Route A effect-time guarantee, no operational trust root, no GCR integration, no release or production.

**4. Which existing contracts are reused?** R08-S01 `r08-v1` verification (ten layers) and decision kinds as the base for the additive `r08-v2`; `TrustSnapshot.min_epochs`; ADR-REG-TR01 ownership; the P0 extractability test; the Runtime `BEGIN IMMEDIATE` path and the operation-identity destination pattern; `LocalExecutionPolicy.check` order and reason texts; Control Plane `_fresh`, the approval commitment and the single-effect gate. Detail in [04](04-component-ownership-and-adapter-matrix.md).

**5. What is the minimum PR sequence?** Twenty-two S1 to S4 PRs (including one non-code checks confirmation), nine S5 PRs and six S6 PRs, plus optional hardening and budgeted remediation; the first, `EXT-S1-1`, is a docs-only ADR. The sequence, with a per-PR card, is in [06](06-pr-and-sprint-execution-plan.md).

**6. Which workstreams can execute in parallel?** Runtime characterization (`EXT-S2-1`), Control Plane characterization and helper (`EXT-S3-1`, `EXT-S3-2`), the R6 cap, the Ed25519 adapter, the conformance kit, S4-0 drafting, the Control Plane claim binding against a fixture binding, and the independent oracle predeclaration. See [05](05-contract-and-integration-dependency-graph.md).

**7. Which dependencies force serialization?** The ADR freeze; **the Control Plane claim binding before the Runtime destination (mandatory)**; shared registry `v2_*` files; the `EXT-S3-2` bounds table before the registry F4/F5 merge; F4 then F5 and the R6 cap before F5 wiring; one open source PR per shared Control Plane file; one owner for the two Runtime atomic files; any head change, which invalidates evidence at the old tuple.

**8. What are the independent acceptance gates?** QG-01..QG-16 in [07](07-independent-qualification-matrix.md) (QG-02 deferred, QG-15/16 new), with negative controls NX-01..12. None is met today.

**9. What existing tests establish each gate?** Mapped in [07](07-independent-qualification-matrix.md) and `data/qualification-gate-matrix-v2.json`, with their true statuses. For gates QG-05, 06 (effect level), 08, 09, 10 and 16 there is nothing to execute until the S1/S4 code exists.

**10. What are the remaining residual risks?** [08](08-exclusions-and-residual-risks.md): no operational trust root or independent lead, Route A open and excluded, new durable mutable state, restore rolling back high-water and revocations together, builder-only oracles, digest-profile and constant proposals awaiting ADR ratification.

## Stop gates (nothing proceeds past a gate that is not recorded)

| Gate | Condition | Status |
|---|---|---|
| G-0 | Inventory baseline | **Closed.** PR #227 merged at `be1994a9`; provenance and reconciliation in [03](03-field-extraction-register.md) |
| G-1 | Architect accepts the integrated plan | Closed by the Architect's finalization directive; this PR records the corrections |
| G-2 | Operator approves the V1 capability scope | **Closed.** Option B and atomic Route B only ([09](09-operator-scope-decision.md)) |
| G-2b | Implementation authorization | **Open.** Follows separately; no `EXT-` PR starts before it |
| G-3 | `EXT-S1-1` ADR accepted by the Architect | Open |
| G-4 | `EXT-S4-0` ADR accepted: binding schema, digest profile, closed codes, claim profile URN | Open. Replaces the earlier carriage-mechanism disposition: carriage is decided (claim-carried, R11) |
| G-5 | Age constants (`AGE_MAX`, any host floor) confirmed by a Control Plane owner survey | Open. The rulings R1 to R6 are recorded; only the constants remain |
| G-6 | Independent qualification lead designated in writing | Open. S5 stays PREPARE-only until closed |
| G-7 | Release, publication, production | **HOLD** until the operator lifts it; never inferred |

## Estimated effort and major uncertainties

Planning estimates in engineer or author days (judgement, not measured; ranges are wide on purpose). They exclude operator and lead scheduling latency. Per-sprint figures and the critical path are in [06](06-pr-and-sprint-execution-plan.md).

| Sprint | Estimate | Main uncertainty |
|---|---|---|
| S1 registry foundation | 31 to 46 | `r08-v2` surface, port drift, Ed25519 hash-lock, registry CI |
| S2 Runtime adapter | 5 to 8 | Characterization coverage that does not exist at the pin |
| S3 Control Plane adapter | 15 to 21 | `AGE_MAX` survey; R6 vocabulary change; F5 approval coupling |
| S4 claim-bound integration | 25 to 37 | New durable Runtime state and custody; Control Plane claim change moves both heads |
| S5 independent qualification | 53 (+ up to 9 remediation) | No lead designated; oracle independence; race and clock gates need repetition |
| S6 closeout | 15 | Any head change reopens gates |
| **Total (8-field V1)** | **144 to 189** | Supersedes 58 to 93; `max_amount` adds nothing (deferred) |

Roughly 12 to 16 calendar weeks with three builders and one independent author. The path is set by the mandatory Control Plane to Runtime claim-binding chain and its meeting with the registry chain at the S4 gate.

## Items for the Architect, not the operator

Ratification at the ADRs, not new operator questions: the `EXT-S4-0` choices (claim profile URN and member names, digest profile with a non-ASCII vector, closed codes, tenant and operation mapping, digest-only versus carrying the sets in the claim, whether optional hardening H-1 is in V1, the structured carrier for the registry cause, the stale-sync disposition); the age constants after the owner survey; the LD-02 granularity and vocabulary questions; custody review of the new mutable destination state; and review of any change to the eight-field scope, the atomic-route boundary, authority ownership or an ADR decision. See [05](05-contract-and-integration-dependency-graph.md).
