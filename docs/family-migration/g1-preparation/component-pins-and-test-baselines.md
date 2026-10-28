# Exact component pins and test baselines (deliverable 4)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## 1. Pins

| Component | Exact SHA | Role |
|---|---|---|
| Registry (code) | 317eb76acb2847c534c3ce7c2180b89b4aef987d | G0 inventory source pin; Registry code identical at the G0 merge commit |
| Registry main (G0 merge) | 7208eb6f53f12677f138fe0c64ec48a2e58292b5 | frozen G0 baseline; G1 preparation PR is cut from it |
| Control Plane | d66ae07fa240510efdcc11ed4b3e1189dcefc822 | current main, unchanged since G0 (re-checked 2026-10-28) |
| Runtime | 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491 | current main, unchanged since G0 (re-checked) |
| Stack Qualification | bb9b08904192b5f50a49e00ed8de0cab80fd7c19 | current main, unchanged since G0 (re-checked) |
| Constitution pin | 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b | unchanged; the Constitution repository main `a4dd1111` is not adopted |
| Registry pin used by Runtime and Control Plane tests | 943ab1831e39fadac1eb2a414ae322ccfa09bc6a | differs from the G0 Registry pin; the diff was not inspected (PR-1) |

## 2. Test baselines available today

Collection counts (parameter-expanded) for the test files the mappers consulted. No test was executed by this package.

| Repo | SHA | Files | Collected | Not collected (NOT RUN) | Method |
|---|---|---|---|---|---|
| registry | 317eb76acb2847c534c3ce7c2180b89b4aef987d | 37 | 6207 | 0 | collect-only, `/root/.local/bin/pytest` 9.1.1 |
| runtime | 0dde0ef7a55f3d6a43a7da2c6ab1212b8863b491 | 20 | 250 | 6 | collect-only with workaround interpreter; modules needing PyNaCl or component dirs collected 0 and are NOT RUN |
| control_plane | d66ae07fa240510efdcc11ed4b3e1189dcefc822 | 4 | 241 | 0 | collect-only with workaround interpreter; modules needing PyNaCl or component dirs collected 0 and are NOT RUN |
| stack_qualification | bb9b08904192b5f50a49e00ed8de0cab80fd7c19 | 7 | 283 | 2 | collect-only with workaround interpreter; modules needing PyNaCl or component dirs collected 0 and are NOT RUN |

Registry whole-suite baseline: 6207 tests collected at `317eb76a` (6217 with the 10 G0 integrity tests on the G0 branch). A local full run on the G0 branch gave 6214 passed, 2 skipped, 1 failed (`test_installed_cryptography_matches_the_test_only_lock`: local `cryptography` 50.0.2 vs lock 50.0.1; the same failure occurs without any G0 file); GitHub Actions on `7208eb6f` is green (runs 40609560305, 40609560460). The decision-level f1ab suite `tests/test_v01a_v2_record_path.py` needs PyNaCl and skips as a module where PyNaCl is absent; the Node cross-check in `test_ext_s1_5_vectors.py` skips without Node (CI makes it required).

## 3. What a G1 start must establish (not done here)

1. Run the existing Runtime, Control Plane and Stack Qualification suites at their pins in a prepared environment (PyNaCl, pydantic, Node, component directory variables) and record pass/fail counts. Until then the Runtime/Control Plane/SQ baseline is **NOT RUN**.
2. Decide the Registry pin for cross-repository tests (`943ab18` versus `317eb76a`) and run the pin assertions at the chosen one (PR-1).
3. Record the result as a baseline file so oracle additions are measured against a known pass set.
