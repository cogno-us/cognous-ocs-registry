"""`r08-v6` family `f5-terminal-revocation-enablement-policy`: payload validation and composition (BUILDER_TESTED; not independently qualified).

Pure: no signature backend is needed. The scalar `terminal_revocation` has the two-point order `on` (stricter: can only ADD the refusal
`grant_revocation_recorded`) < `off` (looser). Effective = `on` if either side is `on`. The Registry never sees which grants were revoked.
"""
import itertools
from collections.abc import Mapping

import pytest

import r08_support as r
import r08v6_support as t
from registry_successor import v6_families as fam
from registry_successor import v6_record
from registry_successor import v6_terminal_revocation as f

FIELD = f.TR_FIELD
ON, OFF = "on", "off"


def rec(pl=None, **over):
    return v6_record.validate_record_text_v6(r.dumps(t.record(pl, family=f.FAMILY_TR, **over)))


def test_vocabulary_is_the_closed_pair_strictest_first():
    assert f.VALUES == (ON, OFF) and f.ON == ON and f.OFF == OFF and f.TR_FIELDS == (FIELD,) and FIELD == "terminal_revocation"
    assert f.FAMILY_TR == "f5-terminal-revocation-enablement-policy"
    assert f.stricter(ON, OFF) == ON and f.stricter(OFF, ON) == ON and f.stricter(ON, ON) == ON and f.stricter(OFF, OFF) == OFF
    assert f.is_value(ON) and f.is_value(OFF)


@pytest.mark.parametrize("bad", ["On", "ON", " on", "on ", "off ", "OFF", "true", "false", "enabled", "disabled", "", "yes", "1", "on\n", "none"])
def test_unknown_or_respelled_values_are_field_invalid(bad):
    assert f.payload_validator({FIELD: bad}) == "field_invalid"
    assert not f.is_value(bad)


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, 1.0, b"on", ["on"], {"v": "on"}, {}])
def test_non_string_values_are_field_type_invalid_and_booleans_are_not_a_spelling(bad):
    assert f.payload_validator({FIELD: bad}) == "field_type_invalid"
    assert not f.is_value(bad)


def test_str_subclass_values_and_keys_are_refused():
    class S(str):
        pass
    assert f.payload_validator({FIELD: S("on")}) == "field_type_invalid"
    assert f.payload_validator({S(FIELD): "on"}) == "field_type_invalid"
    assert f.normalize_caller({FIELD: S("on")}) is None
    assert f.normalize_caller({S(FIELD): "on"}) is None
    assert not f.is_value(S("on")) and not f.is_value(S("off"))


def test_valid_payloads():
    assert f.payload_validator({FIELD: ON}) is None and f.payload_validator({FIELD: OFF}) is None


@pytest.mark.parametrize("payload,code", [
    ({}, "field_missing"), ({FIELD: ON, "extra": 1}, "field_unknown"), ({"other": ON}, "field_unknown"), ({"other": ON, FIELD: ON}, "field_unknown"),
    ({FIELD: {"class-a": ON}}, "field_type_invalid"),  # a map is not the scalar shape
    ({FIELD: [ON]}, "field_type_invalid"), ({FIELD: None}, "field_type_invalid"), ({1: ON}, "field_type_invalid"), ({FIELD: "maybe"}, "field_invalid"),
])
def test_payload_shape_codes(payload, code):
    assert f.payload_validator(payload) == code


def test_payload_must_be_an_exact_dict():
    class D(dict):
        pass
    assert f.payload_validator(D({FIELD: ON})) == "field_type_invalid"
    assert f.payload_validator([FIELD]) == "field_type_invalid"
    assert f.payload_validator(None) == "field_type_invalid"


# ---- the exhaustive 2x2 composition matrix
EXPECT = {(OFF, OFF): (OFF, ""), (OFF, ON): (ON, ""), (ON, OFF): (ON, "registry_value_not_narrowing:terminal_revocation"), (ON, ON): (ON, "")}


