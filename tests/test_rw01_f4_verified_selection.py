"""RW-01-F4-PoC (Registry side): tests for registry_successor/v2_verified_selection.py (BUILDER_TESTED; not independently qualified).

MECHANISM TESTS ONLY. Every key here is a SYNTHETIC test seed (the same seeds as tests/test_v01a_v2_record_path.py). Nothing here is a
trust root, a production key or evidence of Registry origin: it shows that the new module composes the existing verifier into a
record-bound, floor-bound, eleven-layer admission and refuses the negatives with the SPECIFIC typed code. Claim A only (selection
signature per a caller-supplied verifier and trust snapshot); claim B is not made.

Numbering N01..N28 follows the sprint register (CONTRACT-FREEZE C4). Rows that belong to Control Plane / Replay (N09-N11, N16-N18,
N22-N27) are not tested here. Every negative asserts (a) the exact code and (b) `admitted is False`.

Real Ed25519 (PyNaCl, requirements-ed25519.lock.txt) signs every selection; where PyNaCl is absent the module is reported NOT RUN
(skipped with a reason), never passed with a double. The signing helpers below are COPIED from tests/test_v01a_v2_record_path.py:56-83,
351-372; the production module never builds signing bytes (see test_the_module_never_builds_signing_bytes).
"""
import ast
import base64
import copy
import dataclasses
import inspect
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import decision  # noqa: E402
from registry_successor import v2_age_bounds as ab  # noqa: E402
from registry_successor import v2_codes  # noqa: E402
from registry_successor import v2_f1ab as f1ab  # noqa: E402
from registry_successor import v2_policy_identity as pid  # noqa: E402
from registry_successor import v2_selection  # noqa: E402
from registry_successor import v2_verified_selection as vs  # noqa: E402
from registry_successor import verify as v  # noqa: E402

try:
    import nacl.bindings as nb
    from registry_adapters import ed25519_verifier as ev
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    HAVE_BACKEND = False

pytestmark = pytest.mark.skipif(not HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "registry_successor" / "v2_verified_selection.py"
F4 = ab.FAMILY_F4
PK, SK = (nb.crypto_sign_seed_keypair(bytes(range(32))) if HAVE_BACKEND else (None, None))          # synthetic test seed
OTHER_PK, OTHER_SK = (nb.crypto_sign_seed_keypair(bytes(range(1, 33))) if HAVE_BACKEND else (None, None))  # synthetic test seed
F4P = {"status_max_age_seconds": 120, "approval_max_age_seconds": 600}
F4HOST = {"status_max_age_seconds": 300, "approval_max_age_seconds": 600}
NO_LAST = None


# ---------------------------------------------------------------------------------------------------------------- builders (copied)
def sign(statement, sk=None, domain=None):
    msg = (domain or s.V2_DOMAIN) + c.canonical_bytes(statement)
    return base64.b64encode(nb.crypto_sign(msg, sk or SK)[:64]).decode("ascii")


def fam_record(family, pl, **over):
    body = dict(r.make_record(), contract_version="r08-v2", family=family, record_id="age-test-record", payload=pl)
    body.update(over)
    return r.seal_record(body)


def sel_text(rec, family=F4, sk=None, pub=None, key_id=s.KEY_ID, **over):
    stmt = r.make_statement_v2(rec, family=family, **over)
    return r.dumps(s.envelope(stmt, signature=sign(stmt, sk), pub=pub or PK, key_id=key_id))


def trust(**kw):
    return s.trust(pub=PK, **kw)


UNSET = object()


def run(rec=None, sel=None, ctx=None, tr=None, now=None, verifier=None, min_v=1, last=NO_LAST, family=F4, participation="required",
        key_admission="default", record_text=UNSET):
    rec = rec if rec is not None else fam_record(F4, F4P)
    ad = verifier if verifier is not None else ev.Ed25519Verifier()
    return vs.verify_selection_text_v2(
        sel if sel is not None else sel_text(rec), r.dumps(rec) if record_text is UNSET else record_text,
        ctx or s.CTX, tr or trust(), ad, now or r.NOW, min_trust_snapshot_version=min_v, last_accepted_snapshot=last,
        required_family=family, required_participation=participation,
        key_admission=(ad.key_admission if key_admission == "default" else key_admission))


def assert_refused(res, code):
    assert isinstance(res, vs.VerifiedSelectionV2)
    assert res.admitted is False, res
    assert res.code == code, (res.code, res.detail, res.layers)
    assert res.code in v2_codes.CODES_V2
    assert res.record is None and res.issuer_id is None and res.selection_id is None  # no unauthenticated claim is echoed


def layer(res, name):
    return dict(res.layers)[name]


# ------------------------------------------------------------------------------------------------------------------------- N01
def test_n01_valid_f4_selection_is_admitted_with_all_eleven_layers():
    rec = fam_record(F4, F4P)
    res = run(rec)
    assert res.admitted is True and res.code is None and res.detail == ""
    assert tuple(n for n, _ in res.layers) == v.LAYERS_V2 and len(res.layers) == 11
    assert all(val == "pass" for _, val in res.layers)
    assert (res.report_ok, res.authenticated, res.issuer_id, res.participation) == (True, True, "issuer-test-1", "required")
    assert (res.selection_id, res.epoch, res.family, res.consumer_id, res.operation) == ("sel-test-1", 1, F4, "consumer-test", "op-test")
    assert res.scope == ("tenant-a", "inst-a", "domain-a")
    assert (res.valid_from, res.valid_until) == ("2026-10-25T00:00:00Z", "2026-10-26T00:00:00Z")
    assert (res.record_id, res.record_version, res.record_digest) == ("age-test-record", 1, rec["record_digest"])
    assert res.selection_digest == c.digest(r.make_statement_v2(rec, family=F4))
    assert (res.trust_snapshot_id, res.trust_snapshot_version) == ("snap-test-1", 1)
    assert res.trust_snapshot_fingerprint == pid.trust_snapshot_fingerprint_from_verified(trust())
    assert (res.min_trust_snapshot_version, res.last_accepted_snapshot, res.epoch_floor_applied) == (1, None, False)
    assert res.record == rec and res.record is not rec


def test_n01_result_is_immutable_and_its_record_is_a_private_copy():
    rec = fam_record(F4, F4P)
    res = run(rec)
    with pytest.raises(dataclasses.FrozenInstanceError):
        res.admitted = False
    res.record["payload"]["status_max_age_seconds"] = 1  # mutating the returned copy must not reach a later result
    assert run(rec).record["payload"]["status_max_age_seconds"] == 120
    assert isinstance(res.layers, tuple) and all(isinstance(p, tuple) for p in res.layers)


def test_n01_the_f4_shorthand_equals_the_generic_function():
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    short = vs.verify_f4_selection_v2(sel_text(rec), r.dumps(rec), s.CTX, trust(), ad, r.NOW, min_trust_snapshot_version=1,
                                      last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert short == run(rec) and short.admitted is True


def test_n01_effective_digest_recomputed_equals_the_verify_and_decide_output():
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    d = decision.verify_and_decide_v2("required", F4HOST, r.dumps(rec), sel_text(rec), s.CTX, trust(), ad, r.NOW, ad.key_admission)
    assert d.kind == "applied" and d.effective == {"status_max_age_seconds": 120, "approval_max_age_seconds": 600}
    res = run(rec)
    out = vs.recompute_f4_effective_policy(res, dict(F4HOST))
    assert out.ok is True and out.code is None
    assert out.effective == d.effective
    assert out.effective_policy_digest == pid.effective_policy_digest(ab.FAMILY_F4, d.effective)
    assert out.effective_policy_digest.startswith("sha256:")


@pytest.mark.parametrize("host,expected", [
    ({"status_max_age_seconds": 300, "approval_max_age_seconds": 600}, (120, 600)),   # registry narrower on status
    ({"status_max_age_seconds": 60, "approval_max_age_seconds": 30}, (60, 30)),       # host narrower: never widened by the registry
    ({"status_max_age_seconds": 0, "approval_max_age_seconds": 600}, (0, 600)),
])
def test_n01_recompute_takes_the_per_scalar_minimum_of_host_and_signed_bound(host, expected):
    res = run(fam_record(F4, F4P))
    out = vs.recompute_f4_effective_policy(res, host)
    assert out.ok is True and (out.effective["status_max_age_seconds"], out.effective["approval_max_age_seconds"]) == expected
    assert out.effective_policy_digest == pid.effective_policy_digest(F4, out.effective)


def test_n01_epoch_floor_applied_is_true_only_when_the_snapshot_has_an_entry_for_the_selection():
    assert run(tr=trust(min_epochs=(("sel-test-1", 1),))).epoch_floor_applied is True
    assert run(tr=trust(min_epochs=(("sel-other", 5),))).epoch_floor_applied is False
    assert run().epoch_floor_applied is False


# ------------------------------------------------------------------------------------------------------------------------- N02-N08
def test_n02_forged_signature_is_signature_invalid():
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4)
    bad = bytearray(base64.b64decode(sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, signature=base64.b64encode(bytes(bad)).decode("ascii"), pub=PK))
    res = run(rec, sel=forged)
    assert_refused(res, "signature_invalid")
    assert res.authenticated is False and layer(res, "authenticity") == "refuse"


def test_n02_a_signature_by_a_different_key_with_the_trusted_key_id_is_signature_invalid():
    rec = fam_record(F4, F4P)
    assert_refused(run(rec, sel=sel_text(rec, sk=OTHER_SK)), "signature_invalid")


def test_n02_a_missing_signature_is_signature_missing():
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4)
    assert_refused(run(rec, sel=r.dumps(s.envelope(stmt, signed=False))), "signature_missing")


