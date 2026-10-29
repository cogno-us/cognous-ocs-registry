"""Effective-policy identity for the two `r08-v6` families (BUILDER_TESTED; not independently qualified).

The digest is recomputed with an independent canonical encoder (not the module's), so a serializer defect cannot hide itself.
"""
import hashlib
import itertools
import json
from pathlib import Path

import pytest

import r08v6_support as t
from registry_successor import v2_policy_identity as v2pi
from registry_successor import v3_policy_identity as v3pi
from registry_successor import v4_policy_identity as v4pi
from registry_successor import v5_policy_identity as v5pi
from registry_successor import v6_class_revocation_assurance as f
from registry_successor import v6_policy_identity as v6
from registry_successor import v6_terminal_revocation as ft

VECTORS = json.loads((Path(__file__).parent / "vectors" / "r08v6" / "identity_vectors.json").read_text())
RA = f.FAMILY_F5RA
TR = ft.FAMILY_TR
RF = f.F5RA_FIELD
TF = ft.TR_FIELD
DOMAIN = b"ocs-reg/r08-v6/effective-policy\n"


def independent_digest(preimage, domain=DOMAIN):
    body = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(domain + body).hexdigest()


def eff(m=None):
    return {RF: dict(m if m is not None else {"class-a": "required", "class-b": "not_required"})}


def tr(v="on"):
    return {TF: v}


def code(fn, *a, **k):
    with pytest.raises(v6.IdentityRefusal) as e:
        fn(*a, **k)
    return e.value.code, e.value.member


@pytest.mark.parametrize("vec", VECTORS["vectors"], ids=[x["id"] for x in VECTORS["vectors"]])
def test_pinned_vectors(vec):
    pre = v6.effective_preimage(vec["family"], vec["effective"])
    assert pre == vec["preimage"]
    assert v6.effective_policy_digest(vec["family"], vec["effective"]) == vec["digest"] == independent_digest(vec["preimage"])


def test_vectors_cover_both_families_and_the_domain_is_pinned():
    assert {v["family"] for v in VECTORS["vectors"]} == {RA, TR}
    assert VECTORS["domain"].encode().decode("unicode_escape").encode() == DOMAIN == v6.EFFECTIVE_PREFIX
    assert VECTORS["profile"] == v6.EFFECTIVE_PROFILE


def test_preimage_shape_f5ra():
    pre = v6.effective_preimage(RA, eff())
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v6", "family": RA, "family_version": "v6",
                   "deny_all": [], "effective": eff()}
    assert v6.effective_policy_digest(RA, eff()) == independent_digest(pre)


def test_preimage_shape_terminal_revocation():
    pre = v6.effective_preimage(TR, tr())
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v6", "family": TR, "family_version": "v6",
                   "deny_all": [], "effective": tr()}
    assert v6.effective_policy_digest(TR, tr()) == independent_digest(pre)


def test_family_rows_are_exactly_the_two_registered_families_with_version_v6():
    assert set(v6.IDENTITY_FAMILIES) == {RA, TR}
    assert v6.IDENTITY_FAMILIES[RA].family_version == v6.IDENTITY_FAMILIES[TR].family_version == "v6" == v6.FAMILY_VERSION
    assert v6.IDENTITY_FAMILIES[RA].kind == "classmap-enum" and v6.IDENTITY_FAMILIES[TR].kind == "scalar-enum"
    assert v6.IDENTITY_FAMILIES[RA].members == f.F5RA_FIELDS and v6.IDENTITY_FAMILIES[TR].members == ft.TR_FIELDS
    assert v6.registered_family_version(RA, "r08-v6") == v6.registered_family_version(TR, "r08-v6") == "v6"
    assert v6.REGISTERED_CONTRACT_VERSIONS == ("r08-v6",) and v6.CONTRACT_VERSION == "r08-v6"


def test_changing_any_class_or_value_changes_the_digest():
    base = v6.effective_policy_digest(RA, eff())
    assert base != v6.effective_policy_digest(RA, eff({"class-a": "not_required", "class-b": "not_required"}))
    assert base != v6.effective_policy_digest(RA, eff({"class-a": "required", "class-b": "required"}))
    assert base != v6.effective_policy_digest(RA, eff({"class-a": "required", "class-c": "not_required"}))
    assert base != v6.effective_policy_digest(RA, eff({"class-a": "required"}))
    assert base != v6.effective_policy_digest(RA, eff({"class-a": "required", "class-b": "not_required", "class-c": "required"}))


