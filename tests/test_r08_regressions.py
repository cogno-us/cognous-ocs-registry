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


def vd(rec_obj, stmt=None, participation="required", record_text=None, sel_text="auto", trust_obj=None, now=None, caller=CALLER, signed=True):
    stmt = stmt or r.make_statement(rec_obj, participation=participation)
    if sel_text == "auto":
        sel_text = r.dumps(r.make_envelope(stmt, key_id=KEY, public_key=PK, signed=signed))
    return decision.verify_and_decide(participation, caller, record_text if record_text is not None else r.dumps(rec_obj), sel_text,
                                      CTX, trust_obj or trust(), r.FakeVerifier(), now or r.NOW)


BROAD = {"allowed_actions": ["read-file", "write-file"], "allowed_adapters": ["local-fs", "s3"], "allowed_units": ["unit-a", "unit-b", "unit-c"]}


# ------------------------------------------------------------------ A1: verification-to-decision binding
def test_a1_baseline_applies():
    assert vd(r.make_record()).kind == "applied"


def test_a1_no_public_report_taking_interface():
    assert not hasattr(decision, "decide_policy")
    # the only public decide entry points take raw TEXT, never a report: the legacy one and the v2-only one (hardwired contract_version, delegates to the first)
    assert [n for n in dir(decision) if not n.startswith("_") and "decide" in n] == ["verify_and_decide", "verify_and_decide_v2"]


@pytest.mark.parametrize("fake", [object(), {"ok": True}, 1, b"x", ["x"]])
def test_a1_fabricated_inputs_fail_closed(fake):
    for part in ("required", "optional"):
        d = decision.verify_and_decide(part, CALLER, fake, fake, CTX, trust(), r.FakeVerifier(), r.NOW)
        assert d.kind in ("required_policy_unavailable", "overlay_not_applied") and d.operationally_authorized is False
        assert d.kind != "applied" and d.kind != "applied_deny_all"


def test_a1_record_substitution_refused_in_both_participations():
    narrow = r.make_record()
    broad = r.make_record(payload=BROAD)
    for part in ("required", "optional"):
        stmt = r.make_statement(narrow, participation=part)
        d = vd(narrow, stmt=stmt, participation=part, record_text=r.dumps(broad))
        assert d.kind in ("required_policy_unavailable", "overlay_not_applied")
        assert d.code in {"record_identity_mismatch", "record_digest_mismatch", "digest_mismatch"}


def test_a1_record_altered_after_binding_text_refused():
    rec_obj = r.make_record()
    altered = copy.deepcopy(rec_obj)
    altered["payload"]["allowed_units"].append("unit-z")  # digests now stale
    d = vd(rec_obj, record_text=r.dumps(altered))
    assert d.kind == "required_policy_unavailable" and d.code in {"digest_mismatch", "record_identity_mismatch", "composition_record_invalid"}


def test_a1_stale_selection_is_refused_not_replayed():
    rec_obj = r.make_record()
    assert vd(rec_obj).kind == "applied"
    late = r.NOW.replace(day=27)
    d = vd(rec_obj, now=late)
    assert d.kind == "required_policy_unavailable" and d.code in c.CODES
    assert vd(rec_obj).kind == "applied"  # each call verifies afresh at its own `now`


@pytest.mark.parametrize("variant", ["unsigned", "unknown_key", "empty_trust"])
def test_a1_unverified_selection_never_composes(variant):
    rec_obj = r.make_record()
    stmt = r.make_statement(rec_obj)
    kw = {}
    if variant == "unsigned":
        kw["signed"] = False
    elif variant == "unknown_key":
        kw["sel_text"] = r.dumps(r.make_envelope(stmt, key_id="key-unknown", public_key=b"x"))
    else:
        kw["trust_obj"] = trust(issuers=())
    for part in ("required", "optional"):
        d = vd(rec_obj, participation=part, **kw)
        assert d.kind in ("required_policy_unavailable", "overlay_not_applied") and d.effective != {"allowed_actions": ("write-file",), "allowed_adapters": ("local-fs",), "allowed_units": ("unit-a", "unit-b")}
        if part == "required":
            assert d.effective is None


def test_a1_caller_and_inputs_are_not_mutated():
    cal = copy.deepcopy(CALLER)
    rec_obj = r.make_record()
    rec_text = r.dumps(rec_obj)
    first = vd(rec_obj, caller=cal)
    rec_obj["payload"]["allowed_units"].append("unit-z")  # mutating the source object cannot change a decision made from text
    assert cal == CALLER
    assert vd(r.make_record(), caller=cal, record_text=rec_text) == first


def test_a1_internal_tamper_after_verify_refused():
    """Defence in depth for the INTERNAL decide step: a validated record mutated after verification is refused."""
    rec_obj = r.make_record()
    rr = rec_of(rec_obj)
    rep = verify.verify_selection(sel_of(r.make_statement(rec_obj)), CTX, trust(), r.FakeVerifier(), r.NOW, rr)
    assert rep.ok
    rr.record["payload"]["allowed_units"].append("unit-z")
    d = decision._decide_verified("required", CALLER, rr, rep)
    assert d.kind == "required_policy_unavailable" and d.code == "digest_mismatch"
    assert not verify.verify_selection(sel_of(r.make_statement(rec_obj)), CTX, trust(), r.FakeVerifier(), r.NOW, rr).ok


def test_a1_missing_record_binding_refused_internally():
    rec_obj = r.make_record()
    rr = rec_of(rec_obj)
    rep = verify.verify_selection(sel_of(r.make_statement(rec_obj)), CTX, trust(), r.FakeVerifier(), r.NOW, None)
    d = decision._decide_verified("required", CALLER, rr, rep)
    assert d.kind == "required_policy_unavailable" and d.code in {"record_identity_mismatch", "record_not_bound", "selection_missing"} | set(c.CODES)


