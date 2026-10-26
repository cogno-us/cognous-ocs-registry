"""V01a tests: the public r08-v2 decision path must accept a valid `f1ab` five-set record (BUILDER_TESTED; not independently qualified).

PREDECLARED ORACLES (committed before any source change; expected outcome at baseline `17675ee1` in the right-hand column):

  V1A-01  valid signed f1ab selection + record -> kind `applied`, exact five-set intersection   | baseline: FAIL (composition_record_invalid)
  V1A-02  narrowing: caller units {u-read,u-write}, record units {u-read} -> effective units (u-read,) | baseline: FAIL
  V1A-03  empty record set -> `applied_deny_all`, field listed, never the caller policy         | baseline: FAIL
  V1A-04  malformed record (missing / unknown / unsorted / non-JSON) -> `required_policy_unavailable`; validator returns the typed code, decision returns `composition_record_invalid` (corrected, see below) | baseline: wrong codes
  V1A-05  forged signature / wrong-key signature -> `signature_invalid`, no policy             | baseline: PASS (refusal)
  V1A-06  record altered after signing -> validator `digest_mismatch`; decision `composition_record_invalid`; resealed -> `record_digest_mismatch`                            | baseline: refusal (wrong cause)
  V1A-07  authenticated withdrawal -> `selection_withdrawn`, no policy                          | baseline: PASS
  V1A-08  expired selection / expired trust snapshot -> `selection_expired` / `trust_snapshot_expired` | baseline: PASS
  V1A-09  wrong tenant / consumer / operation -> `selection_scope_mismatch` / `selection_consumer_mismatch` / `selection_operation_mismatch` | PASS
  V1A-10  selection pins record A, record B supplied -> `record_identity_mismatch`/`record_digest_mismatch` | wrong cause at baseline
  V1A-11  r08-v1 entry points unchanged: f1ab record at v1 -> refusal; v1 f1a record at v1 entry -> applied | PASS (guard)
  V1A-12  v2 record validator refuses an r08-v1 document, v1 validator refuses an r08-v2 document (no cross acceptance) | guard
  V1A-13  the v2 decision calls the one existing verifier `verify_selection_v2` (no second verifier)  | guard
  V1A-14  `operationally_authorized` is False on every outcome; refusals never return the caller policy under `required` | guard
  V1A-16  STRICT SEPARATION: r08-v1 record at the v2 entry -> validator `contract_unsupported`, decision `composition_record_invalid`; r08-v2 record at the v1 entry refuses; r08-v1 f1ab unsupported; r08-v2 f1a accepted at v2 | baseline: FAIL (v1 f1a was accepted at v2)
  V1A-15  optional participation: any refusal leaves `overlay_not_applied` (not an application) | guard

ACTUAL baseline result at `17675ee1` (unchanged source, recorded before the fix): 19 failed, 5 passed. The failing set includes cases the
right-hand column predicted would pass: the f1ab record is refused at record validation (family_unsupported/contract_unsupported, surfacing as
composition_record_invalid), so the specific selection-layer codes are never reached. The 5 passing are the guards (V1A-11, V1A-14, V1A-15, V1A-07's
and V1A-12's non-record parts).

Real synthetic Ed25519 (PyNaCl from requirements-ed25519.lock.txt) signs every selection here; where PyNaCl is absent the module is
reported NOT RUN (skipped with a reason), never passed with a double.
"""
import base64
import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import decision  # noqa: E402
from registry_successor import record as record_mod  # noqa: E402
from registry_successor import verify as v  # noqa: E402
from registry_successor import v2_f1ab as f  # noqa: E402

try:
    import nacl.bindings as nb
    from registry_adapters import ed25519_verifier as ev
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    HAVE_BACKEND = False

pytestmark = pytest.mark.skipif(not HAVE_BACKEND, reason="NOT RUN: pynacl not installed (requirements-ed25519.lock.txt)")

FIELDS = f.F1AB_FIELDS
PK, SK = (nb.crypto_sign_seed_keypair(bytes(range(32))) if HAVE_BACKEND else (None, None))
OTHER_PK, OTHER_SK = (nb.crypto_sign_seed_keypair(bytes(range(1, 33))) if HAVE_BACKEND else (None, None))


def payload(**over):
    p = {"allowed_actions": ["act-copy", "act-list"], "allowed_adapters": ["a-local"], "allowed_units": ["u-read"],
         "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"]}
    p.update(over)
    return p


