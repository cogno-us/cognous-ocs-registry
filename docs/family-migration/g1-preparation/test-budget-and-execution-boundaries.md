# Proposed test budget and execution boundaries (deliverable 5)

G0: ACCEPTED AFTER VERIFIED MERGE. G1–G5: NOT AUTHORIZED. V09 independent V07 security review: OPEN. V09 independent V08 Tier 1 qualification: NOT STARTED. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

All figures are **proposals for Architect ratification**, estimated from the recorded sizes (Registry 6207 collected tests; a full local Registry run took about 265 s, roughly 43 ms per test on average). They are not measured budgets.

## 1. Proposed budget

| Item | Proposed cap | Basis |
|---|---|---|
| Candidate oracles | 65 (one per gap; independent author may merge, must account for every gap id) | m1-oracle-register.json |
| New collected cases (parametrised) | ≤ 700 across all packages | OW-1 and OW-4 need per-set × relation grids; the 648-cell baseline grid is sampled today at 93 cells |
| Added Registry CI time | ≤ 60 s | 700 cases × 43 ms ≈ 30 s plus grid overhead |
| Added Runtime CI time | ≤ 180 s | durable-path cases run SQLite `BEGIN IMMEDIATE` transactions; estimate, not measured |
| Vector data | ≤ 300 KB JSON in total | ext-s1-5 vector file as the size reference |
| Mutation runs | ≤ 40 mutants, each run only against its work package's oracles, in disposable copies | section 2 of the independent-oracle specification |
| New dependencies | none (PyNaCl, pydantic and Node already required by existing suites) | avoid new supply-chain surface |
| Paid provider calls | 0 | none are needed |
| External deployment | none | no deployment, no network |

## 2. Execution boundaries

1. **Documentation-only until G1 is authorized.** This preparation changes no test and no code.
2. **Oracle changes touch tests and data only**: no change to `registry_*` production packages, Runtime `engine/` or `host/`, Control Plane `src/`, schemas, frozen contracts, golden vectors or reason-code registries. A needed production change is a finding, not part of M1.
3. **Placement is a decision (PD-7):** Registry `tests/` (smallest, same repository as the contract), a separate oracle package (cleaner independence), or Stack Qualification (already the cross-component home but its F-01 requalification shares builder fixtures). The recommendation is a separate oracle directory owned by the designated independent author, reviewed in the Registry PR.
4. **Deterministic and offline:** no network, no clock dependence beyond injected time, temporary databases only, no writes outside a temporary directory.
5. **Environments:** a prepared environment with PyNaCl, pydantic, Node and the component directory variables is a prerequisite (PR-2); oracles must fail loudly, not skip silently, when a required dependency is missing in CI.
6. **No claim of independence from CI** and no PASS in an independent gate for any builder-authored test.

## 3. Staging

Registry-only packages (OW-1, OW-2, parts of OW-8) can land without Runtime changes and give early value. Packages that need ruling (OW-3, OW-9) wait for PD-1 and PD-4. Packages needing the durable path (OW-4..OW-7) need the prepared environment and the pin decision.
