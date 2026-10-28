"""The public `r08-v5` decision path with real synthetic Ed25519 signatures (BUILDER_TESTED; not independently qualified).

Where PyNaCl is absent the module is NOT RUN (skipped with a reason), never passed with a double. The Registry CI installs the hash-locked backend.
"""
import base64
import copy
import datetime
import hashlib
import json
import os

import pytest

import r08_support as r
import r08v5_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import v5_record
from registry_successor import v5_selection
from registry_successor import v5_verify

pytestmark = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

rec_, sel_, decide, assert_refused = t.record, t.selection_text, t.decide, t.assert_refused
FIELD = t.FIELD
R, B = "refuse", "bounded_tolerance"


def cmap(**kw):
    return {FIELD: {k.replace("_", "-"): v for k, v in kw.items()}}


# ---- positive: narrowing, equality, attempted widening
def test_valid_selection_narrows_bounded_tolerance_to_refuse_and_keeps_unlisted_classes():
    d = decide()
    assert d.kind == "applied" and d.code is None and d.deny_all is False and d.operationally_authorized is False and d.caller_unchanged is False
    assert d.effective == {FIELD: {"class-a": R, "class-b": R, "class-c": R}}
    assert d.detail == ""


def test_refuse_stays_refuse():
    d = decide(cl=cmap(class_a=R, class_b=R))
    assert d.kind == "applied" and d.effective == cmap(class_a=R, class_b=R) and d.detail == ""


def test_registry_bounded_tolerance_never_widens_a_refuse_host_value_through_the_signed_path():
    d = decide(rec=rec_(cmap(class_a=B, class_b=B)), cl=cmap(class_a=R, class_b=R))
    assert d.kind == "applied" and d.effective == cmap(class_a=R, class_b=R)
    assert d.detail == "registry_value_not_narrowing:class-a,class-b"
    d2 = decide(rec=rec_(cmap(class_a=B, class_b=R)), cl=cmap(class_a=R, class_b=B))
    assert d2.effective == cmap(class_a=R, class_b=R) and d2.detail == "registry_value_not_narrowing:class-a"


def test_registry_equal_to_host_is_applied_without_a_not_narrowing_report():
    d = decide(rec=rec_(cmap(class_a=B)), cl=cmap(class_a=B, class_b=B))
    assert d.kind == "applied" and d.effective == cmap(class_a=B, class_b=B) and d.detail == ""


def test_the_effective_policy_is_never_looser_than_the_caller_for_any_signed_combination():
    for h in (R, B):
        for g in (R, B):
            d = decide(rec=rec_(cmap(class_a=g)), cl=cmap(class_a=h))
            assert d.kind == "applied"
            assert (d.effective[FIELD]["class-a"] == R) == (R in (h, g))


def test_unknown_registry_class_refuses_and_is_never_created():
    d = decide(rec=rec_(cmap(class_a=R, class_zz=R)), cl=cmap(class_a=B))
    assert_refused(d, "composition_record_invalid")


@pytest.mark.parametrize("bad", [{}, 5, {FIELD: {}}, {FIELD: {"class-a": "x"}}, {FIELD: {"class-a": 1}}, {FIELD: {"class-a": None}},
                                 {FIELD: {"class a": B}}, {FIELD: {"class-a": B}, "x": 1}, "x"])
def test_invalid_caller_refuses_required(bad):
    assert_refused(decide(cl=bad), "composition_caller_invalid")


def test_optional_participation_refusal_leaves_the_caller_policy_unchanged_not_an_application():
    sel = r.dumps(t.envelope(t.statement(rec_(), participation="optional")))
    d = decide(participation="optional", sel=sel, cl=cmap(class_a="x"))
    assert d.kind == "overlay_not_applied" and d.code == "composition_caller_invalid" and d.caller_unchanged is True
    assert d.operationally_authorized is False and d.deny_all is False
    bad_sig = r.dumps(t.envelope(t.statement(rec_(), participation="optional"), sk=t.OTHER_SK))
    d3 = decide(participation="optional", sel=bad_sig, cl=cmap(class_a=B, class_b=B))
    assert d3.kind == "overlay_not_applied" and d3.code == "signature_invalid" and d3.caller_unchanged is True
    assert d3.effective == cmap(class_a=B, class_b=B)  # unchanged caller, NOT a Registry narrowing and NOT a denial
    d4 = decide(participation="optional", sel=sel, cl=cmap(class_a=B, class_b=B))
    assert d4.kind == "applied" and d4.effective == cmap(class_a=R, class_b=R)


