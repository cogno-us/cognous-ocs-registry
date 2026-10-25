"""R08-S01 regression tests for the five PR #19 review findings, using the real parse -> verify -> decide pipeline.
DEVELOPER-TESTED only; not independent qualification. The signature verifier is a test double, not cryptography."""
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import decision, record, selection, verify  # noqa: E402
from test_r08_spec_conformance import CTX, KEY, PK, grant, trust  # noqa: E402

CALLER = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs", "s3"], "allowed_units": ["unit-a", "unit-b", "unit-c"]}


def rec_of(obj):
    return record.validate_record_text(r.dumps(obj))


def sel_of(stmt, **kw):
    return selection.parse_selection_envelope(r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=PK, **kw)))


def run(stmt, rec_obj, participation="required", with_record=True, trust_obj=None):
    rr = rec_of(rec_obj)
    rep = verify.verify_selection(sel_of(stmt), CTX, trust_obj or trust(), r.FakeVerifier(), r.NOW, rr if with_record else None)
    return rr, rep, decision.decide_policy(participation, CALLER, rr, rep)


def test_baseline_pipeline_applies():
    _, rep, d = run(r.make_statement(), r.make_record())
    assert rep.ok and d.kind == "applied"


def test_1_record_swap_is_refused():
    narrow = r.make_record()
    broad = r.make_record(payload={"allowed_actions": ["read-file", "write-file"], "allowed_adapters": ["local-fs", "s3"], "allowed_units": ["unit-a", "unit-b", "unit-c"]})
    _, rep, _ = run(r.make_statement(narrow), narrow)
    d = decision.decide_policy("required", CALLER, rec_of(broad), rep)
    assert d.kind == "required_policy_unavailable" and d.code in {"record_digest_mismatch", "record_identity_mismatch"}
    d = decision.decide_policy("optional", CALLER, rec_of(broad), verify.verify_selection(sel_of(r.make_statement(narrow, participation="optional")), CTX, trust(), r.FakeVerifier(), r.NOW, rec_of(narrow)))
    assert d.kind == "overlay_not_applied"


def test_1_missing_record_binding_is_refused():
    rec_obj = r.make_record()
    rr, rep, d = run(r.make_statement(rec_obj), rec_obj, with_record=False)
    assert d.kind == "required_policy_unavailable" and d.code == "record_identity_mismatch"


def test_2_payload_mutated_after_validation_is_refused():
    rec_obj = r.make_record()
    rr, rep, _ = run(r.make_statement(rec_obj), rec_obj)
    rr.record["payload"]["allowed_units"].append("unit-z")  # nested content is mutable; digests are now stale
    d = decision.decide_policy("required", CALLER, rr, rep)
    assert d.kind == "required_policy_unavailable" and d.code == "digest_mismatch"
    rep2 = verify.verify_selection(sel_of(r.make_statement(rec_obj)), CTX, trust(), r.FakeVerifier(), r.NOW, rr)
    assert not rep2.ok and rep2.code == "digest_mismatch"


@pytest.mark.parametrize("selection_part,operation_part", [("optional", "required"), ("required", "optional")])
def test_3_participation_mismatch_is_refused(selection_part, operation_part):
    rec_obj = r.make_record()
    _, rep, d = run(r.make_statement(rec_obj, participation=selection_part), rec_obj, participation=operation_part)
    assert rep.ok and rep.participation == selection_part
    assert d.code == "participation_mismatch"
    assert d.kind == ("required_policy_unavailable" if operation_part == "required" else "overlay_not_applied")


def test_4_chain_with_expired_middle_selection_resolves():
    a = sel_of(r.make_statement(effective={"valid_from": "2026-10-20T00:00:00Z", "valid_until": "2026-10-30T00:00:00Z"}, epoch=1))

    def ref(o, dec):
        return {"selection_id": o.statement["selection_id"], "epoch": o.statement["epoch"], "statement_digest": o.statement_digest, "decision_ref": dec}
    b = sel_of(r.make_statement(epoch=2, supersedes=ref(a, "decision-2"),
                                effective={"valid_from": "2026-10-20T00:00:00Z", "valid_until": "2026-10-21T00:00:00Z"}))
    cc = sel_of(r.make_statement(epoch=3, supersedes=ref(b, "decision-3"),
                                 effective={"valid_from": "2026-10-25T00:00:00Z", "valid_until": "2026-10-30T00:00:00Z"}))
    for order in ([a, b, cc], [cc, b, a], [b, a, cc]):
        res = selection.resolve_effective(order, CTX, r.NOW)
        assert res.ok and res.selected is cc, order
    # the in-window older statement without the chain still conflicts
    assert selection.resolve_effective([a, cc], CTX, r.NOW).code == "selection_conflict"


def two_issuer_trust(second_grant_op):
    ok = verify.IssuerEntry(key_id="key-good", issuer_id="issuer-good", alg="ed25519", public_key=b"pk-good", authority=(grant(),))
    bad = verify.IssuerEntry(key_id="key-bad", issuer_id="issuer-bad", alg="ed25519", public_key=b"pk-bad", authority=(grant(operation=second_grant_op),))
    return ok, bad


@pytest.mark.parametrize("bad_first", [True, False])
def test_5_signature_order_does_not_change_authority(bad_first):
    from registry_successor.selection import signing_input
    rec_obj = r.make_record()
    stmt = r.make_statement(rec_obj)
    sig = lambda kid, pk: {"alg": "ed25519", "key_id": kid, "signature": r.fake_signature(pk, signing_input(stmt))}
    sigs = [sig("key-bad", b"pk-bad"), sig("key-good", b"pk-good")]
    if not bad_first:
        sigs.reverse()
    env = r.make_envelope(stmt, signed=False)
    env["signatures"] = sigs
    sel = selection.parse_selection_envelope(r.dumps(env))
    assert sel.ok
    ok, bad = two_issuer_trust("some-other-op")
    rep = verify.verify_selection(sel, CTX, trust(issuers=(ok, bad)), r.FakeVerifier(), r.NOW, rec_of(rec_obj))
    assert rep.ok, (rep.code, rep.layers)
    assert rep.issuer_id == "issuer-good"
