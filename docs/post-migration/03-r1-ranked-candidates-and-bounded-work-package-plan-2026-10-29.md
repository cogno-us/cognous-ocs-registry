# R1 ranked candidates and bounded work-package plan (STATIC; no dispatch)

> **Superseded in part by `05-...` (2026-10-29): the line savings, tiers and the package list in this file were corrected by the bounded source crosswalk (annex D). Supported Control Plane net reduction is -96 lines (3.6%), not about 205; CP-9 is not hoistable; CP-2/CP-4/CP-6 are LEAVE; CP-1 and CP-3 are T3 and touch F3-A subject files. Read `05-...` for the current ranking; the text below is retained as the original R1-START record.**


Status: planning record. **Non-authorizing.** No production-code change is authorized or dispatched by it. Each package below is dispatchable only after Gate 2 (Architect review of the inventory and packages) and Gate 3 (explicit authorization), each in its own typed eight-field assignment with the archetype-B verbatim clauses (CA02, CA04, CA05, CA09, CA15) injected by the orchestrator at dispatch time. Pins: Registry `2815643c3e15fbc6aadadbf88dc7596f10120992`, Control Plane `739efe7d8f16a0cee1efc7dd3a978d5d4d85fe69`; they must be re-discovered and re-pinned at dispatch (live source, not these values). Savings are measured or labelled estimates (annex C).

## 1. Top five refactoring opportunities (ranked by benefit, cost and regression risk)

| Rank | Candidate | Benefit (measured / estimate) | Cost | Risk tier | Why this rank |
|---|---|---|---|---|---|
| 1 | **CP-3** one strict-JSON parser and record-payload reader for the four private copies | 36 + 24 lines duplicated (measured); about -41 lines (estimate); the four parsers and the extractors agree on 20,013 documents (measured differential, 0 disagreements) | S, about 5 h | T2 | the best existing oracle; an owner helper already exists (`registry_revocation_governance._record_payload`); stage A touches unpinned files only |
| 2 | **CP-1 stage A** shared Registry-call and verdict-shape preamble for the three unpinned modules (revocation, irreversibility, final3) | 3 x 30 byte-identical lines (measured); about -32 lines (estimate) | M, about 6 h of the 10 h | T2 | identical after renaming; seams (`_registry_modules`, `importlib.import_module`) must be kept because tests monkeypatch them |
| 3 | **CP-9** shared AST-identical test helpers (and CP-8 duplicate dev requirement) | 15 groups = 151 redundant test lines (measured floor, 0.6% of tests/) | M, about 6 h | T1 | tests only; gate counts must stay identical (73/111/148/99/388/576/858, 0 skipped) |
| 4 | **CP-4a** `FAMILY_NAMES = tuple(FAMILY_TABLE)` (one hand-maintained list fewer); **CP-4b** table-driven three `derive_policy` blocks in the existing order | 3 x 11 identical lines (ratio 1.000, measured); about -2 (4a) / -17 (4b) lines (estimate) | S, 4 h | 4a T1; 4b T3 | 4b must preserve the refusal order exactly; do 4a first and 4b only with the order assertions as oracle |
| 5 | **CP-2** one narrowing-check function for three 13-line tails (optional) | 88 duplicated lines (measured); about -45 lines (estimate) | M, about 7 h | T3 | decides `effective_policy_widens_host`/`effective_policy_invalid`; a shared bug would widen three families at once; do last, only if the above landed cleanly |

Registry candidates were evaluated and **none is recommended for production change** (annex B): REG-1..6, 10, 14, 16, 19, 21, 22 are historical-compatibility (byte-frozen, pinned), REG-9/11/12 are deliberate security redundancy, REG-7/13/15/17/18 are independent boundaries; REG-8/REG-20 (about 34 lines) are below the cost of a change. Not recommended at all: **CP-5** (family rows are persisted; STOP-ARCHITECT if any value moves) and **CP-7** (two profile digests of 46 commitments per execute; the re-verification costs more than it saves).

Honest summary: the planned Registry consolidation (R2/R3) is already realized by the unified engine for new versions and is otherwise blocked by byte-pins; the achievable consolidation is a small, low-risk Control Plane cleanup (estimate ceiling about 205 lines, 7.7% of the layer) plus test-helper cleanup. A LOC reduction is not the success criterion (plan section 7).

## 2. Reconciliation of the R1 Static Plan v1.0 with the merged implementation

