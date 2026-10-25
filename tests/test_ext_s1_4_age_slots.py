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
    "docs/decisions/2026-10-25-dr-cp-age-1.md": "f73e43490d90dac04f40c4adf2241259951290fcdb314679eebd87ce6ede7b38",
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
    assert "## What the characterization does and does not establish" in text
    doc = (ROOT / "docs/ext-implementation/ext-s1-4-age-integer-slots.md").read_text(encoding="utf-8")
    assert "## What the characterization does and does not establish" in doc
    for needle in ("7a4bcd40b3b49e61ff3c294dcca53b52f460b22c", "date value out of range", "MUST apply its own stricter bounds", "2**34"):
        assert needle in text and needle in doc, needle


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


class _EqStr(str):
    """A str subclass that claims equality with its base text and inequality never: the shape that defeats `!=` and set checks."""
    def __ne__(self, other):
        return False

    def __eq__(self, other):
        return str.__eq__(self, other)

    __hash__ = str.__hash__


class _BigMapping:
    """A very large Mapping (finite, so an unbounded-copy mutant still terminates). `reads` counts the items its `items()` served:
    a bounded snapshot serves at most limit + 1 of them."""
    N = 50_000

    def __init__(self):
        self.reads = 0

    def __getitem__(self, k):
        return 1

    def __iter__(self):
        return (f"c{i:09d}" for i in range(self.N))

    def __len__(self):
        return self.N

    def items(self):
        def gen():
            for i in range(self.N):
                self.reads += 1
                yield f"c{i:09d}", 1
        return gen()


from collections.abc import Mapping as _Mp  # noqa: E402
_Mp.register(_BigMapping)


class _CollidingMapping:
    """Yields a legitimate exact-str key and then a hash/eq-colliding str subclass for the same text, so a naive dict copy collapses
    the two into one legitimate-looking key carrying the hostile value."""
    def __init__(self, key, good, hostile):
        self._pairs = [(key, good), (_EqStr(key), hostile)]

    def __getitem__(self, k):
        return dict(self._pairs)[k]

    def __iter__(self):
        return iter(k for k, _ in self._pairs)

    def __len__(self):
        return len(self._pairs)

    def items(self):
        return iter(self._pairs)


_Mp.register(_CollidingMapping)


def _snapshot_key_collision_refuses(mod):
    """Review nit 1: the colliding key is refused per item before the copy is built (class map and top level), never collapsed."""
    cls = _CollidingMapping("class-a", 60, 99)
    top = _CollidingMapping(F5K, {"class-a": 60}, {"class-a": 99})
    f4 = _CollidingMapping("status_max_age_seconds", 5, 99)
    return (mod.compose_f5({F5K: cls}, rec(p5({"class-a": 1}), F5)).code == "composition_caller_invalid"
            and mod.compose_f5(top, rec(p5({"class-a": 1}), F5)).code == "composition_caller_invalid"
            and mod.compose_f4(f4, rec(p4(), F4)).code == "composition_caller_invalid")


def _bounded_snapshot_refuses(mod):
    """Huge caller mappings (top level and class map) refuse as `composition_caller_invalid` after a bounded read."""
    e1, e2 = _BigMapping(), _BigMapping()
    r1 = mod.compose_f4(e1, rec(p4(), F4))
    r2 = mod.compose_f5({F5K: e2}, rec(p5(), F5))
    return r1.code == r2.code == "composition_caller_invalid" and e1.reads <= len(F4K) + 1 and e2.reads <= c.MAX_ENTRIES + 1


BAD_TYPES = [True, False, 1.0, 60.0, float("inf"), float("-inf"), float("nan"), "60", "1", "", None, b"60", bytearray(b"1"), [1], (1,), {},
             IntSub(5), IntSub(0), object(), 1 + 0j]
BELOW = [0, -1, -2, -(2**31), -(10**30)]
ABOVE = [2147483648, 2**31, 2**32, 2**33, 2**34, 2**53, 2**63, 10**30, 10**400]
VALID = [1, 2, 5, 59, 60, 61, 2147483646, 2147483647]


# ---------------------------------------------------------------- registration
def test_family_tables_are_exactly_the_registered_families():
    assert set(families.FAMILIES) == {c.FAMILY_F1A}
    from registry_successor import v2_f1ab
    assert set(families.FAMILIES_V2) == {c.FAMILY_F1A, v2_f1ab.FAMILY_F1AB, F4, F5}
    assert len(families.FAMILIES_V2) == 4 and len(families.FAMILIES) == 1


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
    assert set(imports) <= {"itertools", "collections.abc", "typing", "registry_successor", "registry_successor.compose"}, imports
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


