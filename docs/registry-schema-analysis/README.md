# Registry rule-family and schema analysis

**Status: analysis and proposal only. Non-authorizing. Not independently qualified. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.**

This directory answers one question: *which parts of the historical rule inventory could become versioned registry data, which must stay in code, and what minimal schema would carry the former without widening any authority.* It implements nothing. It does not define a schema that any code reads, migrate any rule, change the S03 contract or the S04 consumer, or activate, select or approve any record or pin.

## Boundary

- Based on `main` at `1870f3a62ee16cdea53c4c23a8df8c9be3c2f2cf` (S06 complete, verified as the current head when this branch was cut).
- Owns only `docs/registry-schema-analysis/`. Nothing under `registry_contract/`, `registry_consumer/`, `registry_records/`, `baseline/`, `tests/` or any workflow is touched. PR #13 (`recovery/v02-rule-inventory`) is not modified by this branch.
- Does not duplicate the 3,190-entry catalogue. It is referenced by repository `cogno-us/cognous-open-control-stack`, commit `51c579a3208149922649a31a6eb041106a4121c3`, path `docs/mvp-recovery/registry/catalogue-v0.1/`, manifest digest `sha256:22f49fd1341cfaa6e46727db9b6153c2073b82a3125fd725173494f3ebb37650`.
- Governing references: OCS-REG-PLAN v1.2 (`docs/plans/PROJECT_PLAN-v1.2.md` on `main`, merged and adopted per the operator's closeout instruction) and its GCR crosswalk; this analysis was authored against v1.1 blob `6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2`; Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`.

## Labels

**[V]** verified by reading a named source in this analysis. **[R]** reported by a source (catalogue, S02 worker, an earlier sprint document) and not re-verified. **[I]** inference or proposal by this analysis. Where a claim carries no label in a table, the column header says which it is.

## Reading order

| File | Content |
|---|---|
| [01-inventory-assessment.md](01-inventory-assessment.md) | What the historical inventory is and is not; counts; what it can support |
| [02-rule-family-taxonomy.md](02-rule-family-taxonomy.md) | Categories A to K, eight dimensions, 15 attributes per candidate family |
| [03-source-crosswalk.md](03-source-crosswalk.md) | Source-backed reconciliation, the 32 unresolved rows, the priority rows, 60 versus 300 |
| [04-schema-fitness-matrix.md](04-schema-fitness-matrix.md) | S03 fit codes A to E per family; composition semantics; where non-widening composition is not definable |
| [05-common-envelope-proposal.md](05-common-envelope-proposal.md) | Proposed minimal envelope; RECORD, SELECTION, ACTIVATION |
| [06-family-schema-proposals.md](06-family-schema-proposals.md) | Successor proposal and illustrative examples |
| [07-schema-qualification-plan.md](07-schema-qualification-plan.md) | Schema validation plan (file name per the brief): scenarios with expected results; designed, not executed |
| [08-open-architectural-decisions.md](08-open-architectural-decisions.md) | Decisions needed from the OCS Architect and issues for ISS Architect review |
| [09-implementation-roadmap.md](09-implementation-roadmap.md) | Possible future engineering order; not authorized |

## Headline results

1. The 3,190 catalogue entries are source statements. None is an established executable or configurable policy, and the catalogue has no configurable-parameter type. They cannot populate a registry.
2. **Nine** candidate configurable families are identified from the 11 S02 families (five primary: F1, F4, F5, F6, F7; four secondary: F3, F9, F10, F11). One field group (F1a) is already represented. **Eight** mandatory, non-migratable families (M1 to M8) are identified. These counts are this analysis's grouping and depend on its granularity; they are not source-established totals.
3. The current S03 contract represents exactly one field group directly (F1a: three allow-lists). A bounded extension covers two more fields (F1b). Every other candidate needs a new typed payload (C), new applicability or selection semantics (D), or must never be policy (E).
4. Monotonic non-widening composition is definable per scalar or set field when the stricter direction is ruled. It is **not** definable as one shared algebra, and for F7 (cross-field ordering across two components), F4 (clocks and observation authority) and F5 (profile toggles) it is only definable under rulings that have not been made.
5. Most consequential gaps: no authenticated selection, activation or pin exists; the 32 S02 classifications are unresolved; the `COG-REG-SHARED-ADD-01` source was not available to this analysis; no ISS architecture source was available, so no ISS family payload is proposed.

The Architect's R07 rulings are recorded in 08; they are design guidance and authorize no implementation. Nothing here approves, activates or enforces anything. The successor schema is a proposal for architectural review.
