"""The public `r08-v6` decision path with real synthetic Ed25519 signatures, for BOTH families (BUILDER_TESTED; not independently qualified).

Where PyNaCl is absent the module is NOT RUN (skipped with a reason), never passed with a double. The Registry CI installs the hash-locked backend.
Each record and each selection is for exactly one family under its own operation id: nothing here (or in the contract) makes the two families atomically
applicable.
"""
import base64
import copy
import datetime
import hashlib
import itertools
import json
import os

import pytest

import r08_support as r
import r08v6_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import verify as v
from registry_successor import v6_record
from registry_successor import v6_selection
from registry_successor.v6_decision import verify_and_decide_v6

pytestmark = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

RA, TR = t.FAMILY, t.FAMILY_TR
RF, TF = t.FIELD, t.TR_FIELD
REQ, NREQ = "required", "not_required"
ON, OFF = "on", "off"
assert_refused = t.assert_refused


def rec_(pl=None, family=None, **over):
    return t.record(pl, family=family, **over)


def cmap(**kw):
    return {RF: {k.replace("_", "-"): v for k, v in kw.items()}}


@pytest.fixture(params=[RA, TR], ids=["revocation-assurance", "terminal-revocation"])
def fam(request):
    return request.param


# ---- positive: narrowing, equality, attempted widening (class map)
def test_ra_valid_selection_narrows_not_required_to_required_and_keeps_unlisted_classes():
    d = t.decide()
    assert d.kind == "applied" and d.code is None and d.deny_all is False and d.operationally_authorized is False and d.caller_unchanged is False
    assert d.effective == {RF: {"class-a": REQ, "class-b": REQ, "class-c": REQ}} and d.detail == ""


def test_ra_registry_not_required_never_widens_a_required_host_value_through_the_signed_path():
    d = t.decide(rec=rec_(cmap(class_a=NREQ, class_b=NREQ)), cl=cmap(class_a=REQ, class_b=REQ))
    assert d.kind == "applied" and d.effective == cmap(class_a=REQ, class_b=REQ) and d.detail == "registry_value_not_narrowing:class-a,class-b"
    d2 = t.decide(rec=rec_(cmap(class_a=NREQ, class_b=REQ)), cl=cmap(class_a=REQ, class_b=NREQ))
    assert d2.effective == cmap(class_a=REQ, class_b=REQ) and d2.detail == "registry_value_not_narrowing:class-a"


def test_ra_registry_equal_to_host_is_applied_without_a_not_narrowing_report():
    d = t.decide(rec=rec_(cmap(class_a=NREQ)), cl=cmap(class_a=NREQ, class_b=NREQ))
    assert d.kind == "applied" and d.effective == cmap(class_a=NREQ, class_b=NREQ) and d.detail == ""


@pytest.mark.parametrize("h,g", list(itertools.product((REQ, NREQ), repeat=2)))
def test_ra_never_looser_than_the_caller_for_any_signed_combination(h, g):
    d = t.decide(rec=rec_(cmap(class_a=g)), cl=cmap(class_a=h))
    assert d.kind == "applied" and (d.effective[RF]["class-a"] == REQ) == (REQ in (h, g))


def test_ra_unknown_registry_class_refuses_and_is_never_created():
    assert_refused(t.decide(rec=rec_(cmap(class_a=REQ, class_zz=REQ)), cl=cmap(class_a=NREQ)), "composition_record_invalid")


@pytest.mark.parametrize("bad", [{}, 5, {RF: {}}, {RF: {"class-a": "x"}}, {RF: {"class-a": 1}}, {RF: {"class-a": None}}, {RF: {"class-a": True}},
                                 {RF: {"class a": NREQ}}, {RF: {"class-a": NREQ}, "x": 1}, "x", {TF: ON}])
def test_ra_invalid_caller_refuses_required(bad):
    assert_refused(t.decide(cl=bad), "composition_caller_invalid")


# ---- positive: terminal revocation scalar
@pytest.mark.parametrize("host,reg,eff,detail", [
    (OFF, OFF, OFF, ""), (OFF, ON, ON, ""), (ON, OFF, ON, "registry_value_not_narrowing:terminal_revocation"), (ON, ON, ON, "")])
