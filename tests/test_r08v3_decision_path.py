"""M2 PR-1: the public `r08-v3` decision path with real synthetic Ed25519 signatures (BUILDER_TESTED; not independently qualified).

Where PyNaCl is absent the module is NOT RUN (skipped with a reason), never passed with a double.
"""
import base64
import copy
import datetime
import hashlib
import json

import pytest

import r08_support as r
import r08v3_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import decision
from registry_successor import record as record_mod
from registry_successor import v2_f1ab
from registry_successor import v3_record
from registry_successor import v3_selection
from registry_successor import v3_verify
from registry_successor import verify as v

pytestmark = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

rec_, sel_, decide, assert_refused = t.record, t.selection_text, t.decide, t.assert_refused
A_MAX, E_MAX = 2 ** 53, 2 ** 53 - 1


# ---- positive
def test_valid_selection_applies_exact_seven_member_effective_policy():
    d = decide()
    assert d.kind == "applied" and d.code is None and d.deny_all is False and d.operationally_authorized is False
    assert d.effective == {"allowed_actions": ("act-copy", "act-list"), "allowed_adapters": ("a-local",), "allowed_units": ("u-read",),
                           "allowed_institutions": ("inst-a",), "allowed_authority_domains": ("domain-a",), "max_amount": 100, "max_effects": 3}


def test_registry_never_widens_the_caller_through_the_signed_path():
    wide = t.payload(allowed_units=["u-read", "u-write", "u-x"], allowed_actions=["act-copy", "act-list", "act-other", "act-z"],
                     max_amount=A_MAX, max_effects=E_MAX)
    cl = t.caller(allowed_units=["u-read"], max_amount=7, max_effects=2)
    d = decide(rec=rec_(wide), cl=cl)
    assert d.kind == "applied"
    assert d.effective["allowed_units"] == ("u-read",) and d.effective["max_amount"] == 7 and d.effective["max_effects"] == 2
    assert d.detail == "registry_value_not_narrowing:max_amount,max_effects"
    for k in t.SETS:
        assert set(d.effective[k]) <= set(cl[k]) and set(d.effective[k]) <= set(wide[k])


@pytest.mark.parametrize("amount,effects", [(0, 1), (1, 1), (A_MAX, E_MAX), (A_MAX - 1, E_MAX - 1)])
def test_boundary_ceilings_apply(amount, effects):
    d = decide(rec=rec_(t.payload(max_amount=amount, max_effects=effects)), cl=t.caller(max_amount=A_MAX, max_effects=E_MAX))
    assert d.kind == "applied" and d.effective["max_amount"] == amount and d.effective["max_effects"] == effects


def test_zero_amount_applies_zero_effects_is_deny_all():
    d = decide(rec=rec_(t.payload(max_amount=0)))
    assert d.kind == "applied" and d.deny_all is False and d.effective["max_amount"] == 0
    z = decide(rec=rec_(t.payload(max_effects=0)))
    assert z.kind == "applied_deny_all" and z.deny_all is True and z.deny_all_fields == ("max_effects",)
    assert z.effective["max_effects"] == 0 and z.operationally_authorized is False and z.caller_unchanged is False


def test_empty_record_set_is_deny_all_and_is_never_the_caller_policy():
    d = decide(rec=rec_(t.payload(allowed_units=[])))
    assert d.kind == "applied_deny_all" and d.deny_all_fields == ("allowed_units",) and d.effective["allowed_units"] == ()


# ---- invalid callers (every float form) at the decision level
@pytest.mark.parametrize("bad", [5.0, 99.5, -0.0, 1e300, True, "5", None, -1, A_MAX + 1])
def test_invalid_caller_max_amount_refuses_required(bad):
    assert_refused(decide(cl=t.caller(max_amount=bad)), "composition_caller_invalid")


@pytest.mark.parametrize("bad", [0, -1, True, 1.0, "1", None])
def test_invalid_caller_max_effects_refuses_required(bad):
    assert_refused(decide(cl=t.caller(max_effects=bad)), "composition_caller_invalid")


