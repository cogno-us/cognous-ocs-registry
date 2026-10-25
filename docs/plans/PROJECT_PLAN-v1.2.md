# OCS Registry — Static Engineering Program v1.2

**Plan ID:** OCS-REG-PLAN v1.2  
**Issued:** 2026-10-24 (operator-directed successor planning; repository recording may be later)  
**Status:** PROPOSED FOR OPERATOR ADOPTION; **no implementation sprint authorized by creation or merge of this plan**  
**Program owner/authority:** Cognous operator. **Plan custodian:** OCS Architect. **Execution:** delegated engineering builders with bounded sprint authority.  
**Repository:** `cogno-us/cognous-ocs-registry`. **Cross-domain architectural role:** Governed Cognition Runtime (**GCR**), a replaceable, independently governed cognitive subsystem. The present implementation and review evidence are ISS V6 in `cogno-us/cognous-iss-core`; the OCS contract must not depend on that implementation.  
**Constitution reference:** `cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; reference is not itself proof of formal adoption.  
**Predecessor:** [PROJECT_PLAN-v1.1.md](PROJECT_PLAN-v1.1.md), frozen blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`.  
**Release / publication / production:** HOLD until distinct operator acceptance; plan adoption is not deployment approval.

## 1. Mission and definition of complete

Build a **fully functioning, governed, versioned rule registry** for the selected OCS policy families and a **GCR-compatible, cross-domain registry architecture**, with authenticated selection, deterministic validation, consumer integration, governed activation, negative/changed-condition coverage, independent qualification and operational custody. The end state must be demonstrated in supported execution paths, not merely in stand-alone parsers or synthetic overlay tests.

**Fully working** means all of the following are established for the explicitly declared supported profile:

1. Authorized administrators can create, validate, approve, publish within an approved environment, select, supersede, revoke and audit typed registry records using a documented, recoverable, least-privilege workflow.
2. The registered OCS consumers use an authenticated, approved and version-pinned selection, apply only applicable records, enforce fixed code-owned mandatory invariants, and refuse missing, tampered, invalid, expired, revoked, unsupported, stale or incompatible policy as required by the operation's defined governance profile.
3. No registry record can issue its own authority, create an action grant, broaden an existing permission, bypass effect-time checks, defeat revocation or turn failed custody into permit.
4. The supported integrated OCS admission-to-effect path, including Control Plane/Runtime and evidence/decision boundaries, has reproducible positive, negative, concurrent and changed-condition evidence.
5. A compatible **GCR implementation** supports independently adopted shared logical envelope conventions through a separately approved and qualified GCR-side interface. GCR exclusively owns cognitive admission, canonical cognitive state, source/memory custody, evidence, reliance and permissible outputs; OCS exclusively owns external execution and effect-time authority. Each domain authorizes its own selection and activation and independently evaluates its boundary. Cross-domain compatibility and negative isolation must be tested; matching record identity never transfers decision authority.
6. A versioned, source-backed **coverage register** identifies implemented, qualified, deferred, non-migratable, unresolved and unsupported policy families. The migration goal is all **approved, applicable, configurable families in the adopted operational profile**, not indiscriminate ingestion of 3,190 historical source statements.
7. Independent risk-proportionate qualification, security and supply-chain review, operational recovery/rollback exercises, documentation and an explicit release decision complete the program.

**Not required to claim bounded operational completion:** migrating mandatory constitutional/invariant logic out of code; implementing every historical reason code, validator, test scenario, draft requirement or unknown V0.1 entry as a policy. Any such claim would be false.

## 2. Evidence and frozen baselines

