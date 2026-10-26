"""EXT-S1-5: canonical effective-policy identity for `r08-v2` (production module).

Implements docs/ext-implementation/ext-s1-5-effective-policy-identity-spec.md and is checked against
docs/ext-implementation/data/ext-s1-5-policy-identity-vectors.json (the vectors, not the test reference, are the oracle).

Scope of this module (and only this):
  * a syntax-first strict loader for binding and effective documents (spec 5.5.1, 5.5.2); it does NOT reuse `common.load_document`;
  * the canonical JSON serializer and the three domain-separated digests: binding, effective policy, scope key (spec 5.3, 5.4, 5.7, 6);
  * the 15-member completed-binding validator, identifier grammar and per-field integer ranges (spec 3, 5.1, 5.2, 5.5);
  * the trust snapshot normalizer and fingerprint (spec 7);
  * the scope-token projection and the projection-stage refusal effect (spec 5.6);
  * the module-owned four-row `r08-v2` effective-payload table, from which `family_version` is DERIVED and never accepted (spec 6, ruling N-3);
  * the typed refusal mapping of spec 8.1 for the codes of `CODES_V2_REV2` this package owns (the 48 of revision 1 that apply, plus the three ruled additive
    codes, Amendment 1); the withdrawal and snapshot-floor rows stay absent until their owning contracts and evaluators exist (ruling 4.4);
  * a pure six-member identity comparison (`compare_binding_identity`, ruling 4.3) and the ordered `verify_carried_binding_digest`;
  * the Registry-side adapter from the verifier's `TrustSnapshot` object (`trust_snapshot_from_verified`, ruling 4.6).

Hostile-input boundary (review of PR #33, S1/S2): every public function that takes a document, a value to hash or a snapshot (the validators, the
digest and canonical-bytes functions, the snapshot functions, `deny_all_dimensions`) first copies its input through `_plain`, which accepts ONLY exact
`dict`, `list`/`tuple` (tuples become lists), `str`, `bool`, `int` and `None` (subclasses, floats, bytes and every other type become an opaque marker
that is refused with `field_type_invalid` at its own path), requires `str` keys, refuses a string that contains an adjacent high and low surrogate (two
different native strings would otherwise serialize to the same bytes), and bounds nesting depth and node count. Validation and hashing then operate on
that private plain copy, so a subclass can neither change what is validated versus hashed nor mutate the document in between. The only exceptions the
public surface raises for a document are `IdentityRefusal`; `ValueError` is raised only for programmer errors (an unknown refusal code or role), and its
message never formats the offending object. `IdentityRefusal` does not validate `stage` (a constructor argument, not a document path); `verdict_for` and
`mapping_row_for` treat a `stage` that is not an exact `str` as no match (`KeyError`, or the identifier row for `field_invalid`), never calling its `==`.

Not in this module: composition of registry and caller values (EXT-S1-4), any store, activation state or `activation_sequence` (EXT-S4), the Control
Plane or Runtime guards (the guard comparison ORDER and every durable-state read belong to EXT-S4-2; `compare_binding_identity` is a pure helper over a row the
caller already holds). The three additive codes (`not_activated`, `policy_identity_mismatch`, `store_unknown`) are revision 2 (`r08-v2-reasons/2`,
`v2_codes.CODES_V2_REV2`, Amendment 1 / PR #32); this module maps all three and raises two of them (`policy_identity_mismatch` and `store_unknown`) from
`compare_binding_identity`; `not_activated` is mapped for the guard that will raise it.

DEFERRED (not implemented here, listed so no consumer assumes them): (1) the registry-form identity (null `activation_ref`) built from verified inputs and its
completion with `activation_ref` (spec 4 and 10 assign this to the Registry source PR); (2) the guard itself and durable state (EXT-S4); (3) the mapping rows
for the two v2-only codes of `V2_ADDED_CODES` (withdrawal and the snapshot floor: owning contracts and evaluators absent); (4) the shipped registry statement validator `common.valid_token` (r08-v1, and the verifier's `_normalize_trust` that the adapter calls first) still reads the host Unicode database and is NOT changed here (a bounded follow-up); this module uses the frozen table for effective-payload entries, F5 class names and snapshot-scope tokens; (5) (spec ids renamed: the typed evidence stages are INPUT / DURABLE_STATE); (6) a trust root or any authentication of a snapshot: the adapter
and the digests give integrity only and add no authority.

RULED (Architect Batch 6, 4.6, N-10) and applied here: a snapshot version is a strict int in [1, 2^53 - 1] (not an operational freshness bound); a `min_epochs`
floor and a revoked-selection epoch are strict POSITIVE ints in the declared selection-epoch range; a repeated grant (the same canonical five-token identity
twice in one issuer) is refused while distinct grants, and the same grant under two issuers, are accepted; MAX_SNAPSHOT_NODES (1048576) refuses as `input_too_large`;
a non-str or ambiguous key refuses before any projection or digest; `NON_STRING_KEY` and `AMBIGUOUS_STRING_KEY` are TYPED `DiagnosticLabel` values that the
exact-type boundary refuses everywhere a digest or document could take them; `project_effective_policy_digest` is the public projection entry point;
`verify_carried_binding_digest` orders: binding syntax and version, carried-digest format, authoritative identity and context (when the row is given), then the
digest comparison. This is STRICTER than `verify._normalize_trust` in exactly these places, each fail-closed: a version above 2^53 - 1, a floor or revoked epoch
outside [1, 2147483647] (the verifier accepts any strict int for a revoked epoch and any floor of at least 1), and a repeated grant (the verifier accepts it).

PROPOSED by this PR in addition (each needs an Architect line, none is a ruling): a snapshot shape guard (lowercase hex key, five-token grants); a node ceiling
on one in-memory document (MAX_NODES), refused as `input_too_large` (a size limit, never reported as a malformed snapshot); the members `NON_STRING_KEY` and
`AMBIGUOUS_STRING_KEY` for a dict key that is not an exact str or contains an adjacent surrogate pair, and a refusal of such a string value at its own path (the
order of these refusals against the root-object and `field_missing` checks is not stated by the spec: a non-str key is refused first); long integer literals
load as `OutOfRangeInteger`, never as a plausible int, and the raw serializer refuses it `field_invalid` like a native big int; the comparison order of
`compare_binding_identity` (`selection_id` first, `scope_key` second) and its reading of an unusable durable row as `store_unknown`;
`project_effective_policy_digest` tagging the three effective-derivation kinds as projection-stage refusals.

Known, disclosed limits (PR #33 re-review, PROPOSED where they are choices): (N-C) native input is bounded by node count (MAX_NODES, MAX_SNAPSHOT_NODES)
and depth, not by byte or string length: a very long native string costs time linear in its length and nothing else; (N-D) a NATIVE `str` that contains an
adjacent high and low surrogate in an identifier member is refused `field_type_invalid` (class `other`) where the spec grammar gives `field_invalid` for a
string that does not match; the verdict and retry class are the same, the loader can never produce such a string, and the raw serializer says
`field_invalid`; (N-E) `IdentityRefusal.__reduce__` rebuilds the base class, so a subclass would not survive pickling (none exists in the package).

Rulings N-10 to N-12 are RULED and implemented (syntax-first parse, strict ints, typed INPUT / DURABLE_STATE stage, unknown store HOLD, a refused projection is never
never-activated). N-13 is RULED and adopted: effective-payload list entries and F5 class names are decided by the sha256-pinned Unicode 15.1.0 table (`frozen_token_valid`), never by the host database. N-10(c) is RULED (Architect final ruling): the 2^53 - 1 representation bound is applied at INGEST in `trust_snapshot_from_verified`
(`trust_snapshot_invalid`, stage `ingest`, member `trust_snapshot_version`; the code and stage names are PROPOSED pending Architect confirmation, PR #35 spec 5.5.2); the snapshot shape guard and the projection stage remain second lines of defence.

Pure with one benign exception: no clock, no network, no file I/O. The sha256-pinned Unicode 15.1.0 token table is embedded (`v2_token_table`); it is cached in the
lazily set module global `_TOKEN_TABLE`, and its pin is checked at the FIRST token evaluation (not at import), failing closed with RuntimeError (a failed check is not
cached, so every later evaluation re-checks). A payload with no token to evaluate (for example all-empty deny-all lists) never touches the table.

REMAINING HOST-UNICODE DEPENDENCE and ordering obligations (documented, NOT fixed in this PR; bounded follow-ups):
  * FU-1 (families, r08-v2 composition): `registry_successor/v2_f1ab.py` (`_entry_ok`, `normalize_caller`) and `registry_successor/v2_age_bounds.py` (F5 class keys),
    both registered in `FAMILIES_V2`, still call the host `common.valid_token`, so r08-v2 family COMPOSITION is host-dependent. A host newer than 15.1 may accept a token the
    frozen table rejects (composition passes, then `validate_effective_payload` refuses `field_invalid` at the digest step: fails closed). A host older than 15.1 may
    refuse a token the frozen table accepts (for example U+2EBF0, CJK Extension I). Follow-up FU-1: route both family modules to `frozen_token_valid`
    (tests = the 38 `token_unicode` vectors with `unicodedata` poisoned); this needs the table lifted out of this module to avoid a circular import.
  * TrustSnapshot OBJECT path: `trust_snapshot_from_verified` runs the verifier's `_normalize_trust` (host `common.valid_token`) AND THEN the frozen check, so the decision is
    host AND frozen: never looser than the frozen table; stricter than it only on a host older than 15.1 (a frozen-valid token refused: fail closed). Snapshots given as
    dicts are decided by the frozen table alone.
  * FU-2 (N-10(c) ordering): the snapshot-version ingest bound lives ONLY in `trust_snapshot_from_verified`. `verify._normalize_trust` (shared core, untouched) does not
    enforce it (it accepts a version of 2^60). A caller MUST pass a `TrustSnapshot` through this adapter before any authority evaluation; nothing here can force that
    ordering on a consumer. Follow-up FU-2: a consumer-wiring test, or a bound in the shared verifier under its own PR. Digests give integrity, never authentication.
"""
import hashlib
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Tuple

from . import common as c
from . import verify as _verify
from .v2_codes import CODES_V2, CODES_V2_REV2

IDENTITY_MODULE_VERSION = "ocs-ext-s1-5-identity/1"

