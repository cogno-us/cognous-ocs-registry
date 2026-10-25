# Licensing (S01)

Non-authorizing. Operator decision D3 (2026-10-24, see `docs/decisions/2026-10-24-operator-decisions-D1-D5.md`). No publication authorization is granted.

## Newly authored material — Apache-2.0
Documents, tests, `pytest.ini`, `.gitignore` and other files authored for this repository outside `baseline/` are licensed under Apache-2.0 (root `LICENSE`) per operator decision D3. No copyright-holder statement is made for them: no ownership record for these files exists in this repository, and authorship is not inferred from operator status. They were written by builder sessions working at the operator's direction; if ownership or rights in any file is later found to be in question, the operator resolves the exception. The root `LICENSE` is the unmodified Apache-2.0 text.

## Imported material under `baseline/execution-runtime/` — unchanged, own terms
Governed by its own retained notices, not by the root `LICENSE`:
- `engine/` source (`engine/__init__.py`, `engine/safe_executor.py`): Cognous-authored, Apache-2.0 per `baseline/execution-runtime/NOTICE`, `engine/LICENSE`, `LICENSE-APACHE-2.0`.
- `baseline/execution-runtime/LICENSE`: MIT, Copyright (c) 2025 Peter Steinberger, for the upstream Moltbot application and upstream-derived retained files. The two imported `.py` files carry no upstream-derived marker and none is claimed; the MIT text is retained as notice material and nothing is relicensed by implication.
- Source revision: `cogno-us/cognous-execution-runtime` `ec728da6dc301a664b331ac8986afd6e850a1273`; files are byte-identical to it.

## Copied test material
`tests/test_s01_baseline_local_policy.py` copies synthetic `ExecutionOperation` field values from the Apache-2.0 upstream test `tests/test_producer_contract.py` at the revision above; the attribution is in the test module docstring.

## Not covered
Upstream components not imported, third-party dependencies (pytest and its locked dependencies keep their own licenses), and any distribution, publication or release (all HOLD). This is not legal advice.
