# OCS Registry — Static Engineering Program v1.2

**Plan ID:** OCS-REG-PLAN v1.2  
**Issued:** 2026-10-24 (operator-directed successor planning; repository recording may be later)  
**Status:** PROPOSED FOR OPERATOR ADOPTION; **no implementation sprint authorized by creation or merge of this plan**  
**Program owner/authority:** Cognous operator. **Plan custodian:** OCS Architect. **Execution:** delegated engineering builders with bounded sprint authority.  
**Repository:** `cogno-us/cognous-ocs-registry`. **Sibling system:** `cogno-us/cognous-iss-core` (and its designated ISS owners).  
**Constitution reference:** `cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; reference is not itself proof of formal adoption.  
**Predecessor:** [PROJECT_PLAN-v1.1.md](PROJECT_PLAN-v1.1.md), frozen blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`.  
**Release / publication / production:** HOLD until distinct operator acceptance; plan adoption is not deployment approval.

## 1. Mission and definition of complete

Build a **fully functioning, governed, versioned rule registry** for the selected OCS policy families and a **coordinated ISS-compatible registry architecture**, with authenticated selection, deterministic validation, consumer integration, governed activation, negative/changed-condition coverage, independent qualification and operational custody. The end state must be demonstrated in supported execution paths, not merely in stand-alone parsers or synthetic overlay tests.

**Fully working** means all of the following are established for the explicitly declared supported profile:

1. Authorized administrators can create, validate, approve, publish within an approved environment, select, supersede, revoke and audit typed registry records using a documented, recoverable, least-privilege workflow.
2. The registered OCS consumers use an authenticated, approved and version-pinned selection, apply only applicable records, enforce fixed code-owned mandatory invariants, and refuse missing, tampered, invalid, expired, revoked, unsupported, stale or incompatible policy as required by the operation's defined governance profile.
3. No registry record can issue its own authority, create an action grant, broaden an existing permission, bypass effect-time checks, defeat revocation or turn failed custody into permit.
4. The supported integrated OCS admission-to-effect path, including Control Plane/Runtime and evidence/decision boundaries, has reproducible positive, negative, concurrent and changed-condition evidence.
5. ISS supports the agreed **shared logical envelope conventions** through an independently approved and qualified ISS-side interface; ISS retains its own cognitive admission, evidence, reliance, memory and canonical-state authority. Cross-system compatibility and negative isolation are tested; a common envelope does **not** imply a common policy interpreter or transferable authority.
6. A versioned, source-backed **coverage register** identifies implemented, qualified, deferred, non-migratable, unresolved and unsupported policy families. The migration goal is all **approved, applicable, configurable families in the adopted operational profile**, not indiscriminate ingestion of 3,190 historical source statements.
7. Independent risk-proportionate qualification, security and supply-chain review, operational recovery/rollback exercises, documentation and an explicit release decision complete the program.

**Not required to claim bounded operational completion:** migrating mandatory constitutional/invariant logic out of code; implementing every historical reason code, validator, test scenario, draft requirement or unknown V0.1 entry as a policy. Any such claim would be false.

## 2. Evidence and frozen baselines

- S01–S06 under v1.1 are **DEVELOPMENT PROGRAM COMPLETE — BOUNDED**, not operationally qualified. S06 closeout merge `1870f3a62ee16cdea53c4c23a8df8c9be3c2f2cf`; S06 tests reported 373 pass, 0 pytest fail, 0 pytest skip, with **three distinct E05 behavioral SKIPs in frozen raw evidence**.
- Preserve unchanged the original baseline, S03 validator and contract, S04 optional-overlay consumer, S05 oracle/expectations/raw evidence, historical reports, static v1.1 plan and their exact pins. A successor implementation is additive/versioned until a separately authorized deprecation and independently verified equivalence.
- S02 is a bounded source-code inventory: 620 construct rows, 43 configurable candidates and 32 unresolved classifications. The historic `catalogue-v0.1` contains 3,190 **source-statement entries**, predominantly vocabulary/requirements, with no native configurable-policy record type; no distinct OCS V0.2 release inventory has been established. Historical recovery draft PR #13 is a research input, **not yet an adopted authoritative inventory**. Re-verify its latest review head and merge state before use.
- Current S03 represents only three nonempty allow-lists: `allowed_units`, `allowed_adapters`, `allowed_actions`; it is deliberately stricter than the historical constructor. S04 refusal leaves caller policy in force because the overlay is optional. Digest checks are **integrity, not authentication**. Installed file hashes do not authenticate running Python code. No operational manifest pin has been approved. These are required design inputs, not defects silently declared solved.
- The shared-registry addendum `COG-REG-SHARED-ADD-01` supplies architectural intent only until independently source-verified and adopted by both OCS and ISS owners. Record exact document revision/digest when available; do not claim an unpublished addendum was verified.
- All source, test and decision references must carry immutable revisions. Newly discovered evidence may change a decision record or necessitate v1.3, but **not this frozen static plan's text**.

