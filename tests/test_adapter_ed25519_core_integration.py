"""Ed25519 adapter composed with the core's MANDATORY key admission (PR #34) and driven through verify.py (PR #26, SECURITY-HELD).

Every test here calls `registry_successor.verify.verify_selection(..., contract_version="r08-v2")`, the mandatory-admission path.
Layers, in the order the core applies them (docs/core-security-canonical-signature-and-key-admission.md section 2.0-adapter):
  1. built-in `inspect_ed25519_key` (always; cannot be disabled by omitting or lying in the callback);
  2. the adapter policy `Ed25519Verifier.key_admission` (can only further restrict);
  3. canonical base64 decoding of the signature, then `Ed25519Verifier.verify` (libsodium) on the core's signing input.
Vector rows come from CCTV, Wycheproof and the strict-verification file. The core builds the signed message itself, so a vector's own
message cannot flow through unchanged: `VectorMessageVerifier` is the real adapter with the message replaced by the vector's. The key
(admission, both layers) and the signature (canonical base64 round trip, authenticity loop, the adapter's verify) do travel the real path.
Real-message end to end checks (honest signature, mixed-order key signed over the core's own signing input) are separate tests.

AI review artifact, not independent cryptographic approval: PR #26 stays SECURITY-HELD. Linux x86-64 CPython 3.11-3.13 only.
"""
import base64
import json
from collections import Counter, namedtuple
from pathlib import Path

import pytest

import ed25519_oracle as oracle
import r08_support as r
from registry_adapters import ed25519_verifier as ev
from registry_successor import common as c
from registry_successor import key_admission as ka
from registry_successor import verify as v
from r08_support import signing_input_v2 as signing_input  # S01: r08-v2 signs under its own domain

try:
    import nacl.bindings as nb
    HAVE_BACKEND = True
except ImportError:
    HAVE_BACKEND = False

needs_backend = pytest.mark.skipif(not HAVE_BACKEND, reason="pynacl not installed (requirements-ed25519.lock.txt)")
VECDIR = Path(__file__).resolve().parent / "vectors"
CCTV = json.loads((VECDIR / "cctv" / "ed25519vectors.json").read_bytes())
WYC = json.loads((VECDIR / "wycheproof" / "ed25519_test.json").read_bytes())
SEC = json.loads((VECDIR / "ed25519-security-vectors.json").read_text())
SYN = json.loads((VECDIR / "ed25519-synthetic.json").read_text())

Sel = namedtuple("Sel", "ok code detail envelope statement statement_digest signatures")
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
GRANT = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
V2 = "r08-v2"
BUILTIN_CAUSES = {"key_type", "key_length", "key_non_canonical_y", "key_small_order"}


def _trust(pub, alg="ed25519"):
    return v.TrustSnapshot("snapshot-1", 1, "2026-10-27T00:00:00Z", (v.IssuerEntry("key-test-1", "issuer-test-1", alg, pub, (GRANT,)),))


def _sel(sig_bytes, statement=None, v2=True):
    statement = statement or (r.make_statement_v2() if v2 else r.make_statement())
    env = {**({"contract_version": V2} if v2 else {}), "statement": statement, "statement_digest": c.digest(statement),
           "signatures": [{"alg": "ed25519", "key_id": "key-test-1", "signature": base64.b64encode(sig_bytes).decode("ascii")}]}
    return Sel(True, None, "", env, env["statement"], env["statement_digest"], env["signatures"])


class VectorMessageVerifier:
    """The REAL adapter, but verifying the vector's own message instead of the core's signing input (see module docstring)."""
    def __init__(self, real, msg):
        self.real, self.msg = real, msg

    def verify(self, alg, public_key, message, signature):
        return self.real.verify(alg, public_key, self.msg, signature)


@pytest.fixture(scope="module")
def adapter():
    return ev.Ed25519Verifier()


