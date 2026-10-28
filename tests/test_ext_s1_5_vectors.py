"""EXT-S1-5 contract preparation: validate the policy-identity golden vectors against an INDEPENDENT reference serializer.

Scope: documentation-and-data tooling only. This file imports nothing from registry_successor, registry_consumer,
registry_records, registry_contract, registry_adapters or registry_conformance. Everything it needs (a hand-written canonical JSON
serializer, a strict validator for the binding, the digest construction and the trust-snapshot normalizer) is implemented
below from docs/ext-implementation/ext-s1-5-effective-policy-identity-spec.md and docs/r08-v2-contract.md section 4.1 and 5.
It is NOT a shared module and must not be imported by source code. It qualifies nothing (vectors are BUILDER_TESTED).

The serializer is deliberately NOT json.dumps: it writes the canonical text by hand, and a second check compares it with
json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True), which is what registry_successor/common.py does.
"""
import bisect
import hashlib
import json
import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "docs" / "ext-implementation" / "data" / "ext-s1-5-policy-identity-vectors.json"
V = json.loads(VECTORS.read_text(encoding="ascii"))

DOMAIN_PREFIX = b"ocs-reg/r08-v2/policy-binding\n"
PROFILE = "ocs-policy-binding/1"
EFFECTIVE_PREFIX = b"ocs-reg/r08-v2/effective-policy\n"
EFFECTIVE_PROFILE = "ocs-effective-policy/1"
CONTRACT_VERSION = "r08-v2"
SCOPE_KEY_PREFIX = b"ocs-reg/r08-v2/scope-key\n"
SCOPE_KEY_PROFILE = "ocs-scope-key/1"
MAX_DOCUMENT_BYTES = 65536
MAX_DEPTH = 8

# Explicit PER-FIELD integer domains (Architect ruling OQ-1). Each field has its OWN entry; the entries are independent and
# merely happen to be equal today. They are deliberately written as separate literals, never derived from one shared constant.
RANGES = {
    "record_version": (1, 2147483647),           # SOURCE_JUSTIFIED: record.py 1 <= v <= MAX_INT; s03-contract 1..2147483647
    "selection_epoch": (1, 2147483647),          # SOURCE_JUSTIFIED: selection.py _epoch_ok 1 <= v <= MAX_INT
    # COMPONENT_OWNER_DERIVED (Architect ruling N-1): NO source states a ceiling (verify.py:82 is a floor only, canonical_bytes writes unbounded
    # ints, the durable high-water and guard checks are floors only), so the strict bound the representation supports is the canonical-JSON
    # safe integer range 2**53 - 1. It is deliberately NOT the 2**31 - 1 domain of record_version/selection_epoch or of the ages.
    "trust_snapshot_version": (1, 9007199254740991),
}
AGE_RANGES = {                                   # RULED (OQ-1): technical representation ceiling, not an operational setting
    "registry": (1, 2147483647),                 # AGE_MIN = 1 adopted for registry input
    "caller": (0, 2147483647),                   # the Control Plane models admit 0
    "effective": (0, 2147483647),                # min(caller, registry); a caller 0 stays 0
}
RESERVED_POLICY_GENERATION = (1, 9007199254740991)  # RESERVED ONLY: not a binding member, no vectors, owner EXT-S3-4 (D-16)
VERDICT_CLASSES = ("ACCEPT", "REFUSE", "REFUSE_STALE", "UNKNOWN_FAIL_CLOSED")

# ----------------------------------------------------------------------------------------------------------------------
# Reference canonical serializer (hand-written)
# ----------------------------------------------------------------------------------------------------------------------
_SHORT = {0x22: '\\"', 0x5C: "\\\\", 0x08: "\\b", 0x0C: "\\f", 0x0A: "\\n", 0x0D: "\\r", 0x09: "\\t"}


def _esc_unit(u):
    return "\\u%04x" % u


def ser_string(s):
    out = ['"']
    for ch in s:
        cp = ord(ch)
        if cp in _SHORT:
            out.append(_SHORT[cp])
        elif cp < 0x20 or cp == 0x7F:
            out.append(_esc_unit(cp))  # every code point outside U+0020..U+007E is escaped (DEL too)
        elif cp < 0x80:
            out.append(ch)  # printable ASCII; '/' is not escaped
        elif cp < 0x10000:
            out.append(_esc_unit(cp))
        else:
            cp -= 0x10000
            out.append(_esc_unit(0xD800 + (cp >> 10)) + _esc_unit(0xDC00 + (cp & 0x3FF)))
    out.append('"')
    return "".join(out)


