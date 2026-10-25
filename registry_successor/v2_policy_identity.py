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
  * the typed refusal mapping of spec 8.1 for the codes that already exist in `CODES_V2`.

Not in this module: composition of registry and caller values (EXT-S1-4), any store, activation state or `activation_sequence` (EXT-S4), the Control
Plane or Runtime guards, and the three ruled additive codes (`not_activated`, `policy_identity_mismatch`, `store_unknown`) and `CODES_V2_REV2`
(Amendment 1, PR #32): every refusal here uses a code that is already in `CODES_V2`. The mapping rows for the additive codes are therefore absent
from `REFUSAL_MAPPING` and are to be wired in when the amendment lands.

Items the spec still lists as OPEN are implemented at the spec's current PROPOSED behaviour and are marked `PROPOSED` below; they are not decisions:
N-10 (syntax-first parse order, byte-level input boundary, no verifier ceiling), N-11 (`trust_snapshot_missing`: one code, two stages), N-12 (an
optional scope with an unknown store is UNKNOWN_FAIL_CLOSED; a refused projection never counts as an activation determination), N-13 (the token
rule follows the platform Unicode database through `common.valid_token`).

Pure: no files, no clock, no state. Digests give integrity, never authentication.
"""
import hashlib
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Dict, Tuple

from . import common as c
from .v2_codes import CODES_V2

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
_MAX_EXACT_DIGITS = 20  # every range below is under 20 digits; longer integer literals are classified by length and never converted
_OUT_OF_RANGE = 10 ** 40

# Per-field integer domains (spec 5.2). Each field has its OWN literal on purpose; they are equal today and independent by ruling OQ-1.
INTEGER_RANGES: Dict[str, Tuple[int, int]] = {
    "record_version": (1, 2147483647),
    "selection_epoch": (1, 2147483647),
    "trust_snapshot_version": (1, 9007199254740991),  # N-1: component-owner-derived (no source ceiling); N-10(c) verifier ceiling still OPEN
}
AGE_RANGES: Dict[str, Tuple[int, int]] = {
    "registry": (1, 2147483647),
    "caller": (0, 2147483647),
    "effective": (0, 2147483647),
}

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
    """A typed refusal: `code` is an existing `CODES_V2` entry, `member` the first failing member path (or None)."""

    def __init__(self, code: str, member: Any = None):
        if code not in CODES_V2:  # a raise, not an assert: this must hold under python -O
            raise ValueError("refusal code outside CODES_V2: %r" % (code,))
        super().__init__(code)
        self.code = code
        self.member = member

    @property
    def layer(self) -> str:
        return CODES_V2[self.code][0]


def _refuse(code: str, member: Any = None):
    raise IdentityRefusal(code, member)


# ----------------------------------------------------------------------------------------------------------------------
# Canonical JSON and digests (spec 5.3, 5.4)
# ----------------------------------------------------------------------------------------------------------------------
_SHORT = {0x22: '\\"', 0x5C: "\\\\", 0x08: "\\b", 0x0C: "\\f", 0x0A: "\\n", 0x0D: "\\r", 0x09: "\\t"}


def _unit(u: int) -> str:
    return "\\u%04x" % u


def _serialize_string(s: str) -> str:
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


def _serialize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return _serialize_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(_serialize(x) for x in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(_serialize_string(k) + ":" + _serialize(value[k]) for k in sorted(value)) + "}"
    raise TypeError("unsupported type for canonical serialization: %r" % type(value))


def canonical_json_bytes(value: Any) -> bytes:
    """Canonical JSON: keys sorted by Unicode code point, no whitespace, every code point outside U+0020..U+007E escaped (lowercase hex, surrogate
    pairs above U+FFFF), so the output is pure ASCII. Only None, bool, int, str, list and dict are serializable (TypeError otherwise)."""
    return _serialize(value).encode("ascii")


def _sha(prefix: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(prefix + canonical_json_bytes(value)).hexdigest()


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
_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}
_HEX = frozenset("0123456789abcdefABCDEF")


def _int_literal(text: str) -> int:
    digits = text.lstrip("-")
    if len(digits) <= _MAX_EXACT_DIGITS:
        return int(text)
    return -_OUT_OF_RANGE if text.startswith("-") else _OUT_OF_RANGE


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
    not stripped and an integer literal of any length is valid syntax (classified by length, never converted when long)."""
    if isinstance(raw, (bytes, bytearray)):
        data = bytes(raw)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            _refuse("input_not_text")
    elif isinstance(raw, str):
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
    return isinstance(v, int) and not isinstance(v, bool)


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
    """Return `doc` if it is a well-formed completed binding, else raise IdentityRefusal. Phases (first failure wins, sorted path order inside a
    phase): object, scope object, missing members, unknown members, types, values. The top-level set (14 plain members plus `scope`) and the nested
    `scope` set (tenant, institution, authority_domain) are checked as TWO sets, before flattening."""
    if not isinstance(doc, dict):
        _refuse("field_type_invalid")
    has_scope = "scope" in doc
    nested = doc["scope"] if has_scope else None
    if has_scope and not isinstance(nested, dict):
        _refuse("field_type_invalid", "scope")
    missing = set(TOP_MEMBERS) - {"scope"} - set(doc)
    if not has_scope:
        missing.add("scope")
    else:
        missing |= {"scope." + k for k in SCOPE_MEMBERS if k not in nested}
    if missing:
        _refuse("field_missing", min(missing))
    unknown = {k for k in doc if k not in TOP_MEMBERS}
    unknown |= {"scope." + k for k in nested if k not in SCOPE_MEMBERS}
    if unknown:
        _refuse("field_unknown", min(unknown))
    flat = _flatten_checked(doc)
    for path in sorted(flat):
        v = flat[path]
        if path in _INT_PATHS:
            if not _is_int(v):
                _refuse("field_type_invalid", path)
        elif not isinstance(v, str):
            _refuse("field_type_invalid", path)
    for path in sorted(flat):
        v = flat[path]
        if path in _INT_PATHS:
            lo, hi = INTEGER_RANGES[path]
            if not lo <= v <= hi:
                _refuse("field_invalid", path)
        elif path in _ID_PATHS:
            if not _ascii_match(_IDENT, v):
                _refuse("field_invalid", path)
        elif path in _DIGEST_PATHS:
            if not _ascii_match(_DIGEST, v):
                _refuse("field_invalid", path)
        elif path == "binding_profile" and v != BINDING_PROFILE:
            _refuse("field_invalid", path)
    return doc


def parse_binding(raw: Any) -> dict:
    """Load and validate a completed binding document in one step (the loader and validator are separate public functions as well)."""
    return validate_binding(load_document(raw))


def canonical_binding_bytes(binding: dict) -> bytes:
    return canonical_json_bytes(validate_binding(binding))


def checked_binding_digest(binding: dict) -> str:
    """Validate, then digest. Use this, not `binding_digest`, on anything that did not come from `validate_binding`."""
    return binding_digest(validate_binding(binding))


def verify_carried_binding_digest(binding: dict, carried: Any) -> str:
    """Guard check: a carried digest string is format-checked (`field_invalid`) and compared with the recomputed value (`digest_mismatch`)."""
    recomputed = checked_binding_digest(binding)
    if not (isinstance(carried, str) and _ascii_match(_DIGEST, carried)):
        _refuse("field_invalid")
    if carried != recomputed:
        _refuse("digest_mismatch")
    return recomputed


# ----------------------------------------------------------------------------------------------------------------------
# Trust snapshot fingerprint (spec 7)
# ----------------------------------------------------------------------------------------------------------------------
_SNAPSHOT_MEMBERS = ("issuers", "min_epochs", "revoked_key_ids", "revoked_selections", "snapshot_id", "valid_until", "version")


def _is_pair(p: Any, second_is_int: bool) -> bool:
    if not (isinstance(p, (list, tuple)) and len(p) == 2 and isinstance(p[0], str)):
        return False
    return _is_int(p[1]) if second_is_int else True


def _snapshot_shape_ok(s: Any) -> bool:
    if not (isinstance(s, dict) and set(s) == set(_SNAPSHOT_MEMBERS)):
        return False
    if not (isinstance(s["issuers"], list) and isinstance(s["revoked_key_ids"], list) and isinstance(s["revoked_selections"], list)
            and isinstance(s["min_epochs"], list)):
        return False
    if not all(isinstance(i, dict) and isinstance(i.get("key_id"), str) and isinstance(i.get("authority"), list) for i in s["issuers"]):
        return False
    return (all(isinstance(k, str) for k in s["revoked_key_ids"]) and all(_is_pair(p, True) for p in s["revoked_selections"])
            and all(_is_pair(p, True) for p in s["min_epochs"]))


def normalize_snapshot(snapshot: dict) -> dict:
    """Normalized form: issuers by key_id, each `authority` array sorted, revoked_key_ids sorted, revoked_selections by (selection id, integer epoch),
    min_epochs by selection id. Never mutates the input. A malformed snapshot is `trust_snapshot_invalid` (PROPOSED REFUSE class)."""
    if not _snapshot_shape_ok(snapshot):
        _refuse("trust_snapshot_invalid")
    out = {k: snapshot[k] for k in snapshot}
    out["issuers"] = sorted(({**i, "authority": sorted(i["authority"])} for i in snapshot["issuers"]), key=lambda i: i["key_id"])
    out["revoked_key_ids"] = sorted(snapshot["revoked_key_ids"])
    out["revoked_selections"] = sorted(([p[0], p[1]] for p in snapshot["revoked_selections"]), key=lambda p: (p[0], p[1]))
    out["min_epochs"] = sorted(([p[0], p[1]] for p in snapshot["min_epochs"]), key=lambda p: p[0])
    return out


def check_snapshot_duplicates(snapshot: dict) -> None:
    """Duplicate issuer key ids, min_epoch ids, revoked selection pairs or revoked key ids refuse `trust_snapshot_invalid` (PROPOSED REFUSE class)."""
    if not _snapshot_shape_ok(snapshot):
        _refuse("trust_snapshot_invalid")
    keys = [i["key_id"] for i in snapshot["issuers"]]
    floors = [p[0] for p in snapshot["min_epochs"]]
    pairs = [(p[0], p[1]) for p in snapshot["revoked_selections"]]
    revoked = list(snapshot["revoked_key_ids"])
    if len(set(keys)) != len(keys) or len(set(floors)) != len(floors) or len(set(pairs)) != len(pairs) or len(set(revoked)) != len(revoked):
        _refuse("trust_snapshot_invalid")


def trust_snapshot_fingerprint(snapshot: dict) -> str:
    """`sha256:` + plain digest of the normalized snapshot's canonical (ASCII) bytes; no domain prefix (contract section 5)."""
    check_snapshot_duplicates(snapshot)
    try:
        return plain_digest(normalize_snapshot(snapshot))
    except TypeError:
        _refuse("trust_snapshot_invalid")


# ----------------------------------------------------------------------------------------------------------------------
# Projection from verified inputs (spec 5.6)
# ----------------------------------------------------------------------------------------------------------------------
def project_scope(statement_scope: Any) -> dict:
    """IDENTITY projection: each of the three scope tokens passes through byte for byte when it already matches the ASCII identifier grammar;
    otherwise binding creation is refused `field_invalid` at `scope.<name>` (first in sorted order). No normalization, transliteration, case folding,
    truncation or hashing is ever applied."""
    if not isinstance(statement_scope, dict) or set(statement_scope) != set(SCOPE_MEMBERS):
        _refuse("field_invalid", "scope")
    for k in sorted(SCOPE_MEMBERS):
        v = statement_scope[k]
        if not (isinstance(v, str) and _ascii_match(_IDENT, v)):
            _refuse("field_invalid", "scope." + k)
    return {k: statement_scope[k] for k in SCOPE_MEMBERS}


def project_snapshot_version(version: Any) -> int:
    """A verified snapshot version the binding cannot carry (above 2^53 - 1, or not a strict int in range) refuses `field_invalid` at
    `trust_snapshot_version` at the projection stage. Whether the verifier should also cap it is OPEN (N-10(c)); this is the projection-stage rule."""
    lo, hi = INTEGER_RANGES["trust_snapshot_version"]
    if not _is_int(version) or not lo <= version <= hi:
        _refuse("field_invalid", "trust_snapshot_version")
    return version


PROJECTION_REFUSAL_KINDS = ("scope_token", "trust_snapshot_version", "effective_family_unsupported", "effective_contract_unsupported",
                            "effective_payload_field_invalid")


def projection_effect(participation: Any, activation_state: Any, determination: Any) -> dict:
    """Effect of a refusal at the projection stage (ruling N-5). Binding creation is refused for EVERY participation and kind; this function takes
    no refusal kind. It never yields `overlay_not_applied` and never ACCEPTs by itself. `required` refuses (UNKNOWN_FAIL_CLOSED when the activation
    state is `indeterminate`); `optional` falls back ONLY for (`permits_optional`, `authenticated`). Any other participation is refused
    `field_invalid` at `participation` (a raise, so the rule survives python -O).
    PROPOSED (N-12): optional with `indeterminate` state is UNKNOWN_FAIL_CLOSED; the evidence record layout is owned by EXT-S4 (N-7)."""
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
    """Join a refusal's own code with the single effect function: the code is the only thing a refusal contributes (to the fallback evidence)."""
    if refusal_code not in CODES_V2:
        raise ValueError("refusal code outside CODES_V2: %r" % (refusal_code,))
    out = projection_effect(participation, activation_state, determination)
    if out["fallback_evidence"] is not None:
        out = {**out, "fallback_evidence": {**out["fallback_evidence"], "projection_refusal_code": refusal_code}}
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Scope key (spec 5.7)
# ----------------------------------------------------------------------------------------------------------------------
_SCOPE_KEY_TOP = ("scope_key_profile",) + SCOPE_KEY_MEMBERS


def validate_scope_key(doc: Any) -> dict:
    if not isinstance(doc, dict):
        _refuse("field_type_invalid")
    missing = set(_SCOPE_KEY_TOP) - set(doc)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(doc) - set(_SCOPE_KEY_TOP)
    if unknown:
        _refuse("field_unknown", min(unknown))
    for k in sorted(doc):
        if not isinstance(doc[k], str):
            _refuse("field_type_invalid", k)
    for k in sorted(doc):
        if k == "scope_key_profile":
            if doc[k] != SCOPE_KEY_PROFILE:
                _refuse("field_invalid", k)
        elif not _ascii_match(_IDENT, doc[k]):
            _refuse("field_invalid", k)
    return doc


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
    """Look up the derived tag from the module's own table, keyed by the authenticated record's family id and contract_version (ruling N-3)."""
    if not isinstance(family, str) or family not in IDENTITY_FAMILIES:
        _refuse("family_unsupported", "family")
    if contract_version not in REGISTERED_CONTRACT_VERSIONS:
        _refuse("contract_unsupported", "contract_version")
    return IDENTITY_FAMILIES[family].family_version


def validate_effective_payload(family: Any, payload: Any, role: str = "effective") -> dict:
    """Strict validator of a composed (role `effective`) or input (`registry`, `caller`) family payload. Phases: family, shape (missing, unknown),
    types, values; sorted path order inside a phase. Lists: sorted by code point, duplicate-free, at most 256 entries, tokens per `common.valid_token`
    (platform Unicode database dependence: PROPOSED, N-13); `[]` is an explicit deny-all. Ages: strict ints in the role's range."""
    if role not in AGE_RANGES:
        raise ValueError("unknown role: %r" % (role,))
    if not isinstance(family, str) or family not in IDENTITY_FAMILIES:
        _refuse("family_unsupported", "family")
    row = IDENTITY_FAMILIES[family]
    if not isinstance(payload, dict):
        _refuse("field_type_invalid")
    members = set(row.members)
    missing = members - set(payload)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(payload) - members
    if unknown:
        _refuse("field_unknown", min(unknown))
    flat = {}
    for k in payload:
        if row.kind == "classmap" and isinstance(payload[k], dict):
            for cls, v in payload[k].items():
                flat[k + "." + cls] = v
        else:
            flat[k] = payload[k]
    for path in sorted(flat):
        v = flat[path]
        if row.kind == "lists":
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                _refuse("field_type_invalid", path)
        elif row.kind == "ints":
            if not _is_int(v):
                _refuse("field_type_invalid", path)
        elif path == "class_status_max_age_seconds" or not _is_int(v):
            _refuse("field_type_invalid", path)
    lo, hi = AGE_RANGES[role]
    for path in sorted(flat):
        v = flat[path]
        if row.kind == "lists":
            if len(v) > MAX_LIST_ENTRIES or not all(c.valid_token(x) for x in v) or v != sorted(set(v)):
                _refuse("field_invalid", path)
        elif not lo <= v <= hi:
            _refuse("field_invalid", path)
    if row.kind == "classmap":
        classes = payload["class_status_max_age_seconds"]
        if not classes or not all(c.valid_token(k) for k in classes):
            _refuse("field_invalid", "class_status_max_age_seconds")
    return payload


def deny_all_dimensions(family: str, payload: dict) -> list:
    if IDENTITY_FAMILIES[family].kind != "lists":
        return []
    return sorted(k for k, v in payload.items() if v == [])


def effective_preimage(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> dict:
    """The digest preimage. `family_version` is derived from the module table; no parameter or payload member can supply it."""
    version = registered_family_version(family, contract_version)
    validate_effective_payload(family, payload)
    return {"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": contract_version, "family": family, "family_version": version,
            "deny_all": deny_all_dimensions(family, payload), "effective": payload}


def effective_digest_of_preimage(preimage: dict) -> str:
    return _sha(EFFECTIVE_PREFIX, preimage)


def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> str:
    return effective_digest_of_preimage(effective_preimage(family, payload, contract_version))


def preimage_from_inputs(doc: Any) -> dict:
    """The only consumer-facing input form: {family, contract_version, effective}, family and contract_version taken from the authenticated record.
    Any `family_version` member (whatever its value) is `field_unknown`. Order: member set (missing, unknown), registered lookup (family, then
    contract_version), then the payload. Returns the derived preimage."""
    top = ("contract_version", "effective", "family")
    if not isinstance(doc, dict):
        _refuse("field_type_invalid")
    missing = set(top) - set(doc)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(doc) - set(top)
    if unknown:
        _refuse("field_unknown", min(unknown))
    if not isinstance(doc["family"], str):
        _refuse("field_type_invalid", "family")
    if not isinstance(doc["contract_version"], str):
        _refuse("field_type_invalid", "contract_version")
    return effective_preimage(doc["family"], doc["effective"], doc["contract_version"])


def validate_preimage(doc: Any) -> dict:
    """A presented preimage must equal the one rebuilt from its own family and payload; its tags are compared with the registered ones, never trusted."""
    top = ("contract_version", "deny_all", "effective", "effective_policy_profile", "family", "family_version")
    if not isinstance(doc, dict):
        _refuse("field_type_invalid")
    missing = set(top) - set(doc)
    if missing:
        _refuse("field_missing", min(missing))
    unknown = set(doc) - set(top)
    if unknown:
        _refuse("field_unknown", min(unknown))
    if doc["effective_policy_profile"] != EFFECTIVE_PROFILE:
        _refuse("field_invalid", "effective_policy_profile")
    if not isinstance(doc["family"], str):
        _refuse("field_type_invalid", "family")
    if not isinstance(doc["contract_version"], str):
        _refuse("field_type_invalid", "contract_version")
    registered = registered_family_version(doc["family"], doc["contract_version"])
    validate_effective_payload(doc["family"], doc["effective"])
    if doc["family_version"] != registered:
        _refuse("field_invalid", "family_version")
    if doc["deny_all"] != deny_all_dimensions(doc["family"], doc["effective"]):
        _refuse("field_invalid", "deny_all")
    return doc


# ----------------------------------------------------------------------------------------------------------------------
# Typed refusal mapping (spec 8.1): (verdict class, registry code, decision kind, retry, evidence fields)
# Generated from the vector file's `defect_mapping`; tests/test_ext_s1_5_identity_module.py asserts equality with it. Rows whose code is a
# ruled additive code (not_activated, policy_identity_mismatch, store_unknown), the two non-Registry rows (deny_all, evaluator_denial) and the two
# rows of the v2-only codes that `tests/test_r08v2_family_dispatch.py` keeps out of every module of this package until the package that implements
# them lands (the withdrawal row and the snapshot-floor row) are NOT here: this module emits none of those codes. PROPOSED rows: trust_snapshot_invalid (REFUSE class), trust_snapshot_missing (N-11, two stages).
# ----------------------------------------------------------------------------------------------------------------------
VERDICT_CLASSES = ("ACCEPT", "REFUSE", "REFUSE_STALE", "UNKNOWN_FAIL_CLOSED")


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
               ("registry_code", "layer", "participation", "decision_kind", "stage", "trust_snapshot_version",),),
    MappingRow("MP-selection_revoked", "REFUSE", "selection_revoked", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch", "selection_digest",),),
    MappingRow("MP-issuer_key_revoked", "REFUSE", "issuer_key_revoked", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch",),),
    MappingRow("MP-selection_expired", "REFUSE", "selection_expired", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch",), optional_overlay=True),
    MappingRow("MP-selection_not_yet_effective", "REFUSE", "selection_not_yet_effective", "required_policy_unavailable", "after_validity_window_opens",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch",),),
    MappingRow("MP-participation_mismatch", "REFUSE", "participation_mismatch", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id",),),
    MappingRow("MP-selection_conflict", "REFUSE", "selection_conflict", "required_policy_unavailable", "never_same_input",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "selection_id", "selection_epoch", "selection_digest",),),
    MappingRow("MP-trust_snapshot_missing-verify", "UNKNOWN_FAIL_CLOSED", "trust_snapshot_missing", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "trust_snapshot_version",), stage_value="verify",),
    MappingRow("MP-trust_snapshot_missing-guard", "UNKNOWN_FAIL_CLOSED", "trust_snapshot_missing", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "trust_snapshot_version",), stage_value="guard",),
    MappingRow("MP-trust_snapshot_expired-delivered", "REFUSE", "trust_snapshot_expired", "required_policy_unavailable", "fresh_statement_required",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "trust_snapshot_version",),),
    MappingRow("MP-trust_snapshot_expired-guard", "UNKNOWN_FAIL_CLOSED", "trust_snapshot_expired", "required_policy_unavailable", "after_authoritative_state_available",
               ("registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "trust_snapshot_version",),),
)
MAPPING_BY_ID = MappingProxyType({r.row_id: r for r in REFUSAL_MAPPING})


def mapping_rows_for(code: str) -> Tuple[MappingRow, ...]:
    return tuple(r for r in REFUSAL_MAPPING if r.registry_code == code)


def verdict_for(code: str, stage: Any = None) -> MappingRow:
    """The unique mapping row for a registry code (and, for the codes with several rows, a stage); a code with no row is a contract change and raises
    KeyError. `trust_snapshot_missing` has two rows (stage `verify` / `guard`) and `trust_snapshot_expired` two (use `MAPPING_BY_ID`)."""
    rows = mapping_rows_for(code)
    if stage is not None:
        rows = tuple(r for r in rows if r.stage_value == stage)
    if len(rows) != 1:
        raise KeyError((code, stage))
    return rows[0]


def _check_module_tables() -> None:
    used = {r.registry_code for r in REFUSAL_MAPPING}
    if not used <= set(CODES_V2):
        raise RuntimeError("mapping uses a code outside CODES_V2: %s" % sorted(used - set(CODES_V2)))
    if not all(r.verdict_class in VERDICT_CLASSES for r in REFUSAL_MAPPING):
        raise RuntimeError("mapping uses a verdict class outside the closed vocabulary")


_check_module_tables()
