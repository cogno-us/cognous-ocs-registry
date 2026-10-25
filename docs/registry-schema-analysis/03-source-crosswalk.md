# 03 Source crosswalk

Non-authorizing analysis. Labels: [V] verified by reading source in this analysis, [R] reported, [I] inferred. Source reads were of Control Plane tag commit `0a41faa9` and Runtime tag commit `ec728da6` (the S02 pins) in scratch clones; they are not committed. Line numbers are as read at those commits.

Match labels: **EXACT MATCH** (same construct or identical string in the same role), **RELATED** (same subject, different role or representation), **LEXICAL LEAD** (shared words only), **UNRELATED**, **UNRESOLVED**. A similar name is never a match.

## 1. Documents reconciled

| Document | Used for |
|---|---|
| `docs/s02-inventory.md`, `docs/s02-evidence/W1..W9.md` | families F1 to F11, 620 rows, 32 unresolved |
| `docs/s03-contract.md`, `docs/s04-implementation.md`, `docs/s05-equivalence-report.md` | current contract, consumer, evidence |
| `docs/s06-next-family-recommendation.md`, `docs/trust-limitations.md` | candidate ordering, limits T1 to T14 |
| `docs/historical-recovery/` (PR #13, head `16b9ca81`, not yet merged) | catalogue accounting and lexical leads |

## 2. Family against catalogue

| S02 family | Catalogue counterpart | Label | Basis |
|---|---|---|---|
| F1 | none names `LocalExecutionPolicy` or its allow-lists; 11 lexical leads are limit-related codes | LEXICAL LEAD | PR #13 crosswalk §3 [R] |
| F1c ceilings | codes such as `missing_amount_limit`, `effect_limit_malformed` | LEXICAL LEAD | same |
| F4 | ODES `freshness-clocks` rows (74 unknown-strength rows, 10 reason codes) | LEXICAL LEAD | rows read as error-code tables; none carries the 300, 86,400 or 60 literals [R] |
| F5 | `R-CP:RAR02:holder_inventory_missing` against S02 W8-068 `HolderInventory` | EXACT MATCH on the code string; RELATED in role | host data feeding a check versus a vocabulary entry [R] |
| F7 | `dedupe_operation_effect_applied`, `dedupe_unresolved_attempt_blocks_new_key`, `escalation_after_key_ttl`, `attempt_unresolved_past_horizon` | RELATED (names the same semantics) | not used to resolve W3-063 or W9-027 |
| F6, F2, F8, F9 | none | UNRELATED | zero leads [R] |
| F10 | ODES rule-revision rows | LEXICAL LEAD | weak overlap [R] |
| F11 | validator rules on redaction in other repositories | LEXICAL LEAD | not the Control Plane redaction configuration [R] |
| M7 | 1,819 reason-code entries | RELATED | S02 REFUSAL rows are codes in Runtime/Control Plane code; the catalogue entries are registry and table rows |

Only 369 of 3,190 catalogue entries come from the two S02 repositories, and the single shared code file is `manifest_validation.py` [R].

## 3. Priority rows read from source

### W8-091 effect cap origin [V]

`effective_max_effects` is the minimum of the requirement permission's `max_effects`, the grant permission's `max_effects` and the action's `effect_limits.max_effects` (defaulting to the proposal's effect count), computed in Control Plane `bounded.py` near lines 2570 to 2574. It is consumed as the budget `max_effects` at Control Plane `local_authority_effect.py:443` and compared in Runtime `safe_executor.py:429` against the policy's `max_effects` ceiling. The S02 coordinate `LAE:443` is a cumulative W8 coordinate.

Result: the **origin** is established (a minimum over three authority-derived sources). Whether the Runtime ceiling is an invariant, caller data or registry-eligible data is a classification and remains UNRESOLVED.

### W3-063 dedupe TTL [V]

Runtime `engine/dedupe_destination.py` `_operation_guard` refuses `operation_already_committed` for a different effect id inside the TTL and forgets the key after it. The module documents the forgetting as a deliberate model of the duplicate that the Control Plane escalation deadline exists to beat. `dedupe_ttl_seconds` must be a positive int; default 600 in `DedupeTtlOperationDestination`. Control Plane `dedupe.py` `DedupeProfile` is a triple with the ordering `provider_horizon_seconds <= escalation_deadline_seconds < dedupe_ttl_seconds`. `dedupe_mode` is `destination_ttl` only when the destination declares capability `dedupe-ttl/0.1` with a TTL not below the profile's. The Control Plane ledger memory never expires.