def test_optional_participation_refusal_leaves_the_caller_policy_unchanged_not_an_application():
    sel = r.dumps(t.envelope(t.statement(rec_(), participation="optional")))
    d = decide(participation="optional", sel=sel, cl=t.caller(max_amount=5.0))
    assert d.kind == "overlay_not_applied" and d.code == "composition_caller_invalid" and d.caller_unchanged is True
    assert d.operationally_authorized is False and d.deny_all is False
    d2 = decide(participation="optional", sel=sel, cl=t.caller(allowed_units=["u-read"]), rec=rec_(t.payload()))
    assert d2.kind == "applied"
    bad_sig = r.dumps(t.envelope(t.statement(rec_(), participation="optional"), sk=t.OTHER_SK))
    d3 = decide(participation="optional", sel=bad_sig, cl=t.caller(allowed_units=["u-read", "u-write"]))
    assert d3.kind == "overlay_not_applied" and d3.code == "signature_invalid"
    assert d3.effective["allowed_units"] == ("u-read", "u-write") and d3.effective["max_amount"] == 500


# ---- malformed records: validator code and decision code
@pytest.mark.parametrize("mutate,code", [
    (lambda p: p.pop("max_amount"), "field_missing"), (lambda p: p.pop("max_effects"), "field_missing"),
    (lambda p: p.pop("allowed_institutions"), "field_missing"), (lambda p: p.update(max_age=1), "field_unknown"),
    (lambda p: p.update(max_effects=True), "field_type_invalid"),
    (lambda p: p.update(max_amount="5"), "field_type_invalid"), (lambda p: p.update(max_effects=None), "field_type_invalid"),
    (lambda p: p.update(max_amount=-1), "field_invalid"), (lambda p: p.update(max_amount=A_MAX + 1), "field_invalid"),
    (lambda p: p.update(max_effects=-1), "field_invalid"), (lambda p: p.update(max_effects=E_MAX + 1), "field_invalid"),
    (lambda p: p.update(max_effects=2 ** 63), "field_invalid"), (lambda p: p.update(allowed_units=["u-write", "u-read"]), "field_invalid"),
    (lambda p: p.update(allowed_units="u-read"), "field_type_invalid"),
])
def test_malformed_payload_typed_validator_code_and_decision_refusal(mutate, code):
    pl = t.payload()
    mutate(pl)
    rec = rec_(pl)
    assert v3_record.validate_record_text_v3(r.dumps(rec)).code == code
    assert_refused(decide(rec=rec, sel=sel_(rec)), "composition_record_invalid")


@pytest.mark.parametrize("literal,code", [("5.0", "json_number_unsupported"), ("1e3", "json_number_unsupported"), ("1E+2", "json_number_unsupported"),
                                          ("NaN", "json_number_unsupported"), ("Infinity", "json_number_unsupported"),
                                          ("-Infinity", "json_number_unsupported"), ("0.0", "json_number_unsupported")])
def test_float_and_non_finite_literals_never_reach_validation(literal, code):
    text = r.dumps(rec_()).replace('"max_amount": 100', '"max_amount": %s' % literal)
    assert text != r.dumps(rec_())
    assert v3_record.validate_record_text_v3(text).code == code
    assert_refused(decide(record_text=text), "composition_record_invalid")


def test_duplicate_key_and_non_json_records_refuse():
    text = r.dumps(rec_()).replace('"max_amount": 100', '"max_amount": 100, "max_amount": 1')
    assert v3_record.validate_record_text_v3(text).code == "json_duplicate_key"
    assert v3_record.validate_record_text_v3("not json").code == "json_malformed"
    assert v3_record.validate_record_text_v3(None).code == "input_not_text"
    assert_refused(decide(record_text="not json"), "composition_record_invalid")


