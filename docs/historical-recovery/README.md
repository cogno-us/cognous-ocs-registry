# Historical recovery: V0.1 catalogue reconciliation (no separate V0.2 inventory)

Non-authorizing, builder-side, unqualified. Release, publication and production HOLD. This directory is an independent research workstream. It is not S06, not a registry migration and not a change to the static engineering plan. Nothing here activates a registry record, approves a manifest pin or changes runtime behaviour.

- Plan: OCS-REG-PLAN v1.1, blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2` (re-verified with `git hash-object docs/plans/PROJECT_PLAN-v1.1.md` on the base commit).
- Constitution pin: `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (cited from `docs/sprint-status.md`; the Constitution repository was not fetched in this exercise).
- Base: `cogno-us/cognous-ocs-registry` `main` at `091355fd0abc368d07c71bfa0673f25feaa97979` (Merge PR #11, s05-closeout). The head SHA is recorded in the PR, not here, because a file cannot contain the hash of the commit that holds it.
- Owned path: `docs/historical-recovery/` only. Every other path is read-only.

## Purpose and scope

Recover and classify the historical rule inventory (a V0.1 review-tag catalogue; this exercise does not claim a separate V0.2 inventory was recovered) held in `docs/mvp-recovery/registry/catalogue-v0.1/` of `cogno-us/cognous-open-control-stack`, and reconcile it against the current S02 source-based inventory (`docs/s02-inventory.md`, 620 rows, F1 to F11, 32 unresolved).

The catalogue is evidence to be classified, not a rule set. No catalogue entry has present-day authorization because it appears there (every entry carries `authority: none`).

## Headline findings

Labels used throughout: **[V]** verified by reading or recomputing in this exercise; **[R]** reported by a source document or by the catalogue itself, not independently checked here; **[I]** inferred classification, not established by source.

1. **The catalogue is a V0.1 catalogue, and V0.2 provenance is not established.** [V] All 3,190 rule entries carry `release_scope: v0_1`; the manifest `registry_version` is `0.1.0`; every source revision is the review tag `review-v0.1-g8-r10-20261022` (or an unrecorded revision). No rule entry cites a path under `docs/program-v0.2/` (scenarios, tests and fixtures were not searched for it). The only content labelled "0.2" is the `runtime-authority-reasons/0.2` reason-code registry (164 entries, a registry version, not a release scope). See `unresolved.md` U1.
2. **The catalogue is internally consistent.** [V] The catalogue's own validator passes (3,190 rules, 2,840 scenarios, 6,648 tests, 2,011 fixtures, 19,860 evidence records, 51,837 crosswalk rows, 6,030 coverage rows, 2 lineage sets; manifest digest `sha256:22f49fd1341cfaa6e46727db9b6153c2073b82a3125fd725173494f3ebb37650`), the three external artifacts verify against the index, and the generated reports are fresh. Internal consistency is not truth of source claims (the validator says so itself).
3. **1,819 of 3,190 rules are reason codes or refusal vocabulary; 247 are policy statements as stated, 240 are enforcement candidates (enforcement not established), 244 are historical proposals or decisions, 640 are unattributed; none is typed as a configurable policy parameter.** [V counts, I category mapping] See `catalogue-accounting.md`.
4. **The catalogue and S02 are different populations.** [V] S02 is code-derived (Runtime `ec728da6` and Control Plane `0a41faa9`). The catalogue is documentation-, schema- and test-contract-derived across twelve repositories. Only 369 of 3,190 entries come from the two S02 repositories, and of those only one code file (`src/agent_control_plane/manifest_validation.py`, 25 entries) was also inventoried by S02. Reconciliation is therefore mostly "not represented on the other side", not "match".
5. **2,978 of 3,190 rules have unresolved MVP applicability; 17,704 of 19,860 evidence records carry no source revision.** [V] These are preserved as adverse findings.
6. **The 32 unresolved S02 classifications are preserved unchanged.** [V] No catalogue entry is used to resolve any of them.

## Files

| File | Content |
|---|---|
| `source-inventory.md` | Exact repositories, commits, hashes, verification performed and not performed |
| `catalogue-accounting.md` | Rule and scenario denominators, category mapping, duplicates, unresolved accounting |
| `classification-crosswalk.md` | Historical categories against S02 categories and families F1 to F11 |
| `unresolved.md` | Missing provenance, contradictions, the 32 S02 unresolved rows, items not verified |
| `migration-candidates.md` | Ranked recommendations (not implementation authority) |
| `recount.py` | Read-only script that recomputes the catalogue counts quoted in `catalogue-accounting.md` (see its scope note) |
| `recount-output.json` | Its output at the recorded source commit |

## Reproduction

```
git clone https://github.com/cogno-us/cognous-open-control-stack SRC
git -C SRC checkout 51c579a3208149922649a31a6eb041106a4121c3   # the clone follows the default branch; pin explicitly
python3 -I docs/historical-recovery/recount.py SRC .
python3 -I SRC/docs/mvp-recovery/registry/tools/validate_registry.py --root SRC/docs/mvp-recovery/registry/catalogue-v0.1
```

`recount.py` imports the catalogue's own decoder and denominator functions from `SRC` (read-only use; bytecode writes are disabled) and executes no rule, scenario or test. It recomputes layer counts, normative-type, adoption, scope and applicability counts, the ten denominators (and checks them equal to the manifest), crosswalk dispositions, unresolved accounting (checked equal to the manifest), verdict groups, directory size, duplicate groups, and the S02 class counts. It does **not** recompute: raw-to-canonical absorption ratios and coverage-report figures (read from the generated reports, [R]), source tag peels, reason-registry file contents and file hashes (checked by separate commands recorded in `source-inventory.md`).

## Limitations

- The category mapping in `catalogue-accounting.md` is derived here from the catalogue's `normative_type` and `adoption_status` attributes. The catalogue states those attributes are not verified against source text; they are [I], not [V].
- The raw partition outputs (426 input files) that the catalogue was generated from are not in either repository. Regeneration was not reproduced.
- Only the Control Plane reason registries were spot-checked against source at the pinned tag. No other entry was re-read against source.
- Copilot review (when it occurs) is code and documentation review, not independent qualification. No qualification, certification or readiness claim is made.

## Merge control

Draft PR only. Not to be merged until S06 has merged and closed, the PR is re-checked against the new `main` head, its changed-file list contains only `docs/historical-recovery/`, provenance and accounting have been reviewed, and the operator explicitly approves integration.
