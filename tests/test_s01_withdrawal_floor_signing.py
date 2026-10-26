"""S01 oracle (EXT-S1-6 withdrawal and snapshot floor, r08-v2 signing domain, EXT-S1-9 builder-side battery).

FROZEN BEFORE IMPLEMENTATION: expected outcomes below were predeclared in docs/s01/s01-test-inventory.md and committed before
any source change; on the pre-S01 main this module fails (the v2 selection parser and the v2 verification semantics do not exist).
BUILDER_TESTED. Not independently qualified. Not an independent cryptographic assessment. The Ed25519 adapter (#26) and core hardening
(#34) stay SECURITY-HELD. Synthetic keys only. Linux x86-64 CPython 3.11-3.13.

Stateless verifier note: whether a withdrawal supersedes an *activated* selection is consumer state (S04). These tests cover what the
Registry verifier can decide on one presented statement; ordering against activation is covered only by reusing the EXT-S1-8 reference
vectors (WA-01), which are a reference model, not the Runtime.
"""
import copy
import json
from datetime import datetime, timedelta

import pytest

import r08_support as r
import s01_support as s
from registry_successor import common as c
from registry_successor import decision
from registry_successor import record as record_mod
from registry_successor import selection as sel_mod
from registry_successor import verify as v
from registry_successor import v2_codes
from registry_successor import v2_policy_identity as pid
from registry_successor import v2_selection as v2s

try:
    import nacl.bindings as nb
    from registry_adapters import ed25519_verifier as ev
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    HAVE_BACKEND = False
needs_backend = pytest.mark.skipif(not HAVE_BACKEND, reason="pynacl not installed (requirements-ed25519.lock.txt)")

FAKE = r.FakeVerifier()
CTX, NOW = s.CTX, s.NOW


def parse2(env):
    return v2s.parse_selection_envelope_v2(r.dumps(env))


def verify2(env_or_sel, trust=None, now=NOW, ctx=CTX, rec=None, **kw):
    sel = parse2(env_or_sel) if isinstance(env_or_sel, dict) else env_or_sel
    assert sel.ok, (sel.code, sel.detail)
    return v.verify_selection_v2(sel, ctx, trust or s.trust(), FAKE, now, rec, **kw)


def verify1(env, trust=None, now=NOW, ctx=CTX, rec=None):
    sel = sel_mod.parse_selection_envelope(r.dumps(env))
    assert sel.ok, (sel.code, sel.detail)
    return v.verify_selection(sel, ctx, trust or s.trust(), FAKE, now, rec)


# ================================================================ SD: signing-domain separation
def test_sd01_valid_v2_signature_under_v2_domain_succeeds():
    rep = verify2(s.envelope(s.select_statement()))
    assert (rep.ok, rep.code, rep.authenticated) == (True, None, True)
    assert rep.layers["disposition"] == "pass" and rep.operationally_authorized is False


def test_sd02_v1_signed_v2_statement_is_rejected():
    env = s.envelope(s.select_statement(), domain=s.V1_DOMAIN)
    rep = verify2(env)
    assert (rep.ok, rep.code, rep.authenticated) == (False, "signature_invalid", False)


def test_sd03_v2_signed_v1_statement_is_rejected():
    env = s.v1_envelope(domain=s.V2_DOMAIN)
    rep = verify1(env)
    assert (rep.ok, rep.code) == (False, "signature_invalid")


def test_sd04_v1_signing_and_verification_are_unchanged():
    assert sel_mod.SIGNING_DOMAIN == s.V1_DOMAIN
    stmt = s.v1_statement()
    assert sel_mod.signing_input(stmt) == s.V1_DOMAIN + c.canonical_bytes(stmt)
    rep = verify1(s.v1_envelope(stmt))
    assert (rep.ok, rep.code, rep.authenticated) == (True, None, True)
    assert tuple(rep.layers) == v.LAYERS and "disposition" not in rep.layers  # the v1 report shape is frozen


def test_sd05_signing_input_v2_is_domain_separated():
    stmt = s.select_statement()
    assert v2s.SIGNING_DOMAIN_V2 == s.V2_DOMAIN
    assert v2s.signing_input_v2(stmt) == s.V2_DOMAIN + c.canonical_bytes(stmt)
    assert v2s.signing_input_v2(stmt) != sel_mod.signing_input(stmt)
    assert not s.V2_DOMAIN.startswith(s.V1_DOMAIN) and not s.V1_DOMAIN.startswith(s.V2_DOMAIN)


