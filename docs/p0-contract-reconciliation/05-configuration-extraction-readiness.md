# 5. Configuration-extraction readiness

Pins: hub `51c579a3` (OCS), registry `ce00520f` (`REG:`). No tests were executed. This document does not repeat the R07 rule inventory.

> **Source limitation.** The P0 worker did not inspect Control Plane or Execution Runtime source; claims about them are second-hand from registry R08/R10 documents. This document establishes contract and decision reconciliation, not independent verification of implementation claims. **P1 must inspect the exact source revisions directly before accepting each configurable-field extraction mapping.** ADR-REG-TR01 needed no additional source (it assigns ownership between written requirements).

## Answer

**Partly yes.** The partition rule and the mechanisms that enforce it already exist and are reusable. A multi-family parameter path does not: the only end-to-end typed-parameter path is **F1a**, hard-wired to one family. Wholesale extraction therefore needs bounded engineering prerequisites (below), not new architecture.

| Question | Verdict | Ledger |
|---|---|---|
| Is a configuration-versus-code-owned-invariant partition rule established? | Yes, ADOPTED | `DGR-ARCH-1.0.0` |
| Is there a code mechanism making a record unable to weaken a guardrail? | Yes, implemented, not qualified | `CODE-OWNED-FLOOR-EXPLICIT-ARGUMENT`, `REG-RECORD-0`, `MANIFEST-0` |
| Does an implemented path exist for typed parameter values with non-widening composition? | Only F1a (inactive, unwired) | `S03-…`, `S04-…`, `R08-V1-SUCCESSOR-FOUNDATION`, `NON-WIDENING-COMPOSITION` |
| Can it extend to F1b/F6/F1c/F4/F5 without redesign? | F1b yes with a contract version; others need per-field rulings and, for F4/F5, a Control Plane adapter | `R07-ENVELOPE-FAMILY-PROPOSALS` |

## The partition rule (reuse verbatim)

Hub `docs/declarative-governance-registry.md`: **"Governance rules are versioned data. Constitutional invariants stay enforced code."** Three partitions: (1) constitutional floor in code, owned by each component's one gate ("a registry entry cannot disable or weaken any of these"); (2) versioned, authenticated registry data; (3) registered evaluators as code ("no arbitrary expressions, downloaded scripts, caller-supplied rules or new general-purpose rule language"). Adoption: hub `operator-decisions.md` "Adopted architectural direction". The registry program applies the same rule with a finer test (S02 `docs/s02-inventory.md` §4 non-migratable list; R07 categories A and B; fit codes where E "should never be configurable policy"; plan v1.3 §3 and the P1 dispositions `DIRECT/CONDITIONAL/CODE_GUARDRAIL/UNRESOLVED`). **No contradictory partition exists.**

Operative extractability test already used in the sources (compose; do not invent): a value is extractable iff (a) it is already caller/constructor/profile data, (b) a code-owned hard bound or floor remains, (c) the registry value can only **narrow** what the caller permits, and (d) refusal is deterministic and never widens. Guards, check order, reason texts, `__post_init__` validation, vocabularies, lifecycle and relaxing toggles (for example `allow_synthetic_resolver`) stay code.

## Reusable components

