# Sprint status (the only live status document)

Updated 2026-10-24. Non-authorizing, builder-side. Release, publication and production are on HOLD.
Plan: OCS-REG-PLAN v1.1 (https://github.com/cogno-us/cognous-ocs-registry/blob/s01-baseline/docs/plans/PROJECT_PLAN-v1.1.md). Constitution pin: https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md.

| Field | Value |
|---|---|
| Sprint | S01: historical baseline recovery (proposed candidate, not an adopted release) |
| State | Operator decisions D1–D5 recorded ([record](decisions/2026-10-24-operator-decisions-D1-D5.md)). Baseline `g8-r10` selected (D1); Runtime-only scope accepted (D2); Apache-2.0 for new material (D3). PR #1 is draft and unmerged pending the D4 conditions (see Open items). S02 conditionally pre-authorized (D5), effective only after S01 PASS and merge. |
| Baseline | v0.1 review tuple `g8-r10` (hub `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c`, lock sha256 `dcd3ab9e...`), Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`, `engine/safe_executor.py` and `engine/__init__.py`. Operator-selected (D1); not an original or published release; not independently qualified. |
| Tests | 63 passed, 0 failed, 0 skipped on CPython 3.13.17 (hash-locked pytest 8.3.5), fresh clone at the head recorded in the PR comment. CI: none exists. 3.11/3.12 results are earlier builder self-runs. |
| Provenance | Imported files byte-identical to upstream `ec728da6` (`git hash-object` against a fresh upstream clone); hub lock hash `dcd3ab9e...` and tag peel `a2d9396c` re-verified. |
| Architect disposition | Received 2026-10-24: S01 BLOCKED on operator baseline selection; S02 NOT AUTHORIZED; PR #1 draft, not approved for merge. Focused independent inspection required before PASS. |
| CI | None; no workflow exists. |
| Qualification | None. Developer tests and a read-only reviewer worker are not independent qualification. |
| Open items | D4 condition 5 is NOT established: the fresh-context review was coordinator-directed and self-declared non-independent; a genuinely separate reviewer (or an operator ruling that this review suffices) is required before merge. Condition 12 (final-head verification) is checked at merge time. Known limitations (D4 condition 9): see source-provenance.md section 8 (policy construction validation, strict-number rejections, order beyond one pair, per-restriction failure-row assertion, unreachable one-effect branch). Mutation checks are scratch only. Per-file license headers not required by the retained texts. 3.11/3.12 are earlier self-runs. Embedded `CONTROL_PLANE_COMMIT` `2ea9528e...` differs from the lock's `0a41faa9` and is preserved unmodified. Plan v1.1 custody wording: [erratum](decisions/2026-10-24-plan-v1.1-custody-erratum.md), blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`. |
| Next authorized action | Complete D4 conditions for PR #1. S02 begins only after S01 PASS, merge, merge SHA recorded here, and a check against the unchanged S02 section of the plan. Do not begin S03. |
