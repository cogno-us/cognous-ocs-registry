# Rules omitted from the current 97-group inventory

> Registry release, publication and production remain on HOLD. This is an architecture and eligibility audit; it is NOT independent Tier 1 qualification. No production code, frozen G0/S02 evidence, migration plan or backlog is modified by this audit.

Rules that are configurable (or pending a decision) and have no counterpart in the 116-record / 97-group G0 inventory: **10**. **Newly discovered Registry-eligible rules among them: 1.**

| Rule | Disposition | Configurable | Origin | Why it is not Registry-manageable / what is pending |
|---|---|---|---|---|
| LR-F5-CLASS-STATUS-AGE/mechanism | RETAIN-IN-CODE | YES | HISTORICAL | LEAD-OVERRIDE: Mechanism rows separated from the eligible F5 parameter, as done for 13 other rows.  |
| NEW:destination-database-name | PROVIDER-OR-HOST-OWNED | YES | HISTORICAL | UNANIMOUS WORKER ROWS  |
| NEW:evidence-registry-governance-quorum | OUT-OF-SCOPE | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:evidence-registry-jwt-defaults | PROVIDER-OR-HOST-OWNED | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:genfence-refusal-budget | OUT-OF-SCOPE | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:hub-context-journal-max-uncommitted | CALLER-OR-ISSUER-OWNED | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:hub-operational-state-contract-thresholds | CALLER-OR-ISSUER-OWNED | YES | REPO-COVERAGE | REPO-COVERAGE WORKER  |
| NEW:revocation-writer-enable-flags | PROVIDER-OR-HOST-OWNED | YES | HISTORICAL | UNANIMOUS WORKER ROWS  |
| NEW:sqlite-busy-timeout | PROVIDER-OR-HOST-OWNED | YES | HISTORICAL | UNANIMOUS WORKER ROWS  |
| NEW:terminal-revocation-marker | REGISTRY-ELIGIBLE | YES | HISTORICAL | LEAD-OVERRIDE: Pass 2 (Worker G-01 proposal, verified by the lead): the profile is an opt-in safeguard (runtime_authority.py:182-191,214) with a single consumer (bounded.py:2390-2392). Its only varia… |

Also omitted from the *historical-row* populations of S02 because it was not read: Action Manifest, Governed Exchange, Institutional Governance, Evidence Pack, Replay Bundle, ODES, Evidence Registry, Evidence Attestation, hub, verifier and Stack Orchestrator sources. They were swept by the repository-coverage workers (see `worker-evidence/I1.json`, `I2.json`, `I3.json`); none yielded a new Registry-eligible rule.