def test_tr_signed_matrix(host, reg, eff, detail):
    d = t.decide(rec=rec_({TF: reg}, TR), cl={TF: host})
    assert d.kind == "applied" and d.effective == {TF: eff} and d.detail == detail and d.deny_all is False and d.deny_all_fields == ()
    assert d.operationally_authorized is False and d.caller_unchanged is False and d.code is None


@pytest.mark.parametrize("bad", [{}, 5, "on", {TF: "x"}, {TF: True}, {TF: 1}, {TF: None}, {TF: {"class-a": ON}}, {TF: ON, "x": 1}, {TF: "ON"}, cmap(class_a=REQ)])
def test_tr_invalid_caller_refuses_required(bad):
    assert_refused(t.decide(rec=rec_(family=TR), cl=bad), "composition_caller_invalid")


def test_tr_missing_caller_refuses_required():
    ad = t.ev.Ed25519Verifier()
    rec = rec_(family=TR)
    assert_refused(verify_and_decide_v6("required", None, r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission),
                   "composition_caller_invalid")


# ---- optional participation (both families)
def test_optional_participation_refusal_leaves_the_caller_policy_unchanged_not_an_application(fam):
    rec = rec_(family=fam)
    sel = r.dumps(t.envelope(t.statement(rec, participation="optional")))
    bad_caller = cmap(class_a="x") if fam == RA else {TF: "x"}
    d = t.decide(participation="optional", rec=rec, sel=sel, cl=bad_caller)
    assert d.kind == "overlay_not_applied" and d.code == "composition_caller_invalid" and d.caller_unchanged is True
    assert d.operationally_authorized is False and d.deny_all is False and d.effective == bad_caller
    good = cmap(class_a=NREQ, class_b=NREQ) if fam == RA else {TF: OFF}
    bad_sig = r.dumps(t.envelope(t.statement(rec, participation="optional"), sk=t.OTHER_SK))
    d3 = t.decide(participation="optional", rec=rec, sel=bad_sig, cl=good)
    assert d3.kind == "overlay_not_applied" and d3.code == "signature_invalid" and d3.caller_unchanged is True
    assert d3.effective == good  # unchanged caller, NOT a Registry narrowing and NOT a denial
    d4 = t.decide(participation="optional", rec=rec, sel=sel, cl=good)
    assert d4.kind == "applied" and d4.effective == ({RF: {"class-a": REQ, "class-b": REQ}} if fam == RA else {TF: ON})


def test_optional_refusal_normalizes_a_well_formed_caller_of_either_shape_and_passes_others_through():
    unsigned = "{}"
    d = t.decide(participation="optional", sel=unsigned, cl={RF: dict(reversed(list({"class-a": REQ, "class-b": NREQ}.items())))})
    assert d.kind == "overlay_not_applied" and d.effective == {RF: {"class-a": REQ, "class-b": NREQ}} and list(d.effective[RF]) == ["class-a", "class-b"]
    d = t.decide(participation="optional", rec=rec_(family=TR), sel=unsigned, cl={TF: ON})
    assert d.kind == "overlay_not_applied" and d.effective == {TF: ON}
    junk = {"zzz": 1}
    d = t.decide(participation="optional", sel=unsigned, cl=junk)
    assert d.kind == "overlay_not_applied" and d.effective == junk and d.caller_unchanged is True and d.operationally_authorized is False


# ---- malformed records: validator code and decision refusal
@pytest.mark.parametrize("pl,code", [
    ({}, "field_missing"), ({RF: {"class-a": REQ}, "x": 1}, "field_unknown"), ({"other": {"class-a": REQ}}, "field_unknown"),
    ({RF: {"class-a": 1}}, "field_type_invalid"), ({RF: {"class-a": None}}, "field_type_invalid"), ({RF: {"class-a": True}}, "field_type_invalid"),
    ({RF: {"class-a": False}}, "field_type_invalid"), ({RF: REQ}, "field_type_invalid"), ({RF: [REQ]}, "field_type_invalid"),
    ({RF: {"class-a": "optional"}}, "field_invalid"), ({RF: {"class-a": "Required"}}, "field_invalid"), ({RF: {}}, "field_invalid"),
    ({RF: {"*": REQ}}, "field_invalid"), ({RF: {"class a": REQ}}, "field_invalid"), ({TF: ON}, "field_unknown"),
])
def test_ra_malformed_payload_typed_validator_code_and_decision_refusal(pl, code):
    rec = rec_(pl)
    assert v6_record.validate_record_text_v6(r.dumps(rec)).code == code
    assert_refused(t.decide(rec=rec, sel=t.selection_text(rec)), "composition_record_invalid")


