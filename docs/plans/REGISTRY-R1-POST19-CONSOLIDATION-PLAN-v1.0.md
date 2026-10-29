# R1 — Post-19 Registry Architectural Consolidation and Final Qualification: Static Engineering Plan v1.0

**Identifier:** COG-REG-R1-POST19/1.0  
**Status:** PROPOSED / STATIC PLAN ONLY; no implementation, refactor, release, merge or qualification authorized by this artifact.  
**Date:** 2026-10-29  
**Governance:** Engineering Constitution and ADOPTION.md at `cogno-us/cognous-engineering-constitution@1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`; Registry Static Migration Plan v1.1 §12; Engineering Plan v1.5; audit PR #60, consolidation #65/#67, architecture PR #68 and architecture v1.1 PR #72.

## 1. Objective, sequence and entry condition

**Purpose:** After the 19 audited Registry-manageable parameters are fully consumer-integrated, remove accidental duplication and fragmentation in the Registry and Control Plane while preserving externally observable behavior, constitutional enforcement, frozen contracts and existing approval/evidence semantics. Establish a reproducible **pre-refactor functional baseline**, perform bounded behavior-preserving consolidation, prove compatibility, freeze exact final engineering heads and conduct **one comprehensive final independent Tier 1 qualification campaign**.

**Mandatory order:** (1) 19/19 integrated → (2) functional baseline → (3) bounded refactor → (4) post-refactor equivalence → (5) engineering freeze → (6) full independent qualification → (7) separate release/security acceptance. No refactor may start before the 19/19 engineering gate unless the Architect separately authorizes a specific safety correction or dependency change. If any of the final three parameters cannot be integrated safely, keep R1 blocked; do not rename unresolved items as integrated merely to start R1. A documented exception requires an explicit Architect revision of this plan, rather than implicit deferral.

**Current recorded status at plan creation:** 16/19 integrated; three remain (FreshnessProfile.anchor_deadline_to_inputs; ObservationPolicy.max_age_seconds; ObservationPolicy.clock_tolerance_seconds); zero independently accepted. These are historical as-of facts, **not** an assertion about future main heads. D-06, D-07 and AR-1 are not presumed resolved.

## 2. Program boundaries

**In scope:** Registry `registry_successor/` version dispatch, canonical verification orchestration, record/selection/identity glue; shared typed family registration; cross-family effective policy composition; Control Plane governed workflow lifecycle, immutable EffectivePolicySnapshot integration, selection rechecks and policy digest plumbing; tests, fixtures, vector generators, documentation and evidence duplication. Only evidence-backed no-behavior-change refactoring is allowed.

**Out of scope:** New parameters, new authorization or trust roots, changed issuer authority, new administrator policy capabilities, dynamic interpreters, agent/task inheritance hierarchy, revised eligibility denominator, weakening a refusal, altered revocation/effect transitions, persisted schema or approval-preimage migrations, remediation of unrelated security findings, production rollout, and changes to held constructor clock tolerance. Durable activation is currently a separate design obligation, not something this refactor may claim to have implemented. Security defects found during R1 are documented and corrected in separately authorized PRs with independent assessment; they do not silently enter no-change refactor scope.

**Protected and frozen:** Historical `r08-v1`–`r08-v7` contracts **to the extent each is merged and explicitly frozen**, signature preimages/domains, accepted canonical JSON bytes, stable reason/denial vocabulary, frozen vectors, approval commitments, evidence custody, protected evaluator logic and externally observable operations. Do not modify historical frozen contracts in place. Preserve all incumbent APIs, or use tested compatible delegation behind those APIs where frozen-byte preservation permits. If a file is actually byte-frozen, leave the file byte-identical and consolidate only new shared internal code or future paths. Record any protected-source conflict as a stop condition.

## 3. Work-package ledger and ownership