def caller(**over):
    p = {"allowed_actions": ["act-copy", "act-list", "act-other"], "allowed_adapters": ["a-local", "a-other"],
         "allowed_units": ["u-read", "u-write"], "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"]}
    p.update(over)
    return p


def record(pl=None, **over):
    body = dict(r.make_record(), contract_version="r08-v2", family=f.FAMILY_F1AB, record_id="f1ab-test-record",
                payload=pl if pl is not None else payload())
    body.update(over)
    return r.seal_record(body)


def sign(statement, sk=None, domain=None):
    msg = (domain or s.V2_DOMAIN) + c.canonical_bytes(statement)
    return base64.b64encode(nb.crypto_sign(msg, sk or SK)[:64]).decode("ascii")


def selection_text(rec, sk=None, pub=None, **over):
    stmt = r.make_statement_v2(rec, family=f.FAMILY_F1AB, **over)
    return r.dumps(s.envelope(stmt, signature=sign(stmt, sk), pub=pub or PK))


def decide(participation="required", rec=None, sel=None, ctx=None, trust=None, now=None, cl=None, record_text=None):
    rec = rec if rec is not None else record()
    ad = ev.Ed25519Verifier()
    return decision.verify_and_decide_v2(
        participation, cl if cl is not None else caller(), record_text if record_text is not None else r.dumps(rec),
        sel if sel is not None else selection_text(rec), ctx or s.CTX, trust or s.trust(pub=PK), ad, now or r.NOW, ad.key_admission)


def assert_refused(d, code):
    assert d.kind == "required_policy_unavailable", d
    assert d.code == code, d
    assert d.effective is None and d.caller_unchanged is False and d.operationally_authorized is False


# ---- V1A-01 / 02 / 03
def test_v1a_01_valid_f1ab_is_applied_with_exact_intersection():
    d = decide()
    assert d.kind == "applied" and d.code is None, d
    assert d.effective == {"allowed_actions": ("act-copy", "act-list"), "allowed_adapters": ("a-local",), "allowed_units": ("u-read",),
                           "allowed_institutions": ("inst-a",), "allowed_authority_domains": ("domain-a",)}
    assert d.deny_all is False and d.operationally_authorized is False
    for k in FIELDS:  # never wider than caller or record
        assert set(d.effective[k]) <= set(caller()[k]) and set(d.effective[k]) <= set(payload()[k])


def test_v1a_02_narrowing_removes_u_write():
    d = decide(cl=caller(allowed_units=["u-read", "u-write"]), rec=record(payload(allowed_units=["u-read"])))
    assert d.kind == "applied" and d.effective["allowed_units"] == ("u-read",)


def test_v1a_03_empty_set_is_explicit_deny_all():
    d = decide(rec=record(payload(allowed_units=[])))
    assert d.kind == "applied_deny_all" and d.deny_all is True and d.deny_all_fields == ("allowed_units",)
    assert d.effective["allowed_units"] == () and d.operationally_authorized is False


# ---- V1A-04 malformed record
@pytest.mark.parametrize("mutate,code", [
    (lambda p: p.pop("allowed_institutions"), "field_missing"),
    (lambda p: p.update(allowed_amount=["x"]), "field_unknown"),
    (lambda p: p.update(allowed_units=["u-write", "u-read"]), "field_invalid"),
    (lambda p: p.update(allowed_units="u-read"), "field_type_invalid"),
])
def test_v1a_04_malformed_payload_refuses_with_typed_code(mutate, code):
    # ORACLE CORRECTION (recorded in the second commit): the predeclared expectation was the typed shape code at the DECISION level. The
    # frozen r08-v1 behaviour, kept unchanged for v2, reports any invalid record as `composition_record_invalid` at the decision (the
    # verifier's record_binding layer wins) while the typed shape code is the VALIDATOR's result. Both levels are asserted here.
    pl = payload()
    mutate(pl)
    rec = record(pl)
    assert decision.validate_record_text_v2(r.dumps(rec)).code == code
    assert_refused(decide(rec=rec, sel=selection_text(rec)), "composition_record_invalid")


def test_v1a_04_non_json_record_refuses():
    d = decide(record_text="not json")
    assert decision.validate_record_text_v2("not json").code == "json_malformed"
    assert_refused(d, "composition_record_invalid")


