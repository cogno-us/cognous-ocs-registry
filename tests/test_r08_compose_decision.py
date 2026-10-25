"""R08-S01 Lane C developer tests: F1a composition and per-operation decision. DEVELOPER-TESTED, not independently qualified.

Record and report objects are local stand-ins so these tests do not depend on record.py or verify.py.
"""
import itertools
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import r08_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor.compose import compose_f1a  # noqa: E402
from registry_successor.decision import decide_policy  # noqa: E402

F = c.F1A_FIELDS


@dataclass(frozen=True)
class Rec:
    ok: bool = True
    code: Optional[str] = None
    detail: str = ""
    record: Any = None
    record_digest: Optional[str] = None


@dataclass(frozen=True)
class Rep:
    ok: bool = True
    code: Optional[str] = None
    participation: Optional[str] = None


def rec(**payload):
    base = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a", "unit-b"]}
    base.update(payload)
    return Rec(record=s.make_record(payload=base))


def caller(**over):
    base = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"], "allowed_units": ["unit-b", "unit-c"]}
    base.update(over)
    return base


# ---- composition ----

def test_intersection_per_field_sorted_tuples():
    r = compose_f1a(caller(), rec())
    assert r.ok and r.code is None and not r.deny_all and r.deny_all_fields == ()
    assert r.effective == {"allowed_actions": ("write-file",), "allowed_adapters": ("local-fs",), "allowed_units": ("unit-b",)}


def test_caller_accepts_sets_tuples_and_collapses_duplicates():
    r = compose_f1a({"allowed_actions": {"write-file"}, "allowed_adapters": ("local-fs", "local-fs"), "allowed_units": frozenset({"unit-a"})}, rec())
    assert r.ok and r.effective["allowed_adapters"] == ("local-fs",)


@pytest.mark.parametrize("empty", F)
def test_empty_record_dimension_is_valid_deny_all(empty):
    r = compose_f1a(caller(), rec(**{empty: []}))
    assert r.ok and r.deny_all and r.deny_all_fields == (empty,) and r.effective[empty] == ()


def test_empty_intersection_is_valid_deny_all():
    r = compose_f1a(caller(allowed_units=["unit-z"]), rec())
    assert r.ok and r.deny_all and r.deny_all_fields == ("allowed_units",)


def test_caller_empty_dimension_is_deny_all():
    r = compose_f1a(caller(allowed_actions=[]), rec())
    assert r.ok and r.deny_all and r.deny_all_fields == ("allowed_actions",)


def test_all_dimensions_empty_lists_all_fields():
    r = compose_f1a({f: [] for f in F}, rec(**{f: [] for f in F}))
    assert r.ok and r.deny_all and r.deny_all_fields == F


def test_exhaustive_small_universe_matches_set_intersection_and_never_widens():
    universe = ["a", "b", "c"]
    subsets = [list(x) for n in range(len(universe) + 1) for x in itertools.combinations(universe, n)]
    for cal, reg in itertools.product(subsets, subsets):
        r = compose_f1a({f: cal for f in F}, rec(**{f: reg for f in F}))
        assert r.ok
        for f in F:
            assert set(r.effective[f]) == set(cal) & set(reg)
            assert set(r.effective[f]) <= set(cal) and set(r.effective[f]) <= set(reg)
            assert list(r.effective[f]) == sorted(r.effective[f])
        assert r.deny_all == any(not r.effective[f] for f in F)


def test_registry_superset_does_not_widen_caller():
    r = compose_f1a(caller(allowed_units=["unit-b"]), rec(allowed_units=["unit-a", "unit-b", "unit-c", "unit-d"]))
    assert r.effective["allowed_units"] == ("unit-b",)


@pytest.mark.parametrize("op", ["union", "", None, "INTERSECTION", "min", 3])
def test_unsupported_operator_refuses(op):
    r = compose_f1a(caller(), rec(), op)
    assert not r.ok and r.code == "composition_operator_unsupported" and r.effective is None


