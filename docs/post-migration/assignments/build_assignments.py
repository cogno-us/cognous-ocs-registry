import json, re, sys, pathlib
from jsonschema import Draft202012Validator
CONST = pathlib.Path('/home/claude/cogno-us/cognous-engineering-constitution')
OUT = pathlib.Path(sys.argv[1])
REV = 'dcdbe3b76843d672ca3cfb1f000124ecd78ed03c'
REG_MAIN = '2815643c3e15fbc6aadadbf88dc7596f10120992'
CP_MAIN = '739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69'
schema = json.loads((CONST/'schemas/orchestrator-assignment-v1.schema.json').read_text())
addendum = (CONST/'ENGINEERING_COMPLIANCE_ADDENDUM.md').read_text().split('\n')

def slice_rows(arch):
    i = [k for k, l in enumerate(addendum) if l.strip() == f'### Archetype {arch}'][0]
    rows = []
    for l in addendum[i+1:i+12]:
        if l.startswith('| CA'):
            c = [x.strip() for x in l.strip().strip('|').split('|')]
            rows.append((c[0].split(' ')[0], c[1], c[2]))
    return rows

def clauses(arch, bindings):
    rows = slice_rows(arch)
    assert [r[0] for r in rows] == list(bindings), (arch, [r[0] for r in rows])
    return [dict(article=a, requiredBehavior=rb, prohibitedShortcut=ps, binding=bindings[a]) for a, rb, ps in rows]

HOLDS = ['Registry #58/#59: HELD', 'Control Plane #87: HELD', 'Constructor tolerance: NOT AUTHORIZED', 'Ed25519 #26/#34: HELD', 'V09: SEPARATE',
         'Tier 1 final qualification: DEFERRED, NOT WAIVED', 'Publication, release, production: HOLD',
         'DEF-OBS-TOL-OVERFLOW-1 remains a separate unresolved defect and is outside every scope here']
ADOPT = dict(status='CONFLICT',
    evidence='OCS records pin different constitutional revisions (Registry plans and R1 plan: 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b; the final-three directive: 230c0aff1c2d1e054652cfc1be175147260b8aae); the Architect directives of 2026-10-29 name dcdbe3b76843d672ca3cfb1f000124ecd78ed03c as the prompt-engineering policy revision, and its Orchestrator Prompt Engineering Addendum states it is not adopted by publication or merge. No formal adoption record selecting dcdbe3b for OCS was found; existing project adoption records are preserved unchanged. Architect decision D7 in docs/post-migration/04-architect-decision-packet-2026-10-29.md.')
COMMON_GOV = dict(constitutionalRevision=REV, projectAdoption=ADOPT, complianceAddendumRevision=REV, testingPolicyRevision=REV)

def src(loc, ident, purpose): return dict(location=loc, identity=ident, purpose=purpose)
CP_SRC = [src('cogno-us/cognous-control-plane main', CP_MAIN, 'frozen subject for F3-A and F3-B (merge of PR #97; contains D-06 via #96 and D-07 via #97)'),
          src('cogno-us/cognous-ocs-registry main', REG_MAIN, 'frozen contract source (closeout #78; r08-v8 merge 188e90efc02e857928e857998231473c3f235b16)'),
          src('cogno-us/cognous-ocs-registry docs/family-migration/final-three/03-f3-qualification-expectations-F3A-F3B-2026-10-29.md', f'blob at main {REG_MAIN}', 'builder-written minimum oracle expectations (written before the changes; minimum, never the ceiling)'),
          src('cogno-us/cognous-ocs-registry docs/post-migration/annex/A-f3-source-binding-and-coverage-map-developer-record.md', 'PR #79 head 4c343b52a0baffde8631e3867cfbe55134fa50f4 (not yet on main)', 'factual map of developer tests and source hashes; developer evidence, not a verdict')]

D_BIND = {
 'CA04': 'Define and run the qualifier\'s own scope and oracle; the builder expectations are a minimum and are not the test selection; no developer test substitutes for a qualification case.',
 'CA06': 'Keep every adverse result with its original raw output (including the 41 known environmental baseline failures and their causes); never rescore, relabel or edit a frozen oracle to obtain green.',
 'CA07': 'Qualify only the frozen heads in Inputs; evidence from the pre-merge branch heads 5ffd0ae, 4adb84b, b8fbe95, a1de48c, 55488d2 is not transferred to main without a recorded identity argument.',
 'CA08': 'Report delivery state precisely (merged, developer-tested, independently qualified or not); green CI, documents and PR counts are never reported as qualification.',
 'CA23': 'The qualifier must be separate from the implementation builder (Lead Builder and its workers); report contribution, inspection, qualification, certification and integration as separate roles; a builder-spawned reviewer is not independent.'}

