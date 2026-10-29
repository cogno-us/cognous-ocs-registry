"""`r08-v8` family `f5-anchor-deadline-to-inputs-policy`: payload validation and composition (APPROVED CANDIDATE; BUILDER_TESTED; not independently qualified).

Pure: no signature backend is needed. The only relation asserted is the two-point order `anchor` (stricter) < `no_change` (looser). The Registry can never assert false:
there is no such word in the vocabulary and a JSON boolean is a type refusal. Registering the family enables no consumer.
"""
import itertools
from collections.abc import Mapping

import pytest

import r08_support as r
import r08v8_support as t
from registry_successor import common as c
from registry_successor.engine import families_anchor as f
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e

FIELD = f.ANCHOR_FIELD
A, N = "anchor", "no_change"


def rec(pl=None, **over):
    return record_e.validate_record_text(profiles.V8, r.dumps(t.record(pl, family=f.FAMILY_ANCHOR, **over)))


# ---- vocabulary and order
def test_vocabulary_is_the_closed_pair_strictest_first_and_names_no_false():
    assert f.VALUES == (A, N) and f.ANCHOR == A and f.NO_CHANGE == N and f.ANCHOR_FIELDS == (FIELD,) and f.ANCHOR_FIELD == "anchor_deadline_to_inputs"
    assert f.stricter(A, N) == A and f.stricter(N, A) == A and f.stricter(A, A) == A and f.stricter(N, N) == N
    assert f.SCHEMA_REVISION == 1 and type(f.SCHEMA_REVISION) is int and f.NOT_NARROWING == "registry_value_not_narrowing"
    assert f.FAMILY_ANCHOR == "f5-anchor-deadline-to-inputs-policy"
    for word in ("false", "False", "off", "no", "disabled", "unanchor", "unanchored", "none", "0", "no-change"):
        assert word not in f.VALUES and not f.is_value(word)


@pytest.mark.parametrize("bad", ["Anchor", "ANCHOR", " anchor", "anchor ", "anchor\n", "true", "false", "True", "False", "on", "off", "", "no-change", "No_Change", "NO_CHANGE",
                                 "none", "unanchor", "аnchor", "anchor\x00"])
def test_unknown_or_respelled_values_are_field_invalid(bad):
    assert f.payload_validator({FIELD: bad}) == "field_invalid"
    assert f.normalize_caller({FIELD: bad}) is None


@pytest.mark.parametrize("bad", [None, True, False, 0, 1, 1.0, b"anchor", ["anchor"], {"v": "anchor"}, ("anchor",)])
def test_non_string_values_including_json_booleans_are_field_type_invalid(bad):
    assert f.payload_validator({FIELD: bad}) == "field_type_invalid"
    assert f.normalize_caller({FIELD: bad}) is None


def test_str_subclass_values_and_keys_are_refused_not_compared_by_value():
    class S(str):
        pass
    assert f.payload_validator({FIELD: S("anchor")}) == "field_type_invalid"
    assert f.payload_validator({S(FIELD): "anchor"}) == "field_type_invalid"
    assert f.normalize_caller({FIELD: S("anchor")}) is None
    assert f.normalize_caller({S(FIELD): "anchor"}) is None
    assert not f.is_value(S("anchor"))


def test_payload_must_be_an_exact_dict():
    class D(dict):
        pass
    assert f.payload_validator(D({FIELD: A})) == "field_type_invalid"
    assert f.payload_validator([FIELD]) == "field_type_invalid"
    assert f.payload_validator(None) == "field_type_invalid"
    assert f.payload_validator("anchor") == "field_type_invalid"


@pytest.mark.parametrize("payload,code", [
    ({}, "field_missing"), ({FIELD: A, "extra": 1}, "field_unknown"), ({"other": A}, "field_unknown"), ({1: A}, "field_type_invalid"),
    ({FIELD: A, 1: A}, "field_type_invalid"), ({"anchor": A}, "field_unknown"), ({"terminal_revocation": "enable"}, "field_unknown"),
    ({"class_irreversible": {"class-a": "irreversible"}}, "field_unknown"), ({"observation_max_age_seconds": 60}, "field_unknown"),
    ({FIELD: {"class-a": A}}, "field_type_invalid"), ({FIELD: "true"}, "field_invalid"),
])
def test_payload_shape_codes(payload, code):
    assert f.payload_validator(payload) == code


# ---- the exhaustive 2x2 composition matrix: narrowing only, never widening, never false
@pytest.mark.parametrize("host,reg", list(itertools.product((A, N), repeat=2)))
def test_composition_matrix_is_anchor_if_either_side_is_anchor(host, reg):
    res = f.compose_anchor({FIELD: host}, rec({FIELD: reg}))
    assert res.ok and res.deny_all is False and res.deny_all_fields == () and res.code is None
    expected = A if A in (host, reg) else N
    assert res.effective == {FIELD: expected}
    assert f._RANK[res.effective[FIELD]] <= f._RANK[host] and f._RANK[res.effective[FIELD]] <= f._RANK[reg]
    assert res.detail == ((f.NOT_NARROWING + ":" + FIELD) if (reg, host) == (N, A) else "")


