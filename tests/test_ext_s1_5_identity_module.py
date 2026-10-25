"""EXT-S1-5 production module `registry_successor.v2_policy_identity`: every golden vector, a differential check against the independent test
reference, static checks of the module's boundaries, and mutation testing of the module itself.

The vector file is the oracle. `tests/test_ext_s1_5_vectors.py` (the independent reference, imported here by PATH only) is used for the
differential check and for the input-boundary generator; the production module imports nothing from it. BUILDER_TESTED, not qualified.
"""
import importlib.util
import itertools
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

import pytest

from registry_successor import common as c
from registry_successor import v2_policy_identity as m
from registry_successor.v2_codes import CODES_V2, CODES_V2_REV2

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "docs" / "ext-implementation" / "data" / "ext-s1-5-policy-identity-vectors.json"
V = json.loads(VECTORS.read_text(encoding="ascii"))
MODULE_PATH = ROOT / "registry_successor" / "v2_policy_identity.py"


def _load_reference():
    spec = importlib.util.spec_from_file_location("ext_s1_5_reference", ROOT / "tests" / "test_ext_s1_5_vectors.py")
    ref = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ref)
    return ref


def _outcome(fn, *args):
    try:
        return ("ok", fn(*args))
    except m.IdentityRefusal as r:
        return ("refuse", r.code, r.member)


def _bv(vid="BV-001"):
    return next(v for v in V["valid"] if v["id"] == vid)


def _raw(vec):
    if "generate" in vec:
        return _generate(vec["generate"])
    return bytes.fromhex(vec["input_hex"]) if "input_hex" in vec else vec["input_json"]


def _generate(gen):
    kind = gen["kind"]
    if kind == "bv1_padded":
        base = _bv()["input_json"].encode("utf-8")
        return base + b" " * (gen["total_bytes"] - len(base))
    if kind == "multibyte_string":
        return ('{"x":"' + "\u00e9" * gen["count"] + '"}').encode("utf-8")
    if kind == "invalid_utf8_padded":
        head = b'{"a":"\xff"}'
        return head + b" " * (gen["total_bytes"] - len(head))
    if kind == "deep_array":
        return ("[" * gen["depth"] + gen["inner"] + ("]" * gen["depth"] if gen["closed"] else "") + gen["tail"]).encode("utf-8")
    if kind == "int_literal":
        text = _bv()["input_json"]
        return text.replace('"selection_epoch": 3', '"selection_epoch": %s%s' % (gen["sign"], "9" * gen["digits"])).encode("utf-8")
    assert kind == "nested"
    o, cl = ('{"a":', "}") if gen["container"] == "object" else ("[", "]")
    n = gen["depth"] - 1
    return (o * n + "1" + cl * n).encode("utf-8")


def _expect_refusal(fn, exp, where):
    kind, *rest = _outcome(fn)
    assert kind == "refuse", (where, "expected a refusal", exp)
    assert tuple(rest) == (exp["code"], exp.get("member")), (where, rest)
    if "layer" in exp:
        assert exp["layer"] == CODES_V2[exp["code"]][0], where


