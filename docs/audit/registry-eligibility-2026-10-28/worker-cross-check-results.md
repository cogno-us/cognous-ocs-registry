# Worker evidence and independent cross-check results

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

## First-pass workers

| Shard | Scope | Rows or groups |
|---|---|---|
| A | 43 CONFIGURABLE-CANDIDATE | 43 |
| B | 51 INCIDENTAL-CONDITIONAL | 51 |
| C | 32 UNRESOLVED | 32 |
| D1–D4 | 354 MANDATORY-INVARIANT | 354 |
| F1–F2 | 90 SERIALIZATION-OR-EVIDENCE | 90 |
| G | 50 REFUSAL-OR-REASON-VOCABULARY | 50 |
| H1–H2 | 97 current rule groups (116 source sites) | 97 |
| I1–I3 | Repository coverage (Runtime, Control Plane, Action Manifest, Governed Exchange, nine further OCS repos, Stack Orchestrator) | 35 candidate sites |

## Independent cross-checks (blind second review / falsification)

Raw outputs: `worker-evidence/J*.jsonl`. Disposition of every disagreement: `lead-adjudications.json` (`cross_check_resolutions`).

| Item | Lead resolution | Reason |
|---|---|---|
| W1-007 | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | Blind J1a rated the structural caps eligible (narrow-only, low value); D1/J1c retain. Genuine split, so the merged rule LR-RUNTIME-ADMISSION-SIZE-BUDGETS is UNRESOLVED with a blocking question. |
| W1-008 | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | Same admission-budget question as W1-007 (J1b eligible vs. first-pass retain). |
| W1-010 | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | J1c retain vs J1a/J1b eligible; carried by the merged UNRESOLVED admission-budget rule. |
| W1-011 | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | As W1-010. |
| W1-038 | NO-CHANGE | Evaluator row; its parameter is already counted under governed RG-F1A. Row stays a retained mechanism. |
| W7-004 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Accessor mechanism; a host-owned label does not change the outcome. |
| W9-040 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Redaction-default mechanism row; ownership is carried by the UNRESOLVED parameter rule RG-F11-REDACTION-DEFAULTS. |
| W3-024 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Both labels non-manageable. |
| W4-018 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Both labels non-manageable. |
| W7-025 | NO-CHANGE | The tunable parameter is already carried by existing eligible freshness rules; this row is the check mechanism. |
| W9-003 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | CLI 1 MiB cap is host-owned or retained; neither is manageable. |
| W9-049 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Both labels non-manageable. |
| W6-042 | NO-CHANGE | Parameter already covered by eligible RG-F4-OBSERVATION-POLICY; this row is the presence-requirement mechanism. |
| W7-042 | NO-CHANGE | Parameter already covered by eligible rule RG-C-007 family; this row is a mechanism. |
| W8-098 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Both labels non-manageable. |
| W9-006 | NO-CHANGE (label-only; both the first-pass and the blind label are non-manageable) | Both labels non-manageable. |
| NEW:simulate-fault-injection | ADOPTED | RETAIN-IN-CODE (test hook on live path). |
| NEW:synthetic-refund-intent-profile | ADOPTED | RETAIN-IN-CODE (profile id constant). |
| RG-B-031 | ADOPTED | PROVIDER-OR-HOST-OWNED (operator provisioning step). |
| RG-C-015 | ADOPTED | PROVIDER-OR-HOST-OWNED (host labels). |
| RG-C-037 | ADOPTED | PROVIDER-OR-HOST-OWNED, LOW confidence; either label is non-manageable. |
| NEW:destination-capability-identifiers | ADOPTED | OUT-OF-SCOPE. |
| NEW:policy-config-authority-source-label | ADOPTED | OUT-OF-SCOPE. |
| RG-C-011 | [SUPERSEDED BY PASS 2] ADOPTED-WITH-RETAINED-DISAGREEMENT | REGISTRY-ELIGIBLE, MEDIUM. A rank-raising-only overlay is monotone and reversibility.py already forces irreversible for several classes. First-pass workers treated it as a producer assertion of fact. Depends on AUD-D06. |
| RG-D-012 | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | Carries the minimum-redaction-floor ownership question (AUD-D05). |
| RG-D-021 | [SUPERSEDED BY PASS 2] REJECTED | Retained PROVIDER-OR-HOST-OWNED: no hard-coded value exists; the value lives in the hub reference_profiles. Reviewer J3b disagrees (retained disagreement). |
| RG-F11-REDACTION-DEFAULTS | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | Caller-owned presentation (H1) vs an OR-floor (J3b): ownership of a minimum-redaction floor is a privacy-owner decision (AUD-D05). |
| RG-F7-DEDUPE | [SUPERSEDED BY PASS 2] ADOPTED-AS-UNRESOLVED | G0 C-022 stands: horizon/TTL/escalation deadline ownership is open. |
| NEW:hub-registry-record-profile-vocabulary | ADOPTED | RETAIN-IN-CODE (wire contract). |
| RG-C-005 | ADOPTED | BLOCKED on DR-CP-AGE-1; parameter count corrected to 2. |
| RG-C-006 | ADOPTED | BLOCKED on DR-CP-AGE-1. |
| RG-C-018 | [SUPERSEDED BY PASS 2] ADOPTED | PROVIDER-OR-HOST-OWNED; supersedes the lead's earlier marginal-eligible call. |
| RG-C-021 | ADOPTED (MERGE) | Merged into LR-F5-CLASS-STATUS-AGE; counted once. |
| RG-D-022 | ADOPTED | OUT-OF-SCOPE, LOW confidence. |
| RG-F4-OBSERVATION-POLICY | ADOPTED | Parameter count corrected to 2 (max_age_seconds, clock_tolerance_seconds); disposition unchanged. |
| LR-MANIFEST-DEFAULT-ACTION | NO-CHANGE (label-only) | J2 prefers RETAIN-IN-CODE, lead keeps CALLER-OR-ISSUER-OWNED (manifest-authored data); both non-manageable. J2 confirms G0's ALREADY-GOVERNED for RG-C-031 was wrong. |
| W5-012 | [SUPERSEDED BY PASS 2] ADOPTED (RETAIN-IN-CODE, superseding the pass-1 UNRESOLVED) | Blind reviewer J1b rated the custom action-type sets eligible on the premise that action_type is an open string; pass-2 Workers E and G showed the manifest action_type is a closed 9-member enum (action-manifest models.p… |

- J1_blind_reaudit: rows=178, risk_selected=148, random=30, disagreements_with_final=16, label_only=9, adjudicated_to_unresolved=4, no_change_parameter_already_counted=3
- J3a_out_of_scope_claims: claims=35, confirmed=30, falsified=5, falsified_toward_eligible=0
- J3b_host_caller_claims: claims=40, confirmed=33, falsified=7, adopted=4, rejected=1, to_unresolved=3
- J2_verification_of_governed_eligible_unresolved_blocked: rules_verified=22, confirmed=16, downgraded=5, merged=1, duplicate_site_candidate_review=36 sites: 27 legitimate, 4 merge candidates, 5 double-counts (raw: worker-evidence/J2_sites.json). Site-level duplicates affect source-site counts only, not rule or parameter counts; not re-keyed.

## Pass 2 workers (correction pass, 2026-10-28)

| Worker | Scope | Raw output |
|---|---|---|
| A | Parameter denominator | worker-evidence/pass2/A.jsonl |
| B | G0 group merge/split audit | B.jsonl |
| C | M11 / DR-CP-AGE-1 / AD-07 decision conflict | C.json |
| D | Current implementation truth (represented / integrated / accepted) | D.jsonl |
| E | Configurability challenge (ten disagreements) | E.jsonl |
| F | Missed source coverage | F.json (+ I4.json) |
| G | Retain-in-code challenge | G.jsonl |
| H | Independent reconciliation of the lead's ledgers | H.json |

### Lead adjudication of pass-2 findings

| Worker | Item | Lead decision | Reason |
|---|---|---|---|
| B | RG-F1D-TARGET-PREFIXES + RG-F1D-TARGET-MATCH | ADOPTED (merge) | One joint narrowing relation; governed rules 5 to 4; parameters unchanged. |
| B | W3-062/W3-063 row keys | ADOPTED (re-key) | No count effect. |
| B | RG-B-022 and RG-D-019 split proposals | NOT ADOPTED | MEDIUM-LOW confidence, retain-only effect; the timeouts are carried as host-owned parameters in the parameter ledger instead of creating a rule. Recorded as an alternative partition. |
| B | F1a (five allow-sets), F4 (two ages), F5 merges | JUSTIFIED (kept) | Each shares owner, consumer, relation and record slot. |
| B | max_amount / max_effects kept as two rules | KEPT; sensitivity reported | EITHER_DEFENSIBLE. Rule-level coverage is partition-dependent, so parameters are the headline and rule-level results are reported under three stated partitions. |
| B | RG-C-021 folded into LR-F5 | KEPT | age_ceilings is a host-copied carrier of the F5 value, counted as a site not a parameter (Worker A agrees). |
| E | Structural admission budgets | ADOPTED: RETAIN-IN-CODE (disagreement retained) | See rule override. |
| E | RG-C-011 reversibility | KEPT ELIGIBLE (LOW-MEDIUM) | Re-specified after Worker H C-08 as the profile-free ActionClass.irreversible False-to-True lever; LOW-MEDIUM; gated on AUD-D06. |
| E | RG-D-021 resolver SourceProfile | ADOPTED: OUT-OF-SCOPE | Label only. |
| E | RG-C-018 nonce toggle | KEPT PROVIDER-OR-HOST-OWNED | Resolver silently falls back to a plain read when it lacks nonce support (bounded.py:2208-2223). |
| E | Redaction minimum floor | ADOPTED: CALLER-OR-ISSUER-OWNED | Unresolved in pass 1. |
| E | Dedupe TTL ownership | ADOPTED: PROVIDER-OR-HOST-OWNED | Unresolved in pass 1. |
| E | High-risk/custom action-type sets | ADOPTED: RETAIN-IN-CODE | Factual premise corrected. |
| E | Operation-identity enablement | ADOPTED: PROVIDER-OR-HOST-OWNED | Unresolved in pass 1. |
| E | Funded merge authority lists (RG-C-024) | KEPT UNRESOLVED | The roster is checked only against an unauthenticated, asserted merged_by name and deny-all is inexpressible. Blocking decision: is a roster checked against an unauthenticated name acceptable as a Registry-narrowable control now, or must merger identity be authenticated first? |
| E | Claim-scanner terms (RG-D-025) | KEPT UNRESOLVED on AD-21 | Are claim-scanner term tables in scope of cognous-ocs-registry or only of the hub OCS-DGR-ARCH registry? Term lists already differ between the verifier and hub copies. The hub collateral_evidence_snapshot.py:73-84 vocabulary is not separately catalogued (recorded as an uncatalogued sibling). |
| G | G-01 terminal-revocation enablement | ADOPTED as a newly discovered ELIGIBLE rule (1 parameter) | Verified in source by the lead. Missed by G0 and by pass-1 because the row was classed 'no tunable value'. |
| G | G-02 recovery writer_enabled | ADOPTED: host-owned parameter of the retained rule; not counted separately | Synthetic ledger. |
| G | G-03 anchor LOCK_TIMEOUT_SECONDS | ADOPTED: host-owned parameter carried under RG-B-022 | Class constant; no host-supplied path today. |
| G | G-04 five uncovered sqlite timeout sites | ADOPTED as source sites of NEW:sqlite-busy-timeout | Site coverage gap, no new parameter. |
| G | G-05/G-06 risk-class sets in four copies | ADOPTED as sites of RG-C-032 (RETAIN-IN-CODE) | Zero parameters. |
| G | Remaining 47 of 55 clusters | RETAIN CONFIRMED | No retained numeric limit that a Registry should narrow was found beyond G-01 (cluster-level review, not all 544 rows opened). |
| F | Stack Qualification, Orchestrator, Action Manifest, Governed Exchange, hub and evidence repos | NO NEW ELIGIBLE OR UNRESOLVED PARAMETER | Six new non-eligible catalogue entries added from I4.json; seven candidates are duplicates of existing rules; coverage statements per repo in worker-evidence/pass2/F.json. |
| F | F-07 replay recovery_inspection 0..86400 cap | RECORDED AS LOCKSTEP NOTE | Mirrors RG-B-016: both must change together if either becomes configurable. |
| F | F-01 restart_quorum and F-15 governance_quadratic_scaling | RECORDED AS UNCOUNTED MEMBERS | Under OUT-OF-SCOPE synthetic/reference rules; non-manageable either way. |
| D | Stale descriptions (14) | ADOPTED | Catalogue names and coverage for the F1C/F1D rules corrected; 'Control Plane imports no Registry code' and 'no default_action slot' remain TRUE on main and are not changed; PRs #58/#87 are unmerged and not governed. |
| D | RG-C-019 partly derived from F5 ceilings | CHANGED after Worker H C-02: derived, merged into LR-F5-CLASS-STATUS-AGE | DR-CP-AGE-1 decision 5 defines it as derived from the narrowed F5 ceilings. |
| D | RG-C-005 identity/mandate exclusion wording | ADOPTED (wording) | Worker C: DR-CP-AGE-1 declares these 'out of scope and not covered'; it does not expressly prohibit. BLOCKED stands because nothing authorizes them (AR-4). |
| D | Safety observations | RECORDED | No material safety defect in the merged M2/M3 path or in M11 PRs. |
| A | 19 Registry-manageable parameters | VERIFIED: 9 governed + 10 eligible (before pass-2 additions) | Nine f1abcd members counted once (Runtime LocalExecutionPolicy fields): nine fields in eight narrowing units. After pass 2 the manageable set is 19 parameters in 18 narrowing units. |
| A | RG-D-027 tier ceilings INVARIANT rather than BLOCKED | SUPERSEDED by Worker H C-03: RG-D-027 is OUT-OF-SCOPE | The tier ceilings are a reference-harness constant used only by tests; the pass-1 BLOCKED label and the A dissent both rested on a misquote. |
| A | RG-C-010 and RG-C-011 LOW confidence | KEPT, tiered | Reported as the 'qualified' eligible tier; confirmed-core count excludes them. |

### Worker H independent reconciliation

Worker H recomputed the totals independently from the JSON ledgers as drafted before its challenges (so some figures below predate the lead's fixes; the final figures are in `parameter-reconciliation.md`). Its recomputation reproduced the draft ledger exactly. Raw: `worker-evidence/pass2/H.json`.

| Challenge | Severity | Finding | Lead response |
|---|---|---|---|
| C-01 | MATERIAL | The pass-1 prose was not regenerated after pass 2. reconciliation-report.md still says 439 rules, 5 governed rules, 8 eligible, 19 parameters, 13 of 439 = 3.0%, 13 of 47 configuration-bearing, 11 unresolved-or-blocked, RG-D-021/RG-C-011 pass-1 labels, F1D TAR… | ACCEPTED. All reports regenerated from the final ledgers; the integrity test fails if any rendered file differs from a fresh recomputation. |
| C-02 | MATERIAL | DR-CP-AGE-1 decision 5 (accepted) already assigns the composition of this exact field: max_age_extension_seconds := min(original, min over classes max(0, ceiling_c - narrowed_base_c)) in a later host factory EXT-S3-4. A second, stand-alone Registry slot would… | ACCEPTED. RG-C-019 is derived under DR-CP-AGE-1 decision 5 and merged into LR-F5-CLASS-STATUS-AGE (not an independent parameter). Manageable 19 parameters, 12 rules. |
| C-03 | MATERIAL | The source says the opposite. authority_context.py:12-15: 'Proposed per-tier ceilings ... Owner to confirm: no value is validated or derived from the constitution.' The quoted evidence drops the negation. The constant lives in testing/harness/authority_contex… | ACCEPTED. Misquote corrected; RG-D-027 is OUT-OF-SCOPE (test-harness reference constant). Worker A's dissent withdrawn as unsupported. |
| C-04 | MINOR | The built catalogue has it RETAIN-IN-CODE (category C 'mandatory invariant'). tools/build_parameters.py:54-57 inherits the rule disposition unless an 'overrides' entry exists, and 'additions' do not count as overrides, so the lead's stated classification was … | ACCEPTED. The builder now honours an addition's own eligibility; the lock timeout is PROVIDER-OR-HOST-OWNED. |
| C-05 | MATERIAL | Worker D classified ObservationPolicy.clock_tolerance_seconds as BLOCKED (decision conflict). DR-CP-AGE-1 line 8 lists 'clock_tolerance_seconds' (unqualified) as out of scope and decision 4 calls 'Clock-tolerance behaviour ... untouched and host-owned'; the d… | ACCEPTED IN PART. Explicit adjudication recorded: kept ELIGIBLE as QUALIFIED pending AR-1; sensitivity row added (-1 parameter). |
| C-06 | MATERIAL | These come from the pass-1 Worker H group flags (h['agrees_with_g0']), not from the final g0_group_crosswalk beside them. Final crosswalk: 38 groups differ from G0 (list omits RG-B-031, RG-C-005, RG-C-006, RG-C-015, RG-D-003, RG-F1C-MAX-AMOUNT, RG-F1C-MAX-EFF… | ACCEPTED. Group-level fields in reconciliation.json are now derived from the final g0_group_crosswalk; the pass-1 flags are relabelled; one configuration-bearing denominator (rules with at least one counted parameter) is used in the headline. |
| C-07 | MINOR | The 'disappearing record reverts to host baseline' objection applies to every Registry narrowing (F1a withdrawal returns the caller policy) and is not what distinguishes op-identity (a 3-way protocol selection that changes identity semantics, not a strictness… | ACCEPTED. The eligibility test is stated in the method section: ELIGIBLE = strictness-only, one-way, fail-closed, adds only refusals, with a design gate; BLOCKED = an accepted decision stands in the way; operation-identity enablement fails the test because it… |
| C-08 | MINOR | A Registry cannot force reversibility='irreversible' without the reversibility/0.1 profile: runtime_authority.py (model_validator _profiles_compose) raises 'reversibility values need the reversibility/0.1 profile' for any declared class, and the lead's own te… | ACCEPTED. RG-C-011 re-specified to the profile-free ActionClass.irreversible lever; QUALIFIED; LOW-MEDIUM. |
| C-09 | MINOR | (a) D lists 14 stale items, not 15. (b) Stale text remains in rule-catalogue.json proposed_narrowing_semantics: LR-F1D-TARGET-POLICY 'containment order undefined in Registry; set-intersection composer is NOT valid here'; RG-F1C-MAX-AMOUNT/MAX-EFFECTS 'NaN/inf… | ACCEPTED. Narrowing text rewritten for the three governed rules; the stale-description count is 14. The narrowing-adapter observation is recorded as test-only in the observations. |
| C-10 | MINOR | parameter_count is 0 for 40 rules that own counted parameters (sums to 20, i.e. only the manageable ones); 'configurable'=NO for 14 rules that own counted parameters (LR-MANIFEST-DEFAULT-ACTION, RG-D-001, RG-F7-DEDUPE, RG-D-018 ...), YES for 33 vs 53 rules wi… | ACCEPTED. `parameter_count` in rule-catalogue.json counts Registry-manageable parameters only and `configurable` is the pass-1 rule-level flag; both are documented as such and superseded for denominators by parameter-catalogue.json. |
| C-11 | MINOR | The 81 includes 4 records whose own disposition is RETAIN-IN-CODE with 'no configuration surface' (admission depth, nodes, max_bytes; B-022 lock timeout) and the RG-D-027 harness constant (see C-03). The denominator is therefore not the stated unit; 20/81 = 2… | ACCEPTED. The ledger is relabelled 'candidate configurable parameters' and reports a strict count excluding parameters the audit retains in code, with both percentages. |
| C-12 | MINOR | On pinned Registry main there is no f4t family; v2_age_bounds.py:6 documents that the F4 payload has NO clock_tolerance key. The only representation is unmerged PR #58. The other 105 records use YES/NO; PARTIAL (unmerged) invites miscounting. Not in the 12 re… | ACCEPTED. registry_represented is NO with a note that only unmerged PR #58 represents it. |
| C-13 | MINOR | P-RG-C-020's own note says 'Coupled to F5 ceilings: mandatory True when ceilings present' (policy_binding.py:126-127 emits 'unanchored' otherwise), the same dependency used to mark C-019 COUPLED. Tiering is inconsistent; core count could be 15 and qualified/c… | ACCEPTED. RG-C-020 tiered COUPLED. |
| C-14 | MINOR | Two MANDATORY-INVARIANT historical rows (W8-004 irreversible default/class_id/on_unreadable; W8-031 age<0 refusal evaluator) are mapped to the eligible LR-F5-CLASS-STATUS-AGE with row disposition REGISTRY-ELIGIBLE; W8-013 maps to eligible TR rule but is RETAI… | ACCEPTED. W8-004 and W8-031 re-keyed to LR-F5-CLASS-STATUS-AGE/mechanism (RETAIN-IN-CODE); W8-013 stays the single documented row whose disposition differs from its rule. |