BINDING_PROFILE = "ocs-policy-binding/1"
EFFECTIVE_PROFILE = "ocs-effective-policy/1"
SCOPE_KEY_PROFILE = "ocs-scope-key/1"
CONTRACT_VERSION = "r08-v2"
BINDING_PREFIX = b"ocs-reg/r08-v2/policy-binding\n"
EFFECTIVE_PREFIX = b"ocs-reg/r08-v2/effective-policy\n"
SCOPE_KEY_PREFIX = b"ocs-reg/r08-v2/scope-key\n"

MAX_DOCUMENT_BYTES = 65536
MAX_DEPTH = 8
MAX_LIST_ENTRIES = 256
MAX_NODES = 65536  # nodes of one in-memory document accepted by `_plain` (the byte limit of the loader is MAX_DOCUMENT_BYTES)
MAX_SNAPSHOT_NODES = 1048576  # PROPOSED ceiling for one trust snapshot (about 349,000 revoked pairs): over it is `input_too_large`, never `trust_snapshot_invalid`
_MAX_EXACT_DIGITS = 20  # every range below is under 20 digits; longer integer literals are classified by length and never converted
_INT_BOUND = 10 ** _MAX_EXACT_DIGITS  # the serializer refuses an integer of 20 or more digits (it never calls str() on an unbounded int)

# Per-field integer domains (spec 5.2). Each field has its OWN literal on purpose; they are equal today and independent by ruling OQ-1.
INTEGER_RANGES = MappingProxyType({
    "record_version": (1, 2147483647),
    "selection_epoch": (1, 2147483647),
    "trust_snapshot_version": (1, 9007199254740991),  # N-1: component-owner-derived (no source ceiling); N-10(c) RULED: the bound is also applied at ingest, `trust_snapshot_from_verified`
})
AGE_RANGES = MappingProxyType({
    "registry": (1, 2147483647),
    "caller": (0, 2147483647),
    "effective": (0, 2147483647),
})  # read-only views: a process-wide widening of the grammar must not be possible by assignment

TOP_MEMBERS = ("activation_ref", "binding_profile", "consumer_id", "effective_policy_digest", "family", "operation", "record_digest", "record_id",
               "record_version", "scope", "selection_digest", "selection_epoch", "selection_id", "trust_snapshot_fingerprint", "trust_snapshot_version")
SCOPE_MEMBERS = ("authority_domain", "institution", "tenant")
_ID_PATHS = frozenset(("record_id", "selection_id", "family", "consumer_id", "operation", "scope.tenant", "scope.institution", "scope.authority_domain"))
_DIGEST_PATHS = frozenset(("record_digest", "selection_digest", "effective_policy_digest", "activation_ref", "trust_snapshot_fingerprint"))
_INT_PATHS = frozenset(INTEGER_RANGES)
SCOPE_KEY_MEMBERS = ("authority_domain", "consumer_id", "family", "institution", "operation", "selection_id", "tenant")  # sorted

_IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")  # always used with fullmatch (== \A...\Z)
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class IdentityRefusal(Exception):
    """A typed refusal: `code` is a `CODES_V2_REV2` entry (revision 2 of the one Registry v2 vocabulary, 51 codes), `member` the first failing member path (a str) or None, `stage` the pipeline stage the
    refusal belongs to (`projection` for a refusal to project verified inputs into a binding, else None: the shape stage), `evidence` a read-only
    mapping of the spec 8.1 evidence values this module can compute (`observed_value_class`, `expected_range`, `carried_digest`, `recomputed_digest`,
    `projection_refusal_code`); values only a consumer knows (`original_selection_digest`, `scope_key_digest`, ...) are never filled in here."""

    def __init__(self, code: str, member: Any = None, stage: Any = None, evidence: Any = None):
        if type(code) is not str or code not in CODES_V2_REV2:  # a raise, not an assert: this must hold under python -O
            raise ValueError("refusal code outside CODES_V2_REV2 (got a %s)" % type(code).__name__)
        super().__init__(code)
        self.code = code
        self.member = member
        self.stage = stage
        self.evidence = MappingProxyType(dict(evidence or {}))

    def __reduce__(self):
        """Picklable and copyable (a `MappingProxyType` is neither): rebuilt from plain values, so a refusal can cross a process boundary. It rebuilds the BASE
        class: a subclass (none exists here) must define its own `__reduce__`."""
        return (IdentityRefusal, (self.code, self.member, self.stage, dict(self.evidence)))

    @property
    def layer(self) -> str:
        return CODES_V2_REV2[self.code][0]


def _refuse(code: str, member: Any = None, stage: Any = None, evidence: Any = None):
    raise IdentityRefusal(code, member, stage, evidence)


# ----------------------------------------------------------------------------------------------------------------------
# Hostile-input boundary: exact-type, bounded, private plain copy
# ----------------------------------------------------------------------------------------------------------------------
class OutOfRangeInteger:
    """What the loader returns for an integer literal of more than 20 digits (spec 5.5.1: classified by length, never converted). It is a distinct
    marker, never a plausible `int`: it is integer-TYPED (so a range check reports `field_invalid`, not a type error), it is outside EVERY range, it
    equals only a marker with the same literal, and the serializer refuses it."""

    __slots__ = ("literal",)

    def __init__(self, literal: str):
        self.literal = literal

    def __eq__(self, other: Any) -> bool:
        return type(other) is OutOfRangeInteger and other.literal == self.literal

    def __hash__(self) -> int:
        return hash(("OutOfRangeInteger", self.literal))

    def __repr__(self) -> str:
        return "OutOfRangeInteger(%d digits)" % len(self.literal.lstrip("-"))


class _Foreign:
    """Stands for any value `_plain` does not accept (a subclass, float, bytes, set, object, ...). Equal only to itself; every validator refuses it
    as a type error at its own path and the serializer refuses it."""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<foreign>"


class _Ambiguous(_Foreign):
    """Stands for a `str` that contains an adjacent high and low surrogate: it would serialize to the same bytes as the astral character those two code
    units spell, so two different native strings could share a digest. Refused like any foreign value (a type error at its own path; `field_invalid` in
    the raw serializer)."""

    __slots__ = ()


_FOREIGN = _Foreign()
_AMBIGUOUS = _Ambiguous()
_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")
class DiagnosticLabel(str):
    """A TYPED diagnostic member label (ruling 4.6). It is a `str` subclass on purpose: `_plain` accepts exact `str` only, so a label can never be hashed, serialized
    or placed in a document, a binding, a preimage or any signed or digest input (it becomes an opaque marker that is refused). It is equal to its text so a
    consumer can compare a refusal's `member`, and `type(member) is DiagnosticLabel` tells a diagnostic placeholder from a real member path. A real document
    key with the same text is an ordinary `str` and is refused on its own merits."""

    __slots__ = ()


NON_STRING_KEY = DiagnosticLabel("<non-string key>")  # PROPOSED (spec 5.5 is silent): the member reported for a dict key that is not an exact str
AMBIGUOUS_STRING_KEY = DiagnosticLabel("<ambiguous string key>")  # PROPOSED: the member reported for a str key that contains an adjacent high and low surrogate


def _value_class(v: Any) -> str:
    if v is None:
        return "null"
    return {bool: "boolean", int: "integer", str: "string", list: "array", dict: "object", OutOfRangeInteger: "integer"}.get(type(v), "other")


def _plain(value: Any, depth: int = 1, budget: Any = None, limit: int = MAX_NODES) -> Any:
    """A private plain copy of `value`: exact dict/list/str/bool/int/None only (tuples become lists; anything else becomes `_FOREIGN`), `str` keys only
    (any other key refuses `field_unknown` at NON_STRING_KEY), nesting no deeper than MAX_DEPTH (`json_nesting_too_deep`, counting scalars like the loader
    does) and at most `limit` nodes (`input_too_large`; MAX_NODES unless the caller passes MAX_SNAPSHOT_NODES). Recursion is bounded by MAX_DEPTH, so a
    self-referential list ends in a typed refusal. A shared (DAG) input is counted per visit, so it cannot expand without bound."""
    if budget is None:
        budget = [limit]
    budget[0] -= 1
    if budget[0] < 0:
        _refuse("input_too_large")
    if depth > MAX_DEPTH:
        _refuse("json_nesting_too_deep")
    t = type(value)
    if t is str:
        return _AMBIGUOUS if _SURROGATE_PAIR.search(value) else value
    if value is None or t is bool or t is int or t is OutOfRangeInteger:
        return value
    if t is list or t is tuple:
        return [_plain(x, depth + 1, budget, limit) for x in value]
    if t is dict:
        out = {}
        for k, v in value.items():
            if type(k) is not str:
                _refuse("field_unknown", NON_STRING_KEY)
            if _SURROGATE_PAIR.search(k):
                _refuse("field_unknown", AMBIGUOUS_STRING_KEY)
            out[k] = _plain(v, depth + 1, budget, limit)
        return out
    return _FOREIGN


# ----------------------------------------------------------------------------------------------------------------------
# Canonical JSON and digests (spec 5.3, 5.4)
# ----------------------------------------------------------------------------------------------------------------------
_SHORT = MappingProxyType({0x22: '\\"', 0x5C: "\\\\", 0x08: "\\b", 0x0C: "\\f", 0x0A: "\\n", 0x0D: "\\r", 0x09: "\\t"})


def _unit(u: int) -> str:
    return "\\u%04x" % u


def _serialize_string(s: str) -> str:
    if _SURROGATE_PAIR.search(s):  # defence in depth: `_plain` already refuses it; two different native strings must never share bytes
        _refuse("field_invalid")
    out = ['"']
    for ch in s:
        cp = ord(ch)
        if cp in _SHORT:
            out.append(_SHORT[cp])
        elif cp < 0x20 or cp == 0x7F:
            out.append(_unit(cp))
        elif cp < 0x80:
            out.append(ch)
        elif cp < 0x10000:
            out.append(_unit(cp))
        else:
            cp -= 0x10000
            out.append(_unit(0xD800 + (cp >> 10)) + _unit(0xDC00 + (cp & 0x3FF)))
    out.append('"')
    return "".join(out)


