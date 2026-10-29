# D-06 Persisted effective-configuration binding ("Option B") - design contract

Status: DESIGN ONLY. Nothing implemented, no repo file touched. Everything marked **[AUTH]** requires explicit Architect authorization and F3 requalification before any implementation.
Non-authorizing: the binding is an integrity/equality check that can only refuse; it confers no authority and is never an input to an approval.

Paths are relative to `m12/r8_cp/src/agent_control_plane/` (CP main b7eb11a). "R" = verified by reading; "X" = verified by running code (scratch interpreter `venv-g1-212`, `-I`, no repo writes).

## 0. Verdict in five lines
1. Today a governed decision persists only profile-bearing identity (`catalogue_digest`, `approval_commitment`). F4 scalars, ObservationPolicy, clock tolerance, identity/mandate ages and the declared family set (with contract versions) are persisted nowhere and bound to nothing. The only record of the configuration is `GovernedActivationLedger`, which is in-process and non-durable.
2. A decision persisted under configuration A is executable after restart/rebuild under configuration B whenever the final profile is byte-identical (existing test `test_i04`, tests/test_governed_policy_composition.py:468-476, characterizes this).
3. Recommended design: a versioned, domain-separated digest plus a descriptive members object, carried in the already-persisted opaque dict `binding.runtime_authority["effective_configuration"]`, minted/checked by an override in the non-protected `registry_governed_lifecycle.py`. No pydantic or JSON-schema change; **no protected evaluator edit**. Refusal reuses the registered `authorization_binding_changed` (durable `EffectTimeRefusal`).
4. The "no-schema-change" carriage is NOT gate-neutral: because `execute` compares `current != persisted.binding` over the whole dict, it changes the authorization gate's persisted content and comparison set. It is also fail-CLOSED for legacy readers (X), whereas a typed top-level member is fail-OPEN for legacy readers (X). Both need **[AUTH]**.
5. Missing-binding safety needs a record-external anchor (a host `legacy_cutoff` count, or a durable floor row [AUTH, schema]); an absent key alone cannot distinguish "legacy" from "stripped".

## 1. What a governed decision persists today (trace)

