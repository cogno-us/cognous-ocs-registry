# Architectural consolidation assessment (READ-ONLY), 2026-10-28

Status: **DOCUMENTATION ONLY. Non-authorizing. No production code is changed by this PR. Recommendations are NOT implementation authorization.** Builder assessment; not independently reviewed. Independent Tier 1 qualification is deferred (not waived) to the final integrated engineering freeze. V09 assurance separate. Ed25519 #26/#34 SECURITY-HELD. Release, Publication, Production HOLD.

## 0. Mandatory references and exact pins
- Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ENGINEERING_CONSTITUTION.md`, `ADOPTION.md` at the same revision). Static Migration Plan v1.1 (`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`). Engineering Plan v1.5 (`docs/plans/PROJECT_PLAN-v1.5.md`). Adopted inventory: Registry PR #60, merge `6516446a4e551e50f2bb47c1d57fbf8ace27d7c5`.
- Component heads assessed: Registry main `47adfc8f0a07ec488030fe8d83fde6d84a1cd51c` (docs PR #63); Control Plane main `5f11e0f9b10d05cf6970aac0e8023ecbdd448c42` (PR #89); Runtime main `f7a55e2a8494801e49193f9f46935f0a971c248d` (module facts read from a local checkout at `e8323f1d7`, the M3 re-pin; the `registry_f1*_narrowing.py` files are the ones read).
- Open, unmerged, assessed as proposals only: Registry PR #64 head `6c3e5e4037d34bd2b31371461bfc872c762026b9` (r08-v5 `on_unreadable`); Control Plane PR #90 head `e5426dd943106b422d1c5dfcee0ba22e64a47c11` (`GovernedClassUnreadableWorkflow`, consumes r08-v5). Held, NOT modified: Registry #58, #59; Control Plane #87.
- Method: source reading, line counts and normalized diffs on the exact heads above; no production file was edited, no test was added by this document. Where a statement rests on the audit catalogue instead of re-reading source, it says so.

## 1. Executive summary
1. **No active authority-widening defect was found.** Every overlay in the cumulative architecture is individually monotone, and the one joint case that exists (class status age + `on_unreadable`) binds a single effective profile. No stop condition of the directive was met.
2. The architecture is **coherent but linearly expensive**: every parameter has cost one new Registry contract slot (or family) plus one Control Plane workflow subclass of roughly 260-380 lines, and the cost of the next parameters is about to become **multiplicative** (combinations) for class-field overlays unless the lifecycle skeleton and the composition step are made shared (finding P1-1).
3. The real gaps are **coverage and composition** gaps, not widening gaps: F4 and F5 cannot govern the same action today (P1-2), there is no technical guard against a host running two independent governed workflows for one action (P1-3), and the Registry contract copy-per-version pattern has reached the point where three `*_verify/_selection/_record` triples are identical modulo version names (P2-1).
4. Nothing here requires touching a protected evaluator. Every recommendation below is optional engineering; none is authorized.

## 2. ASSESSMENT A: contract proliferation
### 2.1 Inventory (Registry main `47adfc8` plus PR #64 as proposal)
| Contract | Families (payload) | Source modules | Signing domain | Policy identity | Status |
|---|---|---|---|---|---|
| r08-v1 | baseline | `selection.py`, `record.py`, `verify.py`, `compose.py`, `families.py` | v1 domain | n/a | frozen |
| r08-v2 | f1ab allow-sets; f4 `status_max_age_seconds`+`approval_max_age_seconds`; f5 `class_status_max_age_seconds` | `v2_selection.py`, `v2_f1ab.py`, `v2_age_bounds.py`, `v2_token*.py`, `v2_policy_identity.py` (1472 lines), `v2_codes.py`; dispatch in `decision.py`/`verify.py` | `ocs-reg/r08-v2/...` | one module, per-family branches | frozen (amended 1-4) |
| r08-v3 | f1abc `max_amount`, `max_effects` | `v3_*` (7 modules) | v3 domain | `v3_policy_identity.py` | frozen/merged |
| r08-v4 | f1abcd (adds `allowed_target_prefixes`, `target_match`) | `v4_*` (7 modules) | v4 domain | `v4_policy_identity.py` | frozen/merged |
| r08-v5 (proposal, PR #64) | f5 `class_on_unreadable` | `v5_*` (7 modules) | `ocs-reg/r08-v5/selection` | `v5_policy_identity.py` | OPEN |
| r08-v5 (proposal, PR #58) | f4t constructor clock tolerance | same file names | same contract id | | HELD, COLLIDES (see 2.4) |

Consumers: Runtime `engine/registry_f1a_narrowing.py` (129 lines), `registry_f1abc_narrowing.py` (118), `registry_f1abcd_narrowing.py` (121), plus `registry_selection_authority.py` (1871); Control Plane `registry_f4_age_governance.py` (260), `registry_f5_class_age_governance.py` (286), PR `registry_f5_class_unreadable_governance.py` (378).

### 2.2 Measured duplication (normalized diff, version tokens replaced)
- `v3_verify.py` vs `v4_verify.py`: **0** differing lines (244 lines each). `v4_verify.py` vs `v5_verify.py`: **2**. `v4_selection.py` vs `v5_selection.py`: **0** (124 lines). `v4_record.py` vs `v5_record.py`: **2** (42 lines). `v4_decision.py` vs `v5_decision.py`: **7** (99-100 lines; the difference is the optional caller normalizer). The v5 proposal carries parity tests asserting equality with the v4 orchestration modulo version names (`test_r08v5_frozen_baseline.py` in PR #64); v3 and v4 carry frozen-baseline tests (`test_r08v3_frozen_baseline.py`, `test_r08v4_frozen_baseline.py`); whether v3/v4 also assert orchestration parity was not re-verified here.
- What genuinely differs per version: the **signing domain** (cross-version replay separation), the **registered family table** (frozen dispatch tables refuse unknown versions, which is a deliberate safety property), the **family payload validator and composer**, and the **effective-policy identity preimage**. The verification orchestration itself does not differ.

### 2.3 Distinct semantics versus duplication
- **Distinct and worth keeping:** version-specific signing domains and identity preimages (they stop a v4 signature verifying a v5 statement); the family-level validators and composers (the only place narrowing order is defined); the byte-identical frozen baselines (manifest tests of 158 files and growing).
- **Avoidable duplication:** the three identical `*_verify/_selection/_record` triples (about 410 lines each version) and the per-version `*_decision` wrappers. Reusable infrastructure already present: `verify.py`/`key_admission.py`/`canonical_b64.py`/`common.py` (shared), `v2_token.py` (frozen token predicate), the Ed25519 adapter, `v2_policy_identity.py` machinery.
- **Why it was done this way:** the frozen-contract rule forbids editing r08-v2 to add a family, and v3-v5 chose copy over refactor to keep every earlier file byte-identical (manifest-tested). That is a sound decision per increment; its cumulative cost is what is measured here.
- r08-v2 itself shows the alternative: one contract version carrying **three families** (f1ab, f4, f5) through documented amendments. r08-v3/v4/v5 each carry one.

### 2.4 The r08-v5 collision (decided by the Architect, 2026-10-28)
Registry PR #58 (held; clock tolerance F4T) and PR #64 both claim contract id `r08-v5`, both add `registry_successor/v5_*.py` and `docs/r08-v5-contract.md`. **Disposition (Architect):** `r08-v5` is reserved for the authorized `on_unreadable` implementation. PR #58 must not later merge under the same contract version or file names; it must be rebased on the then-current Registry baseline and assigned a distinct successor version, or reconciled explicitly by the Architect. The two proposals are not combined into a composite record. PR #58's historical evidence is not rewritten. Constructor clock tolerance remains NOT AUTHORIZED. Consequence recorded for the compatibility ledger: the next unallocated contract id is `r08-v6`.

## 3. ASSESSMENT B: workflow fragmentation
Compared: `GovernedAgeWorkflow` (F4, ctor scalars), `GovernedClassAgeWorkflow` (F5 class age), `GovernedClassUnreadableWorkflow` (PR; optionally with the class-age pair), and the Runtime narrowing adapters.

| Aspect | F4 `GovernedAgeWorkflow` | F5 `GovernedClassAgeWorkflow` | `GovernedClassUnreadableWorkflow` (PR) |
|---|---|---|---|
| Carrier | constructor scalars (no profile; **refuses** a runtime-authority profile, `runtime_authority_profile_unsupported`) | effective `RuntimeAuthorityProfile` | effective `RuntimeAuthorityProfile` (optionally with F5 age derived by the unchanged F5 function) |
| Selection verify | `verify_scope_selection` | `derive_effective` | `derive_unreadable`, `derive_governed` |
| Lifecycle boundaries | construction, decide, execute entry, commit gate | same | same, plus held-profile digest re-check before AND after source reads |
| Commit gate | `_GatedDestination` + `DefinitiveDestinationRejection("registry_f4_selection_invalid")` | same wrapper, `registry_f5_selection_invalid` | same wrapper, `registry_f5_unreadable_selection_invalid` |
| Refusal class | `RegistrySelectionRefused` | `RegistryClassAgeRefused` | `RegistryClassUnreadableRefused` |
| Identity property | `registry_f4_policy_identity` | `registry_f5_policy_identity` | `registry_f5_unreadable_policy_identity` |

- **Shared already:** `GovernedScope`, `SelectionMaterial`, `Refusal`, `_GatedDestination`, `_declared_authority` (F4 module, imported by the F5 modules); `profile_digest` and `derive_effective` (F5, imported by the PR). The F5 PR reuses rather than copies where a function was extractable.
- **Duplicated skeleton:** `_xx_revalidate`, `_xx_reverify`, `_xx_commit_gate`, `decide`, `execute`, the identity property and the constructor prologue (scope checks, host snapshot, destination wrap, bound tuple) are re-implemented per class: about 150-250 lines each, structurally identical, differing in the derive call and the compared tuple. This is the largest avoidable duplication in the Control Plane.
- **Useful specialization:** the derive function per family (what is verified, what is composed, which host invariants apply). The joint case already shows the right shape: a single workflow calling an ordered list of derive steps and binding one final profile digest.
- **Conflicting subclass composition:** stacking two governed subclasses is not possible by design (a second wrapper over an already gated destination is refused `destination_invalid`; tested). There is no accidental double-narrowing path. The cost is that every combination needs its own joint class (see C).
- **Inconsistent refusal semantics (minor):** three different exception classes and three `REJECTION_CODE` strings for the same event class (selection not valid at a boundary); the code vocabularies overlap but are not identical (F4 reports a changed scalar as `scalars_modified`, the F5 workflows report a changed profile as `profile_modified`; `class_age:`-prefixed codes appear only in the joint workflow). A caller cannot handle "any Registry-governed refusal" uniformly except through the shared base class `RegistrySelectionRefused`, which the three do share.
- **Runtime adapters:** the three `registry_f1*_narrowing.py` files differ by 85-127 normalized lines because each family's members differ; they are per-family narrowing adapters over one shared selection-authority module, which is the appropriate split.
- **Shared custody assumptions:** all three rely on the same host `selection_source` custody document (rollback, epoch, revocation visibility are host duties; no Control Plane ratchet). This is consistent and is not duplicated in code.
- **Commit-time enforcement differences:** none in mechanism (same wrapper, same rejection path). The PR adds a second held-profile check at the end of re-verification; F4/F5 check it once before the source read. Recorded as a hardening candidate for the older two (P2-3), not a defect.

## 4. ASSESSMENT C: atomic policy composition
Do not assume separate monotone narrowings compose safely. Answers, with evidence:

1. **Can F4 and F5 apply to the same action?** **No, not in one workflow today.** F4 refuses any runtime-authority profile (`registry_f4_age_governance.py:180`) and F5 requires one. Under a runtime-authority deployment only the F5 class bound is Registry-governed (for grant status); the constructor status and approval ages, which still bound conflict and policy status reads, are host-only. This is a coverage gap, not a widening (the host value always remains in force). See P1-2.
2. **Can F5 class-age and `on_unreadable` coexist?** **Yes, in one workflow** (`GovernedClassUnreadableWorkflow` with the age pair). The age part is derived by the unchanged F5 function; `on_unreadable` is composed over the age-effective profile; the fields touched are disjoint (`max_status_age_seconds` and, only when an outage extension is configured, `freshness.max_age_extension_seconds` versus `on_unreadable`). Tested: either selection changing, revoked or withdrawn, or either source failing, refuses at every boundary; there is no fallback to either family alone; a dropped age component cannot execute a persisted decision.
3. **One coherent effective-policy identity?** **Yes, as the final effective-profile digest.** `approval_commitment` and the persisted `catalogue_digest` hash the whole composed profile. The Registry per-family policy digests are carried in the workflow's in-memory bound tuple and compared at every boundary but are **not persisted** in the decision binding (known since F5; P2-2). Two different selections that yield the same final profile are indistinguishable in persisted evidence.
4. **Can the approval commitment bind all applicable policy?** For every overlay that lives in the profile, yes by construction (`approval_commitment` hashes `profile.model_dump()`). It cannot bind overlays that live outside the profile: constructor scalars (F4), `ObservationPolicy`, and the clock tolerance. Those need a separate binding decision (relevant to two of the six remaining parameters).
5. **Can revocation invalidate one family without leaving another improperly active?** In the joint workflow, no: any component failing refuses the whole workflow. Across **independently constructed** workflows (one age-only, one unreadable-only, same action) each is individually safe, but nothing technical prevents a host from running both and issuing approvals for each; that is the "uncontrolled sequence of overlays" the directive warns about, enforced today only by documentation (P1-3).
6. **Can partially updated selections create inconsistent decisions?** Within one workflow no (all-or-nothing identity tuple). A host that rebuilds one workflow with a new selection and keeps old decisions: old decisions cannot execute under a different effective profile (`authorization-critical inputs changed before effect`), tested.
7. **Do lifecycle checks cover all applicable families?** In the joint workflow yes: both sources are read at all four boundaries (tested: four calls per source per effect).
8. **Implicit paths that bypass required Registry participation?** Participation is a **deployment property**, not enforced inside `BoundedAuthorizationWorkflow`: a host can instantiate the plain workflow with the host profile and no Registry. The governed classes refuse optional participation, non-admitted verifiers and unreadable material, but cannot prevent their own non-use. No code path inside a governed workflow bypasses Registry. P1-3 covers the deployment-level control.

Additional composition risks identified for the **future** class-field overlays (not present today):
- **Post-composition validity.** `bounded.py:2111` makes an irreversible class with `on_unreadable != refuse` invalid. Today a narrowing of `on_unreadable` cannot produce that state (the host is validated first; narrowing only moves toward `refuse`). A future `reversibility` overlay moves a class toward irreversible and could produce an invalid composed profile (all actions of the class refuse: not a widening, but an availability defect that must be detected and reported at construction, not discovered at decide time). The rule "validate host first, compose, then validate the composed profile" should be shared infrastructure.
- **Shared profile members.** F5 composition already adjusts `freshness.max_age_extension_seconds`; the `anchor_deadline_to_inputs` parameter lives in the same `freshness` member and `policy_binding.py:126` already requires it when age ceilings are present. Overlay order and ownership of that member must be defined once.
- **Combinatorics.** With one joint subclass per combination, N class-field overlays need up to 2^N classes. An ordered list of derive steps removes this.

## 5. ASSESSMENT D: enforcement and custody
| Item | Finding |
|---|---|
| Construction | all governed workflows verify and compose before `super().__init__`; the PR validates the host first. |
| Decision / execute entry | re-verification before any state write; refusal raises before any record. |
| Pre-dispatch | `_GatedDestination.apply` re-verifies and raises the existing `DefinitiveDestinationRejection`; the attempt is recorded `failed`, which blocks automatic retry. |
| Delegated apply window | residual window between the gate and the delegated `apply` is **accepted for bounded engineering only** (previous Architect decision). Stronger production atomicity is not established. |
| `selection_source` custody | host-owned; durable host-side rollback and epoch protection required; no Control Plane ratchet (unchanged; `registry-f4-selection-source-custody.md`). |
| State recovery | a restarted workflow with the same host config and selection resumes persisted decisions; a different effective profile cannot execute them (tested). |
| Selection replacement | an equal effective identity is accepted; any change refuses until the host rebuilds the workflow and re-issues approvals. |
| Commitment / persisted identity | final-profile digest and `approval_commitment` persisted; per-family Registry digests not persisted (P2-2). |
No change to any of these Architect decisions is proposed.

## 6. ASSESSMENT E: cost of the six remaining parameters (after `on_unreadable` merges)
Remaining (from `parameter-catalogue.json`, denominator 19): `requires_revocation_assurance`, `reversibility`, `anchor_deadline_to_inputs`, terminal-revocation enablement, `ObservationPolicy.max_age_seconds`, `ObservationPolicy.clock_tolerance_seconds`. (The constructor clock tolerance RG-C-006 and the identity/mandate ages are BLOCKED and outside the 19.) Classification below is a builder estimate from the catalogue and the source read here; none was prototyped.

| Parameter | Registry today | Consumer today | Contract change | Commitment change | Lifecycle | Reuse | Coupling | Class |
|---|---|---|---|---|---|---|---|---|
| `requires_revocation_assurance` (bool, False to True only) | none | profile member read by `holder_inventory.py`; class holds `holder_inventory_missing` until an inventory exists | one new family slot (bool) | dump changes when True: new approval needed | existing machinery | the `on_unreadable` overlay pattern almost verbatim | self-inflicted denial if no inventory (open Architect question in the catalogue) | **MEDIUM** |
| `reversibility` | none | `bounded.py:2111/2189`, `reversibility.py` (producer assertions, member reshaping) | a family over producer assertions; member rules (AUD-D06 J3b) | profile dump changes | existing machinery | partial | **interacts with `on_unreadable` validity and the cached-purpose path**; fact-versus-claim question | **HIGH** |
| `anchor_deadline_to_inputs` (freshness member) | none | `bounded.py:1416,2105`; `policy_binding.py:126` | new family or composite with age | freshness member in the dump | existing machinery | partial | **shares `freshness` with the F5 extension composition; required True when ceilings are present** | **HIGH** |
| terminal-revocation enablement | none | `bounded.py:2390` (`_recorded_grant_denial`) | boolean/enum family | profile member | existing machinery | pattern reusable | host must have the recorded-denial infrastructure; AUD-D06 coupling | **MEDIUM** |
| `ObservationPolicy.max_age_seconds` | none | constructor argument (`bounded.py:414`), not in the profile | family `min(host, registry)` | **not in the approval commitment**: needs a binding decision (F4-style ctor path) | needs the F4/F5 coexistence gap closed (P1-2) | F4 scalar pattern | 60 vs 300 relation unresolved; no profile carrier | **HIGH** |
| `ObservationPolicy.clock_tolerance_seconds` | `f4t` proposal is for the other tolerance (PR #58, held) | constructor argument | distinct successor id (not `r08-v5`) | same as above | same | partial | blocked on AR-1/AR-2 whether the DR-CP-AGE-1 exclusion extends to it | **MEDIUM, gated by an Architect decision** |

## 7. Recommendations (not authorization)
Classification: P0 = prevents an actual authority or consistency defect; P1 = needed before further coupled-parameter migration; P2 = useful simplification; P3 = optional.

**P0: none found.**

**P1**
- **P1-1 Shared governed-workflow skeleton with an ordered list of derive steps.** Extract `revalidate/reverify/commit_gate/decide/execute/identity` and the constructor prologue once; each family contributes a derive step and a compose step; the bound identity becomes the tuple of all steps plus the final profile digest; a new overlay adds no new subclass and no new combination class. Must leave the three existing public classes and their tests intact (wrappers). Add the post-composition validity check here.
- **P1-2 Decide how F4 constructor scalars coexist with F5 profile overlays** (a runtime-authority deployment currently cannot Registry-govern the constructor status and approval ages). Needed before `ObservationPolicy` parameters.
- **P1-3 A deployment-level control for "one governed workflow per action"**, so two independently governed workflows cannot be issued approvals for the same action (documentation or a registry of constructed scopes is the minimum; a code check inside one process cannot see another process). Needs an Architect decision on where the control lives.
- **P1-4 Contract-allocation policy.** Decide whether remaining families go into new single-family versions (the r08-v3/v4/v5 pattern) or into one new version carrying several families (the r08-v2 pattern), and record the allocation table (`r08-v5` = on_unreadable; next free `r08-v6`).

**P2**
- **P2-1** Shared Registry orchestration for `*_verify/_selection/_record` in a new successor, importing rather than copying (frozen files untouched; parity tests become import-identity tests).
- **P2-2** Persist the per-family Registry effective-policy digests (or the selection ids and epochs) in the decision evidence so persisted provenance names the selection, not only the effective profile.
- **P2-3** Apply the PR's before-and-after held-profile check to the F4 and F5 class-age workflows.
- **P2-4** One refusal exception class and one rejection-code vocabulary for all governed workflows.

**P3**
- **P3-1** Generate the per-version manifest and vector scaffolding from one script (already scripted ad hoc).
- **P3-2** One generic test fixture library for the Control Plane governed-workflow tests (about 400 lines of fixtures are re-created per module).

### Components that should remain separate (recommendation A)
Version-specific signing domains and identity preimages; family payload validators and composers; the host-owned `selection_source` custody; the Runtime per-family narrowing adapters over their one selection-authority module; the frozen baselines.
### Unnecessary abstraction (recommendation H)
A generic policy language or interpreter; a plugin registry for families; a Control Plane ratchet or durable selection store (explicitly not authorized); merging the Registry families into one composite record.
### Recommended sequence for the remaining parameters (recommendation J)
1. Land `on_unreadable` (Architect decision on the open PRs). 2. P1-4 allocation decision, then P1-1 skeleton (optional but cheapest before the next overlay). 3. `requires_revocation_assurance` (MEDIUM, closest pattern). 4. terminal-revocation enablement (MEDIUM). 5. Close P1-2, then `ObservationPolicy.max_age_seconds`. 6. `anchor_deadline_to_inputs` together with a decision on freshness-member ownership. 7. `reversibility` last (highest coupling). 8. `ObservationPolicy.clock_tolerance_seconds` only after AR-1/AR-2. This ordering is a recommendation; none of it is authorized.

## 8. Architect decisions requested
- **DEC-1** Accept the `r08-v5` allocation (reserved to `on_unreadable`; `r08-v6` next) and record it in the compatibility ledger (already ruled; confirm the ledger wording).
- **DEC-2** Authorize or decline P1-1 (shared skeleton) as a separate increment before the next class-field parameter.
- **DEC-3** Decide P1-2 (F4 constructor scalars with runtime-authority profiles).
- **DEC-4** Decide P1-3 (where the single-governed-workflow-per-action control lives).
- **DEC-5** Decide P1-4 (single-family versions versus multi-family version for the remaining families).

## 9. Limits of this assessment
Source was read at the pinned heads, not executed beyond the test runs recorded in the increment PRs. The `reversibility`, `anchor_deadline_to_inputs`, terminal-revocation and `ObservationPolicy` rows rely partly on the audit catalogue and were not prototyped. No security review was performed. Nothing here changes the denominator (19), the static plan, the S02/G0 evidence or any accepted decision.