@pytest.mark.parametrize("host,reg", list(itertools.product((OFF, ON), repeat=2)))
def test_composition_matrix(host, reg):
    res = f.compose_tr({FIELD: host}, rec({FIELD: reg}))
    eff, detail = EXPECT[(host, reg)]
    assert res.ok and res.code is None and res.effective == {FIELD: eff} and res.detail == detail and res.deny_all is False and res.deny_all_fields == ()
    assert (eff == ON) == (ON in (host, reg)) and f._RANK[eff] <= f._RANK[host] and f._RANK[eff] <= f._RANK[reg]


def test_registry_off_over_a_caller_on_never_widens_and_is_reported():
    res = f.compose_tr({FIELD: ON}, rec({FIELD: OFF}))
    assert res.ok and res.effective == {FIELD: ON} and res.detail == "registry_value_not_narrowing:terminal_revocation"


def test_registry_off_over_off_is_off_and_not_reported_as_not_narrowing():
    res = f.compose_tr({FIELD: OFF}, rec({FIELD: OFF}))
    assert res.ok and res.effective == {FIELD: OFF} and res.detail == ""


def test_composition_is_pure_and_deterministic():
    host = {FIELD: OFF}
    a, b = f.compose_tr(host, rec({FIELD: ON})), f.compose_tr(host, rec({FIELD: ON}))
    assert a == b and a.effective == {FIELD: ON} and host == {FIELD: OFF}


# ---- refusals never carry a policy and never return the caller
@pytest.mark.parametrize("caller", [
    None, {}, {FIELD: "x"}, {FIELD: None}, {FIELD: True}, {FIELD: False}, {FIELD: 1}, {FIELD: ""}, {FIELD: "ON"}, {FIELD: {"class-a": ON}}, {FIELD: [ON]},
    {FIELD: ON, "extra": OFF}, {"other": ON}, {1: ON}, "on", 5, [FIELD], (FIELD, ON),
])
def test_invalid_caller_refuses_without_a_policy(caller):
    res = f.compose_tr(caller, rec())
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None and res.deny_all is False


def test_hostile_caller_mappings_are_read_once_and_bounded():
    class Flip(Mapping):
        def __init__(self):
            self.n = 0

        def __iter__(self):
            return iter([FIELD])

        def __len__(self):
            return 1

        def __getitem__(self, k):
            self.n += 1
            return ON if self.n % 2 else OFF

        def items(self):
            self.n += 1
            return iter([(FIELD, OFF)])
    res = f.compose_tr(Flip(), rec({FIELD: ON}))
    assert res.ok and res.effective == {FIELD: ON}

    class Endless(Mapping):
        def __iter__(self):
            return iter(range(10 ** 9))

        def __len__(self):
            return 10 ** 9

        def __getitem__(self, k):
            return ON

        def items(self):
            return (((("c%d" % i)), ON) for i in itertools.count())
    assert f.compose_tr(Endless(), rec()).code == "composition_caller_invalid"

    class Boom(Mapping):
        def __iter__(self):
            raise RuntimeError("x")

        def __len__(self):
            return 1

        def __getitem__(self, k):
            raise RuntimeError("x")

        def items(self):
            raise RuntimeError("x")
    assert f.compose_tr(Boom(), rec()).code == "composition_caller_invalid"


@pytest.mark.parametrize("operator", ["union", "", None, "Intersection", 1])
def test_only_the_intersection_operator_is_supported(operator):
    res = f.compose_tr({FIELD: OFF}, rec({FIELD: ON}), operator)
    assert not res.ok and res.code == "composition_operator_unsupported" and res.effective is None