# ---------------------------------------------------------------- registry never disables a stricter component-owned bound
CALLER_GRID = [0, 1, 2, 59, 60, 61, 3600, MAX - 1, MAX]
REG_GRID = [1, 2, 59, 60, 61, 3600, MAX - 1, MAX]


@pytest.mark.parametrize("caller", [1, 0, 60])
def test_f4_f5_registry_max_never_loosens_a_stricter_caller(caller):
    res = compose4(c4(status_max_age_seconds=caller, approval_max_age_seconds=caller), p4(status_max_age_seconds=MAX, approval_max_age_seconds=MAX))
    assert res.ok and res.effective == {"status_max_age_seconds": caller, "approval_max_age_seconds": caller}
    assert res.detail == "registry_value_not_narrowing:status_max_age_seconds,approval_max_age_seconds"
    res = compose5(c5({"class-a": caller, "class-b": caller}), p5({"class-a": MAX, "class-b": MAX}))
    assert res.ok and res.effective == {F5K: {"class-a": caller, "class-b": caller}}
    assert res.detail == "registry_value_not_narrowing:class-a,class-b"


def test_registry_value_equal_to_maximum_never_changes_a_stricter_caller():
    for cal in CALLER_GRID:
        r4 = compose4(c4(status_max_age_seconds=cal, approval_max_age_seconds=cal), p4(status_max_age_seconds=MAX, approval_max_age_seconds=MAX))
        r5 = compose5(c5({"class-a": cal}), p5({"class-a": MAX}))
        assert r4.ok and r5.ok
        assert r4.effective == {k: cal for k in F4K} and r5.effective == {F5K: {"class-a": cal}}
        # reported as not narrowing exactly when the caller is strictly stricter than the maximum
        assert (a.NOT_NARROWING in r4.detail) == (cal < MAX) and (a.NOT_NARROWING in r5.detail) == (cal < MAX)
        if cal == MAX:
            assert r4.detail == "" and r5.detail == ""


def test_no_input_yields_an_effective_value_above_the_caller():
    """Property-style grid over boundary values: no registry value, field, operator or record shape makes any effective value exceed the caller."""
    for cal, reg in itertools.product(CALLER_GRID, REG_GRID):
        r4 = compose4(c4(status_max_age_seconds=cal, approval_max_age_seconds=MAX - cal), p4(status_max_age_seconds=reg, approval_max_age_seconds=reg))
        r5 = compose5(c5({"class-a": cal, "class-b": MAX - cal}), p5({"class-a": reg, "class-b": reg}))
        assert r4.ok and r5.ok
        assert r4.effective["status_max_age_seconds"] == min(cal, reg) <= cal
        assert r4.effective["approval_max_age_seconds"] == min(MAX - cal, reg) <= MAX - cal
        assert r5.effective[F5K]["class-a"] == min(cal, reg) <= cal
        assert r5.effective[F5K]["class-b"] == min(MAX - cal, reg) <= MAX - cal
        assert set(r5.effective[F5K]) == {"class-a", "class-b"}
        assert (a.NOT_NARROWING in r4.detail) == (reg > cal or reg > MAX - cal)
        # every path that is not an acceptance returns no policy, so a refusal cannot hand back a looser value
        for bad_reg in ABOVE[:4] + BELOW[:2] + [True, 1.5, None]:
            for res in (compose4(c4(status_max_age_seconds=cal), p4(status_max_age_seconds=bad_reg)),
                        compose5(c5({"class-a": cal}), p5({"class-a": bad_reg})),
                        compose4(c4(status_max_age_seconds=cal), p4(), operator="union"),
                        compose5(c5({"class-a": cal}), p5(), operator="max")):
                assert res.ok is False and res.effective is None and res.deny_all is False


def test_composer_has_no_widening_operator_or_extra_slot():
    for operator in ("union", "max", "replace", "override", "widen", "Intersection", None, 1):
        refused(compose4(c4(), operator=operator), "composition_operator_unsupported")
        refused(compose5(c5(), operator=operator), "composition_operator_unsupported")
    for extra in ("max_amount", "max_amount_minor", "identity_max_age_seconds"):
        assert families.lookup_v2(F4).payload_validator(p4(**{extra: 1})) == "field_unknown"
    assert families.lookup_v2(F5).payload_validator({**p5(), "max_amount": {"class-a": 1}}) == "field_unknown"


