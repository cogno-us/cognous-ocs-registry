# Control Plane simplification: bounded source crosswalk (T0, read-only, NOT a qualification, NOT a reduction target)

Subject: `cognous-control-plane` HEAD `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69` (verified `git rev-parse HEAD`; working tree clean before and after; one git-ignored `__pycache__` that my first import created was deleted again).
Excluded: DEF-OBS-TOL-OVERFLOW-1. No repo file edited, no commit, no suite run (existing tests only grep-verified for existence).
Prior inventory re-derived, not trusted: `/tmp/claude-0/-home-claude/139dd095-4028-5533-a993-4a7fc4b564f0/scratchpad/r1/out/control-plane-inventory.md`.

## 0. Method (so every number can be reproduced)

* Baseline: 10 modules = 2,674 physical lines (150+168+271+354+243+338+521+190+230+209), recounted.
* Duplication: normalized-line SequenceMatcher plus exact-line set intersection with version tokens renamed (`out/scripts2/cp1.py`); AST dump with names and docstrings stripped for tests (`out/scripts2/cp9.py`).
* NET lines: I wrote each refactor as a real text transformation of a COPY of the source (`out/proto_cp1/`, `out/proto_cp3/`, `out/proto_cp4b.py`; scripts `out/scripts2/cp1_net.py`, `cp2_net.py`, `cp3_net.py`, `cp4_net.py`), parsed it with `ast`, and counted physical lines of the copy minus the original. The shared helper, its blank lines, retained loaders and import lines are all counted. "Estimate" is not used for GO items.
* Behaviour: scratch differentials on copies against a FAKE Registry (not a real pin): `cp1_diff.py` (17 verdict shapes x 3 modules = 51 comparisons, plus 44 full-function comparisons of `derive_unreadable`, old versus rewritten): 0 differences. `cp3_diff.py` (30,022 documents: 22 hand-written/edge plus 30,000 random mutations; four `_strict_pairs/_reject_number` copies, `registry_class_map`, `registry_unreadable_map` versus `_record_payload` plus predicate): 0 differences. `cp4_diff.py` (64 declared/derive-refusal/compose-raise combinations of the three blocks; compares result and the full ordered call log with kwargs): 0 differences.
* Tier rule used (Architect's): T3 if it decides a refusal, narrowing, composition order or identity; T4 if protected evaluator, persisted schema or approval preimage; T1 tests/docs/metadata only.

## 1. F3-A subject and structural constraints (facts that bind every row)

* F3-A subject (per `out/f3-source-binding-and-coverage-map.md` section 1 and the Architect's list): `effective_configuration_binding.py`, `registry_governed_lifecycle.py`, `registry_governed_policy.py`, `registry_f4_age_governance.py`, `registry_f5_class_age_governance.py`, `registry_f5_class_unreadable_governance.py`, `registry_final3_governance.py`, `registry_effective_policy.py`. NOT in it: `registry_revocation_governance.py`, `registry_irreversibility_governance.py` (but both are executed by the composed F3-A suites through `registry_governed_policy.py`).
* Byte pins: `registry_f4_age_governance.py` = `fdf3c17d...` and `registry_f5_class_age_governance.py` = `f381fbe7...` (recomputed, match). Tests: `tests/test_f5_class_age_governance.py::test_s01_protected_evaluators_and_the_f4_consumer_are_unmodified_by_this_increment[registry_f4_age_governance.py]` (pin line 1017); `tests/test_f5_class_unreadable_governance.py::test_s01_protected_evaluators_and_the_earlier_consumers_are_unmodified_by_this_increment[registry_f4_age_governance.py]` and `[registry_f5_class_age_governance.py]` (pin lines 1447-1448). Editing F5-age alone costs ONE re-pin line (test_f5_class_unreadable_governance.py:1448); `test_f5_class_age_governance.py` does not pin F5-age itself.
* `tests/test_governed_policy_composition.py::test_z04_the_shared_lifecycle_holds_no_policy_no_registry_import_and_never_touches_a_governed_field` forbids imports containing `importlib`/`registry_successor`/`runtime_authority` and the strings `approval_commitment`, `on_unreadable`, `max_status_age_seconds`, `model_dump` in `registry_governed_lifecycle.py`. A loader-injected helper would pass the letter of it but is against its intent; I do not propose it.
* Seams: tests monkeypatch `ir._registry_modules` (`test_irreversibility_unit.py:72,257`, `test_irreversibility_governance.py:985,1001`) and `ir.importlib`, `gov.importlib` (`test_f5_class_unreadable_governance.py:1393-1399`), `f3.importlib` (`test_final3_observation.py:483`). Consequence: every converted module must keep its own `import importlib` and a module-level `_registry_modules`, and the helper must receive the loader as a parameter and resolve the Registry function by name at call time (also `dec.verify_and_decide_v2`, `test_f4_age_governance.py::test_d01_...`).
* Source-text guards that a new line could trip: F4 banned substrings (`test_f4_age_governance.py::test_s01_module_excludes_clock_tolerance_and_other_families`); F5-age `test_n04_the_module_excludes_clock_tolerance_other_families_and_every_other_class_field` (splits on the docstring phrase "Registry is resolved lazily"); F5-unreadable `test_n10_the_module_governs_one_field_only_and_excludes_every_other_parameter`, `test_e08_...` (no new file may contain `on_unreadable`); no-class/no-evaluator-import ASTs `test_revocation_families_governance.py::test_s02_...`, `test_irreversibility_governance.py::test_s07_...`, `test_final3_composed_binding.py::test_f04_...`.
* Existing oracle that a move would break: `docs/evidence/final3-consumers/mutation_harness.py` applies 64 mutants by exact text. Five `verified-*` mutants match the text of `registry_final3_governance._verified` and two (`pol-name-order-anchor-last`, `pol-name-dropped-tolerance`) match the `FAMILY_NAMES` literal; after CP-1(f3) or CP-4a they would be INVALID until re-pointed and the run repeated (about 64 x 90 s was the recorded control time, my estimate of cost, not measured).
* The four boundaries (construction, decision entry, execute entry, commit gate) and both held-state checks are NOT touched by any GO item: the shared code is called from `derive_*` exactly as often as before (CP-4b differential shows identical call log).

## 2. Crosswalk rows

### CP-1 Registry-call and verdict-shape adapter (6 copies) - split A / B' / F4

* Verified ranges (physical lines): rev `registry_revocation_governance.py:150-172` (23, loader `:141-147`); irr `registry_irreversibility_governance.py:132-154` (23, loader `:123-129`); f3 `registry_final3_governance.py:158-180` (23, loader `:149-155`); F4 `registry_f4_age_governance.py:63-87` (25); F5-age `registry_f5_class_age_governance.py:139-162` (24); F5-unreadable `registry_f5_class_unreadable_governance.py:158-181` (24).
* Genuine vs mandatory: the three `_verified` are the same code after renaming (normalized 22-23 of 23 lines identical pairwise; irr vs f3 23/23). F4 / F5-age / F5-unreadable share 18-23 of 23 normalized lines with them; 16 normalized lines are common to all six. It is the same adapter written six times, not an independent boundary: the plan's four boundaries are about WHEN the check runs, and each `derive_*` still runs it at each boundary.
* Existing abstraction: none for the adapter. Precedent for cross-module sharing: `_record_payload` at `registry_revocation_governance.py:100` imported by `registry_irreversibility_governance.py:38` and `registry_final3_governance.py:36` (the prior inventory cited `:9` and `:19`, wrong).
* New abstraction: ONE function `verify_required(modules, decide_name, scope, institution_id, authority_domain, caller, material, verifier, now)`, 23 lines, class-free, loader and Registry function resolved at call time. Home options: (H1) `registry_revocation_governance.py` next to `_record_payload` (no new file, zero new edges for irr/f3, two new edges f5a->rev, f5u->rev, acyclic); (H2) new module (+about 8 lines, one new file to scope, cleaner direction); (H3) lifecycle: rejected (z04 intent).
* Gross / NET (measured on copies, helper counted, H1): A (rev, irr, f3): 69 duplicate lines removed, +25 helper, +9 wrappers = NET -35 (rev +5, irr -20, f3 -20). B' (F5-age, F5-unreadable): each keeps a 9-line `_registry_modules` and a 4-line call = NET -9 each = -18. F4 EXCLUDED: its import `try` also loads `v2_age_bounds` (needed for `FAMILY_F4` at the digest); moving that import would change the code reported under a partial Registry from `registry_unavailable` to `effective_policy_digest_unavailable`, and it is byte-pinned twice. Total NET -53. Without f3: A = -15.
* Edges: f5a->rev and f5u->rev new (H1); no importlib/registry_successor edge moves into lifecycle; each family keeps `_registry_modules` and `import importlib`.
* Authority paths: it DECIDES refusals (`material_invalid`, `registry_unavailable`, `verifier_not_admitted`, `registry_call_failed`, `registry_decision_invalid`, `registry_not_applied`) and the order among them. No narrowing, composition order, identity or persisted binding. Reason vocabulary unchanged.
* Tier: T3 (prior said T2). F3-A: f3, f5a, f5u are subject files; rev, irr are not.
* Minimum regression evidence (all exist at 739efe7, grep-verified): `tests/test_irreversibility_unit.py::test_a_failing_digest_and_a_missing_registry_and_a_foreign_verifier_and_wrong_material_are_refusals`, `::test_the_real_registry_import_failure_is_a_refusal_not_an_exception`; `tests/test_irreversibility_governance.py::test_u02_a_verifier_that_is_not_the_admitted_ed25519_verifier_and_wrong_material_types_are_refused`, `::test_u03_registry_unavailable_and_call_failure_are_refusals`, `::test_f04_a_registry_decision_of_the_wrong_shape_is_refused`; `tests/test_revocation_families_governance.py::test_u02_a_verifier_that_is_not_the_admitted_ed25519_verifier_and_wrong_material_types_are_refused`, `::test_f05_a_registry_decision_of_the_wrong_shape_is_refused`; `tests/test_final3_observation.py::test_g04_a_registry_decision_of_the_wrong_shape_is_refused`, `::test_g06_a_verifier_that_is_not_the_admitted_ed25519_verifier_wrong_material_types_and_an_unavailable_registry_are_refused`, `::test_g07_a_registry_call_that_raises_is_a_refusal`, `::test_g09_an_operationally_authorized_registry_verdict_and_a_non_1_schema_revision_are_refused`; `tests/test_final3_anchor.py::test_g02_a_registry_verdict_of_the_wrong_shape_is_refused`; `tests/test_f5_class_unreadable_governance.py::test_n05_an_unexpected_registry_decision_shape_is_refused`, `::test_n06_a_registry_call_failure_is_a_refusal`, `::test_n07_a_missing_registry_dependency_or_an_older_registry_without_r08_v5_is_a_refusal`, `::test_n01_defence_in_depth_refuses_a_registry_result_wider_than_the_host`; `tests/test_f5_class_age_governance.py::test_n06_an_unexpected_registry_decision_shape_is_refused`, `::test_n01_defence_in_depth_refuses_a_registry_result_wider_than_the_host`, `::test_n04_...`; `tests/test_f4_age_governance.py::test_d01_defence_in_depth_refuses_a_registry_result_wider_than_the_host` (F4 unchanged but shares the Registry callable seam); the seven gates unchanged (f4 73, f5 age 111, unreadable 148, composed 99, revocation 388, irreversibility 576, final3 858).
* Existing differential/oracle: none old-vs-new. Mutants `verified-skips-verifier-admission`, `-skips-deny-all-check`, `-skips-operational-check`, `-wrong-consumer-in-context`, `-participation-optional` cover only f3 and must be re-pointed. My scratch differential (`cp1_diff.py`) is the template; keeping it as a permanent test is optional and would add test lines.
* Rollback: one `git revert` per stage (A, then B'); no persisted data. B' depends on A (helper). F5-age edit needs the one-line re-pin revert.
* Semantic effect: places that must change for a new Registry decision kind or a new refusal rule: 6 today, 2 after (helper + F4 inline; 1 if F4 is later converted). Bug class that disappears: five-of-six partial fix of the adapter. Bug class that appears: one helper defect now widens five families at once (that is why T3 and the differential).
* VERDICT: GO for A + B' (F4 left), value HIGH versus qualification cost MEDIUM-HIGH: three of the four edited files are F3-A subject files (f3, f5a, f5u), so it forces F3-A re-scoping (or is sequenced after F3-A) and costs one re-pin plus a mutation-harness re-point. Only A-without-f3 (-15) avoids F3-A, but then four copies remain beside the helper (a fifth variant): not recommended.

### CP-2 Class-map narrowing tail, host extractors, `stricter_*`

* Verified ranges: tails `registry_revocation_governance.py:183-195`, `registry_irreversibility_governance.py:165-177`, `registry_f5_class_unreadable_governance.py:182-194` (13 lines each; normalized identical). Extractors `registry_f5_class_age_governance.py:79-89`, `registry_f5_class_unreadable_governance.py:100-110`, `registry_revocation_governance.py:70-81`, `registry_irreversibility_governance.py:60-71`. F5-age tail (`:164-173`) differs (ints, `min`).
* Genuine vs mandatory: genuine copies of one rule, but this is the narrowing check itself (`effective_policy_widens_host`, `effective_policy_invalid`), the per-family defence in depth next to the final composition validator (`final_composition_defect`, not redundant).
* Existing abstraction: none. New: `narrowing_defect(effective, host_values, registry, value_ok, rank, stricter)` (11 lines + 2 blank). Call site 9 lines -> 4.
* NET measured: -15 at call sites + 13 helper = -2 for three sites (rev + irr only: +3, i.e. larger). Extractors via one `class_values(...)`: about -12 (three unpinned) to -22 (all four), not measured to the line; `stricter_*` one-liners: about 0. The prior's -45 is not supported.
* Edges: new shared home needed (f5u->rev or new module). Authority: decides narrowing/refusal. Tier T3. F3-A: f5u is a subject file.
* Evidence that would be needed: `tests/test_revocation_families_governance.py::test_f03_a_forged_registry_result_that_is_not_the_stricter_of_host_and_record_is_refused`, `::test_a02_the_effective_value_is_the_stricter_of_host_and_registry_and_never_looser`; `tests/test_irreversibility_governance.py::test_f02_...`, `::test_a02_...`; `tests/test_f5_class_unreadable_governance.py::test_n01_...`, `::test_n02_a_registry_result_that_disagrees_with_the_record_minimum_is_refused`; `tests/test_governed_policy_composition.py::test_f01_...`, `::test_f02_...`, `::test_f03_...` and a new three-way differential (not built by me).
* Semantic effect: 3 hand-maintained tails -> 1 (+3 call sites) but the call sites still carry the family-specific order; one shared bug widens three families.
* VERDICT: LEAVE. Net -2 for T3 narrowing code that touches an F3-A file.

### CP-3 Private strict-integer JSON parsers and record-map readers

* Verified ranges: parser pair `registry_effective_policy.py:40-48`, `registry_f5_class_age_governance.py:92-100`, `registry_f5_class_unreadable_governance.py:121-129`, canonical `registry_revocation_governance.py:89-97`; readers `registry_f5_class_age_governance.py:103-114`, `registry_f5_class_unreadable_governance.py:132-143` versus `_record_payload` `registry_revocation_governance.py:100-107`; `selection_ref` `registry_effective_policy.py:51-61`.
* Genuine vs mandatory: the second strict parse of the verified record is a mandatory check, but the FOUR parser copies are not independent validation (same function, only the unused exception text differs: "non-integer number" vs "non-string number"). My differential: 30,022 documents, 0 disagreements among the four parsers and between both readers and `_record_payload` plus predicate (RecursionError included). `strict_json.strict_loads` is NOT a substitute (accepts finite floats), as the prior said; confirmed not re-run.
* Existing abstraction: `_record_payload` (rev:100), already imported by irr and f3. New abstraction: none (reuse; `registry_class_map` and `registry_unreadable_map` remain as thin predicate wrappers because tests call them by name).
* NET measured: effective_policy -10, f5u -16, f5a -16 = -42 (f5a/f5u also drop `import json`; effective_policy keeps it for `selection_ref`). Without the pinned f5a: -26.
* Edges: NEW effective_policy->rev (a snapshot module starts to depend on a family module; acyclic), f5a->rev, f5u->rev. Authority: feeds `scoped_class_not_governed`/`effective_policy_invalid` and, via `selection_ref`, the snapshot identity. Tier T3 (prior: T2). F3-A: all three edited files are subject files; f5a is also byte-pinned (1 re-pin line).
* Evidence: `tests/test_f5_class_age_governance.py::test_n03_the_record_class_map_parser_is_strict`; `tests/test_f5_class_unreadable_governance.py::test_n08_the_record_class_map_parser_is_strict`; `tests/test_revocation_families_governance.py::test_u01_the_second_strict_parse_of_the_verified_record_text_refuses_anything_unusual`; `tests/test_irreversibility_governance.py::test_u01_...`, `::test_s05_the_selection_ref_parser_is_strict`; `tests/test_final3_observation.py::test_g08_the_derivation_re_reads_the_record_value_and_its_floor`; guards `test_irreversibility_governance.py::test_s07_...`, `test_f5_class_unreadable_governance.py::test_n10_...`. No existing old-vs-new differential; mine (`cp3_diff.py`) is the template. No mutant targets these parsers.
* Rollback: one revert (plus the re-pin line). Semantic effect: strict-parser copies 4 -> 1 and inline record readers 2 -> 0: a future hardening (for example NaN/size rules) would today have to be applied in 4 places and a miss silently changes which records count as coverage. Appears: one parser defect now affects all families.
* VERDICT: GO (value HIGH for semantics, small in lines), but it forces F3-A re-scoping. Combine with CP-1 B' in one F5 edit so f5a/f5u are re-hashed once.

### CP-4a `FAMILY_NAMES = tuple(FAMILY_TABLE)`

* `registry_governed_policy.py:64-65` versus `registry_effective_policy.py:25-35`; equal at runtime (re-measured by the prior, plausible, not needed). NET -1 (prior -2).
* `FAMILY_NAMES` is the `order=` of the persisted D-06 rows (`registry_governed_policy.py:417,486`), so this moves authority over persisted row order to another file's dict literal: not T1; T3. Already guarded three ways: `test_irreversibility_governance.py:381` (literal), `test_irreversibility_unit.py:377`, `test_effective_configuration_binding_dedicated.py:327-329`, `test_final3_composed_binding.py:253`. Two mutants (`pol-name-*`) would be re-pointed.
* VERDICT: LEAVE. One line, F3-A (policy + effective_policy), existing guards already catch drift.

### CP-4b three identical blocks in `derive_policy`

* `registry_governed_policy.py:208-218, 219-229, 230-240` (33 lines with blanks as one region 33). Rewritten as a table loop inside the function (resolved at call time, order preserved): NET -16 (prior -17). My differential: 64 combinations, identical result and call log.
* Not a new abstraction beyond a local table; edits the composition-order function. Tier T3. F3-A: `registry_governed_policy.py`.
* Evidence: `tests/test_governed_policy_composition.py::test_b04_composition_is_deterministic_and_order_of_construction_does_not_matter`, `::test_c04_an_unusable_selection_in_any_declared_family_refuses_and_names_the_family`, `::test_k06_each_component_of_the_bound_identity_is_compared_on_its_own`, `::test_h01_an_invalid_original_host_is_refused_before_any_registry_call_and_is_not_repaired`.
* Semantic effect: the three blocks become one, but anchor, observation, terminal and F4/class-age blocks stay different, so the module still reads as "table plus five special cases"; explicit blocks make refusal order easy to audit.
* VERDICT: LEAVE (-16 in the largest F3-A file does not pay for re-scoping).

### CP-5 Family id / contract / schema revision kept in two places

* `registry_effective_policy.py:25-37` versus module constants. The cross-check is deliberate (tests compare; mutants `eff-age-family-id-typo`, `eff-schema-revision-2` etc. are killed); rows are persisted identity. 0 lines gained. T4-adjacent (any moved value changes persisted digests). VERDICT: NO-GO (agree with prior).

### CP-6 Identity-property builders

* `registry_f4_age_governance.py:141-145`, `registry_f5_class_age_governance.py:239-244`, `registry_f5_class_unreadable_governance.py:308-319`, `registry_governed_policy.py:440-466`. `dataclasses.asdict(GovernedScope)` would save about 1 line in F4, 1 in F5-age, 0 in F5-unreadable and costs an import each; rows loop about -6. NET about -3 to -9, public identity surface (`registry_governed_policy_identity` etc.), two byte-pinned files. T3 (identity). VERDICT: LEAVE.

### CP-7 Double member build in `_resolve`

* `registry_governed_lifecycle.py:252-261` (`configuration_binding_status`: members at 256, `ecb.mint` at 261) and `:263-285` (`_resolve`: members 271, mint 272; the prior said mint at 256/261, wrong). `configuration_binding_status` is a public read-only classifier that `_resolve` reuses by design; passing `live` in changes when the live configuration is read relative to the refusing equality (the "LOAD-BEARING" comment). Gain about 3 commitments of 46 per execute; time share 0.02%. Persisted binding classification path: T3/T4-adjacent. VERDICT: NO-GO (agree).

### CP-8 `pyproject.toml` duplicate dev requirement

* `pyproject.toml:21` and `:23` both `pytest-asyncio>=0.23`; `cryptography>=43` also at `:17` and `:22`. Delete line 23: NET -1, T1, no source pin, no cache key (`grep` for `hashFiles` finds none), not a Registry-layer file, no F3-A impact. Evidence: CI `pip install -e ".[dev]"` unchanged resolution. Rollback: revert. Semantic effect: none. VERDICT: GO (hygiene; fold into any other commit).

### CP-9 Duplicate test helpers

* Re-measured (`cp9.py`): 2,084 functions, 13 AST-identical groups (>= 4 lines), 139 redundant lines (prior: 15 groups, 151); 99 of them across governed-layer test files. Free-variable analysis shows they are NOT hoistable as identical: `prepared` reads 12 module-level names, `_unavailable` reads module `_REQUIRED` and does an import-time skip/fail (hoisting would change the strict-pin behaviour), `Source.__call__` x7 are methods of classes/subclasses with different `__init__`, `classes`/`umap` read module constants. Only `stall_once` x3 (freshness tests, outside the governed layer) is free of globals. Realistic governed-layer net after import lines: 0 to -20. Tests are not in the 2,674 baseline and are the F3-A evidence (its test sources are bound).
* VERDICT: NO-GO.

## 3. Totals

| quantity | prior | supported here |
|---|---|---|
| Source net if ALL of CP-1..CP-8 done | about 205 (7.7%) | about -118 (4.4%): CP-1 -53, CP-2 -2, CP-3 -42, CP-4a -1, CP-4b -16, CP-6 -3, CP-8 -1 |
| Source net for the GO set (CP-1 A+B', CP-3, CP-8) | n/a | **-96 lines (3.6% of 2,674)** (-35 -18 -42 -1) |
| GO set without any F3-A file | n/a | **-1** (CP-8). CP-1 A on rev+irr alone is -15 but leaves the adapter in 5 variants |
| Tests (CP-9) | -151 | 0 to -20, not recommended |

The 205 figure is NOT supported. The difference: CP-1 stage B and CP-2 were overstated (loaders must stay for the importlib seams; F4 cannot move; the narrowing helper breaks even), CP-4/CP-6 were rounded up, and CP-9 is not hoistable.

Semantic-complexity gain, separately (GO set): 10 hand-maintained duplicate blocks removed: 5 Registry verdict-adapter copies (6 -> helper + F4), 3 strict-JSON parser copies (4 -> 1), 2 inline record-map readers (-> existing `_record_payload`). Future-change sites: adapter rules 6 -> 2, strict-parse rules 4 -> 1, record-map reading 3 -> 1. New abstractions added: exactly 1 (`verify_required`). No refusal code, order, digest, persisted field or reason is changed (differentials above).

## 4. Questions (a) and (b)

(a) F3-A subject files touched by each candidate: CP-1 f3 (A), f5a + f5u (B'); CP-2 f5u; CP-3 effective_policy + f5a + f5u; CP-4a/4b policy (+ effective_policy for 4a); CP-5 effective_policy; CP-6 f4 + f5a + f5u + policy; CP-7 lifecycle. Not touching F3-A: CP-8 (metadata), CP-9 (tests, but they are F3-A evidence), CP-1 stage A on rev + irr only. `effective_configuration_binding.py` is touched by none.
(b) Without touching any F3-A file only CP-8 is deliverable with value; every item that removes semantic duplication lives in F3-A subject files, so the choice is sequencing (after F3-A) or re-scoping, not a cheaper variant.

## 5. Unverified

* No test or gate was run; all behaviour evidence is scratch differentials against a fake Registry, not the pinned Registry.
* F5-age stage B' and CP-3 stage on F5-age were transformed and parsed but not differentially executed (same shape as F5-unreadable, which was).
* CP-2, CP-6 nets for extractors/rows are estimates; no CP-2 differential built.
* Mutation re-run cost and the Engineering Constitution tier text were not available; tier rule is the Architect's.
* Whether the F3-A frozen subject also hashes rev/irr transitively is not stated in the sources I read.
