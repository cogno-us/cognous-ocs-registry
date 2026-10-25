# 7. P1 handoff

**Disposition: P1 may proceed without another broad contract review.** TR-01 is architecturally resolved by ADR-REG-TR01 (2026-10-25); mechanics are delegated (DT-01..DT-09); nothing is implemented or qualified. P0 is conditionally accepted; P1 readiness: PASS for planning. This document lists the ledger contracts the scenario-inventory output and the extraction manifest can safely rely on, what they must treat as unsettled, and what is still missing from custody. It does not duplicate or restate the scenario inventory.

## P1 inputs not yet in custody

Plan v1.3 §4 assigns the scenario Inventory Worker report to `cognous-stack-qualification`. No such deliverable was found in that repository at `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` (only the existing `docs/test-inventory.md` and `process/release-gate/inventory.json`). P1 consumes it when it lands; P0 neither produced nor assumed it.

## 1. May rely on (cite the ledger id and its decision record)

| Area | Ledger ids | Reliance and limit |
|---|---|---|
| Partition doctrine | `DGR-ARCH-1.0.0`, `DGR-SEQUENCE-R0-R4`, `CODE-OWNED-FLOOR-EXPLICIT-ARGUMENT`, `NON-WIDENING-COMPOSITION` | Use the extractability test in `05-configuration-extraction-readiness.md` ("The partition rule"): caller/constructor data, code-owned bound remains, narrow-only, deterministic non-widening refusal. Floor is an explicit code argument. Builder-tested only |
| Code-owned classes | `CODE-OWNED-INVARIANT-CLASSES` (proposed in R07), M1–M8 non-migratable list | Map to `CODE_GUARDRAIL`. The 32 historical S02 unresolved classifications stay unresolved unless source-specific findings decide them |
| Reference path | `S03-LOCALEXECUTIONPOLICY-ALLOWLIST`, `S04-OVERLAY-CONSUMER`, `S05-DIFFERENTIAL-EQUIVALENCE`, `R08-V1-SUCCESSOR-FOUNDATION`, `F1A-TARGET-MSOP` | F1a as frozen/implemented reference. F1a is the *target* MSOP, a scope decision, not operational acceptance. Do not claim the full MSOP complete |
| Authority | `CP-SINGLE-EFFECT-GATE`, `AUTHZ-EVIDENCE-SEPARATION-FLOOR`, `SELECTION-IS-NOT-A-GRANT`, `GCR-AUTHORITY-ISOLATION`, `RECORD-SELECTION-ACTIVATION-LIFECYCLES` | Treat any manifest field whose true authority owner is the Control Plane or Runtime as owner-enforced. A registry value never grants |
| Identity and canonicalization | `CANONICAL-JSON-ADR-P01`, `SP-01-STABLE-EFFECT-ID`, `WORKFLOW-VOCABULARY-12`, `AOI-ADOPTED-DECISIONS`, `ADR-P05/P07/P08` | Record digests using a named profile (see X-01). Reconcile-only recovery: no unknown becomes success, absence or retry |
| Implemented building blocks | `REG-RECORD-0`, `MANIFEST-0`, `MANDATORY-INPUT-KINDS`, `FAILURE-REFUSAL-SEMANTICS`, `REVOCATION-AND-EPOCH-FLOOR`, `AUTHENTICATED-SELECTION-STATE` | Available as code, never as qualified. Cite "Copilot-reviewed, not independently qualified" |
| Baseline | `W0-C1`…`W0-C8`, `LOCK-IFACE-01`…`12`, `COMPONENT-LOCK-SELECTION` | Frozen historical g8-r10 baseline (operator decision). Not current release or qualification status |
| Activation and epoch ownership | `ADR-TR-01-ACTIVATION-EPOCH-OWNERSHIP` (`ADOPTED_FROZEN`: decision recorded; not implemented; not qualified), plus the `architectural_resolution` field on `ACTIVATION-EPOCH-AUTHORITY-OWNER` and `REGISTRY-ACTIVATION-2.4-V02` | Rely on the ownership assignment only: the selection issuer assigns the selection epoch; the enforcing component owns activation and the high-water state; the registry never activates. Do not cite it as an implemented or qualified mechanism |
| Process | `INDEPENDENT-QUALIFICATION-OBLIGATION`, `M0-DECISION-RECORD` | Independent qualification owns oracles and verdicts. The architect may not self-certify Tier 1 |

