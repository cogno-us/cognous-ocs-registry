"""EXT-S1-5 contract preparation: validate the policy-identity golden vectors against an INDEPENDENT reference serializer.

Scope: documentation-and-data tooling only. This file imports nothing from registry_successor, registry_consumer,
registry_records, registry_contract, registry_adapters or registry_conformance. Everything it needs (a hand-written canonical JSON
serializer, a strict validator for the binding, the digest construction and the trust-snapshot normalizer) is implemented
below from docs/ext-implementation/ext-s1-5-effective-policy-identity-spec.md and docs/r08-v2-contract.md section 4.1 and 5.
It is NOT a shared module and must not be imported by source code. It qualifies nothing (vectors are BUILDER_TESTED).

The serializer is deliberately NOT json.dumps: it writes the canonical text by hand, and a second check compares it with
json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True), which is what registry_successor/common.py does.
"""
import hashlib
import json
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


class _Dup(Exception):
    pass


class _Num(Exception):
    pass


def _pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise _Dup(k)
        out[k] = v
    return out


def _reject(_x):
    raise _Num(_x)


def _depth(value):
    stack = [(value, 1)]
    while stack:
        node, d = stack.pop()
        if d > MAX_DEPTH:
            return False
        if isinstance(node, dict):
            stack.extend((c, d + 1) for c in node.values())
        elif isinstance(node, list):
            stack.extend((c, d + 1) for c in node)
    return True


def load(raw):
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise Refuse("input_not_text")
    else:
        text = raw
    if len(text.encode("utf-8", "surrogatepass")) > MAX_DOCUMENT_BYTES:
        raise Refuse("input_too_large")
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_float=_reject, parse_constant=_reject)
    except _Dup:
        raise Refuse("json_duplicate_key")
    except _Num:
        raise Refuse("json_number_unsupported")
    except RecursionError:
        raise Refuse("json_nesting_too_deep")
    except ValueError:
        raise Refuse("json_malformed")
    if not _depth(value):
        raise Refuse("json_nesting_too_deep")
    return value


IDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")  # used with fullmatch (== \A...\Z); classes are explicit ASCII ranges
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
ID_MEMBERS = ("record_id", "selection_id", "family", "consumer_id", "operation", "scope.tenant", "scope.institution", "scope.authority_domain")
DIGEST_MEMBERS = ("record_digest", "selection_digest", "effective_policy_digest", "activation_ref", "trust_snapshot_fingerprint")
INT_MEMBERS = ("record_version", "selection_epoch", "trust_snapshot_version")
SCOPE_KEYS = ("authority_domain", "institution", "tenant")
TOP_KEYS = ("activation_ref", "binding_profile", "consumer_id", "effective_policy_digest", "family", "operation", "record_digest", "record_id",
            "record_version", "scope", "selection_digest", "selection_epoch", "selection_id", "trust_snapshot_fingerprint", "trust_snapshot_version")


def _flatten(doc):
    flat = {}
    for k, v in doc.items():
        if k == "scope" and isinstance(v, dict):
            for sk, sv in v.items():
                flat["scope." + sk] = sv
        else:
            flat[k] = v
    return flat


def validate_binding(doc):
    """Returns the doc if it is a well formed COMPLETED binding; raises Refuse(code, member) otherwise."""
    if not isinstance(doc, dict):
        raise Refuse("field_type_invalid")
    expected = set(TOP_KEYS) - {"scope"}
    expected |= ({"scope." + k for k in SCOPE_KEYS} if "scope" in doc else {"scope"})
    flat = _flatten(doc)
    if "scope" in doc and not isinstance(doc["scope"], dict):
        raise Refuse("field_type_invalid", "scope")
    # phase 1: missing, phase 2: unknown (sorted path order); an absent scope is the single missing member `scope`
    missing = sorted(expected - set(flat))
    if missing:
        raise Refuse("field_missing", missing[0])
    unknown = sorted(set(flat) - expected)
    if unknown:
        raise Refuse("field_unknown", unknown[0])
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
    """Ruling N-5 reference rules for a scope whose projection was refused (binding creation is refused for EVERY participation).
    The projection refusal is never an authorization: no branch yields overlay_not_applied or an ACCEPT by itself."""
    if participation == "required":
        out = "UNKNOWN_FAIL_CLOSED" if activation_state == "indeterminate" else "REFUSE"
        return {"effect_outcome": out, "decision_kind": "required_policy_unavailable", "fallback_permitted": False, "fallback_evidence": None}
    assert participation == "optional"
    if activation_state == "indeterminate":
        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None, "fallback_permitted": False, "fallback_evidence": None}
    if determination == "authenticated" and activation_state == "permits_optional":
        return {"effect_outcome": "optional_fallback_via_determination", "decision_kind": None, "fallback_permitted": True,
                "fallback_evidence": {"kind": "absence_or_withdrawal", "projection_refusal_code": "field_invalid"}}
    return {"effect_outcome": "REFUSE", "decision_kind": None, "fallback_permitted": False, "fallback_evidence": None}


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


