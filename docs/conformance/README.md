# OCS consumer activation / high-water conformance kit (EXT-S1-8)

Status: **IMPLEMENTED / DEVELOPER-TESTED**, aligned to the Architect rulings R1 to R4 of 2026-10-25 (verdict semantics, revocation scope, selection versus activation, lost state fails closed). Builder-authored. Not independently qualified, not an oracle, not a verdict. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

This is a **conformance kit, not an activation store.** The Registry holds no activation state, no high-water, no revoked set and no ratchet (ADR-REG-TR01; `docs/r08-v2-contract.md` section 7). The enforcing component (Runtime, Control Plane) owns the real store. The kit defines the pure transition and derivation rules and a corpus of vectors so each owner can check its own implementation.

Contents (all new):

| Path | Purpose |
|---|---|
| `registry_conformance/highwater.py` | pure `advance(state, observation) -> (new_state, verdict)`, pure derived `policy_state(...)`, `empty_state()`, `verify_state()` |
| `registry_conformance/__init__.py` | strict vector validator (`validate_vector_set`, `MalformedVector`) and pure vector runner (`run_vector`, `run_vector_set`) |
| `registry_conformance/vectors/*.json` | 103 language-neutral vectors in 11 files, all `SYNTHETIC-TEST-ONLY` |
| `docs/conformance/recovery-event-proposal.md` | **NOT IMPLEMENTED / NOT AUTHORIZED** proposal for a separate recovery event (documentation only) |
| `tests/test_conformance_kit.py` | developer tests, malformed-vector refusals, in-suite mutation checks, randomized monotonicity invariants |

## Boundaries (what the kit never does)

- No I/O, no persistence, no network, no clock read (time is the integer `now` in every observation), standard library only, no import of any registry module. The core does not import the kit (a test enforces both directions).
- It never mints authorization: a verdict `ACCEPT` means only that the supplied transition or comparison is consistent with the supplied state. Verdicts carry no authorization member (the runner fails any verdict with an unexpected key).
- It never reverses a revocation, never clears the `scope_required` ratchet, never lowers a high-water, floor or snapshot version. The vector runner asserts these monotonic invariants after **every** step of **every** vector, plus: log and evidence are append-only; each rejected transition appends exactly one negative-evidence record (`ocs-registry-failure-detail/1`) and an accept appends none; `guard` never changes state.
- It does not verify signatures. A `select` or `withdraw` observation carries `verified: true/false` as the caller's assertion that the ten registry layers passed; `false` is refused `statement_not_verified`.

## Verdicts (ruling R1)

Four verdicts with distinct semantics. Every vector step states one of them; vectors `VD-01` to `VD-06` (`11_verdict_semantics.json`) prove each, and the runner fails any step that breaks the rules below.

| Verdict | Meaning | Typical codes | Vectors |
|---|---|---|---|
| `ACCEPT` | The transition or comparison is valid under authenticated authority and the applicable monotonic state. It is **not** an authorization and carries no authorization member. | `activated`, `withdrawn`, `synced`, `guard_pass`, `restore_consistent`, `overlay_not_applied` (optional fallback, `applied=false`) | VD-01 |
| `REFUSE` | Definitive invalidity or authority violation: unverified, outside the validity window, withdrawn, revoked (selection, key, issuer or record scope), conflicting, malformed, or an operation that is defined but not authorized (`relax_scope_required`, `rebaseline`). Authenticated, current withdrawal is `REFUSE` (`selection_withdrawn`). Retrying does not turn it into success. | `statement_not_verified`, `selection_expired`, `selection_withdrawn`, `selection_revoked`, `issuer_key_revoked`, `issuer_revoked`, `record_revoked`, `participation_mismatch`, `relaxation_not_authorized_v1`, `rebaseline_not_authorized_v1` | VD-02, RV-13 to RV-18 |
| `REFUSE_STALE` | Definitive stale, replayed or rolled-back epoch (or snapshot version, floor): the state is known and the input is behind it. | `selection_epoch_stale`, `trust_snapshot_version_stale`, `trust_snapshot_revocation_omitted`, `min_epoch_floor_lowered`, `external_floor_lowered` | VD-03 |
| `UNKNOWN_FAIL_CLOSED` | Authority or durable state is **indeterminate** (store unavailable, lost, rolled back, torn, tampered, absent; snapshot support missing or expired). No effect may proceed. UNKNOWN is never collapsed into authorization: it is never `ACCEPT`, never an optional fallback, and the kit never recovers an unknown store by itself. | `store_unknown`, `state_lost`, `state_malformed`, `state_older_than_anchor`, `anchor_head_mismatch`, `state_log_mismatch`, `log_chain_broken`, `trust_snapshot_missing`, `trust_snapshot_expired` (guard) | VD-04, VD-05, VD-06, RC-17, RC-19 |