- S01–S06 under v1.1 are **DEVELOPMENT PROGRAM COMPLETE — BOUNDED**, not operationally qualified. S06 closeout merge `1870f3a62ee16cdea53c4c23a8df8c9be3c2f2cf`; S06 tests reported 373 pass, 0 pytest fail, 0 pytest skip, with **three distinct E05 behavioral SKIPs in frozen raw evidence**.
- Preserve unchanged the original baseline, S03 validator and contract, S04 optional-overlay consumer, S05 oracle/expectations/raw evidence, historical reports, static v1.1 plan and their exact pins. A successor implementation is additive/versioned until a separately authorized deprecation and independently verified equivalence.
- S02 is a bounded source-code inventory: 620 construct rows, 43 configurable candidates and 32 unresolved classifications. The historic `catalogue-v0.1` contains 3,190 **source-statement entries**, predominantly vocabulary/requirements, with no native configurable-policy record type; no distinct OCS V0.2 release inventory has been established. Historical recovery draft PR #13 is a research input, **not yet an adopted authoritative inventory**. Re-verify its latest review head and merge state before use.
- Current S03 represents only three nonempty allow-lists: `allowed_units`, `allowed_adapters`, `allowed_actions`; it is deliberately stricter than the historical constructor. S04 refusal leaves caller policy in force because the overlay is optional. Digest checks are **integrity, not authentication**. Installed file hashes do not authenticate running Python code. No operational manifest pin has been approved. These are required design inputs, not defects silently declared solved.
- The supplied 7-page `COG-REG-SHARED-ADD-01` (2026-10-24) is accepted-in-principle architectural direction, not an implemented contract or approval to change either domain. It defines shared outer conventions with separate domain authority and warns against cross-domain proof transfer. Source revision/digest custody for the addendum remains a separate adoption requirement. The GCR/ISS review is documented in `cogno-us/cognous-iss-core` PR #12 at `547b9052805b7e57ee44ae15f064725b97823405`; its findings are design inputs, not evidence of qualified integration.
- All source, test and decision references must carry immutable revisions. Newly discovered evidence may change a decision record or necessitate v1.3, but **not this frozen static plan's text**.

## 3. Architecture contract and non-negotiable invariants

### 3.1 Three separate objects

**Record:** typed, authenticated-origin configuration/evidence-reference data with stable identity, family, contract/record versions, canonicalization, provenance, applicability, evaluator identity/revision, content digest and supersession lineage. Its lifecycle distinguishes draft, validation, approval, publication, supersession and archival. A valid or published record has no self-authorizing effect. An immutable history must survive supersession.

**Selection:** a separate domain-owner-approved and authenticated selection identity, revision/epoch and exact record/version/digest/evaluator pins, governing context, tenant/scope, effective interval and withdrawal/revocation reference. Selection approval, publication, withdrawal and revocation are independent of record status. Never select `latest` implicitly, or infer approval from record status, a digest, PR merge or repository presence.

**Activation:** the domain consumer's distinct, context-specific determination that an independently authorized selection may govern an operation, bound to selection identity/epoch, record and evaluator digests and operation/decision/evidence references. Activation, evaluation, commit and revalidation are domain-owned transitions, not global registry status. An approved selection is neither an OCS execution grant nor GCR cognitive admission.

### 3.2 Typed semantics, not universal code-as-data

- Use a small shared **envelope and selection-reference discipline** with explicit family-specific schema, deterministic evaluator and separately versioned compatibility contracts.
- For comparable allowed sets, use intersection. For numeric maxima/minima, use correct typed monotonic composition with domain-specific precision, units and floors. For evidence and status requirements, use explicitly defined typed combination; if no sound operator exists, **refuse unsupported composition**. Never invent one universal rule algebra.
- Define explicit **deny-all** or unambiguous empty-set semantics in a new version when required; a refused empty record that leaves caller policy active is *not* denial. Define optional versus required participation per operation and prohibit permissive fallback for required participation.
- Keep fixed enforcement, grant, approval, revocation, effect-time rechecks, negative evidence, tenant isolation, safe serialization, bounded resource checks and applicable constitutional floors in component-owned code.
- Preserve closed refusal/reason-code vocabularies through separately versioned compatibility processes; catalogue inclusion is not authority to rewrite them.
- No registry-provided scripts, expressions, dynamic imports or arbitrary evaluators. A family binds to a vetted registered code evaluator with source/build identity.
- Loaded-runtime integrity and deployment custody must be addressed for the adopted threat model; hashing a file on disk is insufficient evidence of loaded-code integrity.
- Separate OCS external effects from GCR cognition; no second decision authority, universal policy engine or competing canonical state/ledger. Each domain exclusively owns its admission and commit boundary. The shared registry is a logical contract discipline, not a required shared service/database.

