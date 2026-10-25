# Architect ADR (ADR-REG-TR01): activation and selection-epoch ownership

- Status: **ADOPTED by the OCS Architect, 2026-10-25.** Architectural resolution of P0 conflict TR-01. **Not implemented.** Nothing is activated, approved, qualified or released.
- Decided by: OCS Architect, under the technical decision rights delegated by plan v1.3 §8 ("V0.2 clause/status reconciliation … C-01 integration host identification … field schemas and versioning … Document source-backed decisions as ADRs"). Recorded by the P0 reconciliation worker from the Architect's instruction "FINALIZE P0, RECORD TR-01 ADR, PREPARE MERGE", issued on the reviewed head of PR #21 (`711a09ccbdd4757edc260248c5f6d7c7633c9c2d`). The instruction text is the primary source; quoted decisions below follow it.
- Not an operator decision: the operator-approved plan v1.3 (approval merge `ce00520f91bf3986a08b4d13a1fb062057babc71`) already adopts consumer-owned activation; this ADR introduces no departure from the existing OCS authority separation, no OCS/GCR choice, no spending and no release (plan v1.3 §8 items 1–4 are not triggered).
- Resolves: conflict **TR-01** in `docs/p0-contract-reconciliation/06-targeted-conflict-register.md` (ledger row `ACTIVATION-EPOCH-AUTHORITY-OWNER`).
- Preserves: all V0.2 documents are unchanged. Their proposal language is reconciled below, not rewritten.

## 1. Context

V0.2 proposals (hub `51c579a3`, `docs/program-v0.2/`) give the Control Plane the registry epoch and the activation decision (`s02/contracts/1.3-registry-r0.md` §3 and §5; `s05/2.4-architect-defaults-successor-note.md` default 5). Plan v1.3 §3 item 3 and the R08 preparation documents say activation is consumer-owned and the selection authority issues the epoch. For Runtime-enforced families the two readings cannot both hold: two parties would each claim the active epoch and the anti-rollback state would have no owner. Neither side implements activation. The full conflict evidence is preserved, unchanged, in the P0 conflict register §1.

## 2. Decision

1. The **authorized selection issuer** assigns the **selection epoch** within its governed scope.
2. The **enforcing component** owns **activation** and its **anti-rollback high-water state**.
3. The **Control Plane** retains activation responsibility for **Control Plane-enforced policy** (plan v1.3 §5: freshness F4, per-class authority F5, other proven Control Plane parameters, and the mandatory-check registry as V0.2 intended).
4. **Runtime-enforced policy** (plan v1.3 §5: F1a, F1b, F1c, F6 and F1d only if qualified) is activated by the **designated host/Runtime integration gate**, **subject to existing Control Plane authority**.
5. The **registry** stores and distributes governed records and selection references. It does **not** activate policy, issue grants, or authorize execution.
6. **Record succession and selection epochs are distinct concepts** and must not be conflated.
7. **Publication is not activation.**
8. **Revocation, expiry and changed-condition enforcement remain mandatory at the applicable effect boundary.**
9. A **selection is never a substitute for a grant.**
10. **No global atomicity or cross-domain authority transfer is implied.**

### Reading rules that follow directly from the decision (no new design)

- "Enforcing component" means the component whose own gate evaluates the policy at the effect or decision it governs. Which component that is for a given family is fixed by plan v1.3 §5; this ADR does not move a family.
- "Subject to existing Control Plane authority" (item 4) means the Control Plane's powers as recorded in hub `operator-decisions.md` (second-hand with respect to the code; see §7) are unchanged: grant and approval issuance and validation, the single effect-authorization decision, and grant/approval revocation. A Runtime activation can only narrow what those already permit (plan v1.3 §3.5, non-widening composition). It cannot create, widen or substitute for authority.
- Activation is a determination by the enforcing gate, not an approval, and is not stored in the registry (R08-PREP `01-lifecycle-contract.md` §3.4). The selection epoch is an input to that determination; the high-water epoch is the enforcing component's own state.
- Existing refusal rules stand: an unknown or ambiguous state refuses; a required operation with missing or invalid policy never falls back to a wider caller policy; an optional overlay refusal means "not applied", not denial (plan v1.3 §3.5).

## 3. Reconciliation of V0.2 proposal language against this ADR

Historical documents are not edited. Each row says how a reader must interpret the quoted language from now on.

