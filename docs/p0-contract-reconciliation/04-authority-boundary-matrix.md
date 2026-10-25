# 4. Authority-boundary matrix

Pins: hub `51c579a3` (OCS), registry `ce00520f` (REG), qualification `998d39c5` (QUAL).

**Evidence limit.** Control Plane and Execution Runtime source trees were not read. Source lines for those components are second-hand, from REG `docs/r08-preparation/03`, `04`, `10` and `docs/r10-feasibility/`, which cite Control Plane `0a41faa9`/`7a4bcd40` and Runtime `ec728da6`/`c5e97e87`. Rows that rest on that are marked.

Status key: **ADOPTED** = a decision record exists; **IMPL** = implemented, not independently qualified; **PROP** = proposal only; **OPEN** = no decision.

## Principle-level ownership (settled)

Ownership is settled **as principle**, not as frozen contract text. The record is hub `operator-decisions.md` ("Keep Control Plane/Runtime effect authority … No alternate authorization point"), the adopted DGR direction (operator, 2026-10-21) and plan v1.3 §1/§3.1. Contract `1.2-authority-and-separation.md` labels every normative sentence PROPOSED until M0 records an outcome; M0 approved ADR-P05/P07/P08 and the workflow vocabulary but not the 1.2/1.4 text. Cite the underlying adopted records, never the 1.2 text. F-06 (via ADR-P07) and F-10 (via ADR-P08) are adopted; the rest of F-01..F-10 and the 1.2 §2 power table are PROPOSED.

## Matrix

| Boundary | Owner | Enforcer | Registry MAY | Registry MAY NOT | Established | Open |
|---|---|---|---|---|---|---|
| **Grant and approval issuance and validation** | Control Plane (single decision gate); Action Manifest declares only; Orchestrator never mints or widens | Control Plane workflow, host-configured resolver; Route B destination re-reads stored grant/approval state at commit | Carry non-authorizing configuration records and selections | Mint, widen or emulate a grant or approval; model a selection as grant `policy_versions`; take authority from a matching digest | ADOPTED boundary; validation code IMPL | `approval_ref` versus `approval_id` (identity-and-lifecycle row 12). `effect_id` changes per `grant_revision`; SP-01 `operation_id` approved at M0 row 9, opt-in |
| **Authorization versus evidence separation** | Each component's one gate (code floor) | Component gate code; Qualification for independent verdicts | Reference evidence by digest | Treat evidence, replay, a digest or a merge as permission; weaken a floor item | ADOPTED principle (DGR); wire formats not frozen | Per-component enforcement qualification |
| **Runtime admission and evaluation** | Execution Runtime owns `LocalExecutionPolicy.check`; activation is consumer-owned (v1.3 §3.3); the constructing host integrator is unassigned | Runtime executor policy check | Supply S03/`r08-v1` record and selection; a read-only consumer narrowing caller ∩ registry | Evaluate, activate or authorize; fall back to a broader caller policy for a required operation; add a registry call inside the commit transaction | ADOPTED: consumer-owned activation; F1a/F1b to Runtime. Evaluator IMPL | C-01 host integrator; construction site (E-05); mandatory profile is "design capability, activation not authorized" |
| **Atomic effect boundary** | Runtime destination plus Control Plane claim materialization | `execute_claim_atomic` under `BEGIN IMMEDIATE`; `_validate_claim_state` | Provide immutable data a successor profile may bind | Claim global or cross-domain atomicity; check authority outside the owner's transaction | Route B IMPL, UNQUALIFIED (profile URN ends `0.1.0-proposed`; lock scope "not atomic/refund-intent profile activation"). Boundary principle ADOPTED (v1.2 §3.3-binding, v1.3 §3.6) | Selection/epoch/evaluator binding at commit is PROP only (R10 options A/B/C). Route A cannot be closed |
| **Authority revocation** | Control Plane (grant status); Runtime destination (retained revoked sets). Registry owns **selection** revocation separately | Destination rechecks under lock (Route B); Control Plane `execute()` re-resolve (Route A, open window) | Issue and publish signed selection revocation; keep append-only history | Revoke or reinstate grants/approvals; let replay or restore revive withdrawn authority; treat "no revocation seen" as valid | Grant terminality IMPL. Approval terminality IMPL only at Runtime `c5e97e87`, not hub-locked | LD-04 propagation of selection withdrawal to the destination; B-08 latency bound; Route A fence (R-REVIEW-C0); pin choice R10-F-03 |
| **Configuration revalidation** | Control Plane at decision and effect time; Runtime per call; destination at commit | Same | Supply exact pins; wrong identity is refused at the consumer | Substitute its own pre-dispatch check; use `latest`; hot-swap | Grant policy-ref revalidation IMPL. Registry-selection revalidation does **not exist** | LD-01, LD-09 (expiry at commit; Option C clamp is the cheapest stopgap), LD-05 receipt content, freshness 60-versus-300 |
| **Negative-evidence custody** | Each enforcing component: Control Plane `EffectTimeRefusal`, Runtime failure rows, ODES journal; GCR for cognitive negative-record continuity | Component code floor; independent verdicts by Qualification | Keep registry record and selection logs, append-only | Hold effect-time negative evidence; erase or reinterpret history; claim atomic negative-record custody | Principle ADOPTED; custody code IMPL | Runtime failure rows are written after the refusal in a separate step; optional-overlay refusal leaves no durable record; QUAL SCN-D07 INCONCLUSIVE; B-11 witness holder and A-10 erasure authority are operator-open |