### 3.3 Atomic effective-policy binding and non-forgetting

Every governed operation must bind **one authorized effective-policy identity**: selection ID/epoch, exact applicable record/version/digests, registered evaluator revision/build identity, scope/context, evaluation time, admission result and the canonical transaction or effect/evidence commitment. A matching record digest alone does not establish authority, freshness or atomicity. The consumer must define a commit-boundary revalidation protocol for concurrent selection changes, withdrawal/revocation, expiry, stale caches, authority/evidence invalidation, conflicting state changes, failed commits, restoration and replay. On changed conditions, required profiles HOLD/REFUSE or restart through a separately evaluated transaction under the owning domain; no silent hot-swap or fallback. OCS independently rechecks at the actual authority-to-effect boundary. GCR independently rechecks applicable cognitive authority, policy and evidence before its canonical transaction and evaluates current reliance/output eligibility at the relevant boundary. Historical decisions and record references remain inspectable; replay never reactivates withdrawn authority.

**Source preservation and non-forgetting:** retained original cognitive source material, attribution, provenance and historical record revisions cannot be erased, overwritten or silently reinterpreted by ordinary registry supersession, invalidation, compression or selection withdrawal. Invalidated evidence may lose reliance eligibility without disappearing from historical custody. Mandatory source preservation, negative-record continuity, canonical-StateDelta controls and safe refusal remain GCR-owned invariant code. Authorized erasure and legally required retention/disposal are separate, explicitly governed lifecycle decisions and must not be inferred from compression settings or an ordinary registry record. Do not claim atomic negative-record custody or full output-envelope enforcement before independent qualification.

### 3.4 Minimum operational profile and completion

Before operational-complete claims, the operator must approve a **Minimum Supported Operational Profile (MSOP)** identifying exact OCS rule families, evaluator/build pins, named Control Plane/Runtime consumers, mandatory/optional participation per operation, authenticated selection/custody mechanism, activation/effect-time path, supported tenant/institution scope, adverse-condition handling, evidence/qualification gates, operational environment and excluded capabilities. Minimum candidate coverage is the existing three-field F1 allow-list profile plus an approved selection/activation path in real OCS consumers; extensions to institutions/domains, permissions, freshness and authority profiles are individually justified and independently authorized. This is a **candidate**, not a preapproved minimum: R07/R08 must establish whether a narrower or broader profile truly exercises required registry functions. No component count or passing synthetic-only suite can substitute for end-to-end evidence. OCS-only MSOP completion is distinguishable from the later GCR-compatible cross-domain profile. Do not claim cross-domain completion before an actual independently qualified GCR consumer and R16 isolation evidence.

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

**R07–R08 are information/architecture gates; R09–R13 deliver OCS registry functionality; R14–R16 establish GCR compatibility through separate ownership; R17–R18 qualify and close out.** Phase numbers are program increments, not automatic sprint authorizations. The historical v1.1 S01–S06 IDs are unchanged; proposed v1.2 work uses **R07–R18** to avoid retrospectively renaming history.

