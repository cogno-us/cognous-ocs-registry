# R08-S01 successor contract `r08-v1` (interface specification, written before the modules)

Authorization: operator R08-S01 (bounded foundation; F1a adopted as TARGET scope, not operational acceptance). Governing: plan v1.2 blob `32319775c6e2d9c3fff1e2171c8f4c9d096911d6`, crosswalk, Constitution pin `1c2e920f4e58e07a52e8e2408a506cf7dbc1292b` (formal adoption not asserted), merged R07 inventory, merged R08-PREP (`1324bab15da20a32fb82f54c444d1e808543b0e6`, `docs/r08-preparation/`). Frozen and unchanged: `registry_contract/` (s03-v1), `registry_consumer/` (s04-v1), `registry_records/`, `baseline/`.

Status: developer-tested foundation only. Not a working registry. No activation, no approved pin, no operational trust root, no runtime wiring, no independent qualification.

## 1. Modules (new package `registry_successor/`; one owner per file)

| Module | Owns | Public API |
|---|---|---|
| `common.py` | strict JSON, canonical bytes, digests, validators, closed `CODES` | `load_document`, `canonical_bytes`, `digest`, `CODES`, validators |
| `record.py` | F1a record validation | `validate_record_text(text) -> RecordResult`; `RecordResult(ok, code, detail, record, record_digest)` |
| `selection.py` | selection envelope structure, signing input, effective-selection resolution | `parse_selection_envelope(text) -> SelectionResult(ok, code, detail, envelope, statement, statement_digest, signatures)`; `signing_input(statement) -> bytes`; `resolve_effective(selections, context, now) -> ConflictResult(ok, code, detail, selected)` where `selected` is the winning `SelectionResult` |
| `verify.py` | layered technical verification against explicit trusted inputs | `verify_selection(selection, context, trust, verifier, now, record=None) -> VerificationReport` |
| `compose.py` | F1a typed composition | `compose_f1a(caller, record, operator="intersection") -> CompositionResult` |
| `decision.py` | per-operation outcome (required vs optional) | `decide_policy(participation, caller, record, report) -> PolicyDecision` |

Rules: no module imports the Runtime, `registry_contract` or `registry_consumer`; no I/O, clocks, network, randomness or global state (time is injected); every refusal uses a code from `common.CODES`; modules never raise on bad input (a defensive broad `except` returns the refusal, never an acceptance).

## 2. Record format (`kind: "record"`, exact fields, no others)

`contract_version` = `r08-v1`; `kind` = `record`; `family` = `f1a-local-execution-allowlist`; `record_id` (`[a-z0-9][a-z0-9._-]{2,63}`); `record_version` (int 1..2^31-1); `non_authorizing` = `true`; `supersedes` = null or `{record_id, record_version, record_digest}` (version strictly lower than own, same id); `evaluator` = `{evaluator_id, binding, source_blob_id (40 hex), source_sha256 (sha256:hex)}` with id and binding equal to `common.EVALUATOR_ID` / `EVALUATOR_BINDING`; `source` = `{repository, commit (40 hex), path, blob_id (40 hex), sha256}`; `payload` = exactly `allowed_actions`, `allowed_adapters`, `allowed_units`; `payload_digest` = digest of canonical payload; `provenance` = `{decision_ref, authored_at (strict timestamp), authored_by}`; `record_digest` = digest of the record without `record_digest`.

There is **no `status`** field: lifecycle state is event-derived and outside the record (Architect ruling on A-01/A-02). A record states no activity.

