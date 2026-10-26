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
  V1A-16  r08-v1 f1a record at the v2 entry keeps its pre-V01a result (applied, three-set); r08-v1 document claiming f1ab still refuses | guard
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
    assert record_mod.validate_record_text_v2(r.dumps(rec)).code == code
    assert_refused(decide(rec=rec, sel=selection_text(rec)), "composition_record_invalid")


def test_v1a_04_non_json_record_refuses():
    d = decide(record_text="not json")
    assert d.kind == "required_policy_unavailable" and d.effective is None and d.code in c.CODES


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
    assert record_mod.validate_record_text_v2(r.dumps(tampered)).code == "digest_mismatch"  # validator-level typed code
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
    assert d1.kind == "required_policy_unavailable" and d1.effective is None
    f1a = r.make_record()
    caller3 = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
    env = r.make_envelope(r.make_statement(f1a), public_key=s.PK)
    d2 = decision.verify_and_decide("required", caller3, r.dumps(f1a), r.dumps(env), s.CTX, s.trust(), r.FakeVerifier(), r.NOW)
    assert d2.kind == "applied" and d2.effective["allowed_units"] == ("unit-a",)


def test_v1a_12_validators_do_not_cross_accept():
    v2_text, v1_text = r.dumps(record()), r.dumps(r.make_record())
    assert record_mod.validate_record_text(v2_text).code in ("contract_unsupported", "family_unsupported")
    assert record_mod.validate_record_text_v2(v2_text).ok is True
    res = record_mod.validate_record_text_v2(v1_text)
    assert res.ok is False and res.code == "contract_unsupported"


# ---- V1A-16 legacy records at the v2 entry (compatibility finding recorded in the second commit)
def test_v1a_16_v1_contract_records_keep_their_existing_v2_entry_behaviour():
    """Existing tests and callers feed `r08-v1` `f1a` records to verify_and_decide_v2; that stays applied with the three-set composition, and an
    `r08-v1` document claiming family `f1ab` still refuses (the v2 family table is reachable only by an `r08-v2` document)."""
    f1a = r.make_record()
    caller3 = {"allowed_actions": ["write-file"], "allowed_adapters": ["local-fs"], "allowed_units": ["unit-a"]}
    stmt = r.make_statement_v2(f1a)
    ad = ev.Ed25519Verifier()
    sel = r.dumps(s.envelope(stmt, signature=sign(stmt), pub=PK))
    d = decision.verify_and_decide_v2("required", caller3, r.dumps(f1a), sel, s.CTX, s.trust(pub=PK), ad, r.NOW, ad.key_admission)
    assert d.kind == "applied" and d.effective["allowed_units"] == ("unit-a",)
    legacy_f1ab = r.seal_record(dict(r.make_record(), family=f.FAMILY_F1AB, payload=payload()))  # contract_version stays r08-v1
    d2 = decide(rec=legacy_f1ab, sel=selection_text(legacy_f1ab))
    assert d2.kind == "required_policy_unavailable" and d2.effective is None


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