# ---------------------------------------------------------------- contract_version dispatch for F4 and F5
@pytest.mark.parametrize("fam,cal,pl", [(F4, c4(), p4()), (F5, c5(), p5())])
def test_dispatch_by_contract_version_for_f4_f5(fam, cal, pl):
    spec = families.lookup_v2(fam)
    r = rec(pl, fam)
    # r08-v1: table is FAMILIES, family unregistered there -> v1 behaviour
    sel1 = families.table_for_contract_version("r08-v1")
    assert sel1.ok and sel1.table is families.FAMILIES and fam not in sel1.table
    assert families.lookup_for("r08-v1", fam) is None
    refused(families.compose_for("r08-v1", cal, r), "composition_family_unsupported")
    # r08-v2: table is FAMILIES_V2 and the family composes
    sel2 = families.table_for_contract_version("r08-v2")
    assert sel2.ok and sel2.table is families.FAMILIES_V2 and sel2.table[fam] is spec
    assert families.lookup_for("r08-v2", fam) is spec
    res = families.compose_for("r08-v2", cal, r)
    assert res.ok and res.effective is not None and res.effective == families.compose_v2(cal, r).effective
    # unknown versions: contract_unsupported, no table, no policy, no fallback
    for v in ("r08-v3", "r08-v0", "R08-V2", "r08-v2 ", " r08-v2", "r08-v2\n", "", None, 2, b"r08-v2", ("r08-v2",), StrSub("r08-v2"), StrSub("r08-v1")):
        sel = families.table_for_contract_version(v)
        assert (sel.ok, sel.code, sel.table) == (False, "contract_unsupported", None)
        assert families.lookup_for(v, fam) is None
        refused(families.compose_for(v, cal, r), "contract_unsupported")


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
    chk("caller_output_sorted", lambda: list(comp5(c5({"class-c": 9, "class-a": 5, "class-b": 7}), p5({"class-a": 1})).effective[F5K]) == ["class-a", "class-b", "class-c"])
    chk("operator", lambda: mod.compose_f4(c4(), rec(p4(), F4), "union").code == "composition_operator_unsupported")
    chk("family", lambda: mod.compose_f4(c4(), rec(p5(), F5)).code == "composition_family_unsupported")
    chk("ok_exactly_true", lambda: mod.compose_f4(c4(), rec(p4(), F4, ok=1)).code == "composition_record_invalid"
        and mod.compose_f5(c5(), rec(p5(), F5, ok="yes")).code == "composition_record_invalid")
    chk("exact_str_family", lambda: mod.compose_f4(c4(), rec(p4(), _EqStr(F4))).code == "composition_family_unsupported"
        and mod.compose_f5(c5(), rec(p5(), _EqStr(F5))).code == "composition_family_unsupported")
    chk("exact_str_operator", lambda: mod.compose_f4(c4(), rec(p4(), F4), _EqStr("intersection")).code == "composition_operator_unsupported"
        and mod.compose_f5(c5(), rec(p5(), F5), _EqStr("intersection")).code == "composition_operator_unsupported")
    chk("exact_str_payload_key", lambda: v4({_EqStr("status_max_age_seconds"): 5, "approval_max_age_seconds": 5}) == "field_type_invalid"
        and v5({_EqStr(F5K): {"a": 1}}) == "field_type_invalid" and v5({F5K: {_EqStr("a"): 1}}) == "field_type_invalid")
    chk("exact_str_caller_key", lambda: mod.compose_f4({_EqStr("status_max_age_seconds"): 5, "approval_max_age_seconds": 5}, rec(p4(), F4)).code == "composition_caller_invalid"
        and mod.compose_f5({_EqStr(F5K): {"class-a": 5}}, rec(p5({"class-a": 1}), F5)).code == "composition_caller_invalid"
        and mod.compose_f5({F5K: {_EqStr("class-a"): 5}}, rec(p5({"class-a": 1}), F5)).code == "composition_caller_invalid")
    chk("bounded_snapshot", lambda: _bounded_snapshot_refuses(mod))
    chk("snapshot_key_collision", lambda: _snapshot_key_collision_refuses(mod))
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
    "drop operator check f4": ("def compose_f4(caller: Any, record: Any, operator: Any = \"intersection\") -> CompositionResult:\n    try:\n        if type(operator) is not str or operator != \"intersection\":\n            return _refuse(\"composition_operator_unsupported\")\n",
                               "def compose_f4(caller: Any, record: Any, operator: Any = \"intersection\") -> CompositionResult:\n    try:\n", "operator"),
    "drop family check": ("    if type(family_seen) is not str or family_seen != family:  # exact str: no str subclass with an overridden __ne__\n        return None, \"composition_family_unsupported\"\n", "", "family"),
    "family compare without exact str": ("type(family_seen) is not str or family_seen != family", "family_seen != family", "exact_str_family"),
    "operator compare without exact str": ("if type(operator) is not str or operator != \"intersection\":\n            return _refuse(\"composition_operator_unsupported\")\n        payload, code = _record_payload(record, FAMILY_F4",
                                           "if operator != \"intersection\":\n            return _refuse(\"composition_operator_unsupported\")\n        payload, code = _record_payload(record, FAMILY_F4", "exact_str_operator"),
    "payload keys without exact str": ("    if not all(type(k) is str for k in payload):  # exact str keys: no str subclass with a custom __eq__/__hash__\n        return \"field_type_invalid\"\n", "", "exact_str_payload_key"),
    "class keys without exact str": ("if not all(type(k) is str for k in m) or not all(type(v) is int for v in m.values()):", "if not all(type(v) is int for v in m.values()):", "exact_str_payload_key"),
    "caller f4 keys without exact str (both layers)": (("    if snap is None or not all(type(k) is str for k in snap) or set(snap) != set(F4_FIELDS):", '        if any(type(k) is not str for k, _ in items):\n            return None\n'), ("    if snap is None or set(snap) != set(F4_FIELDS):", ""), "exact_str_caller_key"),
    "caller f5 keys without exact str (both layers)": (("    if snap is None or not all(type(k) is str for k in snap) or set(snap) != set(F5_FIELDS):", '        if any(type(k) is not str for k, _ in items):\n            return None\n'), ("    if snap is None or set(snap) != set(F5_FIELDS):", ""), "exact_str_caller_key"),
    "ok truthy instead of True": ("if getattr(record, \"ok\", False) is not True:", "if not getattr(record, \"ok\", False):", "ok_exactly_true"),
    "unbounded snapshot": ("items = list(itertools.islice(m.items(), limit + 1))", "items = list(m.items())", "bounded_snapshot"),
    "snapshot without per-item key type": ("        if any(type(k) is not str for k, _ in items):\n            return None\n", "", "snapshot_key_collision"),
    "snapshot bound off by one": ("        if len(items) > limit:\n            return None\n", "        if len(items) > limit + 1:\n            return None\n", "bounded_snapshot"),
    "caller empty map accepted": ("    if m is None or not m:", "    if m is None:", "caller_empty_map"),
    "caller output unsorted": ("return {F5_FIELD: {k: m[k] for k in sorted(m)}}", "return {F5_FIELD: dict(m)}", "caller_output_sorted"),
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