@pytest.mark.parametrize("pl,code", [
    ({}, "field_missing"), ({TF: ON, "x": 1}, "field_unknown"), ({"other": ON}, "field_unknown"), ({TF: True}, "field_type_invalid"),
    ({TF: False}, "field_type_invalid"), ({TF: 1}, "field_type_invalid"), ({TF: None}, "field_type_invalid"), ({TF: [ON]}, "field_type_invalid"),
    ({TF: {"class-a": ON}}, "field_type_invalid"), ({TF: "enabled"}, "field_invalid"), ({TF: "ON"}, "field_invalid"), ({TF: ""}, "field_invalid"),
    ({RF: {"class-a": REQ}}, "field_unknown"),
])
def test_tr_malformed_payload_typed_validator_code_and_decision_refusal(pl, code):
    rec = rec_(pl, TR)
    assert v6_record.validate_record_text_v6(r.dumps(rec)).code == code
    assert_refused(t.decide(rec=rec, sel=t.selection_text(rec)), "composition_record_invalid")


@pytest.mark.parametrize("literal", ["5.0", "1e3", "NaN", "Infinity", "-Infinity", "0.0", "true", "false", "null"])
def test_non_string_literals_never_reach_validation(fam, literal):
    rec = rec_(family=fam)
    base = r.dumps(rec)
    old = '"class-a": "required"' if fam == RA else '"terminal_revocation": "on"'
    text = base.replace(old, old.split(":")[0] + ": " + literal)
    assert text != base
    assert v6_record.validate_record_text_v6(text).code in ("json_number_unsupported", "field_type_invalid")
    assert_refused(t.decide(rec=rec, record_text=text), "composition_record_invalid")


def test_duplicate_key_and_non_json_records_refuse(fam):
    rec = rec_(family=fam)
    old = '"class-a": "required"' if fam == RA else '"terminal_revocation": "on"'
    dup = old.replace("required", "not_required").replace('"on"', '"off"') + ", " + old
    text = r.dumps(rec).replace(old, dup)
    assert text != r.dumps(rec)
    assert v6_record.validate_record_text_v6(text).code == "json_duplicate_key"
    assert v6_record.validate_record_text_v6("not json").code == "json_malformed"
    assert v6_record.validate_record_text_v6(None).code == "input_not_text"
    assert_refused(t.decide(rec=rec, record_text=text), "composition_record_invalid")


def test_record_top_level_checks(fam):
    assert v6_record.validate_record_text_v6(r.dumps(rec_(family=fam))).ok
    assert v6_record.validate_record_text_v6(r.dumps(rec_(family=fam, kind="selection"))).code == "kind_unsupported"
    assert v6_record.validate_record_text_v6(r.dumps(rec_(family=fam, non_authorizing=False))).code == "field_invalid"
    assert v6_record.validate_record_text_v6(r.dumps(rec_(family=fam, record_version=0))).code == "field_invalid"


