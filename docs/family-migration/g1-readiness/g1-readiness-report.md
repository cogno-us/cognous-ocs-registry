# G1 readiness report

Non-authorizing, documentation only. No oracle is implemented, executed or independent; nothing here is qualified or certified. Release, publication and production are not authorized.

G0: ACCEPTED AND FROZEN. G1: PREPARATION ONLY. G1 CONTRACT/ORACLE IMPLEMENTATION: NOT AUTHORIZED. G2–G5: NOT AUTHORIZED. V09 independent V07 review: OPEN. V09 independent V08 Tier 1: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## Summary

- PR #51 merged: `2afbd8cd119751842b5df824229726aeb0e4a863` (head `00e9bb63e0ad32c7900713050e47b5df22279152` unchanged, exact-head CI green).
- Registry delta `943ab18..317eb76a` contains **no code change**; the seven code trees are byte-identical at five commits. It adds Amendment 3 (effective), Amendment 4 (DRAFT), V09 candidate documents, the plan and four tests. The Phase B end SHA typed in the directive does not exist; `317eb76a…89b4aef987d` was used.
- Environment: two hash-locked profiles reproduce collection of all eight previously uncollected files (Runtime 293, SQ 70) and all 6207 Registry tests. No test was executed. Blockers recorded: Control Plane needs pydantic >= 2.12 (Profile X), one hard-coded commit assertion (Registry `943ab18`), one hard-coded worktree path, Runtime CI skips the six Registry-gated modules.
- Eight-file closure complete (PASS for location, reading, collection; NOT RUN for execution). 4 register gaps were narrowed by reading and 6 confirmed open.
- PR-4: the Runtime F-01 suite does **not** exercise the pin path. Pin plus containment is shown per set for allowed_actions and allowed_units only; the other three sets only in one aggregated case.
- Specification: 65 oracles in nine families; SPEC-READY 41, CHARACTERISATION-ONLY 16, BLOCKED-SEMANTICS (PD-1) 7, CLAIM-CHECK 1.
- HIGH gaps (11): ready for ratification M1-E-06, M1-E-10, M1-E-21, M1-E-26, M1-E-30, M1-F-06, M1-F-07, M1-F-26 (E-21 and F-06 and F-07 carry restricted sub-expectations); blocked by PD-1 M1-E-12, M1-E-34, M1-F-08.

## Outstanding Architect decisions

PD-3, PD-7, PD-8, PD-9 ratification; PD-5 confirmation; **PD-6 designation of the independent oracle author and reviewer (blocks authoring of every oracle)**; the separate binding contract for PD-1; the corrected Phase B end SHA; profile choice per suite; AD-04 to AD-24.

## Recommendation

The package is ready for Architect review as an oracle **specification**. No oracle should be authored or run until PD-6 is decided and the per-suite profile and pin baseline are ratified. G1 contract development and oracle implementation remain NOT AUTHORIZED; this report is not a request for that authorization and does not claim clearance, certification or readiness for production.
