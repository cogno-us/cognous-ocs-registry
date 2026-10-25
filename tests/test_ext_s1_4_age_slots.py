"""EXT-S1-4 tests: F4 `f4-control-plane-age-bounds` and F5 `f5-action-class-age-bounds` integer-second families.
BUILDER_TESTED: builder-authored evidence, not an independently qualified oracle, and no claim of independent qualification.
"""
import hashlib
import itertools
import json
import re
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import families  # noqa: E402
from registry_successor import record as record_mod  # noqa: E402
from registry_successor import v2_age_bounds as a  # noqa: E402
from registry_successor import v2_codes  # noqa: E402

F4 = a.FAMILY_F4
F5 = a.FAMILY_F5
F4K = ("status_max_age_seconds", "approval_max_age_seconds")
F5K = "class_status_max_age_seconds"
MAX = 2147483647

# ---------------------------------------------------------------- source pins
PINS = {
    "docs/r08-v2-contract.md": "64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01",
    "docs/decisions/2026-10-25-adr-ext-s1-1-v1-contract.md": "b9ad06be559bfb99c5e669ca7217d2ee28b62cda7738206c31fd8e6866233b67",
    "docs/decisions/2026-10-25-dr-cp-age-1.md": "10f78e1b735d60d80c5d0354a1dba63dd7935e4b4ad9c9c26cf35ecd49109737",
}
CONTRACT_TEXT = [
    "| `f4-control-plane-age-bounds` (v2) | `status_max_age_seconds`, `approval_max_age_seconds` | strict integer seconds, `min(caller, registry)` per scalar | Control Plane |",
    "| `f5-action-class-age-bounds` (v2) | `class_status_max_age_seconds`: object of `action_class -> int seconds` | per-class `min(caller, registry)` | Control Plane |",
    "No universal five-second floor. No cross-bound among the distinct ages: an individually valid inverted pair is accepted.",
    "An unknown action class, a third F4 key or an empty class map refuses.",
]


def test_sources_are_pinned():
    for rel, digest in PINS.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f"{rel} changed: re-read it, then re-pin"
    text = (ROOT / "docs/r08-v2-contract.md").read_text(encoding="utf-8")
    for line in CONTRACT_TEXT:
        assert line in text, line


def test_bounds_equal_the_dr_cp_age_1_table():
    """The validator carries no private constant: it must equal the table in the decision record."""
    text = (ROOT / "docs/decisions/2026-10-25-dr-cp-age-1.md").read_text(encoding="utf-8")
    rows = {m.group(1): (int(m.group(2)), int(m.group(3))) for m in
            re.finditer(r"^\| (Registry-managed value|Caller value) \| (\d+) \| (\d+) \|", text, re.M)}
    assert rows == {"Registry-managed value": (1, 2147483647), "Caller value": (0, 2147483647)}
    assert (a.AGE_MIN, a.AGE_MAX, a.CALLER_MIN) == (1, MAX, 0) == (rows["Registry-managed value"][0], rows["Registry-managed value"][1], rows["Caller value"][0])
    assert "`AGE_MIN = 1`, `AGE_MAX = 2147483647`" in text
    assert "not an operational setting" in text


# ---------------------------------------------------------------- builders
def p4(**over):
    p = {"status_max_age_seconds": 30, "approval_max_age_seconds": 120}
    p.update(over)
    return p


def p5(m=None):
    return {F5K: {"class-a": 30, "class-b": 600} if m is None else m}


def c4(**over):
    p = {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}
    p.update(over)
    return p


def c5(m=None):
    return {F5K: {"class-a": 60, "class-b": 60, "class-c": 90} if m is None else m}


def rec(pl, family, ok=True):
    body = dict(s.make_record(), family=family, payload=pl)
    return record_mod.RecordResult(ok, None, "", body, body["record_digest"])


def compose4(cl, pl=None, **kw):
    return families.compose_v2(cl, rec(p4() if pl is None else pl, F4), **kw)


def compose5(cl, pl=None, **kw):
    return families.compose_v2(cl, rec(p5() if pl is None else pl, F5), **kw)


def refused(res, code):
    assert (res.ok, res.code, res.effective, res.deny_all) == (False, code, None, False), res


class IntSub(int):
    pass


class StrSub(str):
    pass


BAD_TYPES = [True, False, 1.0, 60.0, float("inf"), float("-inf"), float("nan"), "60", "1", "", None, b"60", bytearray(b"1"), [1], (1,), {},
             IntSub(5), IntSub(0), object(), 1 + 0j]
BELOW = [0, -1, -2, -(2**31), -(10**30)]
ABOVE = [2147483648, 2**31, 2**32, 2**33, 2**34, 2**53, 2**63, 10**30, 10**400]
VALID = [1, 2, 5, 59, 60, 61, 2147483646, 2147483647]


