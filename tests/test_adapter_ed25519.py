"""Developer tests for registry_adapters.ed25519_verifier (IMPLEMENTED / DEVELOPER-TESTED; not independently qualified).

High-risk (signature verification). Synthetic keys only (tests/vectors/ed25519-synthetic.json, SYNTHETIC-TEST-ONLY).
GAP-G3-07 (operational trust root) is NOT closed by this adapter or these tests.
"""
import ast
import base64
import datetime
import json
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import verify as v  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VEC = json.loads((ROOT / "tests" / "vectors" / "ed25519-synthetic.json").read_text())
HAVE_BACKEND = True
try:
    import cryptography  # noqa: F401
except ImportError:
    HAVE_BACKEND = False

from registry_adapters import ed25519_verifier as ev  # noqa: E402

needs_backend = pytest.mark.skipif(not HAVE_BACKEND, reason="cryptography not installed (requirements-ed25519.lock.txt)")
L = 2 ** 252 + 27742317777372353535851937790883648493
ALG = "ed25519"
V1 = b"ocs-reg/r08-v1/selection\n"
V2 = b"ocs-reg/r08-v2/selection\n"


def _priv(seed_hex):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex))


def _pub(seed_hex):
    from cryptography.hazmat.primitives import serialization as s
    return _priv(seed_hex).public_key().public_bytes(s.Encoding.Raw, s.PublicFormat.Raw)


