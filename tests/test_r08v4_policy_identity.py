"""M3 PR-1: effective-policy identity for `f1abcd-local-execution-limits` under `r08-v4` (BUILDER_TESTED; not independently qualified).

The digest is recomputed with an independent canonical encoder (not the module's), so a serializer defect cannot hide itself.
"""
import hashlib
import json
from pathlib import Path

import pytest

import r08v4_support as t
from registry_successor import v2_policy_identity as v2pi
from registry_successor import v3_f1abc
from registry_successor import v3_policy_identity as v3pi
from registry_successor import v4_f1abcd as f
from registry_successor import v4_policy_identity as v4

VECTORS = json.loads((Path(__file__).parent / "vectors" / "r08v4" / "identity_vectors.json").read_text())
FAM = f.FAMILY_F1ABCD


def independent_digest(preimage):
    body = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(b"ocs-reg/r08-v4/effective-policy\n" + body).hexdigest()


def eff(**over):
    p = dict(t.payload(), allowed_actions=["act-copy", "act-list"])
    p.update(over)
    return p


def code(fn, *a, **k):
    with pytest.raises(v4.IdentityRefusal) as e:
        fn(*a, **k)
    return e.value.code, e.value.member


@pytest.mark.parametrize("vec", VECTORS["vectors"], ids=[x["id"] for x in VECTORS["vectors"]])
def test_pinned_vectors(vec):
    pre = v4.effective_preimage(FAM, vec["effective"])
    assert pre == vec["preimage"]
    assert v4.effective_policy_digest(FAM, vec["effective"]) == vec["digest"] == independent_digest(vec["preimage"])


def test_preimage_shape_and_binding_of_all_nine_members():
    pre = v4.effective_preimage(FAM, eff())
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v4", "family": FAM, "family_version": "v4",
                   "deny_all": [], "effective": eff()}
    assert len(pre["effective"]) == 9 and v4.effective_policy_digest(FAM, eff()) == independent_digest(pre)


@pytest.mark.parametrize("name,other", [("allowed_actions", ["act-copy"]), ("allowed_adapters", ["a-other"]), ("allowed_units", ["u-write"]),
                                        ("allowed_institutions", ["inst-b"]), ("allowed_authority_domains", ["domain-b"]), ("max_amount", 101),
                                        ("max_effects", 4), ("allowed_target_prefixes", ["rec/in/"]), ("target_match", "exact")])
def test_changing_any_one_of_the_nine_members_changes_the_digest(name, other):
    assert v4.effective_policy_digest(FAM, eff()) != v4.effective_policy_digest(FAM, eff(**{name: other}))


def test_v3_seven_member_identity_cannot_equal_a_v4_identity():
    seven = {k: v for k, v in eff().items() if k in v3_f1abc.F1ABC_FIELDS}
    assert v3pi.effective_policy_digest(v3_f1abc.FAMILY_F1ABC, seven) != v4.effective_policy_digest(FAM, eff())
    assert code(v4.effective_policy_digest, FAM, seven)[0] == "field_missing"  # no default for the two new members
    assert code(v3pi.effective_policy_digest, FAM, eff()) == ("family_unsupported", "family")
    assert code(v2pi.effective_policy_digest, FAM, eff()) == ("family_unsupported", "family")
    assert code(v4.effective_policy_digest, v3_f1abc.FAMILY_F1ABC, eff()) == ("family_unsupported", "family")


def test_deterministic_and_input_form_independent():
    d = v4.effective_policy_digest(FAM, eff())
    assert d == v4.effective_policy_digest(FAM, dict(reversed(list(eff().items()))))
    assert d == v4.effective_policy_digest(FAM, dict(eff(), allowed_target_prefixes=("rec/in/", "rec/out")))


def test_deny_all_includes_empty_targets():
    assert v4.deny_all_dimensions(FAM, eff(allowed_target_prefixes=[])) == ["allowed_target_prefixes"]
    assert v4.deny_all_dimensions(FAM, eff(allowed_target_prefixes=[], max_effects=0, allowed_units=[])) == ["allowed_target_prefixes", "allowed_units", "max_effects"]
    assert v4.effective_preimage(FAM, eff(allowed_target_prefixes=[]))["deny_all"] == ["allowed_target_prefixes"]


