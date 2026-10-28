# G1 preparation (documentation only)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

Prepared 2026-10-28 on top of the merged G0 package (`7208eb6f53f12677f138fe0c64ec48a2e58292b5`). **G1 is not authorized.** Nothing here implements a migration, modifies production code, edits a frozen contract, or claims independent qualification. Builder-created tests are not independent.

| Document | Deliverable |
|---|---|
| [g0-freeze-record.md](g0-freeze-record.md) | G0 merge SHA, frozen location, blob ids, retained counts, AD history (Phase B) |
| [g0-erratum.md](g0-erratum.md) | Additive corrections to frozen G0 statements |
| [m1-existing-contract-crosswalk.md](m1-existing-contract-crosswalk.md) | 1. M1 existing-contract crosswalk |
| [m1-negative-oracle-coverage-matrix.md](m1-negative-oracle-coverage-matrix.md) | 2. M1 negative-oracle coverage matrix |
| [independent-oracle-specification.md](independent-oracle-specification.md), [m1-oracle-register.json](m1-oracle-register.json) | 3. Proposed independent-oracle specification |
| [component-pins-and-test-baselines.md](component-pins-and-test-baselines.md) | 4. Exact pins and test baselines |
| [test-budget-and-execution-boundaries.md](test-budget-and-execution-boundaries.md) | 5. Proposed budget and boundaries |
| [successor-contract-strategy.md](successor-contract-strategy.md) | 6. Successor-contract strategy |
| [open-decisions-and-prerequisites.md](open-decisions-and-prerequisites.md) | 7. Open decisions and prerequisites |
| [g1-authorization-recommendation.md](g1-authorization-recommendation.md) | 8. G1 authorization recommendation |
| `evidence/worker-E`, `evidence/worker-F` | Read-only mapper outputs (topics, test inventories, notes) |

Method and limits: two read-only AI workers mapped twelve M1 topics at the pinned commits; the lead spot-checked the Runtime/Control Plane Registry pin (`943ab18`), the single use of `evaluate_with_registry_selection`, and the `policy_not_subset` cause. No test was executed; collection only. Worker claims not spot-checked are labelled worker findings.