| Component | Path | Gives | Status | Disposition |
|---|---|---|---|---|
| Floor passed explicitly; registry cannot weaken | `tools/registry_records.py` `validate_record(floor_mandatory_rule_ids)`; `tools/mandatory_checks.py` `check_completeness(floor_check_ids)` | Mechanical guardrail pattern | IMPL | REUSE_UNCHANGED (pattern) |
| Strict JSON / JCS / digest | `tools/registry_records.py` `jcs_dumps`, `loads_strict`, `record_digest` | ADR-P01 profile | IMPL | REUSE_WITH_ADAPTER |
| Append-only store, succession | `tools/registry_records.py` `check_succession`, `RegistryStore` | Epoch/predecessor, tamper-refusing store | IMPL | REUSE_WITH_ADAPTER |
| Data grammar plus fixed evaluator template | hub `s04/2.2-scanner-profile-contract.md` §2–3 | Template for structured (non-set) payloads: closed kinds, no free text | candidate data + tests, no live evaluator | REUSE_WITH_ADAPTER |
| Strict loader, canonical bytes, closed `CODES` | `REG:registry_successor/common.py` | Family-agnostic infrastructure | IMPL | REUSE_UNCHANGED |
| Selection envelope, structural lineage | `REG:registry_successor/selection.py` `parse_selection_envelope`, `resolve_effective` | epoch, scope, interval, revocation_ref, supersession | IMPL | REUSE_UNCHANGED (family check is the one F1a coupling) |
| Layered verification, injected verifier/trust | `REG:registry_successor/verify.py` `verify_selection`, `SignatureVerifier` | Authenticity, authority, scope, time, revocation, epoch layers; no verifier supplied | IMPL | REUSE_UNCHANGED |
| Required versus optional outcome; deny-all distinct from refusal | `REG:registry_successor/decision.py` `verify_and_decide` | Only public decision entrypoint | IMPL | REUSE_WITH_ADAPTER (calls `compose_f1a`) |
| Typed composition (intersection) | `REG:registry_successor/compose.py` `compose_f1a` | Reference for set families (F1a/F1b/F6 per-agent) | IMPL | REUSE_WITH_ADAPTER (field set hard-coded) |
| Non-widening check | `REG:registry_contract/validator.py` `widening_violations` | CR-NW function | IMPL | REUSE_UNCHANGED |
| Frozen s03-v1 validator | `REG:registry_contract/validator.py` `validate_record_text` | Unchanged baseline; successor must not edit | IMPL | REUSE_UNCHANGED |
| Evaluator adapter (overlay onto `LocalExecutionPolicy`) | `REG:registry_consumer/consumer.py` `apply_registry_overlay` | Trusted evaluator re-hash; caller policy returned unchanged on refusal; no mutation | IMPL | REUSE_WITH_ADAPTER (optional profile only) |
| Differential method | `REG:tests/s05_oracle.py`, `s05_expectations.json`, `test_s05_equivalence.py` | Frozen-expectations equivalence, non-widening, refusal grid | IMPL | REUSE_WITH_ADAPTER (per family) |
| Authentication primitives | `REG:docs/r08-s01/authentication-reuse-assessment.md` (BitRep, ODES `signatures.py`, Control Plane `validate_evidence`; pyca Ed25519) | No new primitive needed; no anti-rollback anywhere | assessment only | DEFER to R09 |

No V0.2 code evaluates numeric/set parameter payloads: `tools/registry_records.py` carries rule-table metadata, not parameter values. The two registries are complementary record types under one doctrine, not duplicates.

## Findings that matter for scenario-driven extraction

- **Evaluators are already code and stay code.** `LocalExecutionPolicy.check` is bound as `registered-code-reference` (`REG:registry_successor/common.py:19-20`); neither design has an expression or script field.
- **Guardrails are protected by construction on the F1a path:** unknown fields are refused; the record supplies only three sets; registry code never constructs `LocalExecutionPolicy`; composition is a subset of the caller. The limit is honest: shown for F1a only, and only by builder tests and a builder-written oracle.
- **V0.2's activation requirement for evaluators is stricter than R08's.** `tools/registry_records.py` refuses an evaluator without `qualification_ref` (`unqualified_evaluator`); `registry_successor` binds evaluator source blob/sha only. Any activation path under the DGR floor needs a qualification reference for `LocalExecutionPolicy.check` and each Control Plane evaluator. This is a prerequisite, not a conflict (`r08-v1` is inactive).
- **Participation semantics are already reconciled in principle.** The DGR resolver never falls back to a smaller manifest; R08 `required_policy_unavailable` never returns the caller policy; S04's optional overlay returns the caller policy because it is an optional profile over narrowing parameters, which R07 D7 and plan v1.3 §3.5 already distinguish.