def ser(value):
    """Canonical JSON text: sorted keys (by code point), no whitespace, ASCII only; ints, strs, lists, dicts, None only."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return ser_string(value)
    if isinstance(value, list):
        return "[" + ",".join(ser(x) for x in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(ser_string(k) + ":" + ser(value[k]) for k in sorted(value)) + "}"
    raise TypeError("unsupported type for canonical serialization: %r" % type(value))


def canon(value):
    text = ser(value)
    assert text.isascii()
    return text.encode("utf-8")


def sha_hex(data):
    return hashlib.sha256(data).hexdigest()


def binding_digest(binding):
    return "sha256:" + sha_hex(DOMAIN_PREFIX + canon(binding))


def plain_digest(value):
    return "sha256:" + sha_hex(canon(value))


# ----------------------------------------------------------------------------------------------------------------------
# Reference strict loader and validator (first failing phase wins; see spec section 5)
# ----------------------------------------------------------------------------------------------------------------------
class Refuse(Exception):
    def __init__(self, code, member=None):
        super().__init__(code)
        self.code = code
        self.member = member


class _Obj(list):
    """An object whose (key, value) pairs are preserved in document order, so duplicate keys can be examined AFTER the syntax phase."""


BIG_INT_SENTINEL = 10 ** 40  # an integer literal of more than MAX_EXACT_DIGITS digits is syntactically valid; the reference maps it to a value
#                              strictly outside every field range (it never reaches canonical bytes: it is refused by the range rule)
MAX_EXACT_DIGITS = 20  # every per-field range (largest 2**53 - 1, 16 digits) is far below 20 digits; longer literals are classified by LENGTH, never converted


def _parse_int(text):
    """Classify by literal syntax (spec 5.5.1): up to 20 digits the exact value, beyond that a value outside every range. int() is never called on
    an unbounded literal, so the result cannot depend on sys.set_int_max_str_digits or PYTHONINTMAXSTRDIGITS (any setting from 640 up, or 0)."""
    digits = text.lstrip("-")
    if len(digits) <= MAX_EXACT_DIGITS:
        return int(text)
    return -BIG_INT_SENTINEL if text.startswith("-") else BIG_INT_SENTINEL


_WS = " \t\n\r"
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?")
_STRING_CHUNK = re.compile(r'[^"\\\x00-\x1f]*')
_ESCAPES = {'"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"}
_HEX = frozenset("0123456789abcdefABCDEF")


def _scan_string(text, i):
    """RFC 8259 string starting at text[i] == '"': raw control characters are syntax errors, \\uXXXX escapes are decoded and a high surrogate
    escape followed by a low surrogate escape is one code point (so a key written with a pair equals the same key written raw). A lone
    surrogate escape stays one distinct code unit."""
    n = len(text)
    i += 1
    out = []
    while True:
        m = _STRING_CHUNK.match(text, i)
        out.append(m.group())
        i = m.end()
        if i >= n:
            raise ValueError("unterminated string")
        c = text[i]
        if c == '"':
            return "".join(out), i + 1
        if c != "\\":
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


def _scan(text):
    """ITERATIVE JSON scanner (spec 5.5.1): an explicit stack, no recursion, so the syntax, number-literal and duplicate-key steps are not
    limited by the interpreter's recursion depth and every implementation can follow the same order on a document nested thousands of
    levels deep (the 65536-byte size limit bounds the work). Returns (tree, saw_number_literal); raises ValueError for any syntax error.
    Grammar: RFC 8259 plus the tokens NaN, Infinity and -Infinity (recognized only so they can be refused as number literals)."""
    n = len(text)
    i = 0
    stack = []  # open containers: _Obj (pairs in document order) or list
    key_of = []  # the pending key of each open _Obj (None for an array frame)
    root = None
    done = False
    saw_number = False
    expecting = "value"  # value | value_or_end (after '[') | key_or_end (after '{') | key (after ',' in an object) | after (a value just ended)

    def attach(v):
        nonlocal root, done
        if not stack:
            root, done = v, True
        elif isinstance(stack[-1], _Obj):
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
        c = text[i]
        if expecting == "after":
            top = stack[-1]
            if c == ",":
                i += 1
                expecting = "key" if isinstance(top, _Obj) else "value"
            elif c == ("}" if isinstance(top, _Obj) else "]"):
                i += 1
                close()
            else:
                raise ValueError("expected , or close")
            continue
        if expecting in ("key", "key_or_end"):
            if c == "}" and expecting == "key_or_end":
                i += 1
                close()
                expecting = "after"
                continue
            if c != '"':
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
        if expecting == "value_or_end" and c == "]":
            i += 1
            close()
            expecting = "after"
            continue
        if c == "{":
            stack.append(_Obj())
            key_of.append(None)
            i += 1
            expecting = "key_or_end"
        elif c == "[":
            stack.append([])
            key_of.append(None)
            i += 1
            expecting = "value_or_end"
        elif c == '"':
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
                attach(_parse_int(m.group()))
            i = m.end()
            expecting = "after"


def _walk(node):
    stack = [node]
    while stack:
        n = stack.pop()
        if isinstance(n, _Obj):
            yield n
            stack.extend(v for _, v in n)
        elif isinstance(n, list):
            stack.extend(n)


def _depth(value):
    stack = [(value, 1)]
    while stack:
        node, d = stack.pop()
        if d > MAX_DEPTH:
            return False
        if isinstance(node, _Obj):
            stack.extend((v, d + 1) for _, v in node)
        elif isinstance(node, list):
            stack.extend((c, d + 1) for c in node)
    return True


def _materialize(node):
    if isinstance(node, _Obj):
        return {k: _materialize(v) for k, v in node}
    if isinstance(node, list):
        return [_materialize(c) for c in node]
    return node


def load(raw):
    """Normative parse order (spec 5.5.1), identical for every implementation regardless of its parser's streaming order:
    1 input boundary: strict UTF-8 or text (input_not_text), then size of the UTF-8 bytes (input_too_large);
    2 SYNTAX on the whole text, by an ITERATIVE scan that is not limited by recursion depth: JSON grammar extended only by the tokens NaN,
      Infinity, -Infinity (json_malformed); a byte order mark is not stripped, an integer literal of any length is valid syntax;
    3 number literals: any float, exponent or NaN/Infinity token anywhere (json_number_unsupported);
    4 duplicate object keys at any depth, after unescaping (json_duplicate_key);
    5 nesting deeper than 8 (json_nesting_too_deep)."""
    if isinstance(raw, (bytes, bytearray)):
        data = bytes(raw)
        try:
            text = data.decode("utf-8")  # strict: overlong forms, encoded surrogates and truncated sequences refuse
        except UnicodeDecodeError:
            raise Refuse("input_not_text")
    elif isinstance(raw, str):
        text = raw
        try:
            data = text.encode("utf-8")  # a lone surrogate cannot be encoded
        except UnicodeEncodeError:
            raise Refuse("input_not_text")
    else:
        raise Refuse("input_not_text")
    if len(data) > MAX_DOCUMENT_BYTES:  # bytes, not characters
        raise Refuse("input_too_large")
    try:
        value, saw_number = _scan(text)
    except ValueError:
        raise Refuse("json_malformed")
    if saw_number:
        raise Refuse("json_number_unsupported")
    for obj in _walk(value):
        keys = [k for k, _ in obj]
        if len(keys) != len(set(keys)):
            raise Refuse("json_duplicate_key")
    if not _depth(value):
        raise Refuse("json_nesting_too_deep")
    return _materialize(value)


IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")  # used with fullmatch (== \A...\Z); classes are explicit ASCII ranges
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
ID_MEMBERS = ("record_id", "selection_id", "family", "consumer_id", "operation", "scope.tenant", "scope.institution", "scope.authority_domain")
DIGEST_MEMBERS = ("record_digest", "selection_digest", "effective_policy_digest", "activation_ref", "trust_snapshot_fingerprint")
INT_MEMBERS = ("record_version", "selection_epoch", "trust_snapshot_version")
SCOPE_KEYS = ("authority_domain", "institution", "tenant")
TOP_KEYS = ("activation_ref", "binding_profile", "consumer_id", "effective_policy_digest", "family", "operation", "record_digest", "record_id",
            "record_version", "scope", "selection_digest", "selection_epoch", "selection_id", "trust_snapshot_fingerprint", "trust_snapshot_version")


def _flatten(doc):
    """Only for a document whose top-level and `scope` member sets were ALREADY checked separately (validate_binding): by then no top-level key can
    contain a dot, so a literal `scope.tenant` can never collide with the nested member."""
    flat = {}
    for k, v in doc.items():
        if k == "scope" and isinstance(v, dict):
            for sk, sv in v.items():
                flat["scope." + sk] = sv
        else:
            flat[k] = v
    return flat


def validate_binding(doc):
    """Returns the doc if it is a well formed COMPLETED binding; raises Refuse(code, member) otherwise.
    The top-level member set and the `scope` member set are checked as TWO separate sets BEFORE anything is flattened (review of PR #30, Copilot): a
    top-level key that is literally `scope.tenant` is an unlisted TOP-LEVEL member (`field_unknown`), never the nested tenant, whatever the key order."""
    if not isinstance(doc, dict):
        raise Refuse("field_type_invalid")
    nested = doc.get("scope") if "scope" in doc else None
    if "scope" in doc and not isinstance(nested, dict):
        raise Refuse("field_type_invalid", "scope")
    top_required = set(TOP_KEYS) - {"scope"}
    # phase 1: missing, phase 2: unknown (sorted path order); an absent scope is the single missing member `scope`
    missing = sorted((top_required - set(doc)) | ({"scope"} if "scope" not in doc else {"scope." + k for k in SCOPE_KEYS if k not in nested}))
    if missing:
        raise Refuse("field_missing", missing[0])
    unknown = sorted({k for k in doc if k not in TOP_KEYS} | ({"scope." + k for k in nested if k not in SCOPE_KEYS} if nested is not None else set()))
    if unknown:
        raise Refuse("field_unknown", unknown[0])
    flat = _flatten(doc)
    for path in sorted(flat):  # phase 3: types
        val = flat[path]
        if path in INT_MEMBERS:
            if isinstance(val, bool) or not isinstance(val, int):
                raise Refuse("field_type_invalid", path)
        elif not isinstance(val, str):
            raise Refuse("field_type_invalid", path)
    for path in sorted(flat):  # phase 4: values
        val = flat[path]
        if path in INT_MEMBERS:
            lo, hi = RANGES[path]
            if not lo <= val <= hi:
                raise Refuse("field_invalid", path)
        elif path in ID_MEMBERS:
            if not val.isascii() or IDENT.fullmatch(val) is None:
                raise Refuse("field_invalid", path)
        elif path in DIGEST_MEMBERS:
            if not val.isascii() or DIGEST.fullmatch(val) is None:
                raise Refuse("field_invalid", path)
        elif path == "binding_profile":
            if val != PROFILE:
                raise Refuse("field_invalid", path)
    return doc


def run_binding(vec):
    raw = bytes.fromhex(vec["input_hex"]) if "input_hex" in vec else vec["input_json"]
    doc = validate_binding(load(raw))
    c = canon(doc)
    return {"canonical_bytes_hex": c.hex(), "canonical_ascii": c.decode("ascii"), "binding_digest": binding_digest(doc),
            "digest_without_prefix_control": plain_digest(doc)}


# trust snapshot normalizer (contract section 5)
def normalize_snapshot(s):
    out = json.loads(json.dumps(s))
    for issuer in out["issuers"]:
        issuer["authority"] = sorted(issuer["authority"])
    out["issuers"] = sorted(out["issuers"], key=lambda i: i["key_id"])
    out["revoked_key_ids"] = sorted(out["revoked_key_ids"])
    out["revoked_selections"] = sorted(out["revoked_selections"], key=lambda p: (p[0], p[1]))
    out["min_epochs"] = sorted(out["min_epochs"], key=lambda p: p[0])
    return out


def check_snapshot_duplicates(s):
    keys = [i["key_id"] for i in s["issuers"]]
    floors = [p[0] for p in s["min_epochs"]]
    pairs = [tuple(p) for p in s["revoked_selections"]]
    if len(set(keys)) != len(keys) or len(set(floors)) != len(floors) or len(set(pairs)) != len(pairs) \
            or len(set(s["revoked_key_ids"])) != len(s["revoked_key_ids"]):
        raise Refuse("trust_snapshot_invalid")


# ----------------------------------------------------------------------------------------------------------------------
# Statement token replica, scope projection (OQ-4)
# ----------------------------------------------------------------------------------------------------------------------
def statement_valid_token(value):
    """Replica of registry_successor/common.py valid_token (the check a signed v2 statement's scope fields pass today): 1..128
    characters, no '*', no Unicode category C* or Z* character. It accepts non-ASCII text, which is why projection must refuse it."""
    if not isinstance(value, str) or not 1 <= len(value) <= 128 or "*" in value:
        return False
    return all(unicodedata.category(ch)[0] not in ("C", "Z") for ch in value)


# Frozen token membership (Architect Batch 6 rulings, N-13). The token rule of the effective payload (list entries, F5 class names) is decided by
# this committed, hash-pinned table of EXCLUDED code point ranges (Unicode 15.1.0 general categories C* and Z*, unassigned included), never by the
# interpreter's own Unicode database. The statement_valid_token replica above stays runtime-dependent on purpose: it replicates the shipped
# validator, which is exactly the dependence this ruling removes from the new contract.
TOKEN_TABLE_FILE = ROOT / "docs" / "ext-implementation" / "data" / "ext-s1-5-token-unicode-15.1-excluded-ranges.json"
TOKEN_TABLE_SHA256 = "8c85813d25f6ed53371e27f0e4895a89de44a619824486dcff8d48ff8b607474"  # literal pin, also recorded in the vectors (pins.token_unicode_table)
_TOKEN_TABLE_BYTES = TOKEN_TABLE_FILE.read_bytes()
_TOKEN_RANGES = [(int(a, 16), int(b, 16)) for a, b in json.loads(_TOKEN_TABLE_BYTES.decode("ascii"))["excluded_ranges"]]
_TOKEN_STARTS = [a for a, _ in _TOKEN_RANGES]
MAX_TOKEN_CHARS = 128


def frozen_cp_excluded(cp):
    """True when the code point lies in an excluded range of the pinned table. A code point the table does not list as permitted is excluded:
    the table lists exclusions over the whole range U+0000..U+10FFFF, so a code point assigned after Unicode 15.1.0 (unassigned there) is refused."""
    i = bisect.bisect_right(_TOKEN_STARTS, cp) - 1
    return i >= 0 and _TOKEN_RANGES[i][0] <= cp <= _TOKEN_RANGES[i][1]


def frozen_token_valid(value):
    """The token rule with frozen membership: a str of 1..128 code points, no '*', no code point in the pinned excluded ranges. No normalization
    is applied. Consults no runtime Unicode database (unicodedata is not used)."""
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_TOKEN_CHARS or "*" in value:
        return False
    return not any(frozen_cp_excluded(ord(ch)) for ch in value)


def project_scope(statement_scope):
    """IDENTITY projection only: each of the three scope tokens is passed through byte for byte when it already matches the ASCII
    identifier grammar, otherwise binding creation is refused field_invalid at member scope.<name> (first in sorted path order).
    No transliteration, normalization, case folding, truncation or hashing is ever applied."""
    if not isinstance(statement_scope, dict) or set(statement_scope) != set(SCOPE_KEYS):
        raise Refuse("field_invalid", "scope")
    for k in sorted(SCOPE_KEYS):
        v = statement_scope[k]
        if not (isinstance(v, str) and v.isascii() and IDENT.fullmatch(v)):
            raise Refuse("field_invalid", "scope." + k)
    return {k: statement_scope[k] for k in SCOPE_KEYS}


def projection_effect(participation, activation_state, determination):
    """Ruling N-5 reference rules for a refusal at the projection stage (binding creation is refused for EVERY participation, whatever the
    refusal kind: the function takes no refusal kind and no member). The refusal is never an authorization: no branch yields
    overlay_not_applied or an ACCEPT by itself. `participation` is exactly "required" or "optional"; anything else is refused, never read
    as optional (a raise, not an assert, so the rule survives python -O)."""
    if participation == "required":
        out = "UNKNOWN_FAIL_CLOSED" if activation_state == "indeterminate" else "REFUSE"
        return {"effect_outcome": out, "decision_kind": "required_policy_unavailable", "fallback_permitted": False, "fallback_evidence": None}
    if participation != "optional":
        raise Refuse("field_invalid", "participation")
    if activation_state == "indeterminate":
        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None, "fallback_permitted": False, "fallback_evidence": None}
    if determination == "authenticated" and activation_state == "permits_optional":
        return {"effect_outcome": "optional_fallback_via_determination", "decision_kind": None, "fallback_permitted": True,
                "fallback_evidence": {"kind": "absence_or_withdrawal", "projection_refusal_code": "field_invalid"}}
    return {"effect_outcome": "REFUSE", "decision_kind": None, "fallback_permitted": False, "fallback_evidence": None}


def projection_effect_for(refusal_code, participation, activation_state, determination):
    """The join of a refusal's own registry code with the one effect function: the only thing a refusal kind contributes is the code the
    fallback evidence record carries. The outcome never depends on the refusal."""
    out = projection_effect(participation, activation_state, determination)
    if out["fallback_evidence"] is not None:
        out = {**out, "fallback_evidence": {**out["fallback_evidence"], "projection_refusal_code": refusal_code}}
    return out


# ----------------------------------------------------------------------------------------------------------------------
# Scope key (OQ-5)
# ----------------------------------------------------------------------------------------------------------------------
SK_MEMBERS = ("authority_domain", "consumer_id", "family", "institution", "operation", "selection_id", "tenant")  # sorted
SK_TOP = ("scope_key_profile",) + SK_MEMBERS


def validate_scope_key(doc):
    if not isinstance(doc, dict):
        raise Refuse("field_type_invalid")
    missing = sorted(set(SK_TOP) - set(doc))
    if missing:
        raise Refuse("field_missing", missing[0])
    unknown = sorted(set(doc) - set(SK_TOP))
    if unknown:
        raise Refuse("field_unknown", unknown[0])
    for k in sorted(doc):
        if not isinstance(doc[k], str):
            raise Refuse("field_type_invalid", k)
    for k in sorted(doc):
        if k == "scope_key_profile":
            if doc[k] != SCOPE_KEY_PROFILE:
                raise Refuse("field_invalid", k)
        elif not (doc[k].isascii() and IDENT.fullmatch(doc[k])):
            raise Refuse("field_invalid", k)
    return doc


def scope_key_text(doc):
    return canon(validate_scope_key(doc))


def scope_key_digest(doc):
    return "sha256:" + sha_hex(SCOPE_KEY_PREFIX + scope_key_text(doc))


def scope_key_from_binding(b):
    return {"scope_key_profile": SCOPE_KEY_PROFILE, "tenant": b["scope"]["tenant"], "institution": b["scope"]["institution"],
            "authority_domain": b["scope"]["authority_domain"], "consumer_id": b["consumer_id"], "operation": b["operation"],
            "family": b["family"], "selection_id": b["selection_id"]}


# ----------------------------------------------------------------------------------------------------------------------
# Effective policy identity (OQ-3)
# ----------------------------------------------------------------------------------------------------------------------
F1AB_KEYS = ("allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains")
FAMILIES = {  # contract section 2 table: family id, table tag, payload shape
    "f1a-local-execution-allowlist": {"version": "v1", "kind": "lists", "keys": ("allowed_actions", "allowed_adapters", "allowed_units")},
    "f1ab-local-execution-allowlist": {"version": "v2", "kind": "lists", "keys": F1AB_KEYS},
    "f4-control-plane-age-bounds": {"version": "v2", "kind": "ints", "keys": ("status_max_age_seconds", "approval_max_age_seconds")},
    "f5-action-class-age-bounds": {"version": "v2", "kind": "classmap", "keys": ("class_status_max_age_seconds",)},
}


REGISTERED_CONTRACT_VERSIONS = {  # an effective-policy identity exists for contract_version r08-v2 ONLY, for every family (even f1a, which the shipped r08-v1 table also registers)
    "f1a-local-execution-allowlist": ("r08-v2",), "f1ab-local-execution-allowlist": ("r08-v2",),
    "f4-control-plane-age-bounds": ("r08-v2",), "f5-action-class-age-bounds": ("r08-v2",)}


def registered_family_version(family, contract_version):
    """Ruling N-3: family_version is LOOKED UP from the registered family table keyed by the authenticated record's family id and
    contract_version. It is never a parameter, a payload member or a caller choice anywhere in this module."""
    if not isinstance(family, str) or family not in FAMILIES:
        raise Refuse("family_unsupported", "family")
    if contract_version not in REGISTERED_CONTRACT_VERSIONS[family]:
        raise Refuse("contract_unsupported", "contract_version")
    return FAMILIES[family]["version"]


def _strict_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def validate_effective_payload(family, payload, role="effective"):
    """Strict validator of a composed (or, with role registry/caller, an input) family payload. First failing phase wins:
    family, shape (missing, unknown), types, values; sorted path order inside each phase."""
    if not isinstance(family, str) or family not in FAMILIES:
        raise Refuse("family_unsupported", "family")
    fam = FAMILIES[family]
    if not isinstance(payload, dict):
        raise Refuse("field_type_invalid")
    keys = set(fam["keys"])
    missing = sorted(keys - set(payload))
    if missing:
        raise Refuse("field_missing", missing[0])
    unknown = sorted(set(payload) - keys)
    if unknown:
        raise Refuse("field_unknown", unknown[0])
    flat = {}
    for k in payload:
        if fam["kind"] == "classmap" and isinstance(payload[k], dict):
            for c, v in payload[k].items():
                flat[k + "." + c] = v
        else:
            flat[k] = payload[k]
    for path in sorted(flat):  # types
        v = flat[path]
        if fam["kind"] == "lists":
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                raise Refuse("field_type_invalid", path)
        elif fam["kind"] == "ints":
            if not _strict_int(v):
                raise Refuse("field_type_invalid", path)
        elif path == "class_status_max_age_seconds" or not _strict_int(v):
            raise Refuse("field_type_invalid", path)
    lo, hi = AGE_RANGES[role]
    for path in sorted(flat):  # values
        v = flat[path]
        if fam["kind"] == "lists":
            if len(v) > 256 or not all(frozen_token_valid(x) for x in v) or v != sorted(set(v)):
                raise Refuse("field_invalid", path)
        elif not lo <= v <= hi:
            raise Refuse("field_invalid", path)
    if fam["kind"] == "classmap":
        m = payload["class_status_max_age_seconds"]
        if not m or not all(frozen_token_valid(c) for c in m):
            raise Refuse("field_invalid", "class_status_max_age_seconds")
    return payload


def deny_all_dimensions(family, payload):
    if FAMILIES[family]["kind"] != "lists":
        return []
    return sorted(k for k, v in payload.items() if v == [])


def effective_preimage(family, payload, contract_version=CONTRACT_VERSION):
    version = registered_family_version(family, contract_version)  # derived, never supplied
    validate_effective_payload(family, payload)
    return {"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": contract_version, "family": family,
            "family_version": version, "deny_all": deny_all_dimensions(family, payload), "effective": payload}


def effective_digest_of_preimage(pre):
    return "sha256:" + sha_hex(EFFECTIVE_PREFIX + canon(pre))


def effective_policy_digest(family, payload, contract_version=CONTRACT_VERSION):
    return effective_digest_of_preimage(effective_preimage(family, payload, contract_version))


def validate_effective_inputs(doc):
    """The ONLY consumer-facing input of the effective digest: {family, contract_version, effective}, where family and contract_version come
    from the authenticated record. Any family_version member is a refusal (ruling N-3): member set first (missing, then unknown), then the
    registered lookup (family, then contract_version), then the effective payload. Returns the derived preimage."""
    top = ("contract_version", "effective", "family")
    if not isinstance(doc, dict):
        raise Refuse("field_type_invalid")
    missing = sorted(set(top) - set(doc))
    if missing:
        raise Refuse("field_missing", missing[0])
    unknown = sorted(set(doc) - set(top))
    if unknown:
        raise Refuse("field_unknown", unknown[0])
    if not isinstance(doc["family"], str):
        raise Refuse("field_type_invalid", "family")
    if not isinstance(doc["contract_version"], str):
        raise Refuse("field_type_invalid", "contract_version")
    return effective_preimage(doc["family"], doc["effective"], doc["contract_version"])


def validate_preimage(doc):
    """A presented preimage must equal the one rebuilt from its own family and effective payload (no free-standing flags)."""
    top = ("contract_version", "deny_all", "effective", "effective_policy_profile", "family", "family_version")
    if not isinstance(doc, dict):
        raise Refuse("field_type_invalid")
    missing = sorted(set(top) - set(doc))
    if missing:
        raise Refuse("field_missing", missing[0])
    unknown = sorted(set(doc) - set(top))
    if unknown:
        raise Refuse("field_unknown", unknown[0])
    if doc["effective_policy_profile"] != EFFECTIVE_PROFILE:
        raise Refuse("field_invalid", "effective_policy_profile")
    if not isinstance(doc["family"], str):
        raise Refuse("field_type_invalid", "family")
    if not isinstance(doc["contract_version"], str):
        raise Refuse("field_type_invalid", "contract_version")
    registered = registered_family_version(doc["family"], doc["contract_version"])  # family_unsupported, then contract_unsupported (same as the input path)
    validate_effective_payload(doc["family"], doc["effective"])
    if doc["family_version"] != registered:  # compared with the registered tag, never trusted
        raise Refuse("field_invalid", "family_version")
    if doc["deny_all"] != deny_all_dimensions(doc["family"], doc["effective"]):
        raise Refuse("field_invalid", "deny_all")
    return doc


def compose(family, registry, caller):
    """Independent restatement of contract section 2 composition for the vectors: F1ab/f1a intersection per key, F4 min per scalar,
    F5 min per class (the vectors use identical class sets)."""
    validate_effective_payload(family, registry, "registry")
    validate_effective_payload(family, caller, "caller")
    kind = FAMILIES[family]["kind"]
    if kind == "lists":
        return {k: sorted(set(registry[k]) & set(caller[k])) for k in registry}
    if kind == "ints":
        return {k: min(registry[k], caller[k]) for k in registry}
    r, c = registry["class_status_max_age_seconds"], caller["class_status_max_age_seconds"]
    assert set(r) == set(c)
    return {"class_status_max_age_seconds": {k: min(r[k], c[k]) for k in r}}


# ----------------------------------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------------------------------
def test_vector_file_is_builder_tested_and_large_enough():
    assert V["schema"] == "ocs-ext-s1-5-policy-identity-vectors/1"
    assert V["status"] == "BUILDER_TESTED"
    assert len(V["valid"]) >= 10
    assert len(V["invalid"]) >= 50
    assert len(V["valid"]) + len(V["invalid"]) >= 25
    ids = [x["id"] for x in V["valid"] + V["invalid"] + V["guard_digest_checks"] + V["effective_payloads"] + V["trust_snapshots"] + V["trust_snapshots_invalid"]]
    assert len(ids) == len(set(ids)), "vector ids must be unique"
    cats = {x["category"] for x in V["invalid"]}
    required = {"non-ASCII", "homoglyph", "fullwidth", "NFC/NFD", "whitespace", "empty", "length", "bad leading char", "control", "duplicate key",
                "wrong type", "missing member", "extra member", "uppercase hex", "wrong prefix", "short digest"}
    assert required <= cats, required - cats


def test_reference_serializer_matches_registry_profile_on_every_value():
    """The hand-written serializer equals json.dumps(sort_keys, compact, ensure_ascii=True) (the registry canonical_bytes profile)."""
    samples = [x for x in V["valid"]]
    for vec in samples:
        doc = load(vec["input_json"])
        assert canon(doc) == json.dumps(doc, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    nasty = {"a": "café", "b": "\U0001F600", "c": 'q"\\/\x00\x1f\x7f\n\t', "d": [1, [], {}, None], "A": {"z": 1, "y": 2}, "é": 0}
    assert canon(nasty) == json.dumps(nasty, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    for s in V["identifier_matrix"]["bad_values"]:
        if "\ud800" in s["value"]:
            continue
        assert ser_string(s["value"]) == json.dumps(s["value"], ensure_ascii=True)


def test_every_valid_vector_reproduces_expected_bytes_and_digest():
    by_id = {}
    for vec in V["valid"]:
        got = run_binding(vec)
        exp = vec["expected"]
        assert exp["result"] == "valid"
        assert got["canonical_bytes_hex"] == exp["canonical_bytes_hex"], vec["id"]
        assert got["canonical_ascii"] == exp["canonical_ascii"], vec["id"]
        assert got["binding_digest"] == exp["binding_digest"], vec["id"]
        assert got["digest_without_prefix_control"] == exp["digest_without_prefix_control"], vec["id"]
        assert exp["binding_digest"] != exp["digest_without_prefix_control"], "domain separation must change the digest: " + vec["id"]
        assert re.fullmatch(r"sha256:[0-9a-f]{64}", exp["binding_digest"])
        assert bytes.fromhex(exp["canonical_bytes_hex"]).isascii()
        by_id[vec["id"]] = exp
    for vec in V["valid"]:
        if "equivalent_to" in vec:
            assert vec["expected"] == by_id[vec["equivalent_to"]], vec["id"]
        for other in vec.get("must_differ_from", []):
            assert vec["expected"]["binding_digest"] != by_id[other]["binding_digest"], vec["id"]
            assert vec["expected"]["canonical_bytes_hex"] != by_id[other]["canonical_bytes_hex"], vec["id"]


def test_contract_worked_example_is_reproduced_from_the_contract_text():
    """BV-001 and TF-001 must equal the digests printed in docs/r08-v2-contract.md (not only the vector file)."""
    text = (ROOT / "docs" / "r08-v2-contract.md").read_text(encoding="utf-8")
    blocks = [json.loads(b) for b in re.findall(r"```json\n(.*?)```", text, re.S) if b.lstrip().startswith("{")]
    worked = [b for b in blocks if "binding_digest" in b][0]
    snap = [b for b in blocks if "fingerprint" in b][0]
    assert binding_digest(worked["binding"]) == worked["binding_digest"]
    assert plain_digest(snap["normalized"]) == snap["fingerprint"]
    bv1 = next(v for v in V["valid"] if v["id"] == "BV-001")
    assert load(bv1["input_json"]) == worked["binding"]
    assert bv1["expected"]["binding_digest"] == worked["binding_digest"]
    tf1 = next(v for v in V["trust_snapshots"] if v["id"] == "TF-001")
    assert tf1["expected"]["trust_snapshot_fingerprint"] == snap["fingerprint"]
    assert len(bytes.fromhex(bv1["expected"]["canonical_bytes_hex"])) == 834


def _outcome_codes():
    ld = json.loads((ROOT / "docs" / "p1-extraction-plan" / "data" / "ld02-outcome-map.json").read_text(encoding="utf-8"))
    return {k: v["verification_layer"] for k, v in ld["codes"].items()}


def test_every_invalid_vector_is_refused_with_the_expected_code_and_member():
    codes = _outcome_codes()
    for vec in V["invalid"]:
        exp = vec["expected"]
        assert exp["result"] == "refuse"
        assert exp["code"] in codes, "no new codes: " + vec["id"]
        assert exp["layer"] == codes[exp["code"]], vec["id"]
        with pytest.raises(Refuse) as info:
            run_binding(vec)
        assert info.value.code == exp["code"], (vec["id"], info.value.code)
        assert info.value.member == exp["member"], (vec["id"], info.value.member)


def test_invalid_vectors_are_not_silently_rewritten_into_valid_ones():
    """No normalization: no refused identifier equals a valid one after NFC/NFKC, casefold or strip."""
    import unicodedata
    for entry in V["identifier_matrix"]["bad_values"]:
        v = entry["value"]
        for variant in (unicodedata.normalize("NFC", v), unicodedata.normalize("NFKC", v), v.strip(), v.casefold()):
            if variant != v and variant.isascii() and IDENT.fullmatch(variant):
                # the refused value WOULD become valid if a component normalized it: that is the hazard the vector exists to catch
                doc = json.loads(json.dumps(load(V["valid"][0]["input_json"])))
                doc["scope"]["tenant"] = v
                with pytest.raises(Refuse):
                    validate_binding(doc)
    nfc, nfd = "café", "café"
    assert unicodedata.normalize("NFC", nfd) == nfc and nfc != nfd
    for s in (nfc, nfd):
        assert IDENT.fullmatch(s) is None


def test_identifier_matrix_every_bad_value_in_every_identifier_member():
    base = load(next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"])
    m = V["identifier_matrix"]
    assert tuple(m["members"]) == ID_MEMBERS
    assert len(m["bad_values"]) >= 30
    for entry in m["bad_values"]:
        for member in m["members"]:
            doc = json.loads(json.dumps(base))
            if "." in member:
                a, k = member.split(".")
                doc[a][k] = entry["value"]
            else:
                doc[member] = entry["value"]
            with pytest.raises(Refuse) as info:
                validate_binding(doc)
            assert (info.value.code, info.value.member) == ("field_invalid", member), (entry["id"], member)


def test_regex_uses_end_of_string_not_dollar():
    """Python re '$' accepts a trailing newline; the contract requires \\Z semantics. Guard the reference and the vector file."""
    assert re.match(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$", "a\n") is not None  # the hazard
    assert IDENT.fullmatch("a\n") is None
    assert V["profile"]["identifier_regex"] == r"\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z"
    assert V["profile"]["digest_regex"] == r"\Asha256:[0-9a-f]{64}\Z"
    assert len("A" + "z" * 127) == 128 and IDENT.fullmatch("A" + "z" * 127)
    assert IDENT.fullmatch("A" + "z" * 128) is None


def test_mutation_negative_control_any_single_member_change_changes_the_digest():
    for vec in V["valid"]:
        doc = validate_binding(load(vec["input_json"]))
        base = binding_digest(doc)
        flat = _flatten(doc)
        assert set(flat) == (set(TOP_KEYS) - {"scope"}) | {"scope." + k for k in SCOPE_KEYS}
        for path, val in flat.items():
            mutated = json.loads(json.dumps(doc))
            if path in INT_MEMBERS:
                new = val - 1 if val > 1 else val + 1
            elif path in DIGEST_MEMBERS:
                new = val[:-1] + ("0" if val[-1] != "0" else "1")
            elif path == "binding_profile":
                new = None
            else:
                new = val[:-1] + ("b" if val[-1] != "b" else "c") if len(val) > 1 else ("b" if val != "b" else "c")
            if new is None:
                continue  # the profile constant cannot change within a valid binding (any other value is refused)
            target = mutated
            parts = path.split(".")
            for p in parts[:-1]:
                target = target[p]
            target[parts[-1]] = new
            validate_binding(mutated)  # the mutation is itself a valid binding...
            assert binding_digest(mutated) != base, (vec["id"], path)  # ...with a different digest
        # removing or adding a member is refused (not hashed)
        for path in flat:
            cut = json.loads(json.dumps(doc))
            t = cut
            parts = path.split(".")
            for p in parts[:-1]:
                t = t[p]
            del t[parts[-1]]
            with pytest.raises(Refuse):
                validate_binding(cut)
        extra = json.loads(json.dumps(doc))
        extra["x"] = 1
        with pytest.raises(Refuse):
            validate_binding(extra)
        # a different prefix or no prefix changes the digest (domain separation)
        assert "sha256:" + sha_hex(canon(doc)) != base
        assert "sha256:" + sha_hex(b"ocs-reg/r08-v2/policy-binding" + canon(doc)) != base  # missing newline
        assert "sha256:" + sha_hex(DOMAIN_PREFIX.replace(b"policy-binding", b"policy-bindinG") + canon(doc)) != base


def test_digests_are_unique_across_valid_vectors_except_declared_equivalents():
    seen = {}
    for vec in V["valid"]:
        d = vec["expected"]["binding_digest"]
        if "equivalent_to" in vec:
            assert seen[d] == vec["equivalent_to"]
        else:
            assert d not in seen, (vec["id"], seen.get(d))
            seen[d] = vec["id"]


def test_guard_digest_checks():
    codes = _outcome_codes()
    by_id = {v["id"]: v for v in V["valid"]}
    for g in V["guard_digest_checks"]:
        doc = validate_binding(load(by_id[g["binding_ref"]]["input_json"]))
        carried = g["carried_digest"]
        exp = g["expected"]
        try:
            if not (isinstance(carried, str) and carried.isascii() and DIGEST.fullmatch(carried)):
                raise Refuse("field_invalid")
            if carried != binding_digest(doc):
                raise Refuse("digest_mismatch")
            got = {"result": "valid"}
        except Refuse as r:
            got = {"result": "refuse", "code": r.code}
        assert got["result"] == exp["result"], g["id"]
        if exp["result"] == "refuse":
            assert got["code"] == exp["code"] and exp["code"] in codes, g["id"]
            assert exp["layer"] == codes[exp["code"]], g["id"]  # the layer is checked against the outcome map for every guard vector (no label bypass)
        assert "code_status" not in exp, g["id"]


def test_effective_payload_digests_use_the_domain_separated_preimage():
    by_id = {e["id"]: e for e in V["effective_payloads"]}
    assert V["profile"]["effective_policy"]["domain_prefix_hex"] == EFFECTIVE_PREFIX.hex()
    assert EFFECTIVE_PREFIX == b"ocs-reg/r08-v2/effective-policy\n"
    for ep in V["effective_payloads"]:
        exp = ep["expected"]
        pre = effective_preimage(ep["family"], ep["payload"])
        c = canon(pre)
        assert c.hex() == exp["preimage_canonical_bytes_hex"], ep["id"]
        assert c.decode("ascii") == exp["preimage_canonical_ascii"], ep["id"]
        assert effective_policy_digest(ep["family"], ep["payload"]) == exp["effective_policy_digest"], ep["id"]
        # domain separation and the preimage wrapper both change the digest relative to the interim plain digests
        assert exp["effective_policy_digest"] != exp["digest_without_prefix_control"] == plain_digest(pre), ep["id"]
        assert exp["effective_policy_digest"] != exp["legacy_payload_only_digest_control"] == plain_digest(ep["payload"]), ep["id"]
        assert set(pre) == {"contract_version", "deny_all", "effective", "effective_policy_profile", "family", "family_version"}
        assert pre["family_version"] == FAMILIES[ep["family"]]["version"] and pre["contract_version"] == "r08-v2"
        if "inputs" in ep:  # narrowed values: the digest covers the NARROWED effective data, recomputed independently
            assert compose(ep["family"], ep["inputs"]["registry"], ep["inputs"]["caller"]) == ep["payload"], ep["id"]
        if "equivalent_to" in ep:
            assert by_id[ep["equivalent_to"]]["expected"] == exp, ep["id"]
    digests = [e["expected"]["effective_policy_digest"] for e in V["effective_payloads"] if "equivalent_to" not in e]
    assert len(digests) == len(set(digests))
    # explicit empty set (deny-all) differs from every non-empty case and lists its dimensions; routes to the same sets agree
    assert by_id["EP-004"]["expected"]["preimage_canonical_ascii"].count('"deny_all":["allowed_actions"') == 1
    assert effective_preimage("f1ab-local-execution-allowlist", by_id["EP-011"]["payload"])["deny_all"] == ["allowed_units"]
    assert by_id["EP-012"]["expected"] == by_id["EP-011"]["expected"]
    # caller dependence: same registry payload, different caller, different effective digest (so it can never be compared to durable state)
    assert by_id["EP-007"]["inputs"]["registry"] == by_id["EP-008"]["inputs"]["registry"]
    assert by_id["EP-007"]["expected"]["effective_policy_digest"] != by_id["EP-008"]["expected"]["effective_policy_digest"]
    # changing any single set element changes the effective digest
    fam = "f1ab-local-execution-allowlist"
    p = json.loads(json.dumps(by_id["EP-001"]["payload"]))
    base = effective_policy_digest(fam, p)
    for k in list(p):
        q = json.loads(json.dumps(p))
        q[k] = sorted(q[k] + ["extra-zz"])
        assert effective_policy_digest(fam, q) != base
    # an explicitly empty dimension differs from a non-empty one; an omitted dimension refuses
    q = json.loads(json.dumps(p))
    q["allowed_units"] = []
    assert effective_policy_digest(fam, q) != base
    del q["allowed_units"]
    with pytest.raises(Refuse) as info:
        effective_policy_digest(fam, q)
    assert (info.value.code, info.value.member) == ("field_missing", "allowed_units")


def test_family_version_is_looked_up_from_the_registered_table_and_is_never_an_input():
    """Ruling N-3. family_version comes from the registered, authenticated family contract (keyed by family id and contract_version). No
    function of the identity API takes it; a caller- or payload-supplied family_version is refused; an unregistered family or contract
    version is refused."""
    import inspect
    for fn in (effective_preimage, effective_policy_digest, validate_effective_payload, validate_effective_inputs, compose, registered_family_version):
        assert "family_version" not in inspect.signature(fn).parameters, fn.__name__
    ep = V["profile"]["effective_policy"]
    assert ep["input_members"] == ["contract_version", "effective", "family"] and ep["preimage_members_derived"] == ["family_version"]
    assert "family_version" not in ep["input_members"] and ep["registered_contract_versions"] == ["r08-v2"]
    by_id = {e["id"]: e for e in V["effective_payloads"]}
    valid = refused = 0
    for vec in V["effective_inputs"]:
        exp = vec["expected"]
        if exp["result"] == "valid":
            pre = validate_effective_inputs(load(vec["input_json"]))
            assert pre["family_version"] == exp["derived_family_version"] == FAMILIES[pre["family"]]["version"], vec["id"]
            assert effective_digest_of_preimage(pre) == exp["effective_policy_digest"] == by_id[exp["equals"]]["expected"]["effective_policy_digest"], vec["id"]
            assert "family_version" not in load(vec["input_json"]), vec["id"]
            valid += 1
        else:
            with pytest.raises(Refuse) as info:
                validate_effective_inputs(load(vec["input_json"]))
            assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
            assert exp["code"] in _outcome_codes(), vec["id"]
            refused += 1
    assert valid == 4 and refused >= 9
    # every refusal that supplies a family_version (whatever its value, even the registered one) is field_unknown at that member
    supplied = [v for v in V["effective_inputs"] if "family_version" in load(v["input_json"]) or "family_version" in load(v["input_json"]).get("effective", {})]
    assert len(supplied) >= 5 and all(v["expected"] == {"result": "refuse", "code": "field_unknown", "member": "family_version"} for v in supplied)
    assert {"family_unsupported", "contract_unsupported"} <= {v["expected"].get("code") for v in V["effective_inputs"]}
    # the registered tag is a pure function of (family, contract_version): all four registered families, one tag each
    assert {f: registered_family_version(f, "r08-v2") for f in FAMILIES} == {"f1a-local-execution-allowlist": "v1", "f1ab-local-execution-allowlist": "v2",
                                                                              "f4-control-plane-age-bounds": "v2", "f5-action-class-age-bounds": "v2"}


def test_effective_policy_controls_and_invalid_inputs():
    base = next(e for e in V["effective_payloads"] if e["id"] == "EP-001")
    for c in V["effective_policy_controls"]:
        pre = json.loads(json.dumps(effective_preimage(base["family"], base["payload"])))
        assert canon(load(c["preimage_canonical_ascii"])).decode("ascii") == c["preimage_canonical_ascii"]
        assert effective_digest_of_preimage(load(c["preimage_canonical_ascii"])) == c["effective_policy_digest"], c["id"]
        assert c["effective_policy_digest"] != base["expected"]["effective_policy_digest"], c["id"]
        # review (Copilot): each control is validated against its DECLARED status; only a control the validator refuses is non-registrable
        try:
            validate_preimage(load(c["preimage_canonical_ascii"]))
            validates = True
        except Refuse:
            validates = False
        assert c["registrable"] is validates, c["id"]
    ids = {c["id"] for c in V["effective_policy_controls"]}
    assert {"EC-001", "EC-002", "EC-003", "EC-007"} <= ids  # family version, family id, contract version, display metadata
    # wrong-prefix and no-prefix preimage digests differ
    pre = effective_preimage(base["family"], base["payload"])
    assert "sha256:" + sha_hex(canon(pre)) != effective_digest_of_preimage(pre)
    assert "sha256:" + sha_hex(EFFECTIVE_PREFIX[:-1] + canon(pre)) != effective_digest_of_preimage(pre)
    assert "sha256:" + sha_hex(DOMAIN_PREFIX + canon(pre)) != effective_digest_of_preimage(pre)  # not the binding prefix either
    codes = _outcome_codes()
    for vec in V["effective_payloads_invalid"]:
        exp = vec["expected"]
        assert exp["code"] in codes, vec["id"]
        with pytest.raises(Refuse) as info:
            validate_effective_payload(vec["family"], load(vec["payload_json"]), vec["role"])
        assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
    for vec in V["effective_preimage_invalid"]:
        exp = vec["expected"]
        assert exp["code"] in codes, vec["id"]
        with pytest.raises(Refuse) as info:
            validate_preimage(load(vec["input_json"]))
        assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
    for e in V["effective_payloads"]:
        validate_preimage(effective_preimage(e["family"], e["payload"]))


def test_trust_snapshot_fingerprints_and_mutation_control():
    for t in V["trust_snapshots"]:
        check_snapshot_duplicates(t["input"])
        n = normalize_snapshot(t["input"])
        c = canon(n)
        assert c.hex() == t["expected"]["canonical_bytes_hex"], t["id"]
        assert plain_digest(n) == t["expected"]["trust_snapshot_fingerprint"], t["id"]
        assert set(n) == {"snapshot_id", "version", "valid_until", "issuers", "revoked_key_ids", "revoked_selections", "min_epochs"}
        neg = t.get("negative_control_ensure_ascii_false")
        if neg:
            raw = json.dumps(n, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            assert raw.hex() == neg["bytes_hex"] and neg["bytes_hex"] != t["expected"]["canonical_bytes_hex"]
            assert "sha256:" + sha_hex(raw) == neg["fingerprint"] != t["expected"]["trust_snapshot_fingerprint"]
            assert c.isascii() and not raw.isascii()
    base = next(t for t in V["trust_snapshots"] if t["id"] == "TF-001")
    n = base["input"]
    f0 = plain_digest(normalize_snapshot(n))

    def mut(fn):
        m = json.loads(json.dumps(n))
        fn(m)
        return plain_digest(normalize_snapshot(m))

    changes = [
        lambda m: m.__setitem__("snapshot_id", "snap-example-8"),
        lambda m: m.__setitem__("version", 8),
        lambda m: m.__setitem__("valid_until", "2026-12-02T00:00:00Z"),
        lambda m: m["issuers"][0].__setitem__("key_id", "key-example-2"),
        lambda m: m["issuers"][0].__setitem__("issuer_id", "issuer-b"),
        lambda m: m["issuers"][0].__setitem__("alg", "ed25519x"),
        lambda m: m["issuers"][0].__setitem__("public_key", "ff" + m["issuers"][0]["public_key"][2:]),
        lambda m: m["issuers"][0]["authority"][0].__setitem__(4, "op-other"),
        lambda m: m["issuers"][0]["authority"].append(["a", "b", "c", "d", "e"]),
        lambda m: m["revoked_key_ids"].append("key-old-2"),
        lambda m: m["revoked_selections"][0].__setitem__(1, 3),
        lambda m: m["min_epochs"][0].__setitem__(1, 4),
    ]
    results = [mut(c) for c in changes]
    assert all(r != f0 for r in results)
    assert len(set(results)) == len(results)
    for t in V["trust_snapshots_invalid"]:
        with pytest.raises(Refuse) as info:
            check_snapshot_duplicates(t["input"])
        assert info.value.code == t["expected"]["code"] and t["expected"]["code"] in _outcome_codes()
    # a snapshot content change changes the fingerprint; an order-only change does not
    tf2 = next(t for t in V["trust_snapshots"] if t["id"] == "TF-002")
    shuffled = json.loads(json.dumps(tf2["input"]))
    shuffled["issuers"].reverse()
    shuffled["revoked_selections"].reverse()
    assert plain_digest(normalize_snapshot(shuffled)) == tf2["expected"]["trust_snapshot_fingerprint"]


def test_revoked_selection_epoch_sorts_numerically_not_lexically():
    s = next(t for t in V["trust_snapshots"] if t["id"] == "TF-002")["input"]
    assert [p for p in s["revoked_selections"] if p[0] == "sel-old-1"] == [["sel-old-1", 10], ["sel-old-1", 2]]
    n = normalize_snapshot(s)
    assert [p for p in n["revoked_selections"] if p[0] == "sel-old-1"] == [["sel-old-1", 2], ["sel-old-1", 10]]


def test_outcome_map_is_the_48_code_map_and_no_new_codes_are_used():
    codes = _outcome_codes()
    assert len(codes) == 48
    assert [c["code"] for c in V["outcome_map"]["codes"]] == list(codes)
    assert {c["code"]: c["layer"] for c in V["outcome_map"]["codes"]} == codes
    assert "trust_snapshot_version_stale" in codes and "selection_withdrawn" in codes
    assert V["outcome_map"]["code_count"] == 48
    used = set(V["outcome_map"]["codes_used_by_this_file"])
    assert used <= set(codes)
    expected_used = {v["expected"]["code"] for v in V["invalid"]} | {g["expected"]["code"] for g in V["guard_digest_checks"] if "code" in g["expected"]} \
        | {t["expected"]["code"] for t in V["trust_snapshots_invalid"]}
    for key in ("integer_boundary", "effective_integer_boundary", "effective_payloads_invalid", "effective_preimage_invalid", "scope_keys_invalid", "effective_inputs"):
        expected_used |= {x["expected"]["code"] for x in V[key] if x["expected"]["result"] == "refuse"}
    expected_used |= {x["expected"]["code"] for x in V["scope_projection"] if x["expected"]["result"] == "refuse"}
    assert used == expected_used
    ld_bytes = (ROOT / "docs" / "p1-extraction-plan" / "data" / "ld02-outcome-map.json").read_bytes()
    assert sha_hex(ld_bytes) == V["pins"]["outcome_map_sha256"], "ld02 outcome map changed: re-review the identity spec and vectors"


def _section(text, start, end_regex):
    i = text.index(start)
    m = re.search(end_regex, text[i + len(start):], re.M)
    return text[i:i + len(start) + m.start()] if m else text[i:]


def test_contract_section_pins():
    """Pin the exact contract and ADR sections the spec depends on. A change to any of them requires re-reviewing the spec and vectors."""
    pins = V["pins"]
    texts = {"contract": (ROOT / pins["contract_file"]).read_text(encoding="utf-8"), "adr": (ROOT / pins["adr_file"]).read_text(encoding="utf-8"),
             "readme": (ROOT / pins["readme_file"]).read_text(encoding="utf-8")}  # ruling N-6: the README must exist; absence is a failure
    assert len(pins["enforced_section_hashes"]) >= 9 and "readme:## Verdicts (ruling R1)" in pins["enforced_section_hashes"]
    for name, pin in pins["enforced_section_hashes"].items():
        which = name.split(":", 1)[0]
        section = _section(texts[which], pin["start"], pin["end_regex"])
        got = hashlib.sha256(section.rstrip().encode("utf-8")).hexdigest()
        assert got == pin["sha256"], "pinned section changed: %s (re-review docs/ext-implementation/ext-s1-5-*.md and the vectors)" % name
    # N-6: the four-verdict table itself is enforced (the section hash above covers it); the four names are asserted as table rows too
    verdict_section = _section(texts["readme"], "## Verdicts (ruling R1)", r"^## ")
    for verdict in VERDICT_CLASSES:
        assert re.search(r"^\| `%s` \|" % verdict, verdict_section, re.M), verdict
    # anchors the spec quotes verbatim
    c = texts["contract"]
    for anchor in ("## 4. Canonical policy binding (D-14, D-15)", "### 4.1 Serialization and digest", "### 4.2 Two states of the object",
                   "ocs-reg/r08-v2/policy-binding\\n", r"`\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z`", "`sha256:[0-9a-f]{64}`"):
        assert anchor in c, anchor


def test_spec_document_exists_and_references_the_pins():
    spec = (ROOT / V["spec"]).read_text(encoding="utf-8")
    for heading in ("Consumers and handoff", "Open questions for Architect", "Additive codes ruled required (not yet in CODES_V2)"):
        assert heading.lower() in spec.lower()
    for oq in ("OQ-1", "OQ-2", "OQ-3", "OQ-4", "OQ-5", "N-1", "N-3", "N-4", "N-5", "N-6"):
        assert oq in spec
    assert "handled by the docs-only amendment PR" in spec and "overlay_not_applied" in spec
    assert "never yields `overlay_not_applied`" in spec and "component-owner-derived" in spec.lower()
    for domain in ("ocs-reg/r08-v2/effective-policy", "ocs-reg/r08-v2/scope-key", "ocs-scope-key/1", "ocs-effective-policy/1"):
        assert domain in spec, domain
    for field, rng in V["profile"]["integer_ranges"].items():
        assert "`%s" % field in spec, field
    assert V["pins"]["contract_file_sha256_informational"] in spec
    for name in V["pins"]["enforced_section_hashes"]:
        assert V["pins"]["enforced_section_hashes"][name]["sha256"] in spec, name
    assert V["pins"]["outcome_map_sha256"] in spec
    for member in V["profile"]["members"]:
        assert "`%s`" % member in spec, member


def _binding_with(member, literal_text):
    d = load(next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"])
    d[member] = "@@LIT@@"
    return json.dumps(d).replace('"@@LIT@@"', literal_text)


def test_integer_ranges_are_explicit_per_field_and_independent():
    ranges = V["profile"]["integer_ranges"]
    assert set(ranges) >= {"record_version", "selection_epoch", "trust_snapshot_version", "status_max_age_seconds", "approval_max_age_seconds",
                           "class_status_max_age_seconds", "policy_generation"}
    for field, (lo, hi) in RANGES.items():
        assert (ranges[field]["min"], ranges[field]["max"]) == (lo, hi), field
        assert ranges[field]["domain"] == "binding"
    for field in ("status_max_age_seconds", "approval_max_age_seconds", "class_status_max_age_seconds"):
        assert ranges[field]["max"] == AGE_RANGES["effective"][1] == AGE_RANGES["registry"][1] == AGE_RANGES["caller"][1] == 2147483647
        assert {k: AGE_RANGES[k][0] for k in AGE_RANGES} == ranges[field]["role_min"] == {"registry": 1, "caller": 0, "effective": 0}
        assert ranges[field]["status"] == "ARCHITECT_RULED"
    # statuses are honest: two are source-justified, the snapshot version is component-owner-derived (N-1), the generation counter is reserved
    assert ranges["record_version"]["status"] == ranges["selection_epoch"]["status"] == "SOURCE_JUSTIFIED"
    assert ranges["trust_snapshot_version"]["status"] == "COMPONENT_OWNER_DERIVED"  # N-1: no source ceiling; bound derived from the representation
    gen = ranges["policy_generation"]
    assert gen["status"] == "RESERVED" and (gen["min"], gen["max"]) == RESERVED_POLICY_GENERATION
    assert "policy_generation" not in V["profile"]["members"] and "policy_generation" not in V["profile"]["integer_members"]
    assert not any("policy_generation" in v.get("input_json", "") for v in V["valid"] + V["invalid"])
    # the epoch and age domains are different entries and the generation domain is wider than both (never assumed equal)
    assert gen["max"] > RANGES["selection_epoch"][1]
    snap = ranges["trust_snapshot_version"]
    assert snap["max"] == RANGES["trust_snapshot_version"][1] == 9007199254740991 != RANGES["selection_epoch"][1]
    assert "status_max_age_seconds" in snap["independent_of"] and "selection_epoch" in snap["independent_of"]
    assert V["profile"]["integer_members"] == list(INT_MEMBERS)
    # source ties (reads text only, imports nothing): the two source-justified bounds are the Registry's own
    common = (ROOT / "registry_successor" / "common.py").read_text(encoding="utf-8")
    assert "MAX_INT = 2**31 - 1" in common
    assert "1 <= value <= c.MAX_INT" in (ROOT / "registry_successor" / "record.py").read_text(encoding="utf-8")
    assert "1 <= value <= c.MAX_INT" in (ROOT / "registry_successor" / "selection.py").read_text(encoding="utf-8")
    assert "trust.version < 1" in (ROOT / "registry_successor" / "verify.py").read_text(encoding="utf-8")  # snapshot version: floor only, no ceiling


def test_trust_snapshot_version_bound_is_tied_to_source_text_never_imports():
    """Ruling N-1: the claim 'no source ceiling for the trust snapshot version, so the bound is the canonical-JSON safe integer range' is tied
    to the source TEXT (read, never imported). The evidence entries recorded in the vector file must each occur in their file; the snapshot
    code paths must contain no MAX_INT, MAX_VERSION, 2**31 or 2**53 ceiling; MAX_INT must be used only by record.py and selection.py."""
    snap = V["profile"]["integer_ranges"]["trust_snapshot_version"]
    assert snap["status"] == "COMPONENT_OWNER_DERIVED" and (snap["min"], snap["max"]) == RANGES["trust_snapshot_version"]
    assert snap["max"] == 2**53 - 1  # the largest integer exact in every JSON implementation
    assert len(snap["source_evidence"]) >= 6
    for ev in snap["source_evidence"]:
        text = (ROOT / ev["file"]).read_text(encoding="utf-8")
        assert ev["text"] in text, ("source evidence text not found", ev["file"], ev["text"])
        assert isinstance(ev["line"], int) and ev["line"] >= 1 and ev["shows"]
    verify = (ROOT / "registry_successor" / "verify.py").read_text(encoding="utf-8")
    body = verify[verify.index("def _normalize_trust"):]
    body = body[:body.index("\ndef ", 10)]
    assert "trust.version < 1" in body
    # N-10(c) (RULED) requires the 2^53 - 1 representation bound at ingest, so that exact bound is allowed to appear in the verifier once the source
    # PR applies it; any OTHER ceiling (the int32 record/epoch domain) would be a wrong borrowed bound and still fails here.
    for ceiling in ("MAX_INT", "MAX_VERSION", "2**31", "2147483647"):
        assert ceiling not in body, ("a snapshot-version ceiling appeared in the verifier: re-derive the bound", ceiling)
    scanned = [p for pkg in ("registry_successor", "registry_consumer") for p in sorted((ROOT / pkg).glob("*.py"))] + [ROOT / "registry_conformance" / "highwater.py"]
    users = set()
    for path in scanned:
        for line in path.read_text(encoding="utf-8").splitlines():
            if "snapshot" in line.lower() and any(t in line for t in ("MAX_INT", "MAX_VERSION", "2**31", "2147483647")):
                pytest.fail("snapshot line with a ceiling in %s: %s" % (path.name, line))
            if "MAX_INT" in line or "MAX_VERSION" in line:
                users.add(path.name)
    assert users <= {"common.py", "record.py", "selection.py", "v2_selection.py", "v3_selection.py", "consumer.py"}, users  # S01: v2_selection.py mirrors selection.py's record_version bound; M2 PR-1: so does v3_selection.py
    common_text = (ROOT / "registry_successor" / "common.py").read_text(encoding="utf-8")
    assert 'json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)' in common_text  # unbounded Python ints
    hw = (ROOT / "registry_conformance" / "highwater.py").read_text(encoding="utf-8")
    assert 'fl["snapshot_version"] < 0' in hw and 'b["trust_snapshot_version"] >= 1' in hw


def test_integer_boundary_vectors_cover_every_integer_field():
    required = {"min", "max", "max-plus-1", "zero", "minus-1", "bool-true", "float", "string"}
    seen = {}
    for vec in V["integer_boundary"]:
        seen.setdefault(vec["field"], set()).add(vec["case"])
        lo, hi = RANGES[vec["field"]]
        exp = vec["expected"]
        if vec["case"] == "min":
            assert vec["literal"] == str(lo) and exp["result"] == "valid"
        if vec["case"] == "max":
            assert vec["literal"] == str(hi) and exp["result"] == "valid"
        if vec["case"] == "max-plus-1":
            assert vec["literal"] == str(hi + 1) and exp["result"] == "refuse" and exp["code"] == "field_invalid"
        assert vec["input_json"] == _binding_with(vec["field"], vec["literal"]), vec["id"]
        if exp["result"] == "valid":
            got = run_binding(vec)
            assert got["canonical_bytes_hex"] == exp["canonical_bytes_hex"] and got["binding_digest"] == exp["binding_digest"], vec["id"]
        else:
            with pytest.raises(Refuse) as info:
                run_binding(vec)
            assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
            assert exp["code"] in _outcome_codes()
    assert set(seen) == set(INT_MEMBERS)
    for field, cases in seen.items():
        assert required <= cases, (field, required - cases)
    # the three fields reach their maximum independently: a vector where only one is at its maximum is valid for each
    assert len({v["expected"]["binding_digest"] for v in V["integer_boundary"] if v["expected"]["result"] == "valid"}) == 7
    # trust_snapshot_version is NOT in the 2**31 - 1 domain: 2147483648 is valid for it and refused for the two source-bounded counters
    extra = next(v for v in V["integer_boundary"] if v["id"] == "IB-trust_snapshot_version-int32-max-plus-1")
    assert extra["literal"] == "2147483648" and extra["expected"]["result"] == "valid"
    assert next(v for v in V["integer_boundary"] if v["id"] == "IB-selection_epoch-max-plus-1")["literal"] == "2147483648"


def test_effective_integer_boundary_vectors_per_age_field_and_role():
    required = {("registry", "min"), ("registry", "zero"), ("registry", "max"), ("registry", "max-plus-1"), ("registry", "minus-1"), ("registry", "bool-true"),
                ("registry", "float"), ("registry", "string"), ("effective", "zero"), ("effective", "max"), ("effective", "max-plus-1"),
                ("effective", "minus-1"), ("effective", "bool-true"), ("effective", "float"), ("effective", "string")}
    seen = {}
    for vec in V["effective_integer_boundary"]:
        seen.setdefault(vec["field"], set()).add((vec["role"], vec["case"]))
        exp = vec["expected"]
        try:
            doc = validate_effective_payload(vec["family"], load(vec["payload_json"]), vec["role"])
            got = ("valid", None, None)
        except Refuse as r:
            got = ("refuse", r.code, r.member)
        assert got[0] == exp["result"], vec["id"]
        if exp["result"] == "refuse":
            assert got[1:] == (exp["code"], exp["member"]) and exp["code"] in _outcome_codes(), vec["id"]
        elif vec["role"] == "effective":
            pre = effective_preimage(vec["family"], doc)
            assert canon(pre).hex() == exp["preimage_canonical_bytes_hex"] and effective_digest_of_preimage(pre) == exp["effective_policy_digest"], vec["id"]
        if vec["case"] in ("max", "max-plus-1"):
            assert vec["literal"] == str(2147483647 + (vec["case"] == "max-plus-1"))
    assert set(seen) == {"status_max_age_seconds", "approval_max_age_seconds", "class_status_max_age_seconds.class-a"}
    for field, cases in seen.items():
        assert required <= cases, (field, required - cases)
    # registry 0 refuses while effective 0 (a caller value of 0 stays 0) is valid
    r0 = {(v["field"], v["role"], v["case"]): v["expected"]["result"] for v in V["effective_integer_boundary"]}
    assert r0[("status_max_age_seconds", "registry", "zero")] == "refuse" and r0[("status_max_age_seconds", "effective", "zero")] == "valid"


def test_scope_projection_is_identity_or_refusal_never_normalization():
    codes = _outcome_codes()
    assert V["profile"]["scope_projection"]["error"] == {"code": "field_invalid", "layer": "shape", "stage": "projection"}
    rule = V["profile"]["scope_projection"]["decision"]  # ruling N-5: no overlay_not_applied shortcut anywhere
    assert "never yields overlay_not_applied" in rule["never"] and "refused for every participation" in rule["binding_creation"]
    assert "overlay_not_applied" not in rule["required"] + rule["optional"]
    assert "authenticated" in rule["optional"] and "absence or withdrawal" in rule["optional"] and "original projection refusal code" in rule["optional"]
    kinds = {v["category"] for v in V["scope_projection"]}
    assert {"ascii", "unicode", "ascii-out-of-grammar"} <= kinds
    assert any(v["expected"]["result"] == "projected" for v in V["scope_projection"])
    for vec in V["scope_projection"]:
        scope, exp = vec["statement_scope"], vec["expected"]
        # every vector is a scope a signed statement carries today: it passes the existing statement token validator
        assert vec["statement_validator_accepts"] is True and all(statement_valid_token(v) for v in scope.values()), vec["id"]
        # original statement scope bytes are retained verbatim as provenance
        assert {k: bytes.fromhex(h).decode("utf-8") for k, h in vec["original_scope_utf8_hex"].items()} == scope, vec["id"]
        if exp["result"] == "projected":
            out = project_scope(scope)
            assert out == scope == exp["scope"] and all(out[k] is scope[k] or out[k] == scope[k] for k in out)
            assert all(out[k].encode("utf-8") == scope[k].encode("utf-8") for k in out)
        else:
            with pytest.raises(Refuse) as info:
                project_scope(scope)
            assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
            assert exp["code"] in codes and exp["layer"] == "shape" and exp["stage"] == "projection" and exp["binding_created"] is False
            assert "decision_optional" not in exp and "decision_required" not in exp, vec["id"]
            assert exp["projection_refusal_code"] == "field_invalid" and exp["yields_overlay_not_applied"] is False and exp["yields_accept"] is False, vec["id"]
            # a binding built by hand around that scope is refused by the binding validator too (the two layers agree)
            doc = load(next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"])
            doc["scope"] = scope
            with pytest.raises(Refuse) as info2:
                validate_binding(doc)
            assert (info2.value.code, info2.value.member) == ("field_invalid", exp["member"]), vec["id"]
    # the hazard the rule exists for: the refused tokens WOULD become valid identifiers under normalization, truncation or folding
    hazards = 0
    for vec in V["scope_projection"]:
        if vec["expected"]["result"] != "refuse":
            continue
        for tok in vec["statement_scope"].values():
            for variant in (unicodedata.normalize("NFC", tok), unicodedata.normalize("NFKC", tok), unicodedata.normalize("NFKD", tok), tok.casefold(), tok[:128]):
                if variant != tok and variant.isascii() and IDENT.fullmatch(variant):
                    hazards += 1
    assert hazards >= 3, "the vectors must contain tokens that normalization would silently turn into valid identifiers"
    # two distinct refused tokens are never collapsed: they refuse independently (no hash or transliteration can make them equal)
    nfc = next(v for v in V["scope_projection"] if v["id"] == "PJ-010")["statement_scope"]["tenant"]
    nfd = next(v for v in V["scope_projection"] if v["id"] == "PJ-011")["statement_scope"]["tenant"]
    assert nfc != nfd and unicodedata.normalize("NFC", nfd) == nfc
    # sorted-path first failing member is reported when several scope members are bad
    multi = next(v for v in V["scope_projection"] if v["id"] == "PJ-019")
    assert multi["expected"]["member"] == "scope.authority_domain"


def test_unprojectable_scope_effects_never_authorize_and_never_yield_overlay_not_applied():
    """Ruling N-5. Binding creation is refused for every participation; required refuses (HOLD only if state is indeterminate); optional
    falls back ONLY through the authenticated optional-state determination when the activation state permits it, and the fallback carries
    the original projection refusal code as an absence or withdrawal evidence record. Nothing yields overlay_not_applied or ACCEPT."""
    rows = V["scope_projection_effects"]
    assert {(r["participation"], r["activation_state"], r["optional_determination"]) for r in rows} >= {
        ("required", "known", "n/a"), ("required", "indeterminate", "n/a"), ("optional", "permits_optional", "authenticated"),
        ("optional", "forbids_fallback", "authenticated"), ("optional", "permits_optional", "not_authenticated"), ("optional", "indeterminate", "authenticated")}
    fallbacks = 0
    for r in rows:
        exp = r["expected"]
        want = projection_effect(r["participation"], r["activation_state"], r["optional_determination"])
        assert {k: exp[k] for k in want} == want, r["id"]
        assert exp["binding_created"] is False and exp["projection_verdict"] == "REFUSE", r["id"]
        assert exp["yields_overlay_not_applied"] is False and exp["yields_accept"] is False, r["id"]
        assert "overlay_not_applied" not in json.dumps(exp).replace("yields_overlay_not_applied", ""), r["id"]
        assert exp["effect_outcome"] in ("REFUSE", "UNKNOWN_FAIL_CLOSED", "optional_fallback_via_determination"), r["id"]
        if r["participation"] == "required":
            assert exp["effect_outcome"] != "optional_fallback_via_determination" and exp["fallback_permitted"] is False
        if exp["fallback_permitted"]:
            fallbacks += 1
            assert r["participation"] == "optional" and r["activation_state"] == "permits_optional" and r["optional_determination"] == "authenticated"
            assert exp["fallback_evidence"] == {"kind": "absence_or_withdrawal", "projection_refusal_code": "field_invalid"}
        else:
            assert exp["fallback_evidence"] is None
    assert fallbacks == 1
    # exhaustive: over every combination only (optional, permits, authenticated) can fall back, and nothing ever ACCEPTs
    for part in ("required", "optional"):
        for st in ("known", "permits_optional", "forbids_fallback", "indeterminate"):
            for det in ("authenticated", "not_authenticated", "n/a"):
                out = projection_effect(part, st, det)
                assert out["effect_outcome"] != "ACCEPT" and out["decision_kind"] != "overlay_not_applied"
                assert out["fallback_permitted"] is ((part, st, det) == ("optional", "permits_optional", "authenticated"))
    # no vector, mapping row or evidence entry anywhere uses overlay_not_applied as a projection verdict
    for vec in V["scope_projection"]:
        assert "overlay_not_applied" not in json.dumps(vec["expected"]).replace("yields_overlay_not_applied", ""), vec["id"]
    row = next(r for r in V["defect_mapping"] if r["id"] == "MP-field_invalid-projection")
    assert "overlay_not_applied" not in json.dumps(row).replace("Never overlay_not_applied", "") and "projection_refusal_code" in row["evidence_fields"]
    assert "projection_refusal_code" in V["evidence_field_vocabulary"]


def test_scope_key_unambiguous_versioned_and_domain_separated():
    sk = V["profile"]["scope_key"]
    assert sk["profile"] == SCOPE_KEY_PROFILE and tuple(sk["members"]) == SK_MEMBERS and tuple(sk["all_members_with_profile"]) == SK_TOP
    assert sk["domain_prefix_hex"] == SCOPE_KEY_PREFIX.hex()
    # the seven members are exactly the contract's seven (7.4 line 2): selection_id, consumer_id, tenant, institution, authority_domain, operation, family
    contract = (ROOT / "docs" / "r08-v2-contract.md").read_text(encoding="utf-8")
    assert "the scope key built from the claim's `selection_id`, `consumer_id`, `tenant`, `institution`, `authority_domain`, `operation` and `family`" in contract
    assert set(SK_MEMBERS) == {"selection_id", "consumer_id", "tenant", "institution", "authority_domain", "operation", "family"}
    # nothing that changes at a transition is a member
    assert set(sk["omitted_on_purpose"]).isdisjoint(SK_TOP) and {"selection_epoch", "record_version", "activation_ref"} <= set(sk["omitted_on_purpose"])
    by_id = {}
    for vec in V["scope_keys"]:
        doc = validate_scope_key(load(vec["input_json"]))
        exp = vec["expected"]
        assert scope_key_text(doc).hex() == exp["scope_key_canonical_bytes_hex"] and scope_key_text(doc).decode("ascii") == exp["scope_key_canonical_ascii"], vec["id"]
        assert scope_key_digest(doc) == exp["scope_key_digest"], vec["id"]
        assert exp["scope_key_digest"] != exp["digest_without_prefix_control"] == plain_digest(doc), vec["id"]
        by_id[vec["id"]] = vec
    # derived from the binding vector: Runtime and Control Plane derive the same key from the same completed binding
    bv = load(next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"])
    assert scope_key_from_binding(bv) == load(by_id["SK-001"]["input_json"])
    for v in V["valid"]:
        key = scope_key_from_binding(load(v["input_json"]))
        validate_scope_key(key)  # every valid binding yields a valid key
    assert scope_key_text(load(by_id["SK-002"]["input_json"])) == scope_key_text(load(by_id["SK-001"]["input_json"]))
    # changing ANY member changes the key; a case change changes it; digests are pairwise distinct
    muts = [v for v in V["scope_keys"] if v["id"].startswith("SK-MUT-")]
    assert {m["mutated_member"] for m in muts} == set(SK_MEMBERS)
    base = by_id["SK-001"]["expected"]
    for m in muts + [by_id["SK-CASE"]]:
        assert m["expected"]["scope_key_digest"] != base["scope_key_digest"] and m["expected"]["scope_key_canonical_bytes_hex"] != base["scope_key_canonical_bytes_hex"]
    digests = [v["expected"]["scope_key_digest"] for v in V["scope_keys"] if "equivalent_to" not in v]
    assert len(digests) == len(set(digests))
    # delimiter-collision pairs: a naive join collides, the versioned canonical key does not
    order = ["selection_id", "consumer_id", "tenant", "institution", "authority_domain", "operation", "family"]
    assert len(V["scope_key_collision_pairs"]) >= 5
    for pr_ in V["scope_key_collision_pairs"]:
        a, b = validate_scope_key(pr_["a"]), validate_scope_key(pr_["b"])
        d = pr_["naive_delimiter"]
        assert d.join(a[k] for k in order) == d.join(b[k] for k in order) == pr_["naive_join_a"] == pr_["naive_join_b"], pr_["id"]
        assert a != b and scope_key_text(a) != scope_key_text(b), pr_["id"]
        assert scope_key_digest(a) == pr_["expected"]["scope_key_digest_a"] != scope_key_digest(b) == pr_["expected"]["scope_key_digest_b"], pr_["id"]
        assert scope_key_text(a).decode("ascii") == pr_["expected"]["canonical_ascii_a"] and scope_key_text(b).decode("ascii") == pr_["expected"]["canonical_ascii_b"]
        # every member is a quoted JSON string with its own key: no value can run into the next member
        assert all(('"%s":"%s"' % (k, a[k])) in pr_["expected"]["canonical_ascii_a"] for k in SK_MEMBERS)
    # exhaustive small-domain check: no two distinct 7-tuples over a tiny alphabet containing every delimiter collide
    import itertools
    alphabet = ["a", "a:b", "b:c", "c", "a.b"]
    seen_keys = {}
    for tup in itertools.product(alphabet, repeat=3):
        key = scope_key_text(dict(zip(("scope_key_profile",) + ("tenant", "consumer_id", "operation"), (SCOPE_KEY_PROFILE,) + tup),
                                   authority_domain="d", family="f", institution="i", selection_id="s"))
        assert key not in seen_keys
        seen_keys[key] = tup
    # invalid keys
    codes = _outcome_codes()
    for vec in V["scope_keys_invalid"]:
        exp = vec["expected"]
        assert exp["code"] in codes
        with pytest.raises(Refuse) as info:
            validate_scope_key(load(vec["input_json"]))
        assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
    # domain separation: not the binding prefix, not no prefix
    key = load(by_id["SK-001"]["input_json"])
    assert "sha256:" + sha_hex(DOMAIN_PREFIX + canon(key)) != scope_key_digest(key)
    assert "sha256:" + sha_hex(SCOPE_KEY_PREFIX[:-1] + canon(key)) != scope_key_digest(key)


CONTRACT_DECISION_KINDS = ("applied", "applied_deny_all", "overlay_not_applied", "required_policy_unavailable")  # contract 3.2 (closed set)


def test_defect_mapping_uses_only_codes_v2_plus_marked_proposals_and_keeps_verdict_classes_apart():
    codes = _outcome_codes()
    assert tuple(V["profile"]["verdict_classes"]) == VERDICT_CLASSES
    prop = V["ruled_additive_codes"]
    assert prop["status"] == "RULED_REQUIRED_NOT_YET_IN_CODES_V2" and "proposed_additive_codes" not in V  # ruling N-4
    proposed = {c["code"]: c for c in prop["codes"]}
    assert set(proposed).isdisjoint(codes), "a proposed code must never repurpose or shadow an existing CODES_V2 entry"
    assert len(codes) == 48
    vocab = set(V["evidence_field_vocabulary"])
    ids = [r["id"] for r in V["defect_mapping"]]
    assert len(ids) == len(set(ids))
    by_code = {}
    for r in V["defect_mapping"]:
        assert set(r["evidence_fields"]) <= vocab and {"registry_code", "layer", "participation", "decision_kind", "stage"} <= set(r["evidence_fields"]), r["id"]
        code, cls = r["registry_code"], r["verdict_class"]
        assert r["decision_kind"] in CONTRACT_DECISION_KINDS or r["decision_kind"] is None, (r["id"], "decision kind outside contract 3.2")
        if code is None:  # deny-all and evaluator denial are not Registry refusals and carry no Registry verdict class
            assert cls is None and (r["decision_kind"] == "applied_deny_all" or r.get("non_registry_outcome") == "evaluator_denied"), r["id"]
            continue
        assert r["decision_kind"] == "required_policy_unavailable", r["id"]  # every refusal row is the required-participation kind; optional never gets a shortcut
        assert cls in VERDICT_CLASSES, r["id"]
        assert "proposed_additive_code" not in r, r["id"]
        if r.get("ruled_additive_code"):
            assert code in proposed and proposed[code]["verdict_class"] == cls, r["id"]
        else:
            assert code in codes, ("no existing CODES_V2 entry named", r["id"], code)
        by_code.setdefault(code, set()).add(cls)
    # the proposal list is exactly the proposed codes that rows use
    assert set(proposed) == {r["registry_code"] for r in V["defect_mapping"] if r.get("ruled_additive_code")}
    # a cause code names one class; the single documented dual-class code is trust_snapshot_expired (README): REFUSE for a delivered expired
    # snapshot, UNKNOWN_FAIL_CLOSED for the expired current snapshot at the guard. trust_snapshot_missing is mapped in its guard form only.
    assert {k for k, v in by_code.items() if len(v) > 1} == {"trust_snapshot_expired"}, {k: v for k, v in by_code.items() if len(v) > 1}
    assert by_code["trust_snapshot_expired"] == {"REFUSE", "UNKNOWN_FAIL_CLOSED"} and by_code["trust_snapshot_missing"] == {"UNKNOWN_FAIL_CLOSED"}
    withdrawn = next(r for r in V["defect_mapping"] if r["id"] == "MP-selection_withdrawn")
    assert withdrawn["optional_branch"]["decision_kind"] == "overlay_not_applied" and withdrawn["optional_branch"]["registry_code"] == "selection_withdrawn"
    assert "authenticated optional-state determination" in withdrawn["optional_branch"]["only_through"]
    stale = {c for c, v in by_code.items() if v == {"REFUSE_STALE"}}
    assert stale == {"selection_epoch_stale", "trust_snapshot_version_stale"}
    terminal = {"selection_revoked", "selection_withdrawn", "issuer_key_revoked"}
    assert all(by_code[c] == {"REFUSE"} for c in terminal)  # terminal revocation and withdrawal are never stale and never HOLD
    hold = {c for c, v in by_code.items() if "UNKNOWN_FAIL_CLOSED" in v}
    assert hold == {"trust_snapshot_missing", "trust_snapshot_expired", "store_unknown"}
    assert hold.isdisjoint(terminal | stale)
    for r in V["defect_mapping"]:
        if r["registry_code"]:
            assert (r["retry"] == "after_authoritative_state_available") == (r["verdict_class"] == "UNKNOWN_FAIL_CLOSED"), r["id"]
    assert all(r["verdict_class"] in ("REFUSE", "REFUSE_STALE") for r in V["defect_mapping"] if r["registry_code"] in terminal | stale or r["id"] == "MP-trust_snapshot_expired-delivered")
    # the original Registry cause is always preserved as structured evidence and distinct causes keep distinct rows
    assert len([r for r in V["defect_mapping"] if r["registry_code"]]) == len({(r["registry_code"], r["id"]) for r in V["defect_mapping"] if r["registry_code"]})
    for c in ("selection_withdrawn", "selection_revoked", "selection_epoch_stale", "trust_snapshot_version_stale", "issuer_key_revoked", "store_unknown"):
        assert c in by_code
    kinds = {r["decision_kind"] for r in V["defect_mapping"]}
    assert "applied_deny_all" in kinds and any(r.get("non_registry_outcome") == "evaluator_denied" for r in V["defect_mapping"])
    # review SF-4: one code, one class in every context; the two contexts of trust_snapshot_missing are told apart by the evidence field `stage`
    miss = [r for r in V["defect_mapping"] if r["registry_code"] == "trust_snapshot_missing"]
    assert {r["id"]: r["stage_value"] for r in miss} == {"MP-trust_snapshot_missing-input": "INPUT", "MP-trust_snapshot_missing-durable-state": "DURABLE_STATE"}  # ruling N-11
    assert all(r["verdict_class"] == "UNKNOWN_FAIL_CLOSED" and r["retry"] == "after_authoritative_state_available" and "definitive" not in r["defect"].lower() for r in miss)
    assert not any("definitive input fact" in json.dumps(r) for r in V["defect_mapping"])
    # review SF-6, narrowed by the N-12 ruling: an optional branch exists only for the withdrawn row (a valid withdrawal transition); expiry matches no
    # permitted basis, so it carries no branch and is RULED not a fallback basis (N-12(c)); never_activated has no registry code
    branches = {r["registry_code"]: r["optional_branch"] for r in V["defect_mapping"] if "optional_branch" in r}
    assert set(branches) == {"selection_withdrawn"}
    exp_row = next(r for r in V["defect_mapping"] if r["id"] == "MP-selection_expired")
    assert "optional_branch" not in exp_row and "RULED" in exp_row["optional_rule"] and "N-12(c)" in exp_row["optional_rule"] and "not a fallback basis" in exp_row["optional_rule"] and "owner decision" not in exp_row["optional_rule"]
    for code, br in branches.items():
        assert br["decision_kind"] == "overlay_not_applied" and br["registry_code"] == code and br["applied"] is False, code
        assert "authenticated optional-state determination" in br["only_through"], code
    assert len(V["defect_mapping"]) == 35
    # every code used by an identity validator in this file appears in the mapping
    mapped = set(by_code)
    for c in V["outcome_map"]["codes_used_by_this_file"]:
        assert c in mapped, c  # no exemption: every code an identity validator can emit has a mapping row (review, Copilot)
    # the vocabulary matches the merged conformance kit when that README is present in this checkout (PR #28 is merged; the README is present at base f618cdf)
    # the vocabulary is the one in the merged conformance README, whose verdict section is an ENFORCED pin (test_contract_section_pins; ruling N-6)
    readme = ROOT / "docs" / "conformance" / "README.md"
    assert readme.exists(), "docs/conformance/README.md (PR #28) must be present: the four-verdict vocabulary is pinned"
    text = readme.read_text(encoding="utf-8")
    for v in VERDICT_CLASSES:
        assert "`%s`" % v in text, v


def _generate(gen):
    if gen["kind"] == "bv1_padded":
        base = next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"].encode("utf-8")
        return base + b" " * (gen["total_bytes"] - len(base))
    if gen["kind"] == "multibyte_string":
        return ('{"x":"' + "\u00e9" * gen["count"] + '"}').encode("utf-8")
    if gen["kind"] == "invalid_utf8_padded":  # an invalid UTF-8 byte at the start, then space padding up to total_bytes (over the size limit)
        head = b'{"a":"\xff"}'
        return head + b" " * (gen["total_bytes"] - len(head))
    if gen["kind"] == "deep_array":  # depth levels of '[' around `inner`; `closed` False leaves them unclosed; `tail` follows the document
        return ("[" * gen["depth"] + gen["inner"] + ("]" * gen["depth"] if gen["closed"] else "") + gen["tail"]).encode("utf-8")
    if gen["kind"] == "int_literal":  # BV-001 with selection_epoch replaced by an integer literal of `digits` nines
        text = next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"]
        assert '"selection_epoch": 3' in text
        return text.replace('"selection_epoch": 3', '"selection_epoch": %s%s' % (gen["sign"], "9" * gen["digits"])).encode("utf-8")
    assert gen["kind"] == "nested"
    o, c = ('{"a":', "}") if gen["container"] == "object" else ("[", "]")
    containers = gen["depth"] - 1  # "depth" is the depth of the deepest value; the scalar leaf counts as a level (root = 1)
    return (o * containers + "1" + c * containers).encode("utf-8")


def test_input_boundary_vectors_pin_size_text_and_depth_edges():
    """Spec 5.5.1 and 5.5.2: size is counted in UTF-8 bytes before parsing; input is strict UTF-8; a BOM is not stripped; depth 8 passes and 9 refuses."""
    codes = _outcome_codes()
    by_id = {v["id"]: v for v in V["valid"]}
    seen = set()
    for vec in V["input_boundary"]:
        raw = _generate(vec["generate"]) if "generate" in vec else (bytes.fromhex(vec["input_hex"]) if "input_hex" in vec else vec["input_json"])
        exp = vec["expected"]
        if exp["result"] == "valid":
            doc = validate_binding(load(raw))
            assert binding_digest(doc) == by_id[exp["equals"]]["expected"]["binding_digest"] and canon(doc).hex() == by_id[exp["equals"]]["expected"]["canonical_bytes_hex"], vec["id"]
            assert len(raw) == MAX_DOCUMENT_BYTES
        else:
            assert exp["code"] in codes and codes[exp["code"]] == exp["layer"], vec["id"]
            with pytest.raises(Refuse) as info:
                validate_binding(load(raw))
            assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vec["id"]
        seen.add(exp.get("code", "valid"))
    assert {"valid", "input_not_text", "input_too_large", "json_nesting_too_deep", "json_malformed", "field_missing", "field_type_invalid", "field_invalid"} <= seen
    # the byte-versus-character distinction is real in the vectors: the over-limit multibyte document is under 65536 CHARACTERS
    over = _generate(next(v for v in V["input_boundary"] if v["id"] == "IBND-MULTIBYTE-OVER-LIMIT")["generate"])
    assert len(over) > MAX_DOCUMENT_BYTES and len(over.decode("utf-8")) < MAX_DOCUMENT_BYTES
    # a str entry point (the registry loader takes str only) agrees with the bytes entry point on every vector it can receive
    for vec in V["input_boundary"]:
        if "generate" in vec or "input_hex" in vec:
            data = _generate(vec["generate"]) if "generate" in vec else bytes.fromhex(vec["input_hex"])
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                assert vec["expected"]["code"] == "input_not_text", vec["id"]
                continue
            if vec["expected"]["result"] == "valid":
                continue
            with pytest.raises(Refuse) as a:
                validate_binding(load(data))
            with pytest.raises(Refuse) as b:
                validate_binding(load(text))
            assert (a.value.code, a.value.member) == (b.value.code, b.value.member), vec["id"]
    with pytest.raises(Refuse) as info:
        load("\ud800")  # a lone surrogate in a str cannot be encoded as UTF-8
    assert info.value.code == "input_not_text"
    for not_text in (None, 5, [], {}):
        with pytest.raises(Refuse) as info:
            load(not_text)
        assert info.value.code == "input_not_text"


def test_scanner_grammar_edges_are_each_pinned_by_a_vector_so_a_second_parser_cannot_drift():
    """Spec 5.5.1 step 2 (review SF-A): the syntax step decides json_malformed against a later-step code, so every grammar edge of a hand-written
    or lenient scanner needs its own vector. Each document is also checked against a stock strict parser, so the expectation is the RFC, not the reference."""
    vecs = {v["id"]: v for v in V["invalid"] if v["category"] == "scanner grammar"}
    assert set(vecs) == {"BI-GRAMMAR-ARRAY-TRAILING-COMMA", "BI-GRAMMAR-NEG-INFINITY", "BI-GRAMMAR-FLOAT-TRAILING-DOT", "BI-GRAMMAR-EXPONENT-NO-DIGITS",
                         "BI-GRAMMAR-UNKNOWN-ESCAPE", "BI-GRAMMAR-UNICODE-ESCAPE-PLUS-SIGN", "BI-GRAMMAR-UNICODE-ESCAPE-UNDERSCORE",
                         "BI-GRAMMAR-UNICODE-ESCAPE-SPACE", "BI-GRAMMAR-UNICODE-ESCAPE-NON-HEX", "BI-GRAMMAR-RAW-TAB-IN-STRING",
                         "BI-GRAMMAR-RAW-NEWLINE-IN-STRING", "BI-GRAMMAR-FORM-FEED-WHITESPACE"}
    for vid, vec in vecs.items():
        text = vec["input_json"]
        with pytest.raises(Refuse) as info:
            load(text)
        assert info.value.code == vec["expected"]["code"], vid
        if vec["expected"]["code"] == "json_malformed":
            with pytest.raises(ValueError):  # a strict RFC 8259 parser refuses the same document
                json.loads(text)
        else:
            assert vid == "BI-GRAMMAR-NEG-INFINITY" and vec["expected"]["code"] == "json_number_unsupported"
            assert json.loads(text) == {"a": float("-inf")}  # a stock parser ACCEPTS the token: only a hand scan can map it to the spec's code
    # the three \u hazards are exactly what a naive int(h, 16) hex check lets through
    for h in ("+123", "1_23", " 123"):
        assert int(h, 16) == int(h.replace("_", "").replace("+", "").strip(), 16)
    # the grammar edges are decided at the syntax step: a lenient scanner would have reached a later step, so the same document padded with a
    # float would report json_number_unsupported if the syntax defect were missed
    for text in ('{"a":[1,],"b":2.5}', '{"a":1.,"b":NaN}', '{"a":"\\x","b":Infinity}'):
        with pytest.raises(Refuse) as info:
            load(text)
        assert info.value.code == "json_malformed", text


def test_unknown_members_are_reported_in_code_point_order_not_utf16_order():
    """Spec 5.3 and 5.5: the sorted path order of the member-set phase is by code point. U+E000 sorts before U+10000 by code point and after it by UTF-16."""
    a, b = "\ue000", "\U00010000"
    assert sorted([a, b]) == [a, b] and sorted([a, b], key=lambda x: x.encode("utf-16-be")) == [b, a]
    for vid in ("BI-ORDER-UNKNOWN-MEMBERS-CODE-POINT-ORDER-TOP", "BI-ORDER-UNKNOWN-MEMBERS-CODE-POINT-ORDER-SCOPE"):
        vec = next(v for v in V["invalid"] if v["id"] == vid)
        assert vec["expected"]["code"] == "field_unknown"
        with pytest.raises(Refuse) as info:
            validate_binding(load(vec["input_json"]))
        assert (info.value.code, info.value.member) == ("field_unknown", vec["expected"]["member"]), vid
        # the UTF-16 answer is a different member, so a UTF-16 sorter fails the vector
        unknown = [m for m in ((a, b) if vid.endswith("TOP") else ("scope." + a, "scope." + b))]
        assert sorted(unknown, key=lambda x: x.encode("utf-16-be"))[0] != vec["expected"]["member"]
    vec = next(v for v in V["effective_payloads_invalid"] if v["id"] == "EI-ORDER-UNKNOWN-MEMBERS-CODE-POINT-ORDER")
    with pytest.raises(Refuse) as info:
        validate_effective_payload(vec["family"], load(vec["payload_json"]), vec["role"])
    assert (info.value.code, info.value.member) == ("field_unknown", a)
    assert sorted([a, b], key=lambda x: x.encode("utf-16-be"))[0] != vec["expected"]["member"]


def test_input_not_text_is_reported_before_input_too_large():
    """Spec 5.5.1 step 1: strict decoding comes first, so an over-size document that is also invalid UTF-8 is input_not_text."""
    vec = next(v for v in V["input_boundary"] if v["id"] == "IBND-NOT-TEXT-BEFORE-TOO-LARGE")
    raw = _generate(vec["generate"])
    assert len(raw) > MAX_DOCUMENT_BYTES
    with pytest.raises(Refuse) as info:
        load(raw)
    assert info.value.code == "input_not_text"
    over_valid = next(v for v in V["input_boundary"] if v["id"] == "IBND-OVER-LIMIT")
    with pytest.raises(Refuse) as info:
        load(_generate(over_valid["generate"]))
    assert info.value.code == "input_too_large"  # the same size with valid UTF-8 is the size refusal


def test_parse_order_is_syntax_then_numbers_then_duplicates_then_depth_and_huge_integers_are_syntactically_valid():
    """Spec 5.5.1: a single total order, independent of a parser's streaming order."""
    order = {v["id"]: v["expected"]["code"] for v in V["invalid"] if v["category"] == "parse order"}
    assert order["BI-PARSE-ORDER-DUP-THEN-TRAILING"] == "json_malformed"
    assert order["BI-PARSE-ORDER-FLOAT-BEFORE-DUP"] == order["BI-PARSE-ORDER-FLOAT-BEFORE-DEPTH"] == order["BI-PARSE-ORDER-NAN-BEFORE-DUP"] == "json_number_unsupported"
    assert order["BI-PARSE-ORDER-DUP-BEFORE-DEPTH"] == "json_duplicate_key"
    assert order["BI-PARSE-ORDER-DEPTH-THEN-TRAILING"] == order["BI-PARSE-ORDER-FLOAT-THEN-TRAILING"] == "json_malformed"
    # a streaming implementation (object hook fires on close, float hook fires on parse) gives the other answer: the order is not accidental
    class _Stream(Exception):
        pass

    def _hook(pairs):
        out = {}
        for k, v in pairs:
            if k in out:
                raise _Stream("dup")
            out[k] = v
        return out
    with pytest.raises(_Stream):  # the object hook fires as soon as the object closes, before the trailing text is examined
        json.loads('{"a":1,"a":2} x', object_pairs_hook=_hook)
    # huge integers: valid syntax at any length, refused only by the field range, never json_malformed (CPython's digit limit is not a code)
    for vid, member in (("BI-INT-5000-DIGITS", "selection_epoch"), ("BI-INT-5000-DIGITS-NEGATIVE", "selection_epoch")):
        vec = next(v for v in V["invalid"] if v["id"] == vid)
        assert vec["expected"] == {"result": "refuse", "code": "field_invalid", "layer": "shape", "member": member}
        doc = load(vec["input_json"])
        assert abs(doc[member]) >= BIG_INT_SENTINEL
        with pytest.raises(Refuse) as info:
            validate_binding(doc)
        assert (info.value.code, info.value.member) == ("field_invalid", member)
    import sys
    int_vecs = [v for v in V["input_boundary"] if "generate" in v and v["generate"]["kind"] == "int_literal"]
    assert {v["generate"]["digits"] for v in int_vecs} >= {20, 21, 700, 3999, 4001}  # lengths below, at and above every old threshold (4000, 4300)
    big_vec = next(v for v in V["invalid"] if v["id"] == "BI-INT-5000-DIGITS")
    saved = sys.get_int_max_str_digits()
    try:
        for limit in (0, 640, 700, 4000, 4300):
            sys.set_int_max_str_digits(limit)
            for vec in int_vecs + [big_vec]:
                raw = _generate(vec["generate"]) if "generate" in vec else bytes.fromhex(vec["input_hex"]) if "input_hex" in vec else vec["input_json"]
                with pytest.raises(Refuse) as info:
                    validate_binding(load(raw))
                assert (info.value.code, info.value.member) == ("field_invalid", "selection_epoch"), (limit, vec["id"])  # independent of the interpreter digit limit
    finally:
        sys.set_int_max_str_digits(saved)
    # a 20-digit literal is the exact value, a 21-digit one is classified by length (both outside every range)
    assert load('{"x":%s}' % ("9" * 20))["x"] == int("9" * 20) and load('{"x":%s}' % ("9" * 21))["x"] == BIG_INT_SENTINEL
    assert load('{"x":-%s}' % ("9" * 700))["x"] == -BIG_INT_SENTINEL


def test_deep_documents_follow_the_parse_order_whatever_the_recursion_limit():
    """Spec 5.5.1 (review SF-1): the syntax, number-literal and duplicate-key steps are not limited by recursion depth, so a document nested far
    beyond any recursive parser's cap gets the answer of the order, not a depth refusal first. Run with the recursion limit lowered to just
    above the current stack depth to prove the reference scan is iterative."""
    import inspect
    import sys
    deep = [v for v in V["input_boundary"] if "generate" in v and v["generate"]["kind"] == "deep_array"]
    assert {v["expected"]["code"] for v in deep} == {"json_malformed", "json_nesting_too_deep", "json_number_unsupported", "json_duplicate_key", "input_too_large"}
    assert max(v["generate"]["depth"] for v in deep) >= 32768 and min(v["generate"]["depth"] for v in deep) >= 9000
    saved = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(len(inspect.stack(0)) + 60)  # far below the 9000 to 32769 levels the vectors nest
        for vec in deep:
            raw = _generate(vec["generate"])
            with pytest.raises(Refuse) as info:
                validate_binding(load(raw))
            assert (info.value.code, info.value.member) == (vec["expected"]["code"], vec["expected"]["member"]), vec["id"]
    finally:
        sys.setrecursionlimit(saved)
    # the stdlib parser is NOT such a scan: it gives up with a recursion error (this is why the spec states the requirement)
    sys.setrecursionlimit(saved)
    with pytest.raises(RecursionError):
        json.loads("[" * 200000 + "]" * 200000)
    # the unclosed document is malformed, the balanced one with a float is a number-literal refusal, at every depth
    for depth in (9, 100, 5000):
        with pytest.raises(Refuse) as a:
            load("[" * depth)
        assert a.value.code == "json_malformed"
        with pytest.raises(Refuse) as b:
            load("[" * depth + "1.5" + "]" * depth)
        assert b.value.code == "json_number_unsupported"
    # duplicate keys inside nested containers and the pair-versus-raw key comparison
    for vid, code in (("BI-DUP-NESTED-IN-ARRAY", "json_duplicate_key"), ("BI-DUP-ESCAPED-PAIR-VS-RAW", "json_duplicate_key"), ("BI-LONE-SURROGATE-KEYS-DISTINCT", "field_missing")):
        vec = next(v for v in V["invalid"] if v["id"] == vid)
        assert vec["expected"]["code"] == code
        with pytest.raises(Refuse) as info:
            validate_binding(load(vec["input_json"]))
        assert (info.value.code, info.value.member) == (code, vec["expected"]["member"]), vid
    assert load('{"\\ud83d\\ude00":1}') == {"\U0001F600": 1}  # a high plus a low surrogate escape is one code point
    assert list(load('{"\\ud800":1,"\\ud801":2}')) == ["\ud800", "\ud801"]  # lone surrogate escapes stay distinct code units


def test_sorted_means_unicode_code_point_order_and_utf16_order_is_refused():
    """Spec 5.3 and 6: every 'sorted' list (payload lists, trust snapshot arrays) is ordered by code point, equal to UTF-8 byte order."""
    a, b = "\uff21", "\U00010400"  # code point order a < b; UTF-16 code unit order b < a
    assert sorted([a, b]) == [a, b] and sorted([a, b], key=lambda x: x.encode("utf-16-be")) == [b, a]
    assert sorted([a, b], key=lambda x: x.encode("utf-8")) == [a, b]
    assert frozen_token_valid(a) and frozen_token_valid(b)
    assert not frozen_token_valid("\uffff")  # U+FFFF is a noncharacter (Cn): a different example is needed to separate the orders
    ep = next(e for e in V["effective_payloads"] if e["id"] == "EP-015")
    assert ep["payload"]["allowed_actions"] == [a, b]
    assert effective_policy_digest(ep["family"], ep["payload"]) == ep["expected"]["effective_policy_digest"]
    swapped = json.loads(json.dumps(ep["payload"]))
    swapped["allowed_actions"] = [b, a]
    with pytest.raises(Refuse) as info:
        validate_effective_payload(ep["family"], swapped)
    assert (info.value.code, info.value.member) == ("field_invalid", "allowed_actions")
    assert effective_digest_of_preimage({**effective_preimage(ep["family"], ep["payload"]), "effective": swapped}) != ep["expected"]["effective_policy_digest"]
    assert compose(ep["family"], ep["inputs"]["registry"], ep["inputs"]["caller"]) == ep["payload"]
    inv = next(v for v in V["effective_payloads_invalid"] if v["id"] == "EI-016")
    with pytest.raises(Refuse) as info:
        validate_effective_payload(inv["family"], load(inv["payload_json"]), inv["role"])
    assert (info.value.code, info.value.member) == ("field_invalid", "allowed_actions")


def _ser_utf16(value):
    """The wrong serializer a review mutant uses: object keys sorted by UTF-16 code unit."""
    if isinstance(value, dict):
        return "{" + ",".join(ser_string(k) + ":" + _ser_utf16(value[k]) for k in sorted(value, key=lambda x: x.encode("utf-16-be"))) + "}"
    if isinstance(value, list):
        return "[" + ",".join(_ser_utf16(x) for x in value) + "]"
    return ser(value)


def test_object_keys_and_snapshot_arrays_sort_by_code_point_and_snapshot_arrays_are_normalized_not_refused():
    """Spec 5.3 (review SF-3): which orderings are refused (effective payload lists, field_invalid) and which are normalized (snapshot arrays and
    every object's keys, never refused for order; a duplicate refuses trust_snapshot_invalid)."""
    a, b = "\uff21", "\U00010400"
    ep = next(e for e in V["effective_payloads"] if e["id"] == "EP-016")
    classes = ep["payload"]["class_status_max_age_seconds"]
    assert list(classes) == [b, a], "the input lists the class names in UTF-16 order; input order is irrelevant"
    pre = effective_preimage(ep["family"], ep["payload"])
    ascii_ = canon(pre).decode("ascii")
    assert ascii_.index("\\uff21") < ascii_.index("\\ud801\\udc00"), "canonical bytes list U+FF21 before U+10400 (code point order)"
    assert effective_digest_of_preimage(pre) == ep["expected"]["effective_policy_digest"]
    wrong = "sha256:" + sha_hex(EFFECTIVE_PREFIX + _ser_utf16(pre).encode("ascii"))
    assert wrong != ep["expected"]["effective_policy_digest"], "a UTF-16 key sort is a different digest"
    assert frozen_token_valid(a) and frozen_token_valid(b)
    tf = next(t for t in V["trust_snapshots"] if t["id"] == "TF-005")
    check_snapshot_duplicates(tf["input"])  # unsorted input is NOT refused (it is normalized)
    assert tf["input"]["revoked_key_ids"][0] == "key-" + b, "the input lists the non-BMP id first (UTF-16 order)"
    n = normalize_snapshot(tf["input"])
    assert n["revoked_key_ids"] == ["key-old-1", "key-" + a, "key-" + b]
    tenants = [x[1] for x in n["issuers"][0]["authority"] if x[1] in ("tenant-" + a, "tenant-" + b)]
    assert tenants == ["tenant-" + a, "tenant-" + b]
    utf16 = json.loads(json.dumps(n))
    utf16["revoked_key_ids"] = sorted(utf16["revoked_key_ids"], key=lambda x: x.encode("utf-16-be"))
    utf16["issuers"][0]["authority"] = sorted(utf16["issuers"][0]["authority"], key=lambda r: [x.encode("utf-16-be") for x in r])
    assert utf16["revoked_key_ids"] != n["revoked_key_ids"] and utf16["issuers"][0]["authority"] != n["issuers"][0]["authority"]
    assert plain_digest(utf16) != tf["expected"]["trust_snapshot_fingerprint"], "a UTF-16 normalizer gives another fingerprint"
    # a duplicate is the one refusal for snapshot arrays, and it is trust_snapshot_invalid (not field_invalid)
    dup = json.loads(json.dumps(tf["input"]))
    dup["revoked_key_ids"].append("key-" + a)
    with pytest.raises(Refuse) as info:
        check_snapshot_duplicates(dup)
    assert info.value.code == "trust_snapshot_invalid"
    spec = (ROOT / "docs" / "ext-implementation" / "ext-s1-5-effective-policy-identity-spec.md").read_text(encoding="utf-8")
    assert "normalized" in spec and "`trust_snapshot_invalid`" in spec


def test_contract_version_keying_one_code_on_both_paths_and_identity_exists_for_r08_v2_only():
    """Spec 6: the shipped r08-v1 table registers f1a, but no effective-policy identity exists for r08-v1 for any family."""
    for family in FAMILIES:
        assert REGISTERED_CONTRACT_VERSIONS[family] == ("r08-v2",)
        with pytest.raises(Refuse) as info:
            registered_family_version(family, "r08-v1")
        assert (info.value.code, info.value.member) == ("contract_unsupported", "contract_version")
    f1a_in = next(v for v in V["effective_inputs"] if v["id"] == "EFV-020")
    f1a_pre = next(v for v in V["effective_preimage_invalid"] if v["id"] == "EPI-008")
    assert load(f1a_in["input_json"])["family"] == "f1a-local-execution-allowlist" == load(f1a_pre["input_json"])["family"]
    assert f1a_in["expected"] == {"result": "refuse", "code": "contract_unsupported", "member": "contract_version"}
    assert f1a_pre["expected"] == f1a_in["expected"]
    assert next(v for v in V["effective_preimage_invalid"] if v["id"] == "EPI-002")["expected"] == next(v for v in V["effective_inputs"] if v["id"] == "EFV-016")["expected"]
    for fam, ver in (("f1a-local-execution-allowlist", "r08-v1"), ("f1ab-local-execution-allowlist", "r08-v1")):
        base = next(e for e in V["effective_payloads"] if e["family"] == fam)["payload"]
        for fn in (lambda: validate_effective_inputs({"family": fam, "contract_version": ver, "effective": base}),
                   lambda: validate_preimage({"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": ver, "family": fam, "family_version": "v1", "deny_all": [], "effective": base})):
            with pytest.raises(Refuse) as info:
                fn()
            assert info.value.code == "contract_unsupported"


def project_snapshot_version(v):
    """Projection of a verified TrustSnapshot.version into the binding: identity or refusal at the projection stage (the verifier itself accepts any
    strict int >= 1 and applies no ceiling)."""
    lo, hi = RANGES["trust_snapshot_version"]
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise Refuse("field_invalid", "trust_snapshot_version")
    return v


def test_every_projection_stage_refusal_has_the_same_participation_effects_and_never_falls_open():
    """Spec 5.6 (generalized, review S-5): a scope token and a snapshot version above 2^53-1 are both projection-stage refusals with one effect rule."""
    assert "exactly the participation effects of scope_projection_effects" in V["projection_stage_refusals_rule"]
    import inspect
    # a documentation check of THIS reference only (it proves nothing about an implementation); the normative join is the data of projection_effect_matrix
    assert list(inspect.signature(projection_effect).parameters) == ["participation", "activation_state", "determination"]  # no member argument
    refused = projected = 0
    for vec in V["projection_stage_refusals"]:
        exp = vec["expected"]
        assert vec["verifier_accepts"] is True and vec["trust_snapshot_version"] >= 1
        if exp["result"] == "projected":
            assert project_snapshot_version(vec["trust_snapshot_version"]) == exp["trust_snapshot_version"]
            projected += 1
            continue
        refused += 1
        with pytest.raises(Refuse) as info:
            project_snapshot_version(vec["trust_snapshot_version"])
        assert (info.value.code, info.value.member) == (exp["code"], exp["member"])
        assert exp["stage"] == "projection" and exp["binding_created"] is False and exp["projection_refusal_code"] == "field_invalid"
        assert exp["yields_overlay_not_applied"] is False and exp["yields_accept"] is False
        doc = load(next(v for v in V["valid"] if v["id"] == "BV-001")["input_json"])
        doc["trust_snapshot_version"] = vec["trust_snapshot_version"]
        with pytest.raises(Refuse) as info2:
            validate_binding(doc)  # the binding validator agrees with the projection
        assert (info2.value.code, info2.value.member) == ("field_invalid", "trust_snapshot_version")
    assert refused >= 2 and projected >= 1
    # the effect rule is the same function for both kinds: only (optional, permits_optional, authenticated) may fall back
    for part in ("required", "optional"):
        for st in ("known", "permits_optional", "forbids_fallback", "indeterminate"):
            for det in ("authenticated", "not_authenticated", "n/a"):
                out = projection_effect(part, st, det)
                assert out["decision_kind"] != "overlay_not_applied" and out["effect_outcome"] != "ACCEPT"
                assert out["fallback_permitted"] is ((part, st, det) == ("optional", "permits_optional", "authenticated"))
    row = next(r for r in V["defect_mapping"] if r["id"] == "MP-field_invalid-projection")
    assert "trust snapshot version" in row["defect"] and "any projection-stage refusal" in row["defect"]


def test_projection_effect_matrix_joins_refusal_kind_participation_and_state():
    """Spec 5.6 (review SF-6 and SF-7): the effect is joined to each refusal kind in DATA (refusal kind x participation x state x determination
    -> outcome), so the claim 'every projection-stage refusal has the same effect' is not only prose or a signature inspection."""
    rows = V["projection_effect_matrix"]
    kinds = V["profile"]["projection_stage"]["kinds"]
    assert set(kinds) == {"scope_token", "trust_snapshot_version", "effective_family_unsupported", "effective_contract_unsupported", "effective_payload_field_invalid"}
    assert {r["refusal_kind"] for r in rows} == set(kinds) and len(rows) == len(kinds) * 6
    by_case = {}
    for r in rows:
        exp = r["expected"]
        want = projection_effect_for(r["registry_code"], r["participation"], r["activation_state"], r["optional_determination"])
        assert (exp["effect_outcome"], exp["fallback_permitted"]) == (want["effect_outcome"], want["fallback_permitted"]), r["id"]
        evidence_code = want["fallback_evidence"]["projection_refusal_code"] if want["fallback_evidence"] else None
        assert exp["fallback_evidence_code"] == evidence_code == (r["registry_code"] if exp["fallback_permitted"] else None), r["id"]
        assert exp["binding_created"] is False and exp["yields_overlay_not_applied"] is False and exp["yields_accept"] is False, r["id"]
        assert exp["effect_outcome"] in ("REFUSE", "UNKNOWN_FAIL_CLOSED", "optional_fallback_via_determination"), r["id"]
        by_case.setdefault((r["participation"], r["activation_state"], r["optional_determination"]), set()).add(exp["effect_outcome"])
    assert len(by_case) == 6 and all(len(v) == 1 for v in by_case.values()), "one outcome per case: the effect never depends on the refusal kind"
    assert sum(1 for r in rows if r["expected"]["fallback_permitted"]) == len(kinds)  # exactly one case per kind can fall back
    assert {r["registry_code"] for r in rows} <= set(_outcome_codes())
    # the derivation refusals are real refusals of the reference identity code, with the codes the rows carry
    refusals = {
        "family_unsupported": lambda: effective_policy_digest("f9-unknown-family", {}),
        "contract_unsupported": lambda: effective_policy_digest("f4-control-plane-age-bounds", {"status_max_age_seconds": 1, "approval_max_age_seconds": 1}, "r08-v1"),
        "field_invalid": lambda: effective_policy_digest("f4-control-plane-age-bounds", {"status_max_age_seconds": 2147483648, "approval_max_age_seconds": 1}),
    }
    for kind, code in (("effective_family_unsupported", "family_unsupported"), ("effective_contract_unsupported", "contract_unsupported"), ("effective_payload_field_invalid", "field_invalid")):
        assert {r["registry_code"] for r in rows if r["refusal_kind"] == kind} == {code}
        with pytest.raises(Refuse) as info:
            refusals[code]()
        assert info.value.code == code
    # an unknown participation is refused, never read as optional; the rule survives python -O (a raise, not an assert)
    for vec in V["projection_effect_invalid"]:
        with pytest.raises(Refuse) as info:
            projection_effect(vec["participation"], vec["activation_state"], vec["optional_determination"])
        assert (info.value.code, info.value.member) == (vec["expected"]["code"], vec["expected"]["member"]), vec["id"]
    import sys
    code = ("import importlib.util\ns = importlib.util.spec_from_file_location('t', %r)\nm = importlib.util.module_from_spec(s)\ns.loader.exec_module(m)\n"
            "try:\n    m.projection_effect('OPTIONAL', 'permits_optional', 'authenticated')\n    print('NOT_REFUSED')\nexcept m.Refuse as e:\n    print(e.code)\n") % str(Path(__file__))
    out = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True, timeout=60, check=True).stdout.strip()
    assert out == "field_invalid"
    assert "RULED" in V["projection_effect_matrix_rule"] and "does not establish 'never activated'" in V["projection_effect_matrix_rule"]  # N-12 ruled (was a residual)


_JS = r"""
const fs = require('fs');
const V = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const crypto = require('crypto');
const cmp = (a, b) => { const x = Array.from(a), y = Array.from(b); const n = Math.min(x.length, y.length);
 for (let i = 0; i < n; i++) { const d = x[i].codePointAt(0) - y[i].codePointAt(0); if (d) return d; } return x.length - y.length; };
function ss(s){let o='"';for(const ch of s){const c=ch.codePointAt(0);
 if(c===0x22)o+='\\"';else if(c===0x5c)o+='\\\\';else if(c===8)o+='\\b';else if(c===12)o+='\\f';else if(c===10)o+='\\n';
 else if(c===13)o+='\\r';else if(c===9)o+='\\t';else if(c<0x20||c===0x7f)o+='\\u'+c.toString(16).padStart(4,'0');
 else if(c<0x80)o+=ch;else if(c<0x10000)o+='\\u'+c.toString(16).padStart(4,'0');
 else{const d=c-0x10000;o+='\\u'+(0xd800+(d>>10)).toString(16)+'\\u'+(0xdc00+(d&0x3ff)).toString(16);}}return o+'"';}
function ser(v){if(v===null)return 'null';if(typeof v==='number')return String(v);if(typeof v==='string')return ss(v);
 if(Array.isArray(v))return '['+v.map(ser).join(',')+']';
 return '{'+Object.keys(v).sort(cmp).map(k=>ss(k)+':'+ser(v[k])).join(',')+'}';}
const hex = s => Buffer.from(s, 'hex');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const pre = hex(V.profile.domain_prefix_hex), preEff = hex(V.profile.effective_policy.domain_prefix_hex), preSk = hex(V.profile.scope_key.domain_prefix_hex);
const FAM = V.profile.effective_policy.families;
const out = {};
const bindingOut = x => { const c = Buffer.from(ser(JSON.parse(x.input_json)), 'ascii'); return [c.toString('hex'), 'sha256:' + sha(Buffer.concat([pre, c]))]; };
for (const x of V.valid) out[x.id] = bindingOut(x);
for (const x of V.integer_boundary) if (x.expected.result === 'valid') out[x.id] = bindingOut(x);
function compose(fam, reg, cal) {
  const kind = FAM[fam].kind;
  if (kind === 'lists') { const r = {}; for (const k of Object.keys(reg)) r[k] = reg[k].filter(v => cal[k].includes(v)).sort(cmp); return r; }
  if (kind === 'ints') { const r = {}; for (const k of Object.keys(reg)) r[k] = Math.min(reg[k], cal[k]); return r; }
  const m = {}; const rr = reg.class_status_max_age_seconds, cc = cal.class_status_max_age_seconds;
  for (const k of Object.keys(rr)) m[k] = Math.min(rr[k], cc[k]); return { class_status_max_age_seconds: m };
}
function preimage(fam, payload) {
  const f = FAM[fam]; const deny = [];
  if (f.kind === 'lists') for (const k of Object.keys(payload).sort(cmp)) if (payload[k].length === 0) deny.push(k);
  return { effective_policy_profile: V.profile.effective_policy.profile, contract_version: V.profile.effective_policy.contract_version, family: fam,
           family_version: f.version, deny_all: deny, effective: payload };
}
const effOut = (fam, payload) => { const c = Buffer.from(ser(preimage(fam, payload)), 'ascii'); return [c.toString('hex'), 'sha256:' + sha(Buffer.concat([preEff, c]))]; };
for (const x of V.effective_payloads) {
  out[x.id] = effOut(x.family, x.payload);
  if (x.inputs) out[x.id + ':compose'] = ser(compose(x.family, x.inputs.registry, x.inputs.caller)) === ser(x.payload);
}
for (const x of V.effective_integer_boundary) if (x.expected.result === 'valid' && x.role === 'effective') out[x.id] = effOut(x.family, JSON.parse(x.payload_json));
// N-3: family_version is derived from the registered table, never an input. Same member-set, lookup, then payload order as the Python reference.
function effInput(doc) {
  const top = ['contract_version', 'effective', 'family'];
  if (doc === null || typeof doc !== 'object' || Array.isArray(doc)) return ['refuse', 'field_type_invalid', null];
  const miss = top.filter(k => !(k in doc)).sort(cmp); if (miss.length) return ['refuse', 'field_missing', miss[0]];
  const unk = Object.keys(doc).filter(k => !top.includes(k)).sort(cmp); if (unk.length) return ['refuse', 'field_unknown', unk[0]];
  if (typeof doc.family !== 'string') return ['refuse', 'field_type_invalid', 'family'];
  if (typeof doc.contract_version !== 'string') return ['refuse', 'field_type_invalid', 'contract_version'];
  if (!(doc.family in FAM)) return ['refuse', 'family_unsupported', 'family'];
  if (!V.profile.effective_policy.registered_contract_versions.includes(doc.contract_version)) return ['refuse', 'contract_unsupported', 'contract_version'];
  const extra = Object.keys(doc.effective).filter(k => !FAM[doc.family].keys.includes(k)).sort(cmp);
  if (extra.length) return ['refuse', 'field_unknown', extra[0]];
  return ['valid'].concat(effOut(doc.family, doc.effective));
}
for (const x of V.effective_inputs) out[x.id] = effInput(JSON.parse(x.input_json));
const PE = (part, st, det) => part === 'required' ? (st === 'indeterminate' ? 'UNKNOWN_FAIL_CLOSED' : 'REFUSE')
  : part !== 'optional' ? 'INVALID_PARTICIPATION'
  : st === 'indeterminate' ? 'UNKNOWN_FAIL_CLOSED' : (det === 'authenticated' && st === 'permits_optional') ? 'optional_fallback_via_determination' : 'REFUSE';
for (const x of V.scope_projection_effects) out[x.id] = PE(x.participation, x.activation_state, x.optional_determination);
for (const x of V.projection_effect_matrix) out[x.id] = PE(x.participation, x.activation_state, x.optional_determination);
for (const x of V.projection_effect_invalid) out[x.id] = PE(x.participation, x.activation_state, x.optional_determination);
for (const x of V.effective_policy_controls) { const c = Buffer.from(ser(JSON.parse(x.preimage_canonical_ascii)), 'ascii'); out[x.id] = [c.toString('hex'), 'sha256:' + sha(Buffer.concat([preEff, c]))]; }
for (const x of V.trust_snapshots) { const c = Buffer.from(ser(x.expected_normalized || JSON.parse(x.normalized_json)), 'ascii'); out[x.id] = [c.toString('hex'), 'sha256:' + sha(c)]; }
const skOut = o => { const c = Buffer.from(ser(o), 'ascii'); return [c.toString('hex'), 'sha256:' + sha(Buffer.concat([preSk, c]))]; };
for (const x of V.scope_keys) out[x.id] = skOut(JSON.parse(x.input_json));
for (const x of V.scope_key_collision_pairs) out[x.id] = [skOut(x.a)[1], skOut(x.b)[1]];
const IDENT = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
for (const x of V.scope_projection) {
  let res = ['projected', null];
  for (const k of ['authority_domain', 'institution', 'tenant']) { const v = x.statement_scope[k]; if (!(/^[\x00-\x7f]*$/.test(v) && IDENT.test(v))) { res = ['refuse', 'scope.' + k]; break; } }
  out[x.id] = res;
}
// review N-d additions: the identifier matrix, the snapshot version bound, and code point sortedness of every list, recomputed in a second language
V.identifier_matrix.bad_values.forEach((e, i) => { out['IM:' + i] = /^[\x00-\x7f]*$/.test(e.value) && IDENT.test(e.value); });
for (const x of V.projection_stage_refusals) { const v = BigInt(x.trust_snapshot_version); out[x.id] = (v >= 1n && v <= 9007199254740991n) ? 'projected' : 'refuse'; }
for (const x of V.snapshot_version_ingest_bound.vectors) { const t = x.text_repeat ? x.text_repeat[0].repeat(x.text_repeat[1]) : x.text; out[x.id] = (x.representation === 'int' && /^-?(0|[1-9][0-9]*)$/.test(t) && BigInt(t) >= 1n && BigInt(t) <= 9007199254740991n) ? 'accepted' : 'refuse'; }
const sortedLists = p => Object.values(p).every(l => !Array.isArray(l) || l.every((v, i) => i === 0 || cmp(l[i - 1], v) < 0));
for (const x of V.effective_payloads) out[x.id + ':sorted'] = sortedLists(x.payload);
for (const x of V.effective_payloads_invalid) if (x.id === 'EI-016') out[x.id + ':sorted'] = sortedLists(JSON.parse(x.payload_json));
// N-13: the token rule consults the committed, hash-pinned table, never the runtime database
const T = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
out['token:table_sha256'] = sha(fs.readFileSync(process.argv[3]));
const RS = T.excluded_ranges.map(r => [parseInt(r[0], 16), parseInt(r[1], 16)]);
const excl = cp => { let lo = 0, hi = RS.length - 1; while (lo <= hi) { const m = (lo + hi) >> 1; if (cp < RS[m][0]) hi = m - 1; else if (cp > RS[m][1]) lo = m + 1; else return true; } return false; };
const tokenValid = cps => cps.length >= 1 && cps.length <= 128 && !cps.includes(0x2a) && !cps.some(excl);
for (const x of V.token_unicode.vectors) {
  let cps = x.code_points.map(h => parseInt(h, 16)); if (x.repeat) cps = Array(x.repeat).fill(cps[0]);
  out['token:' + x.id] = tokenValid(cps);
  if (x.kind === 'divergent') out['live:' + x.id] = /^[^\p{C}\p{Z}]+$/u.test(String.fromCodePoint(...cps));  // the runtime database, informational only
}
let bm = ''; for (let cp = 0; cp <= 0x10ffff; cp++) bm += excl(cp) ? '1' : '0';
out['token:full_scan'] = [sha(Buffer.from(bm, 'ascii')), (bm.match(/1/g) || []).length];
out['token:node_unicode'] = process.versions.unicode;
console.log(JSON.stringify(out));
"""


def test_node_is_available_under_ci():
    """The second-language check is skipped on a machine without Node.js, but it must never be silently skipped in CI (GitHub-hosted runners ship Node)."""
    if os.environ.get("CI") == "true":
        assert shutil.which("node") is not None, "CI=true but node is missing: the non-Python cross-check would be silently skipped"


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed; the non-Python cross-check runs where Node.js is present and is required under CI=true")
def test_non_python_reference_agrees_byte_for_byte(tmp_path):
    """One non-Python implementation (Node.js, written inline) recomputes every valid binding, effective preimage and digest (including
    composition of narrowed values), scope key and scope-key collision pair, trust snapshot and scope projection verdict."""
    data = json.loads(VECTORS.read_text(encoding="ascii"))
    for t in data["trust_snapshots"]:
        t["normalized_json"] = json.dumps(normalize_snapshot(t["input"]))
    p = tmp_path / "v.json"
    p.write_text(json.dumps(data), encoding="ascii")
    js = tmp_path / "ref.js"
    js.write_text(_JS, encoding="utf-8")
    res = subprocess.run(["node", str(js), str(p), str(TOKEN_TABLE_FILE)], capture_output=True, text=True, timeout=60, check=True)
    got = json.loads(res.stdout)
    by_ep = {e["id"]: e for e in V["effective_payloads"]}
    n = 0
    for vec in V["valid"]:
        assert got[vec["id"]] == [vec["expected"]["canonical_bytes_hex"], vec["expected"]["binding_digest"]], vec["id"]
        n += 1
    for vec in V["integer_boundary"]:
        if vec["expected"]["result"] == "valid":
            assert got[vec["id"]] == [vec["expected"]["canonical_bytes_hex"], vec["expected"]["binding_digest"]], vec["id"]
            n += 1
    for ep in V["effective_payloads"]:
        assert got[ep["id"]] == [ep["expected"]["preimage_canonical_bytes_hex"], ep["expected"]["effective_policy_digest"]], ep["id"]
        if "inputs" in ep:
            assert got[ep["id"] + ":compose"] is True, ep["id"]
        n += 1
    for vec in V["effective_integer_boundary"]:
        if vec["expected"]["result"] == "valid" and vec["role"] == "effective":
            assert got[vec["id"]] == [vec["expected"]["preimage_canonical_bytes_hex"], vec["expected"]["effective_policy_digest"]], vec["id"]
            n += 1
    for c in V["effective_policy_controls"]:
        assert got[c["id"]] == [c["preimage_canonical_bytes_hex"], c["effective_policy_digest"]], c["id"]
        n += 1
    for t in V["trust_snapshots"]:
        assert got[t["id"]] == [t["expected"]["canonical_bytes_hex"], t["expected"]["trust_snapshot_fingerprint"]], t["id"]
        n += 1
    for sk in V["scope_keys"]:
        assert got[sk["id"]] == [sk["expected"]["scope_key_canonical_bytes_hex"], sk["expected"]["scope_key_digest"]], sk["id"]
        n += 1
    for pr_ in V["scope_key_collision_pairs"]:
        assert got[pr_["id"]] == [pr_["expected"]["scope_key_digest_a"], pr_["expected"]["scope_key_digest_b"]] and got[pr_["id"]][0] != got[pr_["id"]][1], pr_["id"]
        n += 1
    for pj in V["scope_projection"]:
        exp = pj["expected"]
        want = ["projected", None] if exp["result"] == "projected" else ["refuse", exp["member"]]
        assert got[pj["id"]] == want, pj["id"]
        n += 1
    for ei in V["effective_inputs"]:
        exp = ei["expected"]
        want = ["valid", exp["canonical_bytes_hex"] if "canonical_bytes_hex" in exp else None, exp["effective_policy_digest"]] if exp["result"] == "valid" else ["refuse", exp["code"], exp["member"]]
        if exp["result"] == "valid":
            assert got[ei["id"]][0] == "valid" and got[ei["id"]][2] == exp["effective_policy_digest"], ei["id"]
            assert got[ei["id"]][1] == by_ep[exp["equals"]]["expected"]["preimage_canonical_bytes_hex"], ei["id"]
        else:
            assert got[ei["id"]] == want, ei["id"]
        n += 1
    for se in V["scope_projection_effects"]:
        assert got[se["id"]] == se["expected"]["effect_outcome"], se["id"]
        n += 1
    for row in V["projection_effect_matrix"]:
        assert got[row["id"]] == row["expected"]["effect_outcome"], row["id"]  # the joined refusal-kind matrix, recomputed in a second language
        n += 1
    for row in V["projection_effect_invalid"]:
        assert got[row["id"]] == "INVALID_PARTICIPATION", row["id"]
        n += 1
    for i, entry in enumerate(V["identifier_matrix"]["bad_values"]):
        assert got["IM:%d" % i] is False, entry  # every bad identifier fails the grammar in the second language too
        n += 1
    for vec in V["projection_stage_refusals"]:
        assert got[vec["id"]] == ("projected" if vec["expected"]["result"] == "projected" else "refuse"), vec["id"]
        n += 1
    for vec in V["snapshot_version_ingest_bound"]["vectors"]:  # N-10(c): the ingest bound decided identically in the second language
        assert got[vec["id"]] == ("accepted" if vec["expected"]["result"] == "accepted_for_authority_evaluation" else "refuse"), vec["id"]
        n += 1
    for ep in V["effective_payloads"]:
        assert got[ep["id"] + ":sorted"] is True, ep["id"]
    assert got["EI-016:sorted"] is False  # UTF-16 order is not code point order
    # N-13: Node consults the same pinned table and decides every token vector identically, including the known divergent code points
    assert got["token:table_sha256"] == TOKEN_TABLE_SHA256 == V["pins"]["token_unicode_table"]["sha256"]
    for vec in V["token_unicode"]["vectors"]:
        assert got["token:" + vec["id"]] is vec["expected"]["valid"], vec["id"]
        n += 1
    pin = V["pins"]["token_unicode_table"]["full_scan"]
    assert got["token:full_scan"] == [pin["bitmap_sha256"], pin["excluded_count"]]  # all 1114112 code points agree between the two runtimes
    # informational: where the Node runtime database is newer than 15.1 it ACCEPTS the divergent code points the frozen table refuses (that is
    # the dependence N-13 removes); where it is not newer there is nothing to show, and the frozen decision above is the only claim made
    # (restricted to Node databases at least as new as 17.0, the measured divergence: a 16.x database has not yet assigned every sample vector)
    if tuple(int(x) for x in got["token:node_unicode"].split(".")[:2]) >= (17, 0):
        assert all(got["live:" + v["id"]] is True for v in V["token_unicode"]["vectors"] if v["kind"] == "divergent")
    assert n >= 80


# ----------------------------------------------------------------------------------------------------------------------
# Architect Batch 6 rulings: N-13 (frozen Unicode token table), N-10, N-11, N-12 and ruling 4.3
# ----------------------------------------------------------------------------------------------------------------------
def _vector_token(vec):
    cps = [int(h, 16) for h in vec["code_points"]]
    if "repeat" in vec:
        cps = cps * vec["repeat"]
    return "".join(chr(c) for c in cps)


def test_frozen_token_table_is_hash_pinned_and_covers_the_whole_code_point_range():
    """N-13: the table is a committed file whose sha256 is pinned in the test AND in the vectors; ranges are ascending, non-adjacent and inside U+0000..U+10FFFF."""
    pin = V["pins"]["token_unicode_table"]
    assert sha_hex(_TOKEN_TABLE_BYTES) == TOKEN_TABLE_SHA256 == pin["sha256"], "token table changed: re-review N-13 and re-pin"
    assert pin["file"] == "docs/ext-implementation/data/ext-s1-5-token-unicode-15.1-excluded-ranges.json" and pin["unicode_version"] == "15.1.0"
    assert pin["status"].startswith("FROZEN") and "PROPOSED" not in pin["status"]  # N-13 ruled: Unicode 15.1.0 is frozen, no longer a proposal
    ver = pin["independent_verification"]  # provenance of the table against three independent 15.1.0 sources, with the one thing that could not be checked
    assert len(ver["sources"]) == 3 and "HTTP 403" in ver["note"] and "NOT compared with the UCD text files" in ver["note"]
    doc = json.loads(_TOKEN_TABLE_BYTES.decode("ascii"))
    assert doc["schema"] == "ocs-token-unicode-table/1" and doc["unicode_version"] == "15.1.0"
    prev_end = -2
    for a, b in _TOKEN_RANGES:
        assert 0 <= a <= b <= 0x10FFFF and a > prev_end + 1, (a, b)
        prev_end = b
    assert V["profile"]["token"]["platform_database_consulted"] is False and V["profile"]["token"]["not_replaced_by_ascii_grammar"] is True
    # the full-scan pin: one character per code point, computed from the table alone
    bitmap = "".join("1" if frozen_cp_excluded(c) else "0" for c in range(0x110000))
    assert sha_hex(bitmap.encode("ascii")) == pin["full_scan"]["bitmap_sha256"] and bitmap.count("1") == pin["full_scan"]["excluded_count"]


def test_frozen_token_table_is_reproducible_where_the_runtime_is_unicode_15_1():
    """N-13: the documented generation procedure (spec 6.1) reproduces the committed table byte for byte on a runtime whose database is exactly 15.1.0.
    On any other runtime the committed table is still authoritative and nothing about authorization changes; only this regeneration check is skipped."""
    if unicodedata.unidata_version != "15.1.0":
        pytest.skip("runtime Unicode %s is not the pinned 15.1.0; the committed table is authoritative" % unicodedata.unidata_version)
    ranges, start = [], None
    for cp in range(0x110000):
        ex = unicodedata.category(chr(cp))[0] in ("C", "Z")
        if ex and start is None:
            start = cp
        elif not ex and start is not None:
            ranges.append([start, cp - 1])
            start = None
    if start is not None:
        ranges.append([start, 0x10FFFF])
    assert [(a, b) for a, b in ranges] == _TOKEN_RANGES


def test_token_rule_does_not_consult_the_runtime_unicode_database(monkeypatch):
    """N-13: the decision is a function of the pinned table alone. Poisoning unicodedata must change nothing."""
    expected = [(v["id"], v["expected"]["valid"]) for v in V["token_unicode"]["vectors"]]

    def boom(*a, **k):
        raise AssertionError("runtime Unicode database consulted")
    with monkeypatch.context() as m:  # scoped, so pytest's own reporting is not affected
        for name in ("category", "normalize", "name", "east_asian_width", "bidirectional", "decomposition", "numeric"):
            m.setattr(unicodedata, name, boom)
        got = [(v["id"], frozen_token_valid(_vector_token(v))) for v in V["token_unicode"]["vectors"]]
    assert got == expected


def test_token_unicode_vectors_and_known_divergent_code_points():
    vecs = V["token_unicode"]["vectors"]
    ids = [v["id"] for v in vecs]
    assert len(ids) == len(set(ids))
    for v in vecs:
        assert frozen_token_valid(_vector_token(v)) is v["expected"]["valid"], v["id"]
    div = [v for v in vecs if v["kind"] == "divergent"]
    assert len(div) >= 20 and "TU-D01" in ids and next(v for v in div if v["id"] == "TU-D01")["code_points"] == ["088F"]
    assert all(v["expected"]["valid"] is False and v["frozen_class"] == "Cn@15.1.0" for v in div)
    meas = V["token_unicode"]["divergence_measured"]
    assert meas["count"] == 5690 and meas["first"] == "U+088F" and meas["last"] == "U+2CEAD"  # U+0080..U+2FFFF only
    assert meas["whole_range"]["count"] == 9988 and meas["whole_range"]["plane3_extra"]["count"] == 4298
    assert any(int(v["code_points"][0], 16) >= 0x30000 for v in div)  # a plane 3 divergent vector
    assert frozen_token_valid("\U0002ebf0") and next(v for v in vecs if v["id"] == "TU-018")["expected"]["valid"] is True  # assigned exactly in 15.1
    # a code point assigned after 15.1.0 (unassigned in the table) is refused, and also refused inside an otherwise valid token
    assert not frozen_token_valid("\u088f") and not frozen_token_valid("a\u088fb") and frozen_token_valid("ab")
    # Unicode entries that were permitted stay permitted: the rule is not silently replaced by the ASCII binding identifier grammar
    for ok in ("\u0416", "\U00010400", "\u4e2d", "a/b", "%", "_x", "caf\u00e9"):
        assert frozen_token_valid(ok), ok  # includes entries outside the ASCII binding identifier grammar ("a/b", "%", "_x", non-ASCII text)
    assert frozen_token_valid("\u0416") and frozen_token_valid("caf\u00e9") and frozen_token_valid("a/b")
    # no normalization is applied: NFC and NFD forms are two different permitted texts, never merged
    assert frozen_token_valid("e\u0301") and frozen_token_valid("\u00e9") and e_not_equal()
    # the effective payload refuses a divergent entry and a divergent F5 class name with field_invalid, whatever the runtime
    for fam, payload, member in (
            ("f1ab-local-execution-allowlist", {"allowed_actions": ["a\u088f"], "allowed_adapters": ["x"], "allowed_units": ["x"], "allowed_institutions": ["x"], "allowed_authority_domains": ["x"]}, "allowed_actions"),
            ("f5-action-class-age-bounds", {"class_status_max_age_seconds": {"c\u088f": 5}}, "class_status_max_age_seconds")):
        with pytest.raises(Refuse) as info:
            validate_effective_payload(fam, payload, "registry")
        assert (info.value.code, info.value.member) == ("field_invalid", member), fam


def e_not_equal():
    return "e\u0301" != "\u00e9"


def test_mutation_guard_a_runtime_database_token_rule_would_disagree_with_the_frozen_table():
    """N-13 negative control: a token rule built from a newer Unicode database (here, a rule that treats the divergent code points as assigned)
    accepts what the frozen table refuses; the vectors detect it. Simulated, because a second database may not be installed."""
    def newer_database_rule(value):
        divergent = {int(h, 16) for v in V["token_unicode"]["vectors"] if v["kind"] == "divergent" for h in v["code_points"]}
        return isinstance(value, str) and 1 <= len(value) <= 128 and "*" not in value and not any(
            frozen_cp_excluded(ord(c)) and ord(c) not in divergent for c in value)
    wrong = [v["id"] for v in V["token_unicode"]["vectors"] if newer_database_rule(_vector_token(v)) is not v["expected"]["valid"]]
    assert wrong and all(i.startswith("TU-D") for i in wrong)  # the divergent vectors, and only they, catch it


def test_defect_mapping_stage_is_typed_and_versioned_n11():
    miss = [r for r in V["defect_mapping"] if r["registry_code"] == "trust_snapshot_missing"]
    assert {r["id"] for r in miss} == {"MP-trust_snapshot_missing-input", "MP-trust_snapshot_missing-durable-state"}
    assert "stage_version" in V["evidence_field_vocabulary"]
    for r in miss:
        assert {"stage", "stage_version"} <= set(r["evidence_fields"]) and r["stage_version"] == "ocs-evidence-stage/1", r["id"]
        assert r["verdict_class"] == "UNKNOWN_FAIL_CLOSED", r["id"]
        assert "NOT equivalent causes" in r["note"] or "not an equivalent underlying cause" in r["note"], r["id"]
    inp, dur = (next(r for r in miss if r["stage_value"] == s) for s in ("INPUT", "DURABLE_STATE"))
    assert inp["defect"] != dur["defect"] and "none was supplied" in inp["defect"] and "durable state" in dur["defect"]
    assert "trust_snapshot_invalid" in inp["note"] and "never `trust_snapshot_missing`" in inp["note"]  # definitive malformed input is not 'missing'
    assert all(r["registry_code"] != "trust_snapshot_missing" or r["verdict_class"] == "UNKNOWN_FAIL_CLOSED" for r in V["defect_mapping"])


def optional_fallback(refusal_kind, participation, store, basis, authenticated, independent, revives):
    """N-12 reference rule. An unknown store is HOLD for every participation; required fails closed; a refused projection never establishes
    'never activated' (the determination must be independent of it); family and contract unsupported need a separate non-participation determination."""
    if participation not in ("required", "optional"):
        raise Refuse("field_invalid", "participation")  # a raise, so the rule survives python -O
    if store != "known":
        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "fallback_permitted": False}
    if participation == "required":
        return {"effect_outcome": "REFUSE", "fallback_permitted": False}
    if not authenticated or not independent or revives:
        return {"effect_outcome": "REFUSE", "fallback_permitted": False}
    if refusal_kind == "selection_expired":
        ok = False  # N-12(c) RULED: expiry is never a fallback basis; it refuses the expired selection (a withdrawn row is decided on the withdrawal)
    elif refusal_kind in ("effective_family_unsupported", "effective_contract_unsupported"):
        ok = basis == "authenticated_non_participation"
    else:
        ok = basis in ("never_required_governed_policy", "valid_withdrawal_fallback_transition")
    return {"effect_outcome": "optional_fallback_via_determination" if ok else "REFUSE", "fallback_permitted": ok}