## 3. Architecture contract and non-negotiable invariants

### 3.1 Three separate objects

**Record:** typed configuration/evidence-reference data with stable identity, version, canonicalization, provenance, applicability, evaluator binding, content digest, and supersession lineage. A record has no self-authorizing effect.

**Selection:** independently attributable, authenticated, signed or comparably custody-protected owner-approved choice of specific records/versions/digests, scope, effective period, conditions and revocation reference. Never select `latest` implicitly or infer selection from record status alone.

**Activation:** the domain consumer's verified decision that a selected applicable record can govern this invocation. Approval of a record is not an execution grant; OCS still requires applicable action authority at the effect boundary and ISS independently requires its cognitive admission.

### 3.2 Typed semantics, not universal code-as-data

- Use a small shared **envelope and selection-reference discipline** with explicit family-specific schema, deterministic evaluator and separately versioned compatibility contracts.
- For comparable allowed sets, use intersection. For numeric maxima/minima, use correct typed monotonic composition with domain-specific precision, units and floors. For evidence and status requirements, use explicitly defined typed combination; if no sound operator exists, **refuse unsupported composition**. Never invent one universal rule algebra.
- Define explicit **deny-all** or unambiguous empty-set semantics in a new version when required; a refused empty record that leaves caller policy active is *not* denial. Define optional versus required participation per operation and prohibit permissive fallback for required participation.
- Keep fixed enforcement, grant, approval, revocation, effect-time rechecks, negative evidence, tenant isolation, safe serialization, bounded resource checks and applicable constitutional floors in component-owned code.
- Preserve closed refusal/reason-code vocabularies through separately versioned compatibility processes; catalogue inclusion is not authority to rewrite them.
- No registry-provided scripts, expressions, dynamic imports or arbitrary evaluators. A family binds to a vetted registered code evaluator with source/build identity.
- Loaded-runtime integrity and deployment custody must be addressed for the adopted threat model; hashing a file on disk is insufficient evidence of loaded-code integrity.
- Separate OCS effects from ISS cognition; no second decision authority, universal policy engine or competing canonical state/ledger. The shared registry is a logical discipline, not necessarily a shared service/database.

### 3.3 Threat model, custody and authorization

Threat model must distinguish untrusted policy/record input, unauthorized repository changes, compromised selection/storage, stale or revoked authority, cross-tenant substitution, runtime tampering, infrastructure compromise, insider roles and unavailable dependencies. State exclusions honestly. Approved trust roots, key lifecycle, authenticated policy provenance, signed/verifiable manifests or equivalent custody, least privilege, audit logs and recovery must be defined *before active Runtime adoption*. Do not claim security against out-of-scope administrators or compromised runtime.

## 4. Work authorization and concurrency

This document approves **planning structure only**. Each sprint below requires an explicit operator implementation authorization, including scope, owning repositories, source pins, allowed effect environments, spending limits and merge boundaries. No developer or review bot can authorize itself to advance stages or publish.

