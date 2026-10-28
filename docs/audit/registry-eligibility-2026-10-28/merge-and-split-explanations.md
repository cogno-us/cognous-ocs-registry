# Merge, split and re-key explanations

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

## Lead merges (many-to-one, explained)

- **LR-F4-STATUS-APPROVAL-AGE** ← RG-A-007, RG-C-003, RG-C-004: Workers H1 and A found RG-A-007 (Registry composer side) and RG-C-003/RG-C-004 (Control Plane consumer-side defaults) are one logical rule viewed from two repositories; the Registry F4 payload carries exactly these two scalars.
- **LR-F5-CLASS-STATUS-AGE** ← RG-A-008, RG-C-008, NEW:class-status-age-bound: H1 found RG-A-008 and RG-C-008 are one rule; Worker D4 independently re-discovered it as NEW:class-status-age-bound (W8-004, W8-031). Merged so it is counted once and is not reported as a newly discovered rule.
- **LR-MANIFEST-DEFAULT-ACTION** ← RG-C-031, RG-D-003: Worker H2: RG-C-031 and RG-D-003 are the same manifest field split across two groups.
- **LR-RUNTIME-ADMISSION-SIZE-BUDGETS** ← RG-B-001, RG-B-002: Same admission guard (safe_executor._admit_plain_data and the max_bytes budget); G0 split them into two retain groups. Merged so the open question is carried once.

## Lead splits (one G0 group divided because the parts have different dispositions)

- **RG-D-001** split from RG-F1C-MAX-AMOUNT (record G0-D-001): Worker H1: OVER-MERGED. A manifest-authored ceiling is issuer data, distinct from the host LocalExecutionPolicy ceiling that M2 governs.
- **RG-D-002** split from RG-F1D-TARGET-PREFIXES (record G0-D-002): Worker H1: OVER-MERGED. Digest-bound manifest content, distinct from the host policy prefixes M3 governs.
- **RG-D-007** split from RG-F11-REDACTION-DEFAULTS (record G0-D-007): Worker H1: three unrelated defaults in three repositories grouped by name only.
- **RG-D-012** split from RG-F11-REDACTION-DEFAULTS (record G0-D-012): Worker H1: see RG-D-007.
- **RG-B-014** split from RG-F6-ACTION-LISTS (record G0-B-014): Worker H2: B-014 is legacy and non-effecting (OUT-OF-SCOPE); D-008 is live manifest content (issuer-owned). Workers A and D4 reached the same split.
- **RG-B-015** split from RG-F7-DEDUPE (record G0-B-015): Worker H2: B-015 is a synthetic CI/local destination default; C-022 describes provider behaviour.

## Row re-keys (mechanism separated from the parameter it sits beside)

- W2-074 → **RG-C-017/mechanism**: Worker D2 rated the reaper-forwarding mechanism RETAIN-IN-CODE; the interval value (W8-041) is a separate host-owned parameter. Split so one rule never carries two dispositions.
- W8-052 → **RG-C-016/mechanism**: flock poll loop is an implementation detail (RETAIN-IN-CODE); the lease-acquire timeout (W8-040) is the separate host-owned parameter.
- W2-088 → **RG-B-027/mechanism**: CLI digest check, process-group kill cleanup and fixed output cap are protected mechanisms (RETAIN-IN-CODE); the OpenShell command timeout (W2-083) is the separate host-owned parameter. Resource-budget scope question stays open (G0 F3).
- W2-089 → **RG-B-027/mechanism**: Scrubbed CLI environment and fixed exec flags are protected mechanisms; see W2-088.
- W8-087 → **RG-C-012/mechanism**: Critical-evidence skipping logic is a retained evaluator; the evidence threshold value (W8-011) arrives in the issuer-approved authority context and is issuer-owned.
- W9-040 → **RG-F11-REDACTION-DEFAULTS/mechanism**: The redaction mechanism driven by RedactionConfig is retained (confidentiality); the caller-overridable default values are the separate presentation-default rule.
- W3-061 → **RG-B-015**: Site is the constructor default of the synthetic reference destination (dedupe_destination.py). Worker D2 viewed it as a provider fact; Worker H1/H2 audit of G0-B-015 judged it a synthetic default outside the production boundary. Lead: the synthetic constructor default is OUT-OF-SCOPE; the provider-declared TTL semantics remain in RG-F7-DEDUPE (W3-062, W3-063, W2-062).
- W3-065 → **RG-B-015**: Reference/qualification destination modelling provider behaviour: synthetic, outside the production boundary (Worker D2 also rated it OUT-OF-SCOPE).
- W8-014 → **NEW:runtime-authority-profile-producer-keys**: Producer keys are host trust roots, not a Registry candidate; separated from the RG-C-013 container group (Worker H1: container record, not one rule).
- W5-023 → **LR-MANIFEST-DEFAULT-ACTION**: Worker C and the group audit (H2) agree the validator's `default_action` fallback is the same logical field as RG-C-031/RG-D-003; blind reviewer J1a classed it CALLER-OR-ISSUER-OWNED. Lead: merged into LR-MANIFEST-DEFAULT-ACTION.
- W1-009 → **RG-B-001/number-domain**: Integer bit-length 256 and finite-float rule define the canonical number domain (protocol constant, retained); separated from the size/depth budgets that are the subject of the open admission-budget question.