# ---- malformed records: validator code and decision refusal
@pytest.mark.parametrize("pl,code", [
    ({}, "field_missing"), ({FIELD: {"class-a": R}, "x": 1}, "field_unknown"), ({"other": {"class-a": R}}, "field_unknown"),
    ({FIELD: {"class-a": 1}}, "field_type_invalid"), ({FIELD: {"class-a": None}}, "field_type_invalid"), ({FIELD: {"class-a": True}}, "field_type_invalid"),
    ({FIELD: "refuse"}, "field_type_invalid"), ({FIELD: ["class-a"]}, "field_type_invalid"),
    ({FIELD: {"class-a": "tolerate"}}, "field_invalid"), ({FIELD: {"class-a": "Refuse"}}, "field_invalid"), ({FIELD: {}}, "field_invalid"),
    ({FIELD: {"*": R}}, "field_invalid"), ({FIELD: {"class a": R}}, "field_invalid"),
])
def test_malformed_payload_typed_validator_code_and_decision_refusal(pl, code):
    rec = rec_(pl)
    assert v5_record.validate_record_text_v5(r.dumps(rec)).code == code
    assert_refused(decide(rec=rec, sel=sel_(rec)), "composition_record_invalid")


@pytest.mark.parametrize("literal", ["5.0", "1e3", "NaN", "Infinity", "-Infinity", "0.0"])
def test_non_string_numeric_literals_never_reach_validation(literal):
    text = r.dumps(rec_()).replace('"class-a": "refuse"', '"class-a": %s' % literal)
    assert text != r.dumps(rec_())
    assert v5_record.validate_record_text_v5(text).code in ("json_number_unsupported", "field_type_invalid")
    assert_refused(decide(record_text=text), "composition_record_invalid")


def test_duplicate_key_and_non_json_records_refuse():
    text = r.dumps(rec_()).replace('"class-a": "refuse"', '"class-a": "bounded_tolerance", "class-a": "refuse"')
    assert v5_record.validate_record_text_v5(text).code == "json_duplicate_key"
    assert v5_record.validate_record_text_v5("not json").code == "json_malformed"
    assert v5_record.validate_record_text_v5(None).code == "input_not_text"
    assert_refused(decide(record_text=text), "composition_record_invalid")


def test_record_top_level_checks():
    assert v5_record.validate_record_text_v5(r.dumps(rec_())).ok
    assert v5_record.validate_record_text_v5(r.dumps(rec_(kind="selection"))).code == "kind_unsupported"
    assert v5_record.validate_record_text_v5(r.dumps(rec_(non_authorizing=False))).code == "field_invalid"
    assert v5_record.validate_record_text_v5(r.dumps(rec_(record_version=0))).code == "field_invalid"


# ---- families
def test_other_families_are_unsupported_in_the_v5_table():
    for fam_id in ("f1abcd-local-execution-limits", "f1abc-local-execution-limits", "f1ab-local-execution-allowlist", c.FAMILY_F1A,
                   "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "unknown-family"):
        rec = rec_(family=fam_id)
        assert v5_record.validate_record_text_v5(r.dumps(rec)).code == "family_unsupported"
        stmt = r.make_statement_v2(rec, family=fam_id)
        text = r.dumps(s.envelope(stmt, domain=t.V5_DOMAIN, contract="r08-v5", signature=t.sign(stmt), pub=t.PK))
        assert v5_selection.parse_selection_envelope_v5(text).code == "family_unsupported"
        assert_refused(decide(rec=rec, sel=text), "family_unsupported")


def test_selection_and_record_family_must_agree():
    other = rec_(family="f5-action-class-age-bounds", payload={"class_status_max_age_seconds": {"class-a": 30}})
    assert_refused(decide(rec=other, sel=sel_(rec_())), "composition_record_invalid")


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
    if ctx is not None:
        d = decide(ctx=ctx)
    else:
        from registry_successor.v5_decision import verify_and_decide_v5
        ad = t.ev.Ed25519Verifier()
        rec = rec_()
        d = verify_and_decide_v5("required", t.caller(), r.dumps(rec), sel_(rec), None, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert_refused(d, code)


def test_signer_without_exact_authority_is_not_authorized():
    other = v.AuthorityGrant("consumer-test", "tenant-other", "inst-a", "domain-a", "op-test")
    tr = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (other,)),))
    assert_refused(decide(trust=tr), "issuer_not_authorized")


