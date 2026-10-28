# Cognous OCS — Static Engineering Plan: Registry Migration of All Eligible Rule Families

**Identifier:** COG-REG-FAMILY-MIGRATION-PLAN/1.1  
**Status:** PROPOSED v1.1 — pending Architect adoption and audit PR #60 acceptance; v1.0 remains frozen  
**Date:** 2026-10-28  
**Execution authorization:** PAUSED pending audit adoption and new Architect authorization. Existing merged M2/M3 code is preserved; M11 PRs remain unmerged.  
**Relationship to existing program:** Successor expansion after OCS Plan v1.5 V09 freeze-candidate preparation; not a modification of the frozen V01–V09 scope, and not a release plan.

## 1. Purpose and completion definition

Systematically externalize **all eligible configurable policy values** currently embedded in, or supplied outside, the Cognous Registry across the relevant OCS components, without externalizing the enforcement constitution. Eligibility is **not equivalent to every literal or branch in source**. A family is eligible only when its value can be represented as a versioned, authenticated, bounded, qualified Registry record and consumed through an existing, source-owned enforcement boundary without widening authority or weakening a mandatory invariant.

**Program completion** means: (a) every identified source-backed candidate has a final MIGRATED, ALREADY-GOVERNED, RETAIN-IN-CODE, OUT-OF-SCOPE, or BLOCKED disposition; (b) every MIGRATED item has a pinned record schema, evaluator binding, admissibility rules, atomic effective-state semantics where applicable, reproducible negative/equivalence tests, and evidence; (c) all in-scope component and repository deltas have been reconciled; and (d) no unresolved item is silently counted as migrated. A BLOCKED candidate prevents a claim of *all eligible families migrated* unless formally adjudicated as ineligible, with rationale and operator approval.

No automatic rollout to production is implied. Independent qualification and release remain separate gates.

## 2. Governing, immutable and historical baselines

- Static Engineering Plan v1.5: `cogno-us/cognous-ocs-registry/docs/plans/PROJECT_PLAN-v1.5.md`.
- Engineering Constitution and ADOPTION.md: `cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`.
- Existing contracts: `r08-v2`, Amendments 1–4; `ADR-REG-S4-0`; existing typed reasons, claim commitments, Control Plane approvals, Runtime effect-commit and pin protocol.
- Historical S02 inventory: `cogno-us/cognous-ocs-registry/docs/s02-inventory.md` and raw `docs/s02-evidence/W1.md`–`W9.md`.
- Historical S06 family recommendation: `docs/s06-next-family-recommendation.md`.
- V09 engineering candidate: Registry #47 merge `b695f67d944286c76100ddab36818f926958297f`; post-merge record Registry #48 `dabe69eeaa301365f18e8e452b8914089c340a99`; Control Plane `d66ae07fa240510efdcc11ed4b3e1189dcefc822`; Runtime #149 merge `b5605f525ae73cbb7adcfef4716c67cdd33a5f7d` and F3 record #150 merge `0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491`; Qualification #237 merge `bb9b08904192b5f50a49e00ed8de0cab80fd7c19`. These are historical anchors, **not** automatically the source heads for future work. At G0 inventory current heads and qualify any changed baseline.
- Preserve V07 F-01 and V08 F-A1 historical negative evidence, V09 limitations, Security-Held Ed25519 #26/#34, and independent V07/V08 gates. This new plan neither resolves nor waives those gates.

No edits to the historical plans, accepted frozen contracts, historical failed results, or the protected `engine/safe_executor.py` evaluator are permitted under this plan. Material contract amendments need a separately approved, versioned successor, not a mutation of frozen contracts.

## 3. Inventory basis and its limits

S02 counted **620** bounded source rows: 354 MANDATORY-INVARIANT, 90 SERIALIZATION-OR-EVIDENCE, 51 INCIDENTAL-CONDITIONAL, 50 REFUSAL-OR-REASON-VOCABULARY, 43 CONFIGURABLE-CANDIDATE, and 32 UNRESOLVED. These categories are **row counts, not the number of migration tasks**. Four of the 43 configurable rows required provisional special dispositions in S02 §3a. The inventory was AI-worker-produced, partially spot-verified, and **not exhaustive**: some test, schema, tool, conformance and other-component directories were outside its survey. The observed `60` versus `300` freshness relationship remains unresolved.