def test_domain_separation_and_version_dispatch():
    pre = v4.effective_preimage(FAM, eff())
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    for dom in (b"ocs-reg/r08-v2/effective-policy\n", b"ocs-reg/r08-v3/effective-policy\n"):
        assert "sha256:" + hashlib.sha256(dom + body).hexdigest() != v4.effective_policy_digest(FAM, eff())
    for ver in ("r08-v3", "r08-v2", "r08-v1"):
        assert code(v4.effective_policy_digest, FAM, eff(), ver) == ("contract_unsupported", "contract_version")
    assert code(v4.effective_policy_digest, FAM, eff(), None) == ("field_type_invalid", "contract_version")


@pytest.mark.parametrize("name", f.F1ABCD_FIELDS)
def test_missing_and_unknown_members(name):
    p = eff()
    del p[name]
    assert code(v4.effective_policy_digest, FAM, p) == ("field_missing", name)
    assert code(v4.effective_policy_digest, FAM, dict(eff(), zzz=1)) == ("field_unknown", "zzz")


@pytest.mark.parametrize("bad", [True, 5.0, "5", None, b"5", [5]])
@pytest.mark.parametrize("name", f.CEILING_FIELDS)
def test_ceiling_type_refusals(name, bad):
    assert code(v4.effective_policy_digest, FAM, eff(**{name: bad})) == ("field_type_invalid", name)


@pytest.mark.parametrize("bad", ["rec/", None, 5, [1], ("rec/", 1)])
def test_prefix_type_refusals(bad):
    assert code(v4.effective_policy_digest, FAM, eff(allowed_target_prefixes=bad)) == ("field_type_invalid", "allowed_target_prefixes")


@pytest.mark.parametrize("bad", [["b", "a"], ["a", "a"], ["*"], [""], ["x" * 129], ["a b"], ["a\n"]])
def test_prefix_value_refusals(bad):
    assert code(v4.effective_policy_digest, FAM, eff(allowed_target_prefixes=bad)) == ("field_invalid", "allowed_target_prefixes")


@pytest.mark.parametrize("bad", [1, None, True, ["segment"], b"segment"])
def test_mode_type_refusals(bad):
    assert code(v4.effective_policy_digest, FAM, eff(target_match=bad)) == ("field_type_invalid", "target_match")


@pytest.mark.parametrize("bad", ["", "Segment", "prefix", "segment ", "legacy_prefix"])
def test_mode_value_refusals(bad):
    assert code(v4.effective_policy_digest, FAM, eff(target_match=bad)) == ("field_invalid", "target_match")


@pytest.mark.parametrize("mode", f.MODES)
def test_every_mode_has_an_independently_checked_digest(mode):
    assert v4.effective_policy_digest(FAM, eff(target_match=mode)) == independent_digest(v4.effective_preimage(FAM, eff(target_match=mode)))


def test_too_many_prefixes_refused():
    many = sorted("p%03d" % i for i in range(257))
    assert code(v4.effective_policy_digest, FAM, eff(allowed_target_prefixes=many)) == ("field_invalid", "allowed_target_prefixes")


@pytest.mark.parametrize("a", [0, 1, 2 ** 53])
@pytest.mark.parametrize("e", [0, 1, 2 ** 53 - 1])
def test_boundary_ceilings_have_a_digest(a, e):
    assert v4.effective_policy_digest(FAM, eff(max_amount=a, max_effects=e)) == independent_digest(v4.effective_preimage(FAM, eff(max_amount=a, max_effects=e)))


def test_composed_effective_policy_round_trips_through_identity():
    from registry_successor.record import RecordResult
    rec = t.record()
    res = f.compose_f1abcd(t.caller(), RecordResult(True, None, "", rec, rec["record_digest"]))
    plain = {k: (list(v) if isinstance(v, tuple) else v) for k, v in res.effective.items()}
    assert v4.effective_policy_digest(FAM, plain) == independent_digest(v4.effective_preimage(FAM, plain))
