# Lane C: authority and effect boundaries

Pins: OCS hub `51c579a3208149922649a31a6eb041106a4121c3` (OCS); registry `ce00520f91bf3986a08b4d13a1fb062057babc71` (REG); qualification `998d39c5ba1c9d537be8289f7658f2e9cde6cbba` (QUAL). Paths are repo-relative. 22 ledger rows in `C.jsonl`.

**Evidence limit.** The Control Plane and Execution Runtime source trees are not in the local checkouts. Every source line cite below for those components (`bounded.py`, `local_authority_effect.py`, `safe_executor.py`) is second-hand, from REG `docs/r08-preparation/03`, `04`, `10` and `docs/r10-feasibility/`, which cite CP `0a41faa9`/`7a4bcd40` and Runtime `ec728da6`/`c5e97e87`. Statuses that rest on that are marked as such.

## 1. Key findings

1. **Ownership is settled at principle level, and nothing in the V0.2 authority contracts is frozen as a document.** `operator-decisions.md` (OCS) records "Keep Control Plane/Runtime effect authority ... No alternate authorization point". `docs/declarative-governance-registry.md` (OCS) is an adopted direction (operator, 2026-10-21): floor in code, registry as data, evaluators as code. Plan v1.3 s1 and s3.1 (REG, operator-approved 2026-10-24) say a registry "cannot issue OCS grants, substitute for the Control Plane, or authorize effects". Contract `1.2-authority-and-separation.md` labels every normative sentence "PROPOSED until the M0 gate". `m0-decision-record.md` approves ADR-P01..P09 and AOI rows. It does not adopt 1.2 or 1.4 text. F-06 (ADR-P07) and F-10 (ADR-P08) are adopted through their ADRs. The rest of F-01..F-10 and the 1.2 s2 power table are PROPOSED_ONLY. Cite the underlying adopted records, not the 1.2 text.
2. **Atomic effect boundary: implemented, not qualified.** Route B (`execute_claim_atomic`, `BEGIN IMMEDIATE`) is one SQLite database with no remote atomicity. Its profile URN ends `0.1.0-proposed`. `component-lock.json` `qualification_evidence.scope` says "not atomic/refund-intent profile activation". The Route B suites in QUAL (`suites/mvp-d2-route-b`) are "builder evidence ... not a Qualification verdict".
3. **Registry integration at the effect boundary is not designed, and this is the one genuinely open boundary.** `LocalExecutionPolicy.check` runs before the claim transaction (`atomic_local_control_plane_executor.py:69`; transaction begins around `local_authority_effect.py:798`). Plan v1.3 s3.6 (operator-approved) already says this "is NOT a transaction-time guarantee". The Architect prefers R10 Option B for investigation, with expiry clamping (Option C) as defence in depth. No R10 implementation is authorized (`docs/decisions/2026-10-24-r08-s01-authorization.md`).
4. **Revocation is split across three owners, and the registry owns none of it.**
   - Grant and approval revocation sit with the Control Plane and the Runtime destination's retained revoked sets.
   - Registry selection revocation is a separate, signed, registry-side artifact (`01-lifecycle-contract.md` s3.3; `02` s4.7).
   - Route A (check-then-apply) keeps an open residual: OCS `residual-risks.json` R-REVIEW-C0 says the selected C0 "can commit after revocation arriving after revalidation".
5. **Terminal approval revocation exists only at a revision the hub has not selected.** The Runtime head `c5e97e87` has it; the hub lock selects `ec728da6` (lock `moltbot_safe.accepted_sha`). QUAL `suites/mvp-chain/README.md:34` labels `c5e97e87` and CP `7a4bcd40` "PROVISIONAL, UNQUALIFIED". The Qualification expectation NC1-04 failed at `ec728da6`. This is a pin-selection matter (R10-F-03). It is not an architecture conflict.
6. **Negative-evidence custody belongs to the enforcing components.** It is a floor item ("Source and negative-record integrity") in the OCS DGR. The registry holds only record and selection logs. Gaps:
   - Runtime failure rows are written after the refusal, in a separate step.
   - The S04 overlay writes nothing, so an optional-overlay refusal leaves no durable record.
   - QUAL SCN-D07 (restore re-admits effects after history erasure) is INCONCLUSIVE.
   - OCS R-REVIEW-OPERATIONS is open.
   - The plan forbids claiming atomic negative-record custody before independent qualification.
