# Worker C: AR-1 for ObservationPolicy and the three Registry family definitions (2026-10-29)

Read-only against all repos. Baselines: Control Plane main b7eb11a (`m12/r8_cp`), Registry main 67512a7 (`m12/r8_reg`). Interpreter: `venv-g1-212`.
Scratch artifacts (outside any repo): `final3/probes/*.py`, `final3/proto_reg/` (a COPY of Registry main with a prototype of the three families; never a repo edit).
"V" = verified by running code; "R" = verified by reading. Nothing here is implemented in a repo, authorized, or qualified. Anything that changes a persisted-decision schema, an
approval preimage or a protected evaluator is labelled "requires Architect authorization and F3 requalification".

## 0. Bottom line

1. Both ObservationPolicy fields are strictly monotone: lowering either value can only add refusals (V, grid of 3 host configs x all lower pairs x 21 offsets: 0 violations).
2. AR-1 for `ObservationPolicy.clock_tolerance_seconds`: the DR-CP-AGE-1 exclusion text (line 8) names the bare string `clock_tolerance_seconds` and the audit/plan scope it to the constructor
   tolerance (RG-C-006). Nothing in the source tree says it covers the ObservationPolicy field; but nothing affirmatively permits it either. This is a genuine ruling, not a reading. Section 1.6.
3. Registry domain should be strict `int`, floor 1 (max_age) / 0 (tolerance), and NO host ceiling exists (V: 10**30 accepted by pydantic). The only structural token range
   already in the Registry is 0..2147483647 (`common.MAX_INT`, `v2_age_bounds.AGE_MAX`). Using it is an Architect decision (AR-2 style), flagged below.
4. Registry cannot supply a policy the host passed as None (V: caller None -> `composition_caller_invalid`; CP None stays a `observation_policy_missing` hold).
5. Smallest compatible boundary for the three families: additive registration in the (unfrozen) `r08-v7` profile does NOT alter any existing family's signing domain, identity digest or accepted
   behaviour (V). It DOES flip three tested "refuses `family_unsupported`" behaviours to "accepts", and the two int families need one new engine identity kind (`scalar-int`). If v7 is frozen, the
   smallest compatible boundary is `r08-v8` carrying only the new families. Section 2.5.
6. The binding gap (D-06) is separate and unchanged: ObservationPolicy is constructor-only and not in the approval/catalogue digest. This report does not choose A/B/C. Section 1.7.

---

## Part 1: AR-1 and the ObservationPolicy family facts

### 1.1 Host definition (R unless noted)
| Item | max_age_seconds | clock_tolerance_seconds |
|---|---|---|
| Declaration | `bounded.py:414` `int = Field(gt=0)`, required, no default | `bounded.py:415` `int = Field(default=5, ge=0)` |
| Class | `ObservationPolicy(BaseModel)` `bounded.py:411-415`, no `model_config`; exported `__init__.py:24,82` | same |
| Construction | ctor arg `observation_policy: ObservationPolicy \| None = None` `bounded.py:1276`, deep copied `:1300`. Only production literal `cli_run.py:510` `ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5)`. All other uses are tests (e.g. `tests/test_bounded_authorization.py:351,666,731,789,1101`, `tests/test_terminal_revocation.py:28` with default tolerance). | same |
| Only consumer | `bounded.py:1925` `(evaluation_time - observed_at).total_seconds() > policy.max_age_seconds` -> `observation_stale` | `bounded.py:1922-1924` `future_limit = reference + timedelta(seconds=policy.clock_tolerance_seconds)`; `observed_at > future_limit` -> `observation_time_future` |
| Recorded trace | `ReconciliationResult.observation_max_age_seconds` `bounded.py:427` (`int \| None = None`), written `:1868,1963` | `...clock_tolerance_seconds` `:428`, written `:1869,1964` |

Grep (V): `observation_policy.` / `policy.max_age_seconds` / `policy.clock_tolerance_seconds` appear in `src` only at `bounded.py:1300,1868-1869,1922,1925,1963-1964`. `local_authority_effect.py:384` uses
the CONSTRUCTOR `workflow.clock_tolerance_seconds`, not this field. The two 5-second defaults (ctor `bounded.py:1275`, policy `:415`) are independent parameters.