- Target sprint 1–3 working days, maximum planned 5; split larger work into separately authorized subincrements retaining the numbered phase gate. Time targets are guidelines, not proof or deadlines.
- Parallel workers are encouraged on disjoint files/components. One canonical integration owner serializes shared schema, trust contract, authority and state changes. No overlapping edits to same file or canonical activation path.
- One primary PR per bounded increment, with exact head, changed-file inventory, tests, negative evidence, review findings and PASS/BLOCKED. Routine repair/eligible merges are autonomous **only within the operator-authorized sprint**. Material semantic/security changes escalate.
- Copilot reviews exact heads as developer technical reviewer; it cannot substitute for independent Tier 1 qualification. Independent qualification owner must not solely accept their own oracle and implementation.
- No paid model calls, cloud provisioning, credentialed effects, real production changes or deployment without specific budget/environment authorization.
- Retain static plan only at `docs/plans/PROJECT_PLAN-v1.2.md`, live execution status only at `docs/sprint-status.md`, dated decisions in `docs/decisions/`, immutable evidence in qualification source repos. Do not replicate test-result narrative across README files.
- Every phase must list supported profiles, unsupported profiles, explicit risks and required next operator decision. No PASS by skipping mandatory cases.

## 5. Sequenced engineering program

**P1 and P2 are information/architecture gates; P3–P8 deliver OCS registry functionality; P9–P10 align ISS; P11–P12 qualify and release.** Phase numbers are program increments, not automatic sprint authorizations. The historical v1.1 S01–S06 IDs are unchanged; proposed v1.2 work uses **R07–R18** to avoid retrospectively renaming history.

### R07 — Source inventory and authoritative migration register
**Dependencies:** v1.1 closeout; recovery PR #13 provenance reconciliation.  
**Tasks:** resolve historical V0.1/V0.2 naming; incorporate source-pinned S02 and recovery crosswalk without importing 3,190 entries; classify each current candidate as parameter, mandatory invariant, reason vocabulary, non-policy, deferred or unresolved; trace real source evaluator/consumer; rule on critical W8-091, W3-063, W9-027, W8-014, W6-042 and 60-versus-300 *before any affected family is migrated*. Scope bounded to a named baseline set; inventory incompleteness visible.  
**Exit:** signed-off taxonomy, prioritized family/owner matrix, provenance and denominator report, unresolved decision queue, family-specific acceptance cases; no source semantic change. **Gate:** operator adopts candidate migration profile.

### R08 — Versioned contract and ISS cross-system architectural review
**Dependencies:** R07.  
**Tasks:** propose successor schema distinct from frozen S03; minimal shared record envelope, explicit typed payloads, evaluator registry, applicability, selection pin, supersession, status, effective time, refusal semantics, explicit deny-all, compatibility and profile capability discovery. Compare with ISS cognitive admission, StateDelta/reliance/evidence/memory architecture through ISS owner. Record adopted/shared and rejected/commonality assumptions.  
**Exit:** versioned schemas, formal invariants, negative examples, migration/rollback and compatibility plan, ISS Architect disposition, exact cross-system interface contract; no implementation. **Gate:** operator approves contract version and scope; no implicit adoption of ISS policy semantics.

### R09 — Authentication, approval, selection and custody
**Dependencies:** R08.  
**Tasks:** implement an auditable, access-controlled record lifecycle, immutable approved selection manifests/pins, trusted activation configuration, authorization changes, anti-rollback/version rules, revocation and key/identity management or equivalent approved custody, recovery and reconciliation. Separate record approval from effect authority. Implement no automatic `latest` activation.  
**Exit:** negative tests for forged/altered/replayed/cross-tenant/expired/superseded/revoked selection, source substitution, stale cache, missing custody and rollback; documented operator workflow and external anchoring where needed. **Gate:** independent security review of authority-bearing paths before activation.

### R10 — OCS integration: mandatory/optional admission and effect-time boundary
**Dependencies:** R09.  
**Tasks:** wire registry selection to actual supported OCS Control Plane and Runtime paths; define exact ownership and consistency at authority-to-effect, including in-flight revocation, withdrawal, evidence invalidation and version changes. For required policy, missing/refused registry is HOLD/DENY as semantics dictate; optional profile explicitly remains optional and is never misrepresented as mandatory denial. Bound caching; atomically bind selection identity to admission/effect evidence.  
**Exit:** live component integration tests in safe emulator, exact record/manifest/evaluator identities in decision/evidence; no unauthorized widening and no split-brain policy. **Gate:** an effecting production path remains inactive until qualification.