### R07 — Source inventory and authoritative migration register
**Dependencies:** v1.1 closeout; recovery PR #13 provenance reconciliation.  
**Tasks:** resolve historical V0.1/V0.2 naming; incorporate source-pinned S02 and recovery crosswalk without importing 3,190 entries; classify each current candidate as parameter, mandatory invariant, reason vocabulary, non-policy, deferred or unresolved; trace real source evaluator/consumer; rule on critical W8-091, W3-063, W9-027, W8-014, W6-042 and 60-versus-300 *before any affected family is migrated*. Scope bounded to a named baseline set; inventory incompleteness visible.  
**Exit:** signed-off taxonomy, prioritized family/owner matrix, provenance and denominator report, unresolved decision queue, family-specific acceptance cases; no source semantic change. **Gate:** operator adopts candidate migration profile.

### R08 — Versioned contract and preliminary GCR architectural review
**Dependencies:** R07.  
**Tasks:** propose successor schema distinct from frozen S03; minimal shared record envelope, explicit typed payloads, evaluator registry, applicability, selection pin, supersession, status, effective time, refusal semantics, explicit deny-all, compatibility and profile capability discovery. Compare proposed outer conventions against the GCR architectural role with an independent GCR architect (using ISS V6 source as the current concrete reference, not a required dependency). Record shared versus rejected conventions and the independent ownership of selection and activation. This preliminary **read-only** review is not R14 readiness certification and does not depend on completion of ISS Core S05.  
**Exit:** versioned schemas, formal invariants, negative examples, migration/rollback and compatibility plan, GCR Architect preliminary disposition, proposed cross-domain interface contract; no implementation. **Gate:** operator approves contract version and scope; no implicit adoption of GCR policy semantics.

### R09 — Authentication, independent lifecycles, selection and custody
**Dependencies:** R08.  
**Tasks:** implement three explicit and independently auditable lifecycles: (1) record validation/approval/publication/supersession/archival; (2) domain-owned selection approval/revision/withdrawal/revocation; (3) domain-consumer activation/evaluation/commit. Implement access control, immutable approved selection manifests/pins/epochs, trusted activation configuration, authorization changes, anti-rollback/version rules, selection revocation and key/identity management or equivalent approved custody, recovery and reconciliation. Separate record approval from effect authority. Implement no automatic `latest` activation.  
**Exit:** negative tests for forged/altered/replayed/cross-tenant/expired/superseded/revoked selection, source substitution, stale cache, missing custody and rollback; documented operator workflow and external anchoring where needed. **Gate:** independent security review of authority-bearing paths before activation.

### R10 — OCS integration: mandatory/optional admission and effect-time boundary
**Dependencies:** R09.  
**Tasks:** wire registry selection to actual supported OCS Control Plane and Runtime paths; define exact ownership and consistency at authority-to-effect, including in-flight revocation, withdrawal, evidence invalidation and version changes. For required policy, missing/refused registry is HOLD/DENY as semantics dictate; optional profile explicitly remains optional and is never misrepresented as mandatory denial. Bound caching; implement domain-specific revalidation of selection epoch and effective record/evaluator identity at the effect boundary, and bind that identity to admission, atomic effect and evidence without claiming global atomicity.  
**Exit:** live component integration tests in safe emulator, exact record/manifest/evaluator identities in decision/evidence; no unauthorized widening and no split-brain policy. **Gate:** an effecting production path remains inactive until qualification.

### R11 — Policy family migrations, bounded and typed
**Dependencies:** R08–R10 for active integration; R07 family approval.  
**Tasks:** R11 is a **migration umbrella, not a single unlimited sprint authorization**. Migrate each approved configurable family in a **separately operator-authorized, bounded PR/lane with its own exact source profile, decision and qualification gate**. Default candidate order for architectural assessment: remaining F1 set fields (institutions, authority domains), F6 agent permissions, then F1 numeric ceilings/target prefixes with distinct operators, F4 freshness, F5 authority profiles, and justified F7/F3/F9/F10/F11 where operational value warrants. Not every listed family is automatically in the adopted MVP. For each: upstream pin, authority tier, registered evaluator, schema, refusal/widening proof, independent expected-outcome oracle, differential and changed-condition battery, and legacy cleanup only after qualified cutover.  
**Exit:** approved-family coverage matrix with named qualifier/owner and independently supported result for each active family, zero unexamined transitions; non-migratable invariants still in code. A deferred or blocked family must not be reported as migrated. **Gate:** each Tier 1 family separately independently qualified before activation.