### 1.2 Existing host domain (V, `probes/c_probe_obs_domain.py`)
Pydantic LAX int coercion, no `model_config`, `extra` silently ignored, assignment not re-validated.
- `max_age_seconds` accepted: `1`, `True` (-> 1), `"7"`, `" 7"`, `"7.0"`, `3.0`, `b"7"` (-> 7), `2147483647`, `2147483648`, `10**30`, `10**400`. Refused: `0`, `-1`, `False`, `3.5`, `None`, `inf`, `nan`.
- `clock_tolerance_seconds` accepted: `0`, `5`, `True` (-> 1), `False` (-> 0), `"5"`, `5.0`, `2147483647`, `2147483648`, `10**30`. Refused: `-1`, `5.5`, `None`, `inf`.
- Therefore the CP lower bounds are exactly `>= 1` and `>= 0`, there is NO upper bound, and the value types are laxer than a Registry strict `int` (the Registry only reads the post-coercion int the
  host holds, so no mismatch arises: the consumer reads `policy.max_age_seconds`, an `int`).
- Consequence of "no upper bound" (V, `probes/c_probe_obs_reconcile.py`): a host tolerance of `10**12` or `10**30` makes `reconcile()` raise `OverflowError` out of `_reconcile_observation`
  (`reference + timedelta(...)`, `:1922`); `2**31-1` and `2**31` work. A large `max_age` never overflows (float comparison). This is a pre-existing host fragility, not introduced by the Registry;
  a Registry narrowing only reduces it. Worth reporting, not fixing here (protected `bounded.py`).

### 1.3 Semantics, narrowing, and probes (V, `probes/c_probe_obs_reconcile.py`, harness = `tests/test_bounded_authorization.py::observation_workflow` with the policy replaced after construction)
Boundary (host 300/5, `NOW`, one observation):
```
offset -301: hold observation_stale      -300,-299,0,4,5: observed_absent      +6: hold observation_time_future
```
Both comparisons are strict `>`: age == max_age passes; offset == tolerance passes.
- Lowering tolerance 5 -> 3 -> 2 at offset +3: accepted, accepted, `observation_time_future`. At offset +5: tol 5 accepted, tol 4 refused. Only `observation_time_future` is added.
- Lowering max_age 300 -> 100 -> 99 at offset -100: accepted, accepted, `observation_stale`. Only `observation_stale` is added.
- Monotonicity grid: 3 host configs ((10,5),(10,0),(6,3)), every lowered pair, offsets -12..8: 0 cases where lowered accepts what host refuses.
- if/elif (`:1923-1926`): future is judged first, stale only otherwise. Observations up to `tol` in the future have negative age and pass staleness, so tolerance only widens acceptance on the future side; max_age is the sole past-side bound.
- Cross-field (V): max_age=2, tol=10 behaves exactly as the two independent rules (offsets -3 stale; -2..+10 accepted; +11 future). No code orders tolerance against max_age, so NO cross-field rule is needed
  and none must be invented. Lowering one while the other stays at the host value cannot widen anything.

Clock source and future-stamp behaviour (R, `bounded.py:62-63,1305-1311,1875-1888,1920-1922`; V by `tests/test_freshness.py::test_observation_clock_is_decoupled_from_the_evaluation_pass` passing):
- `evaluation_time` is `_now()` (UTC, control-plane clock) unless `allow_test_time`, in which case the caller `now` (UTC-normalised, tz-aware required). Staleness is measured against `evaluation_time`.
- Future limit reference: `evaluation_time`, or `max(evaluation_time, _now())` when `self._freshness is not None` (freshness/0.1 configured). So with freshness active the reference moves with the live service clock;
  lowering tolerance to 0 still only adds refusals but can refuse a destination-stamped observation that is a few ms ahead of the evaluation instant. That is restrictive, never permissive.
- `observed_at` comes from `parse_instant` of the destination-stamped string; naive/malformed/missing times hold with their own reasons (`:1906-1915`).