def test_every_value_pair_and_scalar_has_an_independently_checked_digest_and_all_are_distinct():
    seen = set()
    for a, b in itertools.product(f.VALUES, repeat=2):
        e = eff({"class-a": a, "class-b": b})
        d = v6.effective_policy_digest(RA, e)
        assert d == independent_digest(v6.effective_preimage(RA, e))
        seen.add(d)
    for v in ft.VALUES:
        d = v6.effective_policy_digest(TR, tr(v))
        assert d == independent_digest(v6.effective_preimage(TR, tr(v)))
        seen.add(d)
    assert len(seen) == 6


def test_deterministic_and_input_form_independent():
    d = v6.effective_policy_digest(RA, eff())
    assert d == v6.effective_policy_digest(RA, {RF: dict(reversed(list(eff()[RF].items())))})


def test_neither_family_is_a_deny_all_dimension():
    assert v6.deny_all_dimensions(RA, eff({"class-a": "required"})) == []
    assert v6.deny_all_dimensions(TR, tr("on")) == []
    assert v6.effective_preimage(RA, eff({"class-a": "required"}))["deny_all"] == []
    assert v6.effective_preimage(TR, tr("on"))["deny_all"] == []
    assert code(v6.deny_all_dimensions, TR, tr("x")) == ("field_invalid", TF)


def test_family_is_bound_into_the_digest_and_the_payload_cannot_cross_families():
    assert code(v6.effective_policy_digest, RA, tr()) == ("field_missing", RF)
    assert code(v6.effective_policy_digest, TR, eff()) == ("field_missing", TF)
    assert code(v6.effective_policy_digest, TR, dict(tr(), **eff())) == ("field_unknown", RF)
    # the same preimage members with the other family string would hash differently; the family is in the preimage
    pre = v6.effective_preimage(TR, tr("on"))
    assert independent_digest(dict(pre, family=RA)) != v6.effective_policy_digest(TR, tr("on"))
    assert independent_digest(dict(pre, family_version="v5")) != v6.effective_policy_digest(TR, tr("on"))
    assert independent_digest(dict(pre, contract_version="r08-v5")) != v6.effective_policy_digest(TR, tr("on"))
    assert independent_digest(dict(pre, deny_all=["x"])) != v6.effective_policy_digest(TR, tr("on"))
    assert independent_digest(dict(pre, effective_policy_profile="ocs-effective-policy/2")) != v6.effective_policy_digest(TR, tr("on"))
    assert independent_digest(dict(pre, effective=tr("off"))) != v6.effective_policy_digest(TR, tr("on"))


def test_no_earlier_identity_accepts_these_families_and_domains_are_separated():
    for mod in (v2pi, v3pi, v4pi, v5pi):
        assert code(mod.effective_policy_digest, RA, eff()) == ("family_unsupported", "family")
        assert code(mod.effective_policy_digest, TR, tr()) == ("family_unsupported", "family")
    assert code(v6.effective_policy_digest, "f5-action-class-unreadable-policy", {"class_on_unreadable": {"class-a": "refuse"}}) == ("family_unsupported", "family")
    assert code(v6.effective_policy_digest, "f5-action-class-age-bounds", {"class_status_max_age_seconds": {"class-a": 30}}) == ("family_unsupported", "family")
    for family, e in ((RA, eff()), (TR, tr())):
        pre = v6.effective_preimage(family, e)
        for dom in (b"ocs-reg/r08-v2/effective-policy\n", b"ocs-reg/r08-v3/effective-policy\n", b"ocs-reg/r08-v4/effective-policy\n",
                    b"ocs-reg/r08-v5/effective-policy\n", b"", b"ocs-reg/r08-v6/selection\n"):
            assert independent_digest(pre, dom) != v6.effective_policy_digest(family, e)


