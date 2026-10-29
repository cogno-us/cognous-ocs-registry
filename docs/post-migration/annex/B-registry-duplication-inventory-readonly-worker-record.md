# Registry R1 duplication / architecture inventory (read-only, T0 inspection)

Subject: `cogno-us/cognous-ocs-registry` clone at `/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/cognous-ocs-registry`
`git rev-parse HEAD` = `2815643c3e15fbc6aadadbf88dc7596f10120992` (matches the required head; re-checked at the end of the inspection).
Date: 2026-10-29. Worker role: read-only inspection. No tracked repository file was modified, nothing was committed or pushed, the test suites were not run (only `pytest --collect-only`).

Documents read first: `docs/plans/REGISTRY-R1-POST19-CONSOLIDATION-PLAN-v1.0.md` (sections 2, 5, 7), `docs/family-migration/IMPLEMENTATION-CLOSEOUT-2026-10-29.md`, `docs/r08-v8-contract.md`, and the frozen-baseline tests/manifests (`tests/test_r08v{3..8}_frozen_baseline.py`, `tests/vectors/r08v{3..8}/frozen_baseline_manifest.json`).

Process disclosures (honesty notes):
- While probing network availability I ran `pip download pynacl` from inside the clone, which dropped three `.whl` files in the clone root (untracked). I moved them to `.../r1/out/wheels/` immediately and removed the `__pycache__` directories my runs had created; `git status` afterwards showed no tracked change. PyNaCl 1.6.2 (from those local wheels) was then installed with `pip install --no-index --target .../r1/out/site` so that a few read-only profiling scripts and `--collect-only` could import the Ed25519 test backend. Nothing was installed into the system Python.
- The clone is shared: during the inspection another actor staged `docs/post-migration/**` (`git status` shows three `A` entries). No tracked file under `registry_*` or `tests/` changed (`git diff --stat HEAD -- registry_successor tests registry_*` empty) and HEAD did not move.
- The `out/` directory also holds files written by other workers (e.g. `archD.md`, `scripts/`); I only wrote `registry-inventory.md` and my own helper scripts/outputs listed in the Measurements section.

---

## 0. Headline findings (all measured, see section 3 and section 4)

1. **Almost everything that is duplicated is byte-frozen.** All 77 non-doc `registry_*/**` files hashed in `tests/vectors/r08v8/frozen_baseline_manifest.json` still match their baseline bytes at HEAD (script `hashcheck`, section 4.1), i.e. the whole per-version tree `v2_*`..`v6_*`, `v7_*`, the base `verify/selection/record/decision/families/compose/common`, and the engine files `engine/{__init__,decide,record,selection,verify,families_irreversibility}.py`. Only `engine/{profile,identity,profiles}.py` (additive edits pinned line by line) and the new v8 files (`v8_*.py`, `engine/families_anchor.py`, `engine/families_observation.py`) and the v8 tests are outside the byte hashes. Per plan section 2 the recommendation for these is "leave byte-identical; consolidate only new/shared path".
2. **The measured duplicate mass is large but historical:** `v4/v5/v6` `verify`, `selection` and `record` are AST-identical to the `v3` copy after version-token normalization: 1,026 code lines (1,230 physical lines) = 11.0 % of the 9,345 code lines of `registry_successor/` (19.5 % when the 2,863-line data table `v2_token_table.py` is excluded from the denominator). The `v4..v6` decision modules add 237 code lines (307 physical) that are 91.2 %..98.7 % line-identical to `v3_decision.py`. Combined 13.5 % of code lines (12.9 % of physical lines).
3. **The consolidation the plan asks for in R2 already exists for new versions:** the per-version cost of a contract version was 850/901/837/993 physical lines for r08-v3..v6 (mean 895) versus 101 (v7) and 110 (v8) lines of per-version modules on the unified engine (`registry_successor/engine/`, 1,290 lines). Including the family modules the new version needs: v7 = 101 + 149 (`engine/families_irreversibility.py`) = 250; v8 = 110 + 125 + 140 = 375.
4. **Expected production-line reduction under the plan constraints is approximately zero.** Every in-place consolidation of v3..v6 is blocked by byte-pin tests and by `tests/test_r08v8_frozen_baseline.py::test_no_frozen_module_imports_the_engine_a_v7_or_a_v8_module` (frozen modules may not import the engine). The only ACCIDENTAL_DUPLICATION candidates that live in not-pinned files total about 34 lines (REG-8 and REG-20) and I recommend not touching them.
5. **No unnecessary runtime dependency found.** The Registry core is standard-library only; the only third-party production import is `nacl` (lazy, inside `registry_adapters/ed25519_verifier.py`) and the vendored baseline runtime `engine.safe_executor` (in `registry_consumer/consumer.py`). `cryptography` is test-only and used by one test file.
6. **Repeated work per decision is real but small and deliberate:** one `verify_and_decide_v8` call computes 8 `common.digest` values (6 are re-checks of the record digests, 2 of the statement digest) and 10 `parse_timestamp` calls over 4 distinct strings. Measured share of a 984 microsecond decision: 7.6 % + 2.9 % + 7.6 % (overlapping upper bound about 18 %). All of it sits in byte-frozen files and is documented as defence in depth; no change recommended.

---

## 1. Summary table

Classification legend: DSR = DELIBERATE_SECURITY_REDUNDANCY, IB = INDEPENDENT_BOUNDARY, HC = HISTORICAL_COMPATIBILITY (byte-frozen or frozen contract), AD = ACCIDENTAL_DUPLICATION.
Tier legend (my proposal): T0 documentation/inspection only; T3 shared contract and boundary (the tier recorded for r08-v8 in `docs/r08-v8-contract.md` section 9); T4 protected/frozen change.

