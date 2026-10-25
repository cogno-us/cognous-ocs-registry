# R08 successor contract `r08-v2` (interface specification; documentation only)

Status: **PROPOSED, for Architect adoption through `EXT-S1-1`**; the Architect's round-2 rulings of 2026-10-25 are applied (provenance table in ADR section 6) (decisions in [`docs/decisions/2026-10-25-adr-ext-s1-1-v1-contract.md`](decisions/2026-10-25-adr-ext-s1-1-v1-contract.md), cited as `D-nn`). Nothing here is implemented, activated, approved, qualified or released. It authorizes no EXT PR after `EXT-S1-1`. RELEASE, PUBLICATION and PRODUCTION: HOLD.

Relation to `r08-v1` ([`r08-s01-contract.md`](r08-s01-contract.md)): `r08-v2` is a strict additive successor. Every `r08-v1` behaviour, code, signing input, serialized output, golden output and test stays unchanged (D-09). Source-byte identity is reserved for the frozen legacy directories `registry_contract/`, `registry_consumer/` and `baseline/`; shared `registry_successor/` files may be refactored only under the golden-replay proof. This page states only what `r08-v2` adds or fixes. Anything not stated here is the `r08-v1` rule.

Scope (D-11, D-12): five Runtime allowlists and three Control Plane freshness bounds, atomic Route B only. No `max_amount` slot (reserved or inactive), no ninth field. `identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds` and the evidence-obligation age limits are out of V1 extraction: not added to the profile, and their Control Plane enforcement is not disabled. The registry stores and distributes verified, narrowing, non-authorizing data. It never activates, never issues a grant, never authorizes an effect (D-22).

## 1. Versioning, dispatch and module layout (D-09, D-10)

- `contract_version` = `r08-v2` on every v2 record and selection envelope. A v2 document presented to a v1 entry point refuses `contract_unsupported`; a v1 document presented to a v2 entry point refuses the same way. Signing input is `b"ocs-reg/r08-v2/selection\n" + canonical_bytes(statement)`, so a v1 signature never verifies a v2 statement and the reverse.
- **Family dispatch table** (small, data only): `family -> (payload_validator, composer, evaluator_binding, caller_normalizer, enforcing_component)`. A family absent from the table, or spelled with a different case or whitespace, refuses `family_unsupported` (parse) or `composition_family_unsupported` (compose). The table is the only place a family is registered. `EXT-S1-2` registers `f1a-local-execution-allowlist` alone and proves the refactor is behaviour-preserving before any v2 family is added.
- **Reuse before addition.** v2 reuses the public interfaces of `common.py` (`load_document`, `canonical_bytes`, `digest`, validators), `record.py`, `compose.py`, `selection.py`, `verify.py` and `decision.py`. v2-specific code lives in new `v2_*.py` modules only where reuse would alter v1 behaviour (the v2 statement shape with `disposition`, the extra verification layer, the identity object, `CODES_V2`). No second copy of the strict loader, digest, verification layers or decision function is permitted.
- `registry_contract/`, `registry_consumer/`, `baseline/` stay frozen. `registry_successor/` core files change only by `EXT-S1-2` to `S1-6` and `S4-1`, one owner at a time, each change proved byte-preserving for v1 by goldens captured from the unrefactored head.

## 2. Families (D-10, D-11)

| Family id | Payload (exact keys, no others) | Composition with the caller | Enforcing component |
|---|---|---|---|
| `f1a-local-execution-allowlist` (v1, unchanged) | `allowed_actions`, `allowed_adapters`, `allowed_units` | intersection | Runtime |
| `f1ab-local-execution-allowlist` (v2) | `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains` | intersection per key | Runtime |
| `f4-control-plane-age-bounds` (v2) | `status_max_age_seconds`, `approval_max_age_seconds` | strict integer seconds, `min(caller, registry)` per scalar | Control Plane |
| `f5-action-class-age-bounds` (v2) | `class_status_max_age_seconds`: object of `action_class -> int seconds` | per-class `min(caller, registry)` | Control Plane |

Rules common to every v2 payload:

- Absent key: `field_missing`. Extra key (including any amount key): `field_unknown`. An empty F1ab list is a valid explicit deny-all for that dimension; an absent list is never an implicit allow or deny.
- F1ab lists: sorted, duplicate-free, at most 256 entries, each 1..128 characters, no control, separator or `*` characters, exact-string membership (no case folding, no wildcard).
- F4/F5 **registry** values: Python `int` (not `bool`, not float, not string), at least 1 (`AGE_MIN`, adopted) and at most the Control Plane maximum (section 2.1; **pending**, not adopted); nonfinite, zero, negative and unrepresentable values refuse. The floor validates the registry value; it never clamps the effective output. No universal five-second floor. No cross-bound among the distinct ages: an individually valid inverted pair is accepted. An unknown action class, a third F4 key or an empty class map refuses.
- A registry value above the caller value never widens: the effective value is the caller value and the outcome is reported `registry_value_not_narrowing`. An invalid caller value refuses and is never clamped or replaced. A required operation that cannot compose never returns the caller value.
- Deny-all is decided by the enforcing gate before any policy object is built (D-20). The family composers never construct a Runtime policy.

### 2.1 Safety bounds belong to the Control Plane (D-27)

