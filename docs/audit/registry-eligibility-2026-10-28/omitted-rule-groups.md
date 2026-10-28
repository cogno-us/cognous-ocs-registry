# Rules omitted from the current 97-group inventory

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

Rules that are configurable (or pending a decision) and have no counterpart in the 116-record / 97-group G0 inventory: **9**. **Newly discovered Registry-eligible rules among them: 0.**

| Rule | Disposition | Configurable | Origin | Why it is not Registry-manageable / what is pending |
|---|---|---|---|---|
| NEW:destination-database-name | PROVIDER-OR-HOST-OWNED | YES | HISTORICAL | UNANIMOUS WORKER ROWS  |
| NEW:evidence-registry-governance-quorum | OUT-OF-SCOPE | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:evidence-registry-jwt-defaults | PROVIDER-OR-HOST-OWNED | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:genfence-refusal-budget | OUT-OF-SCOPE | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:hub-context-journal-max-uncommitted | CALLER-OR-ISSUER-OWNED | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:hub-operational-state-contract-thresholds | CALLER-OR-ISSUER-OWNED | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:operation-identity-enablement | UNRESOLVED | UNKNOWN | HISTORICAL | UNANIMOUS WORKER ROWS Is enabling operation-identity a governed policy narrowing, or a host protocol-profile/wiring choice that must be set jointly in Runtime ctor, CP profile and destination capabil… |
| NEW:revocation-writer-enable-flags | PROVIDER-OR-HOST-OWNED | YES | HISTORICAL | UNANIMOUS WORKER ROWS  |
| NEW:sqlite-busy-timeout | PROVIDER-OR-HOST-OWNED | YES | HISTORICAL | UNANIMOUS WORKER ROWS  |

Also omitted from the *historical-row* populations of S02 because it was not read: Action Manifest, Governed Exchange, Institutional Governance, Evidence Pack, Replay Bundle, ODES, Evidence Registry, Evidence Attestation, hub, verifier and Stack Orchestrator sources. They were swept by the repository-coverage workers (see `worker-evidence/I1.json`, `I2.json`, `I3.json`); none yielded a new Registry-eligible rule.