Missing policy (V, `tests/test_bounded_authorization.py:842-853`; probe "missing policy"): `observation_policy_missing`, `result="hold"`, applied values recorded as `None`. A governed path must never create a
policy the host passed as None. The Registry-side guarantee is the caller normalizer (section 2.3): a caller of `None` is `composition_caller_invalid`. Host side (consumer, outside the Registry): do not
select this family when `observation_policy is None`.

Compatibility with already-recorded observations (V): `ReconciliationResult` rows lacking the two applied-value fields validate as `None`/`None` (probe). A narrowed policy only affects observations
reconciled AFTER it is applied; recorded `accepted` observations are not re-judged (no replay reads the values, 07 doc line 12). So lowering is forward-only; a later, stricter tolerance can make a once-accepted
observation unreproducible by replay, which is the D-06 reproducibility point (1.7), not a safety loss.

### 1.4 Registry domain, bounds and narrowing (proposal; Architect decisions flagged)
- Type: `type(v) is int` exactly (bool, float, str, None, bytes, Decimal, int subclasses, lists refuse), as `v2_age_bounds.py` (`:6-9`, `:63-65`).
- Lower bound (supported by source): max_age >= 1 (`gt=0`), tolerance >= 0 (`ge=0`). A Registry tolerance of 0 is meaningful ("no future allowance"), is not a deny-all, and is source-valid. NOTE this differs from
  the age families, which refuse Registry 0 (`AGE_MIN = 1`, `v2_age_bounds.py:50-51`, because 0 there has deny-all weight). **Architect decision D-C1**: admit Registry tolerance 0 (recommended: source-valid, strictest) or floor at 1.
- Upper bound: none exists in the Control Plane (V). Not invented. Proposal: reuse the existing structural token ceiling `2147483647` (`common.MAX_INT = 2**31-1`, `common.py:28`; `v2_age_bounds.AGE_MAX`,
  `v2_age_bounds.py:51`) ONLY because (a) the Registry's canonical JSON integer range is already bounded there (`OutOfRangeInteger` in `_plain`), (b) a narrowing-only family needs no operational ceiling since the effective
  value is `min(caller, registry)`, and (c) every value the Registry can emit is <= 2147483647, which the host handles (V: 2**31 ran). DR-CP-AGE-1 itself states this is a "technical representation ceiling", "not an
  operational setting" and does not replace Control Plane validation (`docs/decisions/2026-10-25-dr-cp-age-1.md:6,20-24`). **Architect decision D-C2**: confirm that reuse, or direct a different/no ceiling.
  The `docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md:170` AR-2 text says "do not infer 0..2147483647 is a mandatory host bound": this proposal respects that, it is a Registry token range, not a host bound.
- Caller domain: the same range. Host values above 2147483647 (legal in the CP) are `composition_caller_invalid` (fail closed: no narrowing, host value untouched), mirroring DR-CP-AGE-1 decision 7 for the age
  families (`f5-class-age` doc line 74). **Architect decision D-C3**: accept that hosts above 2^31-1 are simply not narrowable.
- Narrowing: `effective = min(caller, registry)`; Registry above caller -> caller, with `detail = registry_value_not_narrowing:<member>`; never above the host; `deny_all` never set.
- 60/300 facts (R): 60 = default of the authority-input ages `status/identity/mandate/approval_max_age_seconds` (`bounded.py:1271-1274`); 300 = the CLI/test literal for this field (`cli_run.py:510`), which has no code default.
  No code compares or orders them (D-07 left open). The Registry asserts NO ordering. Note: an operator may legitimately choose a Registry max_age below or above 60; the min rule keeps it <= host.
- Tolerance vs max_age cross-field: none needed (1.3), none proposed.

### 1.5 Which authority sets which scalar, and what lowering implies for operators
- Lowering max_age: more `observation_stale` holds on reconcile (retry is never eligible, `retry_eligible=False` always at `:1960`), so a too-low Registry value can wedge uncertain-effect reconciliation into holds.
  It cannot turn a hold into a pass. Operator-facing risk only (availability), not authority widening.
- Lowering tolerance: more `observation_time_future` holds under clock skew between destination and control plane.