### R12 — Cross-component policy distribution and auditability
**Dependencies:** R09–R11 selected profile.  
**Tasks:** secure record publication/discovery, tenant and institution scoping, source/manifest/evaluator pin distribution, deterministic cache invalidation, observability, audit evidence, denial reasons and operational dashboards or CLI. Reuse OCS existing Evidence/ODES and verification mechanisms; avoid unnecessary new database/service.  
**Exit:** reproducible end-to-end policy create→approve→select→apply→observe→revoke cycle and recoverable audit trail, including unavailable stores and stale subscribers.

### R13 — OCS cleanup and legacy configuration retirement
**Dependencies:** qualified R11 migrations and working R12 profile.  
**Tasks:** identify only provably redundant embedded *policy choices* and obsolete configuration loaders, not code-owned safety invariants. Preserve historical versions and rollback adapters until cutover gate. Separate per-component PRs; verify no hidden active consumer or permissive fallback remains.  
**Exit:** retired-path reachability report, matching behavior after removal and component regression evidence. **Gate:** no forced deletion of old code while unsupported consumers remain.

### R14 — GCR read-only crosswalk and owner-approved interface
**Dependencies:** R08 proposed common envelope; availability of an actual GCR implementation/source baseline for a read-only crosswalk and GCR owner's architectural review. R14 does not imply GCR implementation readiness.  
**Tasks:** examine the GCR implementation's actual canonical state/transition, cognitive admission, evidence/reliance and source-preserving memory contracts (currently ISS V6 where applicable). Map only envelope, manifest identity, provenance, version and reference semantics across OCS/ISS. Identify incompatible types and preserve independent authority; no GCR execution changes in this phase.  
**Exit:** joint versioned compatibility crosswalk, named OCS/GCR owners, negative isolation matrix and explicit GCR interface-readiness disposition (not an implementation approval).

### R15 — GCR local registry consumer and compatibility qualification
**Dependencies:** R14; independently established GCR implementation readiness and separate operator/domain-owner authorization (for ISS V6, its own ISS Core and ISSBench gates must be honored).  
**Tasks:** implement a minimal GCR-side **read-only, pinned** consumer for separately approved GCR families using the agreed envelope; GCR-owned evaluator and canonical state authority remain exclusive. For ISS V6, follow existing Governor/StateDelta contracts rather than duplicating them. Validate missing/untrusted/stale/withdrawn selection, profile mismatch and forbidden OCS-effect authority transfer.  
**Exit:** GCR-owner-accepted independently qualified local profile, frozen crosswalk evidence and source pins; no OCS-effect grant from GCR registry selection. Where the implementation is ISS V6, use existing ISSBench V2 as the independent qualification facility; do not create a duplicate harness. **Gate:** GCR owner accepts local profile.

### R16 — Cross-domain compatibility and end-to-end governance
**Dependencies:** R10–R12, R15.  
**Tasks:** cross-system manifest compatibility, provenance and schema/version negotiation; test OCS and GCR as independent consumers of common envelope conventions, including revocation propagation, stale decisions, negative records, inconsistent versions, outage recovery, and a matched policy identity that confers **no** transferable decision authorization. Do **not** require a single physical store or global authority ledger unless separately justified and authorized.  
**Exit:** independent OCS and GCR outcomes, compatibility report, no authority transfer and no hidden shared interpreter; cross-system HOLD on unsupported combinations.