### R11 — Policy family migrations, bounded and typed
**Dependencies:** R08–R10 for active integration; R07 family approval.  
**Tasks:** migrate approved configurable families **one family per subordinate authorized PR/lane**. Default candidate order for architectural assessment: remaining F1 set fields (institutions, authority domains), F6 agent permissions, then F1 numeric ceilings/target prefixes with distinct operators, F4 freshness, F5 authority profiles, and justified F7/F3/F9/F10/F11 where operational value warrants. Not every listed family is automatically in the adopted MVP. For each: upstream pin, authority tier, registered evaluator, schema, refusal/widening proof, independent expected-outcome oracle, differential and changed-condition battery, and legacy cleanup only after qualified cutover.  
**Exit:** approved-family coverage matrix with complete qualifier and owner, zero unexamined transitions; non-migratable invariants still in code. **Gate:** each Tier 1 family separately independently qualified before activation.

### R12 — Cross-component policy distribution and auditability
**Dependencies:** R09–R11 selected profile.  
**Tasks:** secure record publication/discovery, tenant and institution scoping, source/manifest/evaluator pin distribution, deterministic cache invalidation, observability, audit evidence, denial reasons and operational dashboards or CLI. Reuse OCS existing Evidence/ODES and verification mechanisms; avoid unnecessary new database/service.  
**Exit:** reproducible end-to-end policy create→approve→select→apply→observe→revoke cycle and recoverable audit trail, including unavailable stores and stale subscribers.

### R13 — OCS cleanup and legacy configuration retirement
**Dependencies:** qualified R11 migrations and working R12 profile.  
**Tasks:** identify only provably redundant embedded *policy choices* and obsolete configuration loaders, not code-owned safety invariants. Preserve historical versions and rollback adapters until cutover gate. Separate per-component PRs; verify no hidden active consumer or permissive fallback remains.  
**Exit:** retired-path reachability report, matching behavior after removal and component regression evidence. **Gate:** no forced deletion of old code while unsupported consumers remain.

### R14 — ISS read-only crosswalk and owner-approved interface
**Dependencies:** R08 shared architecture and ISS core readiness; ISS independent architectural authorization.  
**Tasks:** examine ISS canonical StateDelta, cognitive admission, evidence/reliance and memory profile contracts. Map only envelope, manifest identity, provenance, version and reference semantics across OCS/ISS. Identify incompatible types and preserve independent authority; no ISS execution changes in this phase.  
**Exit:** joint versioned compatibility crosswalk, named OCS/ISS owners, negative isolation matrix and ISS readiness disposition.

### R15 — ISS local registry consumer and compatibility qualification
**Dependencies:** R14; relevant ISS core sprints completed and ISS operator authorization.  
**Tasks:** implement a minimal ISS-side **read-only, pinned** consumer for separately approved ISS families using the agreed envelope; ISS-owned evaluator and canonical state authority remain exclusive. Validate missing/untrusted/stale/withdrawn selection, profile mismatch and forbidden OCS-effect authority transfer.  
**Exit:** ISS-owned independent qualification, frozen crosswalk evidence and source pins; no ISS execution grant from OCS registry. **Gate:** ISS owner accepts local profile.

### R16 — Cross-system compatibility and end-to-end governance
**Dependencies:** R10–R12, R15.  
**Tasks:** cross-system manifest compatibility, provenance and schema/version negotiation; test both systems as independent consumers of common envelope conventions, including revocation propagation, stale decisions, negative records, inconsistent versions and outage recovery. Do **not** require a single physical store or global authority ledger unless separately justified and authorized.  
**Exit:** independent OCS and ISS outcomes, compatibility report, no authority transfer and no hidden shared interpreter; cross-system HOLD on unsupported combinations.

### R17 — Independent security, qualification and operations acceptance
**Dependencies:** completed supported operational profile and ISS compatibility.  
**Tasks:** adversarial source/selection/loaded-code custody checks, changed-condition races, isolation, policy confusion, fuzz/invalid data, resource exhaustion, backups/restore, key compromise/rotation, rollout/rollback, SBOM/licenses, supply-chain and distribution controls. Freeze candidate source and manifest digests **at qualification boundary**, not at every exploratory sprint. Run independent exact-head component and integration batteries against intended deployment environment.  
**Exit:** signed independent qualification verdict with negative evidence and residual-risk ownership, truthful supported-profile matrix, reproducible package/restore, operational runbooks and incident drills. Defects BLOCK acceptance; ordinary developer/Copilot PASS is insufficient.

