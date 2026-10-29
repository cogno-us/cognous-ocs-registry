# `r08-v8` contract: a compatible successor carrying ONLY the three remaining families, on the existing unified engine

Status: APPROVED CANDIDATE: Architect-selected successor (D-C5, 2026-10-29) for the three families; BUILDER_TESTED; non-authorizing; not independently qualified; independent Tier 1 qualification DEFERRED, NOT WAIVED; changes still require F3 requalification, refreeze and re-review before acceptance. Nothing in this document is a security clearance, certification or statement of production readiness, and no independent qualification has been performed (not by the builder, the lead or CI). Registry-side only: no Control Plane consumer exists.

Provenance and status of this change (verifiable from git):

- Work package OCS-REG-FINAL3. The Architect authorization record and contract freeze is `docs/family-migration/final-three/02-architect-authorization-and-contract-freeze-2026-10-29.md` (Registry PR #75). Its section 1 records the Architect decisions D-06 (Option B), D-07 (Option A), AR-1 and D-C5; its section 2 records D-C1, D-C2, D-C3, D-C4 (moot) and D-C6 as resolutions made by the Lead Builder inside that authorization, listed so the Architect can overrule them in one consolidated review. This contract implements section 3 of that freeze.
- This branch (`r08-v8-remaining-families-prep`) carries Registry draft PR #77 (head `4df3a656cd82ef109169c52c3444e8ed8cf2ec4f`, unmerged, draft) merged with Registry `main` `b3eb7fe2b2a676580c293d21df688323fd2f0620` (local merge commit `1ec324a461023912c606107dd859e2c3a5f9202f`), plus the commits made in this finalization. `main` `b3eb7fe` differs from `67512a71546748cd888e4cf790485ea0bef9199a` (the frozen-baseline commit used by the manifest) only by two added plan documents under `docs/plans/` (#74); the frozen manifest hashes no file under `docs/plans/` and needed no regeneration for that (section 6). Nothing is merged to `main` and no pull request is created or changed by this document; merging remains an Architect-gated action (freeze record section 8, order: #75, #77, CP #94, CP D-07, CP D-06, CP consumers).
- Governing documents: Engineering Constitution baseline for this work package `230c0aff1c2d1e054652cfc1be175147260b8aae` (freeze record header), Static Migration Plan v1.1 section 12, Engineering Plan v1.5, adopted audit (Registry PR #60), `docs/r08-v7-contract.md` (the engine this builds on), the family definitions annex (`docs/family-migration/final-three/annex/C-ar1-observation-policy-and-registry-family-definitions.md`).

## 1. What this change is and is not

IS: a new profile `V8` (contract `r08-v8`) on the existing parameterised engine `registry_successor/engine/`, carrying exactly three families, each with schema revision 1:

| Family id | Payload member | Host field (Control Plane, read only) |
|---|---|---|
| `f5-anchor-deadline-to-inputs-policy` | `anchor_deadline_to_inputs` | `FreshnessProfile.anchor_deadline_to_inputs` |
| `f5-observation-max-age-policy` | `observation_max_age_seconds` | `ObservationPolicy.max_age_seconds` |
| `f5-observation-clock-tolerance-policy` | `observation_clock_tolerance_seconds` | `ObservationPolicy.clock_tolerance_seconds` |

IS NOT:

- It does NOT enable any consumer. Registering a family in a Registry profile makes a Registry record and signed selection decidable; it adds no enforcement anywhere. The Control Plane consumers for these three families are NOT implemented by this change.
- It does NOT change `r08-v7` or any frozen `r08-v1` .. `r08-v7` behaviour (section 6). `V7` still registers exactly one family, irreversibility; a v7 record or selection naming any of the three family ids still refuses `family_unsupported` (tested). `PROFILES` is unchanged and `V8` is not a member of it.
- It does NOT re-register irreversibility or any earlier family. Under `r08-v8` irreversibility refuses `family_unsupported`, and a genuine v7 document refuses `contract_unsupported` (tested). Irreversibility stays under `r08-v7`.
- It adds NO new reason code. Every refusal uses the existing closed vocabulary (tested by an AST scan and an emitted-literal pin).
- It does NOT persist or bind any observation value. Observation values are bound by the Control Plane D-06 effective-configuration binding (`effective-configuration-binding/0.1`, freeze record section 4), NOT by this contract; that binding is a Control Plane change that is not part of this change and is not implemented here. A signed Registry selection by itself is not a persisted binding.
- It does NOT close the purpose-observation residual. The anchor family can only add the anchor flag. The residual (with the anchor flag set and no `policy_binding`, the purpose-input window can still be the 2x window) is closed only together with the separately authorized D-07 Control Plane correction (`runtime_authority.py`, freeze record section 6). This contract alone does not close it, and until that Control Plane change is merged and qualified no closure is claimed.
- The numeric ranges are STRUCTURAL REGISTRY TOKEN RANGES, not host bounds (D-C2). 2147483647 is `common.MAX_INT`, the ceiling already used by the Registry's canonical integer range and by `v2_age_bounds.AGE_MAX`; the Control Plane has no such ceiling for these fields. A host value above the token range is not narrowable: the whole caller refuses (D-C3); it is never clamped or rewritten.

## 2. The three families

Common to all three: `enforcing_component` is `control-plane`; evaluator binding `(common.EVALUATOR_ID, common.EVALUATOR_BINDING)` (the registered reference, as r08-v7); the only composition operator is `intersection` (the frozen dispatch name for narrowing; any other operator refuses `composition_operator_unsupported`); `deny_all` is never set and the family is not a deny-all dimension; exact types only (`type(x) is str` or `is int`; no bool or float coercion, no case folding, no clamping, no defaults, no str or int subclass); every refusal carries no effective policy and an invalid caller is never replaced.

Payload validator codes (types before values): not an exact dict or a non-`str` key `field_type_invalid`; an extra key `field_unknown`; an absent key `field_missing`; a wrong value type `field_type_invalid`; a value outside the closed domain `field_invalid`. Composer codes: `composition_operator_unsupported`, `composition_record_invalid` (record not ok, not an exact dict, or payload invalid), `composition_family_unsupported` (record family mismatch), `composition_caller_invalid`. The composer works on a validated copy of the Registry payload and a single bounded snapshot of the caller (at most two items are consumed from a hostile mapping); a deterministic test mutates the live payload between validation and use and shows the copy is what composes.

### 2.1 `f5-anchor-deadline-to-inputs-policy` (module `engine/families_anchor.py`)

- Payload: exactly `anchor_deadline_to_inputs`, an exact `str` in the closed vocabulary `anchor` | `no_change`. A JSON boolean is `field_type_invalid`; the vocabulary names no false and the Registry value can never assert false.
- Order: `anchor` (stricter) < `no_change` (looser). Composition: effective = `anchor` if EITHER side is `anchor`. A Registry `no_change` over a caller `anchor` yields `anchor`, reported in `detail` as `registry_value_not_narrowing:anchor_deadline_to_inputs` (section 2.4).
- Caller: exactly `{"anchor_deadline_to_inputs": "anchor" | "no_change"}`; the consumer maps the host bool to the exact strings (a bool caller refuses `composition_caller_invalid`).
- Identity row: kind `scalar-enum` (existing; no engine change for this family).

### 2.2 `f5-observation-max-age-policy` (module `engine/families_observation.py`)

- Payload: exactly `observation_max_age_seconds`, a strict `int`, `1 <= v <= 2147483647` (floor follows the host `gt=0`). 0, negatives, bool, float, str, None, bytes, Decimal, int subclasses and values above the token range refuse.
- Composition: `effective = min(caller, registry)`; a Registry value above the caller yields the caller value with `detail = registry_value_not_narrowing:observation_max_age_seconds`; equal reports nothing. A caller outside `1..2147483647` (including a host value above the token range, or a host `None` policy) refuses the whole caller `composition_caller_invalid`: nothing is narrowed.
- The Registry asserts no ordering between 60 and 300 (D-07 ordering item; the freeze record D-60/300 row).
- Operator consequence: lowering the value can add `observation_stale` holds on reconcile (never a retry); it cannot turn a hold into a pass.
- Identity row: kind `scalar-int` (additive, section 4).

### 2.3 `f5-observation-clock-tolerance-policy` (module `engine/families_observation.py`)

- Payload: exactly `observation_clock_tolerance_seconds`, a strict `int`, `0 <= v <= 2147483647` (floor follows the host `ge=0`). A Registry value of 0 is admitted (D-C1: "no future allowance"; not a deny-all).
- AR-1 (Architect-decided): `ObservationPolicy.clock_tolerance_seconds` is distinct from the held constructor tolerance, and the constructor exclusion does not automatically extend to it. The member name MUST NOT alias the held constructor tolerance member `clock_tolerance_seconds` (the f4t member, governed by DR-CP-AGE-1 and held under RG-C-006): a record using that name refuses (`field_unknown` at record validation, `composition_record_invalid` at the decision), a caller using it refuses `composition_caller_invalid`, and an identity payload using it refuses (`field_missing` / `field_unknown`). There is no shared member, family id or selection with the f4t tolerance. The constructor clock tolerance is NOT narrowable by anything in this contract.
- Composition as 2.2 (min, same detail rule with the tolerance member name).
- Operator consequence: lowering the tolerance can add `observation_time_future` holds under clock skew between the destination and the control plane.
- Identity row: kind `scalar-int`.

The two observation scalars are independent records and selections (the engine allows one identity member per family); atomicity across them is a consumer concern, and each is independently monotone.

### 2.4 Exact `detail` rule

`CompositionResult.detail` is `registry_value_not_narrowing:<member>` exactly when the Registry value is strictly looser than the caller value, and the empty string otherwise. Anchor: iff the Registry says `no_change` and the caller says `anchor` (the effective value is then the caller's `anchor`); every other pair reports nothing. Ints: iff Registry value `>` caller value (the effective value is then the caller's); equal or lower reports nothing. The detail is informational; it is not a refusal and not a reason code.

## 3. The surface the Control Plane consumer calls

All of these are public names in `registry_successor/`. A consumer must not import `registry_successor.engine.*` (engine internals) or any underscore name; everything needed is below. All functions are pure (no I/O, clock, randomness or mutable state) and never raise on hostile input except where stated.

### 3.1 `registry_successor/v8_decision.py`

```
verify_and_decide_v8(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission=None) -> PolicyDecision
```

There is no `contract_version` parameter (hardwired `r08-v8`). It takes raw record and selection TEXT, parses and verifies both at one `now`, and composes only on success. Result type `registry_successor.decision.PolicyDecision` (frozen dataclass: `kind, effective, deny_all, deny_all_fields, code, detail, caller_unchanged, operationally_authorized`; a refusal that carries a typed sub-cause is `TypedPolicyDecision`). `kind` is one of `applied` (success; `effective` is `{<member>: <value>}`, `deny_all` False, `code` None), `required_policy_unavailable` (participation `required` refusal: `effective` None, `caller_unchanged` False, `code` the reason) or `overlay_not_applied` (participation `optional` refusal: `effective` is the caller policy normalized by the first table family that accepts its shape, else the caller unchanged; `caller_unchanged` True; not denial). `operationally_authorized` is always False and `deny_all` is never True (tested on every outcome). `applied_deny_all` is not reachable for these families. A withdrawn selection is never an application (`selection_withdrawn`). An unknown or non-`required`/`optional` participation refuses `participation_mismatch`.

### 3.2 `registry_successor/v8_families.py`

- `CONTRACT_V8 == "r08-v8"`; `FAMILIES_V8` (a read-only mapping family id to `FamilySpec`, in table order); `lookup_v8(family) -> Optional[FamilySpec]` (exact string equality; None otherwise; never raises).
- Family id constants: `FAMILY_ANCHOR_V8`, `FAMILY_OBSERVATION_MAX_AGE_V8`, `FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8` and the tuple `FAMILY_IDS_V8` (table order; equal to `tuple(FAMILIES_V8)`).
- `table_for_contract_version_v8(version) -> TableSelection` (anything but exactly `r08-v8` refuses `contract_unsupported`); `compose_v8(caller, record, operator="intersection") -> CompositionResult`; `compose_for_v8(version, caller, record, operator="intersection") -> CompositionResult`.
- `compose_v8` and `compose_for_v8` take a validated record object (`ok`, `record`); a consumer that needs signed, verified application calls `verify_and_decide_v8`, not these.

### 3.3 `registry_successor/v8_policy_identity.py`

- `CONTRACT_VERSION == "r08-v8"`, `EFFECTIVE_PREFIX == b"ocs-reg/r08-v8/effective-policy\n"`, `IDENTITY_FAMILIES`, `REGISTERED_CONTRACT_VERSIONS == ("r08-v8",)`.
- `registered_family_version(family, contract_version) -> int`: the family schema revision (1 for all three under exactly `r08-v8`); `IdentityRefusal` otherwise.
- `effective_policy_digest(family, payload, contract_version="r08-v8") -> str` (`"sha256:" + 64 lowercase hex`), `effective_preimage(family, payload, contract_version="r08-v8") -> dict`, `effective_digest_of_preimage(preimage) -> str`, `validate_effective_payload(family, payload) -> dict`, `deny_all_dimensions(family, payload) -> list` (always `[]` here), `IdentityRefusal` (exception whose `.args[0]` / `.code` is the reason).
- `payload` is the EFFECTIVE value as the consumer holds it after composition, for example `{"observation_max_age_seconds": 60}` (not a record).

### 3.4 Schema revision, effective-policy digest preimage and domains

Family schema revision: 1 for each family (`registered_family_version`). The version member in the preimage is the integer `family_schema_revision`. Effective-policy digest: `sha256` over `b"ocs-reg/r08-v8/effective-policy\n"` followed by the canonical bytes of exactly

```
{"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v8", "family": <family id>, "family_schema_revision": 1, "deny_all": [], "effective": {<member>: <value>}}
```

Selection signing input: `b"ocs-reg/r08-v8/selection\n" + canonical_bytes(statement)`. Example (pinned in `tests/vectors/r08v8/identity_vectors.json`, recomputed by an independent encoder): the digest of `{"observation_max_age_seconds": 60}` for `f5-observation-max-age-policy` is `sha256:5c4f58a3713719a5399534314927a843228f59da09b0bb362202239313a02bdc`. These domains, members, ranges and digests are frozen by the freeze record (D-C1, D-C2, D-C6); a change to any of them changes the digests and is a contract change needing the Lead and the Architect.

### 3.5 Filling a D-06 binding `families` entry

The freeze record (section 4) requires each declared family entry `{slot, family_id, contract_version, family_schema_revision, effective_policy_digest}`. From this surface: `family_id` from `FAMILY_IDS_V8`; `contract_version` from `CONTRACT_V8` (`"r08-v8"`); `family_schema_revision` from `registered_family_version(family_id, CONTRACT_V8)` (exact `int`, never bool); `effective_policy_digest` from `effective_policy_digest(family_id, effective_payload)` (`sha256:` + 64 lowercase hex, never all-zero). `slot` is a Control Plane concept the Registry does not define or know. The consumer, not the Registry, validates the entry before hashing it into the binding (freeze record section 4). Tested: `tests/test_r08v8_engine_profile.py::test_public_family_id_constants_match_the_profile_table_and_expose_the_binding_fields`.

### 3.6 Refusal reasons a consumer can see

No reason code is added; the vocabulary is the existing closed set. On the decision path the reasons seen in tests include `composition_caller_invalid`, `composition_record_invalid`, `composition_family_unsupported`, `composition_operator_unsupported` (composer only), `family_unsupported`, `contract_unsupported`, `participation_mismatch`, `selection_missing`, `selection_withdrawn`, `signature_invalid`, `digest_mismatch`, `kind_unsupported`, `supersession_invalid`, `selection_consumer_mismatch`, `selection_scope_mismatch`, `selection_operation_mismatch`, record parse reasons (`json_malformed`, `json_duplicate_key`, `input_not_text`) and record field reasons (`field_unknown`, `field_missing`, `field_type_invalid`, `field_invalid`), plus the existing key, trust, revocation and expiry reasons exercised in `tests/test_r08v8_decision_path.py`. Identity functions raise `IdentityRefusal` with `family_unsupported` (a family not in the v8 table, including irreversibility) or `contract_unsupported` (a contract version other than `r08-v8`), or the payload codes above.

## 4. Host-precondition semantics: what the Registry checks and what it deliberately does not

The Registry checks ONLY the shape and domain of the caller value it is handed, and the record, signature, scope, trust and time. It never reads a Control Plane object.

Anchor (`f5-anchor-deadline-to-inputs-policy`):

- Registry checks: the caller is exactly `{"anchor_deadline_to_inputs": "anchor" | "no_change"}` (exact dict-like mapping with one `str` key, exact `str` value in the vocabulary). Anything else (None, a bool, an extra key, a subclass value) refuses `composition_caller_invalid`.
- The host `FreshnessProfile` must already exist. The Registry never invents, creates or supplies a `FreshnessProfile`, and never supplies a missing host profile: there is no spelling in the caller or the payload for "no profile". A consumer that has no `FreshnessProfile` must not call the decision as if it had one and must itself refuse or hold; if it passes a missing caller the Registry refuses `composition_caller_invalid` (tested for `None`).
- No `PolicyBinding` requirement is placed on the host by this contract, because D-07 (the Control Plane correction) removes the dependency of purpose-observation anchoring on `PolicyBinding` presence. That dependency is a Control Plane fact; the Registry does not check for a `PolicyBinding`, and until D-07 is merged the residual in section 1 stands.
- The consumer, not the Registry, enforces the host preconditions, maps the host bool to the two strings and back, and rebuilds the freshness profile (the anchor flag lives in the freshness profile that the age composition rebuilds, so ordering against other composed families is a consumer concern).

Observation families:

- Registry checks: the caller is exactly `{<member>: <strict int in the family range>}`. A host `ObservationPolicy` that is missing (None), a value outside the range (including a legal host value of 2**31 or more, D-C3), a bool, float or str, or an extra or aliased member refuses `composition_caller_invalid`; nothing is narrowed and the host value is never replaced.
- The Registry never supplies a missing host `ObservationPolicy` (a missing host policy remains the host's own hold, `observation_policy_missing`, freeze record section 7). Whether a host value may be narrowed at all, and how a refusal is reported, is Control Plane design.
- The Registry does not bound the host: it neither knows nor imposes the host's own limits. The pre-existing extreme-tolerance `OverflowError` in protected `bounded.py` is a host fragility recorded in `docs/family-migration/final-three/04-defect-record-extreme-tolerance-overflow-2026-10-29.md`; it is neither introduced nor fixed here and no policy ceiling is silently introduced.

What the Registry cannot know (consumer-owned): the host profile, the freshness profile, the host `policy_binding` state, the host observation policy, the clock skew, the destination, the D-06 binding contents, the `slot` of a family entry, and the ordering of these selections against other composed families.

## 5. Profile `V8`, engine delta and identity

`engine/profiles.py` gains `CONTRACT_V8 = "r08-v8"`, `SELECTION_DOMAIN_V8`, `EFFECTIVE_DOMAIN_V8` and `V8` (three families in the table order of section 1, `family_schema_revision` 1 each, version member `family_schema_revision`). `V7`, `V6_COMPAT` and `PROFILES` are unchanged. As for v3 to v7, `families.table_for_contract_version("r08-v8")` is `contract_unsupported`; the engine is the only implementation of the orchestration. Each public function in `v8_*.py` is a single `return` of an engine call (tested by AST); the public id constants are plain re-exports.

Engine delta (additive):

- `engine/profile.py`: two lines are each replaced by a longer line: the `KINDS` tuple gains `"scalar-int"`, and the comment on `IdentityRow.kind` names it.
- `engine/identity.py`: one insertion of five lines, a new `elif row.kind == "scalar-int":` branch in `validate_effective_payload` before the existing `else:  # scalar-enum`: `type(value) is int` (else a type refusal at the member), then `row.is_value(value)` (else `field_invalid`). The `classmap-enum` and `scalar-enum` branches are byte-unchanged, so `V7` and `V6_COMPAT` behave identically (the `V6_COMPAT` differential, the r08-v7 identity vectors and the v6 vectors pass unchanged).
- `engine/profiles.py`: one replaced docstring header line, one added docstring paragraph, two added import lines, and the `V8` block.
- Two new engine modules (`families_anchor.py`, `families_observation.py`) and three new thin modules (`v8_decision.py`, `v8_families.py`, `v8_policy_identity.py`).

Pinned vectors (independent encoder `docs/family-migration/final-three-prep/evidence/genvec8.py`): `tests/vectors/r08v8/identity_vectors.json` (nine vectors: anchor and no_change; max age 1, 60, 300 and the token ceiling; tolerance 0, 5 and the token ceiling) and `tests/vectors/r08v8/signed_selection_vector.json` (real Ed25519, SYNTHETIC test keys). Unchanged in this finalization.

## 6. Frozen baseline and allowlisted edits

`tests/vectors/r08v8/frozen_baseline_manifest.json` (generator `docs/family-migration/final-three-prep/evidence/genman8.py`) extends the r08-v7 manifest with every r08-v7 module, unedited engine module, contract document, test and vector (213 files hashed from `git show 67512a71546748cd888e4cf790485ea0bef9199a:<path>`): `r08-v1` .. `r08-v7` are byte-identical to that baseline. The three engine files with additive edits are recorded with their baseline hash and the exact line-level edit; `tests/test_r08v8_frozen_baseline.py` reverses the edit and recovers the baseline byte for byte, and pins that only the listed baseline lines were replaced. The manifest hashes only files that existed at the baseline and are not edited here; the two plan documents added to `main` by #74 are new files, are not hashed, and the tripwire (`git diff --diff-filter=MDRT` against the baseline) ignores added files. Regenerating the manifest with `genman8.py` against `b3eb7fe` therefore yields identical hashes; it was regenerated once in this finalization only because the recorded `profiles.py` docstring paragraph changed text (status wording), and the diff of the manifest is that one text and the `profile` label.

Allowlist-only edits to existing guard tests (not in any manifest, no assertion weakened, unchanged in this finalization): `tests/test_ext_s1_5_identity_module.py` (five new permitted module paths) and `tests/test_r08v7_frozen_baseline.py` (`ENGINE_MODULES` gains the two new engine family module names). A comment in the former still says "DRAFT / GATED"; it is left as is because it sits in an existing guard test.

## 7. Evidence

Tests (`tests/test_r08v8_*.py`, `tests/r08v8_support.py`): `anchor_family` (validation incl. hostile inputs, exhaustive 2x2 composition, post-validation-mutation defence), `observation_families` (strict-int validation, boundaries 0/1/2147483647/2147483648, grid composition, caller refusal, alias refusal, post-validation-mutation defence), `policy_identity` (independent-encoder vectors, refusals, additive `scalar-int`), `engine_profile` (profile content, v7 untouched, thin bindings by AST, public id constants), `decision_path` (real synthetic Ed25519: key revocation, withdrawal, expiry, wrong scope/operation/family, label swaps, tamper, signed vector), `cross_version` (v2..v8 entry points; v7 refuses the three ids; v8 refuses irreversibility; V6_COMPAT smoke), `frozen_baseline` (manifest and additive-edit reversal), `ast_scan` (no interpreter, I/O, clock, randomness, mutable global or new reason code). Counts, mutation results (`mut_r8.py`, raw logs, including the earlier runs kept unchanged) and the whole-suite comparison are in `docs/family-migration/final-three-prep/evidence/SUMMARY.txt`; the CI Scope Declaration is section 9.

## 8. Limitations

- BUILDER_TESTED only. Registry-side only. No Control Plane consumer, no activation; nothing here is counted as implemented or independently accepted (accounting stays 16/19 integrated, 3 remaining, 0 independently accepted until enforcement implementations merge).
- The observation values are bound only by the Control Plane D-06 binding, which this change does not implement; the binding guards configuration drift, not an attacker who can rewrite the store, and gives no anti-rollback guarantee (freeze record section 5). The anchor residual is closed only together with the separately authorized D-07 correction.
- Anti-rollback, signed decision store, the constructor clock tolerance, Registry #58/#59, Control Plane #87, Ed25519 #26/#34, V09, publication, release and production remain held or separate (freeze record section 1).
- Pre-existing failures on `main` (not caused or touched by this change, NOT fixed): `tests/test_r08v7_frozen_baseline.py::test_every_other_committed_registry_file_is_unchanged_from_the_baseline_except_the_allowlisted_guards` (it diffs against the r08-v6 head `42a666328b974a7581013358bcf8bc7b9eac7761` and sees `docs/family-migration/contract-version-allocation.md` and `docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`, edited by #72 after that baseline) and `tests/test_adapter_ed25519.py::test_installed_cryptography_matches_the_test_only_lock` (the installed `cryptography` differs from the lock in this environment).

## 9. CI Scope Declaration

- Risk tier: T3 (shared contract and boundary).
- Exact head and dependencies: the head is the last commit of branch `r08-v8-remaining-families-prep` in the evidence directory's `SUMMARY.txt` (a document cannot name the commit that contains it); base Registry `main` `b3eb7fe2b2a676580c293d21df688323fd2f0620`; carried draft PR #77 head `4df3a656cd82ef109169c52c3444e8ed8cf2ec4f`; local merge `1ec324a461023912c606107dd859e2c3a5f9202f`. Depends on Registry #75 (decision and freeze records) being merged first (freeze record section 8). Python: the scratchpad `venv-g1-212` interpreter (3.13.17; pytest, pynacl). No dependency on any Control Plane change.
- Tests executed: see `SUMMARY.txt` (new r08v8 tests, `tests/test_r08v7_engine_differential.py`, the frozen baselines, mutation harness `mut_r8.py` over the new modules, the whole Registry suite once at the end).
- Evidence reused: none. Every result in `SUMMARY.txt` was produced against the exact head recorded there, with one exception stated there if any (earlier mutation logs of the draft are kept as history and are NOT counted as evidence for this head).
- Not run, and why: independent Tier 1 qualification and F3 requalification (deferred, not waived; the builder does not qualify its own work); any Control Plane test (no Control Plane file is touched); paid or external testing (not authorized).
- Original versus new failures: original (on `main`) two failures listed in section 8; new failures: none (see `SUMMARY.txt`).
- Remaining qualification obligations: independent Tier 1 qualification of this successor; F3 requalification, refreeze and re-review before acceptance; the Control Plane D-06 (F3-A) and D-07 (F3-B) qualification tracks (`docs/family-migration/final-three/03-f3-qualification-expectations-F3A-F3B-2026-10-29.md`); the Architect's consolidated review of the Lead Builder sub-decisions (freeze record section 2).
