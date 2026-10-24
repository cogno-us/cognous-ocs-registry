# Source provenance (S01)

Written 2026-10-24 by the S01 implementation worker. Non-authorizing, builder-side. Release, publication and production are on HOLD. Nothing here is a qualification, certification, security clearance or readiness claim. A reviewer separate from this worker has not yet read this record.

Labels used: **VERIFIED** (I read it from the named source or ran it in this session), **REPORTED** (stated in a source document I read; I did not re-run or re-derive it).

## 1. Proposed S01 baseline

**OCS v0.1 review tuple `g8-r10`, reduced to one component: Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`, files `engine/__init__.py` and `engine/safe_executor.py`.**

Status: PROPOSED, determined from the hub's own records, for operator confirmation. The baseline is not "UNDETERMINED", but the word "original" is not used by the sources, and earlier candidates exist (section 3). Reasons for the choice:

1. The hub names this tuple "v0.1". Its annotated tag `review-v0.1-g8-r10-20261022` exists in 14 repositories, and the hub's `docs/releases/v0.1-known-issues.md` calls it "the v0.1 public review release" (VERIFIED, hub docs; tags VERIFIED by REST). The same documents say the tag is a review marker, not a version or release, and that contracts remain `0.1.0-draft`.
2. The hub's MVP definition describes `g8-r10` as the existing, "pre-F3" tuple that the October MVP candidate re-pins after the F3 repairs (hub `docs/mvp-recovery/mvp-definition.md`, VERIFIED). So `g8-r10` is the last tuple before the F3 repairs, which is the "original v0.1 plus selectively retained improvements" shape the S01 mission asks for.
3. The chosen file `engine/safe_executor.py` is byte-identical (Git blob `2fc880dae37eac76e5074533435740ce0684209d`, 44,576 bytes) at `g8-r10` and at the MVP Runtime `c5e97e87` (VERIFIED by REST). The F3 repair does not touch it, so this baseline is not invalidated by the later improvement.
4. It is the smallest closed family of hardcoded rules with observable outcomes that runs with the standard library only: the Runtime's local execution restrictions (`LocalExecutionPolicy.check`), reached through the real `execute_snapshot` path.

If the operator intends an earlier "original" (the W7 bounded V1 reference or the `f5b` reference), choose it from section 3 and S01 should be re-run; the file differs at those revisions.

## 2. Exact revisions

Hub tag `review-v0.1-g8-r10-20261022` (annotated tag object `00c915d3a12400f38d1e753ecbe5576404c99840`) peels to hub commit `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c`. The hub `component-lock.json` at that commit has SHA-256 `dcd3ab9e4e737c7e50f4bc38c2439438f156da64c9eb1e46725f477973da59ff` (VERIFIED: fetched by REST at that commit and hashed; matches the value in the known-issues register). Lock `runtime_profile` is `security-runtime-p2-20261018`.

| Lock key | Repository | Revision (full) | Imported here |
|---|---|---|---|
| `moltbot_safe` | `cogno-us/cognous-execution-runtime` | `ec728da6dc301a664b331ac8986afd6e850a1273` | yes, two files |
| `control_plane` | `cogno-us/cognous-control-plane` | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | no |
| `replay_bundle` | `cogno-us/cognous-replay-bundle` | `028f63d1c001f99580583888fa4b4e46d77a267b` | no |
| `governance_evidence_pack` | `cogno-us/cognous-governance-evidence-pack` | `a3ebbb90559a44a88855139a182649d3792bb1ca` | no |
| `odes` | `cogno-us/open-decision-evidence-standard` | `e86a25a1d660e74533337d38744e2934200a50ae` | no |
| `action_manifest` | `cogno-us/cognous-action-manifest` | `fa170815ef96a54c233d0dd9da821b60debabf8b` | no |
| `verifier` | `cogno-us/cognous-open-control-stack-verifier` | `c0b8ba1f55b75db787a320f3de0f79342c6f6826` | no |
| hub | `cogno-us/cognous-open-control-stack` | `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c` | no |

The lock lists further components (governed exchange `7f7569b0`, institutional governance `9b5ab721`, evidence attestation `981036c3`, evidence registry `b2485998`, `prp`, `research_intelligence`, `tfa`); none is needed and none is imported.

Historical test evidence for this tuple (REPORTED, hub `docs/releases/v0.1-known-issues.md`): qualification run `g8-r10` ([39690459403](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/39690459403), validation `v1-2026-10-16-a`, profile `r13`, workflow revision `4a57a309`, results retained at qualification `27e3deb1`) returned PASS over the reduced mandatory claim only (39 rows); the unreduced verdict is INCOMPLETE; 34 jobs PASS, 2 FAIL (ODES suite, four declared tests), 2 NOT RUN; the run was not independently audited; the verifier entry was not probed. S01 did not re-run or rely on that run.

## 3. Tuple comparison

| | W7 bounded V1 reference selection | `f5b` public reference (V1 reference tags) | **v0.1 review `g8-r10` (proposed S01)** | October 2026 MVP candidate |
|---|---|---|---|---|
| Dates (REST) | Runtime merge 2026-10-08 | Runtime tag commit 2026-10-16 | tags 2026-10-22 | 2026-10-23 to 2026-10-24 |
| Runtime | `da9f52900ee2596dab087ec6c249ba84915d2b13` | tag `e20f92e104aba2ba6ad06120d8549c6170eaf63f`; the hub lock at the `f5b` hub tag still names `c3c3ee7188b9367cf70b08074b9c40a5c70c94ac` | `ec728da6dc301a664b331ac8986afd6e850a1273` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` |
| Control Plane | `e66e5f163c5d5c112ff345a2f332b4c3893ee183` | lock `d3dadee70bd319812b207389ab1e0f6efe511916` | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` |
| Replay | `2069a0ba1398812c3a8669331a7d8b87c80c4a48` | lock `459e4ba62fca49364aebb0050cd5fb2dd5a71bfa` | `028f63d1c001f99580583888fa4b4e46d77a267b` | `40012b8c174c6f25685bd5d9bc93ff46cc9a5842` |
| Evidence Pack | `87293cfcbe8dfa2368d5bf77019945ba8ef1ae71` | lock `b4baccd823d2a73be276c1de745b19cf7c56a0d6` | `a3ebbb90559a44a88855139a182649d3792bb1ca` | `7b9511f2c6d56d424f17b078826594abd29f6c96` |
| ODES | not in the selection table | lock `c5e9a0f3695ae836b803be06c46d2c669642ee03` | `e86a25a1d660e74533337d38744e2934200a50ae` | `1a5e1d300250d832e611633f0bf8f762e398c0ec` |
| Action Manifest | `8d1572d4f926c968a8704cb912a6e9d49166f74a` | lock `46c950bed37fe3812000895430bc0312d29e37ce` | `fa170815ef96a54c233d0dd9da821b60debabf8b` | `fa170815ef96a54c233d0dd9da821b60debabf8b` |
| Verifier | not in the table | not in the lock | `c0b8ba1f55b75db787a320f3de0f79342c6f6826` | `c0b8ba1f55b75db787a320f3de0f79342c6f6826` |
| Hub | merge `f7d03c719b9be3b9c3fe0fe300df642b0f408d98` | tag `a2d3a509856e1621105664c5f11195f6f6b100ce` | tag `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c` | `c897266b7ce4b921889519087fa8b1863b4302e3` |
| `safe_executor.py` blob (bytes) | `a13892f0...` (31,540) | `aedb0cd5...` (37,177) at the tag; `ed7cd85f...` (27,771) at the lock's Runtime | `2fc880da...` (44,576) | `2fc880da...` (44,576) |
| Target matching in `LocalExecutionPolicy` | plain prefix (no `target_match`) | plain prefix (no `target_match`) | segment-aware default, input hygiene (Runtime #114, #115) | same as `g8-r10` |

Sources: hub `docs/releases/bounded-v1-reference-release.md`, hub `docs/release-status.md`, hub `component-lock.json` at each hub revision (the `g8-r10` and `f5b` locks fetched by REST, the latter SHA-256 `dc66aafeb15eb2d5695b2217019775a1a2e517b3a6ab55b07c1b37349d8ee5cc`), hub `docs/mvp-package/candidate-manifest.json` (MVP revisions match the S01 task text exactly), and REST file reads of `engine/safe_executor.py` at each Runtime revision. The "no `target_match`" row was checked by searching those file contents. The W7 row's dates and blobs come from REST; I did not fetch the other W7 components.

Reading: the bounded V1 reference candidates (W7, `f5b`) precede `g8-r10` and have different Runtime policy code. The MVP candidate is `g8-r10` plus the F3 repairs (section 6) and re-pins; it is a later program step and is not the S01 baseline. The MVP tuple is provisional and described by the hub as UNQUALIFIED for the later pins (REPORTED).

## 4. Dependencies

| Item | Value | Source |
|---|---|---|
| Python for the baseline | 3.12 (Runtime CI `python-safety.yml` at `ec728da6`; qualification also ran 3.11 and 3.12 jobs) | VERIFIED workflow file; REPORTED qualification matrix |
| Runtime packages for the imported source | none (standard library only: copy, hashlib, json, math, re, sqlite3, time, unicodedata, uuid, dataclasses, pathlib, typing) | VERIFIED by reading imports |
| Test lock used here | `requirements-s01.lock.txt`: pytest 8.3.5, pluggy 1.7.0, iniconfig 2.3.1, packaging 26.3 (colorama on Windows only), hashes included | byte-for-byte copy of Runtime `.github/locks/pytest-b61d81.txt`, SHA-256 `257be2880f0486e1ec637276cd13755e02969b257c8da089c1b744914ac11cb3` |
| Full Runtime suite lock (not imported) | `.github/locks/pydantic-pytest-f8aeba.txt`: pytest 8.3.5, pydantic 2.11.9, pydantic-core 2.33.2, annotated-types 0.8.0, typing-extensions 4.16.0, typing-inspection 0.4.4, plus pytest's set; SHA-256 `9bf5704d232c2ca15fd843d96ea9a23fa217c771c1df6509794795b3bdf91dc6` | VERIFIED file |
| MVP profile (not the baseline) | CPython 3.13 only; pydantic 2.13.5, pytest 8.3.5, cryptography 50.0.0 | REPORTED, hub `docs/mvp-package/dependency-manifest.md` |

The Runtime has no `pyproject.toml` or `requirements` file at `ec728da6`; its `CLAUDE.md` gives the test command (`pip install pytest==8.3.5 pydantic==2.11.9`). pydantic is needed only by tests that touch the Control Plane path, not by the imported module.

## 5. What was imported, and why

Total under `baseline/execution-runtime/`: 6 files, 69,370 bytes. Plus `requirements-s01.lock.txt` (the lock above).

| File | Bytes | Git blob (equals the source revision) | Why |
|---|---|---|---|
| `engine/safe_executor.py` | 44,576 | `2fc880dae37eac76e5074533435740ce0684209d` | the behaviour under test: envelope snapshot and validation, `LocalExecutionPolicy`, SQLite destination, `LocalDestinationExecutor` |
| `engine/__init__.py` | 32 | `9013e21fc7b3726aa9b65ddc381bfcb8310f2ccf` | makes `engine` importable |
| `engine/LICENSE` | 11,358 | `d645695673349e3947e8e5ae42332d0ac3164cd7` | Apache-2.0 text for `engine/` |
| `LICENSE-APACHE-2.0` | 11,358 | `d645695673349e3947e8e5ae42332d0ac3164cd7` | preserved as the Runtime's `CLAUDE.md` requires (identical to `engine/LICENSE`) |
| `LICENSE` | 1,074 | `f7b526698bb7ed2d26d96c49f2f32234c88f69bc` | MIT, upstream Moltbot; `NOTICE` says it stays with the code |
| `NOTICE` | 972 | `f2e9d127dbe54f68791e28cb6d1614909caf2d19` | Cognous notice and license scoping |

The Runtime has no separate third-party notices file at that revision beyond `NOTICE` (VERIFIED by listing the tree). Nothing in `engine/safe_executor.py` was modified; `tests/test_s01_baseline_local_policy.py` fails if any imported file's blob id changes.

Licenses by component (GitHub-reported SPDX, VERIFIED by REST on 2026-10-24; none of the others is imported): hub, Control Plane, Replay, Evidence Pack, ODES, Verifier, Action Manifest: Apache-2.0. Runtime: GitHub reports MIT for the repository root; its own `NOTICE` states that `engine/` and its tests are Apache-2.0 while upstream-derived files remain MIT. Both texts are preserved. I did not audit file-level headers.

### Not imported, and why

| Not imported | Reason |
|---|---|
| Historical registry catalogue (hub `docs/mvp-recovery/registry/catalogue-v0.1/`, about 3,190 rules, 2,840 scenarios, 6,648 tests, evidence index) and its generated artifacts | Prohibited by the sprint restriction; read-only discovery only. I looked at file names only to recognise it. |
| Other Runtime modules (`control_plane_adapter`, `local_authority_effect`, atomic, dedupe, operation-identity, refund-intent, openshell, recovery) | Not needed to inspect the local restriction family; most need the Control Plane |
| Legacy `engine/permissions.py`, `action_schema.py`, `engine.py`, `audit.py` and `permissions.json` | A compatibility shell that "performs no side effect"; a second, smaller hardcoded-permission family, left as a candidate for a later authorized sprint |
| Control Plane, Replay, Evidence Pack, ODES, Verifier, Action Manifest, hub tooling | Not on the path of the chosen behaviour; they remain authoritative in their repositories |
| Runtime test suite (about 40 Python test files) | Bulk historical tests are prohibited. I ran it once in a scratch checkout for comparison only (section 7) |
| Qualification suites, CI workflows, release manifests, selected-notices, run logs | Release-packaging and evidence machinery; links only |

## 6. Later improvements (listed, NOT imported)

| Improvement | Exact revision | What it changes | Effect on the S01 file |
|---|---|---|---|
| Runtime PR #144, F3, NC1-04 "approval revocation is not terminal" | PR head `ee1ff55c250455a3bb14939ca0ce10aeeac70ccb`, merge commit `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (merged into main, VERIFIED by REST) | Approval revocation becomes terminal per `approval_ref` on `AtomicAuthorityEffectDestination`: a retained table `authority_approval_revocations_v1`, refusal of any non-revoked status on a revoked ref, provisioning refuses a revoked ref. Production change is `engine/local_authority_effect.py` (+52/-3) plus two new test files. Behaviour change disclosed in the PR: revoked to `unknown` is now refused. | none; `safe_executor.py` blob unchanged |
| Control Plane PR #83, F3 claim-journal repair | merge `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (candidate `df4794c8`, base `0a41faa9`) | Binds the claim-stage journal check to the claim stage, decision and a distinct `check_ref`, so completed journal checks no longer reuse the decision-stage identity (the Verifier refuted that as `journal_check_reused`; Replay refused the record). Change in `local_authority_effect.py` and `tests/test_claim_journal_stage.py` | none (different component) |
| Replay #78 / #79 | `ab421ad0`, merge `40012b8c174c6f25685bd5d9bc93ff46cc9a5842` | admits `failure_class` on route B denial exports; re-ties the Programme 2 pairing to Runtime `c5e97e87` | none |
| Evidence Pack #63 / #64, ODES #139 / #141 | `7b9511f2c6d56d424f17b078826594abd29f6c96`, `1a5e1d300250d832e611633f0bf8f762e398c0ec` | re-pins to Replay, Control Plane and Runtime F3 revisions | none |

