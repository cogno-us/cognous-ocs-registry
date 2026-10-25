# R08-S01 candidate qualification specification (frozen candidate; builder-authored preparation)

Status: **candidate specification, not independent qualification.** Written by the builder, blind to the implementation, from `docs/r08-s01-contract.md`, `registry_successor/common.py` (closed `CODES`) and `tests/r08_support.py` only. The independent Tier 1 qualification lead is **not designated** (operator, R08-S01 authorization). Nothing here is `[QUALIFIED]`; the executable form, `tests/test_r08_spec_conformance.py`, is DEVELOPER-TESTED-class evidence at best and carries no independence.

Governing: plan v1.2 (blob `32319775c6e2d9c3fff1e2171c8f4c9d096911d6`), crosswalk, Constitution pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (formal adoption not asserted), merged R08-PREP (`1324bab15da20a32fb82f54c444d1e808543b0e6`, esp. `docs/r08-preparation/06-qualification-contract.md`). Form follows `cognous-stack-qualification` (`docs/refusal-test-template.md`: negative leg, typed refusal, positive control, mutation, provenance; `docs/release-gate/pre-registration.md`: expectations fixed before runs). That repository is not modified and is not itself an independence authority.

## 1. Candidate under test and pins

| Item | Value |
|---|---|
| Contract | `r08-v1` (`docs/r08-s01-contract.md`); package `registry_successor/` |
| Candidate source | exact PR head SHA, recorded at the qualification boundary (not known when this spec was written) |
| Frozen, must be unchanged | `registry_contract/validator.py` `afee88b37197ca4aa3842b228fbc348f585b937a`; `registry_consumer/consumer.py` `bf382d00cb275fa056d60713bf8fc119e9bee7da`; `baseline/execution-runtime/engine/safe_executor.py` `2fc880dae37eac76e5074533435740ce0684209d` |
| Closed code set | `registry_successor/common.py` `CODES` at the candidate head |
| Verifier | none supplied; tests use a labelled test double (`tests/r08_support.py` `FakeVerifier`), which is not cryptography |
| Environment | CPython 3.13.17, hash-locked venv; no network, paid, or credentialed calls |

## 2. What is and is not claimed

DEVELOPER-TESTED means the builder's own tests pass. INDEPENDENTLY QUALIFIED means a designated lead, who is not the author, owned the expected outcomes, froze them before execution, supervised the run and issued a bounded verdict. **Not claimed:** independent qualification; operational authorization of any selection (`operationally_authorized` is always `False`); any cryptographic authenticity claim (no real verifier is supplied); effect-time or commit-boundary behavior (R10, UNQUALIFIED); any family beyond F1a; production or runtime behavior.

## 3. Independence steps the qualifier must perform (not performed)

1. Designation of the lead by the operator; record independence from the authors and from Copilot.
2. Re-derive or independently re-approve every expectation below; builder expectations stay DEVELOPER-TESTED until then.
3. Freeze expectations, candidate SHA and this spec's digest **before** executing the candidate; amendments are dated, recorded, never made to obtain a pass.
4. Execute or supervise; retain raw adverse outputs; preserve negative findings.
5. Run the mutation leg (disable a refusal check; the case must then fail) for each refusal family.
6. Report limitations and a bounded verdict that transfers only to the exact candidate and profile.
7. A mismatch against a resolved expectation is FAIL; unresolved mapping is BLOCKED; never edited to fit.

## 4. Case catalogue

Layer names are those of the contract (parse, contract, shape, integrity, identity, selection, trust, authenticity, authority, scope, time, revocation, composition, participation). "Test" names the function in `tests/test_r08_spec_conformance.py`. Expected codes come from the contract text only.