# ---- V1A-05 forged / wrong key
def test_v1a_05_forged_signature_refuses():
    rec = record()
    stmt = r.make_statement_v2(rec, family=f.FAMILY_F1AB)
    bad = bytearray(base64.b64decode(sign(stmt)))
    bad[0] ^= 1
    sel = r.dumps(s.envelope(stmt, signature=base64.b64encode(bytes(bad)).decode("ascii"), pub=PK))
    assert_refused(decide(rec=rec, sel=sel), "signature_invalid")


def test_v1a_05_signature_by_untrusted_key_refuses():
    rec = record()
    assert_refused(decide(rec=rec, sel=selection_text(rec, sk=OTHER_SK, pub=PK)), "signature_invalid")


def test_v1a_05_v1_domain_signature_refuses():
    rec = record()
    stmt = r.make_statement_v2(rec, family=f.FAMILY_F1AB)
    sel = r.dumps(s.envelope(stmt, signature=sign(stmt, domain=s.V1_DOMAIN), pub=PK))
    assert_refused(decide(rec=rec, sel=sel), "signature_invalid")


# ---- V1A-06 modified record
def test_v1a_06_record_altered_after_signing_refuses():
    rec = record()
    sel = selection_text(rec)
    tampered = copy.deepcopy(rec)
    tampered["payload"]["allowed_units"] = ["u-read", "u-write"]  # widen without resealing
    assert decision.validate_record_text_v2(r.dumps(tampered)).code == "digest_mismatch"  # validator-level typed code
    assert_refused(decide(rec=tampered, sel=sel), "composition_record_invalid")  # decision-level (ORACLE CORRECTION, as for V1A-04)
    resealed = r.seal_record(tampered)  # widen and reseal: no longer the record the signed selection pins
    assert_refused(decide(rec=resealed, sel=sel), "record_digest_mismatch")


# ---- V1A-07 withdrawn
def test_v1a_07_withdrawn_selection_refuses():
    rec = record()
    sel_stmt = r.make_statement_v2(rec, family=f.FAMILY_F1AB)
    wd = s.withdraw_statement(sel_stmt)
    sel = r.dumps(s.envelope(wd, signature=sign(wd), pub=PK))
    assert_refused(decide(rec=rec, sel=sel), "selection_withdrawn")


# ---- V1A-08 stale / expired
def test_v1a_08_expired_selection_refuses():
    import datetime
    late = r.NOW + datetime.timedelta(days=3)
    rec = record()
    assert_refused(decide(rec=rec, now=late, trust=s.trust(pub=PK, valid_until="2026-12-31T00:00:00Z")), "selection_expired")


def test_v1a_08_expired_trust_snapshot_refuses():
    rec = record()
    assert_refused(decide(rec=rec, trust=s.trust(pub=PK, valid_until="2026-10-25T11:00:00Z")), "trust_snapshot_expired")