# ---------------------------------------------------------------- registration
def test_registered_in_v2_table_only():
    assert set(families.FAMILIES) == {c.FAMILY_F1A}
    assert {F4, F5} <= set(families.FAMILIES_V2)
    for fam, fields, comp, norm in ((F4, F4K, a.compose_f4, a.normalize_caller_f4), (F5, (F5K,), a.compose_f5, a.normalize_caller_f5)):
        spec = families.lookup_v2(fam)
        assert spec is families.FAMILIES_V2[fam] and spec.family == fam
        assert spec.payload_fields == fields and spec.composer is comp and spec.caller_normalizer is norm
        assert spec.enforcing_component == "control-plane"
        assert families.lookup(fam) is None
        assert families.lookup_for("r08-v1", fam) is None and families.lookup_for("r08-v2", fam) is spec
    assert families.FAMILIES_V2[c.FAMILY_F1A] is families.FAMILIES[c.FAMILY_F1A]
    with pytest.raises(TypeError):
        families.FAMILIES_V2["x"] = families.FAMILIES_V2[F4]


@pytest.mark.parametrize("fam", ["F4-CONTROL-PLANE-AGE-BOUNDS", " f4-control-plane-age-bounds", "f4-control-plane-age-bounds\n", "f4", "f5",
                                 "F5-ACTION-CLASS-AGE-BOUNDS", "f5-action-class-age-bounds ", "f5-action-class-age-bound", None, 4, b"f4", StrSub("x")])
def test_lookup_exact_only(fam):
    assert families.lookup_v2(fam) is None


def test_v1_entry_points_still_refuse_f4_f5():
    for fam, pl in ((F4, p4()), (F5, p5())):
        body = s.seal_record({**s.make_record(), "family": fam, "payload": pl})
        r = record_mod.validate_record_text(json.dumps(body))
        assert (r.ok, r.code) == (False, "family_unsupported")
        refused(families.compose(c4(), rec(pl, fam)), "composition_family_unsupported")
        refused(families.compose_for("r08-v1", c4(), rec(pl, fam)), "composition_family_unsupported")
    refused(families.compose_for("r08-v3", c4(), rec(p4(), F4)), "contract_unsupported")


def test_no_new_codes_and_table_shape():
    assert len(c.CODES) == 46 and len(v2_codes.CODES_V2) == 48
    # every refusal code this module can emit exists in the closed set
    for code in ("field_unknown", "field_missing", "field_type_invalid", "field_invalid", "composition_record_invalid",
                 "composition_caller_invalid", "composition_family_unsupported", "composition_operator_unsupported"):
        assert code in v2_codes.CODES_V2


def test_module_is_pure_and_imports_no_component():
    src = (ROOT / "registry_successor/v2_age_bounds.py").read_text(encoding="utf-8")
    imports = re.findall(r"^(?:from|import) ([\w.]+)", src, re.M)
    assert set(imports) <= {"collections.abc", "typing", "registry_successor", "registry_successor.compose"}, imports
    for banned in ("agent_control_plane", "engine", "open(", "time.", "datetime", "os.", "random"):
        assert banned not in src, banned
    # no amount slot, reserved or inactive, anywhere in the payload field sets
    assert not any("amount" in k for k in a.F4_FIELDS + a.F5_FIELDS)
    assert a.F4_FIELDS == F4K and a.F5_FIELDS == (F5K,)


# ---------------------------------------------------------------- F4 payload
def test_f4_valid():
    assert a.f4_payload_validator(p4()) is None
    assert a.f4_payload_validator({"status_max_age_seconds": 1, "approval_max_age_seconds": 1}) is None


@pytest.mark.parametrize("field", F4K)
@pytest.mark.parametrize("v", BAD_TYPES)
def test_f4_wrong_type_per_field(field, v):
    assert a.f4_payload_validator(p4(**{field: v})) == "field_type_invalid"


@pytest.mark.parametrize("field", F4K)
@pytest.mark.parametrize("v", BELOW + ABOVE)
def test_f4_out_of_range_per_field(field, v):
    assert a.f4_payload_validator(p4(**{field: v})) == "field_invalid"


@pytest.mark.parametrize("field", F4K)
@pytest.mark.parametrize("v", VALID)
def test_f4_boundaries_accepted(field, v):
    assert a.f4_payload_validator(p4(**{field: v})) is None


def test_f4_huge_digit_strings_and_json_numbers_never_become_valid():
    for text in ("9" * 5000, "1e3", "60.0", "-0", "0x10", "٦٠"):
        assert a.f4_payload_validator(p4(status_max_age_seconds=text)) == "field_type_invalid"
    for body in ('{"status_max_age_seconds": 60.0, "approval_max_age_seconds": 60}', '{"status_max_age_seconds": 1e3, "approval_max_age_seconds": 60}',
                 '{"status_max_age_seconds": NaN, "approval_max_age_seconds": 60}', '{"status_max_age_seconds": Infinity, "approval_max_age_seconds": 60}'):
        assert c.load_document(body).code == "json_number_unsupported"
    # a huge JSON integer parses as int and is range-refused, never wrapped or clamped
    v = c.load_document('{"status_max_age_seconds": 1' + "0" * 400 + ', "approval_max_age_seconds": 60}')
    if v.ok:
        assert a.f4_payload_validator(v.value) == "field_invalid"