# ---- families
def test_other_families_are_unsupported_in_the_v6_table():
    for fam_id in ("f1abcd-local-execution-limits", "f1abc-local-execution-limits", "f1ab-local-execution-allowlist", c.FAMILY_F1A,
                   "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "f5-action-class-unreadable-policy", "unknown-family"):
        rec = rec_(family=fam_id)
        assert v6_record.validate_record_text_v6(r.dumps(rec)).code == "family_unsupported"
        stmt = r.make_statement_v2(rec, family=fam_id)
        text = r.dumps(s.envelope(stmt, domain=t.V6_DOMAIN, contract="r08-v6", signature=t.sign(stmt), pub=t.PK))
        assert v6_selection.parse_selection_envelope_v6(text).code == "family_unsupported"
        assert_refused(t.decide(rec=rec, sel=text), "family_unsupported")


def test_selection_and_record_family_must_agree_in_both_directions():
    ra, tr_ = rec_(family=RA), rec_(family=TR)
    # family 1 record under a family 2 selection, and the reverse: the signed statement names the other family
    for rec, other in ((ra, tr_), (tr_, ra)):
        stmt = r.make_statement_v2(rec, family=other["family"])
        sel = r.dumps(t.envelope(stmt))
        assert v6_selection.parse_selection_envelope_v6(sel).ok
        assert_refused(t.decide(rec=rec, sel=sel), "family_unsupported")
    # a selection of one family that pins the other family's record (record id, version and digest of the other record)
    cross = r.make_statement_v2(tr_, family=RA)
    assert_refused(t.decide(rec=tr_, sel=r.dumps(t.envelope(cross))), "family_unsupported")
    # a record of one family supplied against a selection that pins the other record
    assert_refused(t.decide(rec=tr_, sel=t.selection_text(ra)), "family_unsupported")
    assert_refused(t.decide(rec=ra, sel=t.selection_text(tr_)), "family_unsupported")


def test_each_family_is_its_own_record_and_selection_with_its_own_operation():
    """The two families are never combined by the Registry: a decision names exactly one family's payload."""
    ra_d = t.decide(rec=rec_(family=RA))
    tr_d = t.decide(rec=rec_(family=TR))
    assert set(ra_d.effective) == {RF} and set(tr_d.effective) == {TF}
    ops = {"op-ra": RA, "op-tr": TR}
    for op, family in ops.items():
        rec = rec_(family=family)
        ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", op)
        grant = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", op)
        trust = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (grant,)),))
        d = t.decide(rec=rec, sel=t.selection_text(rec, operation=op), ctx=ctx, trust=trust)
        assert d.kind == "applied" and set(d.effective) == ({RF} if family == RA else {TF})
        other_ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-tr" if op == "op-ra" else "op-ra")
        assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, operation=op), ctx=other_ctx, trust=trust), "selection_operation_mismatch")


# ---- wrong tenant / scope / consumer / operation
@pytest.mark.parametrize("ctx,code", [
    (c.ExpectedContext("other-consumer", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch"),
    (None, "selection_scope_mismatch"),
])
def test_wrong_tenant_scope_consumer_operation_refuse(fam, ctx, code):
    rec = rec_(family=fam)
    if ctx is not None:
        d = t.decide(rec=rec, ctx=ctx)
    else:
        ad = t.ev.Ed25519Verifier()
        d = verify_and_decide_v6("required", t.caller(fam), r.dumps(rec), t.selection_text(rec), None, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert_refused(d, code)


def test_signer_without_exact_authority_is_not_authorized(fam):
    for other in (v.AuthorityGrant("consumer-test", "tenant-other", "inst-a", "domain-a", "op-test"),
                  v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"),
                  v.AuthorityGrant("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test")):
        tr_ = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (other,)),))
        assert_refused(t.decide(rec=rec_(family=fam), trust=tr_), "issuer_not_authorized")


# ---- signature
def test_forged_wrong_key_missing_and_noncanonical_signatures_refuse(fam):
    rec = rec_(family=fam)
    stmt = t.statement(rec)
    bad = bytearray(base64.b64decode(t.sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, domain=t.V6_DOMAIN, contract="r08-v6", signature=base64.b64encode(bytes(bad)).decode(), pub=t.PK))
    assert_refused(t.decide(rec=rec, sel=forged), "signature_invalid")
    assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, sk=t.OTHER_SK)), "signature_invalid")
    unsigned = r.dumps(s.envelope(stmt, domain=t.V6_DOMAIN, contract="r08-v6", signed=False))
    assert_refused(t.decide(rec=rec, sel=unsigned), "signature_missing")
    good = t.sign(stmt)
    for noncanon in (good + "\n", good.replace("=", "") if "=" in good else good + "=", good[:-4]):
        sel = r.dumps(s.envelope(stmt, domain=t.V6_DOMAIN, contract="r08-v6", signature=noncanon, pub=t.PK))
        d = t.decide(rec=rec, sel=sel)
        assert d.kind == "required_policy_unavailable" and d.effective is None