def test_record_top_level_checks():
    assert v3_record.validate_record_text_v3(r.dumps(rec_())).ok
    assert v3_record.validate_record_text_v3(r.dumps(rec_(kind="selection"))).code == "kind_unsupported"
    assert v3_record.validate_record_text_v3(r.dumps(rec_(non_authorizing=False))).code == "field_invalid"
    assert v3_record.validate_record_text_v3(r.dumps(rec_(record_version=0))).code == "field_invalid"


# ---- cross-family and cross-version substitution
def test_other_families_are_unsupported_in_the_v3_table():
    for fam_id in (v2_f1ab.FAMILY_F1AB, c.FAMILY_F1A, "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "unknown-family"):
        rec = rec_(family=fam_id)
        assert v3_record.validate_record_text_v3(r.dumps(rec)).code == "family_unsupported"
        stmt = r.make_statement_v2(rec, family=fam_id)
        text = r.dumps(s.envelope(stmt, domain=t.V3_DOMAIN, contract="r08-v3", signature=t.sign(stmt), pub=t.PK))
        assert v3_selection.parse_selection_envelope_v3(text).code == "family_unsupported"
        assert_refused(decide(rec=rec, sel=text), "family_unsupported")


def test_selection_and_record_family_must_agree():
    rec_ab = rec_(family=v2_f1ab.FAMILY_F1AB, payload={k: t.payload()[k] for k in t.SETS})
    assert_refused(decide(rec=rec_ab, sel=sel_(rec_())), "composition_record_invalid")


def test_f1abc_record_and_selection_are_refused_by_the_v1_and_v2_entry_points():
    rec = rec_()
    assert decision.validate_record_text_v2(r.dumps(rec)).code == "contract_unsupported"
    assert record_mod.validate_record_text(r.dumps(rec)).code == "contract_unsupported"
    sel = sel_(rec)
    from registry_successor import selection as s1
    from registry_successor.v2_selection import parse_selection_envelope_v2
    assert parse_selection_envelope_v2(sel).code == "contract_unsupported"
    assert s1.parse_selection_envelope(sel).code == "contract_unsupported"
    ad = t.ev.Ed25519Verifier()
    d2 = decision.verify_and_decide_v2("required", v2_caller(), r.dumps(rec), sel, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d2.kind == "required_policy_unavailable" and d2.effective is None
    d1 = decision.verify_and_decide("required", v2_caller(), r.dumps(rec), sel, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d1.kind == "required_policy_unavailable" and d1.effective is None


def v2_caller():
    return {k: t.caller()[k] for k in t.SETS}


def test_v2_and_v1_records_and_selections_are_refused_by_the_v3_entry_point():
    v2rec = r.make_record_v2(family=v2_f1ab.FAMILY_F1AB, payload={k: t.payload()[k] for k in t.SETS})
    assert v3_record.validate_record_text_v3(r.dumps(v2rec)).code == "contract_unsupported"
    assert v3_record.validate_record_text_v3(r.dumps(r.make_record())).code == "contract_unsupported"
    stmt = r.make_statement_v2(v2rec, family=v2_f1ab.FAMILY_F1AB)
    v2env = r.dumps(s.envelope(stmt, domain=s.V2_DOMAIN, contract="r08-v2", signature=t.sign(stmt, domain=s.V2_DOMAIN), pub=t.PK))
    assert v3_selection.parse_selection_envelope_v3(v2env).code == "contract_unsupported"
    assert_refused(decide(rec=v2rec, sel=v2env), "contract_unsupported")
    v1env = r.dumps(s.v1_envelope())
    assert v3_selection.parse_selection_envelope_v3(v1env).code == "contract_unsupported"


def test_label_swap_a_v2_signed_statement_relabelled_r08_v3_fails_signature():
    rec = rec_()
    stmt = t.statement(rec)
    for domain in (s.V2_DOMAIN, s.V1_DOMAIN, b"", b"ocs-reg/r08-v3/other\n"):
        sel = r.dumps(s.envelope(stmt, domain=domain, contract="r08-v3", signature=t.sign(stmt, domain=domain), pub=t.PK))
        assert_refused(decide(rec=rec, sel=sel), "signature_invalid")


def test_v3_signed_statement_relabelled_r08_v2_is_refused_by_the_v2_verifier():
    rec = rec_()
    stmt = t.statement(rec)
    env = t.envelope(stmt, contract="r08-v2")
    parsed = type("P", (), {"ok": True, "code": None, "envelope": env, "statement": stmt, "statement_digest": c.digest(stmt), "signatures": env["signatures"]})()
    rep = v.verify_selection_v2(parsed, s.CTX, s.trust(pub=t.PK), t.ev.Ed25519Verifier(), r.NOW, None, t.ev.Ed25519Verifier().key_admission)
    assert rep.ok is False and rep.layers["structural"] == "refuse"  # family f1abc is not in the frozen v2 table
    # and with a v2-table family the v3 domain signature does not verify under v2
    v2stmt = r.make_statement_v2(r.make_record_v2(), family=c.FAMILY_F1A)
    parsed2 = type("P", (), {"ok": True, "code": None, "envelope": s.envelope(v2stmt), "statement": v2stmt, "statement_digest": c.digest(v2stmt),
                             "signatures": [{"alg": "ed25519", "key_id": s.KEY_ID, "signature": t.sign(v2stmt, domain=t.V3_DOMAIN)}]})()
    rep2 = v.verify_selection_v2(parsed2, s.CTX, s.trust(pub=t.PK), t.ev.Ed25519Verifier(), r.NOW, None, t.ev.Ed25519Verifier().key_admission)
    assert rep2.ok is False and rep2.code == "signature_invalid"


def test_the_v3_verifier_takes_no_contract_version_and_rejects_a_foreign_envelope_object():
    import inspect
    assert "contract_version" not in inspect.signature(v3_verify.verify_selection_v3).parameters
    foreign = type("P", (), {"ok": True, "code": None, "envelope": {"contract_version": "r08-v2"}, "statement": t.statement(rec_()),
                             "statement_digest": c.digest(t.statement(rec_())), "signatures": []})()
    rep = v3_verify.verify_selection_v3(foreign, s.CTX, s.trust(pub=t.PK), t.ev.Ed25519Verifier(), r.NOW, None)
    assert rep.ok is False and rep.code == "contract_unsupported"


# ---- wrong tenant / scope / consumer / operation
@pytest.mark.parametrize("ctx,code", [
    (c.ExpectedContext("other-consumer", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch"),
    (None, "selection_scope_mismatch"),
])
def test_wrong_tenant_scope_consumer_operation_refuse(ctx, code):
    d = decide(ctx=ctx) if ctx is not None else _decide_no_ctx()
    assert_refused(d, code)


def _decide_no_ctx():
    from registry_successor.v3_decision import verify_and_decide_v3
    ad = t.ev.Ed25519Verifier()
    rec = rec_()
    return verify_and_decide_v3("required", t.caller(), r.dumps(rec), sel_(rec), None, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)


def test_signer_without_exact_authority_is_not_authorized():
    other = v.AuthorityGrant("consumer-test", "tenant-other", "inst-a", "domain-a", "op-test")
    tr = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (other,)),))
    assert_refused(decide(trust=tr), "issuer_not_authorized")


# ---- signature
def test_forged_wrong_key_missing_and_noncanonical_signatures_refuse():
    rec = rec_()
    stmt = t.statement(rec)
    bad = bytearray(base64.b64decode(t.sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, domain=t.V3_DOMAIN, contract="r08-v3", signature=base64.b64encode(bytes(bad)).decode(), pub=t.PK))
    assert_refused(decide(rec=rec, sel=forged), "signature_invalid")
    assert_refused(decide(rec=rec, sel=sel_(rec, sk=t.OTHER_SK)), "signature_invalid")
    unsigned = r.dumps(s.envelope(stmt, domain=t.V3_DOMAIN, contract="r08-v3", signed=False))
    assert_refused(decide(rec=rec, sel=unsigned), "signature_missing")
    good = t.sign(stmt)
    for noncanon in (good + "\n", good.replace("=", "") if "=" in good else good + "=", good[:-4]):
        sel = r.dumps(s.envelope(stmt, domain=t.V3_DOMAIN, contract="r08-v3", signature=noncanon, pub=t.PK))
        d = decide(rec=rec, sel=sel)
        assert d.kind == "required_policy_unavailable" and d.effective is None


def test_signature_by_a_different_trusted_key_id_or_untrusted_issuer():
    rec = rec_()
    stmt = t.statement(rec)
    sel = r.dumps(s.envelope(stmt, domain=t.V3_DOMAIN, contract="r08-v3", key_id="key-unknown", signature=t.sign(stmt), pub=t.PK))
    assert_refused(decide(rec=rec, sel=sel), "issuer_untrusted")


# ---- incorrect digests and pins
def test_altered_record_statement_and_pins_refuse():
    rec = rec_()
    sel = sel_(rec)
    tampered = copy.deepcopy(rec)
    tampered["payload"]["max_amount"] = A_MAX  # widen the ceiling without resealing
    assert v3_record.validate_record_text_v3(r.dumps(tampered)).code == "digest_mismatch"
    assert_refused(decide(rec=tampered, sel=sel), "composition_record_invalid")
    resealed = r.seal_record(tampered)  # widen and reseal: not the record the signed selection pins
    assert_refused(decide(rec=resealed, sel=sel), "record_digest_mismatch")
    stmt = t.statement(rec)
    env = t.envelope(stmt)
    env["statement_digest"] = "sha256:" + "0" * 64
    assert_refused(decide(rec=rec, sel=r.dumps(env)), "digest_mismatch")
    other = rec_(record_version=2)
    assert_refused(decide(rec=other, sel=sel), "record_identity_mismatch")
    assert_refused(decide(rec=rec_(record_id="f1abc-other-record"), sel=sel), "record_identity_mismatch")


def test_evaluator_mismatch_between_selection_and_record():
    rec = rec_()
    stmt = t.statement(rec)
    stmt["evaluator"] = dict(stmt["evaluator"], source_blob_id="1" * 40)
    sel = r.dumps(t.envelope(stmt))
    assert_refused(decide(rec=rec, sel=sel), "evaluator_mismatch")


def test_no_selection_or_record_refuses():
    assert_refused(decide(sel=None) if False else _decide_with(None, r.dumps(rec_())), "selection_missing")
    d = _decide_with(sel_(rec_()), None)
    assert d.kind == "required_policy_unavailable" and d.effective is None


def _decide_with(sel, rec_text):
    from registry_successor.v3_decision import verify_and_decide_v3
    ad = t.ev.Ed25519Verifier()
    return verify_and_decide_v3("required", t.caller(), rec_text, sel, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)


# ---- lifecycle: withdrawn, revoked, stale, expired
def test_withdrawn_selection_refuses():
    rec = rec_()
    wd = s.withdraw_statement(t.statement(rec))
    sel = r.dumps(t.envelope(wd))
    assert_refused(decide(rec=rec, sel=sel), "selection_withdrawn")
    unsigned_wd = r.dumps(s.envelope(wd, domain=t.V3_DOMAIN, contract="r08-v3", signed=False))
    assert_refused(decide(rec=rec, sel=unsigned_wd), "signature_missing")  # an unauthenticated withdrawal is not honoured as one


def test_revoked_stale_and_expired_refuse():
    rec = rec_()
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 2),))), "selection_epoch_stale")
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    late = r.NOW + datetime.timedelta(days=3)
    assert_refused(decide(rec=rec, now=late, trust=s.trust(pub=t.PK, valid_until="2026-12-31T00:00:00Z")), "selection_expired")
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, valid_until="2026-10-25T06:00:00Z")), "trust_snapshot_expired")
    early = r.NOW - datetime.timedelta(days=3)
    assert_refused(decide(rec=rec, now=early), "selection_not_yet_effective")
    assert_refused(decide(rec=rec, now=None) if False else _decide_now(None), "time_unavailable")
    assert_refused(decide(participation="optional", rec=rec).__class__ and decide(participation="required", sel=sel_(rec, participation="optional")),
                   "participation_mismatch")