| V0.2 source (hub `51c579a3`) | Language | Provenance status | Reading under this ADR |
|---|---|---|---|
| `s02/contracts/1.3-registry-r0.md` §3 | `epoch` is "Monotone activation epoch", owner "Control Plane at activation" | Proposed contract draft; no decision recorded | The **selection epoch** is assigned by the selection issuer (decision 1). The enforcing component enforces monotonicity against its own high-water state (decision 2). For Control Plane-enforced policy the Control Plane is that component, so "Control Plane at activation" holds only there |
| `s02/contracts/1.3-registry-r0.md` §5 | "A registry becomes active only through the Control Plane's own gate"; refusal list including "the epoch is not strictly greater than the active epoch" | Proposed | Holds for Control Plane-enforced policy. For Runtime-enforced policy the same refusal list applies at the Runtime/host integration gate. "Becomes active" is read as "the enforcing gate activates"; publication is not activation (decision 7) |
| `s02/contracts/1.2-authority-and-separation.md` §4 | Rule-set activation attributed to the Control Plane at an epoch | Proposed (header: PROPOSED until M0 records an outcome; the M0 record does not list the 1.2 text among its approved items) | Same as §5 above. Control Plane exclusive powers over grants, approvals and the effect decision are unchanged (decision 4) |
| `s05/2.4-architect-defaults-successor-note.md` default 5 | "Control Plane owns selected effective epoch and activation decision; custody outside the registry store" (operator gate: "Final cross-component authority commitment") | Architect default, not adopted; 2.4 activation code is not authorized | Superseded for Runtime-enforced policy; retained for Control Plane-enforced policy. "Custody outside the registry store" is preserved and strengthened (decision 5). This ADR does **not** authorize step 2.4 and does not discharge any operator gate recorded for 2.4 activation authorization |
| `s02/adr-proposals.md` ADR-P03, consequences (M0 row 3 approves the location decision) | "Activation and freshness remain the Control Plane's existing authority (steps 2.4, 3.3)" | Approved location decision; the consequence sentence is part of the approved text | Interpretive reconciliation, text unchanged: the Control Plane's existing authority is retained as defined in decision 4 (grants, approvals, effect decision, and activation of Control Plane-enforced policy). It does not make the Control Plane the activator of Runtime-local parameters it does not evaluate. The separate question of where the production pin and artifact are held remains open (OB-03) |
| `s03/identity-and-lifecycle.md` and hub `tools/registry_records.py` | `ocs-registry-record/0` carries an `epoch` checked as strictly increasing against the predecessor | Implemented, not qualified | In that record the `epoch` field is the **record succession counter** (decision 6). It is not the selection epoch and must not be used as one. Mapping and naming are delegated (DT-03); the hub implementation is not modified here |
| `docs/declarative-governance-registry.md` | Deciding components bind the selected registry and evaluator versions into their context commitment | Adopted direction | Unchanged and consistent. The binding contract itself (FP-04) remains a missing contract (MC-04, DT-07) |
| Plan v1.3 §3 item 3; R08-PREP `01-lifecycle-contract.md` §3.3–3.4; `r08-s01-contract.md` §3 | "Activation is consumer-owned"; epoch is a field in the selection authority's signed statement | Operator-approved plan; candidate models | Confirmed and made specific by decisions 1–4. "Host integrator" in R08 documents is read as the designated host/Runtime integration gate (decision 4) |

## 4. Consequences

- TR-01 is **architecturally resolved**. It is **not implemented**: no code, record, selection, trust root, verifier, host or activation exists as a result of this ADR.
- The anti-rollback high-water state has an owner (the enforcing component). Its design, persistence and recovery are delegated (DT-02).
- Control Plane authority is unchanged. None transfers to the registry, and none transfers across domains (decisions 5, 9, 10).
- P1 may record the enforcing component for each family in its extraction manifest; it need not wait for activation mechanics.
- No locked component is changed. No F3 change is authorized by this ADR.

## 5. Delegated engineering tasks (implementation details; not operator decisions)

Phases are P2, P3 or P4 as shown per task (DT-08 is P3; DT-09 follows P2 as a separate hub change).