### 1.6 AR-1: does the historical exclusion apply to this field?
Sources (R): DR-CP-AGE-1 line 8 (`docs/decisions/2026-10-25-dr-cp-age-1.md:8`): "Out of scope and not covered: `identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds`, evidence-obligation
ages (host-owned, unvalidated, never registry-managed)." The same record's table row says `bounded.py:411-415` is `ObservationPolicy.max_age_seconds` (`gt=0`) and "is not an F4/F5 field" (`:12`). Plan v1.1:169-170
(`docs/plans/REGISTRY-FAMILY-MIGRATION-PLAN-v1.1.md`): AR-1 = "Whether CONSTRUCTOR `clock_tolerance_seconds` may become Registry-managed ... Decide separately from `ObservationPolicy.clock_tolerance_seconds`." Audit rule RG-C-006 is the
constructor field (`docs/family-migration/m2/01-migration-backlog.md:35`, "Host constructor ... default 5 ... used in `_fresh`"); the audit notes the ObservationPolicy field is a distinct row ("default 5; distinct from ctor tolerance RG-C-006",
`docs/audit/registry-eligibility-2026-10-28/crosswalk.json:15805`). 01-crosswalk row 19 and 07-commitment doc (`:12`) record the ObservationPolicy field as separate and unauthorised.

Assessment:
- The exclusion's "host-owned, unvalidated, never registry-managed" rationale does NOT fit this field: it is validated (`ge=0`, `bounded.py:415`) and the three adjacent justifications used for the age families
  (validated lower bound, single consumer, strictly monotone, recorded applied value) all hold (1.1-1.3). The ctor tolerance is unvalidated and has three consumers (`_fresh`, `_record_check`, issuance snapshot).
- But the exclusion text is a bare field name with no qualifier, there is no affirmative permission, and the Registry plan says "decide separately". So the correct statement is: **the exclusion does not, on
  its reasoning, extend to the ObservationPolicy field, but a ruling is required that it does not.** I recommend a separate decision record (never an edit of DR-CP-AGE-1, which is historical), e.g. "DR-CP-OBS-1":
  (i) the DR-CP-AGE-1 line-8 exclusion applies to the workflow constructor `clock_tolerance_seconds` only; (ii) `ObservationPolicy.clock_tolerance_seconds` may be Registry-narrowed under min(host, registry); (iii) ranges D-C1/D-C2/D-C3.