The registry F4/F5 validator carries no private constant. Bounds are read from a table in the Control Plane contract that records, per field, the lower bound, the upper bound, the evidence for it and the source head. The registry validator copies the table with a citation and a test that fails if the two differ. `AGE_MIN = 1` is adopted for registry input. `AGE_MAX = 2678400` is **not adopted**: the maximum is an evidence-supported value selected by the Control Plane owner after source characterization; no production requirement is inferred from fixture values (largest fixture value 3600 s, synthetic) and no universal bound is invented.

**Interim supported range: `1 <= value <= MAX`, with `MAX` pending.** Until `MAX` is recorded the schema stays bounded and refuses non-integers (`bool`, float, string), nonfinite values, zero, negative values and any integer unrepresentable in Control Plane arithmetic (adding it to a datetime raises or otherwise fails). Worker D's reading is that with the freshness profile on, a base near 2.5e11 s overflows date arithmetic (unhandled `OverflowError`); that is a failure point for the owner to characterize exactly, not a supported maximum. The precise supported range and its evidence are documented in the Control Plane contract **before `EXT-S1-4` or `EXT-S3-2` merges**; neither merges with a placeholder bound. A caller value is valid only as a strict integer with `0 <= value <= MAX` (the Control Plane models admit 0; the registry-input range `1 <= value <= MAX` differs only at 0); a caller value of 0 stays 0 because the floor never clamps the effective output; an invalid caller refuses and is never replaced.

### 2.2 Freshness ceiling at the dispatch and authorization boundary (D-29)

The effective registry-narrowed freshness limit must remain binding throughout supported Route B operation and is enforced at the applicable dispatch/authorization boundary. Host-factory composition of the ceiling is necessary but insufficient where a later dispatch can act on an observation beyond the effective ceiling. The smallest compatible implementation uses existing deadline anchoring where supported. `anchor_deadline_to_inputs` adds a key to the profile dump when true and therefore changes `approval_commitment`: commitments must not change silently, and any use is an explicit, tested, re-pinned change in a bounded Control Plane PR with Architect review. The previously observed 2x dispatch window is **not** an accepted V1 freshness guarantee. With no registry configuration applied, behaviour and commitments are unchanged. It must be demonstrated that an outage extension cannot widen a registry-narrowed ceiling. A change to Control Plane enforcement source is isolated in its own bounded PR: characterize existing behaviour first, targeted negative and compatibility tests, re-pin affected contracts and source revisions, Architect review before merge.

## 3. Selection statement and disposition (D-01, D-02)

A v2 statement has the `r08-v1` fields plus `disposition` in `{select, withdraw}`. `participation` stays the only required/optional source. `epoch` stays the selection epoch (the field name is unchanged; the record succession counter of `ocs-registry-record/0` is a different concept, D-30).

| Rule | `select` | `withdraw` |
|---|---|---|
| `record`, `evaluator` | present and pinned as in v1 | both `null` (a withdrawal pins no record) |
| `supersedes` | `null` only for the first selection in a scope; otherwise exact `{selection_id, epoch, statement_digest, decision_ref}` of a strictly lower epoch of the same `selection_id` | required, same shape, strictly lower epoch |
| `participation`, `family`, scope, `operation`, `effective`, `revocation_ref`, `selector_ref`, `issued_at` | as v1 | as v1 (the withdrawal has its own validity window) |

A malformed `supersedes`, a `withdraw` with a record pin, a `withdraw` without `supersedes`, or a `withdraw` at a lower or equal epoch refuses `selection_supersession_invalid` (same code and asymmetry as v1 section 3a). A higher epoch alone never supersedes: the newer statement must name the older exactly. Supersession requires a fresh authenticated statement with a strictly higher applicable selection epoch. Replay, restoration, withdrawal or stale selection state never reactivates or supersedes implicitly, and every rejected transition leaves preserved negative evidence (section 7.1).

### 3.1 Verification layers

`LAYERS_V2` = the ten `r08-v1` layers plus a final `disposition` layer. `record_binding` is `not_evaluated` for a withdrawal and does not count against `ok` for that disposition only. All ten v1 layers must pass before `disposition` is reached, so an unsigned, expired, revoked, stale, out-of-scope or untrusted withdrawal refuses with its own specific code and **never** with `selection_withdrawn`: an invalid selection cannot masquerade as an intentional withdrawal (D-17). An authenticated, in-window, unrevoked, in-scope withdrawal fails the `disposition` layer with `selection_withdrawn`. `operationally_authorized` is always `False`.

### 3.2 Decision kinds

Unchanged: `applied`, `applied_deny_all`, `overlay_not_applied` (optional only), `required_policy_unavailable` (required only). `selection_withdrawn` is an ordinary refusal and is never translated into success. For a required scope effect it is a **REFUSE** when the withdrawal is authenticated, current and definitively applies to the attempted effect, and a **HOLD** only when the authoritative state is unavailable or indeterminate and execution is prohibited; required returns no policy and never the caller policy. Optional returns the unchanged caller policy as `overlay_not_applied` with `registry_code = selection_withdrawn` and `applied=false` only through the authenticated optional-state determination of section 7.4, line 8 (the fallback reason `withdrawn` is preserved in evidence).

### 3.3 Closed codes (D-02)

