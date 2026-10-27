# G0 Worker B notes (Execution Runtime 0dde0ef7)
## Scope covered
Read in full or in the relevant ranges: engine/safe_executor.py (policy, admission, attempts), permissions.py/.json, engine.py, dedupe_destination.py, recovery_resolution.py (freshness), operation_admission.py, refund_intent.py, control_plane_adapter.py (execute/reconcile ranges), openshell_environment.py/openshell_worker.py (limits), registry_f1a_narrowing.py (full), registry_selection_authority.py (constants, check_effect/containment, sa_fields/digest helpers), authorization_pin.py/authorization_pin_format.py (constants, fence, check_claim_against_pin), host/authorization_pin/installer.py (config, fence), local_authority_effect.py (git diff vs old pin, budget code, remove_authoritative_state), examples/openshell/provision.py (args). Old pin compared via git diff --stat (permissions, dedupe, recovery, safe_executor, openshell, refund_intent, operation_admission, control_plane_adapter are UNCHANGED; only LAE and atomic executor changed).
## NOT read / only grepped
Bodies of registry_selection_authority.py outside constants/check_effect (replay, sync, snapshot logic), authorization_pin_format.py parse functions, installer.py crash-recovery body, revocation_closeout.py, producer_contract.py, effective_grant.py, c8_source_evidence.py, delayed_commit_destination.py, operation_identity_*.py (grepped for numeric literals only: none policy-like). Test bodies not read except where cited. docs/ not read beyond names. .github workflows: names listed and grepped for timeouts (CI only; no runtime value).
## Directories that do not exist
No conformance/, schemas/, tools/ in this checkout (ls shows engine host tests examples sandbox collateral docs). tests/contracts and tests/fixtures exist; only authorization_pin_vectors.json noted.
## Method
grep for literals/defaults/dataclass fields/environ/getenv/argparse/json.load; git diff --stat ec728da6..HEAD; targeted reads.
## Surprises
1. S02-named tests (test_amount_exactly_at_max_is_allowed, test_effective_max_effects_equal_to_policy_max_is_allowed, test_each_local_restriction_refuses_with_its_stable_reason, test_default_target_match_is_segment_aware_..., test_segment_aware_target_matching_through_execute_snapshot, test_exact_target_match_mode_allows_only_the_exact_target) are NOT FOUND by those names in current tests; equivalents are cited in candidates. No test found for max_amount/max_effects equal-boundary by name.
2. The Runtime effect-time Registry guard compares only the five f1ab sets (F-01 subset + digest). max_amount, max_effects, allowed_target_prefixes and target_match are never compared with any Registry record; registry_f1a_narrowing preserves them from the caller policy.
3. Per the brief the Registry contract carries institutions and authority domains unchanged, yet Runtime narrows/contains all five including those two; Architect should confirm the intended order relation for those two (equal vs subset).
4. Tenant length: Runtime 128, Registry identifier 128, pin string members 512.
5. Pin is default-off (authorization_pin=None keeps pre-pin behaviour); selection guard returns None (legacy behaviour) when no store, no binding, no tables.
6. remove_authoritative_state deletes grant rows without a retained-revocation record, while approvals gained authority_approval_revocations_v1; authority-surface question, not a config value.
7. reconcile() derives trusted_institution_id/authority_domain from the envelope's own snapshot.
## Architect decisions needed
- Is a new Registry family for amount/effects/target (CONDITIONAL, G0-B-004/006/007/008) wanted; target prefix order relation is non-trivial.
- Confirm F3 limits (G0-B-001/002/003/028) stay floors, with at most host-owned lowering.
- recovery 86400 window (G0-B-016) and OpenShell timeout (G0-B-027) are the only low-risk resource-budget candidates, both tier 3.
- F6 permissions and F7 TTL are legacy/synthetic: confirm OUT-OF-SCOPE.
