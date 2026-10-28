# Worker E notes (Registry-side), registry @ 317eb76acb2847c534c3ce7c2180b89b4aef987d

Method: read-only. No test executed; `pytest --collect-only` only (system `python -m pytest` is unavailable, `/root/.local/bin/pytest` 9.1.1 used, see test_inventory.json). Checkout `git status` stayed clean. Claims marked VERIFIED were read in source; INFERRED are called out.

## Answers to the four focus questions

(a) G0 worker A's claim ("decision-level narrowing and deny-all tested only for allowed_units"):
- VERIFIED at the public decision level: tests/test_v01a_v2_record_path.py V1A-02 (narrowing) and V1A-03 (deny-all) use allowed_units only; V1A-01 has identical single-element caller/registry sets for institutions and domains; the only institutions-specific decision-level case is `pop('allowed_institutions')` (V1A-04).
- REFUTED at the composer level: tests/test_r08v2_f1ab_family.py covers all five keys for field_missing, malformed lists, oversize (256/257), token rule, 32 empty combinations (deny-all) and caller-missing-set. Its only per-set weakness is that the grid, registry-cannot-widen and 128-boundary tests use one key (units / actions / actions).
- PARTIAL for vectors: EP-004 (all five empty), EP-007 and EP-008 (institutions and domains narrowed) exist in docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json, but their composition is checked with a test-local `compose()` (tests/test_ext_s1_5_vectors.py:744) and Node, never with `v2_f1ab.compose_f1ab`. Single-dimension deny-all vectors (EP-011/012) are units only.

(b) Golden vectors with f1ab records narrowing institutions/domains: none in tests/golden (f1ab appears only as a refused family string on a 3-key payload under r08-v1) or in tests/vectors. The registry_conformance vectors name the family f1ab but carry no payload sets. The only vectors with narrowed institutions/domains are the ext-s1-5 EP-007/EP-008 effective payloads (see above).

(c) Crossing scope.institution / scope.authority_domain with payload sets: no test, vector or code does. VERIFIED by grep: allowed_institutions / allowed_authority_domains occur in registry_successor only in v2_f1ab.py and the member tuple of v2_policy_identity.py. All fixtures use inst-a / domain-a for both. The contract never states the intended relation (independent vs containment). This is the largest specification gap (M1-E-12, M1-E-34).

(d) Typed reason codes per set for malformed / empty / case-fold / NFC:
- Payload validation: `field_missing`, `field_unknown`, `field_type_invalid`, `field_invalid` (v2_f1ab.payload_validator) with NO member name; v2_policy_identity.validate_effective_payload reports (code, member) but its vectors only name allowed_actions / allowed_units.
- Empty list: valid, explicit deny-all (no code). Case-fold and NFC/NFD: no code; both are distinct exact strings (test_no_normalization_or_case_folding_in_matching, institutions only), a mismatch yields an empty intersection -> deny-all, not a refusal.
- Composition: `composition_record_invalid`, `composition_caller_invalid`, `composition_family_unsupported`, `composition_operator_unsupported`.
- Decision level: any record fault is collapsed to `composition_record_invalid` (verify.py 412-415; decision.py 89-95), the validator's typed code is visible only from validate_record_text_v2.

## Surprises and contradictions (contract text vs code, or document vs document)