def test_sd06_v1_envelope_at_v2_entry_and_v2_envelope_at_v1_entry_are_unsupported():
    v1_sel = sel_mod.parse_selection_envelope(r.dumps(s.v1_envelope()))
    rep = v.verify_selection_v2(v1_sel, CTX, s.trust(), FAKE, NOW)
    assert (rep.ok, rep.code) == (False, "contract_unsupported")
    v2_sel = parse2(s.envelope(s.select_statement()))
    rep = v.verify_selection(v2_sel, CTX, s.trust(), FAKE, NOW)
    assert (rep.ok, rep.code) == (False, "contract_unsupported")
    rep = v.verify_selection(v2_sel, CTX, s.trust(), FAKE, NOW, contract_version="r08-v1")
    assert (rep.ok, rep.code) == (False, "contract_unsupported")


def test_sd07_v2_entry_refuses_a_statement_without_disposition():
    class Sel:  # a hand-built selection object whose envelope claims r08-v2 but whose statement has the v1 shape
        pass
    stmt = s.v1_statement()
    sel = Sel()
    sel.ok, sel.code, sel.detail = True, None, ""
    sel.statement, sel.statement_digest = stmt, c.digest(stmt)
    sel.envelope = s.envelope(stmt)
    sel.signatures = sel.envelope["signatures"]
    rep = v.verify_selection_v2(sel, CTX, s.trust(), FAKE, NOW)
    assert (rep.ok, rep.code) == (False, "field_invalid")


@needs_backend
def test_sd08_real_ed25519_v2_domain_end_to_end():
    import base64
    seed = bytes(range(32))
    pk, sk = nb.crypto_sign_seed_keypair(seed)
    stmt = s.select_statement()
    adapter = ev.Ed25519Verifier()

    def sign(domain):
        return base64.b64encode(nb.crypto_sign(domain + c.canonical_bytes(stmt), sk)[:64]).decode("ascii")

    def run(signature):
        sel = parse2(s.envelope(stmt, signature=signature, pub=pk))
        assert sel.ok
        return v.verify_selection_v2(sel, CTX, s.trust(pub=pk), adapter, NOW, key_admission=adapter.key_admission)

    assert run(sign(s.V2_DOMAIN)).ok is True
    assert run(sign(s.V1_DOMAIN)).code == "signature_invalid"
    good = bytearray(base64.b64decode(sign(s.V2_DOMAIN)))
    good[0] ^= 1
    assert run(base64.b64encode(bytes(good)).decode("ascii")).code == "signature_invalid"
    # the same real v1-domain signature still verifies at the unchanged v1 entry point
    stmt1 = s.v1_statement()
    sig1 = base64.b64encode(nb.crypto_sign(s.V1_DOMAIN + c.canonical_bytes(stmt1), sk)[:64]).decode("ascii")
    sel1 = sel_mod.parse_selection_envelope(r.dumps(s.v1_envelope(stmt1, signature=sig1, pub=pk)))
    assert v.verify_selection(sel1, CTX, s.trust(pub=pk), adapter, NOW).ok is True


# ================================================================ WD: withdrawal (EXT-S1-6)
def test_wd01_valid_withdrawal_is_authenticated_and_refused_as_withdrawn():
    sel_stmt = s.select_statement()
    assert verify2(s.envelope(sel_stmt)).ok is True  # activation precondition: the named select verifies
    wd = s.withdraw_statement(sel_stmt)
    rep = verify2(s.envelope(wd))
    assert (rep.ok, rep.code, rep.authenticated, rep.operationally_authorized) == (False, "selection_withdrawn", True, False)
    assert rep.layers["disposition"] == "refuse" and rep.layers["record_binding"] == "not_evaluated"
    assert all(rep.layers[n] == "pass" for n in v.LAYERS if n != "record_binding")
    assert rep.bound_record_digest is None


def test_wd02_withdrawal_is_never_translated_into_success_by_decide():
    rec_text = r.dumps(r.make_record())
    wd = s.withdraw_statement()
    for participation, kind, unchanged in (("required", "required_policy_unavailable", False), ("optional", "overlay_not_applied", True)):
        caller = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
        wd_p = s.withdraw_statement(s.select_statement(participation=participation), participation=participation)
        d = decision.verify_and_decide_v2(participation, caller, rec_text, r.dumps(s.envelope(wd_p)), CTX, s.trust(), FAKE, NOW)
        assert (d.kind, d.code, d.caller_unchanged, d.operationally_authorized) == (kind, "selection_withdrawn", unchanged, False)
        if participation == "required":
            assert d.effective is None  # the caller policy is never returned on a required operation
        else:  # optional: unchanged caller policy (normalized to tuples), explicitly not denial
            assert d.effective == {k: tuple(vv) for k, vv in caller.items()}


