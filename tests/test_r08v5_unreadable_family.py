"""`r08-v5` family `f5-action-class-unreadable-policy`: payload validation and composition (BUILDER_TESTED; not independently qualified).

Pure: no signature backend is needed. The consuming evaluator branches (Control Plane `bounded.py:2111`, `:2189`) support only the two-point order
`refuse` < `bounded_tolerance`; the matrix below pins that order and its non-widening property exhaustively.
"""
import itertools
from collections.abc import Mapping

import pytest

import r08_support as r
import r08v5_support as t
from registry_successor import common as c
from registry_successor import v5_class_unreadable as f
from registry_successor import v5_families as fam

FIELD = f.F5U_FIELD
R, B = "refuse", "bounded_tolerance"


def rec(pl=None, **over):
    return c_rec(t.record(pl, **over))


def c_rec(body):
    from registry_successor import v5_record
    return v5_record.validate_record_text_v5(r.dumps(body))


# ---- vocabulary and order
def test_vocabulary_is_the_closed_control_plane_pair_strictest_first():
    assert f.VALUES == (R, B) and f.REFUSE == R and f.BOUNDED_TOLERANCE == B
    assert f.stricter(R, B) == R and f.stricter(B, R) == R and f.stricter(R, R) == R and f.stricter(B, B) == B


@pytest.mark.parametrize("bad", ["Refuse", "REFUSE", " refuse", "refuse ", "tolerate", "allow", "", "bounded-tolerance", "bounded_tolerance\n", "none"])
def test_unknown_or_respelled_values_are_field_invalid(bad):
    assert f.payload_validator({FIELD: {"class-a": bad}}) == "field_invalid"


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, 1.0, b"refuse", ["refuse"], {"v": "refuse"}])
def test_non_string_values_are_field_type_invalid(bad):
    assert f.payload_validator({FIELD: {"class-a": bad}}) == "field_type_invalid"


def test_str_subclass_values_and_keys_are_refused_not_compared_by_value():
    class S(str):
        pass
    assert f.payload_validator({FIELD: {"class-a": S("refuse")}}) == "field_type_invalid"
    assert f.payload_validator({FIELD: {S("class-a"): "refuse"}}) == "field_type_invalid"
    assert f.normalize_caller({FIELD: {"class-a": S("refuse")}}) is None
    assert f.normalize_caller({FIELD: {S("class-a"): "refuse"}}) is None
    assert not f.is_value(S("refuse"))


# ---- payload shape
def test_valid_payloads():
    assert f.payload_validator({FIELD: {"class-a": R}}) is None
    assert f.payload_validator({FIELD: {"class-a": B, "class-b": R}}) is None


@pytest.mark.parametrize("payload,code", [
    ({}, "field_missing"), ({FIELD: {"class-a": R}, "extra": 1}, "field_unknown"), ({"other": {"class-a": R}}, "field_unknown"),
    ({FIELD: []}, "field_type_invalid"), ({FIELD: "refuse"}, "field_type_invalid"), ({FIELD: None}, "field_type_invalid"),
    ({FIELD: {}}, "field_invalid"), ({FIELD: {"class-b": R, "class-a": R}}, "field_invalid"), ({FIELD: {"*": R}}, "field_invalid"),
    ({FIELD: {"": R}}, "field_invalid"), ({FIELD: {"a" * 129: R}}, "field_invalid"), ({FIELD: {"class a": R}}, "field_invalid"),
    ({FIELD: {"class-a": R, "class-b": "x"}}, "field_invalid"), ({1: {"class-a": R}}, "field_type_invalid"), ({FIELD: {1: R}}, "field_type_invalid"),
])
def test_payload_shape_codes(payload, code):
    assert f.payload_validator(payload) == code


def test_oversized_class_map_is_refused():
    big = {("c%03d" % i): R for i in range(c.MAX_ENTRIES + 1)}
    assert f.payload_validator({FIELD: big}) == "field_invalid"
    ok = {("c%03d" % i): R for i in range(c.MAX_ENTRIES)}
    assert f.payload_validator({FIELD: ok}) is None