def _run(sel, pub, verifier, admission="adapter", adapter_obj=None, contract=V2):
    policy = adapter_obj.key_admission if admission == "adapter" and adapter_obj else None
    return v.verify_selection(sel, CTX, _trust(pub), verifier, r.NOW, key_admission=policy, contract_version=contract)


def _layer(rep):
    if rep.ok:
        return "accepted"
    if rep.code == "trust_snapshot_invalid":
        return "admission_adapter" if getattr(rep, "detail_cause", None) == "policy_refused" else "admission_builtin"
    assert rep.code == "signature_invalid", rep.code
    return "verifier"


def _through_core(adapter_obj, pk, msg, sig):
    return _run(_sel(sig), pk, VectorMessageVerifier(adapter_obj, msg), adapter_obj=adapter_obj)


def _cctv_rows():
    return [("cctv%d" % t["number"], bytes.fromhex(t["key"]), t["msg"].encode(), bytes.fromhex(t["sig"]), bool(t["flags"])) for t in CCTV]


def _wyc_rows():
    return [("wyc%d-%s" % (t["tcId"], t["result"]), bytes.fromhex(g["publicKey"]["pk"]), bytes.fromhex(t["msg"]), bytes.fromhex(t["sig"]),
             t["result"]) for g in WYC["testGroups"] for t in g["tests"]]


def _sec_rows():
    rows = []
    for grp in ("small_order_key_equation_rows", "small_order_key_rb_rows", "keyholder_r_identity_rows", "mixed_order_key_rows"):
        rows += [(grp, bytes.fromhex(x["pk"]), bytes.fromhex(x["msg"]), bytes.fromhex(x["sig"])) for x in SEC[grp]]
    return rows


# ---- composition and the adapter policy shape ----------------------------------------------------------------
@needs_backend
def test_adapter_policy_has_the_cores_two_argument_shape(adapter):
    pk = oracle.pubkey(bytes.fromhex(SYN["synthetic_keys"]["A"]["seed_hex"]))
    assert adapter.key_admission("ed25519", pk) is True
    assert adapter.key_admission("ed25519", bytes(31)) is False and adapter.key_admission("ed25519", None) is False
    assert adapter.key_admission("ed25519", ka_identity()) is False
    assert adapter.key_admission("other-alg", b"anything") is True  # not judged here, as in the core; the core never verifies it


def ka_identity():
    return bytes([1]) + bytes(31)


@needs_backend
def test_passing_the_one_argument_method_to_the_core_refuses_every_key_fail_closed(adapter):
    """Misuse pin: `acceptable_public_key(pk)` is not a core policy. The core calls policy(alg, pk), the call raises, the key is refused."""
    seed = bytes.fromhex(SYN["synthetic_keys"]["A"]["seed_hex"])
    pk = oracle.pubkey(seed)
    wrong = ka.compose_key_admission(adapter.acceptable_public_key)
    rep = v.verify_selection(_sel(oracle.sign(seed, signing_input(r.make_statement_v2()))), CTX, _trust(pk), adapter, r.NOW,
                             key_admission=wrong, contract_version=V2)
    assert rep.ok is False and rep.code == "trust_snapshot_invalid" and rep.detail_cause == "policy_refused"


@needs_backend
def test_honest_signature_is_authenticated_on_the_mandatory_path_with_and_without_the_adapter_policy(adapter):
    for name in ("A", "B"):
        seed = bytes.fromhex(SYN["synthetic_keys"][name]["seed_hex"])
        pk = oracle.pubkey(seed)
        sel = _sel(oracle.sign(seed, signing_input(r.make_statement_v2())))
        for policy in (None, adapter.key_admission, ka.compose_key_admission(adapter.key_admission)):
            rep = v.verify_selection(sel, CTX, _trust(pk), adapter, r.NOW, key_admission=policy, contract_version=V2)
            assert rep.ok is True and rep.authenticated is True and rep.operationally_authorized is False, (name, policy)