G0 MUST preserve all 620 original classifications and source evidence unchanged, inventory the current version of Runtime and Control Plane, examine relevant missing OCS components and directories, identify changed/moved/deleted locations, and produce an append-only crosswalk with stable row IDs and provenance. Do not invent a numeric total of eligible families in advance of G0 adjudication.

Each candidate row must record: origin (file, symbol, exact commit, S02 ID), current data/constant source, evaluator, governance layer, trust boundary, authority/effect impact, tier, already-externalized status, proposed Registry representation, non-widening operator, contract version, refusal and recovery rules, baseline and test coverage, unresolved questions, and final disposition.

## 4. Hard boundary: configurable values versus intrinsic controls

**May migrate subject to approval:** bounded allow-sets, policy ceilings, freshness settings, host-authored authority-profile declarations, agent permission tables, duplicate windows, approved resource limits, diagnostic thresholds, and safe redaction configuration, to the extent a source-backed decision proves them eligible.

**Must remain in executable constitutional/enforcement logic:** authenticating and pinning records; actor/authority provenance; admissibility and fail-closed validation; check ordering and committed reason-code compatibility; schema/strict-number validation; target-path safety and enumerated match semantics; authorization issuance and revocation; atomic effect/evidence transaction; replay/restore/rollback custody; monotonically enforced floors; denial on unknown state; mandatory security limits and safeguards. A configurable value never disables its own validator or the baseline mandatory floor.

Registry is a **policy-data authority, not an execution-authority issuer**. A signed Registry selection alone never grants approval, activates a policy, or authorizes an effect. Control Plane authorization, Runtime durable activation and commit-time enforcement remain distinct. Values can only narrow the permissible space relative to immutable floors, authenticated source authority, caller restrictions, and current durable state.

## 5. Family disposition and delivery sequence

The F identifiers below retain S02's meaning; they are not new normative Registry schema names. Sequencing prioritizes reusable low-semantic-risk migrations, then broader Tier 1 authority controls, with non-gating families last. Every row is a **candidate pending G0 eligibility adjudication**.

| Wave | Historical family | Source-derived scope and disposition target | Primary risk / precondition | Expected deliverable |
|---|---|---|---|---|
| M1 | **F1b** allow-set completion | `allowed_institutions`, `allowed_authority_domains`. The existing five-set F1a envelope carries these; establish actual narrowed-value differential coverage and decide if any further record versioning is required. | Tier 1; deny-all representation and refusal semantics; unchanged baseline evaluator | Source-backed exact-set non-widening, signed selection and effect-time negative tests |
| M2 | **F1c** numeric ceilings | `max_amount`, `max_effects` | Strict number/binary64 semantics (W1-015), W8-091 origin of effect cap, ordering and equality | Versioned bounded ceiling semantics and differential tests |
| M3 | **F1d** target configuration | `allowed_target_prefixes`, configurable `target_match` choice, if eligible; fixed mode vocabulary, path safety and separators stay code | Prefix/segment semantics not set intersection; ambiguity and traversal | Explicit partial-order or proof of non-widening, exhaustive negatives |
| M4 | **F6** agent permissions | Agent permission allow-list, **only after locating and verifying the actual current `engine/permissions.py` and `permissions.json` baseline**, which S06 says was outside imported baseline | New record mapping, provenance, missing-file deny-all, malformed JSON historical exception | Versioned per-agent record; source-preserving compatibility or approved refusal-only correction |
| M5 | **F7** dedupe/replay window | Configurable dedupe TTL and equivalent eligible profiles | Tier 2 value with Tier 1 replay guard; W3-063 unresolved | Floor-preserving window config; replay and restart oracles |
| M6 | **F3** size/depth/timeout budgets | Only adjudicated resource-limit **configuration**, not mandatory admission floors (depth/node/text/process limits and tools) | Mixed Tier 1/2; resource exhaustion; no default widening | Authenticated bounded resource profiles and denial/failure tests |
| M7 | **F9** tenant-ID length | Bounded tenant ID length if not contract-frozen | Identity canonicalization and compatibility | Versioned bounded value, invariant unchanged |
| M8 | **F10** diagnostic trend thresholds | Non-authorizing thresholds, only if independently proven not to influence authority decisions | Downstream reliance and false benign classification | Bounded diagnostic profile and exact baseline diffs |
| M9 | **F8** demo policy lists | Only if currently reachable as a supported policy configuration; otherwise RETAIN/REMOVE-DEMO by separate decision | Source demo values may feed grant records; no backdoor authority | Decision with provenance, no unreviewed demo-to-production promotion |
| M10 | **F11** redaction defaults | Eligible presentation defaults only; mandatory confidentiality redaction remains protected | Privacy/security Tier 1 for affected fields | Confidentiality-floor invariant, differential and leakage tests |
| M11 | **F4** freshness | Observation/status/approval age parameters and qualified liveness defaults; not the missing-observation check itself | W6-042; `60` vs `300`; precedence; freshness-floor proof | Cross-CP/Runtime consistent, versioned freshness policy and changed-condition tests |
| M12 | **F5** authority-profile declarations | Eligible per-action-class values including status-age, unreadable behavior, revocation assurance, reversibility and evidence thresholds | W8-014 host trust; mixed types; trust authority cannot be Registry-created | Closed schema and Control Plane/Runtime consumer integration without authority widening |
| M13 | **Delta and residual closure** | Any additional eligible families from current-source survey, four S02 §3a dispositions, and all 32 unresolved rows | Requires explicit family eligibility decision; do not bundle unreviewed Tier 1 changes | Complete candidate ledger, qualified/adjudicated disposition per source row |