def test_payload_must_be_an_exact_dict():
    class D(dict):
        pass
    assert f.payload_validator(D({FIELD: {"class-a": R}})) == "field_type_invalid"
    assert f.payload_validator({FIELD: D({"class-a": R})}) == "field_type_invalid"
    assert f.payload_validator([FIELD]) == "field_type_invalid"


# ---- the exhaustive 2x2 composition matrix: narrowing only, never widening
@pytest.mark.parametrize("host,reg", list(itertools.product((R, B), repeat=2)))
def test_composition_matrix_is_the_stricter_value_and_never_looser_than_the_host(host, reg):
    res = f.compose_f5u({FIELD: {"class-a": host}}, rec({FIELD: {"class-a": reg}}))
    assert res.ok and res.deny_all is False and res.deny_all_fields == ()
    eff = res.effective[FIELD]["class-a"]
    assert eff == (R if R in (host, reg) else B)
    assert f._RANK[eff] <= f._RANK[host] and f._RANK[eff] <= f._RANK[reg]


def test_bounded_tolerance_is_narrowed_to_refuse():
    res = f.compose_f5u({FIELD: {"class-a": B}}, rec({FIELD: {"class-a": R}}))
    assert res.ok and res.effective == {FIELD: {"class-a": R}} and res.detail == ""


def test_refuse_stays_refuse_and_a_registry_bounded_tolerance_never_widens_it():
    res = f.compose_f5u({FIELD: {"class-a": R}}, rec({FIELD: {"class-a": B}}))
    assert res.ok and res.effective == {FIELD: {"class-a": R}}
    assert res.detail == "registry_value_not_narrowing:class-a"


def test_not_narrowing_detail_lists_only_the_looser_registry_classes_sorted():
    res = f.compose_f5u({FIELD: {"class-a": R, "class-b": B, "class-c": R}}, rec({FIELD: {"class-a": B, "class-b": B, "class-c": B}}))
    assert res.ok and res.detail == "registry_value_not_narrowing:class-a,class-c"
    assert res.effective == {FIELD: {"class-a": R, "class-b": B, "class-c": R}}


def test_unlisted_caller_classes_keep_their_value_and_unknown_registry_classes_refuse():
    res = f.compose_f5u({FIELD: {"class-a": B, "class-b": B}}, rec({FIELD: {"class-a": R}}))
    assert res.ok and res.effective == {FIELD: {"class-a": R, "class-b": B}}
    bad = f.compose_f5u({FIELD: {"class-a": B}}, rec({FIELD: {"class-a": R, "class-zz": R}}))
    assert not bad.ok and bad.code == "composition_record_invalid" and bad.effective is None


def test_composition_is_independent_of_registry_class_coverage_order_and_pure():
    host = {FIELD: {"class-a": B, "class-b": B, "class-c": B}}
    r1 = f.compose_f5u(host, rec({FIELD: {"class-a": R, "class-c": R}}))
    r2 = f.compose_f5u(host, rec({FIELD: {"class-a": R, "class-c": R}}))
    assert r1 == r2 and r1.effective == {FIELD: {"class-a": R, "class-b": B, "class-c": R}}
    assert host == {FIELD: {"class-a": B, "class-b": B, "class-c": B}}


# ---- refusals never carry a policy and never return the caller
@pytest.mark.parametrize("caller", [
    None, {}, {FIELD: {}}, {FIELD: {"class-a": "x"}}, {FIELD: {"class-a": None}}, {FIELD: {"class-a": True}}, {FIELD: {"class a": R}}, {FIELD: {"": R}},
    {FIELD: {"class-a": R}, "extra": {}}, {"other": {"class-a": R}}, {FIELD: ["class-a"]}, {FIELD: {1: R}}, "x", 5,
])
def test_invalid_caller_refuses_without_a_policy(caller):
    res = f.compose_f5u(caller, rec())
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None and res.deny_all is False