def test_invalid_or_foreign_records_refuse():
    good = rec({FIELD: ON})
    assert good.ok
    assert f.compose_tr({FIELD: OFF}, None).code == "composition_record_invalid"
    assert f.compose_tr({FIELD: OFF}, object()).code == "composition_record_invalid"
    other_family = type("Rec", (), {"ok": True, "record": dict(good.record, family="f5-action-class-revocation-assurance-policy")})()
    assert f.compose_tr({FIELD: OFF}, other_family).code == "composition_family_unsupported"
    bad_payload = type("Rec", (), {"ok": True, "record": dict(good.record, payload={FIELD: "x"})})()
    assert f.compose_tr({FIELD: OFF}, bad_payload).code == "composition_record_invalid"
    not_dict = type("Rec", (), {"ok": True, "record": dict(good.record, payload=[FIELD])})()
    assert f.compose_tr({FIELD: OFF}, not_dict).code == "composition_record_invalid"
    not_ok = type("Rec", (), {"ok": False, "record": good.record})()
    assert f.compose_tr({FIELD: OFF}, not_ok).code == "composition_record_invalid"
    assert f.compose_tr({FIELD: OFF}, type("Rec", (), {"ok": True, "record": [1]})()).code == "composition_record_invalid"


def test_normalize_caller_returns_a_private_copy_or_none():
    src = {FIELD: ON}
    out = f.normalize_caller(src)
    assert out == src and out is not src
    assert f.normalize_caller({FIELD: OFF}) == {FIELD: OFF}
    assert f.normalize_caller({FIELD: "x"}) is None and f.normalize_caller({}) is None and f.normalize_caller(None) is None


def test_valid_record_is_accepted_and_malformed_ones_carry_the_shape_codes():
    assert rec().ok
    assert rec({FIELD: "enabled"}).code == "field_invalid"
    assert rec({FIELD: True}).code == "field_type_invalid"
    assert rec({FIELD: {"class-a": ON}}).code == "field_type_invalid"
    assert rec({}).code == "field_missing"
    assert rec({FIELD: ON, "x": 1}).code == "field_unknown"


def test_the_family_is_registered_in_the_v6_table_with_its_own_normalizer():
    spec = fam.lookup_v6(f.FAMILY_TR)
    assert spec.enforcing_component == "control-plane" and spec.payload_fields == (FIELD,) and spec.composer is f.compose_tr
    assert spec.caller_normalizer is f.normalize_caller and spec.payload_validator is f.payload_validator
    assert fam.compose_for_v6("r08-v6", {FIELD: OFF}, rec({FIELD: ON})).effective == {FIELD: ON}
    assert fam.compose_for_v6("r08-v5", {FIELD: OFF}, rec({FIELD: ON})).code == "contract_unsupported"
    assert fam.compose_for_v6("r08-v6", {FIELD: OFF}, rec({FIELD: ON}), "union").code == "composition_operator_unsupported"


def test_composer_dispatch_goes_by_record_family_and_a_caller_of_the_other_shape_is_invalid():
    ra_rec = v6_record.validate_record_text_v6(r.dumps(t.record()))
    assert ra_rec.ok
    # the dispatcher uses the RECORD's family: a class-map record composes with a class-map caller only
    assert fam.compose_for_v6("r08-v6", t.caller(), ra_rec).ok
    assert fam.compose_for_v6("r08-v6", {FIELD: OFF}, ra_rec).code == "composition_caller_invalid"
    tr_rec = rec({FIELD: ON})
    assert fam.compose_for_v6("r08-v6", t.caller(), tr_rec).code == "composition_caller_invalid"
    # a family composer handed the other family's record refuses by family, never composes
    assert f.compose_tr({FIELD: OFF}, ra_rec).code == "composition_family_unsupported"
    from registry_successor import v6_class_revocation_assurance as ra
    assert ra.compose_f5ra(t.caller(), tr_rec).code == "composition_family_unsupported"
    unknown = type("Rec", (), {"ok": True, "record": {"family": "nope", "payload": {}}})()
    assert fam.compose_for_v6("r08-v6", {FIELD: OFF}, unknown).code == "composition_family_unsupported"
    assert fam.compose_for_v6("r08-v6", {FIELD: OFF}, None).code == "composition_record_invalid"