| ID | Candidate | Files | Measured | Class | Proposed action | Tier | Frozen? |
|---|---|---|---|---|---|---|---|
| REG-1 | `v3..v6_verify.py` orchestration copies | `registry_successor/v{3,4,5,6}_verify.py` 1-244 | 4 x 244 lines; AST-identical after version-token normalization (198 AST lines each); 99.2..100 % token-normalized | HC | leave byte-identical; record residual duplication | T0 | yes, STOP-ARCHITECT only for delegation |
| REG-2 | `v3..v6_selection.py` copies | `v{3,4,5,6}_selection.py` 1-124 | 4 x 124; AST-identical | HC | leave; record | T0 | yes |
| REG-3 | `v3..v6_record.py` copies | `v{3,4,5,6}_record.py` 1-42 | 4 x 42; AST-identical | HC | leave; record | T0 | yes |
| REG-4 | `v3..v6_decision.py` copies | `v{3,4,5,6}_decision.py` 1-99/108 | 237 code lines in v4..v6; 91.2..98.7 % AST-line match | HC | leave; record | T0 | yes |
| REG-5 | per-version identity triplets | `v{3..6}_policy_identity.py`, `v2_policy_identity.py` 1242-1257 | 4 triplets (`effective_preimage`, `effective_digest_of_preimage`, `effective_policy_digest`) + engine; one shared hash site `v2_policy_identity._sha` | HC | leave; note single digest primitive already shared | T0 | yes |
| REG-6 | `v3..v6_families.py` dispatch tables | `v{3,4,5,6}_families.py` | 80/80/81/93 lines; 54.8..66.2 % pairwise | HC | leave | T0 | yes |
| REG-7 | typed per-family validators | `v3_f1abc`, `v4_f1abcd`, `v5_class_unreadable`, `v6_class_revocation_assurance`, `v6_terminal_revocation`, `engine/families_{irreversibility,anchor,observation}` | 20.1..82.9 % pairwise AST-line match | IB | keep explicit (plan section 5) | none | partly (v8 pair unfrozen) |
| REG-8 | 17 identical 3-line `_refuse` helpers | 17 files (listed in record) | 17 x 3 lines; one `compose._refuse` exists | AD | do not change (value 6 lines in unpinned files) | T0 | 15 of 17 frozen |
| REG-9 | per-version domain constants | `SIGNING_DOMAIN_V*`, `EFFECTIVE_PREFIX`, `engine/profiles.py` | 6 selection + 6 effective domains | DSR | untouched | none | yes |
| REG-10 | legacy `verify.py` `_verify`/`_authenticity` vs engine | `verify.py` 435-487, 538-695; `engine/verify.py` 33-79, 82-230 | 75.8 % line match (`_verify`); 731-line file | HC | leave | T0 | yes |
| REG-11 | repeated digest recomputation per decision | `engine/record.py` 36-38, `verify.py` 418-419, `engine/decide.py` 75-76, `engine/selection.py` 110, `engine/verify.py` 118 | 8 digests/decision; 75 us + 29 us of 984 us | DSR | untouched | none | yes |
| REG-12 | repeated timestamp parse / private copies | `engine/selection.py` 80-84 (statement_code, called twice), `engine/verify.py` | 10 calls, 4 distinct strings; 75 us (7.6 %) | DSR | untouched | none | yes |
| REG-13 | `v7_*` / `v8_*` thin binding modules | `v7_*.py` (101 lines), `v8_*.py` (110 lines) | `v7_policy_identity` and `v8_policy_identity` AST-identical modulo profile name (29 lines) | IB | keep (public per-contract API, hardwired version) | none | v7 frozen, v8 candidate |
| REG-14 | `V6_COMPAT` adapter + engine differential | `engine/profiles.py` 90-97, `tests/test_r08v7_engine_differential.py` | reachable only from tests | HC | keep; reuse as R2 oracle | none | yes |
| REG-15 | per-version entry modules with no in-repo production importer | `v3..v8_decision.py`, `v3..v5_policy_identity.py`, `v7/v8_{families,policy_identity}.py` | 0 production importers, tests only | IB | keep; external consumer use UNVERIFIED | none | mostly frozen |
| REG-16 | unreferenced names in frozen identity module | `v2_policy_identity.py` 716, 94 | 2 names, 0 references | HC | leave | T0 | yes |
| REG-17 | independent canonical-JSON / digest / sha-regex sites | `common.py` 102-107, `registry_contract/validator.py` 74-79, `registry_conformance/highwater.py` 99, `v2_policy_identity.py` 290-330 | 4 canonicalizers, 6 sha regexes | IB | keep | none | yes |
| REG-18 | dependencies / lock files | `requirements-*.lock.txt` | 309 lines, 3 locks; prod third-party: `nacl` only | IB | no change | none | n/a |
| REG-19 | near-identical per-version tests and support files | `tests/test_r08v{3..7}_*`, `tests/r08v{3..7}_support.py` | 423 redundant function-body lines in 49 groups among pinned test files; `decision_path` v3 vs v4 98.7 % | HC | leave | T0 | yes (34 test .py pinned) |
| REG-20 | duplicates inside the unpinned v8 tests | `tests/r08v8_support.py` 88, `test_r08v8_frozen_baseline.py` 49, `test_r08v8_policy_identity.py` 39/54, `test_r08v8_engine_profile.py` 148 | 5 functions, 28 lines | AD | do not change (value 28 lines) | T0 | no |
| REG-21 | cumulative frozen-baseline manifests | `tests/vectors/r08v{3..8}/frozen_baseline_manifest.json` | 1,004 pin rows for 213 unique paths, 0 hash conflicts | HC | leave | none | yes |
| REG-22 | per-version evidence scripts and vectors | `docs/**/evidence/*.py` (26 files), `tests/vectors/r08v*/` (30 files, 968 KB) | mutation harnesses 3.5..28.8 % similar | HC | add-only; reuse | none | records |

Counts by classification: HC 12 (REG-1,2,3,4,5,6,10,14,16,19,21,22), IB 5 (REG-7,13,15,17,18), DSR 3 (REG-9,11,12), AD 2 (REG-8,20). Total 22.
STOP-ARCHITECT items: REG-1..REG-6, REG-10 and REG-19 *only if* someone proposes to change the bytes of the frozen files in place or to make a frozen module import the engine (delegation). The inspection does not recommend that. Additional STOP-ARCHITECT trigger discovered: any edit of a file that existed at baseline `67512a71546748cd888e4cf790485ea0bef9199a` outside the allowlist trips `tests/test_r08v8_frozen_baseline.py::test_every_other_committed_file_is_unchanged_from_main_except_the_allowlisted_edits` (it would need a guard allowlist edit, which is itself a protected guard change).

---

## 2. Detail records

Common facts used by several records (so each record can stay short):

- **Pinning tests (all named tests exist in the repo).** Byte pin: `tests/test_r08v8_frozen_baseline.py::test_frozen_file_is_byte_identical_to_the_baseline` (parametrized per manifest path; same name in `test_r08v{3,4,5,6,7}_frozen_baseline.py`); manifest extension: `test_r08v8_frozen_baseline.py::test_the_manifest_extends_the_r08_v7_manifest_without_changing_any_hash`; additive-edit pins for the three engine files: `test_the_additive_edit_reverses_to_the_baseline_byte_for_byte`, `test_the_additive_edits_are_pure_insertions_apart_from_the_pinned_comment_and_kind_lines`, `test_the_inserted_identity_lines_are_exactly_the_scalar_int_branch`; import fence: `test_no_frozen_module_imports_the_engine_a_v7_or_a_v8_module` and the per-version `test_no_frozen_module_imports_an_r08_v{3,4,5,6}_module`; whole-tree tripwire: `test_every_other_committed_file_is_unchanged_from_main_except_the_allowlisted_edits` (git diff vs baseline, `--diff-filter=MDRT`). The tripwire's baseline commit is present in this clone, so it is not skipped; by static prediction (`git diff --name-only --diff-filter=MDRT 67512a7 HEAD` lists `docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`, which is not in the allowlist) it fails at HEAD, like the v7 variant that `docs/r08-v8-contract.md` section 8 documents as a pre-existing failure. **Not executed; UNVERIFIED.**
- **Orchestration-equality pins (the copies are asserted equal on purpose):** `tests/test_r08v5_frozen_baseline.py::test_v5_verify_orchestration_is_the_v4_orchestration_modulo_version_names`, `::test_v5_decision_orchestration_is_the_v4_orchestration_modulo_version_names`, `::test_v5_selection_statement_shape_and_layers_are_the_v4_ones`; `tests/test_r08v6_frozen_baseline.py::test_v6_verify_orchestration_is_the_v5_orchestration_modulo_version_names`, `::test_v6_decision_orchestration_is_the_v5_orchestration_modulo_version_names`, `::test_v6_record_and_selection_are_the_v5_ones_modulo_version_names`, `::test_v6_selection_statement_shape_and_layers_are_the_v5_ones`. v3 and v4 have no `modulo_version_names` test (only byte pins and import fences).
- **Engine equivalence oracle (reusable evidence):** `tests/test_r08v7_engine_differential.py` (543 lines, 23 collected cases; module is skipped when PyNaCl is absent): `::test_one_axis_at_a_time_hostile_variations_are_identical`, `::test_seeded_random_combinations_are_identical`, `::test_verification_reports_parse_and_validation_results_are_identical`, `::test_identity_digests_preimages_and_refusals_are_identical_over_a_hostile_grid`, `::test_signing_input_and_domains_are_identical`, `::test_the_pinned_v6_signed_vectors_decide_identically_and_to_the_pinned_effective_policy`, `::test_every_document_is_accepted_only_by_its_own_contract_and_refused_everywhere_else`, `::test_a_signature_over_another_contracts_domain_never_verifies_under_this_one`; plus `tests/test_r08v7_engine_profile.py::test_engine_calls_the_same_shared_helpers_as_the_frozen_orchestration`, `::test_a_third_profile_runs_on_the_same_engine_and_is_isolated_from_the_others`, and `tests/test_r08v8_cross_version.py` (17 cases, collected only with PyNaCl). Mutation harnesses: `docs/family-migration/unified-engine/evidence/mut_r7.py` (177 lines), `docs/family-migration/final-three-prep/evidence/mut_r8.py` (150 lines). Pinned vectors: `tests/vectors/r08v{3..8}/identity_vectors.json`, `signed_selection_vector.json`.
- **Shared helpers that already exist (source-backed, so no new abstraction is needed):** `registry_successor/verify.py` is imported by every orchestration (`v3..v6_verify.py` and `engine/verify.py` import it as `v`) for `_private_selection/_private_record/_private_trust/_private_context/_private_now`, `_normalize_trust`, `_admission_failure`, `_record_binding`, `_floor_outcome`, `VerificationReport`, `LAYERS_V2`; `v2_policy_identity._sha`/`_plain`/`_serialize` is the one digest primitive for all effective-policy digests (`engine/identity.py:104`, `v3..v6_policy_identity.py` `effective_digest_of_preimage`); `engine/profile.py` `lookup/table_for_contract_version/compose/compose_for` replaces the per-version `v*_families.py` bodies for v7/v8; `compose._refuse` exists (REG-8).
- **Effort figures are estimates (not measured).** Reversibility: documentation items are fully reversible; any change to a pinned file is reversible only by git revert plus guard-test re-pinning, and re-pinning is itself a protected change.