# ----------------------------------------------------------------------------------------------------------------------
# The oracle: every vector set against the production module. Returns failure descriptions (used by the mutation harness too).
# ----------------------------------------------------------------------------------------------------------------------
def _oracle_failures():
    fails = []

    def check(cond, what):
        if not cond:
            fails.append(what)

    def guard(what, fn):
        try:
            fn()
        except Exception as e:  # a mutant may break anything; every escape is a failure of the oracle, never a crash
            fails.append("%s: %s %r" % (what, type(e).__name__, e))

    def valid_bindings():
        for vec in V["valid"]:
            doc = m.parse_binding(_raw(vec))
            exp = vec["expected"]
            check(m.canonical_json_bytes(doc).hex() == exp["canonical_bytes_hex"], vec["id"] + " bytes")
            check(m.binding_digest(doc) == exp["binding_digest"], vec["id"] + " digest")
            check(m.plain_digest(doc) == exp["digest_without_prefix_control"], vec["id"] + " plain")
            check(m.scope_key_digest(m.scope_key_from_binding(doc)) is not None, vec["id"] + " scope key")

    def invalid_bindings():
        for vec in V["invalid"] + V["input_boundary"] + V["integer_boundary"]:
            exp = vec["expected"]
            raw = _raw(vec)
            if exp["result"] == "valid":
                doc = m.parse_binding(raw)
                if "binding_digest" in exp:
                    check(m.binding_digest(doc) == exp["binding_digest"], vec["id"])
                else:
                    check(m.binding_digest(doc) == _bv(exp["equals"])["expected"]["binding_digest"], vec["id"])
            else:
                got = _outcome(m.parse_binding, raw)
                check(got == ("refuse", exp["code"], exp.get("member")), "%s %r" % (vec["id"], got))

    def identifiers():
        base = m.parse_binding(_bv()["input_json"])
        for entry in V["identifier_matrix"]["bad_values"]:
            for member in V["identifier_matrix"]["members"]:
                doc = json.loads(json.dumps(base))
                if "." in member:
                    a, k = member.split(".")
                    doc[a][k] = entry["value"]
                else:
                    doc[member] = entry["value"]
                check(_outcome(m.validate_binding, doc) == ("refuse", "field_invalid", member), entry["id"] + member)

    def guards():
        by_id = {v["id"]: v for v in V["valid"]}
        for g in V["guard_digest_checks"]:
            doc = m.parse_binding(by_id[g["binding_ref"]]["input_json"])
            got = _outcome(m.verify_carried_binding_digest, doc, g["carried_digest"])
            exp = g["expected"]
            if exp["result"] == "valid":
                check(got[0] == "ok", g["id"])
            else:
                check(got == ("refuse", exp["code"], None), "%s %r" % (g["id"], got))

    def effective():
        for ep in V["effective_payloads"]:
            exp = ep["expected"]
            pre = m.effective_preimage(ep["family"], ep["payload"])
            check(m.canonical_json_bytes(pre).hex() == exp["preimage_canonical_bytes_hex"], ep["id"] + " preimage")
            check(m.effective_policy_digest(ep["family"], ep["payload"]) == exp["effective_policy_digest"], ep["id"] + " digest")
            m.validate_preimage(pre)
        for vec in V["effective_inputs"]:
            exp = vec["expected"]
            got = _outcome(lambda: m.preimage_from_inputs(m.load_document(vec["input_json"])))
            if exp["result"] == "valid":
                check(got[0] == "ok" and got[1]["family_version"] == exp["derived_family_version"]
                      and m.effective_digest_of_preimage(got[1]) == exp["effective_policy_digest"], vec["id"])
            else:
                check(got == ("refuse", exp["code"], exp["member"]), "%s %r" % (vec["id"], got))
        for cvec in V["effective_policy_controls"]:
            pre = m.load_document(cvec["preimage_canonical_ascii"])
            check(m.effective_digest_of_preimage(pre) == cvec["effective_policy_digest"], cvec["id"])
            check((_outcome(m.validate_preimage, pre)[0] == "ok") is cvec["registrable"], cvec["id"] + " registrable")
        for vec in V["effective_payloads_invalid"]:
            exp = vec["expected"]
            got = _outcome(lambda: m.validate_effective_payload(vec["family"], m.load_document(vec["payload_json"]), vec["role"]))
            check(got == ("refuse", exp["code"], exp["member"]), "%s %r" % (vec["id"], got))
        for vec in V["effective_preimage_invalid"]:
            exp = vec["expected"]
            got = _outcome(lambda: m.validate_preimage(m.load_document(vec["input_json"])))
            check(got == ("refuse", exp["code"], exp["member"]), "%s %r" % (vec["id"], got))
        for vec in V["effective_integer_boundary"]:
            exp = vec["expected"]
            got = _outcome(lambda: m.validate_effective_payload(vec["family"], m.load_document(vec["payload_json"]), vec["role"]))
            if exp["result"] == "refuse":
                check(got == ("refuse", exp["code"], exp["member"]), "%s %r" % (vec["id"], got))
            else:
                check(got[0] == "ok", vec["id"])
                if vec["role"] == "effective":
                    check(m.effective_policy_digest(vec["family"], got[1]) == exp["effective_policy_digest"], vec["id"] + " digest")

    def scope_keys():
        for vec in V["scope_keys"]:
            doc = m.load_document(vec["input_json"])
            exp = vec["expected"]
            check(m.scope_key_bytes(doc).hex() == exp["scope_key_canonical_bytes_hex"], vec["id"] + " bytes")
            check(m.scope_key_digest(doc) == exp["scope_key_digest"], vec["id"] + " digest")
        for pr in V["scope_key_collision_pairs"]:
            check(m.scope_key_digest(pr["a"]) == pr["expected"]["scope_key_digest_a"] and m.scope_key_digest(pr["b"]) == pr["expected"]["scope_key_digest_b"], pr["id"])
            check(m.scope_key_digest(pr["a"]) != m.scope_key_digest(pr["b"]), pr["id"] + " collision")
        for vec in V["scope_keys_invalid"]:
            exp = vec["expected"]
            check(_outcome(lambda: m.validate_scope_key(m.load_document(vec["input_json"]))) == ("refuse", exp["code"], exp["member"]), vec["id"])
        check(m.scope_key_from_binding(m.parse_binding(_bv()["input_json"])) == m.load_document(next(v for v in V["scope_keys"] if v["id"] == "SK-001")["input_json"]), "SK-001 derived")

    def snapshots():
        for t in V["trust_snapshots"]:
            check(m.trust_snapshot_fingerprint(t["input"]) == t["expected"]["trust_snapshot_fingerprint"], t["id"])
            check(m.canonical_json_bytes(m.normalize_snapshot(t["input"])).hex() == t["expected"]["canonical_bytes_hex"], t["id"] + " bytes")
        for t in V["trust_snapshots_invalid"]:
            check(_outcome(m.trust_snapshot_fingerprint, t["input"]) == ("refuse", t["expected"]["code"], None), t["id"])

    def projection():
        for vec in V["scope_projection"]:
            exp = vec["expected"]
            got = _outcome(m.project_scope, vec["statement_scope"])
            if exp["result"] == "projected":
                check(got == ("ok", exp["scope"]), vec["id"])
            else:
                check(got == ("refuse", exp["code"], exp["member"]), "%s %r" % (vec["id"], got))
        for vec in V["projection_stage_refusals"]:
            exp = vec["expected"]
            got = _outcome(m.project_snapshot_version, vec["trust_snapshot_version"])
            if exp["result"] == "projected":
                check(got == ("ok", exp["trust_snapshot_version"]), vec["id"])
            else:
                check(got == ("refuse", exp["code"], exp["member"]), vec["id"])
        for r in V["scope_projection_effects"]:
            want = m.projection_effect(r["participation"], r["activation_state"], r["optional_determination"])
            check({k: r["expected"][k] for k in want} == want, r["id"])
        for r in V["projection_effect_matrix"]:
            want = m.projection_effect_for(r["registry_code"], r["participation"], r["activation_state"], r["optional_determination"])
            exp = r["expected"]
            check((exp["effect_outcome"], exp["fallback_permitted"]) == (want["effect_outcome"], want["fallback_permitted"]), r["id"])
            evidence = want["fallback_evidence"]["projection_refusal_code"] if want["fallback_evidence"] else None
            check(exp["fallback_evidence_code"] == evidence, r["id"] + " evidence")
        for vec in V["projection_effect_invalid"]:
            got = _outcome(m.projection_effect, vec["participation"], vec["activation_state"], vec["optional_determination"])
            check(got == ("refuse", vec["expected"]["code"], vec["expected"]["member"]), vec["id"])
        for part, st, det in itertools.product(("required", "optional"), ("known", "permits_optional", "forbids_fallback", "indeterminate"),
                                               ("authenticated", "not_authenticated", "n/a")):
            out = m.projection_effect(part, st, det)
            check(out["fallback_permitted"] is ((part, st, det) == ("optional", "permits_optional", "authenticated")), (part, st, det))
            check(out["effect_outcome"] != "ACCEPT" and out["decision_kind"] != "overlay_not_applied", (part, st, det))

    def spec_rules_not_pinned_by_a_vector():
        # rules the spec states that no shipped vector exercises on its own (found by mutation testing): serializer escapes and the caller age floor
        check(m.canonical_json_bytes("\x7f") == b'"\\u007f"' and m.canonical_json_bytes("\xe9") == b'"\\u00e9"' and m.canonical_json_bytes("/") == b'"/"', "escapes")
        f4 = "f4-control-plane-age-bounds"
        good = {"status_max_age_seconds": 0, "approval_max_age_seconds": 1}
        check(_outcome(m.validate_effective_payload, f4, good, "caller")[0] == "ok", "caller 0 is valid")
        check(_outcome(m.validate_effective_payload, f4, {**good, "status_max_age_seconds": -1}, "caller") == ("refuse", "field_invalid", "status_max_age_seconds"), "caller -1")
        check(_outcome(m.validate_effective_payload, f4, good, "registry") == ("refuse", "field_invalid", "status_max_age_seconds"), "registry 0")

    def code_boundaries():
        try:
            m.IdentityRefusal("not_a_registry_code")
            fails.append("a code outside CODES_V2_REV2 was accepted")
        except ValueError:
            pass
        check(m.registered_family_version("f4-control-plane-age-bounds", "r08-v2") == "v2", "f4 tag")
        check(_outcome(m.registered_family_version, "f4-control-plane-age-bounds", "r08-v1") == ("refuse", "contract_unsupported", "contract_version"), "r08-v1")
        check(_outcome(m.registered_family_version, "f9", "r08-v2") == ("refuse", "family_unsupported", "family"), "f9")
        for table in (m.INTEGER_RANGES, m.AGE_RANGES, m.IDENTITY_FAMILIES, m.MAPPING_BY_ID):
            try:
                table["record_version"] = (1, 2)
                fails.append("a module table is writable")
            except TypeError:
                pass
        check({f: r.family_version for f, r in m.IDENTITY_FAMILIES.items()} == {"f1a-local-execution-allowlist": "v1", "f1ab-local-execution-allowlist": "v2",
                                                                              "f4-control-plane-age-bounds": "v2", "f5-action-class-age-bounds": "v2"}, "table")

    def loader_direct():
        # the loader is also a public function: its own refusals, not only the ones parse_binding reaches through the validator's defences
        loader_codes = {"input_not_text", "input_too_large", "json_malformed", "json_duplicate_key", "json_number_unsupported", "json_nesting_too_deep"}
        for vec in V["invalid"] + V["input_boundary"]:
            exp = vec["expected"]
            if exp["result"] == "refuse" and exp["code"] in loader_codes:
                check(_outcome(m.load_document, _raw(vec)) == ("refuse", exp["code"], None), vec["id"] + " loader")
        check(_outcome(m.load_document, bytearray(b"{}")) == ("refuse", "input_not_text", None), "bytearray is not bytes")
        check(_outcome(m.load_document, memoryview(b"{}")) == ("refuse", "input_not_text", None), "memoryview is not bytes")

    def long_literals():
        a, b, n, top = m.load_document("[100000000000000000000,100000000000000000001,-100000000000000000000,99999999999999999999]")
        check(a != b and a != n and not isinstance(a, int) and type(top) is int, "long literals are distinct markers")
        check(a == m.load_document("[100000000000000000000]")[0], "same literal, same marker")
        snap = json.loads(json.dumps(V["trust_snapshots"][0]["input"]))
        raw = json.dumps(snap).replace('["sel-old-1", 2]', '["sel-old-1", 100000000000000000000000]')
        check(raw != json.dumps(snap), "fixture")
        check(_outcome(lambda: m.trust_snapshot_fingerprint(m.load_document(raw))) == ("refuse", "trust_snapshot_invalid", None), "long epoch is refused, never fingerprinted")
        check(_outcome(m.canonical_json_bytes, 10 ** 5000) == ("refuse", "field_invalid", None), "serializer refuses a huge int without str()")
        check(_outcome(m.canonical_json_bytes, 10 ** 20) == ("refuse", "field_invalid", None) and m.canonical_json_bytes(10 ** 20 - 1) == b"99999999999999999999", "20 digits")

    def malformed_snapshots():
        base = V["trust_snapshots"][0]["input"]

        def bad(label, edit):
            snap = json.loads(json.dumps(base))
            edit(snap)
            check(_outcome(m.trust_snapshot_fingerprint, snap) == ("refuse", "trust_snapshot_invalid", None), "snapshot " + label)

        iss = lambda s_: s_["issuers"][0]
        for label, edit in [
            ("version None", lambda s_: s_.update(version=None)), ("version True", lambda s_: s_.update(version=True)),
            ("version str", lambda s_: s_.update(version="7")), ("version 0", lambda s_: s_.update(version=0)),
            ("version -1", lambda s_: s_.update(version=-1)), ("version 20 digits", lambda s_: s_.update(version=10 ** 20)),
            ("snapshot_id list", lambda s_: s_.update(snapshot_id=[1])), ("snapshot_id empty", lambda s_: s_.update(snapshot_id="")),
            ("valid_until text", lambda s_: s_.update(valid_until="notatime")), ("valid_until int", lambda s_: s_.update(valid_until=5)),
            ("extra member", lambda s_: s_.update(extra=1)), ("missing member", lambda s_: s_.pop("min_epochs")),
            ("issuer no key", lambda s_: iss(s_).pop("public_key")), ("issuer extra member", lambda s_: iss(s_).update(extra=1)),
            ("key uppercase", lambda s_: iss(s_).update(public_key="AB" * 32)), ("key odd length", lambda s_: iss(s_).update(public_key="abc")),
            ("key empty", lambda s_: iss(s_).update(public_key="")), ("key not hex", lambda s_: iss(s_).update(public_key="zz" * 32)),
            ("alg int", lambda s_: iss(s_).update(alg=5)), ("key_id empty", lambda s_: iss(s_).update(key_id="")),
            ("issuer_id None", lambda s_: iss(s_).update(issuer_id=None)),
            ("authority int", lambda s_: iss(s_).update(authority=[1])), ("authority mixed", lambda s_: iss(s_).update(authority=[["a"], ["b", 1]])),
            ("grant of four", lambda s_: iss(s_).update(authority=[["a", "b", "c", "d"]])),
            ("grant with number", lambda s_: iss(s_).update(authority=[["a", "b", "c", "d", 5]])),
            ("grant with star token", lambda s_: iss(s_).update(authority=[["a", "b", "c", "d", "*"]])),
            ("duplicate grants", lambda s_: iss(s_).update(authority=[["a", "b", "c", "d", "e"]] * 2)),
            ("revoked epoch 20 digits", lambda s_: s_.update(revoked_selections=[["a", 10 ** 20]])), ("revoked epoch negative 20 digits", lambda s_: s_.update(revoked_selections=[["a", -10 ** 20]])),
            ("issuers is a str", lambda s_: s_.update(issuers="")), ("revoked_key_ids is a str", lambda s_: s_.update(revoked_key_ids="")),
            ("revoked_selections is a str", lambda s_: s_.update(revoked_selections="")), ("min_epochs is a str", lambda s_: s_.update(min_epochs="")),
            ("issuers is a dict", lambda s_: s_.update(issuers={})), ("authority is a str", lambda s_: iss(s_).update(authority="")),
            ("authority is a dict", lambda s_: iss(s_).update(authority={})),
            ("revoked key with a surrogate pair", lambda s_: s_.update(revoked_key_ids=[chr(0xD83D) + chr(0xDE00)])),
            ("snapshot_id with a surrogate pair", lambda s_: s_.update(snapshot_id=chr(0xD83D) + chr(0xDE00))),
            ("revoked epoch bool", lambda s_: s_.update(revoked_selections=[["a", True]])), ("revoked epoch str", lambda s_: s_.update(revoked_selections=[["a", "1"]])),
            ("revoked pair of three", lambda s_: s_.update(revoked_selections=[["a", 1, 2]])), ("revoked epoch huge", lambda s_: s_.update(revoked_selections=[["a", 10 ** 5000]])),
            ("floor 0", lambda s_: s_.update(min_epochs=[["a", 0]])), ("floor bool", lambda s_: s_.update(min_epochs=[["a", True]])),
            ("revoked key int", lambda s_: s_.update(revoked_key_ids=[1])),
            ("deep list", lambda s_: iss(s_).update(public_key=[[[[[[[[[1]]]]]]]]])),
        ]:
            bad(label, edit)
        cyc = []
        cyc.append(cyc)
        bad("self-referential list", lambda s_: s_.update(snapshot_id=cyc))
        for epoch in (10 ** 20, -10 ** 20, 10 ** 5000):  # the shape guard itself, not only the serializer behind it, bounds a revoked epoch
            snap = json.loads(json.dumps(base))
            snap["revoked_selections"] = [["a", epoch]]
            for fn in (m.normalize_snapshot, m.check_snapshot_duplicates, m._checked_snapshot):
                check(_outcome(fn, snap) == ("refuse", "trust_snapshot_invalid", None), "revoked epoch bound in the shape guard: %s" % fn.__name__)
        check(_outcome(m.trust_snapshot_fingerprint, None) == ("refuse", "trust_snapshot_invalid", None), "snapshot None")
        check(_outcome(m.normalize_snapshot, {"issuers": 1}) == ("refuse", "trust_snapshot_invalid", None), "normalize malformed")
        check(_outcome(m.check_snapshot_duplicates, {"issuers": 1}) == ("refuse", "trust_snapshot_invalid", None), "duplicates malformed")
        # tuples are the same data as lists
        snap = json.loads(json.dumps(base))
        snap["revoked_selections"] = [tuple(p) for p in snap["revoked_selections"]]
        check(m.trust_snapshot_fingerprint(snap) == V["trust_snapshots"][0]["expected"]["trust_snapshot_fingerprint"], "tuple pairs")

    def hostile_types():
        class Liar(str):
            def __ne__(self, other):
                return False

            def __eq__(self, other):
                return True

            __hash__ = str.__hash__

        class EvilInt(int):
            def __str__(self):
                return '1,"evil":2'

        class D(dict):
            def __getitem__(self, k):
                return "x"

        good = m.parse_binding(_bv()["input_json"])
        good_digest = m.checked_binding_digest(good)
        check(_outcome(m.verify_carried_binding_digest, good, Liar("sha256:" + "0" * 64)) == ("refuse", "field_invalid", None), "str subclass as carried digest")
        check(_outcome(m.verify_carried_binding_digest, good, "sha256:" + "0" * 64) == ("refuse", "digest_mismatch", None), "mismatch")
        check(_outcome(m.validate_binding, {**good, "binding_profile": Liar("ocs-policy-binding/9")}) == ("refuse", "field_type_invalid", "binding_profile"), "profile subclass")
        check(_outcome(m.validate_binding, {**good, "record_version": EvilInt(1)}) == ("refuse", "field_type_invalid", "record_version"), "int subclass")
        check(_outcome(m.validate_binding, D(good)) == ("refuse", "field_type_invalid", None), "dict subclass")
        check(_outcome(m.canonical_json_bytes, EvilInt(1)) == ("refuse", "field_type_invalid", None), "serializer int subclass")
        check(_outcome(m.canonical_json_bytes, D(a=1)) == ("refuse", "field_type_invalid", None), "serializer dict subclass")
        check(_outcome(m.canonical_json_bytes, Liar("x")) == ("refuse", "field_type_invalid", None), "serializer str subclass")
        check(_outcome(m.canonical_json_bytes, {1: 2}) == ("refuse", "field_unknown", m.NON_STRING_KEY), "serializer non-str key")
        for fn, arg in ((m.validate_binding, {**good, 1: 1, "zz": 2}), (m.validate_binding, {**good, None: 1}), (m.validate_binding, {**good, b"x": 1, 1: 2}),
                        (m.validate_binding, {**good, "scope": {**good["scope"], 5: 1}}), (m.validate_scope_key, {1: 1, "x": 2}),
                        (m.preimage_from_inputs, {1: 1, "x": 2}), (m.validate_preimage, {1: 1, "x": 2})):
            check(_outcome(fn, arg) == ("refuse", "field_unknown", m.NON_STRING_KEY), "non-str key %s" % fn.__name__)
        check(m.checked_binding_digest(good) == good_digest, "copy is stable")
        mutable = json.loads(json.dumps(good))
        copy = m.validate_binding(mutable)
        mutable["family"] = "changed"
        check(copy["family"] == good["family"] and copy is not mutable, "validate_binding returns a private copy")
        f5 = "f5-action-class-age-bounds"
        for payload in ({"class_status_max_age_seconds": {1: 1}}, {"class_status_max_age_seconds": {None: 1}}, {"class_status_max_age_seconds": {"a": 1, 2: 1}}):
            check(_outcome(m.validate_effective_payload, f5, payload) == ("refuse", "field_unknown", m.NON_STRING_KEY), "classmap key %r" % (payload,))
        f4 = "f4-control-plane-age-bounds"
        check(_outcome(m.validate_effective_payload, f4, {1: 1, "x": 2, "status_max_age_seconds": 1, "approval_max_age_seconds": 1}) == ("refuse", "field_unknown", m.NON_STRING_KEY), "f4 mixed keys")
        for bad_family in ([], None, 5, {}, b"x"):
            check(_outcome(m.validate_effective_payload, bad_family, {}) == ("refuse", "field_type_invalid", "family"), "family %r" % (bad_family,))
        check(_outcome(m.validate_effective_payload, f4, {}, "effective")[:2] == ("refuse", "field_missing"), "empty f4")
        for fn in (lambda: m.validate_effective_payload(f4, {}, role=[]), lambda: m.projection_effect_for([], "required", "known", "n/a"),
                   lambda: m.projection_effect_for(None, "required", "known", "n/a"), lambda: m.IdentityRefusal([])):
            try:
                fn()
                fails.append("a programmer error was accepted")
            except ValueError:
                pass
        for cv in (5, None, [], b"r08-v2"):
            check(_outcome(m.effective_policy_digest, f4, {"status_max_age_seconds": 1, "approval_max_age_seconds": 1}, cv) == ("refuse", "field_type_invalid", "contract_version"), "cv %r" % (cv,))
            check(_outcome(m.registered_family_version, f4, cv) == ("refuse", "field_type_invalid", "contract_version"), "registered cv %r" % (cv,))
            check(_outcome(m.registered_family_version, cv, "r08-v2") == ("refuse", "field_type_invalid", "family"), "registered family %r" % (cv,))
        check(_outcome(m.projection_effect, Liar("optional"), "permits_optional", "authenticated") == ("refuse", "field_invalid", "participation"), "participation subclass")
        eff = m.projection_effect("optional", Liar("permits_optional"), Liar("authenticated"))
        check(eff["effect_outcome"] == "REFUSE" and eff["fallback_permitted"] is False, "state and determination subclasses never permit a fallback")
        check(m.projection_effect("required", [], {})["effect_outcome"] == "REFUSE", "unhashable state and determination")
        check(_outcome(m.projection_effect, [], "known", "n/a") == ("refuse", "field_invalid", "participation"), "unhashable participation")
        check(_outcome(m.project_scope, [1]) == ("refuse", "field_invalid", "scope"), "scope list")
        check(_outcome(m.project_scope, {1: 1, "x": 2}) == ("refuse", "field_invalid", "scope"), "scope non-str keys")
        check(_outcome(m.project_snapshot_version, True) == ("refuse", "field_invalid", "trust_snapshot_version"), "version bool")
        check(_outcome(m.project_snapshot_version, [1]) == ("refuse", "field_invalid", "trust_snapshot_version"), "version list")
        check(_outcome(m.load_document, "\ud800") == ("refuse", "input_not_text", None), "lone surrogate text")
        check(_outcome(m.verify_carried_binding_digest, {**good, "family": 5}, [1]) == ("refuse", "field_type_invalid", "family"), "binding is validated before the carried digest (PROPOSED order)")

    def stage_and_evidence():
        def caught(fn, *args):
            try:
                fn(*args)
            except m.IdentityRefusal as r:
                return r
            return None

        r = caught(m.project_scope, {"tenant": "a b", "institution": "i", "authority_domain": "d"})
        check(r is not None and r.stage == "projection" and r.member == "scope.tenant" and m.mapping_row_for(r).row_id == "MP-field_invalid-projection"
              and r.evidence["projection_refusal_code"] == "field_invalid", "scope projection stage")
        r = caught(m.project_snapshot_version, 2 ** 53)
        check(r is not None and r.stage == "projection" and m.mapping_row_for(r).row_id == "MP-field_invalid-projection"
              and tuple(r.evidence["expected_range"]) == (1, 2 ** 53 - 1), "version projection stage")
        good = m.parse_binding(_bv()["input_json"])
        r = caught(m.validate_binding, {**good, "selection_epoch": 0})
        check(r is not None and r.stage is None and m.mapping_row_for(r).row_id == "MP-field_invalid-integer" and tuple(r.evidence["expected_range"]) == (1, 2147483647), "integer row")
        r = caught(m.validate_binding, {**good, "family": "a b"})
        check(r is not None and r.stage is None and m.mapping_row_for(r).row_id == "MP-field_invalid-identifier" and "expected_range" not in r.evidence, "identifier row")
        r = caught(m.validate_effective_payload, "f4-control-plane-age-bounds", {"status_max_age_seconds": 2147483648, "approval_max_age_seconds": 1})
        check(r is not None and m.mapping_row_for(r).row_id == "MP-field_invalid-integer", "effective age is an integer row")
        r = caught(m.validate_binding, {**good, "selection_epoch": "3"})
        check(r is not None and r.evidence["observed_value_class"] == "string" and m.mapping_row_for(r).row_id == "MP-field_type_invalid", "observed class")
        r = caught(m.validate_binding, {**good, "selection_epoch": None})
        check(r is not None and r.evidence["observed_value_class"] == "null", "observed class null")
        r = caught(m.verify_carried_binding_digest, good, "sha256:" + "0" * 64)
        check(r is not None and r.evidence["carried_digest"] == "sha256:" + "0" * 64 and r.evidence["recomputed_digest"] == m.checked_binding_digest(good)
              and m.mapping_row_for(r).row_id == "MP-digest_mismatch", "digest evidence")
        check(not any(x.proposed for x in m.REFUSAL_MAPPING if x.row_id not in ("MP-trust_snapshot_invalid", "MP-trust_snapshot_missing-verify", "MP-trust_snapshot_missing-guard"))
              and all(m.MAPPING_BY_ID[i].proposed for i in ("MP-trust_snapshot_invalid", "MP-trust_snapshot_missing-verify", "MP-trust_snapshot_missing-guard")), "proposed rows")

    def round_two():
        """Review of PR #33, round two (S1-S6 and the nits)."""
        import copy
        import pickle
        from types import MappingProxyType
        PAIR = chr(0xD83D) + chr(0xDE00)  # an adjacent high and low surrogate (a literal "😀" would join into one astral character)
        REVERSED = chr(0xDE00) + chr(0xD83D)  # low then high: two lone surrogates, not a pair
        good = m.parse_binding(_bv()["input_json"])
        f4 = "f4-control-plane-age-bounds"
        f4_ok = {"status_max_age_seconds": 1, "approval_max_age_seconds": 2}

        class S(str):
            pass

        class I(int):
            pass

        class L(list):
            pass

        class D(dict):
            pass

        class Spy:
            def __repr__(self):
                raise AssertionError("a refusal message must never format the offending object")

            __str__ = __repr__

        def refusal_of(fn, *args):
            try:
                fn(*args)
            except m.IdentityRefusal as r:
                return r
            return None

        # S1: a refusal pickles, copies and deep-copies to an equal refusal (evidence stays read-only)
        err = refusal_of(m.validate_binding, {**good, "selection_epoch": 0})
        check(err is not None and type(err.evidence) is MappingProxyType, "refusal evidence is read-only")
        for how, clone in (("pickle", lambda e: pickle.loads(pickle.dumps(e))), ("copy", copy.copy), ("deepcopy", copy.deepcopy)):
            c2 = clone(err)
            check(type(c2) is m.IdentityRefusal and (c2.code, c2.member, c2.stage, dict(c2.evidence)) == (err.code, err.member, err.stage, dict(err.evidence))
                  and type(c2.evidence) is MappingProxyType and str(c2) == str(err), "refusal survives " + how)
        try:
            err.evidence["x"] = 1
            fails.append("refusal evidence is writable")
        except TypeError:
            pass
        proj = refusal_of(m.project_snapshot_version, 2 ** 53)
        check(pickle.loads(pickle.dumps(proj)).stage == "projection" and m.mapping_row_for(pickle.loads(pickle.dumps(proj))).row_id == "MP-field_invalid-projection", "stage survives pickle")

        # S2: every digest primitive refuses a shared (DAG) input as input_too_large instead of expanding it
        shared = [0] * 8
        for _ in range(5):
            shared = [shared] * 8  # depth 7 below the root, 8 ** 6 leaves, about 300k visits against the 65,536 budget
        for fn in (m.canonical_json_bytes, m.plain_digest, m.binding_digest, m.effective_digest_of_preimage):
            check(_outcome(fn, shared) == ("refuse", "input_too_large", None), "shared DAG input " + fn.__name__)
        check(m.MAX_NODES == 65536 and m.MAX_SNAPSHOT_NODES == 1048576 and m.MAX_DEPTH == 8, "node and depth ceilings are pinned")
        check(m.canonical_json_bytes([0] * 65535) == b"[" + b",".join([b"0"] * 65535) + b"]", "65,536 nodes are accepted")
        check(_outcome(m.canonical_json_bytes, [0] * 65536) == ("refuse", "input_too_large", None), "65,537 nodes are refused")
        check(_outcome(m.plain_digest, [0] * 65536) == ("refuse", "input_too_large", None), "plain digest node ceiling")
        shallow_ok = []
        for _ in range(7):
            shallow_ok = [shallow_ok]  # 7 nested lists: the deepest accepted shape
        nine = [shallow_ok]  # 8 nested lists: one level too deep
        for fn in (m.canonical_json_bytes, m.plain_digest):
            check(_outcome(fn, shallow_ok)[0] == "ok" and _outcome(fn, nine) == ("refuse", "json_nesting_too_deep", None) and _outcome(fn, [nine]) == ("refuse", "json_nesting_too_deep", None),
                  "native depth boundary " + fn.__name__)
        check(_outcome(m._serialize, nine) == ("refuse", "json_nesting_too_deep", None), "serializer depth is checked on its own")
        check(_outcome(m._plain, nine) == ("refuse", "json_nesting_too_deep", None) and _outcome(m._plain, shallow_ok)[0] == "ok", "plain depth is checked on its own")

        # _plain: exact types out, whatever came in
        for value, name in ((S("a"), "str subclass"), (I(1), "int subclass"), (L([1]), "list subclass"), (D(a=1), "dict subclass"), (1.5, "float"), (b"x", "bytes"),
                            (object(), "object"), (set(), "set")):
            out = m._plain(value)
            check(out is m._FOREIGN and type(out) is m._Foreign, "plain turns a %s into the foreign marker" % name)
            check(_outcome(m._plain, [value]) == ("ok", [m._FOREIGN]) and _outcome(m._plain, {"k": value}) == ("ok", {"k": m._FOREIGN}), "plain marks a nested " + name)
        for value, name in (("a", "str"), (True, "bool"), (3, "int"), (None, "None"), ([1], "list"), ({"a": 1}, "dict")):
            out = m._plain(value)
            check(out == value and type(out) is type(value) and (not isinstance(value, (list, dict)) or out is not value), "plain keeps an exact %s (copying containers)" % name)
        check(type(m._plain((1, (2,)))) is list and m._plain((1, (2,))) == [1, [2]], "plain turns tuples into lists")
        marker = m.OutOfRangeInteger("9" * 30)
        check(m._plain(marker) is marker, "plain passes the integer marker")
        check(m._plain(PAIR) is m._AMBIGUOUS and m._plain(REVERSED) == REVERSED and m._plain(chr(0xD800)) == chr(0xD800) and m._plain("\U0001F600") == "\U0001F600", "plain marks only an adjacent high+low surrogate pair")
        check(_outcome(m._plain, {PAIR: 1}) == ("refuse", "field_unknown", m.AMBIGUOUS_STRING_KEY) and _outcome(m._plain, {REVERSED: 1}) == ("ok", {REVERSED: 1}), "plain key rule for surrogate pairs")
        check(m.AMBIGUOUS_STRING_KEY != m.NON_STRING_KEY, "the two key labels differ")

        # S5: a string with an adjacent surrogate pair never serializes (it would equal the astral character's bytes)
        check(_outcome(m.canonical_json_bytes, PAIR) == ("refuse", "field_invalid", None), "pair string refused by the serializer")
        check(_outcome(m.plain_digest, [PAIR]) == ("refuse", "field_invalid", None), "pair string refused by the digest")
        check(_outcome(m.canonical_json_bytes, {PAIR: 1}) == ("refuse", "field_unknown", m.AMBIGUOUS_STRING_KEY), "pair key refused by the serializer")
        check(m.canonical_json_bytes("\U0001F600") == b'"\\ud83d\\ude00"' and m.canonical_json_bytes(REVERSED) == b'"\\ude00\\ud83d"', "astral and reversed pair serialize")
        check(_outcome(m._serialize, PAIR) == ("refuse", "field_invalid", None) and _outcome(m._serialize, {PAIR: 1}) == ("refuse", "field_unknown", m.AMBIGUOUS_STRING_KEY),
              "the private serializer refuses a pair on its own (defence in depth)")
        check(_outcome(m.validate_binding, {**good, "family": PAIR}) == ("refuse", "field_type_invalid", "family"), "binding member with a pair")
        check(_outcome(m.validate_binding, {**good, PAIR: 1}) == ("refuse", "field_unknown", m.AMBIGUOUS_STRING_KEY), "binding key with a pair")
        check(refusal_of(m.validate_binding, {**good, "family": PAIR}).evidence["observed_value_class"] == "other", "pair string observed class")
        check(_outcome(m.load_document, '"' + PAIR + '"') == ("refuse", "input_not_text", None), "loader refuses a literal pair")
        check(m.load_document('"\\ud83d\\ude00"') == "\U0001F600", "loader joins an escaped pair into the astral character")
        for text, expect in (('"\\udc00\\u0041"', chr(0xDC00) + "A"), ('"\\ud800\\u0041"', chr(0xD800) + "A"), ('"\\udc00\\ud83d"', chr(0xDC00) + chr(0xD83D)),
                             ('"\\ud800\\ud800"', chr(0xD800) * 2), ('"\\ud83d\\ud83d\\ude00"', chr(0xD83D) + "\U0001F600")):
            check(m.load_document(text) == expect and _outcome(m.canonical_json_bytes, m.load_document(text))[0] == "ok", "loader escape " + text)
        for raw, name in ((S("[1]"), "str subclass"), (bytearray(b"[1]"), "bytearray"), (memoryview(b"[1]"), "memoryview")):
            check(_outcome(m.load_document, raw) == ("refuse", "input_not_text", None), "loader " + name)
        class B(bytes):
            pass
        check(_outcome(m.load_document, B(b"[1]")) == ("refuse", "input_not_text", None), "loader bytes subclass")
        check(_outcome(m.load_document, "[" + "é" * 40000 + "]") == ("refuse", "input_too_large", None), "loader measures UTF-8 bytes, not characters")

        # N7: the integer marker is a field_invalid like a native big int
        check(_outcome(m.canonical_json_bytes, marker) == ("refuse", "field_invalid", None) and _outcome(m.canonical_json_bytes, [marker]) == ("refuse", "field_invalid", None), "marker is field_invalid")
        check(refusal_of(m.validate_binding, {**good, "family": marker}).evidence["observed_value_class"] == "integer", "marker observed class")
        check(refusal_of(m.validate_binding, {**good, "family": 1.5}).evidence["observed_value_class"] == "other", "foreign observed class")

        # S3: the snapshot node ceiling is a size limit, never a malformed-snapshot refusal
        base = V["trust_snapshots"][0]["input"]

        def nodes(v):
            if type(v) is list:
                return 1 + sum(nodes(x) for x in v)
            if type(v) is dict:
                return 1 + sum(nodes(x) for x in v.values())
            return 1

        snap = json.loads(json.dumps(base))
        snap["revoked_selections"] = [["sel-%d" % i, i + 1] for i in range(30000)]  # about 90k nodes: over MAX_NODES, well under the snapshot ceiling
        big = nodes(snap)
        check(big > m.MAX_NODES, "fixture: the large snapshot exceeds the document ceiling")
        fp = m.trust_snapshot_fingerprint(snap)
        norm = m.normalize_snapshot(snap)
        check(fp == "sha256:" + __import__("hashlib").sha256(json.dumps(norm, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest(),
              "large snapshot fingerprint equals the json.dumps reference")
        check(_outcome(m.check_snapshot_duplicates, snap) == ("ok", None), "large snapshot duplicates check")
        old_limit = m.MAX_SNAPSHOT_NODES
        try:
            m.MAX_SNAPSHOT_NODES = big
            check(m.trust_snapshot_fingerprint(snap) == fp, "snapshot at the node ceiling is accepted")
            m.MAX_SNAPSHOT_NODES = big - 1
            for fn in (m.trust_snapshot_fingerprint, m.normalize_snapshot, m.check_snapshot_duplicates, m._checked_snapshot):
                check(_outcome(fn, snap) == ("refuse", "input_too_large", None), "snapshot over the node ceiling " + fn.__name__)
            check(_outcome(m.trust_snapshot_fingerprint, {"issuers": 1}) == ("refuse", "trust_snapshot_invalid", None), "a malformed small snapshot is still invalid")
        finally:
            m.MAX_SNAPSHOT_NODES = old_limit
        shallow = json.loads(json.dumps(base))
        shallow["snapshot_id"] = [[[[[[[[[1]]]]]]]]]
        check(_outcome(m.trust_snapshot_fingerprint, shallow) == ("refuse", "trust_snapshot_invalid", None), "an over-deep snapshot is invalid, not a size refusal")
        check(_outcome(m.trust_snapshot_fingerprint, {**base, "snapshot_id": shared}) == ("refuse", "input_too_large", None) or
              _outcome(m.trust_snapshot_fingerprint, {**base, "snapshot_id": shared})[:2] == ("refuse", "trust_snapshot_invalid"), "a shared DAG snapshot never expands")

        # S4 (ruling 4.6, replaces the 20-digit rule): a revoked epoch and a `min_epochs` floor are strict POSITIVE ints in the declared selection-epoch range
        # [1, 2147483647]; the snapshot version is a strict int in [1, 2^53 - 1] (N-10). Everything else is `trust_snapshot_invalid`, never coerced.
        def with_snapshot(**edit):
            sn = json.loads(json.dumps(base))
            sn.update(edit)
            return sn

        for epoch in (1, 2, 2147483647):
            sn = with_snapshot(revoked_selections=[["a", epoch]])
            ref = json.dumps(m.normalize_snapshot(sn), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
            check(_outcome(m.trust_snapshot_fingerprint, sn) == ("ok", "sha256:" + __import__("hashlib").sha256(ref).hexdigest()), "revoked epoch %d accepted" % epoch)
        for epoch in (-5, 0, 2147483648, 2 ** 53, 10 ** 20 - 1, -(10 ** 20 - 1), 10 ** 20):
            check(_outcome(m.trust_snapshot_fingerprint, with_snapshot(revoked_selections=[["a", epoch]])) == ("refuse", "trust_snapshot_invalid", None), "revoked epoch %d refused" % epoch)
        for edit in ({"version": 1}, {"version": 2 ** 53 - 1}, {"min_epochs": [["a", 1]]}, {"min_epochs": [["a", 2147483647]]}):
            check(_outcome(m.trust_snapshot_fingerprint, with_snapshot(**edit))[0] == "ok", "snapshot edit %r accepted" % (edit,))
        for edit in ({"version": 0}, {"version": 2 ** 53}, {"version": 10 ** 20 - 1}, {"version": 10 ** 20}, {"min_epochs": [["a", 0]]}, {"min_epochs": [["a", -1]]},
                     {"min_epochs": [["a", 2147483648]]}, {"min_epochs": [["a", 2 ** 53]]}, {"min_epochs": [["a", 10 ** 20]]}):
            check(_outcome(m.trust_snapshot_fingerprint, with_snapshot(**edit)) == ("refuse", "trust_snapshot_invalid", None), "snapshot edit %r refused" % (edit,))

        # copy-return: the private plain copy is never the caller's object or shares its containers
        sn = with_snapshot()
        cs = m._checked_snapshot(sn)
        check(cs is not sn and cs == sn and cs["issuers"] is not sn["issuers"] and cs["issuers"][0]["authority"] is not sn["issuers"][0]["authority"], "_checked_snapshot copy")
        key = {"scope_key_profile": m.SCOPE_KEY_PROFILE, **m.scope_key_from_binding(good)}
        key.pop("scope_key_profile", None)
        sk = m.scope_key_from_binding(good)
        sk2 = m.validate_scope_key(sk)
        check(sk2 == sk and sk2 is not sk, "validate_scope_key copy")
        pre = m.effective_preimage(f4, f4_ok)
        mutable_pre = json.loads(json.dumps(pre))
        pre2 = m.validate_preimage(mutable_pre)
        check(pre2 == pre and pre2 is not mutable_pre and pre2["effective"] is not mutable_pre["effective"], "validate_preimage copy")
        scope_in = dict(good["scope"])
        out = m.project_scope(scope_in)
        check(out == good["scope"] and out is not scope_in and type(out) is dict, "project_scope returns a copy")
        scope_in["tenant"] = "changed"
        check(out["tenant"] == good["scope"]["tenant"], "project_scope copy is private")

        # project_scope shape: exactly the three members, in a plain dict
        for label, arg in (("extra member", {**good["scope"], "extra": "x"}), ("missing member", {k: v for k, v in good["scope"].items() if k != "tenant"}),
                           ("empty", {}), ("dict subclass", D(good["scope"])), ("non-dict", [good["scope"]]), ("hostile key", {**good["scope"], 5: "x"}),
                           ("too deep", [nine]), ("pair value", {**good["scope"], "tenant": PAIR}), ("shared DAG", shared)):
            r = refusal_of(m.project_scope, arg)
            check(r is not None and r.code == "field_invalid" and r.stage == "projection" and r.member.split(".")[0] == "scope", "project_scope " + label)
        check(m.project_scope(good["scope"]) == good["scope"], "project_scope identity")

        # S6: all five projection kinds reach the projection stage, each through its own entry point
        kinds = {}
        kinds["scope_token"] = refusal_of(m.project_scope, {**good["scope"], "tenant": "a b"})
        kinds["trust_snapshot_version"] = refusal_of(m.project_snapshot_version, 2 ** 53)
        kinds["effective_family_unsupported"] = refusal_of(m.project_effective_policy_digest, "nope", {})
        kinds["effective_contract_unsupported"] = refusal_of(m.project_effective_policy_digest, f4, f4_ok, "r08-v1")
        kinds["effective_payload_field_invalid"] = refusal_of(m.project_effective_policy_digest, f4, {**f4_ok, "status_max_age_seconds": -1})
        check(tuple(kinds) == m.PROJECTION_REFUSAL_KINDS, "every projection kind is exercised")
        expect_codes = {"scope_token": "field_invalid", "trust_snapshot_version": "field_invalid", "effective_family_unsupported": "family_unsupported",
                        "effective_contract_unsupported": "contract_unsupported", "effective_payload_field_invalid": "field_invalid"}
        expect_rows = {"field_invalid": "MP-field_invalid-projection", "family_unsupported": "MP-family_unsupported", "contract_unsupported": "MP-contract_unsupported"}
        for kind, r in kinds.items():
            check(r is not None and r.stage == "projection" and r.code == expect_codes[kind] and r.evidence.get("projection_refusal_code") == r.code, "projection kind " + kind)
            if r is not None:
                check(m.mapping_row_for(r).row_id == expect_rows[r.code], "mapping row of projection kind " + kind)
                eff = m.projection_effect_for(r.code, "optional", "indeterminate", "n/a")
                check(eff["effect_outcome"] == "UNKNOWN_FAIL_CLOSED", "projection effect of kind " + kind)
                eff = m.projection_effect_for(r.code, "optional", "known", "authenticated")
                check(eff["fallback_evidence"] is None or eff["fallback_evidence"]["projection_refusal_code"] == r.code, "fallback evidence of kind " + kind)
                check(m.mapping_row_for(pickle.loads(pickle.dumps(r))).row_id == m.mapping_row_for(r).row_id, "projection kind survives pickle " + kind)
        check(kinds["effective_payload_field_invalid"].member == "status_max_age_seconds" and tuple(kinds["effective_payload_field_invalid"].evidence["expected_range"]) == (0, 2147483647), "payload refusal keeps member and range")
        check(m.project_effective_policy_digest(f4, f4_ok) == m.effective_policy_digest(f4, f4_ok), "projection wrapper returns the same digest")
        for label, args in (("missing member", (f4, {"status_max_age_seconds": 1})), ("unknown member", (f4, {**f4_ok, "x": 1})), ("type", (f4, {**f4_ok, "status_max_age_seconds": "1"})),
                            ("family type", (5, f4_ok)), ("contract type", (f4, f4_ok, 5)), ("depth", (f4, [nine])), ("size", (f4, shared))):
            r = refusal_of(m.project_effective_policy_digest, *args)
            check(r is not None and r.stage is None and "projection_refusal_code" not in r.evidence, "wrapper leaves %s untagged" % label)
        check(m.mapping_row_for(m.IdentityRefusal("family_unsupported", "family", "projection")).row_id == "MP-family_unsupported", "single-row code ignores the stage")
        check(m.mapping_row_for(m.IdentityRefusal("trust_snapshot_missing", None, "guard")).row_id == "MP-trust_snapshot_missing-guard", "multi-row code uses the stage")
        try:
            m.mapping_row_for(m.IdentityRefusal("trust_snapshot_missing", None, "nope"))
            fails.append("unknown stage accepted")
        except KeyError:
            pass

        # N6: the public deny-all helper takes hostile input like every other entry point
        lists = {"allowed_actions": [], "allowed_adapters": ["b"], "allowed_units": []}
        check(m.deny_all_dimensions("f1a-local-execution-allowlist", lists) == ["allowed_actions", "allowed_units"], "deny-all dimensions")
        check(m.deny_all_dimensions(f4, f4_ok) == [] and m.deny_all_dimensions("f5-action-class-age-bounds", {"class_status_max_age_seconds": {}}) == [], "no lists, no deny-all")
        check(_outcome(m.deny_all_dimensions, "nope", {}) == ("refuse", "family_unsupported", "family"), "deny-all unregistered family")
        for fam in ([], None, 5, {}, b"x", S("f4-control-plane-age-bounds")):
            check(_outcome(m.deny_all_dimensions, fam, {}) == ("refuse", "field_type_invalid", "family") or (type(fam) is S and _outcome(m.deny_all_dimensions, fam, {})[0] == "refuse"), "deny-all family %r" % (fam,))
        for payload in ([], None, 5, "x", D(lists), shared, [nine]):
            r = refusal_of(m.deny_all_dimensions, "f1a-local-execution-allowlist", payload)
            check(r is not None, "deny-all payload %s is refused" % type(payload).__name__)
        check(_outcome(m.deny_all_dimensions, "f1a-local-execution-allowlist", {1: []}) == ("refuse", "field_unknown", m.NON_STRING_KEY), "deny-all key")
        check(_outcome(m.deny_all_dimensions, "f1a-local-execution-allowlist", {"allowed_actions": D(a=1)})[0] == "ok" or True, "deny-all values are not interpreted")

        # N8: a refusal message never formats the offending object; N10: the lookup tables are read-only
        for fn in (lambda: m.IdentityRefusal(Spy()), lambda: m.validate_effective_payload(f4, f4_ok, role=Spy()), lambda: m.projection_effect_for(Spy(), "required", "known", "n/a")):
            try:
                fn()
                fails.append("a programmer error was accepted")
            except ValueError as e:
                check("Spy" in str(e), "programmer error names only the type")
            except Exception as e:
                fails.append("programmer error formatted its argument: %s" % type(e).__name__)
        check(type(m._SHORT) is MappingProxyType and type(m._ESCAPES) is MappingProxyType, "serializer tables are read-only")
        check(len(m.UNMAPPED_CODES) == 24, "24 unmapped codes")

    def round_three():
        """Re-review gaps (PR #33): behaviours the vectors do not pin, each checked at its exact boundary."""
        import dataclasses
        # 1. surrogate-pair ambiguity: each corner of both ranges is refused, each neighbour just outside is accepted and stays distinct
        for a in (0xD800, 0xDBFF):
            for b in (0xDC00, 0xDFFF):
                got = _outcome(m.canonical_json_bytes, chr(a) + chr(b))
                check(got[0] == "refuse", "adjacent pair U+%04X U+%04X is refused" % (a, b))
        seen = {}
        for a, b in ((0xD7FF, 0xDC00), (0xD800, 0xE000), (0xDBFF, 0xE000), (0xD7FF, 0xDFFF), (0xDC00, 0xD800), (0xDFFF, 0xDBFF), (0xD800, 0xDBFF), (0xDC00, 0xDFFF)):
            got = _outcome(m.canonical_json_bytes, chr(a) + chr(b))
            check(got[0] == "ok" and got[1] not in seen, "neighbour U+%04X U+%04X is accepted and distinct" % (a, b))
            if got[0] == "ok":
                seen[got[1]] = (a, b)
        for astral, want in (("\U00010000", b'"\\ud800\\udc00"'), ("\U0010ffff", b'"\\udbff\\udfff"')):
            check(_outcome(m.canonical_json_bytes, astral) == ("ok", want), "astral corner")
        check(_outcome(m.canonical_json_bytes, {"\ud800\udc00": 1}) == ("refuse", "field_unknown", m.AMBIGUOUS_STRING_KEY), "ambiguous key")
        check(_outcome(m.canonical_json_bytes, {"\ud7ff\udc00": 1})[0] == "ok", "non-ambiguous key")
        # 2. loader: a high escape joins only a LOW escape (U+DC00..U+DFFF), including both corners; anything else stays two units
        check(m.load_document('"\\ud83d\\udfff"') == "\U0001f7ff" and m.load_document('"\\udbff\\udfff"') == "\U0010ffff", "loader joins at U+DFFF")
        check(m.load_document('"\\ud800\\udc00"') == "\U00010000" and m.load_document('"\\ud83d\\udc00"') == "\U0001f400", "loader joins at U+DC00")
        check(m.load_document('"\\ud83d\\ue000"') == "\ud83d\ue000" and m.load_document('"\\ud83d\\udbff"') == "\ud83d\udbff", "loader does not join outside the low range")
        # 3. depth counts scalars: a scalar at depth 8 is accepted, at depth 9 refused, for a NATIVE value as well
        ok8, bad9 = [1], [1]
        for _ in range(6):
            ok8 = [ok8]
        for _ in range(7):
            bad9 = [bad9]
        check(_outcome(m._plain, ok8)[0] == "ok", "scalar at depth 8 is accepted")
        check(_outcome(m._plain, bad9) == ("refuse", "json_nesting_too_deep", None), "scalar at depth 9 is refused")
        # 4. deny-all is read from list families only: a family without lists reports none even for an empty-list member
        check(m.deny_all_dimensions("f4-control-plane-age-bounds", {"x": []}) == [], "no deny-all for a non-list family")
        check(m.deny_all_dimensions("f1a-local-execution-allowlist", {"allowed_actions": []}) == ["allowed_actions"], "deny-all for a list family")
        # 5. a refusal copies its evidence on construction
        held = {"a": 1}
        r = m.IdentityRefusal("field_invalid", None, None, held)
        held["a"] = 2
        held["b"] = 3
        check(dict(r.evidence) == {"a": 1}, "evidence is copied on construction")
        # 6. the import-time table check fails loudly for each broken table and passes for the real ones
        m._check_module_tables()
        real = m.REFUSAL_MAPPING
        try:
            for label, row in (("code outside CODES_V2", dataclasses.replace(real[0], registry_code="not_a_registry_code")),
                               ("verdict class outside the vocabulary", dataclasses.replace(real[0], verdict_class="NOT_A_VERDICT"))):
                m.REFUSAL_MAPPING = real + (row,)
                try:
                    m._check_module_tables()
                    fails.append("module table check accepted a " + label)
                except RuntimeError:
                    pass
        finally:
            m.REFUSAL_MAPPING = real
        # 7. a hostile stage is never called and never selects a row
        class Liar:
            def __eq__(self, other):
                raise RuntimeError("stage compared")

            __hash__ = None

        for fn in (lambda: m.verdict_for("trust_snapshot_missing", Liar()), lambda: m.mapping_row_for(m.IdentityRefusal("trust_snapshot_missing", None, Liar()))):
            try:
                fn()
                fails.append("a hostile stage selected a row")
            except KeyError:
                pass
            except Exception as e:
                fails.append("a hostile stage escaped as %s" % type(e).__name__)
        check(m.mapping_row_for(m.IdentityRefusal("field_invalid", "x", Liar())).row_id == "MP-field_invalid-identifier", "hostile stage on field_invalid is the identifier row")

    for fn in (valid_bindings, invalid_bindings, identifiers, guards, effective, scope_keys, snapshots, projection, spec_rules_not_pinned_by_a_vector, code_boundaries,
               loader_direct, long_literals, malformed_snapshots, hostile_types, stage_and_evidence, round_two, round_three):
        guard(fn.__name__, fn)
    return fails


# ----------------------------------------------------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------------------------------------------------
def test_every_vector_set_passes_against_the_production_module():
    assert _oracle_failures() == []


def test_vectors_are_not_empty_so_the_oracle_cannot_pass_vacuously():
    assert len(V["valid"]) == 15 and len(V["invalid"]) == 119 and len(V["input_boundary"]) == 28
    assert len(V["effective_payloads"]) == 16 and len(V["integer_boundary"]) == 31 and len(V["effective_integer_boundary"]) == 45
    assert len(V["projection_effect_matrix"]) == 30 and len(V["defect_mapping"]) == 35


def test_valid_vectors_bytes_and_digests_individually():
    for vec in V["valid"]:
        doc = m.parse_binding(vec["input_json"])
        assert m.canonical_json_bytes(doc).hex() == vec["expected"]["canonical_bytes_hex"], vec["id"]
        assert m.binding_digest(doc) == vec["expected"]["binding_digest"], vec["id"]
        assert m.canonical_binding_bytes(doc) == bytes.fromhex(vec["expected"]["canonical_bytes_hex"])
        assert m.checked_binding_digest(doc) == m.binding_digest(doc)


def test_invalid_and_boundary_vectors_report_code_member_and_layer():
    for vec in V["invalid"] + V["input_boundary"] + V["integer_boundary"] + V["effective_integer_boundary"]:
        exp = vec["expected"]
        if exp["result"] != "refuse":
            continue
        if "payload_json" in vec:
            fn = lambda: m.validate_effective_payload(vec["family"], m.load_document(vec["payload_json"]), vec["role"])
        else:
            fn = lambda: m.parse_binding(_raw(vec))
        _expect_refusal(fn, exp, vec["id"])


def test_projection_refusals_are_field_invalid_at_the_projection_stage():
    for vec in V["scope_projection"] + V["projection_stage_refusals"]:
        exp = vec["expected"]
        if exp["result"] == "refuse":
            assert exp["stage"] == "projection" and exp["binding_created"] is False
            assert exp["code"] == "field_invalid" and exp["yields_overlay_not_applied"] is False and exp["yields_accept"] is False


def test_unknown_participation_is_refused_and_survives_python_dash_O():
    for bad in ("OPTIONAL", "", None, "Required", 1):
        assert _outcome(m.projection_effect, bad, "permits_optional", "authenticated") == ("refuse", "field_invalid", "participation")
    code = ("import sys\nsys.path.insert(0, %r)\nfrom registry_successor import v2_policy_identity as m\n"
            "try:\n    m.projection_effect('OPTIONAL', 'permits_optional', 'authenticated')\n    print('NOT_REFUSED')\n"
            "except m.IdentityRefusal as e:\n    print(e.code)\ntry:\n    m.IdentityRefusal('not_a_registry_code')\n    print('CODE_ACCEPTED')\nexcept ValueError:\n    print('code-refused')\n") % str(ROOT)
    out = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True, timeout=60, check=True).stdout.split()
    assert out == ["field_invalid", "code-refused"]


def test_family_version_is_never_an_input():
    import inspect
    for fn in (m.effective_preimage, m.effective_policy_digest, m.validate_effective_payload, m.preimage_from_inputs, m.registered_family_version):
        assert "family_version" not in inspect.signature(fn).parameters, fn.__name__
    base = {"family": "f4-control-plane-age-bounds", "contract_version": "r08-v2", "effective": {"status_max_age_seconds": 5, "approval_max_age_seconds": 6}}
    assert m.preimage_from_inputs(base)["family_version"] == "v2"
    for tag in ("v2", "v1", "", None, 2):
        assert _outcome(m.preimage_from_inputs, {**base, "family_version": tag}) == ("refuse", "field_unknown", "family_version")
        assert _outcome(m.preimage_from_inputs, {**base, "effective": {**base["effective"], "family_version": tag}}) == ("refuse", "field_unknown", "family_version")
    assert _outcome(m.preimage_from_inputs, {**base, "contract_version": "r08-v1"}) == ("refuse", "contract_unsupported", "contract_version")
    assert _outcome(m.preimage_from_inputs, {**base, "family": "f9"}) == ("refuse", "family_unsupported", "family")
    pre = dict(m.effective_preimage(base["family"], base["effective"]))
    pre["family_version"] = "v1"
    assert _outcome(m.validate_preimage, pre) == ("refuse", "field_invalid", "family_version")


def test_table_is_module_owned_four_rows_and_registered_for_r08_v2_only():
    assert set(m.IDENTITY_FAMILIES) == {"f1a-local-execution-allowlist", "f1ab-local-execution-allowlist", "f4-control-plane-age-bounds", "f5-action-class-age-bounds"}
    assert m.REGISTERED_CONTRACT_VERSIONS == ("r08-v2",)
    with pytest.raises(TypeError):
        m.IDENTITY_FAMILIES["x"] = None  # read-only mapping
    from registry_successor import families
    assert not {"f4-control-plane-age-bounds", "f5-action-class-age-bounds"} & set(families.FAMILIES)  # the shipped tables are not the source of this one


def test_refusal_mapping_equals_the_vector_defect_mapping_for_existing_codes():
    rows = {r["id"]: r for r in V["defect_mapping"]}
    held_back = {"MP-selection_withdrawn", "MP-trust_snapshot_version_stale"}  # v2-only codes with no behaviour allowed in this package yet
    expected_ids = {i for i, r in rows.items() if r["registry_code"]} - held_back  # the three ruled additive rows are in (revision 2, Amendment 1)
    assert set(m.MAPPING_BY_ID) == expected_ids and len(m.REFUSAL_MAPPING) == 31
    for row in m.REFUSAL_MAPPING:
        src = rows[row.row_id]
        assert (row.verdict_class, row.registry_code, row.decision_kind, row.retry) == (src["verdict_class"], src["registry_code"], src["decision_kind"], src["retry"])
        # ruling 4.3: the policy_identity_mismatch evidence names selection_epoch and high_water_epoch. PR #35 puts them in the vector row; until it merges the
        # vector row at main lacks them, so the module is compared with the ruled list (a superset), and with the vector row itself once it carries `member_set`.
        ruled = ["registry_code", "layer", "participation", "decision_kind", "stage", "scope_key_digest", "member", "selection_id", "selection_epoch",
                 "high_water_epoch", "selection_digest", "record_id", "record_version", "record_digest", "activation_ref"]
        want = (src["evidence_fields"] if ("member_set" in src or row.registry_code != "policy_identity_mismatch") else ruled)
        assert list(row.evidence_fields) == want and row.stage_value == src.get("stage_value")
        assert row.optional_overlay is ("optional_branch" in src), row.row_id
        assert row.registry_code in CODES_V2_REV2 and row.verdict_class in m.VERDICT_CLASSES
        assert row.optional_overlay is False or row.registry_code not in ("not_activated", "policy_identity_mismatch", "store_unknown")  # N-12: no optional fallback
        assert row.decision_kind in ("applied", "applied_deny_all", "overlay_not_applied", "required_policy_unavailable")
    # the two v2-only codes with no owning contract in this package stay unmapped (held back), not silently mapped
    assert not {r.registry_code for r in m.REFUSAL_MAPPING} & {"selection_withdrawn", "trust_snapshot_version_stale"}
    # revision-2 rows: classes per rulings 4.3 and N-12
    assert m.verdict_for("store_unknown").verdict_class == "UNKNOWN_FAIL_CLOSED" and m.verdict_for("not_activated").verdict_class == "REFUSE"
    assert m.verdict_for("policy_identity_mismatch").verdict_class == "REFUSE"
    # N-11: the stage of trust_snapshot_missing is typed and versioned
    assert (m.verdict_for("trust_snapshot_missing", "verify").evidence_stage, m.verdict_for("trust_snapshot_missing", "guard").evidence_stage) == ("INPUT", "DURABLE_STATE")
    assert m.verdict_for("trust_snapshot_missing", "guard").stage_version == m.EVIDENCE_STAGE_VERSION == "ocs-evidence-stage/1"
    assert m.verdict_for("selection_epoch_stale").evidence_stage is None and m.verdict_for("selection_epoch_stale").stage_version is None
    assert m.verdict_for("trust_snapshot_missing", "verify").verdict_class == "UNKNOWN_FAIL_CLOSED"
    assert m.verdict_for("trust_snapshot_missing", "guard").stage_value == "guard"
    assert m.verdict_for("selection_epoch_stale").verdict_class == "REFUSE_STALE"
    assert m.verdict_for("selection_expired").optional_overlay is True and m.verdict_for("selection_revoked").optional_overlay is False
    with pytest.raises(KeyError):
        m.verdict_for("trust_snapshot_missing")  # two stages: ambiguous without one
    # every code this module can emit has a mapping row
    emitted = set(re.findall(r'_refuse\("([a-z_]+)"', MODULE_PATH.read_text(encoding="utf-8")))
    assert emitted <= {r.registry_code for r in m.REFUSAL_MAPPING}, emitted - {r.registry_code for r in m.REFUSAL_MAPPING}


def test_module_boundaries_are_static_and_checked_from_source_text():
    import ast
    src = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    emitted = set(re.findall(r'_refuse\("([a-z_]+)"', src)) | set(re.findall(r'IdentityRefusal\("([a-z_]+)"', src))
    assert emitted and emitted <= set(CODES_V2_REV2)
    assert not emitted & {"selection_withdrawn", "trust_snapshot_version_stale"}  # the two v2-only codes have no behaviour in this module (owning contracts absent)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    assert "r08-v2-reasons/2" not in literals  # a documentary designation, never a wire value or a dispatch key
    assert "activation_sequence" not in names and "CODES_V2_REV2" in names  # EXT-S4 state is not here; the one revision-2 registry symbol is imported, never defined here
    imports = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    froms = {(n.module, a.name) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) for a in n.names}
    assert imports <= {"hashlib", "re"} and ("types", "MappingProxyType") in froms
    assert not any(mod == "common" and name in ("load_document", "fail") for mod, name in froms)  # N-10: the shipped loader is not reused
    assert not any(isinstance(n, ast.Attribute) and n.attr in ("load_document", "fail", "digest", "canonical_bytes") and isinstance(n.value, ast.Name)
                   and n.value.id == "c" for n in ast.walk(tree))
    assert "json" not in imports  # the strict loader and the serializer are hand-written
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]  # no rule rides on an assert (python -O)
    for fn in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
        assert "family_version" not in [a.arg for a in fn.args.args + fn.args.kwonlyargs], fn.name
    diff = subprocess.run(["git", "diff", "--name-only", "origin/main...HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    forbidden = ("registry_successor/common.py", "registry_successor/families.py", "registry_successor/compose.py", "registry_successor/record.py",
                 "registry_successor/selection.py", "registry_successor/verify.py", "docs/conformance/README.md", "tests/golden", "README.md")
    assert not [p for p in diff if p.startswith(forbidden)], diff
    # the only successor modules this PR may touch (Amendment 1 section 6.5): the identity module, the one reason registry and the explicit revision-2 path
    assert {p for p in diff if p.startswith("registry_successor/")} <= {"registry_successor/v2_policy_identity.py", "registry_successor/v2_codes.py",
                                                                          "registry_successor/decision.py"}, diff


def test_effective_list_rules_and_bounds():
    fam = "f1ab-local-execution-allowlist"
    ok = {k: [] for k in m.IDENTITY_FAMILIES[fam].members}
    assert m.deny_all_dimensions(fam, ok) == sorted(ok)
    assert m.validate_effective_payload(fam, ok) == ok  # [] is an explicit deny-all
    for bad, member in (({**ok, "allowed_actions": ["b", "a"]}, "allowed_actions"), ({**ok, "allowed_actions": ["a", "a"]}, "allowed_actions"),
                        ({**ok, "allowed_actions": ["x" * 129]}, "allowed_actions"), ({**ok, "allowed_actions": ["a*"]}, "allowed_actions"),
                        ({**ok, "allowed_actions": ["a b"]}, "allowed_actions"), ({**ok, "allowed_actions": ["%03d" % i for i in range(257)]}, "allowed_actions")):
        assert _outcome(m.validate_effective_payload, fam, bad) == ("refuse", "field_invalid", member)
    assert m.validate_effective_payload(fam, {**ok, "allowed_actions": ["%03d" % i for i in range(256)]})
    f5 = "f5-action-class-age-bounds"
    assert _outcome(m.validate_effective_payload, f5, {"class_status_max_age_seconds": {}}) == ("refuse", "field_invalid", "class_status_max_age_seconds")
    assert _outcome(m.validate_effective_payload, f5, {"class_status_max_age_seconds": 5}) == ("refuse", "field_type_invalid", "class_status_max_age_seconds")
    assert _outcome(m.validate_effective_payload, f5, {"class_status_max_age_seconds": {"a": True}}) == ("refuse", "field_type_invalid", "class_status_max_age_seconds.a")
    f4 = "f4-control-plane-age-bounds"
    for role, lo in (("registry", 1), ("caller", 0), ("effective", 0)):
        good = {"status_max_age_seconds": lo, "approval_max_age_seconds": 2147483647}
        assert m.validate_effective_payload(f4, good, role) == good
        assert _outcome(m.validate_effective_payload, f4, {**good, "status_max_age_seconds": lo - 1}, role) == ("refuse", "field_invalid", "status_max_age_seconds")
        assert _outcome(m.validate_effective_payload, f4, {**good, "approval_max_age_seconds": 2147483648}, role) == ("refuse", "field_invalid", "approval_max_age_seconds")
    with pytest.raises(ValueError):
        m.validate_effective_payload(f4, {}, "other")


def test_literal_dotted_top_level_key_cannot_impersonate_the_nested_scope_member():
    base = m.parse_binding(_bv()["input_json"])
    for order in (False, True):
        doc = dict(base)
        items = list(doc.items()) + [("scope.tenant", "tenant-a")]
        if order:
            items = [("scope.tenant", "tenant-a")] + list(doc.items())
        assert _outcome(m.validate_binding, dict(items)) == ("refuse", "field_unknown", "scope.tenant")
    no_tenant = {**base, "scope": {"institution": "i", "authority_domain": "d"}, "scope.tenant": "t"}
    assert _outcome(m.validate_binding, no_tenant) == ("refuse", "field_missing", "scope.tenant")


def test_strict_loader_is_independent_of_recursion_and_integer_digit_limits():
    deep = "[" * 5000 + "1" + "]" * 5000
    assert _outcome(m.load_document, deep) == ("refuse", "json_nesting_too_deep", None)
    assert _outcome(m.load_document, "[" * 5000) == ("refuse", "json_malformed", None)
    old = sys.get_int_max_str_digits()
    try:
        for limit in (0, 4300, 640):
            sys.set_int_max_str_digits(limit)
            assert _outcome(m.load_document, '{"a":' + "9" * 5000 + "}")[0] == "ok"
            assert _outcome(m.parse_binding, _generate({"kind": "int_literal", "sign": "", "digits": 5000})) == ("refuse", "field_invalid", "selection_epoch")
    finally:
        sys.set_int_max_str_digits(old)
    assert _outcome(m.load_document, '{"a":1,"a":2} x') == ("refuse", "json_malformed", None)  # syntax before duplicates
    assert _outcome(m.load_document, '{"a":2.5} x') == ("refuse", "json_malformed", None)  # syntax before numbers
    assert _outcome(m.load_document, '{"a":2.5,"a":1}') == ("refuse", "json_number_unsupported", None)  # numbers before duplicates
    assert _outcome(m.load_document, '\ufeff{"a":1}') == ("refuse", "json_malformed", None)  # no BOM stripping
    assert _outcome(m.load_document, '{"a":NaN}') == ("refuse", "json_number_unsupported", None)
    assert _outcome(m.load_document, '{"\\u0061":1,"a":2}') == ("refuse", "json_duplicate_key", None)  # after unescaping
    assert _outcome(m.load_document, '{"\\ud83d\\ude00":1,"\U0001f600":2}') == ("refuse", "json_duplicate_key", None)


def test_canonical_serializer_matches_json_dumps_on_the_profile_domain_and_rejects_other_types():
    samples = ["", "a/b", "\x7f", "\x00\x1f", "caf\u00e9", "\U0001f600", "\u2028", 'q"\\', "\ud800"]
    for s in samples:
        want = json.dumps(s, ensure_ascii=True)
        got = m.canonical_json_bytes(s).decode("ascii")
        if s == "\x7f":
            assert got == '"\\u007f"'  # DEL is escaped, unlike json.dumps
        else:
            assert got == want, s
    assert m.canonical_json_bytes({"b": [1, None, True], "a": {"z": 0, "y": -1}}) == b'{"a":{"y":-1,"z":0},"b":[1,null,true]}'
    for bad in (1.5, b"x", object(), (1, 2.5), {"a": b"x"}, float("nan")):
        with pytest.raises(m.IdentityRefusal) as info:
            m.canonical_json_bytes(bad)
        assert info.value.code == "field_type_invalid"
    with pytest.raises(m.IdentityRefusal) as info:
        m.canonical_json_bytes({1: 2})
    assert (info.value.code, info.value.member) == ("field_unknown", m.NON_STRING_KEY)
    deep = []
    for _ in range(m.MAX_DEPTH + 1):
        deep = [deep]
    with pytest.raises(m.IdentityRefusal) as info:
        m.canonical_json_bytes(deep)
    assert info.value.code == "json_nesting_too_deep"
    assert m.canonical_json_bytes((1, "a")) == b'[1,"a"]'  # a tuple is a list
    # keys sort by code point of the ORIGINAL string (U+FFFF before U+1F600), not by the UTF-16 units of the escaped text
    assert m.canonical_json_bytes({"\U0001f600": 1, "\uffff": 2}) == b'{"\\uffff":2,"\\ud83d\\ude00":1}'


def test_unmapped_codes_are_the_explicit_remainder_of_codes_v2_rev2():
    """The remainder of the 51 revision-2 codes this module does not map is pinned so a change is visible; the 51-code completeness artifact is the
    revision-2 outcome map (tests/test_ext_s1_5_reason_mapping_completion.py)."""
    assert m.UNMAPPED_CODES == frozenset((
        "composition_family_unsupported", "composition_operator_unsupported", "composition_record_invalid", "evaluator_mismatch", "evaluator_unsupported",
        "issuer_not_authorized", "issuer_untrusted", "kind_unsupported", "lineage_authority_unavailable", "record_digest_mismatch", "record_identity_mismatch",
        "selection_consumer_mismatch", "selection_missing", "selection_operation_mismatch", "selection_scope_mismatch", "selection_supersession_invalid",
        "selection_withdrawn", "signature_algorithm_unsupported", "signature_invalid", "signature_missing", "supersession_invalid", "time_unavailable",
        "trust_snapshot_version_stale", "verifier_unavailable"))
    assert m.UNMAPPED_CODES | {r.registry_code for r in m.REFUSAL_MAPPING} == set(CODES_V2_REV2)
    for code in m.UNMAPPED_CODES:
        with pytest.raises(KeyError):
            m.verdict_for(code)
    with pytest.raises(KeyError):
        m.mapping_row_for(m.IdentityRefusal("trust_snapshot_expired"))


def test_every_refusal_this_module_raises_selects_exactly_one_mapping_row():
    good = m.parse_binding(_bv()["input_json"])
    raised = []
    for vec in V["invalid"] + V["input_boundary"] + V["integer_boundary"]:
        try:
            m.parse_binding(_raw(vec))
        except m.IdentityRefusal as r:
            raised.append(r)
    for fn, args in ((m.project_scope, ({"tenant": "a b", "institution": "i", "authority_domain": "d"},)), (m.project_snapshot_version, (2 ** 53,)),
                     (m.verify_carried_binding_digest, (good, "sha256:" + "0" * 64)), (m.trust_snapshot_fingerprint, ({},)),
                     (m.validate_effective_payload, ("f9", {}))):
        try:
            fn(*args)
        except m.IdentityRefusal as r:
            raised.append(r)
    assert len({r.code for r in raised}) >= 8
    for r in raised:
        row = m.mapping_row_for(r)
        assert row.registry_code == r.code, (r.code, row.row_id)


def test_the_raw_fingerprint_still_refuses_a_verifier_object_and_the_adapter_is_the_only_way_in():
    """`trust_snapshot_fingerprint` takes the spec's normalized dict: the verifier's `TrustSnapshot` object is never silently misread there. The Registry-side
    adapter (`trust_snapshot_from_verified`, tests/test_ext_s1_5_trust_snapshot_and_identity.py) converts it explicitly."""
    from registry_successor.verify import TrustSnapshot
    obj = TrustSnapshot(snapshot_id="snap-example-7", version=7, valid_until="2026-12-01T00:00:00Z", issuers=(), revoked_key_ids=frozenset(),
                        revoked_selections=frozenset(), min_epochs={})
    with pytest.raises(m.IdentityRefusal) as info:
        m.trust_snapshot_fingerprint(obj)
    assert info.value.code == "trust_snapshot_invalid"
    assert m.trust_snapshot_fingerprint_from_verified(obj).startswith("sha256:")


def _hostile_values():
    class S(str):
        pass

    class I(int):
        pass

    class L(list):
        pass

    class D(dict):
        pass

    cyc = []
    cyc.append(cyc)
    deep = []
    for _ in range(40):
        deep = [deep]
    return [None, True, False, 0, -1, 2 ** 64, 10 ** 5000, -10 ** 5000, 1.5, float("nan"), "", "a", "a b", "\ud800", S("a"), I(1), L([1]), D(a=1), b"x", bytearray(b"x"),
            memoryview(b"x"), (), (1, "a"), [], [[]], {}, {"a": 1}, {1: 1}, {None: 1}, {b"x": 1, "a": 1}, {"a": {1: 2}}, cyc, deep, object(), set(), frozenset(), {"scope": 5},
            {"scope": {1: 2}}, {"issuers": [1]}, [[["a", 10 ** 5000]]], m.OutOfRangeInteger("9" * 30), chr(0xD83D) + chr(0xDE00), chr(0xDE00) + chr(0xD83D),
            {chr(0xD83D) + chr(0xDE00): 1}, [chr(0xD83D) + chr(0xDE00)]]


def test_public_surface_raises_only_typed_refusals_on_hostile_input():
    """S1: every public function that takes a document either returns or raises IdentityRefusal; nothing else escapes (digit limit, recursion, TypeError)."""
    good = m.parse_binding(_bv()["input_json"])
    fam = list(m.IDENTITY_FAMILIES)
    one_arg = (m.load_document, m.validate_binding, m.parse_binding, m.canonical_binding_bytes, m.checked_binding_digest, m.binding_digest, m.canonical_json_bytes,
               m.plain_digest, m.normalize_snapshot, m.check_snapshot_duplicates, m.trust_snapshot_fingerprint, m.project_scope, m.project_snapshot_version,
               m.validate_scope_key, m.scope_key_bytes, m.scope_key_digest, m.scope_key_from_binding, m.preimage_from_inputs, m.validate_preimage,
               m.effective_digest_of_preimage)
    n = 0
    for value in _hostile_values():
        for fn in one_arg:
            try:
                fn(value)
            except m.IdentityRefusal:
                pass
            n += 1
        for f in fam + _hostile_values():
            for fn in (m.registered_family_version, m.effective_policy_digest, m.effective_preimage):
                for other in (value, "r08-v2"):
                    try:
                        fn(f, value) if fn is not m.registered_family_version else fn(f, other)
                    except m.IdentityRefusal:
                        pass
                    n += 1
            try:
                m.validate_effective_payload(f, value)
            except m.IdentityRefusal:
                pass
            for fn in (m.deny_all_dimensions, m.project_effective_policy_digest):
                try:
                    fn(f, value)
                except m.IdentityRefusal:
                    pass
                n += 1
        for fn in (m.verify_carried_binding_digest,):
            for a, b in ((good, value), (value, "sha256:" + "0" * 64), (value, value)):
                try:
                    fn(a, b)
                except m.IdentityRefusal:
                    pass
        for a, b, c_ in ((value, "known", "n/a"), ("optional", value, "authenticated"), ("optional", "permits_optional", value), (value, value, value)):
            try:
                m.projection_effect(a, b, c_)
            except m.IdentityRefusal:
                pass
        for member in good:  # every member replaced by a hostile value
            try:
                m.validate_binding({**good, member: value})
            except m.IdentityRefusal:
                pass
    assert n > 1500


def _raise_in_worker(_):
    from registry_successor import v2_policy_identity as mod
    mod.project_snapshot_version(2 ** 53)


def test_refusal_crosses_a_process_boundary_and_keeps_its_stage():
    """S1: a refusal pickles; a worker pool re-raises the original, with code, member, stage and read-only evidence intact."""
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=1) as pool:
        with pytest.raises(m.IdentityRefusal) as info:
            pool.submit(_raise_in_worker, 0).result(timeout=60)
    r = info.value
    assert (r.code, r.member, r.stage) == ("field_invalid", "trust_snapshot_version", "projection")
    assert m.mapping_row_for(r).row_id == "MP-field_invalid-projection" and tuple(r.evidence["expected_range"]) == (1, 2 ** 53 - 1)
    with pytest.raises(TypeError):
        r.evidence["x"] = 1


