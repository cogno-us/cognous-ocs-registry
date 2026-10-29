"""`r08-v6` exact-boundary, exact-type and layer-isolation checks for both families (BUILDER_TESTED; not independently qualified).

These pin the edges the broader decision-path tests do not: inclusive/exclusive time bounds, the epoch floor, exact-type dispatch (a str subclass
never selects a family or a table), truthy-but-not-True record objects, and that each verification layer refuses on its own.
"""
import copy
import datetime

import pytest

import r08_support as r
import r08v6_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import v6_class_revocation_assurance as ra
from registry_successor import v6_families as fam
from registry_successor import v6_policy_identity as v6pi
from registry_successor import v6_terminal_revocation as tr

RA, TR = t.FAMILY, t.FAMILY_TR
FAMS = pytest.mark.parametrize("family", [RA, TR], ids=["revocation-assurance", "terminal-revocation"])


class S(str):
    pass


def test_exact_type_family_and_version_dispatch():
    for family in (RA, TR):
        assert fam.lookup_v6(family) is not None
        assert fam.lookup_v6(S(family)) is None  # equal and same hash, but not an exact str
        assert v6pi.registered_family_version(family, "r08-v6") == "v6"
        with pytest.raises(v6pi.IdentityRefusal):
            v6pi.registered_family_version(S(family), "r08-v6")
        with pytest.raises(v6pi.IdentityRefusal):
            v6pi.registered_family_version(family, S("r08-v6"))
    assert fam.table_for_contract_version_v6("r08-v6").ok
    sel = fam.table_for_contract_version_v6(S("r08-v6"))
    assert not sel.ok and sel.code == "contract_unsupported" and sel.table is None
    assert fam.compose_for_v6(S("r08-v6"), t.caller(), type("R", (), {"ok": True, "record": {}})()).code == "contract_unsupported"
    assert fam.lookup_v6([RA]) is None and fam.lookup_v6(None) is None and fam.lookup_v6({}) is None


def test_composer_operator_and_record_flags_are_exact():
    rec_ra = type("R", (), {"ok": 1, "record": {"family": RA, "payload": t.payload(RA)}})()
    rec_tr = type("R", (), {"ok": 1, "record": {"family": TR, "payload": t.payload(TR)}})()
    assert ra.compose_f5ra(t.caller(RA), rec_ra).code == "composition_record_invalid"
    assert tr.compose_tr(t.caller(TR), rec_tr).code == "composition_record_invalid"
    assert fam.compose_for_v6("r08-v6", t.caller(RA), rec_ra).code == "composition_record_invalid"
    for op in (S("intersection"),):
        assert ra.compose_f5ra(t.caller(RA), type("R", (), {"ok": True, "record": rec_ra.record})(), op).code == "composition_operator_unsupported"
        assert tr.compose_tr(t.caller(TR), type("R", (), {"ok": True, "record": rec_tr.record})(), op).code == "composition_operator_unsupported"
        assert fam.compose_for_v6("r08-v6", t.caller(RA), type("R", (), {"ok": True, "record": rec_ra.record})(), op).code == "composition_operator_unsupported"
    fam_sub = type("R", (), {"ok": True, "record": {"family": S(TR), "payload": t.payload(TR)}})()
    assert tr.compose_tr(t.caller(TR), fam_sub).code == "composition_family_unsupported"
    fam_sub = type("R", (), {"ok": True, "record": {"family": S(RA), "payload": t.payload(RA)}})()
    assert ra.compose_f5ra(t.caller(RA), fam_sub).code == "composition_family_unsupported"
    assert fam.compose_for_v6("r08-v6", t.caller(RA), fam_sub).code == "composition_family_unsupported"


