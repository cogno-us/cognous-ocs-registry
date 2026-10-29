"""`r08-v8` families `f5-observation-max-age-policy` and `f5-observation-clock-tolerance-policy` (DRAFT / PROPOSED / GATED; BUILDER_TESTED; not independently qualified).

Strict ints, `min(caller, registry)` composition, no host bound implied: 2147483647 is the structural Registry token range (`common.MAX_INT`), not a Control Plane bound.
A caller above the range refuses the WHOLE caller. The tolerance member must never alias the held constructor tolerance member `clock_tolerance_seconds`.
"""
import decimal
import fractions
import itertools
from collections.abc import Mapping

import pytest

import r08_support as r
import r08v8_support as t
from registry_successor import common as c
from registry_successor.engine import families_observation as f
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e

INT_MAX = 2147483647
MAXAGE = dict(family=f.FAMILY_MAX_AGE, field=f.MAX_AGE_FIELD, lo=1, validator=f.max_age_payload_validator, composer=f.compose_max_age,
              normalizer=f.normalize_caller_max_age, is_value=f.is_max_age, name="max_age")
TOL = dict(family=f.FAMILY_TOLERANCE, field=f.TOLERANCE_FIELD, lo=0, validator=f.tolerance_payload_validator, composer=f.compose_tolerance,
           normalizer=f.normalize_caller_tolerance, is_value=f.is_tolerance, name="tolerance")
BOTH = pytest.mark.parametrize("fam", [MAXAGE, TOL], ids=lambda d: d["name"])


def rec(fam, pl=None, **over):
    return record_e.validate_record_text(profiles.V8, r.dumps(t.record(pl, family=fam["family"], **over)))


class S(str):
    pass


class I(int):  # noqa: E742
    pass


# ---- constants and names
def test_constants_and_names():
    assert f.FAMILY_MAX_AGE == "f5-observation-max-age-policy" and f.FAMILY_TOLERANCE == "f5-observation-clock-tolerance-policy"
    assert f.MAX_AGE_FIELD == "observation_max_age_seconds" and f.TOLERANCE_FIELD == "observation_clock_tolerance_seconds"
    assert f.MAX_AGE_FIELDS == (f.MAX_AGE_FIELD,) and f.TOLERANCE_FIELDS == (f.TOLERANCE_FIELD,)
    assert f.INT_MAX == INT_MAX == c.MAX_INT and f.MAX_AGE_MIN == 1 and f.TOLERANCE_MIN == 0
    assert f.SCHEMA_REVISION == 1 and type(f.SCHEMA_REVISION) is int
    assert f.MAX_AGE_FIELD != "max_age_seconds" and f.TOLERANCE_FIELD != "clock_tolerance_seconds"


def test_the_ranges_are_structural_registry_token_ranges_and_equal_the_age_token_ceiling():
    from registry_successor import v2_age_bounds as ab
    assert f.INT_MAX == ab.AGE_MAX


# ---- domain boundaries
@BOTH
def test_domain_boundaries(fam):
    lo, field = fam["lo"], fam["field"]
    for ok in (lo, lo + 1, 59, 60, 300, 86400, INT_MAX - 1, INT_MAX):
        assert fam["is_value"](ok) and fam["validator"]({field: ok}) is None and fam["normalizer"]({field: ok}) == {field: ok}
    for bad in (lo - 1, -1, -2 ** 31, INT_MAX + 1, 2 ** 31, 2 ** 32, 2 ** 63, 10 ** 12, 10 ** 30):
        assert not fam["is_value"](bad) and fam["validator"]({field: bad}) == "field_invalid" and fam["normalizer"]({field: bad}) is None


def test_the_only_difference_between_the_two_floors_is_zero():
    assert f.is_tolerance(0) and not f.is_max_age(0) and f.max_age_payload_validator({f.MAX_AGE_FIELD: 0}) == "field_invalid"
    assert f.tolerance_payload_validator({f.TOLERANCE_FIELD: 0}) is None
    assert not f.is_tolerance(-1) and not f.is_max_age(-1)