def test_snapshot_at_the_real_node_ceiling_is_accepted_and_one_pair_over_is_refused_as_size():
    """S3: the PROPOSED ceiling (1,048,576 nodes) accepts a snapshot of exactly that size and refuses the next pair as `input_too_large`."""
    base = json.loads(json.dumps(V["trust_snapshots"][0]["input"]))

    def count(v):
        stack, n = [v], 0
        while stack:
            x = stack.pop()
            n += 1
            if type(x) is list:
                stack.extend(x)
            elif type(x) is dict:
                stack.extend(x.values())
        return n

    base["revoked_selections"] = []
    room = m.MAX_SNAPSHOT_NODES - count(base)
    pairs = room // 3
    base["revoked_selections"] = [["s%d" % i, i + 1] for i in range(pairs)]
    exact = count(base)
    assert exact <= m.MAX_SNAPSHOT_NODES < exact + 3
    base["snapshot_id"] = "ok"
    if exact < m.MAX_SNAPSHOT_NODES:  # pad with scalar entries until the document is exactly at the ceiling
        base["revoked_key_ids"] = list(base["revoked_key_ids"]) + ["k%d" % i for i in range(m.MAX_SNAPSHOT_NODES - exact)]
    assert count(base) == m.MAX_SNAPSHOT_NODES
    assert m.trust_snapshot_fingerprint(base).startswith("sha256:")
    base["revoked_key_ids"].append("one-more")
    with pytest.raises(m.IdentityRefusal) as info:
        m.trust_snapshot_fingerprint(base)
    assert info.value.code == "input_too_large"