def _serialize(value: Any, depth: int = 1) -> str:
    """Exact types only (a subclass is a refusal, not a coercion), nesting bounded by MAX_DEPTH, integers below 20 digits; every failure is an
    IdentityRefusal (`field_type_invalid`, `field_invalid`, `json_nesting_too_deep`) and `str()` is never called on an unbounded integer."""
    if depth > MAX_DEPTH:
        _refuse("json_nesting_too_deep")
    t = type(value)
    if value is None:
        return "null"
    if t is bool:
        return "true" if value else "false"
    if t is int:
        if not -_INT_BOUND < value < _INT_BOUND:
            _refuse("field_invalid")
        return "%d" % value
    if t is str:
        return _serialize_string(value)
    if t is OutOfRangeInteger or t is _Ambiguous:
        _refuse("field_invalid")  # the same code a native big int gets
    if t is list or t is tuple:
        return "[" + ",".join(_serialize(x, depth + 1) for x in value) + "]"
    if t is dict:
        if any(type(k) is not str for k in value):
            _refuse("field_unknown", NON_STRING_KEY)
        if any(_SURROGATE_PAIR.search(k) for k in value):
            _refuse("field_unknown", AMBIGUOUS_STRING_KEY)
        return "{" + ",".join(_serialize_string(k) + ":" + _serialize(value[k], depth + 1) for k in sorted(value)) + "}"
    _refuse("field_type_invalid")


def canonical_json_bytes(value: Any) -> bytes:
    """Canonical JSON: keys sorted by Unicode code point, no whitespace, every code point outside U+0020..U+007E escaped (lowercase hex, surrogate
    pairs above U+FFFF), so the output is pure ASCII. Only exact None, bool, int (under 20 digits), str, list, tuple and dict (str keys) are
    serializable; anything else, or nesting deeper than MAX_DEPTH, or more than MAX_NODES nodes, is an IdentityRefusal. The input is first copied through
    the same bounded boundary as every validator, so a shared (DAG) input refuses `input_too_large` instead of expanding without bound."""
    return _serialize(_plain(value)).encode("ascii")


def _sha_plain(prefix: bytes, plain: Any) -> str:
    """Digest of a tree that already went through `_plain` (private: skips the copy)."""
    return "sha256:" + hashlib.sha256(prefix + _serialize(plain).encode("ascii")).hexdigest()


def _sha(prefix: bytes, value: Any) -> str:
    return _sha_plain(prefix, _plain(value))


def plain_digest(value: Any) -> str:
    """Un-prefixed digest of the canonical bytes (the trust snapshot fingerprint form)."""
    return _sha(b"", value)


def binding_digest(binding: Any) -> str:
    """Digest of a COMPLETED binding. The caller must have validated it (`validate_binding`); a carried digest is never trusted, only recomputed."""
    return _sha(BINDING_PREFIX, binding)


# ----------------------------------------------------------------------------------------------------------------------
# Strict loader (spec 5.5.1, 5.5.2): input boundary, then syntax, then number literals, then duplicate keys, then depth
# ----------------------------------------------------------------------------------------------------------------------
class _Pairs(list):
    """An object whose (key, value) pairs keep document order so duplicate keys can be examined after the syntax phase."""


