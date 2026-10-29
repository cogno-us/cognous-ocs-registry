"""Test builders for the `r08-v8` remaining families on the unified engine (test-only; DRAFT / PROPOSED / GATED; BUILDER_TESTED, not independently qualified).

Three families, each with one payload member: `f5-anchor-deadline-to-inputs-policy` (str `anchor` | `no_change`), `f5-observation-max-age-policy` and
`f5-observation-clock-tolerance-policy` (strict ints). Every builder takes the family (default the anchor family). Real Ed25519 (PyNaCl, deterministic) signs every
selection; the deterministic seed keys are SYNTHETIC test keys.
"""
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import r08_support as r  # noqa: E402
import s01_support as s  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor.engine import families_anchor as anc  # noqa: E402
from registry_successor.engine import families_observation as obs  # noqa: E402

try:
    import nacl.bindings as nb
    from registry_adapters import ed25519_verifier as ev
    HAVE_BACKEND = True
except ImportError:  # pragma: no cover
    nb = ev = None
    HAVE_BACKEND = False

V8_DOMAIN = b"ocs-reg/r08-v8/selection\n"
V7_DOMAIN = b"ocs-reg/r08-v7/selection\n"
V6_DOMAIN = b"ocs-reg/r08-v6/selection\n"
V5_DOMAIN = b"ocs-reg/r08-v5/selection\n"
V2_DOMAIN = s.V2_DOMAIN
V1_DOMAIN = s.V1_DOMAIN
PK, SK = (nb.crypto_sign_seed_keypair(bytes(range(32))) if HAVE_BACKEND else (None, None))
OTHER_PK, OTHER_SK = (nb.crypto_sign_seed_keypair(bytes(range(1, 33))) if HAVE_BACKEND else (None, None))

ANCHOR, MAXAGE, TOL = anc.FAMILY_ANCHOR, obs.FAMILY_MAX_AGE, obs.FAMILY_TOLERANCE
FAMILIES = (ANCHOR, MAXAGE, TOL)
FIELDS = {ANCHOR: anc.ANCHOR_FIELD, MAXAGE: obs.MAX_AGE_FIELD, TOL: obs.TOLERANCE_FIELD}
RECORD_IDS = {ANCHOR: "f5anc-test-record", MAXAGE: "f5obsage-test-record", TOL: "f5obstol-test-record"}
DEFAULT_REGISTRY = {ANCHOR: "anchor", MAXAGE: 60, TOL: 0}
DEFAULT_CALLER = {ANCHOR: "no_change", MAXAGE: 300, TOL: 5}
FAMILY, FIELD = ANCHOR, FIELDS[ANCHOR]


def payload(family=ANCHOR, value=None):
    family = family if family in FIELDS else ANCHOR  # a family outside the v8 table: any well-formed payload (the refusal is on the family)
    return {FIELDS[family]: DEFAULT_REGISTRY[family] if value is None else value}


def caller(family=ANCHOR, value=None):
    family = family if family in FIELDS else ANCHOR  # a family outside the v8 table: any well-formed caller (the refusal is on the family)
    return {FIELDS[family]: DEFAULT_CALLER[family] if value is None else value}


def record(pl=None, family=ANCHOR, contract="r08-v8", **over):
    body = dict(r.make_record(), contract_version=contract, family=family, record_id=RECORD_IDS.get(family, "f5-test-record"),
                payload=pl if pl is not None else payload(family))
    body.update(over)
    return r.seal_record(body)


def sign(statement, sk=None, domain=None):
    msg = (V8_DOMAIN if domain is None else domain) + c.canonical_bytes(statement)
    return base64.b64encode(nb.crypto_sign(msg, sk or SK)[:64]).decode("ascii")


def statement(rec, **over):
    over.setdefault("family", rec["family"])
    return r.make_statement_v2(rec, **over)


def envelope(stmt, sk=None, pub=None, domain=None, contract="r08-v8", **over):
    return s.envelope(stmt, domain=V8_DOMAIN if domain is None else domain, contract=contract, signature=sign(stmt, sk, domain), pub=pub or PK, **over)


def selection_text(rec, sk=None, pub=None, domain=None, contract="r08-v8", **over):
    return r.dumps(envelope(statement(rec, **over), sk, pub, domain, contract))


def decide(participation="required", rec=None, sel=None, ctx=None, trust=None, now=None, cl=None, record_text=None, family=ANCHOR):
    from registry_successor.v8_decision import verify_and_decide_v8
    rec = rec if rec is not None else record(family=family)
    ad = ev.Ed25519Verifier()
    return verify_and_decide_v8(
        participation, cl if cl is not None else caller(rec["family"]), record_text if record_text is not None else r.dumps(rec),
        sel if sel is not None else selection_text(rec), ctx or s.CTX, trust or s.trust(pub=PK), ad, now or r.NOW, ad.key_admission)


def assert_refused(d, code):
    assert d.kind == "required_policy_unavailable", d
    assert d.code == code, d
    assert d.effective is None and d.caller_unchanged is False and d.operationally_authorized is False and d.deny_all is False