### REG-1: `v3_verify.py`, `v4_verify.py`, `v5_verify.py`, `v6_verify.py` (verification orchestration)
- Files and ranges: each file 1-244: `_authenticity_vN` 36-82, `_verify_vN` 85-233, `verify_selection_vN` 236-244. Related: `engine/verify.py` 1-243 (`_authenticity` 33-79, `_verify` 82-230, `verify_selection` 233-243); `verify.py` `_verify` 538-695.
- Current behavior: five hand-copied implementations of the same layered verification (structural, integrity, record_binding, trust_snapshot, authenticity, authority, scope, time, revocation, epoch, disposition) that differ only in the hard-wired contract constants (`V{N}_CONTRACT`, `v{N}_sel.signing_input_v{N}`, `v{N}_sel._statement_code_v{N}`). `engine/verify.py` is the single parameterised implementation used by v7/v8 (and by `V6_COMPAT`).
- Measured: no two of the 25 files compared are byte-identical (`sha256sum`). Plain `diff` line match: v3 vs v4/v5/v6 = 212 of 244 lines (86.9 %), the rest is docstring and names. Version-token-normalized line match: v3=v4 100 %; v3/v4 vs v5 243/244 (99.6 %); vs v6 242/244 (99.2 %); v5 vs v6 243/244 (99.6 %); the residual lines are docstring sentences only. After removing docstrings and normalizing tokens the ASTs of all four are identical (198 AST lines each; `astcmp.py`). v6 vs `engine/verify.py`: 207/244 plain (84.8 %), 178/199 AST lines (89.4 %). `verify._verify` (158 lines) vs `_verify_v6` (149): 113/149 normalized lines (75.8 %), the difference being the `contract_version`/`v2`/`canonical_b64` switches.
- Classification: **HISTORICAL_COMPATIBILITY** (byte-frozen, signature-domain bearing, contract `r08-v3`..`r08-v6`).
- Pins: byte pin `tests/test_r08v{3,4,5,6}_frozen_baseline.py::test_frozen_file_is_byte_identical_to_the_baseline` (all four verify files are in the cumulative manifests); copy-equality pin `test_r08v5_frozen_baseline.py::test_v5_verify_orchestration_is_the_v4_orchestration_modulo_version_names`, `test_r08v6_frozen_baseline.py::test_v6_verify_orchestration_is_the_v5_orchestration_modulo_version_names`.
- Proposed minimum refactoring: **none in place.** "Leave byte-identical; consolidate only new/shared path." Record the 4 x 244-line residual duplication in the R1 baseline as the plan section 5 last bullet requires. Any future contract version must use an engine profile (already the rule for v7/v8).
- Expected simplification: 0 lines under the plan constraints. Duplicate mass for the record: v4+v5+v6 = 3 x 244 = 732 physical (627 code) lines identical to the v3 copy. A hypothetical delegation of v3..v6 to the engine would remove roughly that mass minus shim bodies; that figure is an **estimate, not measured, and not recommended**.
- Changed reachability: none. Contract impact: none if untouched; delegation would change frozen bytes (STOP-ARCHITECT) and would need an exception to the import fence.
- Risk tier: T0 (documentation). Delegation variant: T4.
- Necessary tests: the pins above plus the full differential oracle (common facts) if delegation were ever authorized.
- Reusable evidence: common facts (engine differential, mutation harnesses, vectors).
- Effort estimate: S, 1-2 h to document. Delegation variant (not recommended): L, 40+ h plus F3 requalification (estimate).
- Reversibility: documentation fully reversible.
- STOP-ARCHITECT: only for the delegation variant.

### REG-2: `v3_selection.py`..`v6_selection.py`
- Ranges: 1-124 each: `signing_input_vN` 27-28, `_no` 31-33, `_statement_code_vN` 36-90, `_parse` 93-116, `parse_selection_envelope_vN` 119-124. Related: `engine/selection.py` 1-122, `v2_selection.py` 1-127, `selection.py` 1-247.
- Current behavior: per-version closed statement shape, envelope parser and signing input; the only semantic differences are the domain constant `SIGNING_DOMAIN_VN` and the family table.
- Measured: plain line match 85.5 % pairwise (106/124); token-normalized v3=v4=v5 100 %, v6 differs by one docstring line (123/124); AST identical for all four (104 AST lines). v6 vs engine: 100/124 plain (80.6 %), 89/104 AST lines (85.6 %).
- Classification: **HISTORICAL_COMPATIBILITY**. Domain separation inside (`SIGNING_DOMAIN_VN`) is DELIBERATE and see REG-9.
- Pins: byte pins as REG-1; `test_r08v6_frozen_baseline.py::test_v6_record_and_selection_are_the_v5_ones_modulo_version_names`, `::test_v6_selection_statement_shape_and_layers_are_the_v5_ones`.
- Proposed refactoring: none in place; leave byte-identical.
- Expected simplification: 0 lines. Duplicate mass v4..v6: 3 x 124 = 372 physical (300 code) lines.
- Reachability/contract impact: none if untouched.
- Tier T0. Tests: pins + differential `::test_signing_input_and_domains_are_identical`. Evidence: common facts. Effort S (0.5 h). Reversibility full. STOP-ARCHITECT only for in-place change.