_WS = " \t\n\r"
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
_STRING_CHUNK = re.compile(r'[^"\\\x00-\x1f]*')
_ESCAPES = MappingProxyType({'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"})
_HEX = frozenset("0123456789abcdefABCDEF")


def _int_literal(text: str) -> Any:
    digits = text.lstrip("-")
    if text == "-0":  # negative zero (spec 5.5.1) is NEVER the integer 0: the rejected-literal marker is integer-typed, outside every range, refused by the serializer
        marker = OutOfRangeInteger
        return marker(text)
    if len(digits) <= _MAX_EXACT_DIGITS:
        return int(text)
    return OutOfRangeInteger(text)


def _scan_string(text: str, i: int):
    n = len(text)
    i += 1
    out = []
    while True:
        m = _STRING_CHUNK.match(text, i)
        out.append(m.group())
        i = m.end()
        if i >= n:
            raise ValueError("unterminated string")
        ch = text[i]
        if ch == '"':
            return "".join(out), i + 1
        if ch != "\\":
            raise ValueError("control character in string")
        i += 1
        if i >= n:
            raise ValueError("unterminated escape")
        e = text[i]
        if e == "u":
            h = text[i + 1:i + 5]
            if len(h) != 4 or not _HEX.issuperset(h):
                raise ValueError("bad unicode escape")
            cp = int(h, 16)
            i += 5
            if 0xD800 <= cp <= 0xDBFF and text[i:i + 2] == "\\u":
                h2 = text[i + 2:i + 6]
                if len(h2) == 4 and _HEX.issuperset(h2) and 0xDC00 <= int(h2, 16) <= 0xDFFF:
                    cp = 0x10000 + ((cp - 0xD800) << 10) + (int(h2, 16) - 0xDC00)
                    i += 6
            out.append(chr(cp))
        elif e in _ESCAPES:
            out.append(_ESCAPES[e])
            i += 1
        else:
            raise ValueError("bad escape")


def _scan(text: str):
    """Iterative JSON scanner (explicit stack, no recursion). RFC 8259 grammar plus the tokens NaN, Infinity, -Infinity, recognized only so they can be
    refused as number literals. Returns (tree, saw_unsupported_number); raises ValueError on any syntax error."""
    n = len(text)
    i = 0
    stack = []
    key_of = []
    root = None
    done = False
    saw_number = False
    expecting = "value"  # value | value_or_end | key_or_end | key | after

    def attach(v):
        nonlocal root, done
        if not stack:
            root, done = v, True
        elif isinstance(stack[-1], _Pairs):
            stack[-1].append((key_of[-1], v))
        else:
            stack[-1].append(v)

    def close():
        top = stack.pop()
        key_of.pop()
        attach(top)

    while True:
        while i < n and text[i] in _WS:
            i += 1
        if done:
            if i != n:
                raise ValueError("extra data")
            return root, saw_number
        if i >= n:
            raise ValueError("unexpected end")
        ch = text[i]
        if expecting == "after":
            top = stack[-1]
            if ch == ",":
                i += 1
                expecting = "key" if isinstance(top, _Pairs) else "value"
            elif ch == ("}" if isinstance(top, _Pairs) else "]"):
                i += 1
                close()
            else:
                raise ValueError("expected , or close")
            continue
        if expecting in ("key", "key_or_end"):
            if ch == "}" and expecting == "key_or_end":
                i += 1
                close()
                expecting = "after"
                continue
            if ch != '"':
                raise ValueError("expected a key")
            k, i = _scan_string(text, i)
            while i < n and text[i] in _WS:
                i += 1
            if i >= n or text[i] != ":":
                raise ValueError("expected :")
            i += 1
            key_of[-1] = k
            expecting = "value"
            continue
        if expecting == "value_or_end" and ch == "]":
            i += 1
            close()
            expecting = "after"
            continue
        if ch == "{":
            stack.append(_Pairs())
            key_of.append(None)
            i += 1
            expecting = "key_or_end"
        elif ch == "[":
            stack.append([])
            key_of.append(None)
            i += 1
            expecting = "value_or_end"
        elif ch == '"':
            s, i = _scan_string(text, i)
            attach(s)
            expecting = "after"
        elif text.startswith("true", i):
            attach(True)
            i += 4
            expecting = "after"
        elif text.startswith("false", i):
            attach(False)
            i += 5
            expecting = "after"
        elif text.startswith("null", i):
            attach(None)
            i += 4
            expecting = "after"
        elif text.startswith("NaN", i) or text.startswith("Infinity", i) or text.startswith("-Infinity", i):
            saw_number = True
            i += 3 if text.startswith("NaN", i) else (8 if text.startswith("Infinity", i) else 9)
            attach(0)
            expecting = "after"
        else:
            m = _NUMBER.match(text, i)
            if m is None:
                raise ValueError("unexpected character")
            if m.group(1) is not None or m.group(2) is not None:
                saw_number = True
                attach(0)
            else:
                attach(_int_literal(m.group()))
            i = m.end()
            expecting = "after"


def _objects(node):
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, _Pairs):
            yield cur
            stack.extend(v for _, v in cur)
        elif isinstance(cur, list):
            stack.extend(cur)


def _within_depth(value) -> bool:
    stack = [(value, 1)]
    while stack:
        node, d = stack.pop()
        if d > MAX_DEPTH:
            return False
        if isinstance(node, _Pairs):
            stack.extend((v, d + 1) for _, v in node)
        elif isinstance(node, list):
            stack.extend((x, d + 1) for x in node)
    return True


def _materialize(node):
    """Iterative: the nesting limit is checked before this runs, so depth is bounded by MAX_DEPTH here."""
    if isinstance(node, _Pairs):
        return {k: _materialize(v) for k, v in node}
    if isinstance(node, list):
        return [_materialize(x) for x in node]
    return node


def load_document(raw: Any) -> Any:
    """Parse a binding, scope-key, preimage or effective document. Order (PROPOSED, N-10): input boundary (strict UTF-8 or text, then UTF-8 size in
    BYTES), whole-text syntax, number literals (float, exponent, NaN, Infinity), duplicate keys at any depth after unescaping, nesting depth. A BOM is
    not stripped and an integer literal of any length is valid syntax (classified by length, never converted when long: it loads as an `OutOfRangeInteger`
    marker, never a plausible int). Only exact `bytes` and `str` are accepted; any other type is `input_not_text`."""
    if type(raw) is bytes:
        data = raw
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            _refuse("input_not_text")
    elif type(raw) is str:
        text = raw
        try:
            data = text.encode("utf-8")
        except UnicodeEncodeError:
            _refuse("input_not_text")
    else:
        _refuse("input_not_text")
    if len(data) > MAX_DOCUMENT_BYTES:
        _refuse("input_too_large")
    try:
        tree, saw_number = _scan(text)
    except ValueError:
        _refuse("json_malformed")
    if saw_number:
        _refuse("json_number_unsupported")
    for obj in _objects(tree):
        keys = [k for k, _ in obj]
        if len(keys) != len(set(keys)):
            _refuse("json_duplicate_key")
    if not _within_depth(tree):
        _refuse("json_nesting_too_deep")
    return _materialize(tree)


# ----------------------------------------------------------------------------------------------------------------------
# Completed-binding validation (spec 3, 5.1, 5.2, 5.5)
# ----------------------------------------------------------------------------------------------------------------------
def _is_int(v: Any) -> bool:
    """A strict integer: exactly `int` (never bool, never a subclass)."""
    return type(v) is int


def _int_typed(v: Any) -> bool:
    """Integer-TYPED for the type phase: a strict int or the loader's out-of-range marker (which then fails every range check with `field_invalid`)."""
    return type(v) is int or type(v) is OutOfRangeInteger


def _in_range(v: Any, lo: int, hi: int) -> bool:
    return type(v) is int and lo <= v <= hi


def _type_refusal(path: Any, value: Any):
    _refuse("field_type_invalid", path, evidence={"observed_value_class": _value_class(value)})


def _range_refusal(path: str, lo: int, hi: int):
    _refuse("field_invalid", path, evidence={"expected_range": (lo, hi)})


def _ascii_match(pattern, value: str) -> bool:
    return value.isascii() and pattern.fullmatch(value) is not None


def _flatten_checked(doc: dict) -> dict:
    """Only after the top-level and `scope` member sets were checked separately: no top-level key can then contain a dot, so a literal
    `scope.tenant` can never stand in for the nested member."""
    flat = {}
    for k, v in doc.items():
        if k == "scope":
            for sk, sv in v.items():
                flat["scope." + sk] = sv
        else:
            flat[k] = v
    return flat


def validate_binding(doc: Any) -> dict:
    """Return a private plain COPY of `doc` if it is a well-formed completed binding, else raise IdentityRefusal (never the caller's own object, never
    a subclass). Phases (first failure wins, sorted path order inside a phase): object, scope object, missing members, unknown members, types, values.
    The top-level set (14 plain members plus `scope`) and the nested `scope` set (tenant, institution, authority_domain) are checked as TWO sets, before
    flattening."""
    d = _plain(doc)
    if type(d) is not dict:
        _type_refusal(None, d)
    has_scope = "scope" in d
    nested = d["scope"] if has_scope else None
    if has_scope and type(nested) is not dict:
        _type_refusal("scope", nested)
    missing = set(TOP_MEMBERS) - {"scope"} - set(d)
    if not has_scope:
        missing.add("scope")
    else:
        missing |= {"scope." + k for k in SCOPE_MEMBERS if k not in nested}
    if missing:
        _refuse("field_missing", min(missing))
    unknown = {k for k in d if k not in TOP_MEMBERS}
    unknown |= {"scope." + k for k in nested if k not in SCOPE_MEMBERS}
    if unknown:
        _refuse("field_unknown", min(unknown))
    flat = _flatten_checked(d)
    for path in sorted(flat):
        v = flat[path]
        if path in _INT_PATHS:
            if not _int_typed(v):
                _type_refusal(path, v)
        elif type(v) is not str:
            _type_refusal(path, v)
    for path in sorted(flat):
        v = flat[path]
        if path in _INT_PATHS:
            lo, hi = INTEGER_RANGES[path]
            if not _in_range(v, lo, hi):
                _range_refusal(path, lo, hi)
        elif path in _ID_PATHS:
            if not _ascii_match(_IDENT, v):
                _refuse("field_invalid", path)
        elif path in _DIGEST_PATHS:
            if not _ascii_match(_DIGEST, v):
                _refuse("field_invalid", path)
        elif path == "binding_profile" and v != BINDING_PROFILE:
            _refuse("field_invalid", path)
    return d


def parse_binding(raw: Any) -> dict:
    """Load and validate a completed binding document in one step (the loader and validator are separate public functions as well)."""
    return validate_binding(load_document(raw))


def canonical_binding_bytes(binding: dict) -> bytes:
    return canonical_json_bytes(validate_binding(binding))


def checked_binding_digest(binding: dict) -> str:
    """Validate, then digest. Use this, not `binding_digest`, on anything that did not come from `validate_binding`."""
    return binding_digest(validate_binding(binding))


# The authoritative identity members of the complete declared canonical binding version `ocs-policy-binding/1` (ruling 4.3). SIX members; the selected record
# identity is the triple, so eight VALUES are compared. `scope_key` is the scope-key DIGEST (spec 5.7); the other seven are binding members. A member a
# historical binding version does not declare is never manufactured: this table is the declared v1 binding, not a superset of it.
POLICY_IDENTITY_MEMBER_SET = ("scope_key", "selection_id", "selection_epoch", "selection_digest", "record", "activation_ref")
POLICY_IDENTITY_MEMBER_VALUES = ("scope_key", "selection_id", "selection_epoch", "selection_digest", "record_id", "record_version", "record_digest", "activation_ref")
# Comparison order for the FIRST differing member: `selection_id` precedes `scope_key` because the scope-key digest includes `selection_id` (spec 5.7), so a
# `selection_id` difference would otherwise always be reported as `scope_key`. PROPOSED and local to this pure helper; the guard order stays with EXT-S4-2.
_COMPARE_ORDER = ("selection_id", "scope_key", "selection_epoch", "selection_digest", "record_id", "record_version", "record_digest", "activation_ref")
_ROW_IDENTITY = ("selection_id", "scope_key")  # compared BEFORE any epoch: an epoch is meaningful only against the row of the same scope key and selection id
_ROW_INT_PATHS = frozenset(("selection_epoch", "record_version"))
_ROW_ID_PATHS = frozenset(("selection_id", "record_id"))
_ROW_DIGEST_PATHS = frozenset(("scope_key", "selection_digest", "record_digest", "activation_ref"))


def _authoritative_row_ok(row: Any) -> bool:
    """The consumer-owned durable row as the comparison needs it: exactly the eight values, each in its binding grammar. Anything else means the
    authoritative state is not usable (the caller maps that to `store_unknown`, never to a fallback)."""
    if type(row) is not dict:
        return False
    for k in row:  # every key is an exact str BEFORE any set comparison: a str subclass with a raising `__eq__` must refuse here, not leak from the comparison
        if type(k) is not str:
            return False
    if set(row) != set(POLICY_IDENTITY_MEMBER_VALUES):
        return False
    for k, v in row.items():
        if type(k) is not str:
            return False
        if k in _ROW_INT_PATHS:
            lo, hi = INTEGER_RANGES[k]
            if not (type(v) is int and lo <= v <= hi):
                return False
        elif k in _ROW_ID_PATHS:
            if not (type(v) is str and _ascii_match(_IDENT, v)):
                return False
        elif not (type(v) is str and _ascii_match(_DIGEST, v)):
            return False
    return True


def compare_binding_identity(binding: Any, authoritative: Any) -> str:
    """Compare a claim-carried completed binding with the consumer-owned durable activation row over ALL six authoritative identity members of
    `ocs-policy-binding/1` (ruling 4.3). PURE: it reads no store and decides no guard order (EXT-S4-2 owns the guard); `authoritative` is the row the caller
    already holds. The binding is validated first (syntax, version and every member), so a malformed binding is refused with its own code.
      * `authoritative` that is not exactly the eight values in their grammar: `store_unknown` (UNKNOWN_FAIL_CLOSED): an unusable row is indeterminate state,
        never a fallback and never a match. No member is skipped because it is missing.
      * ROW IDENTITY FIRST: epochs are comparable only within one scope key and one selection id, so `selection_id` and then `scope_key` are compared before
        any epoch. A claim whose `selection_id` or `scope_key` differs from the row is NOT this row's claim: it is `policy_identity_mismatch` (REFUSE, `member`
        naming it), whatever its epoch (review S-1). This reconciles with the kit, which resolves the row BY SCOPE KEY (the conformance kit `highwater.py:980`)
        and only then compares the epoch (stale return at `highwater.py:997-998`, other members at `:999-1001`): a claim for another scope never reaches a row of this one.
      * then, for the SAME scope key and selection id, a claim epoch BEHIND the row: `selection_epoch_stale` (REFUSE_STALE, evidence `selection_epoch`,
        `high_water_epoch`); it takes precedence over the remaining members (a definitively stale epoch is never a generic identity mismatch).
      * otherwise the FIRST differing member in `_COMPARE_ORDER` (`selection_epoch` AHEAD of the row, `selection_digest`, the record triple, `activation_ref`):
        `policy_identity_mismatch` (REFUSE). The claim's `effective_policy_digest` is never compared with durable state (contract 7.4: it is caller-dependent).
    Returns the recomputed binding digest when every member matches."""
    # ONE exact private copy of the row BEFORE any validation, used for the whole comparison (like the binding): a concurrent mutation of the caller's row cannot
    # make the comparison combine values from two row states. Only an exact dict is copied; anything else is passed on and refused by `_authoritative_row_ok`.
    row = dict(authoritative) if type(authoritative) is dict else authoritative
    b = validate_binding(binding)
    if not _authoritative_row_ok(row):
        _refuse("store_unknown", "authoritative")
    claim = {"scope_key": scope_key_digest(scope_key_from_binding(b))}
    claim.update({k: b[k] for k in POLICY_IDENTITY_MEMBER_VALUES if k != "scope_key"})
    for k in _ROW_IDENTITY:
        if claim[k] != row[k]:
            _refuse("policy_identity_mismatch", k)
    if claim["selection_epoch"] < row["selection_epoch"]:
        _refuse("selection_epoch_stale", "selection_epoch", evidence={"selection_epoch": claim["selection_epoch"], "high_water_epoch": row["selection_epoch"]})
    for k in _COMPARE_ORDER:
        if claim[k] != row[k]:
            _refuse("policy_identity_mismatch", k)
    return binding_digest(b)


def verify_carried_binding_digest(binding: dict, carried: Any, authoritative: Any = None) -> str:
    """Guard check on a carried binding digest. Order (ruling 4.6): (1) the binding is validated (syntax, `binding_profile` version, all 15 members), (2) the
    carried digest's format (`field_invalid`), (3) when `authoritative` (the consumer-owned durable row, `compare_binding_identity`) is given, the authoritative
    identity and context are compared (`store_unknown`, `selection_epoch_stale`, `policy_identity_mismatch`), and only then (4) the carried digest is compared
    with the recomputed value (`digest_mismatch`, evidence carried and recomputed). WITHOUT `authoritative` this is a digest-integrity check only: it verifies
    no identity and no context, and a caller that needs the identity guarantee MUST pass the row (the guard, EXT-S4-2, is the consumer).
    WARNING: `authoritative=None` is NOT an identity verification. A matching digest proves only that the binding is internally consistent; it never shows that the
    binding names the activated policy, scope or epoch. Do not use the None form as a guard."""
    b = validate_binding(binding)  # ONE private validated copy: the digest and the identity below are both of THIS copy (no mutation of the caller's object between them)
    recomputed = binding_digest(b)
    if not (type(carried) is str and _ascii_match(_DIGEST, carried)):
        _refuse("field_invalid", evidence={"observed_value_class": _value_class(carried)})
    if authoritative is not None:
        compare_binding_identity(b, authoritative)
    if carried != recomputed:
        _refuse("digest_mismatch", evidence={"carried_digest": carried, "recomputed_digest": recomputed})
    return recomputed


# ----------------------------------------------------------------------------------------------------------------------
# Trust snapshot fingerprint (spec 7)
# ----------------------------------------------------------------------------------------------------------------------
_SNAPSHOT_MEMBERS = ("issuers", "min_epochs", "revoked_key_ids", "revoked_selections", "snapshot_id", "valid_until", "version")
_ISSUER_MEMBERS = ("alg", "authority", "issuer_id", "key_id", "public_key")
_LOWER_HEX = frozenset("0123456789abcdef")


# ----------------------------------------------------------------------------------------------------------------------
# Frozen token membership (spec 6.1, ruling N-13): Unicode 15.1.0, a committed excluded-range table, NO runtime Unicode database and no network.
# ----------------------------------------------------------------------------------------------------------------------
TOKEN_TABLE_SHA256 = "8c85813d25f6ed53371e27f0e4895a89de44a619824486dcff8d48ff8b607474"  # pinned in the spec and the vectors (pins.token_unicode_table)
_TOKEN_TABLE: Any = None
_RANGE_RE = re.compile(rb'\[\s*"([0-9A-F]{4,6})",\s*"([0-9A-F]{4,6})"\s*\]')


def _load_token_table(raw: Any = None, expected: str = TOKEN_TABLE_SHA256) -> Tuple[list, list]:
    """Verify the sha256 of the embedded table bytes BEFORE parsing and fail closed: a mismatched or malformed table raises RuntimeError (a build defect, never a
    typed refusal and never an accepting default). No file is opened and no host Unicode database is read."""
    try:
        if raw is None:
            from .v2_token_table import TABLE_BYTES as raw
        if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected or b'"unicode_version": "15.1.0"' not in raw:
            raise ValueError("pin")
        head, _, tail = raw.partition(b'"excluded_ranges"')
        ranges = [(int(x, 16), int(y, 16)) for x, y in _RANGE_RE.findall(tail)]
        if not ranges or any(a > b or (i and a <= ranges[i - 1][1]) for i, (a, b) in enumerate(ranges)) or ranges[-1][1] > 0x10FFFF:
            raise ValueError("ranges")
    except Exception:
        raise RuntimeError("the pinned Unicode 15.1.0 token table does not match its sha256 pin or is malformed") from None
    return [a for a, _ in ranges], ranges


def frozen_token_valid(value: Any) -> bool:
    """The token rule with frozen membership: an exact `str` of 1..128 code points, no `*`, no code point inside an excluded range of the pinned table.
    No normalization. Consults no runtime Unicode database."""
    global _TOKEN_TABLE
    if type(value) is not str or not 1 <= len(value) <= c.MAX_ENTRY_CHARS or "*" in value:
        return False
    if _TOKEN_TABLE is None:
        _TOKEN_TABLE = _load_token_table()
    starts, ranges = _TOKEN_TABLE
    for ch in value:
        cp = ord(ch)
        lo, hi = 0, len(starts)  # binary search: the last range whose start is <= cp
        while lo < hi:
            mid = (lo + hi) // 2
            if starts[mid] <= cp:
                lo = mid + 1
            else:
                hi = mid
        i = lo - 1
        if i >= 0 and ranges[i][0] <= cp <= ranges[i][1]:
            return False
    return True


def _token(v: Any) -> bool:
    """A snapshot-scope token on the r08-v2 identity path: decided by the frozen Unicode 15.1.0 table (`frozen_token_valid`), never by the host database. The
    shipped `common.valid_token` (r08-v1, the verifier) is NOT changed; the adapter still passes a `TrustSnapshot` through the verifier first, so the v2 decision is
    the verifier's AND this one: never looser than the frozen table, stricter only on a host older than 15.1, and host-independent for every snapshot given as a dict."""
    return frozen_token_valid(v)


def _snapshot_version_ok(v: Any) -> bool:
    """`TrustSnapshot.version`: a strict int in [1, 2^53 - 1] (ruling N-10, interoperable V1 representation; the same range as the binding's
    `trust_snapshot_version`). Not an operational freshness bound. `bool` and every subclass are refused."""
    lo, hi = INTEGER_RANGES["trust_snapshot_version"]
    return type(v) is int and lo <= v <= hi


def _epoch(v: Any) -> bool:
    """A selection epoch in a snapshot (a `min_epochs` floor or a revoked-selection epoch): a strict POSITIVE int in the declared `selection_epoch` range
    [1, 2147483647] (ruling 4.6: strict, unambiguous positive integers within the declared versioned range; the verifier requires a floor of at least 1 and
    accepts any strict int for a revoked epoch, so this is STRICTER than `verify._normalize_trust` and fail-closed: a refusal, never a coercion)."""
    lo, hi = INTEGER_RANGES["selection_epoch"]
    return type(v) is int and lo <= v <= hi


_revoked_epoch = _epoch  # the same declared range for a revoked-selection epoch (it names a selection epoch); kept as a name so the two uses read apart


def _hex_key(v: Any) -> bool:
    return type(v) is str and len(v) > 0 and len(v) % 2 == 0 and _LOWER_HEX.issuperset(v)


def _grant_ok(g: Any) -> bool:
    return type(g) is list and len(g) == 5 and all(_token(x) for x in g)


def _issuer_ok(i: Any) -> bool:
    """One issuer in the normalized shape of contract section 5: exactly alg, authority, issuer_id, key_id, public_key (lowercase hex, non-empty)."""
    return (type(i) is dict and set(i) == set(_ISSUER_MEMBERS) and _token(i["key_id"]) and _token(i["issuer_id"]) and type(i["alg"]) is str
            and _hex_key(i["public_key"]) and type(i["authority"]) is list and all(_grant_ok(g) for g in i["authority"]))


def _pair_ok(p: Any, epoch_ok: Any = _epoch) -> bool:
    return type(p) is list and len(p) == 2 and type(p[0]) is str and epoch_ok(p[1])


def _revoked_pair_ok(p: Any) -> bool:
    return _pair_ok(p, _revoked_epoch)


def _snapshot_shape_ok(s: Any) -> bool:
    """The delivered snapshot in the spec's normalized shape, checked against the verifier's own rules (valid tokens, version and floors of at least 1,
    any strict-int revoked epoch, parseable `valid_until`, five-token grants) plus the exact member set. Takes the PLAIN copy produced by `_checked_snapshot`."""
    if not (type(s) is dict and set(s) == set(_SNAPSHOT_MEMBERS)):
        return False
    if not (_token(s["snapshot_id"]) and _snapshot_version_ok(s["version"]) and type(s["valid_until"]) is str and c.parse_timestamp(s["valid_until"]) is not None):
        return False
    if not (type(s["issuers"]) is list and type(s["revoked_key_ids"]) is list and type(s["revoked_selections"]) is list and type(s["min_epochs"]) is list):
        return False
    return (all(_issuer_ok(i) for i in s["issuers"]) and all(type(k) is str for k in s["revoked_key_ids"])
            and all(_revoked_pair_ok(p) for p in s["revoked_selections"]) and all(_pair_ok(p) for p in s["min_epochs"]))


def _checked_snapshot(snapshot: Any) -> dict:
    """A private plain copy of a shape-valid snapshot, or `trust_snapshot_invalid` (PROPOSED REFUSE class) for a shape defect, a hostile type or a
    too-deep input. A snapshot over MAX_SNAPSHOT_NODES is `input_too_large` (a size limit, not a malformed snapshot)."""
    try:
        plain = _plain(snapshot, limit=MAX_SNAPSHOT_NODES)
    except IdentityRefusal as e:
        if e.code == "input_too_large":
            raise
        _refuse("trust_snapshot_invalid")
    if not _snapshot_shape_ok(plain):
        _refuse("trust_snapshot_invalid")
    return plain


def _duplicates(plain: dict) -> bool:
    keys = [i["key_id"] for i in plain["issuers"]]
    floors = [p[0] for p in plain["min_epochs"]]
    pairs = [(p[0], p[1]) for p in plain["revoked_selections"]]
    revoked = plain["revoked_key_ids"]
    grants = [i["authority"] for i in plain["issuers"]]
    per_issuer = any(len({tuple(g) for g in a}) != len(a) for a in grants)  # PROPOSED: a repeated grant inside one issuer (contract 5: "Duplicates are refused")
    return (len(set(keys)) != len(keys) or len(set(floors)) != len(floors) or len(set(pairs)) != len(pairs) or len(set(revoked)) != len(revoked)
            or per_issuer)


def normalize_snapshot(snapshot: dict) -> dict:
    """Normalized form: issuers by key_id, each `authority` array sorted, revoked_key_ids sorted, revoked_selections by (selection id, integer epoch),
    min_epochs by selection id. Never mutates the input and returns a plain copy. A malformed snapshot is `trust_snapshot_invalid` (PROPOSED REFUSE
    class); duplicates are NOT checked here (see `check_snapshot_duplicates`, `trust_snapshot_fingerprint`)."""
    plain = _checked_snapshot(snapshot)
    out = dict(plain)
    out["issuers"] = sorted(({**i, "authority": sorted(i["authority"])} for i in plain["issuers"]), key=lambda i: i["key_id"])
    out["revoked_key_ids"] = sorted(plain["revoked_key_ids"])
    out["revoked_selections"] = sorted(([p[0], p[1]] for p in plain["revoked_selections"]), key=lambda p: (p[0], p[1]))
    out["min_epochs"] = sorted(([p[0], p[1]] for p in plain["min_epochs"]), key=lambda p: p[0])
    return out


def check_snapshot_duplicates(snapshot: dict) -> None:
    """A malformed snapshot, or a duplicate issuer key id, min_epoch id, revoked selection pair, revoked key id or (PROPOSED) repeated grant inside one
    issuer, refuses `trust_snapshot_invalid` (PROPOSED REFUSE class)."""
    if _duplicates(_checked_snapshot(snapshot)):
        _refuse("trust_snapshot_invalid")


def trust_snapshot_fingerprint(snapshot: dict) -> str:
    """`sha256:` + plain digest of the normalized snapshot's canonical (ASCII) bytes; no domain prefix (contract section 5). Takes the SPEC's normalized
    dict shape (hex public keys, list pairs); an adapter from the verifier's `TrustSnapshot` object is deferred (see the PR body)."""
    plain = _checked_snapshot(snapshot)
    if _duplicates(plain):
        _refuse("trust_snapshot_invalid")
    try:
        return _sha_plain(b"", normalize_snapshot(plain))  # `plain` is already plain and size-checked at the snapshot ceiling; `normalize_snapshot` copies and re-validates it once more (a second pass, about
        # twice the cost at the ceiling, never a smaller ceiling and never the caller's original object)
    except IdentityRefusal:  # unreachable for a shape-valid snapshot; kept so the entry point can only ever raise trust_snapshot_invalid
        _refuse("trust_snapshot_invalid")


# ----------------------------------------------------------------------------------------------------------------------
# Registry-side adapter from the verifier's `TrustSnapshot` object (ruling 4.6: the P1 worker owns it; it is NOT a second trust authority)
# ----------------------------------------------------------------------------------------------------------------------
_SEQUENCE_TYPES = (tuple, list)
_SET_TYPES = (set, frozenset, tuple, list)


def trust_snapshot_from_verified(trust: Any) -> dict:
    """Convert a snapshot the VERIFIER accepts into the spec's normalized dict shape (public key bytes to lowercase hex, grants to five-token arrays, pairs to
    two-element lists), for `trust_snapshot_fingerprint`. It adds no authority: the object is only ever read, never trusted, signed or stored.
      * `None` (no required snapshot supplied): `trust_snapshot_missing` at the `INPUT` stage (typed, ruling N-11).
      * anything else that is not exactly a `TrustSnapshot` (a subclass, a dict, a look-alike), or that `verify._normalize_trust` refuses, or whose members are
        not exactly the verifier's types: `trust_snapshot_invalid` (definitive malformed input is never called missing).
    The result is then re-checked by the stricter shape guard of `trust_snapshot_fingerprint` (version and epoch ranges from `INTEGER_RANGES`, no repeated
    grant inside one issuer), so a snapshot that passes the verifier can still be refused here, never the reverse."""
    if trust is None:
        _refuse("trust_snapshot_missing", None, "INPUT")
    if type(trust) is _verify.TrustSnapshot:
        # N-10(c) ingest bound (PROPOSED mapping, PR #35 spec 5.5.2): the representation bound is applied to the delivered version BEFORE the snapshot is used in
        # authority evaluation (`_normalize_trust`), the fingerprint or any projection; `bool`, floats, strings, None and out-of-range ints never get further.
        try:
            version = trust.version
        except Exception:  # a missing or unreadable version (e.g. `TrustSnapshot.__new__`) is an invalid ingest value, never an escaping AttributeError
            _refuse("trust_snapshot_invalid", "trust_snapshot_version", "ingest",
                    evidence={"expected_range": INTEGER_RANGES["trust_snapshot_version"], "observed_value_class": "missing"})
        if not _snapshot_version_ok(version):
            _refuse("trust_snapshot_invalid", "trust_snapshot_version", "ingest",
                    evidence={"expected_range": INTEGER_RANGES["trust_snapshot_version"], "observed_value_class": _value_class(version)})
    try:
        if type(trust) is not _verify.TrustSnapshot:
            raise TypeError
        # `min_epochs` is read more than once below and `_normalize_trust` iterates it: a one-shot iterator would be consumed and then fingerprint as an empty
        # floor list. Only a re-iterable container is admitted (an exact dict or mapping proxy, a tuple or a list); anything else is refused before normalization.
        if type(trust.min_epochs) not in (dict, MappingProxyType, tuple, list):
            raise TypeError
        normalized = _verify._normalize_trust(trust)
        if normalized is None:
            raise TypeError
        if not (type(trust.issuers) in _SEQUENCE_TYPES and type(trust.revoked_key_ids) in _SET_TYPES and type(trust.revoked_selections) in _SET_TYPES):
            raise TypeError
        issuers = []
        for e in trust.issuers:
            if type(e) is not _verify.IssuerEntry or type(e.public_key) is not bytes or type(e.authority) not in _SEQUENCE_TYPES:
                raise TypeError
            grants = []
            for g in e.authority:
                if type(g) is not _verify.AuthorityGrant:
                    raise TypeError
                grants.append([g.consumer_id, g.tenant, g.institution, g.authority_domain, g.operation])
            issuers.append({"key_id": e.key_id, "issuer_id": e.issuer_id, "alg": e.alg, "public_key": e.public_key.hex(), "authority": grants})
        revoked = []
        for item in trust.revoked_selections:
            if type(item) is not tuple or len(item) != 2:
                raise TypeError
            revoked.append([item[0], item[1]])
        # the floors are the verifier's OWN returned dict, never a second read of the caller's container (a one-shot `items()` would read back empty)
        mins = [[sid, floor] for sid, floor in normalized["floors"].items()]
        out = {"snapshot_id": trust.snapshot_id, "version": trust.version, "valid_until": trust.valid_until, "issuers": issuers,
               "revoked_key_ids": list(trust.revoked_key_ids), "revoked_selections": revoked, "min_epochs": mins}
    except Exception:  # a hostile or malformed object is a definitive refusal, never an escape, and never formatted into a message
        _refuse("trust_snapshot_invalid")
    check_snapshot_duplicates(out)  # a repeated grant (the same canonical five-token identity twice in one issuer), issuer key, pair or key id: trust_snapshot_invalid
    return normalize_snapshot(out)


def trust_snapshot_fingerprint_from_verified(trust: Any) -> str:
    """`trust_snapshot_fingerprint` of the adapter's normalized dict for a verifier `TrustSnapshot` (spec 7); same refusals as `trust_snapshot_from_verified`
    plus duplicates (`trust_snapshot_invalid`)."""
    return trust_snapshot_fingerprint(trust_snapshot_from_verified(trust))


# ----------------------------------------------------------------------------------------------------------------------
# Projection from verified inputs (spec 5.6)
# ----------------------------------------------------------------------------------------------------------------------
def _projection_refusal(member: str, **evidence):
    _refuse("field_invalid", member, stage="projection", evidence={"projection_refusal_code": "field_invalid", **evidence})


def project_scope(statement_scope: Any) -> dict:
    """IDENTITY projection: each of the three scope tokens passes through byte for byte when it already matches the ASCII identifier grammar;
    otherwise binding creation is refused `field_invalid` at `scope.<name>` (first in sorted order), at the `projection` stage. No normalization,
    transliteration, case folding, truncation or hashing is ever applied. Returns a plain copy."""
    try:
        d = _plain(statement_scope)
    except IdentityRefusal:
        _projection_refusal("scope")
    if type(d) is not dict or set(d) != set(SCOPE_MEMBERS):
        _projection_refusal("scope")
    for k in sorted(SCOPE_MEMBERS):
        v = d[k]
        if not (type(v) is str and _ascii_match(_IDENT, v)):
            _projection_refusal("scope." + k)
    return {k: d[k] for k in SCOPE_MEMBERS}


def project_snapshot_version(version: Any) -> int:
    """A verified snapshot version the binding cannot carry (above 2^53 - 1, or not a strict int in range) refuses `field_invalid` at
    `trust_snapshot_version` at the PROJECTION stage. The ingest-stage bound (N-10(c)) is applied earlier, in `trust_snapshot_from_verified`; this is the second line of defence."""
    lo, hi = INTEGER_RANGES["trust_snapshot_version"]
    if not _in_range(version, lo, hi):
        _projection_refusal("trust_snapshot_version", expected_range=(lo, hi))
    return version


# The five projection kinds of spec 5.6 and the entry point that tags each (a refusal reaches the projection stage ONLY through these):
#   scope_token -> project_scope; trust_snapshot_version -> project_snapshot_version;
#   effective_family_unsupported / effective_contract_unsupported / effective_payload_field_invalid -> project_effective_policy_digest.
PROJECTION_REFUSAL_KINDS = ("scope_token", "trust_snapshot_version", "effective_family_unsupported", "effective_contract_unsupported",
                            "effective_payload_field_invalid")


PROJECTION_REFUSAL_CODES = frozenset(("field_invalid", "family_unsupported", "contract_unsupported"))  # the codes of the five kinds above


def _text_or_none(v: Any) -> Any:
    """Only an exact `str` can name a participation, state or determination; anything else (a subclass with a lying `__eq__`, an unhashable) is NONE,
    which every branch below treats as unknown."""
    return v if type(v) is str else None


def projection_effect(participation: Any, activation_state: Any, determination: Any) -> dict:
    """Effect of a refusal at the projection stage (ruling N-5). Binding creation is refused for EVERY participation and kind; this function takes
    no refusal kind. It never yields `overlay_not_applied` and never ACCEPTs by itself. `required` refuses (UNKNOWN_FAIL_CLOSED when the activation
    state is `indeterminate`); `optional` falls back ONLY for (`permits_optional`, `authenticated`). Any other participation (including a non-str) is
    refused `field_invalid` at `participation` (a raise, so the rule survives python -O). An unknown or non-str state or determination never permits a
    fallback (REFUSE).
    PROPOSED (N-12): optional with `indeterminate` state is UNKNOWN_FAIL_CLOSED; the evidence record layout is owned by EXT-S4 (N-7)."""
    participation, activation_state, determination = _text_or_none(participation), _text_or_none(activation_state), _text_or_none(determination)
    if participation == "required":
        outcome = "UNKNOWN_FAIL_CLOSED" if activation_state == "indeterminate" else "REFUSE"
        return {"effect_outcome": outcome, "decision_kind": "required_policy_unavailable", "fallback_permitted": False, "fallback_evidence": None}
    if participation != "optional":
        _refuse("field_invalid", "participation")
    if activation_state == "indeterminate":
        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None, "fallback_permitted": False, "fallback_evidence": None}
    if determination == "authenticated" and activation_state == "permits_optional":
        return {"effect_outcome": "optional_fallback_via_determination", "decision_kind": None, "fallback_permitted": True,
                "fallback_evidence": {"kind": "absence_or_withdrawal", "projection_refusal_code": "field_invalid"}}
    return {"effect_outcome": "REFUSE", "decision_kind": None, "fallback_permitted": False, "fallback_evidence": None}


