"""S03 acceptance cases for the local-execution-allowlist record contract (non-authorizing, synthetic, builder-side).

Cases are defined in docs/s03-contract.md section 5 and were committed before registry_contract/validator.py existed.
Digests here are computed by independent helpers in this module, not by the validator, so the digest checks are not
circular. Nothing here populates a registry, wires a record into Runtime, or qualifies anything.

Plan: OCS-REG-PLAN v1.1 S03 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2).
Constitution: cognous-engineering-constitution 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path

import pytest

from registry_contract.validator import (
    REASON_CODES,
    validate_record,
    validate_record_text,
    widening_violations,
)

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_SOURCE = ROOT / "baseline" / "execution-runtime" / "engine" / "safe_executor.py"
PACKAGE = ROOT / "registry_contract"

RUNTIME_COMMIT = "ec728da6dc301a664b331ac8986afd6e850a1273"
RUNTIME_BLOB = "2fc880dae37eac76e5074533435740ce0684209d"
RUNTIME_SHA256 = "sha256:940e781934542a7acd7bbe2f6833f9d329325d94b49425afd9d2bedcf23c5b68"
EVALUATOR_ID = "engine.safe_executor.LocalExecutionPolicy.check"
SUPPLIES = ["allowed_actions", "allowed_adapters", "allowed_units"]
OTHER_BLOB = "0" * 40
OTHER_SHA = "sha256:" + "0" * 64


def canon(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha(value) -> str:
    return "sha256:" + hashlib.sha256(canon(value)).hexdigest()


def seal(rec: dict) -> dict:
    rec["data_digest"] = sha(rec["data"])
    body = {k: v for k, v in rec.items() if k != "record_digest"}
    rec["record_digest"] = sha(body)
    return rec


def base(version: int = 1) -> dict:
    rec = {
        "record_type": "local-execution-allowlist",
        "contract_version": "s03-v1",
        "record_id": "lep.allowlist.synthetic",
        "record_version": version,
        "status": "active",
        "non_authorizing": True,
        "supersedes": None,
        "source": {
            "repository": "cogno-us/cognous-execution-runtime",
            "commit": RUNTIME_COMMIT,
            "path": "engine/safe_executor.py",
            "blob_id": RUNTIME_BLOB,
            "sha256": RUNTIME_SHA256,
            "field_lines": "358-372",
            "check_lines": "417-424",
        },
        "applicability": {"runtime_source_blob_id": RUNTIME_BLOB},
        "evaluator": {"evaluator_id": EVALUATOR_ID, "binding": "registered-code-reference", "supplies": list(SUPPLIES)},
        "data": {
            "allowed_units": ["USD"],
            "allowed_adapters": ["urn:cognous:adapter:synthetic-refund"],
            "allowed_actions": ["refund.issue"],
        },
        "data_digest": "",
        "provenance": {
            "decision_ref": "docs/decisions/2026-10-24-s03-authorization.md",
            "authored_at": "2026-10-24T12:00:00Z",
            "authored_by": "synthetic test fixture",
        },
        "record_digest": "",
    }
    if version > 1:
        prev = seal(base(version - 1))
        rec["supersedes"] = {
            "record_id": rec["record_id"],
            "record_version": version - 1,
            "record_digest": prev["record_digest"],
        }
    return seal(rec)


def ctx(**over) -> dict:
    c = {"runtime_source_blob_id": RUNTIME_BLOB, "runtime_source_sha256": RUNTIME_SHA256, "latest_known_version": 1}
    c.update(over)
    return c


def make(mut=None, version: int = 1, reseal: bool = True) -> dict:
    rec = base(version)
    if mut:
        mut(rec)
    return seal(rec) if reseal else rec


def refused(record, context, reason):
    result = validate_record(record, context)
    assert (result.outcome, result.reason) == ("REFUSE", reason), result


# ---------------------------------------------------------------- P: positive

def test_P1_valid_active_record_accepted():
    result = validate_record(make(), ctx())
    assert (result.outcome, result.reason) == ("ACCEPT", None)


def test_P2_v2_superseding_v1_accepted():
    result = validate_record(make(version=2), ctx(latest_known_version=2))
    assert (result.outcome, result.reason) == ("ACCEPT", None)


def test_P3_key_order_does_not_change_outcome_or_digests():
    rec = make()
    text = json.dumps(rec, sort_keys=False)
    reversed_text = json.dumps(dict(reversed(list(rec.items()))))
    a = validate_record_text(text, ctx())
    b = validate_record_text(reversed_text, ctx())
    assert (a.outcome, b.outcome) == ("ACCEPT", "ACCEPT")
    assert sha(json.loads(text)["data"]) == sha(json.loads(reversed_text)["data"]) == rec["data_digest"]


def test_P4_multi_entry_sorted_lists_accepted():
    def mut(r):
        r["data"] = {
            "allowed_units": ["EUR", "GBP", "USD"],
            "allowed_adapters": ["urn:a", "urn:b"],
            "allowed_actions": ["refund.issue", "refund.preview"],
        }
    assert validate_record(make(mut), ctx()).outcome == "ACCEPT"


def test_P5_deterministic_and_non_mutating():
    rec = make()
    before = copy.deepcopy(rec)
    first = validate_record(rec, ctx())
    second = validate_record(rec, ctx())
    assert first == second
    assert rec == before


def test_P6_example_record_ships_proposed_and_is_refused_until_changed():
    example = json.loads((ROOT / "docs" / "s03-example-record.json").read_text(encoding="utf-8"))
    refused(example, ctx(), "status_not_active")
    example["status"] = "active"
    assert validate_record(seal(example), ctx()).outcome == "ACCEPT"


# ---------------------------------------------------------------- N: negative

@pytest.mark.parametrize("status", ["proposed", "superseded", "withdrawn"])
def test_N1_status_not_active(status):
    refused(make(lambda r: r.update(status=status)), ctx(), "status_not_active")


def test_N2_data_altered_without_redigest():
    rec = make()
    rec["data"]["allowed_actions"] = ["refund.issue", "refund.zzz"]
    refused(rec, ctx(), "digest_mismatch")


def test_N3_record_digest_altered():
    rec = make()
    rec["record_digest"] = "sha256:" + "1" * 64
    refused(rec, ctx(), "digest_mismatch")


def test_N3b_other_field_altered_without_redigest():
    rec = make()
    rec["provenance"]["authored_by"] = "someone else"
    refused(rec, ctx(), "digest_mismatch")


@pytest.mark.parametrize("field,value", [
    ("evaluator_id", "engine.safe_executor.Other.check"),
    ("binding", "script"),
])
def test_N4_evaluator_unsupported(field, value):
    refused(make(lambda r: r["evaluator"].update({field: value})), ctx(), "evaluator_unsupported")


@pytest.mark.parametrize("supplies", [
    SUPPLIES + ["max_amount"],
    ["allowed_actions", "allowed_adapters"],
    ["allowed_units", "allowed_adapters", "allowed_actions"],  # right members, not the canonical order
    [],
])
def test_N5_supply_list_must_be_exact(supplies):
    refused(make(lambda r: r["evaluator"].update(supplies=supplies)), ctx(), "evaluator_unsupported")


def test_N6_not_applicable():
    def mut(r):
        r["applicability"]["runtime_source_blob_id"] = OTHER_BLOB
        r["source"]["blob_id"] = OTHER_BLOB
    refused(make(mut), ctx(), "not_applicable")


def test_N7_source_mismatch():
    refused(make(), ctx(runtime_source_sha256=OTHER_SHA), "source_mismatch")
    refused(make(lambda r: r["source"].update(blob_id=OTHER_BLOB)), ctx(), "source_mismatch")


@pytest.mark.parametrize("rec_version,latest", [(1, 2), (3, 2)])
def test_N8_version_not_latest(rec_version, latest):
    refused(make(version=rec_version), ctx(latest_known_version=latest), "version_not_latest")


def test_N9_non_authorizing_must_be_true():
    refused(make(lambda r: r.update(non_authorizing=False)), ctx(), "record_invalid")


@pytest.mark.parametrize("name,mut,version", [
    ("v1_with_supersedes", lambda r: r.update(supersedes={"record_id": "lep.allowlist.synthetic", "record_version": 1,
                                                             "record_digest": "sha256:" + "2" * 64}), 1),
    ("v2_without_supersedes", lambda r: r.update(supersedes=None), 2),
    ("wrong_id", lambda r: r["supersedes"].update(record_id="lep.allowlist.other"), 2),
    ("wrong_version", lambda r: r["supersedes"].update(record_version=5), 2),
])
def test_N10_supersession_invalid(name, mut, version):
    refused(make(mut, version=version), ctx(latest_known_version=version), "supersession_invalid")


@pytest.mark.parametrize("entry", ["*", "refund.*", "has space", " lead", "trail ", "zero​width", "nul\x00x", "tab\tx", ""])
def test_N11_bad_entries(entry):
    refused(make(lambda r: r["data"].update(allowed_actions=[entry])), ctx(), "record_invalid")


@pytest.mark.parametrize("name,value", [
    ("empty_list", []),
    ("duplicates", ["a", "a"]),
    ("unsorted", ["b", "a"]),
    ("too_many", ["e%04d" % i for i in range(257)]),
    ("too_long", ["x" * 129]),
])
def test_N12_bad_lists(name, value):
    refused(make(lambda r: r["data"].update(allowed_units=value)), ctx(), "record_invalid")


def test_N12b_bounds_are_inclusive():
    def mut(r):
        r["data"]["allowed_units"] = ["e%04d" % i for i in range(256)]
        r["data"]["allowed_actions"] = ["x" * 128]
    assert validate_record(make(mut), ctx()).outcome == "ACCEPT"


@pytest.mark.parametrize("name,mut", [
    ("upper_hex_data_digest", lambda r: r.update(data_digest="sha256:" + "A" * 64)),
    ("no_prefix", lambda r: r.update(record_digest="1" * 64)),
    ("short", lambda r: r.update(record_digest="sha256:abc")),
    ("record_id_upper", lambda r: r.update(record_id="Lep.Allowlist")),
    ("record_id_short", lambda r: r.update(record_id="ab")),
    ("authored_at_offset", lambda r: r["provenance"].update(authored_at="2026-10-24T12:00:00+00:00")),
    ("authored_at_date_only", lambda r: r["provenance"].update(authored_at="2026-10-24")),
    ("version_zero", lambda r: r.update(record_version=0)),
    ("version_negative", lambda r: r.update(record_version=-1)),
    ("commit_short", lambda r: r["source"].update(commit="abc")),
    ("decision_ref_empty", lambda r: r["provenance"].update(decision_ref="")),
    ("status_unknown", lambda r: r.update(status="ACTIVE")),
    ("field_lines_bad", lambda r: r["source"].update(field_lines="358")),
])
def test_N13_invalid_values(name, mut):
    # Applied without resealing: value rules (check 5) come before digest checks (check 6).
    refused(make(mut, reseal=False), ctx(), "record_invalid")


# ---------------------------------------------------------------- M: malformed

@pytest.mark.parametrize("bad", [[], ["a"], "text", 7, 1.5, True])
def test_M1_record_not_an_object(bad):
    refused(bad, ctx(), "record_malformed")


REQUIRED = ["record_type", "contract_version", "record_id", "record_version", "status", "non_authorizing",
            "supersedes", "source", "applicability", "evaluator", "data", "data_digest", "provenance", "record_digest"]


@pytest.mark.parametrize("field", REQUIRED)
def test_M2_required_field_absent(field):
    rec = make()
    del rec[field]
    refused(rec, ctx(), "record_malformed")


@pytest.mark.parametrize("path", [(), ("source",), ("applicability",), ("evaluator",), ("data",), ("provenance",)])
def test_M3_unknown_field_refused_at_every_level(path):
    rec = make()
    target = rec
    for key in path:
        target = target[key]
    target["extra"] = "x"
    refused(rec, ctx(), "record_malformed")


def test_M3b_unknown_field_inside_supersedes():
    rec = make(version=2)
    rec["supersedes"]["extra"] = 1
    refused(rec, ctx(latest_known_version=2), "record_malformed")


@pytest.mark.parametrize("name,mut", [
    ("list_as_string", lambda r: r["data"].update(allowed_units="USD")),
    ("list_as_null", lambda r: r["data"].update(allowed_units=None)),
    ("list_as_object", lambda r: r["data"].update(allowed_units={"USD": 1})),
    ("number_entry", lambda r: r["data"].update(allowed_units=[5])),
    ("null_entry", lambda r: r["data"].update(allowed_units=[None])),
    ("version_string", lambda r: r.update(record_version="1")),
    ("version_bool", lambda r: r.update(record_version=True)),
    ("version_float", lambda r: r.update(record_version=1.0)),
    ("non_authorizing_string", lambda r: r.update(non_authorizing="true")),
    ("data_as_list", lambda r: r.update(data=[])),
    ("source_as_string", lambda r: r.update(source="x")),
    ("supplies_as_string", lambda r: r["evaluator"].update(supplies="allowed_units")),
    ("supersedes_as_string", lambda r: r.update(supersedes="x")),
])
def test_M4_wrong_json_types(name, mut):
    refused(make(mut, reseal=False), ctx(), "record_malformed")


@pytest.mark.parametrize("text", [
    '{"a": 1, "a": 2}',
    '{"record_type": NaN}',
    '{"x": Infinity}',
    json.dumps(base()) + " trailing",
    "",
    "   ",
    "not json",
    "[1, 2",
])
def test_M5_bad_json_text(text):
    result = validate_record_text(text, ctx())
    assert (result.outcome, result.reason) == ("REFUSE", "record_malformed")


def test_M5b_duplicate_key_in_otherwise_valid_text():
    good = json.dumps(base())
    dup = good[:-1] + ', "status": "withdrawn"}'
    assert validate_record_text(good, ctx()).outcome == "ACCEPT"
    result = validate_record_text(dup, ctx())
    assert (result.outcome, result.reason) == ("REFUSE", "record_malformed")


def test_M5c_invalid_utf8_bytes():
    result = validate_record_text(b"\xff\xfe{}", ctx())
    assert (result.outcome, result.reason) == ("REFUSE", "record_malformed")


def test_M5d_bytes_input_accepted_when_valid_utf8():
    assert validate_record_text(json.dumps(base()).encode("utf-8"), ctx()).outcome == "ACCEPT"


@pytest.mark.parametrize("field,value", [("contract_version", "s03-v2"), ("contract_version", ""), ("record_type", "other-family")])
def test_M6_contract_unsupported(field, value):
    refused(make(lambda r: r.update({field: value})), ctx(), "contract_unsupported")


# ---------------------------------------------------------------- X: missing

def test_X1_no_record():
    refused(None, ctx(), "record_missing")


@pytest.mark.parametrize("bad_ctx", [
    None, [], "x",
    {},
    {"runtime_source_blob_id": RUNTIME_BLOB, "runtime_source_sha256": RUNTIME_SHA256},
    ctx(latest_known_version="1"),
    ctx(latest_known_version=True),
    ctx(latest_known_version=0),
    ctx(runtime_source_blob_id=None),
    ctx(runtime_source_sha256=5),
])
def test_X2_context_missing_or_wrong(bad_ctx):
    refused(make(), bad_ctx, "context_missing")


def test_X2b_extra_context_keys_are_refused():
    refused(make(), ctx(extra="x"), "context_missing")


def test_X3_empty_object():
    refused({}, ctx(), "record_malformed")


# ---------------------------------------------------------------- O: order

def _cases():
    def malformed_and_unsupported():
        r = make(lambda r: r.update(contract_version="s03-v2"))
        r["extra"] = 1
        return r, ctx(), "record_malformed"

    def unsupported_and_invalid():
        return make(lambda r: r.update(contract_version="s03-v2", record_id="X"), reseal=False), ctx(), "contract_unsupported"

    def invalid_and_digest():
        rec = make()
        rec["data"]["allowed_units"] = ["b", "a"]
        return rec, ctx(), "record_invalid"

    def digest_and_status():
        rec = make(lambda r: r.update(status="withdrawn"))
        rec["data"]["allowed_units"] = ["EUR"]
        return rec, ctx(), "digest_mismatch"

    def supersession_and_status():
        return make(lambda r: r.update(status="proposed", supersedes={
            "record_id": "lep.allowlist.synthetic", "record_version": 1, "record_digest": "sha256:" + "2" * 64})), ctx(), "supersession_invalid"

    def status_and_version():
        return make(lambda r: r.update(status="withdrawn")), ctx(latest_known_version=2), "status_not_active"

    def version_and_evaluator():
        return make(lambda r: r["evaluator"].update(binding="script")), ctx(latest_known_version=2), "version_not_latest"

    def evaluator_and_applicability():
        def mut(r):
            r["evaluator"]["binding"] = "script"
            r["applicability"]["runtime_source_blob_id"] = OTHER_BLOB
        return make(mut), ctx(), "evaluator_unsupported"

    def applicability_and_source():
        def mut(r):
            r["applicability"]["runtime_source_blob_id"] = OTHER_BLOB
        return make(mut), ctx(runtime_source_sha256=OTHER_SHA), "not_applicable"

    def missing_and_context():
        return None, None, "record_missing"

    def context_and_malformed():
        return {"x": 1}, None, "context_missing"

    return [malformed_and_unsupported, unsupported_and_invalid, invalid_and_digest, digest_and_status,
            supersession_and_status, status_and_version, version_and_evaluator, evaluator_and_applicability,
            applicability_and_source, missing_and_context, context_and_malformed]


@pytest.mark.parametrize("build", _cases(), ids=lambda f: f.__name__)
def test_O1_first_failing_check_wins(build):
    record, context, expected = build()
    refused(record, context, expected)


def test_O1b_reason_codes_are_the_closed_ordered_set():
    assert REASON_CODES == (
        "record_missing", "context_missing", "record_malformed", "contract_unsupported", "record_invalid",
        "digest_mismatch", "supersession_invalid", "status_not_active", "version_not_latest",
        "evaluator_unsupported", "not_applicable", "source_mismatch",
    )


# ---------------------------------------------------------------- L: limitation

def test_L1_integrity_is_not_authenticity():
    """Pinned limitation: a tampered record whose digests were recomputed is ACCEPTED. S03 has no authentication."""
    rec = make(lambda r: r["data"].update(allowed_actions=["attacker.action", "refund.issue"]))
    assert validate_record(rec, ctx()).outcome == "ACCEPT"


# ---------------------------------------------------------------- I: preserved invariants

def _source_lines():
    return RUNTIME_SOURCE.read_text(encoding="utf-8").splitlines()


def test_I1_baseline_pin_and_line_ranges():
    data = RUNTIME_SOURCE.read_bytes()
    assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == RUNTIME_BLOB
    assert "sha256:" + hashlib.sha256(data).hexdigest() == RUNTIME_SHA256
    lines = _source_lines()
    assert lines[361].strip() == "allowed_adapters: frozenset[str]"
    assert lines[362].strip() == "allowed_actions: frozenset[str]"
    assert lines[364].strip() == "allowed_units: frozenset[str]"
    assert lines[357].strip() == "@dataclass(frozen=True)"
    assert lines[358].startswith("class LocalExecutionPolicy")
    assert "op.adapter_id not in self.allowed_adapters" in lines[416]
    assert "op.action_id not in self.allowed_actions" in lines[418]
    assert "op.unit not in self.allowed_units" in lines[422]
    base_record = base()
    assert base_record["source"]["blob_id"] == RUNTIME_BLOB
    assert base_record["source"]["sha256"] == RUNTIME_SHA256


def _policy_class():
    tree = ast.parse(RUNTIME_SOURCE.read_text(encoding="utf-8"))
    return next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LocalExecutionPolicy")


def test_I2_check_raises_in_baseline_order():
    check = next(n for n in _policy_class().body if isinstance(n, ast.FunctionDef) and n.name == "check")
    raises = sorted((n for n in ast.walk(check) if isinstance(n, ast.Raise)), key=lambda n: n.lineno)
    messages = [n.exc.args[0].value for n in raises]
    assert messages == [
        "local institution restriction",
        "local authority-domain restriction",
        "local adapter restriction",
        "local action restriction",
        "local target restriction",
        "local unit restriction",
        "local amount restriction",
        "local adapter supports exactly one effect",
        "local effect-count restriction",
    ]


def _policy(**over):
    from engine.safe_executor import LocalExecutionPolicy
    args = dict(
        allowed_institutions=frozenset({"i"}),
        allowed_authority_domains=frozenset({"d"}),
        allowed_adapters=frozenset({"a"}),
        allowed_actions=frozenset({"x"}),
        allowed_target_prefixes=("urn:t:",),
        allowed_units=frozenset({"USD"}),
        max_amount=1.0,
        max_effects=1,
    )
    args.update(over)
    return LocalExecutionPolicy(**args)


@pytest.mark.parametrize("field", ["allowed_adapters", "allowed_actions", "allowed_units"])
@pytest.mark.parametrize("bad", [["a"], "abc", frozenset({""}), frozenset({1})])
def test_I3_baseline_constructor_still_rejects_bad_values(field, bad):
    with pytest.raises(ValueError):
        _policy(**{field: bad})


def test_I3b_baseline_constructor_accepts_empty_frozenset_so_record_rule_is_stricter():
    assert _policy(allowed_units=frozenset()).allowed_units == frozenset()


def test_I4_dataclass_fields_are_supplied_plus_not_supplied():
    import dataclasses
    from engine.safe_executor import LocalExecutionPolicy
    supplied = {"allowed_units", "allowed_adapters", "allowed_actions"}
    not_supplied = {"allowed_institutions", "allowed_authority_domains", "allowed_target_prefixes", "target_match",
                    "max_amount", "max_effects"}
    assert {f.name for f in dataclasses.fields(LocalExecutionPolicy)} == supplied | not_supplied
    assert set(base()["data"]) == supplied
    assert set(base()["evaluator"]["supplies"]) == supplied


def test_I5_contract_package_is_not_wired_to_runtime_and_reads_no_files():
    forbidden_modules = {"engine", "pathlib", "os", "subprocess", "socket", "shutil", "importlib"}
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not {a.name.split(".")[0] for a in node.names} & forbidden_modules, path
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_modules, path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"open", "eval", "exec", "compile", "__import__"}, path


def test_I6_schema_and_validator_field_names_agree():
    from registry_contract import validator
    schema = json.loads((PACKAGE / "local_execution_allowlist.schema.json").read_text(encoding="utf-8"))
    props = schema["properties"]
    assert set(schema["required"]) == set(props) == set(validator.TOP_LEVEL_FIELDS)
    for name, fields in validator.NESTED_FIELDS.items():
        node = props[name]
        if "oneOf" in node:
            node = next(n for n in node["oneOf"] if n.get("type") == "object")
        assert set(node["required"]) == set(node["properties"]) == set(fields), name


# ---------------------------------------------------------------- W: non-widening

def test_W1_widening_violations():
    caller = {"allowed_units": ["USD", "EUR"], "allowed_adapters": ["a"], "allowed_actions": ["x", "y"]}
    assert widening_violations({"allowed_units": ["USD"], "allowed_adapters": ["a"], "allowed_actions": ["x"]}, caller) == []
    assert widening_violations(dict(caller), caller) == []
    assert widening_violations({"allowed_units": ["USD", "GBP"], "allowed_adapters": ["a", "b"], "allowed_actions": ["x"]},
                               caller) == ["allowed_adapters", "allowed_units"]
    assert widening_violations({"allowed_units": ["USD"], "allowed_adapters": ["a"]}, caller) == ["allowed_actions"]
    assert widening_violations({"allowed_units": ["USD"], "allowed_adapters": ["a"], "allowed_actions": ["x"]},
                               {"allowed_units": ["USD"]}) == ["allowed_actions", "allowed_adapters"]
