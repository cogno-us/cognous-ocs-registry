# Cognous OCS Registry (engineering baseline)

Status: builder-side, non-authorizing. Release, publication and production are on HOLD. Nothing in this repository is a qualification, certification, security clearance or readiness claim, and no production use is claimed or implied.

## Mission

Migrate configurable, hardcoded governance rules of the Cognous Open Control Stack (OCS) into a versioned declarative registry, one rule family at a time. That is the sole development objective of this repository.

This is not a new OCS implementation program. It does not reconstruct the stack, duplicate established components, reactivate the v0.2 program, or migrate the historical qualification corpus.

## Governing references

Static plan OCS-REG-PLAN v1.1: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md. Engineering Constitution (exact pin): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md.

## Licensing

Newly authored material: Apache-2.0 (`LICENSE`); imported material keeps its own notices. See [LICENSING.md](LICENSING.md).

## Operator decisions

D1–D5 of 2026-10-24: [docs/decisions/2026-10-24-operator-decisions-D1-D5.md](docs/decisions/2026-10-24-operator-decisions-D1-D5.md).

## Current state (reconciled in S06; the live record is [docs/sprint-status.md](docs/sprint-status.md); program closeout: [docs/closeout/](docs/closeout/program-closeout-2026-10-26.md))

S01 to S05 are complete and merged (S01 baseline recovery, S02 inventory, S03 contract, S04 consumer, S05 differential equivalence); S06 consolidation is recorded in the status file. No further sprint is authorized: a new rule family, shared ISS/OCS registry work, dynamic activation, approval of a manifest pin, publication, production and formal independent qualification each need a separate operator decision. Release, publication and production are on HOLD.

What exists: a record contract and validator for three `LocalExecutionPolicy` allow-lists (`registry_contract/`, [S03](docs/s03-contract.md)); a consumer that can only narrow a caller's policy (`registry_consumer/`, [S04](docs/s04-implementation.md)); a differential battery and its recorded results ([S05](docs/s05-equivalence-report.md), `docs/s05-results/`). Nothing calls the consumer, no pin is approved, and the Runtime is unchanged. Read [docs/trust-limitations.md](docs/trust-limitations.md) before relying on any of it, and [docs/s06-representation-and-e05.md](docs/s06-representation-and-e05.md) for what the contract cannot express. The next-family recommendation is [docs/s06-next-family-recommendation.md](docs/s06-next-family-recommendation.md) (a proposal, not authorization).

## Family migration and F3 status (2026-10-30)