def test_wd03_valid_select_decides_applied_at_the_v2_entry():
    rec = r.make_record()
    caller = {"allowed_actions": ["write-file", "read-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a", "unit-c"]}
    d = decision.verify_and_decide_v2("required", caller, r.dumps(rec), r.dumps(s.envelope(s.select_statement())), CTX, s.trust(), FAKE, NOW)
    assert (d.kind, d.code) == ("applied", None)
    assert d.effective == {"allowed_actions": ("write-file",), "allowed_adapters": ("local-fs",), "allowed_units": ("unit-a",)}


@pytest.mark.parametrize("name,mutate,code", [
    pytest.param("unsigned", lambda e: e.update(signatures=[]), "signature_missing", id="WD04a-unsigned"),
    pytest.param("wrong-key-id", lambda e: e["signatures"][0].update(key_id="key-unknown"), "issuer_untrusted", id="WD04b-wrong-key"),
    pytest.param("forged", lambda e: e["signatures"][0].update(signature="AAAA"), "signature_invalid", id="WD04c-forged"),
])
def test_wd04_invalid_withdrawal_never_reports_selection_withdrawn(name, mutate, code):
    env = s.envelope(s.withdraw_statement())
    mutate(env)
    rep = verify2(env)
    assert (rep.ok, rep.code) == (False, code) and rep.code != "selection_withdrawn" and rep.layers["disposition"] == "not_evaluated"


def test_wd05_withdrawal_that_is_expired_revoked_stale_or_out_of_scope_keeps_its_own_code():
    env = s.envelope(s.withdraw_statement())
    late = datetime(2026, 10, 26, tzinfo=s.UTC)
    assert verify2(env, now=late).code == "selection_expired"
    assert verify2(env, now=datetime(2026, 10, 24, 23, tzinfo=s.UTC)).code == "selection_not_yet_effective"
    assert verify2(env, trust=s.trust(revoked_selections=frozenset({("sel-test-1", 2)}))).code == "selection_revoked"
    assert verify2(env, trust=s.trust(min_epochs=(("sel-test-1", 3),))).code == "selection_epoch_stale"
    assert verify2(env, trust=s.trust(revoked_key_ids=frozenset({s.KEY_ID}))).code == "issuer_key_revoked"
    assert verify2(env, ctx=c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test")).code == "selection_scope_mismatch"
    for rep in (verify2(env, now=late), verify2(env, trust=s.trust(revoked_selections=frozenset({("sel-test-1", 2)})))):
        assert rep.layers["disposition"] == "not_evaluated" and rep.authenticated is True or rep.authenticated is False


@pytest.mark.parametrize("over,code", [
    pytest.param(dict(record={"record_id": "f1a-test-record", "record_version": 1, "record_digest": r.SHA}), "selection_supersession_invalid", id="WD06a-record-pin"),
    pytest.param(dict(evaluator=dict(r.EVALUATOR)), "selection_supersession_invalid", id="WD06b-evaluator-pin"),
    pytest.param(dict(supersedes=None), "selection_supersession_invalid", id="WD06c-no-supersedes"),
    pytest.param(dict(epoch=1), "selection_supersession_invalid", id="WD06d-equal-epoch"),
    pytest.param(dict(epoch=0), "field_invalid", id="WD06e-epoch-zero"),
    pytest.param(dict(disposition="revoke"), "field_invalid", id="WD06f-unknown-disposition"),
    pytest.param(dict(disposition=1), "field_type_invalid", id="WD06g-disposition-type"),
])
def test_wd06_withdrawal_shape_is_closed(over, code):
    wd = s.withdraw_statement(**over)
    res = parse2(s.envelope(wd))
    assert (res.ok, res.code) == (False, code)


def test_wd07_withdrawal_naming_another_selection_or_lower_than_supersedes_is_refused():
    base = s.withdraw_statement()
    other = copy.deepcopy(base)
    other["supersedes"]["selection_id"] = "sel-other"
    assert parse2(s.envelope(other)).code == "selection_supersession_invalid"
    low = s.withdraw_statement(s.select_statement(epoch=5), epoch=3)
    assert parse2(s.envelope(low)).code == "selection_supersession_invalid"


def test_wd08_select_shape_and_first_selection_rules():
    first = s.select_statement()
    assert parse2(s.envelope(first)).ok is True and first["supersedes"] is None
    no_disp = s.v1_statement()
    assert parse2(s.envelope(no_disp)).code == "field_missing"
    extra = s.select_statement(unexpected=1)
    assert parse2(s.envelope(extra)).code == "field_unknown"
    unpinned = s.select_statement(record=None)
    assert parse2(s.envelope(unpinned)).ok is False
    bad_fam = s.select_statement(family="zzz")
    assert parse2(s.envelope(bad_fam)).code == "family_unsupported"
    v2_family = s.select_statement(family="f1ab-local-execution-allowlist")
    assert parse2(s.envelope(v2_family)).code != "family_unsupported"  # the r08-v2 family table is used


def test_wd09_parser_rejects_v1_documents_and_digest_tampering():
    assert v2s.parse_selection_envelope_v2(r.dumps(s.v1_envelope())).code == "contract_unsupported"
    env = s.envelope(s.select_statement())
    env["statement"]["epoch"] = 9
    assert v2s.parse_selection_envelope_v2(r.dumps(env)).code == "digest_mismatch"
    assert sel_mod.parse_selection_envelope(r.dumps(s.envelope(s.select_statement()))).code == "contract_unsupported"
    for bad in (None, "", "[]", "{", 7):
        assert v2s.parse_selection_envelope_v2(bad).ok is False


def test_wa01_withdraw_after_activation_reuses_the_ext_s1_8_reference_vectors():
    import glob, os
    import registry_conformance as kit
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "registry_conformance", "vectors",
                        "02_revocation_withdrawal_replay.json")
    doc = json.load(open(path, encoding="utf-8"))
    want = {"RV-03-withdraw-epoch-ordering", "RV-05-reversal-only-by-fresh-higher-epoch", "RV-02-sync-never-reactivates"}
    got = [x for x in doc["vectors"] if x["id"] in want]
    assert {x["id"] for x in got} == want
    for vec in got:
        assert kit.run_vector(doc, vec) == []