Definitive versus indeterminate: the same stale or withdrawn claim is `REFUSE_STALE` or `REFUSE` while the state is known and `UNKNOWN_FAIL_CLOSED` once the state is indeterminate (VD-05). A cause code names one verdict class; the single documented exception is `trust_snapshot_expired` (`REFUSE` for a delivered expired snapshot, `UNKNOWN_FAIL_CLOSED` for an expired current snapshot at the guard, contract 7.4 line 7). A test enforces this.

Runner invariants (checked after every step of every vector): while the store is `unknown` no step is `ACCEPT` and the store stays `unknown`; `rebaseline` is never accepted.

Mapping to the ADR vocabulary (D-21): `REFUSE_STALE` and `REFUSE` are the ADR **REFUSE** (stale epoch, rollback and withdrawal are never a retryable success); `UNKNOWN_FAIL_CLOSED` is the ADR **HOLD** (authority state unavailable or indeterminate, execution prohibited). `code` carries the cause: closed registry codes where one exists (`selection_epoch_stale`, `selection_withdrawn`, `selection_revoked`, `issuer_key_revoked`, `participation_mismatch`, `selection_supersession_invalid`, `selection_conflict`, `selection_expired`, `selection_not_yet_effective`, `trust_snapshot_version_stale`, `trust_snapshot_expired`), otherwise a kit-local code (for example `store_unknown`, `state_older_than_anchor`, `relaxation_not_authorized_v1`, `rebaseline_not_authorized_v1`, `issuer_revoked`, `record_revoked`). Kit-local codes are conformance vocabulary, not additions to `CODES_V2`.

## Revocation scope (ruling R2)

Revocation scope is explicit, and a higher epoch never bypasses any scope:

| Scope | Carried by | Effect | Vectors |
|---|---|---|---|
| Selection identity `(selection_id, epoch)` | `revoked_selections` | the pair is revoked **permanently**; the row at that epoch reads `revoked`; replaying or re-activating the pair is `REFUSE selection_revoked`; a later snapshot may not omit it | RV-04, RV-05, RV-17 |
| Record `(record_id, record_version)` | `revoked_records` (kit extension, see below) | rows using the record become `revoked`; **no** select naming the record is accepted at any epoch, `REFUSE record_revoked`; another version of the record is a different record | RV-13, RV-14, RV-18 |
| Issuer `issuer_id` | `revoked_issuers` (kit extension) | rows become `revoked`; every key of the issuer is covered, so a fresh key does not help, `REFUSE issuer_revoked` for `select` and `withdraw` | RV-15 |
| Key `issuer_key_id` | `revoked_key_ids` | rows signed by the key become `revoked`; select or withdraw under the key is `REFUSE issuer_key_revoked` | RV-06, RV-12, RV-16 |

A fresh authenticated higher-epoch selection naming a revoked row is accepted **only** when none of the record, issuer or key scopes applies to the new selection, i.e. when the prior revocation was specific to the old selection identity (or to a key or issuer the new selection does not use). The revoked identity itself stays revoked (RV-05, RV-17). There is no successor mechanism in the kit that un-revokes an identity.

Kit extension disclosed: the contract snapshot object (section 5, fingerprint profile) lists `revoked_key_ids`, `revoked_selections` and `min_epochs` only. `revoked_records` and `revoked_issuers` are optional snapshot members of the **kit's observation** (absent means empty) and `select` and `withdraw` observations carry `issuer_id`. They are conformance vocabulary for the ruling, not a change to the V1 snapshot fingerprint profile; whether and how the real snapshot carries record or issuer scope is for the Architect to confirm.

## State model (a conformance model, not a physical schema)

