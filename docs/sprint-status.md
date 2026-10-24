# Sprint status (the only live status document)

Updated 2026-10-24. Non-authorizing, builder-side. Release, publication and production are on HOLD.
Plan: OCS-REG-PLAN v1.1 (https://github.com/cogno-us/cognous-ocs-registry/blob/s01-baseline/docs/plans/PROJECT_PLAN-v1.1.md). Constitution pin: https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md.

| Field | Value |
|---|---|
| Sprint | S01: historical baseline recovery (proposed candidate, not an adopted release) |
| State | Draft PR #1 updated after review round; baseline choice unconfirmed; not merged. |
| Proposed baseline | v0.1 review tuple `g8-r10`, Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`, `engine/safe_executor.py` and `engine/__init__.py` (see [source-provenance.md](source-provenance.md)). Proposed, not confirmed by the operator. |
| Tests | 17 passed on CPython 3.13.17 (hash-locked pytest 8.3.5) in this session; 13 passed at the prior head from a fresh clone. 3.11 and 3.12 results are earlier builder self-runs, not re-run by the completion session. SKIP: none. |
| Provenance | Imported files byte-identical to upstream `ec728da6` (`git hash-object` against a fresh upstream clone); hub lock hash `dcd3ab9e...` and tag peel `a2d9396c` re-verified. |
| Architect disposition | Received 2026-10-24: S01 BLOCKED on operator baseline selection; S02 NOT AUTHORIZED; PR #1 draft, not approved for merge. Focused independent inspection required before PASS. |
| CI | None; no workflow exists. |
| Qualification | None. Developer tests and a read-only reviewer worker are not independent qualification. |
| Open items | Operator: OD-01 select baseline; OD-02 accept Runtime-only scope; OD-03 licence; OD-04 accept package and authorize merge; OD-05 authorize S02 (separate). Also: confirm baseline (is `g8-r10` the intended "original v0.1"; earlier W7/`f5b` tuples exist); decide this repository's license; decide whether the Runtime #144 / F3 merge-status discrepancy needs action; formal Constitution adoption record. Known gaps: malformed-target cases of `_target_is_well_formed` untested; per-file license headers not audited; mutation checks not committed. |
| Next authorized action | **None** until the operator authorizes one. Do not start S02 or any rule extraction. |