def test_wrong_family_refuses():
    r = compose_f1a(caller(), Rec(record=dict(s.make_record(), family="f1b-other")))
    assert not r.ok and r.code == "composition_family_unsupported"


def test_record_not_ok_or_shapeless_refuses():
    assert compose_f1a(caller(), Rec(ok=False, code="digest_mismatch")).code == "composition_record_invalid"
    assert compose_f1a(caller(), Rec(record=None)).code == "composition_record_invalid"
    assert compose_f1a(caller(), None).code == "composition_record_invalid"
    broken = s.make_record()
    broken["payload"] = {"allowed_actions": ["x"]}
    assert compose_f1a(caller(), Rec(record=broken)).code == "composition_record_invalid"
    unsorted = s.make_record()
    unsorted["payload"] = {f: ["b", "a"] for f in F}
    assert compose_f1a(caller(), Rec(record=unsorted)).code == "composition_record_invalid"


@pytest.mark.parametrize("bad", [
    None, "allowed_units", [], {"allowed_actions": ["a"]},
    {**{f: ["a"] for f in F}, "extra": ["a"]},
    {**{f: ["a"] for f in F}, "allowed_units": "unit-a"},
    {**{f: ["a"] for f in F}, "allowed_units": ["*"]},
    {**{f: ["a"] for f in F}, "allowed_units": [1]},
    {**{f: ["a"] for f in F}, "allowed_units": None},
    {**{f: ["a"] for f in F}, "allowed_units": ["a\nb"]},
])
def test_caller_invalid_refuses(bad):
    r = compose_f1a(bad, rec())
    assert not r.ok and r.code == "composition_caller_invalid" and r.effective is None


def test_composition_is_deterministic_and_does_not_mutate_inputs():
    cal = caller()
    before = {k: list(v) for k, v in cal.items()}
    record = rec()
    first = compose_f1a(cal, record)
    assert compose_f1a(cal, record) == first
    assert cal == before


def test_all_composition_codes_are_in_closed_set():
    for r in (compose_f1a(None, rec()), compose_f1a(caller(), rec(), "x"), compose_f1a(caller(), None)):
        assert r.code in c.CODES and c.CODES[r.code][0] == "composition"


# ---- decision ----

OK = Rep(ok=True)


def test_applied_and_deny_all_kinds():
    d = decide_policy("required", caller(), rec(), OK)
    assert d.kind == "applied" and d.code is None and not d.caller_unchanged and not d.deny_all
    assert d.effective["allowed_units"] == ("unit-b",)
    d = decide_policy("optional", caller(allowed_units=["unit-z"]), rec(), OK)
    assert d.kind == "applied_deny_all" and d.deny_all and d.deny_all_fields == ("allowed_units",)


def test_operationally_authorized_is_always_false():
    for p in ("required", "optional"):
        assert decide_policy(p, caller(), rec(), OK).operationally_authorized is False
        assert decide_policy(p, caller(), rec(), None).operationally_authorized is False
    assert decide_policy("required", caller(), rec(), Rep(ok=True, code=None)).operationally_authorized is False


def refusal_sources():
    return {
        "missing_selection": ((rec(), None), "selection_missing"),
        "bad_report": ((rec(), Rep(ok=False, code="signature_invalid")), "signature_invalid"),
        "bad_report_unknown_code": ((rec(), Rep(ok=False, code="not-a-code")), "selection_missing"),
        "missing_record": ((None, OK), "composition_record_invalid"),
        "bad_record": ((Rec(ok=False, code="digest_mismatch"), OK), "digest_mismatch"),
        "bad_record_no_code": ((Rec(ok=False), OK), "composition_record_invalid"),
        "wrong_family": ((Rec(record=dict(s.make_record(), family="other")), OK), "composition_family_unsupported"),
        "selection_participation_differs": ((rec(), Rep(ok=True, participation="optional")), "participation_mismatch"),
    }


