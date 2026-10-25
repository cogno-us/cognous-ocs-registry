# Lane D: configuration vs guardrail partition (readiness assessment)

Commits: OCS `51c579a3208149922649a31a6eb041106a4121c3` (hub); Registry `ce00520f91bf3986a08b4d13a1fb062057babc71`. Ledger: `lanes/D.jsonl` (16 rows, IDs D1..D16). Paths below are repo-relative (OCS unless prefixed `REG:`).

## 1. Answer

**Partly yes.** The partition *rule* and the *mechanisms that enforce it* already exist and are reusable. What does not yet exist is a multi-family, parameter-payload implementation: the only end-to-end typed-parameter path is F1a, hard-wired to one family. "Wholesale extraction" therefore needs engineering prerequisites (section 5), not new architecture.

| Question | Verdict | Basis |
|---|---|---|
| Is a configuration vs code-owned-invariant partition rule already established? | Yes, ADOPTED | D1 |
| Is there a code mechanism making a record unable to weaken a guardrail? | Yes, implemented, not qualified | D4, D3, D6 |
| Does an implemented path exist for typed parameter values with non-widening composition? | Only F1a (inactive, unwired) | D9-D12, D15 |
| Can it extend to F1b/F6/F1c/F4/F5 without redesign? | F1b yes with a contract version; others need per-field rulings and, for F4/F5, a Control Plane adapter | D13, D15 |

## 2. The partition rule (reuse verbatim)

`docs/declarative-governance-registry.md`, "Constitutional principle": **"Governance rules are versioned data. Constitutional invariants stay enforced code."** Three partitions (same file, "Three partitions"; restated in `docs/program-v0.2/s02/contracts/1.3-registry-r0.md` s1):

1. Constitutional floor, in code, owned by each component's one gate. "A registry entry cannot disable or weaken any of these."
2. Versioned, authenticated registry data.
3. Registered evaluators as code: "No arbitrary expressions, downloaded scripts, caller-supplied rules or new general-purpose rule language."

Adoption evidence: `docs/program-v0.2/operator-decisions.md` row "Governed registry rather than scattered hard-coded configurable rules" = "Adopted architectural direction"; the doc's own header cites operator instruction 2026-10-21. Limits: the doc says wire schemas are frozen "before any code is written" (not frozen by it) and Constitution revision adoption is "a separate recorded act".

The registry repo applies the same rule with a finer test: S02 `REG:docs/s02-inventory.md` s4 (non-migratable list), R07 `REG:docs/registry-schema-analysis/02` Cat A (configurable parameter) vs B (mandatory invariant), `04` s2 fit codes (A-D representable, **E "should never be configurable policy"**), and plan v1.3 s3 constraint 1 ("Code remains the enforcement owner") + P1 dispositions `DIRECT/CONDITIONAL/CODE_GUARDRAIL/UNRESOLVED`. These agree with the OCS floor list; no contradictory partition exists.