def test_optional_fallback_rules_n12():
    sec = V["optional_fallback_determination"]
    assert "Architect Batch 6 rulings, N-12" in sec["rule"] and set(sec["bases"]) == {"never_required_governed_policy", "valid_withdrawal_fallback_transition", "authenticated_non_participation"}
    ids = [v["id"] for v in sec["vectors"]]
    assert len(ids) == len(set(ids)) >= 16 and "open_interpretation" not in sec and "RULED" in sec["expiry_rule"] and "N-12(c)" in sec["rule"]
    for v in sec["vectors"]:
        got = optional_fallback(v["refusal_kind"], v["participation"], v["store"], v["determination_basis"], v["authenticated"], v["independent_of_refusal"], v["revives_previous_authority"])
        assert got == {k: v["expected"][k] for k in got}, v["id"]
        assert v["expected"]["yields_overlay_not_applied_by_itself"] is False and "overlay_not_applied" not in v["expected"]["effect_outcome"], v["id"]
        if v["store"] != "known":
            assert v["expected"]["effect_outcome"] == "UNKNOWN_FAIL_CLOSED", v["id"]  # unknown store: HOLD, never a fallback
        if v["participation"] == "required":
            assert v["expected"]["fallback_permitted"] is False, v["id"]
    by_id = {v["id"]: v for v in sec["vectors"]}
    assert by_id["OFD-004"]["independent_of_refusal"] is False and by_id["OFD-004"]["expected"]["fallback_permitted"] is False  # refused projection is not 'never activated'
    assert by_id["OFD-003"]["revives_previous_authority"] is True and by_id["OFD-003"]["expected"]["fallback_permitted"] is False
    for i in ("OFD-010", "OFD-011"):
        assert by_id[i]["expected"]["effect_outcome"] == "REFUSE"  # family/contract unsupported without a separate non-participation determination
    # exhaustive: over every input combination, a fallback needs optional + known store + authenticated + independent + no revival + a matching basis
    kinds = ("scope_token", "trust_snapshot_version", "effective_family_unsupported", "effective_contract_unsupported", "effective_payload_field_invalid", "selection_expired")
    for kind in kinds:
        for part in ("required", "optional"):
            for store in ("known", "unknown"):
                for basis in sec["bases"] + [None, "row_past_valid_until"]:
                    for auth in (True, False):
                        for indep in (True, False):
                            for rev in (True, False):
                                out = optional_fallback(kind, part, store, basis, auth, indep, rev)
                                assert out["effect_outcome"] != "ACCEPT"
                                if out["fallback_permitted"]:
                                    assert (part, store, auth, indep, rev) == ("optional", "known", True, True, False)
                                    assert kind != "selection_expired" and basis != "row_past_valid_until"  # expiry never falls back (N-12(c) RULED)
                                if store == "unknown":
                                    assert out["effect_outcome"] == "UNKNOWN_FAIL_CLOSED"
    with pytest.raises(Refuse):
        optional_fallback("scope_token", "OPTIONAL", "known", "never_required_governed_policy", True, True, False)
    # the mapping rows carry the same rules
    for i in ("MP-family_unsupported", "MP-contract_unsupported"):
        r = next(x for x in V["defect_mapping"] if x["id"] == i)
        assert r["verdict_class"] == "REFUSE" and "non-participation determination" in r["optional_rule"] and "optional_branch" not in r
    su = next(x for x in V["defect_mapping"] if x["id"] == "MP-store_unknown")
    assert su["verdict_class"] == "UNKNOWN_FAIL_CLOSED" and "never overlay_not_applied" in su["optional_rule"] and "optional_branch" not in su
    assert "RULED" in V["projection_effect_matrix_rule"] and "never justifies a fallback" in V["projection_effect_matrix_rule"]