def _decide_now(now):
    from registry_successor.v3_decision import verify_and_decide_v3
    ad = t.ev.Ed25519Verifier()
    rec = rec_()
    return verify_and_decide_v3("required", t.caller(), r.dumps(rec), sel_(rec), s.CTX, s.trust(pub=t.PK), ad, now, ad.key_admission)


def test_trust_snapshot_missing_unverifier_and_bad_key():
    from registry_successor.v3_decision import verify_and_decide_v3
    rec = rec_()
    ad = t.ev.Ed25519Verifier()
    args = ("required", t.caller(), r.dumps(rec), sel_(rec), s.CTX)
    assert_refused(verify_and_decide_v3(*args, None, ad, r.NOW), "trust_snapshot_missing")
    assert_refused(verify_and_decide_v3(*args, s.trust(pub=t.PK), None, r.NOW), "verifier_unavailable")
    small_order = bytes.fromhex("01" + "00" * 31)
    assert_refused(verify_and_decide_v3(*args, s.trust(pub=small_order), ad, r.NOW), "trust_snapshot_invalid")


def test_bad_participation_value_refuses():
    for bad in ("sometimes", None, 1, b"required"):
        d = decide(participation=bad)
        assert d.kind == "required_policy_unavailable" and d.code == "participation_mismatch" and d.effective is None


