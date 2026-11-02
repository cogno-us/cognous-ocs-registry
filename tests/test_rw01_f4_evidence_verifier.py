"""RW-01-F4-PoC (Registry side): tests for registry_consumer/evidence_verifier.py, the adapter an enforcing consumer constructs
(BUILDER_TESTED; not independently qualified). MECHANISM TESTS ONLY with SYNTHETIC test seeds (helpers are shared with
tests/test_rw01_f4_verified_selection.py). Claim A only; claim B not made. Real Ed25519 (PyNaCl) signs every selection.
Every negative asserts the SPECIFIC code and ok False (and that no admission members leak). N-numbers follow the sprint register.
"""
import ast
import copy
import datetime
import hashlib
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_successor import v2_age_bounds as ab  # noqa: E402
from registry_successor import v2_codes  # noqa: E402
from registry_successor import v2_policy_identity as pid  # noqa: E402
from registry_successor import verify as v  # noqa: E402

try:
    import nacl.bindings  # noqa: F401
    from registry_adapters import ed25519_verifier as ev
    from registry_consumer import evidence_verifier as adapter_mod
    from registry_consumer.evidence_verifier import RegistryEvidenceVerifierV2
    from test_rw01_f4_verified_selection import F4, F4P, F4HOST, OTHER_SK, fam_record, sel_text, trust
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    HAVE_BACKEND = False

