# G1 readiness package (documentation only)

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Scope: the directive "G1 PREPARATION CLOSEOUT AND ORACLE READINESS" (2026-10-27). One documentation-only change in `cogno-us/cognous-ocs-registry`. It changes no Registry production code, Control Plane, Runtime, contract or qualification result. The frozen G0 evidence under `docs/family-migration/g0/` and the merged G1 preparation files under `docs/family-migration/g1-preparation/` are unchanged (new directory, additive text only).

| # | File | Content |
|---|---|---|
| 1 | [g1-preparation-merge-record.md](g1-preparation-merge-record.md) | PR #51 verification and merge record |
| 2 | [registry-pin-delta-assessment.md](registry-pin-delta-assessment.md) | PR-1: Registry delta `943ab18..317eb76a`, three baselines |
| 3 | [environment-profile.md](environment-profile.md) | PR-2: reproducible environment profile, PASS/BLOCKED/NOT RUN |
| 4 | [eight-file-test-evidence-closure.md](eight-file-test-evidence-closure.md) (+ `.json`) | PR-3: the eight files the workers could not collect |
| 5 | [runtime-f01-pin-path-assessment.md](runtime-f01-pin-path-assessment.md) | PR-4: does the Runtime F-01 suite exercise the pin path? |
| 6 | [architect-decision-register.md](architect-decision-register.md) | PD-1 to PD-10 dispositions; final versus provisional |
| 7 | [m1-oracle-specification.md](m1-oracle-specification.md) (+ `m1-oracle-specification.json`) | Revised specification: nine families, 65 oracles |
| 8 | [gap-to-oracle-traceability-matrix.md](gap-to-oracle-traceability-matrix.md) | 65 gaps to oracles and families; old-to-new family mapping |
| 9 | [g1-readiness-report.md](g1-readiness-report.md) | Readiness summary and recommendation |
| 10 | `tests/test_g1_readiness_integrity.py` | Documentation-integrity tests (outside this directory) |

Vocabulary. Oracle verdicts: PASS, FAIL, BLOCK, INCONCLUSIVE (and CHARACTERISED for characterisation-only oracles). They correspond to the program's assessment words HELD, BREACH, BLOCKED, INCONCLUSIVE, CHARACTERIZED. Gate-matrix words: BUILDER-TESTED / SAME-ORGANIZATION QUALIFIED / INDEPENDENTLY QUALIFIED / BLOCKED / NOT RUN / NOT APPLICABLE. Nothing in this package reaches INDEPENDENTLY QUALIFIED.
