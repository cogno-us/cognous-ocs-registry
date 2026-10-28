"""M2 PR-1: `f1abc-local-execution-limits` payload validation, caller normalization and composition (BUILDER_TESTED; not independently qualified).

Covers: the seven-member schema, missing/extra members, types, the full representable integer boundary domain, zero semantics, invalid callers
(including every float form), deny-all propagation, set intersection, numeric minimum, refusal-without-policy, and an exhaustive no-widening grid
checked against an independent oracle.
"""
import decimal
import itertools
import json

import pytest

import r08v3_support as t
from registry_successor import common as c
from registry_successor import v2_f1ab
from registry_successor import v3_f1abc as f
from registry_successor import v3_families as fam
from registry_successor.compose import CompositionResult

A_MAX, E_MAX = 2 ** 53, 2 ** 53 - 1


class IntSub(int):
    pass


def rec_result(pl):
    return type("R", (), {"ok": True, "record": {"family": f.FAMILY_F1ABC, "payload": pl}})()


def compose(cl, pl, op="intersection"):
    return f.compose_f1abc(cl, rec_result(pl), op)


def refused(res, code):
    assert isinstance(res, CompositionResult)
    assert res.ok is False and res.code == code, res
    assert res.effective is None and res.deny_all is False and res.deny_all_fields == ()


# ---- schema: exactly seven members
def test_seven_members_exactly():
    assert f.F1ABC_FIELDS == ("allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains",
                              "max_amount", "max_effects")
    assert f.payload_validator(t.payload()) is None
    assert f.FAMILY_F1ABC == "f1abc-local-execution-limits"


@pytest.mark.parametrize("name", f.F1ABC_FIELDS)
def test_missing_member_refuses_field_missing(name):
    p = t.payload()
    del p[name]
    assert f.payload_validator(p) == "field_missing"


@pytest.mark.parametrize("extra", ["max_age", "deny_all", "allowed_targets", "max_amount ", "MAX_AMOUNT", ""])
def test_extra_member_refuses_field_unknown(extra):
    assert f.payload_validator(dict(t.payload(), **{extra: 1})) == "field_unknown"


def test_f1ab_only_payload_is_missing_the_ceilings():
    five = {k: t.payload()[k] for k in f.SET_FIELDS}
    assert f.payload_validator(five) == "field_missing"


@pytest.mark.parametrize("bad", [None, [], "x", 1, (), set()])
def test_non_dict_payload(bad):
    assert f.payload_validator(bad) == "field_type_invalid"


# ---- types
@pytest.mark.parametrize("name", f.SET_FIELDS)
@pytest.mark.parametrize("bad", ["a", ("a",), None, 1, {"a"}, {"a": 1}])
def test_set_member_must_be_a_list(name, bad):
    assert f.payload_validator(t.payload(**{name: bad})) == "field_type_invalid"


@pytest.mark.parametrize("name", f.CEILING_FIELDS)
@pytest.mark.parametrize("bad", [True, False, 5.0, 0.0, -0.0, 1e300, float("nan"), float("inf"), "5", None, decimal.Decimal(5), b"5", [5], {"v": 5},
                                 IntSub(5)])
def test_ceiling_must_be_an_exact_int(name, bad):
    assert f.payload_validator(t.payload(**{name: bad})) == "field_type_invalid"


# ---- full representable integer boundary domain
AMOUNT_OK = [0, 1, 2, 10 ** 9, A_MAX - 1, A_MAX]
AMOUNT_BAD = [-1, -(2 ** 53), A_MAX + 1, A_MAX + 2, 2 ** 63 - 1, 2 ** 63, 2 ** 64, 10 ** 30]
EFFECTS_OK = [0, 1, 2, 10 ** 9, E_MAX - 1, E_MAX]
EFFECTS_BAD = [-1, -(2 ** 53), E_MAX + 1, A_MAX, 2 ** 63 - 1, 2 ** 63, 2 ** 64, 10 ** 30]


@pytest.mark.parametrize("v", AMOUNT_OK)
def test_max_amount_valid_domain(v):
    assert f.payload_validator(t.payload(max_amount=v)) is None and f.is_registry_amount(v)


