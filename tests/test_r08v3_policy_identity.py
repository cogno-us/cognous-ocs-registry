"""M2 PR-1: effective-policy identity for `f1abc-local-execution-limits` under `r08-v3` (BUILDER_TESTED; not independently qualified).

The digest is recomputed here with an independent canonical encoder (not the module's), so a serializer defect cannot hide itself.
"""
import hashlib
import json
from pathlib import Path

import pytest

import r08v3_support as t
from registry_successor import v2_policy_identity as v2pi
from registry_successor import v3_f1abc as f
from registry_successor import v3_policy_identity as v3

VECTORS = json.loads((Path(__file__).parent / "vectors" / "r08v3" / "identity_vectors.json").read_text())
FAM = f.FAMILY_F1ABC


def independent_digest(preimage):
    body = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(b"ocs-reg/r08-v3/effective-policy\n" + body).hexdigest()


def eff(**over):
    p = {"allowed_actions": ["act-copy", "act-list"], "allowed_adapters": ["a-local"], "allowed_units": ["u-read"],
         "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"], "max_amount": 100, "max_effects": 3}
    p.update(over)
    return p


def code(fn, *a, **k):
    with pytest.raises(v3.IdentityRefusal) as e:
        fn(*a, **k)
    return e.value.code, e.value.member


@pytest.mark.parametrize("vec", VECTORS["vectors"], ids=[x["id"] for x in VECTORS["vectors"]])
def test_pinned_vectors(vec):
    pre = v3.effective_preimage(FAM, vec["effective"])
    assert pre == vec["preimage"]
    assert v3.effective_policy_digest(FAM, vec["effective"]) == vec["digest"] == independent_digest(vec["preimage"])


def test_preimage_shape_and_binding_of_all_seven_members():
    pre = v3.effective_preimage(FAM, eff())
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v3", "family": FAM, "family_version": "v3",
                   "deny_all": [], "effective": eff()}
    assert v3.effective_policy_digest(FAM, eff()) == independent_digest(pre)


@pytest.mark.parametrize("name,other", [("allowed_actions", ["act-copy"]), ("allowed_adapters", ["a-other"]), ("allowed_units", ["u-write"]),
                                        ("allowed_institutions", ["inst-b"]), ("allowed_authority_domains", ["domain-b"]), ("max_amount", 101),
                                        ("max_effects", 4)])
def test_changing_any_one_of_the_seven_members_changes_the_digest(name, other):
    assert v3.effective_policy_digest(FAM, eff()) != v3.effective_policy_digest(FAM, eff(**{name: other}))


def test_deterministic_and_input_form_independent():
    d = v3.effective_policy_digest(FAM, eff())
    assert d == v3.effective_policy_digest(FAM, eff())
    shuffled = dict(reversed(list(eff().items())))
    assert d == v3.effective_policy_digest(FAM, shuffled)
    tupled = dict(eff(), allowed_actions=("act-copy", "act-list"))
    assert d == v3.effective_policy_digest(FAM, tupled)  # tuples are copied as lists by the shared boundary


def test_deny_all_is_part_of_the_identity():
    z = v3.effective_preimage(FAM, eff(max_effects=0, allowed_units=[]))
    assert z["deny_all"] == ["allowed_units", "max_effects"]
    assert v3.deny_all_dimensions(FAM, eff(max_effects=0)) == ["max_effects"]
    assert v3.deny_all_dimensions(FAM, eff(max_amount=0)) == []  # a zero amount ceiling is not deny-all


def test_domain_separation_from_r08_v2():
    pre = v3.effective_preimage(FAM, eff())
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    as_v2 = "sha256:" + hashlib.sha256(b"ocs-reg/r08-v2/effective-policy\n" + body).hexdigest()
    assert as_v2 != v3.effective_policy_digest(FAM, eff())


def test_v2_identity_module_still_refuses_this_family_and_v3_refuses_v2_inputs():
    assert code(v2pi.effective_policy_digest, FAM, eff()) == ("family_unsupported", "family")
    assert code(v3.effective_policy_digest, "f1ab-local-execution-allowlist", eff()) == ("family_unsupported", "family")
    assert code(v3.effective_policy_digest, FAM, eff(), "r08-v2") == ("contract_unsupported", "contract_version")
    assert code(v3.effective_policy_digest, FAM, eff(), "r08-v1") == ("contract_unsupported", "contract_version")
    assert code(v3.effective_policy_digest, FAM, eff(), None) == ("field_type_invalid", "contract_version")
    assert code(v3.effective_policy_digest, None, eff()) == ("field_type_invalid", "family")


@pytest.mark.parametrize("name", f.F1ABC_FIELDS)
def test_missing_and_unknown_members(name):
    p = eff()
    del p[name]
    assert code(v3.effective_policy_digest, FAM, p) == ("field_missing", name)
    assert code(v3.effective_policy_digest, FAM, dict(eff(), zzz=1)) == ("field_unknown", "zzz")


@pytest.mark.parametrize("bad", [True, 5.0, "5", None, b"5", [5]])
@pytest.mark.parametrize("name", f.CEILING_FIELDS)
def test_ceiling_type_refusals(name, bad):
    assert code(v3.effective_policy_digest, FAM, eff(**{name: bad})) == ("field_type_invalid", name)


@pytest.mark.parametrize("v", [-1, 2 ** 53 + 1, 2 ** 63, 10 ** 19, 10 ** 20, 10 ** 30])
def test_amount_out_of_range(v):
    assert code(v3.effective_policy_digest, FAM, eff(max_amount=v)) == ("field_invalid", "max_amount")


@pytest.mark.parametrize("v", [-1, 2 ** 53, 2 ** 63, 10 ** 20, 10 ** 30])
def test_effects_out_of_range(v):
    assert code(v3.effective_policy_digest, FAM, eff(max_effects=v)) == ("field_invalid", "max_effects")


@pytest.mark.parametrize("a", [0, 1, 2 ** 53])
@pytest.mark.parametrize("e", [0, 1, 2 ** 53 - 1])
def test_boundary_values_have_a_digest(a, e):
    assert v3.effective_policy_digest(FAM, eff(max_amount=a, max_effects=e)) == independent_digest(
        v3.effective_preimage(FAM, eff(max_amount=a, max_effects=e)))


@pytest.mark.parametrize("bad", [["b", "a"], ["a", "a"], ["*"], [""], ["x" * 129]])
def test_set_value_refusals_follow_the_frozen_f1ab_rules(bad):
    assert code(v3.effective_policy_digest, FAM, eff(allowed_units=bad))[0] == "field_invalid"


def test_set_type_refusal():
    assert code(v3.effective_policy_digest, FAM, eff(allowed_units="u"))[0] == "field_type_invalid"
    assert code(v3.effective_policy_digest, FAM, eff(allowed_units=[1]))[0] == "field_type_invalid"


def test_composed_effective_policy_round_trips_through_identity():
    res = f.compose_f1abc(t.caller(), type("R", (), {"ok": True, "record": {"family": FAM, "payload": t.payload()}})())
    plain = {k: (list(v) if k in f.SET_FIELDS else v) for k, v in res.effective.items()}
    assert v3.effective_policy_digest(FAM, plain) == independent_digest(v3.effective_preimage(FAM, plain))