def test_expiry_is_never_a_fallback_basis_n12c():
    """N-12(c) (Architect final ruling): selection_expired does not establish eligibility for optional fallback. Definitive expiry refuses the expired
    selection; unavailable authoritative state is UNKNOWN_FAIL_CLOSED; only an independently authenticated never-required or valid withdrawn state
    permits an otherwise permitted fallback, and that state is decided on its own code, never on the expiry."""
    sec = V["optional_fallback_determination"]
    expiry = [v for v in sec["vectors"] if v["refusal_kind"] == "selection_expired"]
    assert {v["id"] for v in expiry} >= {"OFD-015", "OFD-016", "OFD-017", "OFD-018", "OFD-019", "OFD-020", "OFD-021"}
    for v in expiry:
        want = "UNKNOWN_FAIL_CLOSED" if v["store"] != "known" else "REFUSE"
        assert v["expected"]["effect_outcome"] == want and v["expected"]["fallback_permitted"] is False, v["id"]
    # even the two bases the ruling names cannot turn an expiry into a fallback, with every authentication, independence and revival value
    for basis in ("never_required_governed_policy", "valid_withdrawal_fallback_transition", "authenticated_non_participation", "row_past_valid_until", None):
        for auth in (True, False):
            for indep in (True, False):
                for rev in (True, False):
                    assert optional_fallback("selection_expired", "optional", "known", basis, auth, indep, rev) == {"effect_outcome": "REFUSE", "fallback_permitted": False}
                    assert optional_fallback("selection_expired", "optional", "unknown", basis, auth, indep, rev) == {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "fallback_permitted": False}
    # the same bases DO permit a fallback for a kind they apply to, so the expiry refusal is the ruling and not a blanket rule of the function
    assert optional_fallback("scope_token", "optional", "known", "never_required_governed_policy", True, True, False)["fallback_permitted"] is True
    assert optional_fallback("scope_token", "optional", "known", "valid_withdrawal_fallback_transition", True, True, False)["fallback_permitted"] is True
    row = next(r for r in V["defect_mapping"] if r["id"] == "MP-selection_expired")
    assert row["verdict_class"] == "REFUSE" and "optional_branch" not in row and "UNKNOWN_FAIL_CLOSED" in row["optional_rule"]
    spec = (ROOT / V["spec"]).read_text(encoding="utf-8")
    assert "owner decision that this document does not make" not in spec and "RULED (Architect final ruling, N-12(c))" in spec