@pytest.mark.parametrize("v", AMOUNT_BAD)
def test_max_amount_invalid_domain(v):
    assert f.payload_validator(t.payload(max_amount=v)) == "field_invalid" and not f.is_registry_amount(v)


@pytest.mark.parametrize("v", EFFECTS_OK)
def test_max_effects_valid_domain(v):
    assert f.payload_validator(t.payload(max_effects=v)) is None and f.is_registry_effects(v)


@pytest.mark.parametrize("v", EFFECTS_BAD)
def test_max_effects_invalid_domain(v):
    assert f.payload_validator(t.payload(max_effects=v)) == "field_invalid" and not f.is_registry_effects(v)


def test_bounds_are_the_ruled_constants():
    assert (f.AMOUNT_MIN, f.AMOUNT_MAX) == (0, 2 ** 53) and (f.EFFECTS_MIN, f.EFFECTS_MAX) == (0, 2 ** 53 - 1)


def test_type_error_precedes_value_error():
    assert f.payload_validator(t.payload(max_amount=-1, max_effects=1.5)) == "field_type_invalid"
    assert f.payload_validator(t.payload(max_amount=-1, allowed_units=["b", "a"])) == "field_invalid"


# ---- f1ab set rules are the frozen validator's
@pytest.mark.parametrize("bad", [["b", "a"], ["a", "a"], ["*"], [""], ["a b"], ["x" * 129], [1]])
def test_set_value_rules_match_the_frozen_f1ab_validator(bad):
    five = {k: t.payload()[k] for k in f.SET_FIELDS}
    five["allowed_units"] = bad
    expected = v2_f1ab.payload_validator(five)
    got = f.payload_validator(t.payload(allowed_units=bad))
    assert got == expected and got is not None


def test_empty_set_is_a_valid_explicit_deny_all_record():
    assert f.payload_validator(t.payload(allowed_units=[])) is None


# ---- caller normalization
@pytest.mark.parametrize("bad", [5.0, 99.5, -0.0, 0.0, 1e300, float("nan"), float("inf"), True, False, "5", None, -1, A_MAX + 1, IntSub(5),
                                 decimal.Decimal(5), [5]])
def test_caller_max_amount_invalid_including_every_float(bad):
    assert f.normalize_caller(t.caller(max_amount=bad)) is None
    refused(compose(t.caller(max_amount=bad), t.payload()), "composition_caller_invalid")


@pytest.mark.parametrize("bad", [0, -1, True, False, 1.0, 5.5, float("nan"), "1", None, IntSub(3), decimal.Decimal(1), [1]])
def test_caller_max_effects_invalid(bad):
    assert f.normalize_caller(t.caller(max_effects=bad)) is None
    refused(compose(t.caller(max_effects=bad), t.payload()), "composition_caller_invalid")


@pytest.mark.parametrize("v", [0, 1, 12345, A_MAX])
def test_caller_max_amount_valid_domain(v):
    assert f.normalize_caller(t.caller(max_amount=v))["max_amount"] == v


@pytest.mark.parametrize("v", [1, 2, E_MAX, A_MAX, 2 ** 62, 2 ** 63, 10 ** 30])
def test_caller_max_effects_valid_domain_has_no_upper_bound(v):
    assert f.normalize_caller(t.caller(max_effects=v))["max_effects"] == v


def test_caller_shape():
    for drop in f.F1ABC_FIELDS:
        cl = t.caller()
        del cl[drop]
        refused(compose(cl, t.payload()), "composition_caller_invalid")
    refused(compose(dict(t.caller(), extra=1), t.payload()), "composition_caller_invalid")
    refused(compose(None, t.payload()), "composition_caller_invalid")
    refused(compose(["a"], t.payload()), "composition_caller_invalid")
    refused(compose(t.caller(allowed_units=["bad*"]), t.payload()), "composition_caller_invalid")
    refused(compose({"allowed_actions": []}, t.payload()), "composition_caller_invalid")


def test_caller_set_forms_accepted_like_f1ab():
    for form in (list, tuple, set, frozenset):
        res = compose(t.caller(allowed_units=form(["u-read", "u-write"])), t.payload())
        assert res.ok and res.effective["allowed_units"] == ("u-read",)