def projection_effect_for(refusal_code: str, participation: Any, activation_state: Any, determination: Any) -> dict:
    """Join a refusal's own code with the single effect function: the code is the only thing a refusal contributes (to the fallback evidence). The code
    is a programmer argument: anything but one of the three codes the five projection-refusal kinds use (`PROJECTION_REFUSAL_CODES`) is a ValueError, never a
    typed refusal, so a durable-state code (`store_unknown`, `policy_identity_mismatch`, `not_activated`, ...) can never be turned into a fallback."""
    if type(refusal_code) is not str or refusal_code not in PROJECTION_REFUSAL_CODES:
        raise ValueError("refusal code is not a projection-refusal code (got a %s)" % type(refusal_code).__name__)
    out = projection_effect(participation, activation_state, determination)
    if out["fallback_evidence"] is not None:
        out = {**out, "fallback_evidence": {**out["fallback_evidence"], "projection_refusal_code": refusal_code}}
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Scope key (spec 5.7)
# ----------------------------------------------------------------------------------------------------------------------
_SCOPE_KEY_TOP = ("scope_key_profile",) + SCOPE_KEY_MEMBERS


def validate_scope_key(doc: Any) -> dict:
    """Return a private plain copy of a well-formed scope-key object, else raise IdentityRefusal."""
    d = _plain(doc)
    if type(d) is not dict:
        _type_refusal(None, d)
    missing = set(_SCOPE_KEY_TOP) - set(d)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(d) - set(_SCOPE_KEY_TOP)
    if unknown:
        _refuse("field_unknown", min(unknown))
    for k in sorted(d):
        if type(d[k]) is not str:
            _type_refusal(k, d[k])
    for k in sorted(d):
        if k == "scope_key_profile":
            if d[k] != SCOPE_KEY_PROFILE:
                _refuse("field_invalid", k)
        elif not _ascii_match(_IDENT, d[k]):
            _refuse("field_invalid", k)
    return d