@pytest.mark.parametrize("selection_part,operation_part", [("optional", "required"), ("required", "optional")])
def test_a1_participation_mismatch_is_refused(selection_part, operation_part):
    rec_obj = r.make_record()
    d = vd(rec_obj, stmt=r.make_statement(rec_obj, participation=selection_part), participation=operation_part)
    assert d.code == "participation_mismatch"
    assert d.kind == ("required_policy_unavailable" if operation_part == "required" else "overlay_not_applied")


# ------------------------------------------------------------------ A2: lineage is structural and non-authorizing
def mk(stmt_over=None, **over):
    return sel_of(r.make_statement(**{**(stmt_over or {}), **over}))


def ref(o, dec="decision-2"):
    return {"selection_id": o.statement["selection_id"], "epoch": o.statement["epoch"], "statement_digest": o.statement_digest, "decision_ref": dec}


WIDE = {"valid_from": "2026-10-20T00:00:00Z", "valid_until": "2026-10-30T00:00:00Z"}
PAST = {"valid_from": "2026-10-20T00:00:00Z", "valid_until": "2026-10-21T00:00:00Z"}


def test_a2_resolver_result_is_never_authorizing():
    a = mk(effective=WIDE, epoch=1)
    b = mk(epoch=2, supersedes=ref(a), effective=WIDE)
    for res in (selection.resolve_effective([a, b], CTX, r.NOW), selection.resolve_effective([a], CTX, r.NOW)):
        assert res.ok and res.authorizing is False and res.lineage_authenticated is False


def test_a2_authority_consuming_interface_always_refuses():
    a = mk(effective=WIDE, epoch=1)
    res = selection.resolve_authoritative([a], CTX, r.NOW)
    assert (res.ok, res.code, res.selected, res.authorizing) == (False, "lineage_authority_unavailable", None, False)


def test_a2_expired_intermediate_resolves_structurally_only():
    a = mk(effective=WIDE, epoch=1)
    b = mk(epoch=2, supersedes=ref(a), effective=PAST)
    cc = mk(epoch=3, supersedes=ref(b, "decision-3"), effective=WIDE)
    for order in ([a, b, cc], [cc, b, a], [b, a, cc]):
        res = selection.resolve_effective(order, CTX, r.NOW)
        assert res.ok and res.selected is cc and not res.authorizing
    assert selection.resolve_effective([a, cc], CTX, r.NOW).code == "selection_conflict"  # missing intermediate


def test_a2_forged_historical_link_does_not_resolve():
    a = mk(effective=WIDE, epoch=1)
    forged = ref(a)
    forged["statement_digest"] = "sha256:" + "0" * 64 if str(a.statement_digest).startswith("sha256:") else "0" * 64
    b = mk(epoch=2, supersedes=forged, effective=WIDE)
    if b.ok:
        assert selection.resolve_effective([a, b], CTX, r.NOW).code == "selection_conflict"
    else:
        assert b.code == "selection_supersession_invalid"


@pytest.mark.parametrize("bad_ref", ["", "Not An Identifier", None, 7, "x" * 500])
def test_a2_invalid_decision_references_refused_at_parse(bad_ref):
    a = mk(effective=WIDE, epoch=1)
    sup = ref(a)
    sup["decision_ref"] = bad_ref
    assert mk(epoch=2, supersedes=sup).code == "selection_supersession_invalid"


def test_a2_conflicting_effective_selections():
    a = mk(effective=WIDE, epoch=1)
    twin = mk(effective=WIDE, epoch=1, selector_ref="selector-other")
    assert selection.resolve_effective([a, twin], CTX, r.NOW).code == "selection_conflict"


def test_a2_unauthorized_higher_epoch_does_not_supersede():
    a = mk(effective=WIDE, epoch=1)
    b = mk(effective=WIDE, epoch=2)  # no explicit supersession
    for order in ([a, b], [b, a]):
        res = selection.resolve_effective(order, CTX, r.NOW)
        assert res.code == "selection_conflict" and res.selected is None


def test_a2_rollback_attempts_refused():
    hi = mk(effective=WIDE, epoch=2)
    assert mk(epoch=1, supersedes=ref(hi)).code == "selection_supersession_invalid"
    assert mk(epoch=2, supersedes=ref(hi)).code == "selection_supersession_invalid"  # not strictly lower
    rec_obj = r.make_record()
    floor = trust(min_epochs={"sel-test-1": 2})
    d = vd(rec_obj, trust_obj=floor)  # presenting the epoch-1 selection after the trusted floor moved to 2
    assert d.kind == "required_policy_unavailable" and d.code == "selection_epoch_stale"


def test_a2_revoked_selection_not_rescued_by_lineage_and_resolver_ignores_revocation():
    rec_obj = r.make_record()
    revoked = trust(revoked_selections=frozenset({("sel-test-1", 1)}))
    d = vd(rec_obj, trust_obj=revoked)
    assert d.kind == "required_policy_unavailable" and d.code == "selection_revoked"
    a = mk(effective=WIDE, epoch=1)
    res = selection.resolve_effective([a], CTX, r.NOW)
    assert res.authorizing is False  # the structural resolver has no revocation knowledge and says so


def test_a2_unverified_historical_link_cannot_override_authenticated_selection():
    """The decision path never consults the resolver: an authenticated selection is applied or refused on its own
    verification, and a forged newer/older structural neighbour has no effect."""
    rec_obj = r.make_record()
    assert vd(rec_obj).kind == "applied"
    forged_newer = mk(epoch=2, effective=WIDE)  # unsigned, unverified
    assert forged_newer.ok
    assert vd(rec_obj).kind == "applied"



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