| ID | Task | Owner | Phase | Inputs |
|---|---|---|---|---|
| DT-01 | Name the designated host/Runtime integration gate for the emulator profile (C-01). The production host owner stays tied to production activation, an operator item | Architect and Runtime owner (emulator) | P4 | plan v1.3 §8; R08-PREP `03` §4.1 |
| DT-02 | Design the enforcing component's anti-rollback high-water state: persistence, restart recovery, scope key `(selection_id, consumer_domain, scope)`, behavior on older or equal epoch (B-05, B-07) | Architect with Control Plane and Runtime owners | P2 (design), P4 (integration) | R08-PREP `01` §3.3, `02` |
| DT-03 | Define distinct names and an adapter map for record succession counter versus selection epoch across `ocs-registry-record/0` and `r08-v1` | Registry builder and hub record owner | P2 | crosswalk (naming list); decision 6 |
| DT-04 | Specify activation acknowledgement semantics at the enforcing gate: unacknowledged publication reads UNKNOWN, not ACTIVE (CA-03); bounded offline freshness rule | Architect with component owners | P2/P4 | hub `1.3` §5; Q14 default 8 |
| DT-05 | Selection validity and applicability at the commit boundary; expiry at commit (LD-09; Option C clamp as defense in depth); changed-condition behavior (decision 8; MC-01) | Runtime and Control Plane owners, Architect | P4 | R10 feasibility; plan v1.3 §3.6 |
| DT-06 | Selection-withdrawal propagation to the destination (LD-04) and a durable carrier for registry refusal evidence (LD-05) (MC-02, MC-03) | Architect and component owners | P2/P4 | R08-PREP `01` §3.3, `04` |
| DT-07 | Rule-set / selection identity in the decision context (FP-04), scoped to Control Plane gate rule-sets; Runtime selections use the separate applicability binding (MC-04, T3) | Architect | P4 | hub `f3-change-proposals.md`; R08-PREP `03` §4.3 |
| DT-08 | Control Plane adapter for Control Plane-enforced families F4/F5 under the existing gate, no second engine (G4, MC-07) | Control Plane owner | P3 | readiness document G4 |
| DT-09 | Reconcile hub step 2.4 package wording with this ADR if and when the hub owner reopens 2.4; the hub owner may annotate, supersede or leave the historical text | Hub owner | After P2, separate hub change | §3 above |

## 6. Explicitly not decided or authorized

R09 operational custody, key ceremony, trust root, verifier, witness holder; any R10 implementation or protocol option choice (A, B or B+C); activation of any record or selection; approval of any pin; step 2.4 authorization; any Control Plane or Runtime change or F3 package; naming of the production host owner; independent Tier 1 qualification lead; release, publication or production (all HOLD).

## 7. Evidence and limitation

This ADR rests on documents read at registry `ce00520f`, hub `51c579a3` and qualification `998d39c5`: plan v1.3 §§3, 5, 8; R08-PREP `01`, `03`, `04`; `r08-s01-contract.md`; hub `1.2`, `1.3`, `2.4` successor note, `adr-proposals.md`, `m0-decision-record.md`, `operator-decisions.md`.

**Source-verification limitation (preserved from P0).** The Control Plane and Execution Runtime source trees were **not** inspected by the P0 worker. Statements about their current behavior are second-hand from registry R08/R10 documents. The decision is an architectural assignment of ownership; it asserts nothing about what either component's code does today. No additional source was inspected to establish TR-01: the conflict was between written requirements, and the resolution assigns ownership without depending on implementation behavior. P1 must inspect exact source revisions directly before accepting each configurable-field extraction mapping.

## Appendix A. Primary source: the Architect's instruction (verbatim)

The text below is the Architect's instruction "FINALIZE P0, RECORD TR-01 ADR, PREPARE MERGE" as received by the P0 worker (attachment `d482ebcf-attachment.txt`), reproduced unchanged for provenance. It also records the Architect's conditional acceptance of P0 and approval of the TR-01 reconciliation. It contains no operator approval of activation, release, publication or production.

````text

put the maximum number of parallel agents to work

ROLE: OCS REGISTRY — P0 RECONCILIATION WORKER
FROM: OCS ARCHITECT
SUBJECT: FINALIZE P0, RECORD TR-01 ADR, PREPARE MERGE
AUTHORIZATION: DOCUMENTATION-ONLY REMEDIATION

REPOSITORY:
cogno-us/cognous-ocs-registry

EXISTING PR:
https://github.com/cogno-us/cognous-ocs-registry/pull/21

REVIEWED HEAD:
711a09ccbdd4757edc260248c5f6d7c7633c9c2d

GOVERNING REFERENCES:

Approved Project Plan v1.3:
docs/plans/PROJECT_PLAN-v1.3-DRAFT.md

Previous Project Plan v1.2:
docs/plans/PROJECT_PLAN-v1.2.md

Engineering Constitution:
https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md

P0 deliverables:
docs/p0-contract-reconciliation/

ARCHITECT DISPOSITION

P0 is CONDITIONALLY ACCEPTED.

The reconciliation establishes:

- 139 canonical contracts.
- 35 adopted/frozen contracts.
- 99 contracts with reuse dispositions.
- One genuine architectural conflict, TR-01.
- No need for another broad contract review.
- P1 readiness: PASS for planning.