def scope_key_bytes(doc: dict) -> bytes:
    return canonical_json_bytes(validate_scope_key(doc))


def scope_key_digest(doc: dict) -> str:
    return _sha(SCOPE_KEY_PREFIX, validate_scope_key(doc))


def scope_key_from_binding(binding: dict) -> dict:
    """The versioned canonical scope-key object of a COMPLETED binding. Never a delimiter-joined string."""
    b = validate_binding(binding)
    s = b["scope"]
    return {"scope_key_profile": SCOPE_KEY_PROFILE, "tenant": s["tenant"], "institution": s["institution"], "authority_domain": s["authority_domain"],
            "consumer_id": b["consumer_id"], "operation": b["operation"], "family": b["family"], "selection_id": b["selection_id"]}


# ----------------------------------------------------------------------------------------------------------------------
# Effective policy identity (spec 6): module-owned four-row `r08-v2` table; family_version is derived, never an input
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class FamilyRow:
    family: str
    family_version: str
    kind: str  # lists | ints | classmap
    members: Tuple[str, ...]


_F1AB_MEMBERS = ("allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains")
IDENTITY_FAMILIES = MappingProxyType({
    "f1a-local-execution-allowlist": FamilyRow("f1a-local-execution-allowlist", "v1", "lists", ("allowed_actions", "allowed_adapters", "allowed_units")),
    "f1ab-local-execution-allowlist": FamilyRow("f1ab-local-execution-allowlist", "v2", "lists", _F1AB_MEMBERS),
    "f4-control-plane-age-bounds": FamilyRow("f4-control-plane-age-bounds", "v2", "ints", ("status_max_age_seconds", "approval_max_age_seconds")),
    "f5-action-class-age-bounds": FamilyRow("f5-action-class-age-bounds", "v2", "classmap", ("class_status_max_age_seconds",)),
})
REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)  # an identity exists for `r08-v2` only; `r08-v1` and anything else is `contract_unsupported`


