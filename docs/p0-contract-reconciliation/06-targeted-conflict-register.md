# 6. Targeted conflict register

**Status: TR-01 architecturally resolved by ADR-REG-TR01 (2026-10-25); implementation delegated (DT-01..DT-09). Counts: 1 genuine conflict identified, 0 open. Not implemented, not qualified; release, publication and production remain HOLD.** The conflict evidence below is the historical P0 finding at head `711a09ccbdd4757edc260248c5f6d7c7633c9c2d` and is preserved unchanged.

Only real incompatibilities that require resolution. Count of genuine conflicts identified: **1** (open: **0**). Required targeted reconciliations: **1** (TR-01, resolved architecturally; implementation delegated). Everything else examined is listed in §2 with the reason it is not counted, so P1–P6 do not re-litigate it.

## 1. Genuine conflict

### TR-01 — Who issues the epoch and owns the activation decision

Ledger: `ACTIVATION-EPOCH-AUTHORITY-OWNER` (`CONFLICTING`, `TARGETED_RECONCILIATION`); related `REGISTRY-ACTIVATION-2.4-V02` (`PROPOSED_ONLY`), `RECORD-SELECTION-ACTIVATION-LIFECYCLES` (`ADOPTED_FROZEN`).

**Conflicting requirements**

| Side | Requirement | Status of that side |
|---|---|---|
| V0.2 | Hub `s02/contracts/1.3-registry-r0.md` §3: `epoch`, owner "Control Plane at activation". §5: "A registry becomes active only through the Control Plane's own gate". `s05/2.4-architect-defaults-successor-note.md` default 5: "Control Plane owns selected effective epoch and activation decision; custody outside the registry store" (operator gate: "Final cross-component authority commitment"). ADR-P03 consequence text: "Activation and freshness remain the Control Plane's existing authority (steps 2.4, 3.3)" | Proposed contract draft and an Architect default. Step 2.4 is not authorized (hub `s05/architect-disposition-q1-q17.md` status table: "2.4 activation code | Not authorized"; the 2.4 successor note: gates 1 and 2 are not established). Hub `operator-decisions.md` lists "Activation/freshness semantics" as an OPEN contract detail |
| Registry | `docs/plans/PROJECT_PLAN-v1.3-DRAFT.md` §3 item 3: "Activation is consumer-owned"; "publication or newer epoch does not imply activation or authority". §5: Runtime owns F1a/F1b/F1c/F6; Control Plane owns F4/F5. `docs/r08-preparation/03` §4.1: "Host integrator owns ACTIVATION. The Runtime owns evaluation"; named host not designated (C-01). `docs/r08-s01-contract.md` §3: epoch is a field in the selection authority's signed statement | Operator-approved plan (adopted); R08 documents are candidate models |

**Existing implementation behavior.** Neither side implements activation. Registry S04 overlay is caller-invoked with an operator pin. `verify_selection` only reports technical verification and sets `operationally_authorized` to false. The Control Plane never references `LocalExecutionPolicy` (R08 `03` §3.1).

**Consequence.** For Runtime-enforced families, two parties could each claim to hold the "active epoch" (Control Plane per V0.2, host per R08). The anti-rollback high-water state (R09 B-05) would have no owner. Read literally, the V0.2 proposal would make the Control Plane the activator of Runtime-local F1a. That risks split-brain policy (plan v1.3 §3 item 6; R10 gate) and would give the Control Plane authority over parameters it does not evaluate.

**Resolution recommended in P0 (adopted as ADR-REG-TR01) (reuse; no redesign; no registry authority).** One ADR by the OCS Architect with the Control Plane and Runtime owners:

1. The **selection authority** issues the epoch (R08, signed selection). Epoch ownership wording in 1.3 §3 is read as "enforced by the activating component", not "issued by it".
2. The **enforcing component's own gate** performs activation, holds the high-water epoch and applies the V0.2 §5 refusal list: the Control Plane for Control Plane-enforced policy (F4/F5 and the mandatory-check registry, as V0.2 intended); the named C-01 host for Runtime families (F1a/F1b/F1c/F6).
3. The **registry holds neither** the epoch decision nor the high-water state. Control Plane authority is preserved; none transfers to the registry.
4. V0.2's 1.3 §5 and 2.4 default 5 become `SUPERSEDED_BY_ADOPTED_CONTRACT` for Runtime families and stay as proposals for Control Plane families (a reading adopted by the ADR; the ledger deliberately does not apply that label and preserves the historical status).
5. Name the two meanings of "epoch" distinctly (record succession order versus selected effective epoch).