### 4.1 Records (validate_record_text)
| ID | Recipe | Expected | Layer |
|---|---|---|---|
| QR01 | valid F1a record | ok, `record_digest` as built | - |
| QR02a-d | empty list in one dimension / all three | ok (explicit deny-all, valid) | shape |
| QR03 | payload field absent | `field_missing` (absent is neither allow nor deny) | shape |
| QR04, QR05 | unknown payload / top-level field | `field_unknown` | shape |
| QR06 | `status` field present | `field_unknown` (no status; event-derived) | shape |
| QR07 | `contract_version` `s03-v1` | `contract_unsupported` | contract |
| QR08, QR09 | wrong `kind` / `family` | `kind_unsupported` / `family_unsupported` | contract |
| QR10-QR17 | unsorted; duplicate; `*`; 257 entries; 129 chars; control char; space; empty entry | `field_invalid` | shape |
| QR18 | list field is a string | `field_type_invalid` | shape |
| QR19 | `non_authorizing` false | `field_invalid` | shape |
| QR20, QR21 | evaluator id / binding wrong | `evaluator_unsupported` | identity |
| QR22, QR23 | version 0; version `true` | `field_invalid`; `field_type_invalid` or `field_invalid` | shape |
| QR24, QR25 | supersedes higher version; other id | `supersession_invalid` | identity |
| QR26 | `authored_at` not strict timestamp | `field_invalid` | shape |
| QR27 | payload or record digest altered | `digest_mismatch` | integrity |
| QR28 | forged payload re-sealed with valid digests | ok: **integrity is not authentication** | integrity |
| QR29 | duplicate key; >65536 bytes; malformed; bytes input; float; depth 9; lone surrogate | `json_duplicate_key`; `input_too_large`; `json_malformed`; `input_not_text`; `json_number_unsupported`; `json_nesting_too_deep`; `input_not_text` | parse |
| QR30 | byte corruption in valid text; truncation | `digest_mismatch`; `json_malformed` | integrity, parse |

### 4.2 Selection structure (parse_selection_envelope, then verify where noted)
| ID | Recipe | Expected |
|---|---|---|
| QS01 | valid envelope | ok; `statement_digest` matches |
| QS02, QS03 | unknown / missing statement field | `field_unknown` / `field_missing` |
| QS04-QS06 | epoch 0; epoch `true`; participation `maybe` | `field_invalid`; `field_type_invalid` or `field_invalid`; `field_invalid` |
| QS07-QS11 | inverted, equal, null-ended (perpetual), missing, malformed interval | `field_invalid`; `field_invalid`; `field_type_invalid` or `field_invalid`; `field_missing`; `field_invalid` |
| QS12 | wildcard in scope | `field_invalid` |
| QS13 | supersedes without `decision_ref` | **ORIGINAL (frozen blind) expectation: `field_missing`.** Candidate returned `selection_supersession_invalid`; the developer-side expectation was later changed to that. See section 5a (provenance); not independently adjudicated |
| QS14, QS15 | supersedes epoch not lower; other selection id | `selection_supersession_invalid` or `field_invalid` |
| QS16-QS19 | wrong family; envelope contract/kind/unknown field | `family_unsupported`; `contract_unsupported`; `kind_unsupported`; `field_unknown` |
| QS20 | `statement_digest` altered (parse or verify) | `digest_mismatch` |
| QS21 | duplicate key; oversized; non-text; truncated; float | `json_duplicate_key`; `input_too_large`; `input_not_text`; `json_malformed`; `json_number_unsupported` |