class _AuthorityProbe:
    """Records whether authority evaluation or projection was reached."""
    def __init__(self):
        self.authority_calls = self.projection_calls = 0

    def authority(self, version):
        self.authority_calls += 1

    def project(self, version):
        self.projection_calls += 1
        return project_snapshot_version(version)


def ingest_snapshot_version(representation, text, probe):
    """N-10(c) reference: the representation bound is applied FIRST. Only a strict integer in [1, 2^53 - 1] (exact canonical JSON integer text) goes on
    to authority evaluation and projection; anything else is refused at ingest and neither is called."""
    lo, hi = RANGES["trust_snapshot_version"]
    # _parse_int classifies a literal of more than MAX_EXACT_DIGITS digits by LENGTH (int() is never called on it), so a 700- or 5000-digit literal is
    # refused whatever sys.set_int_max_str_digits says (no ValueError from the interpreter's 4300-digit limit)
    ok = representation == "int" and re.fullmatch(r"-?(0|[1-9][0-9]*)", text) is not None and lo <= _parse_int(text) <= hi
    if not ok:
        raise Refuse("trust_snapshot_invalid", "trust_snapshot_version")
    version = int(text)
    probe.authority(version)
    probe.project(version)
    return version


def test_snapshot_version_bound_is_applied_before_authority_evaluation_n10c():
    """N-10(c) (Architect final ruling): the representation bound precedes authorization and projection; an unsupported representation never
    reaches authority evaluation."""
    sec = V["snapshot_version_ingest_bound"]
    assert "BEFORE the snapshot is used in authorization or projection" in sec["rule"] and sec["stage"] == "ingest" and sec["code"] == "trust_snapshot_invalid"
    assert (sec["min"], sec["max"]) == RANGES["trust_snapshot_version"] and "ACCEPTED mapping" in sec["code_status"]
    ids = [v["id"] for v in sec["vectors"]]
    assert ids == ["SIB-%03d" % i for i in range(1, 14)]
    for v in sec["vectors"]:  # long literals are generated (the file stays small): "text_repeat": [digit, count]
        if "text_repeat" in v:
            v["text"] = v["text_repeat"][0] * v["text_repeat"][1]
    accepted = refused = 0
    for v in sec["vectors"]:
        probe, exp = _AuthorityProbe(), v["expected"]
        if exp["result"] == "refuse":
            with pytest.raises(Refuse) as info:
                ingest_snapshot_version(v["representation"], v["text"], probe)
            assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), v["id"]
            assert (probe.authority_calls, probe.projection_calls) == (0, 0), v["id"]  # the unsupported representation never reached authority evaluation
            assert exp["authority_evaluation_reached"] is False and exp["projection_reached"] is False and exp["binding_created"] is False
            assert exp["yields_overlay_not_applied"] is False and exp["yields_accept"] is False
            refused += 1
        else:
            assert ingest_snapshot_version(v["representation"], v["text"], probe) == int(v["text"]) and (probe.authority_calls, probe.projection_calls) == (1, 1), v["id"]
            accepted += 1
    assert accepted == 3 and refused == 10
    import sys
    for limit in (640, 4300, 0):  # the interpreter's integer-string limit must not change any ingest decision
        old = sys.get_int_max_str_digits()
        sys.set_int_max_str_digits(limit)
        try:
            for v in sec["vectors"]:
                if v["expected"]["result"] == "refuse":
                    with pytest.raises(Refuse):
                        ingest_snapshot_version(v["representation"], v["text"], _AuthorityProbe())
        finally:
            sys.set_int_max_str_digits(old)
    # the strict JSON loader agrees on the textual forms that parse as something other than a strict integer (no coercion: none becomes an int)
    for text, kind in (("7.0", "float"), ("7e0", "float"), ('"7"', "string"), ("true", "bool"), ("null", "null")):
        try:
            parsed = load(text)
        except Refuse:
            continue
        assert not (isinstance(parsed, int) and not isinstance(parsed, bool)), (text, kind)
    # the projection stage stays a second line of defence for a non-conforming ingest (the bound is the same), and the order is fixed in the spec
    assert project_snapshot_version(2**53 - 1) == 2**53 - 1
    with pytest.raises(Refuse):
        project_snapshot_version(2**53)
    spec = (ROOT / V["spec"]).read_text(encoding="utf-8")
    assert "RULED (Architect final ruling, N-10(c))" in spec and "never reaches authority evaluation" in spec