`CODES_V2` = the 46 `r08-v1` `CODES` entries (unchanged, same layers and meanings) plus exactly two additions:

| Code | Layer | Meaning |
|---|---|---|
| `trust_snapshot_version_stale` | `trust` | snapshot version is below the supplied floor, or equals it with a different fingerprint |
| `selection_withdrawn` | `disposition` | an authenticated withdrawal is the head statement for this scope |

`CODES` (46) is not modified; `CODES_V2` is a separate mapping declared by `EXT-S1-2`. The completeness test iterates every `CODES_V2` entry (48) and fails on any unmapped code. A v1 consumer never sees a v2-only code.

## 4. Canonical policy binding (D-14, D-15)

One typed object, **owned by `EXT-S1-5`** (`EffectivePolicyIdentity`, produced from verified inputs), consumed and specialized for the effect boundary by `EXT-S4-0`. No other member list exists. Members, fixed here:

| Member | Source | Existing registry field? |
|---|---|---|
| `binding_profile` = `ocs-policy-binding/1` | constant | new constant |
| `record_id`, `record_version`, `record_digest` | verified record (selection `record` pin) | yes (`record` pin; `record_digest` also covers the evaluator pin) |
| `selection_id`, `selection_epoch`, `selection_digest` | verified statement (`selection_id`, `epoch`, `statement_digest`) | yes (`selection_epoch` is the statement `epoch`) |
| `family`, `consumer_id`, `scope` (`tenant`, `institution`, `authority_domain`), `operation` | verified statement | yes |
| `effective_policy_digest` | `digest` of the canonical composed effective payload (record payload composed with the caller policy by `min`). **Caller-dependent evidence member, not selection state:** it may differ per caller policy under one unchanged selection epoch | new, derived |
| `activation_ref` | immutable reference to the consumer-owned activation transition: the entry hash of the `activate` log entry that made this selection active (section 4.2) | new; **not registry-derived** |
| `trust_snapshot_version`, `trust_snapshot_fingerprint` | verified `TrustSnapshot.version`; digest of the normalized snapshot (section 5) | version yes; fingerprint new |

Deliberately **not** members: `snapshot_id` (covered by the fingerprint), evaluator blob and hash (covered by `record_digest`), `participation` (covered by `selection_digest`; the scope ratchet is consumer state), the caller policy digest (evidence only; `effective_policy_digest` already changes if the caller policy changes), `valid_from`/`valid_until` (covered by `selection_digest`; the guard reads the row and the lock-time clock), and any state or presentation value.

### 4.1 Serialization and digest

**Digest.** `binding_digest` = `"sha256:" + hex(sha256(b"ocs-reg/r08-v2/policy-binding\n" + canonical_bytes(binding)))` with lowercase hex.

**Serialization and byte encoding.** `canonical_bytes` is exactly `registry_successor/common.py`: JSON text with object keys sorted, separators `,` and `:` (no whitespace), `ensure_ascii=True`, encoded as UTF-8. Because every string member is ASCII (below), the output is pure 7-bit ASCII bytes and equals the Control Plane `commitment` serializer's output (which uses `ensure_ascii=False`, source reading at Control Plane `7a4bcd40`, `bounded.py` `_canonical_bytes`).

**Field ordering.** Members are serialized in sorted key order (byte order of the ASCII key names), at every nesting level including `scope`; declared order in section 4 is documentation only and never affects the bytes. The binding has exactly the members of section 4: a missing or extra member refuses.

**Value rules.** Integers (`record_version`, `selection_epoch`, `trust_snapshot_version`) are JSON integers in base 10 with no sign, leading zeros, fraction or exponent, at least 1, and not `bool`. Digest members (`record_digest`, `selection_digest`, `effective_policy_digest`, `activation_ref`, `trust_snapshot_fingerprint`) match `sha256:[0-9a-f]{64}` exactly. `binding_profile` is the constant `ocs-policy-binding/1`. No `null`, float or boolean appears in a completed binding.

**ASCII-only V1 policy-binding identifiers.** The identifier members (`record_id`, `selection_id`, `family`, `consumer_id`, `operation`, and `scope.tenant`, `scope.institution`, `scope.authority_domain`) must match, on the raw string with no normalization and no case folding, the regular expression `\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z`, with the classes read as the explicit ASCII ranges (no locale, `\w`, `\d`, `re.IGNORECASE` or Unicode-aware class). That is: 1 to 128 characters; first character `A-Z`, `a-z` or `0-9`; the rest from those plus `.`, `_`, `:`, `-`. Any other character, including every non-ASCII code point, whitespace, control, `*` and `/`, refuses with `field_invalid`. Unsupported Unicode is rejected, never normalized (no NFC, NFKC, case folding or transcoding), so components cannot normalize inconsistently. This is a V1 interoperability restriction on canonical identity fields only; it does not restrict human-readable policy metadata, which is never a binding member. (Existing `r08-v1` identifier validation is `[a-z0-9][a-z0-9._-]{2,63}`, a subset of this set; v1 scope tokens may carry Unicode, which `r08-v2` refuses.)

