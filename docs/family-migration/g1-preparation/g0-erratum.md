# G0 erratum (additive; G0 files are not edited)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

The G1 preparation review (Workers E and F, read-only, at Registry `317eb76a`, Runtime `0dde0ef7`, Control Plane `d66ae07f`, Stack Qualification `bb9b0890`) found statements in the frozen G0 package that the new evidence contradicts or refines. Each is a proposed correction for the Architect to accept; none changes a count, a disposition or a classification.

| Id | Frozen G0 statement | G1 preparation finding | Evidence |
|---|---|---|---|
| EG-1 | Ledger G0-A-001/002 and G0-B-009/010/012/013 record no missing oracles for the five f1ab sets (and the matrix calls F1b an 'evidence gap' only for allowed_units). | All twelve M1 topics are PARTIAL for institutions and authority domains (none FULL); 65 oracle gaps, 11 HIGH (m1-negative-oracle-coverage-matrix.md). | evidence/worker-E and worker-F topics.json |
| EG-2 | G0-B-009 wording 'carries these unchanged' for the allow-sets. | Wrong for f1ab: the Registry validates, narrows by intersection and permits deny-all for all five sets; 'carried unchanged' applies only to the frozen r08-v1/S04 overlay (already stated in the matrix section 3). | registry_successor/v2_f1ab.py; Worker F contradiction 1 |
| EG-3 | G0 worker A: decision-level narrowing and deny-all are tested only for `allowed_units`. | Holds at the decision level (V1A-02, V1A-03); refuted at the composer level, where `tests/test_r08v2_f1ab_family.py` covers all five keys (32 empty combinations, shape, bounds, token rule). | Worker E note (a) |
| EG-4 | Inventory treats Runtime effect-time enforcement as the five-set subset guard. | Effect time is executor-subset-of-record, not intersection; `evaluate_with_registry_selection` (the caller-intersect-record code) is imported by no engine module; the effect-time path requires the Registry package to be importable (HOLD `registry_unavailable_for_policy_digest` otherwise), contrary to a docstring. | Worker F contradictions 2 and 8; lead spot-check: the function is referenced only in `engine/registry_f1a_narrowing.py` |
| EG-5 | Component pins quoted as current for tests. | Runtime and Control Plane tests pin Registry `943ab1831e39fadac1eb2a414ae322ccfa09bc6a` (lead spot-check: `PIN` in `tests/test_registry_f1a_narrowing.py:50`), not `317eb76a`. The diff `943ab18..317eb76` was not inspected. | Worker F contradiction 5 |

The erratum does not reopen G0 acceptance. It records why M1 is negative-oracle closure and not 'nothing to do'.