def test_f4_key_sets():
    assert a.f4_payload_validator({"status_max_age_seconds": 5}) == "field_missing"
    assert a.f4_payload_validator({"approval_max_age_seconds": 5}) == "field_missing"
    assert a.f4_payload_validator({}) == "field_missing"
    for extra in ("identity_max_age_seconds", "mandate_max_age_seconds", "clock_tolerance_seconds", "max_amount", "amount", "max_effects",
                  "class_status_max_age_seconds", "observation_max_age_seconds", "Status_Max_Age_Seconds", "status_max_age_seconds "):
        assert a.f4_payload_validator(p4(**{extra: 5})) == "field_unknown", extra
    for notmap in (None, [], "x", 3, [("status_max_age_seconds", 1)]):
        assert a.f4_payload_validator(notmap) == "field_type_invalid"


def test_f4_unknown_beats_missing_and_type_beats_range():
    assert a.f4_payload_validator({"status_max_age_seconds": 5, "x": 1}) == "field_unknown"
    assert a.f4_payload_validator(p4(status_max_age_seconds=-1, approval_max_age_seconds="1")) == "field_type_invalid"


# ---------------------------------------------------------------- F5 payload
def test_f5_valid():
    assert a.f5_payload_validator(p5()) is None
    assert a.f5_payload_validator(p5({"x": 1})) is None
    assert a.f5_payload_validator(p5({"x": MAX})) is None


@pytest.mark.parametrize("v", BAD_TYPES)
def test_f5_value_wrong_type_per_class(v):
    assert a.f5_payload_validator(p5({"class-a": 30, "class-b": v})) == "field_type_invalid"
    assert a.f5_payload_validator(p5({"class-a": v})) == "field_type_invalid"


@pytest.mark.parametrize("v", BELOW + ABOVE)
def test_f5_value_out_of_range_per_class(v):
    assert a.f5_payload_validator(p5({"class-a": 30, "class-b": v})) == "field_invalid"
    assert a.f5_payload_validator(p5({"class-a": v})) == "field_invalid"


@pytest.mark.parametrize("v", VALID)
def test_f5_boundaries_accepted(v):
    assert a.f5_payload_validator(p5({"class-a": v})) is None


def test_f5_each_class_checked_independently():
    names = [f"c{i:03d}" for i in range(8)]
    for bad_index in range(8):
        for bad in (0, MAX + 1, True, "5"):
            m = {n: 5 for n in names}
            m[names[bad_index]] = bad
            assert a.f5_payload_validator(p5(m)) in ("field_invalid", "field_type_invalid")


def test_f5_map_shape():
    assert a.f5_payload_validator(p5({})) == "field_invalid"  # empty class map
    for notmap in (None, [], [["a", 1]], "a", 3, (("a", 1),), IntSub(1), True):
        assert a.f5_payload_validator({F5K: notmap}) == "field_type_invalid"

    class D(dict):
        pass
    assert a.f5_payload_validator({F5K: D({"a": 1})}) == "field_type_invalid"
    assert a.f5_payload_validator({F5K: {1: 5}}) == "field_type_invalid"  # non-str key
    assert a.f5_payload_validator({F5K: {StrSub("a"): 5}}) == "field_type_invalid"
    assert a.f5_payload_validator({F5K: {None: 5}}) == "field_type_invalid"


def test_f5_key_sets():
    assert a.f5_payload_validator({}) == "field_missing"
    for extra in ("status_max_age_seconds", "approval_max_age_seconds", "max_amount", "amount", "identity_max_age_seconds",
                  "mandate_max_age_seconds", "clock_tolerance_seconds", "class_status_max_age_seconds_2"):
        assert a.f5_payload_validator({**p5(), extra: 5}) == "field_unknown", extra
    assert a.f5_payload_validator({"Class_Status_Max_Age_Seconds": {"a": 1}}) == "field_unknown"
    assert a.f5_payload_validator({"max_status_age_seconds": {"a": 1}}) == "field_unknown"


@pytest.mark.parametrize("key", ["", " ", "a b", "a\tb", "a\nb", "a*b", "*", "a\x00", "a b", "a b", "x" * 129, "a​b"])
def test_f5_invalid_class_tokens_refused(key):
    assert a.f5_payload_validator(p5({key: 5})) == "field_invalid"


@pytest.mark.parametrize("key", ["a", "x" * 128, "Class-A", "class.a:b", "CLASS", "ünï", "a_b", "0", "class/x"])
def test_f5_valid_tokens_exact_no_case_folding(key):
    assert a.f5_payload_validator(p5({key: 5})) is None