### REG-3: `v3_record.py`..`v6_record.py`
- Ranges: 1-42 each (`validate_record_text_vN` 15-42). Related: `engine/record.py` 1-42, `record.py` 1-132.
- Measured: AST identical for all four (34 AST lines); plain match v3 vs v4/v5 83.3 %, vs v6 81.0 %; token-normalized v3=v4 100 %, v5 97.6 %, v6 92.9 % (docstring text). v6 vs engine 33/42 plain (78.6 %), 30/35 AST (85.7 %).
- Classification: **HISTORICAL_COMPATIBILITY**. Pins as REG-1 and `test_v6_record_and_selection_are_the_v5_ones_modulo_version_names`.
- Proposed: none. Expected simplification 0; duplicate mass v4..v6 = 126 physical (99 code) lines. Tier T0, effort S (0.5 h), reversibility full.
- Note: each file contains the record-digest and payload-digest recomputation (lines 36 and 38), counted in REG-11.

### REG-4: `v3_decision.py`..`v6_decision.py`
- Ranges: v3/v4 `_refusal` 27-40, `_decide_verified` 43-80, `verify_and_decide_vN` 83-99; v5 28-41, 44-81, 84-100; v6 33-49, 52-89, 92-108. Related: `engine/decide.py` (`_refusal` 28-44, `decide_verified` 47-86, `verify_and_decide` 89-106), `decision.py` 1-206.
- Current behavior: per-version verify-and-decide orchestration. Differences: the optional-participation normalizer (v3/v4/v5: one family lookup; v6: loop over two families), the imported modules.
- Measured: AST-line match to v3: v4 98.7 %, v5 97.4 %, v6 91.2 %; v6 vs `engine/decide.py` 58.8 %. v4+v5+v6 = 237 code lines (307 physical).
- Classification: **HISTORICAL_COMPATIBILITY**. The refusal mapping and final record re-check are DELIBERATE_SECURITY_REDUNDANCY and must survive any consolidation (REG-11).
- Pins: byte pins; `test_r08v5_frozen_baseline.py::test_v5_decision_orchestration_is_the_v4_orchestration_modulo_version_names`, `test_r08v6_frozen_baseline.py::test_v6_decision_orchestration_is_the_v5_orchestration_modulo_version_names`.
- Proposed: none in place. Simplification 0. Tier T0. Effort S (0.5 h). Reversibility full.

### REG-5: effective-policy identity construction sites
- Sites (functions `effective_preimage`, `effective_digest_of_preimage`, `effective_policy_digest`): `v2_policy_identity.py` 1242-1257; `v3_policy_identity.py` 93-106; `v4_policy_identity.py` 106-119; `v5_policy_identity.py` 84-97; `v6_policy_identity.py` 95-108; `engine/identity.py` 92-108 (parameterised); `v7_policy_identity.py` 37-46 and `v8_policy_identity.py` 37-46 (delegating).
- Current behavior: each version re-declares the three functions, `EFFECTIVE_PREFIX` and its family-row table; every one of them bottoms out in the single hashing primitive `v2_policy_identity._sha(prefix, value)` (`v2_policy_identity.py` 332), which uses the hostile-input-bounded `_plain`/`_serialize` canonicalizer. So there is exactly **one** digest/commitment primitive in the successor and 7 thin per-version wrappers (+1 engine wrapper).
- Measured: `effective_preimage..effective_policy_digest` bodies: v3 and v4 hash-identical (md5 of the source slice), v5 and v6 hash-identical; whole-file AST-line match v3-v4 84.1 %, v5-v6 69.3 %, v3-v6 65.3 %. `v7_policy_identity.py` vs `v8_policy_identity.py`: AST identical (29 lines), 71.7 % plain. 40 `c.digest(` call sites exist in `registry_successor/` (19 for `record_digest`, 13 for `statement`, 14 for `payload`; some lines match two patterns), plus 7 `c.canonical_bytes(` signing-input sites.
- Classification: **HISTORICAL_COMPATIBILITY** (frozen identity vectors `tests/vectors/r08v{3..8}/identity_vectors.json`); the per-version domain prefix is DELIBERATE_SECURITY_REDUNDANCY (REG-9).
- Pins: byte pins; identity vectors via `tests/test_r08v{3,4,5,6,7,8}_policy_identity.py::test_pinned_vectors` (v8) and equivalents; differential `::test_identity_digests_preimages_and_refusals_are_identical_over_a_hostile_grid`.
- Proposed: none. No new abstraction is needed; the shared primitive already exists. Simplification 0. Tier T0, effort S (0.5 h). Changed identity if touched: yes (digests), hence T4.

### REG-6: `v3_families.py`..`v6_families.py`
- Ranges: `v3_families.py` 34-80 (`lookup_v3` 34, `table_for_contract_version_v3` 44, `_refuse` 52, `compose_v3` 57, `compose_for_v3` 76); v4 same shape (80 lines); v5 81 lines; v6 93 lines; engine replacement `engine/profile.py` 102-149.
- Measured: pairwise plain match v3-v4 66.2 %, v3-v5 63.0 %, v3-v6 54.8 %, v5-v6 57.0 %; `v7_families.py` (35 lines) and `v8_families.py` (44 lines) are the thin form; v7 vs v8 AST 40.9 % plain only because v8 has three families.
- Classification: **HISTORICAL_COMPATIBILITY**. Pins: byte pins; `tests/test_r08v6_frozen_baseline.py::test_earlier_tables_are_unchanged_by_the_new_families`, `::test_frozen_entry_points_still_refuse_r08_v6`.
- Proposed: none. Simplification 0. Tier T0, effort S (0.5 h).

### REG-7: typed per-family validators and composers
- Files: `v3_f1abc.py` (155), `v4_f1abcd.py` (193), `v5_class_unreadable.py` (149), `v6_class_revocation_assurance.py` (149), `v6_terminal_revocation.py` (125), `engine/families_irreversibility.py` (149), `engine/families_anchor.py` (125), `engine/families_observation.py` (140).
- Measured (AST-line match): `v5_class_unreadable` vs `v6_class_revocation_assurance` 82.9 %; `v5_class_unreadable` vs `engine/families_irreversibility` 81.3 %; `families_anchor` vs `families_observation` 41.4 %; `families_observation` vs `v4_f1abcd` 20.1 %.
- Classification: **INDEPENDENT_BOUNDARY**. Each is the typed, explicit domain validator and mathematical narrowing relation of one family; plan section 5 says to keep these explicit and not to replace them with a programmable policy interpreter. The v8 pair is additionally fenced by `tests/test_r08v8_ast_scan.py::test_family_modules_do_not_import_each_other_or_any_other_family_or_the_profiles` and `::test_no_mutable_module_global_and_no_class_state`.
- Proposed: none. Do not extract a shared validator base. Tier none. Effort none.