@needs_backend
def test_callback_cannot_relax_builtin_admission_and_omission_does_not_skip_it(adapter):
    seed = bytes.fromhex(SYN["synthetic_keys"]["A"]["seed_hex"])
    for bad in (ka_identity(), bytes(32), (2 ** 255 - 19).to_bytes(32, "little"), bytes(31)):
        sel = _sel(oracle.sign(seed, signing_input(r.make_statement_v2())))
        for policy in (None, lambda alg, pk: True, ka.compose_key_admission(lambda a, k: True)):
            rep = v.verify_selection(sel, CTX, _trust(bad), adapter, r.NOW, key_admission=policy, contract_version=V2)
            assert rep.ok is False and rep.code == "trust_snapshot_invalid" and rep.detail_cause in BUILTIN_CAUSES, bad.hex()
    for contract in ("r08-v2", None, "R08-V1", "r08-v1 ", 2):  # only the exact legacy string skips (core tests own this table)
        rep = v.verify_selection(_sel(bytes(64), v2=(contract == "r08-v2")), CTX, _trust(ka_identity()), adapter, r.NOW, contract_version=contract)
        assert rep.code == "trust_snapshot_invalid" and rep.detail_cause == "key_small_order"


# ---- key classes: which layer refuses, with the real libsodium --------------------------------------------------
def _torsion_order8():
    for y in sorted(ka.SMALL_ORDER_Y):
        point = oracle.decompress(y.to_bytes(32, "little"))
        if point is not None and not oracle.eq(oracle.mul(4, point), oracle.ZERO):
            return point
    raise AssertionError("no order-8 point")


def _off_curve_canonical_y():
    for y in range(2, 1000):
        enc = y.to_bytes(32, "little")
        if oracle.decompress(enc) is None and ka.inspect_ed25519_key(enc) is None:
            return enc
    raise AssertionError("none found")


def _mixed_order_key_and_signature(seed, message_for):
    """Mixed-order key A+T (T of order 8) with a signature that libsodium's signature check ACCEPTS on message_for(n); grinds n."""
    a, prefix = oracle.secret_expand(seed)
    pk = oracle.compress(oracle.add(oracle.mul(a, oracle.G), _torsion_order8()))
    for n in range(1, 400):
        msg = message_for(n)
        rr = oracle._h(prefix, msg)
        R = oracle.compress(oracle.mul(rr, oracle.G))
        sig = R + ((rr + oracle._h(R, pk, msg) * a) % oracle.L).to_bytes(32, "little")
        try:
            nb.crypto_sign_open(sig + msg, pk)
            return n, pk, sig
        except Exception:
            continue
    raise AssertionError("no accepted grind")


@needs_backend
def test_mixed_order_key_pinned_libsodium_signature_check_accepts_but_each_registry_layer_refuses(adapter):
    seed = bytes.fromhex(SYN["synthetic_keys"]["A"]["seed_hex"])
    n, pk, sig = _mixed_order_key_and_signature(seed, lambda n: signing_input(r.make_statement_v2(epoch=n)))
    msg, statement = signing_input(r.make_statement_v2(epoch=n)), r.make_statement_v2(epoch=n)
    point = oracle.decompress(pk)
    assert not oracle.is_small_order(point) and not oracle.in_prime_order_subgroup(point)  # genuinely mixed order
    assert ka.inspect_ed25519_key(pk) is None  # built-in admission (#34) does NOT see it: canonical, not in the small-order y set
    nb.crypto_sign_open(sig + msg, pk)  # pinned libsodium: signature check alone ACCEPTS (raises on failure)
    assert nb.crypto_core_ed25519_is_valid_point(pk) is False  # libsodium's own point validation refuses the key
    sel = _sel(sig, statement)
    raw = type("RawLibsodium", (), {"verify": staticmethod(lambda alg, k, m, s: _raw_ok(k, m, s))})()
    # builtin-only admission + a verifier that is libsodium's signature check alone: ACCEPTED (the limit #34 documents)
    assert _run(sel, pk, raw, admission=None, adapter_obj=None).ok is True
    # the adapter policy composed at admission refuses it before any signature check
    rep = _run(sel, pk, raw, admission="adapter", adapter_obj=adapter)
    assert (rep.ok, rep.code, rep.detail_cause) == (False, "trust_snapshot_invalid", "policy_refused")
    # the adapter's own verify refuses it even when admission is NOT composed (defence in depth)
    rep = _run(sel, pk, adapter, admission=None, adapter_obj=None)
    assert (rep.ok, rep.code) == (False, "signature_invalid")
    # both together
    assert _layer(_run(sel, pk, adapter, adapter_obj=adapter)) == "admission_adapter"