def test_signature_by_an_unknown_key_id_is_untrusted(fam):
    rec = rec_(family=fam)
    stmt = t.statement(rec)
    sel = r.dumps(s.envelope(stmt, domain=t.V6_DOMAIN, contract="r08-v6", key_id="key-unknown", signature=t.sign(stmt), pub=t.PK))
    assert_refused(t.decide(rec=rec, sel=sel), "issuer_untrusted")


def test_label_swap_a_statement_signed_over_another_domain_fails_signature(fam):
    rec = rec_(family=fam)
    stmt = t.statement(rec)
    for domain in (s.V2_DOMAIN, s.V1_DOMAIN, b"", b"ocs-reg/r08-v5/selection\n", b"ocs-reg/r08-v4/selection\n", b"ocs-reg/r08-v3/selection\n",
                   b"ocs-reg/r08-v6/other\n", b"ocs-reg/r08-v6/effective-policy\n"):
        sel = r.dumps(s.envelope(stmt, domain=domain, contract="r08-v6", signature=t.sign(stmt, domain=domain), pub=t.PK))
        assert_refused(t.decide(rec=rec, sel=sel), "signature_invalid")


# ---- digests and pins
def test_altered_record_statement_and_pins_refuse(fam):
    rec = rec_(family=fam)
    sel = t.selection_text(rec)
    tampered = copy.deepcopy(rec)
    if fam == RA:
        tampered["payload"][RF]["class-a"] = NREQ  # widen the Registry value without resealing
    else:
        tampered["payload"][TF] = OFF
    assert v6_record.validate_record_text_v6(r.dumps(tampered)).code == "digest_mismatch"
    assert_refused(t.decide(rec=tampered, sel=sel), "composition_record_invalid")
    resealed = r.seal_record(tampered)  # widen and reseal: not the record the signed selection pins
    assert_refused(t.decide(rec=resealed, sel=sel), "record_digest_mismatch")
    stmt = t.statement(rec)
    env = t.envelope(stmt)
    env["statement_digest"] = "sha256:" + "0" * 64
    assert_refused(t.decide(rec=rec, sel=r.dumps(env)), "digest_mismatch")
    assert_refused(t.decide(rec=rec_(family=fam, record_version=2), sel=sel), "record_identity_mismatch")
    assert_refused(t.decide(rec=rec_(family=fam, record_id="f5-other-record"), sel=sel), "record_identity_mismatch")


def test_evaluator_mismatch_between_selection_and_record(fam):
    rec = rec_(family=fam)
    stmt = t.statement(rec)
    stmt["evaluator"] = dict(stmt["evaluator"], source_blob_id="1" * 40)
    assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(stmt))), "evaluator_mismatch")


def test_no_selection_or_record_refuses(fam):
    ad = t.ev.Ed25519Verifier()
    rec = rec_(family=fam)
    assert_refused(verify_and_decide_v6("required", t.caller(fam), r.dumps(rec), None, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission), "selection_missing")
    d = verify_and_decide_v6("required", t.caller(fam), None, t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.effective is None


# ---- lifecycle: withdrawn, revoked, stale, expired
def test_withdrawn_selection_refuses(fam):
    rec = rec_(family=fam)
    wd = s.withdraw_statement(t.statement(rec))
    assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd))), "selection_withdrawn")
    assert_refused(t.decide(rec=rec, sel=r.dumps(s.envelope(wd, domain=t.V6_DOMAIN, contract="r08-v6", signed=False))), "signature_missing")
    # a withdrawal signed by the wrong key is a signature failure, never a withdrawal
    assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd, sk=t.OTHER_SK))), "signature_invalid")


