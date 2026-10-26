# S01 test inventory and predeclared outcomes (frozen before implementation)

Status: committed before any source change (S01, plan v1.4 Amendment 1). BUILDER_TESTED when green; **not** independently qualified; **not** an independent cryptographic assessment. Executable form: `tests/test_s01_withdrawal_floor_signing.py` (+ `tests/s01_support.py`). Predeclared API: `registry_successor.v2_selection.parse_selection_envelope_v2`, `signing_input_v2`, `SIGNING_DOMAIN_V2`; `verify.verify_selection_v2(..., *, min_trust_snapshot_version=None, last_accepted_snapshot=None)`; `verify.LAYERS_V2`.

Expected outcome on pre-S01 main: the module cannot import (`v2_selection` absent), so every case fails. Recorded in the PR.

| ID | Case | Expected |
|---|---|---|
| SD-01 | Valid v2 statement signed under the v2 domain | ok, authenticated, `disposition` layer pass |
| SD-02 | v2 statement signed under the v1 domain | `signature_invalid`, not authenticated |
| SD-03 | v1 statement signed under the v2 domain, v1 entry | `signature_invalid` |
| SD-04 | v1 signing and verification unchanged | `SIGNING_DOMAIN` and `signing_input` unchanged; v1 report layers unchanged (no `disposition`) |
| SD-05 | `signing_input_v2` | v2 prefix + canonical bytes; differs from v1; prefixes not prefix-related |
| SD-06 | v1 envelope at v2 entry; v2 envelope at v1 entry | `contract_unsupported` both ways |
| SD-07 | v2 entry, statement without `disposition` | `field_invalid` |
| SD-08 | Real Ed25519 (PyNaCl, adapter, mandatory admission) | v2-domain ok; v1-domain `signature_invalid`; bit-flip `signature_invalid`; v1 entry still ok with a v1-domain signature |
| WD-01 | Valid withdrawal naming the select | not ok, `selection_withdrawn`, authenticated, layers: ten pass, `record_binding` not_evaluated, `disposition` refuse |
| WD-02 | Withdrawal through `verify_and_decide_v2` | required: `required_policy_unavailable`, no policy; optional: `overlay_not_applied`, caller unchanged; code `selection_withdrawn`; never applied |
| WD-03 | Valid select through `verify_and_decide_v2` | `applied`, intersection |
| WD-04 | Unsigned, unknown key id, forged withdrawal | `signature_missing`, `issuer_untrusted`, `signature_invalid`; never `selection_withdrawn`; `disposition` not_evaluated |
| WD-05 | Withdrawal expired / not yet effective / revoked / epoch below floor / key revoked / cross-scope | own codes, never `selection_withdrawn` |
| WD-06 | Withdraw with record pin, evaluator pin, no supersedes, equal epoch | `selection_supersession_invalid`; epoch 0 `field_invalid`; unknown disposition `field_invalid`; non-string disposition `field_type_invalid` |
| WD-07 | Withdraw naming another selection id / epoch lower than the named one | `selection_supersession_invalid` |
| WD-08 | Select/first-selection shape; missing disposition; unknown member; unknown family; v2 family table | ok; `field_missing`; `field_unknown`; `family_unsupported`; v2 family accepted |
| WD-09 | v2 parser: v1 document, digest tampering; v1 parser given v2 document; garbage input | `contract_unsupported`; `digest_mismatch`; `contract_unsupported`; refused, never raises |
| WA-01 | Withdraw-after-activation ordering (consumer state) | Reuses EXT-S1-8 reference vectors RV-02/03/05 (reference model, not the Runtime). The Registry verifier is stateless: activation state is S04 |
| SF-01 | Floor inputs default off; v1 entry has no floor parameter | unchanged results |
| SF-02 | External floor | equal/above ok; below `trust_snapshot_version_stale` |
| SF-03 | Invalid floor (0, negative, bool, str, float, huge, list) | `trust_snapshot_invalid` |
| SF-04 | `last_accepted_snapshot` | idempotent same fingerprint ok; newer ok; equal version different fingerprint stale; older stale |
| SF-05 | Malformed `last_accepted_snapshot` | `trust_snapshot_invalid` |
| SF-06 | Expired and below floor | `trust_snapshot_expired` (expiry first) |
| SF-07 | Older snapshot hiding a revocation | stateless alone accepts; with floor or last-accepted: `trust_snapshot_version_stale`; the newer snapshot gives `selection_revoked` |
| SF-08 | Floor failure | not authenticated, authenticity not_evaluated; decide exposes no floor input in S01 (documented limitation) |
| AV-01..AV-10 | Forged/altered (re-digested, digest kept); exact expiry boundaries (microsecond); wrong/unknown/revoked/small-order key; cross consumer/tenant/institution/domain/operation; epoch floor, revoked pair; participation missing/unsupported/invalid and operation mismatch; unselected record pin; unknown family/contract; v1/v2 cross replay both directions; closed vocabulary (48/46 codes, `LAYERS_V2`) | per the test bodies; codes are the existing vocabulary |

