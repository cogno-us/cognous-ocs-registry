# EXT-S2-G: CI check inventory for the four repositories

Work package: EXT-S2-G (Required-checks confirmation), card in `docs/p1-extraction-plan/11-ext-pr-execution-cards.md`.
Nature: documentation only. No workflow, setting, ruleset or branch-protection change was made. No qualification claim is made or implied.
Inspection date: 2026-10-25.

## 1. Purpose and scope

The execution cards name "required GitHub checks" (REG, RT-core, RT-ref, RT-w21, CP, CP-b, QUAL) and state that required-ness is unconfirmed until EXT-S2-G, and that unknown counts as not required. This note records, per repository, what workflows and checks exist (PRESENT), whether any are REQUIRED according to what could be read, where the evidence stops, and which gaps matter for V1. It also lists exact-head local validation commands for the preserved test sets FS-RT and FS-CP.

Statements are labelled:
- **Observed**: read directly from a file at a named commit, from a GitHub API response, or from a command run for this note.
- **Inferred**: derived from observed facts by a stated rule; not seen on GitHub.

## 2. Method and access limits

- Commit SHAs: `git fetch` in each clone, then compared with `gh api repos/<org>/<repo>/commits/main --jq .sha`. The API call succeeded only for the registry. For the other three repositories `gh api` returned HTTP 403 ("GitHub access to this repository is not enabled for this session"). Their default-branch SHA is therefore the `origin/main` value read by `git fetch` from the git proxy, not an API read. `add_repo` reported read-only git access as available and API access as needing a push-level attachment; that was not requested because it exceeds this package's read-only scope.
- Workflow facts for the Control Plane, Runtime and qualification repositories come from `git show origin/main:<path>`. Delegated Runtime jobs are read from the qualification repository at the pinned suite commit `1c1755ff4ea719cfa12f72bcd8c81dd51cff7fb2` (fetched by SHA from the qualification repository).
- Branch protection, rulesets, branch rules and observed check-runs on merged PRs: queried only for the registry. For the other three: **not determinable with available access**. No attempt was made to route around the 403.
- Check-run naming rule (Inferred from GitHub Actions behaviour, partly confirmed by the registry observation): the REST check-run name for an Actions job is the job `name:` if set, otherwise the job id, with a matrix suffix ` (<value>)`. The Actions UI shows `<workflow name> / <job>`. For a job that calls a reusable workflow the name is `<caller job id> / <called job name or id>` (the called workflow's own `name:` is not part of it). Only `Analyze (python)` and `CodeQL` were confirmed against real check-runs, and only in the registry. Every other name below is Inferred and must be confirmed from a real check-run on a PR head before a ruleset is written.
- Local commands were run in a scratch virtualenv (Python 3.12.3, pytest 9.1.1, pydantic 2.14.1) with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`; no clone was modified. No credentialed tests were run.

## 3. Per-repository inventory

### 3.1 cogno-us/cognous-ocs-registry

| Item | Finding |
|---|---|
| Default-branch SHA | `d2c472e4a09543228bad62235e07a0dedfd7f48b` (API and local `origin/main` agree; Observed). The card's pin `d61ef729883c9c127cbd05b8f8a1a5944dc0e717` is PR #21's merge commit; #22 merged on top. |
| In-tree workflows | None. `.github/` is absent at `d2c472e` and at `d61ef729` (Observed). |
| Actions workflows registered on GitHub | `Copilot` (dynamic/agents/copilot-pull-request-reviewer), `Dependabot Updates`, `Dependency Graph`, `CodeQL` (dynamic/github-code-scanning/codeql), all `active` (Observed via `actions/workflows`). |
| Check-runs seen | On the PR #22 head `b34fa6613f22...` and the PR #21 head `ac54f2351326...`: `CodeQL` (app `github-advanced-security`, success) and `Analyze (python)` (app `github-actions`, success). On merge commit `d2c472e`: `Analyze (python)` only (Observed). |
| Triggers / paths | CodeQL dynamic workflow: trigger configuration not readable here (not in tree). Not path-filtered by anything in the tree. |
| Python versions | None in CI. Lock header says compiled with `--python-version 3.11`. |
| Branch protection | `GET branches/main/protection` returned 404 "Branch not protected" (Observed). |
| Rulesets | `GET rulesets` returned `[]`; `GET rules/branches/main` returned `[]` (Observed). |
| Required or present | **No required checks exist** (Observed: no protection, no rulesets, no rules apply to `main`). `Analyze (python)` and `CodeQL` are PRESENT only. |
| Test workflow | None. The 683 registry tests run in no check (Observed; confirmed by the empty tree). `Registry tests / pytest` is proposed by EXT-S1-0 and does not exist. |

### 3.2 cogno-us/cognous-control-plane

Default-branch SHA: `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` (clone and `origin/main` agree; API read 403, so not API-confirmed).

| Workflow file | `name:` | Job id (`name:` unset) | Inferred check-run name (UI form) | Triggers | Python |
|---|---|---|---|---|---|
| `.github/workflows/tests.yml` | Tests | `test`, matrix `python-version` 3.11, 3.12 | `test (3.11)`, `test (3.12)` (UI: `Tests / test (3.11)`, `Tests / test (3.12)`) | `push` (all branches), `pull_request` (no path filter) | 3.11, 3.12 |
| same | Tests | `manifest-validator-parity` | `manifest-validator-parity` (UI: `Tests / manifest-validator-parity`) | same | 3.12 |
| `.github/workflows/o6-p1b-durable-refusal.yml` | O6 P1B durable refusal | `scoped-qualification` | `scoped-qualification` (UI: `O6 P1B durable refusal / scoped-qualification`) | `pull_request` only when paths match `src/agent_control_plane/bounded.py`, `tests/test_check_commit_inventory.py`, `docs/durable-refusal-profile.md`, the workflow file; `workflow_dispatch` | 3.11 |
| `.github/workflows/o6-p0-check-commit-inventory.yml` | O6 P0 check-commit inventory | `scoped-qualification` | UI: `O6 P0 check-commit inventory / scoped-qualification` | `pull_request` only for `tests/test_check_commit_inventory.py`, `docs/check-commit-inventory.md`, the workflow file; `workflow_dispatch` | 3.11 |
| `.github/workflows/w5-microsoft-agt.yml` | W5 Microsoft AGT compatibility | `pinned-sdk` | UI: `W5 Microsoft AGT compatibility / pinned-sdk` | `pull_request` only for `src/agent_control_plane/microsoft_agt.py`, `tests/test_microsoft_agt.py`, `docs/microsoft-agt-compatibility.md`, the workflow file; `workflow_dispatch` | 3.11 |

What the jobs run (Observed): `test` runs `pip install -e ".[dev]"` (not hash-locked), `pytest`, then `python tools/adversarial_mutations.py`. `manifest-validator-parity` installs the action-manifest at `MANIFEST_UPSTREAM_COMMIT` and runs `pytest -q -rs tests/test_scan6_manifest_validator_parity.py`; its comment says codes the pinned validator does not implement are reported as skipped. `scoped-qualification` in the P1B workflow runs `tests/test_check_commit_inventory.py`, the same file as the P0 workflow.

Required or present: **not determinable with available access** (branch protection, rulesets and rules not readable; no merged-PR check-runs read). All four workflow files (five jobs or matrix legs, counting the two `Tests` jobs and their matrix as in the table) are PRESENT. Path-filtered ones (O6 P1B, O6 P0, W5) will not run on a docs-only or test-only PR that touches none of their paths; `Tests` runs on every PR.

Note: the card's CP-b notes O6 P1B runs only if `bounded.py` or its listed paths are touched; confirmed. The appendix does not list O6 P0 or W5; they exist.

### 3.3 cogno-us/cognous-execution-runtime

Default-branch SHA: `c5e97e87dd239c821b1b4a406a55dcd03c5bc61f` (clone, detached HEAD, equals `origin/main`; API read 403, so not API-confirmed).

Native workflows (run on the runner, no delegation):

| Workflow file | `name:` | Job id / `name:` | Inferred check-run name (UI form) | Triggers | Python |
|---|---|---|---|---|---|
| `workflow-sanity.yml` | Workflow Sanity | `no-tabs` | `no-tabs` (UI: `Workflow Sanity / no-tabs`) | `pull_request` (all), `push` (all) | system (script only) |
| `python-safety.yml` | Python safety boundary | `native`, `name: Component-local checks` | `Component-local checks` (UI: `Python safety boundary / Component-local checks`) | `pull_request`, `push`; paths `engine/**`, `examples/openshell/**`, `docs/openshell-adapter.md`, `tests/**`, `docs/execution-boundary.md`, `docs/control-plane-interface-gap.md`, the workflow file | 3.12 |
| `o6-p1a-operation-admission.yml` | O6 P1A operation admission | `operation-admission` | UI: `O6 P1A operation admission / operation-admission` | `pull_request`, `push`; paths `engine/operation_admission*`, `tests/test_o6_p1a*`, `docs/o6-p1a*`, workflow | 3.12 |
| `o6-p1d-revocation-closeout.yml` | O6 P1D revocation closeout | `revocation-closeout` | UI: `O6 P1D revocation closeout / revocation-closeout` | paths `engine/revocation_closeout.py`, its test and doc, workflow | 3.12 |
| `recovery-resolution-synthetic.yml` | Synthetic recovery resolution | `synthetic-recovery` | UI: `Synthetic recovery resolution / synthetic-recovery` | paths `engine/recovery_resolution.py`, `engine/revocation_closeout.py`, three tests, doc, workflow | 3.12 |
| `reference-docs.yml` | Reference documentation | `documentation` | UI: `Reference documentation / documentation` | paths `README.md`, `collateral/business-collateral.md`, `collateral/one-page-overview.md`, workflow; push only on `main` | system `python3` |

Delegated workflows. Each caller job is `cross-component` and calls a reusable workflow in `cognous-stack-qualification` pinned to `1c1755ff4ea719cfa12f72bcd8c81dd51cff7fb2`, passing `source_revision` = the PR head SHA (push: `github.sha`). The caller's `qualification_revision` is the same pin, not the qualification repository's current `be1994a9`.

| Caller workflow file (`name:`) | Inferred check-run name | Called job id | Triggers (paths) | Python | Control Plane commit the job checks out |
|---|---|---|---|---|---|
| `python-safety.yml` (Python safety boundary) | `cross-component / safety-tests` | `safety-tests` | same paths as native job | 3.12 | `2ea9528eeb87e14ff10f05de06473122b9df540f` |
| `durable-refusal.yml` (Durable refusal capture) | `cross-component / refusal (3.11)`, `cross-component / refusal (3.12)` | `refusal`, matrix `python` 3.11, 3.12 | `pull_request` and `push` to `main`; paths `engine/**`, `tests/test_refusal_capture.py`, workflow | 3.11, 3.12 | `c7f122ba3a6e39f9268a7163c99be3ee514cd97e` |
| `worker21-authority-effect.yml` (Worker21 local authority-effect profile) | `cross-component / focused` | `focused` | `pull_request`, `workflow_dispatch`; paths `engine/local_authority_effect.py`, `engine/atomic_local_control_plane_executor.py`, `engine/local_authority_effect_recovery.py`, `engine/safe_executor.py`, `engine/refund_intent.py`, five tests, two docs, workflow | 3.12 | `e66e5f163c5d5c112ff345a2f332b4c3893ee183` |
| `openappa-conjunction.yml` (OpenAPPA synthetic authority conjunction) | `cross-component / conjunction` | `conjunction` | `pull_request`, `workflow_dispatch`; paths (for `pull_request`) `tools/openappa/**`, `engine/control_plane_adapter.py`, `engine/safe_executor.py`, workflow | 3.12 | `2ea9528eeb87e14ff10f05de06473122b9df540f` |
| `openappa-embedded-runtime.yml` (OpenAPPA pinned embedded runtime) | `cross-component / embedded-runtime` | `embedded-runtime` | paths `tools/openappa/cognous_embedded_contract.rs`, workflow | not set in called job | none |
| `openappa-local-resume.yml` (OpenAPPA local host resume) | `cross-component / local-resume` | `local-resume` | paths four `tools/openappa/` files, workflow | 3.12 | none |
| `openappa-trajectory.yml` (OpenAPPA persistent trajectory qualification) | `cross-component / trajectory` | `trajectory` | paths `tools/openappa/cognous_trajectory_contract.rs`, workflow | not set | none |
| `openappa-wire-fixtures.yml` (OpenAPPA pinned wire fixtures) | `cross-component / codec` | `codec` | paths `tools/openappa/**`, `tests/fixtures/openappa/**`, one test, workflow | 3.12 | none |
| `openshell-image-qualification.yml` (OpenShell worker image qualification) | `cross-component / worker-image` | `worker-image` | paths `engine/openshell_worker.py`, `engine/openshell_environment.py`, `engine/safe_executor.py`, `examples/openshell/**`, tests/tools/docs, workflow | 3.12 | none |
| `live-openshell-readiness.yml` (Live OpenShell readiness) | `cross-component / readiness` | `readiness` | paths `tools/live_openshell_readiness.py`, test, three docs/results files, workflow | 3.12 | none |

Trigger note: every delegated caller except `python-safety.yml` and `durable-refusal.yml` also declares `workflow_dispatch` (Observed), so those jobs can be run manually regardless of path filters; `durable-refusal.yml` also triggers on `push` to `main`, and `python-safety.yml` on `push`.

Notes: the qualification repository also holds `cognous-execution-runtime--openappa-reply-admission.yml`; no Runtime caller exists for it (Observed). Delegated jobs overlay suite files from the qualification repository onto the Runtime checkout (`tools/install_suite.py --suite cognous-execution-runtime`), so the tests they run are not only the files in the Runtime tree.

Required or present: **not determinable with available access**. All workflows above are PRESENT. For an S2 PR that touches only a new Runtime test file and expected-values JSON, `Workflow Sanity / no-tabs` runs; `Python safety boundary` (native and delegated) runs because `tests/**` matches; the Worker21, OpenAPPA, OpenShell and Durable refusal jobs do not (Inferred from the path lists; `engine/**` is needed for Durable refusal). A new `engine/` file would additionally trigger `Durable refusal capture`.

### 3.4 cogno-us/cognous-stack-qualification

Default-branch SHA: `be1994a961e4e40612d999972ede6547a3729887` (local `origin/main`; commit date 2026-10-25T00:38:12-07:00; the local checkout `998d39c5` is behind; API read 403). 70 workflow files at `origin/main`; 11 of them have a `pull_request` trigger.

Checks named by the card:

| Workflow file (`name:`) | Job id | Inferred check-run name (UI form) | Triggers | Python |
|---|---|---|---|---|
| `catalog-validation.yml` (Catalog validation) | `validate` | `validate` (UI: `Catalog validation / validate`) | `push`, `pull_request` (no path filter), `workflow_dispatch` | not pinned in workflow; runner `python3` (Inferred: runner default) |
| `qualification-dashboard.yml` (Qualification dashboard build) | `validate-and-build` | `validate-and-build` (UI: `Qualification dashboard build / validate-and-build`) | `pull_request` (no path filter), `push` to `main`, `workflow_dispatch` | 3.12 |
| `migration-integrity.yml` (Cross-component migration integrity) | `integrity` | `integrity` (UI: `Cross-component migration integrity / integrity`) | `pull_request` and `push`, only for `suites/**`, `migrations/**`, `tools/install_suite.py`, `tools/run_suite.py`, `tools/validate_migrations.py`, `tests/test_suite_install.py`, `.github/workflows/*--*.yml`, the workflow | 3.12 |

Other workflows with a `pull_request` trigger, all path-filtered (names are workflow `name:`; jobs listed by id):
- Claude Opus 5.5 agent pilot (`offline-controls`; `actual-agent` runs only on `main` push or authorised dispatch).
- OpenAI GPT-6.1 Sol agent pilot (`offline-controls`; `actual-agent` on `main` push only).
- Nonselected reference compatibility (`reference`, calls `cognous-open-control-stack--remediation-full-reference.yml`).
- Runtime authority candidate (`candidate`, matrix 3.11, 3.12).
- Security evidence tooling (`receipt-tools`).
- F5b-repaired runtime requalification (`actual-components`).
- Repaired-source runtime qualification (`actual-components`).
- Serial local trajectory qualification (`local-native`).

No `p1-config-extraction` workflow exists at `be1994a9`; the card says it arrives with `S5-2`. The reusable `cognous-*` workflows are `workflow_call` or `workflow_dispatch` only.

Required or present: **not determinable with available access**. All are PRESENT. `Catalog validation` and `Qualification dashboard build` run on every PR including docs-only PRs; `Cross-component migration integrity` does not unless a listed path changes. A `suites/**` change triggers it (Observed from the path filter).

## 4. Cross-repository gap list

1. **Registry has no test workflow.** The 683 tests run in no check until EXT-S1-0. Locally, `pytest` collects 683 and all pass (Observed, section 5). No required check exists in the registry (Observed).
2. **Registry lock sources are not in the tree.** `requirements-s01.lock.txt` says it was compiled from `.github/locks/pytest-b61d81.in` and installs from `.github/locks/pytest-b61d81.txt`; the registry has no `.github/`. The lock body is byte-identical to the Runtime's `.github/locks/pytest-b61d81.txt` (same sha256 of the whole file `257be288...`), and that `.in` contains the single line `pytest==8.3.5` (Observed). This is relevant to S1-0 step 3 (restore or record the gap).
3. **Runtime atomic tests skip without the Control Plane on the path.** Several Runtime test modules guard on `agent_control_plane.local_authority_effect` (`skipif` or `importorskip`, for example `test_atomic_post_commit_fault_injection.py`, `test_crashed_holder.py`, `test_atomic_approval_status_terminality.py`). Running the twelve FS-RT files with `PYTHONPATH=.:src` (no Control Plane) gave `114 passed, 35 skipped`; with the Control Plane `src` on the path, `149 passed`, no skips (Observed). The native job `Component-local checks` installs only the pydantic/pytest lock and sets `PYTHONPATH=.:src` (Observed in the workflow; the Runtime tree has no `src/` directory), so it likely skips the same tests (Inferred; the CI run was not read).
4. **Delegated Runtime jobs run an older Control Plane.** The delegated jobs check out Control Plane `2ea9528e`, `c7f122ba` or `e66e5f16`, never `7a4bcd40`, and run suite revision `1c1755ff`, not the qualification repository's current head. A green delegated job is therefore not evidence at an exact Control Plane pin (Observed pins; the consequence is Inferred).
5. **Delegated jobs are path-filtered** and do not run on a PR touching only files outside their lists (for example a docs-only Runtime PR that falls outside every workflow path filter runs only `no-tabs`; a change to `README.md` also triggers `Reference documentation`, and a change to `docs/openshell-adapter.md`, `docs/execution-boundary.md` or `docs/control-plane-interface-gap.md` triggers both Python safety jobs including the delegated one).
6. **Control Plane FS-CP has a skipped module in this environment.** `tests/test_claim_journal_stage.py` calls `pytest.importorskip("cognous_verify.engine")` at module level; without that package the whole module is skipped (`292 passed, 1 skipped` on the ten FS-CP files, Observed locally). `tests.yml` installs only `.[dev]` and no `cognous_verify` (Observed), so CI likely skips it as well (Inferred; the CI run was not read). `pyproject.toml` lists no `cognous_verify` dependency (Observed).
7. **Control Plane CI install is not hash-locked** (`pip install -e ".[dev]"`, `pydantic>=2.12`), unlike the Runtime native job (hash-locked `pydantic-pytest-f8aeba.txt`) and the qualification repository's native jobs (hash-locked `jsonschema-pyyaml-c943d3.txt`). The delegated Runtime jobs are also not hash-locked: `safety-tests` and `refusal` pin versions without hashes (`pytest==8.3.5 pydantic==2.11.9`), and `focused` (Worker21) installs unpinned `pytest pydantic` (Observed at suite pin `1c1755ff`). Version drift between runs is possible (Inferred).
8. **Conditional or skipped behaviour in checks:** manifest-validator parity reports unimplemented codes as skipped (stated in the workflow comment); qualification pilots have `actual-agent` jobs gated to `main`.
9. **Required-ness is unknown for three of four repositories** (API access not enabled). Under the card's rule these count as not required. An operator or the Architect with settings access needs to supply a dated export of branch protection, rulesets and `rules/branches/main` for the Control Plane, Runtime and qualification repositories.
10. **Appendix omissions.** The card appendix does not list: Runtime `O6 P1A`, `O6 P1D`, `Synthetic recovery resolution`, `Reference documentation`, `Live OpenShell readiness`, OpenAPPA embedded-runtime, local-resume, trajectory and wire-fixtures jobs; Control Plane `O6 P0` and `W5`; most qualification workflows. None is shown to be required.
11. **Code scanning outside the registry is unknown.** `Analyze (python)` and `CodeQL` were seen only on the registry; whether the other repositories have CodeQL default setup could not be queried.

## 5. Recommended exact-head validation commands

Run from a clean checkout of the exact commit under test. Use a throwaway virtualenv; avoid writing bytecode into the checkout.

Common prefix used below: `export PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`.

**Registry** (Observed: `683 tests collected`, `683 passed` in about 3 seconds, Python 3.12.3, pytest 9.1.1; the lock pins pytest 8.3.5, so CI-faithful runs should install the lock):

    python -m pip install --require-hashes -r requirements-s01.lock.txt
    python -m pytest -q -rs

`pytest.ini` sets `testpaths = tests` and `pythonpath = baseline/execution-runtime .`. `-rs` lists any skip. The integrity test is `tests/test_s06_integrity.py`.

**Runtime FS-RT** (Observed: all twelve files exist; `149 tests collected`; `149 passed`, no skips with the Control Plane on the path; `114 passed, 35 skipped` without it). Replace `<CP>` with a Control Plane checkout at the exact pin:

    cd <runtime checkout>
    export PYTHONDONTWRITEBYTECODE=1
    PYTHONPATH=.:<CP>/src python -m pytest -q -rs -p no:cacheprovider \
      tests/test_valid_flow_byte_identity.py tests/test_atomic_route_valid_flow_identity.py \
      tests/test_route_a_local_policy_reason.py tests/test_security_admission.py \
      tests/test_r2_atomic_operation_identity.py tests/test_atomic_post_commit_fault_injection.py \
      tests/test_atomic_post_commit_unresolved.py tests/test_crashed_holder.py \
      tests/test_atomic_grant_status_and_envelope_binding.py tests/test_atomic_approval_status_terminality.py \
      tests/test_atomic_approval_terminality_flow.py tests/test_public_runtime_surface.py

Treat any `SKIPPED` line as a failure of the evidence requirement (the card says a skipped run is not evidence). Add `tests/test_amount_binding_and_known_limits.py tests/test_adapter_forwarding.py` for the S2-1 list (Observed: 12 passed with the Control Plane on the path). `test_public_runtime_imports_without_test_modules` is a function in `tests/test_public_runtime_surface.py`, not a separate file. The whole Runtime suite collects 556 tests with the Control Plane on the path (Observed). Requires `pydantic` and `pytest`; the Runtime CI lock is `.github/locks/pydantic-pytest-f8aeba.txt`.

**Control Plane FS-CP** (Observed: all ten files exist; `292 tests collected`; `292 passed, 1 skipped` in about 31 seconds; the skip is the whole `test_claim_journal_stage.py` module, see gap 6; whole suite collects 1194 tests):

    cd <control-plane checkout>
    export PYTHONDONTWRITEBYTECODE=1
    PYTHONPATH=src python -m pytest -q -rs -p no:cacheprovider \
      tests/test_local_authority_effect_profile.py tests/test_claim_journal_stage.py \
      tests/test_decision_input_commitment_profile.py tests/test_bounded_authorization.py \
      tests/test_freshness.py tests/test_reversibility.py tests/test_runtime_authority.py \
      tests/test_holder_inventory.py tests/test_operation_identity.py tests/test_merge_record.py

Requires `pydantic>=2.12`, `cryptography>=43`, `pytest`, `pytest-asyncio`. To make the skipped module run, `cognous_verify` must be importable; its source is not identified in this inventory (open question 3). CI also runs `python tools/adversarial_mutations.py` after `pytest`; that command was not run for this note.

**Qualification** (run from an export of `be1994a9`; hash-locked install `.github/locks/jsonschema-pyyaml-c943d3.txt`): `python tools/validate_catalog.py` (Observed: "Valid: 40 Cognous + 656 Wiki specifications"), `python tools/validate_migrations.py` (Observed: "194 original files, 50 workflows, 19 public repositories inventoried"), and `python -m unittest discover -s tests -v`. Observed with the unpinned scratch virtualenv: `Ran 780 tests` in about 277 seconds, `OK (skipped=2)` (a long suite; not required for routine checks).

## 6. Open questions

1. Operator or Architect: provide dated REST exports of `branches/main/protection`, `rulesets` and `rules/branches/main` for the Control Plane, Runtime and qualification repositories; until then every check there counts as not required.
2. Confirm the exact check-run names (section 2 naming rule) from a real PR head in each of those repositories before writing any ruleset; the Inferred names for reusable-workflow jobs are the least certain.
3. Which package provides `cognous_verify`, and should the Control Plane exact-head validation install it so `test_claim_journal_stage.py` executes?
4. Should the Runtime exact-head validation use a Control Plane pin newer than the delegated jobs' pins (`2ea9528e`, `c7f122ba`, `e66e5f16`), given gap 4?
5. For the registry, does the Architect require a repository ruleset to make `Registry tests / pytest` required once S1-0 merges (none exists today)?
6. Do the Control Plane, Runtime and qualification repositories have CodeQL default setup (gap 11)?
