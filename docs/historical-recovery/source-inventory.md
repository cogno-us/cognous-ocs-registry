# Source inventory

Exact references used in this exercise. Labels: **[V]** verified here, **[R]** reported by a source, **[I]** inferred.

## 1. Repositories and commits

| Item | Reference | Status |
|---|---|---|
| Registry repository base | `cogno-us/cognous-ocs-registry` `main` = `091355fd0abc368d07c71bfa0673f25feaa97979` (Merge PR #11 from `s05-closeout`, 2026-10-24T19:32:12-07:00) | [V] `git rev-parse` on the clone and `git ls-remote origin refs/heads/main` at branch creation |
| Recovery branch | `recovery/v02-rule-inventory`, created from the commit above | [V] |
| Source repository | `cogno-us/cognous-open-control-stack` HEAD `51c579a3208149922649a31a6eb041106a4121c3` (2026-10-24T12:45:47-07:00) | [V] clone HEAD equals `git ls-remote origin HEAD` at the time of reading |
| Historical catalogue | `docs/mvp-recovery/registry/catalogue-v0.1/` in the source repository at the commit above | [V] |
| Plan | `docs/plans/PROJECT_PLAN-v1.1.md`, blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2` | [V] `git hash-object` on the base commit |
| Constitution | `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` | [R] from `docs/sprint-status.md`; not fetched |
| S02 inventory | `docs/s02-inventory.md` and `docs/s02-evidence/W1.md` to `W9.md` on the base commit | [V] read; 620 rows reparsed, class counts reproduce |

## 2. Catalogue files relied on (source commit `51c579a3`)

Paths relative to `docs/mvp-recovery/registry/`. `sha256` is over file bytes; "blob" is `git hash-object`.

| Path | sha256 | blob |
|---|---|---|
| `README.md` | `eea66903d87c1c3fb93cfd88ddc8b9ac294cf04d52bd7e4b9592ddf8a549dcb6` | `fa11d6bf96d83e94e66d7a333762408a72e3a1f4` |
| `catalogue-v0.1/manifest.json` | `5a91ff1a1da2dde440ec10852ad3818b5205ae09e55f59bc7904a9130afd0123` | `a24090d64611f0b27685310051ab830ce9492fd0` |
| `catalogue-v0.1/reports/generated/catalogue-integrity-report.md` | `2698688931c4db876f560ba8a41b8dd0073eb57fc464e628e58e25daaafc814a` | `5e84519b67f46fbf28498d32e7aa565dcac98146` |
| `catalogue-v0.1/reports/generated/denominator-report.md` | `e1a51d395610f784ff638d6cfee91f41876d0ddadc742bd3818348da0b1e37ee` | `640fe227853adbb3507f642963f043c50f206b6f` |
| `catalogue-v0.1/reports/generated/governance-coverage-report.md` | `2816db65a7e9f646477455c3d1726dc6e8ef728993b18a99aa1bf70115a5e312` | `062e24f92e7101982fe2597608826307759febd9` |
| `catalogue-v0.1/artifacts/crosswalk-rows.6810f07e12d1.json.gz` | `408dc62b34cfa706356d17d1262ca98e8bd8763fb15e6fca9192344b158b890c` | `02a80c114ef5182652660ea9d220c67302780bba` |
| `catalogue-v0.1/artifacts/evidence-records.eda862089253.json.gz` | `45577e32baa4bb8981fa892bb49b2ca1b257d67ab386cc47f0cf32bc56d9681c` | `20e7c15f29f805b230034562f995198cf0874690` |
| `catalogue-v0.1/artifacts/relationship-rows.3de4a6fb387c.json.gz` | `05d3e3e3f6c21fb7d4f409a4998c65c7df25b24f369431ec593c4d36d821752a` | `19369af37f994cbaf09f96092af08cad6ff91beb` |
| `overlays/mvp-linked-q8.json` | `99ead4d79ec4b27e256df56c1360ea3df568805706f97fc296cf4ee9cb6f018e` | `c1d7f7fc135bd359a304ee3c8ab42bd770ed4a65` |
| `tools/validate_registry.py` | `175c1667270cb737625218d573e636e2ef579a973f4156c13235ae9d0f9c59d1` | `3ddcbc61343f6a64a62dc76c5b4574a40ef442b9` |
| `tools/load_partitions.py` | `d2167c5cfe89c768ea0ce4b1a09e9799e7f1cbf339bb855f7a61d6877f99b63e` | `f41e6b6c1005548c7244e8e44b72ed79e06c2355` |
| `tools/build_registry.py` | `b618e34d1e6a0d0c3096e87631816b5224392be9e60fe5153483382a6891d46f` | `8540806262198824563b14054262b202f7a4b5e9` |
| `tools/generate_reports.py` | `37777d492e4de9a44874d1ebcd0738dc8bf4ada1fdb2b18fc40257c5e64dc872` | `74b55198f7b4c1ae36b24d769faf54e360e27471` |

The three tool hashes for `validate_registry.py`, `load_partitions.py` and `build_registry.py` equal the values recorded in `manifest.generation_tool.files`. [V]

The manifest has two distinct identifiers that must not be confused: the file `sha256` above (`5a91ff1a...`) and the canonical manifest digest `sha256:22f49fd1341cfaa6e46727db9b6153c2073b82a3125fd725173494f3ebb37650` (RFC 8785 canonical JSON, excluding its own `digest` member). Reports and this directory cite the canonical digest.

The catalogue's 496 committed partitions are each pinned by `sha256` in `manifest.partitions`; the validator re-hashed every one and every partition passed. [V] The repository also contains a small synthetic sample catalogue at the root of `docs/mvp-recovery/registry/` (`synthetic_sample: true`); it is not part of this inventory.

## 3. Verification performed

| Check | Command or method | Result |
|---|---|---|
| Catalogue consistency | `python3 -I tools/validate_registry.py --root catalogue-v0.1` | `catalogue consistent: coverage=6030, crosswalk=51837, evidence=19860, fixtures=2011, lineage_sets=2, rules=3190, scenarios=2840, tests=6648`; 3 external artifacts verified against the index [V] |
| Report freshness | `python3 -I tools/generate_reports.py --root catalogue-v0.1 --check` | exit 0 [V] |
| Decoded layer counts against manifest | `recount.py` | all eight layers equal `manifest.layer_counts` [V] |
| Crosswalk accounting | sum of raw-set record counts | 2,863 + 3,655 + 2,316 + 11,360 + 346 + 3,112 + 26,110 + 2,075 = 51,837 = crosswalk rows [V arithmetic on manifest values] |
| Review tags of all twelve source repositories | `git ls-remote <repo> 'refs/tags/review-v0.1-g8-r10*'` | In each repository the peeled commit equals the commit the manifest records, and the tag object equals the manifest's tag object wherever the manifest records one (table below) [V] |
| Control Plane reason registries | shallow clone at tag commit `0a41faa9`; read `schemas/runtime_authority_reasons_0_1.json` and `_0_2.json` | 121 and 164 codes; the 0.2 set contains all 121 codes of 0.1 plus 43 more; equals the catalogue's 121 and 164 entries [V] |
| Plan blob | `git hash-object` | equals `6ece90f6...` [V] |
| S02 counts | re-parsed `docs/s02-evidence/W*.md` | 620 rows; 354 / 90 / 51 / 50 / 43 / 32; the 32 unresolved IDs equal the list in `docs/s02-inventory.md` section 5 [V] |

### Review tags (tag object, peeled commit)

| Repository (under `cogno-us/`) | Tag object | Peeled commit | Peeled commit equals manifest |
|---|---|---|---|
| `cognous-open-control-stack` | `00c915d3a12400f38d1e753ecbe5576404c99840` | `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c` | yes |
| `cognous-institutional-governance` | `3b15712bd21cf3b87edae261fc97ad9125403c24` | `9b5ab721ae0684150e466c01e9d0d59ec61c3e00` | yes |
| `cognous-control-plane` | `e33c55f707e04025d3f5abe70c59e8c914dce31f` | `0a41faa972699f7ec3063967a14cd9bdd3e67d27` | yes |
| `cognous-action-manifest` | `d2b3a02224928bc55ecc73d414a2ac89c88d4d48` | `fa170815ef96a54c233d0dd9da821b60debabf8b` | yes |
| `cognous-execution-runtime` | `e1249262cbe6139c46fc9a3b599e6b5179ab991e` | `ec728da6dc301a664b331ac8986afd6e850a1273` | yes |
| `cognous-governance-evidence-pack` | `43b3aa2e0ec9b39fad9e4ec96d06b69651b5095e` | `a3ebbb90559a44a88855139a182649d3792bb1ca` | yes |
| `cognous-open-control-stack-verifier` | `8e16b19a64bea3302b5e248ccae162004f6c6058` | `c0b8ba1f55b75db787a320f3de0f79342c6f6826` | yes |
| `cognous-replay-bundle` | `aa30b4ca29ec9075805f73d6c57b0ac4822b3bd3` | `028f63d1c001f99580583888fa4b4e46d77a267b` | yes |
| `open-decision-evidence-standard` | `926046fe04571dfb5ffe3c993c07819825b0dd4e` | `e86a25a1d660e74533337d38744e2934200a50ae` | yes |
| `cognous-governed-exchange` | `71f1ae03515121633ff06d6625cfb95a4bc4d986` | `7f7569b02666b99669a9fca61117ca1f4bce5f0d` | yes |
| `cognous-open-control-stack-ergonomics` | `7b0be32a2b7647f6f2c87a5e9c1d2599cf321363` | `54807212f002bf20d9eba4c0037cb61214aa045f` | yes |
| `cognous-stack-qualification` | `8a8a3be598d1aee412fe4856465db7fdc301702c` | `195c728fa292e7f20f6ccca0f625a744c5bf5aec` | yes |

The S02 pins coincide with the catalogue pins for the two overlapping repositories: Runtime `ec728da6dc301a664b331ac8986afd6e850a1273` and Control Plane `0a41faa972699f7ec3063967a14cd9bdd3e67d27`. [V]

Partition D (Qualification) also cites `main` `4298247e860126d04d0bc44e1f2aef0fde1c4c97` and branch `origin/mvp-final-expectations-v6` at `c106b8693509290283177176e19c4d9f91ca16ad`. Neither was checked. The Qualification `HEAD` read from the remote during this exercise is `998d39c5ba1c9d537be8289f7658f2e9cde6cbba`, so `main` has moved since generation. [V that it differs; the consequences are not assessed]

## 4. Raw sets behind the catalogue

| Raw set | Raw records | Inventory digest (from manifest) | Source repositories |
|---|---|---|---|
| A | 2,863 | `sha256:df5e48440d5c66a57f18cb118206dbe9f41af214776220d2c502c061e11982ad` | institutional-governance, open-control-stack (incl. tar members) |
| A2 | 3,655 | `sha256:03dc65f405e413ae003803af2dd04b895d2d34cebb2aa6161d6e85db228b8ec9` | same as A |
| B | 2,316 | `sha256:e8336e13959d2ce31fe67c6823f58722bc8e18e40951dcd840216528de28e1b3` | action-manifest, control-plane (some revisions `unrecorded`) |
| C | 11,360 | `sha256:561e34869dce70cf8968efd13b92eb62cfc31b1ef761ad5f29a38a36ea001097` | execution-runtime, evidence-pack, verifier, replay-bundle, ODES |
| C2 | 346 | `sha256:292c0c5c9c35d82a4b5718068c10de090b9dba8b712775b3b7986541c6ec2514` | same as C |
| C3 | 3,112 | `sha256:5520561810e99b0685510cbf867427e7472e0dd873478d31ad402aaa84430ca8` | same as C |
| D | 26,110 | `sha256:4d7557ed7e13c5a31fee6aa27faf73f0d2dabc0d22d39250b8ff5ef3dc99f1c1` | stack-qualification (several revisions, some `unrecorded`) |
| R4 | 2,075 | `sha256:4f5d995a8e9a417e05fab76bc4d26fb3d16f5ee1f94c0da2a7c9beb3417bfd19` | governed-exchange, ergonomics |

These digests are [R]: the raw inputs are not in either repository, so they cannot be re-hashed. `manifest.regeneration` records 426 input files with `input_files_sha256` `sha256:b2db6326ce8f198e91aff572081b9e86f397bacc3e443aa78a38dc397a142a63` [R]. Regeneration was not reproduced.

## 5. Not verified in this exercise

- Content of the raw inputs, and any entry other than the Control Plane reason registries, against source at its tag.
- The Constitution pin, the `CR-001` to `CR-035` text, and whether `CONSTITUTION_v0.1.md` (the origin of the 229 proposed clauses) was ever adopted.
- Statements in the project documents about open hub pull requests (for example that a later hub change bundles a further catalogue manifest revision). Those are [R]; this inventory is of the catalogue as committed at `51c579a3`.
- Whether any later commit in the source repository alters the catalogue (only the commit above was read).