def test_f5_keys_must_be_sorted_and_map_bounded():
    assert a.f5_payload_validator(p5({"b": 1, "a": 1})) == "field_invalid"
    assert a.f5_payload_validator(p5({"a": 1, "B": 1})) == "field_invalid"  # 'a' > 'B' by code point: B first
    assert a.f5_payload_validator(p5({"B": 1, "a": 1})) is None
    big = {f"c{i:04d}": 1 for i in range(c.MAX_ENTRIES)}
    assert a.f5_payload_validator(p5(big)) is None
    big[f"c{c.MAX_ENTRIES:04d}"] = 1
    assert a.f5_payload_validator(p5(big)) == "field_invalid"


def test_f5_duplicate_keys_refused_by_the_strict_loader():
    r = c.load_document('{"class_status_max_age_seconds": {"a": 1, "a": 2}}')
    assert (r.ok, r.code) == (False, "json_duplicate_key")


def test_f5_nested_value_shapes_refused():
    for bad in ({"a": {"b": 1}}, {"a": [1]}, {"a": {}}):
        assert a.f5_payload_validator(p5(bad)) == "field_type_invalid"


# ---------------------------------------------------------------- end to end through the record layer's validator hook
def test_payload_validators_via_spec():
    for fam, good, bad in ((F4, p4(), p4(status_max_age_seconds=0)), (F5, p5(), p5({"a": 0}))):
        spec = families.lookup_v2(fam)
        assert spec.payload_validator(good) is None and spec.payload_validator(bad) == "field_invalid"


# ---------------------------------------------------------------- F4 composition
def test_f4_min_grid_below_equal_above():
    for cal, reg in itertools.product([0, 1, 5, 59, 60, 61, 3600, MAX - 1, MAX], [1, 5, 59, 60, 61, 3600, MAX - 1, MAX]):
        for field in F4K:
            other = F4K[1 - F4K.index(field)]
            res = compose4(c4(**{field: cal}), p4(**{field: reg, other: MAX}))
            assert res.ok and res.code is None and res.deny_all is False and res.deny_all_fields == ()
            assert res.effective[field] == min(cal, reg) <= cal
            assert res.effective[other] == 60  # caller 60, registry MAX: never above caller
            assert (a.NOT_NARROWING in res.detail and field in res.detail) == (reg > cal)


def test_f4_effective_never_exceeds_caller_and_registry():
    for cal, reg in itertools.product(range(0, 8), range(1, 8)):
        res = compose4(c4(status_max_age_seconds=cal, approval_max_age_seconds=cal), p4(status_max_age_seconds=reg, approval_max_age_seconds=reg))
        assert res.effective == {"status_max_age_seconds": min(cal, reg), "approval_max_age_seconds": min(cal, reg)}


def test_f4_caller_zero_stays_zero_and_is_not_deny_all():
    res = compose4(c4(status_max_age_seconds=0), p4())
    assert res.ok and res.effective["status_max_age_seconds"] == 0 and res.deny_all is False


def test_f4_registry_above_caller_reports_not_narrowing():
    res = compose4(c4(), p4(status_max_age_seconds=MAX, approval_max_age_seconds=10))
    assert res.ok and res.effective == {"status_max_age_seconds": 60, "approval_max_age_seconds": 10}
    assert res.detail == "registry_value_not_narrowing:status_max_age_seconds"
    res = compose4(c4(), p4(status_max_age_seconds=60, approval_max_age_seconds=60))
    assert res.ok and res.detail == ""


def test_f4_no_cross_bound_inverted_pair_accepted():
    for st, ap in ((1, MAX), (MAX, 1), (3600, 5), (5, 3600), (1, 2), (2, 1)):
        assert a.f4_payload_validator(p4(status_max_age_seconds=st, approval_max_age_seconds=ap)) is None
        res = compose4(c4(status_max_age_seconds=MAX, approval_max_age_seconds=MAX), p4(status_max_age_seconds=st, approval_max_age_seconds=ap))
        assert res.ok and res.effective == {"status_max_age_seconds": st, "approval_max_age_seconds": ap}


def test_f4_no_five_second_floor():
    for v in (1, 2, 3, 4):
        res = compose4(c4(), p4(status_max_age_seconds=v, approval_max_age_seconds=v))
        assert res.ok and res.effective == {"status_max_age_seconds": v, "approval_max_age_seconds": v}
    res = compose4(c4(status_max_age_seconds=3, approval_max_age_seconds=2), p4(status_max_age_seconds=MAX, approval_max_age_seconds=MAX))
    assert res.ok and res.effective == {"status_max_age_seconds": 3, "approval_max_age_seconds": 2}  # caller below 5 is kept


