# Proposed corrections and additions to the migration backlog (for Architect approval)

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

These are proposals only. The active migration plan and `m2/01-migration-backlog.md` are not changed by this audit and migration work is not blocked by it.

## A. Counts the backlog would carry if the proposals are accepted

| Backlog metric (rule groups / rules) | G0 / backlog today | Audit proposal |
|---|---|---|
| Already governed or implemented | 5 (G0) + 4 implemented M2/M3 pending acceptance | 5 rules / 9 parameters (all implemented; 0 accepted) |
| Eligible, not yet integrated | 23 eligible-not-migrated (19 after M2/M3) | 8 rules / 10 parameters |
| Unresolved or blocked | 5 (G0) | 11 |

## B. Eligible backlog (audit view, ordered by the existing waves)

| Rule | Parameters | Proposed wave | Layer state | Blocking decision |
|---|---|---|---|---|
| LR-F4-STATUS-APPROVAL-AGE | 2 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'YES'} |  |
| RG-C-019 | 1 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |
| RG-C-020 | 1 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |
| RG-F4-OBSERVATION-POLICY | 2 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |
| LR-F5-CLASS-STATUS-AGE | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'YES'} | How does a Registry-narrowed class value enter approval_commitment and the approval-side age_ceilings check, given profile.model_dump is the preimage? |
| RG-C-009 | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} | As RG-C-008: how a narrowed class enum enters the approval commitment. |
| RG-C-010 | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} | Is a Registry-forced 'requires_revocation_assurance' meaningful when it holds the class until the host supplies a holder inventory (self-inflicted denial), and… |
| RG-C-011 | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |

## C. Rules proposed for removal from the eligible backlog

| Rule | G0 | Audit | Reason |
|---|---|---|---|
| RG-B-016 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-C-005 | ELIGIBLE-NOT-MIGRATED | BLOCKED | LEAD-OVERRIDE: Cross-check J2: DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) excludes identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as host-owned and never … |
| RG-C-006 | ELIGIBLE-NOT-MIGRATED | BLOCKED | LEAD-OVERRIDE: Cross-check J2: DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) excludes identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as host-owned and never … |
| RG-C-037 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: J3a: refusal_trends is a documented reporting API with tests, not unused; thresholds are analytics defaults with no authority effect and no enforcement boundary. LOW confidence; either… |
| RG-D-015 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-D-018 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-D-020 | ELIGIBLE-NOT-MIGRATED | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-D-021 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-D-022 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | LEAD-OVERRIDE: Cross-check J2 (LOW): federated_governance.py is synthetic SQLite only and open-control-stack README:155 says synthetic references grant no authority; config is fixed at create with tr… |
| RG-F11-REDACTION-DEFAULTS | ELIGIBLE-NOT-MIGRATED | UNRESOLVED | LEAD-OVERRIDE: First-pass H1 rated the redaction defaults caller-owned presentation choices; cross-check J3b rated an OR-floor of redaction flags REGISTRY-ELIGIBLE. Whether a minimum-redaction floor … |

## D. Rules proposed for addition

| Rule | Disposition | Reason |
|---|---|---|

## E. Corrections to stale labels

- Mark RG-A-007 and RG-A-008 (with the merged RG-C-021 age_ceilings carrier) as *represented in the Registry, not governed*: counting them as ALREADY-GOVERNED overstates coverage until a Control Plane consumer exists (wave M11/M12).
- Mark RG-C-031 as issuer-owned manifest data (no Registry slot).
- Record RG-F11, RG-D-012, RG-F7-DEDUPE, RG-C-032 and the Runtime admission budgets as unresolved pending the owner decisions named in the rule catalogue.
- Record the M2/M3 groups as implemented and integrated, pending independent Tier 1 acceptance.
- Drop RG-B-016 from wave M11: the module is an experimental synthetic ledger no executor imports.
- Bring AD-07 in line with the merged M2/M3 narrowing (see `unresolved-architectural-decisions.md`).

