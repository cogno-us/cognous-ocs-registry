# EXT-S1-5 contract preparation: effective-policy identity specification and cross-component golden vectors

- Status: **CONTRACT PREPARATION ONLY.** Documentation and data. No source change anywhere (no file under `registry_successor/`, `registry_consumer/`, `registry_records/`, `registry_contract/`, `registry_adapters/` or `registry_conformance/` is added or edited; no existing file is modified). The full `EXT-S1-5` source change (identity module, `verify.py`/`decision.py` hooks, outcome-map code) is **not** implemented here and stays a later serial PR after `EXT-S1-3`/`EXT-S1-4`.
- Authorization: Architect authorization to prepare the contract and vectors ahead of `EXT-S1-3` merge (Architect O-3 and the policy-binding serialization ruling).
- Vector status: **BUILDER_TESTED.** Vectors are builder-authored and were recomputed by an independent in-test reference serializer and one non-Python (Node.js) implementation. They are not independently qualified, and no Runtime or Control Plane implementation has been run against them. Nothing here is "qualified". RELEASE: HOLD. PUBLICATION: HOLD. PRODUCTION: HOLD.
- Companion files: [`data/ext-s1-5-policy-identity-vectors.json`](data/ext-s1-5-policy-identity-vectors.json) (the vectors) and [`tests/test_ext_s1_5_vectors.py`](../../tests/test_ext_s1_5_vectors.py) (self-contained validation; imports no registry module).
- Relationship to the existing contract: this document **does not define a second binding**. The one canonical binding is [`docs/r08-v2-contract.md`](../r08-v2-contract.md) section 4 (member table), 4.1 (serialization and digest), 4.2 (two states) and 4.3 (claim carriage), decided in [ADR EXT-S1-1](../decisions/2026-10-25-adr-ext-s1-1-v1-contract.md) D-14 and D-15. Where this document restates a rule it quotes the section and adds nothing to the member list. Where the existing text is silent or ambiguous (section 11) this document says so and records a proposal, never a silent decision.

## 1. What this document fixes

Architect O-3 requires one typed identity carrying: the governing record and version; the selected policy and selection epoch; the enforcing scope; the effective configuration digest; the applicable activation identity; and the relevant trust-snapshot identity. Contract 4 already fixes the members. This document makes the byte-level rules and the test oracle exact so Runtime and Control Plane can implement against shared vectors without importing registry code.

## 2. Pinned dependencies (what this spec depends on)

All hashes are SHA-256 of the exact UTF-8 text of the section (trailing whitespace stripped), extracted from the heading line to the line before the next heading of the same or higher level (ADR: from the `**D-nn` line to the line before the next `**D-nn`). The test fails if any of them changes, which forces a re-review of this spec and the vectors. Whole-file hashes are informational (an unrelated edit elsewhere in the file does not invalidate the vectors; a change inside a pinned section does).

| Pin | Anchor | SHA-256 |
|---|---|---|
| contract section 4 (member table, 4.1, 4.2, 4.3) | `## 4. Canonical policy binding (D-14, D-15)` | `48076eb5fac659603e7fd5c0a1dcead33d5b3c75499859e1f4ab3818886291f7` |
| contract 4.1 serialization and digest | `### 4.1 Serialization and digest` | `84bcb05fb13fd793ea2073597fa9633d4f466bc57803f6dc15ab5a67a8c8ec8c` |
| contract 4.2 two states | `### 4.2 Two states of the object` | `ff79a7e4df9ca951d2b9f8750ade25a405ad2e016c32bba64568fb2804ba54eb` |
| contract 5 trust snapshot floor and fingerprint | `## 5. Trust snapshot floor and fingerprint` | `0071101e0c0f321c9a288e63206a31ac493b1c5fc08815d1e0dadc61428c2096` |
| contract 3.3 closed codes | `### 3.3 Closed codes (D-02)` | `aab329b7cd31ac0a0e88f92cc67be5426f6de413587c1e6ee7937e28f1a18268` |
| ADR D-14 (one canonical contract, `activation_ref`) | `**D-14 One canonical policy-binding contract (O-3).**` | `c5a353a75c5357628ccecd47a047053962362fc90d9739345d37c20794cb151d` |
| ADR D-15 (serialization profile) | `**D-15 Serialization profile for the binding (round-2 ruling).**` | `42a37b50857771e2371b843815be8f404eaf9f082991919c7975cf3cd3f73c8e` |
| ADR D-02 (`CODES_V2`, 48) | `**D-02 ` | `55e9f022b539fa2df20038a86e5b119dac8de72b95687710b6dcb9bf629468ee` |
| outcome map (informational file hash and enforced) | `docs/p1-extraction-plan/data/ld02-outcome-map.json` | `dcb14ec1067ccf3218949de57312040dad9df926b134a67f2826e3f0c37d535c` |