def d_packet(pkg, title, objective, subject_note, success, negatives, evidence, notrun, extra_sources, sources_boundary):
    return dict(schemaVersion='cognous-orchestrator-assignment-v1',
      identity=dict(workPackage=pkg, role='independent_qualification_owner', primaryArchetype='D',
        archetypeMeaning='Apply an independently controlled oracle/protocol to frozen exact subjects; retain raw results, adverse findings and qualified verdict boundaries. (Architect/orchestrator compiles and dispatches; owner NOT DESIGNATED.)',
        repository='cogno-us/cognous-control-plane', baseCommitSha=CP_MAIN, currentHeadSha=CP_MAIN),
      authority=dict(objective=objective,
        sourceDecision='Architect directive OCS-REG-R1-NEXT (2026-10-29) section 5: assignment prepared only; F3 execution NOT authorized by that directive; independent owner not yet designated (F3: READY FOR ASSIGNMENT / OWNER BLOCKED).',
        allowedActions=['Read the frozen subject and the listed sources', 'Define and execute the qualifier\'s own oracle against the exact frozen heads in a clean environment', 'Run the subject\'s existing tests as evidence-gathering where the qualifier selects them', 'Record PASS / FAIL / BLOCKED per criterion with raw outputs', 'Publish the report to the designated location'],
        prohibitedActions=['Self-certification or any verdict by the implementation builder', 'Modifying the subject sources, the builder expectations or any frozen oracle to obtain green', 'Paid or real-environment execution without specific authorization', 'Network or external effects, publication, release, deployment, merging', 'Qualifying a revision other than the frozen heads', 'Changing any standing hold'] + HOLDS,
        paidExecution=dict(authorized=False, maximumUsd=0), mergeAuthorized=False, deploymentAuthorized=False),
      ownership=dict(designatedWriter='independent qualification owner (NOT DESIGNATED; must be separate from the Lead Builder and implementation workers)',
        writablePaths=['The qualifier\'s own report location only (to be named by the Architect at designation)'],
        protectedPaths=['Every path in cogno-us/cognous-control-plane and cogno-us/cognous-ocs-registry (read-only subjects)', 'docs/family-migration/final-three/03-f3-qualification-expectations-F3A-F3B-2026-10-29.md (builder minimum expectations; additions go in the qualifier\'s own report)'] ),
      inputs=dict(projectPlan='docs/plans/REGISTRY-R1-POST19-CONSOLIDATION-PLAN-v1.0.md; docs/family-migration/IMPLEMENTATION-CLOSEOUT-2026-10-29.md; docs/post-migration/01-f3a-f3b-independent-qualification-handoff-2026-10-29.md (Registry PR #79)',
        frozenSources=CP_SRC + extra_sources,
        interfacesAndDependencies=['Registry pins: the F3 subjects (test_final3_*, the D-06 binding files, the D-07 successor tests) run under OCS_REGISTRY_PIN_DIR = a Registry checkout at a40fe755e2384a99c37016fa9ad59396f1835900 (code-identical to Registry main outside documentation) with OCS_REQUIRE_REGISTRY_PIN=1; the whole Control Plane suite needs the workflow\'s five pins (6f600ab, 6c3e5e4, 42a6663, b73c59e, a40fe755) and test_v02 needs 943ab18; Control Plane tests hard-code accepted pins; pin decision is Architect decision D3', 'Python >=3.11 (Control Plane CI runs 3.11 and 3.12), pydantic>=2.12, PyNaCl', subject_note],
        knownBaselineFailures=['41 Control Plane failures identical to docs/evidence/final3-consumers/baseline-failures.txt: test_microsoft_agt 14, test_scan6_agt_exact 16, test_wave7_agt_binding_equality 5 (pytest-asyncio absent); test_v02_claim_policy_binding 6 (older Registry pin); 2 collection errors for 6f600ab-pinned files in single-pin runs']),
      acceptance=dict(riskTier='T4', riskRationale='Prescribed independent qualification of a governance-critical, authority-bearing boundary at a frozen candidate; read-only against the subject, no production effect.',
        successConditions=success, negativeControls=negatives,
        newEvidence=evidence, reusedEvidence=[dict(source=s, applicability=a) for s, a in [(src('docs/evidence/ in cogno-us/cognous-control-plane main', CP_MAIN, 'developer evidence'), 'Context and original failing outputs only; produced at pre-merge heads, not transferable as qualification (CA07)')]],
        notRun=notrun,
        qualificationBoundary=sources_boundary),
      delivery=dict(artifacts=['Qualification report with per-criterion PASS/FAIL/BLOCKED, the exact commands, environment, raw outputs and original failures retained', 'Source-to-observation traceability table', 'List of exclusions, skips and untested expectations'],
        reportFields=['Frozen heads qualified (exact SHAs)', 'Oracle used (qualifier-defined) and how it extends the builder expectations', 'Per-criterion verdict with raw evidence reference', 'Adverse findings and original failures (unaltered)', 'Verdict boundary: what this does and does not qualify', 'Cost and execution budget used'],
        pullRequest='none (qualifier\'s report location to be designated)'),
      boundaries=dict(stopConditions=['Independence cannot be established: report "not independently qualified"', 'Subject head differs from the frozen head', 'Evidence of a real bypass or widened authority: stop and report immediately with the raw evidence', 'Any step needing paid or external execution not authorized', 'Any need to alter the subject or a frozen oracle'],
        escalationOwner='Architect (Cognous)', outOfScope=['Implementation, refactoring or fixes', 'DEF-OBS-TOL-OVERFLOW-1', 'Registry #58/#59, Control Plane #87, constructor tolerance, Ed25519 #26/#34, V09', 'Release, publication, production'] ),
      governance=dict(**COMMON_GOV, archetypeSource='ENGINEERING_COMPLIANCE_ADDENDUM.md §3 Archetype D at '+REV, clauses=clauses('D', D_BIND)))