def test_policy_identity_members_and_the_conformance_kit_agree_on_overlapping_cases_ruling_4_3():
    sec = V["policy_identity_members"]
    members = {m["member"]: m for m in sec["members"]}
    assert set(members) == {"scope_key", "selection_id", "selection_epoch", "selection_digest", "record", "activation_ref"}
    row = next(r for r in V["defect_mapping"] if r["id"] == "MP-policy_identity_mismatch")
    assert row["member_set"] == ["scope_key", "selection_id", "selection_epoch", "selection_digest", "record", "activation_ref"]
    assert row["stale_epoch_routes_to"] == "selection_epoch_stale" and {"selection_epoch", "high_water_epoch"} <= set(row["evidence_fields"])
    assert set(row["member_values"]) >= {"record_id", "record_version", "record_digest"}
    # every record member and the epoch are binding members of the declared profile; nothing is manufactured
    declared = set(V["profile"]["members"])
    for m in sec["members"]:
        assert set(m["binding_members"]) <= declared, m["member"]
    assert sec["binding_profile"] == PROFILE and sec["kit_code_changed"] is False
    assert (V["defect_mapping"][[r["id"] for r in V["defect_mapping"]].index("MP-selection_epoch_stale")]["verdict_class"]) == "REFUSE_STALE"
    # the kit's guard (read as SOURCE TEXT, never imported) has the same stale-before-mismatch order and compares exactly the kit-level members
    src = (ROOT / "registry_conformance" / "highwater.py").read_text(encoding="utf-8")
    stale = src.index('if b["selection_epoch"] < row["epoch"]:')
    stale_ret = src.index('"selection_epoch_stale"', stale)
    mismatch = src.index('"policy_identity_mismatch"', stale_ret)
    assert stale < stale_ret < mismatch
    block = src[stale:mismatch]
    for needle in ('b["selection_epoch"] != row["epoch"]', 'b["selection_digest"] != row["selection_digest"]', 'b["record"] != row["record"]', 'b["activation_ref"] != row["activation_ref"]'):
        assert needle in block, needle
    assert "REFUSE_STALE" in src[stale:stale_ret + 60] and 'REFUSE, "policy_identity_mismatch"' in src[stale_ret:mismatch + 60]
    # the kit selects the row by its scope key (selection_id included); a miss is not_activated, a same-chain other selection_id is selection_conflict
    assert 'row = st["rows"].get(key)' in src and '_verdict(REFUSE, "not_activated")' in src and '_verdict(REFUSE, "selection_conflict")' in src
    # kit vector GD-02 pins the overlapping cases: stale -> REFUSE_STALE; higher epoch, wrong digest, reused activation_ref -> identity mismatch
    gd = json.loads((ROOT / "registry_conformance" / "vectors" / "08_guard_and_optional_fallback.json").read_text(encoding="utf-8"))
    gd02 = json.dumps(next(v for v in gd["vectors"] if v["id"].startswith("GD-02")))
    assert "selection_epoch_stale" in gd02 and "policy_identity_mismatch" in gd02 and "REFUSE_STALE" in gd02