@BOTH
@pytest.mark.parametrize("bad", [None, True, False, 1.0, 60.0, 0.5, float("nan"), float("inf"), "60", "1", "", b"60", [60], (60,), {"v": 60}, decimal.Decimal(60),
                                 fractions.Fraction(60), complex(1), I(60), I(1), 60j, object()])
def test_non_int_values_are_field_type_invalid_and_never_coerced(fam, bad):
    assert fam["validator"]({fam["field"]: bad}) == "field_type_invalid"
    assert fam["normalizer"]({fam["field"]: bad}) is None
    assert not fam["is_value"](bad)


def test_bool_is_never_a_number_even_where_zero_or_one_is_in_range():
    assert not f.is_max_age(True) and not f.is_tolerance(True) and not f.is_tolerance(False)
    assert f.tolerance_payload_validator({f.TOLERANCE_FIELD: False}) == "field_type_invalid"
    assert f.max_age_payload_validator({f.MAX_AGE_FIELD: True}) == "field_type_invalid"


# ---- payload shape and names
@BOTH
@pytest.mark.parametrize("extra", [{}, {"x": 1}, {"max_age_seconds": 60}, {"clock_tolerance_seconds": 5}, {"status_max_age_seconds": 60}, {"approval_max_age_seconds": 60}])
def test_extra_members_are_field_unknown(fam, extra):
    pl = dict({fam["field"]: 60}, **extra)
    assert fam["validator"](pl) == ("field_unknown" if extra else None)


@BOTH
def test_missing_and_foreign_members(fam):
    assert fam["validator"]({}) == "field_missing"
    assert fam["validator"]({"clock_tolerance_seconds": 5}) == "field_unknown"
    assert fam["validator"]({1: 5}) == "field_type_invalid"
    assert fam["validator"]({S(fam["field"]): 5}) == "field_type_invalid"
    assert fam["validator"]([fam["field"]]) == "field_type_invalid"
    assert fam["validator"](None) == "field_type_invalid"
    class D(dict):
        pass
    assert fam["validator"](D({fam["field"]: 5})) == "field_type_invalid"


def test_each_family_refuses_the_other_familys_member():
    assert f.max_age_payload_validator({f.TOLERANCE_FIELD: 5}) == "field_unknown"
    assert f.tolerance_payload_validator({f.MAX_AGE_FIELD: 5}) == "field_unknown"
    assert f.max_age_payload_validator({f.MAX_AGE_FIELD: 5, f.TOLERANCE_FIELD: 5}) == "field_unknown"
    assert f.normalize_caller_max_age({f.TOLERANCE_FIELD: 5}) is None and f.normalize_caller_tolerance({f.MAX_AGE_FIELD: 5}) is None


def test_the_tolerance_family_cannot_be_fed_a_record_using_the_held_constructor_member_name():
    """`clock_tolerance_seconds` is the held constructor tolerance member (RG-C-006); the observation member must not alias it."""
    held = rec(TOL, {"clock_tolerance_seconds": 5})
    assert not held.ok and held.code == "field_unknown"  # the record validator reports an unknown member before a missing one
    both = rec(TOL, {"clock_tolerance_seconds": 5, f.TOLERANCE_FIELD: 5})
    assert not both.ok and both.code == "field_unknown"
    fake = type("Rec", (), {"ok": True, "record": dict(t.record(family=f.FAMILY_TOLERANCE), payload={"clock_tolerance_seconds": 5})})()
    res = f.compose_tolerance({f.TOLERANCE_FIELD: 5}, fake)
    assert not res.ok and res.code == "composition_record_invalid" and res.effective is None
    assert f.compose_tolerance({"clock_tolerance_seconds": 5}, rec(TOL, {f.TOLERANCE_FIELD: 5})).code == "composition_caller_invalid"
    assert f.normalize_caller_tolerance({"clock_tolerance_seconds": 5}) is None


