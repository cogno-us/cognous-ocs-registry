# Reproducible environment profile (PR-2, Phase C)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Constraints observed: no unapproved global installs; no paid service or cloud; local venvs built only from hash-locked files already in the pinned repositories; no test body executed (collection only).

## 1. Two named profiles

| Profile | Use | Source of the lock | Versions installed |
|---|---|---|---|
| R | Registry's own tests; Runtime CI environment | Registry `requirements-ed25519.lock.txt`, `requirements-ed25519-test-oracle.lock.txt`, `requirements-s01.lock.txt`; Runtime `.github/locks/pydantic-pytest-f8aeba.txt` | Python 3.13.17, pytest 8.3.5, pydantic 2.11.9 / pydantic-core 2.33.2, PyNaCl 1.6.2, cffi 2.1.1, cryptography 50.0.1 |
| X | Cross-component (Control Plane V02 dependent) suites: Runtime pin tests, SQ V07 and V08-FA1 | Stack Qualification `.github/locks/v07-pydantic212-pynacl-cryptography-pytest.txt` (and `…pydantic211…` for the V07_PY211 cases) | Python 3.13.17, pytest 9.1.1, pydantic 2.14.1 / pydantic-core 2.50.1, PyNaCl 1.6.2, cffi 2.1.1, cryptography 50.0.2 |

Profile R is not valid for Control Plane dependent execution (item E-05). Profile X cannot satisfy the Registry test that compares the installed cryptography with the Registry lock (item E-06). One profile per suite must be named in any qualification baseline.

## 2. Prerequisite status

| Id | Prerequisite | Status | Evidence |
|---|---|---|---|
| E-01 | Python interpreter | PASS | System Python 3.13.17 (workspace). CI: Registry 3.13; Runtime/Control Plane/Stack Qualification 3.12 (3.11 for CP tests matrix). Execution on 3.12 not performed. |
| E-02 | Isolation of tooling | PASS | Two local venvs under the session scratchpad created from hash-locked files with pip --require-hashes; no global install; no network service used beyond the package index. |
| E-03 | Profile R (Registry tests) hash locks | PASS | Registry requirements-ed25519.lock.txt (PyNaCl 1.6.2, cffi 2.1.1, pycparser 3.12), requirements-ed25519-test-oracle.lock.txt (cryptography 50.0.1), requirements-s01.lock.txt (pytest 8.3.5); Runtime .github/locks/pydantic-pytest-f8aeba.txt (pytest 8.3.5, pydantic 2.11.9). Installed and listed. |
| E-04 | Profile X (cross-component) hash lock | PASS | Stack Qualification .github/locks/v07-pydantic212-pynacl-cryptography-pytest.txt (pydantic 2.14.1, pydantic-core 2.50.1, cryptography 50.0.2, PyNaCl 1.6.2, pytest 9.1.1). Installed and listed. A pydantic 2.11.9 lock for V07_PY211 exists (v07-pydantic211-pynacl-cryptography-pytest.txt). |
| E-05 | Control Plane pydantic requirement | BLOCKED for Profile R | Control Plane pyproject at d66ae07f requires pydantic>=2.12 and uses Field(exclude_if=...) (src/agent_control_plane/operation_identity.py:65). Under pydantic 2.11.9 the keyword is accepted with a deprecation warning and its behaviour is not applied; Profile R is therefore not a valid execution profile for Control Plane dependent cases. Use Profile X. |
| E-06 | Cross-profile cryptography skew | BLOCKED (decision) | Profile R pins cryptography 50.0.1; Profile X pins 50.0.2. The Registry test test_installed_cryptography_matches_the_test_only_lock fails under Profile X (observed earlier in the program). One qualification baseline must name ONE profile per suite; not decided here. |
| E-07 | PyNaCl | PASS | PyNaCl 1.6.2 in both profiles; without it the six Runtime files collect 0 tests (module-level skip 'NOT RUN: PyNaCl'). |
| E-08 | Node toolchain | PASS (available), NOT RUN | node v22.23.4, npm 10.9.9 present. Registry test_ext_s1_5_vectors.py Node cross-check is conditional (skips without Node; Registry CI makes it required). Not executed. |
| E-09 | Registry importability | PASS | From the 317eb76a worktree, registry_records, registry_contract and registry_successor import under -I with PYTHONPATH set; 6207 Registry tests collect (collection only), matching the 6207 recorded by the G0 worker. |
| E-10 | Component checkouts at exact pins | PASS | Git worktrees (detached) created at Registry 317eb76a, Control Plane d66ae07f, Runtime 0dde0ef7, Stack Qualification bb9b0890; V07 set (a1169a05, 1bee3696, ac247daf, e66e5f16) and V08 set (1a4de326, d66ae07f, 3873a61b). HEADs verified with git rev-parse. |
| E-11 | Required environment variables | PASS (defined), NOT RUN | Runtime files: OCS_REGISTRY_PIN_DIR. SQ V07: V07_COMPONENTS_DIR, V07_EVIDENCE_DIR, V07_PY211. SQ V08-FA1: V08_COMPONENTS_DIR, V08_FA1_RESULTS_DIR, V08_FA1_CHILD (OS file), V08_BUDGET_ENFORCE, V08_WORKER. |
| E-12 | Hard-coded machine path | BLOCKED | tests/test_authorization_pin_integration.py: CP_WORKTREE = /home/claude/wt/cp-export. The CP export case is INCONCLUSIVE on any other machine; it is not reproducible from the pins alone. |
| E-13 | Registry pin assertion in a Runtime test | BLOCKED (decision) | tests/test_registry_f1a_narrowing.py: PIN = 943ab183… and test_m1_20 asserts the checkout HEAD equals it. Registry code trees are identical at 317eb76a, but that single case would FAIL at 317eb76a. Resolution (PD-5): run Registry fixtures at 943ab18 or state the case as a commit-identity assertion, not a behaviour assertion. |
| E-14 | Runtime CI coverage of the six Runtime files | FINDING | Runtime CI runs `python -m pytest -q tests` with the pydantic-pytest-f8aeba lock, no PyNaCl and no OCS_REGISTRY_PIN_DIR; the six Registry-gated modules skip at module level. Their only recorded executions are builder-local and Stack Qualification workflows that stage components. |
| E-15 | OS-identity prerequisites | PASS (tools), NOT RUN | useradd and setpriv present, uid 0. test_fa1_os.py and tests/host_pin/test_installer_os_isolation.py (outside the eight files) were not collected or run. |
| E-16 | Existing runners | PASS | pytest invoked as `python -m pytest -p no:cacheprovider --collect-only -q`; Registry pytest.ini sets pythonpath `baseline/execution-runtime .`; SQ conftest adds component paths itself. |
| E-17 | Fixture dependencies | PASS (documented) | Files 1, 5 and 6 import test_registry_selection_effect_guard; file 6 imports file 5; SQ cases import Runtime tests and Control Plane tests (`tests` package name collision handled by subprocesses and sys.path order); SQ V08 vendors _wf.py with a sha256 check. |
| E-18 | Any test execution (as opposed to collection) | NOT RUN | No test body of the eight files was executed in this session. Collection only, per the directive (no full qualification battery). |

