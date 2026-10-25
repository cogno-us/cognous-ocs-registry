# S05 — Frozen comparison specification (written and committed before the harness)

Non-authorizing, builder-side, unqualified. Release, publication and production HOLD.

- Plan: OCS-REG-PLAN v1.1, S05 section: https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.1.md (blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`)
- Constitution (pinned): https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md
- Authorization: [decisions/2026-10-24-s05-authorization.md](decisions/2026-10-24-s05-authorization.md). Subject under test: S04 consumer (`registry_consumer/`) over the frozen S03 validator and the unchanged baseline Runtime.

## 1. Question and method

Does the registry-backed `LocalExecutionPolicy` preserve the behavior and safety boundaries of the historical hardcoded policy, for the three fields `allowed_units`, `allowed_adapters`, `allowed_actions`?

Two paths run on identical inputs:
- **Historical reference:** the baseline `engine.safe_executor.LocalExecutionPolicy`, constructed directly with the allow-lists under test, with every other restriction fixed and allowing.
- **Registry-backed path:** a caller-constructed policy passed through `registry_consumer.apply_registry_overlay` with a pinned manifest and a record, then `check` (and, for end-to-end cases, the baseline `LocalDestinationExecutor`).

## 2. Independence of the oracle (item 6 of the authorization)

Expected outcomes are fixed before the harness exists in two frozen files, whose git blob ids are:

| File | Git blob id |
|---|---|
| `tests/s05_expectations.json` | `37a68275c8c2b932d7a47adac43c05ec802d0081` |
| `tests/s05_oracle.py` | `503851c4ffa989a213c7dfb4d8957d0d540cb73c` |

The harness pins both. The oracle is pure Python and imports nothing from the Runtime, the S03 validator or the S04 consumer. It encodes only the documented rule: `effective = caller ∩ registry` per field, and the first failing membership test in the fixed order adapter, action, unit decides the refusal, using the historical reason texts. The grid operands are enumerated by the oracle itself, not by the code under test.

The oracle is a reading of the historical source and the S04 authorization, and the harness also compares it against the historical `LocalExecutionPolicy` itself. Disagreement between the oracle and the historical policy would be a finding about the oracle or the reading, kept and reported, not adjusted away.

Refusal, authentication, applicability and source expectations come from the S03 contract section 4 and the S04 implementation record section 4, written as an explicit table (`refusal_cases`) before the harness.

**Amendment rule.** An expected outcome or oracle change is permitted only as a separate, dated, recorded amendment that states the reason and keeps the original. It is never made to obtain a pass. A failing case stays failing in the raw results.

## 3. Cases (counts are frozen)

| Group | Content | Count |
|---|---|---|
| G1 | exhaustive: 2 universe values per field, 64 caller policies (all subsets incl. empty) × 27 non-empty registry records × 27 operations (universe plus one outside value per field) | 1,728 pairs, 46,656 comparisons |
| G2 | per-field exhaustive: 3 universe values, 8 caller subsets × 7 non-empty registry subsets × 4 operations, other fields fully allowing; for each of the 3 fields | 168 pairs, 672 comparisons |
| R | refusal cases R01-R34 (absent, malformed, unsupported, tampered, unauthenticated, stale, inapplicable, source mismatch, invalid selection, bad trust configuration, containment) | 34 |
| E | representation classes E01-E20 and representable boundaries B01-B05, each applied to each of the three fields | 20 + 5 |
| X | end-to-end cases through the baseline `LocalDestinationExecutor` and its SQLite destination, historical versus registry-backed | 11 |
| PIN | frozen pin literal accepts; altered pin refuses; the API offers no way to derive the pin from checked files | 3 |
| LIM | documented trust limitations pinned as tests: loaded code object not verified; S03 alone does not authenticate; `record_source` unverified | 3 |

Mapping to the authorization's mandatory comparisons: A is G1, G2, X; B is the non-widening rule over G1, G2 and X; C is R plus the refusal-governs-as-historical check; D is G1, G2, R and X (empty intersections, ordering, versions, source, manifest substitution, selection); E is E and B; F is LIM and PIN; G is the raw results.

## 4. Classification of any difference

Every observed difference between the two paths is assigned to exactly one class and reported; none is dropped:
1. **Behavioral inequivalence:** the same effective sets give different outcomes, or the registry-backed path admits something the caller-constructed historical policy refuses (a widening). A failure of S05.
2. **Unsupported representation:** a historical value the S03 record cannot express. The record is refused, the caller policy governs, and behavior equals historical. Not inequivalence.
3. **Designed narrowing:** a representable record removes a value the caller listed. The registry-backed path refuses what the caller alone admitted. This is the specified intersection and never widening.
A refusal case that produces a different disposition or reason than frozen, or any widening, is a **FAIL** and keeps the evidence. A case that cannot run is **SKIP** with the reason stated, never silently reclassified.

## 5. Results format

The harness writes deterministic raw results (JSON) and the pytest raw output to `docs/s05-results/`, with the execution configuration and the exact identities of the sources (Runtime blob and SHA-256, S03 validator blob, S04 consumer blob, plan blob, Python and pytest versions, base commit). They are bound to those source identities, not to a PR head, since the PR head cannot contain its own hash.

## 6. Out of scope

Behavior beyond the three fields, other families, dynamic activation, pin approval, the loaded code object, a compromised interpreter or host, and independent qualification. The S06 cleanup scope is only recommended in the report.