7. **Registry code (`registry_successor/`, R08-S01) is on `main` at REG HEAD.** It is developer-tested, non-authorizing, and nothing in the stack calls it. `docs/sprint-status.md` still says "DRAFT PR". Treat the merge status as verified from the tree, not from that page.

## 2. Authority-boundary matrix

Status key: ADOPTED = a decision record exists (cited); IMPL = implemented, not independently qualified; PROP = proposal only; OPEN = no decision.

| Boundary | Owner | Enforcer | Registry MAY | Registry MAY NOT | Sources (path; commit) | Established | Open |
|---|---|---|---|---|---|---|---|
| Grant and approval issuance and validation | Control Plane (single decision gate); Action Manifest declares only; Orchestrator never mints or widens | Control Plane workflow (`_resolve_inputs`, secondary), host-configured resolver; Route B destination re-reads stored grant/approval state at commit | Carry non-authorizing configuration records and selections | Mint, widen or emulate a grant or approval; model a selection as grant `policy_versions` or `PolicyStatus.digest` (Architect C-03/LD-01); take authority from a matching digest | OCS `operator-decisions.md`; OCS `1.2` s2 (PROP); REG plan v1.3 s1, s3.1, s5; REG `r08-preparation/03` s3.3, s4.1 (REG; OCS) | ADOPTED boundary. Validation code IMPL | `approval_ref` vs `approval_id` relation (OCS `identity-and-lifecycle.md` row 12). Effect identity: `effect_id` changes per `grant_revision`; SP-01 `operation_id` approved at M0 row 9, opt-in |
| Authorization vs evidence separation | Each component's one gate (code floor) | Component gate code; Qualification for independent verdicts | Reference evidence by digest; supply typed records | Treat evidence, replay, a digest or a merge as permission; disable or weaken any floor item (F-05) | OCS DGR "Three partitions"; OCS `1.2` F-04/F-05 (PROP); REG plan v1.3 s3.7; REG `04` s4.4 (REG; OCS) | ADOPTED principle (DGR). Wire formats not frozen | Qualification of per-component enforcement is Lane E's call |
| Runtime admission and evaluation | Execution Runtime owns `LocalExecutionPolicy.check` evaluation. Activation is consumer-owned (v1.3 s3.3). The constructing host integrator is unassigned | Runtime executor policy check (3 call sites, secondary) | Supply S03/r08-v1 record and selection; a read-only consumer narrowing caller ∩ registry | Evaluate, activate or authorize. Fall back to a broader caller policy for a required operation. Add a registry call inside the commit transaction | REG plan v1.3 s3.3, s5; REG `r08-preparation/03` s3.1, s4.1; REG `r08-s01-implementation.md` (REG) | ADOPTED: consumer-owned activation, F1a/F1b to Runtime. Evaluator IMPL | C-01 host integrator (see T2). E-05 construction site. Mandatory profile: "design capability, activation not authorized" (D7) |
| Atomic effect boundary | Runtime destination plus Control Plane claim materialization | `execute_claim_atomic` under `BEGIN IMMEDIATE`; `_validate_claim_state` | Provide immutable data that a successor profile may bind | Claim global or cross-domain atomicity; check authority outside the owner's transaction; substitute its own commit-time check | REG `04` s2 findings 1-2, s4.2; REG `r10-feasibility` s2; OCS `component-lock.json` `qualification_evidence` (REG; OCS) | Route B IMPL, UNQUALIFIED. Boundary principle ADOPTED (v1.2 s3.3-binding, v1.3 s3.6) | Selection/epoch/evaluator binding at commit: PROP only (R10 options A/B/C). Route A not closable |
| Authority revocation | Control Plane (grant status) and Runtime destination (retained revoked sets). Registry owns selection revocation separately | Destination rechecks under lock (Route B); Control Plane `execute()` re-resolve (Route A, with open window) | Issue and publish signed selection revocation; keep append-only revocation history | Revoke or reinstate grants or approvals; let replay or restore revive withdrawn authority; treat "no revocation seen" as valid | REG `04` s2 findings 2, 4, s5; REG `01` s3.3; OCS `residual-risks.json` R-REVIEW-C0; QUAL `suites/mvp-chain/README.md` (REG; OCS; QUAL) | Grant terminality IMPL. Approval terminality IMPL only at Runtime `c5e97e87`, not hub-locked | LD-04 propagation of selection withdrawal to the destination (writer, ordering). B-08 latency bound. Route A fence. Pin choice (R10-F-03) |
| Configuration revalidation | Control Plane at decision and effect time (grant policy refs). Runtime per call (`LocalExecutionPolicy`). Destination at commit (claim rows) | Same | Supply exact pins; wrong or changed identity is refused at the consumer | Perform its own pre-dispatch check as a substitute; use `latest`; hot-swap | REG `04` s4.2, s5; REG plan v1.3 s3.6; OCS `1.3` s5 (PROP) (REG; OCS) | Policy-ref revalidation for grants IMPL. Registry-selection revalidation does not exist | LD-01, LD-09 expiry at commit (Option C clamp is the cheapest stopgap), LD-05 receipt content, freshness 60-vs-300 unresolved |
| Negative-evidence custody | Each enforcing component: Control Plane `EffectTimeRefusal`, Runtime failure rows, ODES journal; GCR for cognitive negative-record continuity | Component code floor. Independent verdicts by Qualification | Keep registry record and selection logs, append-only | Hold effect-time negative evidence; erase or reinterpret history; claim atomic negative-record custody | OCS DGR floor; REG plan v1.2 s3.3-binding; REG `01` s4; REG `02` s4.9; REG `r10-feasibility` s2 item 8 (REG; OCS) | Principle ADOPTED. Custody code IMPL | Refusal rows written post-refusal, not with the decision. Optional-overlay refusal has no durable record. External witness (B-11) and erasure authority (A-10) are operator-open. SCN-D07 INCONCLUSIVE |