# ================================================================ SF: snapshot-version floor (EXT-S1-6, contract section 5)
def fp(trust):
    return pid.trust_snapshot_fingerprint(pid.trust_snapshot_from_verified(trust))


def test_sf01_floor_inputs_default_off_and_v1_unaffected():
    env = s.envelope(s.select_statement())
    assert verify2(env, trust=s.trust(version=1)).ok is True
    assert verify2(env, trust=s.trust(version=1), min_trust_snapshot_version=None, last_accepted_snapshot=None).ok is True
    import inspect
    assert "min_trust_snapshot_version" not in inspect.signature(v.verify_selection).parameters


def test_sf02_external_floor():
    env = s.envelope(s.select_statement())
    assert verify2(env, trust=s.trust(version=5), min_trust_snapshot_version=5).ok is True
    assert verify2(env, trust=s.trust(version=6), min_trust_snapshot_version=5).ok is True
    rep = verify2(env, trust=s.trust(version=4), min_trust_snapshot_version=5)
    assert (rep.ok, rep.code, rep.layers["trust_snapshot"]) == (False, "trust_snapshot_version_stale", "refuse")


@pytest.mark.parametrize("floor", [0, -1, True, False, "1", 1.0, 2 ** 70, [1], None.__class__])
def test_sf03_invalid_floor_is_refused_trust_snapshot_invalid(floor):
    rep = verify2(s.envelope(s.select_statement()), min_trust_snapshot_version=floor)
    assert (rep.ok, rep.code) == (False, "trust_snapshot_invalid")


def test_sf04_last_accepted_snapshot_rules():
    env = s.envelope(s.select_statement())
    t3 = s.trust(version=3)
    same = (3, fp(t3))
    assert verify2(env, trust=t3, last_accepted_snapshot=same).ok is True                    # idempotent redelivery
    assert verify2(env, trust=s.trust(version=4), last_accepted_snapshot=same).ok is True     # newer
    other = s.trust(version=3, revoked_key_ids=frozenset({"key-zzz"}))
    assert verify2(env, trust=other, last_accepted_snapshot=same).code == "trust_snapshot_version_stale"   # equal version, different fingerprint
    assert verify2(env, trust=s.trust(version=2), last_accepted_snapshot=same).code == "trust_snapshot_version_stale"  # older