@FAMS
def test_time_bounds_are_start_inclusive_and_end_exclusive(family):
    rec = t.record(family=family)
    utc = datetime.timezone.utc
    assert t.decide(rec=rec, now=datetime.datetime(2026, 10, 25, 0, 0, 0, tzinfo=utc)).kind == "applied"
    assert t.decide(rec=rec, now=datetime.datetime(2026, 10, 25, 23, 59, 59, tzinfo=utc)).kind == "applied"
    t.assert_refused(t.decide(rec=rec, now=datetime.datetime(2026, 10, 24, 23, 59, 59, tzinfo=utc)), "selection_not_yet_effective")
    t.assert_refused(t.decide(rec=rec, now=datetime.datetime(2026, 10, 26, 0, 0, 0, tzinfo=utc)), "selection_expired")


@FAMS
def test_trust_snapshot_expiry_is_exclusive(family):
    rec = t.record(family=family)
    utc = datetime.timezone.utc
    tr_ = s.trust(pub=t.PK, valid_until="2026-10-25T12:00:00Z")
    t.assert_refused(t.decide(rec=rec, trust=tr_, now=datetime.datetime(2026, 10, 25, 12, 0, 0, tzinfo=utc)), "trust_snapshot_expired")
    assert t.decide(rec=rec, trust=tr_, now=datetime.datetime(2026, 10, 25, 11, 59, 59, tzinfo=utc)).kind == "applied"


@FAMS
def test_epoch_floor_is_inclusive_and_revocation_is_exact(family):
    rec = t.record(family=family)
    assert t.decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 1),))).kind == "applied"
    t.assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 2),))), "selection_epoch_stale")
    assert t.decide(rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-other", 9),))).kind == "applied"  # another selection's floor
    assert t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-other", 1)}))).kind == "applied"
    t.assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")


@FAMS
def test_a_revoked_key_is_refused_even_when_the_signature_is_otherwise_valid(family):
    rec = t.record(family=family)
    t.assert_refused(t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    assert t.decide(rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({"key-other"}))).kind == "applied"


@FAMS
def test_withdrawal_is_refused_with_its_own_code_only_when_authentic_and_in_scope(family):
    rec = t.record(family=family)
    wd = s.withdraw_statement(t.statement(rec))
    t.assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd))), "selection_withdrawn")
    other_ctx = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")
    t.assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd)), ctx=other_ctx), "selection_operation_mismatch")
    t.assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd)), trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    t.assert_refused(t.decide(rec=rec, sel=r.dumps(t.envelope(wd)), trust=s.trust(pub=t.PK, revoked_selections=frozenset({(wd["selection_id"], wd["epoch"])}))),
                     "selection_revoked")


@FAMS
def test_participation_must_match_the_signed_statement_in_both_directions(family):
    rec = t.record(family=family)
    t.assert_refused(t.decide(participation="required", rec=rec, sel=t.selection_text(rec, participation="optional")), "participation_mismatch")
    d = t.decide(participation="optional", rec=rec, sel=t.selection_text(rec, participation="required"))
    assert d.kind == "overlay_not_applied" and d.code == "participation_mismatch" and d.caller_unchanged is True
    assert t.decide(participation="optional", rec=rec, sel=t.selection_text(rec, participation="optional")).kind == "applied"


@FAMS
def test_key_admission_is_mandatory_on_the_v6_path(family):
    from registry_successor.v6_decision import verify_and_decide_v6
    rec = t.record(family=family)
    ad = t.ev.Ed25519Verifier()
    bad_key = s.trust(pub=bytes.fromhex("01" + "00" * 31))
    d = verify_and_decide_v6("required", t.caller(family), r.dumps(rec), t.selection_text(rec), s.CTX, bad_key, ad, r.NOW, None)
    assert d.kind == "required_policy_unavailable" and d.code == "trust_snapshot_invalid" and d.effective is None


@FAMS
def test_selection_of_one_authority_cannot_be_used_by_a_signer_holding_only_another_scope(family):
    rec = t.record(family=family)
    from registry_successor import verify as v
    grant = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")
    tr_ = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (grant,)),))
    t.assert_refused(t.decide(rec=rec, trust=tr_), "issuer_not_authorized")


