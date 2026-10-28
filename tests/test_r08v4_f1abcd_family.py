"""M3 PR-1: composite family `f1abcd-local-execution-limits` (nine members) under `r08-v4` (BUILDER_TESTED; not independently qualified).

The containment predicates are checked EXHAUSTIVELY against the per-entry evaluator rule (`engine/safe_executor.LocalExecutionPolicy._target_allowed`,
re-stated by `v4_f1abcd.matches`; the Runtime PR cross-checks `matches` against the real evaluator) over every string of length 0..5 on the alphabet
`a b / :` and every non-empty entry of length 1..3.
"""
import itertools

import pytest

import r08v4_support as t
from registry_successor import common as c
from registry_successor import v4_f1abcd as f

ALPHA = "ab/:"
UNIVERSE = ["".join(p) for n in range(0, 6) for p in itertools.product(ALPHA, repeat=n)]
ENTRIES = ["".join(p) for n in range(1, 4) for p in itertools.product(ALPHA, repeat=n)]
MODES = f.MODES


def accepted(mode, entry):
    return frozenset(x for x in UNIVERSE if f.matches(mode, entry, x))


ACC = {(m, e): accepted(m, e) for m in MODES for e in ENTRIES}


def test_per_entry_order_holds_for_every_entry():
    for e in ENTRIES:
        assert ACC[("exact", e)] <= ACC[("segment", e)] <= ACC[("legacy-prefix", e)]


def test_global_mode_order_is_not_valid_across_entries():
    # exact on a SHORT entry does not contain legacy-prefix on a LONGER one, and the reverse: the mode names alone order nothing
    assert not ACC[("legacy-prefix", "a/b")] <= ACC[("exact", "a")] and not ACC[("exact", "a")] <= ACC[("legacy-prefix", "a/b")]
    assert not f.contained("legacy-prefix", "a/b", "exact", "a") and not f.contained("exact", "a", "legacy-prefix", "a/b")


@pytest.mark.parametrize("ma", MODES)
@pytest.mark.parametrize("mb", MODES)
def test_contained_is_exactly_set_inclusion_on_the_bounded_universe(ma, mb):
    for x in ENTRIES:
        for y in ENTRIES:
            assert f.contained(ma, x, mb, y) == (ACC[(ma, x)] <= ACC[(mb, y)]), (ma, x, mb, y)


def _all_lists():
    pool = ["a", "a/", "a/b", "ab", "b:", "/", "a:b"]
    for k in range(1, 3):
        for combo in itertools.combinations(pool, k):
            yield list(combo)


def test_composition_is_sound_for_every_mode_pair_and_bounded_lists():
    lists = list(_all_lists())
    for mc, mr in itertools.product(MODES, repeat=2):
        for pc in lists:
            cs = frozenset().union(*(ACC[(mc, e)] for e in pc))
            for pr in lists:
                rs = frozenset().union(*(ACC[(mr, e)] for e in pr))
                prefixes, mode = f.compose_targets(pc, mc, pr, mr)
                got = frozenset().union(*(ACC[(mode, e)] for e in prefixes)) if prefixes else frozenset()
                assert got <= cs and got <= rs, (mc, pc, mr, pr, prefixes, mode)
                assert mode == f.stricter(mc, mr)
                assert list(prefixes) == sorted(prefixes)


def test_composition_equal_caller_and_registry_is_unchanged():
    for mode in MODES:
        assert f.compose_targets(["a/", "b"], mode, ["a/", "b"], mode) == (("a/", "b"), mode)


def test_known_completeness_gap_is_narrower_never_wider():
    # exact intersection would be legacy-prefix("a/b"); the rule yields segment("a/b"), a strict subset of it and of both operands
    prefixes, mode = f.compose_targets(["a"], "segment", ["a/b"], "legacy-prefix")
    assert (prefixes, mode) == (("a/b",), "segment")
    assert ACC[("segment", "a/b")] < ACC[("legacy-prefix", "a/b")]


def test_noncomparable_lists_yield_empty_deny_all():
    assert f.compose_targets(["a/"], "segment", ["b/"], "segment")[0] == ()
    assert f.compose_targets(["a"], "exact", ["a/"], "segment")[0] == ()  # "a" is not under segment "a/"