REGISTERED_CONTRACT_VERSIONS = {  # contract section 2 table is registered for contract_version r08-v2 only
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
            if len(v) > 256 or not all(statement_valid_token(x) for x in v) or v != sorted(set(v)):
                raise Refuse("field_invalid", path)
        elif not lo <= v <= hi:
            raise Refuse("field_invalid", path)
    if fam["kind"] == "classmap":
        m = payload["class_status_max_age_seconds"]
        if not m or not all(statement_valid_token(c) for c in m):
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
    if doc["contract_version"] != CONTRACT_VERSION:
        raise Refuse("field_invalid", "contract_version")
    validate_effective_payload(doc["family"], doc["effective"])
    if doc["family_version"] != registered_family_version(doc["family"], doc["contract_version"]):  # compared with the registered tag, never trusted
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
        assert exp["layer"] == codes[exp["code"]] or vec["expected"].get("code_status") == "PROPOSED_FROM_EXISTING_CODES", vec["id"]
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
        assert c["registrable"] is False
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
    for ceiling in ("MAX_INT", "MAX_VERSION", "2**31", "2**53", "2147483647", "9007199254740991"):
        assert ceiling not in body, ("a snapshot-version ceiling appeared in the verifier: re-derive the bound", ceiling)
    scanned = [p for pkg in ("registry_successor", "registry_consumer") for p in sorted((ROOT / pkg).glob("*.py"))] + [ROOT / "registry_conformance" / "highwater.py"]
    users = set()
    for path in scanned:
        for line in path.read_text(encoding="utf-8").splitlines():
            if "snapshot" in line.lower() and any(t in line for t in ("MAX_INT", "MAX_VERSION", "2**31", "2**53", "2147483647")):
                pytest.fail("snapshot line with a ceiling in %s: %s" % (path.name, line))
            if "MAX_INT" in line or "MAX_VERSION" in line:
                users.add(path.name)
    assert users <= {"common.py", "record.py", "selection.py", "consumer.py"}, users
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
        if code is None:  # deny-all and evaluator denial are not Registry refusals and carry no Registry verdict class
            assert cls is None and r["decision_kind"] in ("applied_deny_all", "evaluator_denied"), r["id"]
            continue
        assert cls in VERDICT_CLASSES, r["id"]
        assert "proposed_additive_code" not in r, r["id"]
        if r.get("ruled_additive_code"):
            assert code in proposed and proposed[code]["verdict_class"] == cls, r["id"]
        else:
            assert code in codes, ("no existing CODES_V2 entry named", r["id"], code)
        by_code.setdefault(code, set()).add(cls)
    # the proposal list is exactly the proposed codes that rows use
    assert set(proposed) == {r["registry_code"] for r in V["defect_mapping"] if r.get("ruled_additive_code")}
    # a cause code names one class (the single documented dual-class code is trust_snapshot_expired, mapped here only in its guard form)
    assert all(len(v) == 1 for v in by_code.values()), {k: v for k, v in by_code.items() if len(v) > 1}
    stale = {c for c, v in by_code.items() if v == {"REFUSE_STALE"}}
    assert stale == {"selection_epoch_stale", "trust_snapshot_version_stale"}
    terminal = {"selection_revoked", "selection_withdrawn", "issuer_key_revoked"}
    assert all(by_code[c] == {"REFUSE"} for c in terminal)  # terminal revocation and withdrawal are never stale and never HOLD
    hold = {c for c, v in by_code.items() if v == {"UNKNOWN_FAIL_CLOSED"}}
    assert hold == {"trust_snapshot_missing", "trust_snapshot_expired", "store_unknown"}
    assert hold.isdisjoint(terminal | stale)
    retry = {r["registry_code"]: r["retry"] for r in V["defect_mapping"] if r["registry_code"]}
    assert all(retry[c] == "after_authoritative_state_available" for c in hold) and all(retry[c] != "after_authoritative_state_available" for c in terminal | stale)
    # the original Registry cause is always preserved as structured evidence and distinct causes keep distinct rows
    assert len([r for r in V["defect_mapping"] if r["registry_code"]]) == len({(r["registry_code"], r["id"]) for r in V["defect_mapping"] if r["registry_code"]})
    for c in ("selection_withdrawn", "selection_revoked", "selection_epoch_stale", "trust_snapshot_version_stale", "issuer_key_revoked", "store_unknown"):
        assert c in by_code
    kinds = {r["decision_kind"] for r in V["defect_mapping"]}
    assert {"applied_deny_all", "evaluator_denied"} <= kinds
    # every code used by an identity validator in this file appears in the mapping
    mapped = set(by_code)
    for c in V["outcome_map"]["codes_used_by_this_file"]:
        assert c in mapped or c == "trust_snapshot_invalid", c
    # the vocabulary matches the merged conformance kit when that README is present in this checkout (branch predates PR #28)
    # the vocabulary is the one in the merged conformance README, whose verdict section is an ENFORCED pin (test_contract_section_pins; ruling N-6)
    readme = ROOT / "docs" / "conformance" / "README.md"
    assert readme.exists(), "docs/conformance/README.md (PR #28) must be present: the four-verdict vocabulary is pinned"
    text = readme.read_text(encoding="utf-8")
    for v in VERDICT_CLASSES:
        assert "`%s`" % v in text, v


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
  : st === 'indeterminate' ? 'UNKNOWN_FAIL_CLOSED' : (det === 'authenticated' && st === 'permits_optional') ? 'optional_fallback_via_determination' : 'REFUSE';
for (const x of V.scope_projection_effects) out[x.id] = PE(x.participation, x.activation_state, x.optional_determination);
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
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed; non-Python cross-check is optional in this environment")
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
    res = subprocess.run(["node", str(js), str(p)], capture_output=True, text=True, timeout=60, check=True)
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
    assert n >= 80