# ---- composition: intersection and minimum
def test_valid_composition_exact_result():
    res = compose(t.caller(), t.payload())
    assert res.ok and res.code is None and res.deny_all is False and res.deny_all_fields == ()
    assert res.effective == {"allowed_actions": ("act-copy", "act-list"), "allowed_adapters": ("a-local",), "allowed_units": ("u-read",),
                             "allowed_institutions": ("inst-a",), "allowed_authority_domains": ("domain-a",), "max_amount": 100, "max_effects": 3}
    assert res.detail == ""


def test_registry_below_equal_above_caller_for_each_ceiling():
    below = compose(t.caller(max_amount=500, max_effects=10), t.payload(max_amount=100, max_effects=3))
    assert below.effective["max_amount"] == 100 and below.effective["max_effects"] == 3 and below.detail == ""
    equal = compose(t.caller(max_amount=100, max_effects=3), t.payload(max_amount=100, max_effects=3))
    assert equal.effective["max_amount"] == 100 and equal.effective["max_effects"] == 3 and equal.detail == ""
    above = compose(t.caller(max_amount=50, max_effects=2), t.payload(max_amount=100, max_effects=3))
    assert above.ok and above.effective["max_amount"] == 50 and above.effective["max_effects"] == 2
    assert above.detail == "registry_value_not_narrowing:max_amount,max_effects"
    only = compose(t.caller(max_amount=500, max_effects=2), t.payload(max_amount=100, max_effects=3))
    assert only.detail == "registry_value_not_narrowing:max_effects" and only.effective["max_effects"] == 2


def test_registry_cannot_widen_sets():
    wide = t.payload(allowed_actions=["act-copy", "act-list", "act-zzz"], allowed_units=["u-new", "u-read", "u-write"])
    res = compose(t.caller(allowed_units=["u-read"], allowed_actions=["act-copy"]), wide)
    assert res.ok and res.effective["allowed_units"] == ("u-read",) and res.effective["allowed_actions"] == ("act-copy",)


def test_set_intersection_matches_f1ab_composition_exactly():
    for rs, cs in itertools.product([[], ["a"], ["a", "b"], ["b", "c"]], repeat=2):
        five_p = {k: t.payload()[k] for k in f.SET_FIELDS}
        five_c = {k: t.caller()[k] for k in f.SET_FIELDS}
        five_p["allowed_units"], five_c["allowed_units"] = rs, cs
        old = v2_f1ab.compose_f1ab(five_c, type("R", (), {"ok": True, "record": {"family": v2_f1ab.FAMILY_F1AB, "payload": five_p}})())
        new = compose(t.caller(allowed_units=cs), t.payload(allowed_units=rs))
        assert new.ok
        assert {k: new.effective[k] for k in f.SET_FIELDS} == old.effective
        assert set(new.deny_all_fields) - {"max_effects"} == set(old.deny_all_fields)


# ---- zero semantics and deny-all propagation
def test_zero_amount_is_a_valid_ceiling_not_deny_all():
    res = compose(t.caller(), t.payload(max_amount=0))
    assert res.ok and res.deny_all is False and res.effective["max_amount"] == 0 and res.deny_all_fields == ()


def test_zero_effects_is_explicit_deny_all():
    res = compose(t.caller(), t.payload(max_effects=0))
    assert res.ok and res.deny_all is True and res.deny_all_fields == ("max_effects",) and res.effective["max_effects"] == 0


def test_empty_effective_set_is_deny_all_and_combines():
    res = compose(t.caller(allowed_units=["u-write"]), t.payload(allowed_units=["u-read"], max_effects=0))
    assert res.ok and res.deny_all and res.deny_all_fields == ("allowed_units", "max_effects")
    assert res.effective["allowed_units"] == ()
    res2 = compose(t.caller(allowed_institutions=[]), t.payload())
    assert res2.deny_all and res2.deny_all_fields == ("allowed_institutions",)


def test_zero_caller_amount_with_registry_ceiling():
    res = compose(t.caller(max_amount=0), t.payload(max_amount=100))
    assert res.effective["max_amount"] == 0 and res.detail == "registry_value_not_narrowing:max_amount" and not res.deny_all