Operative test already used in the sources (compose, don't invent): a value is extractable iff (a) it is already caller/constructor/profile data, (b) a code-owned hard bound or floor remains, (c) the registry value can only narrow what the caller permits (CR-NW), and (d) refusal is deterministic and never widens. Guards, check order, reason texts, `__post_init__` validation, vocabularies, lifecycle, relaxing toggles (e.g. `allow_synthetic_resolver`) stay code (`REG:docs/s03-contract.md` s2; `04` s2; `02` M1-M8).

## 3. Reusable components

| Component | Path | What it gives | Status | Disposition |
|---|---|---|---|---|
| Floor passed explicitly, registry cannot weaken | `tools/registry_records.py` `validate_record(floor_mandatory_rule_ids)` :195; `tools/mandatory_checks.py` `check_completeness(floor_check_ids)` :439 | Mechanical guardrail pattern (floor subset check, refusal codes) | IMPL_NOT_QUAL (D3,D4,D6) | REUSE_UNCHANGED (pattern) |
| Strict JSON / JCS / digest | `tools/registry_records.py` `jcs_dumps` :74, `loads_strict` :106, `record_digest` :123 | ADR-P01 canonical profile (M0 row 1) | IMPL_NOT_QUAL | REUSE_WITH_ADAPTER (see conflict note 4a) |
| Append-only store / succession | `tools/registry_records.py` `check_succession` :253, `RegistryStore` :267 | Epoch/predecessor, tamper-refusing store | IMPL_NOT_QUAL | REUSE_WITH_ADAPTER |
| Data grammar + fixed evaluator template | `docs/program-v0.2/s04/2.2-scanner-profile-contract.md` s2-s3 | Template for structured (non-set) payloads: closed kinds, no free text | IMPL_NOT_QUAL (data+tests; no live evaluator) | REUSE_WITH_ADAPTER |
| Strict loader, canonical bytes, closed `CODES` | `REG:registry_successor/common.py` `load_document` :152, `canonical_bytes` :102, `CODES` :31 | Family-agnostic infrastructure | IMPL_NOT_QUAL | REUSE_UNCHANGED |
| Selection envelope + structural lineage | `REG:registry_successor/selection.py` `parse_selection_envelope` :165, `resolve_effective` :237 | epoch, scope, interval, revocation_ref, supersession | IMPL_NOT_QUAL | REUSE_UNCHANGED (family check at :85 is the one F1a coupling) |
| Layered verification, injected verifier/trust | `REG:registry_successor/verify.py` `verify_selection` :322, `SignatureVerifier` :60 | Authenticity/authority/scope/time/revocation/epoch layers; no verifier supplied | IMPL_NOT_QUAL | REUSE_UNCHANGED |
| Required vs optional outcome; deny-all distinct from refusal | `REG:registry_successor/decision.py` `verify_and_decide` :83 | Only public decision entrypoint | IMPL_NOT_QUAL | REUSE_WITH_ADAPTER (calls `compose_f1a` at :74) |
| Typed composition (intersection) | `REG:registry_successor/compose.py` `compose_f1a` :62 | Reference for set families (F1a/F1b/F6 per-agent) | IMPL_NOT_QUAL | REUSE_WITH_ADAPTER (field set hard-coded) |
| Non-widening check | `REG:registry_contract/validator.py` `widening_violations` :280 | CR-NW function | IMPL_NOT_QUAL | REUSE_UNCHANGED |
| Frozen s03-v1 validator | `REG:registry_contract/validator.py` `validate_record_text` :261 | Unchanged baseline; successor must not edit | IMPL_NOT_QUAL | REUSE_UNCHANGED |
| Evaluator adapter (overlay onto `LocalExecutionPolicy`) | `REG:registry_consumer/consumer.py` `apply_registry_overlay` :270 | Trusted evaluator re-hash, caller policy returned unchanged on refusal, no mutation | IMPL_NOT_QUAL | REUSE_WITH_ADAPTER (optional profile only) |
| Differential method | `REG:tests/s05_oracle.py`, `s05_expectations.json`, `test_s05_equivalence.py` | Frozen-expectations equivalence, non-widening, refusal grid | IMPL_NOT_QUAL | REUSE_WITH_ADAPTER (per family) |
| Authentication primitives | `REG:docs/r08-s01/authentication-reuse-assessment.md` (BitRep `utils/verification.py`, ODES `signatures.py`, CP `runtime_authority.py validate_evidence`, all pyca Ed25519) | No new primitive needed; no anti-rollback anywhere | assessment only | DEFER to R09 |

No V0.2 code evaluates numeric/set parameter payloads: `tools/registry_records.py` carries rule-table metadata (class, profile, status, disposition, evaluator ref), not parameter values. The two registries are complementary record types under one doctrine, not duplicates.

## 4. Findings relevant to scenario-driven extraction

- **Evaluators are already code and stay code.** `LocalExecutionPolicy.check` is bound as `registered-code-reference` (`REG:registry_successor/common.py:19-20`); no expression/script field exists in either design. Consistent with DGR partition 3 and plan v1.3 s3.2.
- **Guardrails are protected by construction on the F1a path:** unknown fields refused; the record supplies only three sets; `LocalExecutionPolicy` is never constructed by registry code (`compose.py` docstring); composition is a subset of the caller (intersection). Honest limit: this is shown for F1a only, and only by builder tests/oracle.
- **V0.2's activation requirement for evaluators is stricter than R08's.** `tools/registry_records.py` refuses an evaluator without `qualification_ref` (`unqualified_evaluator`; 2.2 note s4 says the illustrative scanner record is refused for exactly this reason). DGR also forbids "an unqualified evaluator version" pairing. `registry_successor` binds evaluator source blob/sha only. Any activation path under the DGR floor therefore needs an evaluator qualification reference for `LocalExecutionPolicy.check` and each Control Plane evaluator. Not a conflict (r08-v1 is inactive); it is a prerequisite.
- **Participation semantics already reconciled in principle:** DGR resolver "never falls back to a smaller manifest"; R08 `required_policy_unavailable` never returns the caller policy; S04's optional overlay returns the caller policy. The first two agree. S04 differs only because it is an optional profile over narrowing parameters (not a mandatory-check manifest), which R07 D7 and plan v1.3 s3.5 already distinguish.

## 5. Technical prerequisites still outstanding (all bounded, no redesign)

| # | Prerequisite | Evidence | Owner |
|---|---|---|---|
| G1 | **Family dispatch.** r08-v1 hard-codes F1a in `common.py:18-21`, `record.py:51,79,110`, `compose.py:31-56`, `selection.py:85`, `decision.py:18,74`. A `family -> (payload validator, composer, evaluator binding, caller normalizer)` table is needed for F1b, F6, F1c, F4, F5. This is the "one typed adapter per owner" of plan v1.3 s5. | code refs listed | Registry builder |
| G2 | **Per-field composition rulings** (units, ordering, floor/cap, direction, code-interaction, unsupported outcome). Not definable today for F1d, F7, F4 cross-bound, F5 `irreversible`, F6 absent agent (`04` s4; D4/D5; S02 unresolved 32 stay unresolved). Only set intersection and (conditionally) minimum with code hard cap are definable. | `04` s3-s4 | P1 lead / Architect per field |
| G3 | **Numeric payload encoding.** Both JCS (`registry_records.py`, floats refused) and `common.load_document` (`_reject_float`) refuse floats; F1c `max_amount` (binary64, W1-015), F4 ages (e.g. `5.0`) need an integer-unit or decimal-string encoding decided per field. | `04` F1c row; `common.py:135` | Registry builder + Runtime/CP owner |
| G4 | **Control Plane consumer/adapter.** No Control Plane code references `LocalExecutionPolicy` or any registry consumer; F4/F5 evaluators (`bounded.py`, `freshness.py`, `runtime_authority.py`) have no registry hook. Needs an adapter under the CP's existing gate (no second engine). | `REG:docs/r08-preparation/05` finding 7; 03 s3 | Control Plane owner |
| G5 | **Authenticated trust root and verifier** (R09). `verify_selection` refuses `verifier_unavailable` with none supplied. | `verify.py:60`; plan v1.3 P2 | Operator/Architect (R09) |
| G6 | **Activation owner for Runtime-enforced parameters** unassigned: Q14 default 5 gives Control Plane activation only for the mandatory-check registry; Runtime policy is built by "an unnamed host integrator". | `2.4-architect-defaults-successor-note.md`; `REG:r08-preparation/03` s2 item 4 | Lane C / R09-R10 |
| G7 | **Evaluator qualification references** (above). | registry_records.py; DGR | Qualification repo owner |
| G8 | **Independent oracle author** for Tier 1 (D13 designation unmet); S05 oracle is builder-written. | `REG:docs/sprint-status.md` "Outstanding operator decisions" (3) | Operator designates |
| G9 | **Record the Architect R07 rulings** as a decision file (currently only builder transcription). | `08` ruling table intro | Architect |

## 6. Genuine conflicts

**None confirmed** between the V0.2 partition design and R07's configurable-family analysis. They share the same doctrine; R07 cites OCS-REG-PLAN v1.2 and the Constitution, not a different rule. No `TARGETED_RECONCILIATION` row is proposed from this lane.

Near-misses (adapter-resolvable; reported for the lead's dedupe against Lane B):

- **4a. Canonical form.** M0 row 1 (ADR-P01, approved): "JCS for new commitments; legacy kept as a named profile" (`docs/program-v0.2/m0-decision-record.md`). Registry `s03-v1`/`r08-v1` use `json.dumps(sort_keys, separators=(",",":"), ensure_ascii=True)` (`REG:registry_successor/common.py:102-103`; `registry_contract/validator.py:74`). Digests of identical data differ (escaping of non-ASCII; key order only by code point vs UTF-16). Consequence arises only if a single digest must be verified by both a registry and a Control Plane decision context (DGR: decisions "bind the selected registry and evaluator versions into their context commitment"). Resolution without redesign: the profile is a *named* label (R07 `05` s2 `canonicalization` field already proposes an exact-match id); if cross-component binding is required in P4, bind the registry's own named profile digest rather than re-canonicalize. Not escalated: ADR-P01 itself keeps named legacy profiles.
- **4b. Evaluator qualification gate** (section 4): V0.2 requires `qualification_ref`; r08-v1 has none. Prerequisite G7, not an incompatibility.

## 7. P1 handoff for this lane

P1 may rely on, without another review: D1 (partition rule), D4/D15 (floor-as-argument and non-widening composition as the guardrail test), D16 (non-migratable classes as `CODE_GUARDRAIL`), D9/D12 (frozen F1a + r08-v1 as the implemented reference path). P1 must treat as unsettled: G2 per field, G3, and everything in D13/D14 beyond what plan v1.3 s3 itself states.

## 8. Could not verify

- Operator decisions D-1..D-4, O-1, O-2 "on #193" (2.2 contract s1): the issue is external; only the doc's transcription is available.
- COG-REG-SHARED-ADD-01 text: not present in any repo read (also per `REG:docs/registry-schema-analysis/08` D10).
- Whether R08-S01 (PR #19) is merged: `docs/sprint-status.md` says "DRAFT PR" yet `registry_successor/` exists at `ce00520f`; merge state not established by this lane (shallow clone, one commit).
- Qualification status of any V0.2 registry tool: `grep` of `cognous-stack-qualification@998d39c5` for `ocs-registry-record`, `mandatory-manifest`, `registry_records` found nothing; absence is recorded as "no qualification reference", not as a negative result.
- Freeze records for `/0` profiles: Q4/Q17 describe a one-at-a-time freeze policy; no freeze record for any registry profile found.
- No tests were executed by this lane.