Informational whole-file hashes at repository head `efeb8cb`: `docs/r08-v2-contract.md` sha256 `64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01` (git blob `ab66cc0e12eda4e5eaf9fb7642fb4fffb5110d4f`); ADR sha256 `b9ad06be559bfb99c5e669ca7217d2ee28b62cda7738206c31fd8e6866233b67` (git blob `f5ca77f9d21689f28066b62b1aba8587102c9cba`); outcome map git blob `2752800d240d4255af3e62d2e911b0821c8e2af4`.

## 3. The canonical binding: one member list

Quoted from contract section 4 (D-14). The binding is a JSON object with **exactly** these members, no others (a missing or extra member refuses, contract 4.1):

| Member (exact name) | Answers (O-3) | Type and rule | Source | Existing registry field |
|---|---|---|---|---|
| `binding_profile` | profile constant | exactly `ocs-policy-binding/1` | constant | new constant |
| `record_id` | governing record | identifier (section 5.1) | verified record pin | `record.record_id` |
| `record_version` | governing record version | integer | verified record pin | `record.record_version` |
| `record_digest` | governing record content | digest | verified record pin (covers the evaluator pin) | `record.record_digest` |
| `selection_id` | selected policy | identifier | verified statement | `selection_id` |
| `selection_epoch` | selection epoch | integer | verified statement | statement `epoch` (renamed here) |
| `selection_digest` | selected policy statement | digest | verified statement | `statement_digest` (renamed here) |
| `family` | enforcing scope | identifier | verified statement | `family` |
| `consumer_id` | enforcing scope | identifier | verified statement | `consumer_id` |
| `scope` | enforcing scope | object with exactly `tenant`, `institution`, `authority_domain`, each an identifier | verified statement | `scope.tenant`, `scope.institution`, `scope.authority_domain` |
| `operation` | enforcing scope | identifier | verified statement | `operation` |
| `effective_policy_digest` | effective configuration | digest; **caller-dependent evidence**, not compared to durable state | derived (section 6) | new |
| `activation_ref` | applicable activation identity | digest in the single canonical form `sha256:` + 64 lowercase hex; produced by the enforcing gate, never by the Registry | consumer activation log | new, not registry-derived |
| `trust_snapshot_version` | relevant trust snapshot | integer | verified `TrustSnapshot.version` | `TrustSnapshot.version` |
| `trust_snapshot_fingerprint` | trust snapshot identity | digest (section 7) | normalized snapshot | new |

That is **15 top-level members** (`scope` is an object of 3) and 17 leaf values: 8 identifiers (5 top-level plus the 3 scope members), 3 integers, 5 digests and the profile constant. The renames (`epoch` to `selection_epoch`, `statement_digest` to `selection_digest`) are the contract's; no alias is introduced. Add no unnecessary duplicate identifiers: `snapshot_id`, evaluator blob/hash, `participation`, the caller policy digest, `valid_from`/`valid_until` and every state or presentation value are **not members** (contract 4, "Deliberately not members") because each is covered by a member or belongs to consumer state. The vectors include `snapshot_id` and `participation` as refused extras.

### 3.1 Semantics that must not be lost

- `effective_policy_digest` is **caller-dependent evidence** (contract 4 and 7.4 line 3): it may legitimately differ per caller policy under one unchanged selection epoch; it is bound by the claim commitment and checked only for self-consistency with the claim; it is **never compared to durable state** and never authority.
- `activation_ref` (ADR D-14, contract 4.2) is an immutable reference to the specific consumer-owned activation transition governing the effect: the entry hash of the enforcing component's `activate` log entry, whose hashed content includes the scope key, the selection epoch, the selection digest and the event type. It identifies scope, selection epoch and activation event. It is **not a Registry-issued authorization token**: the registry never produces it and never treats it as authority. There is one canonical representation across Registry, Runtime, Control Plane and evidence: `sha256:` plus 64 lowercase hexadecimal characters, never re-encoded, abbreviated or wrapped, and no component keeps a second form. It is stable across `sync` entries and changes only with a new activation.
- The binding is evidence of what was selected and activated. It authorizes nothing. `operationally_authorized` semantics, grants, approvals, claims and the commit-time check are unchanged.