def test_contract_version_dispatch():
    for family, e in ((RA, eff()), (TR, tr())):
        for ver in ("r08-v5", "r08-v4", "r08-v3", "r08-v2", "r08-v1", "R08-V6", "", "r08-v6 "):
            assert code(v6.effective_policy_digest, family, e, ver) == ("contract_unsupported", "contract_version")
        assert code(v6.effective_policy_digest, family, e, None) == ("field_type_invalid", "contract_version")
        assert code(v6.effective_policy_digest, family, e, b"r08-v6") == ("field_type_invalid", "contract_version")
        assert v6.effective_policy_digest(family, e, "r08-v6") == v6.effective_policy_digest(family, e)
    assert code(v6.effective_policy_digest, None, eff()) == ("field_type_invalid", "family")
    assert code(v6.effective_policy_digest, 5, tr()) == ("field_type_invalid", "family")
    assert code(v6.effective_policy_digest, "nope", tr()) == ("family_unsupported", "family")


def test_f5ra_missing_unknown_type_and_value_refusals():
    assert code(v6.effective_policy_digest, RA, {}) == ("field_missing", RF)
    assert code(v6.effective_policy_digest, RA, dict(eff(), zzz=1)) == ("field_unknown", "zzz")
    assert code(v6.effective_policy_digest, RA, {RF: []}) == ("field_type_invalid", RF)
    assert code(v6.effective_policy_digest, RA, {RF: "required"}) == ("field_type_invalid", RF)
    assert code(v6.effective_policy_digest, RA, None) == ("field_type_invalid", None)
    for bad in (None, True, False, 1, 1.0, b"required", ["required"]):
        assert code(v6.effective_policy_digest, RA, eff({"class-a": bad})) == ("field_type_invalid", RF + ".class-a")
    for bad in ("Required", "optional", "", "required ", "not-required", "true", "false"):
        assert code(v6.effective_policy_digest, RA, eff({"class-a": bad})) == ("field_invalid", RF + ".class-a")


@pytest.mark.parametrize("m", [{}, {"*": "required"}, {"": "required"}, {"a" * 129: "required"}, {"class a": "required"}, {"a\n": "required"}])
def test_f5ra_class_key_and_size_refusals(m):
    assert code(v6.effective_policy_digest, RA, eff(m)) == ("field_invalid", RF)


def test_f5ra_too_many_classes_refused_and_the_limit_accepted():
    assert code(v6.effective_policy_digest, RA, eff({("c%03d" % i): "required" for i in range(257)})) == ("field_invalid", RF)
    assert v6.effective_policy_digest(RA, eff({("c%03d" % i): "required" for i in range(256)})).startswith("sha256:")


def test_terminal_revocation_missing_unknown_type_and_value_refusals():
    assert code(v6.effective_policy_digest, TR, {}) == ("field_missing", TF)
    assert code(v6.effective_policy_digest, TR, dict(tr(), zzz=1)) == ("field_unknown", "zzz")
    for bad in (None, True, False, 0, 1, 1.0, b"on", ["on"], {"x": "on"}):
        assert code(v6.effective_policy_digest, TR, tr(bad)) == ("field_type_invalid", TF)
    for bad in ("On", "ON", "OFF", "", "on ", "true", "false", "enabled"):
        assert code(v6.effective_policy_digest, TR, tr(bad)) == ("field_invalid", TF)


def test_str_subclass_and_non_dict_payloads_refuse():
    class S(str):
        pass
    assert code(v6.effective_policy_digest, TR, tr(S("on")))[0] in ("field_type_invalid", "field_invalid")
    assert code(v6.effective_policy_digest, RA, eff({"class-a": S("required")}))[0] in ("field_type_invalid", "field_invalid")
    assert code(v6.effective_policy_digest, TR, "on")[0] == "field_type_invalid"
    assert code(v6.effective_policy_digest, TR, ["terminal_revocation"])[0] == "field_type_invalid"


def test_composed_effective_policies_round_trip_through_identity():
    from registry_successor import v6_families as fam
    from registry_successor.record import RecordResult
    for family in (RA, TR):
        rec = t.record(family=family)
        res = fam.compose_for_v6("r08-v6", t.caller(family), RecordResult(True, None, "", rec, rec["record_digest"]))
        assert res.ok
        assert v6.effective_policy_digest(family, res.effective) == independent_digest(v6.effective_preimage(family, res.effective))
