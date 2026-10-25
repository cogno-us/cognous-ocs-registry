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
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "docs" / "ext-implementation" / "data" / "ext-s1-5-policy-identity-vectors.json"
V = json.loads(VECTORS.read_text(encoding="ascii"))

DOMAIN_PREFIX = b"ocs-reg/r08-v2/policy-binding\n"
PROFILE = "ocs-policy-binding/1"
INT_MAX = 2**31 - 1  # INTERIM (spec open question OQ-1): equals registry common.MAX_INT
MAX_DOCUMENT_BYTES = 65536
MAX_DEPTH = 8

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
            if not 1 <= val <= INT_MAX:
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


def test_effective_payload_digests():
    for ep in V["effective_payloads"]:
        c = canon(ep["payload"])
        assert c.hex() == ep["expected"]["canonical_bytes_hex"], ep["id"]
        assert c.decode("ascii") == ep["expected"]["canonical_ascii"]
        assert plain_digest(ep["payload"]) == ep["expected"]["effective_policy_digest"], ep["id"]
        # the payload carries exactly the family payload keys and no registry bookkeeping
        keys = set(ep["payload"])
        fam = ep["family"]
        if fam == "f1ab-local-execution-allowlist":
            assert keys == {"allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains"}
            for lst in ep["payload"].values():
                assert lst == sorted(lst) and len(lst) == len(set(lst))
        elif fam == "f4-control-plane-age-bounds":
            assert keys == {"status_max_age_seconds", "approval_max_age_seconds"}
        elif fam == "f5-action-class-age-bounds":
            assert keys == {"class_status_max_age_seconds"}
        else:
            raise AssertionError(fam)
        if "equivalent_to" in ep:
            ref = next(x for x in V["effective_payloads"] if x["id"] == ep["equivalent_to"])
            assert ref["expected"] == ep["expected"]
    digests = [e["expected"]["effective_policy_digest"] for e in V["effective_payloads"] if "equivalent_to" not in e]
    assert len(digests) == len(set(digests))
    # changing any single set element changes the effective digest
    p = json.loads(json.dumps(V["effective_payloads"][0]["payload"]))
    base = plain_digest(p)
    for k in list(p):
        q = json.loads(json.dumps(p))
        q[k] = q[k] + ["extra-zz"]
        assert plain_digest(q) != base


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
    texts = {"contract": (ROOT / pins["contract_file"]).read_text(encoding="utf-8"), "adr": (ROOT / pins["adr_file"]).read_text(encoding="utf-8")}
    assert len(pins["enforced_section_hashes"]) >= 8
    for name, pin in pins["enforced_section_hashes"].items():
        which = name.split(":", 1)[0]
        section = _section(texts[which], pin["start"], pin["end_regex"])
        got = hashlib.sha256(section.rstrip().encode("utf-8")).hexdigest()
        assert got == pin["sha256"], "pinned section changed: %s (re-review docs/ext-implementation/ext-s1-5-*.md and the vectors)" % name
    # anchors the spec quotes verbatim
    c = texts["contract"]
    for anchor in ("## 4. Canonical policy binding (D-14, D-15)", "### 4.1 Serialization and digest", "### 4.2 Two states of the object",
                   "ocs-reg/r08-v2/policy-binding\\n", r"`\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z`", "`sha256:[0-9a-f]{64}`"):
        assert anchor in c, anchor


def test_spec_document_exists_and_references_the_pins():
    spec = (ROOT / V["spec"]).read_text(encoding="utf-8")
    for heading in ("Consumers and handoff", "Open questions for Architect"):
        assert heading in spec
    assert V["pins"]["contract_file_sha256_informational"] in spec
    for name in V["pins"]["enforced_section_hashes"]:
        assert V["pins"]["enforced_section_hashes"][name]["sha256"] in spec, name
    assert V["pins"]["outcome_map_sha256"] in spec
    for member in V["profile"]["members"]:
        assert "`%s`" % member in spec, member


_JS = r"""
const fs = require('fs');
const V = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const crypto = require('crypto');
function ss(s){let o='"';for(const ch of s){const c=ch.codePointAt(0);
 if(c===0x22)o+='\\"';else if(c===0x5c)o+='\\\\';else if(c===8)o+='\\b';else if(c===12)o+='\\f';else if(c===10)o+='\\n';
 else if(c===13)o+='\\r';else if(c===9)o+='\\t';else if(c<0x20||c===0x7f)o+='\\u'+c.toString(16).padStart(4,'0');
 else if(c<0x80)o+=ch;else if(c<0x10000)o+='\\u'+c.toString(16).padStart(4,'0');
 else{const d=c-0x10000;o+='\\u'+(0xd800+(d>>10)).toString(16)+'\\u'+(0xdc00+(d&0x3ff)).toString(16);}}return o+'"';}
function ser(v){if(v===null)return 'null';if(typeof v==='number')return String(v);if(typeof v==='string')return ss(v);
 if(Array.isArray(v))return '['+v.map(ser).join(',')+']';
 return '{'+Object.keys(v).sort().map(k=>ss(k)+':'+ser(v[k])).join(',')+'}';}
const pre=Buffer.from(V.profile.domain_prefix_hex,'hex');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const out={};
for(const x of V.valid){const c=Buffer.from(ser(JSON.parse(x.input_json)),'ascii');
 out[x.id]=[c.toString('hex'),'sha256:'+sha(Buffer.concat([pre,c]))];}
for(const x of V.effective_payloads){const c=Buffer.from(ser(x.payload),'ascii');out[x.id]=[c.toString('hex'),'sha256:'+sha(c)];}
for(const x of V.trust_snapshots){const c=Buffer.from(ser(x.expected_normalized||JSON.parse(x.normalized_json)),'ascii');out[x.id]=[c.toString('hex'),'sha256:'+sha(c)];}
console.log(JSON.stringify(out));
"""


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed; non-Python cross-check is optional in this environment")
def test_non_python_reference_agrees_byte_for_byte(tmp_path):
    """One non-Python implementation (Node.js, written inline) recomputes every valid binding, effective payload and snapshot."""
    data = json.loads(VECTORS.read_text(encoding="ascii"))
    for t in data["trust_snapshots"]:
        t["normalized_json"] = json.dumps(normalize_snapshot(t["input"]))
    p = tmp_path / "v.json"
    p.write_text(json.dumps(data), encoding="ascii")
    js = tmp_path / "ref.js"
    js.write_text(_JS, encoding="utf-8")
    res = subprocess.run(["node", str(js), str(p)], capture_output=True, text=True, timeout=60, check=True)
    got = json.loads(res.stdout)
    for vec in V["valid"]:
        assert got[vec["id"]] == [vec["expected"]["canonical_bytes_hex"], vec["expected"]["binding_digest"]], vec["id"]
    for ep in V["effective_payloads"]:
        assert got[ep["id"]] == [ep["expected"]["canonical_bytes_hex"], ep["expected"]["effective_policy_digest"]], ep["id"]
    for t in V["trust_snapshots"]:
        assert got[t["id"]] == [t["expected"]["canonical_bytes_hex"], t["expected"]["trust_snapshot_fingerprint"]], t["id"]
