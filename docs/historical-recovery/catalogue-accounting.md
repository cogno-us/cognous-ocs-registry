# Catalogue accounting

Denominators for the historical catalogue (`catalogue-v0.1`, manifest digest `sha256:22f49fd1341cfaa6e46727db9b6153c2073b82a3125fd725173494f3ebb37650`, source commit `51c579a3`). Counts marked [V] are recomputed by `recount.py` (output in `recount-output.json`), which also checks the ten denominators and the unresolved accounting equal the manifest; counts marked [R] are read from the catalogue's generated reports and were not recomputed (see the README for the exact scope of `recount.py`). Labels: **[V]** recomputed here, **[R]** reported by the catalogue's generated reports, **[I]** derived classification.

Counts of different things are never summed into one headline. The catalogue itself has no headline scenario count and no combined reason-code figure, by design.

## 1. Layer counts [V]

| Layer | Entries | Note |
|---|---|---|
| L1 rules | 3,190 | rule *entries*; see section 2 for what they are |
| L2 scenarios | 2,840 | classes in section 4 |
| L3 tests | 6,648 | test implementations; 8,177 parametrized instances counted separately |
| L4 fixtures | 2,011 | references and digests; bytes are not copied |
| L5 evidence records | 19,860 | historical execution records, `current_qualification_effect: none` |
| L6 coverage rows | 6,030 | derived projection, not a primary record |
| crosswalk rows | 51,837 | one per raw record (bookkeeping) |
| lineage sets | 2 | `L-nc4-03-history`, `L-prereg-amendments` (both `post_v0_1`) |

Raw-to-canonical absorption [R, integrity report]: rules 3,328 raw to 3,190; scenarios 6,955 to 2,840; tests 15,943 to 6,648; fixtures 3,301 to 2,011.

Crosswalk dispositions [V]: `TEST_INSTANCE_OR_EXECUTION_OCCURRENCE` 31,445; `CANONICAL` 13,345; `SOURCE_ONLY_ARTIFACT` 4,812; `ALIAS_OF` 1,291; `HISTORICAL_REVISION_OF` 693; `ATTACHED_TO_ENTRY` 242; `UNRESOLVED` 9.

## 2. Rules: what the 3,190 entries are

Every entry is a `source_statement` reference (3,190 of 3,190); none is held in an `ocs-registry-record/0` record (`registry_id` unset on all; `manifest.registry_records` is empty). [V] Every entry has `authority: none` and tier `GOVERNANCE_RULE`.

### By catalogue normative type [V]

| `normative_type` | Entries |
|---|---|
| `reason_code_or_refusal_vocabulary` | 1,819 |
| `unknown` | 869 |
| `validator_rule` | 201 |
| `requirement_row` | 134 |
| `principle` | 68 |
| `mandatory` | 39 |
| `constitutional_floor` | 35 |
| `decision` | 15 |
| `advisory` | 10 |

### By adoption status, release scope, MVP applicability [V]

- Adoption: `unknown` 2,926; `proposed_not_adopted` 229 (all from `constitutional-design/drafts/CONSTITUTION_v0.1.md` in the institutional-governance repository); `adopted` 35 (exactly `CR-001` to `CR-035`).
- Release scope: `v0_1` 3,190. No entry is `post_v0_1` or any V0.2 value.
- MVP applicability: `unresolved` 2,978; `requires_unavailable_component` 205 (204 governed-exchange, 1 Qualification `ER-05-7`); `mvp_fixed` 7. None of the 35 adopted floors has a stated applicability.
- The 7 `mvp_fixed` entries, with the basis each states: `R-CP:LIFE:journal_check_reused` (`MB-JCR`, a known defect named by exact code string); `R-D10-cc772787` and `R-D15-3830802f` (`MB-NAMED-LIMIT`, a named known limit or negative control; the entry says `mvp_fixed` here does not mean satisfied or passed); `R-ER-07-2-07bc0c8d` (`MB-NAMED-FAIL`, a known failure carried visibly, no verdict implied); `R-ver-v4-ledger-rows-agree-with-attempts-1c5eb24f` (`MB-V4ABST`, an expected ABSTAIN); `R-ver-verifier-finding-decision-result-inconsistent-5e16d519` and `R-ver-verifier-finding-journal-check-reused-7bb16c1d` (architect MVP decisions Q8, a point-in-time ruling the catalogue README says is not retained in the repository). So `mvp_fixed` means "named in the fixed MVP profile", frequently as a limit or failure, not "enforced" or "passed". It is a historical label and authorizes nothing.