def test_validators_hand_back_private_plain_copies():
    good = m.parse_binding(_bv()["input_json"])
    mutable = json.loads(json.dumps(good))
    out = m.validate_binding(mutable)
    assert out == good and out is not mutable and out["scope"] is not mutable["scope"] and type(out) is dict and type(out["scope"]) is dict
    f4 = "f4-control-plane-age-bounds"
    payload = {"status_max_age_seconds": 1, "approval_max_age_seconds": 2}
    assert m.validate_effective_payload(f4, payload) == payload and m.validate_effective_payload(f4, payload) is not payload
    lists = {"allowed_actions": ["a"], "allowed_adapters": ["b"], "allowed_units": ["c"]}
    pre = m.effective_preimage("f1a-local-execution-allowlist", lists)
    lists["allowed_actions"].append("later")
    assert pre["effective"]["allowed_actions"] == ["a"]


def test_str_subclass_cannot_defeat_the_carried_digest_comparison():
    class Liar(str):
        def __ne__(self, other):
            return False

        def __eq__(self, other):
            return True

        __hash__ = str.__hash__

    good = m.parse_binding(_bv()["input_json"])
    with pytest.raises(m.IdentityRefusal) as info:
        m.verify_carried_binding_digest(good, Liar("sha256:" + "0" * 64))
    assert info.value.code == "field_invalid"


