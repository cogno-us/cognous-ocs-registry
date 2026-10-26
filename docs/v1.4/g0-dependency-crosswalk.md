# G0 dependency crosswalk

G0 IN REVIEW. Documentation only; proposal for Architect review and operator approval. Nothing here authorizes S01-S09 or any implementation. Dispositions: SATISFIED / REQUIRED / DEFERRED / NOT APPLICABLE / UNVERIFIED. "Satisfied" means the obligation is met **at the level stated** (specified or developer-tested), never independently qualified. Sources: [plan v1.2](../plans/PROJECT_PLAN-v1.2.md) section 5 (R07-R18), [plan v1.3](../plans/PROJECT_PLAN-v1.3-DRAFT.md) section 6 (P0-P6), [plan v1.4](../plans/PROJECT_PLAN-v1.4.md) section 4 (S01-S09), the [EXT cards](../p1-extraction-plan/11-ext-pr-execution-cards.md), the [closeout ledger](../closeout/program-closeout-2026-10-26.md). Profile: [MSOP-F1a-C11](g0-minimum-profile.md).

## 1. Part A: v1.3 phases P0-P6 and v1.2 obligations R07-R18

| Obligation | Owner | Existing implementation or evidence | v1.4 sprint | Disposition | Rationale and reference |
|---|---|---|---|---|---|
| P0 reconciliation | Registry | #21 `d61ef729` | none | SATISFIED (S) | Closeout ledger |
| P1 scenario + extraction profile (R07) | Registry, Qualification | S02 inventory #3; Stack Qualification scope assessment (696 scenarios, 33 gaps); P1 plan #22; P1 follow-ups #36 | G0 | PARTIAL: operator adoption of exact scope pending | G0 proposes `MSOP-F1a-C11`. S02's 32 unresolved classifications and the 60-vs-300 relationship stay unresolved (none affects F1a) |
| R07 critical rulings (W8-091, W3-063, W9-027, W8-014, W6-042, 60 vs 300) | Registry/Architect | Not decided in the repository | none | DEFERRED | Affect families outside F1a. W8-014 is F5. Implication: those families cannot be migrated until ruled |
| R08 versioned contract | Registry | `r08-v2` #25/#32, family `f1ab` #29, identity #33 | none | SATISFIED (S+I+D) | Frozen |
| R08 GCR preliminary review | Registry, GCR architect | [07-gcr-compatibility-boundary](../r08-preparation/07-gcr-compatibility-boundary.md) (specified); GCR architect disposition not found | none | DEFERRED; disposition UNVERIFIED | Missing evidence: a recorded GCR architect disposition. Not needed for an OCS-only demonstration (v1.3 section 6) |
| P2 / R09 authenticated lifecycles, selection, custody, anti-rollback | Registry; Runtime holds state | Verifier #19, Ed25519 #26 and core hardening #34 (SECURITY-HELD), kit #28, ADR-S4-0 (specified) | S01 (withdrawal, snapshot floor), S04 (durable state, anti-rollback), S07 | PARTIAL: REQUIRED | Registry-side verification is developer-tested; withdrawal, durable consumer state and independent security review are missing |
| P3 typed extraction, Runtime lane (F1a) | Runtime | None; Runtime unchanged since `c5e97e87` | **none** | REQUIRED, **no owning sprint** | Mandatory gap G0-GAP-1 below |
| P3 typed extraction, Control Plane lane (F4/F5) | Control Plane | R6 #84 delivers approval generation and ceilings only | none | DEFERRED | Not needed for F1a (section 2) |
| P4 / R10 integration and effect-time boundary | Runtime, Control Plane | None end to end; ADR specifies | S02, S04, S05, S06 | REQUIRED | Core of the demonstration |
| R11 family migrations | Registry + owners | F1a record/compose exist (S03/S04, #29); F4/F5 families (#31) built, unconsumed | S06 for F1a only | F1a REQUIRED; other families DEFERRED | Plan v1.4 section 2. Each deferred family stays unmigrated; customers keep code or host constants |
| R12 distribution and auditability | Registry, Runtime | Evidence streams specified (ADR section 4); nothing built | S04-S06 (evidence only) | PARTIAL: log/evidence REQUIRED; publication, discovery, cache invalidation, dashboards, CLI DEFERRED | The create-approve-select-apply-observe-revoke cycle is exercised by S06 as a test, not as a service |
| P5 / R13 cleanup | Owners | None | none | DEFERRED | Valid only after qualified migration; nothing may be retired now |
| R14-R16 GCR | GCR owners | None | none | DEFERRED | Optional subsequent profile, never blocks OCS-only (v1.3 section 6). Capability not available: cross-domain interoperability |
| P6 / R17 independent security, qualification, operations acceptance | Independent parties | None; Tier 1 NOT STARTED; GAP-G4-13 open | S07, S08 | REQUIRED (verifier and Runtime paths, one exact-pin run); SBOM/licences/supply chain REQUIRED for the candidate; key rotation/compromise, rollout/rollback, runbooks, incident drills DEFERRED | Not satisfiable by builder or AI review (Constitution ADOPTION.md; plan section 5) |
| R18 release candidate and handover | Operator | None | S09 (evidence freeze only) | DEFERRED for release; S09 REQUIRED for the candidate record | No automatic release |

## 2. Part B: do the unfinished EXT items block the minimum demonstration?

"Demo" = required for `MSOP-F1a-C11`. "Later" = required for a later release or broader profile.

| Item | Demo? | Later? | Disposition and reason | v1.4 |
|---|---|---|---|---|
| EXT-S1-6 withdrawal and snapshot floor | **Yes** | Yes | REQUIRED. Withdrawal and snapshot-floor refusals are in the required demonstration; codes exist only as declarations (`registry_successor/v2_codes.py`), no emitter | S01 |
| EXT-S1-9 adversarial verifier battery | **Partly**: cases for tampered, unapproved, expired and replayed selection | Yes | REQUIRED, **no owning sprint** (plan says reused within acceptance/independent testing). Mandatory gap G0-GAP-2 | none; S06/S08 |
| EXT-S2-1 Runtime characterization battery | Yes (baseline for byte-identity and the F1a denial order) | Yes | REQUIRED (test-only) | none; fits S03 regression or S06 |
| EXT-S2-2 narrowing adapter | **Yes** | Yes | REQUIRED, **no owning sprint**. Mandatory gap G0-GAP-1 | none |
| EXT-S3-1 Control Plane characterization | Only the unchanged-claims control | Yes | REQUIRED as a re-run at new heads (plan S03 already re-runs "S3-1 regression") | S03 |
| EXT-S3-2/3 age helper and F4 host factory | No: F4 values are not in the profile | Yes, if F4 is adopted | DEFERRED. Capability not available: central freshness control | none |
| EXT-S3-4 approval generation part | Yes | Yes | SATISFIED for generation and ceilings by #84 (D); AR-11 is exercised end to end in S06 | S02/S06 |
| EXT-S3-4 per-class `min` (F5) | No | Yes, if F5 is adopted | DEFERRED. Capability not available: central per-class authority | none |
| EXT-S3-5 constructor hardening | No | Optional | DEFERRED (card marks it outside the minimum) | none |
| EXT-S4-1 | n/a | n/a | NOT APPLICABLE (absorbed in S1-5; plan says NOT REQUIRED) | none |
| EXT-S4-4 claim-carried binding | Yes | Yes | REQUIRED | S02 |
| EXT-S4-5 re-pin and regression | Yes | Yes | REQUIRED | S03 |
| EXT-S4-2 Runtime destination and guard | Yes | Yes | REQUIRED, split into two PRs | S04, S05 |
| EXT-S4-3 emulator integration | Yes | Yes | REQUIRED | S06 |
| EXT-S5 predeclaration and gates | No (builder stage) | Yes | REQUIRED for the candidate verdict; preparation exists in #231; no automatic equivalence (plan section 4) | S07-S08 |
| EXT-S6 freeze and full run | No | Yes | S09 gives the evidence freeze only; the exact-pin full run is S08 | S08-S09 |

## 3. Mandatory gaps for Architect disposition (no new increment created)

**G0-GAP-1: Runtime-side F1a narrowing is unowned.** The ADR's guard (S4-2, plan S05) compares the claim-carried identity with the durable row; it does not apply the verified selection's allowed sets to the Runtime's `LocalExecutionPolicy`. The Registry has `compose_f1a` (`registry_successor/compose.py`), but the Runtime must call or mirror it so that `op-refused` is refused and the effective-policy digest describes the policy the gate actually applied ([identity spec](../ext-implementation/ext-s1-5-effective-policy-identity-spec.md)). EXT-S2-2 ("narrowing adapter", new file, `safe_executor.py` untouched) is that work, and plan v1.4 maps no sprint to it. Plan v1.4 section 4 already provides the route: a separate operator-approved amendment. Options: (a) add a bounded Runtime sprint before S04 or fold it into S05; (b) weaker demonstration limited to binding, withdrawal and restore refusals with no registry-narrowed value (not recommended: it would not demonstrate registry governance). Evidence it is genuinely missing: Runtime `c5e97e87` has `LocalExecutionPolicy` with no registry-driven narrowing, and the closeout ledger records EXT-S2-1/2 NOT STARTED.

**G0-GAP-2: builder-side adversarial battery (EXT-S1-9) has no sprint.** The plan reuses it in acceptance, but forged, replayed, wrong-participation, unselected-pin and older-snapshot cases need an author before S06 evidence. Existing tests cover part (see the [acceptance matrix](g0-acceptance-matrix.md)); the remainder is unassigned. Options: carry it in S01 (Registry, same files) or S06; it must still be handed to the independent oracle author and never labelled qualified.

**G0-GAP-4: r08-v2 signing-domain separation is specified but, on static reading, not implemented in the verifier.** `docs/r08-v2-contract.md` section 1 requires the signing input `b"ocs-reg/r08-v2/selection\n" + canonical_bytes(statement)` so that a v1 signature never verifies a v2 statement. `registry_successor/verify.py` `_authenticity` (line 440) builds the message with `selection.signing_input`, which hard-codes the `r08-v1` prefix (`selection.py:27`), for every `contract_version`; `verify_selection_v2` delegates to it. `docs/adapters/ed25519.md` already recorded "no r08-v2 signing input or verification path exists in the core" at #26, and no later change was found. This is an inspection finding, **not executed** (UNVERIFIED by test) and not a contract change: it is a possible implementation defect against a frozen contract in a SECURITY-HELD area, and the "v1-signed replayed as v2" case (EXT-S1-9) has no test. Required before any demonstration that signs `r08-v2` selections; owner Registry; suggested home S01 (same verifier files) pending Architect ruling. Missing evidence to settle it: one read-only probe that verifies a v1-prefixed signature through `verify_selection_v2`.

**G0-GAP-3 (readiness, not a code gap): no independent Tier 1 lead.** Plan section 7 asks for one before S07, preferably before the S06 oracle freeze. Operator action.

G0-GAP-3 and G0-GAP-4 are listed for completeness. None of the gaps makes the existing sequence infeasible by itself, but G0-GAP-1 makes the S05 exit ("typed selection guard") insufficient to show a registry-narrowed refusal, so the Architect should rule before S01 is authorized.

## 4. Dependency order for the minimum demonstration

G0 approval → S01 (Registry withdrawal/snapshot floor; G0-GAP-2 optional here) → S02 (Control Plane claim-carried binding) → S03 (re-pin) → [G0-GAP-1 Runtime narrowing, if ruled in] → S04 (durable state) → S05 (guard) → S06 (end-to-end) → S07 → S08 → S09. Registry, Control Plane and Runtime changes touching shared authority state or the claim schema stay serialized (plan section 4). Concurrency is allowed only for read-only inventories and test planning.