@pytest.mark.parametrize("field", F4K)
@pytest.mark.parametrize("v", BAD_TYPES + BELOW[1:] + ABOVE)
def test_f4_invalid_caller_refused_never_replaced(field, v):
    refused(compose4(c4(**{field: v}), p4()), "composition_caller_invalid")
    refused(compose4(c4(**{field: v}), p4(status_max_age_seconds=1, approval_max_age_seconds=1)), "composition_caller_invalid")


@pytest.mark.parametrize("bad", [None, [], "x", 5, {}, {"status_max_age_seconds": 5}, {"approval_max_age_seconds": 5},
                                 {**c4(), "identity_max_age_seconds": 5}, {**c4(), "max_amount": 5}, {"Status_Max_Age_Seconds": 5, "approval_max_age_seconds": 5}])
def test_f4_malformed_caller_refused(bad):
    refused(compose4(bad), "composition_caller_invalid")


def test_f4_caller_boundaries_accepted():
    for v in (0, 1, MAX):
        assert compose4(c4(status_max_age_seconds=v)).ok


@pytest.mark.parametrize("field", F4K)
@pytest.mark.parametrize("v", BAD_TYPES + BELOW + ABOVE)
def test_f4_invalid_registry_refuses_never_yields_caller(field, v):
    res = compose4(c4(), p4(**{field: v}))
    refused(res, "composition_record_invalid")
    assert res.effective is None  # no default, no caller value


def test_f4_record_and_operator_and_family_refusals():
    refused(families.compose_v2(c4(), rec(p4(), F4, ok=False)), "composition_record_invalid")
    refused(families.compose_v2(c4(), None), "composition_record_invalid")
    refused(families.compose_v2(c4(), rec(p4(), F4), "union"), "composition_operator_unsupported")
    refused(families.compose_v2(c4(), rec(p4(), F5)), "composition_record_invalid")  # F5 payload is not F4
    refused(a.compose_f4(c4(), rec(p5(), F5)), "composition_family_unsupported")  # direct call with the wrong family
    refused(a.compose_f5(c5(), rec(p4(), F4)), "composition_family_unsupported")
    refused(families.compose_v2(c4(), rec(p4(), "f4-control-plane-age-bounds ")), "composition_family_unsupported")
    refused(a.compose_f4(c4(), rec(p4(identity_max_age_seconds=5), F4)), "composition_record_invalid")
    refused(a.compose_f4(c4(), rec(p4(max_amount=5), F4)), "composition_record_invalid")
    for bad_op in (None, "", "min", "INTERSECTION", ["intersection"]):
        refused(a.compose_f4(c4(), rec(p4(), F4), bad_op), "composition_operator_unsupported")


def test_f4_inputs_not_mutated():
    cal, pl = c4(), p4()
    cal0, pl0 = dict(cal), dict(pl)
    compose4(cal, pl)
    assert cal == cal0 and pl == pl0


# ---------------------------------------------------------------- F5 composition
def test_f5_min_grid_per_class():
    for cal, reg in itertools.product([0, 1, 5, 60, 61, MAX - 1, MAX], [1, 5, 59, 60, 61, MAX - 1, MAX]):
        res = compose5(c5({"class-a": cal, "class-b": 77}), p5({"class-a": reg}))
        assert res.ok and res.deny_all is False
        assert res.effective == {F5K: {"class-a": min(cal, reg), "class-b": 77}}
        assert res.effective[F5K]["class-a"] <= cal
        assert (a.NOT_NARROWING in res.detail) == (reg > cal)


def test_f5_each_class_independently_narrowed_and_unlisted_caller_class_kept():
    res = compose5(c5(), p5({"class-a": 30, "class-b": 600}))
    assert res.ok and res.effective == {F5K: {"class-a": 30, "class-b": 60, "class-c": 90}}
    assert res.detail == "registry_value_not_narrowing:class-b"
    assert list(res.effective[F5K]) == ["class-a", "class-b", "class-c"]


def test_f5_unknown_registry_class_refused():
    refused(compose5(c5(), p5({"class-a": 1, "class-z": 1})), "composition_record_invalid")
    refused(compose5(c5(), p5({"CLASS-A": 1})), "composition_record_invalid")  # exact, no case folding
    refused(compose5(c5({"class-a": 60}), p5({"class-a ": 1})), "composition_record_invalid")  # token rule refuses it first


def test_f5_no_cross_bound_and_no_five_second_floor():
    res = compose5(c5({"a": MAX, "b": 1, "c": MAX}), p5({"a": 1, "b": MAX, "c": 2}))
    assert res.ok and res.effective == {F5K: {"a": 1, "b": 1, "c": 2}}
    res = compose5(c5({"a": 60}), p5({"a": 1}))
    assert res.ok and res.effective == {F5K: {"a": 1}}


@pytest.mark.parametrize("v", BAD_TYPES + BELOW[1:] + ABOVE)
def test_f5_invalid_caller_value_refused_per_class(v):
    for bad_class in ("class-a", "class-b", "class-c"):
        m = {"class-a": 60, "class-b": 60, "class-c": 60}
        m[bad_class] = v
        refused(compose5(c5(m), p5({"class-a": 1})), "composition_caller_invalid")