# ---- V1A-09 wrong scope
@pytest.mark.parametrize("ctx,code", [
    (c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test"), "selection_scope_mismatch"),
    (c.ExpectedContext("consumer-other", "tenant-a", "inst-a", "domain-a", "op-test"), "selection_consumer_mismatch"),
    (c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other"), "selection_operation_mismatch"),
])
def test_v1a_09_wrong_context_refuses(ctx, code):
    assert_refused(decide(ctx=ctx), code)


# ---- V1A-10 record not the pinned one
def test_v1a_10_other_record_than_pinned_refuses():
    pinned, other = record(), record(payload(allowed_units=["u-read", "u-write"]), record_version=2)
    d = decide(rec=other, sel=selection_text(pinned))
    assert d.kind == "required_policy_unavailable" and d.effective is None and d.code in ("record_identity_mismatch", "record_digest_mismatch")


# ---- V1A-11 / 12 v1 unchanged, no cross acceptance
def test_v1a_11_v1_entry_still_refuses_f1ab_and_accepts_f1a():
    rec = record()
    d1 = decision.verify_and_decide("required", caller(), r.dumps(rec), selection_text(rec), s.CTX, s.trust(pub=PK), r.FakeVerifier(), r.NOW)
    assert d1.kind == "required_policy_unavailable" and d1.effective is None  # cause is asserted at the validator below
    v1_f1ab = r.seal_record(dict(r.make_record(), family=f.FAMILY_F1AB, payload=payload()))
    assert record_mod.validate_record_text(r.dumps(v1_f1ab)).code == "family_unsupported"  # the cause, at the unchanged v1 validator
    f1a = r.make_record()
    caller3 = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
    env = r.make_envelope(r.make_statement(f1a), public_key=s.PK)
    d2 = decision.verify_and_decide("required", caller3, r.dumps(f1a), r.dumps(env), s.CTX, s.trust(), r.FakeVerifier(), r.NOW)
    assert d2.kind == "applied" and d2.effective["allowed_units"] == ("unit-a",)


def test_v1a_12_validators_do_not_cross_accept():
    v2_text, v1_text = r.dumps(record()), r.dumps(r.make_record())
    assert record_mod.validate_record_text(v2_text).code == "contract_unsupported"
    assert decision.validate_record_text_v2(v2_text).ok is True
    res = decision.validate_record_text_v2(v1_text)
    assert res.ok is False and res.code == "contract_unsupported"


# ---- parity: the v2 validator is the v1 validator's checks under the other contract tag (guards the duplicated control flow against drift)
def _swap(body, version):
    return r.seal_record(dict(body, contract_version=version))


@pytest.mark.parametrize("mutate", [
    lambda b: None, lambda b: b.update(kind="x"), lambda b: b.update(family="nope"), lambda b: b.update(record_id="!!"), lambda b: b.update(record_version=0),
    lambda b: b.update(non_authorizing=False), lambda b: b["evaluator"].update(binding="x"), lambda b: b["source"].update(commit="zz"),
    lambda b: b["provenance"].update(authored_at="no"), lambda b: b.update(supersedes={"record_id": "f1a-test-record", "record_version": 1, "record_digest": "sha256:" + "0" * 64}),
    lambda b: b.pop("provenance"), lambda b: b.update(extra=1), lambda b: b["payload"].update(allowed_units=["b", "a"]),
])
def test_v1a_parity_v2_validator_matches_v1_validator_codes(mutate):
    body = copy.deepcopy(r.make_record())  # f1a, valid under both tables
    mutate(body)
    body = r.seal_record(body) if "payload" in body and "provenance" in body else body
    one = record_mod.validate_record_text(r.dumps(_swap(body, "r08-v1") if "payload" in body and "provenance" in body else body))
    two = decision.validate_record_text_v2(r.dumps(_swap(body, "r08-v2") if "payload" in body and "provenance" in body else dict(body, contract_version="r08-v2")))
    assert (one.ok, one.code) == (two.ok, two.code)


# ---- V1A-16 STRICT VERSION SEPARATION (remediation of the Architect review of PR #43; replaces the earlier legacy-compat oracle)
def test_v1a_16_v1_contract_records_are_refused_at_the_v2_entry():
    """Contract section 1: the v2 public decision entry accepts `r08-v2` record documents only. An `r08-v1` `f1a` record (valid at the v1 entry) is
    refused `contract_unsupported` at the validator boundary and `composition_record_invalid` at the decision (established precedence). No
    downgrade, version guessing or retry."""
    f1a = r.make_record()
    caller3 = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
    stmt = r.make_statement_v2(f1a)
    ad = ev.Ed25519Verifier()
    sel = r.dumps(s.envelope(stmt, signature=sign(stmt), pub=PK))
    d = decision.verify_and_decide_v2("required", caller3, r.dumps(f1a), sel, s.CTX, s.trust(pub=PK), ad, r.NOW, ad.key_admission)
    assert_refused(d, "composition_record_invalid")
    assert decision.validate_record_text_v2(r.dumps(f1a)).code == "contract_unsupported"
    assert record_mod.validate_record_text(r.dumps(f1a)).ok is True  # the frozen v1 validator still accepts it at the v1 entry
    legacy_f1ab = r.seal_record(dict(r.make_record(), family=f.FAMILY_F1AB, payload=payload()))  # contract_version stays r08-v1
    assert_refused(decide(rec=legacy_f1ab, sel=selection_text(legacy_f1ab)), "composition_record_invalid")
    assert record_mod.validate_record_text(r.dumps(legacy_f1ab)).code == "family_unsupported"  # r08-v1 f1ab remains unsupported


def test_v1a_16_no_legacy_fallback_symbol_and_v2_f1a_is_accepted(monkeypatch):
    assert not hasattr(decision, "_validate_record_v2_entry")  # the fallback dispatcher is gone
    calls = []
    real = record_mod.validate_record_text
    monkeypatch.setattr(record_mod, "validate_record_text", lambda text: (calls.append(1), real(text))[1])
    f1a_v1 = r.make_record()
    stmt1 = r.make_statement_v2(f1a_v1)
    ad = ev.Ed25519Verifier()
    sel1 = r.dumps(s.envelope(stmt1, signature=sign(stmt1), pub=PK))
    d1 = decision.verify_and_decide_v2("required", {"allowed_actions": [], "allowed_adapters": [], "allowed_units": []}, r.dumps(f1a_v1), sel1, s.CTX,
                                       s.trust(pub=PK), ad, r.NOW, ad.key_admission)
    assert d1.effective is None and calls == []  # the frozen v1 validator is never consulted on the v2 path, for any record
    f1a_v2 = r.seal_record(dict(r.make_record(), contract_version="r08-v2"))
    caller3 = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
    stmt = r.make_statement_v2(f1a_v2)
    ad = ev.Ed25519Verifier()
    sel = r.dumps(s.envelope(stmt, signature=sign(stmt), pub=PK))
    d = decision.verify_and_decide_v2("required", caller3, r.dumps(f1a_v2), sel, s.CTX, s.trust(pub=PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "applied" and d.effective["allowed_units"] == ("unit-a",)


def test_v1a_16_r08_v2_record_is_refused_at_the_v1_entry():
    rec = record()
    d = decision.verify_and_decide("required", caller(), r.dumps(rec), selection_text(rec), s.CTX, s.trust(pub=PK), r.FakeVerifier(), r.NOW)
    assert d.kind == "required_policy_unavailable" and d.effective is None
    assert record_mod.validate_record_text(r.dumps(rec)).code == "contract_unsupported"


# ---- V1A-13 one verifier
def test_v1a_13_v2_decision_uses_the_single_verify_selection_v2(monkeypatch):
    calls = []
    real = v.verify_selection_v2
    monkeypatch.setattr(v, "verify_selection_v2", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    assert decide().kind == "applied" and calls == [1]


# ---- V1A-14 / 15
def test_v1a_14_never_operationally_authorized():
    for d in (decide(), decide(rec=record(payload(allowed_units=[]))), decide(ctx=c.ExpectedContext("x", "tenant-a", "inst-a", "domain-a", "op-test"))):
        assert d.operationally_authorized is False


def test_v1a_15_optional_refusal_is_not_an_application():
    rec = record()
    d = decide(participation="optional", rec=rec, ctx=c.ExpectedContext("x", "tenant-a", "inst-a", "domain-a", "op-test"))
    assert d.kind == "overlay_not_applied" and d.caller_unchanged is True


# =============================================================================================================================================
# REMEDIATION 2: F4/F5 DECISION-LEVEL COVERAGE (Registry decision-path reachability only: no Control Plane wiring, activation or dispatch).
# Predeclared expectations (baseline = unchanged source of commit e3f97ddd, where F4/F5 are already reachable via FAMILIES_V2):
#   V1A-F4-01 valid record + authenticated selection -> applied, effective = min(caller, registry) per field          | baseline: PASS expected
#   V1A-F4-02 registry narrower -> effective = registry; V1A-F4-03 registry wider -> effective = caller (never widened) | PASS expected
#   V1A-F4-04 missing / extra / invalid payload fields -> validator typed code; decision `composition_record_invalid`  | PASS expected
#   V1A-F4-05 boundaries: 1 and AGE_MAX accepted, 0 / -1 / AGE_MAX+1 / bool / str / float / over-large refused         | PASS expected
#   V1A-F4-06 invalid caller values -> `composition_caller_invalid`, no policy                                          | PASS expected
#   V1A-F4-07 required-operation refusals (forged, wrong scope, withdrawn) never return a policy; optional -> overlay_not_applied | PASS expected
#   V1A-F5-01..07 the same for the class-age map, plus: caller class absent from the registry keeps the caller value; registry class unknown
#                 to the caller -> `composition_record_invalid`; empty / unsorted / non-token class keys refused; invalid caller map refused
# Limitation reported, not resolved here: docs/r08-v2-contract.md section 2.1 says the maximum is "pending" while the code and DR-CP-AGE-1 carry
# AGE_MAX = 2147483647 (the V1 technical representation ceiling). These tests pin the code constant imported from v2_age_bounds; no constant is invented.
# =============================================================================================================================================
import json  # noqa: E402

from registry_successor import v2_age_bounds as ab  # noqa: E402

F4P = {"status_max_age_seconds": 120, "approval_max_age_seconds": 600}
F4C = {"status_max_age_seconds": 300, "approval_max_age_seconds": 600}
F5P = {"class_status_max_age_seconds": {"cls-a": 120, "cls-b": 900}}
F5C = {"class_status_max_age_seconds": {"cls-a": 300, "cls-b": 600, "cls-c": 45}}


def fam_record(family, pl, **over):
    body = dict(r.make_record(), contract_version="r08-v2", family=family, record_id="age-test-record", payload=pl)
    body.update(over)
    return r.seal_record(body)


def fam_sel(rec, family, sk=None):
    stmt = r.make_statement_v2(rec, family=family)
    return r.dumps(s.envelope(stmt, signature=sign(stmt, sk), pub=PK))


def fam_decide(family, pl, cl, participation="required", sel=None, text=None, ctx=None, rec=None):
    rec = rec if rec is not None else fam_record(family, pl)
    ad = ev.Ed25519Verifier()
    return decision.verify_and_decide_v2(participation, cl, text if text is not None else r.dumps(rec), sel if sel is not None else fam_sel(rec, family),
                                         ctx or s.CTX, s.trust(pub=PK), ad, r.NOW, ad.key_admission)


# ---- F4
def test_f4_01_valid_selection_composes_with_the_caller():
    d = fam_decide(ab.FAMILY_F4, F4P, F4C)
    assert d.kind == "applied" and d.code is None and d.deny_all is False and d.operationally_authorized is False
    assert d.effective == {"status_max_age_seconds": 120, "approval_max_age_seconds": 600}


def test_f4_02_registry_narrower_than_caller_narrows():
    d = fam_decide(ab.FAMILY_F4, {"status_max_age_seconds": 10, "approval_max_age_seconds": 20}, F4C)
    assert d.kind == "applied" and d.effective == {"status_max_age_seconds": 10, "approval_max_age_seconds": 20}


def test_f4_03_registry_wider_than_caller_never_widens():
    d = fam_decide(ab.FAMILY_F4, {"status_max_age_seconds": 9000, "approval_max_age_seconds": 9000}, F4C)
    assert d.kind == "applied" and d.effective == F4C


@pytest.mark.parametrize("mutate,code", [
    (lambda p: p.pop("approval_max_age_seconds"), "field_missing"),
    (lambda p: p.update(identity_max_age_seconds=5), "field_unknown"),
    (lambda p: p.update(status_max_age_seconds="120"), "field_type_invalid"),
    (lambda p: p.update(status_max_age_seconds=True), "field_type_invalid"),
    (lambda p: p.update(status_max_age_seconds=0), "field_invalid"),
    (lambda p: p.update(status_max_age_seconds=-1), "field_invalid"),
    (lambda p: p.update(status_max_age_seconds=ab.AGE_MAX + 1), "field_invalid"),
])
def test_f4_04_invalid_payloads_refuse(mutate, code):
    pl = dict(F4P)
    mutate(pl)
    rec = fam_record(ab.FAMILY_F4, pl)
    assert decision.validate_record_text_v2(r.dumps(rec)).code == code
    assert_refused(fam_decide(ab.FAMILY_F4, pl, F4C, rec=rec), "composition_record_invalid")


def test_f4_04_float_and_oversized_numbers_refuse_at_the_loader():
    for raw in ("1.5", "1e3", str(2 ** 70)):
        text = json.dumps(fam_record(ab.FAMILY_F4, F4P)).replace('"status_max_age_seconds": 120', '"status_max_age_seconds": ' + raw)
        res = decision.validate_record_text_v2(text)
        assert res.ok is False and res.code in ("json_number_unsupported", "field_invalid", "digest_mismatch", "field_type_invalid"), (raw, res.code)
        assert_refused(fam_decide(ab.FAMILY_F4, F4P, F4C, text=text, rec=fam_record(ab.FAMILY_F4, F4P)), "composition_record_invalid")


@pytest.mark.parametrize("value", [1, ab.AGE_MAX])
def test_f4_05_registry_boundaries_are_accepted(value):
    d = fam_decide(ab.FAMILY_F4, {"status_max_age_seconds": value, "approval_max_age_seconds": value}, {"status_max_age_seconds": ab.AGE_MAX, "approval_max_age_seconds": ab.AGE_MAX})
    assert d.kind == "applied" and d.effective == {"status_max_age_seconds": value, "approval_max_age_seconds": value}


@pytest.mark.parametrize("bad", [
    {"status_max_age_seconds": 1}, {**F4C, "extra": 1}, {**F4C, "status_max_age_seconds": -1}, {**F4C, "status_max_age_seconds": True},
    {**F4C, "status_max_age_seconds": 1.5}, {**F4C, "status_max_age_seconds": "9"}, {**F4C, "status_max_age_seconds": ab.AGE_MAX + 1}, {}, None, "caller",
])
def test_f4_06_invalid_callers_refuse_and_are_never_replaced(bad):
    assert_refused(fam_decide(ab.FAMILY_F4, F4P, bad), "composition_caller_invalid")


def test_f4_06_caller_zero_is_valid_and_stays_zero():
    d = fam_decide(ab.FAMILY_F4, F4P, {"status_max_age_seconds": 0, "approval_max_age_seconds": 600})
    assert d.kind == "applied" and d.effective["status_max_age_seconds"] == 0 and d.deny_all is False


def test_f4_07_required_refusals_return_no_policy_and_optional_is_not_an_application():
    rec = fam_record(ab.FAMILY_F4, F4P)
    stmt = r.make_statement_v2(rec, family=ab.FAMILY_F4)
    bad = bytearray(base64.b64decode(sign(stmt)))
    bad[0] ^= 1
    forged = r.dumps(s.envelope(stmt, signature=base64.b64encode(bytes(bad)).decode("ascii"), pub=PK))
    assert_refused(fam_decide(ab.FAMILY_F4, F4P, F4C, sel=forged, rec=rec), "signature_invalid")
    wrong = c.ExpectedContext("consumer-test", "tenant-b", "inst-a", "domain-a", "op-test")
    assert_refused(fam_decide(ab.FAMILY_F4, F4P, F4C, ctx=wrong, rec=rec), "selection_scope_mismatch")
    wd = s.withdraw_statement(stmt)
    assert_refused(fam_decide(ab.FAMILY_F4, F4P, F4C, rec=rec, sel=r.dumps(s.envelope(wd, signature=sign(wd), pub=PK))), "selection_withdrawn")
    assert_refused(fam_decide(ab.FAMILY_F4, F4P, F4C, rec=rec, participation="required", ctx=c.ExpectedContext("x", "tenant-a", "inst-a", "domain-a", "op-test")), "selection_consumer_mismatch")
    o = fam_decide(ab.FAMILY_F4, F4P, F4C, participation="optional", rec=rec, ctx=wrong)
    assert o.kind == "overlay_not_applied" and o.caller_unchanged is True and o.operationally_authorized is False


# ---- F5
def test_f5_01_valid_class_map_composes_per_class():
    d = fam_decide(ab.FAMILY_F5, F5P, F5C)
    assert d.kind == "applied" and d.operationally_authorized is False
    assert d.effective == {"class_status_max_age_seconds": {"cls-a": 120, "cls-b": 600, "cls-c": 45}}  # cls-b: registry 900 > caller 600 stays 600; cls-c absent from registry keeps 45


def test_f5_02_registry_narrower_narrows_only_that_class():
    d = fam_decide(ab.FAMILY_F5, {"class_status_max_age_seconds": {"cls-a": 7}}, F5C)
    assert d.kind == "applied" and d.effective["class_status_max_age_seconds"] == {"cls-a": 7, "cls-b": 600, "cls-c": 45}


def test_f5_03_registry_wider_never_widens():
    d = fam_decide(ab.FAMILY_F5, {"class_status_max_age_seconds": {"cls-a": 9999, "cls-b": 9999, "cls-c": 9999}}, F5C)
    assert d.kind == "applied" and d.effective == F5C


def test_f5_04_unknown_action_class_refuses():
    assert_refused(fam_decide(ab.FAMILY_F5, {"class_status_max_age_seconds": {"cls-z": 5}}, F5C), "composition_record_invalid")


@pytest.mark.parametrize("pl,code", [
    ({}, "field_missing"),
    ({"class_status_max_age_seconds": {"cls-a": 5}, "extra": {}}, "field_unknown"),
    ({"class_status_max_age_seconds": [1]}, "field_type_invalid"),
    ({"class_status_max_age_seconds": {"cls-a": "5"}}, "field_type_invalid"),
    ({"class_status_max_age_seconds": {"cls-a": True}}, "field_type_invalid"),
    ({"class_status_max_age_seconds": {}}, "field_invalid"),
    ({"class_status_max_age_seconds": {"cls-a": 0}}, "field_invalid"),
    ({"class_status_max_age_seconds": {"cls-a": -3}}, "field_invalid"),
    ({"class_status_max_age_seconds": {"cls-a": ab.AGE_MAX + 1}}, "field_invalid"),
    ({"class_status_max_age_seconds": {"a*b": 5}}, "field_invalid"),
    ({"class_status_max_age_seconds": {"": 5}}, "field_invalid"),
])
def test_f5_05_invalid_payloads_refuse(pl, code):
    rec = fam_record(ab.FAMILY_F5, pl)
    assert decision.validate_record_text_v2(r.dumps(rec)).code == code
    assert_refused(fam_decide(ab.FAMILY_F5, pl, F5C, rec=rec), "composition_record_invalid")


def test_f5_05_unsorted_class_keys_refuse():
    rec = fam_record(ab.FAMILY_F5, {"class_status_max_age_seconds": {"cls-b": 5, "cls-a": 5}})  # insertion order kept by plain json.dumps
    text = json.dumps(rec)
    assert decision.validate_record_text_v2(text).code == "field_invalid"
    assert_refused(fam_decide(ab.FAMILY_F5, None, F5C, rec=rec, text=text), "composition_record_invalid")


@pytest.mark.parametrize("value", [1, ab.AGE_MAX])
def test_f5_05_boundaries_are_accepted(value):
    d = fam_decide(ab.FAMILY_F5, {"class_status_max_age_seconds": {"cls-a": value}}, {"class_status_max_age_seconds": {"cls-a": ab.AGE_MAX}})
    assert d.kind == "applied" and d.effective["class_status_max_age_seconds"] == {"cls-a": value}


@pytest.mark.parametrize("bad", [
    {"class_status_max_age_seconds": {}}, {}, {"class_status_max_age_seconds": {"cls-a": -1}}, {"class_status_max_age_seconds": {"cls-a": True}},
    {"class_status_max_age_seconds": {"cls-a": 1.5}}, {"class_status_max_age_seconds": {"a b": 5}}, {"class_status_max_age_seconds": {"cls-a": ab.AGE_MAX + 1}},
    {"class_status_max_age_seconds": [("cls-a", 1)]}, {**F5C, "extra": 1}, None, "caller",
])
def test_f5_06_invalid_caller_maps_refuse(bad):
    assert_refused(fam_decide(ab.FAMILY_F5, {"class_status_max_age_seconds": {"cls-a": 5}}, bad), "composition_caller_invalid")


def test_f5_07_required_refusals_return_no_policy_and_optional_is_not_an_application():
    rec = fam_record(ab.FAMILY_F5, F5P)
    stmt = r.make_statement_v2(rec, family=ab.FAMILY_F5)
    forged = r.dumps(s.envelope(stmt, signature=sign(stmt, OTHER_SK), pub=PK))
    assert_refused(fam_decide(ab.FAMILY_F5, F5P, F5C, sel=forged, rec=rec), "signature_invalid")
    wrong = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-other")
    assert_refused(fam_decide(ab.FAMILY_F5, F5P, F5C, ctx=wrong, rec=rec), "selection_operation_mismatch")
    wd = s.withdraw_statement(stmt)
    assert_refused(fam_decide(ab.FAMILY_F5, F5P, F5C, rec=rec, sel=r.dumps(s.envelope(wd, signature=sign(wd), pub=PK))), "selection_withdrawn")
    o = fam_decide(ab.FAMILY_F5, F5P, F5C, participation="optional", rec=rec, ctx=wrong)
    assert o.kind == "overlay_not_applied" and o.caller_unchanged is True and o.operationally_authorized is False


def test_f4_f5_decision_does_not_widen_or_authorize_anywhere():
    for d in (fam_decide(ab.FAMILY_F4, F4P, F4C), fam_decide(ab.FAMILY_F5, F5P, F5C)):
        assert d.operationally_authorized is False and d.deny_all is False and d.deny_all_fields == ()