@pytest.mark.parametrize("bad", [(3,), (3, "x"), (0, "sha256:" + "a" * 64), (True, "sha256:" + "a" * 64), (3, 5), "3", [3], (3, "sha256:" + "a" * 64, 1), (2 ** 70, "sha256:" + "a" * 64)])
def test_sf05_malformed_last_accepted_snapshot_is_refused(bad):
    rep = verify2(s.envelope(s.select_statement()), last_accepted_snapshot=bad)
    assert (rep.ok, rep.code) == (False, "trust_snapshot_invalid")


def test_sf06_expiry_is_reported_before_version():
    env = s.envelope(s.select_statement())
    rep = verify2(env, trust=s.trust(version=1, valid_until="2026-10-25T12:00:00Z"), min_trust_snapshot_version=9)
    assert rep.code == "trust_snapshot_expired"


def test_sf07_older_snapshot_hiding_a_revocation_is_not_accepted():
    env = s.envelope(s.select_statement())
    newer = s.trust(version=2, revoked_selections=frozenset({("sel-test-1", 1)}))
    older = s.trust(version=1)  # same issuers, but it does not list the revocation
    assert verify2(env, trust=older).ok is True  # a stateless verifier alone cannot know: this is why the floor input exists
    assert verify2(env, trust=newer).code == "selection_revoked"
    for kw in (dict(last_accepted_snapshot=(2, fp(newer))), dict(min_trust_snapshot_version=2)):
        rep = verify2(env, trust=older, **kw)
        assert (rep.ok, rep.code) == (False, "trust_snapshot_version_stale")


def test_sf08_floor_failure_blocks_authentication_and_decisions():
    env = s.envelope(s.select_statement())
    rep = verify2(env, trust=s.trust(version=1), min_trust_snapshot_version=2)
    assert rep.authenticated is False and rep.layers["authenticity"] == "not_evaluated"
    d = decision.verify_and_decide_v2("required", {"allowed_actions": [], "allowed_adapters": [], "allowed_units": []},
                                      r.dumps(r.make_record()), r.dumps(env), CTX, s.trust(version=1), FAKE, NOW)
    # Documented S01 limitation: verify_and_decide_v2 exposes NO floor input, so a stale snapshot is still accepted there. The floor is
    # enforced at verify_selection_v2; a refused floor report can never become an application:
    assert d.kind == "applied_deny_all"
    floor_rep = verify2(env, trust=s.trust(version=1), min_trust_snapshot_version=2)
    refused = decision._decide_verified("required", {"allowed_actions": [], "allowed_adapters": [], "allowed_units": []},
                                        record_mod.validate_record_text(r.dumps(r.make_record())), floor_rep, v2_codes.CODES_V2)
    assert (refused.kind, refused.code, refused.effective) == ("required_policy_unavailable", "trust_snapshot_version_stale", None)


# ================================================================ AV: EXT-S1-9 adversarial verifier battery (builder side)
def good_env(**over):
    return s.envelope(s.select_statement(**over))


def test_av01_forged_and_altered_selections():
    env = good_env()
    env["signatures"][0]["signature"] = "AAAA"
    assert verify2(env).code == "signature_invalid"
    stmt = s.select_statement()
    env = s.envelope(stmt)
    altered = copy.deepcopy(stmt)
    altered["selection_id"] = "sel-test-2"
    env["statement"], env["statement_digest"] = altered, c.digest(altered)          # re-digested, original signature kept
    assert verify2(env).code == "signature_invalid"
    env = s.envelope(stmt)
    env["statement"] = altered                                                      # altered, digest kept
    assert v2s.parse_selection_envelope_v2(r.dumps(env)).code == "digest_mismatch"


def test_av02_expiry_boundaries_are_exact():
    env = good_env()
    start = datetime(2026, 10, 25, tzinfo=s.UTC)
    end = datetime(2026, 10, 26, tzinfo=s.UTC)
    assert verify2(env, now=start).ok is True
    assert verify2(env, now=start - timedelta(microseconds=1)).code == "selection_not_yet_effective"
    assert verify2(env, now=end - timedelta(microseconds=1)).ok is True
    assert verify2(env, now=end).code == "selection_expired"


def test_av03_wrong_key_unknown_key_and_revoked_key():
    other = bytes.fromhex("3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c")  # RFC 8032 test 2 public key
    env = s.envelope(s.select_statement(), pub=other)                                  # signed for a different public key
    assert verify2(env).code == "signature_invalid"
    assert verify2(good_env(), trust=s.trust(key_id="key-test-2")).code == "issuer_untrusted"
    assert verify2(good_env(), trust=s.trust(revoked_key_ids=frozenset({s.KEY_ID}))).code == "issuer_key_revoked"
    assert verify2(good_env(), trust=s.trust(pub=bytes(32))).code == "trust_snapshot_invalid"        # small-order key refused at admission


