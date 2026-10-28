"""M11 PR-1: single-member family `f4t-control-plane-clock-tolerance` under `r08-v5`: validation, composition, identity, signed decision path, cross-version
and cross-family refusal (BUILDER_TESTED; not independently qualified). Real synthetic Ed25519 where a signature is involved."""
import hashlib
import json

import pytest

import r08_support as r
import r08v5_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import v2_age_bounds as f4
from registry_successor import v2_policy_identity as v2pi
from registry_successor import v5_f4t as f
from registry_successor import v5_policy_identity as ident
from registry_successor import v5_record, v5_selection
from registry_successor.record import RecordResult

MAXV = 2147483647
FAM = f.FAMILY_F4T


def rec_obj(pl=None):
    rec = t.record(pl)
    return RecordResult(True, None, "", rec, rec["record_digest"])


# ---- payload validator
@pytest.mark.parametrize("pl,code", [({}, "field_missing"), ({"clock_tolerance_seconds": 1, "x": 1}, "field_unknown"), ({"x": 1}, "field_unknown"),
                                     ({"clock_tolerance_seconds": True}, "field_type_invalid"), ({"clock_tolerance_seconds": 5.0}, "field_type_invalid"),
                                     ({"clock_tolerance_seconds": "5"}, "field_type_invalid"), ({"clock_tolerance_seconds": None}, "field_type_invalid"),
                                     ({"clock_tolerance_seconds": [5]}, "field_type_invalid"), ({"clock_tolerance_seconds": -1}, "field_invalid"),
                                     ({"clock_tolerance_seconds": MAXV + 1}, "field_invalid"), ({"clock_tolerance_seconds": 2 ** 63}, "field_invalid")])
def test_payload_validator(pl, code):
    assert f.payload_validator(pl) == code


@pytest.mark.parametrize("v", [0, 1, 5, MAXV - 1, MAXV])
def test_boundaries_are_valid_and_zero_is_not_deny_all(v):
    assert f.payload_validator({"clock_tolerance_seconds": v}) is None
    res = f.compose_f4t({"clock_tolerance_seconds": MAXV}, rec_obj({"clock_tolerance_seconds": v}))
    assert res.ok and res.effective == {"clock_tolerance_seconds": v} and res.deny_all is False and res.deny_all_fields == ()


# ---- composition: below / equal / above
@pytest.mark.parametrize("caller,registry,expected,detail", [(10, 5, 5, ""), (10, 10, 10, ""), (5, 10, 5, "registry_value_not_narrowing:clock_tolerance_seconds"),
                                                              (0, 7, 0, "registry_value_not_narrowing:clock_tolerance_seconds"), (3, 0, 0, ""),
                                                              (MAXV, MAXV, MAXV, "")])
def test_composition_never_widens(caller, registry, expected, detail):
    res = f.compose_f4t({"clock_tolerance_seconds": caller}, rec_obj({"clock_tolerance_seconds": registry}))
    assert res.ok and res.effective == {"clock_tolerance_seconds": expected} and expected <= caller and res.detail == detail


@pytest.mark.parametrize("bad", [True, 5.0, "5", None, -1, MAXV + 1, [5]])
def test_invalid_caller_refuses_and_is_never_replaced(bad):
    res = f.compose_f4t({"clock_tolerance_seconds": bad}, rec_obj())
    assert not res.ok and res.code == "composition_caller_invalid" and res.effective is None


@pytest.mark.parametrize("caller", [{}, {"clock_tolerance_seconds": 1, "x": 1}, {"status_max_age_seconds": 1}, None, [], "x"])
def test_wrong_caller_shape_refuses(caller):
    assert f.compose_f4t(caller, rec_obj()).code == "composition_caller_invalid"


def test_composition_refusals():
    assert f.compose_f4t(t.caller(), rec_obj(), "union").code == "composition_operator_unsupported"
    assert f.compose_f4t(t.caller(), None).code == "composition_record_invalid"
    other = rec_obj()
    other.record["family"] = f4.FAMILY_F4
    assert f.compose_f4t(t.caller(), other).code == "composition_family_unsupported"
    bad = rec_obj()
    bad.record["payload"]["clock_tolerance_seconds"] = 5.0
    assert f.compose_f4t(t.caller(), bad).code == "composition_record_invalid"


