# 07 Schema validation plan

(File name kept as listed in the brief's deliverables; this is a validation plan, not a qualification plan.)

**Designed, not executed. No test was run for this plan, no result is claimed, and nothing here is qualification evidence.** Expected results are targets for a conforming successor validator and consumer. Each scenario assumes a single fault and has exactly one expected class; check order is in 06 §3. Rows marked **[cond D4]** depend on unresolved rulings (08 D1, D4, W3-063) and are not expectations until those are made. "Optional" and "mandatory" are the host's ACTIVATION profiles (05 §4). Classes are the existing S03/S04 codes or the proposed classes in 06 §3.

## 1. Record-level scenarios

| # | Scenario | Input | Expected |
|---|---|---|---|
| V1 | Valid successor record, each family | Well-formed, correct digests, matching applicability | Accept (validation only; not activation) |
| V2a | `s03-v1` checked-in example | status `proposed` | REFUSE `status_not_active` (unchanged) |
| V2b | `s03-v1` active test fixture | status set to `active` in memory and re-digested, as `tests/test_s03_contract.py` does | ACCEPT (unchanged) |
| V3 | `s03-v1` record with status `superseded` or `withdrawn` offered via a selection | pinned selection names it | REFUSE `status_not_active`; selection cannot override the frozen gate |
| V4 | `record_missing`, `context_missing`, null record | | existing codes |
| M1 | Not strict JSON (trailing data, NaN, invalid UTF-8, lone surrogate), non-object | | `record_malformed` |
| M2 | Missing required field, unknown field, wrong JSON type (bool for integer) | | `record_malformed` |
| M3 | Payload field referencing an ISS authority, an expression or a script | | `record_malformed` |
| M4 | Record claims `approved`, `active` or `mandatory` | | `record_malformed` (unknown field) |
| K1 | Duplicate keys at any depth | | `record_malformed` |
| I1 | `non_authorizing` false | | `record_invalid` |
| I2 | Digest not `sha256:` plus 64 lowercase hex | | `record_invalid` |
| D1 | `data_digest` wrong | | `digest_mismatch` |
| D2 | `record_digest` wrong | | `digest_mismatch` |
| D3 | Known canonicalization id, but digest computed with another form | | `digest_mismatch` |
| U1 | Unknown `envelope_version` | | `envelope_unsupported` |
| U2 | Unknown `family` or family `contract_version` | | `family_unsupported` |
| U3 | Unknown canonicalization id | | `canonicalization_unsupported` |
| U4 | `family` inconsistent with `evaluator.supplies` | | `evaluator_unsupported` (existing S03 code, preserved) |
| E1 | Evaluator id/binding/supplies mismatch (S04 case N13) | | `evaluator_unsupported` |
| E2 | Evaluator revision not in the host-trusted registry | | `evaluator_revision_unknown` |
| E3 | Evaluator source on disk differs from the trusted source | | `runtime_source_unverified` (existing); in-process replacement stays undetected (T5) |
| A1 | Wrong `target_consumer` | | `consumer_namespace_mismatch` |
| A2 | Component blob id differs | | `not_applicable` |
| A3 | Blob id matches, source sha256 differs | | `source_mismatch` |
| A4 | `consumer_profile_id` mismatch | | `not_applicable` (successor extension of the existing class) |
| A5 | Record's `consumer_profile_id` names a profile other than the host's active profile; record tries to choose optional or mandatory | | no effect on the host profile; mismatch is `not_applicable` |
| X4 | Supersession broken: version 1 with non-null `supersedes`, or version n>1 not naming the same id and version n-1 | | `supersession_invalid` (the predecessor's digest is not compared by S03; 06 §2.7) |
| P1 | F1c numeric payload: bool, NaN, zero, negative, over cap, binary64 edge | | `record_invalid` (or `record_malformed` for bool/NaN by type) **[cond D6]** |
| P2 | F7 record triple internally disordered (`provider_horizon > escalation_deadline`, or `escalation_deadline >= dedupe_ttl`) | | `record_invalid` **[cond D4]** |

## 2. Selection-level scenarios

| # | Scenario | Input | Expected |
|---|---|---|---|
| S1 | Selection bytes changed (or wrong pin) so digest differs from pin | | `selection_pin_mismatch` (successor name; the existing S04 `manifest_pin_mismatch` is not aliased or edited) |
| S2 | No pin supplied by trusted invocation | merging selection and record in one PR supplies none | `trust_config_invalid` (existing); merging is not authorization (T3) |
| S3 | Selection malformed: malformed JSON, duplicate keys, unknown field, unsupported selection version, oversize | | `manifest_invalid` family (existing) |
| S4 | Selection with two entries for one record id | | `manifest_invalid` |
| S5 | Selection entry path traversal or a path not matching the record id **[successor path-binding check; S04 does not bind paths today]** | | `manifest_invalid` |
| S6 | Selection `target_consumer` mismatch | | `consumer_namespace_mismatch` |
| S7 | Record absent from selection or `record_digest` differs from entry | | `record_not_in_selection` |
| S8 | Record bytes differ from entry `file_sha256` | | `record_file_mismatch` (existing) |
| S9 | Data changed and both digests recomputed in the record only | selection and pin unchanged | record validates (integrity only, L1); selection level: `record_not_in_selection` |
| S10 | `valid_from` later than `valid_until`, or malformed timestamp | | `manifest_invalid` |
| S11 | Selection expired | trusted clock past `valid_until` | `selection_expired` (optional: caller policy stands; mandatory: deny) |
| S12 | Selection not yet effective | clock before `valid_from` | `selection_not_yet_effective` |
| S13 | Runtime source blob changed after the selection was authored | | `manifest_runtime_mismatch` (existing) |

Rollback to an older pinned selection is undetectable under pin-only trust. It is recorded as a **limitation** next to L1 and T5, not as a scenario. Likewise the S04 consumer takes `latest_known_version` from the selection entry, so it cannot detect that a newer record version exists; supersession is enforced at selection-authoring time by review, not by the consumer.

## 3. Composition and dependency scenarios

| # | Scenario | Input | Expected |
|---|---|---|---|
| C1 | Two selected records constrain one field with no ruled composition | | `requirement_conflict` |
| C1b | Two families both claim `max_status_age_seconds` (F4 and F5) | | `requirement_conflict`; single field owner is F5 (04) |
| C2 | Effective F7 triple (after composing with the caller's) violates the ordering | | `effective_value_invalid` **[cond D4]** |
| C3 | F7 destination lacks `dedupe-ttl/0.1` or its TTL is below the effective TTL; evidence must come from the host's destination binding, not from the record, the selection or a destination self-assertion | | `dependency_missing` **[cond D4]** |
| C3b | Composition raises the effective TTL above the destination's declared TTL | | `dependency_missing` (re-check after composition) **[cond D4]** |
| C4 | Family with no ruled direction (for example F4 tolerance field) | | `composition_unsupported` **[cond D4]** |
| W1 | Registry value is a superset of the caller's | | successful clamp; effective equals the caller's by intersection; no refusal (cf. `tests/test_s04_overlay.py`) |
| W1b | Defect injection: a composition implementation returns a broader value | test double | `widening_attempt` (successor mapping; S04 surfaces the same defect as `consumer_error`) |
| W2 | Payload tries to relax a toggle (`allow_synthetic_resolver`) or add an undeclared action class | | `relaxation_unsupported` (or `record_malformed` for an unknown field) |
| W2b | F5 payload contains an `irreversible` field (the proposed payload excludes it) | | `record_malformed` (unknown field, before any composition check) |
| W2c-1 | Host-class coherence (separate fault injection, not a payload case): the host class declares `reversibility` (for example `reversible_at_cost`) and a composition tightening would set `irreversible` true alone | test double against the host class | host class raises `irreversible_flag_mismatch` (the legacy boolean contradicts the `reversibility` enum) |
| W2c-2 | Host class has `reads_protected_data` true and declares a `reversibility` other than `irreversible`; `irreversible` absent or equal to the value derived from the enum, so the flag check does not fire first | test double | `protected_read_not_irreversible` (a protected read is paired with an insufficient reversibility classification) |
| W2c-3 | Host class has `counterparty_observable` false and declares a `reversibility` other than `irreversible`; same precondition | test double | `unobservable_not_strict` (an unobservable counterparty requires the strictest value) |
| W2c-4 | Host class declares no `reversibility` but has `reads_protected_data` true or `counterparty_observable` false (the enum then defaults to `irreversible`) and a composition sets `irreversible` false | test double | `irreversible_flag_mismatch` |

For W2c-1 to W2c-4 the three host codes are distinct and are raised by `check_class_members` in `src/agent_control_plane/reversibility.py` as `ValueError` messages whose prefix is the code. The checks run in this order: `reversibility_member_mismatch` and enum validity first, then `irreversible_flag_mismatch`, then `protected_read_not_irreversible`, then `unobservable_not_strict` (lines 130-160). The file is identical at Control Plane `0a41faa9` and at the pinned `7a4bcd40b3b49e61ff3c294dcca53b52f460b22c` [V, `git diff` empty]. A successor consumer would map every one of these to `relaxation_unsupported` while retaining the host code as evidence. W2b (the payload containing an `irreversible` field) remains the separate malformed-payload scenario.
| H1 | Caller policy tightened after authoring (for example record `{b,c}`, caller `{a,b,c}` becomes `{a,b}`) | | effective is the intersection (minimum for ceilings) of the new caller value and the record: `{b}`, not the caller's `{a,b}`. Intersection/min families only; F7 also requires C2 |
| H2 | Caller policy loosened or replaced by an unrelated set | | effective is again the intersection/minimum of the new caller value and the record; never above the caller's and never dropping the record's constraint |
| H3 | Destination capability changed after selection | | `dependency_missing` **[cond D4]** |

## 4. Activation and isolation scenarios

| # | Scenario | Input | Expected |
|---|---|---|---|
| O1 | Any refusal under the optional profile | | caller policy unchanged; "overlay not applied", not "denied" |
| O2 | Any refusal under the mandatory profile | | consumer denies; permitted as an architectural design capability (D7 ruling), not authorized for activation; required-policy failure must not fall back to a broader caller policy |
| O3 | Empty effective set | intersection empty | deny-all for that field; cannot be authored as a record (non-empty lists) |
| O4 | Expiry under the optional profile | | reverts to the caller's possibly broader policy (T7 by time); documented limit |
| T1 | S03/S04 compatibility | existing S03 and S04 cases | same results as on `main`; no existing test changes |
| T2 | S05 harness | existing oracle and expectations | unchanged; not evidence for a successor |
| N1 | Namespace isolation **[cond ISS Q4]** | record or selection from another system namespace | `consumer_namespace_mismatch` |
| N2 | No cross-system input **[cond ISS Q3]** | consumer API | no parameter or path reads another system's selection store or pin |
| N3 | Reason-vocabulary record offered as policy | | refused; vocabulary records carry no behavior |

## 5. Evidence required before any claim

- A differential oracle written by someone other than the validator author for every family beyond F1a, following the S05 method (finite value universe, frozen expectations, no imports from code under test).
- Negative controls for every class above.
- For F4, F5 and F7, evidence from the real Control Plane evaluators, which the S05 harness does not cover (T11).
- Independent review proportionate to Tier 1 (CA14, CA18). Copilot review is technical review only (T10).

## 6. What this plan does not do

It does not execute tests, produce results, select a pin, activate a record, define a Runtime integration or claim qualification.