**Required tests.** Cross-language golden vectors: the binding, its `canonical_bytes` (hex) and `binding_digest` are computed by the registry implementation, by the Control Plane `commitment` serializer and by at least one non-Python implementation, and the three must be byte-identical (`EXT-S1-5`, `EXT-S4-4`). Malformed-input tests, each refused with a typed code: non-ASCII identifier (for example a Latin-1 or non-BMP character, and a precomposed versus decomposed pair that must not be conflated), out-of-set ASCII character, empty and over-128-character identifier, wrong type, missing and extra members, non-canonical integer (leading zero, `1.0`, `true`, exponent, negative, zero), uppercase hex in a digest, wrong `binding_profile`. No Runtime or Control Plane code imports registry code: each side implements this published profile and both are tested against the shared vectors.

### 4.2 Two states of the object

The registry produces the object with `activation_ref = null` (the registry cannot know it: it never activates, and `activation_ref` is not a Registry-issued authorization token). The enforcing gate fills `activation_ref` from its own log and passes the completed object to claim issuance. `activation_ref` is an immutable reference to the specific consumer-owned activation transition governing the effect: the entry hash of the `activate` log entry, whose hashed content includes the scope key, the selection epoch, the selection digest and the event type, so it identifies the applicable scope, selection epoch and activation event and blocks substitution or stale-state reuse. It is stable across `sync` entries and changes only with a new activation. There is one canonical representation across Registry, Runtime, Control Plane and evidence: `sha256:` plus 64 lowercase hex characters (section 4.1), never re-encoded or abbreviated. The claim-carried form requires a non-null `activation_ref`; a null one is refused by the guard. The digest is always computed over the completed form.

### 4.3 Claim carriage (D-13)

The completed object travels inside the Control Plane authorization claim as a **declared optional claim field**, omitted when absent, under a successor claim profile; the claim commitment covers it. (A bare extra dictionary key is dropped on the model path, which breaks `verify_local_execution_claim`; see D-28.) A keyword-argument carrier (B-lite) is rejected. A claim with no binding stays byte-identical to today. It is valid where no registry policy governs the operation, and as an optional fallback only on an authenticated and valid optional-state determination (section 7.4, line 8); an omitted binding is not an intentionally absent optional policy, and a no-binding claim in a ratcheted scope, or one that would bypass an activated policy, is refused. Source-verified carrier functions are in the ADR (D-28). The destination guard (`EXT-S4-2`) compares the claim-carried members with the trusted state row under the destination lock and the lock-time clock; it recomputes `binding_digest` from the members and never trusts a digest string alone (comparison rules in section 7.4).

## 5. Trust snapshot floor and fingerprint (D-25)

- `TrustSnapshot` is unchanged. Two new optional inputs to the v2 verification path, both default off so `r08-v1` and unset-v2 corpora reproduce exactly: `min_trust_snapshot_version` (the external floor) and `last_accepted_snapshot` = `(version, fingerprint)` of the snapshot the consumer previously accepted. A non-int, bool, 0 or negative floor, or a malformed `last_accepted_snapshot`, refuses `trust_snapshot_invalid`. Order: expiry is reported before version.
- Version below the floor, or below `last_accepted_snapshot.version`: `trust_snapshot_version_stale`. Equal to `last_accepted_snapshot.version`: accepted only if the fingerprint is equal (idempotent redelivery); equal version with a different fingerprint refuses `trust_snapshot_version_stale`. **Bootstrap:** with no `last_accepted_snapshot` only the floor applies, and the first accepted fingerprint is recorded by the consumer (a `sync` log entry); the verifier is stateless and the comparison against history is the consumer's input, never something the verifier remembers.
- `trust_snapshot_fingerprint` = `digest` (registry `canonical_bytes`, section 4.1 serializer, no domain prefix) of the normalized snapshot object `{snapshot_id, version, valid_until, issuers, revoked_key_ids, revoked_selections, min_epochs}`: `issuers` sorted by `key_id`, each `{key_id, issuer_id, alg, public_key (lowercase hex), authority}` where `authority` is a list of five-element arrays `[consumer_id, tenant, institution, authority_domain, operation]` (the `AuthorityGrant` fields in that order) sorted lexicographically by array (string comparison by Unicode code point); `revoked_key_ids` sorted; `revoked_selections` sorted as `[selection_id, epoch]` pairs by `(selection_id, epoch)`; `min_epochs` sorted as `[selection_id, floor]` pairs by `selection_id`. Duplicates are refused (`trust_snapshot_invalid`), as the existing normalizer already does for issuer key ids and floors. Vector (input in unsorted order; the normalized form and digest were computed by a throwaway script that applies exactly this profile, not by repository code):