## 3. R09 and R10: established vs genuinely open

**Established (reuse; do not re-adjudicate).**
- Three objects (record, selection, activation) are distinct (v1.3 s3.3, operator-approved). Architect-adopted successor division with event-derived state (08 s3a A-01/A-02).
- Registry cannot issue grants or authorize effects (v1.3 s1).
- Activation is consumer-owned. Required missing policy never falls back to a wider caller policy (v1.3 s3.5). Optional overlay refusal means "not applied", not denial.
- Selection is not a grant. Evidence-only attachment is insufficient (C-03/LD-01).
- The pre-claim check is not a transaction-time guarantee (v1.3 s3.6).
- Reuse existing OCS Ed25519 rather than build a fourth system (B-01 direction). Signature is not authorization.
- No global atomicity and no universal reason vocabulary.
- Failure-code mapping (LD-02), LD-09 expiry/effect-time contract, A-05 duration limits and B-10 adapter are delegated to the Architect and component owners (v1.3 s8). They are technical, not operator items.

**Genuinely open (R09).**
- Trust-root custody, issuer enrollment, key ceremony and signer-compromise recovery. The operator must authorize any ceremony (v1.3 s3.8). B-02, B-04 and the B-11 witness holder are operator items.
- Anti-rollback high-water mark (B-05) and the older-record selection rule (B-07). These are Architect items.
- Independent security review of authority-bearing paths (gate G2) and the independent Tier 1 qualifier (F-01/D13, not designated).
- Loaded-code integrity exclusion (B-09).
- Archival, erasure and legal-hold authority (A-10).

**Genuinely open (R10).**
- Choice of binding protocol: Option A, B or B+C (R10-F-01). The Architect leans to B, which needs a successor profile in both the Runtime and the Control Plane (R10-F-02).
- Writer of the authoritative selection row and the withdrawal path (R10-F-04/LD-04).
- Exact-source integration candidate, hub `ec728da6`/`0a41faa9` vs head `c5e97e87`/`7a4bcd40` (R10-F-03/LD-06).
- Receipt content (LD-05).
- Route A vs Route B scope (C-06). Route A cannot be closed.
- Host integrator naming (C-01).
- Independent qualifier for the effect-time path (LD-07).
- Reachability and designation of the five unmediated effect surfaces (OCS M0 row 10).
- Any locked-component change needs separate F3 authorization (OCS M0 rows 11 and §3).

## 4. Candidate conflicts

No candidate here meets the TARGETED_RECONCILIATION bar: two adopted or frozen requirements that are mutually incompatible. Each is a tension between a proposal and an adopted rule, or between two proposals.