### REG-8: 17 identical `_refuse(code, detail) -> CompositionResult` helpers
- Sites (all 3 lines, identical body `assert code in c.CODES, code; return CompositionResult(False, code, detail)`): `compose.py:24`, `families.py:168`, `v2_f1ab.py:73`, `v2_age_bounds.py:161`, `v3_f1abc.py:114`, `v3_families.py:52`, `v4_f1abcd.py:148`, `v4_families.py:52`, `v5_class_unreadable.py:107`, `v5_families.py:53`, `v6_class_revocation_assurance.py:107`, `v6_terminal_revocation.py:87`, `v6_families.py:65`, `engine/families_irreversibility.py:107`, `engine/families_anchor.py:88`, `engine/families_observation.py:103`, `engine/profile.py:121` (md5 of the unparsed body identical for all 17; `record.py:34` and `v2_policy_identity.py:161` are different helpers). Related plumbing: `_refusal` for `PolicyDecision` exists in `decision.py:46` and 5 per-version copies (`v3_decision.py:27`, `v4_decision.py:27`, `v5_decision.py:28`, `v6_decision.py:33`, `engine/decide.py:28`); `mark(...)` inside each `_verify_vN`; `assert code in CODES` appears once in each of 38 modules.
- Shared helper that already exists: `compose._refuse` (`compose.py` 24-26; underscore-private).
- Classification: **ACCIDENTAL_DUPLICATION** in the narrow sense, but 15 of 17 copies are byte-frozen and the two unfrozen ones (`engine/families_anchor.py:88`, `engine/families_observation.py:103`) are fenced by `tests/test_r08v8_ast_scan.py::test_every_refusal_call_in_the_family_modules_uses_a_literal_code_of_the_closed_vocabulary` (it inspects local `_refuse` call sites by name) and by the import allowlist in `::test_family_modules_do_not_import_each_other_or_any_other_family_or_the_profiles`.
- Proposed minimum refactoring: none recommended. Replacing the two unfrozen copies would save 6 lines and require editing the AST-scan guard.
- Expected simplification: measured 6 lines (2 x 3) in unpinned files; the other 45 lines are in frozen files. Not worth a T3 change.
- Contract impact: none. Tier T0 (note only). Effort S (0.5 h). Reversibility full. STOP-ARCHITECT: no.

### REG-9: per-version domain constants (signature domains and effective-policy domains)
- Sites: selection signing domains `selection.py:27` (`ocs-reg/r08-v1/selection\n`), `v2_selection.py:22`, `v3_selection.py:20`, `v4_selection.py:20`, `v5_selection.py:20`, `v6_selection.py:20`, `engine/profiles.py:29` (v7), `:52` (v8); effective-policy domains `v2_policy_identity.py:101`, `v3_policy_identity.py:27`, `v4_policy_identity.py:30`, `v5_policy_identity.py:26`, `v6_policy_identity.py:26`, `engine/profiles.py:30` (v7), `:53` (v8). Test-side independent copies: `tests/r08v{5,6,7,8}_support.py` (`V*_DOMAIN`).
- Classification: **DELIBERATE_SECURITY_REDUNDANCY**: domain separation by contract version (plan section 5: a v6 signature must never validate a v7 selection). The duplicated tests constants are an independent oracle on purpose.
- Proposed: untouched. Tests that must stay green: `tests/test_r08v6_frozen_baseline.py::test_a_v5_signature_over_a_v6_statement_does_not_verify`, `tests/test_r08v8_cross_version.py::test_a_v7_signature_does_not_verify_a_v8_statement_and_the_reverse`, `::test_a_v8_family_selection_signed_over_another_contracts_domain_never_verifies`, `tests/test_r08v8_engine_profile.py::test_the_shipped_profiles_have_pairwise_distinct_domains_and_versions`, `tests/test_r08v8_policy_identity.py::test_domains_are_separated_and_no_other_identity_accepts_these_families`. Tier: none. Simplification 0 by design.

### REG-10: legacy `verify.py` orchestration vs the engine
- Ranges: `verify.py` 731 lines: `_authenticity` 435-487 (53 lines), `_verify` 538-695 (158 lines), `verify_selection_v2` 698, `verify_selection` 714-731; helper block 101-433 and 490-535 is shared by all orchestrations. `engine/verify.py` `_authenticity` 33-79 (47), `_verify` 82-230 (149).
- Measured: `_authenticity` differs by the `canonical_b64`/`v2` switches (r08-v1 used plain `base64.b64decode(validate=True)`); `_verify` v6 vs `verify._verify` 75.8 % normalized lines. `verify.py` is 24.5 % identical (physical) to each per-version `v*_verify.py` because the helpers are not copied: they are imported.
- Classification: **HISTORICAL_COMPATIBILITY** (the r08-v1/r08-v2 readers; golden replay `tests/test_r08v2_golden_replay.py` and `tests/golden/`). Proposed: leave byte-identical. Tier T0. Effort S.

### REG-11: repeated digest recomputation inside one decision
- Sites: record digest and payload digest recomputed at `engine/record.py:36,38` (validation), `verify.py:418-419` (`_record_binding`), `engine/decide.py:75-76` (final check, plus pin comparison at `:77`); statement digest at `engine/selection.py:110` (`_parse`) and `engine/verify.py:118`. The same pattern exists in `v3..v6_decision.py` / `v3..v6_record.py` / `v3..v6_verify.py`.
- Measured with cProfile call counts (script `profile_callers.py`, one `verify_and_decide_v8` call): 8 `common.digest` calls (selection `_parse` 1, `decide_verified` 2, `validate_record_text` 2, `_record_binding` 2, `_verify` 1) and 9 `canonical_bytes` calls (8 from digest + 1 signing input). Timing (script `time_decide.py`, 3,000 iterations, record 1,123 bytes, selection 1,305 bytes): mean decision 984 us; one record digest pair 25.0 us, one statement digest 14.3 us; 3 record-digest pairs = 75 us (7.6 %), 2 statement digests = 29 us (2.9 %).
- Classification: **DELIBERATE_SECURITY_REDUNDANCY**. The code comments say "defense in depth" / "record content was altered after validation" (`engine/decide.py:75-80`) and this is the TOCTOU re-check on the object actually composed; plan section 5 requires the final composed-policy check to be preserved. All files are byte-frozen.
- Proposed: untouched. Expected simplification: none claimed. Tier none.

### REG-12: repeated timestamp parsing and private copies
- Measured (script `ts_args.py`): 10 `common.parse_timestamp` (each `strptime`) calls per decision over 4 distinct strings: 6 calls re-parse the three statement time fields (`engine/selection.py:80-84` run once at parse and again from `engine/verify.py` through the "re-check the closed statement shape on the private copy" step), 1 in the base `record.py:84`, 1 trust validity in the base `verify.py:194`, 2 in `engine/verify.py:185,207`. Cost 7.5 us each, 75 us total = 7.6 % of the 984 us decision. `_json_copy` runs 61 times per decision (private copies of selection, record, trust, context, now), part of the exact-type hostile-input boundary.
- Classification: **DELIBERATE_SECURITY_REDUNDANCY** (re-validation on the private copy, `engine/verify.py:107-110` comment). Frozen files. Proposed: untouched; if the Architect ever wants a perf change it is a T4 behavior-adjacent change.
- Not measured: wall-clock share of Ed25519 verification (the dominant remaining cost under cProfile was `strptime` 14 % and `all()` 12 % of profiled time; cProfile inflates small calls).

### REG-13: `v7_*.py` and `v8_*.py` thin bindings
- Files: `v7_decision.py` 20 lines (9 code), `v7_families.py` 35 (16), `v7_policy_identity.py` 46 (24); `v8_decision.py` 20 (9), `v8_families.py` 44 (22), `v8_policy_identity.py` 46 (24).
- Measured: `v7_policy_identity.py` vs `v8_policy_identity.py` AST-identical (29 AST lines, the only differences are `_profiles.V7` vs `V8` and docstrings). Each public function is a single `return` of an engine call (`docs/r08-v8-contract.md` section 5; `tests/test_r08v8_engine_profile.py::test_the_public_v8_modules_are_thin_bindings_to_the_engine`).
- Classification: **INDEPENDENT_BOUNDARY**. They are the public per-contract API the Control Plane consumer calls (`docs/r08-v8-contract.md` section 3), with the security property "no `contract_version` parameter, version hard-wired". Collapsing them would change the public surface.
- Proposed: keep. Possible saving if generated from a factory: about 110 lines, **estimate only**, and it would add an abstraction. Not recommended. `v7_*` are byte-frozen; `v8_*` are the unfrozen candidate files.