# ---- exhaustive composition: min(caller, registry), never above the caller
GRID_MAXAGE = (1, 2, 59, 60, 61, 300, 301, INT_MAX - 1, INT_MAX)
GRID_TOL = (0, 1, 2, 4, 5, 6, 10, INT_MAX - 1, INT_MAX)


@pytest.mark.parametrize("fam,grid", [(MAXAGE, GRID_MAXAGE), (TOL, GRID_TOL)], ids=["max_age", "tolerance"])
def test_composition_matrix_is_the_minimum_over_the_whole_grid(fam, grid):
    field = fam["field"]
    seen = 0
    for host, reg in itertools.product(grid, repeat=2):
        res = fam["composer"]({field: host}, rec(fam, {field: reg}))
        assert res.ok and res.code is None and res.deny_all is False and res.deny_all_fields == ()
        assert res.effective == {field: min(host, reg)} and type(res.effective[field]) is int
        assert res.effective[field] <= host and res.effective[field] <= reg
        assert res.detail == ((f.NOT_NARROWING + ":" + field) if reg > host else "")
        seen += 1
    assert seen == len(grid) ** 2


@BOTH
def test_registry_above_the_caller_is_reported_not_applied_and_equal_is_silent(fam):
    field = fam["field"]
    up = fam["composer"]({field: 60}, rec(fam, {field: 300}))
    assert up.ok and up.effective == {field: 60} and up.detail == "registry_value_not_narrowing:" + field
    down = fam["composer"]({field: 300}, rec(fam, {field: 60}))
    assert down.ok and down.effective == {field: 60} and down.detail == ""
    eq = fam["composer"]({field: 60}, rec(fam, {field: 60}))
    assert eq.ok and eq.effective == {field: 60} and eq.detail == ""


def test_the_tolerance_family_admits_registry_zero_and_the_max_age_family_does_not():
    zero = f.compose_tolerance({f.TOLERANCE_FIELD: 5}, rec(TOL, {f.TOLERANCE_FIELD: 0}))
    assert zero.ok and zero.effective == {f.TOLERANCE_FIELD: 0} and zero.deny_all is False
    assert f.compose_tolerance({f.TOLERANCE_FIELD: 0}, rec(TOL, {f.TOLERANCE_FIELD: 10})).effective == {f.TOLERANCE_FIELD: 0}
    bad = type("Rec", (), {"ok": True, "record": dict(t.record(family=f.FAMILY_MAX_AGE), payload={f.MAX_AGE_FIELD: 0})})()
    assert f.compose_max_age({f.MAX_AGE_FIELD: 60}, bad).code == "composition_record_invalid"
    assert f.compose_max_age({f.MAX_AGE_FIELD: 0}, rec(MAXAGE)).code == "composition_caller_invalid"


@BOTH
def test_the_decision_is_never_looser_than_the_caller(fam):
    field = fam["field"]
    for host in (fam["lo"], fam["lo"] + 5, 1000, INT_MAX):
        for reg in (fam["lo"], 7, 500, INT_MAX):
            res = fam["composer"]({field: host}, rec(fam, {field: reg}))
            assert res.effective[field] <= host


# ---- the caller domain: whole-caller refusal
@BOTH
@pytest.mark.parametrize("caller_value", [None, True, False, "300", 300.0, -1, INT_MAX + 1, 2 ** 31, 10 ** 12, 10 ** 30, b"1", [1], {"a": 1}, decimal.Decimal(1), I(5)])
def test_caller_outside_the_domain_refuses_the_whole_caller_and_is_never_replaced(fam, caller_value):
    res = fam["composer"]({fam["field"]: caller_value}, rec(fam))
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None and res.deny_all is False


def test_caller_zero_is_a_domain_violation_for_max_age_only():
    assert f.compose_max_age({f.MAX_AGE_FIELD: 0}, rec(MAXAGE)).code == "composition_caller_invalid"
    res = f.compose_tolerance({f.TOLERANCE_FIELD: 0}, rec(TOL, {f.TOLERANCE_FIELD: 7}))
    assert res.ok and res.effective == {f.TOLERANCE_FIELD: 0}