# F3-A
CP_PATHS_A = 'src/agent_control_plane/effective_configuration_binding.py, registry_governed_lifecycle.py, registry_governed_policy.py, registry_f4_age_governance.py, registry_f5_class_age_governance.py, registry_f5_class_unreadable_governance.py, registry_final3_governance.py, registry_effective_policy.py'
F3A = d_packet('OCS-F3A-QUAL', 'F3-A', 
  'Independently qualify the persisted effective-configuration binding (D-06) at the frozen heads: original and changed configurations, restart persistence, unknown/missing versions, legacy cutoff, wrong-scope and mismatched-family refusal, effective-policy and constructor-scalar binding, claim (pin export) and execution revalidation, negative evidence and source identity; issue a bounded verdict.',
  'Subject files (Control Plane main): ' + CP_PATHS_A,
  ['Same configuration across restart and a separate process is accepted; every member perturbed independently (each F4 scalar, each other scalar incl. constructor tolerance, ObservationPolicy max age, ObservationPolicy tolerance, present vs explicitly absent, host profile digest, effective profile digest, scope, family set, each family contract version, schema revision, effective-policy digest) changes the digest and makes BOTH execute and pin-export refuse with authorization_binding_changed and a durable EffectTimeRefusal, destination untouched (builder expectation F3-A 1)',
   'Unknown binding version, malformed member, digest != recomputation, wrong types (bool, float, str number, negative, huge) refuse (F3-A 2)',
   'Missing member refuses unless the explicit legacy_cutoff rule applies; cutoff default 0; no wildcard accepted; negative/non-int/bool/huge cutoff handled by an explicit documented rule (F3-A 3)',
   'A store generated by the unchanged prior binary executes below the cutoff as legacy and refuses at or past it; approval_commitment byte-identical (F3-A 4)',
   'catalogue_digest, approval_commitment, RuntimeAuthorityProfile dump, published schemas, reason vocabulary, EffectivePolicySnapshot.identity_digest and r08-v1..v7 identities byte-identical to baseline; legacy reader fails closed on new records (F3-A 5)',
   'The binding confers no authority and removes no other refusal (F3-A 6); recovery/crash-point and failed-attempt behavior (F3-A 7); qualifier-constructed negative controls (F3-A 8); limits stated honestly and any anti-rollback claim fails (F3-A 9)',
   'PASS requires every criterion met with raw evidence at the frozen heads; FAIL on any real bypass, widened authority or changed commitment; BLOCKED when independence, environment or the pin cannot be established; each criterion is reported separately'],
  ['Member-order shuffling, duplicate JSON keys, extra unknown members inside effective_configuration', 'Replayed member copied from another decision or scope; downgrade by deleting the member (record at/past cutoff)', 'Every single-member perturbation tested for BOTH execute and pin-export (the builder tests do not drive pin-export for every member)', 'More than one crash point around append_decision; a hold persists no binding', 'A claim of anti-rollback or tamper protection in any document must fail the criterion'],
  [dict(test='Qualifier-defined oracle for criteria 1-9 above', purpose='Independent verification at the frozen heads', result='PLANNED'),
   dict(test='Read-only source inspection of the F3-A subject files against the Registry freeze record section 4-5', purpose='Source-to-observation traceability', result='PLANNED')],
  [dict(test='Any run of the builder\'s mutation harness as qualification', reason='Developer evidence only'), dict(test='Paid or external execution', reason='Not authorized (maximumUsd 0)'), dict(test='Full Tier 1 campaign', reason='DEFERRED, NOT WAIVED; separate gate')],
  [src('cogno-us/cognous-control-plane docs/effective-configuration-binding.md', f'blob at main {CP_MAIN}', 'D-06 design, limits section 10')],
  'Qualifies only the persisted effective-configuration binding of the frozen Control Plane head against the stated expectations and the qualifier\'s oracle; it is not Tier 1, not a security clearance and not release acceptance. Unsigned store, no anti-rollback, legacy_cutoff provenance, mixed-fleet legacy writers and masked host changes are documented limits, not guarantees.')
