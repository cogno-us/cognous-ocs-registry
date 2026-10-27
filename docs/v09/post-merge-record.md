# V09 post-merge record (append-only; 2026-10-27)

Non-authorizing. This file records events after PR #47 and supersedes nothing in the merged V09 package except where the table below says so. The merged files under `docs/v09/` are unchanged historical records of the candidate as prepared.

## Merge
- V09 freeze-candidate PR: [#47](https://github.com/cogno-us/cognous-ocs-registry/pull/47), **merged**, merge commit `b695f67d944286c76100ddab36818f926958297f` (first parent `1a4de326`, second parent the PR head `ae20e43c915b7a0c9446c544db145bb24e253291`; the merge tree equals the PR-head tree).
- The freeze-candidate package is available on `main` at `docs/v09/`. The candidate is **prepared and merged, NOT formally accepted.** No tag, version or release exists.
- Registry `main` therefore moved from the candidate baseline `1a4de326` to `b695f67d`. The change between them is documentation, tests and tools only; every contract blob in the manifest is unchanged (checked offline by `tests/test_v09_candidate_integrity.py`). The manifest still names `1a4de326` as the Registry baseline on which the candidate was built, as designed.

## Items that this record updates
| Merged V09 statement (historical) | Current state |
|---|---|
| `gate-matrix.md`: "V08 F3 re-review ... NOT RUN in repository evidence" | The Architect completed the F3 re-review and accepted Runtime #149 for the bounded candidate (Architect statement, 2026-10-27). Runtime documentation PR [#150](https://github.com/cogno-us/cognous-execution-runtime/pull/150) records it (open for Architect review at the time of writing). It is not independent qualification and not production clearance. |
| `readiness-report.md` blocker 3 (F3 re-review) | Resolved by the Architect acceptance above. |
| `readiness-report.md` blocker 5 (decision on #235 and #236) | #235 stays open and unmerged as the immutable historical reference. #236 verified superseded by #237 and closed (below). |
| `readiness-report.md` blocker 6 (record this PR's merge SHA) | Done in this record and in `docs/sprint-status.md`. |
| `candidate-manifest.json` `holds.V09` ("CANDIDATE PREPARATION AUTHORIZED; ACCEPTANCE NOT YET AUTHORIZED") | Unchanged as the as-prepared record. Current: **FREEZE-CANDIDATE PACKAGE MERGED; FORMAL ACCEPTANCE HELD.** |

## Historical Stack Qualification PRs
- **#235** (head `7b72de9ac7e4898c0f9bdad3e9b337775cc9c543`, branch `v08-tier1-qualification`): **open, unmerged, retained.** It holds the historical F-A1 BREACH, the original failed gate and the original V08 evidence (`results/v08-tier1/`). A deliberately failed qualification is not merged to `main` to obtain a green PR inventory. It also stays reachable at `refs/pull/235/head`. It is not closed because the repository has no other durable preservation path for that evidence on `main`; the Architect may later choose to merge it as a documented failed assessment or archive it by an adopted custody rule.
- **#236** (head `1a9b6a933986a51e2cf8d2e5e79679538305e2c2`): **closed as superseded by #237** after verification that every file of its head exists on `main` (`bb9b08904192b5f50a49e00ed8de0cab80fd7c19`), differing only by the intended pin advance, the byte-for-byte vendoring of the one historical helper (sha256 `a36dc8f81f4789cc795abf43f8f510acc68eac5acfee07806c7a0e237c60d2a7`) with its digest check, and two append-only README notes. Its branch was not deleted; its commits stay reachable by SHA and `refs/pull/236/head`. Its consolidated architect-review handoff comment is retained on the PR.
- **#237** (merge `bb9b0890`, head `ed4f45a525da1a05e5dbb8f0de27ab4bbbd70d3b`): the accepted qualification; its CI evidence is run 40555193111.

## Evidence custody notes
- CI artifact `v08-fa1-evidence` of run 40555193111 (16.7 kB) is not expired and expires on 2027-01-25. The repository holds the run URL and the results README, not the artifact bytes. **Architect action (recommended):** export and archive the artifact before expiry, or direct that it be committed append-only. The builder did not download it (the environment cannot fetch run artifacts).
- All three qualification repositories are public.

## Independent qualification assignments (prepared, not executed)
- [independent-v07-security-review-assignment.md](independent-v07-security-review-assignment.md)
- [independent-v08-tier1-assignment.md](independent-v08-tier1-assignment.md)

Neither assignment designates a reviewer. An AI worker, a separate AI session or a CI run is not an independent external assessor (Constitution `ADOPTION.md` at `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`). The builder performed no part of either review.

## Program status
V01-V08: bounded engineering implementation merged. V09: freeze-candidate package merged; formal acceptance held. Independent V07 security review: OPEN. Independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.