@BOTH
@pytest.mark.parametrize("caller", [None, {}, [], "x", 5, (1,), {"other": 5}, {"max_age_seconds": 5}, {"clock_tolerance_seconds": 5}, {1: 5}])
def test_malformed_callers_refuse(fam, caller):
    res = fam["composer"](caller, rec(fam))
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None


@BOTH
def test_caller_with_extra_or_foreign_members_refuses(fam):
    pl = {fam["field"]: 60, "x": 1}
    assert fam["composer"](pl, rec(fam)).code == "composition_caller_invalid"
    other = f.TOLERANCE_FIELD if fam is MAXAGE else f.MAX_AGE_FIELD
    assert fam["composer"]({other: 60}, rec(fam)).code == "composition_caller_invalid"


@BOTH
def test_host_none_policy_is_never_supplied_by_the_registry(fam):
    res = fam["composer"](None, rec(fam))
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None


@BOTH
def test_hostile_caller_mappings_are_read_once_and_bounded(fam):
    field = fam["field"]
    reads = []

    class Flip(Mapping):
        def __iter__(self):
            return iter([field])

        def __len__(self):
            return 1

        def __getitem__(self, k):
            reads.append(k)
            return 10 if len(reads) % 2 else INT_MAX

        def items(self):
            reads.append("items")
            return iter([(field, 10)])
    res = fam["composer"](Flip(), rec(fam, {field: 50}))
    assert res.ok and res.effective == {field: 10}

    class Endless(Mapping):
        def __iter__(self):
            return iter(range(10 ** 9))

        def __len__(self):
            return 10 ** 9

        def __getitem__(self, k):
            return 5

        def items(self):
            return (((field if i == 0 else "k%d" % i), 5) for i in itertools.count())
    assert fam["composer"](Endless(), rec(fam)).code == "composition_caller_invalid"


@BOTH
@pytest.mark.parametrize("operator", ["union", "", None, "Intersection", 1, b"intersection"])
def test_only_the_intersection_operator_is_supported(fam, operator):
    res = fam["composer"]({fam["field"]: 100}, rec(fam), operator)
    assert not res.ok and res.code == "composition_operator_unsupported" and res.effective is None


@BOTH
def test_invalid_or_foreign_records_refuse(fam):
    field = fam["field"]
    good = rec(fam, {field: 60})
    assert good.ok
    assert fam["composer"]({field: 100}, None).code == "composition_record_invalid"
    assert fam["composer"]({field: 100}, object()).code == "composition_record_invalid"
    other_fam = TOL if fam is MAXAGE else MAXAGE
    other_family = type("Rec", (), {"ok": True, "record": dict(good.record, family=other_fam["family"])})()
    assert fam["composer"]({field: 100}, other_family).code == "composition_family_unsupported"
    anchor_family = type("Rec", (), {"ok": True, "record": dict(good.record, family="f5-anchor-deadline-to-inputs-policy")})()
    assert fam["composer"]({field: 100}, anchor_family).code == "composition_family_unsupported"
    for bad in ("60", 60.0, True, -1, INT_MAX + 1, None, I(60)):
        bad_rec = type("Rec", (), {"ok": True, "record": dict(good.record, payload={field: bad})})()
        assert fam["composer"]({field: 100}, bad_rec).code == "composition_record_invalid", bad
    not_payload = type("Rec", (), {"ok": True, "record": dict(good.record, payload=[60])})()
    assert fam["composer"]({field: 100}, not_payload).code == "composition_record_invalid"
    not_ok = type("Rec", (), {"ok": False, "record": good.record})()
    assert fam["composer"]({field: 100}, not_ok).code == "composition_record_invalid"
    truthy = type("Rec", (), {"ok": 1, "record": good.record})()
    assert fam["composer"]({field: 100}, truthy).code == "composition_record_invalid"
    not_dict = type("Rec", (), {"ok": True, "record": [1]})()
    assert fam["composer"]({field: 100}, not_dict).code == "composition_record_invalid"
    sub = type("Rec", (), {"ok": True, "record": dict(good.record, family=S(fam["family"]))})()
    assert fam["composer"]({field: 100}, sub).code == "composition_family_unsupported"
    assert fam["composer"]({field: 100}, good).ok