These are reconciliation findings, not independent
qualification of component implementations.

Complete the following bounded remediation.

============================================================
TASK 1 — RESOLVE TR-01
============================================================

Create one Architect ADR documenting the reconciliation
of activation and epoch ownership.

Adopt this architecture:

1. The authorized selection issuer assigns the selection
   epoch within its governed scope.

2. The enforcing component owns activation and its
   anti-rollback high-water state.

3. Control Plane retains activation responsibility for
   Control Plane-enforced policy.

4. Runtime-enforced policy is activated by the designated
   host/Runtime integration gate, subject to existing
   Control Plane authority.

5. The registry stores and distributes governed records
   and selection references. It does not activate policy,
   issue grants, or authorize execution.

6. Record succession and selection epochs are distinct
   concepts and must not be conflated.

7. Publication is not activation.

8. Revocation, expiry and changed-condition enforcement
   remain mandatory at the applicable effect boundary.

9. A selection is never a substitute for a grant.

10. No global atomicity or cross-domain authority
    transfer is implied.

Reconcile the V0.2 proposal language against this ADR.

Do not rewrite historical V0.2 documents.

Do not modify the Control Plane or Runtime.

Do not implement activation.

Record any remaining implementation details as delegated
engineering tasks under P2/P4.

============================================================
TASK 2 — UPDATE P0 RECONCILIATION ARTIFACTS
============================================================

Update only the affected P0 documents and ledger rows.

In particular:

- Reference the adopted Architect ADR.
- Change TR-01 from unresolved to architecturally resolved.
- Preserve historical source status and provenance.
- Distinguish architectural resolution from implementation.
- Preserve the original conflict evidence.
- Update P1 handoff dependencies accordingly.

Do not relabel implementation as qualified.

Do not change unrelated classifications.

If the ledger schema cannot accurately express a resolved
historical conflict, add a narrowly defined disposition
field rather than rewriting its history.

============================================================
TASK 3 — SOURCE-VERIFICATION LIMITATION
============================================================

The original P0 worker did not directly inspect
Control Plane or Runtime source.

Preserve this limitation explicitly.

P0 establishes the contract and decision reconciliation,
not independent verification of all implementation claims.

P1 must directly inspect exact source revisions before
accepting each configurable-field extraction mapping.

Do not launch a broad 15-component source audit.

Only inspect additional source if necessary to establish
the correctness of TR-01.

============================================================
TASK 4 — VERIFY FINAL DELIVERABLE
============================================================

Perform mechanical validation of:

- Contract ledger schema.
- Contract IDs and unique rows.
- Closed status vocabularies.
- Source and decision references.
- TR-01 ADR references.
- Crosswalk consistency.
- P1 handoff consistency.
- No unintended changes outside P0 documentation and
  the new Architect ADR.

Preserve the seven lane outputs and status-resolution log.

No test-suite execution is necessary for this
documentation-only remediation.

Do not introduce a new architecture review cycle.

============================================================
TASK 5 — FINALIZE PR #21
============================================================

Commit the bounded remediation to the EXISTING PR #21.

Do not open a replacement PR.

Verify:

- Exact final head SHA.
- Changed-file inventory.
- No code changes.
- No test changes.
- No static-plan changes.
- No component-lock changes.
- No security-boundary changes.
- Applicable GitHub checks.
- PR mergeability.

The operator has already approved the governing
Project Plan v1.3.

The Architect has approved the TR-01 reconciliation.

No additional operator decision is required.

If all checks pass, mark PR #21 ready and merge using
a merge commit with exact-head protection.

If mergeability fails or an unexpected architectural
conflict appears, stop and report the blocker.

Do not broaden the remediation.

============================================================
FINAL REPORT
============================================================

Return only:

1. PR #21 URL and final status.
2. Exact head and merge SHA, if merged.
3. TR-01 ADR location.
4. Ledger validation result.
5. Confirmation of documentation-only changes.
6. P0 disposition: COMPLETE or BLOCKED.
7. P1 readiness: READY or BLOCKED.
8. Any genuinely material remaining blocker.

Do not ask the operator technical implementation questions.

Route implementation details to the Architect or owning
component engineer.

P0 is complete once the reconciliation is recorded,
verified and merged.

P1 will consume the existing scenario-inventory report
when available.

Do not start P1 implementation.
Do not begin R09/R10 implementation.
Do not activate policies.
Do not perform paid or production tests.

RELEASE: HOLD
PUBLICATION: HOLD
PRODUCTION: HOLD
````