@pytest.mark.parametrize("name", sorted(refusal_sources()))
def test_required_refusal_never_returns_caller_policy(name):
    (record, report), code = refusal_sources()[name]
    if name == "selection_participation_differs":
        d = decide_policy("required", caller(), record, report)
    else:
        d = decide_policy("required", caller(), record, report)
    assert d.kind == "required_policy_unavailable"
    assert d.effective is None and d.caller_unchanged is False and d.code == code and not d.deny_all


@pytest.mark.parametrize("name", sorted(refusal_sources()))
def test_optional_refusal_is_overlay_not_applied_caller_unchanged(name):
    (record, report), code = refusal_sources()[name]
    if name == "selection_participation_differs":
        report = Rep(ok=True, participation="required")
        code = "participation_mismatch"
    d = decide_policy("optional", caller(), record, report)
    assert d.kind == "overlay_not_applied" and d.caller_unchanged is True and d.code == code
    assert d.effective == {f: tuple(sorted(caller()[f])) for f in F}
    assert d.deny_all is False  # not denial


def test_composition_failure_distinguished_by_participation():
    bad = caller()
    bad["allowed_units"] = "unit-b"
    req = decide_policy("required", bad, rec(), OK)
    opt = decide_policy("optional", bad, rec(), OK)
    assert req.kind == "required_policy_unavailable" and req.code == "composition_caller_invalid" and req.effective is None
    assert opt.kind == "overlay_not_applied" and opt.code == "composition_caller_invalid" and opt.effective == bad


def test_invalid_participation_value_fails_closed_as_required():
    for p in (None, "", "mandatory", "REQUIRED", 1):
        d = decide_policy(p, caller(), rec(), OK)
        assert d.kind == "required_policy_unavailable" and d.code == "participation_mismatch" and d.effective is None


def test_matching_selection_participation_is_accepted():
    assert decide_policy("required", caller(), rec(), Rep(ok=True, participation="required")).kind == "applied"
    assert decide_policy("optional", caller(), rec(), Rep(ok=True, participation="optional")).kind == "applied"


def test_five_way_distinction_has_distinct_observable_outcomes():
    cases = {
        "valid_deny_all": decide_policy("required", caller(), rec(allowed_units=[]), OK),
        "field_absent": decide_policy("required", caller(), Rec(record={**s.make_record(), "payload": {"allowed_actions": []}}), OK),
        "invalid_record": decide_policy("required", caller(), Rec(ok=False, code="field_invalid"), OK),
        "missing_required_selection": decide_policy("required", caller(), rec(), None),
        "optional_overlay_refusal": decide_policy("optional", caller(), rec(), None),
    }
    assert cases["valid_deny_all"].kind == "applied_deny_all" and cases["valid_deny_all"].code is None
    assert cases["field_absent"].kind == "required_policy_unavailable" and cases["field_absent"].code == "composition_record_invalid"
    assert cases["invalid_record"].code == "field_invalid"
    assert cases["missing_required_selection"].kind == "required_policy_unavailable" and cases["missing_required_selection"].code == "selection_missing"
    assert cases["optional_overlay_refusal"].kind == "overlay_not_applied" and cases["optional_overlay_refusal"].caller_unchanged
    outcomes = {(d.kind, d.code) for d in cases.values()}
    assert len(outcomes) == len(cases)


def test_missing_required_selection_never_falls_back_to_broader_caller():
    broad = {f: ["a", "b", "c", "d"] for f in F}
    d = decide_policy("required", broad, rec(allowed_units=["a"]), None)
    assert d.effective is None and d.kind == "required_policy_unavailable"


def test_decision_deterministic_and_never_raises_on_garbage():
    for args in [("required", object(), object(), object()), ("optional", None, None, None), (object(), 1, 2, 3)]:
        d = decide_policy(*args)
        assert d.kind in ("overlay_not_applied", "required_policy_unavailable") and d.operationally_authorized is False
        assert decide_policy(*args) == d
