"""Test builders for the `r08-v4` composite family (test-only; BUILDER_TESTED, not independently qualified).

Real Ed25519 (PyNaCl, deterministic) signs every selection; the deterministic seed keys are SYNTHETIC test keys.
"""
import base64
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import v4_f1abcd as f  # noqa: E402

try:
    import nacl.bindings as nb
    from registry_adapters import ed25519_verifier as ev
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    nb = ev = None
    HAVE_BACKEND = False

V4_DOMAIN = b"ocs-reg/r08-v4/selection\n"
V2_DOMAIN = s.V2_DOMAIN
V1_DOMAIN = s.V1_DOMAIN
PK, SK = (nb.crypto_sign_seed_keypair(bytes(range(32))) if HAVE_BACKEND else (None, None))
OTHER_PK, OTHER_SK = (nb.crypto_sign_seed_keypair(bytes(range(1, 33))) if HAVE_BACKEND else (None, None))
FIELDS = f.F1ABCD_FIELDS
SETS = f.SET_FIELDS
FAMILY = f.FAMILY_F1ABCD


def payload(**over):
    p = {"allowed_actions": ["act-copy", "act-list"], "allowed_adapters": ["a-local"], "allowed_units": ["u-read"],
         "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"], "max_amount": 100, "max_effects": 3,
         "allowed_target_prefixes": ["rec/in/", "rec/out"], "target_match": "segment"}
    p.update(over)
    return p


def caller(**over):
    p = {"allowed_actions": ["act-copy", "act-list", "act-other"], "allowed_adapters": ["a-local", "a-other"],
         "allowed_units": ["u-read", "u-write"], "allowed_institutions": ["inst-a"], "allowed_authority_domains": ["domain-a"],
         "max_amount": 500, "max_effects": 10, "allowed_target_prefixes": ["rec/"], "target_match": "segment"}
    p.update(over)
    return p


def record(pl=None, **over):
    body = dict(r.make_record(), contract_version="r08-v4", family=FAMILY, record_id="f1abcd-test-record",
                payload=pl if pl is not None else payload())
    body.update(over)
    return r.seal_record(body)


def sign(statement, sk=None, domain=None):
    msg = (V4_DOMAIN if domain is None else domain) + c.canonical_bytes(statement)
    return base64.b64encode(nb.crypto_sign(msg, sk or SK)[:64]).decode("ascii")


def statement(rec, **over):
    return r.make_statement_v2(rec, family=FAMILY, **over)


def envelope(stmt, sk=None, pub=None, domain=None, contract="r08-v4", **over):
    return s.envelope(stmt, domain=V4_DOMAIN if domain is None else domain, contract=contract, signature=sign(stmt, sk, domain), pub=pub or PK, **over)


def selection_text(rec, sk=None, pub=None, domain=None, contract="r08-v4", **over):
    return r.dumps(envelope(statement(rec, **over), sk, pub, domain, contract))


def decide(participation="required", rec=None, sel=None, ctx=None, trust=None, now=None, cl=None, record_text=None):
    from registry_successor.v4_decision import verify_and_decide_v4
    rec = rec if rec is not None else record()
    ad = ev.Ed25519Verifier()
    return verify_and_decide_v4(
        participation, cl if cl is not None else caller(), record_text if record_text is not None else r.dumps(rec),
        sel if sel is not None else selection_text(rec), ctx or s.CTX, trust or s.trust(pub=PK), ad, now or r.NOW, ad.key_admission)


def assert_refused(d, code):
    assert d.kind == "required_policy_unavailable", d
    assert d.code == code, d
    assert d.effective is None and d.caller_unchanged is False and d.operationally_authorized is False and d.deny_all is False