from registry_successor import verify as v  # noqa: E402


# ---- signature
def test_forged_wrong_key_missing_and_noncanonical_signatures_refuse():
    rec = rec_()
    stmt = t.statement(rec)
    bad = bytearray(base64.b64decode(t.sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, domain=t.V5_DOMAIN, contract="r08-v5", signature=base64.b64encode(bytes(bad)).decode(), pub=t.PK))
    assert_refused(decide(rec=rec, sel=forged), "signature_invalid")
    assert_refused(decide(rec=rec, sel=sel_(rec, sk=t.OTHER_SK)), "signature_invalid")
    unsigned = r.dumps(s.envelope(stmt, domain=t.V5_DOMAIN, contract="r08-v5", signed=False))
    assert_refused(decide(rec=rec, sel=unsigned), "signature_missing")
    good = t.sign(stmt)
    for noncanon in (good + "\n", good.replace("=", "") if "=" in good else good + "=", good[:-4]):
        sel = r.dumps(s.envelope(stmt, domain=t.V5_DOMAIN, contract="r08-v5", signature=noncanon, pub=t.PK))
        d = decide(rec=rec, sel=sel)
        assert d.kind == "required_policy_unavailable" and d.effective is None


def test_signature_by_an_unknown_key_id_is_untrusted():
    rec = rec_()
    stmt = t.statement(rec)
    sel = r.dumps(s.envelope(stmt, domain=t.V5_DOMAIN, contract="r08-v5", key_id="key-unknown", signature=t.sign(stmt), pub=t.PK))
    assert_refused(decide(rec=rec, sel=sel), "issuer_untrusted")


def test_label_swap_a_statement_signed_over_another_domain_fails_signature():
    rec = rec_()
    stmt = t.statement(rec)
    for domain in (s.V2_DOMAIN, s.V1_DOMAIN, b"", b"ocs-reg/r08-v4/selection\n", b"ocs-reg/r08-v3/selection\n", b"ocs-reg/r08-v5/other\n"):
        sel = r.dumps(s.envelope(stmt, domain=domain, contract="r08-v5", signature=t.sign(stmt, domain=domain), pub=t.PK))
        assert_refused(decide(rec=rec, sel=sel), "signature_invalid")


# ---- digests and pins
def test_altered_record_statement_and_pins_refuse():
    rec = rec_()
    sel = sel_(rec)
    tampered = copy.deepcopy(rec)
    tampered["payload"][FIELD]["class-a"] = B  # widen the Registry value without resealing
    assert v5_record.validate_record_text_v5(r.dumps(tampered)).code == "digest_mismatch"
    assert_refused(decide(rec=tampered, sel=sel), "composition_record_invalid")
    resealed = r.seal_record(tampered)  # widen and reseal: not the record the signed selection pins
    assert_refused(decide(rec=resealed, sel=sel), "record_digest_mismatch")
    stmt = t.statement(rec)
    env = t.envelope(stmt)
    env["statement_digest"] = "sha256:" + "0" * 64
    assert_refused(decide(rec=rec, sel=r.dumps(env)), "digest_mismatch")
    assert_refused(decide(rec=rec_(record_version=2), sel=sel), "record_identity_mismatch")
    assert_refused(decide(rec=rec_(record_id="f5u-other-record"), sel=sel), "record_identity_mismatch")


def test_evaluator_mismatch_between_selection_and_record():
    rec = rec_()
    stmt = t.statement(rec)
    stmt["evaluator"] = dict(stmt["evaluator"], source_blob_id="1" * 40)
    assert_refused(decide(rec=rec, sel=r.dumps(t.envelope(stmt))), "evaluator_mismatch")