| Plan package | Status against live source |
|---|---|
| R0 Verify 19/19 | Done in `00-...` (heads, merge chain, D-07 on `main` via #97). Architect confirmation of entry still required. |
| R1 Baseline and pin | Structural metrics produced by this inventory (annexes B/C). **Not produced:** wall-clock times, skip counts, mutation numerators, uncovered branches, external-output baselines. Becomes WP-0 below. |
| R2 Registry verification consolidation | Already realized for non-frozen paths by `registry_successor/engine/` (v7/v8 cost 101/110 lines vs mean 895). Frozen v3-v6 may not be edited or made to import the engine. Residual duplication is documented, not removed. **No production work recommended.** |
| R3 Registry composition/identity cleanup | The typed family registration and effective-policy digest plumbing exist in the engine (REG-9/13/17 are boundaries). **No production work recommended.** |
| R4 Control Plane integration cleanup | Substantive remaining work: CP-3, CP-1 (A then B), CP-4, optional CP-2/CP-6. |
| R5 Test and evidence consolidation | CP-9 and CP-8 only; Registry pinned tests (REG-19/21/22) stay. |
| R6 Consolidation acceptance, R7 Freeze, R8 one independent Tier 1 campaign, R9 Closeout | Unchanged. R1-E (Ergonomics) is **proposed only** (Registry #76 open, unmerged), so it is not part of any dispatchable package. |

## 3. Recommended R1 work-package sequence (dependency-ordered; each independently revertible)

Common to every package: single designated writer; the protected evaluators (`bounded.py`, `freshness.py`, `policy_binding.py`, `rule_revision.py`, `reversibility.py`, `holder_inventory.py`, `runtime_authority.py`), all `registry_successor/v2_*..v7_*` and the frozen engine files, schemas, vectors, approval preimages and all historical evidence are **immutable paths**; rollback is `git revert` of the package commit(s) (no persisted data is involved); stop-and-escalate on any refusal-order change, persisted-schema/row change, approval-preimage or reason-vocabulary change, any protected or pinned file outside the package's writable set, or any behavior difference in the differential oracle. Every PR carries a CI Scope Declaration; no required check is bypassed; no automatic merge.

| Package | Content | Writable files (exact, Control Plane unless stated) | Deleted/replaced duplication | Behavior-preservation evidence | Tier / tests |
|---|---|---|---|---|---|
| **WP-0 Baseline capture** (no code) | run the existing gates and full suites at pinned heads; capture wall-clock, skips, test counts, mutation numerators; hash manifests; keep failures | docs only (`docs/post-migration/`) | none | raw logs and counts for both mains; 41 known environmental failures retained | T1; the existing seven gates plus full suites, once |
| **WP-1 Test-helper cleanup** | CP-9 + CP-8 | the governed test modules that carry the 15 helper groups, one new non-collected shared test module, `pyproject.toml` (one line) | 151 redundant test lines | collected count unchanged (3,082), each gate count/threshold unchanged and 0 skipped; Registry pin import enforcement not weakened | T1; seven gates |
| **WP-2 Shared strict parser** | CP-3 stage A | `registry_effective_policy.py`, `registry_f5_class_unreadable_governance.py` (unpinned) and the owner module `registry_revocation_governance.py` only if the helper must be exposed | 2 of the 4 parser copies and 1 of 2 extractors | the 20,013-document differential rerun at the new head; `test_n03/n08/u01/s05/s06` named in annex C | T2; affected suites |
| **WP-3 Shared Registry-call preamble** | CP-1 stage A | `registry_revocation_governance.py`, `registry_irreversibility_governance.py`, `registry_final3_governance.py`, plus one shared helper module | 3 x 30 identical lines | identical refusal codes/order across `material_invalid, registry_unavailable, verifier_not_admitted, registry_call_failed, registry_decision_invalid`; monkeypatch seams retained | T2; affected suites |
| **WP-4 derive_policy tidy** | CP-4a then CP-4b | `registry_governed_policy.py`, `registry_effective_policy.py` (`FAMILY_NAMES` only) | 3 x 11 lines and one list | the existing literal-order assertions (`test_irreversibility_governance.py` near L381; `test_effective_configuration_binding_dedicated.py` L329; `test_final3_composed_binding.py` L253) | 4a T1, 4b T3; broad governed suites |
| **WP-5 (optional, Architect choice) Pinned-module stage B** | CP-3 stage B, CP-1 stage B, CP-6 | the byte-pinned `registry_f4_age_governance.py`, `registry_f5_class_age_governance.py` and the other pinned consumer modules | about 64 + 14 lines (estimate) | deliberate re-pin with recorded old and new hashes in the same PR; **F3-A/F3-B evidence for these modules is then no longer transferable** | T3; all gates plus F3 re-scope |
| **WP-6 (optional, last) Narrowing check** | CP-2 | the three family modules | 88 lines (measured duplicates) | differential over every widening/stricter case; `test_n01`, `test_a02`, `test_f01..f03` | T3 |

Registry: no production package. Residual duplication is recorded (annex B); no frozen module is edited.

## 4. Gates (all must hold; none is satisfied merely because a PR merged)

Gate 1: F3-A/F3-B independent qualification of `main` (handoff `01-...`) or an explicit BLOCKED report with retained evidence. Gate 2: Architect review of this inventory and the packages. Gate 3: explicit authorization of named packages. Gate 4: equivalence and negative behavior verified at the exact implementation heads. Gate 5: engineering freeze, then the prescribed independent Tier 1 campaign. Gate 6: separate security/IP and release decisions. Standing holds are unchanged (see `00-...`).

## 5. Interaction between R1 and F3 (for the Architect)

F3-A/F3-B qualify the merged behavior at the current `main`. Packages WP-1 to WP-4 touch no protected evaluator, persisted schema, approval preimage or pinned consumer module, so F3 coverage remains applicable to the unchanged authority-bearing modules; but any package that edits `registry_governed_policy.py`/`registry_effective_policy.py` (WP-4) or the family modules changes source under the F3-A subject (`registry_final3_governance.py` and others are in the F3-A source list), so a post-R1 differential or targeted re-qualification is needed. The plan's single final Tier 1 campaign at the R7 freeze covers this; the choice of whether F3 is run before or after R1 is Decision D2 in `04-...`.
