# S03 — Minimal registry contract: LocalExecutionPolicy allow-lists

Non-authorizing, builder-side, unqualified. Release, publication and production HOLD. Contract only: no registry, no record store or loader, no Runtime change, no catalogue import, no S04.

- Plan: OCS-REG-PLAN v1.1, S03 section: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`)
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
- Authorization: [decisions/2026-10-24-s03-authorization.md](decisions/2026-10-24-s03-authorization.md). Scope inputs: [s02-inventory.md](s02-inventory.md) section 6.
- Source pin: Execution Runtime `ec728da6dc301a664b331ac8986afd6e850a1273`, `engine/safe_executor.py`, git blob `2fc880dae37eac76e5074533435740ce0684209d`, sha256 `940e781934542a7acd7bbe2f6833f9d329325d94b49425afd9d2bedcf23c5b68` (verified in this PR against `baseline/`).
- Materially applicable CA articles: CA05, CA12, CA14, CA18 (as cited in S02); Tier 1 subject matter (pre-dispatch admission to an effect). A narrow contract does not lower the assurance obligation.

## 1. What this contract covers

It defines one record type, `local-execution-allowlist`, that supplies exactly three values to the existing evaluator `LocalExecutionPolicy.check`: `allowed_units`, `allowed_adapters`, `allowed_actions` (`safe_executor.py:362-365`, checked at `:417-418`, `:419-420`, `:423-424`). The S02 inventory cites `:418-424`; the adapter check begins at line 417.

It reuses existing concepts rather than adding new ones: the evaluator, its field names, its frozenset-of-non-empty-strings value type and its exact-membership semantics are the baseline's. A record is data for that evaluator. It is never a grant, approval, authority record or enforcement decision.

## 2. Invariants this contract does not touch (kept in code)

Not supplied by any record, and unchanged by S03: `allowed_institutions`, `allowed_authority_domains`, `allowed_target_prefixes`, `target_match`, `max_amount`, `max_effects`; the fixed check order (institution, authority domain, adapter, action, target, unit, amount, one-effect rule, effect-count); the reason texts; `__post_init__` fail-closed validation; strict number validators; target well-formedness; and everything upstream of `check` (S02 section 4).

## 3. Record shape (contract_version `s03-v1`)

All fields are required. Unknown fields are refused at every level. Machine-readable form: [`registry_contract/local_execution_allowlist.schema.json`](../registry_contract/local_execution_allowlist.schema.json); the schema is documentation, and a test checks that its field names match the validator's.

| Field | Type / rule |
|---|---|
| `record_type` | string, exactly `local-execution-allowlist` |
| `contract_version` | string, exactly `s03-v1` |
| `record_id` | stable identity; string matching `^[a-z0-9][a-z0-9._-]{2,63}$`; never reused for a different family |
| `record_version` | integer >= 1; one record_id has strictly increasing versions |
| `status` | `proposed`, `active`, `superseded` or `withdrawn`; only `active` can be accepted |
| `non_authorizing` | boolean, exactly `true` |
| `supersedes` | `null` iff `record_version` is 1; otherwise `{record_id, record_version, record_digest}` naming the same `record_id` at `record_version - 1` |
| `source` | `{repository, commit, path, blob_id, sha256, field_lines, check_lines}`: where the values were taken from. `commit` and `blob_id` are 40 lowercase hex; `sha256` is `sha256:` plus 64 lowercase hex |
| `applicability` | `{runtime_source_blob_id}`: the evaluator source revision (40 lowercase hex) these values may apply to. Exact match only; no ranges |
| `evaluator` | `{evaluator_id, binding, supplies}`. v1 registers one binding: `engine.safe_executor.LocalExecutionPolicy.check`, binding `registered-code-reference`, supplies exactly `["allowed_actions","allowed_adapters","allowed_units"]`. No scripts, expressions or other evaluator ids |
| `data` | `{allowed_units, allowed_adapters, allowed_actions}`, each a non-empty, duplicate-free, ascending-sorted array of strings, at most 256 entries, each 1 to 128 characters, no character in Unicode categories C* or Z*, and no `*` |
| `data_digest` | `sha256:` plus lowercase hex of the canonical form of `data` |
| `provenance` | `{decision_ref, authored_at, authored_by}`: `decision_ref` 1-200 characters, `authored_at` `YYYY-MM-DDTHH:MM:SSZ`, `authored_by` 1-120 characters |
| `record_digest` | `sha256:` plus lowercase hex of the canonical form of the whole record without `record_digest` |

Canonical form: UTF-8 bytes of `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.

