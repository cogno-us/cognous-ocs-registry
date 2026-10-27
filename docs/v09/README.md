# V09 freeze candidate (preparation only)

**Status: CANDIDATE PREPARED. NOT ACCEPTED. NOT A RELEASE. No tag or version exists.** Authorized scope: V09 freeze-candidate preparation and evidence handover only, under [Plan v1.5](../plans/PROJECT_PLAN-v1.5.md). Independent V07 security review is OPEN, independent V08 Tier 1 is NOT STARTED, Ed25519 #26/#34 is SECURITY-HELD, release, publication and production are on HOLD.

| Document | Purpose |
|---|---|
| [candidate-manifest.json](candidate-manifest.json) | Exact component pins, trees, blob and sha256 digests, PR map, CI runs |
| [component-inventory.md](component-inventory.md) | Components, contracts, dependencies, qualified-commit equivalence |
| [evidence-index.md](evidence-index.md) | V01-V08 evidence with historical and corrected results kept separate |
| [gate-matrix.md](gate-matrix.md) | Gate-by-gate status with the required vocabulary |
| [limitations-and-exclusions.md](limitations-and-exclusions.md) | Findings, limitation register, operational exclusions |
| [readiness-report.md](readiness-report.md) | Seven-dimension readiness assessment and classification |
| [independent-review-handover.md](independent-review-handover.md) | What an independent reviewer receives and must do |
| [../sprint-status.md](../sprint-status.md) | The single live program status |

Documentation and verification metadata only. No component implementation is modified. Checks: `tests/test_v09_candidate_integrity.py` (offline, Registry-resident files and document consistency) and `tools/verify_v09_candidate.py` (all four repositories, git objects only).