@pytest.mark.parametrize("v", BAD_TYPES + BELOW + ABOVE)
def test_f5_invalid_registry_value_refuses_never_yields_caller(v):
    refused(compose5(c5(), p5({"class-a": v})), "composition_record_invalid")
    refused(compose5(c5(), p5({"class-a": 5, "class-b": v})), "composition_record_invalid")


@pytest.mark.parametrize("bad", [None, [], "x", {}, {F5K: {}}, {F5K: None}, {F5K: []}, {F5K: [("a", 1)]}, {F5K: {"": 5}}, {F5K: {"a b": 5}}, {F5K: {1: 5}},
                                 {F5K: {"a": 5}, "x": 1}, {"status_max_age_seconds": 5}, {F5K: {"class-a": 0}, "max_amount": 1}])
def test_f5_malformed_caller_refused(bad):
    refused(compose5(bad, p5({"a": 1})), "composition_caller_invalid")


def test_f5_caller_zero_stays_zero_and_oversized_caller_map_refused():
    res = compose5({F5K: {"a": 0}}, p5({"a": 5}))
    assert res.ok and res.effective == {F5K: {"a": 0}}
    big = {f"c{i:04d}": 1 for i in range(c.MAX_ENTRIES + 1)}
    refused(compose5({F5K: big}, p5({"c0000": 1})), "composition_caller_invalid")


def test_f5_registry_map_refusals_and_family_checks():
    refused(compose5(c5(), p5({})), "composition_record_invalid")  # empty class map
    refused(compose5(c5(), {F5K: {"b": 1, "a": 1}}), "composition_record_invalid")  # unsorted
    refused(compose5(c5(), {**p5(), "max_amount": 5}), "composition_record_invalid")
    refused(compose5(c5(), {"status_max_age_seconds": 1}), "composition_record_invalid")
    refused(families.compose_v2(c5(), rec(p5(), F5), "union"), "composition_operator_unsupported")
    refused(families.compose_v2(c5(), rec(p5(), F5, ok=False)), "composition_record_invalid")


def test_f5_inputs_not_mutated_and_effective_is_a_copy():
    cal, pl = c5(), p5()
    cal0 = json.dumps(cal)
    res = compose5(cal, pl)
    assert json.dumps(cal) == cal0
    res.effective[F5K]["class-a"] = 9999
    assert cal == c5()


def test_refusals_never_carry_a_policy_exhaustive_f4():
    """Required-policy safety: no refusal returns an effective policy, the caller value or a default."""
    callers = [c4(), None, c4(status_max_age_seconds=True), c4(approval_max_age_seconds=-1), {}]
    payloads = [p4(), p4(status_max_age_seconds=0), p4(status_max_age_seconds=True), {"status_max_age_seconds": 3}, p4(x=1), None, [], p5()]
    for cl, pl in itertools.product(callers, payloads):
        res = a.compose_f4(cl, rec(pl, F4))
        if not res.ok:
            assert res.effective is None and res.deny_all is False and res.deny_all_fields == () and res.code in c.CODES
        else:
            assert all(res.effective[k] <= cl[k] for k in F4K)


def test_unexpected_exception_is_a_refusal():
    class Boom:
        ok = True

        @property
        def record(self):
            raise RuntimeError("x")
    refused(a.compose_f4(c4(), Boom()), "composition_record_invalid")
    refused(a.compose_f5(c5(), Boom()), "composition_record_invalid")