Entries are opaque identifiers compared by exact string equality, as the baseline's frozenset membership does. There is no wildcard, glob, regex, case folding or normalization. The record rules are deliberately stricter than the constructor in three ways (non-empty lists, character restrictions, size bounds). Each is refusal-only: a stricter rule can refuse a record the constructor would have accepted and can never make admission wider. S05 equivalence work must account for this.

Semantics of the digests: they provide integrity, not authenticity. A record altered and re-digested is not detected (acceptance case L1 pins this). CA18 requires authenticated policy data. **S03 provides no authentication.** No record may be activated or consumed by Runtime until the operator decides how records are authenticated; this is the main open item for S04.

## 4. Deterministic failure treatment

The validator takes a record (or strict JSON text) and a verifier context, and returns exactly one outcome: `ACCEPT`, or `REFUSE` with one reason code from a closed set. Checks run in this fixed order and the first failure wins. The verifier context is `{runtime_source_blob_id, runtime_source_sha256, latest_known_version}`, supplied by the consumer from the running evaluator and its own knowledge of the record, never read from the record.

| # | Reason code | Refused when |
|---|---|---|
| 1 | `record_missing` | no record was supplied (`None`) |
| 2 | `context_missing` | context absent, not an object, or a required key is absent or the wrong type |
| 3 | `record_malformed` | not strict JSON (duplicate keys, NaN or Infinity, trailing data, non-UTF-8), not an object, a required field absent, an unknown field present, or a field of the wrong JSON type (a bool is not an integer) |
| 4 | `contract_unsupported` | `record_type` or `contract_version` is not the supported value |
| 5 | `record_invalid` | a value rule in section 3 is violated (pattern, range, emptiness, duplicates, order, size, characters, `non_authorizing` not true) |
| 6 | `digest_mismatch` | `data_digest` or `record_digest` does not match the recomputed value |
| 7 | `supersession_invalid` | `supersedes` is inconsistent with `record_id` and `record_version` |
| 8 | `status_not_active` | `status` is not `active` |
| 9 | `version_not_latest` | `record_version` differs from `latest_known_version` |
| 10 | `evaluator_unsupported` | `evaluator` is not exactly the one registered binding and supply list |
| 11 | `not_applicable` | `applicability.runtime_source_blob_id` differs from the context's |
| 12 | `source_mismatch` | `source.blob_id` differs from `applicability.runtime_source_blob_id`, or `source.sha256` differs from the context's `runtime_source_sha256` |

Refusal treatment for the eventual consumer: any `REFUSE` means no registry data is produced. It never falls back to a permissive default, never ignores a field, and never widens. Whether the caller-constructed policy remains the source of truth after a refusal is an S04 decision; S03 only fixes that refusal cannot widen admission.

Non-widening rule (CR-NW), for S04 and tested here as a pure function: during any transition, each registry-supplied set must be a subset of the corresponding explicitly caller-constructed set. `widening_violations(data, caller)` returns the field names where it is not.

Not provided by S03: record storage, lookup, discovery, loading, caching, activation, revocation, signing or key management, clock-based expiry, tenant or institution scoping, any other family, and any change to `LocalExecutionPolicy`.

## 5. Acceptance cases (defined before the validator was written)

These were committed with the tests before the validator existed (first commit: tests collected and failing for want of the module). Case IDs appear in `tests/test_s03_contract.py` test names.