def _flip(b: bytes, bit: int) -> bytes:
    out = bytearray(b)
    out[bit // 8] ^= 1 << (bit % 8)
    return bytes(out)


@pytest.fixture
def verifier():
    return ev.Ed25519Verifier()


@pytest.fixture
def key_a():
    seed = VEC["synthetic_keys"]["A"]["seed_hex"]
    return _priv(seed), _pub(seed)


@pytest.fixture
def key_b():
    return _pub(VEC["synthetic_keys"]["B"]["seed_hex"])


def test_vector_file_is_labelled_synthetic():
    assert VEC["label"] == "SYNTHETIC-TEST-ONLY"
    assert all(x["label"] == "SYNTHETIC-TEST-ONLY" for x in VEC["rfc8032"])
    assert all(x["label"] == "SYNTHETIC-TEST-ONLY" for x in VEC["synthetic_keys"].values())


@needs_backend
@pytest.mark.parametrize("vec", VEC["rfc8032"], ids=lambda x: x["name"])
def test_rfc8032_known_answers(verifier, vec):
    pk, msg, sig = (bytes.fromhex(vec[k]) for k in ("public_key_hex", "message_hex", "signature_hex"))
    assert _pub(vec["seed_hex"]) == pk
    assert _priv(vec["seed_hex"]).sign(msg) == sig  # deterministic signing reproduces the published signature
    assert verifier.verify(ALG, pk, msg, sig) is True


@needs_backend
@pytest.mark.parametrize("vec", VEC["rfc8032"], ids=lambda x: x["name"])
def test_rfc8032_every_flipped_bit_fails(verifier, vec):
    pk, msg, sig = (bytes.fromhex(vec[k]) for k in ("public_key_hex", "message_hex", "signature_hex"))
    for bit in range(len(sig) * 8):
        assert verifier.verify(ALG, pk, msg, _flip(sig, bit)) is False, ("signature", bit)
    for bit in range(len(pk) * 8):
        assert verifier.verify(ALG, _flip(pk, bit), msg, sig) is False, ("key", bit)
    for bit in range(len(msg) * 8):
        assert verifier.verify(ALG, pk, _flip(msg, bit), sig) is False, ("message", bit)
    assert verifier.verify(ALG, pk, msg + b"\x00", sig) is False
    if msg:
        assert verifier.verify(ALG, pk, msg[:-1], sig) is False


@needs_backend
def test_wrong_key(verifier, key_a, key_b):
    priv, pub = key_a
    sig = priv.sign(b"message")
    assert verifier.verify(ALG, pub, b"message", sig) is True
    assert verifier.verify(ALG, key_b, b"message", sig) is False


@needs_backend
def test_truncated_and_extended_signature_and_bad_key_length(verifier, key_a):
    priv, pub = key_a
    sig = priv.sign(b"m")
    for bad in (sig[:63], sig[:32], sig[:1], b"", sig + b"\x00", sig + sig, b"\x00" + sig):
        assert verifier.verify(ALG, pub, b"m", bad) is False
    for bad in (pub[:31], pub + b"\x00", b""):
        assert verifier.verify(ALG, bad, b"m", sig) is False


@needs_backend
def test_all_zero_key_and_signature(verifier, key_a):
    priv, pub = key_a
    sig = priv.sign(b"m")
    assert verifier.verify(ALG, bytes(32), b"m", bytes(64)) is False
    assert verifier.verify(ALG, pub, b"m", bytes(64)) is False
    assert verifier.verify(ALG, bytes(32), b"m", sig) is False
    assert verifier.verify(ALG, bytes(32), b"", bytes(64)) is False


@needs_backend
def test_non_canonical_s_rejected(verifier, key_a):
    priv, pub = key_a
    sig = priv.sign(b"m")
    s = int.from_bytes(sig[32:], "little")
    assert s < L
    malleated = sig[:32] + (s + L).to_bytes(32, "little")  # same equation mod L, but S >= L
    assert verifier.verify(ALG, pub, b"m", sig) is True
    assert verifier.verify(ALG, pub, b"m", malleated) is False
    assert verifier.verify(ALG, pub, b"m", sig[:32] + L.to_bytes(32, "little")) is False
    assert verifier.verify(ALG, pub, b"m", sig[:32] + (2 ** 256 - 1).to_bytes(32, "little")) is False


@needs_backend
@pytest.mark.parametrize("enc", VEC["small_order_or_noncanonical_public_keys_hex"])
def test_small_order_and_noncanonical_public_keys_rejected(verifier, enc):
    key = bytes.fromhex(enc)
    one = bytes([1]) + bytes(31)
    for msg in (b"", b"anything"):
        for sig in (bytes(64), one + bytes(32), key + bytes(32), bytes(32) + bytes(32)):
            assert verifier.verify(ALG, key, msg, sig) is False


@needs_backend
def test_identity_key_universal_forgery_is_refused_even_though_backend_accepts_it(verifier):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    ident = bytes([1]) + bytes(31)
    forged = ident + bytes(32)  # R = identity, S = 0 satisfies [S]B = R + [k]A for A = identity, every message
    Ed25519PublicKey.from_public_bytes(ident).verify(forged, b"any message")  # raises if a backend ever tightens
    # Observed on cryptography 50.0.1: the backend itself accepts this forgery (the line above does not raise), so the
    # adapter's own small-order refusal is load-bearing. The adapter must refuse regardless of the backend.
    assert verifier.verify(ALG, ident, b"any message", forged) is False


@needs_backend
def test_v1_and_v2_signing_domains_do_not_cross_verify(verifier, key_a):
    priv, pub = key_a
    body = c.canonical_bytes(r.make_statement())
    sig_v1, sig_v2 = priv.sign(V1 + body), priv.sign(V2 + body)
    assert verifier.verify(ALG, pub, V1 + body, sig_v1) is True
    assert verifier.verify(ALG, pub, V2 + body, sig_v2) is True
    assert verifier.verify(ALG, pub, V2 + body, sig_v1) is False  # v1-domain signature is not a v2 statement signature
    assert verifier.verify(ALG, pub, V1 + body, sig_v2) is False  # and the reverse
    assert verifier.verify(ALG, pub, body, sig_v1) is False  # no domain at all


@needs_backend
@pytest.mark.parametrize("alg", ["Ed25519", "ED25519", "ed25519 ", " ed25519", "", "ed448", "rsa", "ed25519\x00", None, b"ed25519", 25519])
def test_wrong_algorithm_string(verifier, key_a, alg):
    priv, pub = key_a
    assert verifier.verify(alg, pub, b"m", priv.sign(b"m")) is False


@needs_backend
def test_str_subclass_algorithm_rejected(verifier, key_a):
    class S(str):
        pass
    priv, pub = key_a
    assert verifier.verify(S("ed25519"), pub, b"m", priv.sign(b"m")) is False


class _B(bytes):
    pass


@needs_backend
@pytest.mark.parametrize("bad", [None, "str", 1, 1.5, [1], (1,), {}, bytearray(b"x"), memoryview(b"x"), _B(b"x")])
def test_non_bytes_inputs_return_false_and_never_raise(verifier, key_a, bad):
    priv, pub = key_a
    sig = priv.sign(b"m")
    assert verifier.verify(ALG, bad, b"m", sig) is False
    assert verifier.verify(ALG, pub, bad, sig) is False
    assert verifier.verify(ALG, pub, b"m", bad) is False
    # a correct-typed value in bytearray/memoryview/subclass form is also refused (exact bytes only)
    assert verifier.verify(ALG, bytearray(pub), b"m", sig) is False
    assert verifier.verify(ALG, pub, bytearray(b"m"), sig) is False
    assert verifier.verify(ALG, pub, b"m", bytearray(sig)) is False
    assert verifier.verify(ALG, _B(pub), b"m", sig) is False


@needs_backend
def test_backend_exception_returns_false_never_raises_never_true(verifier, key_a):
    priv, pub = key_a
    sig = priv.sign(b"m")

    class Boom:
        @staticmethod
        def from_public_bytes(_):
            raise RuntimeError("backend fault")

    class BoomVerify:
        @staticmethod
        def from_public_bytes(_):
            class K:
                def verify(self, *a):
                    raise MemoryError("backend fault")
            return K()

    verifier._public_key_cls = Boom
    assert verifier.verify(ALG, pub, b"m", sig) is False
    verifier._public_key_cls = BoomVerify
    assert verifier.verify(ALG, pub, b"m", sig) is False


def test_dependency_absent_is_explicit_and_core_still_refuses(monkeypatch):
    for name in [m for m in sys.modules if m == "cryptography" or m.startswith("cryptography.")]:
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(ev.Ed25519Unavailable):
        ev.Ed25519Verifier()
    assert ev.load_verifier_or_none() is None
    rep = _run_core(r.make_envelope(), verifier=ev.load_verifier_or_none())
    assert rep.ok is False and rep.code == "verifier_unavailable"
    assert rep.layers["authenticity"] == "refuse" and rep.authenticated is False


# ---- end-to-end through the core with a real signature -------------------------------------------------------
Sel = namedtuple("Sel", "ok code detail envelope statement statement_digest signatures")
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
GRANT = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
NOW = r.NOW


def _trust(pub):
    return v.TrustSnapshot("snapshot-1", 1, "2026-10-27T00:00:00Z",
                           (v.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", pub, (GRANT,)),))


def _signed_envelope(priv, statement=None, prefix=None):
    from registry_successor.selection import signing_input
    statement = statement or r.make_statement()
    message = signing_input(statement) if prefix is None else prefix + c.canonical_bytes(statement)
    sig = base64.b64encode(priv.sign(message)).decode("ascii")
    return {"statement": statement, "statement_digest": c.digest(statement),
            "signatures": [{"alg": "ed25519", "key_id": "key-test-1", "signature": sig}]}


def _run_core(env, verifier, pub=b"p" * 32):
    sel = Sel(True, None, "", env, env["statement"], env["statement_digest"], env["signatures"])
    return v.verify_selection(sel, CTX, _trust(pub), verifier, NOW)


@needs_backend
def test_core_authenticates_real_signature(verifier, key_a):
    priv, pub = key_a
    rep = _run_core(_signed_envelope(priv), verifier, pub)
    assert rep.ok is True and rep.authenticated is True and rep.operationally_authorized is False
    assert rep.layers["authenticity"] == "pass"


@needs_backend
def test_core_refuses_wrong_key_tampered_statement_and_foreign_domain(verifier, key_a, key_b):
    priv, pub = key_a
    env = _signed_envelope(priv)
    assert _run_core(env, verifier, key_b).code == "signature_invalid"
    tampered = dict(env, statement=r.make_statement(epoch=2))
    tampered["statement_digest"] = c.digest(tampered["statement"])
    assert _run_core(tampered, verifier, pub).code == "signature_invalid"
    v2_signed = _signed_envelope(priv, prefix=V2)  # a v2-domain signature must not authenticate a v1 selection
    assert _run_core(v2_signed, verifier, pub).code == "signature_invalid"
    assert _run_core(_signed_envelope(priv, prefix=V1), verifier, pub).ok is True


# ---- hash lock, independence ---------------------------------------------------------------------------------
def test_every_pinned_requirement_has_hashes():
    text = (ROOT / "requirements-ed25519.lock.txt").read_text().replace("\\\n", " ")
    reqs = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert reqs
    names = set()
    for ln in reqs:
        assert re.match(r"^[A-Za-z0-9_.\-]+==[0-9][^\s;]*(\s*;[^-]*)?(\s+--hash=sha256:[0-9a-f]{64})+\s*$", ln), ln
        names.add(ln.split("==")[0].lower())
    assert "cryptography" in names
    assert not [ln for ln in reqs if "--hash=" not in ln]


def _imports(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level:
            names.add("<relative>")
    return names


def test_adapter_does_not_import_the_core_or_other_registry_packages():
    for path in (ROOT / "registry_adapters").glob("*.py"):
        bad = _imports(path) & {"registry_successor", "registry_contract", "registry_consumer", "baseline", "engine", "<relative>"}
        assert not bad, (path.name, bad)


def test_core_does_not_import_the_adapter_or_the_backend():
    for path in (ROOT / "registry_successor").glob("*.py"):
        assert "registry_adapters" not in _imports(path) and not _imports(path) & {"cryptography", "nacl"}, path.name
        assert "registry_adapters" not in path.read_text(), path.name
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); import registry_successor.verify, registry_successor.selection; "
             "bad=[m for m in sys.modules if m.split('.')[0] in ('cryptography','registry_adapters')]; "
             "assert not bad, bad")
    done = subprocess.run([sys.executable, "-c", probe, str(ROOT)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