# ---------------------------------------------------------------- snapshot: no second read of a caller-supplied container
class Flip(dict):
    """Exact-dict subclass is refused outright; this one proves it (a subclass can lie on every read)."""
    def __getitem__(self, k):
        return -7


class StatefulMapping:
    """A Mapping that returns `first` on the first read of each key and `later` afterwards."""
    def __init__(self, first, later):
        self.first, self.later, self.reads = dict(first), dict(later), {}

    def _d(self, k):
        n = self.reads[k] = self.reads.get(k, 0) + 1
        return self.first if n == 1 else self.later

    def __getitem__(self, k):
        return self._d(k)[k]

    def get(self, k, default=None):
        return self._d(k)[k] if k in self.first else default

    def __iter__(self):
        return iter(self.first)

    def __len__(self):
        return len(self.first)

    def keys(self):
        return self.first.keys()

    def items(self):
        return [(k, self[k]) for k in self.first]

    def __contains__(self, k):
        return k in self.first


from collections.abc import Mapping as _M  # noqa: E402
_M.register(StatefulMapping)


class ChangingRecord:
    """ok / record that change between reads: first a valid payload, then an invalid one."""
    def __init__(self, good, bad, family):
        self.good, self.bad, self.family, self.n = good, bad, family, 0

    @property
    def ok(self):
        return True

    @property
    def record(self):
        self.n += 1
        return {**s.make_record(), "family": self.family, "payload": self.good if self.n == 1 else self.bad}