def test_a_registry_no_change_never_lowers_a_caller_anchor_and_reports_it():
    res = f.compose_anchor({FIELD: A}, rec({FIELD: N}))
    assert res.ok and res.effective == {FIELD: A} and res.detail == "registry_value_not_narrowing:anchor_deadline_to_inputs"


def test_no_change_over_no_change_is_no_change_without_a_report():
    res = f.compose_anchor({FIELD: N}, rec({FIELD: N}))
    assert res.ok and res.effective == {FIELD: N} and res.detail == ""


def test_the_family_can_never_produce_a_false_or_a_bool():
    for host, reg in itertools.product((A, N), repeat=2):
        eff = f.compose_anchor({FIELD: host}, rec({FIELD: reg})).effective[FIELD]
        assert type(eff) is str and eff in (A, N)
    for bad in (True, False):
        assert f.compose_anchor({FIELD: bad}, rec()).code == "composition_caller_invalid"
        assert f.compose_anchor({FIELD: N}, type("Rec", (), {"ok": True, "record": dict(rec().record, payload={FIELD: bad})})()).code == "composition_record_invalid"


def test_composition_is_pure_and_does_not_mutate_the_caller():
    host = {FIELD: N}
    r1, r2 = f.compose_anchor(host, rec()), f.compose_anchor(host, rec())
    assert r1 == r2 and host == {FIELD: N}


# ---- refusals never carry a policy and never return the caller
@pytest.mark.parametrize("caller", [None, {}, {FIELD: None}, {FIELD: True}, {FIELD: False}, {FIELD: "x"}, {FIELD: 1}, {FIELD: "Anchor"}, {FIELD: A, "extra": A},
                                    {"other": A}, {1: A}, [FIELD], "anchor", A, 5, {FIELD: [A]}, {FIELD: {"class-a": A}}])
def test_invalid_caller_refuses_without_a_policy(caller):
    res = f.compose_anchor(caller, rec())
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None and res.deny_all is False


def test_hostile_caller_mappings_are_read_once_and_bounded():
    reads = []

    class Flip(Mapping):
        def __iter__(self):
            return iter([FIELD])

        def __len__(self):
            return 1

        def __getitem__(self, k):
            reads.append(k)
            return A if len(reads) % 2 else N

        def items(self):
            reads.append("items")
            return iter([(FIELD, N)])
    res = f.compose_anchor(Flip(), rec({FIELD: A}))
    assert res.ok and res.effective == {FIELD: A} and res.detail == ""

    class Endless(Mapping):
        def __iter__(self):
            return iter(range(10 ** 9))

        def __len__(self):
            return 10 ** 9

        def __getitem__(self, k):
            return A

        def items(self):
            return (((FIELD if i == 0 else "k%d" % i), A) for i in itertools.count())
    assert f.compose_anchor(Endless(), rec()).code == "composition_caller_invalid"

    class Raises(Mapping):
        def __iter__(self):
            raise RuntimeError

        def __len__(self):
            return 1

        def __getitem__(self, k):
            raise RuntimeError

        def items(self):
            raise RuntimeError
    assert f.compose_anchor(Raises(), rec()).code == "composition_caller_invalid"


@pytest.mark.parametrize("operator", ["union", "", None, "Intersection", 1, b"intersection"])
def test_only_the_intersection_operator_is_supported(operator):
    res = f.compose_anchor({FIELD: N}, rec({FIELD: A}), operator)
    assert not res.ok and res.code == "composition_operator_unsupported" and res.effective is None


def test_invalid_or_foreign_records_refuse():
    good = rec({FIELD: A})
    assert good.ok
    assert f.compose_anchor({FIELD: N}, None).code == "composition_record_invalid"
    assert f.compose_anchor({FIELD: N}, object()).code == "composition_record_invalid"
    other_family = type("Rec", (), {"ok": True, "record": dict(good.record, family="f5-observation-max-age-policy")})()
    assert f.compose_anchor({FIELD: N}, other_family).code == "composition_family_unsupported"
    bad_payload = type("Rec", (), {"ok": True, "record": dict(good.record, payload={FIELD: "x"})})()
    assert f.compose_anchor({FIELD: N}, bad_payload).code == "composition_record_invalid"
    bool_payload = type("Rec", (), {"ok": True, "record": dict(good.record, payload={FIELD: True})})()
    assert f.compose_anchor({FIELD: N}, bool_payload).code == "composition_record_invalid"
    not_payload = type("Rec", (), {"ok": True, "record": dict(good.record, payload=[A])})()
    assert f.compose_anchor({FIELD: N}, not_payload).code == "composition_record_invalid"
    not_ok = type("Rec", (), {"ok": False, "record": good.record})()
    assert f.compose_anchor({FIELD: N}, not_ok).code == "composition_record_invalid"
    truthy = type("Rec", (), {"ok": 1, "record": good.record})()
    assert f.compose_anchor({FIELD: N}, truthy).code == "composition_record_invalid"
    not_dict = type("Rec", (), {"ok": True, "record": [1]})()
    assert f.compose_anchor({FIELD: N}, not_dict).code == "composition_record_invalid"
    sub_family = type("S", (str,), {})(f.FAMILY_ANCHOR)
    sub = type("Rec", (), {"ok": True, "record": dict(good.record, family=sub_family)})()
    assert f.compose_anchor({FIELD: N}, sub).code == "composition_family_unsupported"
    assert f.compose_anchor({FIELD: N}, good).ok