**Resolution (2026-10-25).** Adopted by the OCS Architect as `docs/decisions/2026-10-25-adr-tr-01-activation-and-epoch-ownership.md` (ADR-REG-TR01). Ten decisions, in brief: (1) the selection issuer assigns the selection epoch; (2) the enforcing component owns activation and the anti-rollback high-water state; (3) the Control Plane activates Control Plane-enforced policy (F4/F5, mandatory-check registry); (4) Runtime-enforced policy (F1a/F1b/F1c/F6, F1d only if qualified) is activated by the designated host/Runtime integration gate, subject to existing Control Plane authority; (5) the registry stores and distributes only, and never activates, issues grants or authorizes; (6) record succession counter and selection epoch are distinct; (7) publication is not activation; (8) revocation, expiry and changed-condition enforcement stay mandatory at the effect boundary; (9) a selection never substitutes for a grant; (10) no global atomicity or cross-domain authority transfer. The reading of each V0.2 proposal sentence is reconciled in ADR §3 (V0.2 documents are not edited). Implementation is delegated to DT-01..DT-09 (ADR §5 table: owners and phases).

Not resolved by the ADR (ADR §6): implementation of any kind; the R09 trust root, key ceremony, verifier and witness holder; naming of the production host owner (operator item tied to production activation); step 2.4 authorization; any R10 option choice; activation or pin approval; independent Tier 1 lead.

**Status of this finding.** The ledger keeps the historical status and disposition (`CONFLICTING` / `TARGETED_RECONCILIATION` at head `711a09cc`) and records the resolution in the `architectural_resolution` field and in the new row `ADR-TR-01-ACTIVATION-EPOCH-OWNERSHIP` (`ADOPTED_FROZEN` = decision recorded; not implemented; not qualified).

**Source-verification limitation.** The P0 worker did not inspect Control Plane or Execution Runtime source. Statements about them are second-hand from registry R08/R10 documents. P0 establishes contract and decision reconciliation, not independent verification of implementation claims. No additional source was needed for TR-01 (a written-requirement conflict resolved by ownership assignment). P1 must inspect exact source revisions directly before accepting each configurable-field extraction mapping (see `07-p1-handoff.md`). No broad 15-component source audit is launched.

**Escalation.** Not an operator decision under plan v1.3 §8: it is OCS-internal, introduces no OCS/GCR choice and no departure from the existing authority separation. It would escalate only if the ADR moved authority away from the Control Plane's existing gate, which this resolution does not do. The ADR did not, so nothing was escalated. Only the production host owner naming (OB-01) and any trust-root ceremony (OB-02) remain operator-linked.

**Affected components.** Control Plane, Execution Runtime, host integrator (C-01), registry, hub step 2.4 package.

**Impact on phases.** Original P0 assessment: P1 none; P2 blocked custody and activation design (R09); P3 adapters must not embed activation; P4 R10/R12 blocked until the activation owner per family was named; P6 the oracle needs the activation owner. **After ADR-REG-TR01:** P1 none (inventory proceeds and records the enforcing component per family). P2, P3 and P4 no longer wait for an ownership decision; they implement per the ADR through the delegated tasks (P2: DT-02 design, DT-03, DT-04, DT-06; P3: DT-08, adapters still must not embed activation; P4: DT-01, DT-02 integration, DT-04, DT-05, DT-06, DT-07). P6: the oracle takes the activation owner per family from the ADR. Implementation and qualification remain outstanding.

## 2. Examined and not counted