@pytest.mark.parametrize("fam,good,bad,cal,comp", [
    (F4, p4(), p4(status_max_age_seconds=-7, approval_max_age_seconds=-7), c4(), a.compose_f4),
    (F5, p5({"class-a": 30}), p5({"class-a": -7}), c5({"class-a": 60}), a.compose_f5)])
def test_record_changing_between_reads_never_composes_an_unvalidated_value(fam, good, bad, cal, comp):
    res = comp(cal, ChangingRecord(good, bad, fam))
    assert (not res.ok) or all(v >= 0 for v in (res.effective.values() if fam == F4 else res.effective[F5K].values()))
    if res.ok:  # the validated copy is what is used
        assert res.effective == ({"status_max_age_seconds": 30, "approval_max_age_seconds": 60} if fam == F4 else {F5K: {"class-a": 30}})


def test_stateful_payload_mapping_is_refused_not_composed():
    """A payload that is not an exact dict refuses for F4 and F5 alike, so a stateful Mapping cannot reach composition."""
    for fam, good, bad, cal, comp in ((F4, p4(), p4(status_max_age_seconds=-7), c4(), a.compose_f4), (F5, p5({"class-a": 30}), p5({"class-a": -7}), c5({"class-a": 60}), a.compose_f5)):
        for payload in (StatefulMapping(good, bad), Flip(good), types.MappingProxyType(good)):
            refused(comp(cal, rec(payload, fam)), "composition_record_invalid")
    v4, v5 = a.f4_payload_validator, a.f5_payload_validator
    assert v4(types.MappingProxyType(p4())) == "field_type_invalid" and v5(types.MappingProxyType(p5())) == "field_type_invalid"
    assert v5({F5K: types.MappingProxyType({"a": 1})}) == "field_type_invalid"
    assert v5({F5K: Flip({"a": 1})}) == "field_type_invalid"


def test_stateful_record_body_is_refused():
    for fam, good, bad, cal, comp in ((F4, p4(), p4(status_max_age_seconds=-7), c4(), a.compose_f4), (F5, p5({"class-a": 30}), p5({"class-a": -7}), c5({"class-a": 60}), a.compose_f5)):
        body = StatefulMapping({**s.make_record(), "family": fam, "payload": good}, {**s.make_record(), "family": fam, "payload": bad})
        refused(comp(cal, record_mod.RecordResult(True, None, "", body, "x")), "composition_record_invalid")


def test_stateful_caller_policy_uses_one_read_snapshot():
    # F4: first read valid (60), later reads -7. The effective value is the first read, never the later one, and never negative.
    cal = StatefulMapping(c4(), {k: -7 for k in F4K})
    res = a.compose_f4(cal, rec(p4(), F4))
    assert res.ok and res.effective == {"status_max_age_seconds": 30, "approval_max_age_seconds": 60}
    assert all(v >= 0 for v in res.effective.values())
    # F5 (outer container and class map stateful)
    inner = StatefulMapping({"class-a": 60}, {"class-a": -7})
    cal5 = StatefulMapping({F5K: inner}, {F5K: {"class-a": -7}})
    res = a.compose_f5(cal5, rec(p5({"class-a": 30}), F5))
    assert res.ok and res.effective == {F5K: {"class-a": 30}}
    # a caller whose first read is invalid refuses and is never replaced
    refused(a.compose_f4(StatefulMapping({k: -7 for k in F4K}, c4()), rec(p4(), F4)), "composition_caller_invalid")
    refused(a.compose_f5(StatefulMapping({F5K: {"class-a": -7}}, {F5K: {"class-a": 60}}), rec(p5(), F5)), "composition_caller_invalid")


def test_f5_caller_output_is_sorted():
    res = compose5(c5({"class-c": 90, "class-a": 60, "class-b": 60}), p5({"class-a": 1}))
    assert res.ok and list(res.effective[F5K]) == ["class-a", "class-b", "class-c"]
    assert list(a.normalize_caller_f5(c5({"class-c": 1, "class-a": 1, "class-b": 1}))[F5K]) == ["class-a", "class-b", "class-c"]