# ---------------------------------------------------------------- mutation checks
def _battery(mod):
    """Returns the set of property names violated by `mod`. The real module violates none."""
    bad = set()

    def chk(name, cond):
        try:
            if not cond():
                bad.add(name)
        except Exception:
            bad.add(name)

    v4, v5 = mod.f4_payload_validator, mod.f5_payload_validator
    chk("bool_registry", lambda: v4(p4(status_max_age_seconds=True)) == "field_type_invalid" and v5(p5({"a": True})) == "field_type_invalid")
    chk("float_registry", lambda: v4(p4(status_max_age_seconds=60.0)) == "field_type_invalid" and v5(p5({"a": 60.0})) == "field_type_invalid")
    chk("str_none_registry", lambda: v4(p4(approval_max_age_seconds="60")) == "field_type_invalid" and v4(p4(approval_max_age_seconds=None)) == "field_type_invalid"
        and v5(p5({"a": None})) == "field_type_invalid" and v5(p5({"a": "5"})) == "field_type_invalid")
    chk("intsub_registry", lambda: v4(p4(status_max_age_seconds=IntSub(5))) == "field_type_invalid" and v5(p5({"a": IntSub(5)})) == "field_type_invalid")
    chk("zero_registry", lambda: v4(p4(status_max_age_seconds=0)) is not None and v5(p5({"a": 0})) is not None)
    chk("negative_registry", lambda: v4(p4(approval_max_age_seconds=-1)) is not None and v5(p5({"a": -1})) is not None)
    chk("above_ceiling_registry", lambda: v4(p4(status_max_age_seconds=MAX + 1)) is not None and v5(p5({"a": MAX + 1})) is not None
        and v4(p4(approval_max_age_seconds=10**30)) is not None)
    chk("ceiling_accepted", lambda: v4(p4(status_max_age_seconds=MAX)) is None and v5(p5({"a": MAX})) is None)
    chk("floor_one_accepted", lambda: v4(p4(status_max_age_seconds=1)) is None and v5(p5({"a": 1})) is None)
    chk("third_key", lambda: v4(p4(identity_max_age_seconds=5)) == "field_unknown" and v5({**p5(), "x": 1}) == "field_unknown")
    chk("amount_key", lambda: v4(p4(max_amount=5)) == "field_unknown" and v5({**p5(), "max_amount": 5}) == "field_unknown")
    chk("absent_key", lambda: v4({"status_max_age_seconds": 5}) == "field_missing" and v5({}) == "field_missing")
    chk("empty_map", lambda: v5(p5({})) is not None)
    chk("unsorted_keys", lambda: v5(p5({"b": 1, "a": 1})) is not None)
    chk("bad_token", lambda: v5(p5({"a b": 1})) is not None and v5(p5({"": 1})) is not None and v5(p5({"a*": 1})) is not None)
    chk("map_bound", lambda: v5(p5({f"c{i:04d}": 1 for i in range(c.MAX_ENTRIES + 1)})) is not None)
    chk("no_cross_bound", lambda: v4(p4(status_max_age_seconds=1, approval_max_age_seconds=MAX)) is None
        and v4(p4(status_max_age_seconds=MAX, approval_max_age_seconds=1)) is None)

    def comp4(cal, pl):
        return mod.compose_f4(cal, rec(pl, F4))

    def comp5(cal, pl):
        return mod.compose_f5(cal, rec(pl, F5))
    chk("min_f4", lambda: comp4(c4(), p4(status_max_age_seconds=MAX)).effective["status_max_age_seconds"] == 60
        and comp4(c4(), p4(status_max_age_seconds=5)).effective["status_max_age_seconds"] == 5)
    chk("min_f5", lambda: comp5(c5(), p5({"class-a": MAX})).effective[F5K]["class-a"] == 60
        and comp5(c5(), p5({"class-a": 5})).effective[F5K]["class-a"] == 5)
    chk("caller_zero_kept", lambda: comp4(c4(status_max_age_seconds=0), p4()).effective["status_max_age_seconds"] == 0)
    chk("caller_bool", lambda: not comp4(c4(status_max_age_seconds=True), p4()).ok and not comp5(c5({"a": True}), p5({"a": 1})).ok)
    chk("caller_float_str_none", lambda: not comp4(c4(status_max_age_seconds=60.0), p4()).ok and not comp4(c4(approval_max_age_seconds="60"), p4()).ok
        and not comp4(c4(approval_max_age_seconds=None), p4()).ok)
    chk("caller_negative", lambda: not comp4(c4(status_max_age_seconds=-1), p4()).ok and not comp5(c5({"a": -1}), p5({"a": 1})).ok)
    chk("caller_above_ceiling", lambda: not comp4(c4(status_max_age_seconds=MAX + 1), p4()).ok and not comp5(c5({"a": MAX + 1}), p5({"a": 1})).ok)
    chk("caller_extra_key", lambda: not comp4({**c4(), "max_amount": 1}, p4()).ok)
    chk("caller_empty_map", lambda: comp5({F5K: {}}, p5({"a": 1})).code == "composition_caller_invalid")
    chk("unknown_class", lambda: not comp5(c5(), p5({"class-z": 1})).ok and not comp5(c5({"a": 5}), p5({"b": 1})).ok)
    chk("refusal_no_policy", lambda: comp4(c4(), p4(status_max_age_seconds=0)).effective is None and comp5(c5(), p5({})).effective is None)
    chk("operator", lambda: mod.compose_f4(c4(), rec(p4(), F4), "union").code == "composition_operator_unsupported")
    chk("family", lambda: mod.compose_f4(c4(), rec(p5(), F5)).code == "composition_family_unsupported")
    return bad