### 3.2 Fields exempt from the identifier restriction and kept out of the digest

The ASCII-only restriction (section 5.1) applies **only** to the eight identifier members of the binding. It does not apply to, and the binding digest never covers:

- human-readable policy metadata: any record or selection description, title, display name, note or label;
- `registry_detail_text` and any message text in failure evidence (diagnostic only; no decision is derived from it);
- statement bookkeeping that is not a binding member: `issued_at`, `valid_from`, `valid_until`, `selector_ref`, `revocation_ref`, `decision_ref`, `supersedes`, `participation`, signatures;
- the values inside an effective policy payload (for example an allow-list entry), which are governed by their own family rules (contract 2: 1 to 128 characters, no control, separator or `*` characters) and are escaped, never rejected, by the serializer (vector `EP-006`);
- strings inside the trust snapshot (`issuer_id`, `authority` entries and so on), which are governed by the snapshot rules and escaped by the serializer (vector `TF-003`).

If a component wants to record a hash of human-readable metadata as evidence, that hash is a separate evidence value outside this binding; it must never be added as a member or mixed into `binding_digest`. This document defines no such hash.

## 4. Two forms of the object and when an identity is complete

Contract 4.2: the registry produces the object with `activation_ref = null`; the enforcing gate fills `activation_ref` from its own log; the claim-carried form requires a non-null `activation_ref`; **the digest is always computed over the completed form.** Contract 4.1 says no `null` appears in a completed binding. These are consistent only if there are two forms, which this document makes explicit:

| Form | `activation_ref` | Produced by | `binding_digest` |
|---|---|---|---|
| Registry form (incomplete) | `null` | the Registry projection from verified inputs | **never computed** |
| Completed form | `sha256:` + 64 lowercase hex | the enforcing gate | computed over the completed form only |

A null `activation_ref` in a form presented for digesting, carriage or guard comparison is refused (`BI-NULL-ACTIVATION-REF`, `field_type_invalid`). Completion changes exactly one member; the vectors `BV-001` (completed) and the member-mutation control prove that completion changes the digest.

Completeness by registry decision kind (EXT-S1-5 card, criterion 5; to be implemented later, specified here):

| Decision kind | Identity |
|---|---|
| `applied`, `applied_deny_all` | registry-form identity populated from verified inputs (every member except `activation_ref`); `effective_policy_digest` over the composed effective payload (deny-all: the explicit empty-set payload, `EP-004`) |
| `overlay_not_applied` (optional participation) | no policy applied, so no binding is produced; the evidence carries `applied=false` and the original `registry_code` |
| `refused` (required participation, `required_policy_unavailable`) | **never complete.** Failure evidence may carry the already-parsed or already-verified identity fields that `ocs-registry-failure-detail/1` lists (`selection_id`, `epoch`, `selection_digest`, `record_id`, `record_version`, `record_digest`, `trust_snapshot_version` and so on) but **no `binding_digest` and no `effective_policy_digest`**; absence of `binding_digest` is the incompleteness signal, no separate flag is added |

## 5. Serialization rules (exact)

These restate contract 4.1 (pinned) and fix what it leaves implicit. Where this section says more than 4.1, the extra is labelled **(proposed)** and listed in section 11.

### 5.1 Identifier grammar (Architect ACCEPTED)

The eight identifier members (`record_id`, `selection_id`, `family`, `consumer_id`, `operation`, `scope.tenant`, `scope.institution`, `scope.authority_domain`) must match, on the raw string:

```
\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z
```

