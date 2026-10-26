# Core verifier hardening: canonical signature text and key admission

Status: SECURITY-HELD. BUILDER_TESTED. AI-reviewed only (not independent cryptographic review, not Tier 1). Not merged until
Architect security review. Trust-root activation remains held. Authority: Architect Batch 6 ruling 11, separate from PR #26.

## 1. Canonical base64 signature text

Contract `docs/r08-s01-contract.md` section 3 says only "standard base64 text". It does not state the canonical spelling,
so this PR adopts the plain reading: RFC 4648 section 4, padding present, no whitespace or line breaks, unused trailing
bits zero. Implemented by decode then re-encode and compare (`registry_successor/canonical_b64.py`).

Why: `base64.b64decode(..., validate=True)` accepts 16 spellings of every 64-byte signature (the last character carries
four unused bits). That is a second spelling of the same signed envelope.

Scope (Architect ruling): canonical spelling is enforced on the **r08-v2 (mandatory) path only**. The frozen r08-v1 legacy path
keeps the exact origin/main rule (`base64.b64decode(..., validate=True)`; a non-canonical spelling with non-zero trailing bits that
decoded and verified before still verifies, and detail strings are unchanged). Pinned by
`test_m3_legacy_r08_v1_path_keeps_noncanonical_base64_exactly_as_origin_main`.

Behaviour on the r08-v2 path: a signature spelled any way but canonical now refuses `signature_invalid` with detail
`signature is not canonical base64`. Undecodable text keeps `signature is not valid base64`; a canonical signature that
fails verification keeps `signature does not verify`. No reason code is added (CODES stays 46). Non-`str` signature values
(including `bytes`) refuse on that path; parsed envelopes only ever carry `str`. The v1 golden corpus is unchanged and passes.

Open question for the Architect: the contract text should state the canonical spelling explicitly. This PR does not edit the
hash-pinned contract file.

## 2. Key admission at the trust boundary (mandatory on the r08-v2 path)

Architect ruling B: public-key admission is MANDATORY on the r08-v2 verification path.

`verify_selection(..., key_admission=None, contract_version="r08-v1")` and `verify_and_decide(..., key_admission=None,
contract_version="r08-v1")`. Admission is **mandatory unless `contract_version` is exactly the legacy string `r08-v1`**
(fail closed: the legacy path requires `type(x) is str` AND equality, so `r08-v2`, any other string, `None`, a non-string, a `str` subclass or an equal-comparing object such as `UserString("r08-v1")`, and `"R08-V1"` / `"r08-v1 "` all select the mandatory path),
and also whenever the selection envelope itself says `r08-v2`. On the mandatory path the built-in Ed25519 check
(`inspect_ed25519_key`) runs on every issuer key when the trust snapshot is admitted, whether or not a callback is supplied.
The optional `key_admission` policy `(alg, public_key) -> bool` can only ADD refusals: a callback that returns `True` for a
small-order key does not admit it; a callback that raises, or returns anything but exactly `True`, refuses. A refused key makes
the snapshot `trust_snapshot_invalid` (existing code) and authenticity is not evaluated.

The legacy `r08-v1` path keeps its opt-in behaviour (`None` = no admission, a supplied callback still gets the built-in check),
because the frozen v1 golden corpus and fixtures use non-32-byte placeholder keys and must not change. There is no r08-v2
envelope parser in the repository yet (`selection.py` accepts only `r08-v1`); the gate is therefore placed at the verifier so
that the v2 parser (EXT-S1-5/6) inherits it with no further wiring, and the v2 path is exercised here by passing
`contract_version="r08-v2"` with a v1-shaped envelope.

### 2.0-pre The single legacy skip (audit, Batch 7)

`verify._admission_mandatory` returns False (admission NOT mandatory) in exactly one situation: the `contract_version`
argument is an exact built-in `str` (`type(x) is str`) equal to "r08-v1" AND the parsed selection envelope is either absent
(a structurally invalid selection, refused earlier) or a plain `dict` whose `contract_version` is an exact `str` "r08-v1". Why it
exists: the frozen r08-v1 golden corpus and fixtures use non-32-byte placeholder keys, and r08-v1 behaviour
(including the base64 rule) must stay as on origin/main. Everything else is mandatory, and the type test runs before any equality so `__eq__`, `__str__`, `__hash__`
and `__class__` tricks are never consulted:

| `contract_version` argument | result |
|---|---|
| exact `str` "r08-v2" | mandatory |
| `UserString("r08-v2")`, `str` subclass "r08-v2", `bytes` b"r08-v2" | mandatory (not an exact `str`) |
| `None`, `int`, "" , any other string | mandatory |
| `UserString("r08-v1")`, `str` subclass "r08-v1", b"r08-v1" | mandatory (equal-looking but not an exact `str`) |
| `str` subclass or instance with lying `__eq__`/`__str__`/`__class__` | mandatory (type checked first) |
| exact `str` "r08-v1" with an envelope declaring "r08-v2", or any non-exact-`str` envelope version (missing, `None`, `bytes`, `int`, `UserString`) | mandatory (envelope overrides the argument) |
| exact `str` "r08-v1" with an envelope that is a `dict` subclass, a list, a `str`, an `int` or any other non-exact-`dict` (selection `ok`) | mandatory (fail toward mandatory) |
| exact `str` "r08-v1" with a selection whose `ok` is exactly `False` and that has NO envelope (the parser's failure shape; structurally refused) | legacy (golden-corpus compatibility only; refused at the structural layer anyway) |
| exact `str` "r08-v1", no envelope, `ok` anything else (`None`, `1`, `"yes"`, `[1]`) | mandatory (such a selection would be evaluated, so it must not skip admission) |
| exact `str` "r08-v1" with an exact `dict` envelope whose `contract_version` is an exact `str` "r08-v1" | legacy: callback-optional (the only skip for a selection that would be evaluated) |

**Exact types and a single read for every field the mandatory path reads.** The mandatory decision is taken ONCE from the caller's
original objects; then `_verify` replaces the selection, record, context and `now` with private copies (`_private_selection`,
`_private_record`, `_private_context`, `_private_now`) and `_normalize_trust` returns `_private_trust`'s copy. Every later layer
(admission, the caller callback, `verifier.verify`, authority, scope, time, revocation, epoch, the report) reads only those
copies. Subclasses, stateful objects and lying `__eq__`/`__lt__`/`__iter__`/`utcoffset` therefore cannot show one value to one
decision and another to the next. Anything not matching its rule is a typed refusal (`trust_snapshot_invalid` /
`trust_snapshot_malformed`, `field_invalid`, `selection_scope_mismatch`, `time_unavailable`, `composition_record_invalid`);
the legacy path keeps its original code and is not given these rules (it is not hardened against hostile objects).

| Object . field | type rule (mandatory path) | read |
|---|---|---|
| TrustSnapshot | `type(x) is TrustSnapshot` | fields read once into locals |
| .snapshot_id, .valid_until | exact `str` (valid token / strict timestamp) | once |
| .version | exact `int` (not `bool`, not a subclass), >= 1 | once |
| .issuers | exact `list` or `tuple` | one `tuple()` copy |
| IssuerEntry | `type(x) is IssuerEntry` | once, rebuilt as a private entry |
| .key_id, .issuer_id, .alg | exact `str` | once |
| .public_key | any type is read once; only exact non-empty `bytes` is admitted (`key_type` / `key_length` otherwise, any alg) | once |
| .authority | exact `list` or `tuple` of exact `AuthorityGrant`, rebuilt as a tuple | once |
| AuthorityGrant fields (5) | exact `str` each, rebuilt | once |
| .revoked_key_ids | exact `list`/`tuple`/`set`/`frozenset` of exact `str` | one copy -> `frozenset` |
| .revoked_selections | exact container of exact 2-`tuple` (exact `str`, exact `int`, not `bool`) | one copy -> `set` |
| .min_epochs | exact `dict`, or exact `list`/`tuple` of exact 2-tuples; key exact `str`, floor exact `int` >= 1, no duplicates | one copy -> `dict` |
| selection.ok | must be exactly `True` or the selection is a structural refusal | once |
| selection.code | exact `str` in `CODES`, else `field_invalid` | once |
| selection.statement, .signatures | deep copy of exact JSON data only: `dict` (exact-`str` keys), `list`, `tuple`, `str`, `int`, `bool`, `None`; floats, subclasses, sets, bytes, other objects refused; depth <= 32; a container reached twice (cycle or shared reference) is refused; at most `MAX_JSON_NODES` = 10,000 nodes in total per copy (work is linear and bounded; a parsed document never shares containers and the parser caps are far lower); statement must be an exact `dict`, signatures an exact `list`/`tuple` | each node once |
| selection.statement_digest | exact `str` | once |
| selection.envelope | read once, only to choose the path (exact `dict` + exact-`str` "r08-v1" or mandatory) | once |
| record result `.ok`, `.record`, `.record_digest` | `ok is True`; `record` deep exact-JSON copy that is an exact `dict`; digest exact `str`; otherwise a refused record | once |
| ExpectedContext | `type(x) is ExpectedContext` with 5 exact `str` members, rebuilt | once |
| `now` | `type(x) is datetime.datetime`, aware; `utcoffset()` called once, normalised to a plain UTC `datetime` | once |

Accepted limits:
- **Legacy path is not hardened (M1 residual, stated plainly).** A hand-built selection with an exact-`dict` envelope declaring
  exactly "r08-v1", or with a stateful or lying `ok`, takes the unhardened legacy path whenever the caller passes "r08-v1" or
  omits `contract_version`. Nothing in this PR protects that call; the v2-only wrapper decision (M1) is what closes it.
- **Half-built objects.** On the mandatory path an `object.__new__` TrustSnapshot or IssuerEntry is a typed
  `trust_snapshot_invalid` / `trust_snapshot_malformed`; a half-built ExpectedContext is `selection_scope_mismatch`. (A half-built
  selection or record object is a structural / record refusal.) Any other unexpected exception still fails closed as the
  existing untyped `field_invalid` "internal verification error".
- The `verifier` and the caller `key_admission` callable are trusted code and are not copied; exact built-in
classes can still be monkey-patched or mutated through `object.__setattr__`, and nothing here defends against another thread
doing that; a hostile selection object handed to the legacy path (exact `str` "r08-v1" with a falsy-`False` `ok`) is outside
this hardening by design.

**M1: OPEN ARCHITECT DECISION (not implemented; default unchanged).** `contract_version` defaults to "r08-v1". An envelope that
declares "r08-v2", or declares any odd, missing or non-exact-`str` version, already forces the mandatory path whatever the argument
says, so a future v2 parser inherits the gate if its envelopes carry `contract_version`. Residual: a caller that omits the
argument and hands over an envelope declaring exactly "r08-v1" is treated as legacy, which is correct for a genuine r08-v1
selection. Today `selection.py` refuses non-r08-v1 envelopes and no code calls the verifier with a v2 selection, so this is not
reachable now. Changing the default would break the legacy callers and the golden runner. **Decision requested: add, before
any v2 parser lands, a v2-only wrapper entry point that hardwires `contract_version="r08-v2"` (e.g. `verify_selection_v2` /
`verify_and_decide_v2`, or a required keyword on a new v2 entry point), and make every v2 call site use it.** No code for it is in
this PR.

A callback can only add refusals on every path, and the built-in check is never disabled by omitting it. No reason code is
added. Pinned by `test_every_contract_version_but_the_exact_legacy_str_is_mandatory`,
`test_envelope_declared_v2_beats_a_legacy_argument_and_odd_envelope_values_are_mandatory`,
`test_the_only_non_mandatory_path_is_exact_str_r08_v1_argument_with_an_exact_str_r08_v1_envelope` and the mutants
`legacy_equality_only`, `legacy_isinstance_str`, `envelope_equality_only`, `mandatory_ignores_envelope_v2`.

### 2.0-adapter Adapter coordination (PR #26 seam; docs only, no #26 code changed here)

- Seam: `verify._verify` normalizes the snapshot with `_normalize_trust(trust_in, mandatory)` and then calls
  `_admission_failure(trust, key_admission, mandatory)` before any other trust or authenticity layer; signature checking
  (`_authenticity`, which calls `verifier.verify(alg, public_key, message, signature)`) runs only after the snapshot passed.
- Order is fixed: (1) built-in `inspect_ed25519_key` always runs first on the mandatory path (and on the legacy path whenever a
  policy is supplied); (2) then the caller policy. The Ed25519 adapter's `acceptable_public_key` composes at step (2) through
  `key_admission=compose_key_admission(adapter.acceptable_public_key)` (or any callable `(alg, public_key) -> bool`). It can only
  further restrict; returning `True` never admits a key the built-in check refused, and a raise or non-`True` result refuses.
- Not done here: on-curve decompression, prime-order subgroup and mixed-order checking. That is the adapter's job (PR #26) and
  this PR does not perform or claim it. Until it is composed in, mixed-order keys pass admission and signatures made with them MAY
  be accepted by a verifier that does not itself enforce subgroup membership.
- Adapter integration is a separate step after #34 is approved and merged; no code in PR #26 is changed by this PR.

### 2.0 Exact rules checked (`key_admission.inspect_ed25519_key`, pure standard library)

Applied to `alg == "ed25519"` keys, in this order:
1. exact `bytes` type (a `bytes` subclass, `bytearray`, `str`, `None`, int are refused: `key_type`);
2. length exactly 32 (`key_length`);
3. noncanonical encoding: the y coordinate (low 255 bits, little endian) must be below p = 2**255 - 19, so every alias
   y + p (including y = p and the all-ones value) is refused whether or not it decodes to a point (`key_non_canonical_y`);
4. small order, including the identity: the y coordinate must not be one of the five values shared by the eight small-order
   points of edwards25519, for either sign bit: y = 0, y = 1, y = p - 1, and the two order-8 values
   `0x5fc536d8...95e826` and `0x7a03ac92...6a17c7` (`key_small_order`). That refuses the eight canonical small-order encodings
   (identity `01 00..00`, order-2 `ec ff..7f`, the two order-4 and the four order-8 encodings) and the x = 0 sign-bit spellings
   `01 00..80`, `ec ff..ff` that a decoder might reduce to the same point.
Source for the small-order set: RFC 8032 section 5.1.3 (point decoding, rejection of noncanonical y) and the standard list of
the eight small-order points of edwards25519 as used by libsodium `ge25519_has_small_order` and the ed25519-speccheck
("Taming the many EdDSAs") suite. The tests do not copy the list: they recompute the torsion points from the curve equation
by integer arithmetic and compare (`test_small_order_table_matches_independent_arithmetic`).

Not checked here (documented limitation, unchanged): whether a canonical y lies on the curve, and prime-order-subgroup
membership. Mixed-order keys (A plus a small-order point) pass the built-in check and a test pins that. The stricter
`acceptable_public_key` of the Ed25519 adapter (PR #26, unmerged) is to be composed in with `compose_key_admission` after #34
is approved. Until then mixed-order keys and signatures made with them MAY be accepted; PR #26 reports libsodium's signature
check alone accepting mixed-order cases. This PR does not close that gap.

### 2.0a Reason and typed detail (ruling C)

On the mandatory path an empty or wrong-type public key (any algorithm) is an admission failure (`key_length` / `key_type`), not a generic malformed snapshot; legacy normalization is unchanged.

Reason code: `trust_snapshot_invalid` (the existing code; CODES stays 46; the frozen reason-code artifacts are untouched).
Typed detail, in `registry_successor/key_admission.py`:
- `DETAIL_KEY_ADMISSION_INVALID = "key_admission_invalid"`: an admitted issuer key is refused. `detail_cause` is the stable label
  `key_type | key_length | key_non_canonical_y | key_small_order | policy_refused`.
- `DETAIL_TRUST_SNAPSHOT_MALFORMED = "trust_snapshot_malformed"`: any other malformed trust snapshot on the mandatory path.
These are carried as `detail_code` / `detail_cause` on `TypedVerificationReport` (a subclass of `VerificationReport`) and on
`TypedPolicyDecision` (a subclass of `PolicyDecision`). The subclasses are returned only for a refusal that has a typed detail
on the mandatory path (and, on the legacy path, only for a key-admission refusal, which legacy fixtures never trigger). Every
other report or decision is the base class, so the frozen r08-v1 serialized shape is unchanged (golden corpus, 5,000+ cases, passes).
`verify_and_decide` now propagates `detail_code` / `detail_cause`; free-text `detail` is still not surfaced there (pre-existing).

### 2a. Behaviour notes

- **The built-in Ed25519 check always runs** on the mandatory path, and on the legacy path whenever any `key_admission` policy is supplied: `inspect_ed25519_key` is applied
  to every ed25519 issuer key in addition to the policy, and a refusal by either refuses the snapshot. A custom policy can
  therefore only tighten admission; it cannot relax the built-in check (for example to admit test keys). Pinned by a test.
- **Ordering.** An admission refusal outranks `time_unavailable` and `trust_snapshot_expired`: a bad key with an expired snapshot
  reports `trust_snapshot_invalid`.
- **Every issuer is checked.** All issuers in the snapshot are checked, including revoked and non-signing ones, so one bad key
  blocks the whole snapshot. This is fail-closed and intended. Pinned by a test and a mutant.
- **Non-ed25519 algorithms.** `builtin_key_admission` returns `True` for them because the verifier never verifies them
  (`_authenticity` treats any non-ed25519 algorithm as not good); admission is therefore irrelevant to them.
- **Free-text detail is not surfaced by the decision layer.** `verify_and_decide` drops the report `detail` text for every code
  (pre-existing); only the typed `detail_code` / `detail_cause` (section 2.0a) are propagated.

### 2b. Envelope-level spelling is not unique

Canonical spelling applies to the signature that is evaluated. The `signatures` array is outside the signed statement, so an
envelope that carries a canonical signature that verifies plus a non-canonical sibling signature is accepted: the sibling is
ignored because success is "any trusted signer verifies". The non-canonical entry alone is refused. The canonical rule
therefore does not make the whole envelope text unique. Behaviour is unchanged by this PR. If whole-envelope uniqueness is
wanted, a separate decision would reject any non-canonical supported-algorithm signature for a trusted key even when another
verifies.

### 2c. Remaining gate for Architect decision

Mandatory built-in admission on the r08-v2 path is implemented (section 2). Still open before any trust-root activation: a
subgroup-validating check (the PR #26 adapter's `acceptable_public_key`, or equivalent) composed in with `compose_key_admission`
after #34 is approved. Trust-root activation stays held until that is decided and implemented. The contract text should also
state the canonical base64 spelling explicitly (section 1; this PR does not edit hash-pinned contract files).

## 3. Evidence

- 257 behavioural tests (`tests/test_core_security_sig_and_key_admission.py`) and 104 mutation-suite tests (98 source mutants over
  `canonical_b64`, `key_admission`, `verify`, `decision`, all killed, plus probes that pass on unmutated source and one documented
  equivalent mutant), counted from the actual run on this head; full suite 2233 passed. Coverage: 16 noncanonical spellings
  through the full verifier pipeline (v2 strict, legacy stdlib rule); the 8 small-order encodings, the identity, 38 aliases, wrong
  lengths and types, 42 legitimate keys (RFC 8032 vectors 1 and 2 plus 40 derived by plain integer arithmetic); callback omission,
  `lambda: True` bypass attempts, composed and raising callbacks on the mandatory path; `contract_version` fail-closed values;
  envelope-declared r08-v2 and non-exact-dict envelopes; stateful-entry, flipping-`alg`, stateful revoked-list, lying-int floor/epoch/version, statement/signature/record/context/`now` subclass probes (one per row of the field table); valid signatures and
  ordinary callers still applied; negative decisions for required and optional participation; typed-detail distinctness; legacy
  r08-v1 shape unchanged.
- Limits: no real Ed25519 library is used in these tests; point arithmetic is a test-local transcription; only CPython.
