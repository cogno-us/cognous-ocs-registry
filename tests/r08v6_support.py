"""Test builders for the two `r08-v6` revocation families (test-only; BUILDER_TESTED, not independently qualified).

Same public helper names as `r08v5_support`, generalised: every builder takes the family (default `f5-action-class-revocation-assurance-policy`,
module constants FAMILY/FIELD) and a record may be built for either family with the payload given. The second family's constants are FAMILY_TR/TR_FIELD.
Real Ed25519 (PyNaCl, deterministic) signs every selection; the deterministic seed keys are SYNTHETIC test keys.
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import v6_class_revocation_assurance as f  # noqa: E402
from registry_successor import v6_terminal_revocation as ft  # noqa: E402

try:
    import nacl.bindings as nb
    from registry_adapters import ed25519_verifier as ev
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    nb = ev = None
    HAVE_BACKEND = False

V6_DOMAIN = b"ocs-reg/r08-v6/selection\n"
V5_DOMAIN = b"ocs-reg/r08-v5/selection\n"
V2_DOMAIN = s.V2_DOMAIN
V1_DOMAIN = s.V1_DOMAIN
PK, SK = (nb.crypto_sign_seed_keypair(bytes(range(32))) if HAVE_BACKEND else (None, None))
OTHER_PK, OTHER_SK = (nb.crypto_sign_seed_keypair(bytes(range(1, 33))) if HAVE_BACKEND else (None, None))
FIELDS = f.F5RA_FIELDS
FIELD = f.F5RA_FIELD
FAMILY = f.FAMILY_F5RA
FAMILY_TR = ft.FAMILY_TR
TR_FIELD = ft.TR_FIELD
FAMILIES = (FAMILY, FAMILY_TR)
RECORD_IDS = {FAMILY: "f5ra-test-record", FAMILY_TR: "f5tr-test-record"}


def payload(family=None, **over):
    """A Registry record payload of `family`: for F5RA a class map (sorted class keys); for terminal revocation the scalar."""
    family = family or FAMILY
    p = {FIELD: {"class-a": "required", "class-b": "required"}} if family == FAMILY else {TR_FIELD: "on"}
    p.update(over)
    return p


def caller(family=None, **over):
    """A host (caller) policy of `family`: for F5RA every host class and its current value; for terminal revocation the scalar."""
    family = family or FAMILY
    p = ({FIELD: {"class-a": "not_required", "class-b": "not_required", "class-c": "required"}} if family == FAMILY else {TR_FIELD: "off"})
    p.update(over)
    return p


def record(pl=None, family=None, **over):
    family = family or FAMILY
    body = dict(r.make_record(), contract_version="r08-v6", family=family, record_id=RECORD_IDS.get(family, "f5-test-record"),
                payload=pl if pl is not None else payload(family))
    body.update(over)
    return r.seal_record(body)


def sign(statement, sk=None, domain=None):
    msg = (V6_DOMAIN if domain is None else domain) + c.canonical_bytes(statement)
    return base64.b64encode(nb.crypto_sign(msg, sk or SK)[:64]).decode("ascii")


def statement(rec, **over):
    over.setdefault("family", rec["family"])
    return r.make_statement_v2(rec, **over)


def envelope(stmt, sk=None, pub=None, domain=None, contract="r08-v6", **over):
    return s.envelope(stmt, domain=V6_DOMAIN if domain is None else domain, contract=contract, signature=sign(stmt, sk, domain), pub=pub or PK, **over)


def selection_text(rec, sk=None, pub=None, domain=None, contract="r08-v6", **over):
    return r.dumps(envelope(statement(rec, **over), sk, pub, domain, contract))


def decide(participation="required", rec=None, sel=None, ctx=None, trust=None, now=None, cl=None, record_text=None):
    from registry_successor.v6_decision import verify_and_decide_v6
    rec = rec if rec is not None else record()
    ad = ev.Ed25519Verifier()
    return verify_and_decide_v6(
        participation, cl if cl is not None else caller(rec.get("family")), record_text if record_text is not None else r.dumps(rec),
        sel if sel is not None else selection_text(rec), ctx or s.CTX, trust or s.trust(pub=PK), ad, now or r.NOW, ad.key_admission)


def assert_refused(d, code):
    assert d.kind == "required_policy_unavailable", d
    assert d.code == code, d
    assert d.effective is None and d.caller_unchanged is False and d.operationally_authorized is False and d.deny_all is False