**No family is automatically authorized by this table.** The Architect approves exact source, contract scope and tier for each increment. F4/F5 are not covered by Plan v1.5 and must use successor versioned contracts and qualification.

## 6. Standard gated execution template for EVERY migration wave

**G0 — Current-state inventory and eligibility (read-only; first sprint).** Reconcile all old/new source locations; separate values from evaluator mechanisms; record authority ownership; adjudicate which candidate rows are true migration obligations and which are already governed, data-supplied, or intrinsically non-migratable. Preserve 32 unresolved until a documented resolution, not by inference. Freeze coverage ledger and choose the first family. **STOP for Architect approval.**

**G1 — Contract and oracle freeze (separate, authorized).** Write minimal closed schema, stable identity, authenticated provenance, applicability, allowed narrowing relation, baseline-fallback rule, minimal qualified execution configuration, unsupported/unknown refusal, version migration and deterministic vectors. Freeze pre-implementation oracles (positive, negative, malformed, forged, rollback, cross-tenant, stale, revoked, changed-condition). Resolve any semantics requiring operator choice. **STOP for contract decision.**

**G2 — Registry producer/consumer change.** Implement an authenticated, versioned value record and eligibility validation through existing Registry mechanisms. No new generic interpreter. No unsupported syntax, implicit authority, wildcard grant or auto-activation. Keep old qualified profile read-only/frozen. Produce component PR and exact-head tests.

**G3 — Control Plane/Runtime wiring, only where actually needed.** Reuse existing authorization binding, trusted installer, durable selection and `BEGIN IMMEDIATE` effect-time guard. Binding and identity must not be supplier-asserted; policy selection cannot override a narrower existing policy; no old/latest fallback. Do not touch protected evaluators unless separately authorized by the Architect. Lock down ownership and cross-repository dependencies.

**G4 — Differential and adversarial qualification.** At fixed exact pins, compare old and new effects and refusals for the representable domain; separately document approved refusal-only divergences and unrepresentable inputs. Test floor protection, no widening, source preservation, stale/revoke/replay/recovery/atomic negative cases, and corruption/refusal. Record full PASS/FAIL/SKIP/NOT RUN inventory. Independent Tier 1 oracle and reviewer for authority/admission-affecting migrations: same-organization automation cannot self-certify independence. Preserve both old and new raw evidence.