# ---- record validation through the r08-v8 validator
@BOTH
def test_record_validation_codes(fam):
    field = fam["field"]
    assert rec(fam, {field: 60}).ok
    assert rec(fam, {field: "60"}).code == "field_type_invalid"
    assert rec(fam, {field: True}).code == "field_type_invalid"
    assert rec(fam, {field: None}).code == "field_type_invalid"
    assert rec(fam, {field: INT_MAX + 1}).code == "field_invalid"
    assert rec(fam, {field: -1}).code == "field_invalid"
    assert rec(fam, {}).code == "field_missing"
    assert rec(fam, {field: 60, "x": 1}).code == "field_unknown"
    assert rec(fam, {field: INT_MAX}).ok


@BOTH
@pytest.mark.parametrize("literal,code", [("5.0", "json_number_unsupported"), ("1e3", "json_number_unsupported"), ("NaN", "json_number_unsupported"),
                                          ("Infinity", "json_number_unsupported"), ("-Infinity", "json_number_unsupported"), ("true", "field_type_invalid"),
                                          ("false", "field_type_invalid"), ("null", "field_type_invalid"), ('"60"', "field_type_invalid"),
                                          ("99999999999999999999999999", None), ("-1", "field_invalid"), ("2147483648", "field_invalid")])
def test_non_int_or_out_of_range_json_literals_never_reach_composition(fam, literal, code):
    text = r.dumps(t.record(family=fam["family"], pl={fam["field"]: 60}))
    old = '"%s": 60' % fam["field"]
    text2 = text.replace(old, '"%s": %s' % (fam["field"], literal))
    assert text2 != text
    got = record_e.validate_record_text(profiles.V8, text2)
    assert not got.ok
    if code is not None:
        assert got.code == code


@BOTH
def test_record_zero_is_valid_only_for_the_tolerance_family(fam):
    got = rec(fam, {fam["field"]: 0})
    assert got.ok == (fam is TOL)
    if fam is MAXAGE:
        assert got.code == "field_invalid"


def test_the_registered_specs():
    for fam in (MAXAGE, TOL):
        spec = profiles.V8.families[fam["family"]].spec
        assert spec.enforcing_component == "control-plane" and spec.payload_fields == (fam["field"],) and spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING)
        assert spec.payload_validator is fam["validator"] and spec.composer is fam["composer"] and spec.caller_normalizer is fam["normalizer"]


@BOTH
def test_a_caller_mapping_is_read_for_at_most_two_items(fam):
    consumed = []
    field = fam["field"]

    class Counting(Mapping):
        def __iter__(self):
            return iter(())

        def __len__(self):
            return 10 ** 9

        def __getitem__(self, k):
            return 5

        def items(self):
            def gen():
                for i in itertools.count():
                    consumed.append(i)
                    yield (field if i == 0 else "k%d" % i), 5
            return gen()
    assert fam["normalizer"](Counting()) is None and len(consumed) == 2
    consumed.clear()
    assert fam["composer"](Counting(), rec(fam)).code == "composition_caller_invalid" and len(consumed) == 2


@BOTH
def test_a_dict_subclass_record_body_or_payload_is_refused_by_the_composer(fam):
    class D(dict):
        pass
    field = fam["field"]
    good = rec(fam, {field: 60})
    assert fam["composer"]({field: 100}, type("Rec", (), {"ok": True, "record": D(good.record)})()).code == "composition_record_invalid"
    assert fam["composer"]({field: 100}, type("Rec", (), {"ok": True, "record": dict(good.record, payload=D({field: 60}))})()).code == "composition_record_invalid"
    assert fam["composer"]({field: 100}, type("Rec", (), {"ok": True, "record": dict(good.record, payload={field: 60})})()).ok