| ID | Candidate | Why it is not a genuine conflict | Disposition / owner / phase |
|---|---|---|---|
| X-01 | **Canonical JSON** (lanes A2 C-A2-1, B C2, D 4a, E CC-E1). ADR-P01 (approved) says JCS for new commitments; the registry's `s03-v1`/`r08-v1` use `json.dumps(sort_keys, ensure_ascii=True)` | ADR-P01 itself keeps legacy forms as *named* profiles. Digests of identical data differ only for non-ASCII strings. No digest crosses repositories today | Adapter: name the registry form as a legacy profile, or give any later record version JCS before a pin is approved. Registry/Architect, before any pin approval (P2/P3) |
| X-02 | **ADR-P03 versus this repository** (lane A1 CC-1 proposed `TARGETED_RECONCILIATION`) | ADR-P03 states "A separate registry repository can follow if requirements justify it", and the operator authorized this program in its own repository. The unresolved part is the *production* pin carrier and custody, not repository existence | `REUSE_WITH_ADAPTER`. Production location/pin carrier is OB-03, decided at R09 |
| X-03 | **`abstained` outcome** (A2 C-A2-2): Architect Q7 requires `not_applicable` / `abstained` / `error`; code and the `/1` candidate have four outcomes | Q7 is an unadopted Architect ruling; the registry program does not use check dispositions. This is an implementation gap against a proposal, fixable by an additive manifest change | Gap for the manifest `/1` work (hub); not on the P1 critical path |
| X-04 | **Evaluator qualification gate**: V0.2 refuses an evaluator without `qualification_ref`; `r08-v1` has none | `r08-v1` is inactive, so the intended refusal is not triggered. Prerequisite G7, not an incompatibility | Qualification repo owner; P3/P6 |
| X-05 | **Label collision**: "Q" numbers collide across four ruling sets; "epoch" has two meanings; "registry" has three referents | Naming only | Use full names in P1 artifacts; epoch naming is settled by ADR-REG-TR01 decision 6 (record succession counter versus selection epoch; names delegated, DT-03) |
| X-06 | **Hub lock label** (`qualification_status: "accepted"`, `snapshot_status: "current"`) versus `docs/release-status.md` ("superseded") | A *status-label* inconsistency in a hub document about an earlier tuple, not an incompatibility between contracts. Ledger status is `CONFLICTING` so that nobody cites the label | Hub owner to correct or mark superseded; until then cite `release-status.md`. P6 evidence claims |
| X-07 | **Host integrator naming** (T2) | Decision-rights ambiguity. Emulator profile adapter is an Architect/Runtime-owner item (plan v1.3 §8); production host is an operator item tied to production activation. ADR-REG-TR01 decision 4 fixes the role (designated host/Runtime integration gate); naming remains open | OB-01; emulator naming DT-01 |
| X-08 | **FP-04 policy-row binding versus "selection is not a grant"** (T3) | Two proposals/rulings that reconcile by scoping FP-04 to Control Plane gate rule-sets | Architect, in the R10 ADR (P4); scoping adopted in ADR-REG-TR01 (DT-07) |
| X-09 | **Hub lock pin `ec728da6` versus provisional `c5e97e87`** (T4) | Ordinary pin reconciliation (R10-F-03) | Component owners; P4 |
| X-10 | **Fallback wording**: V0.2 "previous behavior unchanged" versus R08 "no fallback to older epoch" | Different events (refused candidate versus invalid current required selection) | None; keep distinct in P2 |
| X-11 | **Q1–Q17 Architect rulings versus plan v1.3** | Lane E rated Q1–Q17 `ADOPTED_FROZEN`; lanes A1/A2 found no operator transcription. Overruled: UNVERIFIED as adoption, usable as Architect-role technical guidance. Not a conflict with the plan | Architect to record (G9) |

## 3. Missing contracts (gaps; each bounded to one owner and phase)

| ID | Missing contract | Owner | Phase |
|---|---|---|---|
| MC-01 | Selection validity and applicability at the commit boundary (R10 options A/B/C; Architect leans to B). Delegated: DT-05 | Runtime + Control Plane owners | P4 |
| MC-02 | Selection-withdrawal propagation to the destination (LD-04). Delegated: DT-06 | Architect | P4 |
| MC-03 | Durable carrier for registry refusal evidence (LD-05). Delegated: DT-06 | Architect + component owners | P2/P4 |
| MC-04 | Rule-set / selection identity in the decision context (FP-04). Delegated: DT-07 | Architect | P4 |
| MC-05 | Evaluator `qualification_ref` for `LocalExecutionPolicy.check` and Control Plane evaluators | Qualification repo owner | P3/P6 |
| MC-06 | Per-field composition rulings and numeric payload encoding beyond F1a (G2, G3) | P1 lead / Architect | P1 |
| MC-07 | Control Plane adapter for F4/F5 (G4). Delegated: DT-08 | Control Plane owner | P3 |
| MC-08 | Authenticated trust root, verifier, anti-rollback high-water holder (G5). TR-01 part settled: the enforcing component owns the high-water state (ADR-REG-TR01 decision 2; design DT-02); trust root and verifier remain open | Architect; operator authorizes any ceremony | P2 |

## 4. Unresolved authority boundaries (not conflicts)

| ID | Boundary | Who decides | Phase |
|---|---|---|---|
| OB-01 | Named host integrator for Runtime policy construction (C-01) | Emulator: Architect and Runtime owner (DT-01). Production: operator. ADR-REG-TR01 settles the role, not the name | P4 (emulator), production gate |
| OB-02 | R09 trust-root custody, key ceremony, witness holder (B-02, B-04, B-11) | Operator authorizes any ceremony; Architect specifies | P2 |
| OB-03 | Production registry location and pin carrier (ADR-P03 follow-on; Q14 default 4) | Architect, at R09 | P2 |
| OB-04 | Independent Tier 1 qualification lead (F-01/D13) | Independent qualification owner appoints the lead (plan v1.3 section 8); operator involvement only if no independent lead can be secured | P6 |
| OB-05 | Terminal-approval-revocation pin: hub `ec728da6` versus `c5e97e87` | Component owners | P4 |
