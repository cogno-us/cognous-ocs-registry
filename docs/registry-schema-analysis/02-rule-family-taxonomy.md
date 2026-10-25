# 02 Rule-family taxonomy

Non-authorizing analysis. A rule may belong to more than one category; the categories are not a partition. Labels: [V] [R] [I] as in the README.

## 1. Categories

| Cat | Name | Meaning | Where it appears (indicative) |
|---|---|---|---|
| A | Configurable governance parameters | A value the code reads from a caller, constructor or profile, whose change moves a bound without changing logic | S02 CONFIGURABLE-CANDIDATE (43 rows) [R]; catalogue has no such type [R] |
| B | Mandatory enforcement invariants | Logic whose change alters what the system guarantees | S02 MANDATORY-INVARIANT (354); catalogue validator_rule 201 and mandatory 39 as enforcement *candidates* only (PR #13 groups the 35 floors with policy statements as stated; placing them near B is this analysis's own assignment) [R] |
| C | Authority and permission requirements | Who may do what; grants, scopes, holders | F5, F6, parts of M4 |
| D | Evidence and provenance requirements | What must be recorded or shown | S02 SERIALIZATION-OR-EVIDENCE (90); catalogue evidence set |
| E | Freshness and temporal conditions | Ages, windows, clocks | F4, F7 |
| F | Resource and operational limits | Size, depth, timeout, TTL | F3, F9, F7 (TTL) |
| G | Refusal and reason-code vocabularies | Names of refusals and reasons | S02 REFUSAL (50); catalogue reason_code_or_refusal_vocabulary 1,819 [R] |
| H | State-transition and lifecycle requirements | Attempt, grant, recovery state machines | M2, M4 |
| I | Verification and diagnostic requirements | Verifiers, trend thresholds, warnings | F10; catalogue verifier groups (`verifier-checks/*`, 72 `validator` entries across v1 to v4 and journal tables, per the group listing of the decoded catalogue) |
| J | Historical proposals and unimplemented rules | Proposed-not-adopted clauses; unwired validators | 229 proposed clauses [R] |
| K | Unknown or unresolved | Strength, applicability or classification not established | 32 S02 rows; catalogue `unknown` 869 [R] |

The figures in the "Where it appears" column are the sources' own counts. This analysis has not assigned the 3,190 entries to A to K, and it does not claim a distribution.

## 2. Eight dimensions (never collapsed into one label)

| Dimension | Question it answers | Example of why it matters |
|---|---|---|
| Normative role | What kind of statement is this (limit, requirement, vocabulary, principle)? | A principle is not a limit |
| Configuration status | Is the value already data today? | `dedupe_ttl_seconds` is constructor-supplied; `_TARGET_MATCH_MODES` is a literal |
| Enforcement mechanism | What code path, if any, enforces it? | An error code in a validator table may have no enforcing path |
| Implementation status | Is the behavior implemented and tested? | A fixture does not prove implementation |
| Adoption status | Has the governing authority adopted it? | 229 clauses are proposed-not-adopted |
| Evidence status | What evidence supports the classification? | Worker inference versus source read |
| Applicability | To which component, revision and profile does it apply? | `runtime_source_blob_id` exact match in S03 |
| Historical release scope | Which release did it come from? | All catalogue rules are `v0_1`; no separate V0.2 inventory was recovered (absence of recovery, not proof that none exists) |

## 3. Candidate configurable families (nine)

Source revisions: Runtime `ec728da6` and Control Plane `0a41faa9` (S02 pins) [R]. "Established" means demonstrated by the S03 to S05 evidence, which covers F1a only. Test statements are S02's by-name claims [R] unless marked.

### F1 LocalExecutionPolicy values (sub-groups F1a to F1d)

1. Family id: `F1`; sub-groups `F1a` allowed_units, allowed_adapters, allowed_actions; `F1b` allowed_institutions, allowed_authority_domains; `F1c` max_amount, max_effects; `F1d` allowed_target_prefixes, target_match.
2. Source: Runtime `engine/safe_executor.py:358-372` (fields), `:374-395` (`__post_init__`), `:410-430` (`check`) at `ec728da6` [R]; the S01 baseline in `baseline/` is the pinned copy.
3. Owning component: Execution Runtime.
4. Evaluator: `LocalExecutionPolicy.check`, fixed check order.
5. Current representation: frozen dataclass constructor arguments; for F1a also an S03 record plus S04 overlay.
6. Already configuration? Yes, caller-constructed data.
7. Implementation established? F1a yes for the bounded profile (S03/S04/S05, trusted-host only, inactive). F1b to F1d: no.
8. Tier: 1 (admission to an effect) [R, S02 normalised].
9. Composition: F1a/F1b sets by intersection; F1c ceilings by minimum; F1d not a set intersection (see 04).
10. Required invariants: check order, reason texts, validation in `__post_init__`, the one-effect rule, target well-formedness stay in code.
11. Refusal semantics: `check` reasons are Runtime code; the S04 overlay refusal means "overlay not applied" and leaves the caller policy in force (T7).
12. Dependencies: none across components for F1a/F1b; F1c depends on the effect-cap origin (W8-091, 03) [I].
13. Tests and evidence: S01 63 tests [R, S01 documents]; S05 differential evidence for F1a; none for F1b to F1d.
14. Unresolved: W1-029 (match-mode set), W8-091 (effect cap origin); W1-015 binary64 handling is a representation concern for F1c.
15. Migration suitability: F1a done; F1b high; F1c moderate with a typed numeric payload; F1d low (new semantics).

### F3 Size, depth, timeout budgets

1. `F3`. 2. Runtime `safe_executor.py:147-184`, `openshell_environment.py`, `strict_json.py:21,24-33`; CP `cli_run.py:61` [R]. 3. Runtime, Control Plane. 4. Admission and I/O guards, various. 5. Mostly literals. 6. Mostly no. 7. No. 8. Mixed: W1-007/008 admission guards Tier 1; others Tier 2 minimum [R]. 9. Ceilings by minimum where a code hard cap exists; admission guards not eligible. 10. The guards themselves. 11. Per-guard, code. 12. None established. 13. None seen for most [R]. 14. W2-082 (`openshell_environment.py:89-90`, qualified profile values; linked to F3 by this analysis, not by S02) [I]. 15. Low: little test evidence and mixed tier.

### F4 Observation, status and approval freshness bounds

1. `F4`. 2. CP `cli_run.py:510`, `bounded.py` (several ranges), `freshness.py:62-72`; Runtime `recovery_resolution.py:266-269` [R]. 3. Control Plane and Runtime. 4. Admission freshness gates in `bounded.py`. 5. Constructor and profile values plus call-site literals. 6. Mixed. 7. No. 8. Tier 1. 9. Per-scalar age ceilings by minimum only under a ruled direction; cross-bound composition not defined. 10. Precedence rules (W7-042) and clock handling stay in code. 11. Absent `observation_policy` yields `observation_policy_missing` and a hold [V, 03]. 12. A clock source; observation authority; ActionClass declarations (F5). 13. `test_bounded_authorization.py`, `test_freshness.py` by name [R]. 14. W6-042 (classification), 60-versus-300 relationship. 15. Low now: wide blast radius, depends on rulings.

### F5 Per-action-class authority declarations

1. `F5`; sole owner of `ActionClass.max_status_age_seconds` (F4 does not carry it, to avoid two families constraining one field). 2. CP `runtime_authority.py:87-121,153-170` [R]; fields read in 03 [V]. 3. Control Plane. 4. Admission gates in `bounded.py`. 5. pydantic host profile (`RuntimeAuthorityProfile`, `ActionClass`). 6. Yes, host profile. 7. No. 8. Tier 1. 9. Per-field directional meet for tightening fields; toggles that relax a check are never registry-configurable (04). 10. Authenticated resolver requirement; profile composition rule (merge and dedupe need operation_identity). 11. `holder_inventory_missing` is given for action classes flagged `requires_revocation_assurance` (`holder_inventory.py:7`) [R]. 12. F4, F7 sub-profiles. 13. `test_runtime_authority.py`, `test_reversibility.py` by name [R]. 14. W8-014 is UNRESOLVED; W8-068 (`HolderInventory`) is a CONFIGURABLE-CANDIDATE, adjacent, Tier 1 until reviewed [R]. 15. Low; split into a tightening-only subset.

### F6 Agent permission allow-list

1. `F6`. 2. Runtime `engine/permissions.py:15-23`, `permissions.json:1-4` [V, 03 §3]. 3. Runtime. 4. `PermissionSystem.is_allowed`, exact string membership. 5. JSON file `{"agent": ["perm", ...]}`. 6. Yes, data file. 7. No; not in this repository's baseline. 8. Tier 1. 9. Per-agent intersection; absent-agent behavior needs a ruling (08). 10. Missing file means deny-all; malformed JSON raises (W2-002) [R]. 11. `is_allowed` returns false. 12. Baseline import for `permissions.py`. 13. `tests/test_permissions.py` by name [R]. 14. None of the 32 rows; absent-agent semantics is a new question. 15. Moderate; new baseline and mapping payload.

### F7 Dedupe and replay-window defaults

1. `F7`. 2. Runtime `engine/dedupe_destination.py` (default 600 s); CP `dedupe.py` `DedupeProfile` [V, 03]. 3. Runtime and Control Plane jointly. 4. `_operation_guard` (Runtime); `DedupeProfile` ordering check and `dedupe_mode` selection (CP). 5. Constructor argument with a literal default; CP profile triple. 6. Yes in both. 7. No. 8. Tier 2 minimum; the guard is Tier 1 [R]. 9. Per-field direction plus a joint ordering check; conditional (04). 10. `provider_horizon <= escalation_deadline < dedupe_ttl`; destination capability `dedupe-ttl/0.1` with TTL not below the profile TTL. 11. `operation_already_committed` within the TTL for a different effect id; after the TTL the key is forgotten by design [V]. 12. Both components must agree. 13. `test_n4_dedupe_destination.py` by name [R]. 14. W3-063, W9-027. 15. Low until the TTL direction and the cross-component dependency are ruled.

### F9 Tenant id length bound

1. `F9`. 2. Runtime `safe_executor.py:318-321`; CP `bounded.py:151-154` [R]. 3. Both. 4. Shape validation. 5. Literal. 6. No. 7. No. 8. Tier 2. 9. Lowering only (minimum). 10. Shape validation itself. 11. Code. 12. Two copies of the literal must agree. 13. None found for the bound [R]. 14. None. 15. Very low; no value in registry data.

### F10 Diagnostic trend thresholds

1. `F10`. 2. CP `reason_vocabulary.py:21-25,31-32` (`5`, `1`) [R]. 3. Control Plane. 4. Non-gating trend report. 5. Keyword defaults. 6. Yes. 7. No. 8. Tier 2 minimum [R]. 9. No authority semantic; no composition needed. 10. None gating. 11. None. 12. None. 13. `test_rule_revision.py:118-120` by name [R]. 14. None. 15. Low risk, low value; useful only as a low-risk contract test vehicle (not recommended).

### F11 Redaction defaults

1. `F11`. 2. CP `models.py:420-451`, `cli.py:107-114` [R]. 3. Control Plane. 4. Redaction configuration. 5. Mechanism configurable, defaults literal. 6. Partly. 7. No. 8. Tier 2 minimum with confidentiality controls treated as Tier 1 [R]. 9. Union of redaction categories (more redaction is stricter), only where categories are compatible. 10. Redaction of protected data is not removable by data. 11. Code. 12. None. 13. W9-002 lists tests by name [R]. 14. None. 15. Moderate; blocked by tier classification.

## 4. Mandatory and non-migratable families (eight)

Assignments below are **proposals pending D1 (08)**. Several S02 source rows placed here are UNRESOLVED (for example W1-029, W2-025, W5-011, W5-012, W5-028, W8-014, W4-022/023); placing them in a family does not classify them.

| Id | Family | Source rows | Why it stays in code |
|---|---|---|---|
| M1 | LocalExecutionPolicy evaluator semantics, including check order, reason texts, `__post_init__`, the one-effect rule, target well-formedness and the F2 match-mode vocabulary | W1 rows; S02 §4 | Protected invariants; CA05, CA12, CA18 [R] |
| M2 | Envelope and snapshot validation, payload commitments, attempt state machine, destination commit, durable failure recording | W1 | Lifecycle logic (category H) |
| M3 | Operation admission and qualification | W2 | Admission invariants; W2-025 unresolved |
| M4 | Grant, approval, revocation, recovery, atomic authority-effect logic | W3 | Authority logic (C, H) |
| M5 | Policy-gate rule chain, manifest gate and validation | W4, W5 | Gate logic |
| M6 | Authority, freshness and reversibility admission gates and the `bounded.py` decision flow | W6 to W8 | Gate logic |
| M7 | Closed reason-code and refusal vocabularies | 50 S02 rows. The catalogue's 1,819 entries are a related but different population (mostly other repositories' registries and tables), not the same set [R, I] | External commitments (CA12, CA21); versioned transition required |
| M8 | Serialization and evidence formats [I: this analysis's extension; S02 §4 lists only the mandatory rows and vocabularies] | 90 S02 rows | Integrity-bearing formats |

F2 (target-match vocabulary) is counted in M1; F8 (demo policy lists) is not a policy family (demo literals that nonetheless feed authority records W4-022/023, so it is Tier 2 until reviewed and not a candidate). The adopted floors CR-001 to CR-035 cut across M1 to M8 and are not separately counted.
