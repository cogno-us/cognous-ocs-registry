"""The public `r08-v7` decision path with real synthetic Ed25519 signatures, irreversibility family (BUILDER_TESTED; not independently qualified).

Where PyNaCl is absent the module is NOT RUN (skipped with a reason), never passed with a double. The Registry CI installs the hash-locked backend.
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
import r08v7_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import verify as v
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e
from registry_successor.engine import selection as selection_e
from registry_successor.v7_decision import verify_and_decide_v7

pytestmark = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

FAM = t.FAMILY
F = t.FIELD
IRR, NC = "irreversible", "no_change"
assert_refused = t.assert_refused
V7 = profiles.V7


def validate(text):
    return record_e.validate_record_text(V7, text)


def rec_(pl=None, family=None, **over):
    return t.record(pl, family=family, **over)


def cmap(**kw):
    return {F: {k.replace("_", "-"): v for k, v in kw.items()}}


# ---- positive: narrowing, equality, attempted lowering
def test_valid_selection_flips_no_change_to_irreversible_and_keeps_unlisted_classes():
    d = t.decide()
    assert d.kind == "applied" and d.code is None and d.deny_all is False and d.operationally_authorized is False and d.caller_unchanged is False
    assert d.effective == {F: {"class-a": IRR, "class-b": IRR, "class-c": IRR}} and d.detail == "" and d.deny_all_fields == ()


def test_registry_no_change_never_lowers_an_irreversible_host_value_through_the_signed_path():
    d = t.decide(rec=rec_(cmap(class_a=NC, class_b=NC)), cl=cmap(class_a=IRR, class_b=IRR))
    assert d.kind == "applied" and d.effective == cmap(class_a=IRR, class_b=IRR) and d.detail == "registry_value_not_narrowing:class-a,class-b"
    d2 = t.decide(rec=rec_(cmap(class_a=NC, class_b=IRR)), cl=cmap(class_a=IRR, class_b=NC))
    assert d2.effective == cmap(class_a=IRR, class_b=IRR) and d2.detail == "registry_value_not_narrowing:class-a"


def test_registry_equal_to_host_is_applied_without_a_not_narrowing_report():
    d = t.decide(rec=rec_(cmap(class_a=NC)), cl=cmap(class_a=NC, class_b=NC))
    assert d.kind == "applied" and d.effective == cmap(class_a=NC, class_b=NC) and d.detail == ""


@pytest.mark.parametrize("h,g", list(itertools.product((IRR, NC), repeat=2)))
def test_never_looser_than_the_caller_for_any_signed_combination(h, g):
    d = t.decide(rec=rec_(cmap(class_a=g)), cl=cmap(class_a=h))
    assert d.kind == "applied" and (d.effective[F]["class-a"] == IRR) == (IRR in (h, g))


def test_unknown_registry_class_refuses_and_is_never_created():
    assert_refused(t.decide(rec=rec_(cmap(class_a=IRR, class_zz=IRR)), cl=cmap(class_a=NC)), "composition_record_invalid")


@pytest.mark.parametrize("bad", [{}, 5, {F: {}}, {F: {"class-a": "x"}}, {F: {"class-a": 1}}, {F: {"class-a": None}}, {F: {"class-a": True}},
                                 {F: {"class-a": False}}, {F: {"class a": NC}}, {F: {"class-a": NC}, "x": 1}, "x", {"terminal_revocation": "on"},
                                 {"class_requires_revocation_assurance": {"class-a": "required"}}])
def test_invalid_caller_refuses_required(bad):
    assert_refused(t.decide(cl=bad), "composition_caller_invalid")


def test_missing_caller_refuses_required():
    ad = t.ev.Ed25519Verifier()
    rec = rec_()
    assert_refused(verify_and_decide_v7("required", None, r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission),
                   "composition_caller_invalid")


# ---- optional participation
def test_optional_participation_refusal_leaves_the_caller_policy_unchanged_not_an_application():
    rec = rec_()
    sel = r.dumps(t.envelope(t.statement(rec, participation="optional")))
    bad_caller = cmap(class_a="x")
    d = t.decide(participation="optional", rec=rec, sel=sel, cl=bad_caller)
    assert d.kind == "overlay_not_applied" and d.code == "composition_caller_invalid" and d.caller_unchanged is True
    assert d.operationally_authorized is False and d.deny_all is False and d.effective == bad_caller
    good = cmap(class_a=NC, class_b=NC)
    bad_sig = r.dumps(t.envelope(t.statement(rec, participation="optional"), sk=t.OTHER_SK))
    d3 = t.decide(participation="optional", rec=rec, sel=bad_sig, cl=good)
    assert d3.kind == "overlay_not_applied" and d3.code == "signature_invalid" and d3.caller_unchanged is True
    assert d3.effective == good  # unchanged caller, NOT a Registry narrowing and NOT a denial
    d4 = t.decide(participation="optional", rec=rec, sel=sel, cl=good)
    assert d4.kind == "applied" and d4.effective == {F: {"class-a": IRR, "class-b": IRR}}


def test_optional_refusal_normalizes_a_well_formed_caller_and_passes_others_through():
    unsigned = "{}"
    d = t.decide(participation="optional", sel=unsigned, cl={F: dict(reversed(list({"class-a": IRR, "class-b": NC}.items())))})
    assert d.kind == "overlay_not_applied" and d.effective == {F: {"class-a": IRR, "class-b": NC}} and list(d.effective[F]) == ["class-a", "class-b"]
    junk = {"zzz": 1}
    d = t.decide(participation="optional", sel=unsigned, cl=junk)
    assert d.kind == "overlay_not_applied" and d.effective == junk and d.caller_unchanged is True and d.operationally_authorized is False
    # a caller of an earlier family's shape is not normalized by the v7 family
    ra_caller = {"class_requires_revocation_assurance": {"class-a": "required"}}
    d = t.decide(participation="optional", sel=unsigned, cl=ra_caller)
    assert d.effective is ra_caller and d.caller_unchanged is True


# ---- malformed records: validator code and decision refusal
@pytest.mark.parametrize("pl,code", [
    ({}, "field_missing"), ({F: {"class-a": IRR}, "x": 1}, "field_unknown"), ({"other": {"class-a": IRR}}, "field_unknown"),
    ({F: {"class-a": 1}}, "field_type_invalid"), ({F: {"class-a": None}}, "field_type_invalid"), ({F: {"class-a": True}}, "field_type_invalid"),
    ({F: {"class-a": False}}, "field_type_invalid"), ({F: IRR}, "field_type_invalid"), ({F: [IRR]}, "field_type_invalid"),
    ({F: {"class-a": "reversible"}}, "field_invalid"), ({F: {"class-a": "Irreversible"}}, "field_invalid"), ({F: {}}, "field_invalid"),
    ({F: {"*": IRR}}, "field_invalid"), ({F: {"class a": IRR}}, "field_invalid"), ({"terminal_revocation": "on"}, "field_unknown"),
    ({"class_requires_revocation_assurance": {"class-a": "required"}}, "field_unknown"),
])
def test_malformed_payload_typed_validator_code_and_decision_refusal(pl, code):
    rec = rec_(pl)
    assert validate(r.dumps(rec)).code == code
    assert_refused(t.decide(rec=rec, sel=t.selection_text(rec)), "composition_record_invalid")


@pytest.mark.parametrize("literal", ["5.0", "1e3", "NaN", "Infinity", "-Infinity", "0.0", "true", "false", "null"])
def test_non_string_literals_never_reach_validation(literal):
    rec = rec_()
    base = r.dumps(rec)
    old = '"class-a": "irreversible"'
    text = base.replace(old, old.split(":")[0] + ": " + literal)
    assert text != base
    assert validate(text).code in ("json_number_unsupported", "field_type_invalid")
    assert_refused(t.decide(rec=rec, record_text=text), "composition_record_invalid")


def test_duplicate_key_and_non_json_records_refuse():
    rec = rec_()
    old = '"class-a": "irreversible"'
    text = r.dumps(rec).replace(old, old.replace("irreversible", "no_change") + ", " + old)
    assert text != r.dumps(rec)
    assert validate(text).code == "json_duplicate_key"
    assert validate("not json").code == "json_malformed"
    assert validate(None).code == "input_not_text"
    assert_refused(t.decide(rec=rec, record_text=text), "composition_record_invalid")


def test_record_supersession_is_validated():
    rec1 = rec_()
    ok = rec_(record_version=2, supersedes={"record_id": rec1["record_id"], "record_version": 1, "record_digest": rec1["record_digest"]})
    assert validate(r.dumps(ok)).ok
    for bad in ({"record_id": "other-record", "record_version": 1, "record_digest": rec1["record_digest"]},
                {"record_id": rec1["record_id"], "record_version": 2, "record_digest": rec1["record_digest"]},
                {"record_id": rec1["record_id"], "record_version": 3, "record_digest": rec1["record_digest"]},
                {"record_id": rec1["record_id"], "record_version": 1, "record_digest": "nope"}):
        assert validate(r.dumps(rec_(record_version=2, supersedes=bad))).code == "supersession_invalid", bad
    assert validate(r.dumps(rec_(record_version=1, supersedes={"record_id": rec1["record_id"], "record_version": 1, "record_digest": rec1["record_digest"]}))).code \
        == "supersession_invalid"


def test_record_top_level_checks():
    assert validate(r.dumps(rec_())).ok
    assert validate(r.dumps(rec_(kind="selection"))).code == "kind_unsupported"
    assert validate(r.dumps(rec_(non_authorizing=False))).code == "field_invalid"
    assert validate(r.dumps(rec_(record_version=0))).code == "field_invalid"


# ---- families
def test_other_families_are_unsupported_in_the_v7_table():
    for fam_id in ("f1abcd-local-execution-limits", "f1abc-local-execution-limits", "f1ab-local-execution-allowlist", c.FAMILY_F1A,
                   "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "f5-action-class-unreadable-policy",
                   "f5-action-class-revocation-assurance-policy", "f5-terminal-revocation-enablement-policy", "unknown-family",
                   "anchor_deadline_to_inputs", "f5-observation-max-age-policy"):
        rec = rec_(family=fam_id)
        assert validate(r.dumps(rec)).code == "family_unsupported"
        stmt = r.make_statement_v2(rec, family=fam_id)
        text = r.dumps(s.envelope(stmt, domain=t.V7_DOMAIN, contract="r08-v7", signature=t.sign(stmt), pub=t.PK))
        assert selection_e.parse_selection_envelope(V7, text).code == "family_unsupported"
        assert_refused(t.decide(rec=rec, sel=text), "family_unsupported")


def test_selection_naming_another_family_than_the_record_is_refused():
    rec = rec_()
    other = "f5-action-class-revocation-assurance-policy"
    stmt = r.make_statement_v2(rec, family=other)
    sel = r.dumps(t.envelope(stmt))
    assert_refused(t.decide(rec=rec, sel=sel), "family_unsupported")


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
    rec = rec_()
    if ctx is not None:
        d = t.decide(rec=rec, ctx=ctx)
    else:
        ad = t.ev.Ed25519Verifier()
        d = verify_and_decide_v7("required", t.caller(), r.dumps(rec), t.selection_text(rec), None, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert_refused(d, code)


def test_signer_without_exact_authority_is_not_authorized():
    for other in (v.AuthorityGrant("consumer-test", "tenant-other", "inst-a", "domain-a", "op-test"),
                  v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"),
                  v.AuthorityGrant("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test")):
        tr_ = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (other,)),))
        assert_refused(t.decide(trust=tr_), "issuer_not_authorized")


# ---- signature
def test_forged_wrong_key_missing_and_noncanonical_signatures_refuse():
    rec = rec_()
    stmt = t.statement(rec)
    bad = bytearray(base64.b64decode(t.sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, domain=t.V7_DOMAIN, contract="r08-v7", signature=base64.b64encode(bytes(bad)).decode(), pub=t.PK))
    assert_refused(t.decide(rec=rec, sel=forged), "signature_invalid")
    assert_refused(t.decide(rec=rec, sel=t.selection_text(rec, sk=t.OTHER_SK)), "signature_invalid")
    unsigned = r.dumps(s.envelope(stmt, domain=t.V7_DOMAIN, contract="r08-v7", signed=False))
    assert_refused(t.decide(rec=rec, sel=unsigned), "signature_missing")
    good = t.sign(stmt)
    for noncanon in (good + "\n", good.replace("=", "") if "=" in good else good + "=", good[:-4], "!" + good[1:], good.replace("=", "").lower()):
        sel = r.dumps(s.envelope(stmt, domain=t.V7_DOMAIN, contract="r08-v7", signature=noncanon, pub=t.PK))
        d = t.decide(rec=rec, sel=sel)
        assert d.kind == "required_policy_unavailable" and d.effective is None and d.code == "signature_invalid", (noncanon, d.code)


def test_signature_by_an_unknown_key_id_is_untrusted():
    rec = rec_()
    stmt = t.statement(rec)
    sel = r.dumps(s.envelope(stmt, domain=t.V7_DOMAIN, contract="r08-v7", key_id="key-unknown", signature=t.sign(stmt), pub=t.PK))
    assert_refused(t.decide(rec=rec, sel=sel), "issuer_untrusted")


def test_label_swap_a_statement_signed_over_another_domain_fails_signature():
    rec = rec_()
    stmt = t.statement(rec)
    for domain in (s.V2_DOMAIN, s.V1_DOMAIN, b"", b"ocs-reg/r08-v6/selection\n", b"ocs-reg/r08-v5/selection\n", b"ocs-reg/r08-v4/selection\n",
                   b"ocs-reg/r08-v3/selection\n", b"ocs-reg/r08-v7/other\n", b"ocs-reg/r08-v7/effective-policy\n"):
        sel = r.dumps(s.envelope(stmt, domain=domain, contract="r08-v7", signature=t.sign(stmt, domain=domain), pub=t.PK))
        assert_refused(t.decide(rec=rec, sel=sel), "signature_invalid")


# ---- digests and pins
def test_altered_record_statement_and_pins_refuse():
    rec = rec_()
    sel = t.selection_text(rec)
    tampered = copy.deepcopy(rec)
    tampered["payload"][F]["class-a"] = NC  # lower the Registry value without resealing
    assert validate(r.dumps(tampered)).code == "digest_mismatch"
    assert_refused(t.decide(rec=tampered, sel=sel), "composition_record_invalid")
    resealed = r.seal_record(tampered)  # lower and reseal: not the record the signed selection pins
    assert_refused(t.decide(rec=resealed, sel=sel), "record_digest_mismatch")
    stmt = t.statement(rec)
    env = t.envelope(stmt)
    env["statement_digest"] = "sha256:" + "0" * 64
    assert_refused(t.decide(rec=rec, sel=r.dumps(env)), "digest_mismatch")
    assert_refused(t.decide(rec=rec_(record_version=2), sel=sel), "record_identity_mismatch")
    assert_refused(t.decide(rec=rec_(record_id="f5-other-record"), sel=sel), "record_identity_mismatch")


def test_evaluator_mismatch_between_selection_and_record():
    rec = rec_()
    stmt = t.statement(rec)
    stmt["evaluator"] = dict(stmt["evaluator"], source_blob_id="1" * 40)
    assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(stmt))), "evaluator_mismatch")


def test_no_selection_or_record_refuses():
    ad = t.ev.Ed25519Verifier()
    rec = rec_()
    assert_refused(verify_and_decide_v7("required", t.caller(), r.dumps(rec), None, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission), "selection_missing")
    d = verify_and_decide_v7("required", t.caller(), None, t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.effective is None


# ---- lifecycle: withdrawn, revoked, stale, expired
def test_withdrawn_selection_refuses():
    rec = rec_()
    wd = s.withdraw_statement(t.statement(rec))
    assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd))), "selection_withdrawn")
    assert_refused(t.decide(rec=rec, sel=r.dumps(s.envelope(wd, domain=t.V7_DOMAIN, contract="r08-v7", signed=False))), "signature_missing")
    assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd, sk=t.OTHER_SK))), "signature_invalid")  # wrong key: a signature failure, never a withdrawal


def test_revoked_key_revoked_selection_stale_expired_and_not_yet_effective_refuse():
    rec = rec_()
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")
    assert t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 2)}))).kind == "applied"  # only the exact epoch
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 2),))), "selection_epoch_stale")
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    late = r.NOW + datetime.timedelta(days=3)
    assert_refused(t.decide(rec=rec, now=late, trust=s.trust(pub=t.PK, valid_until="2026-12-31T00:00:00Z")), "selection_expired")
    assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, valid_until="2026-10-25T06:00:00Z")), "trust_snapshot_expired")
    assert_refused(t.decide(rec=rec, now=r.NOW - datetime.timedelta(days=3)), "selection_not_yet_effective")
    ad = t.ev.Ed25519Verifier()
    assert_refused(verify_and_decide_v7("required", t.caller(), r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, None, ad.key_admission), "time_unavailable")
    assert_refused(t.decide(participation="required", rec=rec, sel=t.selection_text(rec, participation="optional")), "participation_mismatch")


def test_trust_snapshot_missing_unverifier_and_bad_key():
    rec = rec_()
    ad = t.ev.Ed25519Verifier()
    args = ("required", t.caller(), r.dumps(rec), t.selection_text(rec), s.CTX)
    assert_refused(verify_and_decide_v7(*args, None, ad, r.NOW), "trust_snapshot_missing")
    assert_refused(verify_and_decide_v7(*args, s.trust(pub=t.PK), None, r.NOW), "verifier_unavailable")
    assert_refused(verify_and_decide_v7(*args, s.trust(pub=bytes.fromhex("01" + "00" * 31)), ad, r.NOW), "trust_snapshot_invalid")


def test_bad_participation_value_refuses():
    for bad in ("sometimes", None, 1, b"required"):
        d = t.decide(participation=bad)
        assert d.kind == "required_policy_unavailable" and d.code == "participation_mismatch" and d.effective is None


def test_operationally_authorized_is_false_and_deny_all_never_set_on_every_outcome():
    rec = rec_()
    outcomes = [t.decide(rec=rec), t.decide(rec=rec, cl={F: {}}), t.decide(rec=rec, sel="{}"), t.decide(participation="optional", rec=rec, sel="{}")]
    assert all(o.operationally_authorized is False and o.deny_all is False and o.deny_all_fields == () for o in outcomes)
    assert all(o.effective is None for o in outcomes if o.kind == "required_policy_unavailable")


def test_the_decision_never_returns_a_value_looser_than_the_caller_over_a_class_grid():
    """Exhaustive over two classes and every Registry/caller combination: a signed selection can only keep or strengthen the host's value."""
    for h1, h2, g1, g2 in itertools.product((IRR, NC), repeat=4):
        d = t.decide(rec=rec_(cmap(class_a=g1, class_b=g2)), cl=cmap(class_a=h1, class_b=h2))
        assert d.kind == "applied"
        for cls, host, reg in (("class-a", h1, g1), ("class-b", h2, g2)):
            assert d.effective[F][cls] == (IRR if IRR in (host, reg) else NC)
            assert not (host == IRR and d.effective[F][cls] == NC)


