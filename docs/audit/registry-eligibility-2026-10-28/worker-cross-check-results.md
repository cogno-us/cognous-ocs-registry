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
| W1-007 | ADOPTED-AS-UNRESOLVED | Blind J1a rated the structural caps eligible (narrow-only, low value); D1/J1c retain. Genuine split, so the merged rule LR-RUNTIME-ADMISSION-SIZE-BUDGETS is UNRESOLVED with a blocking question. |
| W1-008 | ADOPTED-AS-UNRESOLVED | Same admission-budget question as W1-007 (J1b eligible vs. first-pass retain). |
| W1-010 | ADOPTED-AS-UNRESOLVED | J1c retain vs J1a/J1b eligible; carried by the merged UNRESOLVED admission-budget rule. |
| W1-011 | ADOPTED-AS-UNRESOLVED | As W1-010. |
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
| RG-C-011 | ADOPTED-WITH-RETAINED-DISAGREEMENT | REGISTRY-ELIGIBLE, MEDIUM. A rank-raising-only overlay is monotone and reversibility.py already forces irreversible for several classes. First-pass workers treated it as a producer assertion of fact. Depends on AUD-D06. |
| RG-D-012 | ADOPTED-AS-UNRESOLVED | Carries the minimum-redaction-floor ownership question (AUD-D05). |
| RG-D-021 | REJECTED | Retained PROVIDER-OR-HOST-OWNED: no hard-coded value exists; the value lives in the hub reference_profiles. Reviewer J3b disagrees (retained disagreement). |
| RG-F11-REDACTION-DEFAULTS | ADOPTED-AS-UNRESOLVED | Caller-owned presentation (H1) vs an OR-floor (J3b): ownership of a minimum-redaction floor is a privacy-owner decision (AUD-D05). |
| RG-F7-DEDUPE | ADOPTED-AS-UNRESOLVED | G0 C-022 stands: horizon/TTL/escalation deadline ownership is open. |

- J1_blind_reaudit: rows=178, risk_selected=148, random=30, disagreements_with_final=16, label_only=9, adjudicated_to_unresolved=4, no_change_parameter_already_counted=3
- J3a_out_of_scope_claims: claims=35, confirmed=30, falsified=5, falsified_toward_eligible=0
- J3b_host_caller_claims: claims=40, confirmed=33, falsified=7, adopted=4, rejected=1, to_unresolved=3