# ---- refusal carries no policy
def test_every_refusal_carries_no_effective_policy():
    cases = [
        compose(t.caller(), t.payload(), "union"), compose(t.caller(), t.payload(), None), compose(t.caller(), dict(t.payload(), x=1)),
        compose(t.caller(), t.payload(max_amount=5.0)), compose(t.caller(), t.payload(max_effects=E_MAX + 1)),
        f.compose_f1abc(t.caller(), None), f.compose_f1abc(t.caller(), type("R", (), {"ok": False})()),
        f.compose_f1abc(t.caller(), type("R", (), {"ok": True, "record": {"family": v2_f1ab.FAMILY_F1AB, "payload": t.payload()}})()),
        compose(t.caller(max_amount=1.5), t.payload()),
    ]
    for res in cases:
        assert res.ok is False and res.effective is None and res.deny_all is False and res.code in c.CODES
    assert cases[0].code == "composition_operator_unsupported"
    assert cases[2].code == "composition_record_invalid" and cases[3].code == "composition_record_invalid"
    assert cases[6].code == "composition_record_invalid" and cases[7].code == "composition_family_unsupported"


def test_family_and_operator_must_be_exact_str():
    class S(str):
        pass
    res = f.compose_f1abc(t.caller(), type("R", (), {"ok": True, "record": {"family": S(f.FAMILY_F1ABC), "payload": t.payload()}})())
    assert res.code == "composition_family_unsupported"
    refused(compose(t.caller(), t.payload(), S("intersection")), "composition_operator_unsupported")


# ---- exhaustive no-widening grid against an independent oracle
GRID_A = [0, 1, 2, 3, A_MAX - 1, A_MAX]
GRID_E = [1, 2, 3, E_MAX - 1, E_MAX, A_MAX, 2 ** 62]
REG_E = [0, 1, 2, 3, E_MAX - 1, E_MAX]


@pytest.mark.parametrize("ca,ra", list(itertools.product(GRID_A, GRID_A)))
def test_amount_grid_never_exceeds_caller_or_registry(ca, ra):
    res = compose(t.caller(max_amount=ca), t.payload(max_amount=ra))
    assert res.ok
    eff = res.effective["max_amount"]
    assert eff == (ca if ca <= ra else ra)  # oracle
    assert eff <= ca and eff <= ra
    assert (res.detail != "") == (ra > ca)


@pytest.mark.parametrize("ce,re_", list(itertools.product(GRID_E, REG_E)))
def test_effects_grid_never_exceeds_caller_or_registry(ce, re_):
    res = compose(t.caller(max_effects=ce), t.payload(max_effects=re_))
    assert res.ok
    eff = res.effective["max_effects"]
    assert eff == (ce if ce <= re_ else re_)
    assert eff <= ce and eff <= re_
    assert res.deny_all is (re_ == 0)


def test_composition_is_idempotent_and_does_not_mutate_inputs():
    cl, pl = t.caller(), t.payload()
    cl0, pl0 = json.dumps(cl, sort_keys=True), json.dumps(pl, sort_keys=True)
    first = compose(cl, pl)
    again = compose({**first.effective, **{k: list(first.effective[k]) for k in f.SET_FIELDS}}, pl)
    assert again.effective == first.effective
    assert json.dumps(cl, sort_keys=True) == cl0 and json.dumps(pl, sort_keys=True) == pl0


# ---- table
def test_table_registers_exactly_one_family():
    assert list(fam.FAMILIES_V3) == [f.FAMILY_F1ABC]
    spec = fam.lookup_v3(f.FAMILY_F1ABC)
    assert spec.payload_fields == f.F1ABC_FIELDS and spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING)
    for other in (v2_f1ab.FAMILY_F1AB, c.FAMILY_F1A, "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "F1ABC-LOCAL-EXECUTION-LIMITS",
                  f.FAMILY_F1ABC + " ", None, 1, b"x"):
        assert fam.lookup_v3(other) is None


def test_table_selection_accepts_only_r08_v3():
    assert fam.table_for_contract_version_v3("r08-v3").ok
    for bad in ("r08-v1", "r08-v2", "r08-v4", "R08-V3", "r08-v3 ", " r08-v3", "", None, 3, b"r08-v3", ("r08-v3",)):
        sel = fam.table_for_contract_version_v3(bad)
        assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
    refused(fam.compose_for_v3("r08-v2", t.caller(), rec_result(t.payload())), "contract_unsupported")
    assert fam.compose_for_v3("r08-v3", t.caller(), rec_result(t.payload())).ok