def _raw_ok(k, m, s):
    try:
        nb.crypto_sign_open(s + m, k)
        return True
    except Exception:
        return False


@needs_backend
def test_off_curve_canonical_key_passes_builtin_and_is_refused_by_the_adapter(adapter):
    pk = _off_curve_canonical_y()
    assert ka.inspect_ed25519_key(pk) is None and oracle.decompress(pk) is None
    rep = _run(_sel(bytes(64)), pk, adapter, adapter_obj=adapter)
    assert (rep.code, rep.detail_cause) == ("trust_snapshot_invalid", "policy_refused")
    assert _run(_sel(bytes(64)), pk, adapter, admission=None).code == "signature_invalid"  # no admission composed: verify refuses


@needs_backend
def test_small_order_and_noncanonical_key_encodings_are_refused_by_builtin_admission_first(adapter):
    enc = [bytes.fromhex(x["hex"]) for x in SEC["small_order_and_alias_encodings"]]
    assert len(enc) == 48
    layers = Counter()
    for pk in enc:
        rep = _run(_sel(bytes(64)), pk, adapter, adapter_obj=adapter)
        layers[_layer(rep)] += 1
        assert rep.ok is False and rep.code == "trust_snapshot_invalid"
        if ka.inspect_ed25519_key(pk) is not None:
            assert rep.detail_cause == ka.inspect_ed25519_key(pk)  # built-in label wins: it runs first
    assert layers["accepted"] == 0 and layers["admission_builtin"] + layers["admission_adapter"] == 48


# ---- vectors through verify.py's mandatory path ---------------------------------------------------------------
@needs_backend
def test_cctv_through_the_mandatory_path(adapter):
    layers = Counter()
    for name, pk, msg, sig, flagged in _cctv_rows():
        rep = _through_core(adapter, pk, msg, sig)
        layer = _layer(rep)
        layers[layer] += 1
        assert (layer == "accepted") is (not flagged), name
        assert (layer == "accepted") is adapter.verify("ed25519", pk, msg, sig), name  # core path agrees with the adapter alone
        if ka.inspect_ed25519_key(pk) is not None:
            assert layer == "admission_builtin", name
        elif not adapter.acceptable_public_key(pk):
            assert layer == "admission_adapter", name
    assert sum(layers.values()) == 914 and layers["accepted"] == 1
    assert layers["admission_builtin"] + layers["admission_adapter"] + layers["verifier"] == 913
    assert dict(layers) == CCTV_LAYER_COUNTS, dict(layers)


@needs_backend
def test_wycheproof_through_the_mandatory_path(adapter):
    layers = Counter()
    for name, pk, msg, sig, result in _wyc_rows():
        layer = _layer(_through_core(adapter, pk, msg, sig))
        layers[(result, layer)] += 1
        if result == "valid":
            assert layer == "accepted", name
        else:  # invalid, and acceptable (small-order / mixed-order keys): the registry policy refuses all of them
            assert layer != "accepted", name
        assert (layer == "accepted") is adapter.verify("ed25519", pk, msg, sig), name
    assert sum(n for (res, _), n in layers.items() if res == "valid") == 117
    assert sum(n for (res, _), n in layers.items() if res == "acceptable") == 29
    assert dict(layers) == WYC_LAYER_COUNTS, dict(layers)


