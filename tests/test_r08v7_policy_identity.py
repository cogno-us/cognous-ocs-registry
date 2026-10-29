"""Effective-policy identity for the `r08-v7` irreversibility family (BUILDER_TESTED; not independently qualified).

The digest is recomputed with an independent canonical encoder (not the module's), so a serializer defect cannot hide itself. The preimage carries the
INTEGER `family_schema_revision` (separate from the envelope protocol version) and never the legacy `family_version` tag.
"""
import hashlib
import itertools
import json
from pathlib import Path

import pytest

import r08v7_support as t
from registry_successor import v2_policy_identity as v2pi
from registry_successor import v3_policy_identity as v3pi
from registry_successor import v4_policy_identity as v4pi
from registry_successor import v5_policy_identity as v5pi
from registry_successor import v6_policy_identity as v6pi
from registry_successor import v7_policy_identity as v7
from registry_successor.engine import families_irreversibility as f

VECTORS = json.loads((Path(__file__).parent / "vectors" / "r08v7" / "identity_vectors.json").read_text())
FAM = f.FAMILY_IRREVERSIBILITY
FIELD = f.IRR_FIELD
DOMAIN = b"ocs-reg/r08-v7/effective-policy\n"


def independent_digest(preimage, domain=DOMAIN):
    body = json.dumps(preimage, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(domain + body).hexdigest()


def eff(m=None):
    return {FIELD: dict(m if m is not None else {"class-a": "irreversible", "class-b": "no_change"})}


def code(fn, *a, **k):
    with pytest.raises(v7.IdentityRefusal) as e:
        fn(*a, **k)
    return e.value.code, e.value.member


@pytest.mark.parametrize("vec", VECTORS["vectors"], ids=[x["id"] for x in VECTORS["vectors"]])
def test_pinned_vectors(vec):
    pre = v7.effective_preimage(vec["family"], vec["effective"])
    assert pre == vec["preimage"]
    assert v7.effective_policy_digest(vec["family"], vec["effective"]) == vec["digest"] == independent_digest(vec["preimage"])


def test_vectors_cover_the_one_family_and_the_domain_is_pinned():
    assert {v["family"] for v in VECTORS["vectors"]} == {FAM}
    assert VECTORS["domain"].encode().decode("unicode_escape").encode() == DOMAIN == v7.EFFECTIVE_PREFIX
    assert VECTORS["profile"] == v7.EFFECTIVE_PROFILE


def test_preimage_shape_carries_the_integer_schema_revision_not_the_legacy_tag():
    pre = v7.effective_preimage(FAM, eff())
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v7", "family": FAM, "family_schema_revision": 1,
                   "deny_all": [], "effective": eff()}
    assert "family_version" not in pre and type(pre["family_schema_revision"]) is int
    assert v7.effective_policy_digest(FAM, eff()) == independent_digest(pre)


def test_the_schema_revision_is_part_of_the_digest():
    pre = v7.effective_preimage(FAM, eff())
    base = v7.effective_policy_digest(FAM, eff())
    assert independent_digest(dict(pre, family_schema_revision=2)) != base
    assert independent_digest(dict(pre, family_schema_revision=0)) != base
    assert independent_digest(dict(pre, family_schema_revision="1")) != base
    legacy = {k: v for k, v in pre.items() if k != "family_schema_revision"}
    assert independent_digest(dict(legacy, family_version="v7")) != base
    assert independent_digest(legacy) != base


def test_family_row_is_exactly_the_one_registered_family_with_revision_1():
    assert set(v7.IDENTITY_FAMILIES) == {FAM}
    row = v7.IDENTITY_FAMILIES[FAM]
    assert row.kind == "classmap-enum" and row.members == f.IRR_FIELDS and row.version_member == "family_schema_revision" and row.version_value == 1
    assert v7.registered_family_version(FAM, "r08-v7") == 1 and type(v7.registered_family_version(FAM, "r08-v7")) is int
    assert v7.REGISTERED_CONTRACT_VERSIONS == ("r08-v7",) and v7.CONTRACT_VERSION == "r08-v7"