### By source repository [V]

institutional-governance 778; ODES (`open-decision-evidence-standard`) 641; verifier 363; control-plane 349; open-control-stack 347; governed-exchange 204; stack-qualification 171; ergonomics 163; replay-bundle 77; evidence-pack 42; action-manifest 35; execution-runtime 20.

## 3. Mapping to the eight recovery categories [I]

The task requires keeping eight things apart. The catalogue types only some of them. This mapping is derived here from `normative_type` and `adoption_status`; it is a reading of catalogue attributes, not a verification against source text, and it can be wrong at the entry level.

| Recovery category | Rule entries | Derivation |
|---|---|---|
| 1. Governance policy rules (as stated) | 247 | `constitutional_floor` 35 + `principle` 68 + `requirement_row` 134 + `advisory` 10 |
| 2. Mandatory safety / enforcement invariants (candidates) | 240 | `mandatory` 39 (Qualification requirement rows with `mandatory: true`) + `validator_rule` 201. **Enforcement is not established**: every relationship in the catalogue has `establishes_enforcement: false`, and only 11 rules have a source-stated implementation link |
| 3. Configurable policy parameters | 0 | the catalogue has no such type; any candidate is a lexical lead only (see `classification-crosswalk.md`) |
| 4. Reason codes and refusal vocabulary | 1,819 | `reason_code_or_refusal_vocabulary`; 1,662 distinct code names after stripping the `@0.1` registry-version suffix (1,783 distinct raw native ids) |
| 5. Test cases and scenarios | not rules | 2,840 scenarios, 6,648 tests, 2,011 fixtures (sections 4 and 5) |
| 6. Evidence and verification artifacts | not rules | 19,860 evidence records, 6,030 derived coverage rows (section 5) |
| 7. Historical proposals and unimplemented concepts | 244 | `decision` 15 + `proposed_not_adopted` 229 |
| 8. Unresolved or unattributed | 640 | `unknown` type with `unknown` adoption (normative strength not stated) |

247 + 240 + 0 + 1,819 + 244 + 640 = 3,190. [V arithmetic]

Cautions on the mapping:

- The 134 `requirement_row` entries (92 `mandatory: false` Qualification rows and 42 institutional-governance rows) are requirements, not necessarily policy rules. The 39 `mandatory` entries are rows of `process/v1-validation/v1-2026-10-16-a/requirements.json` in Qualification, a requirements file, not enforcement code.
- 201 `validator_rule` entries are error and warning rules of validators (action-manifest 25, Control Plane port 25, evidence-pack 42, replay-bundle 38, verifier 53, ergonomics 18). Whether a validator is wired into an enforcement path is not stated by the entry.
- The 11 entries flagged `refund_specific` are inside the counts above and are not separated.

## 4. Scenario denominators [V]

Ten denominators are kept apart in `manifest.denominators.ten_denominators`; the validator refuses a committed denominator that differs from the recomputed one.

| Denominator | Count |
|---|---|
| Logical governance scenarios, release scope `v0_1` | 271 |
| Logical governance scenarios, `post_v0_1` (reported apart) | 38 |
| Suite-level acceptance scenarios | 42 |
| Adversarial ideas | 103 |
| Specification cases (unexecuted) | 696 |
| Other unexecuted | 146 |
| Test implementations | 6,648 |
| Parametrized test instances | 8,177 |
| Fixtures and input vectors | 2,011 |
| Historical execution records | 19,860 |
| Distinct (run, test node) pairs / distinct runs / runs with run results | 19,509 / 313 / 263 |

Scenario classes (all entries, 2,840): `fixture_defined_case` 1,459; `adversarial_or_unexecuted_spec` 945 (= 103 + 696 + 146); `logical` 309 (= 271 + 38); `other` 78; `suite_level_acceptance` 42; `demo_step` 7. Differential vector instances (2,290) are instances, not scenarios. Scenario release scope: `v0_1` 2,802; `post_v0_1` 38. Test release scope: `v0_1` 6,612; `post_v0_1` 36.

## 5. Evidence and coverage [V unless marked]

