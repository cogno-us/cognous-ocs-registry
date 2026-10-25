"""Developer tests for registry_successor.record (R08-S01 lane A). DEVELOPER-TESTED only; not independent qualification."""
import copy
import json

import pytest

import r08_support as s
from registry_successor import common as c
from registry_successor.record import validate_record_text


def check(obj, code=None):
    res = validate_record_text(obj if isinstance(obj, str) else s.dumps(obj))
    if code is None:
        assert res.ok and res.code is None, res
    else:
        assert not res.ok and res.code == code, res
        assert res.record is None and res.record_digest is None
    return res


def reseal(**changes):
    rec = s.make_record()
    body = copy.deepcopy(rec)
    for path, value in changes.items():
        cur = body
        keys = path.split("__")
        for k in keys[:-1]:
            cur = cur[k]
        cur[keys[-1]] = value
    return s.seal_record(body)


def test_valid_record():
    rec = s.make_record()
    res = check(rec)
    assert res.record == rec and res.record_digest == rec["record_digest"]
    assert res.record is not rec


@pytest.mark.parametrize("field", c.F1A_FIELDS)
def test_empty_list_is_valid_deny_all(field):
    check(reseal(**{"payload__" + field: []}))


def test_all_empty_valid():
    body = s.make_record()
    for f in c.F1A_FIELDS:
        body["payload"][f] = []
    check(s.seal_record(body))


@pytest.mark.parametrize("field", c.F1A_FIELDS)
def test_missing_payload_field(field):
    body = s.make_record()
    del body["payload"][field]
    check(s.seal_record(body), "field_missing")


@pytest.mark.parametrize("name", ["status", "extra", "active"])
def test_unknown_top_field(name):
    body = s.make_record()
    body[name] = "active"
    check(s.seal_record(body), "field_unknown")


def test_unknown_nested_fields():
    for sect in ("evaluator", "source", "payload", "provenance"):
        body = s.make_record()
        body[sect]["zzz"] = 1
        check(s.seal_record(body), "field_unknown")
    body = s.make_record(supersedes={"record_id": "f1a-test-record", "record_version": 0,
                                     "record_digest": "sha256:" + "0" * 64, "x": 1})
    check(body, "field_unknown")


@pytest.mark.parametrize("top", ["record_id", "record_version", "non_authorizing", "supersedes", "evaluator", "source",
                                 "payload", "payload_digest", "provenance", "record_digest"])
def test_missing_top_field(top):
    body = s.make_record()
    del body[top]
    check(body, "field_missing")


def test_wrong_types():
    for sect in ("evaluator", "source", "payload", "provenance"):
        body = s.make_record()
        body[sect] = "x"
        check(s.seal_record(body) if sect != "payload" else body, "field_type_invalid")
    check([1, 2], "field_type_invalid")
    check(reseal(payload__allowed_units="unit-a"), "field_type_invalid")
    check(reseal(evaluator__source_blob_id=5), "field_type_invalid")
    check(reseal(provenance__decision_ref=None), "field_type_invalid")
    check(reseal(source__path=1), "field_type_invalid")


@pytest.mark.parametrize("bad", [
    ["b", "a"], ["a", "a"], ["x" * 129], [""], ["a*"], ["a\x00b"], ["a b"], ["a​b"], ["a\nb"], [5], [" "],
])
def test_bad_entries(bad):
    check(reseal(payload__allowed_units=bad), "field_invalid")


def test_entry_boundaries():
    check(reseal(payload__allowed_units=sorted("u%03d" % i for i in range(256))))
    check(reseal(payload__allowed_units=sorted("u%03d" % i for i in range(257))), "field_invalid")
    check(reseal(payload__allowed_units=["x" * 128]))


def test_bad_values():
    check(reseal(record_id="A"), "field_invalid")
    check(reseal(record_id="ab"), "field_invalid")
    check(reseal(record_version=0), "field_invalid")
    check(reseal(record_version=2**31), "field_invalid")
    check(reseal(record_version=True), "field_invalid")
    check(reseal(record_version="1"), "field_invalid")
    check(reseal(non_authorizing=False), "field_invalid")
    check(reseal(non_authorizing=1), "field_invalid")
    check(reseal(evaluator__source_blob_id="abc"), "field_invalid")
    check(reseal(evaluator__source_sha256="sha256:abc"), "field_invalid")
    check(reseal(source__commit="zz"), "field_invalid")
    check(reseal(source__blob_id="A" * 40), "field_invalid")
    check(reseal(source__sha256="x"), "field_invalid")
    check(reseal(source__repository=""), "field_invalid")
    check(reseal(provenance__authored_at="2026-10-25"), "field_invalid")
    check(reseal(provenance__authored_at="2026-13-45T00:00:00Z"), "field_invalid")
    check(reseal(provenance__decision_ref=""), "field_invalid")


