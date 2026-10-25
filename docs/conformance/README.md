# OCS consumer activation / high-water conformance kit (EXT-S1-8)

Status: **IMPLEMENTED / DEVELOPER-TESTED.** Builder-authored. Not independently qualified, not an oracle, not a verdict. RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.

This is a **conformance kit, not an activation store.** The Registry holds no activation state, no high-water, no revoked set and no ratchet (ADR-REG-TR01; `docs/r08-v2-contract.md` section 7). The enforcing component (Runtime, Control Plane) owns the real store. The kit defines the pure transition and derivation rules and a corpus of vectors so each owner can check its own implementation.

Contents (all new):

| Path | Purpose |
|---|---|
| `registry_conformance/highwater.py` | pure `advance(state, observation) -> (new_state, verdict)`, pure derived `policy_state(...)`, `empty_state()`, `verify_state()` |
| `registry_conformance/__init__.py` | strict vector validator (`validate_vector_set`, `MalformedVector`) and pure vector runner (`run_vector`, `run_vector_set`) |
| `registry_conformance/vectors/*.json` | 77 language-neutral vectors in 9 files, all `SYNTHETIC-TEST-ONLY` |
| `tests/test_conformance_kit.py` | developer tests, malformed-vector refusals, in-suite mutation checks, randomized monotonicity invariants |

## Boundaries (what the kit never does)

- No I/O, no persistence, no network, no clock read (time is the integer `now` in every observation), standard library only, no import of any registry module. The core does not import the kit (a test enforces both directions).
- It never mints authorization: a verdict `ACCEPT` means only that the supplied transition or comparison is consistent with the supplied state. Verdicts carry no authorization member (the runner fails any verdict with an unexpected key).
- It never reverses a revocation, never clears the `scope_required` ratchet, never lowers a high-water, floor or snapshot version. The vector runner asserts these monotonic invariants after **every** step of **every** vector, plus: log and evidence are append-only; each rejected transition appends exactly one negative-evidence record (`ocs-registry-failure-detail/1`) and an accept appends none; `guard` never changes state.
- It does not verify signatures. A `select` or `withdraw` observation carries `verified: true/false` as the caller's assertion that the ten registry layers passed; `false` is refused `statement_not_verified`.

## Verdicts

`ACCEPT`, `REFUSE_STALE`, `REFUSE`, `UNKNOWN_FAIL_CLOSED`. Mapping to the ADR vocabulary (D-21): `REFUSE_STALE` and `REFUSE` are the ADR **REFUSE** (stale epoch, rollback and withdrawal are never a retryable success); `UNKNOWN_FAIL_CLOSED` is the ADR **HOLD** (authority state unavailable or indeterminate, execution prohibited). `code` carries the cause: closed registry codes where one exists (`selection_epoch_stale`, `selection_withdrawn`, `selection_revoked`, `issuer_key_revoked`, `participation_mismatch`, `selection_supersession_invalid`, `selection_conflict`, `selection_expired`, `selection_not_yet_effective`, `trust_snapshot_version_stale`, `trust_snapshot_expired`), otherwise a kit-local code (for example `store_unknown`, `state_older_than_anchor`, `relaxation_not_authorized_v1`). Kit-local codes are conformance vocabulary, not additions to `CODES_V2`.

## State model (a conformance model, not a physical schema)

`empty_state()` returns a plain JSON-compatible dict: `rows` per scope key (seven-field key of contract section 7), a hash-chained `log` (`entry_type` in `activate`, `withdraw`, `revoke`, `sync`; the vocabulary is not extended), `evidence` (negative evidence stream), `scope_required` ratchet, `floors` (per-scope high-water, revoked pairs, revoked key ids, snapshot version, `min_epochs`; monotone), `snapshot`, `external` floor, `anchor` (log-head anchor) and `store` (`known` or `unknown`). `activation_ref` is the entry hash of the `activate` entry. Physical names belong to EXT-S4-0.

`anchor` stands for the log-head anchor that contract 8.3 requires to be held **outside** the store. In the kit it travels in the state value for convenience; an observation may carry `external_anchor`, which wins when its `log_head` is at least the state's. A host must persist the anchor externally and pass it in.

## Observations

