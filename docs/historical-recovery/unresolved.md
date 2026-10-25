# Unresolved items, missing provenance and contradictions

Adverse findings are preserved here, not smoothed. Labels: **[V]** verified here, **[R]** reported by a source, **[I]** inferred.

## U1. V0.2 provenance is not established

- All 3,190 rule entries have `release_scope: v0_1`; 2,802 scenarios and 6,612 tests are `v0_1`, and 38 scenarios and 36 tests are `post_v0_1`. Fixtures: 1,981 `v0_1`, 30 `unknown`. No layer has a V0.2 value. [V]
- `manifest.registry_version` is `0.1.0`; every source revision is the review tag `review-v0.1-g8-r10-20261022` ("Cognous Open Control Stack v0.1, candidate g8-r10"; the entries describe it as a review marker, not a release) or `unrecorded`. [V]
- No rule entry cites a path under `docs/program-v0.2/`. [V] The only content labelled "0.2" is the `runtime-authority-reasons/0.2` registry (164 entries), which is a registry version and a superset of 0.1 (43 additional codes), not a statement that the entries belong to a V0.2 release. [V]
- The 38 `post_v0_1` scenarios and the lineage sets (`L-nc4-03-history`, `L-prereg-amendments`, both `POST_V0.1`) are later than the review tag but are not labelled V0.2. [V]
- Consequence: the "V0.2 historical rule inventory" named in the assignment cannot be isolated from this catalogue. What is recovered here is the V0.1 review-tag inventory, with the 0.2 reason registry identified as the one explicitly 0.2-labelled population. Which of these the operator means by V0.2 needs an architect or operator ruling.

## U2. Missing and weak provenance (catalogue-recorded) [V counts]

| Gap | Count |
|---|---|
| Evidence records with no source revision | 17,704 of 19,860 (D 17,654; B 50) |
| Evidence records whose kind is unclassified | 1,153 |
| Entries with no source revision | 45 (all fixtures), as reported in `unresolved_accounting`; the partition-B load-problem record lists 123 (see below) |
| Entries lacking G2 attributes | 30 |
| References that are not catalogue ids | 114 (partition A) and 12 (partition D) |
| Unembedded relationship rows with no endpoint | 14,456 |
| Entries with unresolved MVP applicability | 14,176 |
| Unresolved crosswalk rows | 9 (`A2:1022`, `A2:1023`, `C:6845`-`C:6847`, `C2:35`-`C2:38`) |
| Source-inventory revisions recorded as `unrecorded` | the raw-set inventories for action-manifest and control-plane (set B) and stack-qualification (set D) each list `unrecorded` next to the pinned revisions |

Load problems recorded in the manifest are eight records over six kinds: `ref_not_a_catalogue_id`, `entry_without_source_revision`, `evidence_without_source_revision`, `evidence_kind_unclassified`, `entry_without_g2_attributes`, `unresolved_relationship_row_without_endpoint`. [V]

The partition-B load-problem record lists 123 entries without a source revision, while `unresolved_accounting` reports 45. This exercise did not reconcile the two; treat both as catalogue-reported and the difference as unexplained. [V that the two numbers differ; cause unknown]

## U3. Contradictions and ambiguities inside the catalogue

1. **Label versus assignment.** Assignment says V0.2; catalogue says 0.1.0 (U1).
2. **Passing validation does not mean true.** The validator checks internal consistency and digest commitments, not truth of source claims and not raw record content. [R, catalogue README]
3. **Size note.** The catalogue README says the compact catalogue is "about 42 MB, no file over 4 MB". `catalogue-v0.1/` is 53,940,243 bytes; no file exceeds 4 MiB; the largest is 4,128,681 bytes, above 4,000,000. [V] Possibly the README excludes some directories; not investigated.
4. **`mvp_fixed` does not mean enforced.** Of the 7 `mvp_fixed` rules, several are named known limits, a known failure or an expected ABSTAIN. [V] The label cannot be read as "required" or "satisfied".
5. **Statement text that is not rule text.** 28 + 9 + 8 Qualification entries carry a metadata object as their statement; 116 verifier entries carry a templated "refuted finding code ... emitted by `<file>`" sentence; 12 verifier entries state "NO DISPOSITION TEXT in docs/tiers.md (id exists in source only)". [V] These are entries, not independent rules.
6. **Same identifier, several repositories.** 68 native ids (for example `E001`) occur in more than one repository, kept distinct because equivalence is not established. [V]
7. **Vendored copies.** Control Plane lifecycle codes are copies of ODES contract validators (lineage "copied_from ... vendored"), so some Control Plane and ODES entries describe one rule twice. [R]
8. **Moved sources.** Qualification `main` and the Control Plane and Runtime heads differ from the pinned commits at the time of reading (Qualification `998d39c5`, Control Plane `7a4bcd40`, Runtime `c5e97e87`). [V] The catalogue is a point-in-time record.
9. **Not a registry.** No entry is an `ocs-registry-record/0` record (`registry_records: []`); all 3,190 are `source_statement` references. Nothing in the catalogue has been validated against the S03 contract. [V]
10. **Adopted versus proposed.** 35 floors are `adopted`; 229 Constitution v0.1 clauses are `proposed_not_adopted`; the adoption status of the other 2,926 is `unknown`. [V]