### R17 — Independent security, qualification and operations acceptance
**Dependencies:** completed supported OCS operational profile and GCR compatibility for the cross-domain release profile; OCS-only qualification may proceed separately without waiting for unrelated GCR implementation.  
**Tasks:** adversarial source/selection/loaded-code custody checks, changed-condition races, isolation, policy confusion, fuzz/invalid data, resource exhaustion, backups/restore, key compromise/rotation, rollout/rollback, SBOM/licenses, supply-chain and distribution controls. Freeze candidate source and manifest digests **at qualification boundary**, not at every exploratory sprint. Run independent exact-head component and integration batteries against intended deployment environment.  
**Exit:** signed independent qualification verdict with negative evidence and residual-risk ownership, truthful supported-profile matrix, reproducible package/restore, operational runbooks and incident drills. Defects BLOCK acceptance; ordinary developer/Copilot PASS is insufficient.

### R18 — Release candidate, handover and production authorization
**Dependencies:** R17 PASS and each affected owner sign-off.  
**Tasks:** finalize release manifests, distribution exclusions, change logs, operator/admin documentation, migration and rollback guides, environment-specific trust configuration and release checklist; obtain separate operator release, publication and production decisions as applicable.  
**Exit:** working operational registry for the declared supported OCS profile and independently qualified GCR compatibility if that cross-domain profile is part of the release; all deferred families explicitly tracked. No public release, production activation or claim of full historic-rule coverage by default.

## 6. Program gates and evidence ownership

| Gate | Minimum evidence | Decision owner |
|---|---|---|
| G0 Program adoption | v1.2 approved, scope and exclusions recorded | Operator |
| G1 Inventory and architecture | R07 taxonomy, R08 typed schema and preliminary GCR architectural review | OCS Architect + operator; GCR Architect for the GCR-facing contract |
| G2 Authority custody | R09 authenticated selection, adversarial negatives and security disposition | OCS authority owner + independent reviewer |
| G3 OCS active integration | R10 admission/effect-time tests with approved pins in safe environment | OCS Runtime/Control Plane owners + operator |
| G4 Family cutover | Per-family differential, refusal and independent Tier 1 sign-off | Domain owner + independent qualifier |
| G5 GCR compatibility | R14–R16 independently accepted contracts and isolation | GCR Architect/domain owner + OCS owner |
| G6 Operational qualification | R17 exact-head independent OCS and (when in profile) GCR qualification, security, recovery and package evidence; ISSBench V2 for ISS V6 candidates, existing OCS qualification infrastructure for OCS | Independent qualification owner + operator |
| G7 Release | R18 signed artifact, distribution, production/environment decisions | Operator; each affected system owner |

A gate may be BLOCKED, DEFERRED or NOT APPLICABLE only with explicit durable rationale and owner; never silently omitted. External GCR readiness may run concurrently under its own authorization, without blocking independent OCS-only work. No cross-domain operation is declared complete if a GCR consumer remains theoretical.

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

**Initial authorized implementation phase: NONE.** The revision of this draft plan, acceptance of the GCR architectural name, and architectural review do not authorize R07 or any component modifications.  
**Initial next operator decision:** adopt or amend v1.2 and separately authorize R07 (bounded inventory/taxonomy/coverage adjudication), considering ongoing historical-recovery and schema-analysis drafts; avoid duplicating those workers' already completed work.  
**Release HOLD · Publication HOLD · Production HOLD.**

## 9. Cross-domain architectural review dispositions (A1–A10)

This draft incorporates the ISS/GCR review at `cogno-us/cognous-iss-core` PR #12 head `547b9052805b7e57ee44ae15f064725b97823405` and the supplied `COG-REG-SHARED-ADD-01` design addendum. The ISS review is independent technical architectural analysis, not implementation, a merged ISS plan, or qualification. Specific dispositions and source-to-change mapping are recorded in `docs/plans/PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md` in this planning PR. A1–A10 are accepted with clarifications of source-preservation versus authorized erasure, GCR-independent OCS readiness, and the distinction between a candidate and an approved minimum operational profile.