- Held f4t (Registry #58 / Control Plane #87) is the constructor tolerance and is NOT touched: different member name (`clock_tolerance_seconds` there; `observation_clock_tolerance_seconds` here), different family id, no shared payload.
  A ruling here must not be read as authorising #58/#87 (`docs/family-migration/unified/01-...:27`).

### 1.7 Binding (D-06) unchanged, stated for completeness (R)
`RuntimeAuthorityProfile` has no observation field (`runtime_authority.py:194-229`, `extra=forbid`); `approval_commitment` and `catalogue_digest` hash the profile only (`:236-250,:473`); `ObservationPolicy` appears only in `bounded.py` and
`cli_run.py:510` (grep V). So a Registry-narrowed ObservationPolicy would be constructor-only: workflow-local, not in the decision/approval digest, not re-validated at effect. Options A (accept as workflow-local with documented non-reproducibility),
B (persisted effective-configuration field) and C (approval preimage) are D-06; B and C require Architect authorization and F3 requalification. The Registry families below are additive to whichever the Architect picks; their effective-policy digest
(2.4) is bound to the Registry decision, not to the Control Plane approval. A consumer that clamps `observation_policy` before `BoundedAuthorizationWorkflow.__init__` (as `GovernedAgeWorkflow` does for F4) needs no protected-file edit
(`registry_f4_age_governance.py:105-123` forwards `**workflow_kwargs`, R in `rec_observation.md` section 4), but without D-06 the value stays unbound. It is NOT recommended to ship the consumer before D-06.

---

## Part 2: Registry family definitions (r08-v7 engine)

### 2.1 Style and constraints read (R)
Reference family: `registry_successor/engine/families_irreversibility.py` (module doc `:1-17`, validators `:57-84`, snapshot/normalizer `:87-109`, composer `:127-149`); profile wiring `engine/profiles.py:26-56`;
`FamilySpec` fields in `families.py` (`family, payload_fields, payload_validator, composer, evaluator_binding, caller_normalizer, enforcing_component`); `IdentityRow` and `ContractProfile.__post_init__`
(`engine/profile.py:35-114`): one identity row per family, `len(row.members) == 1`, `row.members == spec.payload_fields`, kind in `KINDS = ("classmap-enum", "scalar-enum")`, revision rows need `IdentityRow.version_value == FamilyEntry.schema_revision`;
identity validator `engine/identity.py:56-81` supports only a `str` scalar (`scalar-enum`) or class map. Refusal vocabulary is the existing `CODES_V2`; none added (`docs/r08-v7-contract.md:53`).

### 2.2 Prototype (V)
`final3/proto_reg/registry_successor/engine/families_anchor.py`, `families_observation.py` and the profile edits are a scratch prototype (copy, not a repo edit). `probes/c_probe_families.py <root>` runs the matrices below.

### 2.3 Family definitions

**Common to all three**: contract `r08-v7` (or `r08-v8`, 2.5); `enforcing_component = COMPONENT_CONTROL_PLANE` (`"control-plane"`); `evaluator_binding = (c.EVALUATOR_ID, c.EVALUATOR_BINDING)`; operator only `intersection`;
`deny_all` never set; `schema_revision = 1`; exact types (`type(x) is str/int/dict`), no coercion, no default, no case folding, no clamp; every refusal carries no effective policy; an invalid caller is never replaced.
Payload validator codes: not an exact dict / non-str key / wrong value type -> `field_type_invalid`; extra key -> `field_unknown`; absent key -> `field_missing`; value outside the closed domain -> `field_invalid` (types before values).
Composer codes: `composition_operator_unsupported`, `composition_record_invalid` (record not ok / not dict / payload invalid), `composition_family_unsupported` (record family mismatch), `composition_caller_invalid` (caller fails the normalizer), and success.

**A. `f5-anchor-deadline-to-inputs-policy`** (module `families_anchor.py`)
- Host field: `FreshnessProfile.anchor_deadline_to_inputs` (`freshness.py:72`, bool default False, omitted when False). Registry payload: EXACTLY `anchor_deadline_to_inputs`, an exact `str` in `anchor` | `no_change`.
  No JSON boolean (a `true`/`false` is `field_type_invalid`, V), mirroring irreversibility and `terminal_revocation`.
- Order: `anchor` (stricter) < `no_change`. Composition: effective = `anchor` if either side is `anchor`. Registry `no_change` over caller `anchor` -> `anchor`, detail `registry_value_not_narrowing:anchor_deadline_to_inputs`. Cannot assert False.
- Caller normalizer: exactly `{"anchor_deadline_to_inputs": "anchor"|"no_change"}` (consumer maps host True -> `anchor`, False -> `no_change`; a bool caller is `composition_caller_invalid`, V).
- Identity row: `IdentityRow(family, "scalar-enum", ("anchor_deadline_to_inputs",), anc.is_value, VERSION_MEMBER_REVISION, 1)`. Fits the existing `scalar-enum` kind: NO engine change.
- Matrix (V): caller anchor/reg anchor -> anchor; anchor/no_change -> anchor + detail; no_change/anchor -> anchor; no_change/no_change -> no_change; reg `True/False/"true"/"off"/1/None` -> `composition_record_invalid`.
- Host preconditions (consumer, not visible to the Registry; never invent): a `FreshnessProfile` already exists in the host `RuntimeAuthorityProfile.freshness` (rec_anchor Q5: without it the flag cannot be reached; a whole freshness/0.1 profile with lease/reaper/nonce must never be invented);
  profile has no `policy_binding` (families refuse `policy_binding_unsupported`, `registry_governed_policy.py:257-258`); compose after `class_age` since `compose_profile` rebuilds freshness from the host dump. Consumer refusal names (host-side, not Registry codes): `anchor_freshness_profile_required`, `composed_widens_host`, `composed_profile_invalid`, `policy_binding_unsupported` (rec_anchor.md items 1-3).
- Residual (unchanged): the purpose-observation 2x window with anchor True and no `policy_binding` (D-07, `rec_anchor.md`): the family can be defined and implemented, but the "no extension may defeat a narrowed ceiling" goal is not fully met without a protected-file edit or Architect acceptance of the residual. Architect decision D-C4.
- Binding: covered by `approval_commitment`/`catalogue_digest` because the flag is a profile member (rec_anchor Q4).

**B. `f5-observation-max-age-policy`** (module `families_observation.py`)
- Host field: `ObservationPolicy.max_age_seconds`. Payload member name: `observation_max_age_seconds` (prefix so it can never alias the F4 `status_max_age_seconds`/`approval_max_age_seconds` or the held f4t `clock_tolerance_seconds`).
- Registry domain: exact `int`, `1 <= v <= 2147483647` (D-C2). Caller domain: same (D-C3). Registry 0/negative/bool/float/str/None/2147483648 -> `composition_record_invalid` (V); at identity: `True` -> `field_type_invalid`, `0` -> `field_invalid`, `"1"` -> `field_type_invalid` (V).
- Composition: `min(caller, registry)`; Registry 60 over caller 300 -> 60; Registry 300 over caller 60 -> 60 + detail `registry_value_not_narrowing:observation_max_age_seconds`; equal -> same, no detail (V).
- Caller normalizer: exactly one key; caller `0`, `None`, `True`, `"300"`, `2**31`, `10**12` -> `composition_caller_invalid` (V). Host `observation_policy is None` -> caller None -> `composition_caller_invalid` (V): the Registry never supplies a policy.
- Identity row: `IdentityRow(family, "scalar-int", ("observation_max_age_seconds",), obs.is_max_age, VERSION_MEMBER_REVISION, 1)`. Requires the new `scalar-int` kind (2.4).
- Host preconditions: `BoundedAuthorizationWorkflow.observation_policy` is not None (consumer pre-check; else leave as is, the evaluator's `observation_policy_missing` hold is unchanged). Consumer clamps BEFORE `BoundedAuthorizationWorkflow.__init__` (the workflow deep-copies at `:1300`).
- Refusal vocabulary (Registry): the codes above. Consumer-side (not Registry): suggest `observation_policy_required` when the host policy is absent, reusing the existing pattern of the F4 consumer.

**C. `f5-observation-clock-tolerance-policy`**
- Host field: `ObservationPolicy.clock_tolerance_seconds`; member `observation_clock_tolerance_seconds`.
- Registry/caller domain: exact `int`, `0 <= v <= 2147483647` (D-C1: 0 admitted; D-C2; D-C3). Identity row kind `scalar-int`, `is_value = obs.is_tolerance`.
- Composition: `min(caller, registry)`, same detail rule. Registry 0 over caller 5 -> 0 (V); Registry 10 over caller 5 -> 5 + detail (V); Registry `-1` -> `composition_record_invalid`; member `clock_tolerance_seconds` (the f4t name) -> `composition_record_invalid` (V): this family cannot be fed an f4t record.
- Preconditions: same as B (host `observation_policy` exists). Caller normalizer reads the policy's current tolerance (including the host default 5), never an invented one.
- Consequence to state in the record: lowering the tolerance may create false `observation_time_future` holds under destination/control-plane clock skew (1.5).
- Separate from f4t: no shared member, no shared family id, no shared selection. AR-1 (1.6) is the gating decision.

Cross-family: B and C are INDEPENDENT records and selections (one member each, because `ContractProfile` requires exactly one member per identity row), exactly as F4 age scalars are one family but the engine here forbids multi-member rows. The two ObservationPolicy
scalars are therefore two selections; atomicity across them is a consumer concern (no partial selection concern for safety because each is independently monotone).

### 2.4 Engine and profile deltas needed (V by prototype)
1. Anchor: none beyond registering the family (existing `scalar-enum` kind).
2. B/C: add `"scalar-int"` to `profile.KINDS` (`engine/profile.py:26`) and an `elif row.kind == "scalar-int"` branch in `identity.validate_effective_payload` (`engine/identity.py` just before the `else:  # scalar-enum` at `:73`): `type(value) is int` (else `_type_refusal`), then `row.is_value(value)` (else `field_invalid`).
   This is a pure addition to the engine; the existing branches are byte-identical, so `V6_COMPAT` and the frozen differential are unaffected (see 2.5 test run). The canonical encoder already carries exact ints (`_plain`, `v2_policy_identity.py:243`).
3. Identity digests (V): `f5-observation-max-age-policy` value 60 -> `sha256:b464a17f...054dbc`, tolerance 0 -> `sha256:00d2743d...d25315`, anchor `anchor` -> `sha256:6f70a205...e3998` (prototype, r08-v7 domain, revision 1; preimage `{effective_policy_profile, contract_version, family, family_schema_revision, deny_all [], effective}`).
   These are PROTOTYPE values: they are NOT canonical until the Architect fixes members, domains and ranges.
4. Test changes for the real implementation (not done): new family test modules in the style of `tests/test_r08v7_irreversibility_family.py` + an independent-encoder identity vector file + signed-decision vectors, and updating the three pins in 2.5.

### 2.5 v7 or v8: what adding families changes (V and R)
Question 1: does adding a family to `V7.families` alter signing domains or identity of existing families? **No (V).**
- Signing and effective-policy domains are profile-level constants (`engine/profiles.py:23-24`, `profile.py` validation) and `selection.signing_input` uses only `profile.selection_signing_domain` (`engine/selection.py:30-31`).
  Existing irreversibility digest on main = on the prototype with four families: `sha256:bdf68c52d2e3d33d16592da65fa46bacd5181438d679a3c2f78f1dcbeaee1b2b` (both V). The preimage carries only that family's own revision (`engine/identity.py:97-101`).
- Verification, record validation and composition dispatch look up exact family strings in the profile table (`engine/profile.py:lookup`), so other families' paths are unchanged.
Question 2: is the V7 family set pinned such that adding changes accepted behaviour? **Yes, behaviour and tests (R + V).**
- Behaviour: today a v7 record/selection naming the new family refuses `family_unsupported` (docs/r08-v7-contract.md:11, `v7_families.py` doc, tested). After adding, it is accepted. That is a changed accepted-set for `r08-v7`.
  One subtle second effect: `decide._refusal` (`engine/decide.py:31-35`) normalizes the caller by the FIRST family whose normalizer accepts, in table order; callers of the new shapes are now returned normalized (equal copy) instead of unchanged on optional refusal. The irreversibility caller path is unchanged because it is first.
- Tests that pin it (R, and V where the run completed): `tests/test_r08v7_engine_profile.py::test_v7_profile_content` (`list(V7.families) == [IRR]`), `::test_the_blocked_families_are_not_registered` (`len(V7.families) == 1` and names absent),
  `tests/test_r08v7_decision_path.py::test_other_families_are_unsupported_in_the_v7_table` (V: fails on the prototype with `field_unknown` for `f5-observation-max-age-policy`, because the record validator now routes it to the new family's payload shape instead of refusing the family),
  plus docs claims "exactly ONE family" (`docs/r08-v7-contract.md:1,10,11`, `v7_families.py` doc, `profiles.py` doc). No signed vector changes. See section 2.6 for the full prototype test run.
- Freeze status: `docs/family-migration/unified/02-...md:20` says v7 is unfrozen and "qualified families may be added to its table before the Architect freezes it; after freeze a new family needs a new contract id (never a mutation of v7)"; 07-doc (`:21`) lists "`r08-v7` allocation/freeze" as a pending Architect decision.
  Registry #71 is merged (main 04302e0), so v7 exists on main but the freeze decision is not recorded.
Smallest compatible boundary:
- If the Architect has NOT frozen `r08-v7`: add the three families to `V7` (additive). Existing domains, digests and vectors do not change; three tests and the docs sentences are amended; no new domain; no re-signing of anything signed so far. This is the smallest, and compatible because nothing signed or identity-hashed for existing families moves.
  Requires the `scalar-int` engine kind (2.4).
- If `r08-v7` HAS been frozen (or the Architect wants "accepted set of r08-v7 never changes"): a successor profile `r08-v8` with NEW domains `ocs-reg/r08-v8/selection\n` and `ocs-reg/r08-v8/effective-policy\n`, carrying ONLY the three new families (like v7 not re-registering v6 families, `unified/02-...md:20`), version-checked by `ContractProfile.__post_init__`
  (`profile.py:61-67`). Existing v7 irreversibility records stay valid only under v7; v8 would not re-register irreversibility (re-registering it under v8 would produce different digests by domain, requiring re-signing). Cost: a second signed-selection stack/trust scope for the three families vs. irreversibility, and `v8_*` thin binding modules (decision, families, policy_identity) following the `v7_*` pattern.
- NOT acceptable under either boundary: reusing the `r08-v7` id for different semantics after freeze; adding `scalar-int` by editing frozen v1..v6 modules (not needed; the engine file is not in the frozen manifest, `docs/r08-v7-contract.md:7.4`).
- **Architect decision D-C5**: v7 additive vs v8 successor.

### 2.6 Prototype test run (V)
Command: `PYTHONPATH=. pytest tests/test_r08v7_*.py tests/test_ext_s1_5_identity_module.py tests/test_r08v6_frozen_baseline.py` in `final3/proto_reg` (prototype with the three families in `V7`). Results: **9 failed, 850 passed, 1 skipped** (318 s). All 9 failures are tests that pin the one-family table; none is a vector, digest, signature or differential test:
`test_r08v7_decision_path.py::test_other_families_are_unsupported_in_the_v7_table` (the listed id `f5-observation-max-age-policy` is no longer `family_unsupported`), `test_r08v7_engine_profile.py::{test_v7_profile_content, test_the_blocked_families_are_not_registered, test_a_profile_copies_its_inputs_so_later_mutation_of_the_source_dicts_changes_nothing, test_the_dispatch_itself_enforces_record_validity_operator_and_family_even_for_a_composer_that_does_not}`,
`test_r08v7_frozen_baseline.py::test_v7_modules_are_new_files_only` (pins the ENGINE_MODULES file set; two new engine files), `test_r08v7_irreversibility_family.py::test_the_v7_table_registers_exactly_one_family_and_dispatches_by_exact_string`,
`test_r08v7_lifecycle_boundaries.py::test_a_composer_result_marked_deny_all_is_reported_as_applied_deny_all_and_never_as_applied`, `test_r08v7_policy_identity.py::test_family_row_is_exactly_the_one_registered_family_with_revision_1`.
Passing on the prototype (V): the signed-selection vectors, identity vectors (existing irreversibility digest unchanged), the `V6_COMPAT` engine differential, frozen v1..v6 baseline manifest, decision-path and lifecycle suites for irreversibility, `test_ext_s1_5_identity_module.py`.
So adding to `r08-v7` is behaviour-additive for existing vectors but needs nine test edits (assertions about family count/set), which is itself a change to a merged contract's pinned surface.

### 2.7 Architect decision list (all unresolved)
| Id | Decision | Recommendation |
|---|---|---|
| AR-1 | Does the DR-CP-AGE-1 line-8 `clock_tolerance_seconds` exclusion extend to `ObservationPolicy.clock_tolerance_seconds`? | No, by separate record; do not edit DR-CP-AGE-1; do not touch #58/#87 |
| D-C1 | Registry tolerance 0 admitted (floor 0) or floor 1 | Admit 0 (source `ge=0`) |
| D-C2 | Registry token range ceiling 2147483647 (no host ceiling exists) | Reuse as structural token range only; state it is not a CP bound |
| D-C3 | Host values above 2147483647 refuse the whole caller (not narrowable) | Accept (fail closed), as DR-CP-AGE-1 decision 7 |
| D-C4 | Anchor residual (purpose-input 2x window) and freshness-member ownership | Accept and document, or keep BLOCKED (D-07) |
| D-C5 | r08-v7 additive vs r08-v8 successor; v7 freeze | v7 additive if unfrozen; v8 with only new families if frozen |
| D-06 | Binding of ObservationPolicy (A workflow-local / B persisted field / C approval preimage) | not chosen here; B/C require Architect authorization and F3 requalification |
| D-07 | 60/300 ordering | none required; no source relationship |
| D-C6 | Family ids and member names (`f5-` prefix, `observation_` member prefix) | adopt as proposed; they match the pre-chosen ids in `test_the_blocked_families_are_not_registered` |

### 2.8 What was not done
No repo edit, commit, push or PR. The prototype is a scratch copy. Not run: the full Registry suite, mutation harness, CP Registry-pinned tests, any consumer for the families (none exists; a consumer is a Control Plane change under the binding decision).
