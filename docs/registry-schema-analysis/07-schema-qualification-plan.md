# 07 Schema validation plan

**Designed, not executed. No test was run for this plan, no result is claimed, and nothing here is qualification evidence.** Expected results are what a conforming successor validator and consumer should produce; they are targets for future work. Refusal class names are the proposed classes in 06 §3 or existing S03/S04 codes where noted. "Optional" and "mandatory" are the ACTIVATION profiles in 05 §4.

## 1. Scenarios

| # | Scenario | Input | Expected result |
|---|---|---|---|
| V1 | Valid record, each proposed family | Well-formed envelope and payload, correct digests, matching applicability | Accept (validation only; not activation) |
| V2 | `s03-v1` records under the existing validator | (a) the checked-in example (`status: proposed`); (b) the active test fixture (status changed in memory and re-digested, as `tests/test_s03_contract.py` does) | (a) REFUSE `status_not_active`; (b) ACCEPT. Outcomes identical to current tests; no existing assertion changes |
| M1 | Malformed JSON | Trailing data, NaN, invalid UTF-8, non-object | `record_malformed` |
| M2 | Missing required field; unknown field; wrong JSON type (bool for integer) | | `record_malformed` |
| U1 | Unsupported envelope version | `envelope_version` unknown | `envelope_unsupported` |
| U2 | Unsupported family or family contract version | | `family_unsupported` |
| U3 | Unsupported canonicalization id | | `canonicalization_unsupported` |
| U4 | Newer record version than consumer supports | | refused; never read best-effort |
| K1 | Duplicate keys at any depth | | `record_malformed` |
| D1 | `data_digest` wrong | | `digest_mismatch` |
| D2 | `record_digest` wrong | | `digest_mismatch` |
| D3 | Data changed and both digests recomputed | record bytes only; selection bytes and pin unchanged | Accept at record level (integrity only, limitation L1); at selection level `record_not_in_selection`, because the recomputed `record_digest` differs from the selection entry. The selection bytes and pin are unchanged, so this is not `selection_unauthenticated` |
| S1 | Selection bytes changed (or wrong pin supplied), so the selection digest does not match the pin | | `selection_unauthenticated` (optional: not applied; mandatory: deny) |
| S2 | Selection and record merged in one PR with no separate pin | | No pin exists, so not applied; merging is not authorization (T3) |
| S3 | Record absent from selection, or digest differs | | `record_not_in_selection` |
| A1 | Incorrect consumer namespace (for example a record targeted at another system) | | `consumer_namespace_mismatch` |
| A2 | Component source blob differs from the trusted source | | `not_applicable` / `source_mismatch` (existing) |
| E1 | Unknown evaluator revision | | `evaluator_revision_unknown` |
| E2 | Evaluator source on disk differs from registered blob | | refused (existing `runtime_source_unverified` class); in-process code replacement remains undetected (T5) |
| X1 | Expired selection or record | trusted clock past `valid_until` / `not_after` | `record_expired` |
| X2 | Not yet effective | clock before `not_before` | `record_not_yet_effective` |
| X3 | Superseded record selected | selection names a version that a later selected version supersedes | `version_not_latest` / `supersession_invalid` (existing) |
| X4 | Broken supersession chain | digest of predecessor wrong | `supersession_invalid` |
| C1 | Conflicting requirements | two selected records constrain one field with no ruled composition | `requirement_conflict` or `composition_unsupported`; never a silent pick |
| C2 | F7 triple violates ordering | `provider_horizon > escalation_deadline`, or `escalation_deadline >= dedupe_ttl` | `record_invalid` |
| C3 | F7 destination lacks `dedupe-ttl/0.1` or TTL below profile | | `dependency_missing` |
| C4 | Unsupported composition | family with no ruled direction (for example F4 `clock_tolerance_seconds`) | `composition_unsupported` |
| W1 | Registry value is a superset of the caller's (for example a broader allow-list) | | Successful non-widening case: effective value equals the caller's by intersection; no refusal (cf. `tests/test_s04_overlay.py`) |
| W1b | Defect injection: a composition implementation returns a value broader than the caller's | test double | post-composition assertion fails: `widening_attempt` (detection of a defect, not a data case) |
| W2 | Payload attempts to relax a toggle (`allow_synthetic_resolver`) or add an action class | | `record_malformed` (unknown field) or `requirement_conflict` |
| W3 | Record claims `approved`, `active` or `mandatory` | | `record_malformed` (unknown field); has no effect |
| W4 | Record carries an expression or script field | | `record_malformed` |
| H1 | Changed conditions: caller policy tightened after the record was authored | | effective value is the tighter of the two |
| H2 | Changed conditions: caller policy loosened | | effective value follows the record's narrower value; never above the caller's |
| O1 | Registry failure under optional profile | any refusal above | Caller policy unchanged; result says "overlay not applied", not "denied" |
| O2 | Registry failure under mandatory profile | any refusal above | Consumer denies; this profile is not authorized today |
| O3 | Empty effective set | intersection empty | Deny-all for that field; cannot be authored as a record (non-empty lists), so reached only by intersection |
| T1 | S03/S04 compatibility | existing S03 cases (P, N, M, X, O, L, I, W) and S04 cases | Same results as on `main`; no existing test changes |
| T2 | S05 harness | existing oracle and expectations | Unchanged; not reused as evidence for a successor |
| I1 | ISS/OCS isolation: ISS-namespaced record or selection offered to the OCS consumer | | `consumer_namespace_mismatch` |
| I2 | No shared state | OCS consumer attempts to read an ISS selection store or pin | No such path exists; test asserts the consumer API has no cross-system input |
| I3 | Reason-vocabulary record offered as policy | | refused; vocabulary records carry no behavior |

## 2. Evidence required before any claim

- A differential oracle written by someone other than the validator author, for any family beyond F1a, following the S05 method (finite value universe, frozen expectations, no imports from code under test).
- Negative controls for every refusal class.
- For F4, F5 and F7: evidence from the real Control Plane evaluators, which the S05 harness does not cover (T11).
- Independent review proportionate to Tier 1 (CA14, CA18). Copilot review is technical review only (T10).

## 3. What this plan does not do

It does not execute tests, produce a result table, select a pin, activate a record, define a Runtime integration or claim qualification.