# ---- record validation through the r08-v8 validator
def test_valid_record_is_accepted_and_malformed_ones_carry_the_shape_codes():
    assert rec().ok
    assert rec({FIELD: "off"}).code == "field_invalid"
    assert rec({FIELD: True}).code == "field_type_invalid"
    assert rec({FIELD: 1}).code == "field_type_invalid"
    assert rec({}).code == "field_missing"
    assert rec({FIELD: A, "x": 1}).code == "field_unknown"


def test_record_digest_text_with_a_json_boolean_is_a_type_refusal_not_a_value():
    for literal, code in (("true", "field_type_invalid"), ("false", "field_type_invalid"), ("null", "field_type_invalid"), ("1", "field_type_invalid"),
                          ("1.0", "json_number_unsupported")):
        text = r.dumps(t.record(family=f.FAMILY_ANCHOR)).replace('"anchor_deadline_to_inputs": "anchor"', '"anchor_deadline_to_inputs": ' + literal)
        assert record_e.validate_record_text(profiles.V8, text).code == code, literal


def test_the_family_registration_facts():
    spec = profiles.V8.families[f.FAMILY_ANCHOR].spec
    assert spec.enforcing_component == "control-plane" and spec.payload_fields == (FIELD,) and spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING)
    assert spec.payload_validator is f.payload_validator and spec.composer is f.compose_anchor and spec.caller_normalizer is f.normalize_caller


def test_a_caller_mapping_is_read_for_at_most_two_items():
    """The snapshot bound is `len(fields) + 1`: one item more than the single member is enough to refuse, and never more is consumed."""
    consumed = []

    class Counting(Mapping):
        def __iter__(self):
            return iter(())

        def __len__(self):
            return 10 ** 9

        def __getitem__(self, k):
            return A

        def items(self):
            def gen():
                for i in itertools.count():
                    consumed.append(i)
                    yield (FIELD if i == 0 else "k%d" % i), A
            return gen()
    assert f.normalize_caller(Counting()) is None and len(consumed) == 2
    consumed.clear()
    assert f.compose_anchor(Counting(), rec()).code == "composition_caller_invalid" and len(consumed) == 2


def test_a_dict_subclass_record_body_or_payload_is_refused_by_the_composer():
    class D(dict):
        pass
    good = rec({FIELD: A})
    assert f.compose_anchor({FIELD: N}, type("Rec", (), {"ok": True, "record": D(good.record)})()).code == "composition_record_invalid"
    assert f.compose_anchor({FIELD: N}, type("Rec", (), {"ok": True, "record": dict(good.record, payload=D({FIELD: A}))})()).code == "composition_record_invalid"
    assert f.compose_anchor({FIELD: N}, type("Rec", (), {"ok": True, "record": dict(good.record, payload={FIELD: A})})()).ok


def test_the_validated_payload_copy_is_a_defence_against_mutation_after_validation():
    """Deterministic kill of the aliasing mutant (`snap = payload`): the caller mapping is read AFTER the registry payload was validated and BEFORE the registry value is used,
    and its `items()` mutates the live payload dict (what another thread, a signal handler or a finalizer could do). The composer must use the validated copy."""
    for mutated in (N, "false", True, 0):
        live = {FIELD: A}
        shell = type("Rec", (), {"ok": True, "record": dict(rec({FIELD: A}).record, payload=live)})()
        fired = []

        class Mutating(Mapping):
            def __iter__(self):
                return iter([FIELD])

            def __len__(self):
                return 1

            def __getitem__(self, k):
                return N

            def items(self):
                live[FIELD] = mutated  # after the registry payload was validated
                fired.append(1)
                return iter([(FIELD, N)])
        res = f.compose_anchor(Mutating(), shell)
        assert fired == [1] and live[FIELD] == mutated
        assert res.ok and res.code is None and res.effective == {FIELD: A} and res.detail == ""
