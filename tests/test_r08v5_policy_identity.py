"""Effective-policy identity for `f5-action-class-unreadable-policy` under `r08-v5` (BUILDER_TESTED; not independently qualified).

The digest is recomputed with an independent canonical encoder (not the module's), so a serializer defect cannot hide itself.
"""
import hashlib
import json
from pathlib import Path

import pytest

import r08v5_support as t
from registry_successor import v2_policy_identity as v2pi
from registry_successor import v4_policy_identity as v4pi
from registry_successor import v5_class_unreadable as f
from registry_successor import v5_policy_identity as v5

VECTORS = json.loads((Path(__file__).parent / "vectors" / "r08v5" / "identity_vectors.json").read_text())
FAM = f.FAMILY_F5U
FIELD = f.F5U_FIELD


def independent_digest(preimage):
    body = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(b"ocs-reg/r08-v5/effective-policy\n" + body).hexdigest()


def eff(m=None):
    return {FIELD: dict(m if m is not None else {"class-a": "refuse", "class-b": "bounded_tolerance"})}


def code(fn, *a, **k):
    with pytest.raises(v5.IdentityRefusal) as e:
        fn(*a, **k)
    return e.value.code, e.value.member


@pytest.mark.parametrize("vec", VECTORS["vectors"], ids=[x["id"] for x in VECTORS["vectors"]])
def test_pinned_vectors(vec):
    pre = v5.effective_preimage(FAM, vec["effective"])
    assert pre == vec["preimage"]
    assert v5.effective_policy_digest(FAM, vec["effective"]) == vec["digest"] == independent_digest(vec["preimage"])


def test_preimage_shape():
    pre = v5.effective_preimage(FAM, eff())
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v5", "family": FAM, "family_version": "v5",
                   "deny_all": [], "effective": eff()}
    assert v5.effective_policy_digest(FAM, eff()) == independent_digest(pre)


def test_changing_any_class_or_value_changes_the_digest():
    base = v5.effective_policy_digest(FAM, eff())
    assert base != v5.effective_policy_digest(FAM, eff({"class-a": "bounded_tolerance", "class-b": "bounded_tolerance"}))
    assert base != v5.effective_policy_digest(FAM, eff({"class-a": "refuse", "class-b": "refuse"}))
    assert base != v5.effective_policy_digest(FAM, eff({"class-a": "refuse", "class-c": "bounded_tolerance"}))
    assert base != v5.effective_policy_digest(FAM, eff({"class-a": "refuse"}))
    assert base != v5.effective_policy_digest(FAM, eff({"class-a": "refuse", "class-b": "bounded_tolerance", "class-c": "refuse"}))


def test_every_value_pair_has_an_independently_checked_digest():
    for a in f.VALUES:
        for b in f.VALUES:
            e = eff({"class-a": a, "class-b": b})
            assert v5.effective_policy_digest(FAM, e) == independent_digest(v5.effective_preimage(FAM, e))


def test_deterministic_and_input_form_independent():
    d = v5.effective_policy_digest(FAM, eff())
    assert d == v5.effective_policy_digest(FAM, {FIELD: dict(reversed(list(eff()[FIELD].items())))})


def test_a_refuse_value_is_not_a_deny_all_dimension():
    assert v5.deny_all_dimensions(FAM, eff({"class-a": "refuse"})) == []
    assert v5.effective_preimage(FAM, eff({"class-a": "refuse"}))["deny_all"] == []


def test_no_other_version_or_family_identity_can_equal_or_accept_it():
    assert code(v2pi.effective_policy_digest, FAM, eff()) == ("family_unsupported", "family")
    assert code(v4pi.effective_policy_digest, FAM, eff()) == ("family_unsupported", "family")
    assert code(v5.effective_policy_digest, "f5-action-class-age-bounds", {"class_status_max_age_seconds": {"class-a": 30}}) == ("family_unsupported", "family")
    # the r08-v2 F5 age identity of an unrelated payload is a different family and a different domain
    age = v2pi.effective_policy_digest("f5-action-class-age-bounds", {"class_status_max_age_seconds": {"class-a": 30}})
    assert age != v5.effective_policy_digest(FAM, eff())


def test_domain_separation_and_version_dispatch():
    pre = v5.effective_preimage(FAM, eff())
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    for dom in (b"ocs-reg/r08-v2/effective-policy\n", b"ocs-reg/r08-v3/effective-policy\n", b"ocs-reg/r08-v4/effective-policy\n"):
        assert "sha256:" + hashlib.sha256(dom + body).hexdigest() != v5.effective_policy_digest(FAM, eff())
    for ver in ("r08-v4", "r08-v3", "r08-v2", "r08-v1", "R08-V5", ""):
        assert code(v5.effective_policy_digest, FAM, eff(), ver) == ("contract_unsupported", "contract_version")
    assert code(v5.effective_policy_digest, FAM, eff(), None) == ("field_type_invalid", "contract_version")
    assert code(v5.effective_policy_digest, None, eff()) == ("field_type_invalid", "family")


def test_missing_unknown_and_type_refusals():
    assert code(v5.effective_policy_digest, FAM, {}) == ("field_missing", FIELD)
    assert code(v5.effective_policy_digest, FAM, dict(eff(), zzz=1)) == ("field_unknown", "zzz")
    assert code(v5.effective_policy_digest, FAM, {FIELD: []}) == ("field_type_invalid", FIELD)
    assert code(v5.effective_policy_digest, FAM, {FIELD: "refuse"}) == ("field_type_invalid", FIELD)
    for bad in (None, True, 1, 1.0, b"refuse", ["refuse"]):
        assert code(v5.effective_policy_digest, FAM, eff({"class-a": bad})) == ("field_type_invalid", FIELD + ".class-a")


@pytest.mark.parametrize("bad", ["Refuse", "tolerate", "", "refuse ", "bounded-tolerance"])
def test_unknown_values_refuse(bad):
    assert code(v5.effective_policy_digest, FAM, eff({"class-a": bad})) == ("field_invalid", FIELD + ".class-a")


@pytest.mark.parametrize("m", [{}, {"*": "refuse"}, {"": "refuse"}, {"a" * 129: "refuse"}, {"class a": "refuse"}, {"a\n": "refuse"}])
def test_class_key_and_size_refusals(m):
    assert code(v5.effective_policy_digest, FAM, eff(m)) == ("field_invalid", FIELD)


def test_too_many_classes_refused():
    many = {("c%03d" % i): "refuse" for i in range(257)}
    assert code(v5.effective_policy_digest, FAM, eff(many)) == ("field_invalid", FIELD)


def test_composed_effective_policy_round_trips_through_identity():
    from registry_successor.record import RecordResult
    rec = t.record()
    res = f.compose_f5u(t.caller(), RecordResult(True, None, "", rec, rec["record_digest"]))
    assert v5.effective_policy_digest(FAM, res.effective) == independent_digest(v5.effective_preimage(FAM, res.effective))