Existing suites that must stay green after S01 (the baseline on `ea7fe24e` is 6,012 passed, 2 skipped): the full `tests/` run. Existing v2-entry tests that built v1-shaped inputs and v1-domain signatures encode the signing-domain defect and are updated mechanically through shared helpers (reported in the PR); no v1 golden/replay test and no r08-v1 signing or verification expectation is changed. Correction recorded after implementation: a few v1-entry tests that deliberately fed an envelope DECLARING `r08-v2` to the v1 entry (to prove admission becomes mandatory) now expect `contract_unsupported` instead of `trust_snapshot_invalid`, because S01 refuses a cross-version envelope earlier; their other assertions are unchanged.

Explicitly unsupported in S01 (reported honestly): durable activation/withdrawal state, high-water and ratchet (S04); a floor input on `verify_and_decide_v2` (not requested); v2 record validation for `f1ab` (not requested); independent cryptographic assessment (none).


## S01 results and review (appended after implementation; the table above was frozen first)

Pre-implementation evidence: commit `5efacba` (oracle and this inventory) failed at collection on `ea7fe24e` (no `registry_successor.v2_selection`).

Existing-test changes (all reported in the PR): signing/admission/base64/adapter/mutation tests that exercise the **r08-v2 entry** now build v2-shaped statements (`disposition`) signed under the v2 domain via `r08_support.make_statement_v2/make_envelope_v2/parse_v2`; the v1-entry variants keep the v1 helpers. Source-text guard tests that pinned the pre-S01 state were amended narrowly and each says why: the `verify.py` SHA pin, "v2-only codes have no behaviour" (now: only `verify.py` and `v2_codes.py`), the V1-module code-mention guard (`verify.py` moved to an AST site check: `trust_snapshot_version_stale` only in `_floor_outcome`, `selection_withdrawn` only in `_verify`), the MAX_INT-user and touched-module allow-lists (`v2_selection.py`). Mutation probes use a probe-only double that maps the v2 domain to v1 (domain separation itself is tested in the S01 oracle) and gained four killable mutants (v2 mode off, policy dropped, gate dropped, v2 domain dropped).

Fresh-context technical review (one pass, read-only): no way found to obtain `ok=True` for a withdrawal or a cross-version statement at the v2 entry, and no floor bypass. Applied: the exception fallback of `verify_selection` returns `LAYERS_V2` for the v2 label; the oracle's tautological WD-05 assertion was replaced by explicit per-case assertions; SF-04 now covers every snapshot member; WD-04 gained the v1-domain case.

Remaining limitations (not fixed, for the Architect):
1. **v1 entry, hand-built selection object.** A caller that builds a selection object by hand (no `envelope`) with a `disposition` key and a v1-domain signature gets `ok=True` at `verify_selection`; the parser path (`parse_selection_envelope`, used by `verify_and_decide`) rejects the extra field. Behaviour is unchanged from before S01. Refusing a `disposition` key at the v1 entry would change the r08-v1 refusal set, so it was not done without a ruling.
2. `verify_and_decide_v2` has no floor inputs (the floor is enforced at `verify_selection_v2`).
3. The floor refusal sits in the `trust_snapshot` layer, so an unsigned statement against a stale snapshot reports `trust_snapshot_version_stale` (layer order), not `signature_missing`.
4. Withdraw-after-activation ordering and durable state remain S04; only the EXT-S1-8 reference vectors are reused.