def test_n10_input_contract_requirements_are_each_backed_by_existing_vectors():
    sec = V["n10_input_contract"]
    assert "Architect Batch 6 rulings, N-10" in sec["rule"]
    assert set(sec["requirements"]) == {"deterministic_byte_level_parsing", "duplicate_member_rejection", "ambiguous_key_rejection", "strict_numeric_parsing",
                                        "bounded_input_size", "canonical_serialization", "no_coercion_of_malformed_values"}
    known = {x["id"] for sec_name in ("valid", "invalid", "input_boundary") for x in V[sec_name]}
    for name, vids in sec["requirements"].items():
        assert vids and set(vids) <= known, (name, sorted(set(vids) - known))
    sv = sec["snapshot_version"]
    assert (sv["min"], sv["max"]) == RANGES["trust_snapshot_version"] == (1, 2**53 - 1) and sv["not_an_operational_freshness_bound"] is True
    by_id = {x["id"]: x for x in V["invalid"]}
    assert set(sv["vectors"]) <= set(by_id) and len(sv["vectors"]) >= 9
    for vid in sv["vectors"]:
        exp = by_id[vid]["expected"]
        with pytest.raises(Refuse) as info:
            validate_binding(load(by_id[vid]["input_json"]))
        assert (info.value.code, info.value.member) == (exp["code"], exp["member"]), vid
    # the boundary values themselves are valid and canonical (the strict range is inclusive on both ends)
    assert any(v["id"].startswith("BV-") for v in V["valid"])