The hub states that NC1-04 stays a FAIL until independently requalified and that the later pins are provisional and unqualified (REPORTED, hub `docs/mvp-recovery/architect-rulings-3-and-known-limitations.md`, `docs/mvp-package/dependency-manifest.md`). Whether the PR #144 merge was authorized by the operator is not established by what I read; the PR body I read says "DRAFT ... operator approval pending" while REST reports it merged. That discrepancy is left for the operator. I did not verify the Control Plane and Replay PR contents beyond their REST titles, bodies and compare listings.

## 7. Reproduction record (what was actually run)

Environment: Linux 6.18.44, x86_64, CPython 3.12.3 (system `python3.12`), clean venv created with `python3.12 -m venv`, install with `pip install --require-hashes -r requirements-s01.lock.txt`; `pip freeze` printed exactly iniconfig 2.3.1, packaging 26.3, pluggy 1.7.0, pytest 8.3.5.

| Run | Result |
|---|---|
| `pytest -v` in this repository (S01 fixture, 11 tests) on 3.12.3 | 11 passed in 0.44 s |
| the same on 3.11 and 3.13 (supplementary; 3.13 is the MVP interpreter, 3.11 a qualification interpreter) | 11 passed each |
| negative control: the target-restriction call in a scratch copy of `safe_executor.py` replaced by `if False:` | 2 failed (refusal test and blob-identity test), 9 passed, so the fixture detects that mutation |
| Upstream Runtime full suite at `ec728da6` in a scratch checkout (not imported), 3.12.3, `pydantic-pytest-f8aeba` lock, `PYTHONPATH=".:src" pytest -q tests`, Control Plane absent | 499 passed, 33 skipped, 0 failed; the skipped tests I sampled say they need the Control Plane contract on `PYTHONPATH` (I did not tabulate every skip reason) |