Result: F7 is a multi-field profile spanning two components, not one value. Classification remains UNRESOLVED.

### W9-027 applied versus unresolved attempt [V]

`dedupe.unresolved_effects` treats any closeout as closing an effect. `dedupe.applied_under_other_effect` counts only closeouts whose `observed_state` is `applied` or `partial`, although its docstring says "any attempt with a closeout". `merge.attempt_outcomes` counts only `applied` or `partial` as applied, so an attempt with an `absent` closeout is resolved in one module and unresolved in the other.

Result: the difference is confirmed, along with a docstring/code mismatch. Intent is not determinable from code. UNRESOLVED; needs an architectural ruling.

### W8-014 authority-profile toggles [V]

`RuntimeAuthorityProfile` (`runtime_authority.py:153-170`) carries `allow_synthetic_resolver: bool = False`, consumed at `bounded.py:1288` and `:2113`, which relaxes the authenticated-resolver requirement. It also carries opt-in sub-profiles (operation_identity, freshness, holder_inventory, merge, reversibility, dedupe, terminal_revocation), omitted from dumps when unset; merge and dedupe require operation_identity. `ActionClass` carries `class_id`, `irreversible`, `max_status_age_seconds` (default 60), `on_unreadable` (`refuse` or `bounded_tolerance`), `requires_revocation_assurance`, `reversibility`, `reads_protected_data`, `counterparty_observable`.

Result: the consumer of the toggle is found. Proposal: a security-relaxing host toggle is never registry data (04, 08). Row remains UNRESOLVED.

### W6-042 absent observation policy [V]

When `observation_policy` is None, `bounded.py` (about lines 1856 to 1858 and 1899 to 1901) appends `observation_policy_missing`, giving a hold. `ObservationPolicy.max_age_seconds` is required (positive, no default); `clock_tolerance_seconds` defaults to 5.

Result: fail-closed behavior at those call sites is established. Classification remains UNRESOLVED.

### 60 versus 300 [V]

`ActionClass.max_status_age_seconds` default 60 bounds the age of an authority **status** read per action class. `ObservationPolicy(max_age_seconds=300, clock_tolerance_seconds=5)` at `cli_run.py:510` is a literal bounding **destination observations**. A grep for 300 in the Control Plane source finds only that literal. No code links the two. They are different quantities on different observed objects. This is a source finding, not a ruling; the S02/S06 relationship stays UNRESOLVED until the Architect rules (08). Any schema proposal treats them as two separately typed bounds with no composition between them.

## 4. The 32 unresolved S02 rows

Rule applied: factual resolution of a value's origin or behavior is not resolution of the S02 invariant-versus-configurable classification. **All 32 remain UNRESOLVED.** Ten rows were inspected in this analysis; for those the "read-only finding" is verified. For the other 22 the fact could probably be established by read-only inspection, but that has not been done here [I]. Every row needs an architectural ruling to be classified.

