# S06 consolidation report (bounded, builder-authored, Copilot-reviewed at most)

Plan OCS-REG-PLAN v1.1 (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`); Constitution pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`. Authorization: [decision record](decisions/2026-10-24-s06-authorization.md). Baseline `main` at `091355fd0abc368d07c71bfa0673f25feaa97979` (verified before any change; S05 merge `e10e8077…`, closeout `091355fd…`).

The result and acceptance language are recorded in [sprint-status.md](sprint-status.md) at closeout. This report holds the evidence.

## Deliverables

| | Deliverable | Where |
|---|---|---|
| A | Representation-contract disposition (five questions per value class) | [s06-representation-and-e05.md](s06-representation-and-e05.md) §A |
| B | E05 lone-surrogate boundary; three behavioral SKIPs preserved, not reclassified | same, §B |
| C | One consolidated trust-limitations page (T1–T14, with links to the evidence) | [trust-limitations.md](trust-limitations.md) |
| D | Test-helper review: **no change**, reasons below | this file |
| E | Documentation reconciliation | README, BUILDER_HANDOFF, architecture, sprint-status (see below) |
| F | Next-family recommendation (F1 remainder, F6, F4, F5); not implemented | [s06-next-family-recommendation.md](s06-next-family-recommendation.md) |

## D. Test-helper review (left unchanged)

Measured by comparing the parsed function sources of `tests/test_s03_contract.py`, `tests/test_s04_overlay.py` and `tests/test_s05_equivalence.py`:

| Helper | S03 | S04 | S05 |
|---|---|---|---|
| `canon` | identical (2 lines) | identical | identical |
| `seal` | 5 lines, differs | 4 lines | identical to S04 |
| `sha256_of`, `record_bytes`, `manifest_bytes` | n/a | identical | identical |
| `make_record`, `make_manifest`, `Scenario`, `operation`, `frozen_op` | n/a | present | present, **different bodies** (S05 takes per-field sets, versions and a reseal switch; S04 takes fixed fields and an explicit-`None` sentinel) |

Decision: **do not consolidate.** Reasons:

1. **Independence.** `canon` and `seal` are how each battery computes digests without calling the code under test. The S05 oracle and harness were built to avoid depending on S03 or S04 output. One shared helper module would make a single bug mask itself in all three batteries and would couple S05 to code S06 would then own.
2. **Frozen evidence.** The S01, S03 and S04 test files and the S05 harness (`tests/test_s05_equivalence.py`) are pinned by blob id (`tests/test_s06_integrity.py`) and their results are recorded evidence. Editing them would invalidate the recorded runs, and the instruction forbids altering `tests/s05_expectations.json`, `tests/s05_oracle.py` and prior raw results. The S05 harness is itself the producer of the recorded results.
3. **Risk against benefit.** The only truly identical code is about ten lines (`canon`, `sha256_of`, `record_bytes`, `manifest_bytes`, and `seal` between S04 and S05). The larger helpers differ on purpose. Merging them needs parameters that would weaken each file's self-contained trust assumptions.

Nothing was removed as redundant. No redundancy was demonstrated that could be removed without those costs.

## E. Documentation reconciliation

Updated: `README.md` (replaced the stale "S01 only" authorization section with the current state and links; corrected the "no registry" bullet to say what exists); `docs/BUILDER_HANDOFF.md` ("Current authorization" no longer says S01 only); `docs/architecture.md` (added the later components); `docs/sprint-status.md` (S06 row, outstanding operator decisions, unauthorized future work, next action). Historical documents are not rewritten: `docs/s03-contract.md`, `docs/s04-implementation.md`, the S02 files, `docs/source-provenance.md`, `docs/s05-*` and `docs/s05-results/` are unchanged (the S05 files are pinned).

## Verification

Commands (CPython 3.13.17 in a venv from the hash-locked `requirements-s01.lock.txt`, pytest 8.3.5; the lock's `colorama` is a Windows-only dependency and is not installed on Linux):

```
python -m pytest -q
```

Result on the PR branch: see the PR description and `docs/sprint-status.md` for the exact head and counts; the S01, S03, S04 and S05 batteries are unchanged, so their prior results stand. New in S06: `tests/test_s06_integrity.py` (18 blob pins, a SHA-256 pin on the baseline, a check that the recorded S05 results still show 3 SKIP and 0 failing cases, relative-link checks on the new documents). Skipped tests: none. No CI exists.

## Preserved (verified by `tests/test_s06_integrity.py`)

| Artifact | Git blob id |
|---|---|
| Plan v1.1 | `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2` |
| `safe_executor.py` (sha256 `940e781934542a7acd7bbe2f6833f9d329325d94b49425afd9d2bedcf23c5b68`) | `2fc880dae37eac76e5074533435740ce0684209d` |
| `registry_contract/validator.py`, `__init__.py` | `afee88b37197ca4aa3842b228fbc348f585b937a`, `5d8e9e69697fae3bc027666541a36379ce299d9f` |
| `registry_consumer/consumer.py`, `__init__.py` | `bf382d00cb275fa056d60713bf8fc119e9bee7da`, `22df0efa26bbed8f56cb354111bd7f2d0bf4f68b` |
| `tests/s05_expectations.json`, `tests/s05_oracle.py` | `37a68275c8c2b932d7a47adac43c05ec802d0081`, `503851c4ffa989a213c7dfb4d8957d0d540cb73c` |
| `docs/s05-results/differential-raw.json`, `pytest-output.txt` | `acb0e6903e725766b39c541acba8dc25a4154b57`, `04c3be500d2d2464e21d0a3e0e51ca0f033d2525` |

The remaining pins (S05 spec, report and harness, S01/S03/S04 tests, S04 fixtures) are in the test file.

## Cleanup exclusions and open items

Not done, by instruction: no change to S03 rules, S04 semantics, Runtime enforcement, S05 expectations or raw results; no new rule family, interpreter or infrastructure; no pin approval; no Runtime connection. Erratum recorded (not edited into the pinned S05 report): the S05 report counts 57 of 60 representation rows as full; the accurate split is in [s06-representation-and-e05.md](s06-representation-and-e05.md) §A. Not resolved: the 32 unresolved S02 classifications and the `60` versus `300` relationship; whether to change the contract for deny-all or wider characters; the E05 baseline boundary question (see §B of the disposition). COG-REG-SHARED-ADD-01 was not provided to this session and is deferred.
