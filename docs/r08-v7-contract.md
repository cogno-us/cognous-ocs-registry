# `r08-v7` contract: the unified successor on ONE parameterised engine; family `f5-action-class-irreversibility-policy`

Status: IMPLEMENTED (Registry side only), NOT ACCEPTED, and CONDITIONAL on the final contract-version allocation review. Non-authorizing. BUILDER_TESTED only; Tier 1 independent qualification is required before acceptance and has not been performed (not by the builder, the lead or CI). Frozen `r08-v1` .. `r08-v5` and the preserved transitional `r08-v6` (families `f5-action-class-revocation-assurance-policy` and `f5-terminal-revocation-enablement-policy`) are unchanged byte for byte. Scope is the Registry producer/consumer contract only; the Control Plane consumer is a separate change. Nothing here claims certification, security clearance or production readiness.

Governing documents: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Migration Plan v1.1, Engineering Plan v1.5, adopted audit (Registry PR #60), the PR #68 target architecture (`docs/architecture/*-v1.0.md` on Registry main `d7eb6be`). Preserved and never rewritten: Registry PR #69 (`42a666328b974a7581013358bcf8bc7b9eac7761`, the `r08-v6` head this branch is stacked on) and Control Plane PR #92 (`a62ca8d8e4088c95407c2000dcca081383d8dd4d`).

## 1. DEC-5 handling (decision by the lead builder under the Architect directive)

- `r08-v6` is preserved as the compatible transitional two-family contract (revocation assurance plus terminal revocation). It is NOT repurposed; none of its files, vectors or records change.
- `r08-v7` is the unified successor. It is built on ONE reusable engine and carries exactly ONE family now: irreversibility.
- The families for `anchor_deadline_to_inputs`, `ObservationPolicy.max_age_seconds` and `ObservationPolicy.clock_tolerance_seconds` are BLOCKED by decision record. No family is registered for them, no placeholder exists, and a record naming such a family refuses `family_unsupported` (tested).
- The contract number `r08-v7` is provisional until the version-allocation review; renumbering would change only the profile constants (version string and the two domain prefixes), not the engine.

## 2. Envelope protocol version versus family schema revision

A `ContractProfile` has a `version` (`r08-v7`: the envelope/record protocol and the signing and identity domains). Every family row has its OWN `family_schema_revision` (an `int`; irreversibility is `1`). The two evolve independently: a payload schema change bumps the revision without a new protocol version, and a protocol change does not renumber family payloads. The family schema revision is part of the effective-policy preimage (section 6), as the integer member `family_schema_revision`; the legacy string member `family_version` (`"v2"` .. `"v6"`) is used only by the frozen contracts and is never present in a v7 preimage.

## 3. One engine, many profiles

The package `registry_successor/engine/` implements, once, as functions of an immutable `ContractProfile`:

| Module | Content |
|---|---|
| `engine/profile.py` | `ContractProfile`, `FamilyEntry`, `IdentityRow`; `lookup`, `table_for_contract_version`, `compose`, `compose_for` (the table dispatch of `v6_families`, as functions of a profile) |
| `engine/profiles.py` | the two shipped profiles `V7` and `V6_COMPAT` |
| `engine/selection.py` | envelope parser, statement shape, `signing_input` |
| `engine/record.py` | record validation |
| `engine/verify.py` | layered verification (the SAME layers, order and codes as `v6_verify._verify_v6`) |
| `engine/decide.py` | `decide_verified`, `verify_and_decide` (the decision step) |
| `engine/identity.py` | effective-policy identity |
| `engine/families_irreversibility.py` | the one v7 family: payload validator, caller normalizer, composer |

A profile is DATA: `version`, `selection_signing_domain` (`b"ocs-reg/r08-v7/selection\n"`), `effective_policy_domain` (`b"ocs-reg/r08-v7/effective-policy\n"`), an immutable table family-id to (`FamilySpec`, schema revision) and one identity row per family. There is no general policy interpreter, no executable rule (no `eval`/`exec`, no I/O, no import of the Control Plane: tested by AST scan), no mutable global (module tables are `MappingProxyType`; the profile copies its inputs and is a frozen dataclass; tested) and no run-time registration. Families are typed: each has its own schema, validator, caller normalizer and composer. The engine accepts exactly a `ContractProfile` (a subclass or any other object is a `TypeError`: a programming error, not a hostile-input path). There is no `contract_version` parameter anywhere in the engine's verification or decision entry points; the contract is `profile.version`.

Thin public modules bind the engine to `V7` and add no logic (tested by AST: each public function is a single `return` of an engine call):

| Module | Purpose |
|---|---|
| `v7_decision.py` | `verify_and_decide_v7(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission=None) -> PolicyDecision` (same signature and result type as `verify_and_decide_v6`) |
| `v7_policy_identity.py` | `effective_policy_digest(family, payload, contract_version="r08-v7")`, `effective_preimage`, `validate_effective_payload`, `deny_all_dimensions`, `registered_family_version`, `IdentityRefusal` |
| `v7_families.py` | `FAMILIES_V7`, `lookup_v7`, `CONTRACT_V7`, `table_for_contract_version_v7`, `compose_v7`, `compose_for_v7` |

No frozen module (`verify.py`, `families.py`, `v2_*` .. `v6_*`) is edited, and none imports the engine (tested against a sha256 manifest of the base commit, `tests/vectors/r08v7/frozen_baseline_manifest.json`).

## 4. The compatibility adapter: `V6_COMPAT`

`engine.profiles.V6_COMPAT` carries the exact `r08-v6` constants: version, signing domain `b"ocs-reg/r08-v6/selection\n"`, effective domain `b"ocs-reg/r08-v6/effective-policy\n"`, the SAME `FamilySpec` objects as `v6_families.FAMILIES_V6` (identity-checked by test) and identity rows derived from `v6_policy_identity.IDENTITY_FAMILIES` (tag `family_version` = `"v6"`). It exists to prove, not to replace: `tests/test_r08v7_engine_differential.py` shows that `engine(V6_COMPAT)` returns byte-identical results to the frozen v6 entry points over (a) the pinned `tests/vectors/r08v6` signed and identity vectors, (b) one-at-a-time hostile variations of every argument of the decision path (selection, record, trust, context, time, caller, participation, verifier, key admission), (c) a seeded random sample of combinations, (d) hostile selection objects and snapshot-floor arguments, (e) identity digests, preimages and refusals over a family x payload x contract-version grid, and (f) table dispatch and composition. Cross-version documents (v3, v4, v5, v6 both families, v7) are accepted only by their own contract's entry point and refuse `contract_unsupported` everywhere else (no fallback, no upgrade); a family of another contract inside this contract's envelope refuses `family_unsupported`; a signature over another contract's domain never verifies.

Drift tripwires: the string-literal multiset (layer names, reason codes, detail texts) of the engine's verification, decision, statement and record functions equals the frozen v6 one except for the documented version-specific literals (tested). The engine takes the contract-agnostic helpers (private copies, trust normalization, key admission, record binding, snapshot floor) from the frozen `verify.py`, which is shared, not copied.

## 5. Family `f5-action-class-irreversibility-policy` (schema revision 1)

Payload: EXACTLY one member, `class_irreversible`, an object `action_class -> value` with value in the CLOSED two-string vocabulary `irreversible` | `no_change`. Class keys follow the frozen opaque-token rule of the `r08-v2` F5 family (`frozen_token_valid`, 1..128, no `*`), sorted, at most 256, non-empty map. Missing member `field_missing`, extra `field_unknown`, wrong type (including JSON booleans) `field_type_invalid`, violated value rule `field_invalid` (types before values). No default, no case folding, no coercion, no str subclass. Reason codes: the existing `CODES_V2`; none added. The evaluator binding is the same constant pair as the v6 families (`common.EVALUATOR_ID`, `common.EVALUATOR_BINDING`); the enforcing component is the Control Plane (`FamilySpec.enforcing_component`).

Order and composition (only operator `intersection`, the frozen dispatch name for narrowing). The only relation asserted is `no_change` (looser: the Registry asserts nothing for the class) < `irreversible` (stricter). Effective per class = the stricter of (caller, Registry). A Registry `no_change` over a caller `irreversible` yields the caller value, reported in `detail` as `registry_value_not_narrowing:<classes>` (sorted, only the looser Registry classes). A Registry `no_change` NEVER lowers a caller `irreversible`, and this family can NEVER assert reversibility: its vocabulary has no value that means reversible, and the Control Plane's `False` has no spelling in it. A Registry class the caller does not define refuses `composition_record_invalid` (a class is never created); a caller class the record does not name keeps the caller value. An invalid caller refuses `composition_caller_invalid` and is never replaced. Every refusal carries no effective policy; `deny_all` is never set.

What the Registry cannot know (consumer-owned): it cannot see the host's reversal data (`reversibility`, `reversible_until`, `reversal_cost`, `on_unreadable`, `reads_protected_data`, `counterparty_observable`). Whether a host class may be flipped to irreversible at all, how a flip is refused when it would hide a host defect, and how actions sharing a class are treated are the Control Plane's pre-checks; the Registry only ever supplies the strengthen-only value. Whether `irreversible` has any operational effect depends entirely on the consumer wiring the field.

## 6. Identity (version-specific)

Selection signing input: `b"ocs-reg/r08-v7/selection\n" + canonical_bytes(statement)`; a v1..v6 signature never verifies a v7 statement and the reverse. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v7/effective-policy\n"` + canonical bytes of the preimage `{effective_policy_profile "ocs-effective-policy/1", contract_version "r08-v7", family, family_schema_revision 1, deny_all [], effective}`. The revision is read from the profile's table; no parameter or payload member can supply it, and it is an `int`. It binds every class and value, so no class and no value can be replaced independently, and it differs from every earlier contract's digest by domain. `v2_policy_identity` .. `v6_policy_identity` refuse this family `family_unsupported`; `v7_policy_identity` refuses every other family `family_unsupported` and every other contract version `contract_unsupported`. Vectors are recomputed with an independent encoder (`tests/vectors/r08v7/identity_vectors.json`, generator `genvec7.py`). No new trust root: signing keys, trust snapshots, key admission, withdrawal, revocation and epoch floors are the existing mechanisms, unchanged.

## 7. Compatibility limitations (explicit)

1. The records pin the same registered evaluator reference (`engine.safe_executor.LocalExecutionPolicy.check`, `registered-code-reference`); the enforcing Control Plane evaluator is named by `FamilySpec.enforcing_component` only.
2. Registry tokens exclude spaces and other characters: a class id containing them cannot be governed (refused, never loosened).
3. As with `r08-v3`..`r08-v6`, the frozen dispatch tables refuse `r08-v7` (`families.table_for_contract_version("r08-v7")` is `contract_unsupported`); the engine is the only implementation of the v7 orchestration. Unlike v3..v6 there is no per-version copy of that orchestration: the repeated orchestration (the drift risk recorded in the v6 contract section 7.3) exists for v7 only as parameters of one engine. `V6_COMPAT` is a proof of equivalence with the frozen v6 copy, not a rewrite of it.
4. Three existing source-scan guards enumerate permitted successor modules; `tests/test_ext_s1_5_identity_module.py` is edited to allowlist the new engine package and the three `v7_*` modules (allowlist addition only, as each earlier contract did). It is not in the frozen manifest.
5. The contract number is conditional on the version-allocation review (section 1). No Control Plane activation exists in this change; nothing is counted IMPLEMENTED in the migration ledger until the Control Plane change lands.

## 8. Evidence

Tests: `tests/test_r08v7_irreversibility_family.py` (validation, hostile inputs, exhaustive composition matrix, table), `tests/test_r08v7_policy_identity.py` (identity, independent digest recomputation, schema revision), `tests/test_r08v7_decision_path.py` (real synthetic Ed25519 decisions: key revocation, withdrawal, expiry, wrong scope/operation/family), `tests/test_r08v7_lifecycle_boundaries.py` (exact boundaries, exact-type dispatch, decision-step rechecks), `tests/test_r08v7_engine_profile.py` (profile validation and immutability, no hardwired contract, no mutable global, no drift from the v6 literals, a third test-only profile), `tests/test_r08v7_engine_differential.py` (section 4) and `tests/test_r08v7_frozen_baseline.py` (193 frozen r08-v1..v6 files byte-identical from `42a6663`). Builders: `tests/r08v7_support.py`. Vectors: `tests/vectors/r08v7/`. Generators, the mutation harness `mut_r7.py` and raw logs (mutation, branch and base whole-suite runs): `docs/family-migration/unified-engine/evidence/`.