def test_no_selection_or_record_refuses():
    from registry_successor.v5_decision import verify_and_decide_v5
    ad = t.ev.Ed25519Verifier()
    assert_refused(verify_and_decide_v5("required", t.caller(), r.dumps(rec_()), None, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission), "selection_missing")
    d = verify_and_decide_v5("required", t.caller(), None, sel_(rec_()), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.effective is None


# ---- lifecycle: withdrawn, revoked, stale, expired
def test_withdrawn_selection_refuses():
    rec = rec_()
    wd = s.withdraw_statement(t.statement(rec))
    assert_refused(decide(rec=rec, sel=r.dumps(t.envelope(wd))), "selection_withdrawn")
    assert_refused(decide(rec=rec, sel=r.dumps(s.envelope(wd, domain=t.V5_DOMAIN, contract="r08-v5", signed=False))), "signature_missing")


def test_revoked_stale_expired_and_not_yet_effective_refuse():
    rec = rec_()
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 2),))), "selection_epoch_stale")
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    late = r.NOW + datetime.timedelta(days=3)
    assert_refused(decide(rec=rec, now=late, trust=s.trust(pub=t.PK, valid_until="2026-12-31T00:00:00Z")), "selection_expired")
    assert_refused(decide(rec=rec, trust=s.trust(pub=t.PK, valid_until="2026-10-25T06:00:00Z")), "trust_snapshot_expired")
    assert_refused(decide(rec=rec, now=r.NOW - datetime.timedelta(days=3)), "selection_not_yet_effective")
    from registry_successor.v5_decision import verify_and_decide_v5
    ad = t.ev.Ed25519Verifier()
    assert_refused(verify_and_decide_v5("required", t.caller(), r.dumps(rec), sel_(rec), s.CTX, s.trust(pub=t.PK), ad, None, ad.key_admission), "time_unavailable")
    assert_refused(decide(participation="required", sel=sel_(rec, participation="optional")), "participation_mismatch")


def test_trust_snapshot_missing_unverifier_and_bad_key():
    from registry_successor.v5_decision import verify_and_decide_v5
    rec = rec_()
    ad = t.ev.Ed25519Verifier()
    args = ("required", t.caller(), r.dumps(rec), sel_(rec), s.CTX)
    assert_refused(verify_and_decide_v5(*args, None, ad, r.NOW), "trust_snapshot_missing")
    assert_refused(verify_and_decide_v5(*args, s.trust(pub=t.PK), None, r.NOW), "verifier_unavailable")
    assert_refused(verify_and_decide_v5(*args, s.trust(pub=bytes.fromhex("01" + "00" * 31)), ad, r.NOW), "trust_snapshot_invalid")


def test_bad_participation_value_refuses():
    for bad in ("sometimes", None, 1, b"required"):
        d = decide(participation=bad)
        assert d.kind == "required_policy_unavailable" and d.code == "participation_mismatch" and d.effective is None


def test_operationally_authorized_is_false_on_every_outcome():
    outcomes = [decide(), decide(cl=cmap(class_a=R)), decide(cl={FIELD: {}}), decide(sel="{}"), decide(participation="optional", sel="{}")]
    assert all(o.operationally_authorized is False for o in outcomes)
    assert all(o.effective is None for o in outcomes if o.kind == "required_policy_unavailable")


# ---- canonical serialization pins and the signed vector
def test_record_digest_and_signing_input_are_the_canonical_forms():
    rec = rec_()
    body = {k: v_ for k, v_ in rec.items() if k != "record_digest"}
    indep = "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert rec["record_digest"] == indep
    stmt = t.statement(rec)
    assert v5_selection.signing_input_v5(stmt) == b"ocs-reg/r08-v5/selection\n" + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert v5_selection.SIGNING_DOMAIN_V5 != s.V2_DOMAIN != s.V1_DOMAIN
    reordered = json.dumps(dict(reversed(list(rec.items()))), indent=3)
    assert v5_record.validate_record_text_v5(reordered).ok


def test_signed_vector_is_deterministic_and_verifies():
    vec = json.loads(open(os.path.join(os.path.dirname(__file__), "vectors", "r08v5", "signed_selection_vector.json")).read())
    rec, stmt = vec["record"], vec["statement"]
    assert rec == t.record() and stmt == t.statement(t.record())
    assert v5_selection.signing_input_v5(stmt).hex() == vec["signing_input_hex"]
    assert t.sign(stmt) == vec["signature"] == base64.b64encode(bytes.fromhex(vec["signature_hex"])).decode()
    assert t.nb.crypto_sign_open(bytes.fromhex(vec["signature_hex"]) + bytes.fromhex(vec["signing_input_hex"]), t.PK) == bytes.fromhex(vec["signing_input_hex"])
    d = decide(rec=rec, sel=json.dumps(vec["envelope"]))
    assert d.kind == "applied" and d.effective[FIELD]["class-a"] == R