## R09 and R10: established versus genuinely open

**Established (reuse; do not re-adjudicate).** Record, selection and activation are distinct objects (v1.3 §3.3). A registry cannot issue grants or authorize effects. Activation is consumer-owned. A required missing policy never falls back to a wider caller policy; an optional overlay refusal means "not applied", not denial. A selection is not a grant. The pre-claim check is not a transaction-time guarantee (v1.3 §3.6). Reuse the existing OCS Ed25519 primitives rather than build a fourth system; a signature is not authorization. No global atomicity; no universal reason vocabulary. LD-02 failure-code mapping, LD-09, A-05 and the B-10 adapter are delegated to the Architect and component owners (v1.3 §8), so they are technical items, not operator items.

**Genuinely open — R09.** Trust-root custody, issuer enrollment, key ceremony and signer-compromise recovery (the operator must authorize any ceremony: v1.3 §3.8; B-02, B-04 and the B-11 witness holder are operator items). Anti-rollback high-water mark (B-05) and the older-record rule (B-07): Architect items. Independent security review of authority-bearing paths (gate G2). Independent Tier 1 qualifier (F-01/D13, not designated). Loaded-code integrity exclusion (B-09). Archival, erasure and legal-hold authority (A-10).

**Genuinely open — R10.** Choice of binding protocol, Option A, B or B+C (R10-F-01; the Architect leans to B, which needs a successor profile in both Runtime and Control Plane: R10-F-02). Writer of the authoritative selection row and the withdrawal path (R10-F-04/LD-04). Exact-source integration candidate (R10-F-03/LD-06). Receipt content (LD-05). Route A versus Route B scope (C-06). Host integrator naming (C-01). Independent qualifier for the effect-time path (LD-07). Reachability and designation of the five unmediated effect surfaces (M0 row 10). Any locked-component change needs a separate F3 authorization (M0 rows 11 and §3). No R10 implementation is authorized (`docs/decisions/2026-10-24-r08-s01-authorization.md`).

## Tensions examined (none is a second genuine conflict; see register)

| ID | Tension | Disposition |
|---|---|---|
| T1 | Who activates a rule set | Becomes **TR-01** |
| T2 | Who names the host integrator | Decision-rights ambiguity, not a technical conflict. Architect and Runtime owner name a synthetic integration adapter for the emulator profile (v1.3 §8); the production host owner stays an operator item tied to production activation |
| T3 | Where selection identity binds in the Runtime claim: FP-04 policy-row binding (PROP) versus the Architect ruling that selection is not a grant (C-03/LD-01) | Scope FP-04 to Control Plane gate rule-sets (`RuleKind`/`rule_identity`). Registry selections for Runtime F1a use R10's separate applicability binding. Record in the R10 ADR |
| T4 | Hub lock (`ec728da6`) versus provisional tuple (`c5e97e87`/`7a4bcd40`) | Ordinary pin reconciliation (R10-F-03). Evidence at one tuple does not transfer to the other |
| T5 | Epoch ownership wording (OCS 1.3 §3 versus REG 01 §3.3) | Folded into TR-01 |

**Missing contracts (gaps, not conflicts):** selection validity/applicability at commit (R10), selection-withdrawal propagation (LD-04), a durable refusal carrier for registry outcomes (LD-05). All three are bounded to P2/P4.

## Not verified

Control Plane and Runtime source behavior behind F3 claims; Orchestrator `ARCHITECTURE.md`/`CONTRACTS.md` (quoted via OCS 1.2 only); `COG-REG-SHARED-ADD-01` (text and digest not in custody, so nothing relies on it); whether M0 intended to adopt 1.2/1.3/1.4 text beyond the listed ADR rows (the record is silent, so they stay PROPOSED_ONLY); whether later hub revisions closed the `residual-risks.json` items; formal adoption of the Engineering Constitution revision.
