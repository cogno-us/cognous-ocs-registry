# Version compatibility and migration evidence (2026-10-29)

Status: BUILDER_TESTED developer record. Non-authorizing. Not independently qualified (DEFERRED, NOT WAIVED). Governing: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Plan v1.1 s.12, Engineering Plan v1.5, audit #60, #65/#67, architecture v1.0 (#68, `d7eb6be`).

## Heads recorded
| Item | Base | Head |
|---|---|---|
| Registry #69 (r08-v6) | `e8b572c` lineage | `42a666328b974a7581013358bcf8bc7b9eac7761` (unchanged) |
| Control Plane #92 (r08-v6) | `4780abe0af54147c0770e98cb7b964b74b2008c4` | `a62ca8d8e4088c95407c2000dcca081383d8dd4d` (unchanged) |
| Registry docs #70 | | `f309ae20a194786a45a708118b93603ee4670096` (unchanged) |
| Registry #71 (r08-v7 engine; stacked on #69) | `42a6663` | `b73c59e6769acd5af7263397e81dfc6fa4561f38` |
| Control Plane #93 (irreversibility + snapshot; stacked on #92) | `a62ca8d` | see PR #93 (head at time of writing recorded in the final report) |

## Frozen compatibility (Registry)
- `tests/vectors/r08v7/frozen_baseline_manifest.json`: 193 files (r08-v1..r08-v6 modules, contracts, tests, vectors) byte-identical to `42a6663`; a test pins it. Independent review confirmed by `git diff`: the only existing file edited is `tests/test_ext_s1_5_identity_module.py` (allowlist addition, as each earlier contract did).
- Engine differential: `engine(V6_COMPAT)` equals the frozen v6 entry points (decisions, verification reports, parse/validation results, identity digests, preimages, refusals, table dispatch). One real byte difference (structural-layer detail text) was found by the differential test in development and fixed before the final runs. The independent reviewer re-ran 7000+ generated cases (mutated envelopes, records, trust snapshots, an optional/required x caller x selection x record x trust matrix): 0 mismatches.
- Cross-version: v3..v7 documents are accepted only by their own contract and refuse `contract_unsupported`/`family_unsupported` elsewhere; a statement signed under another version's domain never verifies. No fallback, no implicit upgrade.

## Control Plane compatibility
- Pre-existing configurations: six configurations built on `a62ca8d` (Registry `42a6663`) and on the v7 branch (Registry `b73c59e`) have byte-identical `configuration_digest` and `effective_profile_digest` (reviewer-verified; also a golden-literal test). The identity dict gains the key `class_irreversible: None`; digests do not change.
- Protected evaluators (`bounded.py`, `runtime_authority.py`, `freshness.py`, `policy_binding.py`, `rule_revision.py`, `reversibility.py`, `holder_inventory.py`) byte-identical (empty `git diff`, tested).

## Test results (same interpreter/venv for branch and baseline)
| Suite | Baseline | Branch |
|---|---|---|
| Registry whole suite | main `d7eb6be`: 1 failed / 7476 passed / 2 skipped; base `42a6663`: 1 failed / 8019 / 2 | v7 `b73c59e`: 1 failed / 8469 / 2 (+450 = the new v7 tests) |
| The one failure | `test_adapter_ed25519.py::test_installed_cryptography_matches_the_test_only_lock` | identical on all three; environment cryptography differs from the lock; compared against baseline, not assumed |
| Control Plane whole suite, Python 3.11 and 3.12 (no Registry pin) | main `4780abe`: 1359 passed / 101 skipped (both) | #92 head: 1359 / 102; v7 head: 1406 / 103 (+47 unit tests; +2 pin-gated module skips) |
| Control Plane pinned set (5 files, Registry `b73c59e`, `OCS_REQUIRE_REGISTRY_PIN=1`) | n/a | 576 passed / 0 skipped |
| Mutation, Registry engine | | 126 mutants / 124 killed / 2 proven equivalent (IR26, DE08) |
| Mutation, Control Plane | | 78 / 78 killed |

## Migration / rollback
Nothing migrates records: v6 records stay v6; v7 is additive. Rolling back v7 means not merging #71/#93; no v1..v6 behaviour depends on them. The `V6_COMPAT` profile is verification reuse, not a re-signing of v6 records.

## Known low findings from the independent review (recorded, not hidden)
L-2 `engine.decide.decide_verified` is public (predecessors kept it private; a duck-typed report is trusted; the Control Plane does not reach it); L-3 `final_composition_defect` re-evaluates only one flip cause (defence in depth; the host-based pre-check and the profile validator close the others); L-4 a replacement selection with the same effective value but another selection id/epoch is accepted at boundaries, as the existing families do, and the snapshot names the construction-time selection; I-4 the verifier object is caller-supplied by design in every version. L-1 (snapshot re-read) was fixed in Control Plane #93.