```json
{
  "input_authority_order": "unsorted: op-transfer before op-audit",
  "normalized": {
    "snapshot_id": "snap-example-7",
    "version": 7,
    "valid_until": "2026-12-01T00:00:00Z",
    "issuers": [
      {
        "key_id": "key-example-1",
        "issuer_id": "issuer-a",
        "alg": "ed25519",
        "public_key": "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
        "authority": [
          [
            "runtime-emulator",
            "tenant-a",
            "inst-a",
            "domain-a",
            "op-audit"
          ],
          [
            "runtime-emulator",
            "tenant-a",
            "inst-a",
            "domain-a",
            "op-transfer"
          ]
        ]
      }
    ],
    "revoked_key_ids": [
      "key-old-1"
    ],
    "revoked_selections": [
      [
        "sel-old-1",
        2
      ]
    ],
    "min_epochs": [
      [
        "sel-example-f1ab",
        3
      ]
    ]
  },
  "fingerprint": "sha256:fa8e41adb7732a8f6cb5e593e9328f7b247814ba4631ae4629f7bdcb077ee7a6"
}
```
- Revocation rides the operator-delivered snapshot (`revoked_selections`, `revoked_key_ids`). `revocation_ref` stays validated and unconsumed. A snapshot that omits an entry present in an earlier accepted snapshot is refused by the consumer (revoked set is grow-only, section 7). The snapshot builder takes a required `max_lifetime_seconds` argument and refuses a longer lifetime and unsorted, duplicate or oversize input; **no default lifetime is adopted here** (it follows the operator-set sync cadence, B-08).
- The durable floor and the revoked set belong to the enforcing component, never to the registry.

## 6. Failure carriage and outcome map (D-18 to D-21)

The outcome map is `docs/p1-extraction-plan/data/ld02-outcome-map.json` (merged, unchanged). `EXT-S1-5` implements it with the changes recorded in the ADR. Contract points:

- Every registry refusal travels as **structured negative evidence** (`ocs-registry-failure-detail/1`, carrying at least `registry_code`, `layer`, `participation`, `decision_kind`, `stage`) beside the component refusal category. Distinct registry codes keep distinct cause fields even when they share a component category.
- No authorization, policy-state or retry decision is derived from message text (including `PermissionError` text). Typed reason codes or a typed boundary adapter only; historical text is diagnostic.
- Preconstruction registry deny-all (`registry_deny_all`) is distinct from a denial produced by `LocalExecutionPolicy.check`. Reason and check-order equivalence is asserted only for representable non-empty effective policies.
- A stale or rolled-back epoch is a REFUSE with a specific stale-epoch cause. HOLD is reserved for authority state that is genuinely unavailable or indeterminate with effect execution prohibited. Neither is ever a retryable success.

## 7. Enforcing-component state (consumer-owned; D-03 to D-08, D-24)

The registry holds none of this. The contract fixes the logical schema so `EXT-S4-0` can freeze physical names (indicative names from the P1 plan are kept) and so `EXT-S1-8` vectors have something to test.

**Scope key**: `(selection_id, consumer_id, tenant, institution, authority_domain, operation, family)`. At most one selection chain per `(consumer_id, scope, operation, family)`; a second `selection_id` for the same scope is `selection_conflict` and is never activated.

| Logical store | Content | Mutability |
|---|---|---|
| State | one row per scope key: `activation_state` in `{active, withdrawn, revoked}`, `epoch`, `selection_digest`, `participation`, the verified `valid_from` and `valid_until`, the issuer `key_id` that signed the statement, the record pin (`record_id`, `record_version`, `record_digest`), `activation_ref`, `high_water_epoch` | current value only; the verified values are copied from the authenticated statement at activation and are immutable for that epoch; written by the trusted writer |
| Transition history | append-only, hash-chained log; `entry_type` in `{activate, withdraw, revoke, sync}`; each entry holds scope key, epoch, selection digest, issuer key id, previous entry hash, prior and new `activation_state`, timestamp | append only; never edited or deleted |
| Revoked set | `(selection_id, epoch)` pairs | grow only |
| Scope ratchet | `scope_required` per scope key | one-way (section 7.3) |
| Snapshot high-water | highest accepted `trust_snapshot_version`, its fingerprint and its `valid_until`; the current `min_epochs` floors; the revoked key id set (grow only) | monotone |

State is distinct from history: a row says what is true now; the log says how it became true. No row exists means not activated. `activation_state` is never accepted as input and has no writer other than the transitions below.

### 7.1 Transitions