| ID | Package | Deliverable | Gate |
|---|---|---|---|
| R0 | Verify 19/19 integration | Exact repository heads, 19-field consumer crosswalk, merged status and unresolved limitation ledger | Architect confirms entry |
| R1 | Baseline measurement and pin | Machine-readable inventories, baseline CI/regression evidence, hashes and complexity measurements | Baseline accepted; no refactor before |
| R2 | Registry verification consolidation | Shared mechanical parse/selection/verification/decision engine for *non-frozen* or compatible call paths; no new family behavior | Differential and cross-version checks |
| R3 | Registry composition/identity cleanup | One typed family registration interface and effective-policy digest plumbing; preserve joint target containment and closed semantics | Exact effective-state equivalence |
| R4 | Control Plane integration cleanup | Remove redundant wrapper logic, duplicated revalidation and divergent EffectivePolicySnapshot construction; preserve all mandatory four boundary checks | Approval/decision/effect equivalence |
| R5 | Test and evidence consolidation | Reuse shared fixtures, avoid duplicate test orchestration, retain raw failures and all frozen proof vectors | Coverage and mutation non-regression |
| R6 | Consolidation acceptance | Before/after metrics, exact-head differential report, full developer regressions, documented tradeoffs and unresolved risks | Architect review and merges |
| R7 | Engineering freeze | Pin cross-repo SHA manifest, dependencies, source-to-rule mapping, contract digests, evidence index, known failures | Architect approves freeze |
| R8 | One coordinated independent Tier 1 campaign | Security, adversarial, mutation, rollback, replay, cross-component and effect-boundary acceptance evidence | Independent reviewer decision |
| R9 | Closeout | Accepted/failed/blocked dispositions, documentation and release recommendation | Publication/release/production remain separate HOLD gates |

Plan packages are not per-parameter PRs. Use short-lived parallel workers with nonoverlapping file ownership; one lead builder coordinates integration and submits one consolidated Architect review per bounded consolidation batch. Routine CI failures are repaired within their package. PRs are separate where repository ownership or rollback boundaries demand it.

## 4. R1 — Baseline and metrics (required before refactor)

At exact pinned Registry, Control Plane and Runtime main SHAs (plus all other affected OCS component heads), capture:

1. Production source LOC by package and contract version; common versus version-specific LOC; number of distinct verifier/selection/decision implementations.
2. Duplicate normalized code blocks, especially `v3`–`v7` verify/selection/record/decision orchestration; do not infer safe consolidation from text similarity alone.
3. Number of policy-composition and workflow lifecycle paths, identity/commitment derivation sites, signed selection resolution paths, effect-boundary checks and activation paths.
4. Existing wall-clock test execution times, CI matrix, total tests and skipped tests, mutation numerator/denominator, uncovered branches and tests with known environmental failures.
5. Full externally visible outputs: canonical signed/parsed record formats, effective-policy digests, representative decisions, refusal reasons and ordering, approvals, persisted decision bindings, recovery, replay and revoked/withdrawn selections.
6. Immutable manifest of relevant source and vector hashes; baseline failures and environment reproduction instructions. No silent baseline update to suppress a discrepancy.

Report pre-refactor metrics without promising a numerical reduction before measurement.

## 5. R2/R3 — Registry refactoring invariants

- Prefer shared *mechanical* machinery: canonical parsing, field validation dispatch, verification layers, selection state processing, cryptographic adapter invocation, evidence bookkeeping and stable decision orchestration.
- Keep typed per-family domain validators, normalization, mathematical narrowing relations and cross-field invariants explicit; do not replace them with a programmable policy interpreter.
- Preserve domain-separated signatures and effective-policy identity by contract version and family. A v6 signature must never validate a v7 selection, for example.
- Preserve original host validity check and final composed-policy check; missing or revoked required family refuses; original host policy cannot be repaired by a Registry overlay.
- Retain complete compatibility for already signed material. Never require a silent bulk re-sign or re-issue of historical approvals.
- Maintain each frozen reader/writer and public entry point. Where frozen-byte constraints prevent safe deduplication, document residual duplication and do not force a rewrite.

## 6. R4 — Control Plane and Runtime refactoring invariants

- Preserve typed immutable effective-policy construction and original host authority; do not introduce unbound mutable Registry reads into evaluators.
- Preserve **all mandatory checks** at construction, decision entry, execute entry and nearest supported pre-dispatch gate.
- Preserve profile-bearing approval_commitment, persisted catalogue_digest and any explicitly adopted binding for F4/ObservationPolicy. Never change approval preimages or persisted schema under a refactor-only PR.
- Preserve revocation, withdrawal, terminal negative records, recovery and retry behavior. A host with no ObservationPolicy must remain on hold.
- Preserve cached-purpose, purpose-observation, deadline, extension and clock behavior at the post-19 established baseline, including any separately approved corrections; refactor must not silently reopen the approximately 2x dispatch gap.
- Preserve action irreversibility and holder inventory evidence semantics; requirement does not equal evidence.
- Maintain explicit host-owned activation responsibilities. Advisory local activation must not be represented as durable cross-process exclusivity.