def test_spec_records_the_batch6_rulings_and_keeps_open_items_open():
    spec = (ROOT / V["spec"]).read_text(encoding="utf-8")
    assert "Architect Batch 6 rulings" in spec and TOKEN_TABLE_SHA256 in spec and "ocs-evidence-stage/1" in spec
    closed = spec[spec.index("### Closed by Batch-6 ruling"):spec.index("### Routed")]
    for item in ("N-10", "N-11", "N-12", "N-13", "Ruling 4.3"):
        assert item in closed and "RULED" in closed[closed.index(item):closed.index(item) + 400], item
    remaining = spec[spec.index("### Remaining (genuine)"):spec.index("### Recorded notes")]
    for item in ("N-10(c)", "N-12(c)", "N-13(b)"):  # the former open parts are RULED (Architect final rulings) and no longer listed as open
        assert item not in remaining, item
        assert item in closed and "RULED" in closed[closed.index(item):closed.index(item) + 300], item
    for item in ("N-7", "N-8", "N-9"):  # no canonical source in the repository rules on these: explicitly UNRESOLVED, never silently resolved
        assert item in remaining and "UNRESOLVED" in remaining[remaining.index(item):remaining.index(item) + 400], item
    assert not any(w in remaining[remaining.index("N-7"):] for w in ("RULED", "CLOSED", "resolved by"))
    for retired in ("- **N-11 `trust_snapshot_missing` dual meaning (new", "- **N-12 Optional scopes under an unknown store, and a refused projection read as never activated (new"):
        assert retired not in spec, retired  # the open-question entries are replaced by the ruled entries
    assert "Whether a refused projection may count as `never_activated` is not decided" not in spec
    # the table counts the spec states are the data counts
    assert "| `token_unicode` | %d |" % len(V["token_unicode"]["vectors"]) in spec
    assert "| `optional_fallback_determination` | %d |" % len(V["optional_fallback_determination"]["vectors"]) in spec
    assert "| `invalid` | %d |" % len(V["invalid"]) in spec
    assert "713 ascending" in spec and len(_TOKEN_RANGES) == 713
    # the kit and every frozen pin are untouched by this change: the verdict section pin is still enforced elsewhere in this file
    assert "readme:## Verdicts (ruling R1)" in V["pins"]["enforced_section_hashes"]


def test_ingest_refusal_evidence_carries_the_member_n10c():
    """N-10(c): the ingest refusal names its member, so the mapping row must carry `member` in its evidence fields (spec 8.1 and the JSON row agree)."""
    row = next(r for r in V["defect_mapping"] if r["id"] == "MP-trust_snapshot_invalid")
    assert "member" in row["evidence_fields"] and "trust_snapshot_version" in row["evidence_fields"]
    spec_row = next(l for l in (ROOT / V["spec"]).read_text(encoding="utf-8").splitlines() if l.startswith("| MP-trust_snapshot_invalid |"))
    assert "`trust_snapshot_version`, `member`" in spec_row
    assert V["snapshot_version_ingest_bound"]["member"] == "trust_snapshot_version"