- Evidence kinds: `run_result` 18,697; `unknown` 1,153; `validation_claim` 10.
- Historical verdicts quoted verbatim (largest groups of 19,860 records): `PASS` 12,477; `failure` 2,138 (lowercase, a distinct spelling); `(long verdict text, held in the external record)` 1,358; no verdict recorded 1,153; `INCONCLUSIVE` 651; `NOT RUN` 590; `NOT APPLICABLE` 322; `FAIL` 213 (uppercase); `expected=BLOCK; observed=BLOCK; oracle_satisfied=True` 114; `status="completed"; conclusion="success"` 96; `passed` 76; `expected=BLOCK; observed=ALLOW; oracle_satisfied=False` 57; `INCOMPLETE` 4; 24 JUnit-attribute strings together 114. The vocabulary is not normalized (for example `FAIL`, `failure`, `error`, `returncode=1`); the full verbatim list is in `recount-output.json`. The two failure spellings are kept separate and are not summed here. A historical verdict never transfers to a new candidate.
- Governance Coverage Report [R, recomputed by the validator]: for rules, `implementation_coverage` is `source_stated_link` 11, `derived_candidate_only` 51, `none` 3,128; `test_coverage` is `derived_candidate_only` 131, `none` 3,059; `independent_qualification` is `none` for all 3,190. For scenarios: implementation `derived_candidate_only` 1,143, `none` 1,697; test `derived_candidate_only` 70, `none` 2,770; qualification `none` for all 2,840.

## 6. Reason-code accounting [V]

- 1,819 reason-code entries over 1,662 distinct code names (1,783 distinct native ids before stripping the `@0.1` suffix that 121 entries of the 0.1 registry carry; those names also occur unsuffixed in 0.2). Entries and distinct names are different denominators and are not merged.
- Two registry versions are kept apart: `runtime-authority-reasons/0.1` 121 entries and `/0.2` 164 entries. At the Control Plane tag commit `0a41faa9`, the 0.2 file contains all 121 codes of 0.1 plus 43 more. The catalogue holds them as 285 separate entries with no merge, because a version-0.2 entry may not absorb a 0.1 identity.
- Other large groups: verifier findings 131, subtype `refusal_or_reason_code` 676, subtype `reason_code` 92, execution-attempt-lifecycle codes 39 (plus 39 replay-code-mapping rows).

## 7. Duplicates and aliases [V]

- 199 groups of entries share identical `statement_verbatim` text (716 entries); 164 of those groups span more than one repository. The three largest groups are templated verifier statements ("refuted finding code ... emitted by `rules_journal.py`" 53, `rules_lifecycle.py` 31, `ledger.py` 16, `identity.py` 16) and Qualification requirement rows whose statement is a metadata object (for example `{"adequacy": "adequate", "kind": "tests", "mandatory": true}` 28, `"mandatory": false` 9). Such entries carry no rule text beyond metadata; they are counted as entries, not as distinct rules.
- 68 native identifiers occur in more than one repository (for example `E001` in action-manifest, evidence-pack and replay-bundle). The catalogue keeps them as separate entries because equivalence is not established.
- 874 entries list `alias_candidates` (flagged as possibly equal, deliberately not merged); 132 entries carry retained `aliases` (merges with a stated basis). No entry has recorded `lineage`.

## 8. Unresolved accounting [V from manifest]

| Item | Count |
|---|---|
| Entries with unresolved MVP applicability (all layers) | 14,176 (rules 2,978; scenarios 2,793; tests 6,430; fixtures 1,975) |
| Unresolved relationship placeholders | 15,384 (rules 1,206; scenarios 1,825; tests 12,353) |
| Unembedded unresolved relationship rows | 14,456 |
| Evidence records without source revision | 17,704 |
| Evidence records of unclassified kind | 1,153 |
| Entries without source revision (fixtures) | 45 |
| Unresolved crosswalk rows | 9 (`A2:1022`, `A2:1023`, `C:6845` to `C:6847`, `C2:35` to `C2:38`) |
| Load problems recorded | 8 records over 6 kinds (see `unresolved.md` U2) |

The size note in the catalogue README ("about 42 MB, no file over 4 MB") does not match the directory: `catalogue-v0.1/` is 53,940,243 bytes; no single file exceeds 4 MiB (the largest, a gzip artifact, is 4,128,681 bytes, which is above 4,000,000 bytes). [V] The README may count a subset; this is recorded in `unresolved.md`.