# F3-B
F3B = d_packet('OCS-F3B-QUAL', 'F3-B',
  'Independently qualify the protected temporal-enforcement correction (D-07) at the frozen heads: purpose-observation deadline anchoring, cached-purpose observations, delayed dispatch, clock and deadline boundaries, unchanged grant/identity/mandate behavior, historical predecessor evidence, refusal outcomes and absence of unauthorized external effects; issue a bounded verdict.',
  'Subject file: src/agent_control_plane/runtime_authority.py (sha256 prefix 45a27db8695f; one hunk at lines 404-415 vs the predecessor a4b4ac36 at CP 061a986) plus byte-identity of bounded.py, freshness.py, policy_binding.py, rule_revision.py, reversibility.py, holder_inventory.py; D-07 entered main only through PR #97 (merge 739efe7), not #95 (fb9c7e0 merged into the #94 feature branch)',
  ['At the predecessor (CP 061a986): anchor_deadline_to_inputs=True, no PolicyBinding, class bound 30 s, purpose observation accepted at age 30 s with a 29 s stall is dispatched (age 59 s); at the frozen head the same fixture and the cached-purpose snapshot are refused by the existing check_expired_before_dispatch; strict boundary at the remaining-bound edge, one second inside and outside (F3-B 1)',
   'Grant status, identity and mandate anchoring unchanged; flag False byte-identical to before; reversible/irreversible classes; post-reversal window (F3-B 2)',
   'Outage extensions never raise a narrowed ceiling; the cached-snapshot bound is the recorded bound (F3-B 3)',
   'The correction only adds a min to the deadline: for any input the new deadline <= the old, and anything accepted by the new code is accepted by the old (property-style, not only the 124-case builder grid) (F3-B 4)',
   'No new reason code; profile dump, approval_commitment, catalogue_digest, persisted decision schema and refusal evidence fields unchanged; monotonic and wall-clock-stepped-back guards unchanged (F3-B 5)',
   'The destination apply is never called after the deadline refusal (F3-B 6); the only protected-file change is the authorized one with the new hash recorded and the superseded characterization tests mapped to successors citing the original results (F3-B 7); profile-bearing families and policy_binding_unsupported unchanged (F3-B 8)',
   'PASS requires every criterion met with raw evidence at the frozen heads; FAIL on any dispatch past a bound or any new permission; BLOCKED when independence or environment cannot be established; each criterion reported separately'],
  ['Wall-clock stepped back and monotonic-clock cases', 'Exact-ceiling observation (authorized but refused at dispatch) and one-second-either-side stalls', 'Extension values 0/20/100 with the anchor applied on both live and cached paths (builder tests cover the purpose observation only)', 'Build without D-07 must fail the anchor cases loudly (the guard test points at D-07)', 'Property test that new deadline <= old deadline over generated inputs'],
  [dict(test='Qualifier-defined oracle for criteria 1-8 above', purpose='Independent verification at the frozen heads', result='PLANNED'),
   dict(test='Differential run of predecessor (CP 061a986) vs frozen head on the qualifier fixtures', purpose='Reproduce the original defect and prove the correction', result='PLANNED')],
  [dict(test='Any run of the builder\'s 64-mutant consumer harness or the D-07 mutation harness as qualification', reason='Developer evidence only'), dict(test='Paid or external execution', reason='Not authorized (maximumUsd 0)'), dict(test='Full Tier 1 campaign', reason='DEFERRED, NOT WAIVED; separate gate')],
  [src('cogno-us/cognous-control-plane docs/d07-purpose-observation-anchor-correction.md', f'blob at main {CP_MAIN}', 'D-07 design; the Before comment quotation in it is not verbatim (known documentation defect)'),
   src('cogno-us/cognous-control-plane tests/fixtures/d07_predecessor_outcomes_061a986.json', f'blob at main {CP_MAIN}', 'recorded predecessor outcomes (original evidence)')],
  'Qualifies only the D-07 purpose-observation deadline anchoring in the frozen runtime_authority.py and the unchanged-bytes pin of the other protected evaluators; it is not Tier 1, not a security clearance and not release acceptance. The anchor guarantee depends on D-07 being present; DEF-OBS-TOL-OVERFLOW-1 is out of scope.')