Payload lists: sorted, duplicate-free, at most 256 entries, each 1..128 characters with no control or separator characters and no `*`. **An empty list is valid and means deny all values for that dimension** (explicit deny-all; frozen S03's non-empty rule is unchanged because s03-v1 is untouched). **A missing payload field refuses (`field_missing`)**: for F1a an absent field is neither an implicit allow nor an implicit deny. Unknown field: `field_unknown`.

## 3. Selection envelope (`kind: "selection-envelope"`)

`{contract_version, kind, statement, statement_digest, signatures}`. `statement_digest` = digest of canonical `statement`. `signatures` = list (possibly empty) of `{alg, key_id, signature}` (`alg` = `ed25519`, `signature` standard base64 text; the verifier receives the decoded bytes, and undecodable text is `signature_invalid`). Signing input = `b"ocs-reg/r08-v1/selection\n" + canonical_bytes(statement)`.

`statement` (exact fields): `kind`=`selection`; `selection_id` (identifier); `epoch` (int >= 1); `consumer_id` (identifier); `scope` = `{tenant, institution, authority_domain}` (tokens); `operation` (identifier); `participation` (`required`|`optional`); `family`; `record` = `{record_id, record_version, record_digest}`; `evaluator` (as in records); `effective` = `{valid_from, valid_until}` (strict timestamps, `valid_from < valid_until`; perpetual selections are not representable, pending A-05); `supersedes` = null or `{selection_id, epoch, statement_digest, decision_ref}` (same selection id, lower epoch, `decision_ref` an identifier naming the attributable approved decision); `revocation_ref` (identifier); `selector_ref` (identifier, the selector authority reference); `issued_at` (timestamp).

An epoch is not authorization. A higher epoch never supersedes by itself: supersession needs the newer statement to name the older one exactly (id, epoch, digest) with a `decision_ref`. Two effective selections for the same (consumer_id, scope, operation, family) without such a chain refuse with `selection_conflict`.

### 3a. Clarification recorded after the blind specification run (builder resolution, pending Architect ruling)

A selection `supersedes` object that is malformed in any way (missing or unknown member, wrong type, different selection id, epoch not lower, bad digest, missing or invalid `decision_ref`) refuses with `selection_supersession_invalid`, because that code's meaning covers "supersession reference or decision reference is invalid". For records, a `supersedes` object with a bad shape returns the shape code (`field_unknown`, `field_missing`, `field_type_invalid`) and a well-shaped but rule-violating one returns `supersession_invalid`. The asymmetry is deliberate and is flagged for Architect ruling; the blind qualification spec expected `field_missing` for the missing-`decision_ref` case and was amended to this clarification (disclosed in `docs/r08-s01/qualification-spec.md`, ambiguity 10).

## 4. Verification (`verify.py`)

Explicit trusted inputs only; nothing is hardcoded or discovered. `ExpectedContext(consumer_id, tenant, institution, authority_domain, operation)` is defined in `common.py` (re-exported by `verify.py`). `TrustSnapshot(snapshot_id, version, valid_until, issuers, revoked_key_ids, revoked_selections, min_epochs)`; `IssuerEntry(key_id, issuer_id, alg, public_key, authority)`; `AuthorityGrant(consumer_id, tenant, institution, authority_domain, operation)` exact-match, no wildcards. `SignatureVerifier.verify(alg, public_key, message, signature) -> bool`; **no verifier is supplied by this package**: with none, the authenticity layer refuses `verifier_unavailable`. A SHA-256 match is integrity only and never sets `authenticated`.

`VerificationReport(ok, code, detail, layers, selection_digest, authenticated, issuer_id, operationally_authorized)`; `layers` maps each of `structural`, `integrity`, `record_binding`, `trust_snapshot`, `authenticity`, `authority`, `scope`, `time`, `revocation`, `epoch` to `pass`, `refuse` or `not_evaluated`. `ok` means technically verified only; **`operationally_authorized` is always `False`**. `code` is the first failing layer in the order listed.

## 5. Composition and outcomes

`compose_f1a(caller, record)`: for each F1a field `effective = caller INTERSECTION registry`, returned as sorted tuples. An empty intersection is a valid deny-all (`deny_all` true when any dimension is empty; `deny_all_fields` lists them). Unknown family, operator other than intersection, malformed caller fields or an invalid record refuse. No widening is representable. Mandatory Runtime invariants are code-owned and are not touched (`LocalExecutionPolicy` is not constructed here; consumers must not build one from empty sets).

`decide_policy(participation, caller, record, report)` kinds: `applied`; `applied_deny_all`; `overlay_not_applied` (optional only: caller policy returned unchanged, explicitly not denial); `required_policy_unavailable` (required only: **never** the caller policy; conceptually HOLD, mapping to component classes is open decision LD-02). Missing selection (`report` is None), invalid selection, invalid record, unsupported family and composition refusals carry their closed code. A selection whose participation differs from the operation class refuses `participation_mismatch`.

## 6. Closed refusal taxonomy

The authoritative list is `common.CODES` (code to layer and meaning); `docs/r08-s01-implementation.md` reproduces it and a test keeps the two equal.