def test_revoked_key_revoked_selection_stale_expired_and_not_yet_effective_refuse(fam):
    rec = rec_(family=fam)
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")
    assert t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 2)}))).kind == "applied"  # only the exact epoch
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 2),))), "selection_epoch_stale")
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    late = r.NOW + datetime.timedelta(days=3)
    assert_refused(t.decide(rec=rec, now=late, trust=s.trust(pub=t.PK, valid_until="2026-12-31T00:00:00Z")), "selection_expired")
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, valid_until="2026-10-25T06:00:00Z")), "trust_snapshot_expired")
    assert_refused(t.decide(rec=rec, now=r.NOW - datetime.timedelta(days=3)), "selection_not_yet_effective")
    ad = t.ev.Ed25519Verifier()
    assert_refused(verify_and_decide_v6("required", t.caller(fam), r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, None, ad.key_admission), "time_unavailable")
    assert_refused(t.decide(participation="required", rec=rec, sel=t.selection_text(rec, participation="optional")), "participation_mismatch")


def test_trust_snapshot_missing_unverifier_and_bad_key(fam):
    rec = rec_(family=fam)
    ad = t.ev.Ed25519Verifier()
    args = ("required", t.caller(fam), r.dumps(rec), t.selection_text(rec), s.CTX)
    assert_refused(verify_and_decide_v6(*args, None, ad, r.NOW), "trust_snapshot_missing")
    assert_refused(verify_and_decide_v6(*args, s.trust(pub=t.PK), None, r.NOW), "verifier_unavailable")
    assert_refused(verify_and_decide_v6(*args, s.trust(pub=bytes.fromhex("01" + "00" * 31)), ad, r.NOW), "trust_snapshot_invalid")


def test_bad_participation_value_refuses():
    for bad in ("sometimes", None, 1, b"required"):
        d = t.decide(participation=bad)
        assert d.kind == "required_policy_unavailable" and d.code == "participation_mismatch" and d.effective is None


def test_operationally_authorized_is_false_and_deny_all_never_set_on_every_outcome(fam):
    rec = rec_(family=fam)
    outcomes = [t.decide(rec=rec), t.decide(rec=rec, cl={RF: {}}), t.decide(rec=rec, sel="{}"), t.decide(participation="optional", rec=rec, sel="{}")]
    assert all(o.operationally_authorized is False and o.deny_all is False and o.deny_all_fields == () for o in outcomes)
    assert all(o.effective is None for o in outcomes if o.kind == "required_policy_unavailable")


# ---- canonical serialization pins and the signed vectors
def test_record_digest_and_signing_input_are_the_canonical_forms(fam):
    rec = rec_(family=fam)
    body = {k: v_ for k, v_ in rec.items() if k != "record_digest"}
    indep = "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert rec["record_digest"] == indep
    stmt = t.statement(rec)
    assert v6_selection.signing_input_v6(stmt) == b"ocs-reg/r08-v6/selection\n" + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert len({v6_selection.SIGNING_DOMAIN_V6, s.V2_DOMAIN, s.V1_DOMAIN, t.V5_DOMAIN}) == 4
    reordered = json.dumps(dict(reversed(list(rec.items()))), indent=3)
    assert v6_record.validate_record_text_v6(reordered).ok


@pytest.mark.parametrize("family", [RA, TR])
def test_signed_vector_is_deterministic_and_verifies(family):
    vec = json.loads(open(os.path.join(os.path.dirname(__file__), "vectors", "r08v6", "signed_selection_vector.json")).read())[family]
    rec, stmt = vec["record"], vec["statement"]
    assert rec == t.record(family=family) and stmt == t.statement(t.record(family=family))
    assert v6_selection.signing_input_v6(stmt).hex() == vec["signing_input_hex"]
    assert t.sign(stmt) == vec["signature"] == base64.b64encode(bytes.fromhex(vec["signature_hex"])).decode()
    assert t.nb.crypto_sign_open(bytes.fromhex(vec["signature_hex"]) + bytes.fromhex(vec["signing_input_hex"]), t.PK) == bytes.fromhex(vec["signing_input_hex"])
    d = t.decide(rec=rec, sel=json.dumps(vec["envelope"]))
    assert d.kind == "applied" and d.effective == vec["effective"]
