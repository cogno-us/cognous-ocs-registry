# G1 preparation merge record (Phase A)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Directive condition: "PR #51 is approved for merge, conditional on unchanged head and successful exact-head CI. If the head changed or checks failed, STOP."

| Check | Observed (2026-10-28, immediately before merging) |
|---|---|
| PR | cogno-us/cognous-ocs-registry#51, state open, not merged, mergeable_state clean |
| Approved head | `00e9bb63e0ad32c7900713050e47b5df22279152` |
| Observed head | `00e9bb63e0ad32c7900713050e47b5df22279152` (unchanged) |
| Base at merge time | `7208eb6f53f12677f138fe0c64ec48a2e58292b5` (G0 merge; main had not advanced) |
| Exact-head checks | CodeQL success; pytest success; Analyze (actions) success; Analyze (python) success |
| Changed files | 20: 12 under `docs/family-migration/g1-preparation/`, 3 under `evidence/worker-E/`, 3 under `evidence/worker-F/`, `docs/sprint-status.md`, `tests/test_g1_preparation_integrity.py`. No file outside preparation documents, evidence, status and the integrity test. |
| Merge method | merge commit (REST `PUT /pulls/51/merge`, `merge_method=merge`, guarded with `sha=00e9bb63e0ad32c7900713050e47b5df22279152`) |
| Result | merged; **merge commit `2afbd8cd119751842b5df824229726aeb0e4a863`**, parents `7208eb6f53f12677f138fe0c64ec48a2e58292b5` and `00e9bb63e0ad32c7900713050e47b5df22279152` |
| Checks on the merge commit | pytest, Analyze (python) and Analyze (actions) completed success when queried |

Effect on the program pins. The merge adds documentation only: `git rev-parse` of the seven Registry code directories is identical before and after (see registry-pin-delta-assessment.md). The Registry program pin for cross-repository work stays `317eb76acb2847c534c3ce7c2180b89b4aef987d`; `main` is now `2afbd8cd119751842b5df824229726aeb0e4a863`.

Status vocabulary after the merge: G1 preparation is MERGED. It authorized nothing: G1 contract development, oracle implementation, migration waves and G2 to G5 remain NOT AUTHORIZED.