### REG-14: `V6_COMPAT` compatibility adapter
- Files: `engine/profiles.py` 90-97 (`V6_COMPAT`), 99 (`PROFILES`). Reachability by AST-resolved importers: only `engine/profiles.py` itself in production; tests: `test_r08v7_decision_path.py`, `test_r08v7_engine_differential.py`, `test_r08v7_engine_profile.py`, `test_r08v8_cross_version.py`, `test_r08v8_engine_profile.py`, `test_r08v8_policy_identity.py`; evidence harnesses `mut_r8.py`.
- Classification: **HISTORICAL_COMPATIBILITY** (it is the proof that the engine reproduces frozen v6). Reachable from tests only; that is its purpose. Keep and reuse as the R2 differential oracle. There is no `V3_COMPAT`..`V5_COMPAT`; adding them would edit the additively pinned `engine/profiles.py` (STOP-ARCHITECT, protected pin) and would remove no line unless frozen files were replaced, so it is rejected.

### REG-15: modules with no production importer (reachability)
- AST-resolved importers (script `importers.py`, absolute and relative imports): production importers = 0 for `v3_decision, v4_decision, v5_decision, v6_decision, v7_decision, v8_decision, v3_policy_identity, v4_policy_identity, v5_policy_identity, v7_families, v8_families, v7_policy_identity, v8_policy_identity`; tests-only importers 2..7 each. (`v6_policy_identity` is imported by `engine/profiles.py`.) The chains `v3_verify -> v3_decision`, `v4`, `v5`, `v6` are reachable only through their `*_decision` module, which is reachable only from tests (and from external consumers, UNVERIFIED).
- No file in the package is wholly unreachable from its documented public entry points. `v2_token_table.py` (2,869 lines, 2,863 code lines of data) is imported lazily by `v2_token.py:23` and by two tests.
- Classification: **INDEPENDENT_BOUNDARY** (public per-contract entry points documented in `docs/r08-v{3..8}-contract.md`). Whether the Control Plane or Runtime import any of them is **UNVERIFIED** (outside this repository and no network access used). Therefore nothing is proposed for removal.

### REG-16: unreferenced names in the frozen identity module
- `v2_policy_identity.py:716` `_ROW_DIGEST_PATHS` (zero references anywhere in the repository, text search over all tracked files), `v2_policy_identity.py:94` `IDENTITY_MODULE_VERSION` (zero code references; named once in `docs/family-migration/g0/evidence/worker-A/registry_governance_map.json`). Other public-looking names with zero production importers (`plain_digest`, `parse_binding`, `canonical_binding_bytes`, `checked_binding_digest`, `projection_effect_for`, `scope_key_bytes`, `preimage_from_inputs`, `PROJECTION_REFUSAL_KINDS`, `EVIDENCE_STAGES`, `POLICY_IDENTITY_MEMBER_SET`) are used by tests and are part of the frozen v2 identity surface. Script `deadnames.py` lists 27 module-level names with no production reference outside their own file; 25 of them are test-referenced public API.
- Classification: **HISTORICAL_COMPATIBILITY** (byte-frozen). Proposed: leave. Simplification 2 lines. Tier T0.

### REG-17: independent canonicalization, digest and sha-pattern sites
- `common.py:102-107` `canonical_bytes`/`digest`; `registry_contract/validator.py:74-79` (identical 2 functions in an independently importable validator that "imports nothing from the Runtime"); `registry_conformance/highwater.py:99` `_canon` and `:104` (conformance kit that "imports only the standard library"); `v2_policy_identity.py:290-330` (stricter hand-written canonicalizer for identity digests); `registry_consumer/consumer.py:97-102` `_sha256_of`/blob hash. sha-pattern regexes: `common.py:179`, `verify.py:490`, `v2_policy_identity.py:133`, `registry_contract/validator.py:58`, `registry_consumer/consumer.py:62`, `registry_conformance/highwater.py:76` (6 copies).
- Classification: **INDEPENDENT_BOUNDARY**: the validator, consumer and conformance kit are deliberately separate packages (cross-implementation oracles and consumer boundary); importing `registry_successor` into them would couple the independent checkers. (Rationale taken from the module docstrings of `registry_contract/validator.py`, `registry_conformance/highwater.py`; I did not verify which tests depend on the independence.) Proposed: none. Simplification 0.