@pytest.mark.parametrize("ctx,code", [
    pytest.param(c.ExpectedContext("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch", id="AV04a-cross-consumer"),
    pytest.param(c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch", id="AV04b-cross-tenant"),
    pytest.param(c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"), "selection_scope_mismatch", id="AV04c-cross-institution"),
    pytest.param(c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test"), "selection_scope_mismatch", id="AV04d-cross-domain"),
    pytest.param(c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch", id="AV04e-cross-operation"),
])
def test_av04_cross_scope_replay_is_refused(ctx, code):
    assert verify2(good_env(), ctx=ctx).code == code


def test_av05_epoch_floor_revoked_pair_and_superseded_replay():
    assert verify2(good_env(), trust=s.trust(min_epochs=(("sel-test-1", 2),))).code == "selection_epoch_stale"
    assert verify2(good_env(), trust=s.trust(revoked_selections=frozenset({("sel-test-1", 1)}))).code == "selection_revoked"
    assert verify2(good_env(epoch=2), trust=s.trust(revoked_selections=frozenset({("sel-test-1", 1)}))).ok is True  # a different epoch is not the revoked pair


def test_av06_participation_missing_unsupported_invalid():
    assert parse2(s.envelope(s.select_statement(participation="maybe"))).code == "field_invalid"
    assert parse2(s.envelope(s.select_statement(participation=None))).code == "field_invalid"
    no_part = s.select_statement()
    del no_part["participation"]
    assert parse2(s.envelope(no_part)).code == "field_missing"
    rec_text, caller = r.dumps(r.make_record()), {"allowed_actions": [], "allowed_adapters": [], "allowed_units": []}
    d = decision.verify_and_decide_v2("optional", caller, rec_text, r.dumps(good_env()), CTX, s.trust(), FAKE, NOW)   # signed required, operation optional
    assert (d.kind, d.code) == ("overlay_not_applied", "participation_mismatch")
    d = decision.verify_and_decide_v2("bogus", caller, rec_text, r.dumps(good_env()), CTX, s.trust(), FAKE, NOW)
    assert (d.kind, d.code) == ("required_policy_unavailable", "participation_mismatch")


def test_av07_unselected_pin_and_record_identity():
    rec = record_mod.validate_record_text(r.dumps(r.make_record(record_version=2)))
    rep = verify2(good_env(), rec=rec)
    assert (rep.ok, rep.code) == (False, "record_identity_mismatch")
    good = record_mod.validate_record_text(r.dumps(r.make_record()))
    assert verify2(good_env(), rec=good).ok is True


def test_av08_unknown_family_and_unknown_contract_version():
    assert parse2(s.envelope(s.select_statement(family="nope"))).code == "family_unsupported"
    for bad in ("r08-v3", "R08-V2", "", None):
        assert v2s.parse_selection_envelope_v2(r.dumps(s.envelope(s.select_statement(), contract=bad))).code == "contract_unsupported"


def test_av09_v1_signed_replayed_as_v2_and_back_across_every_entry():
    stmt2 = s.select_statement()
    assert verify2(s.envelope(stmt2, domain=s.V1_DOMAIN)).code == "signature_invalid"
    stmt1 = s.v1_statement()
    assert verify1(s.v1_envelope(stmt1, domain=s.V2_DOMAIN)).code == "signature_invalid"
    # a v1 document signed under v1 never verifies at the v2 entry, even with a matching digest and a valid v1 signature
    sel1 = sel_mod.parse_selection_envelope(r.dumps(s.v1_envelope(stmt1)))
    assert v.verify_selection_v2(sel1, CTX, s.trust(), FAKE, NOW).code == "contract_unsupported"


def test_av10_codes_and_layers_are_the_declared_v2_vocabulary():
    assert v.LAYERS_V2 == v.LAYERS + ("disposition",)
    assert v2_codes.CODES_V2["selection_withdrawn"][0] == "disposition"
    assert v2_codes.CODES_V2["trust_snapshot_version_stale"][0] == "trust"
    assert len(v2_codes.CODES_V2) == 48 and len(c.CODES) == 46          # no new code and no v1 mutation
    rep = verify2(good_env())
    assert tuple(rep.layers) == v.LAYERS_V2