MUTATIONS = {  # name -> (old, new, expected violated property)
    # the type checks are layered (payload validators and the range predicates), so a bool survives only if every layer is dropped
    "drop bool exclusion": (("type(v) is int", "type(payload[k]) is int", "type(v) is int".replace("v", "v")), ("isinstance(v, int)", "isinstance(payload[k], int)", "isinstance(v, int)"), "bool_registry"),
    "drop registry floor": ("return type(v) is int and AGE_MIN <= v <= AGE_MAX", "return type(v) is int and v <= AGE_MAX", "zero_registry"),
    "drop registry ceiling": ("return type(v) is int and AGE_MIN <= v <= AGE_MAX", "return type(v) is int and AGE_MIN <= v", "above_ceiling_registry"),
    "ceiling off by one": ("return type(v) is int and AGE_MIN <= v <= AGE_MAX", "return type(v) is int and AGE_MIN <= v < AGE_MAX", "ceiling_accepted"),
    "five second floor": ("return type(v) is int and AGE_MIN <= v <= AGE_MAX", "return type(v) is int and 5 <= v <= AGE_MAX", "floor_one_accepted"),
    "drop caller floor": ("return type(v) is int and CALLER_MIN <= v <= AGE_MAX", "return type(v) is int and v <= AGE_MAX", "caller_negative"),
    "caller floor one": ("return type(v) is int and CALLER_MIN <= v <= AGE_MAX", "return type(v) is int and 1 <= v <= AGE_MAX", "caller_zero_kept"),
    "drop caller ceiling": ("return type(v) is int and CALLER_MIN <= v <= AGE_MAX", "return type(v) is int and CALLER_MIN <= v", "caller_above_ceiling"),
    "caller accepts bool": ("return type(v) is int and CALLER_MIN <= v <= AGE_MAX", "return isinstance(v, int) and CALLER_MIN <= v <= AGE_MAX", "caller_bool"),
    "drop unknown-key check": ("    if keys - set(fields):\n        return \"field_unknown\"\n", "", "third_key"),
    "drop missing-key check": ("    if set(fields) - keys:\n        return \"field_missing\"\n", "", "absent_key"),
    "drop f4 type check": ("    if not all(type(payload[k]) is int for k in F4_FIELDS):\n        return \"field_type_invalid\"\n", "", "str_none_registry"),
    "drop empty map check": ("    if not m or len(m) > MAX_CLASSES:", "    if len(m) > MAX_CLASSES:", "empty_map"),
    "drop map bound": ("    if not m or len(m) > MAX_CLASSES:", "    if not m:", "map_bound"),
    "drop sorted check": ("keys != sorted(keys)", "False", "unsorted_keys"),
    "drop token check": ("not all(c.valid_token(k) for k in keys) or ", "", "bad_token"),
    "max instead of min f4": ("effective = {k: min(cal[k], payload[k]) for k in F4_FIELDS}", "effective = {k: max(cal[k], payload[k]) for k in F4_FIELDS}", "min_f4"),
    "registry replaces caller f4": ("effective = {k: min(cal[k], payload[k]) for k in F4_FIELDS}", "effective = {k: payload[k] for k in F4_FIELDS}", "min_f4"),
    "max instead of min f5": ("min(base[k], reg[k]) if k in reg else base[k]", "max(base[k], reg[k]) if k in reg else base[k]", "min_f5"),
    "drop unknown class refusal": ("        if set(reg) - set(base):", "        if False:", "unknown_class"),
    "drop caller normalizer f4": ("        cal = normalize_caller_f4(caller)\n        if cal is None:\n            return _refuse(\"composition_caller_invalid\")\n",
                                  "        cal = dict(caller)\n", "caller_extra_key"),
    "refusal returns effective": ("    return CompositionResult(False, code, detail)", "    return CompositionResult(False, code, detail, {})", "refusal_no_policy"),
    "drop operator check f4": ("def compose_f4(caller: Any, record: Any, operator: Any = \"intersection\") -> CompositionResult:\n    try:\n        if operator != \"intersection\":\n            return _refuse(\"composition_operator_unsupported\")\n",
                               "def compose_f4(caller: Any, record: Any, operator: Any = \"intersection\") -> CompositionResult:\n    try:\n", "operator"),
    "drop family check": ("    if body.get(\"family\") != family:\n        return None, \"composition_family_unsupported\"\n", "", "family"),
    "caller empty map accepted": ("    if not isinstance(m, Mapping) or not m or len(m) > MAX_CLASSES:", "    if not isinstance(m, Mapping) or len(m) > MAX_CLASSES:", "caller_empty_map"),
}


def _load(src):
    mod = types.ModuleType("mutant")
    mod.__dict__["__name__"] = "mutant"
    exec(compile(src, "mutant", "exec"), mod.__dict__)
    return mod


def test_battery_passes_on_the_real_module():
    assert _battery(a) == set()


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_mutation_is_detected(name):
    old, new, expected = MUTATIONS[name]
    src = (ROOT / "registry_successor/v2_age_bounds.py").read_text(encoding="utf-8")
    if isinstance(old, tuple):  # a layered mutation replaces every occurrence of each anchor
        for o, n in zip(old[:2], new[:2]):
            assert o in src, o
            src = src.replace(o, n)
        mutated = src
    else:
        assert src.count(old) == 1, f"mutation anchor for {name!r} no longer unique"
        mutated = src.replace(old, new)
    violated = _battery(_load(mutated))
    assert expected in violated, (name, violated)