# ---------------------------------------------------------------- PR #31 review dispositions (N1, N2, N3, N5)
def test_record_ok_must_be_exactly_true():
    """N3: a truthy non-True `ok` is not a valid record (stricter than v1 on purpose)."""
    for bad in (1, "yes", [1], object()):
        refused(a.compose_f4(c4(), rec(p4(), F4, ok=bad)), "composition_record_invalid")
        refused(a.compose_f5(c5(), rec(p5(), F5, ok=bad)), "composition_record_invalid")
    assert a.compose_f4(c4(), rec(p4(), F4, ok=True)).ok


def test_str_subclass_is_not_a_family_operator_or_key():
    """N1: a str subclass that lies about equality is refused for the family, operator and every key, not matched by value."""
    refused(a.compose_f4(c4(), rec(p4(), _EqStr(F4))), "composition_family_unsupported")
    refused(a.compose_f5(c5(), rec(p5(), _EqStr(F5))), "composition_family_unsupported")
    refused(a.compose_f4(c4(), rec(p4(), F4), _EqStr("intersection")), "composition_operator_unsupported")
    refused(a.compose_f5(c5(), rec(p5(), F5), _EqStr("intersection")), "composition_operator_unsupported")
    assert a.f4_payload_validator({_EqStr("status_max_age_seconds"): 5, "approval_max_age_seconds": 5}) == "field_type_invalid"
    assert a.f5_payload_validator({_EqStr(F5K): {"a": 1}}) == "field_type_invalid"
    assert a.f5_payload_validator({F5K: {_EqStr("a"): 1}}) == "field_type_invalid"
    refused(a.compose_f4({_EqStr("status_max_age_seconds"): 5, "approval_max_age_seconds": 5}, rec(p4(), F4)), "composition_caller_invalid")
    refused(a.compose_f5({F5K: {_EqStr("class-a"): 5}}, rec(p5({"class-a": 1}), F5)), "composition_caller_invalid")
    # plain str values are unaffected
    assert a.compose_f4(c4(), rec(p4(), F4), "intersection").ok and a.compose_f5(c5(), rec(p5(), F5), "intersection").ok


def test_huge_caller_mapping_is_refused_after_a_bounded_read():
    """N2: the caller snapshot stops at limit + 1 entries; a huge Mapping is refused without copying it."""
    top, cls = _BigMapping(), _BigMapping()
    refused(a.compose_f4(top, rec(p4(), F4)), "composition_caller_invalid")
    assert top.reads <= len(F4K) + 1
    refused(a.compose_f5({F5K: cls}, rec(p5(), F5)), "composition_caller_invalid")
    assert cls.reads <= c.MAX_ENTRIES + 1
    outer = _BigMapping()
    refused(a.compose_f5(outer, rec(p5(), F5)), "composition_caller_invalid")
    assert outer.reads <= len(a.F5_FIELDS) + 1
    # exactly MAX_ENTRIES classes is still accepted, MAX_ENTRIES + 1 is not
    ok_map = {f"c{i:04d}": 1 for i in range(c.MAX_ENTRIES)}
    assert a.compose_f5({F5K: ok_map}, rec(p5({"c0000": 1}), F5)).ok
    refused(a.compose_f5({F5K: {**ok_map, "c9999": 1}}, rec(p5({"c0000": 1}), F5)), "composition_caller_invalid")


def test_nfc_and_nfd_class_keys_are_distinct_exact_strings():
    """N5: no Unicode normalization. 'é' (U+00E9) and 'e' + U+0301 are two different, individually valid class ids."""
    nfc, nfd = "é", "é"
    assert nfc != nfd and c.valid_token(nfc) and c.valid_token(nfd)
    reg = {k: 5 for k in sorted([nfc, nfd])}
    assert a.f5_payload_validator({F5K: reg}) is None
    res = a.compose_f5({F5K: {nfc: 60}}, rec({F5K: {nfc: 5}}, F5))
    assert res.ok and res.effective == {F5K: {nfc: 5}}
    refused(a.compose_f5({F5K: {nfc: 60}}, rec({F5K: {nfd: 5}}, F5)), "composition_record_invalid")  # NFD registry class unknown to an NFC caller


def test_snapshot_refuses_a_colliding_key_subclass_before_copying():
    """Review nit 1: {'class-a': 60} + a colliding str subclass carrying 99 must not collapse into {'class-a': 99}."""
    assert a._snapshot(_CollidingMapping("class-a", 60, 99), 256) is None
    assert _snapshot_key_collision_refuses(a)
