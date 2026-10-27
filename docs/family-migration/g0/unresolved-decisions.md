# G0 unresolved items and Architect decisions

G0: CONDITIONAL ACCEPTANCE. G1–G5: NOT AUTHORIZED. V09 independent qualification: OPEN. Ed25519 #26/#34: SECURITY-HELD. Release: HOLD. Publication: HOLD. Production: HOLD.

## 1. The 32 historical UNRESOLVED rows (individually tracked)

All 32 keep their historical classification **UNRESOLVED** in `historical-crosswalk.json` (`unresolved_tracking.g0_status = UNRESOLVED-PRESERVED`). The proposal column is a worker's source-quoted proposal with a confidence; it is not a resolution until the Architect ratifies it.

| Row | Historical location | Construct | Confidence | Still configurable? | Candidates | Proposed resolution (truncated; full text in the crosswalk) |
|---|---|---|---|---|---|---|
| W1-029 | 343 | `_TARGET_MATCH_MODES = ("segment","exact","legacy-prefix")` | MEDIUM | UNRESOLVED | B-004 | The vocabulary tuple is a closed, fail-closed enum (IMMUTABLE_CONTROL); the mode CHOICE is already a CALLER_SUPPLIED per-policy field (default 'segment'). Strictness order exact < segment < legacy-prefix. Registry is not involved  |
| W1-056 | 521-562 | legacy attempts migration | MEDIUM | UNRESOLVED | B-030 | Not a configurable rule: schema migration inserting operation_digest 'legacy:unknown' and created_at=time.time(). Propose still_configurable NO (IMMUTABLE_CONTROL). Unchanged since pin. |
| W1-058 | 701-713 | `transition_attempt` | MEDIUM | UNRESOLVED | B-030 | transition_attempt accepts any status string for an existing attempt_id; there is no transition table, and a characterisation test pins this. It is the absence of a rule, not a value; propose NO unless the Architect wants a new tr |
| W1-073 | 1073-1088 | `observe_historical` | HIGH | UNRESOLVED | B-030 | observe_historical snapshots the envelope and calls destination.observe_bound without any authorization renewal and without writes; mandatory invariant (observation does not renew authority). Propose NO. |
| W2-025 | engine/operation_admission.py:152-155 | required observation set `{applied,partial,absent,unknown}` | HIGH | UNRESOLVED | B-023 | Closed qualification floor: all four observation states must be covered. Propose NO (IMMUTABLE_CONTROL); Registry could only add. |
| W2-036 | engine/refund_intent.py:26,34-35 | `effect_class` restricted to `"refund.issue"` | MEDIUM | UNRESOLVED | B-024 | effect_class accepts only 'refund.issue' (hard ValueError otherwise): profile identity of the synthetic refund intent. Propose NO. |
| W2-038 | engine/refund_intent.py:55-59 | scope binding and action id set | MEDIUM | UNRESOLVED | B-024 | Two-string action id set binds the intent to the synthetic profile; scope equality checks institution/domain/customer. Tenant-scoped ops refused. Propose NO (profile binding). |
| W2-067 | engine/control_plane_adapter.py:160-168 | result to exception mapping, definitive-rejection code set | HIGH | UNRESOLVED | B-025 | Closed seven-string set of destination error codes treated as definitive rejections; refusal vocabulary. Propose NO. |
| W2-077 | engine/control_plane_adapter.py:424-436 | `reconcile` trusted ids from snapshot | MEDIUM | UNRESOLVED | none | reconcile builds the adapter with trusted_institution_id and trusted_authority_domain taken from the snapshot's own operation (caller envelope), then workflow.reconcile(effect_id); effect-free and absence never grants dispatch. A  |
| W2-082 | engine/openshell_environment.py:89-90 | qualified profile `docker`, cpu `1`, memory `256Mi` | HIGH | UNRESOLVED | B-026 | Fields runtime/cpu/memory accept only 'docker'/'1'/'256Mi' (equality check raising 'only qualified local Docker profile supported'). Qualified-profile identity, no range. Propose NO. |
| W3-024 | LAE:546-560 | remove_authoritative_state | MEDIUM | UNRESOLVED | B-029 | Unconditional DELETE by key, no revocation write; callers in tests only (owner removal). Not a threshold. Propose NO configurable; flag authority-surface question: grants have no retained revocation table while approvals gained au |
| W3-063 | DD:76-93 | _operation_guard TTL logic | HIGH | UNRESOLVED | B-015 | Guard compares now - committed_at < ttl, deletes key after ttl, InProgress while held < ttl. Models provider dedupe memory; TTL is a destination constructor property (synthetic). Propose NO as Runtime policy (see G0-B-015). |
| W4-004 | policy_gate.py:196-201 | rule `read_allowed_tool_policy` | HIGH | NO | C-029 | Part of the PolicyGate evaluator: reached only after blocked_tool_policy and unknown_tool_policy; whole table is the documented evaluator contract. Proposed IMMUTABLE_CONTROL/RETAIN-IN-CODE. Lead decides. |
| W4-014 | policy_config.py:16-23 | `PolicyConfig` model | HIGH | NO | C-027 | default_action has no consumer in current source: frame_from_policy_config copies only policy_version/allowed_tools/blocked_tools; PolicyGate never reads it. Tool lists remain caller-authored data used by the legacy gate; authorit |
| W4-015 | policy_config.py:23 | default literal `"escalate"` for default_action | HIGH | NO | C-027 | Inert default: declared and validated, never consumed. Not a migration candidate; fail-safe value escalate is irrelevant because nothing reads it. Flag for Architect (dead field). |
| W4-018 | policy_config.py:62-82 | `authority_records_from_policy_config`; default source "policy_config" | HIGH | NO | C-028 | Authority-granting helper, not a tunable: every scope list in authority_required becomes a live AuthorityRecord for the given actor; the action_type key is ignored; expires_at defaults None. Registry must never create grants. Prop |
| W4-022 | demo_policies.py:50-54 | add_authority_record scope ["read"], source "demo_policy_config" | HIGH | NO | C-026 | Hard-coded demo grant of scope read (no expiry), not caller-overridable, not reachable from a supported entry point. Not a migration candidate; Registry must not create grants. |
| W4-023 | demo_policies.py:95-99 | add_authority_record scope ["read","write"] | HIGH | NO | C-026 | Hard-coded demo grant of read+write (no expiry); a write scope makes PolicyGate allow write actions on allowed tools. Same disposition as W4-022: RETAIN-IN-CODE, demo only. |
| W4-033 | rule_revision.py:150 | `d != "unsigned_revision_row"` exemption | HIGH | NO | none | Not a policy knob. Unsigned rows are retained for visibility but never count: revision_defects flags them, counting_rows/valid excludes any row with defects, and the from_digest chain check is skipped for them (line 163). The exem |
| W5-011 | manifest_validation.py:17 | `SUPPORTED_VERSIONS = frozenset({"1.0","1.1"})` | MEDIUM | NO | none | Closed protocol vocabulary: an unsupported version yields a validator error (line 72) and the gate fails closed with invalid_manifest. Proposed IMMUTABLE_CONTROL (closed refusal/support set); adding versions would widen the accept |
| W5-012 | manifest_validation.py:18-21 | `_EFFECTFUL`, `_HIGH_RISK`, `_PRIVILEGED` frozensets of action types ( | MEDIUM | UNRESOLVED | C-032 | Proposed HARD_CODED_LITERAL protective classification mirrored from an external action-manifest validator ('the same gate, the same codes'); removal widens, so keep in code. Residual uncertainty: the external validator is not in t |
| W5-023 | manifest_validation.py:86-88 | `manifest_default = manifest.get("default_action","escalate")` and `ac | MEDIUM | UNRESOLVED | C-031 | Fail-safe validator default. At runtime the only effective value is "block" (bounded.py 2664-2667); "allow"/"escalate" confer nothing; the validator demands review/authority/limits when default != block. The manifest itself is hos |
| W5-028 | decision_input_profile.py:50-56,269-272,332-333 | ALLOWED_ASSURANCE_CLASSES (4), ALLOWED_EVIDENCE_STATES {current, unkno | HIGH | NO | none | Closed vocabularies of a proposed, non-authorizing profile ('authorizing': false, runtime_enforcement_claim false in conformance vectors); validation raises ProfileValidationError for anything else. Proposed IMMUTABLE_CONTROL (clo |
| W5-044 | validation.py:188-193 | `authority_actor_mismatch` is a warning, not an error | HIGH | NO | none | Diagnostic severity only. A mismatched-actor authority record cannot confer authority because PolicyGate._active_authority_scopes skips records whose actor differs from the frame actor (policy_gate.py 283-284). Proposed IMMUTABLE_ |
| W6-004 | 100 | `EVIDENCE_KINDS = {"authorization","context","post_effect"}` | MEDIUM | NO | none | Closed enum used fail-closed: a kind outside it (including case variants) yields required_evidence_not_current (hold). Proposed IMMUTABLE_CONTROL. The authority-context schema that defines the enum is outside this repository (NOT  |
| W6-005 | 101 | `UNKNOWN_BEHAVIORS = {hold_effect, preserve_if_other_basis_suffices, r | MEDIUM | NO | none | Closed protocol vocabulary; an unrecognised value holds (context_unknown_requires_hold). Note: only hold_effect triggers a currency/age check at bounded.py 2551-2557; the other two recognised values add no check in the gate, so th |
| W6-042 | 1276, 1300 | `observation_policy` optional; deep-copied | HIGH | NO | C-001 | Not a configurable rule: absence of an ObservationPolicy is a fail-closed hold, not a permissive default. observation_policy_missing is added to reasons in both the transport-failure path and _reconcile_observation; accepted = not |
| W8-014 | RA:153-170 | RuntimeAuthorityProfile fields: catalogue_version, actions, producer_k | HIGH | NO | C-013 | Host trust configuration (HOST_OWNED_CONFIG at profile level; producer_keys and catalogue membership are trust roots). Not Registry-creatable and not a unit migration candidate; its numeric members are separate candidates. allow_s |
| W8-091 | LAE:443 | max_effects = current.effective_max_effects | HIGH | UNRESOLVED | C-033 | Origin of the effect cap: minimum of three declared integers, none a code literal: (1) requirement permission max_effects, (2) grant permission max_effects (both from the authority context, exact int required), (3) manifest action |
| W9-007 | records.py:66-67, 190-228 | `PolicyGate()` default and `include_trace=True` default | MEDIUM | UNRESOLVED | C-030 | Evaluator selection is code injection by the Python caller, and include_trace only toggles trace retention: both branches call the same rules and record the same decision. Not data-driven policy. Proposed RETAIN-IN-CODE. |
| W9-017 | microsoft_agt.py:288-302 | AGT warnings treated as restrictions | HIGH | NO | none | Protective fail-closed rule stated in the source: 'Warnings are restrictions in this bounded profile. They never become implicit permission merely because the underlying AGT decision allows.' Relaxing it would widen. Proposed IMMU |
| W9-027 | merge.py:129-151; dedupe.py:111-135, 144-155 | Definitions of "applied" and "unresolved" attempt | HIGH | NO | none | Recovery classification that errs toward blocking a new key: an attempted/unknown attempt without a closeout is treated as possibly applied (unresolved) so no new effect id is minted; only failed attempts are treated as not applie |

Decisive evidence summary: W6-042 (a missing `ObservationPolicy` always produces a hold) is an immutable control by source; W4-014/W4-015 are inert (no consumer); W8-091 stays open on source (see AD-22). On the workers' own assessment 16 of the 32 rows remain `still_configurable = UNRESOLVED`: W1-029, W1-056, W1-058, W1-073, W2-025, W2-036, W2-038, W2-067, W2-077, W2-082, W3-024, W3-063, W5-012, W5-023, W8-091, W9-007; the other 16 are assessed NO (not a configurable rule) but are still not reclassified.

## 2. Architect decisions

Recorded 2026-10-27 from the Architect's review of PR #50 at `ad7c7896ee4f9af3cced6e91ce4cc33b6fe93b27`. The original questions and evidence are preserved unchanged; the right-hand column is the only addition. AD-01 is ACCEPTED; AD-02 and AD-03 are DIRECTION ACCEPTED; the other 21 decisions are OPEN. No worker classification, proposed resolution or reclassification is ratified by these dispositions.

| Id | Decision (original question) | Source | Architect disposition |
|---|---|---|---|
| AD-01 | Reclassify M1: F1b is ALREADY-GOVERNED in f1ab; confirm M1 becomes negative-oracle closure. | A finding 2 | **ACCEPTED** (2026-10-27). F1b is already governed through Registry r08-v2 `f1ab`; proposed M1 is reclassified as negative-oracle closure; no additional F1b implementation is required. |
| AD-02 | Reconcile Plan v1.0 'F4/F5 not covered' with the registered `f4`/`f5` families; map M11/M12 to the remainder. | A finding 4 | **DIRECTION ACCEPTED; detailed scope pending.** F4 and F5 are partially Registry-governed; future increments exclude already-governed fields and identify only the remaining eligible configuration; exact contract changes remain subject to G1 review. |
| AD-03 | Contract path for every new Registry-carried field: new family id under r08-v2 (hand edits to `FAMILIES_V2` and `IDENTITY_FAMILIES`) or r08-v3. | A decision 5 | **DIRECTION ACCEPTED; successor contract pending.** Prefer a versioned successor contract over silently modifying frozen r08-v2 schemas; the specific family/version design is deferred to G1; this does not authorize contract implementation. |
| AD-04 | Add a single-source test tying `FAMILIES_V2` to `IDENTITY_FAMILIES` (no test asserts their key sets are equal today). | A decision 3 | OPEN |
| AD-05 | Ratify or replace the constant `MAX_SNAPSHOT_NODES = 1048576`, labelled PROPOSED in source. | A decision 4 | OPEN |
| AD-06 | For institutions and authority domains: equality ('carried unchanged') or subset (what Runtime enforces)? | A/B | OPEN |
| AD-07 | May the Registry ever carry `max_amount`, `max_effects`, `allowed_target_prefixes`, `target_match`, given Amendment 3 records them as caller-owned residuals? | A/B/C | OPEN |
| AD-08 | Confirm F3 limits stay floors (at most host-owned lowering). | B | OPEN |
| AD-09 | Recovery window 86400 s and OpenShell timeout are the only low-risk resource candidates; confirm eligibility. | B | OPEN |
| AD-10 | Confirm F6 (Runtime permissions) and F7 (Runtime TTL) as OUT-OF-SCOPE. | B | OPEN |
| AD-11 | Mapping of the Registry F4 status scalar onto conflict/policy status when a runtime-authority profile exists. | C surprise 5 | OPEN |
| AD-12 | Retire or guard inert `policy_config.default_action`, `authority_records_from_policy_config` and demo helpers. | C | OPEN |
| AD-13 | Is `DedupeProfile` policy or a provider fact? | C | OPEN |
| AD-14 | Relationship of the hub's `ocs-registry-record/0` format to Registry r08-v2. | D | OPEN |
| AD-15 | Constitution checkout HEAD `a4dd1111` inverts tier numbering relative to pin `1c2e920f`; confirm the pin remains authoritative. | D | OPEN |
| AD-16 | Replay-bundle and evidence-pack importers accept only Control Plane `7a4bcd40` / Runtime `c5e97e87` / manifest `fa170815`; current mains are refused. Wave G3 changes will hit this. | D | OPEN |
| AD-17 | The verifier vendors reasons 0.1/0.2 only; the Control Plane ships 0.3 (eight more codes). | D | OPEN |
| AD-18 | Tenant-id bound 128 appears in 8 places across 3 repositories with no shared source. | C/D | OPEN |
| AD-19 | Are hub, exchange, replay-bundle and action-manifest reference values in scope for the migration program? | D | OPEN |
| AD-20 | Consequence-tier delay ceilings (T0 4h … T4 30d) are proposed and unenforced; owner confirmation needed (BLOCKED). | D | OPEN |
| AD-21 | Claim-scanner term tables: in scope of the Registry? | D | OPEN |
| AD-22 | Origin of the effect cap (W8-091): minimum of three declared integers; who owns each? | C | OPEN |
| AD-23 | F10 tier: Tier 3 supportable (worker) vs Tier 2 minimum (S02 section 3). | C | OPEN |
| AD-24 | Several test names cited by S02 are NOT FOUND in current Runtime tests; confirm the cited equivalents. | B | OPEN |

## 3. Reclassification proposals (NOT applied)

Workers proposed 20 reclassifications. They are recorded here and in `evidence/worker-*/reclassification_proposals.json` as **unratified proposals**; the historical classes in the crosswalk are unchanged.

| Worker | Row | Historical class | Proposed |
|---|---|---|---|
| B | W1-007 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL (admission floor) |
| B | W1-008 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL (admission floor) |
| B | W1-027 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL (admission floor) |
| B | W1-030 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL (admission floor) |
| B | W2-086 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL (admission floor) |
| B | W2-087 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL (admission floor) |
| B | W3-062 | CONFIGURABLE-CANDIDATE | CALLER_SUPPLIED (synthetic destination constructor arg), OUT-OF-SCOPE |
| B | W2-001 | CONFIGURABLE-CANDIDATE | HOST_OWNED_CONFIG, OUT-OF-SCOPE (legacy unauthenticated shell) |
| B | W2-003 | CONFIGURABLE-CANDIDATE | sample data, HOST_OWNED_CONFIG, OUT-OF-SCOPE |
| B | W1-040 | CONFIGURABLE-CANDIDATE | ALREADY-GOVERNED (REGISTRY_BACKED sets) |
| C | W8-011 | CONFIGURABLE-CANDIDATE | CALLER_SUPPLIED (approved authority-context data, not host profile policy) |
| C | W6-042 | UNRESOLVED | IMMUTABLE_CONTROL (presence requirement; fail-closed) |
| C | W4-014/W4-015 | UNRESOLVED | DEAD/INERT FIELD (no consumer) |
| C | W4-020/W4-021 | CONFIGURABLE-CANDIDATE | OUT-OF-SCOPE (demo-only caller-overridable defaults, no caller in repo) |
| C | W5-002 | CONFIGURABLE-CANDIDATE | CONFIGURABLE-CANDIDATE, Tier 3 supportable (diagnostic only in this repo) |
| C | W5-044 | UNRESOLVED | IMMUTABLE_CONTROL / diagnostic severity |
| C | W8-042 | CONFIGURABLE-CANDIDATE | IMMUTABLE_CONTROL-adjacent safeguard toggle (migration would only permit weakening) |
| C | W8-040..W8-044 | CONFIGURABLE-CANDIDATE (coordinates 'cumulative') | UNCHANGED class; coordinates corrected |
| C | W9-002 | CONFIGURABLE-CANDIDATE (single row) | split: IMMUTABLE_CONTROL (payload redaction and fingerprint blanking at CLI) + CALLER_SUPP |
| C | W8-091 | UNRESOLVED | derived minimum of host/issuer-declared values (no literal) |

## 4. Coverage limits that bear on these decisions

Test bodies were not read and no test was executed. Evidence-registry and evidence-attestation were not audited. Worker D read slices of Stack Qualification only. Hub docs, scenarios and fixtures, replay-bundle and evidence-pack validators, and ODES RFCs were not read. W3-063 and W1-029 were resolved by Worker B.
