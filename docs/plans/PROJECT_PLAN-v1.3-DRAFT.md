# OCS Registry — Static Project Plan v1.3 (DRAFT FOR OPERATOR ADOPTION)
Date: 2026-10-24
Status: **OPERATOR-APPROVED 2026-10-24; EFFECTIVE UPON MERGE.** Supersedes v1.2 when merged. Plan adoption does not authorize migrations, operational activation, release or production.

## 1. Objective and stopping rule
Build a **broad but finite, customer-scenario-supported, governed configuration registry** for OCS by externalizing *safe configurable policy values* while retaining the already implemented deterministic evaluators and code-owned mandatory guardrails. Avoid duplicating enforcement or creating a universal policy interpreter. A registry cannot issue OCS grants, substitute for the Control Plane, or authorize effects.

**Stopping rule:** the operator-approved V1 supported configuration profile must be externally governed through authenticated record/selection/activation, integrated at supported effect boundaries, with end-to-end independently qualified scenario coverage and explicit exclusions. Neither all historical statements nor all 15 repositories must be migrated. Completion of an OCS-only V1 profile does not require GCR implementation.

## 2. Authoritative source hierarchy and existing V0.2 reuse
- Existing Registry v1.2 plan: [PROJECT_PLAN-v1.2.md](PROJECT_PLAN-v1.2.md); [v1.2 crosswalk](PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md); frozen S03/S04 and merged R07/R08 evidence are preserved.
- OCS hub V0.2 [program README](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/program-v0.2/README.md), [S02 Registry R0 draft](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/program-v0.2/s02/contracts/1.3-registry-r0.md), [program register](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/program-v0.2/engineering-register.md), [declarative-registry direction](https://github.com/cogno-us/cognous-open-control-stack/blob/main/docs/declarative-governance-registry.md).
- [Qualification scenario catalog](https://github.com/cogno-us/cognous-stack-qualification/tree/main/scenarios), [Wiki-derived suite](https://github.com/cogno-us/cognous-stack-qualification/tree/main/suites/wiki-derived), [test inventory](https://github.com/cogno-us/cognous-stack-qualification/blob/main/docs/test-inventory.md).
- [Engineering Constitution pinned revision](https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md). Verify ADOPTION.md before claiming formal adoption.
- Cross-domain addendum COG-REG-SHARED-ADD-01 still requires original source custody; no normative digest or authority may be inferred.

**Do not perform a new broad cross-component contract design.** First produce a V0.2-to-current contract status ledger for each relevant clause: `ADOPTED_FROZEN`, `IMPLEMENTED_NOT_QUALIFIED`, `PROPOSED_ONLY`, `SUPERSEDED`, `CONFLICTING`, `UNVERIFIED`. Every row must include exact document/commit/decision and owner. Reuse or reference frozen clauses verbatim. Only `CONFLICTING` or truly missing clauses require targeted architectural adjudication.

The V0.2 R0 document describes three already designed partitions: (1) constitutional floor in code, (2) typed, versioned registry data, (3) registered deterministic evaluator code. It also proposes evaluator identity, exact content binding, epoch, activation and anti-rollback. **That R0 text labels itself a contract draft and its record layout conceptual**; treat as prior design, not blanket proof of adopted frozen wire formats. V0.2 implementation and qualification state must be checked separately at exact source revisions. V1.2's R08-S01 `r08-v1` is developer-tested foundation, not an operational selected contract.

## 3. Architecture constraints (reused, not reinvented)
1. **Code remains the enforcement owner.** Preserve mandatory admission rules, authorization/evidence separation, revocation checks, single-effect/atomicity invariants, input validation, negative-evidence integrity, lifecycle rules and refusal precedence.
2. **Registry stores governed parameters, not scripts, grants or executable interpretations.** Typed records and named, versioned evaluators; refuse unknown fields and families.
3. **Record, selection and consumer activation are distinct**. Selection provenance and authority must be authenticated under explicit trust; publication or newer epoch does not imply activation or authority. Activation is consumer-owned; no universal shared OCS/GCR ledger.
4. **Composition is typed and field-specific.** Sets may intersect; maxima may take a minimum where defined; other fields require explicit direction, coupling and destination capabilities. No generic 'strictest' algebra. Refuse unsupported composition, never silently widen.
5. **Required versus optional participation belongs to operation activation**. Required missing/invalid policy cannot revert to a wider caller policy; optional nonapplication is not denial. Keep deny-all distinct from refusal. LD-02 remains open for exact component reason mappings.
6. **Authority-to-effect consistency must be proven** for active paths, including in-flight revocation, expiry, trust change, record/evaluator change and retries. Existing `LocalExecutionPolicy.check` pre-claim placement is NOT a transaction-time guarantee.
7. **Evidence captures exact effective-policy identity and negative outcomes**, with source/evaluator/configuration pins, trust snapshot and decision provenance. Evidence traceability is not permission.
8. **No operational effect, key ceremony, credentialed cloud, paid test, publication or production** without separate operator authorization.

## 4. Scope selection: scenario first, implementation by enforcement owner
The already assigned Inventory Worker produces a read-only assessment in `cognous-stack-qualification`. Do not duplicate it. It must map unique scenario IDs, existing tests, observed qualification status, customer/security outcomes, actual enforcement owners, configurable inputs, registry dependency (required/beneficial/unnecessary/unknown) and exclusion impact. Known-limit tests are NOT PASS. Distinguish developer checks, synthetic qualification, independent verdicts and operational coverage.

Construct a canonical **configuration extraction manifest** by joining that assessment with S02/R07 evidence and exact current evaluator source:
- key, typed value, units/range/default, true origin (literal/constructor/file/profile), owning component, owner of authority, evaluator and source pin;
- scenario IDs and existing tests;
- code-owned guardrail/capability interaction;
- composition and absence/deny-all/refusal semantics;
- dependencies and changed-condition/race cases;
- extraction disposition `DIRECT`, `CONDITIONAL`, `CODE_GUARDRAIL`, `UNRESOLVED`;
- whether *central governance* is required for declared V1 customer capability;
- applicable evidence tier and qualification owner.
No count of inventory rows is a count of safe migratable fields. All 32 historical S02 unresolved classifications remain unresolved unless source-specific findings actually decide them.

**V1 profile freeze:** operator selects precise required fields and customer/security scenarios from the manifest. Candidate bundles for comparative analysis: (A) F1a+b; (B) A+F1c+F4+F5; (C) B+F6; (D) C+F1d. Evaluate F7 separately and F3/F8/F9/F10/F11 for critical surprises. These are comparison profiles, NOT approved migration scope. Exclusions must say what *customer capability* is unavailable, not merely what family is missing.

## 5. Component work allocation
Implement by **enforcement owner**, not by all 15 repos:
- **Execution Runtime**: local execution F1a/F1b, bounded quantitative F1c, target F1d only if semantics qualified; F6 agent permissions and relevant resource controls. Existing evaluator semantics and safety guards remain code.
- **Control Plane**: freshness F4, per-class authority F5, and any other proven configurable governed parameters; preserve grant, approval, identity, assurance and recovery machinery in code.
- **Other components**: participate when scenario evidence identifies an actual configurable policy or an evidence/distribution interface. ODES, Replay, Evidence Pack, Attestation, Governed Exchange, etc. do not become policy engines merely because they consume or prove policy identity.
- **Registry**: typed configuration records, validation/adapters, approval/selection/custody metadata and lifecycle contracts.
- **Qualification**: independent scenario and adversarial oracle; no transfer of builder tests into independent status.

Within an owner, extract *all approved safe fields* using one typed adapter and an incremental field manifest, instead of reopening architecture family by family. Different owner work can parallelize after shared contracts are reconciled; source-head and activation changes are serialized.

## 6. Finite phases and gates
| Phase | Task and output | Exit / gate |
|---|---|---|
| **P0 — V0.2 reconciliation** | Source-pinned adopted/proposed/implemented/qualified contract ledger; map to v1.2/R08; record genuine conflicts only. | Architect confirms reusability; no duplicated contract design. |
| **P1 — Scenario + extraction profile** | Consume Inventory Worker deliverable; construct full candidate extraction manifest and scenario/family/exclusion matrices. | Operator adopts exact V1 scope and supported scenario set; all candidate fields dispositioned, unknowns bounded. |
| **P2 — Shared governance foundation (R09)** | Reuse existing selected trust/verifier, record and selection authority, approval and revocation lifecycle, anti-rollback, recovery. | Security review and independent negative gate; operational trust not assumed from a hash. |
| **P3 — Typed component extraction** | Runtime and Control Plane adapter lanes under one frozen contract; retain evaluators and guardrails, preserve old/new differential behavior. | Per-owner safe field set passes source-pinned differential, refusal, boundary, interaction and regression tests; inactive by default. |
| **P4 — Cross-component activation/integration (R10/R12)** | Owner-specific selection/activation, expiry/revocation and effect-boundary revalidation, policy provenance, audit, distribution/recovery. | Integrated emulator tests demonstrate no widening, no false authority, and safe changed-condition behavior across declared routes. |
| **P5 — Cleanup (R13)** | Remove only proved redundant config loaders/embedded policy choices after qualified compatibility; retain rollback and mandated code guards. | Reachability and regression evidence; no unsupported consumer silently abandoned. |
| **P6 — Independent qualification and handover (R17/R18)** | Reuse central Wiki/V1/security-runtime/MVP test batteries, predeclare oracles and exact candidate pins, report gaps and negatives, security and restore acceptance. | Independent OCS-only V1 verdict and truthful release candidate; operator separately controls publication/production. |

R14–R16 GCR comparison and consumer work remain independent, optional *subsequent cross-domain profile* and never silently block OCS-only V1. If any previously proposed R07–R18 obligation is not named as a phase above, it remains linked in the traceability register and must be marked satisfied/deferred/not applicable with rationale—not silently deleted.

## 7. Testing and change control
- **Before extraction:** freeze existing test outcomes and the scenario-to-config crosswalk. Preserve test failures, skips, XFAIL and NOT RUN.
- **Per typed field/owner:** old-versus-new differential battery on actual evaluator, valid/invalid/boundary/empty/absence cases, cross-field checks, capability interaction, restore and changed-condition negatives. Do not move acceptance thresholds after seeing implementation results.
- **Cross-owner:** compare effective grants and policy at the effect commit, including revoked/expired selections, broken trust roots, altered record/evaluator, queued jobs, retries and stale caches.
- **Independent:** distinct oracle author/lead; distinguish behavior supported, unqualified and out of scope; test at exact source/profile pins, synthetic-only unless authorized.
- One PR per bounded owner increment, with no concurrent edits to canonical contract/activation files. One review cycle for material correctness; no editorial loop. No auto merge except separately authorized exact-head changes.
- A new issue is a V1 blocker only if it violates an approved scenario, mandatory security boundary or explicit gate. Otherwise mark `DEFERRED` with owner and impact. Scope changes require operator approval; never auto-add a family.

## 8. Decision rights — minimize operator escalation
The operator sets product/architectural direction; engineers and architects own technical implementation decisions. **Do not ask the operator to adjudicate field names, expiry constants, numeric ranges, mappings, source SHAs, interface details, key algorithms, or test plumbing.** Escalate only genuine strategic tradeoffs or changes to authorized boundaries.

**Operator decisions (only these, when needed):**
1. Adopt the final V1 customer/security capability profile, including meaningful inclusion/exclusion tradeoffs after the inventory report.
2. Approve any material architectural departure from the existing OCS/V0.2 authority separation, code-owned guardrails, or supported trust model; otherwise reuse what exists.
3. Authorize material new spending, production effects, publication/release or changes to held deployment scope.
4. Resolve a material cross-domain OCS/GCR responsibility choice, if the existing architectural division cannot decide it.

**Delegated to the OCS Architect and component owners:** V0.2 clause/status reconciliation, B-10 cryptographic adapter recommendation and explicit trust implementation specification, C-01 integration host identification, LD-02 failure mapping, LD-09 expiry and effect-time contract, A-05 duration limits, affected D1/D5/D6/D12 semantics, G-09 provenance retrieval, evaluator ownership, field schemas and versioning, compatibility plans, and technical PR review. Document source-backed decisions as ADRs; respect component boundaries. If a choice substantively changes approved security architecture, escalate *that specific tradeoff*, not the technical details.

**Independent qualification owner:** nominate and appoint a lead with genuine independence from the implementation, working within the pre-existing qualification governance. F-01 is a role-assignment coordination task; escalate only if an independent lead cannot be secured or qualification scope changes materially. The architect may not self-certify Tier 1 qualification.

**Execution authorization:** plan approval authorizes non-effecting inventory, P0 reconciliation, scope proposals and technical design within existing access. It does not blanket-authorize P2–P6 implementation, environment activation or merges. Builders submit bounded PRs; technical owners handle routine fixes. Seek an operator decision only where authorization or material architectural scope genuinely changes. Do not create an operator-decision queue from ordinary engineering tasks.

## 9. Immediate next step
Finish the existing scenario Inventory Worker; do **not** restart that audit. In parallel, **read-only** reconcile the V0.2 contracts into P0, not a 15-repo redesign. After worker results, a lead architect merges the scenario crosswalk and source-owned configuration manifest, recommends exact V1 extraction scope and requests a single operator freeze decision. Only then initiate P2/P3 authorized implementation.

## 10. Standing holds
R08-S01 PR #19 developer-accepted but verify current merge status separately. No approval or activation is inferred from that PR. Preserve frozen S03/S04 source. All release, publication and production holds stay in force. No GCR grant sharing, universal policy interpreter, broad 15-component refactor, or wholesale auto-activation.