### REG-18: runtime dependencies and lock files
- Measured (script AST import scan): third-party imports in production code: `nacl` (`registry_adapters/ed25519_verifier.py:48`, lazy inside `_load_backend`, failure raises `Ed25519Unavailable`) and `engine` = the vendored baseline runtime under `baseline/execution-runtime` (`registry_consumer/consumer.py:31`). `registry_successor`, `registry_contract`, `registry_conformance` import only the standard library. Tests import `pytest`, `nacl`, `cryptography` (only `tests/test_adapter_ed25519.py`). `tools/verify_v09_candidate.py` has no third-party import.
- Lock files: `requirements-s01.lock.txt` (18 lines: pytest 8.3.5, pluggy, iniconfig, packaging, colorama), `requirements-ed25519.lock.txt` (134 lines: pynacl 1.6.2, cffi 2.1.1, pycparser 3.12), `requirements-ed25519-test-oracle.lock.txt` (157 lines: cryptography 50.0.1, cffi, pycparser; header says TEST-ONLY, not a runtime dependency). The two Ed25519 locks pin the same cffi/pycparser versions.
- Classification: **INDEPENDENT_BOUNDARY** (the `cryptography` oracle is an independent cross-implementation comparison for the SECURITY-HELD Ed25519 work #26/#34). No unnecessary runtime dependency found. Proposed: no change. UNVERIFIED: whether CI installs the oracle lock for jobs that do not need it (`.github/workflows/registry-tests.yml` installs all three locks in one job; read, not executed).

### REG-19: near-identical per-version tests and builders (pinned)
- Measured: collected tests (with PyNaCl present) 9,257 across 75 modules (section 3.3). Version-token-normalized non-blank line match of consecutive files: `test_r08v3_decision_path.py` vs `test_r08v4_decision_path.py` 98.7 % (305/309; 73 vs 73 collected tests); `r08v3_support.py` vs `r08v4_support.py` 89.1 %; v4 vs v5 81.2 %. `tests/testdups.py` found 49 groups of duplicate function bodies (>= 4 lines, identical after token normalization) spread over more than one test file: 459 redundant lines in total, of which 423 are among manifest-pinned files and 28 involve unpinned v8 files (REG-20). Six support files (`r08v3..r08v8_support.py`) each define `sign/statement/envelope/selection_text/decide/assert_refused`; `assert_refused` is identical in all six and `decide` identical in v3, v4, v5, v7.
- Classification: **HISTORICAL_COMPATIBILITY**: 34 test/support `.py` files are in the cumulative manifests (`tests/test_r08v{3..7}_*.py`, `tests/r08v{3..7}_support.py`, `tests/golden/*`), so they are byte-frozen. Shared helpers already exist (`tests/r08_support.py`, `tests/s01_support.py`) and are what each per-version support file wraps; `r08_support.py` and `s01_support.py` themselves are not hashed but are protected by the tripwire (modification of any file that existed at baseline fails it).
- Proposed: none in place. For any NEW contract version, copy-free reuse of `r08v8_support.py` structure rather than a seventh copy (process rule, no code). Tier T0. Effort S (1 h to document).
- STOP-ARCHITECT: only if pinned tests are to be edited.

### REG-20: duplicates inside the unpinned r08-v8 tests
- Functions: `tests/r08v8_support.py:88` `assert_refused` (identical to 5 other copies), `tests/test_r08v8_frozen_baseline.py:49` `test_frozen_file_is_byte_identical_to_the_baseline` (and `test_r08v7_frozen_baseline.py:46`), `tests/test_r08v8_policy_identity.py:39` `code`, `:54` `test_pinned_vectors`, `tests/test_r08v8_engine_profile.py:148` `_docstring_ids` (duplicates the v7 one at `test_r08v7_engine_profile.py:223`). Total 28 lines.
- Classification: **ACCIDENTAL_DUPLICATION**, de minimis. Proposed: leave (consolidating would only be possible by importing from pinned v7 test modules or editing pinned/baseline-protected helpers). Tier T0. Simplification measured 28 lines; not worth a change.

### REG-21: cumulative frozen-baseline manifests
- `tests/vectors/r08v{3..8}/frozen_baseline_manifest.json`: 125, 141, 158, 174, 193, 213 file entries (15,064..30,587 bytes); each extends the previous one (shared entries 125, 141, 158, 174, 193), 0 hash conflicts. 1,004 pin rows for 213 unique paths.
- Classification: **HISTORICAL_COMPATIBILITY**; `test_the_manifest_extends_the_r08_v7_manifest_without_changing_any_hash` and its per-version equivalents require them. Leave. For R7 (freeze) they are the existing machine-readable hash baseline and can be cited rather than regenerated.

### REG-22: evidence scripts, vectors and documents
- `docs/` holds 420 tracked files (14 MB); 26 Python evidence/tool scripts (`docs/**`), generators `genvec6/7/8.py`, `genman6/7/8.py`, mutation harnesses `mut_r6.py` (125), `mut_r7.py` (177), `mut_r8.py` (150), `mutation-harness-mut_c*.py`, `mut_u`, `mut5`. Pairwise normalized similarity of the harnesses: mut_r6/mut_r7 28.8 %, mut_r6/mut_r8 20.0 %, mut_r7/mut_r8 18.2 %, others below 10 % (so they are not duplicates).
- Classification: **HISTORICAL_COMPATIBILITY** (plan section 3 R5: retain raw failures and all frozen proof vectors; the R1 plan section 2 treats evidence as historical). Reusable for R5/R6: `mut_r7.py` and `mut_r8.py` (mutation scaffolding for the engine and v8), `genman8.py` (manifest generator).

---

## 3. Measurements

### 3.1 Lines of code by version (script `loc_by_version.py`)

`registry_successor/` only ("code lines" = non-blank, non-comment, non-docstring lines).

| group | files | total lines | code lines |
|---|---|---|---|
| base v1/shared (common, compose, decision, families, key_admission, record, selection, verify, canonical_b64, `__init__`) | 10 | 1,949 | 1,447 |
| v2 (`v2_*`: policy_identity 1,472, token_table 2,869 data, age_bounds, f1ab, selection, token, codes) | 7 | 4,891 | 4,169 |
| v3 | 7 | 850 | 640 |
| v4 | 7 | 901 | 679 |
| v5 | 7 | 837 | 631 |
| v6 | 8 | 993 | 737 |
| v7 (thin) | 3 | 101 | 49 |
| v8 (thin) | 3 | 110 | 55 |
| engine (unified, v7/v8) | 11 | 1,290 | 938 |
| total | 63 | 11,922 | 9,345 |

Other packages (`wc -l`): `registry_contract/validator.py` 296 (+4 `__init__`), `registry_adapters/ed25519_verifier.py` 127 (+1), `registry_consumer/consumer.py` 279 (+25 `__init__`), `registry_conformance` 1,518 (`highwater.py` 1,098, `__init__.py` 420), `registry_records` JSON only.

Distinct implementations (AST function scan): verification orchestration `_verify`: 6 (`verify._verify`, `_verify_v3..v6`, `engine._verify`); decision `_decide_verified`: 5 per-version plus `decision.py` (v1/v2) = 6, plus engine `decide_verified` = 7 in total counting the engine; selection `_parse` copies: 7 (`selection.py`, `v2_selection`, v3..v6, engine); record validators: 6 (`record.py`, v3..v6, engine). So there are 6 verifier implementations, 5 of which are frozen copies and 1 is the unified engine.

Common vs version-specific (code lines): version-specific = v3..v8 per-version modules = 640 + 679 + 631 + 737 + 49 + 55 = 2,791; common/shared = base 1,447 + engine 938 + v2 families/identity 4,169 = 6,554 (of which 2,863 are the token data table).

### 3.2 Identical / near-identical file table (scripts `astcmp.py`, `normdiff.py`, `diff`, `sha256sum`)

| group | plain `difflib` line match | token-normalized | AST (docstrings removed, tokens normalized) |
|---|---|---|---|
| verify v3..v6 pairwise | 86.9 % (212/244) | v3=v4 100 %; others 99.2..99.6 % | identical (198 lines) |
| verify v6 vs engine | 84.8 % (207/244) | n/a | 89.4 % (178/199) |
| verify v3..v6 vs `verify.py` | 24.5 % (179/731) | n/a | n/a |
| selection v3..v6 pairwise | 85.5 % (106/124) | v3=v4=v5 100 %; v6 99.2 % | identical (104) |
| selection v6 vs engine | 80.6 % | n/a | 85.6 % (89/104) |
| record v3..v6 | 81.0..83.3 % | 92.9..100 % | identical (34) |
| record v6 vs engine | 78.6 % | n/a | 85.7 % (30/35) |
| decision v3 vs v4/v5/v6 | 83.8 / 83.0 / 75.9 % | n/a | 98.7 / 97.4 / 91.2 % |
| decision v6 vs engine | 55.6 % | n/a | 58.8 % |
| policy_identity v3-v4 / v5-v6 / v3-v6 | 76.5 / 61.1 / 56.5 % | n/a | 84.1 / 69.3 / 65.3 % |
| policy_identity v7 vs v8 | 71.7 % | n/a | identical (29) |
| families v3-v4 / v3-v6 / v5-v6 | 66.2 / 54.8 / 57.0 % | n/a | n/a |

`sha256sum` of all `v*_verify/selection/record/policy_identity.py`, `engine/{verify,selection,record}.py`, `verify.py`, `selection.py`, `record.py`: all digests are distinct (no two files are byte-identical).

Duplicate mass (script `dupmass.py`): v4..v6 `verify+selection+record` = 1,026 code / 1,230 physical lines (11.0 % of 9,345 code lines); plus v4..v6 decision 237 code / 307 physical; combined 1,263 code lines = 13.5 % of code (19.5 % excluding the 2,863-line data table); 12.9 % of physical lines.

### 3.3 Tests (commands below; wall-clock not measured)

`pytest --collect-only -q` collected **9,257** tests in 75 modules (PyNaCl present via `out/site`; without PyNaCl: 9,240 and one collection error in `tests/test_r08v8_cross_version.py`, `AttributeError: 'NoneType' object has no attribute 'crypto_sign'`, an environment effect, 17 tests lost). Per-file counts: `.../r1/out/test-counts.txt`.

| group | files incl. support | LOC | collected tests |
|---|---|---|---|
| r08-v2 | 4 | 880 | 427 |
| r08-v3 | 5 | 990 | 518 |
| r08-v4 | 6 | 1,012 | 376 |
| r08-v5 | 5 | 896 | 332 |
| r08-v6 | 7 | 1,581 | 543 |
| r08-v7 | 8 | 2,143 | 450 |
| r08-v8 | 9 | 2,035 | 785 |
| other (v1, S0x, adapter, conformance, integrity) | 41 | 17,561 | 5,826 |
| total | 85 | 27,098 | 9,257 |

Largest: `test_adapter_ed25519_cctv.py` 1,838, `test_adapter_ed25519.py` 708, `test_r08_v2_canonical_base64_vectors.py` 599, `test_ext_s1_4_age_slots.py` 477 collected cases.

### 3.4 Repeated expensive work per decision (scripts `profile_callers.py`, `time_decide.py`, `ts_args.py`)

One `verify_and_decide_v8` call (engine path): 8 `common.digest`, 9 `common.canonical_bytes`, 10 `parse_timestamp` (4 distinct strings), 61 `_json_copy` calls, 1 `crypto_sign_open` (excluding verifier construction, whose known-answer self-test is not part of a decision). Mean wall time 984 us (3,000 iterations after 200 warm-up, CPython 3.13.17, this host); costs: record digest pair 25.0 us, statement digest 14.3 us, `parse_timestamp` 7.5 us. Frozen v6 path has the same counts (63 `_json_copy`, 14 sha256, 13 digest). Absolute numbers are host-specific; the counts are deterministic.

### 3.5 Reproducible commands and scripts

All paths below are under `/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/`. Repo = `cognous-ocs-registry`, helper scripts = `out/` (they read the repo and write nothing into it).

```
cd cognous-ocs-registry && git rev-parse HEAD                      # 2815643c3e15fbc6aadadbf88dc7596f10120992
# LOC by version (section 3.1)
python3 ../out/loc_by_version.py
# byte hashes, pairwise physical and normalized similarity (section 3.2)
sha256sum registry_successor/v?_verify.py registry_successor/engine/verify.py registry_successor/verify.py
python3 ../out/astcmp.py registry_successor/v3_verify.py registry_successor/v4_verify.py registry_successor/v5_verify.py registry_successor/v6_verify.py
python3 ../out/normdiff.py registry_successor/v5_verify.py registry_successor/v6_verify.py   # shows the residual normalized differences (docstring only)
( cd registry_successor && python3 - <<'E'  # difflib physical match, same as used above
import difflib; A=open('v3_verify.py').read().splitlines(); B=open('v4_verify.py').read().splitlines()
print(sum(m.size for m in difflib.SequenceMatcher(None,A,B,autojunk=False).get_matching_blocks()), len(A))
E
)
python3 ../out/dupmass.py                                          # duplicate mass numbers
# byte-freeze check against the manifest (section 4.1)
python3 - <<'E'
import json,hashlib,os
fs=json.load(open('tests/vectors/r08v8/frozen_baseline_manifest.json'))['files']
bad=[p for p,h in fs.items() if p.startswith('registry_') and (not os.path.exists(p) or hashlib.sha256(open(p,'rb').read()).hexdigest()!=h)]
print(len([p for p in fs if p.startswith('registry_')]), 'registry_* files in manifest; mismatching:', bad)
E
git diff --name-only --diff-filter=MDRT 67512a71546748cd888e4cf790485ea0bef9199a HEAD -- .    # tripwire prediction
# reachability (section 2, REG-14..16)
python3 ../out/importers.py          # AST-resolved importers of every registry_* module (prod / tests / other)
python3 ../out/deadnames.py          # module-level names with no production reference elsewhere
# tests
PYTHONPATH=$PWD/../out/site /root/.local/bin/pytest --collect-only -q -p no:cacheprovider
grep '::' collect.txt | awk -F'::' '{c[$1]++} END{for(k in c) print c[k], k}' | sort -k2      # per-file counts
python3 ../out/testdups.py           # duplicate test/support function bodies (49 groups, 459 lines; 423 pinned, 28 unpinned)
# repeated work (section 3.4); needs PYTHONPATH=$PWD/../out/site:.:baseline/execution-runtime:tests
python3 ../out/profile_callers.py ; python3 ../out/time_decide.py ; python3 ../out/ts_args.py
# dependencies
python3 - <<'E'   # AST import scan for third-party imports in registry_* and tools and tests
import ast,glob,sys
std=set(sys.stdlib_module_names)
for pat in ('registry_*/**/*.py','tools/*.py'):
    s=set()
    for p in glob.glob(pat,recursive=True):
        for n in ast.walk(ast.parse(open(p).read())):
            ms=[a.name for a in n.names] if isinstance(n,ast.Import) else ([n.module] if isinstance(n,ast.ImportFrom) and n.level==0 and n.module else [])
            s|={m.split('.')[0] for m in ms}-std
    print(pat,sorted(x for x in s if not x.startswith('registry_')))
E
grep -E '^[a-zA-Z0-9_.-]+==' requirements-*.lock.txt
```

---

## 4. Verification notes and what could not be verified

### 4.1 Frozen map at HEAD
- Of the 213 entries in `tests/vectors/r08v8/frozen_baseline_manifest.json`, 77 are non-doc `registry_*/**` files; the script in section 3.5 reports zero mismatches (all 77 equal their baseline bytes at HEAD). The manifest also pins 61 entries under `tests/` (34 of them `.py`), 69 under `docs/` and 6 baseline-runtime files.
- Not in the byte manifest: `registry_successor/v8_decision.py`, `v8_families.py`, `v8_policy_identity.py`, `engine/families_anchor.py`, `engine/families_observation.py`; `engine/profile.py`, `engine/identity.py`, `engine/profiles.py` (additive edits pinned by line); tests `r08v8_support.py`, `test_r08v8_*.py`, `test_r08v7_frozen_baseline.py` and `test_ext_s1_5_identity_module.py` (the two allowlisted guards).
- `docs/r08-v8-contract.md` states `r08-v1`..`r08-v7` are byte-identical to baseline `67512a7`; the v8 contract itself is "APPROVED CANDIDATE... changes still require F3 requalification, refreeze and re-review" (`docs/r08-v8-contract.md` header).

### 4.2 UNVERIFIED items
- Wall-clock test execution time, CI matrix timing, skip counts at run time, mutation numerator/denominator, uncovered branches (no suite was run; only collection and a handful of read-only profiling scripts).
- Whether `tests/test_r08v8_frozen_baseline.py::test_every_other_committed_file_is_unchanged_from_main_except_the_allowlisted_edits` fails at HEAD (static prediction from `git diff` only).
- Whether Control Plane or Runtime import any `registry_successor.v3..v8_*` public module (outside this repository); relevant to REG-15.
- Whether the `docs/r08-v{3..7}-contract.md` public surfaces are consumed by anything other than tests and the Control Plane consumer described in `docs/r08-v8-contract.md` section 3.
- Timings are host-specific (this sandbox, CPython 3.13.17); the plan's CI uses 3.13 with `pytest 8.3.5`, the sandbox has pytest 9.1.1 (`--collect-only` only).
- Savings for any delegation of v3..v6 to the engine are estimates and are not recommended.

### 4.3 Recommendation for the Architect (from the evidence, not a plan change)
1. Record the measured residual duplication (section 3.2) in the R1 baseline as "documented residual duplication, frozen" and treat REG-1..REG-6 as closed with no action.
2. Do not spend R2/R3 effort on v3..v6; they are protected. The unified engine already carries v7/v8 and the plan's goal of a shared mechanical engine is met for every path that is not byte-frozen.
3. The only candidates with non-zero but trivial payoff are REG-8 (6 lines) and REG-20 (28 lines); both are rejected on value.
4. If the Architect nevertheless wants delegation of v3..v6 onto the engine for LOC reduction, that is a STOP-ARCHITECT decision (frozen bytes, import fence test, additive-edit pins on `engine/profiles.py`, tripwire allowlist) and needs F3 requalification; the existing differential oracle (common facts) is the evidence to reuse.