### 4.3 Verification (verify_selection); all other layers valid
| ID | Recipe | Expected |
|---|---|---|
| QV01 | fully valid | `ok`, `authenticated`, every layer `pass`, `operationally_authorized` False |
| QV02 | no verifier; no signature | `verifier_unavailable`; `signature_missing`; never `authenticated` (digest match is not authentication) |
| QV03 | no trust snapshot; no time; snapshot past `valid_until` | `trust_snapshot_missing`; `time_unavailable`; `trust_snapshot_expired` |
| QV04 | no issuers; unknown key id; revoked key | `issuer_untrusted`; `issuer_untrusted`; `issuer_key_revoked` |
| QV05 | signature over other message; non-base64; algorithm `rsa` | `signature_invalid`; `signature_invalid` or `field_invalid`; `signature_algorithm_unsupported` or `field_invalid` |
| QV06 | grant differs in consumer, tenant, institution, domain or operation; no grants | `issuer_not_authorized` |
| QV07a-e | context consumer / tenant / institution / authority domain / operation differs | `selection_consumer_mismatch`; `selection_scope_mismatch` x3; `selection_operation_mismatch` |
| QV08a-e | now = from-1s; from; until-1s; until; until+1s | `selection_not_yet_effective`; pass; pass; `selection_expired`; `selection_expired` (until is exclusive, from is inclusive) |
| QV09 | epoch floor above / equal to epoch | `selection_epoch_stale`; pass |
| QV10 | revoked (id, epoch); other epoch revoked | `selection_revoked`; pass |
| QV11 | record other version / other id; same id and version other payload; evaluator build differs | `record_identity_mismatch`; `record_identity_mismatch`; `record_digest_mismatch`; `evaluator_mismatch` |
| QV12 | verify a failed parse | not ok; never authorized |

### 4.4 Effective selection (resolve_effective)
| ID | Recipe | Expected |
|---|---|---|
| QC01 | no selections; only another tenant's | `selection_missing` |
| QC02 | two selection ids effective together | `selection_conflict` |
| QC03 | epoch 1 and epoch 2, no supersedes (higher epoch is not authority) | `selection_conflict` |
| QC04 | epoch 2 names epoch 1 exactly with `decision_ref` | ok; epoch 2 selected |
| QC05 | supersedes names a wrong digest | `selection_supersession_invalid` or `selection_conflict` |
| QC06 | one expired, one effective | ok; the effective one |

### 4.5 Composition and deny-all (compose_f1a)
| ID | Recipe | Expected |
|---|---|---|
| QD01 | caller and record overlap | effective = intersection, `deny_all` False |
| QD02 | empty intersection in each dimension | ok, `deny_all` True, field listed |
| QD03 | registry list empty | ok, `deny_all` True, `deny_all_fields == ("allowed_units",)` |
| QD04 | all 64 subset pairs for one field | intersection exactly; never wider than caller or registry |
| QD05 | operator `union`, `latest`, empty, `newest`; non-F1a family | `composition_operator_unsupported`; `composition_family_unsupported` or `composition_record_invalid` |
| QD06 | invalid record; caller missing / extra / string / non-string entries / None | `composition_record_invalid`; `composition_caller_invalid` |

### 4.6 Per-operation outcomes (originally `decide_policy`; now `verify_and_decide`, see 5b)
| ID | Recipe | Expected |
|---|---|---|
| QP01 | verified, valid; verified with empty dimension | `applied`; `applied_deny_all` |
| QP02a-f | required; no selection / untrusted / revoked / expired / no trust root / no verifier | `required_policy_unavailable`, code from `CODES`, **effective never the caller policy** |
| QP03a-f | same six, optional | `overlay_not_applied`, caller returned unchanged, **not denial** (`deny_all` not set) |
| QP04 | missing selection both classes; invalid record | `selection_missing`; the record's code or `composition_record_invalid` |
| QP05 | malformed caller in required / optional | `required_policy_unavailable` + `composition_caller_invalid`; `overlay_not_applied` |
| QP06 | every refusal code returned | member of `CODES` (closed taxonomy) |

## 5. Known ambiguities in the contract text (cases tolerate the named alternatives; each needs an Architect/lead ruling)

