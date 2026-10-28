"""M3 PR-1: target narrowing through the signed `r08-v4` path, cross-version and cross-family refusal, and v3/v4 verification parity
(BUILDER_TESTED; not independently qualified)."""
import pytest

import r08_support as r
import r08v3_support as t3
import r08v4_support as t
import s01_support as s
from registry_successor import v3_decision, v3_selection, v3_verify, v4_decision, v4_selection, v4_verify
from registry_successor import verify as v

pytestmark = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

decide = t.decide
rec_ = t.record


def test_registry_narrower_than_caller_signed():
    d = decide(rec=rec_(t.payload(allowed_target_prefixes=["rec/in/"])), cl=t.caller(allowed_target_prefixes=["rec/"]))
    assert d.kind == "applied" and d.effective["allowed_target_prefixes"] == ("rec/in/",) and d.effective["target_match"] == "segment"


def test_caller_narrower_than_registry_signed():
    d = decide(rec=rec_(t.payload(allowed_target_prefixes=["rec/"])), cl=t.caller(allowed_target_prefixes=["rec/in/x"]))
    assert d.kind == "applied" and d.effective["allowed_target_prefixes"] == ("rec/in/x",)


def test_non_comparable_targets_are_deny_all_not_the_caller_policy():
    d = decide(rec=rec_(t.payload(allowed_target_prefixes=["rec/in/"])), cl=t.caller(allowed_target_prefixes=["other/"]))
    assert d.kind == "applied_deny_all" and d.deny_all and d.deny_all_fields == ("allowed_target_prefixes",)
    assert d.effective["allowed_target_prefixes"] == () and d.operationally_authorized is False and d.caller_unchanged is False


def test_registry_empty_targets_is_explicit_deny_all():
    d = decide(rec=rec_(t.payload(allowed_target_prefixes=[])))
    assert d.kind == "applied_deny_all" and d.deny_all_fields == ("allowed_target_prefixes",)


@pytest.mark.parametrize("reg,cal,mode", [("exact", "legacy-prefix", "exact"), ("legacy-prefix", "exact", "exact"), ("segment", "exact", "exact"),
                                          ("legacy-prefix", "segment", "segment"), ("exact", "exact", "exact")])
def test_effective_mode_is_never_weaker_than_either(reg, cal, mode):
    d = decide(rec=rec_(t.payload(target_match=reg, allowed_target_prefixes=["rec/in/"])), cl=t.caller(target_match=cal, allowed_target_prefixes=["rec/in/"]))
    assert d.kind == "applied" and d.effective["target_match"] == mode


@pytest.mark.parametrize("bad", [{"allowed_target_prefixes": []}, {"allowed_target_prefixes": ["a b"]}, {"target_match": "x"}, {"target_match": None}])
def test_malformed_caller_target_members_refuse_required(bad):
    t_ = t
    d = decide(cl=t_.caller(**bad))
    assert d.kind == "required_policy_unavailable" and d.code == "composition_caller_invalid" and d.effective is None


def test_caller_with_only_the_seven_f1abc_members_refuses_no_default():
    seven = {k: v for k, v in t.caller().items() if k not in ("allowed_target_prefixes", "target_match")}
    d = decide(cl=seven)
    assert d.kind == "required_policy_unavailable" and d.code == "composition_caller_invalid"


@pytest.mark.parametrize("mutate", [lambda p: p.update(target_match="prefix"), lambda p: p.update(allowed_target_prefixes=["b", "a"]),
                                    lambda p: p.pop("target_match"), lambda p: p.pop("allowed_target_prefixes")])
def test_malformed_registry_target_members_refuse(mutate):
    pl = t.payload()
    mutate(pl)
    rec = rec_(pl)
    d = decide(rec=rec)
    assert d.kind == "required_policy_unavailable" and d.code == "composition_record_invalid"


# ---- cross-version and cross-family
def test_v4_selection_and_record_are_refused_by_v3_and_the_reverse():
    rec4 = rec_()
    sel4 = t.selection_text(rec4)
    ad = t.ev.Ed25519Verifier()
    d = v3_decision.verify_and_decide_v3("required", t3.caller(), r.dumps(rec4), sel4, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"
    rec3 = t3.record()
    d = v4_decision.verify_and_decide_v4("required", t.caller(), r.dumps(rec3), t3.selection_text(rec3), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"


@pytest.mark.parametrize("contract", ["r08-v3", "r08-v2", "r08-v1", "r08-v5", "R08-V4", ""])
def test_wrong_contract_envelope_refuses(contract):
    rec = rec_()
    d = decide(rec=rec, sel=t.selection_text(rec, contract=contract))
    assert d.kind == "required_policy_unavailable" and d.code == "contract_unsupported"


@pytest.mark.parametrize("domain", [b"ocs-reg/r08-v3/selection\n", s.V2_DOMAIN, s.V1_DOMAIN])
def test_signature_over_another_version_domain_never_verifies(domain):
    rec = rec_()
    d = decide(rec=rec, sel=t.selection_text(rec, domain=domain))
    assert d.kind == "required_policy_unavailable" and d.code == "signature_invalid"


def test_v3_family_record_inside_a_v4_envelope_is_refused():
    rec = rec_(family="f1abc-local-execution-limits")
    sel = r.dumps(t.envelope(r.make_statement_v2(rec, family="f1abc-local-execution-limits")))
    d = decide(rec=rec, sel=sel)
    assert d.kind == "required_policy_unavailable" and d.code in ("family_unsupported", "composition_family_unsupported")


def test_digest_mismatch_and_wrong_pinned_record():
    a, b = rec_(), rec_(t.payload(allowed_target_prefixes=["rec/in/", "rec/out", "rec/zzz"]), record_id="f1abcd-other")
    d = decide(rec=b, sel=t.selection_text(a))
    assert d.kind == "required_policy_unavailable" and d.code in ("record_identity_mismatch", "record_digest_mismatch", "digest_mismatch")


# ---- parity: the v4 orchestration is the v3 orchestration with only the version, table and domain changed
def _norm(src, tag):
    return src.replace("v" + tag, "vN").replace("V" + tag, "VN").replace("r08-v" + tag, "r08-vN").replace("f1abcd", "f1abc")


def test_v4_verify_orchestration_is_the_v3_orchestration_modulo_version_names():
    import inspect
    a = inspect.getsource(v3_verify._verify_v3)
    b = inspect.getsource(v4_verify._verify_v4)
    assert _norm(a, "3").replace("_verify_vN", "_verify") == _norm(b, "4").replace("_verify_vN", "_verify")
    a = inspect.getsource(v3_verify._authenticity_v3)
    b = inspect.getsource(v4_verify._authenticity_v4)
    assert _norm(a, "3") .replace("_authenticity_vN", "_a") == _norm(b, "4").replace("_authenticity_vN", "_a")


def test_v4_selection_statement_shape_is_the_v3_shape():
    assert v4_selection.STATEMENT_FIELDS_V4 == v3_selection.STATEMENT_FIELDS_V3
    assert v4_verify.LAYERS_V4 == v3_verify.LAYERS_V3 == v.LAYERS_V2
    assert v4_verify.CODES_V4 == v3_verify.CODES_V3
