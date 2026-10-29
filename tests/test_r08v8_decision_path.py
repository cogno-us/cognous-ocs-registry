"""The public `r08-v8` decision path with real synthetic Ed25519 signatures, all three families (APPROVED CANDIDATE; BUILDER_TESTED; not independently qualified).

Where PyNaCl is absent the module is NOT RUN (skipped with a reason), never passed with a double. A decision here enables no consumer and authorizes nothing
(`operationally_authorized` is always False).
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
import r08v8_support as t
import s01_support as s
from registry_successor import common as c
from registry_successor import verify as v
from registry_successor.engine import profiles
from registry_successor.engine import record as record_e
from registry_successor.engine import selection as selection_e
from registry_successor.v8_decision import verify_and_decide_v8

pytestmark = pytest.mark.skipif(not t.HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

ANC, AGE, TOL = t.ANCHOR, t.MAXAGE, t.TOL
FAMS = pytest.mark.parametrize("fam", t.FAMILIES, ids=["anchor", "max_age", "tolerance"])
assert_refused = t.assert_refused
V8 = profiles.V8
INT_MAX = 2147483647


def validate(text):
    return record_e.validate_record_text(V8, text)


def rec_(fam, pl=None, **over):
    return t.record(pl, family=over.pop("family", fam), **over)


def pl(fam, value):
    return {t.FIELDS[fam]: value}


# ---- positive paths with the default fixtures
EXPECT = {ANC: "anchor", AGE: 60, TOL: 0}


@FAMS
def test_valid_selection_narrows_the_caller_and_authorizes_nothing(fam):
    d = t.decide(family=fam)
    assert d.kind == "applied" and d.code is None and d.deny_all is False and d.operationally_authorized is False and d.caller_unchanged is False
    assert d.effective == pl(fam, EXPECT[fam]) and d.detail == "" and d.deny_all_fields == ()


@FAMS
def test_signed_path_applies_the_family_specific_composition(fam):
    cases = {ANC: [("no_change", "no_change", "no_change", ""), ("no_change", "anchor", "anchor", ""), ("anchor", "no_change", "anchor", "registry_value_not_narrowing:anchor_deadline_to_inputs"),
                   ("anchor", "anchor", "anchor", "")],
             AGE: [(300, 60, 60, ""), (60, 300, 60, "registry_value_not_narrowing:observation_max_age_seconds"), (60, 60, 60, ""), (INT_MAX, 1, 1, ""), (1, INT_MAX, 1, "registry_value_not_narrowing:observation_max_age_seconds")],
             TOL: [(5, 0, 0, ""), (0, 5, 0, "registry_value_not_narrowing:observation_clock_tolerance_seconds"), (5, 5, 5, ""), (INT_MAX, 0, 0, ""), (0, 0, 0, "")]}
    for host, reg, eff, detail in cases[fam]:
        d = t.decide(rec=rec_(fam, pl(fam, reg)), cl=pl(fam, host))
        assert d.kind == "applied" and d.effective == pl(fam, eff) and d.detail == detail, (host, reg)


def test_exhaustive_never_looser_than_the_caller_for_the_anchor_pair():
    for h, g in itertools.product(("anchor", "no_change"), repeat=2):
        d = t.decide(family=ANC, rec=rec_(ANC, pl(ANC, g)), cl=pl(ANC, h))
        assert d.kind == "applied" and (d.effective[t.FIELDS[ANC]] == "anchor") == ("anchor" in (h, g))


@pytest.mark.parametrize("fam,grid", [(AGE, (1, 2, 60, 300, INT_MAX)), (TOL, (0, 1, 5, 60, INT_MAX))], ids=["max_age", "tolerance"])
def test_exhaustive_signed_min_over_a_grid(fam, grid):
    for host, reg in itertools.product(grid, repeat=2):
        d = t.decide(rec=rec_(fam, pl(fam, reg)), cl=pl(fam, host))
        assert d.kind == "applied" and d.effective == pl(fam, min(host, reg))


# ---- invalid callers
BAD_CALLERS = {
    ANC: [{}, 5, "anchor", {t.FIELDS[ANC]: True}, {t.FIELDS[ANC]: False}, {t.FIELDS[ANC]: "x"}, {t.FIELDS[ANC]: None}, {t.FIELDS[ANC]: 1}, {t.FIELDS[ANC]: "Anchor"},
          {t.FIELDS[ANC]: "anchor", "x": 1}, {"terminal_revocation": "on"}, {"class_irreversible": {"class-a": "irreversible"}}],
    AGE: [{}, 5, "60", {t.FIELDS[AGE]: True}, {t.FIELDS[AGE]: 0}, {t.FIELDS[AGE]: -1}, {t.FIELDS[AGE]: "60"}, {t.FIELDS[AGE]: 60.0}, {t.FIELDS[AGE]: None},
          {t.FIELDS[AGE]: INT_MAX + 1}, {t.FIELDS[AGE]: 10 ** 12}, {t.FIELDS[AGE]: 60, "x": 1}, {"max_age_seconds": 60}, {t.FIELDS[TOL]: 5}],
    TOL: [{}, 5, "5", {t.FIELDS[TOL]: True}, {t.FIELDS[TOL]: False}, {t.FIELDS[TOL]: -1}, {t.FIELDS[TOL]: "5"}, {t.FIELDS[TOL]: 5.0}, {t.FIELDS[TOL]: None},
          {t.FIELDS[TOL]: INT_MAX + 1}, {t.FIELDS[TOL]: 10 ** 12}, {t.FIELDS[TOL]: 5, "x": 1}, {"clock_tolerance_seconds": 5}, {t.FIELDS[AGE]: 60}],
}


@pytest.mark.parametrize("fam,bad", [(f, b) for f in t.FAMILIES for b in BAD_CALLERS[f]], ids=lambda x: x if isinstance(x, str) and x.startswith("f5") else None)
def test_invalid_caller_refuses_required(fam, bad):
    assert_refused(t.decide(family=fam, cl=bad), "composition_caller_invalid")


@FAMS
def test_missing_caller_refuses_required(fam):
    ad = t.ev.Ed25519Verifier()
    rec = rec_(fam)
    assert_refused(verify_and_decide_v8("required", None, r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission),
                   "composition_caller_invalid")


def test_a_host_value_above_the_token_range_refuses_the_whole_caller_for_both_int_families():
    assert_refused(t.decide(family=AGE, cl=pl(AGE, INT_MAX + 1)), "composition_caller_invalid")
    assert_refused(t.decide(family=TOL, cl=pl(TOL, 2 ** 40)), "composition_caller_invalid")


# ---- optional participation
@FAMS
def test_optional_participation_refusal_leaves_the_caller_policy_unchanged_not_an_application(fam):
    rec = rec_(fam)
    sel = r.dumps(t.envelope(t.statement(rec, participation="optional")))
    bad_caller = BAD_CALLERS[fam][3]
    d = t.decide(participation="optional", rec=rec, sel=sel, cl=bad_caller)
    assert d.kind == "overlay_not_applied" and d.code == "composition_caller_invalid" and d.caller_unchanged is True
    assert d.operationally_authorized is False and d.deny_all is False and d.effective == bad_caller
    good = t.caller(fam)
    bad_sig = r.dumps(t.envelope(t.statement(rec, participation="optional"), sk=t.OTHER_SK))
    d3 = t.decide(participation="optional", rec=rec, sel=bad_sig, cl=good)
    assert d3.kind == "overlay_not_applied" and d3.code == "signature_invalid" and d3.caller_unchanged is True and d3.effective == good
    d4 = t.decide(participation="optional", rec=rec, sel=sel, cl=good)
    assert d4.kind == "applied" and d4.effective == pl(fam, EXPECT[fam])


def test_optional_refusal_normalizes_a_well_formed_caller_of_any_v8_family_and_passes_others_through():
    unsigned = "{}"
    for fam, value in ((ANC, "no_change"), (AGE, 300), (TOL, 5)):
        d = t.decide(participation="optional", sel=unsigned, cl=pl(fam, value), family=fam)
        assert d.kind == "overlay_not_applied" and d.effective == pl(fam, value) and d.caller_unchanged is True and d.operationally_authorized is False
    junk = {"zzz": 1}
    d = t.decide(participation="optional", sel=unsigned, cl=junk)
    assert d.effective == junk and d.caller_unchanged is True
    irr_caller = {"class_irreversible": {"class-a": "irreversible"}}  # an earlier family's shape is not normalized by v8
    d = t.decide(participation="optional", sel=unsigned, cl=irr_caller)
    assert d.effective is irr_caller and d.caller_unchanged is True
    # a bool caller for the anchor family is never normalized into a string
    d = t.decide(participation="optional", sel=unsigned, cl={t.FIELDS[ANC]: True})
    assert d.effective == {t.FIELDS[ANC]: True} and d.effective[t.FIELDS[ANC]] is True


# ---- malformed records: validator code and decision refusal
MALFORMED = {
    ANC: [({}, "field_missing"), ({"anchor_deadline_to_inputs": "anchor", "x": 1}, "field_unknown"), ({"other": "anchor"}, "field_unknown"),
          ({"anchor_deadline_to_inputs": True}, "field_type_invalid"), ({"anchor_deadline_to_inputs": False}, "field_type_invalid"),
          ({"anchor_deadline_to_inputs": None}, "field_type_invalid"), ({"anchor_deadline_to_inputs": 1}, "field_type_invalid"),
          ({"anchor_deadline_to_inputs": ["anchor"]}, "field_type_invalid"), ({"anchor_deadline_to_inputs": "false"}, "field_invalid"),
          ({"anchor_deadline_to_inputs": "Anchor"}, "field_invalid"), ({"anchor_deadline_to_inputs": ""}, "field_invalid"),
          ({"terminal_revocation": "on"}, "field_unknown"), ({"class_irreversible": {"class-a": "irreversible"}}, "field_unknown")],
    AGE: [({}, "field_missing"), ({"observation_max_age_seconds": 60, "x": 1}, "field_unknown"), ({"max_age_seconds": 60}, "field_unknown"),
          ({"observation_max_age_seconds": True}, "field_type_invalid"), ({"observation_max_age_seconds": "60"}, "field_type_invalid"),
          ({"observation_max_age_seconds": None}, "field_type_invalid"), ({"observation_max_age_seconds": [60]}, "field_type_invalid"),
          ({"observation_max_age_seconds": 0}, "field_invalid"), ({"observation_max_age_seconds": -1}, "field_invalid"),
          ({"observation_max_age_seconds": 2147483648}, "field_invalid"), ({"observation_clock_tolerance_seconds": 5}, "field_unknown")],
    TOL: [({}, "field_missing"), ({"observation_clock_tolerance_seconds": 5, "x": 1}, "field_unknown"), ({"clock_tolerance_seconds": 5}, "field_unknown"),
          ({"observation_clock_tolerance_seconds": 5, "clock_tolerance_seconds": 5}, "field_unknown"),
          ({"observation_clock_tolerance_seconds": False}, "field_type_invalid"), ({"observation_clock_tolerance_seconds": "5"}, "field_type_invalid"),
          ({"observation_clock_tolerance_seconds": None}, "field_type_invalid"), ({"observation_clock_tolerance_seconds": {}}, "field_type_invalid"),
          ({"observation_clock_tolerance_seconds": -1}, "field_invalid"), ({"observation_clock_tolerance_seconds": 2147483648}, "field_invalid"),
          ({"observation_max_age_seconds": 60}, "field_unknown")],
}


@pytest.mark.parametrize("fam,payload,code", [(f, p, k) for f in t.FAMILIES for p, k in MALFORMED[f]])
def test_malformed_payload_typed_validator_code_and_decision_refusal(fam, payload, code):
    rec = rec_(fam, payload)
    assert validate(r.dumps(rec)).code == code
    assert_refused(t.decide(family=fam, rec=rec, sel=t.selection_text(rec)), "composition_record_invalid")


@FAMS
@pytest.mark.parametrize("literal", ["5.0", "1e3", "NaN", "Infinity", "-Infinity", "0.0", "true", "false", "null", '"x"', "[]", "{}"])
def test_non_integer_literals_never_reach_validation(fam, literal):
    rec = rec_(fam)
    base = r.dumps(rec)
    old = '"%s": %s' % (t.FIELDS[fam], json.dumps(EXPECT[fam]))
    text = base.replace(old, '"%s": %s' % (t.FIELDS[fam], literal))
    assert text != base
    assert not validate(text).ok
    assert validate(text).code in ("json_number_unsupported", "field_type_invalid", "field_invalid")  # a string that is not in the closed vocabulary is field_invalid
    assert_refused(t.decide(family=fam, rec=rec, record_text=text), "composition_record_invalid")


@pytest.mark.parametrize("fam", (AGE, TOL), ids=["max_age", "tolerance"])
def test_huge_integer_literals_are_refused_never_clamped(fam):
    rec = rec_(fam)
    base = r.dumps(rec)
    old = '"%s": %s' % (t.FIELDS[fam], json.dumps(EXPECT[fam]))
    for literal in ("2147483648", "99999999999999999999999999", "-1", "-2147483649"):
        text = base.replace(old, '"%s": %s' % (t.FIELDS[fam], literal))
        assert not validate(text).ok
        assert_refused(t.decide(family=fam, rec=rec, record_text=text), "composition_record_invalid")


@FAMS
def test_duplicate_key_and_non_json_records_refuse(fam):
    rec = rec_(fam)
    old = '"%s": %s' % (t.FIELDS[fam], json.dumps(EXPECT[fam]))
    text = r.dumps(rec).replace(old, old + ", " + old)
    assert text != r.dumps(rec)
    assert validate(text).code == "json_duplicate_key"
    assert validate("not json").code == "json_malformed"
    assert validate(None).code == "input_not_text"
    assert_refused(t.decide(family=fam, rec=rec, record_text=text), "composition_record_invalid")


@FAMS
def test_record_supersession_is_validated(fam):
    rec1 = rec_(fam)
    ok = rec_(fam, record_version=2, supersedes={"record_id": rec1["record_id"], "record_version": 1, "record_digest": rec1["record_digest"]})
    assert validate(r.dumps(ok)).ok
    for bad in ({"record_id": "other-record", "record_version": 1, "record_digest": rec1["record_digest"]},
                {"record_id": rec1["record_id"], "record_version": 2, "record_digest": rec1["record_digest"]},
                {"record_id": rec1["record_id"], "record_version": 1, "record_digest": "nope"}):
        assert validate(r.dumps(rec_(fam, record_version=2, supersedes=bad))).code == "supersession_invalid", bad


@FAMS
def test_envelope_kind_and_the_record_digest_alone_are_checked(fam):
    rec = rec_(fam)
    env = t.envelope(t.statement(rec))
    env["kind"] = "other"
    assert selection_e.parse_selection_envelope(V8, r.dumps(env)).code == "kind_unsupported"
    assert_refused(t.decide(family=fam, rec=rec, sel=r.dumps(env)), "kind_unsupported")
    bad = dict(rec, record_digest="sha256:" + "0" * 64)
    assert validate(r.dumps(bad)).code == "digest_mismatch"
    assert_refused(t.decide(family=fam, rec=bad, sel=t.selection_text(rec)), "composition_record_invalid")


@FAMS
def test_record_top_level_checks(fam):
    assert validate(r.dumps(rec_(fam))).ok
    assert validate(r.dumps(rec_(fam, kind="selection"))).code == "kind_unsupported"
    assert validate(r.dumps(rec_(fam, non_authorizing=False))).code == "field_invalid"
    assert validate(r.dumps(rec_(fam, record_version=0))).code == "field_invalid"


# ---- families
OTHER_FAMILIES = ("f5-action-class-irreversibility-policy", "f1abcd-local-execution-limits", "f1abc-local-execution-limits", "f1ab-local-execution-allowlist", c.FAMILY_F1A,
                  "f4-control-plane-age-bounds", "f5-action-class-age-bounds", "f5-action-class-unreadable-policy", "f5-action-class-revocation-assurance-policy",
                  "f5-terminal-revocation-enablement-policy", "unknown-family", "anchor_deadline_to_inputs", "ObservationPolicy.max_age_seconds",
                  "ObservationPolicy.clock_tolerance_seconds", "f5-anchor-deadline-to-inputs-policy ", "F5-OBSERVATION-MAX-AGE-POLICY")


@pytest.mark.parametrize("fam_id", OTHER_FAMILIES)
def test_every_other_family_is_unsupported_in_the_v8_table_irreversibility_included(fam_id):
    rec = rec_(AGE, family=fam_id)
    assert validate(r.dumps(rec)).code == "family_unsupported"
    stmt = r.make_statement_v2(rec, family=fam_id)
    text = r.dumps(s.envelope(stmt, domain=t.V8_DOMAIN, contract="r08-v8", signature=t.sign(stmt), pub=t.PK))
    assert selection_e.parse_selection_envelope(V8, text).code == "family_unsupported"
    assert_refused(t.decide(rec=rec, sel=text), "family_unsupported")


def test_selection_naming_another_v8_family_than_the_record_is_refused():
    for rec_fam, sel_fam in itertools.permutations(t.FAMILIES, 2):
        rec = rec_(rec_fam)
        stmt = r.make_statement_v2(rec, family=sel_fam)
        d = t.decide(family=rec_fam, rec=rec, sel=r.dumps(t.envelope(stmt)))
        assert d.kind == "required_policy_unavailable" and d.effective is None
        assert d.code in ("record_identity_mismatch", "family_unsupported", "evaluator_mismatch"), d.code


def test_a_record_of_one_family_with_the_payload_of_another_refuses():
    assert_refused(t.decide(rec=rec_(AGE, pl(TOL, 5)), sel=t.selection_text(rec_(AGE, pl(TOL, 5)))), "composition_record_invalid")
    assert_refused(t.decide(rec=rec_(TOL, pl(AGE, 5)), sel=t.selection_text(rec_(TOL, pl(AGE, 5)))), "composition_record_invalid")
    assert_refused(t.decide(rec=rec_(ANC, pl(AGE, 5)), sel=t.selection_text(rec_(ANC, pl(AGE, 5)))), "composition_record_invalid")


# ---- wrong tenant / scope / consumer / operation
CONTEXTS = [
    (c.ExpectedContext("other-consumer", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch"),
]


@pytest.mark.parametrize("fam,ctx,code", [(f, x, k) for f in t.FAMILIES for x, k in CONTEXTS])
def test_wrong_tenant_scope_consumer_operation_refuse(fam, ctx, code):
    assert_refused(t.decide(family=fam, ctx=ctx), code)


@FAMS
def test_missing_context_refuses(fam):
    ad = t.ev.Ed25519Verifier()
    rec = rec_(fam)
    assert_refused(verify_and_decide_v8("required", t.caller(fam), r.dumps(rec), t.selection_text(rec), None, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission), "selection_scope_mismatch")


@FAMS
def test_signer_without_exact_authority_is_not_authorized(fam):
    for other in (v.AuthorityGrant("consumer-test", "tenant-other", "inst-a", "domain-a", "op-test"), v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"),
                  v.AuthorityGrant("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test")):
        tr_ = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", t.PK, (other,)),))
        assert_refused(t.decide(family=fam, trust=tr_), "issuer_not_authorized")


# ---- signature
@FAMS
def test_forged_wrong_key_missing_and_noncanonical_signatures_refuse(fam):
    rec = rec_(fam)
    stmt = t.statement(rec)
    bad = bytearray(base64.b64decode(t.sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, domain=t.V8_DOMAIN, contract="r08-v8", signature=base64.b64encode(bytes(bad)).decode(), pub=t.PK))
    assert_refused(t.decide(family=fam, rec=rec, sel=forged), "signature_invalid")
    assert_refused(t.decide(family=fam, rec=rec, sel=t.selection_text(rec, sk=t.OTHER_SK)), "signature_invalid")
    unsigned = r.dumps(s.envelope(stmt, domain=t.V8_DOMAIN, contract="r08-v8", signed=False))
    assert_refused(t.decide(family=fam, rec=rec, sel=unsigned), "signature_missing")
    good = t.sign(stmt)
    for noncanon in (good + "\n", good.replace("=", "") if "=" in good else good + "=", good[:-4], "!" + good[1:], good.replace("=", "").lower()):
        sel = r.dumps(s.envelope(stmt, domain=t.V8_DOMAIN, contract="r08-v8", signature=noncanon, pub=t.PK))
        d = t.decide(family=fam, rec=rec, sel=sel)
        assert d.kind == "required_policy_unavailable" and d.effective is None and d.code == "signature_invalid", (noncanon, d.code)


@FAMS
def test_signature_by_an_unknown_key_id_is_untrusted(fam):
    rec = rec_(fam)
    stmt = t.statement(rec)
    sel = r.dumps(s.envelope(stmt, domain=t.V8_DOMAIN, contract="r08-v8", key_id="key-unknown", signature=t.sign(stmt), pub=t.PK))
    assert_refused(t.decide(family=fam, rec=rec, sel=sel), "issuer_untrusted")


@FAMS
def test_label_swap_a_statement_signed_over_another_domain_fails_signature(fam):
    rec = rec_(fam)
    stmt = t.statement(rec)
    for domain in (s.V2_DOMAIN, s.V1_DOMAIN, b"", t.V7_DOMAIN, t.V6_DOMAIN, t.V5_DOMAIN, b"ocs-reg/r08-v4/selection\n", b"ocs-reg/r08-v3/selection\n", b"ocs-reg/r08-v8/other\n",
                   b"ocs-reg/r08-v8/effective-policy\n", b"ocs-reg/r08-v8/selection", b"ocs-reg/r08-v8/selection\n\n"):
        sel = r.dumps(s.envelope(stmt, domain=domain, contract="r08-v8", signature=t.sign(stmt, domain=domain), pub=t.PK))
        assert_refused(t.decide(family=fam, rec=rec, sel=sel), "signature_invalid")


# ---- digests and pins
@FAMS
def test_altered_record_statement_and_pins_refuse(fam):
    rec = rec_(fam)
    sel = t.selection_text(rec)
    tampered = copy.deepcopy(rec)
    tampered["payload"][t.FIELDS[fam]] = {ANC: "no_change", AGE: INT_MAX, TOL: INT_MAX}[fam]  # loosen the Registry value without resealing
    assert validate(r.dumps(tampered)).code == "digest_mismatch"
    assert_refused(t.decide(family=fam, rec=tampered, sel=sel), "composition_record_invalid")
    resealed = r.seal_record(tampered)  # loosen and reseal: not the record the signed selection pins
    assert_refused(t.decide(family=fam, rec=resealed, sel=sel), "record_digest_mismatch")
    stmt = t.statement(rec)
    env = t.envelope(stmt)
    env["statement_digest"] = "sha256:" + "0" * 64
    assert_refused(t.decide(family=fam, rec=rec, sel=r.dumps(env)), "digest_mismatch")
    assert_refused(t.decide(family=fam, rec=rec_(fam, record_version=2), sel=sel), "record_identity_mismatch")
    assert_refused(t.decide(family=fam, rec=rec_(fam, record_id="f5-other-record"), sel=sel), "record_identity_mismatch")


@FAMS
def test_evaluator_mismatch_between_selection_and_record(fam):
    rec = rec_(fam)
    stmt = t.statement(rec)
    stmt["evaluator"] = dict(stmt["evaluator"], source_blob_id="1" * 40)
    assert_refused(t.decide(family=fam, rec=rec, sel=r.dumps(t.envelope(stmt))), "evaluator_mismatch")


@FAMS
def test_no_selection_or_record_refuses(fam):
    ad = t.ev.Ed25519Verifier()
    rec = rec_(fam)
    assert_refused(verify_and_decide_v8("required", t.caller(fam), r.dumps(rec), None, s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission), "selection_missing")
    d = verify_and_decide_v8("required", t.caller(fam), None, t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "required_policy_unavailable" and d.effective is None


# ---- lifecycle: withdrawn, revoked key, revoked selection, stale, expired
@FAMS
def test_withdrawn_selection_refuses(fam):
    rec = rec_(fam)
    wd = s.withdraw_statement(t.statement(rec))
    assert_refused(t.decide(family=fam, rec=rec, sel=r.dumps(t.envelope(wd))), "selection_withdrawn")
    assert_refused(t.decide(family=fam, rec=rec, sel=r.dumps(s.envelope(wd, domain=t.V8_DOMAIN, contract="r08-v8", signed=False))), "signature_missing")
    assert_refused(t.decide(family=fam, rec=rec, sel=r.dumps(t.envelope(wd, sk=t.OTHER_SK))), "signature_invalid")  # wrong key: a signature failure, never a withdrawal


@FAMS
def test_key_revocation_selection_revocation_staleness_expiry_and_not_yet_effective_refuse(fam):
    rec = rec_(fam)
    assert_refused(t.decide(family=fam, rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")
    assert t.decide(family=fam, rec=rec, trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({"some-other-key"}))).kind == "applied"
    assert_refused(t.decide(family=fam, rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")
    assert t.decide(family=fam, rec=rec, trust=s.trust(pub=t.PK, revoked_selections=frozenset({("sel-test-1", 2)}))).kind == "applied"
    assert_refused(t.decide(family=fam, rec=rec, trust=s.trust(pub=t.PK, min_epochs=(("sel-test-1", 2),))), "selection_epoch_stale")
    late = r.NOW + datetime.timedelta(days=3)
    assert_refused(t.decide(family=fam, rec=rec, now=late, trust=s.trust(pub=t.PK, valid_until="2026-12-31T00:00:00Z")), "selection_expired")
    assert_refused(t.decide(family=fam, rec=rec, trust=s.trust(pub=t.PK, valid_until="2026-10-25T06:00:00Z")), "trust_snapshot_expired")
    assert_refused(t.decide(family=fam, rec=rec, now=r.NOW - datetime.timedelta(days=3)), "selection_not_yet_effective")
    ad = t.ev.Ed25519Verifier()
    assert_refused(verify_and_decide_v8("required", t.caller(fam), r.dumps(rec), t.selection_text(rec), s.CTX, s.trust(pub=t.PK), ad, None, ad.key_admission), "time_unavailable")
    assert_refused(t.decide(participation="required", family=fam, rec=rec, sel=t.selection_text(rec, participation="optional")), "participation_mismatch")


def test_a_revoked_key_refuses_even_for_an_otherwise_valid_in_range_tolerance_zero():
    rec = rec_(TOL, pl(TOL, 0))
    assert t.decide(rec=rec, cl=pl(TOL, 5)).effective == pl(TOL, 0)
    assert_refused(t.decide(rec=rec, cl=pl(TOL, 5), trust=s.trust(pub=t.PK, revoked_key_ids=frozenset({s.KEY_ID}))), "issuer_key_revoked")


@FAMS
def test_trust_snapshot_missing_unverifier_and_bad_key(fam):
    rec = rec_(fam)
    ad = t.ev.Ed25519Verifier()
    args = ("required", t.caller(fam), r.dumps(rec), t.selection_text(rec), s.CTX)
    assert_refused(verify_and_decide_v8(*args, None, ad, r.NOW), "trust_snapshot_missing")
    assert_refused(verify_and_decide_v8(*args, s.trust(pub=t.PK), None, r.NOW), "verifier_unavailable")
    assert_refused(verify_and_decide_v8(*args, s.trust(pub=bytes.fromhex("01" + "00" * 31)), ad, r.NOW), "trust_snapshot_invalid")


def test_bad_participation_value_refuses():
    for bad in ("sometimes", None, 1, b"required"):
        d = t.decide(participation=bad)
        assert d.kind == "required_policy_unavailable" and d.code == "participation_mismatch" and d.effective is None


@FAMS
def test_operationally_authorized_is_false_and_deny_all_never_set_on_every_outcome(fam):
    rec = rec_(fam)
    outcomes = [t.decide(family=fam, rec=rec), t.decide(family=fam, rec=rec, cl={}), t.decide(family=fam, rec=rec, sel="{}"),
                t.decide(participation="optional", family=fam, rec=rec, sel="{}")]
    assert all(o.operationally_authorized is False and o.deny_all is False and o.deny_all_fields == () for o in outcomes)
    assert all(o.effective is None for o in outcomes if o.kind == "required_policy_unavailable")


# ---- canonical serialization pins and the signed vector
@FAMS
def test_record_digest_and_signing_input_are_the_canonical_forms(fam):
    rec = rec_(fam)
    body = {k: v_ for k, v_ in rec.items() if k != "record_digest"}
    indep = "sha256:" + hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
    assert rec["record_digest"] == indep
    stmt = t.statement(rec)
    assert selection_e.signing_input(V8, stmt) == b"ocs-reg/r08-v8/selection\n" + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert validate(json.dumps(dict(reversed(list(rec.items()))), indent=3)).ok


VECTOR = json.loads(open(os.path.join(os.path.dirname(__file__), "vectors", "r08v8", "signed_selection_vector.json")).read())


@FAMS
def test_signed_vector_is_deterministic_and_verifies(fam):
    vec = VECTOR[fam]
    rec, stmt = vec["record"], vec["statement"]
    assert rec == t.record(family=fam) and stmt == t.statement(t.record(family=fam))
    assert selection_e.signing_input(V8, stmt).hex() == vec["signing_input_hex"]
    assert t.sign(stmt) == vec["signature"] == base64.b64encode(bytes.fromhex(vec["signature_hex"])).decode()
    assert t.nb.crypto_sign_open(bytes.fromhex(vec["signature_hex"]) + bytes.fromhex(vec["signing_input_hex"]), t.PK) == bytes.fromhex(vec["signing_input_hex"])
    d = t.decide(family=fam, rec=rec, sel=json.dumps(vec["envelope"]), cl=vec["caller"])
    assert d.kind == "applied" and d.effective == vec["effective"]
    assert set(VECTOR) == set(t.FAMILIES)