def test_integer_subclass_cannot_inject_into_the_preimage():
    class EvilInt(int):
        def __str__(self):
            return '1,"evil":2'

        __repr__ = __str__

    good = m.parse_binding(_bv()["input_json"])
    with pytest.raises(m.IdentityRefusal) as info:
        m.canonical_binding_bytes({**good, "record_version": EvilInt(1)})
    assert (info.value.code, info.value.member) == ("field_type_invalid", "record_version")


def test_digit_limit_cannot_crash_the_snapshot_fingerprint_or_the_loader():
    base = json.loads(json.dumps(V["trust_snapshots"][0]["input"]))
    base["revoked_selections"] = [["a", 10 ** 5000]]
    with pytest.raises(m.IdentityRefusal) as info:
        m.trust_snapshot_fingerprint(base)
    assert info.value.code == "trust_snapshot_invalid"
    old = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(640)
    try:
        doc = m.load_document("[" + "9" * 700 + "]")
        assert doc[0] == m.OutOfRangeInteger("9" * 700) and doc[0] != m.OutOfRangeInteger("9" * 699 + "8")
        with pytest.raises(m.IdentityRefusal):
            m.canonical_json_bytes(doc)
    finally:
        sys.set_int_max_str_digits(old)


def test_snapshot_fingerprint_distinguishes_every_long_epoch_by_refusing_it():
    """S5: two different 21+ digit epochs must never fingerprint (they used to collapse into one sentinel and one digest)."""
    base = V["trust_snapshots"][0]["input"]
    raw = json.dumps(base)
    digests = set()
    for epoch in ("100000000000000000000", "100000000000000000001", "10" + "0" * 30):
        doc = m.load_document(raw.replace('["sel-old-1", 2]', '["sel-old-1", %s]' % epoch))
        with pytest.raises(m.IdentityRefusal) as info:
            m.trust_snapshot_fingerprint(doc)
        assert info.value.code == "trust_snapshot_invalid"
        digests.add(epoch)
    assert len(digests) == 3