# ---- evaluator pin and the defence-in-depth checks of the decision step (reachable only by handing it a hand-built report)
@FAMS
def test_selection_and_record_must_name_the_registered_evaluator(family):
    from registry_successor import v6_record, v6_selection
    rec = t.record(family=family)
    for field, value in (("evaluator_id", "other.evaluator"), ("binding", "other-binding")):
        stmt = t.statement(rec)
        stmt["evaluator"] = dict(stmt["evaluator"], **{field: value})
        parsed = v6_selection.parse_selection_envelope_v6(r.dumps(t.envelope(stmt)))
        assert not parsed.ok and parsed.code == "evaluator_unsupported"
        bad_rec = r.seal_record(dict(rec, evaluator=dict(rec["evaluator"], **{field: value})))
        assert v6_record.validate_record_text_v6(r.dumps(bad_rec)).code in ("evaluator_unsupported", "field_invalid")
        t.assert_refused(t.decide(rec=bad_rec, sel=r.dumps(t.envelope(stmt))), "evaluator_unsupported")


@FAMS
def test_the_decision_step_rechecks_report_binding_and_record_digests_itself(family):
    from registry_successor import v6_decision, v6_record
    rec_text = r.dumps(t.record(family=family))
    rec = v6_record.validate_record_text_v6(rec_text)
    assert rec.ok

    def report(**over):
        base = {"ok": True, "code": None, "participation": "required", "layers": {"record_binding": "pass"}, "bound_record_digest": rec.record_digest}
        base.update(over)
        return type("Rep", (), base)()
    caller = t.caller(family)
    good = v6_decision._decide_verified("required", caller, rec, report())
    assert good.kind == "applied"
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, report(bound_record_digest="sha256:" + "0" * 64)), "record_digest_mismatch")
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, report(layers={"record_binding": "refuse"})), "record_identity_mismatch")
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, report(layers={})), "record_identity_mismatch")
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, report(layers=None)), "record_identity_mismatch")
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, report(participation="optional")), "participation_mismatch")
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, report(ok=False, code="signature_invalid")), "signature_invalid")
    t.assert_refused(v6_decision._decide_verified("required", caller, rec, None), "selection_missing")
    t.assert_refused(v6_decision._decide_verified("required", caller, None, report()), "composition_record_invalid")
    # a validated record whose body was altered after validation (payload widened, digests left as recorded)
    altered = copy.deepcopy(rec.record)
    if family == RA:
        altered["payload"]["class_requires_revocation_assurance"]["class-a"] = "not_required"
    else:
        altered["payload"]["terminal_revocation"] = "off"
    forged = type("Rec", (), {"ok": True, "record": altered, "record_digest": rec.record_digest, "code": None})()
    t.assert_refused(v6_decision._decide_verified("required", caller, forged, report()), "digest_mismatch")
    # a non-payload member altered while the recorded digests are left as they were: the record digest no longer matches the body
    altered3 = copy.deepcopy(rec.record)
    altered3["record_id"] = "f5-altered-record"
    forged3 = type("Rec", (), {"ok": True, "record": altered3, "record_digest": rec.record_digest, "code": None})()
    t.assert_refused(v6_decision._decide_verified("required", caller, forged3, report()), "digest_mismatch")
    # payload digest wrong but record digest recomputed over it: still refused
    altered2 = copy.deepcopy(rec.record)
    altered2["payload_digest"] = "sha256:" + "1" * 64
    altered2["record_digest"] = c.digest({k: v for k, v in altered2.items() if k != "record_digest"})
    forged2 = type("Rec", (), {"ok": True, "record": altered2, "record_digest": altered2["record_digest"], "code": None})()
    t.assert_refused(v6_decision._decide_verified("required", caller, forged2, report(bound_record_digest=altered2["record_digest"])), "digest_mismatch")
