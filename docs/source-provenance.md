# Source provenance (S01)

Written 2026-10-24 by the S01 implementation worker, revised once after builder-side checks. Non-authorizing. Release, publication and production are on HOLD. Nothing here is a qualification, certification, security clearance or readiness claim. PR #1 and every check cited here (mine and other builder-side workers') are builder-side inspection, not independent qualification; a separate reviewer is still required.

VERIFIED = read from the named source by REST, or run in this session. REPORTED = stated in a source document I did not re-run.

## 1. Selected baseline (operator-selected under D1; not an original release, not independently qualified)

The S01 baseline, explicitly selected by the operator on 2026-10-24 (decision D1, `docs/decisions/2026-10-24-operator-decisions-D1-D5.md`), is the hub's "v0.1 public review" tuple `g8-r10` (a review marker, not a version or release), reduced to one component: Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`, files `engine/__init__.py` and `engine/safe_executor.py`. The operator selected it as the authoritative historical reference for the registry migration program; it is not described here as the original OCS release, a published release or an independently qualified baseline. The embedded `CONTROL_PLANE_COMMIT` mismatch noted in section 2 is preserved unmodified (D2). Reasons the builder identified for the choice:

1. The hub labels this tuple "v0.1": annotated tag `review-v0.1-g8-r10-20261022` (hub tag object `00c915d3...`, peeled commit `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c`), and the register titled "Known issues register: v0.1 public review release (candidate g8-r10)". The tag message says it is a review marker, not a version or release; contracts stay `0.1.0-draft`. The tag exists in 14 repositories: the 11 lock repositories plus hub, qualification and ergonomics (`prp`, `research_intelligence`, `tfa` have no tag).
2. The hub's MVP definition says "Components at the existing g8-r10 tuple, unchanged on main (pre-F3 text, superseded in part: ...)". "pre-F3" describes that text, so `g8-r10` precedes the F3 repairs. Read by REST at hub main `51c579a3208149922649a31a6eb041106a4121c3` (`docs/mvp-recovery/mvp-definition.md`, line 9); that file does not exist at the tuple commit `a2d9396c`.
3. The hub's registry catalogue manifest (`docs/mvp-recovery/registry/catalogue-v0.1/manifest.json`, hub main `51c579a3`) lists the `g8-r10` hub tag among its source revisions. Pointer only; the catalogue is not imported.
4. `engine/safe_executor.py` is byte-identical (blob `2fc880dae37eac76e5074533435740ce0684209d`, 44,576 B) at `g8-r10` and at the MVP Runtime `c5e97e87`, so the F3 repair does not touch it.
5. It holds a small family of hardcoded local restrictions (`LocalExecutionPolicy.check`) reachable through the real `execute_snapshot` path with the standard library only. No survey of alternative families was made; section 5 names one other.

Whether `g8-r10` is the "original v0.1" the operator intends is not established by the sources. Chronology: "v0.1" labels the **latest** pre-MVP tuple (2026-10-22). The bounded V1 reference tuples (W7, `f5b`) are **earlier**, so "original v0.1 then later V1 candidates" does not match the record.

## 2. Exact revisions of the selected tuple

Hub `component-lock.json` at `a2d9396c`: sha256 `dcd3ab9e4e737c7e50f4bc38c2439438f156da64c9eb1e46725f477973da59ff` (VERIFIED, fetched and hashed); `runtime_profile` `security-runtime-p2-20261018`.

| Lock key | Repository | Revision | Imported |
|---|---|---|---|
| `moltbot_safe` | `cogno-us/cognous-execution-runtime` | `ec728da6dc301a664b331ac8986afd6e850a1273` | two files |
| `control_plane` | `cogno-us/cognous-control-plane` | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | no |
| `replay_bundle` | `cogno-us/cognous-replay-bundle` | `028f63d1c001f99580583888fa4b4e46d77a267b` | no |
| `governance_evidence_pack` | `cogno-us/cognous-governance-evidence-pack` | `a3ebbb90559a44a88855139a182649d3792bb1ca` | no |
| `odes` | `cogno-us/open-decision-evidence-standard` | `e86a25a1d660e74533337d38744e2934200a50ae` | no |
| `action_manifest` | `cogno-us/cognous-action-manifest` | `fa170815ef96a54c233d0dd9da821b60debabf8b` | no |
| `verifier` | `cogno-us/cognous-open-control-stack-verifier` | `c0b8ba1f55b75db787a320f3de0f79342c6f6826` | no |
| hub | `cogno-us/cognous-open-control-stack` | `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c` | no |