## 7. R5/R6 — Equivalence and acceptance

Each consolidation PR must retain baseline and changed outputs at pinned dependencies. Required oracles include:

- Frozen bytes and signature/input-domain round trips across all contract versions.
- Exact signed record and selection parsing, dispatch and refusal behavior.
- Cross-family composition, including two-field target-scope containment.
- Non-widening, invalid original host, and missing mandatory-family refusals.
- Approvals, persisted bindings, recovery and replay equivalence across restarts.
- Selection revocation/withdrawal at decision and effect boundaries; concurrent source changes.
- Observation freshness, future clocks, deadline anchoring, residual-window regression and irreversibility.
- Failed effects, no-action-after-refusal, negative evidence and adapter boundary behavior.
- CI matrix parity, deterministic reproducibility, mutation regression and no hidden skip increases.

**Pass standard:** no newly widened authorized execution paths; no changed commitments, proofs, signed bytes, refusal semantics or replay outcomes. If a test differs, classify as environment, previously documented limitation, real regression or newly discovered bug with retained evidence. Do not normalize away changed behavior to make a refactor pass. For any desired behavior correction, split into separately authorized and qualified change. A reduction in LOC is not itself success.

## 8. R7 — Freeze package

Produce a single GitHub-native freeze index in the qualification hub, with references from Registry and component repositories: exact head SHA per repository, cross-repo dependency manifest, source/contract/vector checksums, 19-field and authority-binding crosswalk, test/mutation evidence, open vulnerability/security/IP issues, negative evidence, known limitations and reproducible runner instructions. Protect the frozen candidate from unreviewed changes. Every later code alteration creates a new candidate requiring targeted revalidation and a revised independent-qualification scope.

## 9. R8 — One full independent qualification campaign

After freeze, execute one coordinated qualification program spanning all 19 effective parameters and every applicable OCS enforcement boundary. Independent reviewers must inspect pinned source and evidence and run appropriate independent tests. Include authorization provenance, source trust, signed selection monotonicity, replay/rollback, revocation, multi-family atomicity, approval/decision/effect binding, long-running and concurrent workflows, restart recovery, observation and deadline tests, boundary failures, mutation/adversarial tests, security reachability and historical known failure reproduction. Record blocks, skips, rejected claims and all original failures. Do not turn ordinary developer CI into independent acceptance.

Independent Tier 1 qualification remains **DEFERRED, NOT WAIVED**, until this phase. V09 is separate. Ed25519 #26/#34 SECURITY-HELD. Release, publication and production remain **HOLD** until their distinct acceptance gates.

## 10. Measurable exit criteria

- 19/19 integrated or explicit Architect revision to this plan; zero unacknowledged parameter exclusions.
- Baseline and post-refactor structural metrics, reproducible at source pins; documented improvement where viable without sacrificing isolation.
- No unexplained behavior changes, widened authority, loss of proof, approval incompatibility, or increased unqualified skips.
- All cross-repository developer checks pass or preserve a separately documented, source-proven inherited failure with accepted disposition; all security-relevant differential tests pass.
- Frozen contract bytes, canonical signing inputs, reason behavior and evidence compatibility verified.
- Complete GitHub-native SHA/evidence freeze index and independently produced qualification report.
- Explicit disposition of any unmet requirements; no assertion of Tier 1 acceptance from a builder-only pass.

## 11. Stop, escalation and merge discipline

**Stop and request an Architect decision** if refactoring requires changing a protected evaluator, frozen schema/vector, canonical signature/identity, approval commitment, persisted decision, refusal ordering, transaction/revocation semantics, trust root or host authority; if a source-backed counterexample shows widening; or if 19/19 cannot be reached safely. Routine failing CI, obvious code defects and documentation corrections may be repaired autonomously. No automatic merges; exact-head CI and Architect merge authorization required. Use project plan, PRs, decision records and status files for continuity, not a long-lived chat session.

**This static plan is intended to be adopted before R1 begins, but executing R1 remains gated on completed 19-parameter integration and an Architect authorization.**