| Event | Precondition (all required) | Effect |
|---|---|---|
| `activate` | verified `select`; epoch strictly greater than `high_water_epoch`; `supersedes` null only if the scope has no history, else exactly the current row's `(selection_id, epoch, statement_digest)`; `(selection_id, epoch)` not in the revoked set; participation not weaker than the ratchet | state `active`, new high-water, log entry |
| `withdraw` | verified `withdraw`; epoch strictly greater than high-water; `supersedes` exactly the current row; participation not weaker than the ratchet | state `withdrawn`, new high-water, log entry; history kept |
| `revoke` | a verified snapshot at or above the floor lists `(selection_id, epoch)`, or lists in `revoked_key_ids` the issuer `key_id` recorded for the row | pair added to the revoked set (for a key revocation, the row's pair, with the distinct cause `issuer_key_revoked` kept in the entry); state `revoked` if it is the row's epoch; terminal for that pair |
| `sync` | a verified snapshot at or above the floor and the `last_accepted_snapshot` rule of section 5 | updates snapshot high-water and records its version and fingerprint in the log; may append `revoke` entries; **never** activates, withdraws, clears a revoked pair, changes a revoked state, or supplies authorization |

**Closing a supersession gap.** A statement may name any strictly lower epoch of the same `selection_id`. If the consumer holds epoch 1 and the issuer produced epoch 2 that never reached it (or that is expired or revoked), the issuer closes the gap by issuing a fresh higher-epoch statement that names the consumer's **current row** exactly. The consumer never processes unactivated ancestors and authenticated lineage stays unavailable (`resolve_authoritative` still refuses). Until then a required scope stays unavailable and an optional scope reports `overlay_not_applied`; neither is success.

Any transition whose precondition fails is refused with the registry code that names the cause, and **negative evidence for every rejected transition is preserved** (`ocs-registry-failure-detail/1` with scope key, epoch, selection digest, code and timestamp) in append-only evidence that is never edited or deleted. `EXT-S4-0` freezes whether it shares the hash-chained log or is a companion stream; either way the closed `entry_type` vocabulary is not extended. A gap in the supersession chain leaves the state unchanged and fails closed until the missing link is delivered. A revoked epoch is never resurrected by reactivation, lineage or restore. There is no implicit reactivation by replay, restoration, withdrawal or stale selection state: reversal is only a fresh authenticated statement with a strictly higher applicable selection epoch that names its predecessor.

### 7.2 Derived read model (A3, D-05)

`policy_state` is computed on read, never stored, never input, never authoritative: `not_selected`, `selected_not_activated`, `active`, `withdrawn`, `revoked`, `expired`, `not_yet_valid`, `superseded`, `unknown`; precedence `unknown`, `revoked`, `withdrawn`, `superseded`, `expired`/`not_yet_valid`, `active`. ENABLED = `active`; DISABLED = `withdrawn` or `not_selected`; every other value shows its own reason. For a required scope that is withdrawn, revoked, expired or unavailable the display is **`REQUIRED — UNAVAILABLE`**, never "disabled". There is no authorizing boolean: a toggle is only a request that becomes a signed select or withdraw statement.

### 7.3 Required-scope ratchet (A4, D-06)

`scope_required` is set one-way by the trusted writer when a `required` selection is activated for the scope (or by explicit authenticated provisioning of the ratchet). Once set: an optional presentation (per call, per selection, per withdrawal, per replayed older statement) refuses `participation_mismatch`; withdrawal or revocation of the selection makes the scope `REQUIRED — UNAVAILABLE` and operations refuse; restoring an older store cannot clear it (the restore fence of section 8 fails closed instead). The ratchet is part of the hash-chained evidence and of restore custody.

**Defined, not authorized.** The only way to clear the ratchet is the administrative transition `relax_scope_required`: an authenticated statement from an authority holding a separate relax grant, naming the scope key and the current ratchet record digest, carrying a strictly higher ratchet generation and an operator-approved `decision_ref`, and logged as its own entry. **No relaxation is authorized in V1.** The closed `entry_type` vocabulary is not extended, no writer exists and no code path is built; adding the entry type needs an ADR amendment and operator authorization.

### 7.4 Guard comparison at the effect boundary (`EXT-S4-2`)

**Atomicity.** The guard compares the claim's policy identity with trusted durable state **inside the atomic transaction** that commits the effect. State changes (activate, withdraw, revoke, sync, ratchet) and effect commits serialize under the applicable transactional boundary, so no effect commits against state a concurrent transition has already changed and no check-then-act gap exists outside the transaction. **Executor-supplied metadata is never authority**: claim members, executor flags, error text and anything else the executor asserts are assertions compared with durable state, never a source of state or of an authorization decision.

Under the destination lock, with the lock-time clock and no network I/O, a claim that carries a binding is refused unless every line holds; the refusal names the first failing cause as a typed code (D-19), never as parsed text. If the authoritative state cannot be read (unavailable, indeterminate, or the store is `unknown` after a restore fence), execution is prohibited: HOLD, never success.

1. The members are well formed under section 4.1 (ASCII character set, value rules), `activation_ref` is non-null, and the recomputed `binding_digest` equals the carried one. An invalid binding refuses; it is never treated as an omitted binding or a withdrawal.
2. Scope identity and withdrawal state: the scope key built from the claim's `selection_id`, `consumer_id`, `tenant`, `institution`, `authority_domain`, `operation` and `family` equals the row's key; a state row exists; and its `activation_state` is `active` (else the cause is not activated, `selection_withdrawn` or revoked; an authenticated, current withdrawal is a REFUSE, D-21).
3. Selection identity, epoch, policy record and digest, activation reference: `selection_id`, `selection_epoch`, `selection_digest`, the record triple (`record_id`, `record_version`, `record_digest`), and `activation_ref` equal the row's values. `effective_policy_digest` and `caller_policy_digest` are **not** compared to durable state: they depend on the caller policy and so legitimately differ per caller under one unchanged selection epoch. They are claim-carried evidence members, bound by the claim commitment, immutable once the claim is issued, recorded in the effect row, and checked only for self-consistency with the claim (they are never authority and never widen what the selection permits); the narrowing itself is enforced by the evaluator on the policy the executor was given, and a caller policy change needs no new signed selection; the epoch equals the high-water for the scope and meets the current trusted `min_epochs` floor for the `selection_id` held in durable state (otherwise `selection_epoch_stale`).
4. Revocation state: `(selection_id, epoch)` is not in the revoked set, and the row's issuer `key_id` is not in the durable revoked key set (else `issuer_key_revoked`, kept distinct).
5. Applicable expiry: the lock-time clock is inside the row's `[valid_from, valid_until)`; any claim or approval expiry that already applies is evaluated by its existing rule and is never widened by this check.
6. Participation: the row's `participation` is not weaker than the scope ratchet; if `scope_required` is set and the row is optional, the claim refuses `participation_mismatch`.
7. `trust_snapshot_version` is at or above the external snapshot floor and `trust_snapshot_fingerprint` equals the fingerprint recorded in the log for that version (else `trust_snapshot_version_stale`). The current snapshot high-water record must also be unexpired at the lock-time clock (its persisted `valid_until`); an expired current snapshot with no newer valid one is indeterminate trusted state, so execution is prohibited (HOLD, typed `trust_snapshot_expired`, never success), and a newer valid snapshot recorded by `sync` restores support for older claims that otherwise pass. Revocation is always judged against the current revoked set, so a newer snapshot never invalidates an older claim only because it is newer.
8. **Claim with no binding.** An omitted binding is not an intentionally absent optional policy. (a) If `scope_required` is set for the scope, the claim is refused (required: a missing binding refuses and a withdrawal cannot downgrade the scope; the durable ratchet is authoritative). (b) If the store is `unknown`, or a row is `active` and inside its window, or `revoked`, the claim is refused: an omitted binding cannot bypass a previously activated policy. (c) Otherwise the claim is an optional fallback only if trusted durable state yields an authenticated and valid optional-state determination (never read from the claim): the scope was never activated (no row and no history); or the row is `withdrawn` by an authenticated `withdraw` log entry of an optional selection; or an optional row is past its verified `valid_until`. The acceptance means only "no registry policy applied": the gate's evidence carries `applied=false`, the original registry code, `fallback=caller_policy` and the fallback reason (`never_activated`, `withdrawn` or `expired`), and the guard never treats an active selection at the destination as applying to it. A claim minted under a binding is never converted to a fallback at the guard: if its row is withdrawn, revoked, expired or replaced it is refused and the operation must be presented again so the gate decides afresh. A scope that must be fail-closed at the commit boundary must have the ratchet set (section 7.3).

### 7.5 Approval generation (D-16)

No approval revives automatically. The Control Plane approval carries an additive approval-generation or policy-binding member in authenticated, approval-bound context (candidate: a key in the `runtime_authority_context` allow-list hashed into `approval_commitment`), with explicit generation continuity: the generation is issued from the authoritative policy state, is monotone, and a withdrawal of a narrowing yields a new, higher generation, never a return to an earlier one. A detached mutable generation substitutable independently of the approval is not permitted. This is a Control Plane source change in a bounded implementation PR with additional tests; this contract authorizes no edit. Mandatory negative sequence: (1) an approval is issued; (2) the profile is narrowed; (3) the approval is invalidated; (4) the narrowing is withdrawn; (5) the original approval remains invalid; (6) a fresh approval succeeds only under the current authoritative policy generation. An old commitment is never reused as evidence of a new authorization.

## 8. Restore, rollback and custody requirements (D-24)

1. One trusted writer per store; never seeded from a claim, a selection or a caller-supplied value; the `provision_claim` seeding pattern is not reused.
2. Every state change and its log entry commit in one transaction; a half-completed activation rolls back.
3. The external floor (`min_epochs`, `min_trust_snapshot_version`) and a log-head anchor are held outside the store they protect. A restored store whose high-water, log head or ratchet disagrees with the anchor, or that is older than the last acknowledged log head, is **unknown**: every required scope refuses, optional scopes report `overlay_not_applied` with the cause, until re-baselined by an explicit, logged operation. Lost state is unknown, never zero.
4. Revoked set and high-water roll back together on database restore; this is a disclosed limit (B14, D07, GAP-G1-02), never claimed as restore safety.
5. Unacknowledged publication reads `UNKNOWN`, not `ACTIVE` (DT-04). Restart before the first successful sync refuses required scopes.
6. No registry call, socket or network I/O inside a destination transaction.
7. Custody of keys, snapshot channel and trust root is operator-gated (no operational trust root in V1); `EXT-S1-8` vectors define the pure transition function only and are not an authoritative store.

## 9. Wire shapes (illustrative; digests computed with the profiles above; signatures are placeholders and do not verify)

**Selection envelope, `select` (envelope shape; the `statement_digest` is `digest(statement)`)**

```json
{
  "contract_version": "r08-v2",
  "kind": "selection-envelope",
  "statement": {
    "kind": "selection",
    "disposition": "select",
    "selection_id": "sel-example-f1ab",
    "epoch": 3,
    "consumer_id": "runtime-emulator",
    "scope": {
      "tenant": "tenant-a",
      "institution": "inst-a",
      "authority_domain": "domain-a"
    },
    "operation": "op-transfer",
    "participation": "required",
    "family": "f1ab-local-execution-allowlist",
    "record": {
      "record_id": "rec-example-f1ab",
      "record_version": 2,
      "record_digest": "sha256:a9dcd70e716cf681dc8e1becd59ebd48efff4da695dfabf7b68873579e6e40e8"
    },
    "evaluator": {
      "evaluator_id": "engine.safe_executor.LocalExecutionPolicy.check",
      "binding": "registered-code-reference",
      "source_blob_id": "2fc880dae37eac76e5074533435740ce0684209d",
      "source_sha256": "sha256:507e39d39cabbf8167794aa03f5fde6266ffab62841cd35d081a83953703254a"
    },
    "effective": {
      "valid_from": "2026-11-01T00:00:00Z",
      "valid_until": "2026-12-01T00:00:00Z"
    },
    "supersedes": {
      "selection_id": "sel-example-f1ab",
      "epoch": 2,
      "statement_digest": "sha256:c54ad42cb1dcd67a09ab3ae5aaf7aba837e2e72d059e2fc76925836e3bde55a7",
      "decision_ref": "dec-example-0007"
    },
    "revocation_ref": "rev-example-f1ab",
    "selector_ref": "selector-example",
    "issued_at": "2026-10-31T12:00:00Z"
  },
  "statement_digest": "sha256:070413bf1b87859ccf447b183abb26b487184ec1d33ef52dc47dea64ac930be3",
  "signatures": [
    {
      "alg": "ed25519",
      "key_id": "key-example-1",
      "signature": "AAAA"
    }
  ]
}
```

**Statement, `withdraw` (names the `select` above exactly; no record pin; envelope omitted)**

```json
{
  "kind": "selection",
  "disposition": "withdraw",
  "selection_id": "sel-example-f1ab",
  "epoch": 4,
  "consumer_id": "runtime-emulator",
  "scope": {
    "tenant": "tenant-a",
    "institution": "inst-a",
    "authority_domain": "domain-a"
  },
  "operation": "op-transfer",
  "participation": "required",
  "family": "f1ab-local-execution-allowlist",
  "record": null,
  "evaluator": null,
  "effective": {
    "valid_from": "2026-11-10T00:00:00Z",
    "valid_until": "2026-12-01T00:00:00Z"
  },
  "supersedes": {
    "selection_id": "sel-example-f1ab",
    "epoch": 3,
    "statement_digest": "sha256:070413bf1b87859ccf447b183abb26b487184ec1d33ef52dc47dea64ac930be3",
    "decision_ref": "dec-example-0008"
  },
  "revocation_ref": "rev-example-f1ab",
  "selector_ref": "selector-example",
  "issued_at": "2026-11-09T12:00:00Z"
}
```

**F1ab payload (the `allowed_units` list is an explicit deny-all) and the composed effective policy against a caller that allows `action-a` only**

```json
{
  "payload": {
    "allowed_actions": [
      "action-a",
      "action-b"
    ],
    "allowed_adapters": [
      "adapter-a"
    ],
    "allowed_institutions": [
      "inst-a"
    ],
    "allowed_authority_domains": [
      "domain-a"
    ],
    "allowed_units": []
  },
  "effective": {
    "allowed_actions": [
      "action-a"
    ],
    "allowed_adapters": [
      "adapter-a"
    ],
    "allowed_institutions": [
      "inst-a"
    ],
    "allowed_authority_domains": [
      "domain-a"
    ],
    "allowed_units": []
  }
}
```

**F4 and F5 payloads**

```json
{
  "f4": {
    "approval_max_age_seconds": 30,
    "status_max_age_seconds": 45
  },
  "f5": {
    "class_status_max_age_seconds": {
      "class-a": 20,
      "class-b": 90
    }
  }
}
```

**Completed policy binding and its digest (`binding_digest` per section 4.1)**

```json
{
  "binding": {
    "binding_profile": "ocs-policy-binding/1",
    "record_id": "rec-example-f1ab",
    "record_version": 2,
    "record_digest": "sha256:a9dcd70e716cf681dc8e1becd59ebd48efff4da695dfabf7b68873579e6e40e8",
    "selection_id": "sel-example-f1ab",
    "selection_epoch": 3,
    "selection_digest": "sha256:070413bf1b87859ccf447b183abb26b487184ec1d33ef52dc47dea64ac930be3",
    "family": "f1ab-local-execution-allowlist",
    "consumer_id": "runtime-emulator",
    "scope": {
      "tenant": "tenant-a",
      "institution": "inst-a",
      "authority_domain": "domain-a"
    },
    "operation": "op-transfer",
    "effective_policy_digest": "sha256:0f51b95ddc52a51b78e718e46cca42b9e0d000740443904c1378da2db828197b",
    "activation_ref": "sha256:7f5cc397f3a75d7eb167f54d7aaac9b7b0aa0a43c7830a12e1717c39a1ff4c2a",
    "trust_snapshot_version": 7,
    "trust_snapshot_fingerprint": "sha256:7a8c10fa61aeac5423592bcb437e26875238614c16ef9a0b8c056b6100f5aefe"
  },
  "binding_digest": "sha256:e1619450a5f57341b735b78293bfa8fdaca4d5414816c16e5eb62f8114c79bfd"
}
```


## 10. What this contract does not decide

Physical table names, the claim successor profile name and field position (`EXT-S4-0`), the Runtime reason-code names for stale-epoch and withdrawn causes (`EXT-S1-5`/`EXT-S4-0`, subject to D-21), the approval-generation derivation and carrier field name (`EXT-S3-4`, D-16), the numeric `AGE_MAX` (Control Plane owner, D-27), the dispatch-boundary freshness mechanism (D-29), the trust-snapshot lifetime, quorum or multi-signer policy, `max_amount`, any family beyond the four above, Route A, and every operator-gated item (trust root, key ceremony, production host, release).