The lock names further components (governed exchange `7f7569b0`, institutional governance `9b5ab721`, evidence attestation `981036c3`, evidence registry `b2485998`, `prp`, `research_intelligence`, `tfa`); none is imported.

Note (VERIFIED, imported file line 17): `safe_executor.py` hard-codes `CONTROL_PLANE_COMMIT = "2ea9528eeb87e14ff10f05de06473122b9df540f"`, older than the lock's Control Plane `0a41faa9`; even the `g8-r10` Runtime self-declares a different Control Plane than the lock pairs it with.

Historical evidence (REPORTED, hub known-issues register): qualification run `g8-r10` ([39690459403](https://github.com/cogno-us/cognous-stack-qualification/actions/runs/39690459403), validation `v1-2026-10-16-a`, profile `r13`, workflow `4a57a309`, results at qualification `27e3deb1`): PASS over a reduced mandatory claim only (39 rows); unreduced verdict INCOMPLETE; 34 jobs PASS, 2 FAIL, 2 NOT RUN; self-run, not independently audited. Not re-run here.

## 3. Candidate census and tuple comparison

All candidate tuples the sources name (read by REST at the hub tag commit `a2d9396c` unless noted). Tag-name SHAs below are peeled commits, not tag objects.

| Candidate | Hub revision | Control Plane | Runtime | Status as read |
|---|---|---|---|---|
| merged-consumer-chain (`merged-producers-v1`), earlier selected lock | `fa27954a4b8ab142f7e110eef36a96b4b5b7799b` (2026-10-07); accepted merge `f801546d5272104b02a240e1126b3f92f26486f2` | `d3dadee70bd319812b207389ab1e0f6efe511916` | `c3c3ee7188b9367cf70b08074b9c40a5c70c94ac` | selected lock at the time |
| W7 bounded V1 reference | merge `f7d03c719b9be3b9c3fe0fe300df642b0f408d98` (profile `w7-bounded-v1-component-lock.candidate.json`) | `e66e5f163c5d5c112ff345a2f332b4c3893ee183` | `da9f52900ee2596dab087ec6c249ba84915d2b13` | bounded V1 reference candidate |
| remediation-candidate-20261015 | profile only | `c7f122ba3a6e39f9268a7163c99be3ee514cd97e` | `309e194c1b0a3de23e11e20133e6eaf88875e48a` | `selected: false` |
| security-runtime-candidate-20261016 | profile only | `996baeb476c8745b1a58ddc968b9eecc6a39b76b` | `fd6b76fa0e85feb5b67324114bf790d3a12fdaf1` (the upstream quarantine commit) | `selected: false` |
| **hub component-lock at the `f5b` tag** (`public-reference-f5b-20261016`) | `a2d3a509856e1621105664c5f11195f6f6b100ce` | `d3dadee70bd319812b207389ab1e0f6efe511916` | `c3c3ee7188b9367cf70b08074b9c40a5c70c94ac` | older components; lock unchanged by the tag |
| **`f5b` candidate profile** (`profiles/security-runtime-f5b-candidate-20261016.json`) | same hub tag commit | `a34c3dc26f84a767a55f9d5c89dc0b53e63fefa5` | `e20f92e104aba2ba6ad06120d8549c6170eaf63f` | `selected: false`; also Replay `79ba16d48b9be1e059b3045989c7df960c3df1c2`, Evidence Pack `893aca8dfb27ba5c5f3e833f2d29210ca7fc92e3`, ODES `eb83220c82f942e429a5e3ef5f677fdd5057ef84`, Exchange `8be6c6b80da8c5038d66419f84c10cc529f78137`, Manifest `2c36bcd0b620dbfe7ad924bc7196a3f0c04c5c5e` |
| g5 / g6 hub freezes (2026-10-21) | source commits `64d89d6f130673b641eb50e322241b7316e884cd`, `97ed5364dd962b61fac520f93c462c623ce87ddb` | not read | selected `c3c3ee7188b9367cf70b08074b9c40a5c70c94ac` | freeze manifests; g7 is named only in the known-issues register and no tuple was read |
| **v0.1 `g8-r10` (selected for S01)** | `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c` | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | `ec728da6dc301a664b331ac8986afd6e850a1273` | review marker; lock sha256 above |
| MVP candidate (2026-10-23/24) | `c897266b7ce4b921889519087fa8b1863b4302e3` | `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` | `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` | provisional, UNQUALIFIED |

MVP tuple rest: Replay `40012b8c174c6f25685bd5d9bc93ff46cc9a5842`, Evidence Pack `7b9511f2c6d56d424f17b078826594abd29f6c96`, ODES `1a5e1d300250d832e611633f0bf8f762e398c0ec`, Verifier `c0b8ba1f55b75db787a320f3de0f79342c6f6826`, Action Manifest `fa170815ef96a54c233d0dd9da821b60debabf8b`; these match hub `docs/mvp-package/candidate-manifest.json` (blob `7afef8de62cb0c9ce5ba0ba48cac242e50112f65`) at hub main `51c579a3`, whose `status` reads UNQUALIFIED and `provisional` true.

`safe_executor.py` by Runtime revision (REST): `c3c3ee71` blob `ed7cd85f` (27,771 B); `da9f5290` `a13892f0` (31,540); `e20f92e1` `aedb0cd5` (37,177); `ec728da6` and `c5e97e87` both `2fc880da` (44,576). The first three have no `target_match` or `_target_is_well_formed` (searched); segment-aware matching arrives in Runtime #114/#115 before `g8-r10`.

## 4. Dependencies

Python 3.12 (Runtime CI `python-safety.yml` at `ec728da6`; qualification also ran 3.11/3.12, REPORTED). The imported module uses the standard library only. Test lock `requirements-s01.lock.txt` is a byte copy of the Runtime's `.github/locks/pytest-b61d81.txt` (sha256 `257be2880f0486e1ec637276cd13755e02969b257c8da089c1b744914ac11cb3`): pytest 8.3.5, pluggy 1.7.0, iniconfig 2.3.1, packaging 26.3. The Runtime's wider suite lock adds pydantic 2.11.9 (not needed here); the MVP profile is CPython 3.13 with pydantic 2.13.5 (not the baseline).

## 5. Imported, not imported

Imported: 6 files, 69,370 bytes, under `baseline/execution-runtime/`; each is byte-identical to the Runtime at `ec728da6` and a test asserts the blob ids.

| File | Bytes | Blob |
|---|---|---|
| `engine/safe_executor.py` | 44,576 | `2fc880dae37eac76e5074533435740ce0684209d` |
| `engine/__init__.py` | 32 | `9013e21fc7b3726aa9b65ddc381bfcb8310f2ccf` |
| `engine/LICENSE` (Apache-2.0) | 11,358 | `d645695673349e3947e8e5ae42332d0ac3164cd7` |
| `LICENSE-APACHE-2.0` (same text) | 11,358 | `d645695673349e3947e8e5ae42332d0ac3164cd7` |
| `LICENSE` (MIT, upstream Moltbot) | 1,074 | `f7b526698bb7ed2d26d96c49f2f32234c88f69bc` |
| `NOTICE` | 972 | `f2e9d127dbe54f68791e28cb6d1614909caf2d19` |

Bounded source-license check (S01 completion, 2026-10-24, VERIFIED by reading the files at `ec728da6`): `NOTICE` (Copyright 2026 Cognous) places the Cognous-authored `engine/` code, its tests and safety documentation under Apache-2.0 and keeps the MIT `LICENSE` (Moltbot, Copyright (c) 2025 Peter Steinberger) for the quarantined upstream application and upstream-derived retained files. Neither imported `.py` file contains a copyright, SPDX, Moltbot or licence string, and neither is named among the upstream-derived files in `NOTICE`. The MIT text is retained unchanged as notice material; no finding that the two imported `.py` files are upstream-derived was made, and none is claimed. New Cognous-authored material in this repository (documents, tests) is licensed Apache-2.0 per operator decision D3 (root `LICENSE`, see `LICENSING.md`); ownership of those files has not been independently verified and no sole-copyright claim is made. Per-file headers are not required by the retained texts as read; this is not legal advice.

Licenses (GitHub SPDX, VERIFIED): hub, Control Plane, Replay, Evidence Pack, ODES, Verifier, Action Manifest Apache-2.0; Runtime repository root MIT, while its `NOTICE` says `engine/` is Apache-2.0. No separate third-party notices file exists in the Runtime tree beyond `NOTICE`. File-level headers were not audited.

Not imported: the historical catalogue and all generated artifacts; the Control Plane, Replay, Evidence Pack, ODES, Verifier, Action Manifest; other Runtime modules; the Runtime test suite; qualification, CI and release machinery.

Candidate files for later sprints (not imported, no decision made): Runtime `engine/effective_grant.py`, `engine/permissions.py` with `permissions.json`, `engine/action_schema.py` (read); Control Plane `policy_gate.py` and `reason_vocabulary.py` (names INFERRED from hub documents, not read). Control Plane scanners, mandatory-check manifests, reason codes and the policy gate are outside this baseline.

## 6. Later improvements (listed, not imported)

| Change | Revision | What it changes |
|---|---|---|
| Runtime #144, F3 NC1-04 approval revocation terminal | merge `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f`; REST head `ee1ff55c250455a3bb14939ca0ce10aeeac70ccb` (hub architect ruling names head `d291eda7`) | terminal revocation per `approval_ref` on `AtomicAuthorityEffectDestination`, retained table `authority_approval_revocations_v1`; `engine/local_authority_effect.py` +52/-3 plus two test files; revoked to `unknown` now refused. `safe_executor.py` unchanged |
| Control Plane #83 claim-journal repair | merge `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (candidate `df4794c8`) | binds the claim-stage journal check to stage, decision and a distinct `check_ref` |
| Replay #78/#79, Evidence Pack #63/#64, ODES #139/#141 | Replay `40012b8c...`, Pack `7b9511f2...`, ODES `1a5e1d30...` | `failure_class` admission on route B denial; re-pins to the F3 revisions |

Recorded as historical GitHub facts only; authorization and independent-review status are unresolved where primary evidence is unavailable, and these merges do not establish qualification of this baseline. Facts left for the operator: the bodies of Runtime #144, Replay #79, Evidence Pack #64 and ODES #141 say DRAFT and (for #79, #64, #141) "do not merge before independent review"; REST shows all four merged (Replay #79 2026-10-24T00:37Z, Pack #64 00:41Z, ODES #141 00:47Z). Evidence Pack #64 cites an "operator directive of 2026-10-23". Control Plane #83 and Replay #78 say "operator-authorized". The hub states the later pins are provisional and UNQUALIFIED (candidate-manifest.json) and that NC1-04 stays a FAIL until requalified (architect-rulings-3, REPORTED). The approval question is not resolved here.

## 7. Reproduction record

Lock self-label: the selected hub `component-lock.json` itself carries `qualification_status: "accepted"` (with its own qualification evidence reference). This repository does not adopt or re-verify that label; per operator decision D1 the tuple is not described here as independently qualified.

Independent-review status (D4 condition 5): a fresh-context reviewer session was briefed by the builder coordinator and found 0 blockers, 2 major and 6 minor findings (provenance, byte identity, lock hash and the `CONTROL_PLANE_COMMIT` mismatch independently confirmed; legacy-prefix wording corrected; well-formedness tests added; 63 tests now pass). That reviewer stated it is not independent of the PR author in the CA04/CA23 sense. It is recorded as coordinator-directed review, not independent qualification.

Review-round verification at PR head `58e9bc46` (S01 completion session, 2026-10-24, not independent qualification): (a) a fresh `git clone` checked out at that head, hash-locked venv, CPython 3.13.17: 13 passed; (b) a separate clone of `cogno-us/cognous-execution-runtime` at `ec728da6`: `git hash-object` of all six imported files equals both the local copies and the blob ids in the test (so byte identity is checked against the upstream revision, not only against constants); (c) hub `component-lock.json` at `a2d9396c` hashes to `dcd3ab9e...` and the tag `review-v0.1-g8-r10-20261022` peels to `a2d9396c`. A read-only reviewer worker found boundary and ordering gaps; four tests were added (17 total). Scratch mutants `amount >= max`, `effective_max_effects >= max` and institution/domain order swap were each caught by the suite at that point; these mutation runs are supplementary scratch observations, not retained or reproducible evidence, and are not cited as qualification.


Clean venv (`python3.12 -m venv`, `pip install --require-hashes -r requirements-s01.lock.txt`), CPython 3.12.3, Linux 6.18.44. Results are in `docs/sprint-status.md` for the PR head. At the first head (`13e7d2de`, 11 tests) a separate builder-side worker re-ran 11 passed on 3.12.3 from a clean clone (not independent qualification); the 3.11/3.13 passes are self-run and were not re-run by another worker.

Finding: `LocalExecutionPolicy.check` has an "exactly one effect" branch ("local adapter supports exactly one effect"), but it is not reachable through the real path: `snapshot_envelope` and `validate_snapshot` refuse `effects != 1` first with `ValueError: effects must equal exactly 1`. The fixture asserts that behavior and the zero-effect, recorded refusal; the mutant below survives for that reason.

Mutation checks (scratch copies, not committed; each makes one restriction allow everything, then the full suite runs; the blob-identity test fails in every case, as expected):

| Mutated check | Behavioural test that failed |
|---|---|
| institution, authority domain, adapter, action, unit, amount, effective max effects | the matching parametrized refusal test (one each) |
| target | refusal-case test and segment-aware test |
| `effects != 1` | none (unreachable branch, mutant survives) |

An earlier mutation (target check, 2026-10-24 first round) failed the refusal test as well.

## 8. Unqualified, unsupported, not done

- Known untested behaviour (to be inventoried in S02 and tested in S05 before any family relies on it for equivalence): `LocalExecutionPolicy.__post_init__` fail-closed validation of malformed policies; `_strict_finite_number` / `_strict_positive_int` rejections (NaN, inf, bool, zero, negative); check order beyond the institution-before-domain pair; recording of the `policy_denial` failure row for each restriction other than target (only target and the `effects != 1` validation path assert it); the unreachable "exactly one effect" branch. Covered after the review round: malformed-target well-formedness (control, format, separator, surrogate characters, dot-segments, every match mode), `/` and `:` boundaries, `exact` mode, and `legacy-prefix` (tested for the non-boundary spill case; not combined with every malformed form).
- Nothing is qualified. The fixture covers the Runtime local policy and SQLite destination only; the Control Plane is intended to call this module (hub documentation, not re-verified here).
- Hub narrative documents were first read from a local clone whose head is not visible by REST. Re-read by REST: `mvp-definition.md` and the catalogue manifest at hub main `51c579a3`, the locks, profiles, freeze manifests and `candidate-manifest.json`. Other hub document citations (known-issues, release-status, bounded-v1, dependency-manifest, architect-rulings) are as read locally and not re-verified at a REST-reachable commit. Runtime and component files were read by REST at exact revisions.
- g7 tuple not read; Control Plane contents of #83 and Replay contents of #78/#79 were checked only through REST titles, bodies and compare listings.
- The upstream Runtime suite was run once in a scratch checkout (499 passed, 33 skipped, Control Plane absent) and is not part of this repo.

## 9. Governing references and Engineering Constitution

- Static plan: OCS-REG-PLAN v1.1, https://github.com/cogno-us/cognous-ocs-registry/blob/s01-baseline/docs/plans/PROJECT_PLAN-v1.1.md (S01 section).
- Engineering Constitution, exact pin: https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md (commit `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`). Its text was fetched and read in the S01 completion session (2026-10-24). The earlier reference to revision `6f7f2731` and the statement that the text was unavailable are superseded by this pin; the earlier wording is retained in Git history.
- Formal adoption: the plan states it does not itself adopt the Constitution; no adoption record was located by this work. Publication of the pinned text confers no adoption.
- Additional articles assessed for S01 (CA14, CA19, CA20): CA14 (secure by construction): the import adds no network, subprocess, cloud or credential effect observed, but no enabled-path security review was done; the imported module is security-sensitive source that warrants focused independent boundary inspection. CA19 (canonical integration): this PR is a proposal; nothing here is canonical until the operator accepts the baseline and an authorized maintainer merges. CA20 (scoped delegation): builder and worker actions were limited to S01 files on this PR branch; no authority beyond the S01 authorization is assumed.
- Risk classification note: per the pinned Constitution, Tier 1 is highest criticality and Tier 3 lowest. S01 changes are documentation and metadata (Tier 3) plus characterisation tests (Tier 2); the imported historical source itself is Tier 1 in subject matter (authority/admission) but is unchanged. The Architect disposition's wording that maps documentation to Tier 1 and authority changes to Tier 3 is inverted relative to the pinned table; it is not adopted here and is flagged for Architect correction.
- Governing documents are cited by branch `s01-baseline` plus exact reviewed commit until merge; main-branch paths do not exist yet and are not treated as canonical.
- Articles materially applied to S01 (inspection of this PR's diff against them, not conformance certification): CA01, CA02, CA04, CA05, CA06, CA07, CA09, CA10, CA11, CA12, CA15, CA16, CA18, CA23. Per CA04/CA23 nothing here is independent qualification.