# ---- canonical serialization pins and the signed vector
def test_record_digest_and_signing_input_are_the_canonical_forms():
    rec = rec_()
    body = {k: v_ for k, v_ in rec.items() if k != "record_digest"}
    indep = "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert rec["record_digest"] == indep
    stmt = t.statement(rec)
    assert selection_e.signing_input(V7, stmt) == b"ocs-reg/r08-v7/selection\n" + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert len({V7.selection_signing_domain, profiles.V6_COMPAT.selection_signing_domain, s.V2_DOMAIN, s.V1_DOMAIN, t.V5_DOMAIN}) == 5
    reordered = json.dumps(dict(reversed(list(rec.items()))), indent=3)
    assert validate(reordered).ok


def test_signed_vector_is_deterministic_and_verifies():
    vec = json.loads(open(os.path.join(os.path.dirname(__file__), "vectors", "r08v7", "signed_selection_vector.json")).read())[FAM]
    rec, stmt = vec["record"], vec["statement"]
    assert rec == t.record() and stmt == t.statement(t.record())
    assert selection_e.signing_input(V7, stmt).hex() == vec["signing_input_hex"]
    assert t.sign(stmt) == vec["signature"] == base64.b64encode(bytes.fromhex(vec["signature_hex"])).decode()
    assert t.nb.crypto_sign_open(bytes.fromhex(vec["signature_hex"]) + bytes.fromhex(vec["signing_input_hex"]), t.PK) == bytes.fromhex(vec["signing_input_hex"])
    d = t.decide(rec=rec, sel=json.dumps(vec["envelope"]))
    assert d.kind == "applied" and d.effective == vec["effective"]