def test_f4_ages_are_not_in_this_family_and_f4_is_untouched():
    assert f4.F4_FIELDS == ("status_max_age_seconds", "approval_max_age_seconds")  # the existing F4 stays closed to two keys
    assert f.payload_validator({"status_max_age_seconds": 60}) == "field_unknown"
    assert f4.f4_payload_validator({"clock_tolerance_seconds": 5, "status_max_age_seconds": 1, "approval_max_age_seconds": 1}) == "field_unknown"


# ---- identity
def indep(pre):
    body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "sha256:" + hashlib.sha256(b"ocs-reg/r08-v5/effective-policy\n" + body).hexdigest()


def test_identity_preimage_and_independent_digest():
    pre = ident.effective_preimage(FAM, {"clock_tolerance_seconds": 5})
    assert pre == {"effective_policy_profile": "ocs-effective-policy/1", "contract_version": "r08-v5", "family": FAM, "family_version": "v5",
                   "deny_all": [], "effective": {"clock_tolerance_seconds": 5}}
    d = ident.effective_policy_digest(FAM, {"clock_tolerance_seconds": 5})
    assert d == indep(pre) == "sha256:b34f64a3db85f0344681ea4764b72d5c34054aed57106ab678ad77b8af3ac0d6"
    assert d != ident.effective_policy_digest(FAM, {"clock_tolerance_seconds": 6})
    for dom in (b"ocs-reg/r08-v2/effective-policy\n", b"ocs-reg/r08-v4/effective-policy\n"):
        body = json.dumps(pre, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        assert "sha256:" + hashlib.sha256(dom + body).hexdigest() != d


@pytest.mark.parametrize("pl,code,member", [({}, "field_missing", "clock_tolerance_seconds"), ({"clock_tolerance_seconds": 1, "z": 1}, "field_unknown", "z"),
                                            ({"clock_tolerance_seconds": 5.0}, "field_type_invalid", "clock_tolerance_seconds"),
                                            ({"clock_tolerance_seconds": True}, "field_type_invalid", "clock_tolerance_seconds"),
                                            ({"clock_tolerance_seconds": -1}, "field_invalid", "clock_tolerance_seconds"),
                                            ({"clock_tolerance_seconds": 10 ** 20}, "field_invalid", "clock_tolerance_seconds")])
def test_identity_refusals(pl, code, member):
    with pytest.raises(ident.IdentityRefusal) as e:
        ident.effective_policy_digest(FAM, pl)
    assert (e.value.code, e.value.member) == (code, member)


def test_identity_version_and_family_dispatch():
    for ver in ("r08-v4", "r08-v3", "r08-v2", "r08-v1"):
        with pytest.raises(ident.IdentityRefusal) as e:
            ident.effective_policy_digest(FAM, {"clock_tolerance_seconds": 5}, ver)
        assert e.value.code == "contract_unsupported"
    with pytest.raises(ident.IdentityRefusal) as e:
        ident.effective_policy_digest(f4.FAMILY_F4, {"status_max_age_seconds": 1, "approval_max_age_seconds": 1})
    assert e.value.code == "family_unsupported"
    with pytest.raises(v2pi.IdentityRefusal) as e:
        v2pi.effective_policy_digest(FAM, {"clock_tolerance_seconds": 5})
    assert e.value.code == "family_unsupported"


# ---- signed decision path
needs_sig = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")


@needs_sig
def test_signed_valid_selection_applies_and_never_widens():
    d = t.decide()
    assert d.kind == "applied" and d.effective == {"clock_tolerance_seconds": 5} and d.deny_all is False and d.operationally_authorized is False
    d = t.decide(rec=t.record(t.payload(clock_tolerance_seconds=50)), cl=t.caller(clock_tolerance_seconds=7))
    assert d.kind == "applied" and d.effective == {"clock_tolerance_seconds": 7} and d.detail == "registry_value_not_narrowing:clock_tolerance_seconds"
    d = t.decide(rec=t.record(t.payload(clock_tolerance_seconds=0)))
    assert d.kind == "applied" and d.effective == {"clock_tolerance_seconds": 0} and d.deny_all is False


@needs_sig
@pytest.mark.parametrize("bad", [5.0, True, "5", None, -1, MAXV + 1])
def test_signed_invalid_caller_refuses_required(bad):
    t.assert_refused(t.decide(cl=t.caller(clock_tolerance_seconds=bad)), "composition_caller_invalid")


@needs_sig
@pytest.mark.parametrize("mutate,vcode", [(lambda p: p.pop("clock_tolerance_seconds"), "field_missing"), (lambda p: p.update(x=1), "field_unknown"),
                                          (lambda p: p.update(clock_tolerance_seconds=5.0), "json_number_unsupported"),
                                          (lambda p: p.update(clock_tolerance_seconds=-1), "field_invalid")])
def test_signed_invalid_record_refuses(mutate, vcode):
    pl = t.payload()
    mutate(pl)
    rec = t.record(pl)
    assert v5_record.validate_record_text_v5(r.dumps(rec)).code == vcode
    t.assert_refused(t.decide(rec=rec, sel=t.selection_text(rec)), "composition_record_invalid")


@needs_sig
def test_signed_wrong_contract_family_signature_scope_revocation():
    rec = t.record()
    for contract in ("r08-v4", "r08-v3", "r08-v2", "r08-v1", "r08-v6", ""):
        t.assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, contract=contract)), "contract_unsupported")
    t.assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, domain=b"ocs-reg/r08-v4/selection\n")), "signature_invalid")
    t.assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, domain=s.V2_DOMAIN)), "signature_invalid")
    t.assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, sk=t.OTHER_SK)), "signature_invalid")
    for ctx, code in ((c.ExpectedContext("other-consumer", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch"),
                      (c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch"),
                      (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch")):
        t.assert_refused(t.decide(rec=rec, ctx=ctx), code)
    # an f4 (ages) record in a v5 envelope is another family
    ages = dict(rec, family=f4.FAMILY_F4, payload={"status_max_age_seconds": 1, "approval_max_age_seconds": 1})
    t.assert_refused(t.decide(rec=r.seal_record(ages), sel=r.dumps(t.envelope(r.make_statement_v2(r.seal_record(ages), family=f4.FAMILY_F4)))),
                     "family_unsupported")
    revoked = s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test", 1)})) if "revoked_selections" in s.trust.__code__.co_varnames else None
    if revoked is not None:
        d = t.decide(rec=rec, trust=revoked)
        assert d.kind == "required_policy_unavailable" and d.code == "selection_revoked"


@needs_sig
def test_v5_envelope_is_refused_by_other_entry_points_and_the_reverse():
    from registry_successor import v4_decision, decision
    rec = t.record()
    ad = t.ev.Ed25519Verifier()
    d = v4_decision.verify_and_decide_v4("required", {}, r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"
    d = decision.verify_and_decide_v2("required", {"status_max_age_seconds": 60, "approval_max_age_seconds": 60}, r.dumps(rec), t.selection_text(rec), s.CTX,
                                      s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"


def test_v5_statement_shape_and_vocabulary_are_the_v4_ones():
    from registry_successor import v4_selection, v4_verify, v5_verify
    assert v5_selection.STATEMENT_FIELDS_V5 == v4_selection.STATEMENT_FIELDS_V4 and v5_verify.LAYERS_V5 == v4_verify.LAYERS_V4
    assert v5_verify.CODES_V5 == v4_verify.CODES_V4
    import inspect
    a, b = inspect.getsource(v4_verify._verify_v4), inspect.getsource(v5_verify._verify_v5)
    norm = lambda x, n: x.replace("v" + n, "vN").replace("V" + n, "VN").replace("r08-v" + n, "r08-vN")
    assert norm(a, "4").replace("_verify_vN", "_verify") == norm(b, "5").replace("_verify_vN", "_verify")


# ---- pinned vectors
import base64
from pathlib import Path

_VEC = Path(__file__).parent / "vectors" / "r08v5"


@pytest.mark.parametrize("vec", json.loads((_VEC / "identity_vectors.json").read_text())["vectors"], ids=lambda v: v["id"])
def test_pinned_identity_vectors(vec):
    assert ident.effective_preimage(FAM, vec["effective"]) == vec["preimage"]
    assert ident.effective_policy_digest(FAM, vec["effective"]) == vec["digest"] == indep(vec["preimage"])


@needs_sig
def test_signed_vector_is_deterministic_and_verifies():
    vec = json.loads((_VEC / "signed_selection_vector.json").read_text())
    rec, stmt = vec["record"], vec["statement"]
    assert rec == t.record() and stmt == t.statement(t.record())
    assert v5_selection.signing_input_v5(stmt).hex() == vec["signing_input_hex"]
    assert t.sign(stmt) == vec["signature"] == base64.b64encode(bytes.fromhex(vec["signature_hex"])).decode()
    d = t.decide(rec=rec, sel=json.dumps(vec["envelope"]))
    assert d.kind == "applied" and d.effective == {"clock_tolerance_seconds": 5}