## 3. Collection results (the only thing run)

`python -m pytest -p no:cacheprovider --collect-only -q` with the component checkouts at the exact pins:

| Target | Profile R | Profile X |
|---|---|---|
| Registry (all tests, 317eb76a) | 6207 | 6207 |
| Runtime tests/test_f01_policy_containment.py | 18 | 18 |
| Runtime tests/test_registry_selection_effect_guard.py | 47 | 47 |
| Runtime tests/test_registry_selection_authority.py | 57 | 57 |
| Runtime tests/test_registry_f1a_narrowing.py | 86 | 86 |
| Runtime tests/test_authorization_pin_guard.py | 67 | 67 |
| Runtime tests/test_authorization_pin_integration.py | 18 | 18 |
| SQ suites/security-v07/test_adversarial.py (V07 component set) | 46 | 46 |
| SQ suites/tier1-v08-fa1/test_fa1_software.py (V08 component set) | 24 after cryptography was added from the Registry test-oracle lock; error without it | 24 |

The workers' NOT RUN verdict for these eight files was an environment artefact: PyNaCl and the component variables were missing. Static AST counts (14, 43, 51, 54, 49, 13, 46, 24) are function counts; collected counts expand parametrization (e.g. 14 functions to 18 tests).

## 4. How a later authorized run would be reproduced

1. Create worktrees at the pins (Registry, Control Plane, Runtime, Stack Qualification; plus the V07 and V08 component sets).
2. Create the venv for the chosen profile with `pip install --require-hashes -r <lock>`.
3. Export the variables in E-11; set `OCS_REGISTRY_PIN_DIR` to the Registry worktree; do not rely on `/home/claude/wt/cp-export` (E-12).
4. Run only the oracles ratified for execution. Nothing here authorizes execution.