pytestmark = pytest.mark.skipif(not HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")
MODULE = Path(__file__).resolve().parent.parent / "registry_consumer" / "evidence_verifier.py"
UTC = datetime.timezone.utc
T = datetime.datetime(2026, 10, 25, 12, 0, 0, tzinfo=UTC)
LAYERS = v.LAYERS_V2


def make_adapter():
    ad = ev.Ed25519Verifier()
    return RegistryEvidenceVerifierV2(ad, ad.key_admission)


def request(rec=None, **over):
    rec = rec if rec is not None else fam_record(F4, F4P)
    req = {
        "contract": adapter_mod.REQUEST_CONTRACT, "family": F4, "registry_contract": "r08-v2", "selection_text": sel_text(rec),
        "record_text": r.dumps(rec),
        "expected_context": {"consumer_id": "consumer-test", "tenant": "tenant-a", "institution": "inst-a", "authority_domain": "domain-a",
                             "operation": "op-test"},
        "expected_operation_id": "op-test", "trust_snapshot": trust(), "verification_time": T, "verification_time_utc": "2026-10-25T12:00:00Z",
        "min_trust_snapshot_version": 1, "last_accepted_snapshot": None, "host_policy": dict(F4HOST)}
    req.update(over)
    return req


def assert_refused(verdict, code, authenticated=None):
    assert verdict["ok"] is False and verdict["code"] == code, verdict
    assert verdict["code"] in v2_codes.CODES_V2
    assert set(verdict) == adapter_mod.VERDICT_KEYS
    for k in ("issuer_id", "selection_id", "epoch", "selection_digest", "bound_record_digest", "effective_policy_digest", "effective_values"):
        assert verdict[k] is None, k
    if authenticated is not None:
        assert verdict["authenticated"] is authenticated


# ----------------------------------------------------------------------------------------------------------------- positive / schema
def test_n01_valid_request_gives_an_ok_verdict_with_the_exact_schema():
    rec = fam_record(F4, F4P)
    req = request(rec)
    out = make_adapter().verify_selection_evidence(req)
    assert set(out) == adapter_mod.VERDICT_KEYS and "key_id" not in out
    assert out["contract"] == "registry-evidence-verdict/0.1" and out["ok"] is True and out["code"] is None and out["authenticated"] is True
    assert list(out["layers"]) == list(LAYERS) and all(x == "pass" for x in out["layers"].values())
    assert (out["family"], out["registry_contract"], out["verification_time_utc"]) == (F4, "r08-v2", "2026-10-25T12:00:00Z")
    assert out["selection_text_sha256"] == hashlib.sha256(req["selection_text"].encode("utf-8")).hexdigest() and len(out["selection_text_sha256"]) == 64
    assert out["record_text_sha256"] == hashlib.sha256(req["record_text"].encode("utf-8")).hexdigest()
    assert not out["selection_text_sha256"].startswith("sha256:")
    assert (out["trust_snapshot_id"], out["trust_snapshot_version"]) == ("snap-test-1", 1)
    assert out["trust_snapshot_fingerprint"] == pid.trust_snapshot_fingerprint_from_verified(trust())
    assert out["floors_applied"] == {"min_trust_snapshot_version": True, "last_accepted_snapshot": False}
    assert out["epoch_floor_applied"] is False
    assert (out["issuer_id"], out["selection_id"], out["epoch"]) == ("issuer-test-1", "sel-test-1", 1)
    assert out["selection_digest"] == s.c.digest(r.make_statement_v2(rec, family=F4))
    assert out["bound_record_digest"] == rec["record_digest"]
    assert out["effective_values"] == {"status_max_age_seconds": 120, "approval_max_age_seconds": 600}
    assert out["effective_policy_digest"] == pid.effective_policy_digest(F4, out["effective_values"])
    assert out["verifier_implementation"]["name"] and out["verifier_implementation"]["registry_revision"]


def test_the_request_is_not_mutated_and_the_verdict_is_a_fresh_plain_dict():
    req = request()
    snapshot = copy.copy(req)
    out = make_adapter().verify_selection_evidence(req)
    assert req.keys() == snapshot.keys() and all(req[k] is snapshot[k] for k in req)
    out["layers"]["scope"] = "refuse"
    out["verifier_implementation"]["name"] = "x"
    assert make_adapter().verify_selection_evidence(req)["layers"]["scope"] == "pass"
    assert adapter_mod.IMPLEMENTATION["name"] == "registry-evidence-verifier-v2"


def test_last_accepted_snapshot_list_form_is_applied_and_echoed():
    fp = pid.trust_snapshot_fingerprint_from_verified(trust())
    out = make_adapter().verify_selection_evidence(request(last_accepted_snapshot=[1, fp]))
    assert out["ok"] is True and out["floors_applied"] == {"min_trust_snapshot_version": True, "last_accepted_snapshot": True}
    bad = make_adapter().verify_selection_evidence(request(last_accepted_snapshot=[1, "sha256:" + "0" * 64]))
    assert bad["ok"] is False and bad["code"] == "trust_snapshot_version_stale"


def test_epoch_floor_applied_is_reported():
    out = make_adapter().verify_selection_evidence(request(trust_snapshot=trust(min_epochs=(("sel-test-1", 1),))))
    assert out["ok"] is True and out["epoch_floor_applied"] is True


def test_effective_values_follow_the_operator_host_policy_not_the_record():
    out = make_adapter().verify_selection_evidence(request(host_policy={"status_max_age_seconds": 60, "approval_max_age_seconds": 30}))
    assert out["ok"] is True and out["effective_values"] == {"status_max_age_seconds": 60, "approval_max_age_seconds": 30}


# ----------------------------------------------------------------------------------------------------------------- negatives
def test_n02_forged_signature():
    rec = fam_record(F4, F4P)
    req = request(rec, selection_text=sel_text(rec, sk=OTHER_SK))
    assert_refused(make_adapter().verify_selection_evidence(req), "signature_invalid", False)


def test_n03_unknown_signer():
    rec = fam_record(F4, F4P)
    assert_refused(make_adapter().verify_selection_evidence(request(rec, selection_text=sel_text(rec, key_id="key-unknown-9"))), "issuer_untrusted")


def test_n05_wrong_tenant():
    ctx = dict(request()["expected_context"], tenant="tenant-b")
    assert_refused(make_adapter().verify_selection_evidence(request(expected_context=ctx)), "selection_scope_mismatch")


def test_n06_operation_in_the_signed_statement_differs_from_the_operator_context():
    ctx = dict(request()["expected_context"], operation="op-other")
    assert_refused(make_adapter().verify_selection_evidence(request(expected_context=ctx, expected_operation_id="op-other")),
                   "selection_operation_mismatch")


def test_n06_adapter_operation_id_must_equal_the_context_operation_even_when_the_signature_would_pass():
    out = make_adapter().verify_selection_evidence(request(expected_operation_id="op-other"))
    assert_refused(out, "selection_operation_mismatch")
    assert all(x == "not_evaluated" for x in out["layers"].values())  # refused before any verification


def test_n08_substituted_record():
    other = fam_record(F4, {"status_max_age_seconds": 9000, "approval_max_age_seconds": 9000})
    assert_refused(make_adapter().verify_selection_evidence(request(record_text=r.dumps(other))), "record_digest_mismatch")


def test_n12_revoked_key():
    assert_refused(make_adapter().verify_selection_evidence(request(trust_snapshot=trust(revoked_key_ids=frozenset({s.KEY_ID})))), "issuer_key_revoked")


def test_n14_below_min_epoch_and_below_snapshot_floor():
    assert_refused(make_adapter().verify_selection_evidence(request(trust_snapshot=trust(min_epochs=(("sel-test-1", 2),)))), "selection_epoch_stale")
    assert_refused(make_adapter().verify_selection_evidence(request(min_trust_snapshot_version=2)), "trust_snapshot_version_stale")


def test_n15_expiry_at_the_explicit_time():
    late = datetime.datetime(2026, 10, 27, 0, 0, 0, tzinfo=UTC)
    assert_refused(make_adapter().verify_selection_evidence(request(verification_time=late, verification_time_utc="2026-10-27T00:00:00Z")),
                   "trust_snapshot_expired")
    mid = datetime.datetime(2026, 10, 26, 0, 0, 0, tzinfo=UTC)
    assert_refused(make_adapter().verify_selection_evidence(request(verification_time=mid, verification_time_utc="2026-10-26T00:00:00Z")),
                   "selection_expired")


def test_n20_authenticated_true_with_ok_false_is_reported_but_not_ok():
    ctx = dict(request()["expected_context"], tenant="tenant-b")
    out = make_adapter().verify_selection_evidence(request(expected_context=ctx))
    assert_refused(out, "selection_scope_mismatch", True)
    assert out["ok"] is False


def test_n21_wrong_family_and_registry_contract():
    assert_refused(make_adapter().verify_selection_evidence(request(family="f1ab-five-set")), "family_unsupported")
    assert_refused(make_adapter().verify_selection_evidence(request(registry_contract="r08-v3")), "contract_unsupported")
    assert_refused(make_adapter().verify_selection_evidence(request(contract="registry-evidence-verification-request/9.9")), "contract_unsupported")


def test_n19_non_ascii_through_the_adapter():
    import base64, json
    import nacl.bindings as nb
    from registry_successor import common as c
    from registry_successor import verify as vv
    from test_rw01_f4_verified_selection import PK, SK
    tenant = "ténant-a"
    rec = fam_record(F4, F4P)
    stmt = r.make_statement_v2(rec, family=F4, scope={"tenant": tenant, "institution": "inst-a", "authority_domain": "domain-a"})
    grant = vv.AuthorityGrant("consumer-test", tenant, "inst-a", "domain-a", "op-test")
    tr = vv.TrustSnapshot("snap-test-1", 1, "2026-10-27T00:00:00Z", (vv.IssuerEntry(s.KEY_ID, "issuer-test-1", "ed25519", PK, (grant,)),))
    ctx = dict(request()["expected_context"], tenant=tenant)

    def text(message):
        sig = base64.b64encode(nb.crypto_sign(message, SK)[:64]).decode("ascii")
        return r.dumps(s.envelope(stmt, signature=sig, pub=PK))
    good = s.V2_DOMAIN + c.canonical_bytes(stmt)
    bad = s.V2_DOMAIN + json.dumps(stmt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    out = make_adapter().verify_selection_evidence(request(rec, selection_text=text(good), trust_snapshot=tr, expected_context=ctx))
    assert out["ok"] is True
    assert_refused(make_adapter().verify_selection_evidence(request(rec, selection_text=text(bad), trust_snapshot=tr, expected_context=ctx)),
                   "signature_invalid")


# ----------------------------------------------------------------------------------------------------------------- pins / N16 / N28
class SubVerifier(ev.Ed25519Verifier if HAVE_BACKEND else object):
    pass


class FakeVerifier:
    def verify(self, alg, public_key, message, signature):
        return True

    def key_admission(self, alg, public_key):
        return True


def test_exact_type_pin_refuses_a_subclass_a_fake_and_junk():
    sub = SubVerifier()
    for bad in (sub, FakeVerifier(), object(), "verifier", ev.Ed25519Verifier):
        with pytest.raises(TypeError):
            RegistryEvidenceVerifierV2(bad, getattr(bad, "key_admission", None))
    ad = ev.Ed25519Verifier()
    for bad_ka in (None, lambda a, k: True, ev.Ed25519Verifier().key_admission, FakeVerifier().key_admission):
        with pytest.raises(TypeError):
            RegistryEvidenceVerifierV2(ad, bad_ka)
    with pytest.raises(TypeError):
        RegistryEvidenceVerifierV2(None, ad.key_admission)


def test_n16_a_fake_verifier_cannot_be_smuggled_in_and_the_adapter_has_no_verdict_input():
    assert list(inspect.signature(RegistryEvidenceVerifierV2.__init__).parameters) == ["self", "verifier", "key_admission"]
    assert list(inspect.signature(RegistryEvidenceVerifierV2.verify_selection_evidence).parameters) == ["self", "request"]
    names = {n for m in ("__init__", "verify_selection_evidence", "load") for n in inspect.signature(getattr(RegistryEvidenceVerifierV2, m)).parameters}
    assert not names & {"verdict", "report", "ok", "authenticated", "layers", "admitted", "verified"}
    # injected verdict-shaped members are an unknown/extra request key, and verdict-shaped values in place of texts are refused
    forged = request(verdict={"ok": True, "code": None, "authenticated": True})
    assert_refused(make_adapter().verify_selection_evidence(forged), "field_invalid")
    assert_refused(make_adapter().verify_selection_evidence(request(selection_text={"ok": True, "authenticated": True})), "input_not_text")
    assert_refused(make_adapter().verify_selection_evidence(request(trust_snapshot={"ok": True})), "trust_snapshot_invalid")


def test_n28_ed25519_unavailable_yields_verifier_unavailable_never_ok(monkeypatch):
    def broken():
        raise ev.Ed25519Unavailable("simulated")
    monkeypatch.setattr(ev, "_load_backend", broken)
    adapter = RegistryEvidenceVerifierV2.load()
    out = adapter.verify_selection_evidence(request())
    assert_refused(out, "verifier_unavailable", False)
    assert out["layers"]["authenticity"] == "not_evaluated"


def test_n28_an_explicitly_unavailable_adapter_never_returns_ok():
    out = RegistryEvidenceVerifierV2(None, None).verify_selection_evidence(request())
    assert_refused(out, "verifier_unavailable")


def test_load_returns_a_working_adapter_when_the_backend_is_available():
    assert RegistryEvidenceVerifierV2.load().verify_selection_evidence(request())["ok"] is True


# ----------------------------------------------------------------------------------------------------------------- request validation
@pytest.mark.parametrize("name", sorted(adapter_mod.REQUEST_KEYS) if HAVE_BACKEND else [])
def test_each_missing_request_key_is_field_invalid(name):
    req = request()
    del req[name]
    assert_refused(make_adapter().verify_selection_evidence(req), "field_invalid")


@pytest.mark.parametrize("bad", [None, [], "req", 7, b"x"])
def test_a_non_dict_request_is_field_invalid(bad):
    assert_refused(make_adapter().verify_selection_evidence(bad), "field_invalid")


def test_a_dict_subclass_request_is_field_invalid():
    class D(dict):
        pass
    assert_refused(make_adapter().verify_selection_evidence(D(request())), "field_invalid")


@pytest.mark.parametrize("host", [None, {}, {"status_max_age_seconds": 1}, {"status_max_age_seconds": 1, "approval_max_age_seconds": 2, "x": 3},
                                  {"status_max_age_seconds": True, "approval_max_age_seconds": 2}, {"status_max_age_seconds": -1, "approval_max_age_seconds": 2},
                                  {"status_max_age_seconds": "1", "approval_max_age_seconds": 2}, "host"])
def test_invalid_host_policy_is_refused_with_composition_caller_invalid(host):
    out = make_adapter().verify_selection_evidence(request(host_policy=host))
    assert_refused(out, "composition_caller_invalid")


@pytest.mark.parametrize("when,when_utc", [
    (None, "2026-10-25T12:00:00Z"), ("2026-10-25T12:00:00Z", "2026-10-25T12:00:00Z"), (datetime.datetime(2026, 10, 25, 12, 0, 0), "2026-10-25T12:00:00Z"),
    (T, "2026-10-25T12:00:01Z"), (T, "2026-10-25T12:00:00+00:00"), (T, None), (T.replace(microsecond=5), "2026-10-25T12:00:00Z")])
def test_invalid_verification_time_fields_are_time_unavailable(when, when_utc):
    assert_refused(make_adapter().verify_selection_evidence(request(verification_time=when, verification_time_utc=when_utc)), "time_unavailable")


def test_a_non_utc_offset_time_is_accepted_when_the_utc_string_matches():
    tz = datetime.timezone(datetime.timedelta(hours=2))
    out = make_adapter().verify_selection_evidence(request(verification_time=T.astimezone(tz), verification_time_utc="2026-10-25T12:00:00Z"))
    assert out["ok"] is True


@pytest.mark.parametrize("bad", [0, -1, True, "1", None, 1.0])
def test_invalid_min_trust_snapshot_version_is_trust_snapshot_invalid(bad):
    out = make_adapter().verify_selection_evidence(request(min_trust_snapshot_version=bad))
    assert_refused(out, "trust_snapshot_invalid")
    assert out["floors_applied"] == {"min_trust_snapshot_version": False, "last_accepted_snapshot": False}


@pytest.mark.parametrize("bad", [[1], [1, 2], (0, "sha256:" + "0" * 64), "x", {}, [True, "sha256:" + "0" * 64], [1, "bad"]])
def test_invalid_last_accepted_snapshot_is_trust_snapshot_invalid(bad):
    assert_refused(make_adapter().verify_selection_evidence(request(last_accepted_snapshot=bad)), "trust_snapshot_invalid")


@pytest.mark.parametrize("key,bad", [("expected_context", None), ("expected_context", {"consumer_id": "c"}), ("expected_operation_id", 5),
                                     ("expected_context", {"consumer_id": "consumer-test", "tenant": 1, "institution": "inst-a",
                                                           "authority_domain": "domain-a", "operation": "op-test"})])
def test_invalid_context_members(key, bad):
    code = "selection_operation_mismatch" if key == "expected_operation_id" else "selection_scope_mismatch"
    assert_refused(make_adapter().verify_selection_evidence(request(**{key: bad})), code)


def test_the_adapter_never_raises_on_hostile_members():
    class Hostile:
        def __getattribute__(self, name):
            raise RuntimeError("hostile")
    for key in sorted(adapter_mod.REQUEST_KEYS):
        out = make_adapter().verify_selection_evidence(request(**{key: Hostile()}))
        assert out["ok"] is False and out["code"] in v2_codes.CODES_V2 and set(out) == adapter_mod.VERDICT_KEYS, key


def test_a_text_that_cannot_be_utf8_encoded_is_refused_without_an_exception():
    out = make_adapter().verify_selection_evidence(request(selection_text="\ud800"))
    assert out["ok"] is False and out["code"] in v2_codes.CODES_V2 and out["selection_text_sha256"] is None


# ----------------------------------------------------------------------------------------------------------------- module shape
def test_the_adapter_module_imports_only_the_two_allowed_first_party_packages():
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names} | \
               {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert imported <= {"datetime", "hashlib", "typing", "registry_adapters", "registry_successor"}, imported
    assert {"registry_adapters", "registry_successor"} <= imported
    assert not any(isinstance(n, ast.ImportFrom) and n.level for n in ast.walk(tree))


def test_the_adapter_has_no_signer_key_material_clock_or_new_code():
    text = MODULE.read_text(encoding="utf-8")
    import re
    assert not re.search(r"seed_keypair|crypto_sign|SigningKey|BEGIN |datetime\.now|utcnow|\btime\.time\(|\bopen\(|key_id", text.replace("key_admission", ""))
    tree = ast.parse(text)
    used = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_Refusal" and n.args and isinstance(n.args[0], ast.Constant):
            used.add(n.args[0].value)
    used |= {"field_invalid"}
    assert used and used <= set(v2_codes.CODES_V2), sorted(used - set(v2_codes.CODES_V2))
    assert "selection_" + "withdrawn" not in text and "trust_snapshot_version_" + "stale" not in text
    assert "CODES_V2_REV2" not in text


def test_the_core_modules_still_do_not_import_the_adapter_or_the_backend():
    root = MODULE.parent.parent
    for path in (root / "registry_successor").glob("*.py"):
        assert "registry_adapters" not in path.read_text(encoding="utf-8"), path.name
