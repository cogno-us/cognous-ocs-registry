# Revised M1 independent-oracle specification (Phase F)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

**Status: PROPOSED. NOT RATIFIED. NOT IMPLEMENTED. NOT EXECUTED.** This revises `g1-preparation/independent-oracle-specification.md` (merged, unchanged) by re-grouping the same 65 gaps into the nine families named by the Architect, adding exact pins, preconditions, expectation sources and verdict criteria, and applying PD-1 to PD-10 as recorded in architect-decision-register.md. It contains no executable test and invents no expected value: where the contract is silent the expectation is stated as NOT SPECIFIED.

Machine-readable form: `m1-oracle-specification.json` (65 entries with every field below).

## 1. Families

| Family | Name | Scope | Oracles | Components | Sources |
|---|---|---|---|---|---|
| OW-1 | F1b set narrowing | Composer- and decision-level narrowing of allowed_institutions and allowed_authority_domains (caller INTERSECT record, per set, deny-all, never wider). | 6 | REG | crosswalk rows 2, 3, 11 (compose_f1ab intersection-only; deny-all representation; caller normalisation); r08-v2 contract section 2 (F1ab lists) |
| OW-2 | Validation and malformed inputs | Token, list, bound and shape validation for the two sets and for the caller policy that meets them. | 10 | REG | crosswalk rows 1, 11 (_entry_ok/_list_ok, payload_validator, normalize_caller, valid_token); r08-v2 contract section 2 line 28; Amendment 1 5.1(3); ext-s1-5 spec 6.1 (N-13) |
| OW-3 | Scope/payload relationship | How scope.institution / scope.authority_domain, grants, ExpectedContext and cross-scope isolation relate to the payload sets. PD-1: independence preserved; no relation may be asserted. | 10 | REG, RT, CP | crosswalk rows 4, 5, 6 (statement scope, authority layer, scope layer, scope_key); Amendment 4 section 3 (pin members, DRAFT) |
| OW-4 | Decision-level outcomes | verify_and_decide_v2 outcomes: applied, applied_deny_all, refusals, substitution, wrong-context, family substitution. | 5 | REG | crosswalk rows 2, 3, 5 (decision.py outcomes, substitution layers) |
| OW-5 | Durable policy activation | Policy that results from a durably activated record: activation boundary, effective-policy derivation and equivalence with LocalExecutionPolicy on the durable path. | 8 | REG, RT | crosswalk rows 7, 11 (Registry stops at composition; baseline LocalExecutionPolicy); Amendment 3 section 2 items 1 and 3 |
| OW-6 | Effect-time containment | Amendment 3 effect-boundary check: executor sets are a subset of the authenticated activated record, per set, atomic, fail-closed. | 11 | REG, RT, CP | Amendment 3 section 2 items 1 to 6 (effective on merge); crosswalk row 7; ADR 7.4/7.6 |
| OW-7 | Revocation, recovery and restart | Withdrawal, revocation, supersession, optional fallback, post-commit unknown paths, restart and corrupted-payload recovery for records that carry the two sets. | 5 | REG, RT, CP | crosswalk rows 8, 9; Amendment 3 section 2 item 2; ADR 3.6/7.5 |
| OW-8 | Reason-code compatibility | Typed codes, REFUSE versus HOLD classes, cause attribution and refusal text. PD-2: committed semantics preserved, unratified map not adopted. | 6 | REG, RT | crosswalk row 10 (CODES 46, CODES_V2 48, CODES_V2_REV2 51); Amendment 1 sections 6.1 and 6.2a; Amendment 3 item 1 (policy_identity_mismatch) |
| OW-9 | Complete pin-plus-containment path | The authorization-pin step followed by five-set containment in one transaction. Amendment 4 is a DRAFT (PD-4). | 4 | REG, RT, CP, SQ | crosswalk row 12; Amendment 4 sections 3 to 6 (DRAFT, not effective); Amendment 3 section 2 |

The nine families replace the nine work packages OW-1..OW-9 of the merged preparation register; the numbers were reused with different meanings. The old-to-new mapping per gap is in gap-to-oracle-traceability-matrix.md. A gap has one primary family (counted above) and optionally one secondary family.

## 2. Pins (proposed independent qualification baseline, PROVISIONAL)

