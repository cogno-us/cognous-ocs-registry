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

Existing suites that must stay green after S01 (the baseline on `ea7fe24e` is 6,012 passed, 2 skipped): the full `tests/` run. Existing v2-entry tests that built v1-shaped inputs and v1-domain signatures encode the signing-domain defect and are updated mechanically through shared helpers (reported in the PR); no v1-entry test is changed.

Explicitly unsupported in S01 (reported honestly): durable activation/withdrawal state, high-water and ratchet (S04); a floor input on `verify_and_decide_v2` (not requested); v2 record validation for `f1ab` (not requested); independent cryptographic assessment (none).