| S02 ID | Construct (S02) | Read-only finding in this analysis | What remains |
|---|---|---|---|
| W1-029 | `_TARGET_MATCH_MODES = ("segment","exact","legacy-prefix")` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W1-056 | legacy attempts migration | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W1-058 | `transition_attempt` | Partly inspected [V]. Callers in `safe_executor.py` and `control_plane_adapter.py:401` pass status strings; no vocabulary check was located in `transition_attempt` by this analysis. | Caller list found. Whether a DB-side check exists was not verified. Ruling needed. |
| W1-073 | `observe_historical` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W2-025 | required observation set `{applied,partial,absent,unknown}` | Partly inspected [V]. `operation_admission.py:152-153` literal set `{applied, partial, absent, unknown}` minus `observation_coverage`. The governing profile text is outside the inspected files. | Literal confirmed. Needs the profile text and a ruling. |
| W2-036 | `effect_class` restricted to `"refund.issue"` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W2-038 | scope binding and action id set | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W2-067 | result to exception mapping, definitive-rejection code set | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W2-077 | `reconcile` trusted ids from snapshot | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W2-082 | qualified profile `docker`, cpu `1`, memory `256Mi` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W3-024 | remove_authoritative_state | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W3-063 | _operation_guard TTL logic | Inspected [V]. `_operation_guard` refuses a different effect id within the TTL and forgets the key after it; this is a documented deliberate model. TTL must be a positive int, default 600. CP `DedupeProfile` requires `provider_horizon <= escalation_deadline < dedupe_ttl`. | Behavior resolved. Ruling needed: whether the TTL is a configurable window or an invariant tied to the escalation deadline (F7). |
| W4-004 | rule `read_allowed_tool_policy` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W4-014 | `PolicyConfig` model | Inspected [V]. `PolicyConfig.default_action` is declared (`policy_config.py:23`). Grep of `src/` finds `default_action` consumers only in `manifest_validation.py:90,99` and `bounded.py:2664`, which read the manifest or action field, not `PolicyConfig`. | No consumer of the `PolicyConfig` field found by grep (not an exhaustive proof). Ruling needed: dead field or planned. |
| W4-015 | default literal `"escalate"` for default_action | Same as W4-014 [V]. | As W4-014. |
| W4-018 | `authority_records_from_policy_config`; default source "policy_config… | Inspected [V]. `authority_records_from_policy_config` iterates `for _action_type, scopes in config.authority_required.items()`; the key is unused, so scopes are not bound to an action type. | Behavior resolved. Ruling needed: intended global grant or defect. |
| W4-022 | add_authority_record scope ["read"], source "demo_policy_config" | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W4-023 | add_authority_record scope ["read","write"] | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W4-033 | `d != "unsigned_revision_row"` exemption | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W5-011 | `SUPPORTED_VERSIONS = frozenset({"1.0","1.1"})` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W5-012 | `_EFFECTFUL`, `_HIGH_RISK`, `_PRIVILEGED` frozensets of action types… | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W5-023 | `manifest_default = manifest.get("default_action","escalate")` and `a… | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W5-028 | ALLOWED_ASSURANCE_CLASSES (4), ALLOWED_EVIDENCE_STATES {current, unkn… | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W5-044 | `authority_actor_mismatch` is a warning, not an error | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W6-004 | `EVIDENCE_KINDS = {"authorization","context","post_effect"}` | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W6-005 | `UNKNOWN_BEHAVIORS = {hold_effect, preserve_if_other_basis_suffices,… | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W6-042 | `observation_policy` optional; deep-copied | Inspected [V]. Absent `observation_policy` appends `observation_policy_missing` (`bounded.py` ~1856-1858, ~1899-1901), giving a hold. `max_age_seconds` has no default. | Fail-closed behavior resolved for those call sites. Classification (invariant vs configurable) still needs a ruling. |
| W8-014 | RuntimeAuthorityProfile fields: catalogue_version, actions, producer_… | Inspected [V]. `allow_synthetic_resolver` (default False) is consumed at CP `bounded.py:1288` and `:2113` and relaxes the authenticated-resolver requirement. Opt-in sub-profiles are omitted from dumps when unset; merge and dedupe require operation_identity. | Consumer found. Ruling needed: the relaxing toggle is proposed as never registry-configurable (04 F5); other fields are host data. |
| W8-091 | max_effects = current.effective_max_effects | Inspected [V]. Origin is `min(requirement max_effects, grant max_effects, action effect_limits.max_effects or proposal.effects)` in CP `bounded.py` (~2570-2574), consumed at CP `local_authority_effect.py:443` and compared to the Runtime policy ceiling at `safe_executor.py:429`. The coordinate "LAE:443" is cumulative. | Origin fact resolved. Ruling still needed: ceiling in `LocalExecutionPolicy` is invariant, caller data or registry-eligible (see 04 F1c). |
| W9-007 | `PolicyGate()` default and `include_trace=True` default | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W9-017 | AGT warnings treated as restrictions | Not inspected in this analysis; S02 reason retained. | Read-only source inspection could probably establish the fact; the classification needs a ruling. [I] |
| W9-027 | Definitions of "applied" and "unresolved" attempt | Inspected [V]. `dedupe.unresolved_effects` treats any closeout as closing an effect; `dedupe.applied_under_other_effect` counts only `applied`/`partial` closeouts although its docstring says "any attempt with a closeout"; `merge.attempt_outcomes` counts only `applied`/`partial` as applied. A closeout observing `absent` resolves an attempt in one module and not the other. | Difference confirmed, intent not determinable from code. Ruling needed: intended divergence or defect. |

Summary: 32 preserved; 10 with a source finding recorded here (none reclassified); 22 not inspected in this analysis; 32 need a ruling. Rows most likely to need a ruling rather than inspection are those whose S02 reason says the code "does not say" (W2-036, W2-038, W4-004, W4-033, W5-044, W9-017).
