# R08-S01 implementation: successor contract `r08-v1` foundation

Status: developer-tested foundation only. **Not a working registry.** Authorized by the operator's R08-S01 instruction ([decision record](decisions/2026-10-24-r08-s01-authorization.md)); F1a is adopted as TARGET scope, not operational acceptance. Release, publication and production are HOLD.

Governing references: plan v1.2 https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.2.md (blob `32319775c6e2d9c3fff1e2171c8f4c9d096911d6`); crosswalk https://github.com/cogno-us/cognous-ocs-registry/blob/main/docs/plans/PROJECT_PLAN-v1.2-REVIEW-CROSSWALK.md; Constitution pin https://github.com/cogno-us/cognous-engineering-constitution/blob/1c2e920f4e58e07a52e8e2408a506cf7dbc1292b/ENGINEERING_CONSTITUTION.md (formal adoption not asserted; ADOPTION.md); merged inventory `docs/historical-recovery`; merged analysis `docs/registry-schema-analysis`; merged preparation `docs/r08-preparation` (merge `1324bab15da20a32fb82f54c444d1e808543b0e6`); frozen `registry_contract/`, `registry_consumer/`, `registry_records/`, `baseline/` unchanged.

## What exists

New package `registry_successor/` (contract `r08-v1`, interface specification [r08-s01-contract.md](r08-s01-contract.md)):

| Module | Does | Does not |
|---|---|---|
| `common.py` | strict JSON (bounded, no duplicate keys, integers only), canonical bytes, digests, validators, the closed refusal-code set | read files, clocks, network |
| `record.py` | exact, bounded F1a record validation; explicit deny-all (empty list); digests | evaluate values; accept a `status` field |
| `selection.py` | selection envelope structure; signing input; effective-selection resolution with explicit supersession | choose by epoch; authenticate |
| `verify.py` | layered technical verification against explicit trusted inputs (structural, integrity, record binding, trust snapshot, authenticity, authority, scope, time, revocation, epoch) | supply a verifier, key or trust root; authorize |
| `compose.py` | F1a `effective = caller INTERSECTION registry` per field; empty intersection is valid deny-all | widen; support another family or operator |
| `decision.py` | per-operation outcome: applied, applied_deny_all, overlay_not_applied (optional only), required_policy_unavailable (required only) | fall back to the caller policy for a required operation |

Frozen S03/S04 behavior is untouched (bytes pinned by `tests/test_s06_integrity.py`). Nothing imports the Runtime or the frozen modules (`tests/test_r08_integrity.py`).

## Behavior summary

- **F1a record.** Exact fields; no `status` (event-derived lifecycle lives outside the record). Payload lists are sorted, duplicate-free, at most 256 entries of 1 to 128 characters without control, separator or `*` characters. An **empty list is a valid deny-all for that dimension**. A **missing field refuses** (`field_missing`): for F1a an absent field is neither implicit allow nor implicit deny. Unknown family, contract, kind or field refuses.
- **Selection.** Exact structure binds record (id, version, digest), evaluator (id, binding, blob, sha), consumer, tenant/institution/authority-domain scope, operation, participation, effective interval (valid_from inclusive, valid_until exclusive), supersession, revocation reference and selector reference. An epoch is not authorization; a higher epoch never supersedes without an explicit named supersession with a decision reference; two effective selections without such a chain refuse (`selection_conflict`).
- **Verification.** A SHA-256 match is integrity only. `authenticated` is true only when an injected `SignatureVerifier` accepts a signature from a non-revoked key in an explicitly supplied, unexpired trust snapshot. **No verifier, key or trust root is supplied by this package**; without one the report refuses `verifier_unavailable`. `operationally_authorized` is always false.
- **Outcomes.** Required operation: any refusal yields `required_policy_unavailable` (conceptually HOLD; mapping to component classes is open decision LD-02) and never the caller policy. Optional operation: any refusal yields `overlay_not_applied` with the caller policy unchanged, explicitly not denial (frozen S04 semantics).

## Authentication reuse recommendation

See [r08-s01/authentication-reuse-assessment.md](r08-s01/authentication-reuse-assessment.md): bundle no verifier and reuse no code in this sprint; keep the injected interface and the explicit `verifier_unavailable` refusal. All three reference verifiers use the same Ed25519 library as each other and none is installed in the registry environment, so a later adapter needs the dependency decision (B-10) first.

## Closed refusal taxonomy

The authoritative set is `registry_successor/common.py` `CODES`; `tests/test_r08_integrity.py` keeps this table equal to it.

