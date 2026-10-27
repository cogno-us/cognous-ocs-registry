# V09 component and dependency inventory (candidate)

Non-authorizing. Documentation and verification metadata only. Machine-readable form: [candidate-manifest.json](candidate-manifest.json). Every SHA below was read from the live GitHub `main` of each repository on 2026-10-27 and cross-checked against local git objects; no branch name is used as a pin.

## 1. Scope
Plan v1.5 and the adopted V03 cross-component baseline name four components plus the Constitution pin. No repository was added or omitted silently:

| In scope | Not in scope (stated, not omitted) |
|---|---|
| Registry, Control Plane, Runtime, Stack Qualification, Constitution (pinned revision only) | Governance Evidence Pack, Replay Bundle, Governed Exchange, Open Decision Evidence Standard, Open Control Stack and their workflows hosted in Stack Qualification: earlier MVP tuple, not part of the V01-V08 vertical slice, neither frozen nor qualified by this candidate. |

## 2. Candidate pins (verified `main`)
| Component | Repository | `main` commit | Tree | CI at exact head (post-merge) |
|---|---|---|---|---|
| Registry (baseline of this PR) | cogno-us/cognous-ocs-registry | `1a4de32605519c505142b1ba3a57fa5b259b0b2c` | `2e163b7bf7db570f5648c5bdd2ea74677ff0a472` | Registry tests run 40511770702 success; CodeQL success |
| Control Plane | cogno-us/cognous-control-plane | `d66ae07fa240510efdcc11ed4b3e1189dcefc822` | `7459fd97aaabec21a06887211d8ae79198c56047` (equals PR #86 head `0fd44d03` tree) | Tests run 40553723040 success (3.11 and 3.12, manifest-validator-parity); CodeQL success |
| Runtime | cogno-us/cognous-execution-runtime | `b5605f525ae73cbb7adcfef4716c67cdd33a5f7d` | `e0d7003e279cddad50062cfb111d498cb4e714de` (equals qualified commit `3873a61b` tree) | Python safety boundary 40575079412, Durable refusal capture 40575079986, Workflow Sanity 40575078458: success |
| Stack Qualification | cogno-us/cognous-stack-qualification | `bb9b08904192b5f50a49e00ed8de0cab80fd7c19` | `dcb663000706e1b4a5cdb233e6b2603d49eda52b` (equals PR #237 head `ed4f45a5` tree) | integrity 40575094573, catalog 40575094587, serial 40575094446, dashboard 40575094652: success |
| Constitution | cogno-us/cognous-engineering-constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (pinned; repository `main` has since moved to `a4dd1111`, which is NOT the adopted revision) | n/a | n/a |

The Registry entry is the baseline on which this docs-only PR is built. This PR's own merge commit cannot be named inside itself; the Architect records it in `docs/sprint-status.md` on merge. The merge commits above are merge commits, so first-parent and second-parent ancestry of every qualified PR head is preserved.

**Qualified-commit equivalence.** The F-A1 qualification (Stack Qualification #237, CI run 40555193111) ran against Control Plane `d66ae07f`, Runtime `3873a61b` and Registry `1a4de326`. Runtime `main` is `b5605f52`, a merge commit with tree `e0d7003e...`, identical to the tree of `3873a61b`, whose code tree is in turn identical to `ad1805e2` (the only difference is one added documentation file). The evidence therefore applies to the content of Runtime `main`, but it was not produced at the SHA `b5605f52`. An independent qualifier should pin the `main` SHAs above and re-run, not rely on this equivalence.

## 3. Contract versions
| Boundary | Version / reference | Blob (git sha1) |
|---|---|---|
| Registry record and selection | `r08-v2`, family `f1ab` (five sets) | contract `docs/r08-v2-contract.md` blob in manifest |
| Amendments | 1, 2, 3 (Runtime-side policy narrowing, V07 F-01), 4 (trusted authorization pin, V08 F-A1) | manifest `blobs_git_sha1` |
| Integration contract | EXT-S4-0 ADR (adopted, AD-1..AD-5) | manifest |
| Canonical policy binding | `ocs-policy-binding/1`, 15 named members; distinct from R6 `policy-binding/0.1` | Control Plane `canonical_policy_binding.py` |
| Claim profile | `local-authority-effect:0.2.0-proposed` (non-production) | Control Plane V02 |
| Reasons registry | `runtime-authority-reasons/0.3` (sha256 in manifest) | Control Plane schema |
| Authorization pin | `ocs-s4/authorization-pin/0.1`, 17 Control-Plane-sourced members plus installer-owned epoch, status and hash chain | `docs/authorization-pin-interface-freeze.md`, `engine/authorization_pin_format.py` |
| Protected source | `engine/safe_executor.py` blob `2fc880dae37eac76e5074533435740ce0684209d`, unchanged from the historical baseline in both Runtime and Registry `baseline/` | verified in manifest |

## 4. Dependency graph (what each component requires of the others)
- Registry: defines the contracts. Imports nothing from the other components at runtime. Vendors the historical Runtime baseline `ec728da6` under `baseline/` (retained MIT and Apache-2.0 notices).
- Control Plane: implements `ocs-policy-binding/1` and the authorization-pin export independently of Registry code; no code import of Runtime.
- Runtime: consumes Registry records and contract text at the pinned revision (tests resolve `OCS_REGISTRY_PIN_DIR`); does not import the Control Plane. The pin store format is frozen in-repo.
- Stack Qualification: pins all three by exact SHA in harness code (`suites/tier1-v08-fa1/conftest.py`) and workflow. V06 and V07 harnesses pin older revisions on purpose (historical baselines, listed in section 6).

## 5. Required source and artifact digests
Git blob SHA-1 for every relied-upon contract and source file, and SHA-256 for the files that Runtime F3 and the Control Plane reasons registry freeze, are in `candidate-manifest.json` and are checked offline by `tests/test_v09_candidate_integrity.py` (Registry-resident files) and online by `tools/verify_v09_candidate.py` (all four repositories).

## 6. Merged implementation PRs by sprint
| Sprint | Repository PR | Merge commit |
|---|---|---|
| V01a | Registry #43 | `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` |
| V01 | Runtime #145 | `b86fa5db8226a9a93a68d0f42bfa6b5cc5caa5fd` |
| V02 | Control Plane #85 | `1bee3696ee6cd8037d142cdbcdb6020e052b0480` |
| V03 | Registry #44 (docs) | `b1def8480135...` |
| V04 | Runtime #146 | `e55826f41efe...` |
| V05 | Runtime #147 | `4199a6c793cd9ec37a5fd451f7d99265dcf634fd` |
| V06 | Stack Qualification #232 | `ae12221831bc39beea6dbf0ae7fda726baeecf1f` |
| V07 | Stack Qualification #234; contract Registry #45; fix Runtime #148 | `90e0e56e69448eadb43ea3df2017be189e09e3bb`; `a1169a05afb917862f4a0f5865e278f4168ed171`; `ac247dafbce3aacde37695575d457cf958b22560` |
| V08 | Registry #46; Control Plane #86; Runtime #149; Stack Qualification #237 | `1a4de326...`; `d66ae07f...`; `b5605f52...`; `bb9b0890...` |
| V08 historical | Stack Qualification #235 (OPEN, unmerged) | head `7b72de9ac7e4898c0f9bdad3e9b337775cc9c543` |

## 7. Known limitations and qualification status per component
See [limitations-and-exclusions.md](limitations-and-exclusions.md). No component is independently qualified. Qualification status per component is in `candidate-manifest.json` and [gate-matrix.md](gate-matrix.md).