1. Token rule text vs code. Contract section 2 (and Amendment 1 5.1(3)) say "no control, separator or `*`". Code and spec 6.1 (N-13) exclude every Unicode 15.1.0 C* and Z* code point, including Cf, Cs, Co and all unassigned. The frozen contract does not mention the table. U+200B (Cf) is refused by the Registry, accepted by a literal reading of the contract. (M1-E-04)
2. Scope tokens vs payload tokens use different rules. Statement scope tokens and grant tokens use `common.valid_token` (host `unicodedata`, v2_selection.py:67-68, verify.py:343-344); payload entries use the frozen table. Contract line 100 says r08-v2 refuses v1 Unicode scope tokens, Amendment 1 5.3 says they are refused only at binding projection; code matches 5.3. No test pins a Unicode institution through verify_and_decide_v2. (M1-E-13)
3. Two independent validators of the same list rules (`v2_f1ab._list_ok`, `v2_policy_identity.validate_effective_payload`) plus three caller validators (`normalize_caller` lenient, `validate_effective_payload` role caller strict, `LocalExecutionPolicy.__post_init__` accepts any non-empty str). (M1-E-02, M1-E-31)
4. Optional-refusal path (decision.py:54-60) normalises the caller with the f1a three-key normaliser; for a five-key caller it returns None and the raw caller object is returned as `effective`. VERIFIED by reading, not executed. Untested. (M1-E-28)
5. ld02-outcome-map.json is an unratified vetted proposal: it still classifies `selection_scope_mismatch` and 23 other codes as HOLD and says `applied` exists for "F1a sets only"; the ADR (line 131) flips only `selection_epoch_stale` and `selection_withdrawn` to REFUSE. Contract section 6 follows the ADR. Amendment 3/4 use REFUSE `policy_identity_mismatch` for the same institution/domain facts that the map would call HOLD at the scope layer. (M1-E-25, M1-E-29)
6. Amendment 3 maps containment failure to `policy_identity_mismatch`, whose Amendment 1 6.1 definition lists claim-carried identity members vs the durable row; executor sets vs record payload are not in that list. "Evidence cause names the first offending set" has no defined order or spelling, and Amendment 1 6.2a says `member` / `unknown_cause` have no normative weight. (M1-E-22, M1-E-23)
7. Amendment 4 is DRAFT (not effective). Amendment 3 says it is not evidence that F-01 is closed. Registry tests for both are text and hash pins only (tests/test_contract_amendment_3_pins.py, _4_pins.py); the Registry has no executable oracle for effect-time containment. (M1-E-21, M1-E-35)
8. Pin members are named `institution_id` / `authority_domain`; binding members are `scope.institution` / `scope.authority_domain`; Amendment 4 step 5 compares the latter "to the pin's" without stating the mapping. (M1-E-33)
9. Conformance kit: `_IDENT = ^[A-Za-z0-9._:/-]{1,128}$` (highwater.py:75) differs from the binding grammar (admits `/` and a leading `.`/`_`/`:`/`-`). Kit scope key is a JSON array of the seven fields; the identity module defines a versioned scope-key object. Kit also uses kit-local codes (`issuer_revoked`, `record_revoked`, `required_binding_missing`) not in CODES_V2_REV2 (Amendment 1 6.1 notes this for finer unknown causes only). (M1-E-20)
10. S04 (frozen v1 overlay) builds a policy with an empty intersection and lets `check()` deny; the v2 contract (D-20, section 6) says deny-all is decided before any policy object exists. Both stand; S04/S05 tests cover three sets only. (M1-E-11, M1-E-32)
11. Contract line 184: the scope key includes `selection_id`, while "at most one selection chain per (consumer_id, scope, operation, family)" excludes it; the kit implements this with `_chain_key`. Consistent, but easy to misread.
12. `v2_f1ab._entry_ok(field, item)` ignores `field`: there is deliberately one rule for all five sets; nothing in the tests would notice a future per-field divergence (M1-E-01).

## Environment caveats

- pynacl is not installed here: tests/test_v01a_v2_record_path.py (the only decision-level f1ab suite) skips as a module; test_s01_withdrawal_floor_signing.py skips its backend tests. Collection counts include them. Node-based cross-check in test_ext_s1_5_vectors.py skips without node (CI=true makes it required, per its skip reason).
- Collected counts are parametrised-expanded; the brief's `python -m pytest --collect-only -q <file>` form failed (no pytest in system python), so the uv-tool pytest binary was used with the same flags.

## Not read (summary; per-topic lists in topics.json)

registry_successor/v2_token_table.py body, v2_age_bounds.py (F4/F5), tests/s05_oracle.py and tests/s05_expectations.json (relied on grep for institution and on the test docstring), tests/test_ext_s1_4_age_slots.py, adapter ed25519 tests, docs/f-a1-authorization-pin/*, ADR EXT-S4-0, docs/conformance/README.md, docs/s05-comparison-spec.md, bodies of highwater.py lines 220-360 and 700-960, large parts of the ext-s1-5 spec beyond section 6.1.
