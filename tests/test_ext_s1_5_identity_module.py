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
from registry_successor.v2_codes import CODES_V2

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
            m.IdentityRefusal("not_activated")
            fails.append("a code outside CODES_V2 was accepted")
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
            ("revoked epoch negative", lambda s_: s_.update(revoked_selections=[["a", -5]])), ("revoked epoch 0", lambda s_: s_.update(revoked_selections=[["a", 0]])),
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

    for fn in (valid_bindings, invalid_bindings, identifiers, guards, effective, scope_keys, snapshots, projection, spec_rules_not_pinned_by_a_vector, code_boundaries,
               loader_direct, long_literals, malformed_snapshots, hostile_types, stage_and_evidence):
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
            "except m.IdentityRefusal as e:\n    print(e.code)\ntry:\n    m.IdentityRefusal('not_activated')\n    print('CODE_ACCEPTED')\nexcept ValueError:\n    print('code-refused')\n") % str(ROOT)
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
    expected_ids = {i for i, r in rows.items() if r["registry_code"] and not r.get("ruled_additive_code")} - held_back
    assert set(m.MAPPING_BY_ID) == expected_ids and len(m.REFUSAL_MAPPING) == 28
    for row in m.REFUSAL_MAPPING:
        src = rows[row.row_id]
        assert (row.verdict_class, row.registry_code, row.decision_kind, row.retry) == (src["verdict_class"], src["registry_code"], src["decision_kind"], src["retry"])
        assert list(row.evidence_fields) == src["evidence_fields"] and row.stage_value == src.get("stage_value")
        assert row.optional_overlay is ("optional_branch" in src), row.row_id
        assert row.registry_code in CODES_V2 and row.verdict_class in m.VERDICT_CLASSES
        assert row.decision_kind in ("applied", "applied_deny_all", "overlay_not_applied", "required_policy_unavailable")
    # the deferred rows are absent, not silently mapped
    assert not {r.registry_code for r in m.REFUSAL_MAPPING} & {"not_activated", "policy_identity_mismatch", "store_unknown"}
    assert m.verdict_for("trust_snapshot_missing", "verify").verdict_class == "UNKNOWN_FAIL_CLOSED"
    assert m.verdict_for("trust_snapshot_missing", "guard").stage_value == "guard"
    assert m.verdict_for("selection_epoch_stale").verdict_class == "REFUSE_STALE"
    assert m.verdict_for("selection_expired").optional_overlay is True and m.verdict_for("selection_revoked").optional_overlay is False
    with pytest.raises(KeyError):
        m.verdict_for("trust_snapshot_missing")  # two stages: ambiguous without one
    with pytest.raises(KeyError):
        m.verdict_for("policy_identity_mismatch")
    # every code this module can emit has a mapping row
    emitted = set(re.findall(r'_refuse\("([a-z_]+)"', MODULE_PATH.read_text(encoding="utf-8")))
    assert emitted <= {r.registry_code for r in m.REFUSAL_MAPPING}, emitted - {r.registry_code for r in m.REFUSAL_MAPPING}


def test_module_boundaries_are_static_and_checked_from_source_text():
    import ast
    src = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    emitted = set(re.findall(r'_refuse\("([a-z_]+)"', src)) | set(re.findall(r'IdentityRefusal\("([a-z_]+)"', src))
    assert emitted and emitted <= set(CODES_V2)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    for deferred in ("not_activated", "policy_identity_mismatch", "store_unknown", "r08-v2-reasons/2"):
        assert deferred not in literals, deferred  # only the docstring may mention them (it is one long literal, never an exact match)
    assert not names & {"CODES_V2_REV2", "activation_sequence"}
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
    forbidden = ("registry_successor/common.py", "registry_successor/families.py", "registry_successor/decision.py", "registry_successor/v2_codes.py",
                 "docs/conformance/README.md", "tests/golden", "README.md")
    assert not [p for p in diff if p.startswith(forbidden)], diff


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


def test_unmapped_codes_are_the_explicit_remainder_of_codes_v2():
    """DEFERRED (spec 8 carry-forward): the 48-code completeness test is not implemented in this PR; the remainder is pinned so a change is visible."""
    assert m.UNMAPPED_CODES == frozenset((
        "composition_family_unsupported", "composition_operator_unsupported", "composition_record_invalid", "evaluator_mismatch", "evaluator_unsupported",
        "issuer_not_authorized", "issuer_untrusted", "kind_unsupported", "lineage_authority_unavailable", "record_digest_mismatch", "record_identity_mismatch",
        "selection_consumer_mismatch", "selection_missing", "selection_operation_mismatch", "selection_scope_mismatch", "selection_supersession_invalid",
        "selection_withdrawn", "signature_algorithm_unsupported", "signature_invalid", "signature_missing", "supersession_invalid", "time_unavailable",
        "trust_snapshot_version_stale", "verifier_unavailable"))
    assert m.UNMAPPED_CODES | {r.registry_code for r in m.REFUSAL_MAPPING} == set(CODES_V2)
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