# R1-NEXT (archetype A) assignment record
A_BIND = {
 'CA01': 'Reuse the existing Registry r08-v8 unified engine and the Control Plane composition mechanisms; propose no new abstraction where an existing shared helper is not demonstrably present.',
 'CA03': 'Freeze exact source identities and interfaces (Registry main, Control Plane main, PR heads) before proposing any implementation change.',
 'CA04': 'Prepare independent F3 expectations and assignments before any acceptance claim; the Lead Builder issues no verdict.',
 'CA18': 'Preserve all mandatory governance and security invariants (four mandatory boundaries, revocation, authentication, held-state checks).',
 'CA21': 'Preserve external semantics, historical signatures, approval commitments, persisted bindings and compatibility.'}
NEXT = dict(schemaVersion='cognous-orchestrator-assignment-v1',
  identity=dict(workPackage='OCS-REG-R1-NEXT', role='implementation_owner', primaryArchetype='A',
    archetypeMeaning='Inventory related items; reconcile shared invariants, interfaces, versioning, failure semantics; select one canonical writer; freeze the common contract before migration. (Here: reconcile existing architectural evidence, frozen interfaces, acceptance prerequisites and dependencies before authorizing implementation.)',
    repository='cogno-us/cognous-ocs-registry', baseCommitSha=REG_MAIN, targetPr=79),
  authority=dict(objective='Close R1-START planning, reconcile R1-E (#76), prepare independent F3-A/F3-B assignments, support the Control Plane duplication estimate with a bounded source crosswalk, and produce a decision-ready R1 proposal. Documentation and planning only.',
    sourceDecision='Architect directive "R1 NEXT WORK PACKAGE", 2026-10-29',
    allowedActions=['Inspect current heads and PRs', 'Review R1-START deliverables and repair documentation inconsistencies (new text; historical evidence not rewritten)', 'Prepare PR #79 for Architect review', 'Reconcile R1-E #76 and recommend one disposition', 'Prepare F3-A/F3-B assignments for an independent owner', 'Produce a decision-ready R1 proposal'],
    prohibitedActions=['Production-code refactoring', 'New Registry contract versions', 'Changes to protected evaluators', 'Independent qualification self-certification', 'Paid tests or external effects', 'Automatic PR merges', 'Release or deployment'] + HOLDS,
    paidExecution=dict(authorized=False, maximumUsd=0), mergeAuthorized=False, deploymentAuthorized=False),
  ownership=dict(designatedWriter='Lead Builder (one designated writer for canonical architectural records)',
    writablePaths=['cogno-us/cognous-ocs-registry: docs/post-migration/ (PR #79 branch r1-start-post-migration-readiness)'],
    protectedPaths=['All source, tests, schemas, vectors, workflows and frozen contracts in both repositories', 'docs/family-migration/final-three/ and other historical evidence (add new text only)', 'cogno-us/cognous-open-control-stack-ergonomics (read-only)'],
    parallelWorkers=[dict(role='read-only reviewers/inspectors (non-overlapping output files only)', writablePaths=['scratchpad output files only'])]),
  inputs=dict(projectPlan='docs/plans/REGISTRY-R1-POST19-CONSOLIDATION-PLAN-v1.0.md (Registry main); docs/post-migration/ (PR #79)',
    frozenSources=[src('cogno-us/cognous-ocs-registry main', REG_MAIN, 'closeout merge #78'), src('cogno-us/cognous-control-plane main', CP_MAIN, 'PR #97 merge'),
      src('cogno-us/cognous-ocs-registry PR #79', '4c343b52a0baffde8631e3867cfbe55134fa50f4', 'R1-START deliverables'),
      src('cogno-us/cognous-ocs-registry PR #76', '138e222998345e021c7f5adf68bf2d2aa719c8a9', 'R1-E addendum (open, unmerged)'),
      src('cogno-us/cognous-open-control-stack-ergonomics main', 'bea582b378af1b0d6854ffe3a1de40df5ad7a0ab', 'read-only ergonomics layer')],
    interfacesAndDependencies=['Registry r08-v1..v8 frozen contracts and signature domains', 'Control Plane protected evaluators (byte-pinned)', 'Control Plane tests accept Registry pin a40fe755 only'],
    knownBaselineFailures=['41 environmental Control Plane failures (baseline-failures.txt)']),
  acceptance=dict(riskTier='T0', riskRationale='Documentation, inspection and planning only; no source, test, schema or workflow change; no reachable production effect.',
    successConditions=['R1-START documentation reconciled with exact-head review and CI Scope Declaration on #79', 'R1-E #76 reconciled with one disposition or a recorded blocker', 'F3-A/F3-B assignments ready for a designated independent owner (owner status stated)', 'Control Plane duplication estimate supported by a bounded source crosswalk or corrected', 'Candidates ranked by actual value, complexity and risk', 'No claim promoted beyond its evidence'],
    negativeControls=['No statement of qualification, acceptance, security clearance or release readiness', 'No savings stated as measured unless traceable to a script or output', 'No change to any file outside docs/post-migration/'],
    newEvidence=[dict(test='Exact-head documentation review of PR #79 by an independent reviewer worker', purpose='Source fidelity of pins, clauses and figures', result='PLANNED'), dict(test='Schema validation of the three assignment packets against orchestrator-assignment-v1.schema.json', purpose='Packet validity', result='PLANNED')],
    reusedEvidence=[dict(source=src('docs/post-migration/annex in PR #79', '4c343b52a0baffde8631e3867cfbe55134fa50f4', 'read-only worker inventories'), applicability='Static measurements at the pinned heads; re-derived or independently reviewed where used')],
    notRun=[dict(test='Full regression suites, F3, Tier 1', reason='Not authorized for this work package; documentation only'), dict(test='Mutation testing', reason='No code change')],
    qualificationBoundary='Developer/inspection record only; not independent qualification.'),
  delivery=dict(artifacts=['PR #79 (updated)', 'docs/post-migration/assignments/ (three schema-validated packets)', 'R1-E reconciliation record', 'Control Plane crosswalk'], reportFields=['Current exact source heads', 'PR #79 disposition', 'R1-E #76 disposition', 'F3 readiness and owner status', 'Top Control Plane simplification opportunities', 'Recommended bounded R1 sequence', 'PR links', 'Remaining Architect decisions'], pullRequest='https://github.com/cogno-us/cognous-ocs-registry/pull/79'),
  boundaries=dict(stopConditions=['A candidate needs a protected evaluator, persisted schema, approval preimage or frozen byte change', 'A claim cannot be supported by source', 'A required check would have to be bypassed'], escalationOwner='Architect (Cognous)', outOfScope=['Production-code refactoring', 'F3 execution', 'Ergonomics implementation', 'DEF-OBS-TOL-OVERFLOW-1']),
  governance=dict(**COMMON_GOV, archetypeSource='ENGINEERING_COMPLIANCE_ADDENDUM.md §3 Archetype A at '+REV, clauses=clauses('A', A_BIND)))

v = Draft202012Validator(schema)
OUT.mkdir(parents=True, exist_ok=True)
for name, pk in (('R1-NEXT', NEXT), ('F3-A', F3A), ('F3-B', F3B)):
    errs = sorted(v.iter_errors(pk), key=lambda e: list(e.path))
    print(name, 'VALID' if not errs else [ (list(e.path), e.message[:120]) for e in errs])
    if errs: sys.exit(1)
    (OUT/f'{name}.assignment.json').write_text(json.dumps(pk, indent=2, ensure_ascii=False)+'\n')