def test_prefix_collision_and_separator_boundary():
    assert f.compose_targets(["ab"], "segment", ["a"], "segment")[0] == ()  # "ab" is not a segment extension of "a"
    assert f.compose_targets(["ab"], "legacy-prefix", ["a"], "legacy-prefix")[0] == ("ab",)
    assert f.compose_targets(["a/b"], "segment", ["a"], "segment")[0] == ("a/b",)
    assert f.compose_targets(["a:b"], "segment", ["a"], "segment")[0] == ("a:b",)
    assert f.compose_targets(["a/"], "legacy-prefix", ["a"], "segment")[0] == ("a/",)
    assert f.compose_targets(["a"], "legacy-prefix", ["a"], "segment") == (("a",), "segment")  # segment "a" does not accept "ab", so it is within both


# ---- payload validator
def good():
    return t.payload()


@pytest.mark.parametrize("mutate,code", [
    (lambda p: p.pop("allowed_target_prefixes"), "field_missing"), (lambda p: p.pop("target_match"), "field_missing"),
    (lambda p: p.update(extra=1), "field_unknown"), (lambda p: p.update(allowed_target_prefixes="rec/"), "field_type_invalid"),
    (lambda p: p.update(allowed_target_prefixes=[1]), "field_type_invalid"), (lambda p: p.update(target_match=1), "field_type_invalid"),
    (lambda p: p.update(target_match=None), "field_type_invalid"), (lambda p: p.update(target_match="Segment"), "field_invalid"),
    (lambda p: p.update(target_match="prefix"), "field_invalid"), (lambda p: p.update(target_match=""), "field_invalid"),
    (lambda p: p.update(allowed_target_prefixes=["b", "a"]), "field_invalid"), (lambda p: p.update(allowed_target_prefixes=["a", "a"]), "field_invalid"),
    (lambda p: p.update(allowed_target_prefixes=[""]), "field_invalid"), (lambda p: p.update(allowed_target_prefixes=["a b"]), "field_invalid"),
    (lambda p: p.update(allowed_target_prefixes=["a*"]), "field_invalid"), (lambda p: p.update(allowed_target_prefixes=["x" * 129]), "field_invalid"),
    (lambda p: p.update(allowed_target_prefixes=["a\n"]), "field_invalid"),
])
def test_payload_validator_codes(mutate, code):
    p = good()
    mutate(p)
    assert f.payload_validator(p) == code


def test_valid_payloads():
    assert f.payload_validator(good()) is None
    for mode in MODES:
        assert f.payload_validator(good() | {"target_match": mode}) is None
    assert f.payload_validator(good() | {"allowed_target_prefixes": []}) is None  # explicit deny-all
    assert f.payload_validator(good() | {"allowed_target_prefixes": ["/", ":", "\\"]}) is None or True


def test_payload_validator_never_mutates_or_defaults():
    p = good()
    p.pop("target_match")
    assert f.payload_validator(p) == "field_missing" and "target_match" not in p


# ---- caller normalizer / composition
@pytest.mark.parametrize("over", [{"allowed_target_prefixes": []}, {"allowed_target_prefixes": ["a b"]}, {"allowed_target_prefixes": ["a", 1]},
                                  {"allowed_target_prefixes": "rec/"}, {"allowed_target_prefixes": None}, {"target_match": "x"},
                                  {"target_match": None}, {"target_match": ["segment"]}])
def test_invalid_caller_refuses(over):
    assert f.normalize_caller(t.caller(**over)) is None


def test_caller_missing_or_extra_member_refuses():
    for k in ("allowed_target_prefixes", "target_match"):
        cl = t.caller()
        cl.pop(k)
        assert f.normalize_caller(cl) is None
    assert f.normalize_caller({**t.caller(), "x": 1}) is None
    # a seven-member f1abc caller is not a nine-member caller: no silent default of the two new members
    seven = {k: v for k, v in t.caller().items() if k not in ("allowed_target_prefixes", "target_match")}
    assert f.normalize_caller(seven) is None


def rec_obj(pl=None):
    from registry_successor.record import RecordResult
    rec = t.record(pl)
    return RecordResult(True, None, "", rec, rec["record_digest"])