@needs_backend
def test_strict_verification_vectors_through_the_mandatory_path(adapter):
    layers = Counter()
    for grp, pk, msg, sig in _sec_rows():
        layer = _layer(_through_core(adapter, pk, msg, sig))
        layers[(grp, layer)] += 1
        assert layer != "accepted", grp
        assert (layer == "accepted") is adapter.verify("ed25519", pk, msg, sig)
    assert sum(layers.values()) == 189 and not any(k[1] == "accepted" for k in layers)
    assert dict(layers) == SEC_LAYER_COUNTS, dict(layers)


@needs_backend
def test_real_message_malleation_and_noncanonical_signature_text_are_refused_through_the_core(adapter):
    seed = bytes.fromhex(SYN["synthetic_keys"]["A"]["seed_hex"])
    pk = oracle.pubkey(seed)
    st = r.make_statement_v2()
    sig = oracle.sign(seed, signing_input(st))
    s_plus_l = sig[:32] + (int.from_bytes(sig[32:], "little") + oracle.L).to_bytes(32, "little")
    assert _run(_sel(sig, st), pk, adapter, adapter_obj=adapter).ok is True
    assert _run(_sel(s_plus_l, st), pk, adapter, adapter_obj=adapter).code == "signature_invalid"
    sel = _sel(sig, st)  # a non-canonical base64 spelling of the SAME valid signature: refused on the mandatory path
    text = base64.b64encode(sig).decode("ascii")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    assert text.endswith("=="), text  # 64 bytes: 86 data characters; the last one carries four unused (must-be-zero) bits
    spelled = text[:-3] + alphabet[alphabet.index(text[-3]) ^ 1] + "=="
    assert base64.b64decode(spelled, validate=True) == sig and spelled != text
    env = dict(sel.envelope, signatures=[dict(sel.signatures[0], signature=spelled)])
    sel2 = Sel(True, None, "", env, env["statement"], env["statement_digest"], env["signatures"])
    rep = _run(sel2, pk, adapter, adapter_obj=adapter)
    assert (rep.code, rep.detail) == ("signature_invalid", "signature is not canonical base64")


# Pinned from the run (see docs/adapters/ed25519.md "Layer map"): which layer refused each vector on the mandatory path.
CCTV_LAYER_COUNTS = {"accepted": 1, "admission_adapter": 360, "admission_builtin": 526, "verifier": 27}
WYC_LAYER_COUNTS = {("acceptable", "admission_adapter"): 21, ("acceptable", "admission_builtin"): 8, ("invalid", "admission_adapter"): 1,
                    ("invalid", "verifier"): 63, ("valid", "accepted"): 117}
SEC_LAYER_COUNTS = {("keyholder_r_identity_rows", "verifier"): 8, ("mixed_order_key_rows", "admission_adapter"): 7,
                    ("small_order_key_equation_rows", "admission_builtin"): 146, ("small_order_key_rb_rows", "admission_builtin"): 28}


@needs_backend
def test_key_admission_fails_closed_on_a_non_exact_str_alg():  # review L2 (PR #26 fresh review)
    class LyingAlg(str):
        def __ne__(self, other):
            return True

        def __eq__(self, other):
            return False

        __hash__ = str.__hash__

    verifier = ev.Ed25519Verifier()
    identity_key = bytes([1]) + bytes(31)
    assert verifier.key_admission(LyingAlg("ed25519"), identity_key) is False
    assert verifier.key_admission(b"ed25519", identity_key) is False
    assert verifier.key_admission(None, identity_key) is False
    assert verifier.key_admission("ed25519", identity_key) is False  # exact str, the identity key is still refused
    assert verifier.key_admission("other-alg", identity_key) is True  # not judged here, as before
