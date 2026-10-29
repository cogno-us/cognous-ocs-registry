# Registry shared-orchestration review (Work Package D): verdict DOCUMENT-ONLY

Status: documentation only; non-authorizing; append-only. 2026-10-28. Governing documents: Static Migration Plan v1.1, Engineering Plan v1.5, adopted audit (PR #60, merge `6516446a4e551e50f2bb47c1d57fbf8ace27d7c5`), consolidation assessment (PR #65, merge `75266cd40400832aee4a798e4d62aba239425b17`), Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (`ADOPTION.md` at the same revision). Reviewed revision: Registry `main` `75266cd40400832aee4a798e4d62aba239425b17` (includes `r08-v5` from PR #64, merge `94e8652725ec34e29fc9b91ed132bb8b5a4b381a`). No Registry code is changed by this increment and `r08-v6` is NOT introduced.

## Question
Can the duplicated verification orchestration in `registry_successor/v3_*`, `v4_*`, `v5_*` (`*_verify`, `*_selection`, `*_record`, `*_decision`) be extracted into one shared implementation while preserving the signing domains, version-specific canonicalization, frozen vectors and contract identities, version-specific validators and composers, public import paths, the source-boundary protections and the byte-identical frozen historical files?

## Finding
- v3/v4/v5 `*_selection` and `*_record` are identical modulo version names (v5 `*_record`/`*_verify` differ from v4 only in one docstring line). `*_decision` differs only in the family-table reference and one family string (and an added import in v5). The version-specific content is the contract and domain constants, the family-table references, the family-name string, the caller-normalizer reference and the per-version function names and exports.
- Verdict: extraction is NOT safe in this increment. Protected, frozen or pinned files and tests block it:
  - `tests/vectors/r08v4/frozen_baseline_manifest.json` and `tests/vectors/r08v5/frozen_baseline_manifest.json` pin the sha256 of the v3 files (and the v5 manifest also the v4 files); `tests/test_r08v4_frozen_baseline.py` and `tests/test_r08v5_frozen_baseline.py` fail on any byte change. Editing v3/v4 is therefore a re-baseline, not a refactor.
  - The frozen-baseline tests assert the exact module sets of `v3_*`, `v4_*` and `v5_*` and forbid frozen modules from naming later-version modules, so v3/v4 cannot import a shared helper that lives in a `v5_*` module, and a new `v[345]_*` module fails the exact-set tests (a neutrally named module would not).
  - Source-text parity tests compare `inspect.getsource` of `_verify_v3`/`_verify_v4` and of the v4/v5 verify, authenticity, `_decide_verified` and `verify_and_decide_*` functions after normalisation (`tests/test_r08v4_targets_and_versions.py`, `tests/test_r08v5_frozen_baseline.py`). Delegating stubs would break them and rewriting them would weaken the parity evidence.
  - `tests/test_ext_s1_5_identity_module.py` runs `git diff --name-only origin/main...HEAD` against a closed allowlist (any new shared module needs a narrow addition); `tests/test_r08_integrity.py`, `tests/test_r08v2_family_dispatch.py`, `tests/test_ext_s1_5_vectors.py` and `tests/test_adapter_ed25519.py` carry closed code/module/import sets a new module would have to satisfy.
- The v5 files are not yet hash-pinned, but they are locked by the exact-file-set test, the allowlist and the parity tests.

## Recommendation (not an authorization; for the Architect, tied to a future contract version)
If a further Registry family is ever authorized (a new contract version, `r08-v6` being only the next free identifier), add the shared mechanism there and leave v3/v4/v5 byte-identical:
1. one neutrally named module (for example `successor_core.py`) parameterised by contract, signing domain, family table and caller normalizer;
2. only the new version's modules use it; narrow allowlist entry; the new version's baseline manifest pins it;
3. a differential test proving the shared path yields outputs identical to v5 on the frozen vectors, so the extraction is evidence-backed rather than assumed.
Changing frozen v3/v4/v5 modules to use it would be a separately gated, Architect-approved requalification and re-baseline. Priority: P2 (useful simplification); not required before the remaining parameters. This review makes no change and starts no migration.
