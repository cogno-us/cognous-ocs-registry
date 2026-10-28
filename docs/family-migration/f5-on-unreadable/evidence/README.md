# Evidence index (F5 on_unreadable increment, 2026-10-28)
Raw results are kept as produced. Historical failures are kept.
- `registry-full-base-lock.log`, `registry-full-v5-lock.log`: full Registry suite under the hash-locked requirements, unchanged main `47adfc8` vs PR #64 head `6c3e5e4` (7145 vs 7477 passed, 2 skipped each, 0 failed).
- `registry-full-base.log`, `registry-full-v5.log`, `registry-full-v5-final.log`: earlier builder-venv runs (cryptography mismatch; `v5.log` = before the allowlist fixes). Historical; superseded by the locked-environment pair.
- `cp-full-main-3.11.log`, `cp-full-main-3.12.log`, `cp-full-branch-3.11.log`, `cp-full-branch-3.12.log`, `cp-freeze-3.1x.txt`: full Control Plane suite in CI-equivalent venvs, main `5f11e0f` vs PR #90 head, with the dependency freezes.
- `mutation-harness-mut_u.py`: the 43-mutant harness (`MUT_ONLY`/`MUT_OUT` select survivors for re-runs).
- `mutation-cp-round1.log` / `mutation-results-cp-round1.json`: first full run (37 killed, 6 survived). `mutation-cp-round2.log` / `-round2.json`: survivors re-run after new tests (5 killed, M31 survived). `mutation-results-cp-round3.json`: M31 re-run (one invalid intermediate test was replaced; see the increment record). `mutation-cp-final.log` / `mutation-results-cp-final.json`: final full run, 43/43 killed.