## Many-to-one groupings by the first-pass workers (rules with more than one historical row)

114 rules contain more than one historical row. The merge basis recorded by the workers is in `crosswalk.json` (`merge_basis`). Largest groups:

| Rule | Historical rows | Disposition | Example merge basis |
|---|---|---|---|
| NEW:attempt-lifecycle-and-commit | 15 | RETAIN-IN-CODE | attempt/commit evaluator |
| NEW:control-plane-binding-adapter | 9 | RETAIN-IN-CODE | control_plane_adapter module |
| NEW:evidence-export-contract | 8 | RETAIN-IN-CODE | evidence/producer contract validators |
| NEW:local-claim-issuance-validation | 8 | RETAIN-IN-CODE |  |
| NEW:refund-intent-profile | 8 | RETAIN-IN-CODE | refund_intent module |
| NEW:reversibility-semantics | 8 | RETAIN-IN-CODE |  |
| RG-C-029 | 8 | RETAIN-IN-CODE | G0 group RG-C-029 |
| NEW:effective-grant-profile | 7 | RETAIN-IN-CODE | effective_grant module |
| NEW:operation-admission-identity | 7 | RETAIN-IN-CODE | operation_admission module |
| NEW:snapshot-structural-validation | 7 | RETAIN-IN-CODE | validate_snapshot field checks |
| RG-C-023 | 7 | RETAIN-IN-CODE | G0 group RG-C-023 |
| NEW:bounded-store-record-primitives | 6 | RETAIN-IN-CODE | same mechanism family: bounded-store-record-primitives |
| NEW:lae-atomic-execute | 6 | RETAIN-IN-CODE | same rule family/evaluator: lae-atomic-execute |
| NEW:manifest-structural-validation | 6 | RETAIN-IN-CODE | same mechanism family: manifest-structural-validation |
| NEW:microsoft-agt-adapter-conjunction | 6 | RETAIN-IN-CODE |  |
| NEW:runtime-authority-extension-gates | 6 | RETAIN-IN-CODE |  |
| RG-B-026 | 6 | RETAIN-IN-CODE | G0 group RG-B-026 |
| NEW:bounded-manifest-conformance | 5 | RETAIN-IN-CODE | same _manifest_mismatches evaluator |
| NEW:evidence-validation-integrity | 5 | RETAIN-IN-CODE |  |
| LR-RUNTIME-ADMISSION-SIZE-BUDGETS | 4 | UNRESOLVED | same floor as other admission bounds (F3) |
| NEW:amount-numeric-validation | 4 | RETAIN-IN-CODE | amount/ceiling numeric validators |
| NEW:check-recovery-mechanism | 4 | RETAIN-IN-CODE | same mechanism family: check-recovery-mechanism |
| NEW:effects-count-validation | 4 | RETAIN-IN-CODE | effect count validators |
| NEW:lae-authoritative-state-checks | 4 | RETAIN-IN-CODE | same rule family/evaluator: lae-authoritative-state-checks |
| NEW:lae-claim-model-validation | 4 | RETAIN-IN-CODE | same rule family/evaluator: lae-claim-model-validation |
| NEW:local-claim-provisioning-verification | 4 | RETAIN-IN-CODE |  |
| NEW:operation-identity-admission | 4 | RETAIN-IN-CODE | same mechanism family: operation-identity-admission |
| NEW:runtime-denial-reason-codes | 4 | RETAIN-IN-CODE | Reason-code literals on denial paths |
| NEW:simulate-fault-injection | 4 | RETAIN-IN-CODE | Four rows share the fault-injection hook (W1-065,W2-066,W3-040,W3-043) |
| NEW:validation-issue-codes | 4 | RETAIN-IN-CODE | Validation issue codes |
| RG-B-005 | 4 | RETAIN-IN-CODE | evaluator semantics for F1d |
| RG-B-011 | 4 | RETAIN-IN-CODE | G0 F2 RETAIN (B-011) |
| RG-B-023 | 4 | RETAIN-IN-CODE | G0 retains closed 4-state set |
| LR-F4-STATUS-APPROVAL-AGE | 3 | REGISTRY-ELIGIBLE | row is a ctor spanning four params; keyed to status, others as children |
| LR-F5-CLASS-STATUS-AGE | 3 | REGISTRY-ELIGIBLE | consumer site of ActionClass.max_status_age_seconds (W8-004) |
| NEW:authority-state-status-vocabularies | 3 | RETAIN-IN-CODE | Closed status enums + terminal revocation |
| NEW:cli-run-input-contract | 3 | RETAIN-IN-CODE | Merged with W9-048/W9-050 |
| NEW:cp-contract-version-constants | 3 | RETAIN-IN-CODE | Merged with W8-001/W8-076: version/profile id constants |
| NEW:evidence-canonical-commitment-serialization | 3 | RETAIN-IN-CODE | Same canonical-JSON+sha256 mechanism recurs across runtime/CP |
| NEW:lae-provision-no-overwrite | 3 | RETAIN-IN-CODE | same rule family/evaluator: lae-provision-no-overwrite |