1. Which of parse or verify raises integrity and structure codes for selections (QS20): the pipeline accepts either location.
2. Codes for wrong-typed integers (`true`), perpetual (`null`) intervals, non-lower supersession, unsupported algorithm: `field_type_invalid` vs `field_invalid`, `selection_supersession_invalid` vs `field_invalid`, `signature_algorithm_unsupported` vs `field_invalid`.
3. Wrong-digest supersession: `selection_supersession_invalid` vs `selection_conflict` (QC05).
4. Non-F1a family reaching composition and an invalid record in the decision entrypoint: family vs record code (QD05, QP04).
5. Concrete types of `TrustSnapshot` members (`revoked_*` as `frozenset`, `min_epochs` as a mapping, `valid_until` as a timestamp string) are not pinned by the contract; the tests assume those.
6. Where `participation_mismatch` is raised is not specified (no participation field in `ExpectedContext` or the report); **no case is written for it**, which is a coverage gap, not a pass.
7. Inclusive/exclusive interval ends are inferred from the wording ("before valid_from", "at or after valid_until").
8. Whether an empty *caller* list composes to deny-all (QD02) is inferred from "empty intersection is valid deny-all".

9. Order of shape/value checks versus digest checks is not specified. QR30's recipe therefore keeps the corrupted list sorted so only the digest layer can fail; a corruption that breaks sort order is `field_invalid` under any shape-first ordering.
10. A supersession object lacking `decision_ref` (QS13): contract section 3 (exact nested fields) suggested `field_missing`; the `CODES` meaning of `selection_supersession_invalid` also fits. The blind run recorded the failure (candidate returned `selection_supersession_invalid`). **Disclosed amendment:** the lead builder then clarified the contract (section 3a: any malformed selection `supersedes` refuses `selection_supersession_invalid`) and changed the QS13 expectation to match. This amendment came after seeing the candidate's behavior, so it is a developer-side resolution, not independent evidence; the Architect should rule on the asymmetry with records (section 3a) and an independent qualifier must freeze its own expectation.

## 5a. QS13 provenance record (A4; historical, not to be rewritten)

| Step | Fact |
|---|---|
| 1. Original expectation | Written blind to the implementation from contract section 3 (exact nested fields): a supersession object without `decision_ref` is `field_missing`. |
| 2. Actual candidate result | `selection_supersession_invalid` (recorded failure `QS13-supersedes-no-decision-ref`, the only conformance failure of the blind run). |
| 3. Contract clarification | After seeing that result, the lead builder added contract section 3a (any malformed selection `supersedes` refuses `selection_supersession_invalid`). |
| 4. Expectation amendment | The executable expectation in `tests/test_r08_spec_conformance.py` was changed to `selection_supersession_invalid`. |
| 5. Status | The amendment was made **after candidate behavior was observed**. It is developer evidence only. It is not independent qualification, and it must not be cited as an independent pass. |
| 6. Required follow-up | The future independent Tier 1 qualifier (not yet designated, F-01) must separately adjudicate and freeze the normative QS13 expectation (including the selection/record asymmetry in contract section 3a) **before** executing the candidate. The discrepancy above is retained, not suppressed. |

Amendment A4 (PR #19 Architect disposition) changed only this documentation; no expectation was altered further.

## 5b. Interface change after this spec was written (A1, A2)

This spec's section 4.6 named `decide_policy(...)`. The public report-taking interface was removed; the public entrypoint is now `verify_and_decide(participation, caller, record_text, selection_text, context, trust, verifier, now)`. Cases QP01-QP06 are executed through it in the developer suite. Lineage resolution is structural and non-authorizing (`resolve_effective`), and `resolve_authoritative` always refuses `lineage_authority_unavailable`. A qualifier must write expectations for these interfaces independently; the builder-authored QP rows are not normative.

## 6. Coverage gaps (explicit)

Not covered: participation mismatch (5.6); real Ed25519 verification (no verifier supplied); expiry and revocation at the commit boundary and the F1 check-to-commit gap (R10, UNQUALIFIED); loaded-code integrity; concurrency; key rotation, anti-rollback beyond the supplied epoch floor; fuzzing beyond the listed boundaries; mutation testing (step 3.5 is the qualifier's).