## 2. Must treat as unsettled

| Item | Ledger id / ref | P1 handling |
|---|---|---|
| Per-field composition for F1d, F7, F4 cross-bound, F5 `irreversible`, F6 absent agent | MC-06 (G2) | Disposition `UNRESOLVED` or `CONDITIONAL` with the missing ruling named; do not guess a direction |
| Numeric encoding (F1c `max_amount`, F4 ages) | MC-06 (G3) | Record the encoding question per field; do not choose a float representation |
| Activation and epoch owner | TR-01: architecturally resolved by ADR-REG-TR01; mechanics delegated (DT-01..DT-09) | Record the **enforcing component per family** in the manifest (plan v1.3 §5; ADR decisions 3 and 4); leave activation mechanics to the delegated tasks |
| Any V0.2 proposal: contracts 1.2/1.3/1.4 text, `/1` record and manifest, step 2.4, FP-01..FP-05, scanner ruleset profile, AOI-C01/C02 text | `PROPOSED_ONLY` rows | Design input only. Never cite as adopted |
| Q1–Q17 Architect rulings, R07 D1–D13 rulings | `ARCHITECT-DISPOSITION-Q1-Q17`, `R07-ARCHITECT-RULINGS-D1-D13` (UNVERIFIED) | Usable as Architect-role technical guidance; flag as not independently recorded |
| Registry location / pin carrier, trust root, host integrator naming, Tier 1 lead | OB-01..OB-04 | Note as dependency of activation; no P1 impact. The host integrator role is fixed by ADR-REG-TR01 decision 4; the name is DT-01 (emulator) or an operator item (production) |
| Control Plane and Runtime behavior | second-hand in this ledger | Re-read the actual evaluator source at the exact pin when building each manifest row; plan v1.3 §4 already requires "exact current evaluator source" |
| Registry-mediated protection at the effect boundary | MC-01 | The pre-claim `LocalExecutionPolicy` check is not a transaction-time guarantee (plan v1.3 §3.6). Do not credit registry-mediated protection at the commit boundary |

## 3. Vocabulary and evidence rules for P1 artifacts

- Use full names: governance registry (OCS-DGR), `cognous-ocs-registry` repository, The Index (`cognous-evidence-registry`).
- Keep "required/advisory" (rule status) distinct from "required/optional" (operation participation).
- Never write "qualified" for builder-tested or Copilot-reviewed results. "Frozen" means byte-pinned or decision-recorded, not qualified.
- Do not cite `component-lock.json` `qualification_status: "accepted"` or `evidence-snapshot.json` `"current"`; cite `docs/release-status.md`.
- Known-limit tests are NOT PASS. Preserve failures, skips, XFAIL and NOT RUN (plan v1.3 §7).

## 4. Dependencies P1 creates for later phases

P2 depends on DT-02, DT-03, DT-04, DT-06 (activation and custody mechanics per ADR-REG-TR01; no longer on an unresolved conflict), plus MC-08, OB-02, OB-03. P3 depends on DT-08, MC-05, G1 and the P1 rulings in MC-06. P4 depends on DT-01, DT-02 (integration), DT-04, DT-05, DT-06, DT-07, plus OB-01 and OB-05. P6 needs OB-04 and G8. None blocks P1.

## Source inspection obligation

**P1 must directly inspect the exact Control Plane, Execution Runtime and evaluator source revisions before accepting each configurable-field extraction mapping.** P0 did not: it did not inspect Control Plane or Runtime source, and every claim about their behavior in the ledger and registers is second-hand from registry R08/R10 documents. P0 establishes contract and decision reconciliation, not independent verification of implementation claims. ADR-REG-TR01 assigns ownership and asserts nothing about what either component's code does today. This is a per-mapping obligation within P1, not a broad 15-component source audit; none is launched.

## 5. Operator decisions

P0 generates none. P1 itself ends in the operator's V1 scope freeze (plan v1.3 §8 item 1), unchanged by this work.