def test_oversized_caller_map_refuses():
    big = {("c%03d" % i): R for i in range(c.MAX_ENTRIES + 1)}
    assert f.compose_f5u({FIELD: big}, rec({FIELD: {"c000": R}})).code == "composition_caller_invalid"


def test_hostile_caller_mappings_are_read_once_and_bounded():
    reads = []

    class Flip(Mapping):
        def __iter__(self):
            return iter(["class-a"])

        def __len__(self):
            return 1

        def __getitem__(self, k):
            reads.append(k)
            return R if len(reads) % 2 else B

        def items(self):
            reads.append("items")
            return iter([("class-a", B)])
    res = f.compose_f5u({FIELD: Flip()}, rec({FIELD: {"class-a": R}}))
    assert res.ok and res.effective == {FIELD: {"class-a": R}}

    class Endless(Mapping):
        def __iter__(self):
            return iter(range(10 ** 9))

        def __len__(self):
            return 10 ** 9

        def __getitem__(self, k):
            return R

        def items(self):
            return ((("c%d" % i), R) for i in itertools.count())
    assert f.compose_f5u({FIELD: Endless()}, rec()).code == "composition_caller_invalid"


@pytest.mark.parametrize("operator", ["union", "", None, "Intersection", 1])
def test_only_the_intersection_operator_is_supported(operator):
    res = f.compose_f5u({FIELD: {"class-a": B}}, rec({FIELD: {"class-a": R}}), operator)
    assert not res.ok and res.code == "composition_operator_unsupported" and res.effective is None


def test_invalid_or_foreign_records_refuse():
    good = rec({FIELD: {"class-a": R}})
    assert good.ok
    assert f.compose_f5u({FIELD: {"class-a": B}}, None).code == "composition_record_invalid"
    assert f.compose_f5u({FIELD: {"class-a": B}}, object()).code == "composition_record_invalid"
    other_family = type("Rec", (), {"ok": True, "record": dict(good.record, family="f5-action-class-age-bounds")})()
    assert f.compose_f5u({FIELD: {"class-a": B}}, other_family).code == "composition_family_unsupported"
    bad_payload = type("Rec", (), {"ok": True, "record": dict(good.record, payload={FIELD: {"class-a": "x"}})})()
    assert f.compose_f5u({FIELD: {"class-a": B}}, bad_payload).code == "composition_record_invalid"
    not_ok = type("Rec", (), {"ok": False, "record": good.record})()
    assert f.compose_f5u({FIELD: {"class-a": B}}, not_ok).code == "composition_record_invalid"


# ---- record validation through the r08-v5 validator
def test_valid_record_is_accepted_and_malformed_ones_carry_the_shape_codes():
    assert rec().ok
    assert rec({FIELD: {"class-a": "tolerate"}}).code == "field_invalid"
    assert rec({FIELD: {"class-a": 1}}).code == "field_type_invalid"
    assert rec({}).code == "field_missing"
    assert rec({FIELD: {"class-a": R}, "x": 1}).code == "field_unknown"
    assert f.payload_validator({FIELD: {"b": R, "a": R}}) == "field_invalid"  # record text is canonicalized on dump, so unsorted order is checked on the payload


def test_the_v5_table_registers_exactly_one_family_and_dispatches_by_exact_string():
    assert set(fam.FAMILIES_V5) == {f.FAMILY_F5U} and fam.CONTRACT_V5 == "r08-v5"
    spec = fam.lookup_v5(f.FAMILY_F5U)
    assert spec.enforcing_component == "control-plane" and spec.payload_fields == (FIELD,)
    for bad in ("F5-ACTION-CLASS-UNREADABLE-POLICY", " f5-action-class-unreadable-policy", None, 1, ["x"], "f5-action-class-age-bounds"):
        assert fam.lookup_v5(bad) is None
    assert fam.table_for_contract_version_v5("r08-v5").ok
    for v in ("r08-v4", "r08-v2", "R08-V5", "r08-v5 ", None, 5):
        sel = fam.table_for_contract_version_v5(v)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
    assert not fam.compose_for_v5("r08-v4", {FIELD: {"class-a": B}}, rec()).ok