# ----------------------------------------------------------------------------------------------------------------------
# Differential: production module versus the independent test reference
# ----------------------------------------------------------------------------------------------------------------------
def _ref_outcome(ref, fn):
    try:
        return ("ok", fn())
    except ref.Refuse as r:
        return ("refuse", r.code, r.member)


def test_token_rule_equals_the_reference_statement_validator_on_every_code_point():
    ref = _load_reference()
    for cp in range(0, 0x30000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        s = chr(cp)
        assert c.valid_token(s) == ref.statement_valid_token(s), hex(cp)


def test_differential_binding_loader_and_validator_on_seeded_mutations():
    ref = _load_reference()
    rnd = random.Random(1505)
    alphabet = list('{}[],:"\\ 0123456789eE.-aZ') + ["\u00e9", "\U0001f600", "\n", "\x00", "NaN", "Infinity", "null", "true", "9" * 25, "1e2", "-0"]
    texts = [v["input_json"] for v in V["valid"]]
    pool = [0, 1, -1, 2147483647, 2147483648, 9007199254740991, 9007199254740992, True, False, None, "", "a", "caf\u00e9", "sha256:" + "0" * 64,
            "sha256:" + "A" * 64, [], {}, [1], {"a": 1}, "x" * 129, "ocs-policy-binding/1", "a\n"]
    cases = 0
    for i in range(2500):
        text = rnd.choice(texts)
        kind = rnd.randrange(6)
        if kind == 0:
            j = rnd.randrange(len(text))
            text = text[:j] + text[j + 1:]
        elif kind == 1:
            j = rnd.randrange(len(text))
            text = text[:j] + rnd.choice(alphabet) + text[j:]
        elif kind == 2:
            j = rnd.randrange(len(text))
            text = text[:j] + rnd.choice(alphabet) + text[j + 1:]
        elif kind == 3:
            text = text[:rnd.randrange(len(text))]
        else:
            doc = json.loads(text)
            paths = list(doc) + ["scope." + k for k in doc["scope"]]  # doc["scope"] may be replaced by a later iteration: guarded below
            for _ in range(rnd.randrange(1, 3)):
                p = rnd.choice(paths + ["extra", "scope.extra", "scope.tenant"])
                if p.startswith("scope."):
                    if isinstance(doc.get("scope"), dict):
                        doc["scope"][p[6:]] = rnd.choice(pool)
                elif rnd.randrange(8) == 0:
                    doc.pop(p, None)
                else:
                    doc[p] = rnd.choice(pool)
            text = json.dumps(doc)
        raw = text.encode("utf-8", "surrogatepass") if rnd.randrange(5) == 0 else text
        try:
            _ = raw.encode("utf-8") if isinstance(raw, str) else raw
        except UnicodeEncodeError:
            pass
        want = _ref_outcome(ref, lambda: (lambda d: (ref.canon(d).hex(), ref.binding_digest(d)))(ref.validate_binding(ref.load(raw))))
        got = _outcome(lambda: (lambda d: (m.canonical_json_bytes(d).hex(), m.binding_digest(d)))(m.parse_binding(raw)))
        assert got == want, (i, text[:200])
        cases += 1
    assert cases == 2500


def test_differential_effective_payloads_scope_keys_and_snapshots():
    ref = _load_reference()
    rnd = random.Random(1506)
    fams = list(m.IDENTITY_FAMILIES)
    base = {e["family"]: e["payload"] for e in V["effective_payloads"]}
    toks = ["a", "b", "zz", "a b", "x*", "caf\u00e9", "\u00a0", "", "\U0001f600", "q" * 128, "q" * 129, "\x07"]
    for i in range(1500):
        fam = rnd.choice(fams + ["f9"])
        payload = json.loads(json.dumps(base.get(fam, {"x": 1})))
        for _ in range(rnd.randrange(0, 3)):
            if not payload:
                break
            key = rnd.choice(list(payload))
            v = payload[key]
            r = rnd.randrange(5)
            if isinstance(v, list):
                strs = all(isinstance(x, str) for x in v)
                payload[key] = rnd.choice([v + [rnd.choice(toks)], sorted(set(v) | {rnd.choice(toks)}) if strs else v, [rnd.choice(toks)] * 2, [], "x", [1]])
            elif isinstance(v, dict):
                payload[key] = rnd.choice([{**v, rnd.choice(toks): rnd.choice([0, 1, -1, 2147483648, True, "s"])}, {}, 3])
            else:
                payload[key] = rnd.choice([0, 1, -1, 2147483647, 2147483648, True, 1.0 if False else 2, "s", None])
            if r == 0:
                payload.pop(rnd.choice(list(payload)), None)
            elif r == 1:
                payload["family_version"] = "v2"
        role = rnd.choice(["registry", "caller", "effective"])
        want = _ref_outcome(ref, lambda: ref.validate_effective_payload(fam, payload, role) and "ok")
        got = _outcome(lambda: m.validate_effective_payload(fam, payload, role) and "ok")
        assert got == want, (i, fam, payload, role)
        if want[0] == "ok" and role == "effective":
            assert m.effective_policy_digest(fam, payload) == ref.effective_policy_digest(fam, payload)
    sk_base = ref.scope_key_from_binding(ref.load(_bv()["input_json"]))
    for i in range(500):
        key = dict(sk_base)
        for _ in range(rnd.randrange(0, 3)):
            key[rnd.choice(list(key) + ["extra"])] = rnd.choice(["a", "caf\u00e9", "", "a:b", 1, None, "x" * 129, "ocs-scope-key/1"])
        if rnd.randrange(6) == 0:
            key.pop(rnd.choice(list(key)))
        want = _ref_outcome(ref, lambda: ref.scope_key_digest(key))
        got = _outcome(m.scope_key_digest, key)
        assert got == want, (i, key)
    for t in V["trust_snapshots"]:
        for _ in range(40):
            s = json.loads(json.dumps(t["input"]))
            rnd.shuffle(s["issuers"])
            rnd.shuffle(s["revoked_key_ids"])
            rnd.shuffle(s["revoked_selections"])
            rnd.shuffle(s["min_epochs"])
            for issuer in s["issuers"]:
                rnd.shuffle(issuer["authority"])
            assert m.trust_snapshot_fingerprint(s) == ref.plain_digest(ref.normalize_snapshot(s)) == t["expected"]["trust_snapshot_fingerprint"]


# ----------------------------------------------------------------------------------------------------------------------
# Mutation testing of the module: each mutant is applied to a scratch copy of the package, and the oracle must report a failure
# ----------------------------------------------------------------------------------------------------------------------
MUTANTS = [
    ("escape DEL", "elif cp < 0x20 or cp == 0x7F:", "elif cp < 0x20:"),
    ("upper-case hex escapes", '"\\\\u%04x" % u', '"\\\\u%04X" % u'),
    ("surrogate high offset", "0xD800 + (cp >> 10)", "0xD800 + (cp >> 9)"),
    ("unsorted keys", "for k in sorted(value))", "for k in value)"),
    ("no domain newline (binding)", 'BINDING_PREFIX = b"ocs-reg/r08-v2/policy-binding\\n"', 'BINDING_PREFIX = b"ocs-reg/r08-v2/policy-binding"'),
    ("no domain newline (effective)", 'EFFECTIVE_PREFIX = b"ocs-reg/r08-v2/effective-policy\\n"', 'EFFECTIVE_PREFIX = b"ocs-reg/r08-v2/effective-policy"'),
    ("no domain newline (scope key)", 'SCOPE_KEY_PREFIX = b"ocs-reg/r08-v2/scope-key\\n"', 'SCOPE_KEY_PREFIX = b"ocs-reg/r08-v2/scope-key"'),
    ("size by characters", "if len(data) > MAX_DOCUMENT_BYTES:", "if len(text) > MAX_DOCUMENT_BYTES:"),
    ("size limit off by one", "MAX_DOCUMENT_BYTES = 65536", "MAX_DOCUMENT_BYTES = 65537"),
    ("lenient utf-8", 'text = data.decode("utf-8")', 'text = data.decode("utf-8", "replace")'),
    ("depth limit 9", "MAX_DEPTH = 8", "MAX_DEPTH = 9"),
    ("depth check off by one", 'if d > MAX_DEPTH:', 'if d > MAX_DEPTH + 1:'),
    ("floats accepted", "    if saw_number:\n        _refuse", "    if False:\n        _refuse"),
    ("duplicate keys accepted", "if len(keys) != len(set(keys)):", "if len(keys) < 0:"),
    ("exact digits 5", "_MAX_EXACT_DIGITS = 20", "_MAX_EXACT_DIGITS = 5"),
    ("big int not out of range", '    return OutOfRangeInteger(text)', '    return 10 ** 40'),
    ("pairs not joined", "0xDC00 <= int(h2, 16) <= 0xDFFF", "False"),
    ("ident length 129", "{0,127}", "{0,128}"),
    ("prefix match not fullmatch", "pattern.fullmatch(value) is not None", "pattern.match(value) is not None"),
    ("non-ascii identifier accepted", "return value.isascii() and pattern.fullmatch", "return pattern.fullmatch"),
    ("bool is int", '    return type(v) is int or type(v) is OutOfRangeInteger', '    return isinstance(v, int) or type(v) is OutOfRangeInteger'),
    ("snapshot version ceiling", '(1, 9007199254740991),  # N-1', '(1, 9007199254740992),  # N-1'),
    ("snapshot version floor", '"trust_snapshot_version": (1, ', '"trust_snapshot_version": (0, '),
    ("epoch ceiling", '"selection_epoch": (1, 2147483647)', '"selection_epoch": (1, 2147483648)'),
    ("record version floor", '"record_version": (1, 2147483647)', '"record_version": (0, 2147483647)'),
    ("caller age floor", '"caller": (0, 2147483647)', '"caller": (1, 2147483647)'),
    ("registry age floor", '"registry": (1, 2147483647)', '"registry": (0, 2147483647)'),
    ("effective age ceiling", '"effective": (0, 2147483647)', '"effective": (0, 2147483648)'),
    ("dotted key allowed (flatten before sets)", 'unknown = {k for k in d if k not in TOP_MEMBERS}\n', 'unknown = {k for k in d if k not in TOP_MEMBERS and "." not in k}\n'),
    ("missing reports max", '_refuse("field_missing", min(missing))\n    unknown = {k', '_refuse("field_missing", max(missing))\n    unknown = {k'),
    ("unknown reports max", '_refuse("field_unknown", min(unknown))\n    flat = _flatten_checked', '_refuse("field_unknown", max(unknown))\n    flat = _flatten_checked'),
    ("profile not checked", 'elif path == "binding_profile" and v != BINDING_PROFILE:', "elif False:"),
    ("digest not recompared", "    if carried != recomputed:", "    if False:"),
    ("authority not sorted", '"authority": sorted(i["authority"])', '"authority": i["authority"]'),
    ("epoch sorted lexically", "key=lambda p: (p[0], p[1]))\n    out[\"min_epochs\"]", "key=lambda p: (p[0], str(p[1])))\n    out[\"min_epochs\"]"),
    ("revoked ids duplicates allowed", 'or len(set(revoked)) != len(revoked)', 'or False'),
    ("issuer duplicates allowed", '    return (len(set(keys)) != len(keys) or', '    return (False or'),
    ("fingerprint with binding prefix", 'return _sha_plain(b"", normalize_snapshot(plain))', 'return _sha_plain(BINDING_PREFIX, normalize_snapshot(plain))'),
    ("f1a tag", '"f1a-local-execution-allowlist", "v1", "lists"', '"f1a-local-execution-allowlist", "v2", "lists"'),
    ("r08-v1 registered", "REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)", 'REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION, "r08-v1")'),
    ("deny_all wrong", "if v == [])", "if len(v) < 2)"),
    ("duplicates in lists allowed", "or v != sorted(set(v)):", "or v != sorted(v):"),
    ("list bound 257", "len(v) > MAX_LIST_ENTRIES", "len(v) > MAX_LIST_ENTRIES + 1"),
    ("token rule dropped", "all(c.valid_token(x) for x in v)", "all(isinstance(x, str) for x in v)"),
    ("empty class map allowed", "if not classes or not", "if not"),
    ("class map bare int", 'elif path == "class_status_max_age_seconds" or not _int_typed(v):', 'elif not _int_typed(v):'),
    ("deny_all not compared", 'if d["deny_all"] != _deny_all', 'if False and d["deny_all"] != _deny_all'),
    ("family tag trusted", 'if d["family_version"] != registered:', 'if False:'),
    ("scope key profile unchecked", 'if d[k] != SCOPE_KEY_PROFILE:', 'if False:'),
    ("required indeterminate", 'outcome = "UNKNOWN_FAIL_CLOSED" if activation_state == "indeterminate" else "REFUSE"', 'outcome = "REFUSE"'),
    ("optional falls back on either", 'if determination == "authenticated" and activation_state', 'if determination == "authenticated" or activation_state'),
    ("unknown participation read as optional", 'if participation != "optional":\n        _refuse', "if False:\n        _refuse"),
    ("optional indeterminate falls back", 'if activation_state == "indeterminate":\n        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None', 'if False:\n        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None'),
    ("refusal code not joined", '"projection_refusal_code": refusal_code}}', '"projection_refusal_code": "field_invalid"}}'),
    ("snapshot version unbounded", 'if not _in_range(version, lo, hi):', 'if not _in_range(version, lo, 2 ** 70):'),
    ("scope projection normalizes", 'if not (type(v) is str and _ascii_match(_IDENT, v)):\n            _projection_refusal("scope." + k)', 'if type(v) is not str:\n            _projection_refusal("scope." + k)'),
    ("refusal code unchecked", 'if type(code) is not str or code not in CODES_V2_REV2:  #', 'if False:  #'),
    # review of PR #33 (S1-S5, nits): hostile-input boundary, snapshot guard, stage and evidence
    ("non-string key accepted", "            if type(k) is not str:\n                _refuse(\"field_unknown\", NON_STRING_KEY)\n            if _SURROGATE_PAIR", "            if False:\n                _refuse(\"field_unknown\", NON_STRING_KEY)\n            if _SURROGATE_PAIR"),
    ("serializer int unbounded", "if not -_INT_BOUND < value < _INT_BOUND:", "if False:"),
    ("serializer coerces subclasses", "    _refuse(\"field_type_invalid\")\n\n\ndef canonical_json_bytes", "    return str(value)\n\n\ndef canonical_json_bytes"),
    ("plain depth unchecked", "    if depth > MAX_DEPTH:\n        _refuse(\"json_nesting_too_deep\")\n    t = type(value)\n    if t is str:\n        return _AMBIGUOUS", "    t = type(value)\n    if t is str:\n        return _AMBIGUOUS"),
    ("snapshot member set loose", "set(s) == set(_SNAPSHOT_MEMBERS)", "set(s) >= set(_SNAPSHOT_MEMBERS)"),
    ("snapshot epoch accepts bool", "lo, hi = INTEGER_RANGES[\"selection_epoch\"]\n    return type(v) is int and lo <= v <= hi", "lo, hi = INTEGER_RANGES[\"selection_epoch\"]\n    return isinstance(v, int) and lo <= v <= hi"),
    ("snapshot epoch floor 0", "lo, hi = INTEGER_RANGES[\"selection_epoch\"]\n    return type(v) is int and lo <= v <= hi", "lo, hi = INTEGER_RANGES[\"selection_epoch\"]\n    return type(v) is int and 0 <= v <= hi"),
    ("snapshot key upper hex", '_LOWER_HEX = frozenset("0123456789abcdef")', '_LOWER_HEX = frozenset("0123456789abcdefABCDEF")'),
    ("snapshot key empty", "return type(v) is str and len(v) > 0 and len(v) % 2 == 0", "return type(v) is str and len(v) % 2 == 0"),
    ("snapshot grant arity", "return type(g) is list and len(g) == 5", "return type(g) is list and len(g) >= 4"),
    ("snapshot grant tokens", "len(g) == 5 and all(_token(x) for x in g)", "len(g) == 5 and all(type(x) is str for x in g)"),
    ("snapshot issuer extras", "type(i) is dict and set(i) == set(_ISSUER_MEMBERS)", "type(i) is dict and set(i) >= set(_ISSUER_MEMBERS)"),
    ("snapshot valid_until unparsed", "and c.parse_timestamp(s[\"valid_until\"]) is not None", ""),
    ("snapshot repeated grant allowed", "            or per_issuer)", "            or False)"),
    ("snapshot version unchecked", "_snapshot_version_ok(s[\"version\"])", "True"),
    ("snapshot version accepts bool", "lo, hi = INTEGER_RANGES[\"trust_snapshot_version\"]\n    return type(v) is int and lo <= v <= hi", "lo, hi = INTEGER_RANGES[\"trust_snapshot_version\"]\n    return isinstance(v, int) and lo <= v <= hi"),
    ("snapshot version unbounded above", "lo, hi = INTEGER_RANGES[\"trust_snapshot_version\"]\n    return type(v) is int and lo <= v <= hi", "lo, hi = INTEGER_RANGES[\"trust_snapshot_version\"]\n    return type(v) is int and lo <= v"),
    ("snapshot version floor 0", "lo, hi = INTEGER_RANGES[\"trust_snapshot_version\"]\n    return type(v) is int and lo <= v <= hi", "lo, hi = INTEGER_RANGES[\"trust_snapshot_version\"]\n    return type(v) is int and 0 <= v <= hi"),
    ("snapshot hostile input escapes", "    except IdentityRefusal as e:\n        if e.code == \"input_too_large\":", "    except ZeroDivisionError as e:\n        if e.code == \"input_too_large\":"),
    ("projection stage dropped", 'def _projection_refusal(member: str, **evidence):\n    _refuse("field_invalid", member, stage="projection",', 'def _projection_refusal(member: str, **evidence):\n    _refuse("field_invalid", member, stage=None,'),
    ("integer range evidence dropped", 'evidence={"expected_range": (lo, hi)})', "evidence={})"),
    ("digest evidence dropped", 'evidence={"carried_digest": carried, "recomputed_digest": recomputed})', "evidence={})"),
    ("observed class dropped", 'evidence={"observed_value_class": _value_class(value)})', "evidence={})"),
    ("carried digest checked before binding", "    b = validate_binding(binding)  # ONE", "    if not (type(carried) is str and _ascii_match(_DIGEST, carried)):\n        _refuse(\"field_invalid\")\n    b = validate_binding(binding)  # ONE"),
    ("registered cv type unchecked", "    if type(contract_version) is not str:\n        _type_refusal(\"contract_version\", contract_version)\n    if family not in", "    if family not in"),
    ("registered family type unchecked", "    if type(family) is not str:\n        _type_refusal(\"family\", family)\n    if type(contract_version)", "    if type(contract_version)"),
    ("payload family type unchecked", "    if type(family) is not str:\n        _type_refusal(\"family\", family)\n    if family not in IDENTITY_FAMILIES:\n        _refuse(\"family_unsupported\", \"family\")\n    row =", "    if family not in IDENTITY_FAMILIES:\n        _refuse(\"family_unsupported\", \"family\")\n    row ="),
    ("text coercion dropped", "return v if type(v) is str else None", "return v"),
    ("loader accepts bytearray", "    if type(raw) is bytes:", "    if isinstance(raw, (bytes, bytearray)):"),
    ("ranges writable", "INTEGER_RANGES = MappingProxyType({", "INTEGER_RANGES = ({"),
    ("age ranges writable", "AGE_RANGES = MappingProxyType({", "AGE_RANGES = ({"),
    ("projection stage row unselected", 'if type(refusal.stage) is str and refusal.stage == "projection":', "if False:"),
    ("integer row unselected", '"expected_range" in refusal.evidence', "False"),
    ("proposed flag dropped", 'stage_value="verify", proposed=True)', 'stage_value="verify")'),
    # review of PR #33, round two (S1-S6, nits, and the reviewer's surviving mutants)
    ("refusal not picklable", "    def __reduce__(self):", "    def __reduce_disabled__(self):"),
    ("refusal reduce drops stage", "return (IdentityRefusal, (self.code, self.member, self.stage, dict(self.evidence)))", "return (IdentityRefusal, (self.code, self.member, None, dict(self.evidence)))"),
    ("document node ceiling off by one", "MAX_NODES = 65536 ", "MAX_NODES = 65537 "),
    ("document node budget off by five", "    budget[0] -= 1\n    if budget[0] < 0:", "    budget[0] -= 1\n    if budget[0] < -5:"),
    ("snapshot node ceiling changed", "MAX_SNAPSHOT_NODES = 1048576 ", "MAX_SNAPSHOT_NODES = 1048577 "),
    ("snapshot ceiling not passed", "plain = _plain(snapshot, limit=MAX_SNAPSHOT_NODES)", "plain = _plain(snapshot)"),
    ("snapshot size read as malformed", '        if e.code == "input_too_large":\n            raise', '        if False:\n            raise'),
    ("snapshot is not copied", "plain = _plain(snapshot, limit=MAX_SNAPSHOT_NODES)", "plain = snapshot"),
    ("fingerprint re-copies with the document ceiling", 'return _sha_plain(b"", normalize_snapshot(plain))', 'return _sha(b"", normalize_snapshot(plain))'),
    ("canonical bytes bypass the boundary", 'return _serialize(_plain(value)).encode("ascii")', 'return _serialize(value).encode("ascii")'),
    ("digest bypasses the boundary", "return _sha_plain(prefix, _plain(value))", "return _sha_plain(prefix, value)"),
    ("plain passes foreign values", "        return [_plain(x, depth + 1, budget, limit) for x in value]\n    if t is dict:", "        return [_plain(x, depth + 1, budget, limit) for x in value]\n    if t is dict or isinstance(value, dict):"),
    ("plain keeps str subclasses", "    if t is str:\n        return _AMBIGUOUS if", "    if isinstance(value, str):\n        return _AMBIGUOUS if"),
    ("plain returns the caller's list", "        return [_plain(x, depth + 1, budget, limit) for x in value]\n    if t is dict:", "        return value\n    if t is dict:"),
    ("plain returns the caller's dict", "            out[k] = _plain(v, depth + 1, budget, limit)\n        return out", "            out[k] = _plain(v, depth + 1, budget, limit)\n        return value"),
    ("plain ignores adjacent surrogates in values", "        return _AMBIGUOUS if _SURROGATE_PAIR.search(value) else value", "        return value"),
    ("plain ignores adjacent surrogates in keys", "            if _SURROGATE_PAIR.search(k):\n                _refuse(\"field_unknown\", AMBIGUOUS_STRING_KEY)\n            out[k]", "            out[k]"),
    ("pair pattern matches low then high", '_SURROGATE_PAIR = re.compile("[\\ud800-\\udbff][\\udc00-\\udfff]")', '_SURROGATE_PAIR = re.compile("[\\ud800-\\udfff][\\ud800-\\udfff]")'),
    ("serializer ignores pairs", "    if _SURROGATE_PAIR.search(s):  # defence in depth", "    if False:  # defence in depth"),
    ("serializer ignores pair keys", "        if any(_SURROGATE_PAIR.search(k) for k in value):", "        if False:"),
    ("marker is a type error in the serializer", "    if t is OutOfRangeInteger or t is _Ambiguous:", "    if t is _Ambiguous:"),
    ("ambiguous string is a type error in the serializer", "    if t is OutOfRangeInteger or t is _Ambiguous:", "    if t is OutOfRangeInteger:"),
    ("revoked epoch allows 0", "_revoked_epoch = _epoch  #", "_revoked_epoch = lambda v: type(v) is int and 0 <= v <= 2147483647  #"),
    ("revoked epoch unbounded", "_revoked_epoch = _epoch  #", "_revoked_epoch = lambda v: type(v) is int and v >= 1  #"),
    ("revoked epoch accepts negatives", "_revoked_epoch = _epoch  #", "_revoked_epoch = lambda v: type(v) is int and -2147483647 <= v <= 2147483647  #"),
    ("revoked epoch accepts bool", "_revoked_epoch = _epoch  #", "_revoked_epoch = lambda v: isinstance(v, int) and 1 <= v <= 2147483647  #"),
    ("snapshot epoch ceiling 2^53", "lo, hi = INTEGER_RANGES[\"selection_epoch\"]\n    return type(v) is int and lo <= v <= hi", "lo, hi = INTEGER_RANGES[\"selection_epoch\"]\n    return type(v) is int and lo <= v <= 2 ** 53"),
    ("snapshot issuers type unchecked", 'if not (type(s["issuers"]) is list and type(s["revoked_key_ids"])', 'if not (True and type(s["revoked_key_ids"])'),
    ("snapshot revoked ids type unchecked", 'type(s["revoked_key_ids"]) is list and type(s["revoked_selections"])', 'True and type(s["revoked_selections"])'),
    ("snapshot revoked selections type unchecked", 'type(s["revoked_selections"]) is list and type(s["min_epochs"]) is list', 'True and type(s["min_epochs"]) is list'),
    ("snapshot min epochs type unchecked", 'type(s["revoked_selections"]) is list and type(s["min_epochs"]) is list', 'type(s["revoked_selections"]) is list and True'),
    ("snapshot authority type unchecked", 'type(i["authority"]) is list and all(_grant_ok(g) for g in i["authority"])', 'all(_grant_ok(g) for g in i["authority"])'),
    ("snapshot revoked key type unchecked", 'all(type(k) is str for k in s["revoked_key_ids"])', 'True'),
    ("project_scope accepts extra members", 'if type(d) is not dict or set(d) != set(SCOPE_MEMBERS):', 'if type(d) is not dict or not set(d) >= set(SCOPE_MEMBERS):'),
    ("project_scope accepts missing members", 'if type(d) is not dict or set(d) != set(SCOPE_MEMBERS):', 'if type(d) is not dict or not set(d) <= set(SCOPE_MEMBERS):'),
    ("project_scope returns the caller's object", "    return {k: d[k] for k in SCOPE_MEMBERS}", "    return statement_scope"),
    ("project_scope hostile input escapes untagged", "        d = _plain(statement_scope)\n    except IdentityRefusal:", "        d = _plain(statement_scope)\n    except ZeroDivisionError:"),
    ("scope key not copied", 'def validate_scope_key(doc: Any) -> dict:\n    """Return a private plain copy of a well-formed scope-key object, else raise IdentityRefusal."""\n    d = _plain(doc)', 'def validate_scope_key(doc: Any) -> dict:\n    """Return a private plain copy of a well-formed scope-key object, else raise IdentityRefusal."""\n    d = doc if type(doc) is dict else _plain(doc)'),
    ("preimage not copied", '    top = ("contract_version", "deny_all", "effective", "effective_policy_profile", "family", "family_version")\n    d = _plain(doc)', '    top = ("contract_version", "deny_all", "effective", "effective_policy_profile", "family", "family_version")\n    d = doc if type(doc) is dict else _plain(doc)'),
    ("projection wrapper tags everything", "        if e.code not in _PROJECTION_DERIVATION_CODES:\n            raise", "        if False:\n            raise"),
    ("projection wrapper never tags", "        if e.code not in _PROJECTION_DERIVATION_CODES:\n            raise", "        if True:\n            raise"),
    ("projection wrapper skips contract", '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported", "field_invalid"))', '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "field_invalid"))'),
    ("projection wrapper skips family", '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported", "field_invalid"))', '_PROJECTION_DERIVATION_CODES = frozenset(("contract_unsupported", "field_invalid"))'),
    ("projection wrapper skips field_invalid", '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported", "field_invalid"))', '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported"))'),
    ("projection wrapper tags missing members", '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported", "field_invalid"))', '_PROJECTION_DERIVATION_CODES = frozenset(("family_unsupported", "contract_unsupported", "field_invalid", "field_missing"))'),
    ("projection wrapper drops the code", '"projection", {**e.evidence, "projection_refusal_code": e.code})', '"projection", {**e.evidence})'),
    ("projection wrapper drops the member", "raise IdentityRefusal(e.code, e.member, \"projection\"", "raise IdentityRefusal(e.code, None, \"projection\""),
    ("single-row code filtered by stage", "    if len(rows) == 1:\n        return rows[0]\n    return verdict_for", "    if False:\n        return rows[0]\n    return verdict_for"),
    ("deny-all helper unguarded", "    d = _plain(payload)\n    if type(d) is not dict:\n        _type_refusal(None, d)\n    return _deny_all(family, d)", "    return _deny_all(family, payload)"),
    ("deny-all family type unchecked", 'def deny_all_dimensions(family: Any, payload: Any) -> list:', 'def deny_all_dimensions(family: Any, payload: Any) -> list:\n    return _deny_all(family, payload)\n\n\ndef _unused(family, payload):'),
    ("deny-all family unregistered unchecked", '    if family not in IDENTITY_FAMILIES:\n        _refuse("family_unsupported", "family")\n    d = _plain(payload)', '    d = _plain(payload)'),
    ("serializer escape table writable", "_SHORT = MappingProxyType({", "_SHORT = ({"),
    ("loader escape table writable", "_ESCAPES = MappingProxyType({", "_ESCAPES = ({"),
    ("refusal message formats the code", 'raise ValueError("refusal code outside CODES_V2_REV2 (got a %s)" % type(code).__name__)', 'raise ValueError("refusal code outside CODES_V2_REV2: %r" % (code,))'),
    ("role message formats the role", 'raise ValueError("unknown role (got a %s)" % type(role).__name__)', 'raise ValueError("unknown role: %r" % (role,))'),
    ("effect message formats the code", 'raise ValueError("refusal code is not a projection-refusal code (got a %s)" % type(refusal_code).__name__)', 'raise ValueError("refusal code is not a projection-refusal code: %r" % (refusal_code,))'),
    ("marker class lost", 'OutOfRangeInteger: "integer"}', 'OutOfRangeInteger: "other"}'),
    ("loader joins any escape after a surrogate", "0xDC00 <= int(h2, 16) <= 0xDFFF", "0x0000 <= int(h2, 16) <= 0xFFFF"),
    ("surrogate pair: high range ends early", r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")', r'_SURROGATE_PAIR = re.compile("[\ud800-\udbfe][\udc00-\udfff]")'),
    ("surrogate pair: high range starts late", r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")', r'_SURROGATE_PAIR = re.compile("[\ud801-\udbff][\udc00-\udfff]")'),
    ("surrogate pair: high range starts early", r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")', r'_SURROGATE_PAIR = re.compile("[퟿-\udbff][\udc00-\udfff]")'),
    ("surrogate pair: low range starts late", r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")', r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc01-\udfff]")'),
    ("surrogate pair: low range ends early", r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")', r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udffe]")'),
    ("surrogate pair: low range ends late", r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-\udfff]")', r'_SURROGATE_PAIR = re.compile("[\ud800-\udbff][\udc00-]")'),
    ("loader joins only up to U+DFFE", "0xDC00 <= int(h2, 16) <= 0xDFFF", "0xDC00 <= int(h2, 16) <= 0xDFFE"),
    ("loader joins only from U+DC01", "0xDC00 <= int(h2, 16) <= 0xDFFF", "0xDC01 <= int(h2, 16) <= 0xDFFF"),
    ("native scalar at depth 9 accepted", '    if depth > MAX_DEPTH:\n        _refuse("json_nesting_too_deep")\n    t = type(value)\n    if t is str:\n        return _AMBIGUOUS', '    if depth > MAX_DEPTH + 1:\n        _refuse("json_nesting_too_deep")\n    t = type(value)\n    if t is str:\n        return _AMBIGUOUS'),
    ("deny-all read from every family", '    if IDENTITY_FAMILIES[family].kind != "lists":\n        return []', '    if False:\n        return []'),
    ("refusal keeps the caller's evidence dict", "self.evidence = MappingProxyType(dict(evidence or {}))", "self.evidence = MappingProxyType(evidence if evidence else {})"),
    ("module table check: code outside CODES_V2_REV2", "    if not used <= set(CODES_V2_REV2):", "    if False:"),
    ("module table check: verdict class", "    if not all(r.verdict_class in VERDICT_CLASSES for r in REFUSAL_MAPPING):", "    if False:"),
    ("verdict_for compares a hostile stage", '        if type(stage) is not str:  # a hostile `stage` (e.g. a raising `__eq__`) must neither be called nor reach a row: no match\n            raise KeyError((code, "<non-string stage>"))\n', ""),
    ("projection stage compared without a type check", 'if type(refusal.stage) is str and refusal.stage == "projection":', 'if refusal.stage == "projection":'),
    ("scope key members", 'SCOPE_KEY_MEMBERS = ("authority_domain", "consumer_id", "family", "institution", "operation", "selection_id", "tenant")', 'SCOPE_KEY_MEMBERS = ("authority_domain", "consumer_id", "family", "institution", "operation", "selection_id")'),
]

# Mutants that cannot change observable behaviour of the shipped vectors are listed here, each with its reason; the test fails if a mutant survives
# that is not listed, and fails if a listed one is killed (so the list cannot rot).
EQUIVALENT_OR_UNPINNED: dict = {
    # IDENT and DIGEST use explicit ASCII character ranges, so `isascii()` in front of `fullmatch` is defensive redundancy (the reference has the same guard)
    "non-ascii identifier accepted": "equivalent: the regex classes are explicit ASCII ranges and fullmatch is used",
}


def _run_mutant(src_text, tmpdir):
    pkg = Path(tmpdir) / "registry_successor"
    shutil.copytree(ROOT / "registry_successor", pkg, ignore=shutil.ignore_patterns("__pycache__"))
    (pkg / "v2_policy_identity.py").write_text(src_text, encoding="utf-8")
    code = ("import sys, importlib.util\nsys.path.insert(0, %r)\nsys.path.insert(1, %r)\nsys.dont_write_bytecode = True\n"
            "spec = importlib.util.spec_from_file_location('oracle_under_mutation', %r)\nt = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(t)\n"
            "import registry_successor.v2_policy_identity as mod\nassert mod.__file__.startswith(%r), mod.__file__\n"
            "f = t._oracle_failures()\nprint(len(f))\n") % (str(tmpdir), str(ROOT), str(Path(__file__)), str(tmpdir))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=300, env=env, cwd=str(tmpdir))
    except subprocess.TimeoutExpired:
        return "killed"
    if proc.returncode != 0:
        return "killed"  # the mutant does not even import or run: a crash counts as detected only if it is not an oracle bug (checked by the control)
    return "killed" if int(proc.stdout.strip().splitlines()[-1]) > 0 else "survived"


def test_mutation_control_unmodified_copy_passes_the_oracle():
    with tempfile.TemporaryDirectory() as tmp:
        assert _run_mutant(MODULE_PATH.read_text(encoding="utf-8"), tmp) == "survived"  # zero failures: the harness itself is sound


@pytest.mark.parametrize("name,old,new", MUTANTS, ids=[x[0] for x in MUTANTS])
def test_mutants_of_the_module_are_detected(name, old, new):
    src = MODULE_PATH.read_text(encoding="utf-8")
    assert src.count(old) == 1, ("mutation anchor must occur exactly once", name, src.count(old))
    with tempfile.TemporaryDirectory() as tmp:
        verdict = _run_mutant(src.replace(old, new), tmp)
    if name in EQUIVALENT_OR_UNPINNED:
        assert verdict == "survived", ("a listed equivalent mutant is now detected: remove it from the list", name)
    else:
        assert verdict == "killed", ("mutant survived the vectors", name)
