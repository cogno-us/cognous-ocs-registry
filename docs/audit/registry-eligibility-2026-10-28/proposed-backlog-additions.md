# Proposed corrections and additions to the migration backlog (for Architect approval)

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

These are proposals only. The active migration plan and `m2/01-migration-backlog.md` are not changed by this audit and migration work is not blocked by it.

## A. Counts the backlog would carry if the proposals are accepted

| Backlog metric (rule groups / rules) | G0 / backlog today | Audit proposal |
|---|---|---|
| Already governed or implemented | 5 (G0) + 4 implemented M2/M3 pending acceptance | 4 rules / 9 parameters (all implemented; 0 accepted) |
| Eligible, not yet integrated | 23 eligible-not-migrated (19 after M2/M3) | 8 rules / 10 parameters |
| Unresolved or blocked | 5 (G0) | 4 |

## B. Eligible backlog (audit view, ordered by the existing waves)

| Rule | Parameters | Proposed wave | Layer state | Blocking decision |
|---|---|---|---|---|
| LR-F4-STATUS-APPROVAL-AGE | 2 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'YES'} |  |
| RG-C-020 | 1 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |
| RG-F4-OBSERVATION-POLICY | 2 | M11 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |
| LR-F5-CLASS-STATUS-AGE | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'YES'} | How does a Registry-narrowed class value enter approval_commitment and the approval-side age_ceilings check, given profile.model_dump is the preimage? |
| RG-C-009 | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} | As RG-C-008: how a narrowed class enum enters the approval commitment. |
| RG-C-010 | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} | Is a Registry-forced 'requires_revocation_assurance' meaningful when it holds the class until the host supplies a holder inventory (self-inflicted denial), and… |
| RG-C-011 | 1 | M12 | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} |  |
| NEW:terminal-revocation-marker | 1 | not scheduled (same Control Plane profile-consumer family as RG-C-010/RG-C-020; not authorized) | {'enforcement_integrated': 'NO', 'independently_accepted': 'NO', 'registry_represented': 'NO'} | How does a Registry-forced profile section enter the approval commitment (the AUD-D06 question shared with RG-C-010)? |

## C. Rules proposed for removal from the eligible backlog

| Rule | G0 | Audit | Reason |
|---|---|---|---|
| RG-B-016 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-C-005 | ELIGIBLE-NOT-MIGRATED | BLOCKED | LEAD-OVERRIDE: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'o… |
| RG-C-006 | ELIGIBLE-NOT-MIGRATED | BLOCKED | LEAD-OVERRIDE: Cross-check J2 and pass 2 (Worker C): DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) declares identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds 'o… |
| RG-C-037 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | LEAD-OVERRIDE: J3a: refusal_trends is a documented reporting API with tests, not unused; thresholds are analytics defaults with no authority effect and no enforcement boundary. LOW confidence; either… |
| RG-D-015 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | H-WORKER GROUP AUDIT |
| RG-D-018 | ELIGIBLE-NOT-MIGRATED | PROVIDER-OR-HOST-OWNED | H-WORKER GROUP AUDIT |
| RG-D-020 | ELIGIBLE-NOT-MIGRATED | CALLER-OR-ISSUER-OWNED | H-WORKER GROUP AUDIT |
| RG-D-021 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | LEAD-OVERRIDE: Pass 2 (Worker E): the hub checker is not wired into any gate and uses a fixture key. Label-only change from PROVIDER-OR-HOST-OWNED; both non-manageable. |
| RG-D-022 | ELIGIBLE-NOT-MIGRATED | OUT-OF-SCOPE | LEAD-OVERRIDE: Cross-check J2 (LOW): federated_governance.py is synthetic SQLite only and open-control-stack README:155 says synthetic references grant no authority; config is fixed at create with tr… |
| RG-F11-REDACTION-DEFAULTS | ELIGIBLE-NOT-MIGRATED | CALLER-OR-ISSUER-OWNED | LEAD-OVERRIDE: Pass 2 (Worker E): redaction is an optional export command (cli.py:51-59,155-168), so a minimum floor cannot be enforced; it also trades against evidence verifiability. |

## D. Rules proposed for addition

| Rule | Disposition | Reason |
|---|---|---|
| NEW:terminal-revocation-marker | REGISTRY-ELIGIBLE | LEAD-OVERRIDE: Pass 2 (Worker G-01 proposal, verified by the lead): the profile is an opt-in safeguard (runtime_authority.py:182-191,214) with a single consumer (bounded.py:2390-2392). Its only varia… |

## E. Corrections to stale labels

- Mark RG-A-007 and RG-A-008 (with the merged RG-C-021 age_ceilings carrier) as *represented in the Registry, not governed*: counting them as ALREADY-GOVERNED overstates coverage until a Control Plane consumer exists (wave M11/M12).
- Mark RG-C-031 as issuer-owned manifest data (no Registry slot).
- Record RG-F11, RG-D-012, RG-F7-DEDUPE, RG-C-032 and the Runtime admission budgets as unresolved pending the owner decisions named in the rule catalogue.
- Record the M2/M3 groups as implemented and integrated, pending independent Tier 1 acceptance.
- Drop RG-B-016 from wave M11: the module is an experimental synthetic ledger no executor imports.
- Bring AD-07 in line with the merged M2/M3 narrowing by an additive dated decision file (the old OPEN row and the frozen G0 records stay untouched); the Architect supplies the M2/M3 ruling texts (see `unresolved-architectural-decisions.md` §1b).
- Correct the progress accounting in unmerged PR #59: RG-C-006 (clock tolerance) is counted as implemented although its own item 6.B is open and the cited basis (Amendment 1 §2) is the section that excludes the field. Show M11 as two groups implemented plus one pending ruling only after AR-1/AR-2 are answered.
- Correct stale text: `docs/sprint-status.md:40` still says M3 is not authorized; the catalogue descriptions 'Registry: no slot' for max_amount, max_effects and target prefixes are superseded by merged M2/M3 (corrected in this audit's catalogue).
- Treat M12 and later waves as not authorized: they are unchanged by this audit.
- Add the newly found eligible rule (terminal-revocation enablement) to the Control Plane profile-consumer family with RG-C-010 and RG-C-020, behind the AUD-D06 commitment-coupling decision. It is not scheduled.