| Item | Finding | Cite |
|---|---|---|
| Persisted unit | `RuntimeDecision.binding: TenantAuthorizationBinding \| AuthorizationBinding \| None`; `AuthorizationBinding.runtime_authority: dict \| None` (free-form). Written by `records.append_decision` -> `_append` (raw document re-read, new row appended, `BoundedRunRecord.model_validate`, atomic write). | bounded.py:343-358, 265, 640-694 (R) |
| Extension minted | `validate_extensions` returns `{profile, approval_commitment, required_inputs_digest, catalogue_digest, expected_effective_grant_digest, effective_grant_derivation_version, [operation_id, operation_issuer], [approval_commitment_version, policy_generation, policy_activation_ref]}` and `bounded.py` stores it as `runtime_authority=extension`. | runtime_authority.py:469-478; bounded.py:2559-2581 (R) |
| `catalogue_digest` | `commitment(profile.model_dump(mode="json"))` = hash of the FINAL effective `RuntimeAuthorityProfile` (the governed workflow's `self.runtime_authority_profile`). | runtime_authority.py:473; registry_f5_class_age_governance.py:129-131 (R) |
| `approval_commitment` | `commitment({profile dump, runtime_authority spec, grant.purpose_ref, grant.expires_at})`; when `profile.policy_binding` is set it is the tagged `approval-commitment/0.2` with `policy_identity` and `policy_generation` members. Recomputed at every `validate_extensions`; approval input must equal it or `runtime_authority_approval_mismatch`. | runtime_authority.py:236-251, 330-334 (R) |
| F4 scalars | `status_max_age_seconds`, `approval_max_age_seconds` are plain constructor attributes of the workflow (bounded.py:1295-1298), NOT members of `RuntimeAuthorityProfile`, so in neither `catalogue_digest` nor `approval_commitment` nor the binding. Consumers: bounded.py:2399-2400 (grant status, only without a profile), 2445, 2469 (conflict/policy status), 2505 (approval). Governed workflow holds them and compares to its in-memory `_gl_bound` at each boundary (registry_governed_lifecycle.py:150-168; registry_governed_policy.py:400-409). Docstring states "UNRESOLVED DESIGN DECISION" (registry_governed_policy.py:21-27). | (R) |
| ObservationPolicy | Constructor arg, deep-copied (bounded.py:1276, 1300). Used only in `_reconcile_observation` / `_observe_and_reconcile`. Its two values are echoed into each persisted `ReconciliationResult` (`observation_max_age_seconds`, `observation_clock_tolerance_seconds`, bounded.py:427-428, 1868-1869, 1963-1964) as record-only evidence; never compared against anything. Not in any `registry_*` identity (grep: no hit in registry_*.py bound/configuration). | (R) |
| Other non-profile scalars | `clock_tolerance_seconds`, `identity_max_age_seconds`, `mandate_max_age_seconds` (bounded.py:1275, 1296-1299): also unbound; docstring registry_f5_class_unreadable_governance.py:49-52 lists them as "NOT governed". | (R) |
| In-process configuration identity | `configuration = commitment({families, scopes(operation ids), consumer/tenant/action/institution/authority_domain, host{scalars, class_age, class_unreadable, class_revocation_assurance, terminal_revocation}, bound})` (+ `host_class_irreversible` wrapper when that family is declared). Held in `GovernedActivationLedger._claims` (dict + `threading.Lock`): process-local, lost at restart. Does NOT contain ObservationPolicy, clock tolerance, identity/mandate ages, contract versions or family schema revisions. | registry_governed_policy.py:93-118, 329-335 (R) |
| Snapshot identity | `EffectivePolicySnapshot.identity_digest` covers host profile digest, effective profile digest, scope, families (slot, family id, contract version, schema revision, effective-policy digest, effective value, selection id/epoch) BUT also `evaluated_at`, which changes at every construction, so it is unusable as a stable persisted binding. | registry_effective_policy.py:25-37, 83-93 (R) |
| Policy-binding generation | `policy_binding/0.1` is a separate opt-in; governed profile-bearing families REFUSE a host profile carrying it (`policy_binding_unsupported`, registry_governed_policy.py:~268). So the generation binding and this binding never co-exist today. | (R) |

### Re-validation on execute / restart / pin export (R, plus X where stated)
* `execute(proposal, decision)`: `records.decision(id)` must equal the passed decision and be `authorized` with a binding (bounded.py:1672-1678); `effect_id` recomputed from binding (1679); `_resolve(stage="effect", decision=persisted)` re-runs the whole gate under the EXECUTING workflow's current profile and scalars (1685); then `current != persisted.binding` -> refusal reasons or `authorization_binding_changed`, persisted as `EffectTimeRefusal` (1690-1712). Because `current.runtime_authority` is rebuilt from the executing workflow's profile, `catalogue_digest` and `approval_commitment` are compared; nothing else configuration-related is.
* `GovernedLifecycle.execute` / `decide` additionally call `_gl_revalidate` (re-verify Registry sources, compare to the in-memory bound identity, check held profile/scalars) and the commit gate before `destination.apply` (registry_governed_lifecycle.py:150-203). All compare against the CURRENT process's `_gl_bound`, never against anything persisted with the decision.
* Restart: a rebuilt workflow re-derives `_gl_bound` from live sources. Persisted decisions are re-read from the JSON store; `test_i03` (restart with same families resumes) and `test_i02` (different final profile refused via `authorization_binding_changed` path) pin current behaviour; `test_i04` pins the F4-only gap (R; not run: those tests need the exact Registry pin `6f600ab...` and `OCS_REGISTRY_PIN_DIR`, which was not available at that commit in this checkout).
* Pin export (`authorization_pin_export`): re-reads `catalogue_digest`, `approval_commitment`, `policy_generation` from the persisted extension (authorization_pin_export.py:128-131), compares to the configured profile (199-204), re-resolves with `workflow._resolve(stage="claim", decision=persisted)` and requires `current == current_binding` (183-188). Any new member that `_resolve` adds therefore gets compared on this path too, with no further change. The `withdrawn` branch deliberately compares nothing about the catalogue (162-168).
* `replay.py` is the generic agent `RunRecord` -> `ReplayBundle` serializer; it holds no authorization binding and does no validation of one (R). "Replay" in the brief therefore means re-execute/pin-export of a persisted authorized decision.
* Legacy-record read: typed models have no `model_config`; extras are IGNORED on typed read (X: `RuntimeDecision.model_validate({..., "new_member": ...})` drops it). `_append` re-reads the raw document and preserves unknown members (bounded.py:690-694; docs/record-store-persistence.md "Appends preserve raw historical fields"). Records are unsigned local JSON: `tests/test_authorization_pin_export.py:165-176` rewrites persisted `catalogue_digest`/`approval_commitment` in place, so the store is not tamper-evident (threat-model limit below).
* Published schema: `schemas/runtime_authority_run_0_1.schema.json` declares `AuthorizationBinding.runtime_authority` as `{"additionalProperties": true, "type": "object"}` or null (X, parsed JSON); no `additionalProperties:false` on `RuntimeDecision` / `AuthorizationBinding`.

## 2. Record shape and canonical digest preimage

### 2.1 Carriage (recommended): inside `binding.runtime_authority`
```json
"runtime_authority": {
  "...existing members unchanged...",
  "effective_configuration": {
    "version": "effective-configuration-binding/0.1",
    "digest": "sha256:<64 hex>",
    "members": { ...the preimage members below, verbatim... }
  }
}
```
* `digest` is a REDUNDANT commitment over `members`; a reader must recompute it from `members` (reject if unequal -> `invalid`) AND compare the recomputed-from-live value (reject if unequal -> `mismatch`). `members` makes a mismatch diagnosable (which member differs) without becoming trusted input.
* Key absent = legacy/pre-binding record. Key present with unknown `version` = refuse (closed version set, exactly like `SUPPORTED_APPROVAL_COMMITMENT_VERSIONS`, policy_binding.py:34-35).
* Typed carriage (alternative, schema change) is described in section 8.

### 2.2 Preimage (canonical form = existing `commitment()`: sorted-key canonical JSON, `bounded.py:86-88`; floats rejected by `_finite_number` policy, all numbers here are exact ints)
```
digest = commitment({
  "domain":  "cognous.control-plane.effective-configuration-binding",   # domain separation: distinct from approval-commitment and catalogue preimages
  "version": "effective-configuration-binding/0.1",
  "scope": {"consumer_id", "tenant_id", "action_id", "institution_id", "authority_domain"},   # governed scope (registry_governed_policy.py:329-331)
  "host_profile_digest":      commitment(host profile dump) | null,       # agemod.profile_digest(host); null when no profile
  "effective_profile_digest": commitment(final profile dump) | null,      # == catalogue_digest for profile-bearing workflows; null otherwise
  "f4_scalars": {"status_max_age_seconds": int, "approval_max_age_seconds": int},   # ALWAYS the live attribute values, even when the F4 family is not declared (the gap test_i04 shows)
  "other_scalars": {"clock_tolerance_seconds": int, "identity_max_age_seconds": int, "mandate_max_age_seconds": int},   # optional member set, see D-06.2
  "observation_policy": null | {"max_age_seconds": int, "clock_tolerance_seconds": int},   # null is bound explicitly (absent policy is a hold, bounded.py:1899-1901)
  "families": [   # declared mandatory family set, FAMILY_NAMES order (registry_governed_policy.py:40)
     {"slot", "family_id", "contract_version", "family_schema_revision": int|null, "effective_policy_digest"} ...
  ]
})
```
Rules:
* `families` entries reuse the values the activation/snapshot code already computes: `FAMILY_TABLE` (registry_effective_policy.py:25-37 gives family id and contract version), `SCHEMA_REVISIONS`, and `bound[slot][1]` (effective-policy digest). A non-declared family is ABSENT from the list (declared set is part of the identity). The list is a set committed in a fixed order.
* Deliberately EXCLUDED: `evaluated_at` (non-deterministic), `selection_id` / `selection_epoch` (an equal replacement selection is accepted today, `test_l05`; including them would invalidate in-flight decisions on a benign re-selection - their effect is already carried by the effective-policy digest). Architect may choose to include them (stricter, **D-06.3**).
* Reuse of the existing identity: the activation ledger's `configuration` digest is NOT reused as is (lacks ObservationPolicy, other scalars, contract versions/schema revisions; wrapped differently when irreversibility is declared; takes `operation_ids` which are Registry-side mappings). It is the same material class and should be built from the same `bound` object by one shared function so the two cannot drift. A new binding digest is therefore proposed rather than overloading `configuration_digest`.
* Value validation before hashing (fail closed, as `member_defects` does): exact `int` (never bool), `0 <= v <= SCALAR_MAX (2147483647)`, strings exact `str`, digests `sha256:<64 lowercase hex>` and not all-zero; otherwise the workflow refuses with `configuration_binding_invalid` before hashing.
* Host custody: all members are read from the executing workflow's own attributes at the moment of check (the same objects `_gl_held_defect` already guards for scalars/profile); `observation_policy` and `other_scalars` need adding to the "held state" guard so a post-construction attribute edit is refused (new coverage, in the non-protected lifecycle module).

## 3. Reader compatibility matrix

Legend: OK = behaves as today; REFUSE = fails closed; OPEN = ignores the binding (would execute); "same-config" = executing workflow's configuration digest equals the persisted one.

| Writer -> Reader | Carriage C2 (dict member, recommended) | Carriage C1 (new typed top-level/binding field) |
|---|---|---|
| Legacy record -> new reader, mode `enforce`, no cutoff | REFUSE `authorization_binding_changed` (persisted lacks member, live has it) | REFUSE (same) |
| Legacy record -> new reader, `enforce` + `legacy_cutoff` and record index < cutoff | OK under the previously established semantics (member stripped from `current` before comparison, nothing else changes); marked "legacy" (below) | same |
| Legacy record index >= cutoff (written by a legacy writer after activation, or stripped) | REFUSE `authorization_binding_changed` | same |
| Legacy record -> new reader with binding feature OFF (default) | OK, byte-identical to today | OK |
| New record, same config -> new reader | OK | OK |
| New record, different config (any member) -> new reader | REFUSE `authorization_binding_changed` (durable `EffectTimeRefusal`, `changed_inputs` unchanged) | REFUSE |
| New record -> new reader, feature OFF (rollback to opt-out) | REFUSE (live `current` lacks member, persisted has it): fail closed; to read it the feature must be on | would be OPEN if reader ignores the field; if it is a typed field the OFF reader still must be told to compare -> define OFF reader = refuse presence |
| New record -> LEGACY reader (old binary) | **REFUSE** (X: `current != persisted.binding` when persisted dict has one more key) with `authorization_binding_changed`; also the pin export claim path refuses | **OPEN** (X: typed extras are dropped, so persisted and current compare equal and the legacy reader executes with no configuration check) |
| Legacy writer appends after upgrade (mixed fleet) | record has no member; new readers REFUSE it past the cutoff; legacy readers accept it (unchanged legacy semantics - cannot be prevented by any in-code design; "stop old writers before upgrading" is already a documented operational requirement, docs/record-store-persistence.md) | same |
| New writer, legacy peer process executing it | peer REFUSES (so a mixed fleet cannot silently bypass binding on records the new writer mints) | peer EXECUTES (bypass) |

Consequence: if a typed field is chosen, a mixed fleet is only safe if the same dict fence is ALSO written (i.e. it degenerates to C2 plus a typed copy). C2 is therefore the safer carriage, which is the opposite of what the "needs schema change" framing suggests.

Unknown `version` on a present member -> REFUSE in every reader that knows the member (closed set). A future 0.2 writer vs this 0.1 reader: 0.1 reader sees an unsupported version and refuses (fail closed).

## 4. Migration rules
1. **Opt-in first.** Constructor parameter on `GovernedPolicyWorkflow` (and family workflows), default OFF. OFF = no member minted, no member tolerated on read of a record that has one (refuse), everything byte-identical to today (existing tests unchanged). Default-ON is a later Architect decision (**D-06.4**).
2. **Pre-existing decisions.** Never rewritten, never re-signed, never back-filled (a back-fill would manufacture a binding the issuer never saw). They stay executable under exactly today's semantics only when the host supplies `legacy_cutoff` = the number of rows in `decisions` at activation (a read-only helper `configuration_binding_status(records)` can report it; computed by the host, passed explicitly; wildcard / "accept all legacy" is not offered: CLAUDE.md "Never add implicit, default or wildcard permissions" - the cutoff is a finite explicit integer).
3. **Index rule.** `decisions` is append-only and ordered under the transaction lock (bounded.py:690-694), so "legacy" = `index_of(decision) < legacy_cutoff`. No timestamp is trusted (timestamps are in the unsigned record).
4. **No cutoff given and the store holds unbound authorized decisions** -> unbound ones are refused at execute, never silently accepted. Construction itself does not fail (they may be dead decisions).
5. **Drain.** A legacy decision either executes (under legacy semantics), or expires through its existing horizon. When none remain executable the host may drop the cutoff (set to the current count or omit); nothing in the store changes.
6. **Approvals.** No approval changes. `approval_commitment` is untouched, so every already-issued approval remains valid under its established semantics; new approvals are issued exactly as today.
7. **Durable floor (optional hardening, [AUTH, schema]).** A new `exclude_if`-empty ledger `configuration_binding_floors` in `BoundedRunRecord` (row: `{version, decisions_index, recorded_at}`) written once at activation, replacing the host-supplied cutoff so the boundary survives host misconfiguration. Legacy readers ignore it (typed extra dropped) and appends preserve it raw.

## 5. Restart / recovery behaviour
* Mint: at `decide`, the governed override of `_resolve` (non-protected `registry_governed_lifecycle.py`) adds `effective_configuration` to the returned binding's `runtime_authority` dict ONLY when `reasons` is empty and the binding is non-None (X: post-construction mutation of the dict survives `model_dump`/JSON round trip and equality). The decision is then persisted by the unchanged `append_decision`. A hold persists no binding, as today.
* Execute / claim: the same override, called with `stage in ("effect","claim")` and `decision=persisted`, (a) recomputes the live members and digest from the executing workflow, (b) reads `persisted.binding.runtime_authority.get("effective_configuration")`, (c) classifies: `bound-match`, `bound-mismatch`, `bound-invalid`, `bound-version-unsupported`, `legacy-accepted` (key absent AND index < cutoff, member omitted from `current` so legacy equality holds), `legacy-refused` (absent, no cutoff or index >= cutoff). Anything but `bound-match` / `legacy-accepted` makes `_resolve` return `authorization_binding_changed` in `reasons`, so `execute` writes the existing durable `EffectTimeRefusal` and raises the existing `PermissionError`; destination untouched.
* After restart nothing is held in memory: the persisted member is authoritative for "what configuration did this decision run under"; the live process supplies "what runs now". Restart with the same families/values/policies -> equal digest -> resumes (extends `test_i03`). Restart with a different F4 scalar, ObservationPolicy, family set, family version or effective value -> refuse (extends `test_i02`/`test_i04` from "executes" to "refuses").
* Attempts already `failed` at the commit gate keep blocking retry (unchanged); a configuration refusal is a pre-dispatch refusal row, not an attempt.
* Recovery from a refused-by-configuration decision: the host rebuilds under the original configuration, or issues a new decision (a new decision binds the new configuration). There is no "re-bind" operation; re-binding an old decision to a new configuration would be an authority change.
* Commit gate: unchanged. Binding is checked at execute entry via `_resolve`; the existing last-moment `_gl_reverify` still protects the live Registry sources.

## 6. Refusal semantics and reason codes
Durable path (a refusal row is written; reuses a REGISTERED code, so no vocabulary change):
| Situation | Code | Where it surfaces |
|---|---|---|
| bound mismatch, bound invalid, version unsupported, legacy-refused, legacy reader on new record | `authorization_binding_changed` (registered: schemas/runtime_authority_reasons_0_3.json:68; emitted today at bounded.py:1693) | `EffectTimeRefusal.reasons`, `PermissionError("authorization-critical inputs changed before effect")` |

Pre-write path (adapter's closed vocabulary, `Refusal(code)` raised as `RegistryGovernedPolicyRefused` before any state write, like `selection_changed`, `scalars_modified`, `profile_modified`): proposed finer-grained diagnostics, only if the Architect wants them as typed adapter codes:
* `configuration_binding_mismatch`, `configuration_binding_missing`, `configuration_binding_invalid`, `configuration_binding_version_unsupported` (NEW adapter-level strings; they are NOT runtime-authority registry codes and need no `runtime-authority-reasons` version).
* A typed DURABLE code for these would be a NEW code in a new immutable registry file `runtime-authority-reasons/0.4`: it requires editing protected `runtime_authority.py` (`CODES_ADDED_IN_*`, `REGISTRY_SHA256`, `vocabulary_for`) plus the Registry-owned code table. **[AUTH]**, and NOT recommended: an unregistered string placed in `reasons` is labelled 0.1 by `vocabulary_for` and then fails `registry_admits` (runtime_authority.py:104-125). So do not invent durable codes without 0.4.
Semantics: any failure refuses the WHOLE execute; there is no fallback to a smaller set, a host value, the legacy path or a warning. A missing/invalid/unsupported binding is never "treated as legacy" unless the explicit cutoff rule applies. Binding evaluation can only add reasons; it never removes one that another check produced.

## 7. Requirements check
| Requirement | How met |
|---|---|
| Existing approvals remain valid under previously established semantics | `approval_commitment` and approval preimage untouched; legacy decisions stay executable via explicit `legacy_cutoff` with the exact legacy comparison (member omitted from `current`) |
| New governed decisions bind the exact configuration | member minted at every authorized `decide` of an opted-in governed workflow; digest covers all section 2.2 members |
| Replay under a different configuration refuses | execute and pin-export claim both go through the overridden `_resolve` -> `authorization_binding_changed` |
| MISSING binding on a record that should have one never falls back to a less restrictive policy | absent member is accepted ONLY for index < host cutoff; otherwise refused; OFF-reader refuses a present member; unknown version refused; no default cutoff. Residual: if the host sets a too-large cutoff, or an attacker edits the unsigned store, the check is defeated (the store gives no tamper evidence, tests/test_authorization_pin_export.py:165-176) |
| Legacy records distinguishable | by member absence + index < cutoff; read-only helper returns `bound` / `legacy` / `unbound-after-cutoff` / `invalid`; the pin export/attempt evidence is unchanged for legacy |
| Confers no authority | member is only compared; never read by an approval, never widens a bound, only adds `authorization_binding_changed`; `GovernedLifecycle` lifecycle stays "holds no policy" (test_z04 asserts it never touches a governed field; the new code must remain compatible with that test or the test updated under [AUTH]) |
| Existing negative evidence intact | no existing code path is removed or loosened; `test_i02`, `test_i03`, `test_i05/i06` unchanged; `test_i04` is intentionally INVERTED (it currently proves the gap; under the opt-in feature the same scenario must refuse) - that inversion needs Architect acknowledgement because it edits a characterization test |

## 8. What would change; F3 impact; the no-schema-change alternative

### 8.1 Files / schemas touched
Carriage C2 (recommended, no protected file):
* `registry_governed_lifecycle.py` (override `_resolve`, held-state guard for `observation_policy`/`other_scalars`, cutoff handling) and `registry_governed_policy.py` (constructor flag, shared digest builder fed by `bound`, family table, public identity gains `effective_configuration_digest`); `registry_effective_policy.py` (optional: expose the family tuple). Byte pins: `test_z03` pins only the six protected evaluators (tests/test_governed_policy_composition.py:781-792) - unchanged; consumer pins in the four per-family tests would need updating for the lifecycle bytes (precedent: docs/governed-workflow-consolidation.md).
* Tests added: mint/compare matrix, legacy cutoff, legacy-reader-on-new (fail closed), restart with each member changed, missing/stripped, OFF-reader. Docs: new section in docs/governed-workflow-consolidation.md and record-store-persistence.md.
* NO change to: bounded.py, runtime_authority.py, freshness.py, policy_binding.py, rule_revision.py, reversibility.py, holder_inventory.py, `approval_commitment`, `schemas/*`, `runtime-authority-reasons`.
Carriage C1 / floor row (schema-altering **[AUTH]**): `bounded.py` `AuthorizationBinding` (+ `TenantAuthorizationBinding`) new optional field, and/or `BoundedRunRecord` new list; regenerate `schemas/runtime_authority_run_0_1.schema.json` (a NEW file version, the 0.1 file is a frozen evidence artifact); protected-evaluator byte pins in test_z03 change; the hub pin of CP changes.
New reason code: protected `runtime_authority.py` + new immutable `schemas/runtime_authority_reasons_0_4.json` + Registry-owned table **[AUTH]**.

### 8.2 F3 requalification impact
Any of the above changes (a) what a persisted authorized decision contains and (b) the set of values the execute gate compares - an authorization-gate semantic change even though no protected file is edited. Required: **Architect authorization**, F3 requalification of the candidate component, refreeze, independent re-review; re-run of the full negative-evidence suite (current governed tests, pin-export tests, fault-injection around `_append`), new mutation tests on the digest members (each member perturbed must flip the verdict), compatibility tests with a frozen legacy fixture store (generated by the current binary) and with a legacy-binary-on-new-record test. Hub pin and Registry-pin re-baseline after merge. Static Plan v1.1 s.12 / audit #60 accounting stays 16/19 integrated until requalified; the three final parameters remain BLOCKED (D-06) until then.

### 8.3 No-schema-change alternative: exists, and is the recommended carriage - with the gate caveat
* Existence (verified): `runtime_authority` is an opaque `dict` (bounded.py:265), JSON-schema `additionalProperties: true` (X), and mutation after construction round-trips (X). Likewise `catalogue_digest` itself is an opaque string member. Equivalent shapes, ranked:
  1. **New named member in the dict (C2).** Recommended (above). Fail-closed for legacy readers (X).
  2. **Fold the new digest INTO the existing `catalogue_digest` string** (e.g. `catalogue_digest = H(profile_digest, config_digest)`). NOT acceptable: `catalogue_digest` has meaning outside the workflow. `authorization_pin_export` (authorization_pin_export.py:199) and all documentation define it as `commitment(profile.model_dump())` and compare it to the configured profile; the per-family tests and docs assert `catalogue_digest == effective_profile_digest` (test_governed_policy_composition.py:162, test_f5_class_age_governance.py:541). Overloading it breaks pin export for every record, destroys distinguishability (a legacy record cannot be told from a mismatched one without recomputation), and it would be an undeclared change to a committed value. Rejected.
  3. **Fold into `approval_commitment`.** That is an approval-preimage change (hard rule) and invalidates every existing approval. Rejected; **[AUTH]** if ever wanted.
  4. **Reuse `required_inputs_digest` / `operation_id` / any approval-owned member.** Rejected: those are issuer-controlled; overloading them lets an approval choose the configuration (the binding must come from the trusted executing workflow, never the approval).
  5. **Side file/ledger outside the store** (host-kept map decision_id -> digest). Possible without any CP change but it is not part of the persisted decision, is not atomic with `append_decision`, and does not protect the pin-export or a legacy reader. Acceptable only as a host custody measure, not as a CP contract.
* Why C2 still needs authorization: the gate (`execute`, `authorization_pin_export`) already compares the entire dict. Adding a member (1) changes the bytes of every new persisted authorized decision, (2) changes execute/claim outcomes for stores shared with legacy binaries (they begin to refuse, which is good but is a behavior change for any deployment with mixed versions), (3) makes `_resolve` overridden in a governed subclass, i.e. a new layer participating in the authorization verdict (CLAUDE.md: "no implicit... permissions"; here it can only add refusals). So "no schema change" must not be presented as "no gate change". Treated as: requires Architect authorization and F3 requalification, identical to the schema-altering variant; the difference is only that no protected evaluator and no published JSON schema file changes.
* Reader-side precision to preserve legacy equality: the legacy-accepted path removes ONLY the new key from `current` before the equality; it never ignores other keys.

## 9. Threat-model limits (state in the decision record)
* The store is unsigned and same-user; anyone who can rewrite it can forge a whole decision, a binding or the cutoff. The binding protects against configuration DRIFT, restart/rebuild mix-ups, partial upgrades and accidental or buggy writers, not against a malicious store writer. A signed-decision design is a separate (larger) item.
* No durable ratchet exists in the CP (docs repeat this): rolling back to an older configuration whose digest equals an older persisted binding revives that old decision. The binding makes rollback explicit (digest equal) but cannot forbid it.
* The binding checks the executing workflow's HOST-supplied values; Registry freshness, revocation visibility and epoch floors remain host custody duties (registry-f4-selection-source-custody.md).
* `observation_policy` and `other_scalars` are host constants in this process: a host that passes different values to different workers has different digests and will refuse each other's decisions (correct, but operationally visible).

## 10. Decision points for the Architect (explicit)
Requires explicit Architect authorization AND F3 requalification (nothing below is implemented):
* D-06.A Authorize adding a persisted configuration binding to authorized decisions at all (changes persisted decision content and the execute/claim comparison set).
* D-06.B Carriage: C2 dict member (recommended; no schema change, fail-closed for legacy readers) vs C1 typed field (schema change, legacy readers fail OPEN, needs a dict fence anyway) vs durable floor row (schema change).
* D-06.1 Preimage member set: confirm f4_scalars + observation_policy + families + both profile digests + scope; and the exclusion of `evaluated_at` and (default) `selection_id/epoch` (D-06.3).
* D-06.2 Whether `clock_tolerance_seconds`, `identity_max_age_seconds`, `mandate_max_age_seconds` join the preimage in v0.1 (cheap now, requires another version later; recommended yes, since the same drift class).
* D-06.4 Opt-in vs default-on for governed workflows; and whether non-governed plain `BoundedAuthorizationWorkflow` ever mints it (currently out of scope: it is the CLI default path, cli_run.py:510).
* D-06.5 Legacy rule: explicit host `legacy_cutoff` (recommended) vs durable floor row (schema).
* D-06.6 Any new durable reason code (`runtime-authority-reasons/0.4`) - not recommended; reuse `authorization_binding_changed`.
* D-06.7 Updating characterization test `test_i04` and test_z04 guard for the new lifecycle code.
Does NOT require authorization: this document; the read-only helper of section 4 (if implemented without minting) only after the Architect accepts the contract; documentation of the existing gap.

## 11. Options A / B / C for the decision record
| Option | What | Pros | Cons |
|---|---|---|---|
| A. Document-only (accept the gap) | Keep F4 scalars/ObservationPolicy as host constants; state it in docs; `anchor_deadline_to_inputs`, `max_age_seconds`, `clock_tolerance_seconds` stay BLOCKED/host-only (D-06) | zero code, zero requalification, no persisted change | the three final parameters can never be Registry-narrowable (not eligible); a decision survives a configuration change; replay under other scalars executes (test_i04 stays true) |
| B. Persisted effective-configuration binding (this design) | versioned digest + members in the opaque dict; opt-in; legacy cutoff | closes restart/replay drift for F4 scalars and ObservationPolicy and the family set; legacy approvals untouched; no protected file change; fail-closed in mixed fleets | changes authorization-gate comparison set and persisted content; **[AUTH] + F3**; operational friction when configs legitimately change (decisions must be re-issued); still unsigned store, no ratchet |
| C. Fold the scalars into the approval preimage / profile (new `approval-commitment/0.3` or move scalars into `RuntimeAuthorityProfile`) | bind at issuance | strongest: binds the issuer's view, covers approvals | changes `approval_commitment` (invalidates every existing approval or needs a dual-version verifier), touches protected `runtime_authority.py`/`bounded.py`, new vocabulary, largest F3 and migration cost; authority-semantic change |

Recommendation: B with carriage C2, opt-in, explicit legacy cutoff, existing code reuse; A remains valid if the Architect does not authorize any persisted-content change (then the three parameters stay BLOCKED); C only if issuer-level binding is required.

## 12. Verified-by-running vs by-reading ledger
* Run (X): typed `RuntimeDecision` drops unknown members; typed `AuthorizationBinding` drops unknown kwargs; a one-key-larger `runtime_authority` dict makes two bindings unequal (legacy `current != persisted` fail-closed); post-construction dict mutation survives JSON round trip and equality; `runtime_authority` is `additionalProperties:true` in the published run schema; `BoundedRunRecord` / `RuntimeDecision` / `AuthorizationBinding` have empty `model_config`.
* Read only (R): every other citation, including the governed tests (`test_i02-i04`); the Registry-pinned governed test suite was NOT run (needs exact Registry pin and `OCS_REGISTRY_PIN_DIR`).
* Not verified: end-to-end behaviour of the proposed override (it is a design; no code was written).
