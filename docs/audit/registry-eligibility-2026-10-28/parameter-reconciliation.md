# Parameter-level reconciliation

> Release: HOLD. Publication: HOLD. Production: HOLD. Audit only; not independent Tier 1 qualification.

Every number below is computed from `parameter-catalogue.json` (rebuilt by `tools/build_parameters.py`); none is copied from prose.

## 1. Five different units

| Unit | Count | What it counts |
|---|---|---|
| Historical rule sites | 620 | Rows of the S02 inventory: one per hard-coded implementation site, including mandatory invariants, vocabularies and serialization details. Many rows implement one rule. |
| G0 rule groups | 97 | G0's grouping of 116 current source records into logical rules. |
| Canonical rules | 444 | This audit's logical rules after merges, splits and the repository-coverage sweep. Most are protected mechanisms with no tunable value. |
| Rules with at least one configurable parameter | 52 | Canonical rules containing at least one independently configurable parameter, whoever owns it. |
| Candidate configurable parameters | 80 | Independently variable fields a legitimate owner could set, whoever owns them, including 3 literals the audit retains in code (77 without them). Composite copies, derived values, site duplicates and invariants are excluded. |
| Registry-manageable parameters | 19 | Parameters of rules that are REGISTRY-GOVERNED or REGISTRY-ELIGIBLE. |

Rules and parameters differ because a rule can carry several parameters (the five F1a allow-sets, two F4 ages, two observation-policy fields, and the governed target prefixes plus match mode). Pass 1 reported 13 manageable rules and 19 parameters. Pass 2 reports 13 rules and 20 parameters: merging prefixes+match removes one governed rule, and the newly found terminal-revocation enablement adds one eligible rule and one parameter.

## 2. Answers

| Question | Answer |
|---|---|
| Distinct logical rules | 444 |
| Rules containing meaningful configurable parameters | 52 |
| Candidate configurable parameters (all owners) | 80 (77 excluding literals retained in code) |
| Registry-manageable parameters | 19 (9 governed + 10 eligible); 12 rules; 18 narrowing units |
| Represented in the Registry | 12 |
| Integrated at an enforcement boundary | 9 |
| Independently accepted | 0 |
| Eligible, not migrated | 10 (3 represented in the Registry but with no consumer) |
| Blocked by an Architect decision | 3 blocked parameters; 1 unresolved parameters (excluded from the manageable numerator) |
| New opportunities missed by G0 | P-RG-C-TERMINAL-REVOCATION-enabled |

## 3. Percentages (denominators stated)

| Ratio | Numerator | Denominator | Percent |
|---|---|---|---|
| Registry-manageable parameters / candidate configurable parameters | 19 | 80 | 23.8 |
| Registry-manageable parameters / candidate parameters excluding those the audit retains in code | 19 | 77 | 24.7 |
| Core-tier manageable parameters / candidate configurable parameters | 14 | 80 | 17.5 |
| Enforcement-integrated parameters / manageable parameters | 9 | 19 | 47.4 |
| Registry-represented parameters / manageable parameters | 12 | 19 | 63.2 |
| Independently accepted parameters / manageable parameters | 0 | 19 | 0.0 |
| Manageable rules / rules with at least one counted parameter | 12 | 52 | 23.1 |
| Manageable rules / all canonical rules | 12 | 444 | 2.7 |
| Manageable narrowing units / all narrowing units (finest partition) | 18 | 79 | 22.8 |

Rule-level coverage depends on how rules are partitioned, so parameter-level coverage is the more stable headline:

| Partition | Manageable | Of |
|---|---|---|
| catalogue rules (this audit) | 12 | 52 |
| one unit per independently narrowable parameter | 18 | 79 |
| worker B alternatives (see worker-evidence/pass2/B.jsonl): F1a split five ways, F4 two ways, max_amount+max_effects joined | 11 to 19 depending on partition | partition-dependent |

Sensitivities on the parameter count:

| Change | Result |
|---|---|
| ObservationPolicy.clock_tolerance_seconds excluded with RG-C-006 if AR-1 extends the exclusion | manageable_parameters=18 |
| drop QUALIFIED/COUPLED tier (P-RG-C-010-requires_revocation_assurance, P-RG-C-011-reversibility, P-RG-C-020-anchor_deadline_to_inputs, P-RG-C-TERMINAL-REVOCATION-enabled, P-RG-F4-OBS-clock_tolerance_seconds) | manageable_parameters=14 |
| RG-C-005 and RG-C-006 authorized by the Architect (AR-1, AR-4) | manageable_parameters=22, note=the three age/tolerance parameters would become eligible (they are the blocked parameters) |

Tiers: CORE parameters have a direct monotone narrowing relation and a defined consumer path. QUALIFIED parameters (opt-in safeguard enablement toggles, or one rank parameter needing re-shaping) and COUPLED parameters (derived in part from another Registry value) are manageable in principle but carry a stated dependency. Qualified/coupled: P-RG-C-010-requires_revocation_assurance, P-RG-C-011-reversibility, P-RG-C-020-anchor_deadline_to_inputs, P-RG-C-TERMINAL-REVOCATION-enabled, P-RG-F4-OBS-clock_tolerance_seconds.

## 4. Parameters by category

| Category | Meaning | Parameters |
|---|---|---|
| A | Registry-manageable | 19 |
| B | Caller/issuer-owned | 15 |
| C | Mandatory invariant parameter (retain in code) | 3 |
| D | Operational, host or provider parameter (incl. out-of-scope) | 39 |
| E | Unresolved or blocked candidate | 4 |

Records excluded from the count: 5 COMPOSITE_MEMBER, 16 INVARIANT_NOT_PARAMETER, 5 SITE_DUPLICATE.

## Governed (9)