- The classes are explicit ASCII ranges: no `\w`, `\d`, locale, `re.IGNORECASE` or any Unicode-aware class. Use end-of-string (`\Z`, or full-match), never `$`: Python `$` accepts a trailing newline (`BI-TRAILING-NEWLINE`; the test asserts the hazard).
- 1 to 128 characters; the first is `A-Z`, `a-z` or `0-9`; the rest are those plus `.`, `_`, `:`, `-`.
- ASCII only. **Unsupported Unicode is rejected, never normalized**: no NFC or NFKC, no case folding, no trimming, no transcoding, no silent rewriting, no replacement. Fullwidth forms, homoglyphs (Cyrillic, Greek, U+2010), case-fold hazards (Kelvin sign U+212A, dotless i U+0131, long s U+017F), NFC and NFD forms of the same text, zero-width and byte-order-mark characters, NBSP, NUL, newline, DEL, `*`, `/` and `%` are all refused `field_invalid`. Both NFC and NFD of the same text are refused, so no component can conflate them.
- Case is significant and preserved: `tenant-a` and `Tenant-a` are two valid, distinct identifiers with different digests (`BV-005`).
- Comparison anywhere (guard, evidence, tests) is exact byte equality of the strings.
- This is a V1 interoperability restriction on canonical identity members only (section 3.2 lists what it does not cover).

### 5.2 Value rules

- Integers (`record_version`, `selection_epoch`, `trust_snapshot_version`): JSON integers in base 10, no sign, leading zero, fraction or exponent, not `bool`, at least 1. **Upper bound (proposed, interim): 2147483647 (2^31 - 1)**, equal to the existing registry `MAX_INT` already applied to record version and epoch; contract 4.1 states no maximum (OQ-1).
- Digest members (`record_digest`, `selection_digest`, `effective_policy_digest`, `activation_ref`, `trust_snapshot_fingerprint`): match `\Asha256:[0-9a-f]{64}\Z` exactly, 71 characters, lowercase hex only. Uppercase hex, any other prefix case or algorithm, missing or doubled prefix, 63 or 65 hex digits, whitespace and non-ASCII digits (fullwidth) are refused. A component never lowercases, trims or re-prefixes a digest.
- `binding_profile`: the constant `ocs-policy-binding/1`, exact bytes.
- No `null`, float, boolean or array appears in a completed binding. `scope` is an object with exactly `authority_domain`, `institution`, `tenant`.

### 5.3 Canonical JSON and byte encoding

`canonical_bytes` is exactly the registry profile (`registry_successor/common.py` `canonical_bytes`, quoted by contract 4.1): JSON text, object keys sorted, separators `,` and `:` with no whitespace, `ensure_ascii=True`, encoded as UTF-8.