def test_trust_snapshot_object_adapter_is_deferred_and_the_object_is_refused_not_misread():
    """The fingerprint takes the spec's normalized dict. The verifier's `TrustSnapshot` object is not accepted (and never silently misread); the adapter
    from a verified snapshot (bytes key to lowercase hex, frozensets to sorted pairs, grants to five-token arrays) is DEFERRED to the Registry source PR."""
    from registry_successor.verify import TrustSnapshot
    obj = TrustSnapshot(snapshot_id="snap-example-7", version=7, valid_until="2026-12-01T00:00:00Z", issuers=(), revoked_key_ids=frozenset(),
                        revoked_selections=frozenset(), min_epochs={})
    with pytest.raises(m.IdentityRefusal) as info:
        m.trust_snapshot_fingerprint(obj)
    assert info.value.code == "trust_snapshot_invalid"
    assert not [n for n in dir(m) if "trust_snapshot_from" in n or "adapter" in n.lower()]


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
            {"scope": {1: 2}}, {"issuers": [1]}, [[["a", 10 ** 5000]]]]


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
    ("fingerprint with binding prefix", 'return plain_digest(normalize_snapshot(plain))', 'return binding_digest(normalize_snapshot(plain))'),
    ("f1a tag", '"f1a-local-execution-allowlist", "v1", "lists"', '"f1a-local-execution-allowlist", "v2", "lists"'),
    ("r08-v1 registered", "REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)", 'REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION, "r08-v1")'),
    ("deny_all wrong", "if v == [])", "if len(v) < 2)"),
    ("duplicates in lists allowed", "or v != sorted(set(v)):", "or v != sorted(v):"),
    ("list bound 257", "len(v) > MAX_LIST_ENTRIES", "len(v) > MAX_LIST_ENTRIES + 1"),
    ("token rule dropped", "all(c.valid_token(x) for x in v)", "all(isinstance(x, str) for x in v)"),
    ("empty class map allowed", "if not classes or not", "if not"),
    ("class map bare int", 'elif path == "class_status_max_age_seconds" or not _int_typed(v):', 'elif not _int_typed(v):'),
    ("deny_all not compared", 'if d["deny_all"] != deny_all_dimensions', 'if False and d["deny_all"] != deny_all_dimensions'),
    ("family tag trusted", 'if d["family_version"] != registered:', 'if False:'),
    ("scope key profile unchecked", 'if d[k] != SCOPE_KEY_PROFILE:', 'if False:'),
    ("required indeterminate", 'outcome = "UNKNOWN_FAIL_CLOSED" if activation_state == "indeterminate" else "REFUSE"', 'outcome = "REFUSE"'),
    ("optional falls back on either", 'if determination == "authenticated" and activation_state', 'if determination == "authenticated" or activation_state'),
    ("unknown participation read as optional", 'if participation != "optional":\n        _refuse', "if False:\n        _refuse"),
    ("optional indeterminate falls back", 'if activation_state == "indeterminate":\n        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None', 'if False:\n        return {"effect_outcome": "UNKNOWN_FAIL_CLOSED", "decision_kind": None'),
    ("refusal code not joined", '"projection_refusal_code": refusal_code}}', '"projection_refusal_code": "field_invalid"}}'),
    ("snapshot version unbounded", 'if not _in_range(version, lo, hi):', 'if not _in_range(version, lo, 2 ** 70):'),
    ("scope projection normalizes", 'if not (type(v) is str and _ascii_match(_IDENT, v)):\n            _projection_refusal("scope." + k)', 'if type(v) is not str:\n            _projection_refusal("scope." + k)'),
    ("refusal code unchecked", 'if type(code) is not str or code not in CODES_V2:  #', 'if False:  #'),
    # review of PR #33 (S1-S5, nits): hostile-input boundary, snapshot guard, stage and evidence
    ("non-string key accepted", "            if type(k) is not str:\n                _refuse(\"field_unknown\", NON_STRING_KEY)\n            out[k]", "            if False:\n                _refuse(\"field_unknown\", NON_STRING_KEY)\n            out[k]"),
    ("serializer int unbounded", "if not -_INT_BOUND < value < _INT_BOUND:", "if False:"),
    ("serializer coerces subclasses", "    _refuse(\"field_type_invalid\")\n\n\ndef canonical_json_bytes", "    return str(value)\n\n\ndef canonical_json_bytes"),
    ("plain depth unchecked", "    if depth > MAX_DEPTH:\n        _refuse(\"json_nesting_too_deep\")\n    t = type(value)\n    if value is None or", "    t = type(value)\n    if value is None or"),
    ("snapshot member set loose", "set(s) == set(_SNAPSHOT_MEMBERS)", "set(s) >= set(_SNAPSHOT_MEMBERS)"),
    ("snapshot epoch accepts bool", "return type(v) is int and 1 <= v < _INT_BOUND", "return isinstance(v, int) and 1 <= v < _INT_BOUND"),
    ("snapshot epoch floor 0", "return type(v) is int and 1 <= v < _INT_BOUND", "return type(v) is int and 0 <= v < _INT_BOUND"),
    ("snapshot key upper hex", '_LOWER_HEX = frozenset("0123456789abcdef")', '_LOWER_HEX = frozenset("0123456789abcdefABCDEF")'),
    ("snapshot key empty", "return type(v) is str and len(v) > 0 and len(v) % 2 == 0", "return type(v) is str and len(v) % 2 == 0"),
    ("snapshot grant arity", "return type(g) is list and len(g) == 5", "return type(g) is list and len(g) >= 4"),
    ("snapshot grant tokens", "len(g) == 5 and all(_token(x) for x in g)", "len(g) == 5 and all(type(x) is str for x in g)"),
    ("snapshot issuer extras", "type(i) is dict and set(i) == set(_ISSUER_MEMBERS)", "type(i) is dict and set(i) >= set(_ISSUER_MEMBERS)"),
    ("snapshot valid_until unparsed", "and c.parse_timestamp(s[\"valid_until\"]) is not None", ""),
    ("snapshot repeated grant allowed", "            or per_issuer)", "            or False)"),
    ("snapshot version unchecked", "_token(s[\"snapshot_id\"]) and _epoch(s[\"version\"])", "_token(s[\"snapshot_id\"]) and True"),
    ("snapshot hostile input escapes", "    except IdentityRefusal:\n        _refuse(\"trust_snapshot_invalid\")\n    if not _snapshot_shape_ok(plain):", "    except ZeroDivisionError:\n        _refuse(\"trust_snapshot_invalid\")\n    if not _snapshot_shape_ok(plain):"),
    ("projection stage dropped", 'def _projection_refusal(member: str, **evidence):\n    _refuse("field_invalid", member, stage="projection",', 'def _projection_refusal(member: str, **evidence):\n    _refuse("field_invalid", member, stage=None,'),
    ("integer range evidence dropped", 'evidence={"expected_range": (lo, hi)})', "evidence={})"),
    ("digest evidence dropped", 'evidence={"carried_digest": carried, "recomputed_digest": recomputed})', "evidence={})"),
    ("observed class dropped", 'evidence={"observed_value_class": _value_class(value)})', "evidence={})"),
    ("carried digest checked before binding", "    recomputed = checked_binding_digest(binding)\n    if not (type(carried) is str", "    if not (type(carried) is str and _ascii_match(_DIGEST, carried)):\n        _refuse(\"field_invalid\")\n    recomputed = checked_binding_digest(binding)\n    if not (type(carried) is str"),
    ("registered cv type unchecked", "    if type(contract_version) is not str:\n        _type_refusal(\"contract_version\", contract_version)\n    if family not in", "    if family not in"),
    ("registered family type unchecked", "    if type(family) is not str:\n        _type_refusal(\"family\", family)\n    if type(contract_version)", "    if type(contract_version)"),
    ("payload family type unchecked", "    if type(family) is not str:\n        _type_refusal(\"family\", family)\n    if family not in IDENTITY_FAMILIES:\n        _refuse(\"family_unsupported\", \"family\")\n    row =", "    if family not in IDENTITY_FAMILIES:\n        _refuse(\"family_unsupported\", \"family\")\n    row ="),
    ("text coercion dropped", "return v if type(v) is str else None", "return v"),
    ("loader accepts bytearray", "    if type(raw) is bytes:", "    if isinstance(raw, (bytes, bytearray)):"),
    ("ranges writable", "INTEGER_RANGES = MappingProxyType({", "INTEGER_RANGES = ({"),
    ("age ranges writable", "AGE_RANGES = MappingProxyType({", "AGE_RANGES = ({"),
    ("projection stage row unselected", 'if refusal.stage == "projection":', "if False:"),
    ("integer row unselected", '"expected_range" in refusal.evidence', "False"),
    ("proposed flag dropped", 'stage_value="verify", proposed=True)', 'stage_value="verify")'),
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