**G5 — Merge and freeze gate.** Architect reviews exact source, CI, lineage, independent findings, and operational exclusions. Merge *only* when authorized and safe; merge commits where pinned ancestry matters. Re-pin downstream, update manifest/status, record provenance, and stop before starting the next wave. A successful component CI is not release authorization.

For Tier 2/3 family values, explicitly establish tier from source and dependent consumers; a seemingly diagnostic value must be escalated to Tier 1 if it gates a decision or confidentiality boundary.

## 7. Eligibility decision rules and refusal semantics

A family is **MIGRATABLE** only if all hold:
1. It changes configuration values, not the definition of an invariant or source of authorization.
2. Its ordering or bounds admit an explicit monotone non-widening relation relative to immutable floors and existing policy restrictions; otherwise a separate approved equivalence rule and safe default is needed.
3. Record identity, author, authority, schema, consumer and valid version are authenticated independently of untrusted claims.
4. Unknown/absent/corrupt/expired/withdrawn/conflicting data cannot create extra permission; any safe legacy behavior is explicit and scope-bound.
5. No unqualified bypass path reaches committed effects; selection, approval, activation and effect-time enforcement are separate.
6. Baseline behavior and refusal semantics can be measured and materially changed semantics are approved, not silently normalized.
7. Negative tests and appropriate independent review are feasible at exact pins.

The Architect may choose RETAIN-IN-CODE for a candidate even if syntactically configurable, where externalization would provide no governance benefit or introduce unacceptable trust, replay, complexity or compatibility risk. This is a reasoned disposition, not a migration failure.

## 8. Specific unresolved gates carried forward

- 32 S02 unresolved classifications, including W8-014, W8-091, W6-042, W3-063, and W1-029. **Do not automatically treat as configuration.**
- `60` versus `300` observation/freshness relationship; resolve from exact current consumers before F4.
- S06 deny-all expressibility, typed reason compatibility, E05 lone-surrogate boundary and representation exclusions.
- F6 original source baseline/provenance before new import.
- Numeric semantics for ceilings and timeouts (NaN, infinity, negative zero, precision, overflow, boundary equality).
- What counts as a mandatory floor versus an operator-adjustable ceiling; no default may weaken CA14/CA18 protections.
- V07 independent cryptographic review, V08 independent Tier 1 lead/oracle, Ed25519 #26/#34 SECURITY-HELD, F-A1 anchor/custody limitations and current release exclusions.
- Original S02 is incomplete; G0 must detect any additional source-backed candidate families without manufacturing migration estimates.

## 9. Governance, evidence and delivery controls

One fresh lead-builder session per increment; short-lived nonoverlapping implementation workers only when interfaces are frozen; one primary PR per repository/increment; no mass concurrent authority/schema edits. Retain immutable plan, Constitution and ADR pins in every builder directive. Static plan remains unchanged after adoption; document subsequent decisions as append-only ADRs/amendments. Maintain `docs/sprint-status.md` as the one live status, and the V09 candidate as a historical frozen engineering baseline.

Standard deliverables: `candidate-ledger.json` (source-backed accounting), `family-contract.md`, `oracle-and-budget.md`, versioned Registry schema/vectors, component PR(s), negative test evidence, reviewer disposition, `family-qualification.md`, changed-file inventory, source/tree hashes, and merge/re-pin record. Schema filenames are illustrative and may be chosen consistently at G0; do not duplicate existing normative records.

**Gate failures:** unauthorized effect, policy widening, missing auth provenance, invalid/ambiguous serialization, unknown state accepted, failing atomicity or custody, unverifiable baseline, unqualified material tier change, or unresolved safety-critical classification. Retain failure evidence, stop the affected wave, do not weaken tests.

**Cost control:** no paid provider calls or cloud deployment unless separately budgeted; use bounded predeclared execution caps decided per wave based on risk and test cardinality. No blanket universal numerical cap is invented here; CI, local and independent tests are accounted for separately. Reuse accepted cases, but never substitute historical green tests for changed-head qualification.

## 10. Gate ledger and completion checklist