## G0 grouping verdicts that did NOT change a disposition (proposals only)

Workers H1/H2 judged these groups over- or under-merged; because the parts share one disposition the audit keeps the G0 group identity and records the proposal:

| G0 group | Verdict | Note |
|---|---|---|
| RG-F1C-MAX-AMOUNT | OVER-MERGED | G0 eligible-not-migrated is superseded by M2 (r08-v3 + Runtime PR-3 #152): implemented and integrated at LAE guard, NOT independently accepted. Split D-001 out (issuer-owned manifest ceiling). |
| RG-F1C-MAX-EFFECTS | OVER-MERGED | Superseded by M2: implemented+integrated, not accepted. Policy ceiling must stay distinct from claim effective_max_effects and manifest limits (issuer-owned). |
| RG-F1D-TARGET-PREFIXES | OVER-MERGED | Superseded by M3 (Registry #56, Runtime #153): implemented+integrated, not accepted. Registry tokens exclude some characters (e.g. space) so some prefixes cannot be governed (v4_f1abcd docstring). |
| RG-F11-REDACTION-DEFAULTS | OVER-MERGED | Not hard-coded policy: overridable defaults for export presentation. Do not count toward eligible coverage; any redaction floor needs separate privacy-owner decision. |
| RG-F6-ACTION-LISTS | OVER-MERGED | Split: B-014 OUT-OF-SCOPE (legacy, non-effecting); D-008 issuer-owned manifest content whose digest is bound, so a Registry overlay would alter an authority definition. |
| RG-F7-DEDUPE | OVER-MERGED | B-015 OUT-OF-SCOPE (synthetic). C-022 describes provider behaviour; a Registry cannot change provider truth, only misdescribe it. Host-owned fact, not narrowing policy. |
| RG-A-007 | UNDER-MERGED | Represented in Registry only (builder-tested); no activation or enforcement boundary in CP. Count as eligible/in-progress, not governed. Merge with RG-C-003/C-004. |
| RG-A-008 | UNDER-MERGED | Represented only. Registry class keys follow frozen token rule (stricter than CP non-empty id), so some class ids cannot be governed. Merge with RG-C-008. |
| RG-B-022 | OVER-MERGED | Core is protocol/store grammar (retain). Two timeouts are operational; low value. |
| RG-C-003 | UNDER-MERGED | Registry f4 exists; CP consumer/activation absent (wave M11). Also unvalidated ctor int (negative allowed). Merge with RG-A-007. |
| RG-C-004 | UNDER-MERGED | As RG-C-003: Registry slot exists, no CP consumer. Merge with RG-A-007. |
| RG-C-008 | UNDER-MERGED | Eligible (monotone min) but interacts with signed outage extensions (extension limit measured from base) and approval-commitment profile binding. Merge with RG-A-008. |
| RG-C-013 | OVER-MERGED | Container record, not one rule: trust roots/synthetic toggle retained; action age members and sub-profiles are separate groups. Schema omits the sub-profile fields (additionalProperties false). |
| RG-C-027 | OVER-MERGED | default_action is inert (no consumer). allowed/blocked tool lists are caller JSON feeding Frame/PolicyGate, a separate param not covered by this verdict. |
| RG-C-030 | OVER-MERGED | Two unrelated params: injected evaluator (code) and trace flag (diagnostic). Neither is Registry policy. |
| RG-C-031 | UNDER-MERGED | NOT governed. Same logical field as RG-D-003 (manifest default_action in action-manifest). Split: configured value=issuer-owned manifest data; absent->escalate default=fail-safe literal. F1a action n… |
| RG-C-041 | OVER-MERGED | Two parameters merged: truncation length (presentation) and escaping (control). Neither is Registry policy. |
| RG-D-003 | UNDER-MERGED | Same logical field as RG-C-031. The omitted-field default 'escalate' is a fail-safe literal (retain); the configured value is manifest data (see RG-C-031). |
| RG-D-017 | OVER-MERGED | Merges rate limit (128/60s, 64), admin command freshness window (60s) and a counter ceiling; source states policy is deliberately non-configurable. |
| RG-D-019 | OVER-MERGED | Six distinct bounds merged; delegation depth (authority chain) is Tier 1 and should be its own group. No narrowing slot exists. |