`empty_state()` returns a plain JSON-compatible dict: `rows` per scope key (seven-field key of contract section 7), a hash-chained `log` (`entry_type` in `activate`, `withdraw`, `revoke`, `sync`; the vocabulary is not extended), `evidence` (negative evidence stream), `scope_required` ratchet, `floors` (per-scope high-water, revoked pairs, the subset of revoked pairs a snapshot listed explicitly, revoked key ids, revoked records, revoked issuers, snapshot version, `min_epochs`; monotone), `snapshot`, `external` floor, `anchor` (log-head anchor) and `store` (`known` or `unknown`). `activation_ref` is the entry hash of the `activate` entry. State integrity is verified by replaying the log: every row field, the persisted revoked sets, revoked keys, `min_epochs`, snapshot record, ratchet and high-water must agree with the log, and **each** trusted anchor (the state's own and any supplied external one) must match the log prefix; anything else is `UNKNOWN_FAIL_CLOSED`. Physical names belong to EXT-S4-0.

`anchor` stands for the log-head anchor that contract 8.3 requires to be held **outside** the store. In the kit it travels in the state value for convenience; an observation may carry `external_anchor`, which wins when its `log_head` is at least the state's. A host must persist the anchor externally and pass it in.

## Observations

`select`, `withdraw`, `sync` (a verified snapshot), `external_floor` (raise-only), `read`, `guard` (contract 7.4 comparisons on a claim with or without a binding), `restore`, `lose_state`, `rebaseline`, `relax_scope_required`. Unknown keys, wrong types, non-ASCII or out-of-set identifiers, bad digests and unsupported kinds are refused `observation_malformed` with evidence and no state change.

`relax_scope_required` is **defined but not authorized in V1**: it is refused `relaxation_not_authorized_v1` however it is populated, and the refused-by-default vectors (RT-04) document it.

`rebaseline` is **rejected** (ruling R4): it is not in the closed activation event vocabulary (`activate`, `withdraw`, `revoke`, `sync`) and the kit has no `rebaselines` list. It remains only as an input kind that is **always refused** (`REFUSE rebaseline_not_authorized_v1`, store and anchor unchanged), whatever it claims, on a known or unknown store (RC-18; `UNKNOWN_FAIL_CLOSED` when the state value itself is unusable, RC-17).

## Lost state and recovery (ruling R4): fail closed

Lost, absent, rolled-back, torn or tampered durable state makes the store `unknown` (`lose_state`, a restore behind the anchor, a log or row mismatch, a missing state value). From `unknown` every observation is `UNKNOWN_FAIL_CLOSED` (`store_unknown`) and nothing in the kit makes the store known again: not `rebaseline`, not a `restore` of any copy, not a newer snapshot or a higher epoch (RC-02, RC-05, RC-16, RC-17, RC-19, VD-04). `restore` into an unknown store returns the original cause. `restore` from a **known** store (RC-13) is only a consistency check of a copy against the anchor and the merged floors; it never repairs loss and never lowers any floor.

Any recovery requires an independently authenticated and authorized recovery procedure with monotonic state continuity. That procedure is **not** part of the kit and no recovery bypass is implemented. A proposed separate recovery-event contract is documented in `recovery-event-proposal.md`, clearly marked **NOT IMPLEMENTED / NOT AUTHORIZED**. Disclosed limit: a freshly created empty state with no externally held anchor is indistinguishable from first use; the host must supply the external anchor (RC-11, RC-17).

## policy_state (ruling R3: selection and activation stay distinct)

`policy_state(state, scope, now, known_selection=None, epoch=None)` returns `{"policy_state", "required", "display"}` and no boolean authority. Precedence: `unknown`, `revoked`, `withdrawn`, `superseded`, `expired`/`not_yet_valid`, `active`; with no row `not_selected`, or `selected_not_activated` when the reader supplies a known unactivated selection. Validity is `[valid_from, valid_until)`. A required scope (ratchet set or required row) that is not `active` displays `REQUIRED — UNAVAILABLE`, never `DISABLED` and never a success state.

`superseded` is derived **only** from (a) the `min_epochs` floor for the selection id exceeding the row epoch (contract 7.4 line 3, `selection_epoch_stale`), or (b) an **activated** newer selection, queried for an earlier identity with `epoch` (the scope's activated row has a higher epoch). Observing a higher **unactivated** epoch (a known selection, an unverified statement, a statement with a supersession gap) is **not** supersession: it does not change the active row's `policy_state`, does not raise the high-water, writes no log entry and activates nothing (PS-11). The previous kit inferred `superseded` from a known higher unactivated epoch; that inference is removed.

| Concept | Where it lives in the kit |
|---|---|
| authenticated newer selection statement | a `select` observation with `verified: true`; it changes nothing until it passes every activation precondition |
| activated newer selection | the `activate` log entry and the row (PS-12) |
| minimum accepted epoch | `floors.min_epochs`, raised only by a verified snapshot (anti-rollback knowledge, PS-13); never activates anything |
| revoked selection | `floors.revoked` and row state `revoked` |
| withdrawn selection | an authenticated `withdraw` entry and row state `withdrawn` |

## Vector format and how to hand it over

Each file is `{schema: "ocs-conformance-vectors/1", label: "SYNTHETIC-TEST-ONLY", scope_base, defaults, vectors[]}`. A vector has `id`, `title`, `cites`, `scopes` (labels merged over `scope_base`) and ordered `steps`:

- `advance`: `obs` (a kit observation; labels resolved, `defaults[kind]` merged under it unless `raw`) and `expect` (`verdict`, `code`, optional `applied`, `fallback_reason`);
- `policy_state`, `check` (log length, evidence count, rows, high-water, revoked pairs, ratchet, store), `save` and `swap_to` (state replaced by an older or forked copy: the custody event), `tear` (torn write or tampering: `state_ahead_of_log`, `log_ahead_of_state`, `log_entry_corrupted`, `row_validity_extended`, `row_issuer_changed`, `revoked_set_truncated`, `ratchet_cleared`), and `concurrent` (every serial permutation must give the stated accepted count and an allowed final row map: the expectation is explicit serialization by the host).

Value macros resolved against the current state: `{"$row": {"scope", "field"}}` (for example `activation_ref`), `{"$anchor": ...}`, `{"$saved": name}`, `{"$saved_anchor": name}`.

For a Runtime or Control Plane owner (EXT-S4-2 and the Control Plane equivalent): read the JSON with any language, map each `advance` observation to your store's operation, apply it to a fresh store per vector, and compare verdict class and code (`UNKNOWN_FAIL_CLOSED` is your HOLD), then the `check` and `policy_state` expectations. Do not import the kit into a production path; it exists to be replayed in tests. Python owners may call `registry_conformance.run_vector_set(doc)` directly as a reference. The runner never touches the filesystem; load the JSON yourself.

## Interpretations the Architect should confirm (none changes a ruled semantic)

1. A fourth verdict `REFUSE` is kept next to the three the ADR names, so non-stale refusals keep a distinct class (ruling R1 adopts the four-state vocabulary).
2. `select` at activation must fall inside `[valid_from, valid_until)` at `now` (the time layer of verification); `withdraw` has no window.
3. A fresh higher-epoch `select` naming a **revoked** current row is accepted only when no record, issuer or key revocation applies to it (contract 7.1, D-04, ruling R2); the revoked identity stays revoked. Replaying or re-activating the revoked pair, or a pre-revoked epoch, is refused. A `withdraw` over a revoked row is refused.
4. Record-scope and issuer-scope revocation (`revoked_records`, `revoked_issuers`, `issuer_id` on statements) are kit extensions needed to give ruling R2 vectors; the contract snapshot profile names neither (see Revocation scope). A record is identified for revocation by `(record_id, record_version)`.
5. `superseded` is derived from the `min_epochs` floor or from an activated newer selection only (ruling R3). The contract names the state and its precedence but not a trigger; no inference from an unactivated epoch is made.
6. `rebaseline` is removed as behaviour (ruling R4); recovery is a documented proposal only. `restore` from a known store is retained as a consistency check, and an unknown store is never made known inside the kit.
7. An identical snapshot redelivery is accepted without a new log entry.
8. The kit models `restore` as merging the pre-restore floors (high-water, revoked, snapshot version) into the restored copy; a real restore without that knowledge is the disclosed limit of contract 8.4, and vector RC-11 records that with no external anchor the kit cannot detect an older copy.

## Not covered (explicit)

Signature, digest and policy-binding serialization checks (contract 4.1 line 1) and the ten verification layers; effective-policy comparison; physical storage, transactions and locks (the kit only states the serialization expectation); explicit ratchet provisioning (no log entry type exists for it); approval generation (D-16); the relaxation transition itself (not authorized). Nothing here is qualified or a verdict, and green CI is not qualification (Risk-Based Testing Addendum, Level 1 and Level 2 scope).