| Code | Layer | Meaning |
|---|---|---|
| `input_not_text` | parse | input is not a str or cannot be encoded as UTF-8 |
| `input_too_large` | parse | encoded input exceeds MAX_DOCUMENT_BYTES |
| `json_malformed` | parse | not valid JSON |
| `json_duplicate_key` | parse | an object repeats a key |
| `json_nesting_too_deep` | parse | nesting exceeds MAX_DEPTH |
| `json_number_unsupported` | parse | a float or non-finite number is present |
| `contract_unsupported` | contract | contract_version is not r08-v1 |
| `kind_unsupported` | contract | kind is not the expected document kind |
| `family_unsupported` | contract | family is not f1a-local-execution-allowlist |
| `field_unknown` | shape | an unknown field is present |
| `field_missing` | shape | a required field is absent |
| `field_type_invalid` | shape | a field has the wrong type |
| `field_invalid` | shape | a field violates its value constraints |
| `digest_mismatch` | integrity | a recorded digest does not match the canonical content |
| `evaluator_unsupported` | identity | evaluator id or binding is not the registered F1a evaluator |
| `evaluator_mismatch` | identity | evaluator identity or build differs between selection and record or expectation |
| `record_identity_mismatch` | identity | selection pins a different record id or version |
| `record_digest_mismatch` | identity | selection pins a different record digest |
| `supersession_invalid` | identity | record supersession reference is invalid |
| `selection_missing` | selection | no selection was supplied or none is effective |
| `selection_epoch_stale` | selection | epoch is below the trusted floor for this selection id |
| `lineage_authority_unavailable` | selection | authenticated, attributable supersession lineage requires R09 infrastructure that does not exist; the structural resolver is non-authorizing |
| `selection_conflict` | selection | two effective selections conflict without explicit supersession |
| `selection_supersession_invalid` | selection | supersession reference or decision reference is invalid |
| `participation_mismatch` | selection | selection participation differs from the consumer's operation class |
| `trust_snapshot_missing` | trust | no trust snapshot was supplied |
| `trust_snapshot_invalid` | trust | trust snapshot is malformed |
| `trust_snapshot_expired` | trust | trust snapshot is past valid_until |
| `time_unavailable` | trust | no trusted current time was supplied |
| `verifier_unavailable` | authenticity | no signature verifier is available; digest match is not authentication |
| `signature_missing` | authenticity | the statement carries no signature |
| `signature_algorithm_unsupported` | authenticity | signature algorithm is not supported |
| `issuer_untrusted` | authenticity | no trusted issuer holds the signing key id |
| `issuer_key_revoked` | authenticity | the signing key id is revoked in the trust snapshot |
| `signature_invalid` | authenticity | signature does not verify |
| `issuer_not_authorized` | authority | issuer holds no authority for this exact consumer, scope and operation |
| `selection_consumer_mismatch` | scope | selection names a different consumer |
| `selection_scope_mismatch` | scope | tenant, institution or authority domain differs |
| `selection_operation_mismatch` | scope | selection names a different operation |
| `selection_not_yet_effective` | time | now is before valid_from |
| `selection_expired` | time | now is at or after valid_until |
| `selection_revoked` | revocation | selection id and epoch are revoked in the trust snapshot |
| `composition_family_unsupported` | composition | family is not composable |
| `composition_operator_unsupported` | composition | operator is not intersection |
| `composition_caller_invalid` | composition | caller policy fields are malformed |
| `composition_record_invalid` | composition | record is not a valid F1a record |

## Qualification status (what is and is not claimed)

- Developer tests: per-module suites plus `tests/test_r08_spec_conformance.py`, a blind builder-authored oracle preparation ([qualification-spec.md](r08-s01/qualification-spec.md)). **None of this is independent qualification.** The independent Tier 1 qualification lead has not been designated; nothing here is self-certified.
- The verifier is tested only with a deterministic test double (`tests/r08_support.py` `FakeVerifier`), which is not cryptography. No Ed25519 behavior is demonstrated by this sprint.
- **UNQUALIFIED:** the F1 authority-to-effect guarantee; authentication of any real issuer; trust-root custody; activation; Runtime or Control Plane integration; the full MSOP. See [r10-feasibility](r10-feasibility/r10-effect-boundary-feasibility.md) for the read-only feasibility recommendation, which implements nothing.

## Open items for Architect or operator

Asymmetry in malformed-`supersedes` codes between records and selections (contract section 3a); perpetual selections (A-05); trust-root custody and issuer enrollment (B-02); dependency decision B-10; LD-02 outcome mapping; the R10 option choice; independent qualifier designation (F-01); successor-contract adoption beyond this foundation (A-01 implementation).
