"""EXT-S1-3 tests: `f1ab-local-execution-allowlist` five-set family. BUILDER_TESTED: builder-authored evidence, not an
independently qualified oracle, and no claim of independent qualification.
"""
import hashlib
import itertools
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import families  # noqa: E402
from registry_successor import record as record_mod  # noqa: E402
from registry_successor import v2_f1ab as f  # noqa: E402
from registry_successor.compose import CompositionResult  # noqa: E402
from registry_successor.decision import verify_and_decide  # noqa: E402

FIELDS = ("allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains")

# ---------------------------------------------------------------- source pins (contract text the tests rely on)
PINS = {
    "docs/r08-v2-contract.md": "64e2d6eb3af7b6024bf0ed7778fcea5ee61fd1cbad247d0199e1b15310ddff01",
    "docs/decisions/2026-10-25-adr-ext-s1-1-v1-contract.md": "b9ad06be559bfb99c5e669ca7217d2ee28b62cda7738206c31fd8e6866233b67",
}
CONTRACT_TEXT = [
    "| `f1ab-local-execution-allowlist` (v2) | `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains` | intersection per key | Runtime |",
    "Absent key: `field_missing`. Extra key (including any amount key): `field_unknown`. An empty F1ab list is a valid explicit deny-all for that dimension; an absent list is never an implicit allow or deny.",
    "F1ab lists: sorted, duplicate-free, at most 256 entries, each 1..128 characters, no control, separator or `*` characters, exact-string membership (no case folding, no wildcard).",
    r"`\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z`",
    "Deny-all is decided by the enforcing gate before any policy object is built (D-20). The family composers never construct a Runtime policy.",
    "an omitted binding is not an intentionally absent optional policy",
]


def test_contract_sources_are_pinned():
    for rel, digest in PINS.items():
        assert hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() == digest, f"{rel} changed: re-read the contract, then re-pin"
    text = (ROOT / "docs/r08-v2-contract.md").read_text(encoding="utf-8")
    for line in CONTRACT_TEXT:
        assert line in text, line