def registered_family_version(family: Any, contract_version: Any) -> str:
    """Look up the derived tag from the module's own table, keyed by the authenticated record's family id and contract_version (ruling N-3). A non-str
    `family` or `contract_version` is `field_type_invalid` at its own member on every entry point (spec 6); an unregistered str is `family_unsupported`
    or `contract_unsupported`."""
    if type(family) is not str:
        _type_refusal("family", family)
    if type(contract_version) is not str:
        _type_refusal("contract_version", contract_version)
    if family not in IDENTITY_FAMILIES:
        _refuse("family_unsupported", "family")
    if contract_version not in REGISTERED_CONTRACT_VERSIONS:
        _refuse("contract_unsupported", "contract_version")
    return IDENTITY_FAMILIES[family].family_version


def validate_effective_payload(family: Any, payload: Any, role: str = "effective") -> dict:
    """Strict validator of a composed (role `effective`) or input (`registry`, `caller`) family payload; returns a private plain copy. Phases: family,
    shape (missing, unknown), types, values; sorted path order inside a phase. Lists: sorted by code point, duplicate-free, at most 256 entries, tokens
    per `frozen_token_valid` (the pinned Unicode 15.1.0 table, N-13; no host Unicode database); `[]` is an explicit deny-all. Ages: strict ints in the role's range.
    A non-str family is `field_type_invalid`. `role` is a programmer argument (ValueError if unknown)."""
    if type(role) is not str or role not in AGE_RANGES:
        raise ValueError("unknown role (got a %s)" % type(role).__name__)
    if type(family) is not str:
        _type_refusal("family", family)
    if family not in IDENTITY_FAMILIES:
        _refuse("family_unsupported", "family")
    row = IDENTITY_FAMILIES[family]
    d = _plain(payload)
    if type(d) is not dict:
        _type_refusal(None, d)
    members = set(row.members)
    missing = members - set(d)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(d) - members
    if unknown:
        _refuse("field_unknown", min(unknown))
    flat = {}
    for k in d:
        if row.kind == "classmap" and type(d[k]) is dict:
            for cls, v in d[k].items():
                flat[k + "." + cls] = v
        else:
            flat[k] = d[k]
    for path in sorted(flat):
        v = flat[path]
        if row.kind == "lists":
            if type(v) is not list or not all(type(x) is str for x in v):
                _type_refusal(path, v)
        elif row.kind == "ints":
            if not _int_typed(v):
                _type_refusal(path, v)
        elif path == "class_status_max_age_seconds" or not _int_typed(v):
            _type_refusal(path, v)
    lo, hi = AGE_RANGES[role]
    for path in sorted(flat):
        v = flat[path]
        if row.kind == "lists":
            if len(v) > MAX_LIST_ENTRIES or not all(frozen_token_valid(x) for x in v) or v != sorted(set(v)):
                _refuse("field_invalid", path)
        elif not _in_range(v, lo, hi):
            _range_refusal(path, lo, hi)
    if row.kind == "classmap":
        classes = d["class_status_max_age_seconds"]
        if not classes or not all(frozen_token_valid(k) for k in classes):
            _refuse("field_invalid", "class_status_max_age_seconds")
    return d


def _deny_all(family: str, plain_payload: dict) -> list:
    """Private: the deny-all dimensions of an already validated plain payload of a registered family."""
    if IDENTITY_FAMILIES[family].kind != "lists":
        return []
    return sorted(k for k, v in plain_payload.items() if v == [])


def deny_all_dimensions(family: Any, payload: Any) -> list:
    """The sorted names of the payload's empty-list (explicit deny-all) dimensions; `[]` for a family that has no lists. Public, so it takes hostile
    input like every other entry point: a non-str family is `field_type_invalid`, an unregistered one `family_unsupported`, a payload that is not a
    plain dict is refused by `_plain` / `field_type_invalid`. Nothing but `IdentityRefusal` escapes."""
    if type(family) is not str:
        _type_refusal("family", family)
    if family not in IDENTITY_FAMILIES:
        _refuse("family_unsupported", "family")
    d = _plain(payload)
    if type(d) is not dict:
        _type_refusal(None, d)
    return _deny_all(family, d)


