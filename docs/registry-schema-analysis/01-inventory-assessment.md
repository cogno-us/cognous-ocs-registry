# 01 Inventory assessment

Non-authorizing analysis. Labels: [V] verified, [R] reported, [I] inferred.

## 1. Provenance of the historical inventory

- The historical catalogue is `catalogue-v0.1` at source commit `51c579a3…`, manifest digest above [R, per `docs/historical-recovery/source-inventory.md` in PR #13].
- No separate OCS V0.2 release inventory was recovered. The `runtime-authority-reasons/0.2` registry (164 entries) is a vocabulary version label. It is not evidence of an OCS V0.2 release inventory. All 3,190 rules carry `release_scope v0_1` [R].
- PR #13's status is reported in the final report and not repeated as a claim here; this file depends only on the counts below.

## 2. Counts preserved

| Item | Count | Basis |
|---|---|---|
| Rule entries | 3,190 | catalogue [R]; recounted in PR #13 `recount.py` |
| Scenarios | 2,840 | catalogue [R] |
| Tests | 6,648 | catalogue [R] |
| Fixtures | 2,011 | catalogue [R] |
| Evidence records | 19,860 | catalogue [R] |
| Coverage rows | 6,030 | catalogue [R] |
| S02 rows | 620 (354 / 90 / 51 / 50 / 43 / 32) | `docs/s02-inventory.md` §2 [R, recount in PR #13] |

## 3. What a rule entry is

Every catalogue rule is a `source_statement`: a sentence, table row, schema property or error-table entry that a source file contains. Entry types, with the counts the catalogue reports [R]:

| `normative_type` | Entries | Reading for this analysis |
|---|---|---|
| reason_code_or_refusal_vocabulary | 1,819 | a name in a vocabulary; registration is not enforcement |
| unknown | 869 | normative strength not stated |
| validator_rule | 201 | an error condition a validator may raise; not shown to be wired into an enforcement path |
| requirement_row | 134 | a requirement statement; strength per source |
| principle | 68 | guidance [I: this analysis's reading] |
| mandatory | 39 | marked `mandatory: true` in a qualification file; acceptance criterion, not runtime enforcement |
| constitutional_floor | 35 | adopted floors CR-001 to CR-035 |
| decision | 15 | preregistration decisions |
| advisory | 10 | advisory-strength statements; PR #13 groups them with policy statements as stated (validator error and warning rules sit inside `validator_rule`) |

Adoption: adopted 35, proposed_not_adopted 229, unknown 2,926 [R]. The 3,190 entries are therefore **not** 3,190 independently established executable or configurable policies. A validator error code does not establish enforcement; a proposed constitutional clause does not establish adoption; a test fixture does not establish implementation. This analysis applies those three rules throughout.

The catalogue contains no entry typed as a configurable parameter [R, `normative_type` list above].

## 4. Verified source facts, catalogue assertions, worker inference

| Kind | Examples |
|---|---|
| Verified source fact | The effective `max_effects` origin (03 §3); the dedupe TTL guard (03 §3); `allow_synthetic_resolver` consumers (03 §3) |
| Catalogue-reported assertion | adoption status, `mvp_fixed` flags, normative type |
| Worker inference | S02 class assignments, tiers, family groupings |

`mvp_fixed` means named in the fixed MVP profile, often as a limit or a failure. It does not mean enforced or passed [R].

## 5. Absence of a configurable classification

The absence of an explicit configurable classification in the catalogue does not establish that no historical rule is configurable. The catalogue was built from documentation and schema artefacts; the S02 inventory was built from code. Only 369 of 3,190 catalogue entries come from the two repositories S02 inventoried, and only `manifest_validation.py` is covered by both [R, PR #13 crosswalk]. Configurable values live mostly in code constructors and profiles, which the catalogue does not model.

## 6. What the inventory can and cannot support

| Use | Supported? |
|---|---|
| Identify which families have data-shaped values in code today | Yes, from S02 [R], with the source reads in 03 |
| Populate registry records from catalogue entries | No: no entry is a typed parameter, and applicability is unresolved for 2,978 of 3,190 [R] |
| Establish a reason-code vocabulary snapshot as reference data | Possible later; names exist, but registry versions 0.1 and 0.2 coexist and no ruling exists on their relationship |
| Claim completeness | No; S02 is bounded and not exhaustive |