`select`, `withdraw`, `sync` (a verified snapshot), `external_floor` (raise-only), `read`, `guard` (contract 7.4 comparisons on a claim with or without a binding), `restore`, `lose_state`, `rebaseline`, `relax_scope_required`. Unknown keys, wrong types, non-ASCII or out-of-set identifiers, bad digests and unsupported kinds are refused `observation_malformed` with evidence and no state change.

`relax_scope_required` is **defined but not authorized in V1**: it is refused `relaxation_not_authorized_v1` however it is populated, and the refused-by-default vectors (RT-04) document it.

## policy_state

`policy_state(state, scope, now, known_selection=None)` returns `{"policy_state", "required", "display"}` and no boolean authority. Precedence: `unknown`, `revoked`, `withdrawn`, `superseded`, `expired`/`not_yet_valid`, `active`; with no row `not_selected`, or `selected_not_activated` when the reader supplies a known unactivated selection. Validity is `[valid_from, valid_until)`. A required scope (ratchet set or required row) that is not `active` displays `REQUIRED — UNAVAILABLE`, never `DISABLED` and never a success state.

## Vector format and how to hand it over

Each file is `{schema: "ocs-conformance-vectors/1", label: "SYNTHETIC-TEST-ONLY", scope_base, defaults, vectors[]}`. A vector has `id`, `title`, `cites`, `scopes` (labels merged over `scope_base`) and ordered `steps`:

- `advance`: `obs` (a kit observation; labels resolved, `defaults[kind]` merged under it unless `raw`) and `expect` (`verdict`, `code`, optional `applied`, `fallback_reason`);
- `policy_state`, `check` (log length, evidence count, rows, high-water, revoked pairs, ratchet, store), `save` and `swap_to` (state replaced by an older or forked copy: the custody event), `tear` (torn write: `state_ahead_of_log`, `log_ahead_of_state`, `log_entry_corrupted`), and `concurrent` (every serial permutation must give the stated accepted count and an allowed final row map: the expectation is explicit serialization by the host).

Value macros resolved against the current state: `{"$row": {"scope", "field"}}` (for example `activation_ref`), `{"$anchor": ...}`, `{"$saved": name}`, `{"$saved_anchor": name}`.

For a Runtime or Control Plane owner (EXT-S4-2 and the Control Plane equivalent): read the JSON with any language, map each `advance` observation to your store's operation, apply it to a fresh store per vector, and compare verdict class and code (`UNKNOWN_FAIL_CLOSED` is your HOLD), then the `check` and `policy_state` expectations. Do not import the kit into a production path; it exists to be replayed in tests. Python owners may call `registry_conformance.run_vector_set(doc)` directly as a reference. The runner never touches the filesystem; load the JSON yourself.

## Interpretations the Architect should confirm (none changes a ruled semantic)

1. A fourth verdict `REFUSE` is added to the three named verdicts so non-stale refusals keep a distinct class.
2. `select` at activation must fall inside `[valid_from, valid_until)` at `now` (the time layer of verification); `withdraw` has no window.
3. A fresh higher-epoch `select` naming a **revoked** current row is accepted (contract 7.1 and D-04: the only reversal path); the revoked pair stays revoked. Replaying or re-activating the revoked pair, or a pre-revoked epoch, is refused. A `withdraw` over a revoked row is refused.
4. `superseded` is derived when the row epoch is below the `min_epochs` floor for its selection id, or the reader knows a higher unactivated epoch; contract 7.2 names the state but not the trigger.
5. `rebaseline` (explicit, authorized, with a `decision_ref`) is refused when the store was lost, or when the state is behind any high-water or revoked pair; otherwise it moves the log-head anchor to the restored head. It is recorded in a separate `rebaselines` list because the `entry_type` vocabulary is closed. The kit models `restore` as merging the pre-restore floors (high-water, revoked, snapshot version) into the restored copy; a real restore without that knowledge is the disclosed limit of contract 8.4, and vector RC-11 records that with no external anchor the kit cannot detect an older copy.
6. An identical snapshot redelivery is accepted without a new log entry.

## Not covered (explicit)

Signature, digest and policy-binding serialization checks (contract 4.1 line 1) and the ten verification layers; effective-policy comparison; physical storage, transactions and locks (the kit only states the serialization expectation); explicit ratchet provisioning (no log entry type exists for it); approval generation (D-16); the relaxation transition itself (not authorized). Nothing here is qualified or a verdict, and green CI is not qualification (Risk-Based Testing Addendum, Level 1 and Level 2 scope).