| Parameter | Rule | Represented | Integrated | Tier | Blocking decision / note |
|---|---|---|---|---|---|
| P-RG-F1A-allowed_actions | RG-F1A-ALLOW-SETS-FIVE | YES | YES | CORE | Counted ONCE although it appears in f1ab/f1abc/f1abcd payloads and (3 of 5) in r08-v1 f1a and the frozen S04 overlay (registry_consumer/consumer.py:42). Five in |
| P-RG-F1A-allowed_adapters | RG-F1A-ALLOW-SETS-FIVE | YES | YES | CORE | Counted ONCE although it appears in f1ab/f1abc/f1abcd payloads and (3 of 5) in r08-v1 f1a and the frozen S04 overlay (registry_consumer/consumer.py:42). Five in |
| P-RG-F1A-allowed_authority_domains | RG-F1A-ALLOW-SETS-FIVE | YES | YES | CORE | Counted ONCE although it appears in f1ab/f1abc/f1abcd payloads and (3 of 5) in r08-v1 f1a and the frozen S04 overlay (registry_consumer/consumer.py:42). Five in |
| P-RG-F1A-allowed_institutions | RG-F1A-ALLOW-SETS-FIVE | YES | YES | CORE | Counted ONCE although it appears in f1ab/f1abc/f1abcd payloads and (3 of 5) in r08-v1 f1a and the frozen S04 overlay (registry_consumer/consumer.py:42). Five in |
| P-RG-F1A-allowed_units | RG-F1A-ALLOW-SETS-FIVE | YES | YES | CORE | Counted ONCE although it appears in f1ab/f1abc/f1abcd payloads and (3 of 5) in r08-v1 f1a and the frozen S04 overlay (registry_consumer/consumer.py:42). Five in |
| P-RG-F1C-MAX-AMOUNT-max_amount | RG-F1C-MAX-AMOUNT | YES | YES | CORE | Counted once across f1abc and f1abcd. Compatibility limit: a caller float ceiling cannot be governed (refused). AD-07 open in register. |
| P-RG-F1C-MAX-EFFECTS-max_effects | RG-F1C-MAX-EFFECTS | YES | YES | CORE | Counted once. Runtime adapter still requires op.effects==1 (safe_executor.py:427) so the ceiling bounds the claim effective_max_effects, not the effect count. |
| P-RG-F1D-TARGET-MATCH-target_match | LR-F1D-TARGET-POLICY | YES | YES | CORE | Pass 2: counted as a payload field; shares narrowing unit NU-F1D-TARGET-SCOPE with allowed_target_prefixes (Worker A tagged it COMPOSITE_MEMBER for the narrowin |
| P-RG-F1D-TARGET-PREFIXES-allowed_target_prefixes | LR-F1D-TARGET-POLICY | YES | YES | CORE | JOINT narrowing unit with target_match: compose_targets (v4_f1abcd.py:84-92) takes (prefix list, mode) pairs; mode alone is not ordered (docstring 11-13). Count |

## Eligible, not migrated (10)

| Parameter | Rule | Represented | Integrated | Tier | Blocking decision / note |
|---|---|---|---|---|---|
| P-LR-F4-approval_max_age_seconds | LR-F4-STATUS-APPROVAL-AGE | YES | NO | CORE | As P-LR-F4-status_max_age_seconds |
| P-LR-F4-status_max_age_seconds | LR-F4-STATUS-APPROVAL-AGE | YES | NO | CORE | No Control Plane consumer on main; PR #87 (unmerged) adds registry_freshness_narrowing; blocked by M11 handoff 6.A (family atomicity) and 6.E (lifecycle) |
| P-LR-F5-class_max_status_age_seconds | LR-F5-CLASS-STATUS-AGE | YES | NO | CORE | How a Registry-narrowed class value enters approval_commitment (profile dump is the preimage, runtime_authority.py:236-251) and the age_ceilings carrier; no CP  |
| P-RG-C-009-on_unreadable | RG-C-009 | NO | NO | CORE | Same approval_commitment entry question as F5 (class dump is in the preimage); no Registry slot |
| P-RG-C-010-requires_revocation_assurance | RG-C-010 | NO | NO | QUALIFIED | Is a Registry-forced True meaningful when it holds the class until a host HolderInventory exists (self-inflicted denial); setting True changes the profile dump  |
| P-RG-C-011-reversibility | RG-C-011 | NO | NO | QUALIFIED | AUD-D06 (J3b override): can a Registry overlay on a producer assertion be authenticated without becoming a fact claim; member re-shaping (reversible_until/rever |
| P-RG-C-020-anchor_deadline_to_inputs | RG-C-020 | NO | NO | COUPLED | Whether a Registry ceiling set must force this True (policy_binding.py:126 already requires it); commitment effect of flipping the dump |
| P-RG-C-TERMINAL-REVOCATION-enabled | NEW:terminal-revocation-marker | NO | NO | QUALIFIED | approval_commitment coupling (AUD-D06) |
| P-RG-F4-OBS-clock_tolerance_seconds | RG-F4-OBSERVATION-POLICY | NO | NO | QUALIFIED | Same as P-RG-F4-OBS-max_age_seconds; also PR #58 f4t covers only the ctor tolerance, not this one |
| P-RG-F4-OBS-max_age_seconds | RG-F4-OBSERVATION-POLICY | NO | NO | CORE | 60 vs 300 relationship between status_max_age default and the CLI observation literal (plan s8) not resolved; no CP consumer |

## Blocked (3)

| Parameter | Rule | Represented | Integrated | Tier | Blocking decision / note |
|---|---|---|---|---|---|
| P-RG-C-005-identity_max_age_seconds | RG-C-005 | NO | NO |  | DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) lists identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as 'out of scope an |
| P-RG-C-005-mandate_max_age_seconds | RG-C-005 | NO | NO |  | DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) lists identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as 'out of scope an |
| P-RG-C-006-clock_tolerance_seconds | RG-C-006 | NO | NO |  | DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md:8) lists identity_max_age_seconds, mandate_max_age_seconds and clock_tolerance_seconds as 'out of scope an |

## Unresolved (1)

| Parameter | Rule | Represented | Integrated | Tier | Blocking decision / note |
|---|---|---|---|---|---|
| P-RG-C-024-funded_authorities | RG-C-024 | NO | NO |  | Is a host principal allow-list a Registry-narrowable allow-set like F1a, given principal namespace and merge profile are host-owned and opt-in |