# ---------------------------------------------------------------- builders
def payload(**over):
    p = {"allowed_actions": ["act-a", "act-b"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a", "unit-b"],
         "allowed_institutions": ["inst-a", "inst-b"], "allowed_authority_domains": ["domain-a"]}
    p.update(over)
    return p


def caller(**over):
    p = {"allowed_actions": ["act-b", "act-c"], "allowed_adapters": ["local-fs", "other"], "allowed_units": ["unit-b"],
         "allowed_institutions": ["inst-a", "inst-b", "inst-z"], "allowed_authority_domains": ["domain-a", "domain-b"]}
    p.update(over)
    return p


def rec(pl=None, family=f.FAMILY_F1AB, ok=True):
    body = dict(s.make_record(), family=family, payload=pl if pl is not None else payload())
    return record_mod.RecordResult(ok, None, "", body, body["record_digest"])


def compose(cl, pl=None, **kw):
    return families.compose_v2(cl, rec(pl), **kw)


# ---------------------------------------------------------------- table registration
def test_v2_table_has_f1ab_and_v1_table_does_not():
    assert set(families.FAMILIES) == {c.FAMILY_F1A}
    assert set(families.FAMILIES_V2) == {c.FAMILY_F1A, f.FAMILY_F1AB}
    spec = families.lookup_v2(f.FAMILY_F1AB)
    assert spec is families.FAMILIES_V2[f.FAMILY_F1AB]
    assert spec.payload_fields == FIELDS and f.F1AB_FIELDS == FIELDS
    assert spec.composer is f.compose_f1ab and spec.enforcing_component == "runtime"
    assert spec.evaluator_binding == (c.EVALUATOR_ID, c.EVALUATOR_BINDING)
    assert families.lookup(f.FAMILY_F1AB) is None
    assert families.FAMILIES_V2[c.FAMILY_F1A] is families.FAMILIES[c.FAMILY_F1A]
    with pytest.raises(TypeError):
        families.FAMILIES_V2["x"] = spec


@pytest.mark.parametrize("fam", ["F1AB-LOCAL-EXECUTION-ALLOWLIST", " f1ab-local-execution-allowlist", "f1ab-local-execution-allowlist ",
                                 "f1ab-local-execution-allowlist\n", "f1a-b-local-execution-allowlist", "f1b-local-execution-allowlist",
                                 "f4-control-plane-age-bounds", "", None, 3, [f.FAMILY_F1AB], b"f1ab"])
def test_v2_lookup_exact_only(fam):
    assert families.lookup_v2(fam) is None


def test_f1ab_through_v1_entry_points_still_refuses_family_unsupported():
    body = s.seal_record({**s.make_record(), "family": f.FAMILY_F1AB, "payload": payload()})
    res = record_mod.validate_record_text(json.dumps(body))
    assert (res.ok, res.code) == (False, "family_unsupported")
    r = families.compose(caller(), rec())
    assert (r.ok, r.code, r.effective) == (False, "composition_family_unsupported", None)


def test_required_and_optional_with_f1ab_on_v1_decision_path():
    body = s.seal_record({**s.make_record(), "family": f.FAMILY_F1AB, "payload": payload()})
    stmt = s.make_statement(s.make_record(), family=f.FAMILY_F1AB)
    for part in ("required", "optional"):
        d = verify_and_decide(part, caller(), json.dumps(body), json.dumps({"statement": stmt}), None, None, None, s.NOW)
        assert d.operationally_authorized is False
        if part == "required":
            assert d.kind == "required_policy_unavailable" and d.effective is None and not d.caller_unchanged
        else:
            assert d.kind == "overlay_not_applied" and not d.deny_all


# ---------------------------------------------------------------- payload shape
def test_valid_payload_accepted_exactly_five_fields():
    assert f.payload_validator(payload()) is None
    assert len(f.F1AB_FIELDS) == 5


@pytest.mark.parametrize("missing", FIELDS)
def test_each_field_absent_refused_field_missing(missing):
    p = payload()
    del p[missing]
    assert f.payload_validator(p) == "field_missing"
    r = compose(caller(), p)
    assert (r.ok, r.effective, r.deny_all) == (False, None, False) and r.code == "composition_record_invalid"


@pytest.mark.parametrize("extra", ["max_amount", "max_effects", "amount", "max_amount_cents", "status_max_age_seconds",
                                   "allowed_targets", "Allowed_Actions", "allowed_actions ", "extra", ""])
def test_sixth_key_refused_field_unknown(extra):
    p = payload()
    p[extra] = []
    assert f.payload_validator(p) == "field_unknown"
    assert compose(caller(), p).code == "composition_record_invalid"


@pytest.mark.parametrize("combo", list(itertools.product([False, True], repeat=5)))
def test_all_32_empty_combinations_are_explicit_deny_all(combo):
    pl = payload(**{k: [] for k, e in zip(FIELDS, combo) if e})
    assert f.payload_validator(pl) is None
    r = compose(caller(), pl)
    assert r.ok
    expect = tuple(k for k, e in zip(FIELDS, combo) if e)
    assert r.deny_all_fields == expect and r.deny_all is bool(expect)
    for k in expect:
        assert r.effective[k] == ()
    # empty on the caller side is equally deny-all and distinct from refusal
    r2 = compose(caller(**{k: [] for k in expect}))
    assert r2.ok and set(expect) <= set(r2.deny_all_fields)


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("bad", [["*"], ["a*"], ["b", "a"], ["a", "a"], [""], [1], [None], [True], ["a\nb"], ["a b"], ["a\x00"],
                                 ["a" * 129], [["a"]], [b"a"], "act-a", None, 1, {"a": 1}, ("a",), {"a"}])
def test_malformed_lists_refused(field, bad):
    code = f.payload_validator(payload(**{field: bad}))
    assert code in ("field_type_invalid", "field_invalid")
    if isinstance(bad, list):
        assert code == "field_invalid"
    else:
        assert code == "field_type_invalid"
    r = compose(caller(), payload(**{field: bad}))
    assert (r.ok, r.effective) == (False, None)


@pytest.mark.parametrize("field", FIELDS)
def test_oversize_list_refused_and_boundary_accepted(field):
    ok = sorted(f"e{i:04d}" for i in range(256))
    assert f.payload_validator(payload(**{field: ok})) is None
    over = sorted(f"e{i:04d}" for i in range(257))
    assert f.payload_validator(payload(**{field: over})) == "field_invalid"


def test_entry_length_boundary_128():
    assert f.payload_validator(payload(allowed_actions=["a" * 128])) is None
    assert f.payload_validator(payload(allowed_actions=["a" * 129])) == "field_invalid"


def test_str_subclass_entries_refused():
    class S(str):
        pass
    assert f.payload_validator(payload(allowed_actions=[S("a")])) == "field_invalid"
    assert f.payload_validator(payload(allowed_actions=type("L", (list,), {})(["a"]))) == "field_type_invalid"


# ---------------------------------------------------------------- ASCII grammar on institution / authority-domain entries
@pytest.mark.parametrize("field", f.ASCII_GRAMMAR_FIELDS)
@pytest.mark.parametrize("bad", ["é", "café", "café", "İnst", "inst\U0001F600", "ａbc", "-inst", ".inst", "_inst", ":inst",
                                 "in st", "in/st", "in*st", " inst", "inst ", "inst\n", "inst\t", "inst​", "a" * 129, "inst@x"])
def test_ascii_grammar_negative_institution_and_domain(field, bad):
    assert f.payload_validator(payload(**{field: [bad]})) == "field_invalid"


@pytest.mark.parametrize("good", ["a", "A", "0", "inst-a", "Inst.A:b_c-d", "a" * 128, "9z"])
def test_ascii_grammar_positive(good):
    assert f.valid_ascii_identifier(good)
    assert f.payload_validator(payload(allowed_institutions=[good], allowed_authority_domains=[good])) is None


def test_ascii_grammar_has_no_normalization_or_case_folding():
    # precomposed vs decomposed are both refused, never conflated; case variants are distinct strings
    assert not f.valid_ascii_identifier("é") and not f.valid_ascii_identifier("é")
    r = compose(caller(allowed_institutions=["Inst-A"]), payload(allowed_institutions=["inst-a"]))
    assert r.ok and r.effective["allowed_institutions"] == () and "allowed_institutions" in r.deny_all_fields
    assert not f.valid_ascii_identifier("a\n")  # `$`-style trailing newline is not accepted


def test_non_grammar_tokens_allowed_for_non_identifier_dimensions():
    # contract section 2: opaque exact-string tokens for actions/adapters/units
    assert f.payload_validator(payload(allowed_actions=["Write-File", "écrire"], allowed_units=["u:1/2"])) is None


# ---------------------------------------------------------------- composition: narrow-only intersection
def test_effective_is_intersection_and_subset_of_both():
    r = compose(caller())
    assert r.ok and not r.deny_all
    assert r.effective == {"allowed_actions": ("act-b",), "allowed_adapters": ("local-fs",), "allowed_units": ("unit-b",),
                           "allowed_institutions": ("inst-a", "inst-b"), "allowed_authority_domains": ("domain-a",)}
    for k in FIELDS:
        assert set(r.effective[k]) <= set(caller()[k]) and set(r.effective[k]) <= set(payload()[k])


def test_registry_cannot_widen_caller():
    wide = payload(allowed_actions=["act-a", "act-b", "act-c", "act-d"])
    r = compose(caller(allowed_actions=["act-c"]), wide)
    assert r.effective["allowed_actions"] == ("act-c",)


def test_disjoint_dimension_is_deny_all_never_caller():
    r = compose(caller(), payload(allowed_units=["unit-x"]))
    assert r.ok and r.deny_all and r.deny_all_fields == ("allowed_units",) and r.effective["allowed_units"] == ()


def test_exhaustive_small_grid_never_widens():
    universe = ["a", "b", "c"]
    subsets = [list(x) for n in range(4) for x in itertools.combinations(universe, n)]
    for cl, rg in itertools.product(subsets, subsets):
        r = compose(caller(allowed_units=cl), payload(allowed_units=rg))
        assert r.ok
        assert set(r.effective["allowed_units"]) == set(cl) & set(rg)
        assert (not r.effective["allowed_units"]) == ("allowed_units" in r.deny_all_fields)


def test_composer_is_pure_and_does_not_mutate():
    cl, pl = caller(), payload()
    cl0, pl0 = json.dumps(cl, sort_keys=True), json.dumps(pl, sort_keys=True)
    compose(cl, pl)
    assert json.dumps(cl, sort_keys=True) == cl0 and json.dumps(pl, sort_keys=True) == pl0


def test_caller_set_types_accepted_and_sorted():
    r = compose({**caller(), "allowed_units": {"unit-b", "unit-a"}}, payload())
    assert r.ok and r.effective["allowed_units"] == ("unit-a", "unit-b")


@pytest.mark.parametrize("missing", FIELDS)
def test_caller_missing_a_set_refuses(missing):
    cl = caller()
    del cl[missing]
    r = compose(cl)
    assert (r.ok, r.code, r.effective) == (False, "composition_caller_invalid", None)


@pytest.mark.parametrize("bad", [None, [], "x", 3, [("allowed_actions", [])], {"allowed_actions": []},
                                 dict(caller(), max_amount=1), dict(caller(), allowed_actions="act-a"),
                                 dict(caller(), allowed_actions=None), dict(caller(), allowed_actions=[1]),
                                 dict(caller(), allowed_units=["a b"]), dict(caller(), allowed_units=["*"]),
                                 dict(caller(), allowed_units=[""]), dict(caller(), allowed_units="unit-b"),
                                 {k.upper(): v for k, v in caller().items()}])
def test_invalid_caller_refuses_and_is_never_replaced(bad):
    r = compose(bad)
    assert (r.ok, r.code, r.effective, r.deny_all) == (False, "composition_caller_invalid", None, False)


def test_caller_str_subclass_entry_refuses():
    class S(str):
        pass
    assert compose(caller(allowed_units=[S("unit-b")])).code == "composition_caller_invalid"


# ---------------------------------------------------------------- fail-closed refusals (required never yields the caller)
@pytest.mark.parametrize("op", ["union", "", None, "Intersection", "intersection ", 1])
def test_operator_must_be_intersection(op):
    r = families.compose_v2(caller(), rec(), op)
    assert (r.ok, r.code, r.effective) == (False, "composition_operator_unsupported", None)


def test_invalid_record_refuses():
    for record in (None, object(), rec(ok=False), record_mod.RecordResult(True, None, "", None, None)):
        r = families.compose_v2(caller(), record)
        assert (r.ok, r.code, r.effective) == (False, "composition_record_invalid", None)


@pytest.mark.parametrize("fam", ["f1a-local-execution-allowlist", "F1AB-LOCAL-EXECUTION-ALLOWLIST", "f4-control-plane-age-bounds", None, "", 5])
def test_wrong_or_varied_family_refuses_composition_family_unsupported(fam):
    r = families.compose_v2(caller(), rec(family=fam))
    if fam == c.FAMILY_F1A:  # f1a is dispatched to the f1a composer, which refuses the five-set payload
        assert not r.ok and r.effective is None
    else:
        assert (r.ok, r.code, r.effective) == (False, "composition_family_unsupported", None)


def test_f1a_record_with_three_key_payload_still_composes_via_v2_table():
    base = s.make_record()
    r = families.compose_v2({k: ["write-file", "local-fs", "unit-a"] for k in c.F1A_FIELDS}, record_mod.RecordResult(True, None, "", base, base["record_digest"]))
    assert r.ok  # f1a behaviour is the unchanged v1 composer


def test_hand_built_record_payload_tampering_is_refused_at_compose():
    for pl in (payload(allowed_units=["b", "a"]), payload(allowed_institutions=["é"]), dict(payload(), max_amount=1), {}, None, [],
               payload(allowed_actions=("a",))):
        body = dict(s.make_record(), family=f.FAMILY_F1AB, payload=pl)
        r = families.compose_v2(caller(), record_mod.RecordResult(True, None, "", body, None))
        assert (r.ok, r.effective) == (False, None)


def test_no_refusal_ever_returns_the_caller_policy():
    cl = caller()
    cases = [families.compose_v2(cl, rec(ok=False)), compose({}), compose(cl, payload(allowed_actions=["z", "a"])),
             families.compose_v2(cl, rec(), "union"), families.compose_v2(cl, rec(family="x"))]
    for r in cases:
        assert isinstance(r, CompositionResult) and not r.ok and r.effective is None and not r.deny_all


def test_composer_never_raises_on_hostile_input():
    class Boom:
        def __getattr__(self, name):
            raise RuntimeError(name)
    for rr in (Boom(), 1, "x"):
        r = families.compose_v2(caller(), rr)
        assert not r.ok and r.effective is None
    r = families.compose_v2(Boom(), rec())
    assert not r.ok and r.effective is None


# ---------------------------------------------------------------- scope guards
def test_no_runtime_or_control_plane_import_and_no_amount_or_age_slot():
    src = (ROOT / "registry_successor" / "v2_f1ab.py").read_text()
    for banned in ("import engine", "from engine", "safe_executor import", "LocalExecutionPolicy(", "import requests", "import socket", "open("):
        assert banned not in src, banned
    assert not any("amount" in k or "age" in k.split("_") for k in f.F1AB_FIELDS)
    import registry_successor.v2_codes as v2c
    assert len(c.CODES) == 46 and len(v2c.CODES_V2) == 48
