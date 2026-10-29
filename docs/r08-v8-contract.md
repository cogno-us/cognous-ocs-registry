# `r08-v8` contract (DRAFT): a compatible successor carrying ONLY the three remaining families, on the existing unified engine

Status: DRAFT / PROPOSED / GATED. NOT FOR MERGE until the Architect decides AR-1, D-C1, D-C2, D-C3, D-C4, D-C5, D-C6, D-06 and D-07 (section 8). BUILDER_TESTED only; non-authorizing; no independent qualification has been performed (not by the builder, the lead or CI), and nothing in this document is a security clearance, certification or statement of production readiness. Changes to this candidate component require F3 requalification, refreeze and re-review before acceptance. This is prepared as a future draft PR on Registry main `67512a71546748cd888e4cf790485ea0bef9199a`; it is carried by a DRAFT, gated Registry preparation pull request that must not be merged before those decisions.

Governing documents: Engineering Constitution `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b`, Static Migration Plan v1.1 section 12, Engineering Plan v1.5, adopted audit (Registry PR #60), `docs/r08-v7-contract.md` (the engine this builds on), the lead builder's final-three brief of 2026-10-29 and the Worker C reconciliation (family definitions, section 2.3 to 2.5).

## 1. What this change is and is not

IS: a new profile `V8` (contract `r08-v8`) on the existing parameterised engine `registry_successor/engine/`, carrying exactly three families, each with schema revision 1:

| Family id | Payload member | Host field (Control Plane, read only) |
|---|---|---|
| `f5-anchor-deadline-to-inputs-policy` | `anchor_deadline_to_inputs` | `FreshnessProfile.anchor_deadline_to_inputs` |
| `f5-observation-max-age-policy` | `observation_max_age_seconds` | `ObservationPolicy.max_age_seconds` |
| `f5-observation-clock-tolerance-policy` | `observation_clock_tolerance_seconds` | `ObservationPolicy.clock_tolerance_seconds` |

IS NOT:

- It does NOT enable any consumer. Registering a family in a Registry profile makes a Registry record and signed selection decidable; it adds no enforcement anywhere. The Control Plane consumers for these three families are NOT implemented, and this change does not implement or design-commit them.
- It does NOT change `r08-v7` or any frozen `r08-v1` .. `r08-v7` behaviour (section 6). `V7` still registers exactly one family, irreversibility; a v7 record or selection naming any of the three family ids still refuses `family_unsupported` (tested). `PROFILES` is unchanged and `V8` is not a member of it.
- It does NOT re-register irreversibility or any earlier family. Re-registering irreversibility under `r08-v8` would change its signing and identity domains and force re-signing; it stays under `r08-v7`. Under `r08-v8` irreversibility refuses `family_unsupported`, and a genuine v7 document refuses `contract_unsupported` (tested).
- It adds NO new reason code. Every refusal uses the existing closed vocabulary `CODES_V2_REV2` (51 codes; tested by AST scan and emitted-literal pin).
- It does NOT persist or bind any observation value. ObservationPolicy is constructor-only in the Control Plane and is not part of the approval or catalogue digest (decision D-06 is open). A signed Registry selection for the two observation families therefore cannot, by itself, be bound into a persisted decision; any persisted-decision schema change, approval-preimage change or new authority requires Architect authorization and F3 requalification and is not done here.
- The anchor family leaves the purpose-observation residual (decision D-C4 / D-07): with the anchor flag set and no `policy_binding`, the purpose-input window can still be the 2x window recorded in the reconciliation. The family narrows what it can (it can only add the anchor); it does not claim the residual is closed, and closing it needs a protected-file edit or an Architect acceptance of the residual.
- The numeric ranges are STRUCTURAL REGISTRY TOKEN RANGES, not host bounds. 2147483647 is `common.MAX_INT`, the ceiling already used by the Registry's canonical integer range and by `v2_age_bounds.AGE_MAX`; the Control Plane has no such ceiling for these fields (a host value of 2**31 or more is legal there). A host value above the token range is not narrowable (the whole caller refuses); it is never clamped or rewritten.

## 2. The three families

Common to all three: `enforcing_component` is `control-plane`; evaluator binding `(c.EVALUATOR_ID, c.EVALUATOR_BINDING)` (the registered reference, as r08-v7); the only composition operator is `intersection` (the frozen dispatch name for narrowing; any other operator refuses `composition_operator_unsupported`); `deny_all` is never set and the family is not a deny-all dimension; exact types only (`type(x) is str` or `is int`; no bool or float coercion, no case folding, no clamping, no defaults, no str or int subclass); every refusal carries no effective policy and an invalid caller is never replaced.

Payload validator codes (types before values): not an exact dict or a non-`str` key `field_type_invalid`; an extra key `field_unknown`; an absent key `field_missing`; a wrong value type `field_type_invalid`; a value outside the closed domain `field_invalid`. Composer codes: `composition_operator_unsupported`, `composition_record_invalid` (record not ok, not a dict, or payload invalid), `composition_family_unsupported` (record family mismatch), `composition_caller_invalid`.

### 2.1 `f5-anchor-deadline-to-inputs-policy` (module `engine/families_anchor.py`)

- Payload: exactly `anchor_deadline_to_inputs`, an exact `str` in the closed vocabulary `anchor` | `no_change`. A JSON boolean is `field_type_invalid`; the vocabulary names no false and the Registry value can never assert false.
- Order: `anchor` (stricter) < `no_change` (looser). Composition: effective = `anchor` if EITHER side is `anchor`. A Registry `no_change` over a caller `anchor` yields `anchor`, reported in `detail` as `registry_value_not_narrowing:anchor_deadline_to_inputs`.
- Caller: exactly `{"anchor_deadline_to_inputs": "anchor" | "no_change"}`; a consumer maps the host bool to the exact strings (a bool caller refuses `composition_caller_invalid`).
- Identity row: kind `scalar-enum` (existing; no engine change for this family).
- Host preconditions (consumer-owned, invisible to the Registry): a `FreshnessProfile` already exists in the host runtime authority profile; the profile carries no `policy_binding`. The Registry never invents either.

### 2.2 `f5-observation-max-age-policy` (module `engine/families_observation.py`)

- Payload: exactly `observation_max_age_seconds`, a strict `int`, `1 <= v <= 2147483647` (floor follows the host `gt=0`). 0, negatives, bool, float, str, None, bytes, Decimal, int subclasses and values above the token range refuse.
- Composition: `effective = min(caller, registry)`; a Registry value above the caller yields the caller value with `detail = registry_value_not_narrowing:observation_max_age_seconds`; equal reports nothing. A caller outside `1..2147483647` (including a host value above the token range, or a host `None` policy) refuses the whole caller `composition_caller_invalid`: nothing is narrowed.
- The Registry asserts no ordering between 60 and 300 (the host fixtures use both; no source compares them, D-07).
- Operator consequence: lowering the value can add `observation_stale` holds on reconcile (never a retry); it cannot turn a hold into a pass.
- Identity row: kind `scalar-int` (additive, section 4).

### 2.3 `f5-observation-clock-tolerance-policy` (module `engine/families_observation.py`)

- Payload: exactly `observation_clock_tolerance_seconds`, a strict `int`, `0 <= v <= 2147483647` (floor follows the host `ge=0`). A Registry value of 0 is admitted ("no future allowance"; not a deny-all) subject to D-C1.
- The member name MUST NOT alias the held constructor tolerance member `clock_tolerance_seconds` (the f4t member, governed by DR-CP-AGE-1 and held under RG-C-006): a record using that name refuses (`field_unknown` at record validation, `composition_record_invalid` at the decision), a caller using it refuses `composition_caller_invalid`, and an identity payload using it refuses (`field_missing` / `field_unknown`). There is no shared member, family id or selection with the f4t tolerance. Whether the DR-CP-AGE-1 exclusion text extends to `ObservationPolicy.clock_tolerance_seconds` is AR-1 (section 8); this change assumes it does not and keeps the two names separate so either ruling can be honoured.
- Composition as 2.2 (min, same detail rule with the tolerance member name).
- Operator consequence: lowering the tolerance can add `observation_time_future` holds under clock skew between the destination and the control plane.
- Identity row: kind `scalar-int`.

The two observation scalars are independent records and selections (the engine allows one identity member per family); atomicity across them is a consumer concern, and each is independently monotone.

## 3. Profile `V8` and the thin public modules

`engine/profiles.py` gains `CONTRACT_V8 = "r08-v8"`, `SELECTION_DOMAIN_V8 = b"ocs-reg/r08-v8/selection\n"`, `EFFECTIVE_DOMAIN_V8 = b"ocs-reg/r08-v8/effective-policy\n"` and `V8` (three families in the table order above, `family_schema_revision` 1 each, version member `family_schema_revision`). `V7`, `V6_COMPAT` and `PROFILES` are unchanged.

| Module | Purpose |
|---|---|
| `v8_decision.py` | `verify_and_decide_v8(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission=None) -> PolicyDecision` |
| `v8_policy_identity.py` | `effective_policy_digest(family, payload, contract_version="r08-v8")`, `effective_preimage`, `validate_effective_payload`, `deny_all_dimensions`, `registered_family_version`, `IdentityRefusal` |
| `v8_families.py` | `FAMILIES_V8`, `lookup_v8`, `CONTRACT_V8`, `table_for_contract_version_v8`, `compose_v8`, `compose_for_v8` |

Each public function is a single `return` of an engine call (tested by AST). As for v3 to v7, `families.table_for_contract_version("r08-v8")` is `contract_unsupported`; the engine is the only implementation of the orchestration.

## 4. Engine delta (additive)

- `engine/profile.py`: `KINDS` gains `"scalar-int"` (and one comment line is extended).
- `engine/identity.py`: one new `elif row.kind == "scalar-int":` branch in `validate_effective_payload`, before the existing `else:  # scalar-enum`: `type(value) is int` (else a type refusal at the member), then `row.is_value(value)` (else `field_invalid`). The `classmap-enum` and `scalar-enum` branches are byte-unchanged, so `V7` and `V6_COMPAT` behave identically (the merged `V6_COMPAT` differential, the r08-v7 identity vectors and the v6 vectors pass unchanged; section 9). The canonical encoder already carries exact ints.
- `engine/profiles.py`: the `V8` block (section 3) and a docstring paragraph.
- Two new engine modules (`families_anchor.py`, `families_observation.py`) and three new thin modules (`v8_*.py`).

## 5. Identity (version-specific)

Selection signing input: `b"ocs-reg/r08-v8/selection\n" + canonical_bytes(statement)`. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v8/effective-policy\n"` + canonical bytes of `{effective_policy_profile "ocs-effective-policy/1", contract_version "r08-v8", family, family_schema_revision 1, deny_all [], effective}`. Pinned vectors (independent encoder, `docs/family-migration/final-three-prep/evidence/genvec8.py`): `tests/vectors/r08v8/identity_vectors.json` (nine vectors: anchor and no_change; max age 1, 60, 300 and the token ceiling; tolerance 0, 5 and the token ceiling). Signed vectors (real Ed25519, SYNTHETIC test keys): `tests/vectors/r08v8/signed_selection_vector.json`. These digests are PROTOTYPE-grade until the Architect fixes members, domains and ranges (D-C1, D-C2, D-C6); a changed member name, domain or range changes them.

## 6. Frozen baseline and allowlisted edits

`tests/vectors/r08v8/frozen_baseline_manifest.json` (generator `docs/family-migration/final-three-prep/evidence/genman8.py`) extends the r08-v7 manifest with every r08-v7 module, unedited engine module, contract document, test and vector (hashes from `git show 67512a71546748cd888e4cf790485ea0bef9199a:<path>`; 213 files): `r08-v1` .. `r08-v7` are byte-identical to main. The three engine files with additive edits are recorded with their baseline hash and the exact line-level edit; `tests/test_r08v8_frozen_baseline.py` reverses the edit and recovers the baseline byte for byte, and pins that only the listed baseline lines were replaced.

Allowlist-only edits to existing guard tests (not in any manifest, no assertion weakened): `tests/test_ext_s1_5_identity_module.py` (five new permitted module paths) and `tests/test_r08v7_frozen_baseline.py` (`ENGINE_MODULES` gains the two new engine family module names). No existing test that pins `len(V7.families) == 1` or the blocked-family sets changes, because `V7` is not touched.

## 7. What the Registry cannot know (consumer-owned)

The Registry cannot see the host profile, the freshness profile, the host `policy_binding` state, the host observation policy, the clock skew or the destination. Whether a host value may be narrowed at all, how a refusal is reported, the ordering of these selections against other composed families (the anchor flag lives in the freshness profile that the age composition rebuilds), and the host-side refusal names are Control Plane design and are not specified or implemented here.

## 8. Architect decisions required (all unresolved)

| Id | Decision | This preparation assumes |
|---|---|---|
| AR-1 | Does the DR-CP-AGE-1 `clock_tolerance_seconds` exclusion extend to `ObservationPolicy.clock_tolerance_seconds`? | No (recommended by the reconciliation); a separate member and family keep either ruling honourable. If yes, family 2.3 is withdrawn from `V8`. |
| D-C1 | Registry tolerance 0 admitted, or floor 1 | Admit 0 (source `ge=0`). Floor 1 changes `TOLERANCE_MIN`, the tolerance identity vectors and tests. |
| D-C2 | Ceiling 2147483647 as the structural token range (no host ceiling exists) | Reuse `common.MAX_INT`, stated as not a host bound. |
| D-C3 | A host value above 2147483647 refuses the whole caller (not narrowable) | Accept (fail closed). |
| D-C4 | Anchor residual (purpose-input 2x window) and freshness-member ownership | Not closed here; documented. Accept the residual, or keep the anchor family BLOCKED. |
| D-C5 | `r08-v7` additive versus a `r08-v8` successor; v7 freeze | `r08-v8` successor (this change). If v7 is unfrozen and additive is chosen instead, the three families move into `V7` and nine pinned v7 assertions are rewritten; this draft is then superseded. |
| D-C6 | Family ids and member names (`f5-` prefix; `observation_` member prefix) | As proposed. |
| D-06 | Binding of ObservationPolicy (workflow-local, persisted field, or approval preimage) | Not chosen; B and C require Architect authorization and F3 requalification. Until decided the observation families do not give a persisted-bound guarantee. |
| D-07 | 60 versus 300 ordering | None required; the Registry asserts none. |

## 9. Evidence

Tests (`tests/test_r08v8_*.py`, `tests/r08v8_support.py`): `anchor_family` (validation incl. hostile inputs, exhaustive 2x2 composition), `observation_families` (strict-int validation, boundaries 0/1/2147483647/2147483648, grid composition, caller refusal, alias refusal), `policy_identity` (independent-encoder vectors, refusals, additive `scalar-int`), `engine_profile` (profile content, v7 untouched, thin bindings by AST), `decision_path` (real synthetic Ed25519: key revocation, withdrawal, expiry, wrong scope/operation/family, label swaps, tamper, signed vector), `cross_version` (v2..v8 entry points; v7 refuses the three ids; v8 refuses irreversibility; V6_COMPAT smoke), `frozen_baseline` (manifest and additive-edit reversal), `ast_scan` (no interpreter, I/O, clock, randomness, mutable global or new reason code). Counts, mutation results (`mut_r8.py`, raw logs) and whole-suite comparison against a clean worktree of main with the same interpreter are in `docs/family-migration/final-three-prep/evidence/SUMMARY.txt`.

## 10. Limitations

- BUILDER_TESTED only. Registry-side only. No Control Plane consumer, no activation, nothing is counted IMPLEMENTED in the migration ledger.
- The two observation scalars have no persisted binding (D-06); the anchor residual (D-C4) is open.
- The pre-existing failure `tests/test_r08v7_frozen_baseline.py::test_every_other_committed_registry_file_is_unchanged_from_the_baseline_except_the_allowlisted_guards` exists on main (documents changed after the r08-v6 baseline by #72) and is unchanged by this change; `test_installed_cryptography_matches_the_test_only_lock` fails in this environment on main and branch alike.