The fixture's positive case (`execute_snapshot` returns `executed`, observation `applied`, one effect row) and refusal cases (target refused with `local target restriction`, a `policy_denial` failure record, zero effects; plus one refusal for each other local restriction, in code order) all passed. The fixture's operation values are taken from the historical Runtime test helper; the test file itself is new. It proves that the baseline behaves as described on those inputs; it does not prove completeness over other inputs.

## 8. Unqualified, unsupported or missing

- Nothing here is qualified. The upstream qualification run is REPORTED only, over a reduced claim, self-run and not independently audited.
- The fixture covers the Runtime's local policy and SQLite destination only. It does not cover the Control Plane authorization decision, Replay, Evidence Pack, ODES, the Verifier, the 121 reason codes, scanners or mandatory-check manifests (the hub's other hardcoded rule families). A later sprint must decide which family comes next; S01 does not.
- Control-Plane-dependent Runtime tests (33 skipped above) were not run with the Control Plane.
- The `target_match="legacy-prefix"` mode and the amount and effect-count rules are tested only on a few values.
- I read hub narrative documents from a local clone at `2faf339a1231888c3f25d763b9bab3c77f56554d` (later than the tuple; not modified). Locks and Runtime files were read by REST at the exact tuple revisions.
- The Engineering Constitution repository was not readable in this session, so article titles were not checked.

## 9. Engineering Constitution status

Revision `6f7f2731` of `cogno-us/cognous-engineering-constitution` is PROVISIONAL guidance. No formal adoption record has been found: the hub's `docs/declarative-governance-registry.md` says adoption of an exact revision is a separate recorded act, and I found no such record. The articles in play for S01 are CA01, CA02, CA04, CA07, CA09, CA10, CA11, CA12, CA18 and CA23, as listed by the operator; I applied them as constraints (bounded scope, provenance, minimal import, no overclaiming, one-sprint stop) and did not read their text, so I make no claim of conformance with them. This worker implemented S01; a separate later reviewer is required, and no coordinator-directed review is independent.