## U4. The 32 unresolved S02 classifications (preserved)

The list equals `docs/s02-inventory.md` section 5. [V] None is resolved, reclassified or proposed for migration by this exercise. The catalogue was not used to resolve any of them: no row has a name-level overlap with a catalogue code, and the three rows that cite a file the catalogue also covers (W5-011, W5-012, W5-023) concern constants and a default posture that no catalogue entry records. The wording below is the S02 raw-table rationale, truncated; the full rows are in `docs/s02-evidence/W1.md` to `W9.md`. Coordinates are as recorded by S02, including the cumulative W8 coordinates and the other citation errata in `docs/s02-evidence/README.md`.

Worker scopes (from `docs/s02-inventory.md` section 2): W1 Runtime `safe_executor.py`; W2 Runtime admission and grant; W3 Runtime effect and recovery; W4 Control Plane policy gate; W5 Control Plane reasons and validation; W6 Control Plane `bounded.py` lines 1 to 1400; W7 `bounded.py` lines 1401 to 2756; W8 Control Plane authority and freshness; W9 Control Plane remaining files. Where the location column below shows only a number, it is a line in that worker's primary file.

| S02 ID | Source location (as recorded) | Construct | Reason recorded in the S02 table (truncated) |
|---|---|---|---|
| W1-029 | 343 | `_TARGET_MATCH_MODES = ("segment","exact","legacy-prefix")` | The mode is already caller-supplied per policy instance, but "legacy-prefix" is a security-weakening option and the allowed set decides what policy authors may choose; whether the set itself is confi… |
| W1-056 | 521-562 | legacy attempts migration | Migration touches historical evidence; I did not verify atomicity, and the "legacy:unknown" sentinel semantics are used nowhere else in this file. |
| W1-058 | 701-713 | `transition_attempt` | The status column is free text here, so the allowed vocabulary is enforced only by callers; I cannot tell from this file whether that is intended. |
| W1-073 | 1073-1088 | `observe_historical` | Deliberately skips authority/policy (docstring); whether any caller gating exists is outside this file. |
| W2-025 | engine/operation_admission.py:152-155 | required observation set `{applied,partial,absent,unknown}` | Could be a tunable qualification bar or a profile invariant; the governing profile text is not in my files so I cannot tell |
| W2-036 | engine/refund_intent.py:26,34-35 | `effect_class` restricted to `"refund.issue"` | Hardcoded profile scope; could be a registry-selectable effect class or a deliberate synthetic-profile limit, code does not say |
| W2-038 | engine/refund_intent.py:55-59 | scope binding and action id set | The scope-equality check is an admission invariant, but the two-element action-id set is hardcoded vocabulary that could be list data; code does not state which |
| W2-067 | engine/control_plane_adapter.py:160-168 | result to exception mapping, definitive-rejection code set | The seven codes are reason vocabulary, but membership decides definitive rejection versus ambiguous failure, which affects reconciliation and retry; I cannot tell if that is policy |
| W2-077 | engine/control_plane_adapter.py:424-436 | `reconcile` trusted ids from snapshot | Unlike `execute` (W2-069), trust is not independently derived; may be acceptable because it is effect-free, but the code does not say |
| W2-082 | engine/openshell_environment.py:89-90 | qualified profile `docker`, cpu `1`, memory `256Mi` | Hardcoded values look like resource configuration, but the error text says they are the qualified profile, so changing them is a qualification decision |
| W3-024 | LAE:546-560 | remove_authoritative_state | Not a rule about thresholds; deleting a grant row removes the revoked status without writing the revocation table, a point the code does not address; whether this is intended test-support or an autho… |
| W3-063 | DD:76-93 | _operation_guard TTL logic | Docstring 6-9 says forgetting the key after TTL is deliberately modelled "that is the duplicate the control plane's escalation deadline ... exists to beat"; the strictness `now - ... < ttl` is behavi… |
| W4-004 | policy_gate.py:196-201 | rule `read_allowed_tool_policy` | Mapping "read => no authority needed" is hardcoded policy-like, but removing/altering it changes admission semantics; cannot show change would not weaken a mandatory check, so not nominated |
| W4-014 | policy_config.py:16-23 | `PolicyConfig` model | Config schema is already data-driven (tools lists, authority_required); `default_action` is declared but a grep of src/ found no consumer in policy_gate.py or policy_config.py (only manifest/bounded… |
| W4-015 | policy_config.py:23 | default literal `"escalate"` for default_action | See W4-014; unused by PolicyGate in inspected files |
| W4-018 | policy_config.py:62-82 | `authority_records_from_policy_config`; default source "policy_config… | Config-defined grants are already data, but the action_type key is ignored so scopes are granted globally; whether that is intended or a mandatory-boundary issue is not decidable from this file; also… |
| W4-022 | demo_policies.py:50-54 | add_authority_record scope ["read"], source "demo_policy_config" | Grants authority (a scope) hardcoded; note gate has no "read" scope check, so scope has no effect on gate; semantics beyond this not inspected |
| W4-023 | demo_policies.py:95-99 | add_authority_record scope ["read","write"] | Hardcoded authority grant unlocks write rule W4-005; authority/admission, so not nominated |
| W4-033 | rule_revision.py:150 | `d != "unsigned_revision_row"` exemption | Deliberate visibility choice per docstring :142; whether it is policy or invariant is not stated |
| W5-011 | manifest_validation.py:17 | `SUPPORTED_VERSIONS = frozenset({"1.0","1.1"})` | Set must track the external action-manifest validator (docstring lines 3-8); whether it is meant to be locally configurable is not stated, and widening weakens a fail-closed gate |
| W5-012 | manifest_validation.py:18-21 | `_EFFECTFUL`, `_HIGH_RISK`, `_PRIVILEGED` frozensets of action types… | Hardcoded and partly overlapping sets mirror an external validator; parity test comments say a later revision treats `export` as effectful (parity test comment near line 196), so authority lies outsi… |
| W5-023 | manifest_validation.py:86-88 | `manifest_default = manifest.get("default_action","escalate")` and `a… | Hardcoded default posture; mirrors external validator semantics, not shown to be locally decided; also the gate tests ::test_action_override_of_a_blocked_manifest_default_is_not_blocked show gate-sid… |
| W5-028 | decision_input_profile.py:50-56,269-272… | ALLOWED_ASSURANCE_CLASSES (4), ALLOWED_EVIDENCE_STATES {current, unkn… | Closed sets at lines 50-56; whether profile intends them extensible is unstated, and the profile is non-authorizing and unwired |
| W5-044 | validation.py:188-193 | `authority_actor_mismatch` is a warning, not an error | Severity could be a policy choice but code gives no rationale; downgrading/upgrading changes whether a report is valid |
| W6-004 | 100 | `EVIDENCE_KINDS = {"authorization","context","post_effect"}` | looks like a schema enum (SERIALIZATION) but consumer not inspected; cannot tell if extensible without weakening a check |
| W6-005 | 101 | `UNKNOWN_BEHAVIORS = {hold_effect, preserve_if_other_basis_suffices,… | allow-list governing unknown-state handling; whether adding values weakens fail-closed unknowable from lines 1-1400 |
| W6-042 | 1276, 1300 | `observation_policy` optional; deep-copied | cannot tell from lines 1-1400 whether absent policy fails closed |
| W8-014 | RA:153-170 | RuntimeAuthorityProfile fields: catalogue_version, actions, producer_… | The catalogue/keys are by design host configuration, but the profile toggles (opt-in sub-profiles; allow_synthetic_resolver consumer is outside my files, grep not done here) cannot be classed without… |
| W8-091 | LAE:443 | max_effects = current.effective_max_effects | Value origin not visible in assigned files |
| W9-007 | records.py:66-67, 190-228 | `PolicyGate()` default and `include_trace=True` default | The actual rule chain is in policy_gate.py (not my file); the default-gate construction cannot be classified without it |
| W9-017 | microsoft_agt.py:288-302 | AGT warnings treated as restrictions | Comment says "in this bounded profile" warnings are restrictions; cannot tell from code alone whether this is a protected invariant or a profile choice that could be loosened; conservative: not marke… |
| W9-027 | merge.py:129-151; dedupe.py:111-135, 14… | Definitions of "applied" and "unresolved" attempt | State-classification semantics duplicated across two modules with a visible difference; I cannot tell from these files whether the difference is intended |

Highest-attention items per S02: W4-033 (unsigned rule-revision rows recorded, not refused), W5-044 (authority and actor mismatch is a warning), W9-017 (AGT warnings force `hold`), W9-027 (definitions of "applied" and "unresolved" attempt differ between `merge.py` and `dedupe.py`).

Each row needs its own architect ruling. Where a catalogue entry is conceptually adjacent (W3-063 and W9-027 with the `dedupe_*` and `attempt_unresolved_past_horizon` codes; W5-011 and W5-012 with the manifest validator rules; W4-033 with the ODES rule-revision rows), the adjacency is noted for the ruling and decides nothing.

## U5. Not verified in this exercise

- Raw inputs behind the catalogue (426 files) and regeneration of any partition.
- Any catalogue entry against its source other than the 285 Control Plane reason-registry entries (counts and code sets only; not text).
- Whether the 12 repositories' current heads still contain the catalogued sources.
- The Constitution text and the adoption record for `CR-001` to `CR-035`.
- Operator adoption of the MVP definition and scope-reduction register (the project crosswalk reports it as not found). [R]
- The hub and Qualification pull requests that may further revise the catalogue manifest. [R]
- Test results: no rule, scenario or test was executed, here or by the catalogue.