def test_changing_any_class_or_value_changes_the_digest():
    base = v7.effective_policy_digest(FAM, eff())
    assert base != v7.effective_policy_digest(FAM, eff({"class-a": "no_change", "class-b": "no_change"}))
    assert base != v7.effective_policy_digest(FAM, eff({"class-a": "irreversible", "class-b": "irreversible"}))
    assert base != v7.effective_policy_digest(FAM, eff({"class-a": "irreversible", "class-c": "no_change"}))
    assert base != v7.effective_policy_digest(FAM, eff({"class-a": "irreversible"}))
    assert base != v7.effective_policy_digest(FAM, eff({"class-a": "irreversible", "class-b": "no_change", "class-c": "irreversible"}))


def test_every_value_pair_has_an_independently_checked_digest_and_all_are_distinct():
    seen = set()
    for a, b in itertools.product(f.VALUES, repeat=2):
        e = eff({"class-a": a, "class-b": b})
        d = v7.effective_policy_digest(FAM, e)
        assert d == independent_digest(v7.effective_preimage(FAM, e))
        seen.add(d)
    assert len(seen) == 4


def test_deterministic_and_input_form_independent():
    d = v7.effective_policy_digest(FAM, eff())
    assert d == v7.effective_policy_digest(FAM, {FIELD: dict(reversed(list(eff()[FIELD].items())))})


def test_the_family_is_not_a_deny_all_dimension():
    assert v7.deny_all_dimensions(FAM, eff({"class-a": "irreversible"})) == []
    assert v7.effective_preimage(FAM, eff({"class-a": "irreversible"}))["deny_all"] == []
    assert code(v7.deny_all_dimensions, FAM, eff({"class-a": "x"})) == ("field_invalid", FIELD + ".class-a")


def test_family_and_contract_are_bound_into_the_digest():
    pre = v7.effective_preimage(FAM, eff())
    d = v7.effective_policy_digest(FAM, eff())
    assert independent_digest(dict(pre, family="f5-action-class-revocation-assurance-policy")) != d
    assert independent_digest(dict(pre, contract_version="r08-v6")) != d
    assert independent_digest(dict(pre, deny_all=["x"])) != d
    assert independent_digest(dict(pre, effective_policy_profile="ocs-effective-policy/2")) != d
    assert independent_digest(dict(pre, effective=eff({"class-a": "no_change"}))) != d


def test_no_other_identity_accepts_this_family_and_domains_are_separated():
    for mod in (v2pi, v3pi, v4pi, v5pi, v6pi):
        assert code(mod.effective_policy_digest, FAM, eff()) == ("family_unsupported", "family")
    # and v7 refuses every earlier family
    assert code(v7.effective_policy_digest, "f5-action-class-revocation-assurance-policy", {"class_requires_revocation_assurance": {"class-a": "required"}}) == (
        "family_unsupported", "family")
    assert code(v7.effective_policy_digest, "f5-terminal-revocation-enablement-policy", {"terminal_revocation": "on"}) == ("family_unsupported", "family")
    assert code(v7.effective_policy_digest, "f5-action-class-unreadable-policy", {"class_on_unreadable": {"class-a": "refuse"}}) == ("family_unsupported", "family")
    assert code(v7.effective_policy_digest, "f5-action-class-age-bounds", {"class_status_max_age_seconds": {"class-a": 30}}) == ("family_unsupported", "family")
    pre = v7.effective_preimage(FAM, eff())
    for dom in (b"ocs-reg/r08-v2/effective-policy\n", b"ocs-reg/r08-v3/effective-policy\n", b"ocs-reg/r08-v4/effective-policy\n",
                b"ocs-reg/r08-v5/effective-policy\n", b"ocs-reg/r08-v6/effective-policy\n", b"", b"ocs-reg/r08-v7/selection\n"):
        assert independent_digest(pre, dom) != v7.effective_policy_digest(FAM, eff())


