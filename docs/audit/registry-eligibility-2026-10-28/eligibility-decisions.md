# Registry eligibility decisions (proposals for Architect approval)

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

Every canonical rule that is governed, eligible, unresolved or blocked is listed with its evidence. Rules that are retained in code, owned by a caller/issuer/provider/host, or out of scope are listed in `rule-catalogue.json` with the reason (`disposition_basis`).

## Registry-governed (implemented and integrated; not independently accepted)

### LR-F1D-TARGET-POLICY — Runtime LocalExecutionPolicy target scope: allowed_target_prefixes + target_match (Registry-governed via r08-v4 f1abcd, M3; one joint containment relation)

- Disposition: **REGISTRY-GOVERNED** (basis: LEAD-OVERRIDE: Merged governed pair (pass 2).); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 2; migration status IMPLEMENTED; layers {'enforcement_integrated': 'YES', 'independently_accepted': 'NO', 'registry_represented': 'YES'}; proposed wave: COMPLETED-IMPLEMENTED: M3 (Registry PR #56 merge b7e6a173; Runtime PR #153 merge f7a55e2a).
- Configuration owner: Host/caller policy; Host/caller policy; Registry may only narrow by accepted-set containment; Host/caller policy; Registry may only narrow via signed selection; Host/caller policy; Registry may only select stricter mode (exact>segment>legacy-prefix)
- Value / domain: allowed_target_prefixes: caller-owned LocalExecutionPolicy field; no Registry slot
- Narrowing semantics: Joint containment over (prefix list, match mode) pairs (v4_f1abcd.py:7-14,63-93): the Registry pair is accepted only if every host-supplied (list, mode) entry is contained in a Registry entry under the sound accepted-set rule; effective policy never exceeds the host policy. Absent or invalid Registry input never adds …
- Existing Registry coverage: FULL for represented+integrated (r08-v4 f1abcd composer; Runtime effect-time containment guard); NOT independently accepted. Stale text 'Registry: no slot' and 'containment order undefined' are superseded.
- Historical rows: W1-033; G0 groups: RG-F1D-TARGET-MATCH, RG-F1D-TARGET-PREFIXES; evidence: docs/r08-v4-contract.md s1-4; safe_executor.py:359-408; registry_f1abcd_narrowing.py:48; registry_selection_authority.py:1706; rt safe_executor.py:343,359-372,393-394; registry v4_f1abcd.py:60-95,3 modes; backlog:75; rt safe_executor.py:358-408; registry v4_f…

### RG-F1A-ALLOW-SETS-FIVE — The five allow-sets (actions, adapters, units, institutions, authority domains): Registry f1ab record, Runtime policy fields, effect-time containment guard, narrowing adapter

- Disposition: **REGISTRY-GOVERNED** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ALREADY-GOVERNED; confidence MEDIUM.
- Parameters: 5; migration status IMPLEMENTED; layers {'enforcement_integrated': 'YES', 'independently_accepted': 'NO', 'registry_represented': 'YES'}; proposed wave: COMPLETED-IMPLEMENTED: r08-v2 f1ab (Registry PR #29 merge f618cdf5); Runtime effect-time guard (registry_selection_authority.py).
- Configuration owner: Host/caller policy narrowed by Registry operator; Registry operator (record author) via signed selection; caller policy is host/Control Plane owned; Registry operator (signed record) narrowing host/caller LocalExecutionPolicy
- Value / domain: Three sorted, duplicate-free token lists, <=256 entries, entry 1..128 chars, [] = deny-all, carried in authenticated r08-v2 f1ab record
- Narrowing semantics: Order: set inclusion. Result subset of both inputs. Floor: Runtime baseline/caller policy. Absent key -> field_missing (never implicit allow/deny); malformed -> typed refusal, required scope returns no policy and never caller policy
- Existing Registry coverage: ['FULL: represented r08-v2 f1ab and integrated at Runtime effect-time containment guard (also inside f1abc/f1abcd composites); check order/evaluator remains code']
- Historical rows: W1-040; G0 groups: RG-F1A-ALLOW-SETS-FIVE; evidence: registry v2_f1ab.py:78-97; rt registry_selection_authority.py:1591-1625; safe_executor.py:410-424; builder tests only (V09 independent review OPEN); safe_executor.py:417-424; registry_selection_authority.py:1591; v2_f1ab.py:78

### RG-F1C-MAX-AMOUNT — Runtime LocalExecutionPolicy max_amount ceiling (host policy; Registry-governed via r08-v3 f1abc, M2)

- Disposition: **REGISTRY-GOVERNED** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 1; migration status IMPLEMENTED; layers {'enforcement_integrated': 'YES', 'independently_accepted': 'NO', 'registry_represented': 'YES'}; proposed wave: COMPLETED-IMPLEMENTED: M2 (Registry PR #54 merge ba98dd26; Runtime PR #151 merge 99f5f053, PR #152 merge dabaa770).
- Configuration owner: Host/caller policy; Host/caller policy; Registry may only lower; Host/caller policy; Registry operator may only lower via min()
- Value / domain: max_amount: numeric ceiling, caller-owned LocalExecutionPolicy field; no Registry slot
- Narrowing semantics: effective ceiling = min(host LocalExecutionPolicy ceiling, Registry ceiling), exact int 0..2^53; bool, float and NaN input are refused (r08-v3 f1abc). Absent Registry input keeps the host value.
- Existing Registry coverage: FULL for represented+integrated (r08-v3 f1abc composer; Runtime effect-time guard); NOT independently accepted. Earlier 'Registry: no slot' and 'NaN undecided' descriptions are superseded by merged M2.
- Historical rows: W1-041; G0 groups: RG-F1C-MAX-AMOUNT; evidence: docs/r08-v3-contract.md s3-4; safe_executor.py:425; registry_selection_authority.py:1678; rt safe_executor.py:262-276,425-426; registry v3_f1abc.py; docs/family-migration/m2/01-migration-backlog.md:70-72 (M2 implemented, 0 accepted)

### RG-F1C-MAX-EFFECTS — Runtime LocalExecutionPolicy max_effects ceiling (host policy; Registry-governed via r08-v3 f1abc, M2)

- Disposition: **REGISTRY-GOVERNED** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 1; migration status IMPLEMENTED; layers {'enforcement_integrated': 'YES', 'independently_accepted': 'NO', 'registry_represented': 'YES'}; proposed wave: COMPLETED-IMPLEMENTED: M2 (Registry PR #54 merge ba98dd26; Runtime PR #151 merge 99f5f053, PR #152 merge dabaa770).
- Configuration owner: Host/caller policy; Host/caller policy; Registry may only lower; Host/caller policy; Registry may only lower via min()
- Value / domain: max_effects: numeric ceiling, caller-owned LocalExecutionPolicy field; no Registry slot
- Narrowing semantics: effective ceiling = min(host LocalExecutionPolicy ceiling, Registry ceiling), exact int 0..2^53-1 (r08-v3 f1abc). Absent Registry input keeps the host value.
- Existing Registry coverage: FULL for represented+integrated (r08-v3 f1abc composer; Runtime effect-time guard); NOT independently accepted. Earlier 'Registry: no slot' and 'NaN undecided' descriptions are superseded by merged M2.
- Historical rows: W1-043; G0 groups: RG-F1C-MAX-EFFECTS; evidence: docs/r08-v3-contract.md s3-4; safe_executor.py:429-430; registry_selection_authority.py:1678; rt safe_executor.py:411-412,429-430; registry_selection_authority.py:1632-1680; backlog m2/01-migration-backlog.md:70-72

## Registry-eligible (not yet governed)

### LR-F4-STATUS-APPROVAL-AGE — Authority-input status and approval age bounds (F4: status_max_age_seconds, approval_max_age_seconds)

- Disposition: **REGISTRY-ELIGIBLE** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ALREADY-GOVERNED, ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 2; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'YES'}; proposed wave: M11.
- Configuration owner: Host (BoundedAuthorizationWorkflow ctor); Registry may only lower via min(); Host constructor (cli_run passes none, literal governs); Host constructor value; Host ctor; Registry may only lower via min(); Registry operator (f4 record) narrowing CP host values …
- Value / domain: two exact ints 1..2147483647 in f4 record; min(caller,registry)
- Narrowing semantics: min(); registry>caller no-op; invalid caller refuses; caller 0 stays 0
- Existing Registry coverage: PARTIAL: Registry r08-v2 f4 composer (registry_successor/v2_age_bounds.py) represents both scalars; the Control Plane has no Registry consumer (VERIFIED-BY-LEAD: policy_binding.py enforces only host-copied age_ceilings). Note: when a RuntimeAuthorityProfile is present the grant-status bound is the per-class max_status…
- Historical rows: W6-040, W7-047, W7-050; G0 groups: RG-A-007, RG-C-003, RG-C-004; evidence: bounded.py:1264-1280; v2_age_bounds.py:51 F4_FIELDS; grep CP: no f4 consumer; bounded.py:2434 conflict, :2461 policy use self.status_max_age_seconds; bounded.py:2506; v2_age_bounds.py:51,207; cp bounded.py:1271,1295; _fresh at 2017-2024; no Registry import in…

### LR-F5-CLASS-STATUS-AGE — Per-action-class status age bound (F5 max_status_age_seconds)

- Disposition: **REGISTRY-ELIGIBLE** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ALREADY-GOVERNED, ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 1; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'YES'}; proposed wave: M12.
- Configuration owner: Host (freshness profile), narrowed by Registry; Host RuntimeAuthorityProfile.actions[...]; Registry may only lower via min(); Host freshness profile; extension signers are rule-revision trust; Host profile slot; value narrowed by Registry; Host-authored Runti…
- Value / domain: object action_class->int 1..2147483647, <=256 sorted token keys
- Narrowing semantics: per-class min()
- Existing Registry coverage: PARTIAL: Registry f5 composer represents the per-class map; the Control Plane has no consumer; open question how a narrowed class value enters approval_commitment.
- Blocking decisions: How does a Registry-narrowed class value enter approval_commitment and the approval-side age_ceilings check, given profile.model_dump is the preimage?
- Historical rows: W8-005, W8-043; G0 groups: RG-A-008, RG-C-008, RG-C-019, RG-C-021; evidence: cp runtime_authority.py:131; bounded.py:1366-1373; policy_binding.py:133; freshness.py:67-68 int>=0 default 0; used bounded.py:1369,1395 and policy_binding.py:128; min(host,registry) monotone, floor 0; freshness.py:68; bounded.py:1369,1395; policy_binding.py:…

### NEW:terminal-revocation-marker — Terminal-revocation opt-in enablement (terminal-revocation/0.1 profile off/on)

- Disposition: **REGISTRY-ELIGIBLE** (basis: LEAD-OVERRIDE: Pass 2 (Worker G-01 proposal, verified by the lead): the profile is an opt-in safeguard (runtime_authority.py:182-191,214) with a single consumer (bounded.py:2390-2392). Its only variation is off to on, the same shape as RG-C-010 and RG-C-020. Registry may only force on; absent or a withdrawn record returns the host baseline. MEDIUM confidence.); G0 disposition(s): not in G0 inventory; confidence HIGH.
- Parameters: 1; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'}; proposed wave: not scheduled (same Control Plane profile-consumer family as RG-C-010/RG-C-020; not authorized).
- Configuration owner: Cognous protected code (no config owner)
- Value / domain: 
- Narrowing semantics: Order: on is stricter than off. Registry may only set off to on (a grant observed revoked for (grant_id, revision) is then refused even if the status read says active). Absent: host value. Memory is the control plane's own record store, so a revocation it never observed cannot be remembered.
- Existing Registry coverage: NONE
- Blocking decisions: How does a Registry-forced profile section enter the approval commitment (the AUD-D06 question shared with RG-C-010)?
- Historical rows: W8-013; G0 groups: none; evidence: runtime_authority.py:182-191

### RG-C-009 — Closed enum, default "refuse" (strict). "bounded_tolerance" is accepted only for a class that is not effectively irreversible: bounded.py 2111 refuses an irreve

- Disposition: **REGISTRY-ELIGIBLE** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 1; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'}; proposed wave: M12.
- Configuration owner: Host RuntimeAuthorityProfile.actions[...]; Host action-class profile; Host profile class; Registry may only move bounded_tolerance->refuse
- Value / domain: Closed enum, default "refuse" (strict). "bounded_tolerance" is accepted only for a class that is not effectively irreversible: bounded.py 2111 refuses an irreversible class carrying anything other than "refuse" with action_class_invalid; bo
- Narrowing semantics: Order: refuse is stricter than bounded_tolerance. Registry may only change bounded_tolerance -> refuse. Absent/malformed: keep host value. A Registry value must never set bounded_tolerance.
- Existing Registry coverage: ['NONE: no Registry slot']
- Blocking decisions: As RG-C-008: how a narrowed class enum enters the approval commitment.
- Historical rows: W8-006; G0 groups: RG-C-009; evidence: cp runtime_authority.py:132; bounded.py:2111; runtime_authority.py:132; bounded.py:2111 action_class_invalid; :2189

### RG-C-010 — bool default False, omitted from dumps while False (keeps legacy commitments byte-identical). When True the class holds with holder_inventory_missing until the 

- Disposition: **REGISTRY-ELIGIBLE** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence LOW.
- Parameters: 1; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'}; proposed wave: M12.
- Configuration owner: Host RuntimeAuthorityProfile.actions[...]; Host action-class profile; Host profile class; narrowing only false->true
- Value / domain: bool default False, omitted from dumps while False (keeps legacy commitments byte-identical). When True the class holds with holder_inventory_missing until the profile carries a HolderInventory with at least one holder (runtime_authority.py
- Narrowing semantics: Order: True is stricter than False. Registry may only set False -> True. Absent: host value. The omission-while-False rule means a registry-set True changes the profile dump and approval commitment.
- Existing Registry coverage: ['NONE: no Registry slot']
- Blocking decisions: Is a Registry-forced 'requires_revocation_assurance' meaningful when it holds the class until the host supplies a holder inventory (self-inflicted denial), and does it need profile-commitment handling?
- Historical rows: W8-007; G0 groups: RG-C-010; evidence: cp runtime_authority.py:135; holder_inventory.py (flag consumer not re-read in depth); runtime_authority.py:135,430-433; holder_inventory.py:7-9

### RG-C-011 — Producer assertions on a class: effective_reversibility (reversibility.py 165-181) returns irreversible when undeclared, when reads_protected_data, when counter

- Disposition: **REGISTRY-ELIGIBLE** (basis: LEAD-OVERRIDE: Pass 2 (Worker H C-08, verified): the declared `reversibility` member needs the reversibility/0.1 profile (runtime_authority.py:223-225), which a Registry must never enable. The profile-free monotone lever is the legacy ActionClass.irreversible flag (default True, runtime_authority.py:130; consumers bounded.py:2111, 2189 via effectively_irreversible): a Registry may only force False to True per class. LOW-MEDIUM confidence; shares the approval_commitment dependency (AUD-D06). Retained disagreement: first-pass workers treated the declaration as a producer assertion of fact.); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 1; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'}; proposed wave: M12.
- Configuration owner: Host RuntimeAuthorityProfile.actions[...]; needs the ReversibilityProfile marker (host) else the profile refuses (runtime_authority.py _profiles_compose).; Host/producer (module: 'producer assertions'); Host/producer asserting real action reversibility facts
- Value / domain: Producer assertions on a class: effective_reversibility (reversibility.py 165-181) returns irreversible when undeclared, when reads_protected_data, when counterparty_observable is False, or when a reversible_until window has passed. `irreve
- Narrowing semantics: Order: irreversible=True is stricter than False. Registry may only set ActionClass.irreversible False to True for a class (never enable the reversibility/0.1 profile, never edit reversible_until, reversal_cost, reads_protected_data or counterparty_observable). Absent: host value.
- Existing Registry coverage: ['NONE']
- Historical rows: W8-008; G0 groups: RG-C-011; evidence: cp runtime_authority.py:138-146; reversibility.py:165-181; reversibility.py:34-35 module doc 'reversible_until and reversal_cost are producer assertions'; :165-181

### RG-C-020 — bool default False, omitted from dumps while False. True anchors the dispatch deadline to the earliest of opened+class bound and observed_at+own bound over ever

- Disposition: **REGISTRY-ELIGIBLE** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 1; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'}; proposed wave: M11.
- Configuration owner: Host (freshness profile); Host RuntimeAuthorityProfile.freshness; Host freshness profile
- Value / domain: bool default False, omitted from dumps while False. True anchors the dispatch deadline to the earliest of opened+class bound and observed_at+own bound over every judged input; False permits status age at dispatch up to twice the bound (docs
- Narrowing semantics: True is stricter than False; registry may only set False -> True. Absent: host value.
- Existing Registry coverage: ['NONE: no Registry slot']
- Historical rows: W8-044; G0 groups: RG-C-020; evidence: freshness.py:69-72 bool default False; bounded.py:1416,2105 anchor logic; policy_binding.py:126 requires True when ceilings present; freshness.py:72; policy_binding.py:126; bounded.py:1416,2105

### RG-F4-OBSERVATION-POLICY — Destination observation age/tolerance (300/5 literal in acp run; required ctor field; importer-recorded copy)

- Disposition: **REGISTRY-ELIGIBLE** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 2; migration status NOT-STARTED; layers {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'}; proposed wave: M11.
- Configuration owner: Evaluator in code; values from host ObservationPolicy; Host (BoundedAuthorizationWorkflow constructor); Registry may only lower via min(); Host constructor of BoundedAuthorizationWorkflow; absent policy refuses; Host/CLI wiring (reference host); Host/construc…
- Value / domain: max_age_seconds: required int > 0 (no default; model refuses absence); clock_tolerance_seconds: int >= 0, HARD_CODED_LITERAL default 5. Judged in _reconcile_observation: future if observed_at > max(evaluation_time,_now() under freshness) + 
- Narrowing semantics: Order: smaller max_age_seconds and smaller clock_tolerance_seconds are stricter (more observations rejected). Floor/baseline: the host-constructed value; a Registry value must satisfy min(host, registry) and must never supply a policy where host passed None (absent policy must stay observation_polic
- Existing Registry coverage: ['NONE (see RG-F4-OBSERVATION-POLICY): no Registry slot or CP consumer', 'NONE: F4 payload closed to status/approval scalars (v2_age_bounds F4_FIELDS); no observation slot, no CP consumer', 'NONE: no observation slot in Registry; no CP consumer']
- Historical rows: W6-016, W7-021, W9-001; G0 groups: RG-F4-OBSERVATION-POLICY; evidence: bounded.py:1925-1942; policy None -> observation_policy_missing; bounded.py:411-415; :1925-1942 reconcile use; docs g0-exit-report s60 vs 300; cli_run.py:510; bounded.py:411-415; cp bounded.py:411-415,1899-1925; cli_run.py:510; cp has no registry_successor im…

## Unresolved or blocked

### RG-C-005 — Two ints, HARD_CODED_LITERAL default 60 each; host may override at construction. Unvalidated.

- Disposition: **BLOCKED** (basis: LEAD-OVERRIDE: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'out of scope and not covered'; it does not expressly prohibit them, but nothing authorizes a Registry slot. Narrowing them would be monotone; adoption needs an Architect ruling (AR-1, AR-4).); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 0; migration status NOT-STARTED; layers None; proposed wave: M11.
- Configuration owner: Host constructor of BoundedAuthorizationWorkflow; cli_run passes none.; Host constructor values; Host ctor; Registry may only lower via min()
- Value / domain: Two ints, HARD_CODED_LITERAL default 60 each; host may override at construction. Unvalidated.
- Narrowing semantics: 
- Existing Registry coverage: ['NONE: Registry f4 excludes identity/mandate keys; no CP consumer']
- Blocking decisions: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'out of scope and not covered'; it do…; Is the omission of identity/mandate ages from F4 (DR-CP-AGE-1) a deliberate exclusion or a gap awaiting a new slot?
- Historical rows: W7-040; G0 groups: RG-C-005; evidence: bounded.py:2352-2368 self.identity_max_age_seconds / mandate_max_age_seconds; cp bounded.py:1272-1273,1296-1297,2352,2366; registry v2_age_bounds.py docstring excludes these keys

### RG-C-006 — int, HARD_CODED_LITERAL default 5; unvalidated. Used (a) in _fresh to reject future-dated authority-input observations (bounded.py 2022), (b) as tolerance_secon

- Disposition: **BLOCKED** (basis: LEAD-OVERRIDE: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'out of scope and not covered'; it does not expressly prohibit them, but nothing authorizes a Registry slot. Narrowing them would be monotone; adoption needs an Architect ruling (AR-1, AR-4).); G0 disposition(s): ELIGIBLE-NOT-MIGRATED; confidence MEDIUM.
- Parameters: 0; migration status NOT-STARTED; layers None; proposed wave: M11.
- Configuration owner: Host constructor; Host constructor; cli_run uses the default 5.; Host ctor (clock quality); Registry may only lower via min()
- Value / domain: int, HARD_CODED_LITERAL default 5; unvalidated. Used (a) in _fresh to reject future-dated authority-input observations (bounded.py 2022), (b) as tolerance_seconds passed to record_resolution_check (1332), (c) to reject a recorded_at earlier
- Narrowing semantics: 
- Existing Registry coverage: ['NONE: F4 docstring excludes clock tolerance; no CP consumer']
- Blocking decisions: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'out of scope and not covered'; it do…
- Historical rows: W6-041; G0 groups: RG-C-006; evidence: bounded.py:1275; _fresh (2013-2022) observed > now+tolerance; _record_check passes it; cp bounded.py:1275,1299,1430,2022-2024; all uses fail closed when smaller

### RG-C-024 — Principals funded to fold operations; an authority outside the set holds (merge_authority_unfunded).

- Disposition: **UNRESOLVED** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): RETAIN-IN-CODE; confidence MEDIUM.
- Parameters: 0; migration status NOT-STARTED; layers None; proposed wave: None.
- Configuration owner: Host (funded merge authorities); Host RuntimeAuthorityProfile.merge; Host trust configuration (authority holders)
- Value / domain: Principals funded to fold operations; an authority outside the set holds (merge_authority_unfunded).
- Narrowing semantics: 
- Existing Registry coverage: ['NONE']
- Blocking decisions: Is a host principal allow-list (funded merge authorities) a Registry-narrowable allow-set like F1a, given principal identity namespace and merge profile are host-owned and opt-in?
- Historical rows: W9-023; G0 groups: RG-C-024; evidence: merge.py:50-57 funded_authorities list min_length 1; merge.py:195 non-member held; subset removal would narrow; merge.py:50-57,195

### RG-D-025 — Four regex rules over normalised text: certified, compliant, production-ready, attested (SOC 1/2/3), with separator and fold tables (PRE_FOLD, EXTRA_DASHES).

- Disposition: **UNRESOLVED** (basis: H-WORKER GROUP AUDIT); G0 disposition(s): UNRESOLVED; confidence MEDIUM.
- Parameters: 0; migration status NOT-STARTED; layers None; proposed wave: None.
- Configuration owner: Code; copies exist in hub, verifier and ergonomics repositories per docs/declarative-governance-registry.md.; Hub declarative-governance registry (OCS-DGR-ARCH)
- Value / domain: Four regex rules over normalised text: certified, compliant, production-ready, attested (SOC 1/2/3), with separator and fold tables (PRE_FOLD, EXTRA_DASHES).
- Narrowing semantics: 
- Existing Registry coverage: None
- Blocking decisions: Do wording/claim scanner term lists belong to the hub declarative-governance registry (OCS-DGR-ARCH) or to cognous-ocs-registry, and is lint-only wording in scope of this program?
- Historical rows: none (G0-current rule); G0 groups: RG-D-025; evidence: scanner_analysis_model.py:17-30 RULES/PRE_FOLD; duplicate in verifier scripts/check_claim_boundaries.py; docs/declarative-governance-registry.md:16,27

## Rules whose disposition differs from G0

| Rule | G0 | Audit | Reason (basis) |
|---|---|---|---|
| LR-F1D-TARGET-POLICY | ELIGIBLE-NOT-MIGRATED | REGISTRY-GOVERNED | LEAD-OVERRIDE: Merged governed pair (pass 2). |
| LR-F4-STATUS-APPROVAL-AGE | ALREADY-GOVERNED, ELIGIBLE-NOT-MIGRATED | REGISTRY-ELIGIBLE | H-WORKER GROUP AUDIT |
| LR-F5-CLASS-STATUS-AGE | ALREADY-GOVERNED, ELIGIBLE-NOT-MIGRATED | REGISTRY-ELIGIBLE | H-WORKER GROUP AUDIT |
| LR-MANIFEST-DEFAULT-ACTION | ALREADY-GOVERNED, RETAIN-IN-CODE | CALLER-OR-ISSUER-OWNED | LEAD-OVERRIDE: Workers H2 audited RG-C-031 CALLER-OR-ISSUER-OWNED and RG-D-003 RETAIN-IN-CODE for the same manifest default_action field. Lead merge: the configured value is issue… |
| RG-B-016 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-B-018 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-B-019 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-B-021 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-B-027 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-B-031 | OUT-OF-SCOPE | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: J3a: examples/openshell/provision.py is the documented operator step for the opt-in OpenShell adapter (docs/openshell-adapter.md:93); sandbox sizing and gateway pin… |
| RG-C-005 | ELIGIBLE-NOT-MIGRATED | BLOCKED | LEAD-OVERRIDE: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_… |
| RG-C-006 | ELIGIBLE-NOT-MIGRATED | BLOCKED | LEAD-OVERRIDE: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_… |
| RG-C-012 | RETAIN-IN-CODE | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-C-014 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-C-015 | OUT-OF-SCOPE | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: J3a: OperationIdentityProfile is on the production RuntimeAuthorityProfile path (runtime_authority.py:204,321,435); resolver_id/resolver_version are host labels. |
| RG-C-016 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-C-017 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-C-018 | RETAIN-IN-CODE | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: Cross-check J2: nonce use depends on resolver capability (bounded.py:2090,2214) and no refusal occurs when it is absent; default is already True (freshness.py:65-66… |
| RG-C-024 | RETAIN-IN-CODE | UNRESOLVED | H-WORKER GROUP AUDIT |
| RG-C-026 | RETAIN-IN-CODE | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-C-033 | UNRESOLVED | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-C-034 | RETAIN-IN-CODE | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-C-037 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: J3a: refusal_trends is a documented reporting API with tests, not unused; thresholds are analytics defaults with no authority effect and no enforcement boundary. LO… |
| RG-D-014 | RETAIN-IN-CODE | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-D-015 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-D-018 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-D-020 | ELIGIBLE-NOT-MIGRATED | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-D-021 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | LEAD-OVERRIDE: Pass 2 (Worker E): the hub checker is not wired into any gate and uses a fixture key. Label-only change from PROVIDER-OR-HOST-OWNED; both non-manageable. |
| RG-D-022 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | LEAD-OVERRIDE: Cross-check J2 (LOW): federated_governance.py is synthetic SQLite only and open-control-stack README:155 says synthetic references grant no authority; config is fix… |
| RG-D-026 | OUT-OF-SCOPE | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-D-027 | BLOCKED | OUT-OF-SCOPE | LEAD-OVERRIDE: Pass 2 (Worker H C-03, verified by the lead): TIER_DELAY_CEILING_SECONDS lives in cognous-institutional-governance testing/harness/authority_context.py, whose docst… |
| RG-F11-REDACTION-DEFAULTS | ELIGIBLE-NOT-MIGRATED | CALLER-OR-ISSUER-OWNED | LEAD-OVERRIDE: Pass 2 (Worker E): redaction is an optional export command (cli.py:51-59,155-168), so a minimum floor cannot be enforced; it also trades against evidence verifiabil… |
| RG-F1C-MAX-AMOUNT | ELIGIBLE-NOT-MIGRATED | REGISTRY-GOVERNED | H-WORKER GROUP AUDIT |
| RG-F1C-MAX-EFFECTS | ELIGIBLE-NOT-MIGRATED | REGISTRY-GOVERNED | H-WORKER GROUP AUDIT |
| RG-F6-ACTION-LISTS | UNRESOLVED | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-F7-DEDUPE | UNRESOLVED | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: Pass 2 (Worker E): dispatch gating depends only on the dedupe profile being present (bounded.py:1578-1580); the horizon, TTL and escalation numbers classify attempt… |