def effective_preimage(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> dict:
    """The digest preimage. `family_version` is derived from the module table; no parameter or payload member can supply it."""
    version = registered_family_version(family, contract_version)
    plain_payload = validate_effective_payload(family, payload)
    return {"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": contract_version, "family": family, "family_version": version,
            "deny_all": _deny_all(family, plain_payload), "effective": plain_payload}


def effective_digest_of_preimage(preimage: dict) -> str:
    """Digest of a preimage; the input goes through the same bounded copy as every other entry point. It is NOT re-validated here (use
    `validate_preimage` first)."""
    return _sha(EFFECTIVE_PREFIX, preimage)


def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> str:
    return effective_digest_of_preimage(effective_preimage(family, payload, contract_version))


_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported", "field_invalid"))


def project_effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> str:
    """The digest derivation at the PROJECTION stage (spec 5.6, kinds `effective_family_unsupported`, `effective_contract_unsupported`,
    `effective_payload_field_invalid`): the same result as `effective_policy_digest`, but a `family_unsupported`, `contract_unsupported` or
    `field_invalid` refusal is re-raised with stage `projection` and evidence `projection_refusal_code` (the member and the rest of the evidence are
    kept), so `projection_effect` / `mapping_row_for` read it as a projection refusal. Every other refusal (missing, unknown, type, size, depth) passes
    through unchanged: the spec lists no projection kind for it."""
    try:
        return effective_policy_digest(family, payload, contract_version)
    except IdentityRefusal as e:
        if e.code not in _PROJECTION_DERIVATION_CODES:
            raise
        raise IdentityRefusal(e.code, e.member, "projection", {**e.evidence, "projection_refusal_code": e.code}) from None


def preimage_from_inputs(doc: Any) -> dict:
    """The only consumer-facing input form: {family, contract_version, effective}, family and contract_version taken from the authenticated record.
    Any `family_version` member (whatever its value) is `field_unknown`. Order: member set (missing, unknown), registered lookup (family, then
    contract_version), then the payload. Returns the derived preimage."""
    top = ("contract_version", "effective", "family")
    d = _plain(doc)
    if type(d) is not dict:
        _type_refusal(None, d)
    missing = set(top) - set(d)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(d) - set(top)
    if unknown:
        _refuse("field_unknown", min(unknown))
    return effective_preimage(d["family"], d["effective"], d["contract_version"])


def validate_preimage(doc: Any) -> dict:
    """A presented preimage must equal the one rebuilt from its own family and payload; its tags are compared with the registered ones, never trusted.
    Returns a private plain copy."""
    top = ("contract_version", "deny_all", "effective", "effective_policy_profile", "family", "family_version")
    d = _plain(doc)
    if type(d) is not dict:
        _type_refusal(None, d)
    missing = set(top) - set(d)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(d) - set(top)
    if unknown:
        _refuse("field_unknown", min(unknown))
    if d["effective_policy_profile"] != EFFECTIVE_PROFILE:
        _refuse("field_invalid", "effective_policy_profile")
    registered = registered_family_version(d["family"], d["contract_version"])
    validate_effective_payload(d["family"], d["effective"])
    if d["family_version"] != registered:
        _refuse("field_invalid", "family_version")
    if d["deny_all"] != _deny_all(d["family"], d["effective"]):
        _refuse("field_invalid", "deny_all")
    return d


# ----------------------------------------------------------------------------------------------------------------------
# Typed refusal mapping (spec 8.1): (verdict class, registry code, decision kind, retry, evidence fields)
# Generated from the vector file's `defect_mapping`; tests/test_ext_s1_5_identity_module.py asserts equality with it. Rows whose code is a
# ruled additive code (not_activated, policy_identity_mismatch, store_unknown), the two non-Registry rows (deny_all, evaluator_denial) and the two
# rows of the v2-only codes that `tests/test_r08v2_family_dispatch.py` keeps out of every module of this package until the package that implements
# them lands (the withdrawal row and the snapshot-floor row) are NOT here: this module emits none of those codes. PROPOSED rows: trust_snapshot_invalid (REFUSE class), trust_snapshot_missing (N-11, two stages).
# ----------------------------------------------------------------------------------------------------------------------
VERDICT_CLASSES = ("ACCEPT", "REFUSE", "REFUSE_STALE", "UNKNOWN_FAIL_CLOSED")
EVIDENCE_STAGE_VERSION = "ocs-evidence-stage/1"  # ruling N-11: the evidence stage is typed and versioned
EVIDENCE_STAGES = ("INPUT", "DURABLE_STATE")
# The merged vector file (PR #35) spells the two typed stage values `INPUT` and `DURABLE_STATE`; the mapping uses them as the row's `stage_value`.
STAGE_TYPES = MappingProxyType({"INPUT": "INPUT", "DURABLE_STATE": "DURABLE_STATE"})


@dataclass(frozen=True)
class MappingRow:
    row_id: str
    verdict_class: str
    registry_code: str
    decision_kind: str
    retry: str
    evidence_fields: Tuple[str, ...]
    stage_value: Any = None
    optional_overlay: bool = False  # only through an authenticated optional-state determination (contract 7.4 line 8(c)); never by the refusal alone
    proposed: bool = False  # True for a row (verdict class or stage split) that is a PROPOSAL of this PR, not an Architect ruling

    @property
    def evidence_stage(self) -> Any:
        """The TYPED evidence stage of a `trust_snapshot_missing` row (ruling N-11): `INPUT` (no required snapshot supplied) or `DURABLE_STATE` (no applicable
        trusted snapshot accepted in authoritative durable state); None for every other row. The two are different underlying conditions under one code."""
        return STAGE_TYPES.get(self.stage_value) if self.registry_code == "trust_snapshot_missing" else None

    @property
    def stage_version(self) -> Any:
        return EVIDENCE_STAGE_VERSION if self.evidence_stage is not None else None


REFUSAL_MAPPING = (
    MappingRow("MP-input_not_text", "REFUSE", "input_not_text", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-input_too_large", "REFUSE", "input_too_large", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-json_malformed", "REFUSE", "json_malformed", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-json_duplicate_key", "REFUSE", "json_duplicate_key", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-json_number_unsupported", "REFUSE", "json_number_unsupported", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-json_nesting_too_deep", "REFUSE", "json_nesting_too_deep", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-field_missing", "REFUSE", "field_missing", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-field_unknown", "REFUSE", "field_unknown", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-field_type_invalid", "REFUSE", "field_type_invalid", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member", "observed_value_class",),),
    MappingRow("MP-field_invalid-identifier", "REFUSE", "field_invalid", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-field_invalid-integer", "REFUSE", "field_invalid", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member", "expected_range",),),
    MappingRow("MP-field_invalid-projection", "REFUSE", "field_invalid", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member", "original_selection_digest", "projection_refusal_code",),),
    MappingRow("MP-digest_mismatch", "REFUSE", "digest_mismatch", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "carried_digest", "recomputed_digest",),),
    MappingRow("MP-family_unsupported", "REFUSE", "family_unsupported", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-contract_unsupported", "REFUSE", "contract_unsupported", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-composition_caller_invalid", "REFUSE", "composition_caller_invalid", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "member",),),
    MappingRow("MP-selection_epoch_stale", "REFUSE_STALE", "selection_epoch_stale", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch", "high_water_epoch", "min_epoch_floor", "selection_digest",),),
    MappingRow("MP-trust_snapshot_invalid", "REFUSE", "trust_snapshot_invalid", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "trust_snapshot_version", "member",), proposed=True),
    MappingRow("MP-selection_revoked", "REFUSE", "selection_revoked", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch", "selection_digest",),),
    MappingRow("MP-issuer_key_revoked", "REFUSE", "issuer_key_revoked", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch",),),
    MappingRow("MP-selection_expired", "REFUSE", "selection_expired", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch",),),  # N-12(c) RULED: expiry is never a fallback basis (REFUSE); only an independently authenticated never-required or withdrawn state is
    MappingRow("MP-selection_not_yet_effective", "REFUSE", "selection_not_yet_effective", "required_policy_unavailable", "after_validity_window_opens",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch",),),
    MappingRow("MP-participation_mismatch", "REFUSE", "participation_mismatch", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id",),),
    MappingRow("MP-selection_conflict", "REFUSE", "selection_conflict", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch", "selection_digest",),),
    MappingRow("MP-trust_snapshot_missing-input", "UNKNOWN_FAIL_CLOSED", "trust_snapshot_missing", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "stage_version", "trust_snapshot_version",), stage_value="INPUT", proposed=True),
    MappingRow("MP-trust_snapshot_missing-durable-state", "UNKNOWN_FAIL_CLOSED", "trust_snapshot_missing", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "stage_version", "scope_key_digest", "trust_snapshot_version",), stage_value="DURABLE_STATE", proposed=True),
    MappingRow("MP-trust_snapshot_expired-delivered", "REFUSE", "trust_snapshot_expired", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "trust_snapshot_version",),),
    MappingRow("MP-trust_snapshot_expired-guard", "UNKNOWN_FAIL_CLOSED", "trust_snapshot_expired", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "trust_snapshot_version",),),
    # Revision-2 codes (`r08-v2-reasons/2`, Amendment 1; rulings 4.3, N-12). None of the three has an optional overlay: an optional scope under an unknown store is
    # HOLD, and a refused identity is never an optional fallback (N-12). The guard that raises them (and its comparison order) is EXT-S4-2, not this module.
    MappingRow("MP-store_unknown", "UNKNOWN_FAIL_CLOSED", "store_unknown", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "unknown_cause",),),
    MappingRow("MP-not_activated", "REFUSE", "not_activated", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id",),),
    MappingRow("MP-policy_identity_mismatch", "REFUSE", "policy_identity_mismatch", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "member", "selection_id", "selection_epoch", "high_water_epoch",
                "selection_digest", "record_id", "record_version", "record_digest", "activation_ref",),),
)
MAPPING_BY_ID = MappingProxyType({r.row_id: r for r in REFUSAL_MAPPING})


def mapping_rows_for(code: str) -> Tuple[MappingRow, ...]:
    return tuple(r for r in REFUSAL_MAPPING if r.registry_code == code)


def verdict_for(code: str, stage: Any = None) -> MappingRow:
    """The unique mapping row for a registry code (and, for the codes with several rows, a stage); a code with no row, or with several rows the stage
    does not single out, raises KeyError. `trust_snapshot_missing` has two rows (stage `INPUT` / `DURABLE_STATE`) and `trust_snapshot_expired` two (use
    `MAPPING_BY_ID`); `field_invalid` has three (use `mapping_row_for`, which reads a refusal's own stage and evidence)."""
    rows = mapping_rows_for(code) if type(code) is str else ()
    if stage is not None:
        if type(stage) is not str:  # a hostile `stage` (e.g. a raising `__eq__`) must neither be called nor reach a row: no match
            raise KeyError((code, "<non-string stage>"))
        rows = tuple(r for r in rows if r.stage_value == stage)
    if len(rows) != 1:
        raise KeyError((code, stage))
    return rows[0]


def mapping_row_for(refusal: IdentityRefusal) -> MappingRow:
    """The spec 8.1 row for a refusal this module raised. `field_invalid` is split by the refusal's own data: stage `projection` selects
    MP-field_invalid-projection; an `expected_range` in its evidence selects MP-field_invalid-integer; anything else is MP-field_invalid-identifier.
    A code with a single row (family_unsupported and contract_unsupported included, whatever their stage, projection among them) maps to that row; a
    code with several rows is singled out by the refusal's stage. A code with no row raises KeyError (the codes in UNMAPPED_CODES are
    not mapped by this module)."""
    if refusal.code == "field_invalid":
        if type(refusal.stage) is str and refusal.stage == "projection":
            return MAPPING_BY_ID["MP-field_invalid-projection"]
        return MAPPING_BY_ID["MP-field_invalid-integer" if "expected_range" in refusal.evidence else "MP-field_invalid-identifier"]
    rows = mapping_rows_for(refusal.code)
    if len(rows) == 1:
        return rows[0]
    return verdict_for(refusal.code, refusal.stage)


def _check_module_tables() -> None:
    used = {r.registry_code for r in REFUSAL_MAPPING}
    if not used <= set(CODES_V2_REV2):
        raise RuntimeError("mapping uses a code outside CODES_V2_REV2: %s" % sorted(used - set(CODES_V2_REV2)))
    if not all(r.verdict_class in VERDICT_CLASSES for r in REFUSAL_MAPPING):
        raise RuntimeError("mapping uses a verdict class outside the closed vocabulary")


UNMAPPED_CODES = frozenset(CODES_V2_REV2) - {r.registry_code for r in REFUSAL_MAPPING}
# `UNMAPPED_CODES` is the explicit remainder of the 51 revision-2 codes (codes owned by another package, plus the two v2-only codes of `V2_ADDED_CODES` whose
# owning contracts and evaluators are not in this package); a test pins it so a mapping change is visible, and the
# revision-2 outcome map (docs/p1-extraction-plan/data/ld02-outcome-map-rev2.json) is the 51-code completeness artifact.

_check_module_tables()