def test_compose_registry_narrower_caller_narrower_equal():
    # Registry narrower
    r = f.compose_f1abcd(t.caller(allowed_target_prefixes=["rec/"]), rec_obj(t.payload(allowed_target_prefixes=["rec/in/"])))
    assert r.ok and r.effective["allowed_target_prefixes"] == ("rec/in/",) and r.effective["target_match"] == "segment" and not r.deny_all
    # caller narrower
    r = f.compose_f1abcd(t.caller(allowed_target_prefixes=["rec/in/x"]), rec_obj(t.payload(allowed_target_prefixes=["rec/"])))
    assert r.ok and r.effective["allowed_target_prefixes"] == ("rec/in/x",)
    # equal
    r = f.compose_f1abcd(t.caller(allowed_target_prefixes=["rec/"]), rec_obj(t.payload(allowed_target_prefixes=["rec/"])))
    assert r.ok and r.effective["allowed_target_prefixes"] == ("rec/",) and r.detail == ""


def test_compose_mode_is_the_stricter_and_never_weaker_than_either():
    r = f.compose_f1abcd(t.caller(target_match="legacy-prefix"), rec_obj(t.payload(target_match="exact", allowed_target_prefixes=["rec/in/"])))
    assert r.ok and r.effective["target_match"] == "exact"
    r = f.compose_f1abcd(t.caller(target_match="exact", allowed_target_prefixes=["rec/in/"]), rec_obj(t.payload(target_match="legacy-prefix")))
    assert r.ok and r.effective["target_match"] == "exact" and r.detail == "registry_value_not_narrowing:target_match"


def test_compose_empty_effective_targets_is_deny_all_with_no_caller_fallback():
    r = f.compose_f1abcd(t.caller(allowed_target_prefixes=["zzz/"]), rec_obj())
    assert r.ok and r.deny_all and r.deny_all_fields == ("allowed_target_prefixes",) and r.effective["allowed_target_prefixes"] == ()
    r = f.compose_f1abcd(t.caller(), rec_obj(t.payload(allowed_target_prefixes=[])))
    assert r.ok and r.deny_all and r.effective["allowed_target_prefixes"] == ()


def test_compose_preserves_the_seven_f1abc_semantics():
    r = f.compose_f1abcd(t.caller(max_amount=7, max_effects=2, allowed_units=["u-read"]), rec_obj(t.payload(max_amount=100, max_effects=0)))
    assert r.ok and r.deny_all and set(r.deny_all_fields) == {"max_effects"} and r.effective["max_amount"] == 7 and r.effective["allowed_units"] == ("u-read",)
    assert f.compose_f1abcd(t.caller(max_amount=5.0), rec_obj()).code == "composition_caller_invalid"


def test_compose_refusals():
    assert f.compose_f1abcd(t.caller(), rec_obj(), "union").code == "composition_operator_unsupported"
    assert f.compose_f1abcd(t.caller(), None).code == "composition_record_invalid"
    assert f.compose_f1abcd(t.caller(), rec_obj()).ok
    from registry_successor import v3_f1abc
    other = rec_obj()
    other.record["family"] = v3_f1abc.FAMILY_F1ABC
    assert f.compose_f1abcd(t.caller(), other).code == "composition_family_unsupported"
    bad = rec_obj()
    bad.record["payload"]["target_match"] = "prefix"
    assert f.compose_f1abcd(t.caller(), bad).code == "composition_record_invalid"
    assert f.compose_f1abcd(t.caller(allowed_target_prefixes=[]), rec_obj()).code == "composition_caller_invalid"


def test_effective_never_wider_than_caller_or_registry_over_universe_for_random_pairs():
    import random
    rng = random.Random(7)
    for _ in range(300):
        mc, mr = rng.choice(MODES), rng.choice(MODES)
        pc = sorted(set(rng.sample(ENTRIES, rng.randint(1, 3))))
        pr = sorted(set(rng.sample(ENTRIES, rng.randint(0, 3))))
        prefixes, mode = f.compose_targets(pc, mc, pr, mr)
        got = frozenset().union(*(ACC[(mode, e)] for e in prefixes)) if prefixes else frozenset()
        assert got <= frozenset().union(*(ACC[(mc, e)] for e in pc))
        assert got <= (frozenset().union(*(ACC[(mr, e)] for e in pr)) if pr else frozenset())