def test_contract_version_dispatch():
    for ver in ("r08-v6", "r08-v5", "r08-v4", "r08-v3", "r08-v2", "r08-v1", "R08-V7", "", "r08-v7 "):
        assert code(v7.effective_policy_digest, FAM, eff(), ver) == ("contract_unsupported", "contract_version")
    assert code(v7.effective_policy_digest, FAM, eff(), None) == ("field_type_invalid", "contract_version")
    assert code(v7.effective_policy_digest, FAM, eff(), b"r08-v7") == ("field_type_invalid", "contract_version")
    assert v7.effective_policy_digest(FAM, eff(), "r08-v7") == v7.effective_policy_digest(FAM, eff())
    assert code(v7.effective_policy_digest, None, eff()) == ("field_type_invalid", "family")
    assert code(v7.effective_policy_digest, 5, eff()) == ("field_type_invalid", "family")
    assert code(v7.effective_policy_digest, "nope", eff()) == ("family_unsupported", "family")
    # v6 identity refuses r08-v7 as the contract version
    assert code(v6pi.effective_policy_digest, "f5-action-class-revocation-assurance-policy", {"class_requires_revocation_assurance": {"class-a": "required"}},
                "r08-v7") == ("contract_unsupported", "contract_version")


def test_missing_unknown_type_and_value_refusals():
    assert code(v7.effective_policy_digest, FAM, {}) == ("field_missing", FIELD)
    assert code(v7.effective_policy_digest, FAM, dict(eff(), zzz=1)) == ("field_unknown", "zzz")
    assert code(v7.effective_policy_digest, FAM, {FIELD: []}) == ("field_type_invalid", FIELD)
    assert code(v7.effective_policy_digest, FAM, {FIELD: "irreversible"}) == ("field_type_invalid", FIELD)
    assert code(v7.effective_policy_digest, FAM, None) == ("field_type_invalid", None)
    assert code(v7.effective_policy_digest, FAM, {"terminal_revocation": "on"}) == ("field_missing", FIELD)
    for bad in (None, True, False, 1, 1.0, b"irreversible", ["irreversible"]):
        assert code(v7.effective_policy_digest, FAM, eff({"class-a": bad})) == ("field_type_invalid", FIELD + ".class-a")
    for bad in ("Irreversible", "reversible", "", "irreversible ", "no-change", "true", "false", "required", "not_required"):
        assert code(v7.effective_policy_digest, FAM, eff({"class-a": bad})) == ("field_invalid", FIELD + ".class-a")


@pytest.mark.parametrize("m", [{}, {"*": "irreversible"}, {"": "irreversible"}, {"a" * 129: "irreversible"}, {"class a": "irreversible"}, {"a\n": "irreversible"}])
def test_class_key_and_size_refusals(m):
    assert code(v7.effective_policy_digest, FAM, eff(m)) == ("field_invalid", FIELD)


def test_too_many_classes_refused_and_the_limit_accepted():
    assert code(v7.effective_policy_digest, FAM, eff({("c%03d" % i): "irreversible" for i in range(257)})) == ("field_invalid", FIELD)
    assert v7.effective_policy_digest(FAM, eff({("c%03d" % i): "irreversible" for i in range(256)})).startswith("sha256:")


def test_str_subclass_and_non_dict_payloads_refuse():
    class S(str):
        pass
    assert code(v7.effective_policy_digest, FAM, eff({"class-a": S("irreversible")}))[0] in ("field_type_invalid", "field_invalid")
    assert code(v7.effective_policy_digest, FAM, "irreversible")[0] == "field_type_invalid"
    assert code(v7.effective_policy_digest, FAM, [FIELD])[0] == "field_type_invalid"
    assert code(v7.registered_family_version, S(FAM), "r08-v7")[0] == "field_type_invalid"
    assert code(v7.registered_family_version, FAM, S("r08-v7"))[0] == "field_type_invalid"


def test_composed_effective_policies_round_trip_through_identity():
    from registry_successor import v7_families as fam
    from registry_successor.record import RecordResult
    rec = t.record()
    res = fam.compose_for_v7("r08-v7", t.caller(), RecordResult(True, None, "", rec, rec["record_digest"]))
    assert res.ok
    assert v7.effective_policy_digest(FAM, res.effective) == independent_digest(v7.effective_preimage(FAM, res.effective))