- **T1: Who activates a rule set.** The adopted rule is "Activation is consumer-owned" (REG v1.3 s3.3, operator-approved). The V0.2 proposals say "A registry becomes active only through the Control Plane's own gate" (OCS `1.3` s5) and "Rule-set activation | Control Plane ... at an epoch" (OCS `1.2` s4). OCS `operator-decisions.md` marks activation and freshness semantics "OPEN contract detail". The existing behavior is that the Control Plane never references `LocalExecutionPolicy` (REG `03` s3.1). The consequence is that, read literally, the V0.2 proposal would make the Control Plane the activator for Runtime-local F1a. Recommended resolution: the enforcement owner per family activates, with Control Plane activation for Control Plane-owned families (F4/F5) as V0.2 intended. The V0.2 text is SUPERSEDED_BY_ADOPTED_CONTRACT for the Runtime families. Affected: Runtime, Control Plane. P1 impact: record the activation owner per family in the manifest. P3/P4 impact: none.
- **T2: Who names the host integrator.** REG `03` C-01/`08` s3a: "operator designates the production host owner before R10". REG plan v1.3 s8 delegates "C-01 integration host identification" to the Architect and component owners. The existing behavior is that no non-test construction site exists. The consequence is a decision-rights ambiguity, not a technical conflict. Recommended resolution: the Architect and Runtime owner name a synthetic integration adapter for the emulator profile (v1.3 s8). The production host owner stays tied to production activation, an operator item (v1.3 s8 item 3, which controls). Affected: Runtime, Registry. P1 impact: none. P4 impact: emulator profile needs the adapter named.
- **T3: Where selection identity binds in the Runtime claim.** OCS `f3-change-proposals.md` FP-04 and `1.3` s6 (both PROPOSED, unauthorized) list the Runtime policy row `authority_policies_v1` as a place to bind rule-set digest and epoch. REG `03` s4.3 and `04` s4.2 withdraw extending the grant-derived `policy_state` row for registry selections (Architect C-03/LD-01). The existing behavior is that `policy_state` carries only `{ref, version, status}`. The consequence is a risk that R10 revives FP-04's policy-row reading and blurs grant authority with selection. Recommended resolution: scope FP-04 to Control Plane gate rule-sets (`RuleKind`/`rule_identity` channel). Registry selections for Runtime F1a use R10's separate applicability binding. Affected: Control Plane, Runtime. P4 impact: record in the R10 ADR.
- **T4: Hub lock vs provisional tuple.** The hub lock selects Runtime `ec728da6`. The Qualification provisional MVP tuple is `c5e97e87`/`7a4bcd40`, and the NC1-04 terminal approval revocation expectation passes only at `c5e97e87`. The consequence is that registry R10 evidence at `c5e97e87` does not transfer to the locked tuple (and vice versa). This is an ordinary pin reconciliation (R10-F-03), not an operator item.
- **T5: Epoch ownership wording.** OCS `1.3` s3 gives `epoch` ("Monotone activation epoch") to the Control Plane at activation. REG `01` s3.3 has the selection authority assign `epoch`, with the consumer holding a high-water mark. Both agree on monotone, no-downgrade, predecessor-matched. Recommended resolution: the selection authority assigns and the consumer enforces. No action beyond naming it in the P2 contract.

**Missing contract (a gap, not a conflict).** Selection validity and applicability at commit (R10), selection-withdrawal propagation (LD-04) and a durable refusal carrier for registry outcomes (LD-05) have no counterpart anywhere in the V0.2 program. All three are bounded to P4 and P2.

## 5. Could not verify

- Control Plane and Runtime source behavior: all line-level claims are second-hand (REG docs) and "not run" per those docs.
- Orchestrator `ARCHITECTURE.md`/`CONTRACTS.md` (quoted only via OCS `1.2`).
- COG-REG-SHARED-ADD-01: text and digest not in custody (REG `11-addendum-source-custody.md`). No clause is relied on.
- Whether M0 intended to adopt contract text 1.2/1.3/1.4 beyond the listed ADR rows. The M0 record is silent, so these stay PROPOSED_ONLY.
- Independent qualification of any path in this lane. No independent Tier 1 qualification lead is designated, and no qualification verdict covering the atomic boundary, revocation terminality or negative-evidence custody was found.
- OCS `residual-risks.json` items are lock-attached residuals. I did not check whether later hub revisions closed them.
- Engineering Constitution formal adoption: not established (`ADOPTION.md` at the pinned revision requires an adoption instrument). Constitution cites here are guidance only.