The 19-parameter family migration is implemented and merged; the S01-S06 text above is historical. Start with the [implementation closeout](docs/family-migration/IMPLEMENTATION-CLOSEOUT-2026-10-29.md), the [final-three decision records](docs/family-migration/final-three/), the [successor interpretation](docs/family-migration/final-three/06-f3a-dev-pe-1-interpretation-v1.0-2026-10-29.md) and the [F3 final engineering closeout](docs/family-migration/final-three/14-f3-final-engineering-closeout-2026-10-30.md). Independent qualification evidence is in the [qualification hub](https://github.com/cogno-us/cognous-stack-qualification/tree/main/results/third-party/cp-739efe7-f3-independent-20261029); open obligations are in [issue #240](https://github.com/cogno-us/cognous-stack-qualification/issues/240). Formal independent acceptance is not established; release and production are on hold.

## What this repository does NOT do

- It does not contain a registry service, an active rule record, scenarios or an extraction tool (no `registry/` or `tools/` directory exists). Since S03 it holds one contract, one non-activated consumer and synthetic fixtures for exactly three `LocalExecutionPolicy` allow-lists; no other rule is extracted or migrated.
- It does not import the historical registry catalogue (about 3,190 rule records, about 2,840 scenarios, 6,648 tests, accumulated evidence) or any of its generated artifacts. That catalogue is a read-only discovery and provenance resource.
- It does not import historical tests in bulk, execution logs, generated test artifacts, CI output, PR reports, superseded planning documents, corpus copies or release-packaging machinery.
- It does not import the Control Plane, Replay, Evidence Pack, ODES, Verifier or Action Manifest. It imports no later improvement (for example the F3 repairs); those are listed, not applied.
- It adds no real payment, network, subprocess or production-credential effect. The only destination is synthetic SQLite.
- It does not claim that the baseline is qualified. See "Unqualified" in [docs/source-provenance.md](docs/source-provenance.md).

## Historical source baseline (operator-selected, exact)

**Scope caveat:** this baseline is a first, narrow slice (the Runtime's local policy only). Control Plane scanners, mandatory-check manifests, reason codes and the policy gate sit outside it. Candidate files for later sprints, not imported: Runtime `engine/effective_grant.py`, `engine/permissions.py` (+json), `engine/action_schema.py`; Control Plane `policy_gate.py` and `reason_vocabulary.py` (names inferred, not read).

The S01 baseline, explicitly selected by the operator in D1 (a review marker, not an original or published release and not independently qualified), is the hub's "v0.1 public review" tuple `g8-r10` (a review marker, not a version or release; hub tag `review-v0.1-g8-r10-20261022`, hub commit `a2d9396c1e2022ac36ae4db58dcc2f2e14161b7c`, component lock SHA-256 `dcd3ab9e4e737c7e50f4bc38c2439438f156da64c9eb1e46725f477973da59ff`). From that tuple only one component's source is imported, in two files:

| Component | Repository | Revision | Imported |
|---|---|---|---|
| Execution Runtime (`moltbot_safe`) | `cogno-us/cognous-execution-runtime` | `ec728da6dc301a664b331ac8986afd6e850a1273` | `engine/__init__.py`, `engine/safe_executor.py`, with `engine/LICENSE`, `LICENSE`, `LICENSE-APACHE-2.0`, `NOTICE` |

Imported files are byte-identical to that revision; a test checks their Git blob ids. Why this baseline, how it differs from the bounded V1 reference candidates and from the October 2026 MVP tuple, and everything else, is in [docs/source-provenance.md](docs/source-provenance.md). The architecture is in [docs/architecture.md](docs/architecture.md).

## Relationship to the existing OCS components

The existing repositories (hub `cogno-us/cognous-open-control-stack`, Control Plane, Execution Runtime, Replay, Evidence Pack, ODES, Verifier, Action Manifest, Stack Qualification) stay authoritative for their implementations. The copy under `baseline/` is a pinned, read-only reference for comparison; do not edit it. A change to behaviour belongs in the owning component repository, not here.

## How to run the tests

Python 3.12 (the version the Runtime's own CI uses at the baseline revision). The only dependency is pytest, hash-locked in `requirements-s01.lock.txt` (a byte-for-byte copy of the Runtime's `.github/locks/pytest-b61d81.txt`). The imported source uses the standard library only.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements-s01.lock.txt
.venv/bin/python -m pytest -v
```

`pytest.ini` puts `baseline/execution-runtime` on the import path. The result recorded for the PR head is in [docs/sprint-status.md](docs/sprint-status.md).

PR #1 and the checks cited in it are builder-side inspection, not independent qualification; a separate reviewer is still required.

## Licenses

The imported Runtime engine (`engine/`) is Apache-2.0 (`baseline/execution-runtime/engine/LICENSE`, `LICENSE-APACHE-2.0`). The Runtime repository root also carries an MIT `LICENSE` (upstream Moltbot, Copyright (c) 2025 Peter Steinberger), kept as retained upstream notice material; it is preserved unchanged next to the import. Original files in this repository (documents and tests) are licensed Apache-2.0 per operator decision D3 (root `LICENSE`); no copyright-holder or independent ownership-verification claim is made. Publication and distribution remain on HOLD. See [LICENSING.md](LICENSING.md) and [docs/source-provenance.md](docs/source-provenance.md).