| Component | Pin |
|---|---|
| Registry | `317eb76acb2847c534c3ce7c2180b89b4aef987d` (code trees identical to `943ab183…`; see registry-pin-delta-assessment.md) |
| Control Plane | `d66ae07fa240510efdcc11ed4b3e1189dcefc822` |
| Runtime | `0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491` |
| Stack Qualification | `bb9b08904192b5f50a49e00ed8de0cab80fd7c19` |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` |

## 3. Common rules

- **Independence.** AI workers, the Lead Builder and CI are never independent. No author or reviewer is designated (PD-6): every oracle has `authored_by: null`. IND-A requires an independent author and reviewer with expected values from the specification source or an independent model. IND-R allows a builder to characterise only.
- **Expectation source labels.** CONTRACT/SPECIFICATION; SOURCE-OBSERVED (current code behaviour recorded, not asserted); NONE (contract silent, nothing is asserted).
- **Security tier (proposed oracle priority, unrelated to the V08 "Tier 1" qualification stage).** T1: severity HIGH, or a MEDIUM oracle in OW-6/OW-9 (failure could permit an effect outside the authorized policy). T3: CHARACTERISATION basis or LOW severity. T2: the rest. Counts: T1 18, T2 24, T3 23.
- **Verdicts.** PASS needs positive evidence that the condition was delivered and refused for the intended typed reason, with the environment at the exact pins. FAIL = contradiction. BLOCK = prerequisite or ruling missing; the oracle is not run. INCONCLUSIVE = ran but could not deliver the condition, or any skip. A skip is never a PASS.
- **Readiness labels.** SPEC-READY (41): the specification can be ratified now. CHARACTERISATION-ONLY (16): verdict is CHARACTERISED. BLOCKED-SEMANTICS (PD-1) (7): relation unspecified; expected value not given. CLAIM-CHECK (1). Authoring and execution of every oracle additionally need PD-6 and the environment of environment-profile.md.
- **Family rules** (apply to every oracle of the family):

### OW-1 - F1b set narrowing

Composer- and decision-level narrowing of allowed_institutions and allowed_authority_domains (caller INTERSECT record, per set, deny-all, never wider).

- Oracles (primary): 6; components: REG
- Specification sources: crosswalk rows 2, 3, 11 (compose_f1ab intersection-only; deny-all representation; caller normalisation); r08-v2 contract section 2 (F1ab lists)
- Test preconditions: Profile R (Registry hash locks) with PyNaCl 1.6.2 where a signed record is built. Registry checkout at the baseline pin, clean tree.
- Mandatory refusal conditions: An effective set containing any member absent from the caller or from the record (widening) is a FAIL. An empty intersection must be reported as deny-all, never as an applied policy.

### OW-2 - Validation and malformed inputs

Token, list, bound and shape validation for the two sets and for the caller policy that meets them.

- Oracles (primary): 10; components: REG
- Specification sources: crosswalk rows 1, 11 (_entry_ok/_list_ok, payload_validator, normalize_caller, valid_token); r08-v2 contract section 2 line 28; Amendment 1 5.1(3); ext-s1-5 spec 6.1 (N-13)
- Test preconditions: Profile R; Node v22 for any vector that reuses the ext-s1-5 Node cross-check. Frozen Unicode table of ext-s1-5 spec 6.1 (N-13) available as the expected-value source.
- Mandatory refusal conditions: Every malformed input in the vector must be refused with a typed code. Acceptance of an input the specification source refuses is a FAIL.

### OW-3 - Scope/payload relationship

How scope.institution / scope.authority_domain, grants, ExpectedContext and cross-scope isolation relate to the payload sets. PD-1: independence preserved; no relation may be asserted.

- Oracles (primary): 10; components: REG, RT, CP
- Specification sources: crosswalk rows 4, 5, 6 (statement scope, authority layer, scope layer, scope_key); Amendment 4 section 3 (pin members, DRAFT)
- Test preconditions: Profile X (pydantic >= 2.12) wherever a Control Plane claim is built. PD-1 recorded as FINAL (independence preserved): no scope/payload relation may be asserted.
- Mandatory refusal conditions: Under PD-1 no oracle may assert any relation between scope.* and the payload sets. Isolation oracles: a row, grant or record for scope A must never be selected for scope B.

### OW-4 - Decision-level outcomes

verify_and_decide_v2 outcomes: applied, applied_deny_all, refusals, substitution, wrong-context, family substitution.

- Oracles (primary): 5; components: REG
- Specification sources: crosswalk rows 2, 3, 5 (decision.py outcomes, substitution layers)
- Test preconditions: Profile R with PyNaCl 1.6.2. Registry checkout at the baseline pin, clean tree.
- Mandatory refusal conditions: Wrong context, substituted record, cross-family or cross-scope inputs must produce a typed refusal; an 'applied' outcome is a FAIL.

### OW-5 - Durable policy activation

Policy that results from a durably activated record: activation boundary, effective-policy derivation and equivalence with LocalExecutionPolicy on the durable path.

- Oracles (primary): 8; components: REG, RT
- Specification sources: crosswalk rows 7, 11 (Registry stops at composition; baseline LocalExecutionPolicy); Amendment 3 section 2 items 1 and 3
- Test preconditions: Profile X; OCS_REGISTRY_PIN_DIR set to the Registry checkout. Runtime engine module registry_f1a_narrowing and the baseline LocalExecutionPolicy both present.
- Mandatory refusal conditions: A deny-all record must never yield an executable policy. A governed claim over a non-narrowing record must not produce a different allow/deny outcome from the ungoverned path.

### OW-6 - Effect-time containment

Amendment 3 effect-boundary check: executor sets are a subset of the authenticated activated record, per set, atomic, fail-closed.

- Oracles (primary): 11; components: REG, RT, CP
- Specification sources: Amendment 3 section 2 items 1 to 6 (effective on merge); crosswalk row 7; ADR 7.4/7.6
- Test preconditions: Profile X; PyNaCl 1.6.2; OCS_REGISTRY_PIN_DIR set; Runtime destination built WITHOUT authorization_pin for direct containment. Fixture independence: do not import the builder's g.Gov fixtures as the expected-value source.
- Mandatory refusal conditions: Executor set member absent from the record set: REFUSE policy_identity_mismatch with zero effect rows. Missing, non-canonical or ill-formed stored payload: HOLD store_unknown with zero effect rows. Binding present and executor sets absent: refuse (verifier_unavailable). An effect committed in any of these is a FAIL.

### OW-7 - Revocation, recovery and restart

Withdrawal, revocation, supersession, optional fallback, post-commit unknown paths, restart and corrupted-payload recovery for records that carry the two sets.

- Oracles (primary): 5; components: REG, RT, CP
- Specification sources: crosswalk rows 8, 9; Amendment 3 section 2 item 2; ADR 3.6/7.5
- Test preconditions: Profile X; PyNaCl; OCS_REGISTRY_PIN_DIR; ability to restart a process against the same SQLite file.
- Mandatory refusal conditions: After withdrawal, revocation, supersession or restore, no effect may commit on the revoked authority; unknown or corrupt state must HOLD, never execute. Effects committed before the transition are not rolled back (ADR 7.5).

### OW-8 - Reason-code compatibility

Typed codes, REFUSE versus HOLD classes, cause attribution and refusal text. PD-2: committed semantics preserved, unratified map not adopted.

- Oracles (primary): 6; components: REG, RT
- Specification sources: crosswalk row 10 (CODES 46, CODES_V2 48, CODES_V2_REV2 51); Amendment 1 sections 6.1 and 6.2a; Amendment 3 item 1 (policy_identity_mismatch)
- Test preconditions: Profile R or X; the committed reason tables CODES (46), CODES_V2 (48), CODES_V2_REV2 (51) read from the baseline pin.
- Mandatory refusal conditions: Committed REFUSE/HOLD classes and codes are recorded as observed; no reclassification is asserted (PD-2). A new code or a changed class is reported, not judged.

### OW-9 - Complete pin-plus-containment path

The authorization-pin step followed by five-set containment in one transaction. Amendment 4 is a DRAFT (PD-4).

- Oracles (primary): 4; components: REG, RT, CP, SQ
- Specification sources: crosswalk row 12; Amendment 4 sections 3 to 6 (DRAFT, not effective); Amendment 3 section 2
- Test preconditions: Profile X; a Control Plane worktree at the baseline pin supplied by a recorded variable (the hard-coded CP_WORKTREE path is not acceptable). Amendment 4 status recorded as DRAFT in the oracle header; any result is labelled DRAFT-DEPENDENT.
- Mandatory refusal conditions: The pin step precedes containment; a pin-valid claim with a widened executor policy must be refused with zero effects. All results are DRAFT-DEPENDENT.


## 4. The 11 HIGH oracles (prioritised)

Order: SPEC-READY first, then BLOCKED. Ready = the specification is ratifiable; none is executable until PD-6 and the environment are in place.

#### OR-E-06 / M1-E-06 - OW-1 (F1b set narrowing), tier T1, SPEC-READY

- Objective (gap): Decision-level (verify_and_decide_v2) narrowing is exercised only for allowed_units (V1A-02); for the two sets the only decision-level case has identical single-element caller and registry sets.
- Kind / basis: negative / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution)
- Fixture inputs: Fixture requirement (G1 register): Table of (caller, registry, expected) per set, expected computed by an independent set-theoretic model, not by compose_f1ab. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-1 (F1b set narrowing): An effective set containing any member absent from the caller or from the record (widening) is a FAIL. An empty intersection must be reported as deny-all, never as an applied policy.
- Expectation source: CONTRACT/SPECIFICATION (sources: crosswalk rows 2, 3, 11 (compose_f1ab intersection-only; deny-all representation; caller normalisation); r08-v2 contract section 2 (F1ab lists))
- Restrictions (what must not be asserted):
  - none beyond the family rule
- PASS: Every row: decision outcome and all five effective sets equal the model's. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-E-10 / M1-E-10 - OW-1 (F1b set narrowing), tier T1, SPEC-READY

- Objective (gap): G0 worker A claim REFUTED at composer level and VERIFIED at decision/vector level: composer deny-all covers all five keys (32 combinations), but decision-level deny-all (V1A-03) and the single-dimension vectors (EP-011/012) are allowed_units only. There is no decision-level or vector case where exactly allowed_institutions (or exactly allowed_authority_domains) is empty and the other four are not.
- Kind / basis: vector / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution)
- Fixture inputs: Fixture requirement (G1 register): Add EP-style vectors with deny_all == [allowed_institutions] and [allowed_authority_domains], plus decision-level applied_deny_all cases. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-1 (F1b set narrowing): An effective set containing any member absent from the caller or from the record (widening) is a FAIL. An empty intersection must be reported as deny-all, never as an applied policy.
- Expectation source: CONTRACT/SPECIFICATION (sources: crosswalk rows 2, 3, 11 (compose_f1ab intersection-only; deny-all representation; caller normalisation); r08-v2 contract section 2 (F1ab lists))
- Restrictions (what must not be asserted):
  - none beyond the family rule
- PASS: Every row yields applied_deny_all naming exactly the empty set, at vector and at verify_and_decide_v2 level. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-E-21 / M1-E-21 - OW-6 (Effect-time containment), tier T1, SPEC-READY

- Objective (gap): No executable Registry-side oracle for effect-time containment of the two sets. Amendment 3 is prose with text-pin tests; the five-set containment vectors (executor sets x record payload sets -> accept / REFUSE policy_identity_mismatch / HOLD store_unknown, including 'first offending set' ordering) do not exist in the Registry repo.
- Kind / basis: vector / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491; Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822
- Fixture inputs: Fixture requirement (G1 register): Publish a Registry-owned vector file: (executor sets, record payload, expected verdict, expected cause) with cases per set, including extras in institutions only and domains only, empty executor set, payload missing a set, malformed payload set. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-6 (Effect-time containment): Executor set member absent from the record set: REFUSE policy_identity_mismatch with zero effect rows. Missing, non-canonical or ill-formed stored payload: HOLD store_unknown with zero effect rows. Binding present and executor sets absent: refuse (verifier_unavailable). An effect committed in any of these is a FAIL.
- Expectation source: CONTRACT/SPECIFICATION (sources: Amendment 3 section 2 items 1 to 6 (effective on merge); crosswalk row 7; ADR 7.4/7.6)
- Restrictions (what must not be asserted):
  - Cause spelling and 'first offending set' ordering are NOT defined by Amendment 3 (E-22, PD-2): record them as CHARACTERISED, never as PASS/FAIL criteria.
  - The Registry repo does not enforce effect-time containment; the vector file is Registry-owned data consumed by a Runtime-side harness.
- PASS: Every vector row yields its verdict class and code with zero effect rows on refusals; the cause string and the order of offending sets are recorded as CHARACTERISED. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-E-26 / M1-E-26 - OW-6 (Effect-time containment), tier T1, SPEC-READY

- Objective (gap): Amendment 3 item 2 requires the Runtime to treat a stored record payload that is missing a set, non-canonical, or not well-formed under the Registry value rules as HOLD store_unknown. The kit stores the record pin (id/version/digest) only, never the payload; no Registry vector covers a restart/restore where the stored payload lacks allowed_institutions or allowed_authority_domains, is truncated, or reorders them.
- Kind / basis: vector / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491; Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822
- Fixture inputs: Fixture requirement (G1 register): Add payload-bearing state to the kit (or a companion vector) with corrupt-payload rows; expected UNKNOWN_FAIL_CLOSED / store_unknown. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-6 (Effect-time containment): Executor set member absent from the record set: REFUSE policy_identity_mismatch with zero effect rows. Missing, non-canonical or ill-formed stored payload: HOLD store_unknown with zero effect rows. Binding present and executor sets absent: refuse (verifier_unavailable). An effect committed in any of these is a FAIL.
- Expectation source: CONTRACT/SPECIFICATION (sources: Amendment 3 section 2 items 1 to 6 (effective on merge); crosswalk row 7; ADR 7.4/7.6)
- Restrictions (what must not be asserted):
  - none beyond the family rule
- PASS: Every corrupt-payload row yields HOLD store_unknown and zero effect rows, both at activation-time reload and after a process restart. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-E-30 / M1-E-30 - OW-5 (Durable policy activation), tier T1, SPEC-READY

- Objective (gap): No differential/equivalence oracle between compose_f1ab effective sets and LocalExecutionPolicy.check for the two sets. The S05 harness is the template (independent oracle, frozen expectations) but is three-set only; nothing builds a LocalExecutionPolicy from a five-set effective result in the Registry repo.
- Kind / basis: differential / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491
- Fixture inputs: Fixture requirement (G1 register): S05-style grid over (caller, registry, op institution/domain) with an independent model; exhaustive over small universes. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-5 (Durable policy activation): A deny-all record must never yield an executable policy. A governed claim over a non-narrowing record must not produce a different allow/deny outcome from the ungoverned path.
- Expectation source: CONTRACT/SPECIFICATION (sources: crosswalk rows 7, 11 (Registry stops at composition; baseline LocalExecutionPolicy); Amendment 3 section 2 items 1 and 3)
- Restrictions (what must not be asserted):
  - none beyond the family rule
- PASS: Every grid point: allow/deny of the evaluator equals the model's. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-F-06 / M1-F-06 - OW-5 (Durable policy activation), tier T1, SPEC-READY

- Objective (gap): Nothing in the engine builds the executor policy from caller policy and the activated record on the durable path: evaluate_with_registry_selection (the only code that computes caller INTERSECT record) is imported by no engine module (grep). The effect-time guard enforces executor SUBSET-OF record, not equality with the intersection. No end-to-end test takes a multi-member caller policy and record, derives the effective policy via the adapter, and drives it through the atomic route to show the two agree for institutions/domains.
- Kind / basis: differential / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491
- Fixture inputs: Fixture requirement (G1 register): Needs a differential oracle comparing adapter output with atomic-route outcome across an institution x domain grid. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-5 (Durable policy activation): A deny-all record must never yield an executable policy. A governed claim over a non-narrowing record must not produce a different allow/deny outcome from the ungoverned path.
- Expectation source: CONTRACT/SPECIFICATION (sources: crosswalk rows 7, 11 (Registry stops at composition; baseline LocalExecutionPolicy); Amendment 3 section 2 items 1 and 3)
- Restrictions (what must not be asserted):
  - Amendment 3 states executor SUBSET-OF record; it does not state executor EQUALS caller INTERSECT record. Intersection equivalence is CHARACTERISED, not asserted.
  - evaluate_with_registry_selection is imported by no engine module (re-verified at Runtime 0dde0ef7); no durable-path derivation exists to compare against.
- PASS: The containment sub-expectation holds on every grid point; the equivalence sub-expectation is reported as CHARACTERISED (agreement or disagreement) and cannot FAIL the oracle. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-F-07 / M1-F-07 - OW-6 (Effect-time containment), tier T1, SPEC-READY

- Objective (gap): Durable and effect-time deny-all is untested for the two sets. No test activates a record whose allowed_institutions or allowed_authority_domains is [] and shows the claim is refused (policy_not_subset:<field>, zero effects), and no test runs an executor whose own allowed_institutions/allowed_authority_domains is empty through the atomic route (expected policy_denial 'local institution restriction'; the atomic-route evaluator test uses allowed_actions). The adapter-level empty branch (:110-111) is exercised only for allowed_units.
- Kind / basis: negative / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491; Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822
- Fixture inputs: Fixture requirement (G1 register): Independent fixture needed: record payload with [] for exactly one of the two sets, otherwise the standard record. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-6 (Effect-time containment): Executor set member absent from the record set: REFUSE policy_identity_mismatch with zero effect rows. Missing, non-canonical or ill-formed stored payload: HOLD store_unknown with zero effect rows. Binding present and executor sets absent: refuse (verifier_unavailable). An effect committed in any of these is a FAIL.
- Expectation source: CONTRACT/SPECIFICATION (sources: Amendment 3 section 2 items 1 to 6 (effective on merge); crosswalk row 7; ADR 7.4/7.6)
- Restrictions (what must not be asserted):
  - Cause spelling policy_not_subset:<field> is source-observed, not contract-defined (E-22); the evaluator text 'local institution restriction' is Runtime evaluator behaviour, recorded not asserted.
- PASS: Both sub-cases: zero effect rows; the first yields policy_identity_mismatch. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-F-26 / M1-F-26 - OW-5 (Durable policy activation), tier T1, SPEC-READY

- Objective (gap): No full-grid differential at the DURABLE effect boundary: governed claim with a NON-narrowing f1ab record versus the same operations on the ungoverned LocalExecutionPolicy path, across an institution x authority_domain grid (allow and every refusal reason). The adapter-level equivalence (M1-16) is a stride-7 sample, and the G0 S05 equivalence is three-set.
- Kind / basis: differential / SPECIFICATION
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491
- Fixture inputs: Fixture requirement (G1 register): Differential harness: ungoverned path vs governed path with an equal-sets record; independent grid generator. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: Per family rule OW-5 (Durable policy activation): A deny-all record must never yield an executable policy. A governed claim over a non-narrowing record must not produce a different allow/deny outcome from the ungoverned path.
- Expectation source: CONTRACT/SPECIFICATION (sources: crosswalk rows 7, 11 (Registry stops at composition; baseline LocalExecutionPolicy); Amendment 3 section 2 items 1 and 3)
- Restrictions (what must not be asserted):
  - none beyond the family rule
- PASS: Every grid point: governed and ungoverned allow/deny are identical. Environment prerequisites satisfied at the exact pins; positive evidence that each condition was delivered.
- FAIL: Any row or grid point contradicts the expectation, or an effect row is committed where a refusal is required.
- BLOCK: Any of: pins not at the baseline; profile not installed from the hash locks; independent author or reviewer not designated (PD-6); an open ruling named in the label.
- INCONCLUSIVE: The oracle ran but the condition could not be delivered (fixture not buildable, module skipped, harness error, unexplained mutant), or a skip occurred. Never reported as PASS.
- Independence: IND-A: independent author and independent reviewer; expected values come from the named specification source or an independent model, never from the code under test.

#### OR-E-12 / M1-E-12 - OW-3 (Scope/payload relationship), tier T1, BLOCKED-SEMANTICS (PD-1)

- Objective (gap): (c) No vector or test crosses scope.institution / scope.authority_domain with the payload sets. Neither contract text nor code states the intended relation (e.g. a statement scoped to inst-a pinning a record whose allowed_institutions is ['inst-b'], or whose allowed_authority_domains excludes the scope's domain). The Registry composes and returns it as 'applied'. Default fixtures use inst-a/domain-a in both places, so even an accidental coupling would be invisible.
- Kind / basis: negative / SPECIFICATION-PENDING-RULING
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491; Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822
- Fixture inputs: Fixture requirement (G1 register; its stated result is a proposal, not an expectation): Specify first (Architect), then add vectors with scope != payload for each set, expected value from the specification, not from code. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: NOT SPECIFIED. PD-1 open: Record the observation; assert nothing.
- Expectation source: NONE: the governing relation is not specified (PD-1); no expected value is given
- Restrictions (what must not be asserted):
  - PD-1: no expected value is given. Do not assert containment, equality or exclusion between scope.institution / scope.authority_domain and the payload sets.
- PASS: Not available until the blocking ruling exists; the expected value is not specified.
- FAIL: Not available until then.
- BLOCK: Mandatory: report BLOCK while the ruling is open (PD-1 is FINAL as 'independence preserved'; the relation itself is unratified).
- INCONCLUSIVE: Not applicable while blocked.
- Independence: IND-A after the ruling named in the label (PD-1).

#### OR-E-34 / M1-E-34 - OW-9 (Complete pin-plus-containment path), tier T1, BLOCKED-SEMANTICS (PD-1) , DRAFT-DEPENDENT

- Objective (gap): Interaction order: pin step 5 (scope.* vs pin) precedes step 6 (scope key from pin) and step 7 (five-set containment); the pin has no member for the five sets. No contract text or vector says that a record activated for the authorized institution may carry allowed_institutions that exclude (or include) that institution, i.e. the same unspecified relation as M1-E-12 seen from the pin side. Pin refusals and containment refusals share the code policy_identity_mismatch and differ only by an unspecified cause string.
- Kind / basis: vector / SPECIFICATION-PENDING-RULING
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491; Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822; Stack Qualification bb9b08904192b5f50a49e00ed8de0cab80fd7c19
- Fixture inputs: Fixture requirement (G1 register; its stated result is a proposal, not an expectation): Joint vector: pin ok + binding ok + executor institution/domain set outside record payload -> REFUSE policy_identity_mismatch, cause names the set. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: NOT SPECIFIED. PD-1 open: Record the observation; assert nothing.
- Expectation source: NONE: the governing relation is not specified (PD-1); no expected value is given
- Restrictions (what must not be asserted):
  - PD-1 and PD-4: the scope-versus-payload relation is unspecified and Amendment 4 is a DRAFT; no expected value is given for 'pin ok + binding ok + executor outside the record'.
  - The Amendment 3 part (executor member outside the record payload is refused) is covered by E-21, independent of the pin.
- PASS: Not available until the blocking ruling exists; the expected value is not specified.
- FAIL: Not available until then.
- BLOCK: Mandatory: report BLOCK while the ruling is open (PD-1 is FINAL as 'independence preserved'; the relation itself is unratified).
- INCONCLUSIVE: Not applicable while blocked.
- Independence: IND-A after the ruling named in the label (PD-1).

#### OR-F-08 / M1-F-08 - OW-3 (Scope/payload relationship), tier T1, BLOCKED-SEMANTICS (PD-1)

- Objective (gap): No Runtime test (and no SQ slice read) puts two governed scopes with different institution or authority_domain in one store and shows isolation: every Runtime/SQ governed fixture uses scope inst-a/domain-a/tenant-a and varies only `operation` (GS_OTHER, B-05, FA1-03, original F-A1 attack). Cross-institution, cross-domain and cross-tenant row selection in check_effect, activation lineage and the unbound-claim scan (:1498) are therefore unexercised.
- Kind / basis: differential / SPECIFICATION-PENDING-RULING
- Components: Registry 317eb76acb2847c534c3ce7c2180b89b4aef987d (code trees identical to 943ab183…; verify the seven tree hashes at execution); Runtime 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491; Control Plane d66ae07fa240510efdcc11ed4b3e1189dcefc822
- Fixture inputs: Fixture requirement (G1 register; its stated result is a proposal, not an expectation): Needs a second activated scope differing only in institution (then only in authority_domain); independent fixture. Default single-member fixtures (inst-a, domain-a) must not be the only inputs.
- Expected observation: NOT SPECIFIED. PD-1 open: Record the observation; assert nothing.
- Expectation source: NONE: the governing relation is not specified (PD-1); no expected value is given
- Restrictions (what must not be asserted):
  - PD-1 (as classified in the merged register): isolation expectations are held until the Architect confirms that scope-key isolation can be asserted without any scope/payload relation. Proposal for that confirmation: split into an isolation oracle (scope key only) and a relation oracle (blocked).
- PASS: Not available until the blocking ruling exists; the expected value is not specified.
- FAIL: Not available until then.
- BLOCK: Mandatory: report BLOCK while the ruling is open (PD-1 is FINAL as 'independence preserved'; the relation itself is unratified).
- INCONCLUSIVE: Not applicable while blocked.
- Independence: IND-A after the ruling named in the label (PD-1).


## 5. All 65 oracles (summary)

| Oracle | Gap | Family (secondary) | Sev | Tier | Kind | Readiness | Decision | Draft-dep. |
|---|---|---|---|---|---|---|---|---|
| OR-E-01 | M1-E-01 | OW-2 | MEDIUM | T2 | vector | SPEC-READY | - | - |
| OR-E-02 | M1-E-02 | OW-2 | MEDIUM | T3 | differential | CHARACTERISATION-ONLY | - | - |
| OR-E-03 | M1-E-03 | OW-4 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-04 | M1-E-04 | OW-2 | MEDIUM | T2 | vector | CHARACTERISATION-ONLY | PD-3 | - |
| OR-E-05 | M1-E-05 | OW-2 | LOW | T3 | positive | SPEC-READY | - | - |
| OR-E-06 | M1-E-06 | OW-1 (OW-4) | HIGH | T1 | negative | SPEC-READY | - | - |
| OR-E-07 | M1-E-07 | OW-1 | MEDIUM | T2 | differential | SPEC-READY | - | - |
| OR-E-08 | M1-E-08 | OW-1 | MEDIUM | T2 | property | SPEC-READY | - | - |
| OR-E-09 | M1-E-09 | OW-1 | MEDIUM | T2 | mutation | SPEC-READY | - | - |
| OR-E-10 | M1-E-10 | OW-1 (OW-4) | HIGH | T1 | vector | SPEC-READY | - | - |
| OR-E-11 | M1-E-11 | OW-5 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-12 | M1-E-12 | OW-3 | HIGH | T1 | negative | BLOCKED-SEMANTICS (PD-1) | PD-1 | - |
| OR-E-13 | M1-E-13 | OW-2 (OW-3) | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-14 | M1-E-14 | OW-3 (OW-4) | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-15 | M1-E-15 | OW-4 (OW-3) | LOW | T3 | negative | SPEC-READY | - | - |
| OR-E-16 | M1-E-16 | OW-4 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-17 | M1-E-17 | OW-3 | MEDIUM | T2 | vector | SPEC-READY | - | - |
| OR-E-18 | M1-E-18 | OW-4 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-19 | M1-E-19 | OW-3 | MEDIUM | T2 | vector | SPEC-READY | - | - |
| OR-E-20 | M1-E-20 | OW-2 | LOW | T3 | differential | CHARACTERISATION-ONLY | - | - |
| OR-E-21 | M1-E-21 | OW-6 | HIGH | T1 | vector | SPEC-READY | - | - |
| OR-E-22 | M1-E-22 | OW-6 (OW-8) | MEDIUM | T1 | negative | CHARACTERISATION-ONLY | PD-2 | - |
| OR-E-23 | M1-E-23 | OW-8 (OW-6) | LOW | T3 | negative | CHARACTERISATION-ONLY | PD-2 | - |
| OR-E-24 | M1-E-24 | OW-7 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-25 | M1-E-25 | OW-8 | LOW | T3 | negative | CHARACTERISATION-ONLY | PD-2 | - |
| OR-E-26 | M1-E-26 | OW-6 (OW-7) | HIGH | T1 | vector | SPEC-READY | - | - |
| OR-E-27 | M1-E-27 | OW-8 (OW-1) | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-E-28 | M1-E-28 | OW-4 | MEDIUM | T3 | differential | CHARACTERISATION-ONLY | - | - |
| OR-E-29 | M1-E-29 | OW-8 | LOW | T3 | negative | CHARACTERISATION-ONLY | PD-2 | - |
| OR-E-30 | M1-E-30 | OW-5 | HIGH | T1 | differential | SPEC-READY | - | - |
| OR-E-31 | M1-E-31 | OW-2 | MEDIUM | T3 | negative | CHARACTERISATION-ONLY | - | - |
| OR-E-32 | M1-E-32 | OW-5 | MEDIUM | T3 | differential | CHARACTERISATION-ONLY | - | - |
| OR-E-33 | M1-E-33 | OW-3 (OW-9) | MEDIUM | T2 | negative | BLOCKED-SEMANTICS (PD-1) | PD-1 | yes |
| OR-E-34 | M1-E-34 | OW-9 | HIGH | T1 | vector | BLOCKED-SEMANTICS (PD-1) | PD-1 | yes |
| OR-E-35 | M1-E-35 | OW-9 | LOW | T3 | positive | CLAIM-CHECK (PD-4: Amendment 4 DRAFT) | PD-4 | yes |
| OR-F-01 | M1-F-01 | OW-6 | MEDIUM | T1 | negative | SPEC-READY | - | - |
| OR-F-02 | M1-F-02 | OW-2 | LOW | T3 | negative | SPEC-READY | - | - |
| OR-F-03 | M1-F-03 | OW-2 | LOW | T3 | vector | SPEC-READY | - | - |
| OR-F-04 | M1-F-04 | OW-1 (OW-6) | MEDIUM | T2 | mutation | SPEC-READY | - | - |
| OR-F-05 | M1-F-05 | OW-6 | MEDIUM | T1 | property | SPEC-READY | - | - |
| OR-F-06 | M1-F-06 | OW-5 | HIGH | T1 | differential | SPEC-READY | - | - |
| OR-F-07 | M1-F-07 | OW-6 (OW-5) | HIGH | T1 | negative | SPEC-READY | - | - |
| OR-F-08 | M1-F-08 | OW-3 | HIGH | T1 | differential | BLOCKED-SEMANTICS (PD-1) | PD-1 | - |
| OR-F-09 | M1-F-09 | OW-3 | MEDIUM | T2 | negative | BLOCKED-SEMANTICS (PD-1) | PD-1 | - |
| OR-F-10 | M1-F-10 | OW-3 (OW-9) | MEDIUM | T2 | negative | SPEC-READY | - | yes |
| OR-F-11 | M1-F-11 | OW-3 | LOW | T3 | negative | SPEC-READY | - | - |
| OR-F-12 | M1-F-12 | OW-6 | MEDIUM | T1 | mutation | SPEC-READY | - | - |
| OR-F-13 | M1-F-13 | OW-6 | MEDIUM | T1 | negative | SPEC-READY | - | - |
| OR-F-14 | M1-F-14 | OW-3 | MEDIUM | T2 | negative | BLOCKED-SEMANTICS (PD-1) | PD-1 | - |
| OR-F-15 | M1-F-15 | OW-5 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-F-16 | M1-F-16 | OW-5 (OW-3) | LOW | T3 | negative | SPEC-READY | - | - |
| OR-F-17 | M1-F-17 | OW-6 | MEDIUM | T3 | negative | CHARACTERISATION-ONLY | - | - |
| OR-F-18 | M1-F-18 | OW-6 | LOW | T3 | property | SPEC-READY | - | - |
| OR-F-19 | M1-F-19 | OW-6 | LOW | T3 | negative | CHARACTERISATION-ONLY | - | - |
| OR-F-20 | M1-F-20 | OW-7 | MEDIUM | T2 | differential | SPEC-READY | - | - |
| OR-F-21 | M1-F-21 | OW-7 | LOW | T3 | negative | CHARACTERISATION-ONLY | - | - |
| OR-F-22 | M1-F-22 | OW-7 | MEDIUM | T2 | vector | SPEC-READY | - | - |
| OR-F-23 | M1-F-23 | OW-7 | LOW | T3 | vector | SPEC-READY | - | - |
| OR-F-24 | M1-F-24 | OW-8 | MEDIUM | T3 | vector | CHARACTERISATION-ONLY | - | - |
| OR-F-25 | M1-F-25 | OW-8 | LOW | T3 | negative | CHARACTERISATION-ONLY | - | - |
| OR-F-26 | M1-F-26 | OW-5 | HIGH | T1 | differential | SPEC-READY | - | - |
| OR-F-27 | M1-F-27 | OW-2 | MEDIUM | T2 | negative | SPEC-READY | - | - |
| OR-F-28 | M1-F-28 | OW-5 | LOW | T3 | differential | CHARACTERISATION-ONLY | - | - |
| OR-F-29 | M1-F-29 | OW-9 | MEDIUM | T1 | negative | SPEC-READY | - | yes |
| OR-F-30 | M1-F-30 | OW-9 (OW-3) | MEDIUM | T1 | negative | BLOCKED-SEMANTICS (PD-1) | PD-1 | yes |

Per-oracle pins, preconditions, fixture requirement, expectation source, refusal conditions and criteria for the remaining 54 are in the JSON file. They are generated from the family rules above and the register entry; they add no oracle-specific expected value.

## 6. What is deliberately not here

No executable test; no fixture file; no generated expected values; no assignment of an author or reviewer; no successor-contract text; no claim that any gap is closed; no run of the proposed battery.