- **Field ordering.** Keys are sorted by Unicode code point (identical to byte order for the ASCII key names) at every nesting level including `scope`. The declared order in section 3 is documentation only and never affects the bytes. The sorted top-level order is: `activation_ref`, `binding_profile`, `consumer_id`, `effective_policy_digest`, `family`, `operation`, `record_digest`, `record_id`, `record_version`, `scope`, `selection_digest`, `selection_epoch`, `selection_id`, `trust_snapshot_fingerprint`, `trust_snapshot_version`; `scope` sorts `authority_domain`, `institution`, `tenant`.
- **String escaping (needed for non-binding values such as snapshot strings).** `"` is `\"`, `\` is `\\`, U+0008, U+000C, U+000A, U+000D, U+0009 are `\b`, `\f`, `\n`, `\r`, `\t`; every other code point outside U+0020 to U+007E, **including U+007F (DEL)**, is written `\uXXXX` with **lowercase** hex; code points above U+FFFF are written as a UTF-16 surrogate pair of two `\uXXXX` escapes. `/` is not escaped. A serializer that emits raw UTF-8 (the Control Plane commitment profile uses `ensure_ascii=False`) differs for any non-ASCII value (`TF-003` carries the divergent bytes as a negative control). Binding identifiers and digests are pure ASCII from the permitted set, so they never need an escape and the two profiles coincide for a valid binding (contract 4.1).
- Integers are written as base-10 digits only. No trailing newline, no byte-order mark. The output is 7-bit ASCII (the largest valid vector, `BV-003`, is 1747 bytes).
- **Recompute, never relay.** A component recomputes `canonical_bytes` from the decoded members and never hashes received text. Input JSON may use any standard escapes or key order and any insignificant whitespace; the decoded members determine the bytes (`BV-011`, `BV-012`, `BV-013` all equal `BV-001`). A duplicate key at any depth is refused even with an equal value (`BI-DUP-TOPLEVEL-SAME`), including a duplicate revealed only after unescaping the key name (`BI-DUP-ESCAPED-KEY`).

### 5.4 Digest construction and domain separation

```
binding_digest = "sha256:" + lowercase_hex( SHA-256( P || canonical_bytes(binding) ) )
P = the 30 bytes of the ASCII text  ocs-reg/r08-v2/policy-binding  followed by one LF (0x0a)
P (hex) = 6f63732d7265672f7230382d76322f706f6c6963792d62696e64696e670a
```

The prefix is not JSON, not part of `canonical_bytes`, and is never emitted. Hashing without the prefix, with the prefix minus its newline, or with a changed prefix yields a different digest (each is asserted by the mutation control). The same hashed-prefix rule does **not** apply to `effective_policy_digest` or `trust_snapshot_fingerprint`, which are plain registry `digest` values (`"sha256:" + hex(SHA-256(canonical_bytes(x)))`, no prefix) per contract 4 and 5.

### 5.5 Validation order and refusal codes

A multi-defect input is refused with the first failing check in this fixed order, so every implementation reports the same code and member for the same input (`BI-MULTI-*` vectors fix the order):

1. parse; 2. document is an object; `scope` is an object; 3. member set, missing first, in sorted path order (`scope.*` paths are `scope.authority_domain`, `scope.institution`, `scope.tenant`); 4. member set, unknown; 5. member types, in sorted path order; 6. member values, in sorted path order.

No new codes are introduced: every refusal below is an entry of the 48-code `CODES_V2` map (section 8). Contract 4.1 names `field_invalid` explicitly only for identifiers; the other assignments are **proposed from existing codes** (OQ-2) and each vector marks them.

| Defect | Code | Layer |
|---|---|---|
| input not text | `input_not_text` | parse |
| document over 65536 bytes (registry loader limit) | `input_too_large` | parse |
| not JSON, trailing text, BOM prefix, leading-zero integer, trailing comma | `json_malformed` | parse |
| duplicate key at any depth | `json_duplicate_key` | parse |
| float, exponent, `NaN`, `Infinity` | `json_number_unsupported` | parse |
| nesting deeper than 8 | `json_nesting_too_deep` | parse |
| document is not an object | `field_type_invalid` | shape |
| a member is absent (including `scope` and any `scope.*`) | `field_missing` | shape |
| an unlisted member (including `scope.*`) | `field_unknown` | shape |
| wrong JSON type, `bool` as integer, `null`, non-object `scope` | `field_type_invalid` | shape |
| identifier outside the grammar; digest malformed; wrong `binding_profile`; integer below 1 or above the bound | `field_invalid` | shape |
| carried `binding_digest` differs from the recomputed one (guard) | `digest_mismatch` (proposed) | integrity |

## 6. `effective_policy_digest` (proposed preimage)

Contract 4 says: `digest` of the canonical composed effective payload (record payload composed with the caller policy by `min`). It gives no worked example, and the contract's section 9 vector shows only the resulting digest. **(Proposed, OQ-3.)** The preimage is the composed effective payload object holding **exactly the family payload keys of contract section 2 and nothing else**:

- `f1ab-local-execution-allowlist`: `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`, each a sorted, duplicate-free list of strings (an explicit deny-all dimension is `[]`);
- `f4-control-plane-age-bounds`: `status_max_age_seconds`, `approval_max_age_seconds`, integers (the composed `min(caller, registry)` values);
- `f5-action-class-age-bounds`: `class_status_max_age_seconds`, an object of action class to integer seconds.

The digest is plain `"sha256:" + hex(SHA-256(canonical_bytes(payload)))` (no domain prefix). The family is **not** in the preimage because it is its own binding member. No registry bookkeeping (selection id, epoch, caller digest, validity window) is in the preimage. Because the value depends on the caller policy, it is evidence only. Vectors `EP-001` to `EP-006`, including a key-order variant (`EP-002` equals `EP-001`), an explicit deny-all (`EP-004`) and a non-ASCII entry (`EP-006`), pin this construction; `BV-014` embeds `EP-004` in a binding.

## 7. Trust snapshot identity

`trust_snapshot_version` is the verified `TrustSnapshot.version`. `trust_snapshot_fingerprint` is contract 5, pinned: the plain registry `digest` (no prefix) of the normalized snapshot object `{snapshot_id, version, valid_until, issuers, revoked_key_ids, revoked_selections, min_epochs}` with: `issuers` sorted by `key_id`, each `{key_id, issuer_id, alg, public_key (lowercase hex), authority}`; `authority` a list of five-element arrays `[consumer_id, tenant, institution, authority_domain, operation]` sorted lexicographically by array (code-point string comparison); `revoked_key_ids` sorted; `revoked_selections` sorted as `[selection_id, epoch]` by `(selection_id, epoch)` with the epoch compared **as an integer** (`["sel-old-1", 2]` before `["sel-old-1", 10]`, asserted by the test); `min_epochs` sorted as `[selection_id, floor]` by `selection_id`. Empty collections are present as `[]`, never omitted or null (`TF-004`). Duplicates (issuer `key_id`, `revoked_selections` pair, `min_epochs` selection id, `revoked_key_ids` entry) refuse `trust_snapshot_invalid` (`TI-001` to `TI-004`). `TF-001` reproduces the contract's printed fingerprint from the contract text; `TF-002` is the unsorted-input case; the test also mutates twelve snapshot fields and requires twelve distinct fingerprints.

The fingerprint's input strings are not ASCII-restricted. It is computed by the Registry serializer (`ensure_ascii=True`). A component that only carries the fingerprint string never recomputes it; a component that recomputes it must use this serializer (section 5.3).

## 8. The code outcome map (reused, not extended)

The outcome map is `docs/p1-extraction-plan/data/ld02-outcome-map.json` (pinned above): **48 codes** = the 46 `r08-v1` `CODES` entries plus exactly `trust_snapshot_version_stale` (layer `trust`) and `selection_withdrawn` (layer `disposition`) (contract 3.3, ADR D-02; declared as `CODES_V2` by `EXT-S1-2`). This work **invents no code**. The identity validators above use ten of the existing codes: `input_not_text`, `input_too_large`, `json_malformed`, `json_duplicate_key`, `json_number_unsupported`, `json_nesting_too_deep`, `field_type_invalid`, `field_missing`, `field_unknown`, `field_invalid`, plus the guard `digest_mismatch` and the snapshot `trust_snapshot_invalid`. The vector file embeds the 48 codes with their layers and the test requires them to equal the map and every vector code to be a member.

Contract points that the later `EXT-S1-5` source change implements and that this document carries forward unchanged: the completeness test iterates **every `CODES_V2` entry (48)** and fails on any unmapped code; no required-policy code maps to an authorizing disposition (the map records `can_authorize_action: false` for every code); distinct codes keep distinct cause fields and the original `registry_code` travels as structured negative evidence (`ocs-registry-failure-detail/1`); `selection_withdrawn` and `trust_snapshot_version_stale` stay distinct causes; no policy decision is derived from message text. Note that the map's own `meta` text still says the two v2 codes are `in_CODES false until EXT-S1-2 declares CODES_V2`; `registry_successor/v2_codes.py` now declares `CODES_V2`, so that sentence is historical (not edited here; the map is pinned and unchanged).

## 9. The vectors

File: `docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json` (ASCII-only JSON, schema `ocs-ext-s1-5-policy-identity-vectors/1`, status `BUILDER_TESTED`).

| Set | Count | Content |
|---|---|---|
| `valid` | 14 | each carries `input_json`, `canonical_bytes_hex`, `canonical_ascii`, `binding_digest` and an unprefixed-digest control; includes the contract's worked example (`BV-001`, reproduced from the contract text), min and max length, punctuation, case-variant distinctness, F4 and F5 families, integer boundaries, digest boundaries, reordered, pretty-printed and `\u`-escaped inputs that must equal `BV-001` |
| `invalid` | 87 | each carries `category`, `input_json` or `input_hex`, and `expected` `{result: refuse, code, layer, member}`; categories: non-ASCII, homoglyph, fullwidth, case-fold hazard, NFC/NFD, whitespace, empty, over-length (129), bad leading character, control (NUL, newline, DEL), out-of-set ASCII, uppercase hex, wrong prefix, short and long digest, non-hex, wrong profile, missing and extra members (top level and `scope`), wrong type (including `bool`, `null`, string integer, non-object `scope`, array document), non-canonical integer (zero, negative, `-0`, float, exponent, leading zero, `NaN`, over bound), duplicate keys (top level, nested, same value, escaped), malformed JSON, BOM, nesting depth, null `activation_ref` (registry form), and validation-order cases |
| `identifier_matrix` | 34 bad values x 8 identifier members = 272 derived refusals | every bad identifier value in every identifier member |
| `guard_digest_checks` | 4 | carried `binding_digest` equal, one hex digit off, unprefixed, uppercase |
| `effective_payloads` | 6 | section 6 preimages and digests |
| `trust_snapshots` / `trust_snapshots_invalid` | 4 / 4 | section 7 fingerprints, unsorted input, non-ASCII with divergent-serializer control, empty collections; duplicate refusals |

The test (`tests/test_ext_s1_5_vectors.py`) contains its own hand-written canonical serializer (not `json.dumps`), cross-checks it against `json.dumps(sort_keys, compact, ensure_ascii=True)`, recomputes every vector, requires exact bytes, digests, refusal code and member, runs a mutation control (changing any single member of every valid binding to another valid value changes the digest; removing any member or adding one refuses; no-prefix, wrong-prefix and truncated-prefix digests differ; twelve snapshot-field mutations give twelve distinct fingerprints), asserts the 48-code map and the section pins, and, when Node.js is present, recomputes every valid binding, effective payload and snapshot in a second language and requires byte equality. The test imports nothing from the registry packages and is not a shared module.

Evidence level: a Python reference, an independent Node.js recomputation and the contract's own printed digests (`BV-001`, `TF-001`) agree. **No Control Plane serializer has been run against these vectors** (no Control Plane code was available to this work); contract 4.1's claim that the Control Plane `commitment` serializer is byte-identical for ASCII input remains a source reading (ADR D-15) until `EXT-S4-4` runs it.

## 10. Consumers and handoff

Nothing below is implemented here. These are the obligations the later PRs take on against these vectors. The vector file is data owned by the Registry contract owner: consumers copy it into their repositories with its SHA-256 recorded and must not edit it; a change is a new schema version.

**Runtime (EXT-S2-x, and the Runtime-owned destination guard `EXT-S4-2`).**
1. Implement the published profile independently (section 5): identifier grammar, ASCII rule, value rules, canonical serializer, domain-separated digest, validation order. **Do not import registry code.** Reproduce every `valid` vector byte for byte (`canonical_bytes_hex`, `binding_digest`) and refuse every `invalid` vector with a typed refusal; map codes to Runtime reasons per the outcome map (`registry_binding_rejected`, `registry_input_rejected`) while keeping the registry code in `detail.registry_code`.
2. At the guard (contract 7.4): refuse a binding failing section 5 before any comparison; refuse null `activation_ref`; **recompute `binding_digest` from the members and never trust a carried digest string**; compare `selection_id`, `selection_epoch`, `selection_digest`, the record triple and `activation_ref` to the trusted row by exact equality; **do not compare `effective_policy_digest` to durable state**; keep it as claim-bound evidence in the effect row.
3. Do not normalize, case-fold, trim or re-encode any member anywhere (including when building the scope key). The identifier grammar permits `:`, `.` and `-`, so a delimiter-joined scope key is ambiguous; use an unambiguous encoding (OQ-5).
4. `S2-2` narrowing adapter computes no identity; if it exposes the composed effective sets, `EP-001` to `EP-006` fix the `effective_policy_digest` preimage a Runtime gate must reproduce when it builds the completed object from a registry-form identity.
5. Put the vector file (hash-pinned) in the Runtime test corpus and run it in the Runtime core job.

**Control Plane (EXT-S3-x, `EXT-S4-0`, `EXT-S4-4`, `EXT-S4-5`).**
1. `EXT-S4-0` consumes this member list and specializes only effect-boundary requirements; **a divergent member list is a stop** (card EXT-S1-5, "stop if the `S4-0` member list diverges"). It may refine the `activation_ref` log-entry layout but must keep the properties of section 3.1.
2. `EXT-S4-4` carries the completed binding as a declared optional claim field (omitted when absent) under the successor claim profile; the claim commitment covers it. Run **every valid vector through the Control Plane `commitment` serializer** and require byte equality with `canonical_bytes_hex`; run every invalid vector and require refusal **before** commitment, because `ensure_ascii=False` would otherwise diverge from the registry bytes for any non-ASCII member (this is exactly what the ASCII restriction prevents).
3. A claim-carried binding with null `activation_ref` is refused; a claim with no binding stays byte-identical to today (contract 4.3).
4. The Control Plane only carries `trust_snapshot_fingerprint` and `effective_policy_digest` as opaque validated digest strings. It must not recompute the fingerprint with `ensure_ascii=False` (section 7).
5. The approval-generation mechanism (ADR D-16) is `EXT-S3-4`'s; nothing here defines it and no member for it is added to the binding.

**Both.** No component keeps a second `activation_ref` form. Guard and evidence code use the codes in section 5.5 and the 48-code map; any code not in the map is a contract change. Each side adds a mutation test of its own (changing any single member changes the digest; adding or removing one refuses).

**Registry (later `EXT-S1-5` source PR, after `EXT-S1-3` and `EXT-S1-4`).** Implements the projection from verified inputs, the effective-digest function (section 6), the fingerprint hook (section 7) and the 48-code map, and replaces this file's reference serializer test with a test that checks the shipped module against the same vectors (the vectors, not this reference, are the oracle).

## 11. Ambiguities found in the existing contract (recorded, not resolved by fiat)

1. **Null versus complete.** Contract 4.1 forbids `null` in a completed binding; 4.2 has the Registry produce `activation_ref = null`. Reconciled here as two forms (section 4). The contract should say so in one sentence when next edited.
2. **Typed codes.** 4.1 requires "each refused with a typed code" but names only `field_invalid` (identifiers). Mapping the other defects to existing codes is a proposal (section 5.5, OQ-2).
3. **Effective payload preimage** is described in words only, with no worked example (section 6, OQ-3).
4. **Integer upper bound** is absent from 4.1 although the registry already bounds epoch and record version at 2^31 - 1 (OQ-1).
5. **ASCII restriction versus statement validation.** The existing statement validators accept Unicode scope tokens (`valid_token`, scope fields) and lowercase 3 to 64 character identifiers for the others; 4.1 says v2 refuses non-ASCII but does not say at which layer. A signed statement with a non-ASCII tenant can verify yet cannot be projected into a binding (OQ-4).
6. **Card title.** The `EXT-S1-5` card heading says "46-code outcome map"; its criterion and ADR D-02 say 48 (46 plus two). This document uses 48.
7. **Stale map note.** The outcome map `meta` still says the v2 codes are `in_CODES false until EXT-S1-2 declares CODES_V2`; `CODES_V2` now exists. Historical, harmless.
8. **Control Plane serializer equivalence** is a source reading (ADR D-15), not a tested result, until `EXT-S4-4`.

## 12. Open questions for Architect

- **OQ-1 Integer ceiling.** Confirm 2147483647 (the existing registry `MAX_INT`) as the upper bound for `record_version`, `selection_epoch` and `trust_snapshot_version` in the binding, or give another value. Contract 4.1 states no maximum and non-Python implementations need one (JSON numbers beyond 2^53 are not interoperable). Vectors `BV-008` and `BI-INT-OVER-MAX` are marked interim.
- **OQ-2 Typed codes for non-identifier defects.** Confirm the section 5.5 mapping to existing codes (missing to `field_missing`, extra to `field_unknown`, wrong type to `field_type_invalid`, bad digest, profile or integer to `field_invalid`, guard digest difference to `digest_mismatch`), or name different existing codes. No new code is requested.
- **OQ-3 `effective_policy_digest` preimage.** Confirm the preimage is the family-payload object only, plain `digest` with no domain prefix, sorted lists, no family or bookkeeping inside (section 6). A different preimage changes `EP-*` and `BV-014` only.
- **OQ-4 Where the ASCII rule is enforced.** Confirm that a verified statement whose scope token is outside the identifier grammar remains a verified statement, and that the binding projection refuses it `field_invalid` (a required scope refuses and never falls back; an optional scope reports `overlay_not_applied`), rather than tightening the v2 statement validators now (a shared-core change that belongs after `EXT-S1-3`).
- **OQ-5 Scope-key construction.** Contract 7.4 line 2 builds a "scope key" from seven members, but the identifier grammar allows `:`, `.`, `_` and `-`, so a delimiter-joined key is ambiguous (for example consumer `a:b` with tenant `c` versus consumer `a` with tenant `b:c`). Please rule, in `EXT-S4-0`, on an unambiguous key (this document suggests the canonical JSON of the ordered seven-member array, hashed or not). Nothing in this document builds a scope key.

## 13. What this document does not do

It adds no code, constant, module, schema, workflow or dependency; edits no existing file; implements no part of `EXT-S1-5`'s source change; defines no approval-generation member, claim field name or log-entry layout; makes no qualification, release or publication claim; and does not claim that Runtime or Control Plane conform.