def test_bad_digests():
    body = s.make_record()
    body["payload_digest"] = "sha256:" + "0" * 64
    check(body, "digest_mismatch")
    body = s.make_record()
    body["record_digest"] = "sha256:" + "0" * 64
    check(body, "digest_mismatch")
    body = s.make_record()
    body["payload"]["allowed_units"] = ["unit-a"]
    check(body, "digest_mismatch")
    body = s.make_record()
    body["provenance"]["authored_by"] = "someone-else"
    check(body, "digest_mismatch")
    body = s.make_record()
    body["record_digest"] = 7
    check(body, "digest_mismatch")


def test_wrong_evaluator():
    check(reseal(evaluator__evaluator_id="engine.other.check"), "evaluator_unsupported")
    check(reseal(evaluator__binding="arbitrary-expression"), "evaluator_unsupported")


def test_unsupported_contract_kind_family():
    check(reseal(contract_version="s03-v1"), "contract_unsupported")
    check(reseal(contract_version="r08-v2"), "contract_unsupported")
    check(reseal(kind="selection"), "kind_unsupported")
    check(reseal(family="f1b-other"), "family_unsupported")
    body = s.make_record()
    del body["contract_version"]
    check(body, "contract_unsupported")


def test_parse_failures():
    check('{"a":1,"a":2}', "json_duplicate_key")
    check("{not json", "json_malformed")
    check("", "json_malformed")
    base = s.dumps(s.make_record())
    check(base.replace('"record_version": 1', '"record_version": 1.0'), "json_number_unsupported")
    check(base.replace('"record_version": 1', '"record_version": NaN'), "json_number_unsupported")
    check("[" * 20 + "]" * 20, "json_nesting_too_deep")
    check(" " * (c.MAX_DOCUMENT_BYTES + 1), "input_too_large")
    check("\ud800", "input_not_text")
    for bad in (None, b"{}", 5, {"a": 1}):
        res = validate_record_text(bad)
        assert not res.ok and res.code == "input_not_text"


def test_duplicate_key_in_nested_object():
    base = s.dumps(s.make_record())
    check(base.replace('"authored_by": "test-author"', '"authored_by": "a", "authored_by": "b"'), "json_duplicate_key")


def test_supersession():
    ok = s.make_record(record_version=2, supersedes={"record_id": "f1a-test-record", "record_version": 1,
                                                     "record_digest": "sha256:" + "1" * 64})
    check(ok)
    for sup in ({"record_id": "f1a-other-record", "record_version": 1, "record_digest": "sha256:" + "1" * 64},
                {"record_id": "f1a-test-record", "record_version": 2, "record_digest": "sha256:" + "1" * 64},
                {"record_id": "f1a-test-record", "record_version": 3, "record_digest": "sha256:" + "1" * 64},
                {"record_id": "f1a-test-record", "record_version": 1, "record_digest": "bad"},
                {"record_id": "f1a-test-record", "record_version": 0, "record_digest": "sha256:" + "1" * 64}):
        check(s.make_record(record_version=2, supersedes=sup), "supersession_invalid")
    check(s.make_record(supersedes="x"), "field_type_invalid")


def test_check_order_first_failure_wins():
    body = s.make_record(contract_version="zzz", kind="zzz")
    body["extra"] = 1
    check(body, "contract_unsupported")
    body = s.make_record()
    body["extra"] = 1
    body["record_id"] = "A"
    body["record_digest"] = "bad"
    check(body, "field_unknown")
    body = s.make_record(record_id="A")
    check(body, "field_invalid")


def test_determinism():
    text = s.dumps(s.make_record())
    assert validate_record_text(text) == validate_record_text(text)
    bad = s.dumps(s.make_record(kind="x"))
    assert validate_record_text(bad) == validate_record_text(bad)


def test_returned_record_is_a_copy():
    res = validate_record_text(s.dumps(s.make_record()))
    res.record["payload"]["allowed_units"].append("tamper")
    assert validate_record_text(s.dumps(s.make_record())).record["payload"]["allowed_units"] == ["unit-a", "unit-b"]


def test_mutation_sanity_every_field_change_refuses():
    text = s.dumps(s.make_record())
    obj = json.loads(text)
    flips = [("record_id", "other-id"), ("record_version", 2), ("payload_digest", "sha256:" + "2" * 64)]
    for key, value in flips:
        mutated = copy.deepcopy(obj)
        mutated[key] = value
        assert not validate_record_text(s.dumps(mutated)).ok
    mutated = copy.deepcopy(obj)
    mutated["payload"]["allowed_actions"].append("zz-extra")
    assert not validate_record_text(s.dumps(mutated)).ok


def test_status_never_accepted_even_resealed():
    body = copy.deepcopy(s.make_record())
    body["status"] = "active"
    check(s.seal_record(body), "field_unknown")


def test_codes_are_in_closed_set():
    for case in (s.make_record(kind="x"), s.make_record(record_id="A")):
        res = validate_record_text(s.dumps(case))
        assert res.code in c.CODES