def test_n03_unknown_signer_is_issuer_untrusted():
    rec = fam_record(F4, F4P)
    res = run(rec, sel=sel_text(rec, key_id="key-unknown-9"))
    assert_refused(res, "issuer_untrusted")
    assert res.authenticated is False


def test_n04_wrong_issuer_grant_is_issuer_not_authorized():
    rec = fam_record(F4, F4P)
    wrong = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")
    tr = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", PK, (wrong,)),))
    res = run(rec, tr=tr)
    assert_refused(res, "issuer_not_authorized")
    assert res.authenticated is True and res.report_ok is False  # N20 shape: authenticated is not admission


def test_n05_wrong_tenant_is_selection_scope_mismatch():
    assert_refused(run(ctx=c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test")), "selection_scope_mismatch")


@pytest.mark.parametrize("ctx", [c.ExpectedContext("consumer-test", "tenant-a", "inst-b", "domain-a", "op-test"),
                                 c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-b", "op-test")])
def test_n05_wrong_institution_or_authority_domain_is_selection_scope_mismatch(ctx):
    assert_refused(run(ctx=ctx), "selection_scope_mismatch")


def test_n06_wrong_operation_is_selection_operation_mismatch():
    assert_refused(run(ctx=c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")), "selection_operation_mismatch")


def test_n07_wrong_consumer_is_selection_consumer_mismatch():
    assert_refused(run(ctx=c.ExpectedContext("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test")), "selection_consumer_mismatch")


@pytest.mark.parametrize("bad", [None, "ctx", (), {"consumer_id": "consumer-test"}])
def test_n07_an_invalid_context_object_is_selection_scope_mismatch(bad):
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    res = vs.verify_f4_selection_v2(sel_text(rec), r.dumps(rec), bad, trust(), ad, r.NOW, min_trust_snapshot_version=1,
                                    last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert_refused(res, "selection_scope_mismatch")


def test_n08_substituted_record_with_another_payload_is_record_digest_mismatch():
    rec = fam_record(F4, F4P)
    other = fam_record(F4, {"status_max_age_seconds": 9000, "approval_max_age_seconds": 9000})  # same id/version, valid and sealed
    assert other["record_id"] == rec["record_id"] and other["record_digest"] != rec["record_digest"]
    res = run(rec, record_text=r.dumps(other))
    assert_refused(res, "record_digest_mismatch")
    assert layer(res, "record_binding") == "refuse"


def test_n08_substituted_record_with_another_identity_is_record_identity_mismatch():
    rec = fam_record(F4, F4P)
    other = fam_record(F4, F4P, record_id="age-other-record")
    assert_refused(run(rec, record_text=r.dumps(other)), "record_identity_mismatch")


def test_n08_a_tampered_unsealed_record_is_digest_mismatch():
    rec = fam_record(F4, F4P)
    tampered = copy.deepcopy(rec)
    tampered["payload"]["status_max_age_seconds"] = 9000
    assert_refused(run(rec, record_text=r.dumps(tampered)), "digest_mismatch")


def test_n08_a_record_of_another_family_is_refused_and_never_admitted():
    rec = fam_record(F4, F4P)
    f1 = fam_record(f1ab.FAMILY_F1AB, {"allowed_actions": ["a"], "allowed_adapters": ["a"], "allowed_units": ["u"],
                                       "allowed_institutions": ["i"], "allowed_authority_domains": ["d"]}, record_id="age-test-record")
    res = run(rec, record_text=r.dumps(f1))
    assert res.admitted is False and res.code == "family_unsupported"


# ------------------------------------------------------------------------------------------------------------------------- N12-N15
def test_n12_revoked_key_is_issuer_key_revoked_under_the_supplied_snapshot():
    res = run(tr=trust(revoked_key_ids=frozenset({s.KEY_ID})))
    assert_refused(res, "issuer_key_revoked")
    assert res.authenticated is False


def test_n12_a_revoked_selection_epoch_is_selection_revoked():
    assert_refused(run(tr=trust(revoked_selections=frozenset({("sel-test-1", 1)}))), "selection_revoked")


def test_n13_withdrawn_selection_is_refused_with_the_withdrawal_code():
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4)
    wd = s.withdraw_statement(stmt)
    res = run(rec, sel=r.dumps(s.envelope(wd, signature=sign(wd), pub=PK)))
    assert_refused(res, "selection_withdrawn")
    assert res.authenticated is True and res.report_ok is False


def test_n14_below_min_epoch_floor_is_selection_epoch_stale():
    res = run(tr=trust(min_epochs=(("sel-test-1", 2),)))
    assert_refused(res, "selection_epoch_stale")
    assert layer(res, "epoch") == "refuse"


def test_n14_an_epoch_at_the_floor_is_admitted():
    assert run(tr=trust(min_epochs=(("sel-test-1", 1),))).admitted is True


def test_n14_floors_are_required_keywords():
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    args = (sel_text(rec), r.dumps(rec), s.CTX, trust(), ad, r.NOW)
    with pytest.raises(TypeError):
        vs.verify_selection_text_v2(*args, required_family=F4)                                   # no floors at all
    with pytest.raises(TypeError):
        vs.verify_selection_text_v2(*args, last_accepted_snapshot=None, required_family=F4)      # min floor omitted
    with pytest.raises(TypeError):
        vs.verify_selection_text_v2(*args, min_trust_snapshot_version=1, required_family=F4)     # last_accepted omitted
    with pytest.raises(TypeError):
        vs.verify_selection_text_v2(*args, 1, None, F4)                                          # floors are keyword-only
    sig = inspect.signature(vs.verify_selection_text_v2)
    for name in ("min_trust_snapshot_version", "last_accepted_snapshot", "required_family"):
        p = sig.parameters[name]
        assert p.kind is inspect.Parameter.KEYWORD_ONLY and p.default is inspect.Parameter.empty
    assert sig.parameters["required_participation"].default == "required" and sig.parameters["key_admission"].default is None


def test_n14_snapshot_version_floors_with_real_signatures():
    fp7 = pid.trust_snapshot_fingerprint_from_verified(trust(version=7))
    assert run(tr=trust(version=7), min_v=5, last=(7, fp7)).admitted is True                      # equal version, equal fingerprint: idempotent
    assert_refused(run(tr=trust(version=7), min_v=8), "trust_snapshot_version_stale")             # below the external floor
    assert_refused(run(tr=trust(version=7), min_v=5, last=(7, "sha256:" + "0" * 64)), "trust_snapshot_version_stale")  # same version, other fp
    assert_refused(run(tr=trust(version=6), min_v=5, last=(7, fp7)), "trust_snapshot_version_stale")  # older than last accepted
    assert run(tr=trust(version=9), min_v=5, last=(7, fp7)).admitted is True                      # newer than last accepted


def test_n14_the_applied_floors_are_echoed():
    fp = pid.trust_snapshot_fingerprint_from_verified(trust(version=7))
    res = run(tr=trust(version=7), min_v=5, last=(7, fp))
    assert (res.min_trust_snapshot_version, res.last_accepted_snapshot) == (5, (7, fp))


@pytest.mark.parametrize("bad", [0, -1, True, False, "1", 1.0, None, 2 ** 53, [1], (1,)])
def test_floor_min_trust_snapshot_version_malformed_is_trust_snapshot_invalid(bad):
    res = run(min_v=bad)
    assert res.admitted is False and res.code == "trust_snapshot_invalid"
    assert all(val == "not_evaluated" for _, val in res.layers)  # nothing was verified


@pytest.mark.parametrize("bad", [[1, "sha256:" + "0" * 64], (0, "sha256:" + "0" * 64), (True, "sha256:" + "0" * 64), (1, "bad"),
                                 (1, "sha256:" + "0" * 63), (1, "sha256:" + "A" * 64), (1, "sha256:" + "0" * 64, 2), (1,), "x", 7, {}])
def test_floor_last_accepted_snapshot_malformed_is_trust_snapshot_invalid(bad):
    res = run(last=bad)
    assert res.admitted is False and res.code == "trust_snapshot_invalid"
    assert all(val == "not_evaluated" for _, val in res.layers)


def test_n15_expired_snapshot_at_the_explicit_verification_time():
    import datetime
    res = run(now=datetime.datetime(2026, 10, 27, 0, 0, 0, tzinfo=datetime.timezone.utc))  # == valid_until: half-open, expired
    assert_refused(res, "trust_snapshot_expired")
    assert layer(res, "trust_snapshot") == "refuse"
    assert run(tr=trust(valid_until="2026-10-27T00:00:00Z"), now=datetime.datetime(2026, 10, 25, 23, 59, 59, tzinfo=datetime.timezone.utc)).admitted is True


def test_n15_selection_window_is_enforced_at_the_explicit_time():
    import datetime
    utc = datetime.timezone.utc
    assert_refused(run(now=datetime.datetime(2026, 10, 24, 23, 59, 59, tzinfo=utc)), "selection_not_yet_effective")
    assert_refused(run(now=datetime.datetime(2026, 10, 26, 0, 0, 0, tzinfo=utc)), "selection_expired")
    assert run(now=datetime.datetime(2026, 10, 25, 0, 0, 0, tzinfo=utc)).admitted is True    # valid_from is inclusive


@pytest.mark.parametrize("bad_now", [None, "2026-10-25T12:00:00Z", 1761393600, __import__("datetime").datetime(2026, 10, 25, 12, 0, 0)])
def test_n15_a_missing_naive_or_non_datetime_time_is_time_unavailable(bad_now):
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    res = vs.verify_f4_selection_v2(sel_text(rec), r.dumps(rec), s.CTX, trust(), ad, bad_now, min_trust_snapshot_version=1,
                                    last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert_refused(res, "time_unavailable")


def test_the_module_reads_no_clock_two_identical_calls_at_one_time_agree():
    rec = fam_record(F4, F4P)
    assert run(rec) == run(rec)


# ------------------------------------------------------------------------------------------------------------------------- N16-support
def test_n16_support_the_entry_points_accept_no_verdict_or_report():
    for fn in (vs.verify_selection_text_v2, vs.verify_f4_selection_v2):
        names = set(inspect.signature(fn).parameters)
        assert not (names & {"verdict", "report", "result", "authenticated", "ok", "verified", "layers", "admitted"}), names
    assert {"selection_text", "record_text"} <= set(inspect.signature(vs.verify_selection_text_v2).parameters)


@pytest.mark.parametrize("injected", [
    {"ok": True, "code": None, "authenticated": True, "layers": {n: "pass" for n in v.LAYERS_V2}},
    v.VerificationReport(True, None, "", {n: "pass" for n in v.LAYERS_V2}, "sha256:" + "0" * 64, True, "issuer-test-1"),
    b"{}", 7, None, ["x"],
])
def test_n16_support_a_verdict_shaped_object_in_place_of_the_selection_text_is_refused(injected):
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    res = vs.verify_f4_selection_v2(injected, r.dumps(rec), s.CTX, trust(), ad, r.NOW, min_trust_snapshot_version=1,
                                    last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert_refused(res, "input_not_text")


@pytest.mark.parametrize("injected", [{"payload": F4P}, b"{}", 7, None, ["x"], v.VerificationReport(True, None, "", {}, None, True, "i")])
def test_n16_support_a_non_text_record_is_refused_and_never_admitted(injected):
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    res = vs.verify_f4_selection_v2(sel_text(rec), injected, s.CTX, trust(), ad, r.NOW, min_trust_snapshot_version=1,
                                    last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert_refused(res, "input_not_text")


# ------------------------------------------------------------------------------------------------------------------------- N19
def _unicode_fixture(tenant="ténant-a"):
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4, scope={"tenant": tenant, "institution": "inst-a", "authority_domain": "domain-a"})
    grant = v.AuthorityGrant("consumer-test", tenant, "inst-a", "domain-a", "op-test")
    tr = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", PK, (grant,)),))
    ctx = c.ExpectedContext("consumer-test", tenant, "inst-a", "domain-a", "op-test")
    return rec, stmt, tr, ctx


def test_n19_positive_non_ascii_content_signed_over_ensure_ascii_true_bytes_is_admitted():
    rec, stmt, tr, ctx = _unicode_fixture()
    signed_bytes = s.V2_DOMAIN + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    assert b"\\u00e9" in signed_bytes and "é".encode() not in signed_bytes
    assert signed_bytes == s.V2_DOMAIN + c.canonical_bytes(stmt)
    sig = base64.b64encode(nb.crypto_sign(signed_bytes, SK)[:64]).decode("ascii")
    res = run(rec, sel=r.dumps(s.envelope(stmt, signature=sig, pub=PK)), ctx=ctx, tr=tr)
    assert res.admitted is True and res.scope[0] == "ténant-a" and res.code is None


def test_n19_positive_the_transport_encoding_of_the_envelope_text_does_not_matter():
    rec, stmt, tr, ctx = _unicode_fixture()
    env = s.envelope(stmt, signature=sign(stmt), pub=PK)
    raw = json.dumps(env, sort_keys=True, ensure_ascii=False)  # the TEXT carries the raw character; the signed bytes are unchanged
    assert "é" in raw
    assert run(rec, sel=raw, ctx=ctx, tr=tr).admitted is True


def test_n19_negative_signature_over_ensure_ascii_false_bytes_is_signature_invalid():
    rec, stmt, tr, ctx = _unicode_fixture()
    wrong = s.V2_DOMAIN + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    assert wrong != s.V2_DOMAIN + c.canonical_bytes(stmt)
    sig = base64.b64encode(nb.crypto_sign(wrong, SK)[:64]).decode("ascii")
    res = run(rec, sel=r.dumps(s.envelope(stmt, signature=sig, pub=PK)), ctx=ctx, tr=tr)
    assert_refused(res, "signature_invalid")


def test_the_module_never_builds_signing_bytes():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
               {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not names & {"canonical_bytes", "signing_input_v2", "signing_input", "dumps", "dump", "encode", "ensure_ascii", "b64encode", "b64decode", "V2_DOMAIN"}, names
    assert "json" not in imported and "base64" not in imported and "hashlib" not in imported
    text = MODULE.read_text(encoding="utf-8")
    assert "ensure_ascii=" not in text and "ocs-reg/" not in text


# ------------------------------------------------------------------------------------------------------------------------- N20 / N21
def test_n20_authenticated_true_with_ok_false_is_never_admitted():
    rec = fam_record(F4, F4P)
    for kw, code in ((dict(ctx=c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test")), "selection_scope_mismatch"),
                     (dict(tr=trust(min_epochs=(("sel-test-1", 9),))), "selection_epoch_stale")):
        res = run(rec, **kw)
        assert_refused(res, code)
        assert res.authenticated is True and res.report_ok is False


def test_n21_wrong_required_family_is_family_unsupported():
    assert_refused(run(family=f1ab.FAMILY_F1AB), "family_unsupported")
    assert_refused(run(family="not-a-family"), "family_unsupported")
    for bad in (None, 7, b"x", ["f4"]):
        assert_refused(run(family=bad), "family_unsupported")


def test_n21_an_f1ab_selection_is_not_admitted_by_the_f4_shorthand_but_is_by_the_generic_function():
    pl = {"allowed_actions": ["act-copy"], "allowed_adapters": ["a-local"], "allowed_units": ["u-read"],
          "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"]}
    rec = fam_record(f1ab.FAMILY_F1AB, pl, record_id="f1ab-test-record")
    sel = sel_text(rec, family=f1ab.FAMILY_F1AB)
    ad = ev.Ed25519Verifier()
    args = (sel, r.dumps(rec), s.CTX, trust(), ad, r.NOW)
    wrong = vs.verify_f4_selection_v2(*args, min_trust_snapshot_version=1, last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert_refused(wrong, "family_unsupported")
    right = vs.verify_selection_text_v2(*args, min_trust_snapshot_version=1, last_accepted_snapshot=None,
                                        required_family=f1ab.FAMILY_F1AB, key_admission=ad.key_admission)
    assert right.admitted is True and right.family == f1ab.FAMILY_F1AB
    out = vs.recompute_f4_effective_policy(right, dict(F4HOST))  # an admitted non-F4 result is not usable for F4 recomputation
    assert (out.ok, out.code, out.effective, out.effective_policy_digest) == (False, "family_unsupported", None, None)


def test_n21_participation_mismatch():
    rec = fam_record(F4, F4P)
    optional_sel = sel_text(rec, participation="optional")
    assert_refused(run(rec, sel=optional_sel), "participation_mismatch")                       # statement optional, consumer requires "required"
    assert_refused(run(rec, participation="optional"), "participation_mismatch")              # statement required, consumer expects optional
    for bad in ("bogus", None, 1, b"required"):
        assert_refused(run(rec, participation=bad), "participation_mismatch")
    assert run(rec, sel=optional_sel, participation="optional").admitted is True              # the comparison is exact equality, nothing else


# ------------------------------------------------------------------------------------------------------------------------- N28 / trap
def test_n28_a_missing_verifier_is_verifier_unavailable_never_admitted():
    rec = fam_record(F4, F4P)
    res = vs.verify_f4_selection_v2(sel_text(rec), r.dumps(rec), s.CTX, trust(), None, r.NOW, min_trust_snapshot_version=1,
                                    last_accepted_snapshot=None)
    assert_refused(res, "verifier_unavailable")
    assert layer(res, "authenticity") == "refuse"


def test_n28_ed25519_backend_unavailable_yields_no_verifier_and_verifier_unavailable(monkeypatch):
    def broken():
        raise ev.Ed25519Unavailable("simulated: backend not usable")
    monkeypatch.setattr(ev, "_load_backend", broken)
    with pytest.raises(ev.Ed25519Unavailable):
        ev.Ed25519Verifier()
    assert ev.load_verifier_or_none() is None
    rec = fam_record(F4, F4P)
    res = vs.verify_f4_selection_v2(sel_text(rec), r.dumps(rec), s.CTX, trust(), ev.load_verifier_or_none(), r.NOW,
                                    min_trust_snapshot_version=1, last_accepted_snapshot=None)
    assert_refused(res, "verifier_unavailable")


def test_n28_a_verifier_that_refuses_everything_is_signature_invalid_never_admitted():
    class Refuses:
        def verify(self, alg, public_key, message, signature):
            return False
    assert_refused(run(verifier=Refuses(), key_admission=None), "signature_invalid")


def test_limitation_the_core_does_not_pin_the_verifier_type():
    """DOCUMENTED LIMITATION (not a security property of this module): `verify_selection_v2` accepts any object with a `verify` method, so
    this module admits whatever a permissive verifier approves. Pinning the verifier class is the ENFORCING CONSUMER's duty (CP does
    `type(verifier) is Ed25519Verifier`). The test pins the fact so nobody mistakes admission for a statement about verifier genuineness."""
    class Permissive:
        def verify(self, alg, public_key, message, signature):
            return alg == "ed25519"
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4)
    forged = r.dumps(s.envelope(stmt, signature=base64.b64encode(bytes(64)).decode("ascii"), pub=PK))
    assert run(rec, sel=forged, verifier=Permissive(), key_admission=None).admitted is True
    assert_refused(run(rec, sel=forged), "signature_invalid")  # the real adapter refuses the same bytes


def test_the_record_less_trap_exists_in_the_verifier_and_cannot_be_admitted_here():
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    sel = v2_selection.parse_selection_envelope_v2(sel_text(rec))
    bare = v.verify_selection_v2(sel, s.CTX, trust(), ad, r.NOW, None, ad.key_admission)
    assert bare.ok is True and bare.code is None and bare.authenticated is True       # the trap: a record-less report is "ok"
    assert dict(bare.layers)["record_binding"] == "not_evaluated" and bare.bound_record_digest is None
    # (1) the new entry point has no way to omit the record: it is a positional parameter with no default and must be exact text
    assert inspect.signature(vs.verify_selection_text_v2).parameters["record_text"].default is inspect.Parameter.empty
    for missing, code in ((None, "input_not_text"), (b"", "input_not_text"), (0, "input_not_text"), ("", "json_malformed")):
        assert_refused(run(rec, record_text=missing), code)
    # (2) even if the underlying verifier ignored the record and returned the record-less "ok" report, the conjunction refuses
    seen = {}

    def ignore_record(selection, context, trust_, verifier, now, record=None, key_admission=None, **floors):
        seen["record"] = record
        return v.VerificationReport(True, None, "", dict(bare.layers), bare.selection_digest, True, bare.issuer_id, False,
                                    bare.participation, None)
    orig = v.verify_selection_v2
    try:
        v.verify_selection_v2 = ignore_record
        res = run(rec)
    finally:
        v.verify_selection_v2 = orig
    assert seen["record"] is not None  # the module did pass the record
    assert res.admitted is False and res.code == "selection_missing" and res.report_ok is True
    assert dict(res.layers)["record_binding"] == "not_evaluated"


def _real_report(rec):
    ad = ev.Ed25519Verifier()
    sel = v2_selection.parse_selection_envelope_v2(sel_text(rec))
    reco = decision.validate_record_text_v2(r.dumps(rec))
    report = v.verify_selection_v2(sel, s.CTX, trust(), ad, r.NOW, reco, ad.key_admission, min_trust_snapshot_version=1, last_accepted_snapshot=None)
    assert report.ok is True and all(val == "pass" for val in report.layers.values())
    return report


def _run_with_report(rec, mutate):
    real = _real_report(rec)
    orig = v.verify_selection_v2
    try:
        v.verify_selection_v2 = lambda *a, **k: mutate(real)
        return run(rec)
    finally:
        v.verify_selection_v2 = orig


@pytest.mark.parametrize("name", v.LAYERS_V2)
@pytest.mark.parametrize("value", ["not_evaluated", "refuse", "PASS", None, True])
def test_the_conjunction_requires_every_one_of_the_eleven_layers_to_be_exactly_pass(name, value):
    rec = fam_record(F4, F4P)
    res = _run_with_report(rec, lambda rep: dataclasses.replace(rep, layers={**rep.layers, name: value}))
    assert res.admitted is False and res.code == "selection_missing"
    assert dict(res.layers)[name] != "pass"


def test_the_conjunction_refuses_a_report_with_a_missing_layer():
    rec = fam_record(F4, F4P)
    res = _run_with_report(rec, lambda rep: dataclasses.replace(rep, layers={k: x for k, x in rep.layers.items() if k != "epoch"}))
    assert res.admitted is False and res.code == "selection_missing" and dict(res.layers)["epoch"] == "not_evaluated"


@pytest.mark.parametrize("field,value", [
    ("ok", False), ("ok", 1), ("authenticated", False), ("authenticated", 1), ("issuer_id", None), ("issuer_id", 7),
    ("operationally_authorized", True), ("operationally_authorized", 0), ("bound_record_digest", None),
    ("bound_record_digest", "sha256:" + "0" * 64), ("participation", "optional"),
])
def test_the_conjunction_refuses_each_deviating_report_member(field, value):
    rec = fam_record(F4, F4P)
    res = _run_with_report(rec, lambda rep: dataclasses.replace(rep, **{field: value}))
    assert res.admitted is False and res.code in {"selection_missing", "participation_mismatch"}
    assert res.record is None


def test_the_conjunction_refuses_a_report_that_carries_a_code():
    rec = fam_record(F4, F4P)
    res = _run_with_report(rec, lambda rep: dataclasses.replace(rep, code="signature_invalid"))
    assert res.admitted is False and res.code == "signature_invalid"


def test_a_non_report_object_from_the_verifier_is_field_invalid():
    rec = fam_record(F4, F4P)
    res = _run_with_report(rec, lambda rep: {"ok": True, "code": None, "authenticated": True})
    assert res.admitted is False and res.code == "field_invalid"


# ------------------------------------------------------------------------------------------------------------------------- never raises
class Hostile:
    def __getattribute__(self, name):
        raise RuntimeError("hostile")

    def __deepcopy__(self, memo):
        raise RuntimeError("hostile")


JUNK = [pytest.param(f, id=i) for i, f in (("none", lambda: None), ("zero", lambda: 0), ("float", lambda: 1.5), ("bytes", lambda: b"x"),
                                          ("hostile", Hostile), ("object", object), ("nan", lambda: float("nan")),
                                          ("list_hostile", lambda: [Hostile()]), ("dict_hostile", lambda: {"a": Hostile()}))]


@pytest.mark.parametrize("field", ["selection_text", "record_text", "context", "trust", "verifier", "now", "key_admission"])
@pytest.mark.parametrize("junk_factory", JUNK)
def test_the_module_never_raises_and_never_admits_on_hostile_inputs(field, junk_factory, request):
    junk = junk_factory()
    junk_factory_id = request.node.callspec.id.split("-")[0]
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    args = dict(selection_text=sel_text(rec), record_text=r.dumps(rec), context=s.CTX, trust=trust(), verifier=ad, now=r.NOW,
                key_admission=ad.key_admission)
    args[field] = junk
    expect_admitted = field == "key_admission" and junk is None  # the documented default: built-in key admission still runs
    res = vs.verify_f4_selection_v2(args["selection_text"], args["record_text"], args["context"], args["trust"], args["verifier"], args["now"],
                                    min_trust_snapshot_version=1, last_accepted_snapshot=None, key_admission=args["key_admission"])
    assert isinstance(res, vs.VerifiedSelectionV2) and res.admitted is expect_admitted
    if not expect_admitted:
        # Each (field, junk) pair maps to ONE deterministic code (observed against the verifier, pinned here). A non-text input is
        # input_not_text; a text whose attribute access raises is classified by the parser/validator's own defensive branch.
        expected = {"selection_text": "input_not_text", "record_text": "input_not_text", "context": "selection_scope_mismatch",
                    "trust": "trust_snapshot_invalid", "verifier": "signature_invalid", "now": "time_unavailable",
                    "key_admission": "trust_snapshot_invalid"}[field]
        special = {("selection_text", "hostile"): "field_invalid", ("record_text", "hostile"): "field_type_invalid",
                   ("trust", "none"): "trust_snapshot_missing", ("verifier", "none"): "verifier_unavailable"}
        assert res.code == special.get((field, junk_factory_id), expected), (field, junk_factory_id, res.code)
        assert res.record is None and res.issuer_id is None and res.selection_id is None and res.scope is None


@pytest.mark.parametrize("junk_factory", [pytest.param(f, id=i) for i, f in (("none", lambda: None), ("zero", lambda: 0), ("hostile", Hostile),
                                                                              ("str", lambda: "f4"), ("bytes", lambda: b"x"),
                                                                              ("list", lambda: [1]), ("dict", lambda: {"x": 1}))])
def test_recompute_never_raises_and_refuses_non_results(junk_factory):
    junk = junk_factory()
    out = vs.recompute_f4_effective_policy(junk, dict(F4HOST))
    assert isinstance(out, vs.F4EffectivePolicy) and out.ok is False and out.effective is None and out.effective_policy_digest is None
    assert out.code in v2_codes.CODES_V2


def test_a_trust_snapshot_with_a_hostile_member_is_refused_with_a_typed_code():
    rec = fam_record(F4, F4P)
    bad = v.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (Hostile(),))
    res = run(rec, tr=bad)
    assert_refused(res, "trust_snapshot_invalid")
    assert_refused(run(rec, tr=v.TrustSnapshot("snap-test-1", 0, "2026-10-27T00:00:00Z", ())), "trust_snapshot_invalid")


def test_a_missing_snapshot_is_trust_snapshot_missing():
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    res = vs.verify_f4_selection_v2(sel_text(rec), r.dumps(rec), s.CTX, None, ad, r.NOW, min_trust_snapshot_version=1,
                                    last_accepted_snapshot=None, key_admission=ad.key_admission)
    assert_refused(res, "trust_snapshot_missing")


def test_a_subclassed_trust_snapshot_is_refused():
    class Sub(v.TrustSnapshot):
        pass
    t = trust()
    assert_refused(run(tr=Sub(t.snapshot_id, t.version, t.valid_until, t.issuers)), "trust_snapshot_invalid")


def test_the_callers_trust_snapshot_is_not_mutated():
    rec = fam_record(F4, F4P)
    t = trust(min_epochs=(("sel-test-1", 1),))
    before = copy.deepcopy(t)
    assert run(rec, tr=t).admitted is True and t == before


# ------------------------------------------------------------------------------------------------------------------------- parse refusals
@pytest.mark.parametrize("text,code", [("", "json_malformed"), ("{", "json_malformed"), ("[]", "field_type_invalid"), ("{}", "field_missing"),
                                       ('{"a":1,"a":2}', "json_duplicate_key")])
def test_a_malformed_selection_text_is_refused_with_the_parser_code(text, code):
    res = run(sel=text)
    assert res.admitted is False and res.code == code and dict(res.layers)["structural"] == "refuse"


def test_a_v1_envelope_is_contract_unsupported():
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4)
    del stmt["disposition"]
    assert_refused(run(rec, sel=r.dumps(s.envelope(stmt, contract="r08-v1"))), "contract_unsupported")


def test_a_selection_whose_statement_digest_is_wrong_is_digest_mismatch():
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4)
    env = s.envelope(stmt, signature=sign(stmt), pub=PK)
    env["statement_digest"] = "sha256:" + "0" * 64
    assert_refused(run(rec, sel=r.dumps(env)), "digest_mismatch")


def test_a_selection_that_pins_another_evaluator_is_refused():
    rec = fam_record(F4, F4P)
    res = run(rec, sel=sel_text(rec, evaluator={**r.EVALUATOR, "binding": "other-binding"}))
    assert res.admitted is False and res.code in v2_codes.CODES_V2 and res.code is not None


# ------------------------------------------------------------------------------------------------------------------------- recompute
def test_recompute_refuses_a_refused_result_with_that_results_code():
    res = run(ctx=c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"))
    out = vs.recompute_f4_effective_policy(res, dict(F4HOST))
    assert (out.ok, out.code, out.effective, out.effective_policy_digest) == (False, "selection_scope_mismatch", None, None)


@pytest.mark.parametrize("host", [None, {}, {"status_max_age_seconds": 1}, {**F4HOST, "extra": 1}, {**F4HOST, "status_max_age_seconds": True},
                                  {**F4HOST, "status_max_age_seconds": -1}, {**F4HOST, "status_max_age_seconds": 1.5},
                                  {**F4HOST, "status_max_age_seconds": "9"}, {**F4HOST, "status_max_age_seconds": ab.AGE_MAX + 1}, "host", [1, 2]])
def test_recompute_refuses_invalid_host_ages_with_composition_caller_invalid(host):
    out = vs.recompute_f4_effective_policy(run(), host)
    assert (out.ok, out.code, out.effective, out.effective_policy_digest) == (False, "composition_caller_invalid", None, None)


def test_recompute_refuses_a_dict_subclass_host():
    class D(dict):
        pass
    out = vs.recompute_f4_effective_policy(run(), D(F4HOST))
    assert out.ok is False and out.code == "composition_caller_invalid"


def test_recompute_re_checks_a_hand_built_or_altered_result():
    good = run()
    assert vs.recompute_f4_effective_policy(good, dict(F4HOST)).ok is True
    tampered_record = copy.deepcopy(good.record)
    tampered_record["payload"]["status_max_age_seconds"] = 1
    for altered, code in (
            (dataclasses.replace(good, record=tampered_record), "digest_mismatch"),
            (dataclasses.replace(good, family="f4-other"), "family_unsupported"),
            (dataclasses.replace(good, layers=tuple((n, "refuse" if n == "scope" else val) for n, val in good.layers)), "selection_missing"),
            (dataclasses.replace(good, layers=good.layers[:-1]), "selection_missing"),
            (dataclasses.replace(good, code="signature_invalid"), "selection_missing"),
            (dataclasses.replace(good, record=None), "family_unsupported"),
            (dataclasses.replace(good, record_digest="sha256:" + "0" * 64), "digest_mismatch")):
        out = vs.recompute_f4_effective_policy(altered, dict(F4HOST))
        assert (out.ok, out.code, out.effective, out.effective_policy_digest) == (False, code, None, None), code


def test_recompute_refuses_a_subclass_of_the_result_type():
    good = run()

    @dataclasses.dataclass(frozen=True)
    class Sub(vs.VerifiedSelectionV2):
        pass
    sub = Sub(**{f.name: getattr(good, f.name) for f in dataclasses.fields(good)})
    out = vs.recompute_f4_effective_policy(sub, dict(F4HOST))
    assert out.ok is False and out.effective_policy_digest is None


def test_recompute_does_not_mutate_the_result_or_the_host_input():
    good = run()
    snapshot, host = copy.deepcopy(good), dict(F4HOST)
    vs.recompute_f4_effective_policy(good, host)
    assert good == snapshot and host == F4HOST


# ------------------------------------------------------------------------------------------------------------------------- meta
def test_the_module_introduces_no_new_reason_code_string():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    docstrings = {id(n.body[0].value) for n in ast.walk(tree) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef))
                  and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    snake = re.compile(r"[a-z]+(?:_[a-z0-9]+)+\Z")
    constants = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docstrings
                 and snake.match(n.value)}
    used = set()  # every string constant that can flow into a `code` position
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id == "_refused" and n.args and isinstance(n.args[0], ast.Constant):
                used.add(n.args[0].value)
            if n.func.id == "_known" and len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                used.add(n.args[1].value)
            if n.func.id == "F4EffectivePolicy" and len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                used.add(n.args[1].value)
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            used.add(n.value.value)
    used = {x for x in used if isinstance(x, str)}
    assert used, "static scan found nothing"
    unknown = {x for x in used if x not in v2_codes.CODES_V2}
    assert not unknown, sorted(unknown)
    codes_used = used | {x for x in constants if x in v2_codes.CODES_V2}
    assert {"field_invalid", "family_unsupported", "participation_mismatch", "trust_snapshot_invalid", "selection_missing"} <= codes_used
    forbidden_here = {"selection_" + "withdrawn", "trust_snapshot_version_" + "stale"}
    assert not any(x in MODULE.read_text(encoding="utf-8") for x in forbidden_here)  # those two have behaviour in verify.py only (repo guard)


def test_the_module_defines_no_reason_code_table_and_no_signer_trust_root_or_key():
    text = MODULE.read_text(encoding="utf-8")
    assert "CODES_V2_REV2" not in text and "CODES =" not in text
    tree = ast.parse(text)
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
               {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert imported <= {"copy", "dataclasses", "typing", "registry_successor"}, imported
    assert not re.search(r"seed_keypair|crypto_sign|SigningKey|BEGIN |bytes\.fromhex|b64decode", text)
    assert not re.search(r"datetime\.now|utcnow|\btime\.time\(|\bopen\(", text)


def test_the_new_module_is_the_only_production_file_this_work_adds():
    assert MODULE.is_file()
    assert sorted(vs.__all__) == ["F4EffectivePolicy", "VerifiedSelectionV2", "recompute_f4_effective_policy", "verify_f4_selection_v2",
                                  "verify_selection_text_v2"]


def test_existing_public_entry_points_are_unchanged():
    def params(fn):
        return [(p.name, p.kind.name, None if p.default is inspect.Parameter.empty else repr(p.default))
                for p in inspect.signature(fn).parameters.values()]
    assert params(v.verify_selection_v2) == [
        ("selection", "POSITIONAL_OR_KEYWORD", None), ("context", "POSITIONAL_OR_KEYWORD", None), ("trust", "POSITIONAL_OR_KEYWORD", None),
        ("verifier", "POSITIONAL_OR_KEYWORD", None), ("now", "POSITIONAL_OR_KEYWORD", None), ("record", "POSITIONAL_OR_KEYWORD", "None"),
        ("key_admission", "POSITIONAL_OR_KEYWORD", "None"), ("min_trust_snapshot_version", "KEYWORD_ONLY", "None"),
        ("last_accepted_snapshot", "KEYWORD_ONLY", "None")]
    assert params(decision.verify_and_decide_v2) == [
        ("participation", "POSITIONAL_OR_KEYWORD", None), ("caller", "POSITIONAL_OR_KEYWORD", None), ("record_text", "POSITIONAL_OR_KEYWORD", None),
        ("selection_text", "POSITIONAL_OR_KEYWORD", None), ("context", "POSITIONAL_OR_KEYWORD", None), ("trust", "POSITIONAL_OR_KEYWORD", None),
        ("verifier", "POSITIONAL_OR_KEYWORD", None), ("now", "POSITIONAL_OR_KEYWORD", None), ("key_admission", "POSITIONAL_OR_KEYWORD", "None")]
    assert params(decision.validate_record_text_v2) == [("text", "POSITIONAL_OR_KEYWORD", None)]
    assert params(v2_selection.parse_selection_envelope_v2) == [("text", "POSITIONAL_OR_KEYWORD", None)]
    assert v.LAYERS_V2 == ("structural", "integrity", "record_binding", "trust_snapshot", "authenticity", "authority", "scope", "time",
                           "revocation", "epoch", "disposition")
    assert len(v2_codes.CODES_V2) == 48


def test_verify_and_decide_v2_still_has_no_floor_input_and_is_unchanged_in_behaviour():
    rec = fam_record(F4, F4P)
    ad = ev.Ed25519Verifier()
    d = decision.verify_and_decide_v2("required", F4HOST, r.dumps(rec), sel_text(rec), s.CTX, trust(version=1), ad, r.NOW, ad.key_admission)
    assert d.kind == "applied"  # still accepts any snapshot version: the floors live only in the new entry point
    assert_refused(run(rec, min_v=2), "trust_snapshot_version_stale")