| Gate | Result required | Authority |
|---|---|---|
| P0 — plan adoption | Accept scope, exclusions, bounded inventory-first sequence | Architect/operator |
| G0 — inventory completeness | Current source delta, all old rows mapped, 32 unresolved explicitly tracked, all new candidates accounted for | Architect |
| G1–G5 per family | Contract, verified source/consumer changes, negative and differential evidence, tier-appropriate independent review, exact-head merge/re-pin | Architect + qualified independent reviewer where mandatory |
| Residual crosswalk | Every candidate has explicit disposition; none silently declared complete | Architect |
| Integrated requalification | Cross-family intersections, precedence, revocation and committed-effect non-widening tested at consolidated exact pins | Independent qualifier where required |
| Final engineering freeze | Exact components, versioned contracts, limitations, raw results, operator exclusions, immutable manifest | Architect |
| Release/production | Independent assurance, Ed25519 security decision and separate deployment authorization | Operator, NOT this plan |

## 11. Immediate next authorized action

**None until adoption.** First proposed increment is **G0 read-only inventory reconciliation**, followed by a distinct Architect eligibility and ordering decision. Do not begin F1b implementation, change current Registry policies, or start F4/F5 by treating this proposed static plan as authorization.

**Standing holds:** independent V07 OPEN; independent V08 NOT STARTED; Ed25519 #26/#34 SECURITY-HELD; formal V09 acceptance HOLD; release/publication/production HOLD. Existing frozen V09 candidate remains available for independent review while the migration program proceeds in a separate line of work.


## 11. Version 1.1 audit reconciliation and revised execution baseline (2026-10-28)