# ---- operationally_authorized is always False
def test_operationally_authorized_is_false_on_every_outcome():
    outcomes = [decide(), decide(rec=rec_(t.payload(max_effects=0))), decide(cl=t.caller(max_amount=1.5)), decide(sel="{}"),
                decide(participation="optional", sel="{}")]
    assert all(o.operationally_authorized is False for o in outcomes)
    assert all(o.effective is None for o in outcomes if o.kind == "required_policy_unavailable")


# ---- canonical serialization pins
def test_record_digest_and_signing_input_are_the_canonical_forms():
    rec = rec_()
    body = {k: v_ for k, v_ in rec.items() if k != "record_digest"}
    indep = "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert rec["record_digest"] == indep
    stmt = t.statement(rec)
    assert v3_selection.signing_input_v3(stmt) == b"ocs-reg/r08-v3/selection\n" + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert v3_selection.SIGNING_DOMAIN_V3 != s.V2_DOMAIN != s.V1_DOMAIN
    reordered = json.dumps(dict(reversed(list(rec.items()))), indent=3)
    assert v3_record.validate_record_text_v3(reordered).ok  # member order and whitespace are not significant; the digest is over canonical bytes


def test_signed_vector_is_deterministic_and_verifies():
    vec = json.loads(open(__import__("os").path.join(__import__("os").path.dirname(__file__), "vectors", "r08v3", "signed_selection_vector.json")).read())
    rec, stmt = vec["record"], vec["statement"]
    assert rec == t.record() and stmt == t.statement(t.record())
    assert v3_selection.signing_input_v3(stmt).hex() == vec["signing_input_hex"]
    assert t.sign(stmt) == vec["signature"] == base64.b64encode(bytes.fromhex(vec["signature_hex"])).decode()
    assert t.nb.crypto_sign_open(bytes.fromhex(vec["signature_hex"]) + bytes.fromhex(vec["signing_input_hex"]), t.PK) == bytes.fromhex(vec["signing_input_hex"])
    d = decide(rec=rec, sel=json.dumps(vec["envelope"]))
    assert d.kind == "applied" and d.effective["max_amount"] == 100