| ID | Case | Expected |
|---|---|---|
| P1 | valid active record, matching context | ACCEPT |
| P2 | valid v2 record superseding v1, `latest_known_version` 2 | ACCEPT |
| P3 | same record parsed from JSON text with permuted key order | ACCEPT, identical digests |
| P4 | multi-entry sorted lists | ACCEPT |
| P5 | validating twice, and the input is not mutated | identical outcome, input unchanged |
| P6 | the committed example record as shipped (`proposed`) | REFUSE `status_not_active`; ACCEPT only after an in-memory status change and re-digest |
| N1 | status `proposed`, `superseded`, `withdrawn` | `status_not_active` |
| N2 | `data` altered without re-digest | `digest_mismatch` |
| N3 | `record_digest` altered | `digest_mismatch` |
| N4 | unknown evaluator id; wrong binding | `evaluator_unsupported` |
| N5 | `supplies` adds a field such as `max_amount`, or omits one | `evaluator_unsupported` |
| N6 | applicability blob differs from context | `not_applicable` |
| N7 | source sha256 differs from context; source blob differs from applicability | `source_mismatch` |
| N8 | record v1 while latest known is 2; record v3 while latest known is 2 | `version_not_latest` |
| N9 | `non_authorizing` false | `record_invalid` |
| N10 | v1 with `supersedes`; v2 without; wrong id; wrong version | `supersession_invalid` |
| N11 | wildcard entry; whitespace entry; zero-width entry; empty string entry | `record_invalid` |
| N12 | empty list; duplicate entries; unsorted entries; over 256 entries; entry over 128 characters | `record_invalid` |
| N13 | bad digest format (uppercase hex, missing prefix, wrong length); bad `record_id`; bad `authored_at`; version 0 | `record_invalid` |
| M1 | record is a list, string, number or boolean | `record_malformed` |
| M2 | each required top-level field absent in turn | `record_malformed` |
| M3 | unknown field at top level and in each nested object | `record_malformed` |
| M4 | wrong JSON types: string for a list, null, number entry, string version, bool version | `record_malformed` |
| M5 | JSON text with duplicate keys, NaN, trailing data, empty text, invalid UTF-8 | `record_malformed` |
| M6 | other `contract_version` or `record_type` | `contract_unsupported` |
| X1 | no record | `record_missing` |
| X2 | context missing, wrong type, key absent | `context_missing` |
| X3 | empty object as record | `record_malformed` |
| O1 | records with two defects return the earlier check's code (pairs across the order in section 4) | as ordered |
| L1 | limitation: data changed and both digests recomputed | ACCEPT (integrity is not authenticity) |
| I1 | baseline pin: blob id, sha256, and the field and check lines in `baseline/` match this contract | holds |
| I2 | `check` raises its reasons in the baseline order | holds |
| I3 | the baseline constructor still rejects non-frozenset or empty-string values for the three fields | holds |
| I4 | dataclass fields equal supplied plus not-supplied sets | holds |
| I5 | no `registry_contract` module imports `engine` or opens files | holds |
| I6 | schema field names equal validator field names | holds |
| W1 | non-widening: subset and equal pass; any extra entry is reported by field | as stated |

## 6. Limitations and no-claims

AI-assisted builder work; Copilot review is technical code review, not independent qualification or certification. The contract has not been exercised against Runtime behavior (no consumer exists, by design), so behavioral equivalence is untested and belongs to S05. Records are unauthenticated (section 3). The Control Plane, other F-families, and the unresolved S02 classifications (32, including the 60-versus-300 observation-window relationship) are untouched and stay unresolved.

## 7. Proposed S04 boundary (proposal only; S04 not authorized)

Needs a new operator decision. Open items it must settle: record authentication (CA18); who supplies the verifier context; whether the caller-constructed policy remains authoritative on refusal; where a first real record is authored and reviewed; the independent-review level Tier 1 requires.