**Precedence:** This section supersedes the historical estimates, wave dispositions and prospective descriptions in §§3, 5 and 8 where they conflict. Other constitutional, security, qualification and execution gates remain unchanged. v1.0 is retained as the immutable predecessor. **This successor is proposed, not yet adopted.** Evidence: [Registry audit PR #60](https://github.com/cogno-us/cognous-ocs-registry/pull/60), head `0f11e5e97b114e79bae0fb29734feae991c278d0`; see `docs/audit/registry-eligibility-2026-10-28/parameter-catalogue.json` and `parameter-reconciliation.md` on that PR. Do not represent these audit files as merged into main before PR #60 merges.

### 11.1 Counting units and program denominator

- 620 historical S02 source-site rows, all mapped; 116 G0 current sites / 97 G0 groups; 444 audited canonical logical rules. These are distinct units and not interchangeable migration denominators.
- 52 canonical rules carry at least one independently configurable parameter; 80 distinct candidate parameters across all ownership categories (77 if excluding three literals retained in code).
- **Provisional Registry-manageable baseline: 19 distinct parameters in 12 canonical rules**, 14 core and five qualified/coupled. 9 are represented and integrated; three more are Registry-represented without a merged consuming Control Plane path; seven are not represented. **10 remain eligible but not integrated**; zero have independent Tier 1 acceptance.
- Three additional parameters are blocked (identity age, mandate age, constructor clock tolerance); one is unresolved (funded merge authorities). Excluded from 19, with explicit decisions needed before inclusion. The ObservationPolicy clock tolerance is separately classified as qualified eligible and is not the constructor clock tolerance.
- The original `5 already governed + 23 eligible = 28 G0 rule groups` is a historical provisional classification, **not** the new program denominator. Do not claim 23 remaining or translate its percentages into parameter-level coverage.
- Track separately: `REGISTRY-REPRESENTED`, `ENFORCEMENT-INTEGRATED`, `INDEPENDENTLY-ACCEPTED`. Composite copies of a parameter in v2/v3/v4 count once; `allowed_target_prefixes` and `target_match` are two parameters but one jointly narrowed target-policy rule.

### 11.2 Completed engineering and held work

- M1/F1a-b: existing five allow-set parameters integrated under r08-v2; negative-oracle gaps are a separate assurance workstream.
- M2: `max_amount` and `max_effects` integrated, Registry #54 merge `ba98dd2689e402a855cacc2c7dc3a108c9144eb1`, Runtime #151 `99f5f05374dc54a998304b5966f5cd2de3b5937b` and #152 `dabaa7701a0fd28ab6dfdf90323d9a792d6d72bc`.
- M3: `allowed_target_prefixes` and `target_match` integrated under composite r08-v4, Registry #56 merge `b7e6a173877c731273858b01b26214147dd0736c`; Runtime #153 merged (record full SHA from GitHub before re-pin); Registry tracking #57 squash `2668094d`.
- M11 remains **OPEN / UNMERGED**: Registry #58 (new r08-v5 F4T constructor clock tolerance), Control Plane #87 (F4 status/approval ages plus separate F4T adapter), Registry accounting #59. Preserve branches and tests. Do not adopt the clock-tolerance field by merging #58 without a scope/range decision. CP #87 has construction-time-only revocation observation and its new pin-dependent tests did not run in its native CI; resolve these as real integration boundaries before merging.
- M12 and later waves are paused. Earlier M4–M10 candidate scopes are historical and **must not** be automatically treated as migration obligations when the audit classifies them issuer-owned, provider-owned, retain-in-code or out of scope.

### 11.3 Revised prioritized migration backlog

**Priority 1 — F4 Control Plane consumption:** two existing Registry-represented scalars `status_max_age_seconds` and `approval_max_age_seconds`. Determine an atomic applicable family/binding path and lifecycle revalidation, then wire the Control Plane consumer using existing F4 representation. Do not mix this implementation with unauthorized constructor `clock_tolerance_seconds`.

**Priority 2 — F5 Control Plane commitment coupling:** `class_max_status_age_seconds` already represented in Registry, without a Control Plane consumer. Decide how narrowed class data enters `approval_commitment` before implementation. Coordinate with `on_unreadable` and `requires_revocation_assurance` only when their distinct constraints and identity preimages are established.

**Priority 3 — Remaining audit-confirmed eligible parameters:** observation policy max age and qualified clock tolerance (separate from constructor tolerance), reversible-policy posture, anchor deadline, terminal revocation enablement and any other named entries from the approved `parameter-catalogue.json`. Implement only with actual consumer, source-backed narrowing relation, identity/commitment binding and Architect authorization.

**Blocked or unresolved:** identity/mandate ages, constructor clock tolerance, funded merge authorities. Never silently reclassify these as eligible. Redaction minimum floors and other new control proposals are feature requests, not migration of existing values without a separate decision.

### 11.4 Required Architect decision ledger

- **AR-1:** Whether constructor `clock_tolerance_seconds` may become Registry-managed; historical DR-CP-AGE-1 calls it out of scope, not affirmatively permitted. Decide separately from `ObservationPolicy.clock_tolerance_seconds`.
- **AR-2:** If AR-1 permits it, approve source-backed range and ordering; do not infer `0..2147483647` is a mandatory host bound.
- **AR-3:** Confirm no merger or reclassification of distinct constructor/observation tolerances.
- **AR-4:** Identity and mandate age fields remain blocked unless separately authorized.
- **AD-07:** Add a dated decision-register addendum ratifying the already-authorized and merged M2/M3 narrowing; retain the historical open row unchanged.
- **F4/M11:** Explicitly resolve multi-family atomicity and live revocation before merging Control Plane consumption; do not accept startup-only checking as continuous effect-time verification.
- **F5/M12:** Resolve approval-commitment binding of Registry-narrowed per-class configuration before implementing its consumer.

### 11.5 Resumption and completion gates

1. Review and merge corrected audit PR #60 on unchanged head with required CI, without modifying frozen evidence.
2. Review/adopt v1.1 plan in a separate change; update the live migration status and parameter ledger after audit acceptance. The historical v1.0 stays unchanged.
3. Architect explicitly authorizes the first scoped restart (F4 ages-only is the recommended first increment). Do not presume that plan adoption authorizes execution or M11 PR merges.
4. Continue small Registry/consumer PRs with exact pins and normal CI, fix actual defects, preserve protected evaluators and independent Tier 1 acceptance requirements. Update the parameter-level denominator only through a documented audit amendment and Architect ruling.
5. Completion means every **confirmed** manageable parameter is integrated and qualified, or has an explicit approved deferral/exclusion. Keep represented, implemented and independently accepted counts separate; blocked/unresolved items remain visible.

**Standing holds:** independent V07/V08 and Tier 1 acceptance pending; Ed25519 #26/#34 SECURITY-HELD; release, publication, production HOLD.