### R18 — Release candidate, handover and production authorization
**Dependencies:** R17 PASS and each affected owner sign-off.  
**Tasks:** finalize release manifests, distribution exclusions, change logs, operator/admin documentation, migration and rollback guides, environment-specific trust configuration and release checklist; obtain separate operator release, publication and production decisions as applicable.  
**Exit:** working operational registry for declared supported OCS profile and independently qualified ISS coordination; all deferred families explicitly tracked. No public release, production activation or claim of full historic-rule coverage by default.

## 6. Program gates and evidence ownership

| Gate | Minimum evidence | Decision owner |
|---|---|---|
| G0 Program adoption | v1.2 approved, scope and exclusions recorded | Operator |
| G1 Inventory and architecture | R07 taxonomy, R08 typed schema and ISS review | OCS Architect + operator; ISS Architect for ISS-facing contract |
| G2 Authority custody | R09 authenticated selection, adversarial negatives and security disposition | OCS authority owner + independent reviewer |
| G3 OCS active integration | R10 admission/effect-time tests with approved pins in safe environment | OCS Runtime/Control Plane owners + operator |
| G4 Family cutover | Per-family differential, refusal and independent Tier 1 sign-off | Domain owner + independent qualifier |
| G5 ISS coordination | R14–R16 independently accepted contracts and isolation | ISS Architect/owner + OCS owner |
| G6 Operational qualification | R17 exact-head full qualification, security, recovery and package evidence | Independent qualification owner + operator |
| G7 Release | R18 signed artifact, distribution, production/environment decisions | Operator; each affected system owner |

A gate may be BLOCKED, DEFERRED or NOT APPLICABLE only with explicit durable rationale and owner; never silently omitted. External ISS readiness may run concurrently once its separate authorization exists. No cross-system operation is declared complete if ISS is only theoretical.

## 7. Migration acceptance standard

For each approved family record:
- exact source and evaluator pins; values and versioned schema; authenticated selection and bounded applicable consumers;
- independently predeclared expected positives, negatives, boundary values, missing/unsupported version, bad provenance, malicious record, revoked/superseded policy and changed-condition tests;
- unchanged mandatory enforcement and non-widening, including cross-field and cross-policy interactions;
- deterministic refusal, no unapproved fallback, evidence of selected effective policy and effect-time state;
- safe migration, rollback and custody; no unsupported deletion of embedded rules;
- clear developer / Copilot / independent qualifier evidence separation;
- release readiness only when the integrated operational profile—not just a library—passes.

A family may be deferred when unsuitable, redundant, source-unsupported, non-migratable, or blocked by unresolved architecture. The coverage register must make this explicit. **100% of the supported approved profile must be qualified; 100% of the historic catalogue need not become registry records.**

## 8. Live status, scope and change control

The static v1.1 plan and S01–S06 histories remain untouched. v1.2 is a *successor* rather than an amendment-in-place; this plan's issuance does not retroactively authorize any work. Record its adoption, exact Git blob and initial baseline in a separate decision under `docs/decisions/` after operator review. Until then `docs/sprint-status.md` remains the sole live execution status.

Changes to the phase architecture, cross-domain authority division, supported profile, trust model, acceptance evidence or release criteria require an operator-approved v1.3 (or explicit bounded decision where no static-plan semantic change is made). No builder can mark a draft PR, static plan or Copilot recommendation as authority. Routine status, issue triage, source discoveries and risk notes go to the live status/decision log, never rewrite static v1.2.

**Initial authorized implementation phase: NONE.**  
**Initial next operator decision:** adopt or amend v1.2 and separately authorize R07 (bounded inventory/taxonomy/coverage adjudication), considering ongoing historical-recovery and schema-analysis drafts; avoid duplicating those workers' already completed work.  
**Release HOLD · Publication HOLD · Production HOLD.**