## Technical prerequisites still outstanding (bounded; no redesign)

| # | Prerequisite | Evidence | Owner | Phase |
|---|---|---|---|---|
| G1 | **Family dispatch.** `r08-v1` hard-codes F1a in `common.py:18-21`, `record.py:51,79,110`, `compose.py:31-56`, `selection.py:85`, `decision.py:18,74`. A `family → (payload validator, composer, evaluator binding, caller normalizer)` table is needed for F1b, F6, F1c, F4, F5. This is plan v1.3 §5's "one typed adapter per owner" | listed code refs | Registry builder | P3 |
| G2 | **Per-field composition rulings** (units, ordering, floor/cap, direction, code interaction, unsupported outcome). Not definable today for F1d, F7, F4 cross-bound, F5 `irreversible`, F6 absent agent; the 32 S02 unresolved classifications stay unresolved unless source-specific findings decide them. Only set intersection and, conditionally, minimum with a code hard cap are definable | R07 `04` §3–4 | P1 lead / Architect, per field | P1 |
| G3 | **Numeric payload encoding.** Both JCS (`registry_records.py`) and `common.load_document` (`_reject_float`) refuse floats. F1c `max_amount` (binary64) and F4 ages (for example `5.0`) need an integer-unit or decimal-string encoding decided per field | R07 `04` F1c row; `common.py:135` | Registry builder + Runtime/Control Plane owner | P1 decides, P3 builds |
| G4 | **Control Plane consumer/adapter.** No Control Plane code references `LocalExecutionPolicy` or any registry consumer; F4/F5 evaluators (`bounded.py`, `freshness.py`, `runtime_authority.py`) have no registry hook. Needs an adapter under the Control Plane's existing gate, not a second engine | `REG:docs/r08-preparation/05` finding 7; `03` §3 | Control Plane owner | P3 |
| G5 | **Authenticated trust root and verifier (R09).** `verify_selection` refuses `verifier_unavailable` when none is supplied | `verify.py:60`; plan v1.3 P2 | Operator/Architect | P2 |
| G6 | **Activation owner for Runtime-enforced parameters** unassigned (Q14 default 5 gives the Control Plane activation only for the mandatory-check registry) | hub `2.4-architect-defaults-successor-note.md`; `REG:r08-preparation/03` §2 item 4 | **Architecturally resolved by ADR-REG-TR01; mechanics delegated (DT-01, DT-02, DT-04).** Not implemented | P2/P4 |
| G7 | **Evaluator qualification references** (above) | `registry_records.py`; DGR | Qualification repo owner | P3/P6 |
| G8 | **Independent oracle author** for Tier 1 (D13 designation unmet); the S05 oracle is builder-written | `REG:docs/sprint-status.md` "Outstanding operator decisions" (3) | Independent qualification owner appoints the lead (plan v1.3 section 8); operator involvement only if no independent lead can be secured | P6 |
| G9 | **Record the Architect R07 rulings** (D1–D13) as a decision file; today only a builder transcription exists (`R07-ARCHITECT-RULINGS-D1-D13`, UNVERIFIED) | R07 `08` ruling table | Architect | P1 |

## Genuine conflicts from this lane

None confirmed. Near-misses, both adapter-resolvable and recorded in the register: canonical JSON form (ADR-P01 JCS versus the registry's legacy form) and the evaluator qualification gate.

## Not verified

Operator decisions D-1..D-4 and O-1/O-2 "on #193" (external issue; only the document's transcription is available); `COG-REG-SHARED-ADD-01` text; qualification status of any V0.2 registry tool (absence of references is recorded as "no qualification reference", not as a negative result); freeze records for any `/0` profile (none found); the Architect R07 rulings beyond the builder transcription.
