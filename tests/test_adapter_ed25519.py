"""Developer tests for registry_adapters.ed25519_verifier (IMPLEMENTED / DEVELOPER-TESTED; not independently qualified).

High-risk (signature verification). SECURITY REVIEW STATUS: BLOCKED - independent cryptographic reviewer not yet named.
Synthetic keys only (tests/vectors/*.json are SYNTHETIC-TEST-ONLY or public Wycheproof data).
GAP-G3-07 (operational trust root) is NOT closed by this adapter or these tests.

Verifier under test: PyNaCl/libsodium. Independent instruments (never imported by the adapter): tests/ed25519_oracle.py
(plain-Python RFC 8032 arithmetic and an executable statement of the registry policy) and, for the CHARACTERIZATION
tests only, the raw `cryptography` backend from the test-only lock requirements-ed25519-test-oracle.lock.txt.
"""
import ast
import base64
import hashlib
import importlib.metadata
import itertools
import json
import os
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import ed25519_oracle as oracle  # noqa: E402
import r08_support as r  # noqa: E402
from registry_successor import common as c  # noqa: E402
from registry_successor import verify as v  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VECDIR = ROOT / "tests" / "vectors"
VEC = json.loads((VECDIR / "ed25519-synthetic.json").read_text())
SEC = json.loads((VECDIR / "ed25519-security-vectors.json").read_text())
WYC_DIR = VECDIR / "wycheproof"
WYC_RAW = (WYC_DIR / "ed25519_test.json").read_bytes()
WYC = json.loads(WYC_RAW)

try:
    import nacl.bindings as nb
    from nacl.signing import SigningKey
    HAVE_BACKEND = True
except ImportError:
    HAVE_BACKEND = False
try:
    import cryptography  # noqa: F401
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    HAVE_CRYPTOGRAPHY = True
except ImportError:
    HAVE_CRYPTOGRAPHY = False

from registry_adapters import ed25519_verifier as ev  # noqa: E402

needs_backend = pytest.mark.skipif(not HAVE_BACKEND, reason="pynacl not installed (requirements-ed25519.lock.txt)")
needs_cryptography = pytest.mark.skipif(
    not HAVE_CRYPTOGRAPHY,
    reason="cryptography not installed: the CHARACTERIZATION of the raw backend needs requirements-ed25519-test-oracle.lock.txt")
P, L = oracle.p, oracle.L
ALG = "ed25519"
V1 = b"ocs-reg/r08-v1/selection\n"
V2 = b"ocs-reg/r08-v2/selection\n"
S_VALUES = {"0": 0, "1": 1, "L-1": L - 1, "L": L, "L+1": L + 1, "2^256-1": 2 ** 256 - 1}
IDENTITY = bytes([1]) + bytes(31)


def _enc(y, sign=0):
    return (y | (sign << 255)).to_bytes(32, "little")


def _sign(seed_hex, msg):
    return SigningKey(bytes.fromhex(seed_hex)).sign(msg).signature


def _pub(seed_hex):
    return bytes(SigningKey(bytes.fromhex(seed_hex)).verify_key)


def _flip(b: bytes, bit: int) -> bytes:
    out = bytearray(b)
    out[bit // 8] ^= 1 << (bit % 8)
    return bytes(out)


def _sodium_accepts(pk, msg, sig):
    """Raw libsodium verification (crypto_sign_verify_detached via crypto_sign_open) with NO adapter checks."""
    try:
        nb.crypto_sign_open(sig + msg, pk)
        return True
    except Exception:
        return False


def _cryptography_accepts(pk, msg, sig):
    try:
        Ed25519PublicKey.from_public_bytes(pk).verify(sig, msg)
        return True
    except (InvalidSignature, ValueError):
        return False


def _rows(group):
    return [(x["pk"], x["msg"], x["sig"], x["why"]) for x in SEC[group]]


def _b(x):
    return bytes.fromhex(x)


@pytest.fixture
def verifier():
    return ev.Ed25519Verifier()


@pytest.fixture
def key_a():
    seed = VEC["synthetic_keys"]["A"]["seed_hex"]
    return seed, _pub(seed)


@pytest.fixture
def key_b():
    return _pub(VEC["synthetic_keys"]["B"]["seed_hex"])


def test_vector_files_are_labelled_synthetic():
    assert VEC["label"] == "SYNTHETIC-TEST-ONLY" and SEC["label"] == "SYNTHETIC-TEST-ONLY"
    assert all(x["label"] == "SYNTHETIC-TEST-ONLY" for x in VEC["rfc8032"])
    assert all(x["label"] == "SYNTHETIC-TEST-ONLY" for x in VEC["synthetic_keys"].values())


# ---- RFC 8032 section 7.1 positive vectors ----------------------------------------------------------------------
@needs_backend
@pytest.mark.parametrize("vec", VEC["rfc8032"], ids=lambda x: x["name"])
def test_rfc8032_known_answers(verifier, vec):
    seed, pk, msg, sig = _b(vec["seed_hex"]), *(_b(vec[k]) for k in ("public_key_hex", "message_hex", "signature_hex"))
    assert oracle.pubkey(seed) == pk and oracle.sign(seed, msg) == sig  # independent plain-Python derivation reproduces them
    assert _pub(vec["seed_hex"]) == pk and _sign(vec["seed_hex"], msg) == sig  # and so does libsodium signing
    assert verifier.verify(ALG, pk, msg, sig) is True
    assert verifier.acceptable_public_key(pk) is True


@needs_backend
@pytest.mark.parametrize("vec", VEC["rfc8032"], ids=lambda x: x["name"])
def test_rfc8032_every_flipped_bit_fails(verifier, vec):
    pk, msg, sig = (_b(vec[k]) for k in ("public_key_hex", "message_hex", "signature_hex"))
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
    seed, pub = key_a
    sig = _sign(seed, b"message")
    assert verifier.verify(ALG, pub, b"message", sig) is True
    assert verifier.verify(ALG, key_b, b"message", sig) is False


@needs_backend
def test_truncated_and_extended_signature_and_bad_key_length(verifier, key_a):
    seed, pub = key_a
    sig = _sign(seed, b"m")
    for bad in (sig[:63], sig[:32], sig[:1], b"", sig + b"\x00", sig + sig, b"\x00" + sig):
        assert verifier.verify(ALG, pub, b"m", bad) is False
    for bad in (pub[:31], pub + b"\x00", b""):
        assert verifier.verify(ALG, bad, b"m", sig) is False


@needs_backend
def test_signature_message_boundary_cannot_be_shifted(verifier, key_a):
    """The library verifies `signature || message`; the adapter's exact length checks are what stop a boundary shift
    (a 63-byte 'signature' whose missing byte is prepended to the message, or a 65-byte one that borrows a message byte)."""
    seed, pub = key_a
    msg = b"boundary-shift message"
    sig = _sign(seed, msg)
    assert verifier.verify(ALG, pub, msg, sig) is True
    assert _sodium_accepts(pub, msg, sig) is True
    assert verifier.verify(ALG, pub, sig[63:] + msg, sig[:63]) is False
    assert verifier.verify(ALG, pub, msg[1:], sig + msg[:1]) is False
    assert verifier.verify(ALG, pub, sig[32:] + msg, sig[:32]) is False
    assert verifier.verify(ALG, pub, b"", sig + msg) is False


@needs_backend
def test_all_zero_key_and_signature(verifier, key_a):
    seed, pub = key_a
    sig = _sign(seed, b"m")
    assert verifier.verify(ALG, bytes(32), b"m", bytes(64)) is False
    assert verifier.verify(ALG, pub, b"m", bytes(64)) is False
    assert verifier.verify(ALG, bytes(32), b"m", sig) is False
    assert verifier.verify(ALG, bytes(32), b"", bytes(64)) is False


# ---- S malleability (S < L is enforced by the library) ----------------------------------------------------------
@needs_backend
def test_signature_malleability_rejected_and_attributable_to_the_s_range_check(verifier, key_a):
    seed, pub = key_a
    msg = b"m"
    sig = _sign(seed, msg)
    s = int.from_bytes(sig[32:], "little")
    assert s < L and verifier.verify(ALG, pub, msg, sig) is True
    for name, bad_s in (("S+L", s + L), ("S+2L", s + 2 * L), ("S|2^255", s | (1 << 255)), ("L", L), ("L+1", L + 1), ("2^256-1", 2 ** 256 - 1)):
        malleated = sig[:32] + bad_s.to_bytes(32, "little")
        assert verifier.verify(ALG, pub, msg, malleated) is False, name
        assert _sodium_accepts(pub, msg, malleated) is False, name  # library enforces S < L on its own
    # S+L satisfies the verification equation (it is the same scalar mod L), so only the range check refuses it
    assert oracle.raw_equation(pub, msg, sig[:32] + (s + L).to_bytes(32, "little")) is True
    assert oracle.policy_verify(pub, msg, sig[:32] + (s + L).to_bytes(32, "little")) is False


# ---- small-order public keys and R: the full matrix --------------------------------------------------------------
SMALL_ORDER_ENCODINGS = [_b(e["hex"]) for e in SEC["small_order_and_alias_encodings"]]


def test_small_order_encoding_list_is_complete_and_correct():
    assert len(SMALL_ORDER_ENCODINGS) == 48 and len(set(SMALL_ORDER_ENCODINGS)) == 48
    canonical_hex = set(VEC["small_order_or_noncanonical_public_keys_hex"])
    assert {e.hex() for e in SMALL_ORDER_ENCODINGS} >= canonical_hex  # every encoding the earlier vector file named
    points = set()
    for e in SMALL_ORDER_ENCODINGS:
        point = oracle.decompress(e, lax=True)
        is_alias = int.from_bytes(e, "little") & (2 ** 255 - 1) >= P
        if point is None:
            continue
        if not is_alias:
            assert oracle.is_small_order(point), e.hex()
            zi = pow(point[2], P - 2, P)
            points.add((point[0] * zi % P, point[1] * zi % P))
        else:  # y + p alias: decodes (leniently) to a small-order or mixed-order point, never to a prime-order non-identity one
            assert oracle.is_small_order(point) or not oracle.in_prime_order_subgroup(point), e.hex()
    assert len(points) == 8  # all eight torsion points are represented (4 of order 8, 2 of order 4, order 2, identity)
    assert len([e for e in SMALL_ORDER_ENCODINGS if int.from_bytes(e, "little") & (2 ** 255 - 1) >= P]) == 38  # the y + p aliases


@needs_backend
def test_small_order_keys_and_r_with_every_s_are_refused_by_adapter_and_by_libsodium(verifier):
    count = 0
    for a_enc in SMALL_ORDER_ENCODINGS:
        assert verifier.acceptable_public_key(a_enc) is False, a_enc.hex()
        for r_enc in SMALL_ORDER_ENCODINGS:
            for s_name, s_val in S_VALUES.items():
                sig = r_enc + s_val.to_bytes(32, "little")
                for msg in (b"", b"m"):
                    count += 1
                    assert verifier.verify(ALG, a_enc, msg, sig) is False, (a_enc.hex(), r_enc.hex(), s_name)
                    assert _sodium_accepts(a_enc, msg, sig) is False, (a_enc.hex(), r_enc.hex(), s_name)
    assert count == 48 * 48 * 6 * 2


@needs_backend
@pytest.mark.parametrize("pk,msg,sig,why", _rows("small_order_key_equation_rows") + _rows("small_order_key_rb_rows"))
def test_every_equation_satisfying_small_order_key_row_is_refused(verifier, pk, msg, sig, why):
    pk, msg, sig = _b(pk), _b(msg), _b(sig)
    assert oracle.raw_equation(pk, msg, sig) is True  # the row is a real forgery candidate for a verifier without the policy
    assert verifier.verify(ALG, pk, msg, sig) is False
    assert _sodium_accepts(pk, msg, sig) is False


@needs_backend
@pytest.mark.parametrize("enc", VEC["small_order_or_noncanonical_public_keys_hex"])
def test_small_order_and_noncanonical_public_keys_rejected(verifier, enc):
    key = _b(enc)
    for msg in (b"", b"anything"):
        for sig in (bytes(64), IDENTITY + bytes(32), key + bytes(32), bytes(32) + bytes(32)):
            assert verifier.verify(ALG, key, msg, sig) is False


# ---- the identity-key universal forgery: named reproducible negative test ---------------------------------------
IDENTITY_FORGERY_SIGNATURE = IDENTITY + bytes(32)  # R = identity, S = 0: 01 followed by 63 zero bytes


@needs_backend
@pytest.mark.parametrize("msg", [b"", b"any message", b"ocs-reg/r08-v1/selection\n{\"x\":1}", bytes(range(256)) * 64])
def test_identity_key_universal_forgery_is_refused_by_the_adapter(verifier, msg):
    assert IDENTITY_FORGERY_SIGNATURE == bytes([1]) + bytes(63)
    assert verifier.verify(ALG, IDENTITY, msg, IDENTITY_FORGERY_SIGNATURE) is False
    # the non-canonical encodings of the identity key are refused too
    for alias in (_enc(1, 1), _enc(P + 1), _enc(P + 1, 1)):
        assert verifier.verify(ALG, alias, msg, IDENTITY_FORGERY_SIGNATURE) is False
        assert verifier.verify(ALG, alias, msg, alias + bytes(32)) is False
    assert verifier.acceptable_public_key(IDENTITY) is False


@needs_backend
def test_identity_key_forgery_is_refused_by_libsodium_itself_at_both_layers():
    assert _sodium_accepts(IDENTITY, b"any message", IDENTITY_FORGERY_SIGNATURE) is False
    assert bool(nb.crypto_core_ed25519_is_valid_point(IDENTITY)) is False


@needs_backend
@pytest.mark.parametrize("scalar", [1, 2, 12345, L - 1])
def test_identity_key_forgery_family_with_non_small_order_r_is_refused(verifier, scalar):
    """For A = identity the equation reduces to [S]B = R, so (R = [s]B, S = s) verifies for EVERY message, and R is an ordinary
    prime-order point: R-side checks cannot stop it, only the public-key policy does. (s = 1 is R = the base point.)"""
    sig = oracle.compress(oracle.mul(scalar, oracle.G)) + scalar.to_bytes(32, "little")
    for msg in (b"", b"any message", b"other"):
        assert oracle.raw_equation(IDENTITY, msg, sig) is True
        assert verifier.verify(ALG, IDENTITY, msg, sig) is False
        assert _sodium_accepts(IDENTITY, msg, sig) is False


def test_identity_forgery_satisfies_the_verification_equation():
    """Why the key refusal is load-bearing: the equation itself holds for A = identity, R = identity, S = 0 for every message."""
    assert all(oracle.raw_equation(IDENTITY, m, IDENTITY_FORGERY_SIGNATURE) for m in (b"", b"any message"))
    assert oracle.policy_verify(IDENTITY, b"any message", IDENTITY_FORGERY_SIGNATURE) is False


# CHARACTERIZATION (not a requirement on the adapter): records what the raw `cryptography` backend does. It is the
# behaviour that motivated the remediation (the adapter used to rely on pre-filters in front of it) and it is why
# `cryptography` is no longer the verifier. These tests only observe; they never gate the adapter's behaviour.
@needs_cryptography
def test_CHARACTERIZATION_raw_cryptography_backend_accepts_the_identity_key_forgery():
    for msg in (b"", b"any message", b"ocs-reg/r08-v1/selection\n{\"x\":1}"):
        Ed25519PublicKey.from_public_bytes(IDENTITY).verify(IDENTITY_FORGERY_SIGNATURE, msg)  # raises InvalidSignature if it ever tightens
        assert _cryptography_accepts(IDENTITY, msg, IDENTITY_FORGERY_SIGNATURE) is True


@needs_cryptography
@pytest.mark.parametrize("scalar", [1, 2, 12345])
def test_CHARACTERIZATION_raw_cryptography_backend_accepts_the_identity_key_forgery_family_with_r_equal_s_times_b(scalar):
    sig = oracle.compress(oracle.mul(scalar, oracle.G)) + scalar.to_bytes(32, "little")
    for msg in (b"", b"any message"):
        assert _cryptography_accepts(IDENTITY, msg, sig) is True


@needs_cryptography
@needs_backend
def test_CHARACTERIZATION_raw_cryptography_backend_accepts_small_order_rows_that_libsodium_and_the_adapter_refuse(verifier):
    accepted = [(pk, msg, sig) for pk, msg, sig, _ in _rows("small_order_key_equation_rows") + _rows("small_order_key_rb_rows")
                if _cryptography_accepts(_b(pk), _b(msg), _b(sig))]
    assert accepted, "expected the raw cryptography backend to accept some small-order-key rows"
    for pk, msg, sig in accepted:
        assert verifier.verify(ALG, _b(pk), _b(msg), _b(sig)) is False
        assert _sodium_accepts(_b(pk), _b(msg), _b(sig)) is False


def test_ci_installs_the_test_only_oracle_lock():
    """In CI (GitHub sets CI=true) the characterization must run, not skip: the workflow installs the test-only lock."""
    if os.environ.get("CI") == "true":
        assert HAVE_CRYPTOGRAPHY, "CI must install requirements-ed25519-test-oracle.lock.txt"
        assert HAVE_BACKEND, "CI must install requirements-ed25519.lock.txt"


# ---- R: small-order R by the key holder (library refuses it) -----------------------------------------------------
@needs_backend
@pytest.mark.parametrize("pk,msg,sig,why", _rows("keyholder_r_identity_rows"))
def test_honest_key_with_identity_r_is_refused_by_the_library(verifier, pk, msg, sig, why):
    pk, msg, sig = _b(pk), _b(msg), _b(sig)
    assert oracle.raw_equation(pk, msg, sig) is True  # S = h*a: the equation holds
    assert verifier.acceptable_public_key(pk) is True  # the key is honest; only R is degenerate
    assert verifier.verify(ALG, pk, msg, sig) is False
    assert _sodium_accepts(pk, msg, sig) is False  # libsodium's small-order-R refusal (and re-encoding comparison)


# ---- mixed-order public keys: the subgroup requirement -----------------------------------------------------------
@needs_backend
@pytest.mark.parametrize("pk,msg,sig,why", _rows("mixed_order_key_rows"))
def test_mixed_order_public_key_is_refused_although_libsodium_signature_check_accepts_it(verifier, pk, msg, sig, why):
    pk, msg, sig = _b(pk), _b(msg), _b(sig)
    point = oracle.decompress(pk)
    assert not oracle.is_small_order(point) and not oracle.in_prime_order_subgroup(point)  # genuinely mixed-order
    assert oracle.raw_equation(pk, msg, sig) is True
    # libsodium's signature verification alone does NOT enforce the subgroup rule ...
    assert _sodium_accepts(pk, msg, sig) is True
    # ... the point-validation call does, and the adapter applies it
    assert bool(nb.crypto_core_ed25519_is_valid_point(pk)) is False
    assert verifier.acceptable_public_key(pk) is False
    assert verifier.verify(ALG, pk, msg, sig) is False


@needs_backend
def test_cofactorless_semantics_a_mixed_order_r_is_refused(verifier, key_a):
    """The verification equation is cofactorless: a signature whose R carries a torsion component satisfies the cofactored equation
    of RFC 8032 but not the cofactorless one, and is refused (libsodium compares the re-encoded R byte for byte)."""
    seed, pub = key_a
    a, _ = oracle.secret_expand(bytes.fromhex(seed))
    order8 = next(oracle.decompress(_b(e["hex"])) for e in SEC["small_order_and_alias_encodings"]
                  if oracle.decompress(_b(e["hex"])) and not oracle.eq(oracle.mul(4, oracle.decompress(_b(e["hex"]))), oracle.ZERO))
    assert oracle.is_small_order(order8) and not oracle.eq(oracle.mul(4, order8), oracle.ZERO)  # a torsion point of order 8
    msg = b"cofactorless"
    rr = 123456789
    R = oracle.compress(oracle.add(oracle.mul(rr, oracle.G), order8))
    sig = R + ((rr + oracle._h(R, pub, msg) * a) % L).to_bytes(32, "little")
    assert oracle.cofactored_equation(pub, msg, sig) is True  # a cofactored verifier would accept it
    assert oracle.raw_equation(pub, msg, sig) is False
    assert verifier.verify(ALG, pub, msg, sig) is False
    assert _sodium_accepts(pub, msg, sig) is False
    assert oracle.policy_verify(pub, msg, sig) is False


@needs_backend
def test_prime_order_keys_are_accepted_by_the_key_policy(verifier):
    for i in range(40):
        seed = hashlib.sha256(b"ocs-ed25519-honest-key-%d" % i).digest()
        pk = bytes(SigningKey(seed).verify_key)
        assert verifier.acceptable_public_key(pk) is True
        assert oracle.key_acceptable(pk) is True
        msg = b"honest-%d" % i
        assert verifier.verify(ALG, pk, msg, SigningKey(seed).sign(msg).signature) is True


# ---- non-canonical encodings of A and R ----------------------------------------------------------------------
NONCANONICAL = [_enc(y, s) for y in range(P, 2 ** 255) for s in (0, 1)] + [_enc(1, 1), _enc(P - 1, 1)]  # y >= p, and x = 0 with sign 1


def test_noncanonical_encoding_set_is_exhaustive_and_each_alias_is_unusable_under_the_policy():
    """All 40 non-canonical encodings (y >= p: 19 values x 2 sign bits; x = 0 with sign bit set: 2). Even a verifier that decoded
    them leniently would have to treat each as undecodable, small-order or mixed-order, never as a prime-order non-identity key."""
    assert len(NONCANONICAL) == 40 and len(set(NONCANONICAL)) == 40
    for e in NONCANONICAL:
        assert oracle.decompress(e) is None  # strict RFC 8032 decoding refuses every one
        lax = oracle.decompress(e, lax=True)
        if lax is not None:
            assert oracle.is_small_order(lax) or not oracle.in_prime_order_subgroup(lax), e.hex()


@needs_backend
def test_noncanonical_public_keys_and_r_are_refused(verifier, key_a):
    seed, pub = key_a
    sig = _sign(seed, b"m")
    for e in NONCANONICAL:
        assert verifier.acceptable_public_key(e) is False, e.hex()
        assert verifier.verify(ALG, e, b"m", sig) is False
        assert verifier.verify(ALG, pub, b"m", e + sig[32:]) is False  # alias as R, honest key
        assert verifier.verify(ALG, e, b"m", e + bytes(32)) is False
        assert _sodium_accepts(e, b"m", sig) is False
        assert _sodium_accepts(pub, b"m", e + sig[32:]) is False


@needs_backend
def test_flipped_sign_bit_of_honest_key_and_r_is_refused(verifier, key_a):
    seed, pub = key_a
    sig = _sign(seed, b"m")
    assert verifier.verify(ALG, _flip(pub, 255), b"m", sig) is False
    assert verifier.verify(ALG, pub, b"m", _flip(sig, 255)) is False


# ---- envelope: algorithm string, types, subclasses ------------------------------------------------------------
@needs_backend
def test_v1_and_v2_signing_domains_do_not_cross_verify(verifier, key_a):
    seed, pub = key_a
    body = c.canonical_bytes(r.make_statement())
    sig_v1, sig_v2 = _sign(seed, V1 + body), _sign(seed, V2 + body)
    assert verifier.verify(ALG, pub, V1 + body, sig_v1) is True
    assert verifier.verify(ALG, pub, V2 + body, sig_v2) is True
    assert verifier.verify(ALG, pub, V2 + body, sig_v1) is False  # v1-domain signature is not a v2 statement signature
    assert verifier.verify(ALG, pub, V1 + body, sig_v2) is False  # and the reverse
    assert verifier.verify(ALG, pub, body, sig_v1) is False  # no domain at all


@needs_backend
@pytest.mark.parametrize("alg", ["Ed25519", "ED25519", "ed25519 ", " ed25519", "", "ed448", "rsa", "ed25519\x00", None, b"ed25519", 25519])
def test_wrong_algorithm_string(verifier, key_a, alg):
    seed, pub = key_a
    assert verifier.verify(alg, pub, b"m", _sign(seed, b"m")) is False


@needs_backend
def test_str_subclass_algorithm_rejected(verifier, key_a):
    class S(str):
        pass
    seed, pub = key_a
    assert verifier.verify(S("ed25519"), pub, b"m", _sign(seed, b"m")) is False


class _B(bytes):
    pass


@needs_backend
@pytest.mark.parametrize("bad", [None, "str", 1, 1.5, [1], (1,), {}, bytearray(b"x"), memoryview(b"x"), _B(b"x")])
def test_non_bytes_inputs_return_false_and_never_raise(verifier, key_a, bad):
    seed, pub = key_a
    sig = _sign(seed, b"m")
    assert verifier.verify(ALG, bad, b"m", sig) is False
    assert verifier.verify(ALG, pub, bad, sig) is False
    assert verifier.verify(ALG, pub, b"m", bad) is False
    # a correct-typed value in bytearray/memoryview/subclass form is also refused (exact bytes only)
    assert verifier.verify(ALG, bytearray(pub), b"m", sig) is False
    assert verifier.verify(ALG, pub, bytearray(b"m"), sig) is False
    assert verifier.verify(ALG, pub, b"m", bytearray(sig)) is False
    assert verifier.verify(ALG, memoryview(pub), b"m", sig) is False
    assert verifier.verify(ALG, pub, memoryview(b"m"), sig) is False
    assert verifier.verify(ALG, pub, b"m", memoryview(sig)) is False
    assert verifier.verify(ALG, _B(pub), b"m", sig) is False
    assert verifier.verify(ALG, pub, _B(b"m"), sig) is False
    assert verifier.verify(ALG, pub, b"m", _B(sig)) is False
    assert verifier.acceptable_public_key(bad) is False
    assert verifier.acceptable_public_key(bytearray(pub)) is False and verifier.acceptable_public_key(_B(pub)) is False


@needs_backend
def test_determinism(key_a):
    seed, pub = key_a
    cases = [(pub, b"m", _sign(seed, b"m")), (pub, b"m", _flip(_sign(seed, b"m"), 7)), (IDENTITY, b"m", IDENTITY_FORGERY_SIGNATURE),
             (pub, bytes(1 << 20), _sign(seed, bytes(1 << 20)))]
    verifiers = [ev.Ed25519Verifier() for _ in range(3)]
    expected = [True, False, False, True]
    for ver in verifiers:
        for _ in range(25):
            assert [ver.verify(ALG, *case) for case in cases] == expected
    assert [type(x) for x in expected] == [bool] * 4


@needs_backend
def test_backend_exception_returns_false_never_raises_never_true(verifier, key_a):
    seed, pub = key_a
    sig = _sign(seed, b"m")
    assert verifier.verify(ALG, pub, b"m", sig) is True

    def boom(*_a):
        raise MemoryError("backend fault")

    verifier._sign_open = boom
    assert verifier.verify(ALG, pub, b"m", sig) is False
    verifier._sign_open = nb.crypto_sign_open
    verifier._is_valid_point = boom
    assert verifier.verify(ALG, pub, b"m", sig) is False
    assert verifier.acceptable_public_key(pub) is False


def test_dependency_absent_is_explicit_and_core_still_refuses(monkeypatch):
    for name in [m for m in sys.modules if m == "nacl" or m.startswith("nacl.")] + ["nacl", "nacl.bindings"]:
        monkeypatch.setitem(sys.modules, name, None)
    with pytest.raises(ev.Ed25519Unavailable):
        ev.Ed25519Verifier()
    assert ev.load_verifier_or_none() is None
    rep = _run_core(r.make_envelope(), verifier=ev.load_verifier_or_none())
    assert rep.ok is False and rep.code == "verifier_unavailable"
    assert rep.layers["authenticity"] == "refuse" and rep.authenticated is False


@needs_backend
def test_backend_without_the_ed25519_point_api_is_unavailable(monkeypatch):
    monkeypatch.setattr(nb, "has_crypto_core_ed25519", False)
    with pytest.raises(ev.Ed25519Unavailable):
        ev.Ed25519Verifier()
    assert ev.load_verifier_or_none() is None


# ---- load-time known-answer self-test: a backend with different semantics must not be usable -------------------
@needs_backend
def test_kat_constants_match_the_independent_oracle():
    assert oracle.pubkey(_b(VEC["rfc8032"][0]["seed_hex"])) == ev._KAT_PK and oracle.policy_verify(ev._KAT_PK, b"", ev._KAT_SIG)
    s = int.from_bytes(ev._KAT_SIG[32:], "little")
    assert ev._KAT_SIG_S_PLUS_L == ev._KAT_SIG[:32] + (s + L).to_bytes(32, "little")
    assert ev._KAT_IDENTITY == IDENTITY
    pk, msg, sig = ev._KAT_KEYHOLDER_R_IDENTITY
    assert oracle.key_acceptable(pk) and oracle.raw_equation(pk, msg, sig) and sig[:32] == IDENTITY and oracle.policy_verify(pk, msg, sig) is False
    pk, msg, sig = ev._KAT_MIXED_ORDER
    point = oracle.decompress(pk)
    assert not oracle.is_small_order(point) and not oracle.in_prime_order_subgroup(point) and oracle.raw_equation(pk, msg, sig)
    assert _sodium_accepts(pk, msg, sig) is True  # so the self-test really exercises the key-policy call


@needs_backend
@pytest.mark.parametrize("weak", ["no_key_policy", "accepts_everything", "rejects_everything"])
def test_weakened_backend_fails_the_self_test_and_is_unavailable(monkeypatch, weak):
    def accept(*_a):
        return b""

    def reject(*_a):
        raise ValueError("no")

    pair = {"no_key_policy": (lambda pk: True, nb.crypto_sign_open),  # signature layer only: mixed-order key slips through
            "accepts_everything": (lambda pk: True, accept),
            "rejects_everything": (nb.crypto_core_ed25519_is_valid_point, reject)}[weak]
    monkeypatch.setattr(ev, "_load_backend", lambda: pair)
    with pytest.raises(ev.Ed25519Unavailable):
        ev.Ed25519Verifier()
    assert ev.load_verifier_or_none() is None


# ---- Wycheproof ----------------------------------------------------------------------------------------------
def test_wycheproof_file_is_the_recorded_upstream_file():
    source = (WYC_DIR / "SOURCE.md").read_text()
    assert hashlib.sha256(WYC_RAW).hexdigest() in source and "d17cc89fa5c8f4f4d378b5385ebf75da5d0926c9" in source
    assert (WYC_DIR / "LICENSE").read_text().lstrip().startswith("Apache License")
    assert WYC["algorithm"] == "EDDSA" and WYC["numberOfTests"] == 210
    tests = [t for g in WYC["testGroups"] for t in g["tests"]]
    assert len(tests) == 210 and len({t["tcId"] for t in tests}) == 210
    counts = {k: sum(1 for t in tests if t["result"] == k) for k in ("valid", "invalid", "acceptable")}
    assert counts == {"valid": 117, "invalid": 64, "acceptable": 29}
    assert {tuple(t["flags"]) for t in tests if t["result"] == "acceptable"} == {("SmallOrderPublicKey",), ("MixedOrderPublicKey",)}


WYC_CASES = [(t["tcId"], t["result"], tuple(t["flags"]), g["publicKey"]["pk"], t["msg"], t["sig"])
             for g in WYC["testGroups"] for t in g["tests"]]


@needs_backend
@pytest.mark.parametrize("tc,result,flags,pk,msg,sig", WYC_CASES, ids=[f"tc{x[0]}-{x[1]}" for x in WYC_CASES])
def test_wycheproof_vector_through_adapter(verifier, tc, result, flags, pk, msg, sig):
    """valid -> accepted; invalid -> refused; acceptable -> REFUSED by registry policy (stricter than RFC 8032: small-order and
    mixed-order public keys are refused); the refusal is attributable to the key policy, never to the equation alone."""
    got = verifier.verify(ALG, _b(pk), _b(msg), _b(sig))
    if result == "valid":
        assert got is True
    elif result == "invalid":
        assert got is False
    else:
        assert got is False
        assert verifier.acceptable_public_key(_b(pk)) is False
        assert flags[0] in ("SmallOrderPublicKey", "MixedOrderPublicKey")


@pytest.mark.parametrize("tc,result,flags,pk,msg,sig", WYC_CASES, ids=[f"tc{x[0]}" for x in WYC_CASES])
def test_wycheproof_vector_through_policy_oracle(tc, result, flags, pk, msg, sig):
    if result == "valid" and len(msg) > 2000:
        pytest.skip("large message: covered through the adapter")
    got = oracle.policy_verify(_b(pk), _b(msg), _b(sig))
    assert got is (result == "valid")


# ---- cross-implementation comparison (bounded; the full corpus runs when OCS_ED25519_FULL_CORPUS=1) ----------------
def _bounded_corpus():
    rows = []  # (category, pk, msg, sig)
    for name in ("A", "B"):
        seed = VEC["synthetic_keys"][name]["seed_hex"]
        pk = _pub(seed)
        for msg in (b"", b"synthetic message", bytes(range(200))):
            sig = _sign(seed, msg)
            s = int.from_bytes(sig[32:], "little")
            rows.append(("legit", pk, msg, sig))
            rows.append(("malleable", pk, msg, sig[:32] + (s + L).to_bytes(32, "little")))
            rows.append(("malleable", pk, msg, sig[:32] + (s | 1 << 255).to_bytes(32, "little")))
            rows.append(("wrong_msg", pk, msg + b"x", sig))
            for bit in range(0, 512, 53):
                rows.append(("bitflip", pk, msg, _flip(sig, bit)))
            rows.append(("A_sign_flip", _flip(pk, 255), msg, sig))
            rows.append(("R_sign_flip", pk, msg, _flip(sig, 255)))
            for e in NONCANONICAL[:6]:
                rows.append(("R_alias", pk, msg, e + sig[32:]))
                rows.append(("A_alias", e, msg, sig))
    for group, cat in (("small_order_key_equation_rows", "smallA_equation"), ("small_order_key_rb_rows", "smallA_equation"),
                       ("keyholder_r_identity_rows", "keyholder_R_identity"),
                       ("mixed_order_key_rows", "mixed_order_key")):
        rows += [(cat, _b(pk), _b(msg), _b(sig)) for pk, msg, sig, _ in _rows(group)]
    return rows


@needs_backend
def test_cross_implementation_comparison_bounded(verifier):
    """adapter vs libsodium (raw) vs policy oracle (vs raw cryptography when installed).
    Invariants: the adapter equals the executable policy on every row; it never accepts a row libsodium refuses; where the raw
    cryptography backend accepts and the adapter refuses, the row belongs to a degenerate-key/R category."""
    degenerate = {"smallA_equation", "keyholder_R_identity", "mixed_order_key", "A_alias", "R_alias"}
    rows = _bounded_corpus()
    assert len(rows) > 300
    for cat, pk, msg, sig in rows:
        adapter = verifier.verify(ALG, pk, msg, sig)
        assert adapter is oracle.policy_verify(pk, msg, sig), (cat, pk.hex(), sig.hex())
        if adapter:
            assert _sodium_accepts(pk, msg, sig), (cat, pk.hex())
            assert cat == "legit"
        if HAVE_CRYPTOGRAPHY and _cryptography_accepts(pk, msg, sig) and not adapter:
            assert cat in degenerate, (cat, pk.hex())
    for cat in ("smallA_equation", "keyholder_R_identity", "mixed_order_key"):
        assert not any(verifier.verify(ALG, pk, msg, sig) for k, pk, msg, sig in rows if k == cat)


@pytest.mark.skipif(not os.environ.get("OCS_ED25519_FULL_CORPUS"), reason="slow: set OCS_ED25519_FULL_CORPUS=1")
def test_full_corpus_regenerates_stored_security_vectors():
    sys.path.insert(0, str(VECDIR))
    import generate_ed25519_security_vectors as gen
    assert json.loads(json.dumps(gen.build())) == SEC


# ---- mutation checks of the vector set: every policy check has a vector that notices its absence ---------------
def _kill_rows():
    rows = [(pk, msg, sig) for pk, msg, sig, _ in _rows("small_order_key_equation_rows") + _rows("small_order_key_rb_rows")
            + _rows("keyholder_r_identity_rows") + _rows("mixed_order_key_rows")]
    seed = VEC["synthetic_keys"]["A"]["seed_hex"]
    pk, sig = _pub(seed), _sign(seed, b"m")
    s = int.from_bytes(sig[32:], "little")
    rows.append((pk.hex(), b"m".hex(), (sig[:32] + (s + L).to_bytes(32, "little")).hex()))
    return [(_b(a), _b(b), _b(c_)) for a, b, c_ in rows]


MUTANTS = {  # dropped check(s) -> whether the vector set must catch the omission
    ("A_small_order",): True,  # needed for the identity key (the identity lies in the prime-order subgroup)
    ("A_subgroup",): True,
    ("R_small_order",): True,
    ("S_canonical",): True,
    ("A_canonical", "A_small_order"): True,
    ("R_canonical", "R_small_order"): True,
    # Provably equivalent single omissions (see test_noncanonical_encoding_set_is_exhaustive...): every non-canonical alias is
    # undecodable, small-order or mixed-order, so the small-order/subgroup checks (A) and small-order check plus the equation (R)
    # refuse it anyway. Documented, not a gap: nothing can distinguish these mutants.
    ("A_canonical",): False,
    ("R_canonical",): False,
}


@needs_backend
@pytest.mark.parametrize("drop", list(MUTANTS), ids=lambda d: "drop-" + "+".join(d))
def test_vector_set_kills_policy_mutants(verifier, drop):
    rows = _kill_rows()
    assert all(oracle.policy_verify(*row) is False for row in rows[:6] + rows[-12:])  # the full policy refuses (spot check)
    verifier._is_valid_point = lambda pk: True  # mutant: all checks come from the weakened executable policy below

    def weak_open(signed, pk):
        if not oracle.policy_verify(pk, signed[64:], signed[:64], drop=drop):
            raise ValueError("refused")

    verifier._sign_open = weak_open
    caught = [row for row in rows if not verifier.verify(ALG, *row)]
    accepted = len(rows) - len(caught)
    if MUTANTS[drop]:
        assert accepted > 0, f"vector set does not notice dropping {drop}"
    else:
        assert accepted == 0


# ---- end-to-end through the core with a real signature -------------------------------------------------------
Sel = namedtuple("Sel", "ok code detail envelope statement statement_digest signatures")
CTX = c.ExpectedContext("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
GRANT = v.AuthorityGrant("consumer-test", "tenant-a", "inst-a", "domain-a", "op-test")
NOW = r.NOW


def _trust(pub):
    return v.TrustSnapshot("snapshot-1", 1, "2026-10-27T00:00:00Z",
                           (v.IssuerEntry("key-test-1", "issuer-test-1", "ed25519", pub, (GRANT,)),))


def _signed_envelope(seed, statement=None, prefix=None):
    from registry_successor.selection import signing_input
    statement = statement or r.make_statement()
    message = signing_input(statement) if prefix is None else prefix + c.canonical_bytes(statement)
    sig = base64.b64encode(_sign(seed, message)).decode("ascii")
    return {"statement": statement, "statement_digest": c.digest(statement),
            "signatures": [{"alg": "ed25519", "key_id": "key-test-1", "signature": sig}]}


def _run_core(env, verifier, pub=b"p" * 32):
    sel = Sel(True, None, "", env, env["statement"], env["statement_digest"], env["signatures"])
    return v.verify_selection(sel, CTX, _trust(pub), verifier, NOW)


@needs_backend
def test_core_authenticates_real_signature(verifier, key_a):
    seed, pub = key_a
    rep = _run_core(_signed_envelope(seed), verifier, pub)
    assert rep.ok is True and rep.authenticated is True and rep.operationally_authorized is False
    assert rep.layers["authenticity"] == "pass"


@needs_backend
def test_core_refuses_wrong_key_tampered_statement_and_foreign_domain(verifier, key_a, key_b):
    seed, pub = key_a
    env = _signed_envelope(seed)
    assert _run_core(env, verifier, key_b).code == "signature_invalid"
    tampered = dict(env, statement=r.make_statement(epoch=2))
    tampered["statement_digest"] = c.digest(tampered["statement"])
    assert _run_core(tampered, verifier, pub).code == "signature_invalid"
    v2_signed = _signed_envelope(seed, prefix=V2)  # a v2-domain signature must not authenticate a v1 selection
    assert _run_core(v2_signed, verifier, pub).code == "signature_invalid"
    assert _run_core(_signed_envelope(seed, prefix=V1), verifier, pub).ok is True


@needs_backend
def test_core_refuses_identity_key_trust_entry_with_the_identity_forgery(verifier):
    env = _signed_envelope(VEC["synthetic_keys"]["A"]["seed_hex"])
    env["signatures"][0]["signature"] = base64.b64encode(IDENTITY_FORGERY_SIGNATURE).decode("ascii")
    rep = _run_core(env, verifier, IDENTITY)
    assert rep.ok is False and rep.code == "signature_invalid" and rep.authenticated is False


# ---- hash locks, pinned versions, independence ---------------------------------------------------------------
def _lock_names(name):
    text = (ROOT / name).read_text().replace("\\\n", " ")
    reqs = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    assert reqs
    pins = {}
    for ln in reqs:
        assert re.match(r"^[A-Za-z0-9_.\-]+==[0-9][^\s;]*(\s*;[^-]*)?(\s+--hash=sha256:[0-9a-f]{64})+\s*$", ln), ln
        pins[ln.split("==")[0].lower()] = ln.split("==")[1].split()[0]
    assert not [ln for ln in reqs if "--hash=" not in ln]
    return pins


def test_every_pinned_runtime_requirement_has_hashes_and_the_runtime_lock_has_no_cryptography():
    pins = _lock_names("requirements-ed25519.lock.txt")
    assert set(pins) == {"pynacl", "cffi", "pycparser"} and pins["pynacl"] == "1.6.2"


def test_test_only_oracle_lock_has_hashes_and_is_not_the_runtime_lock():
    pins = _lock_names("requirements-ed25519-test-oracle.lock.txt")
    assert set(pins) == {"cryptography", "cffi", "pycparser"} and pins["cryptography"] == "50.0.1"
    assert "TEST-ONLY" in (ROOT / "requirements-ed25519-test-oracle.lock.txt").read_text().splitlines()[0]


@needs_backend
def test_installed_pynacl_matches_the_lock():
    assert importlib.metadata.version("PyNaCl") == _lock_names("requirements-ed25519.lock.txt")["pynacl"]


@needs_cryptography
def test_installed_cryptography_matches_the_test_only_lock():
    assert importlib.metadata.version("cryptography") == _lock_names("requirements-ed25519-test-oracle.lock.txt")["cryptography"]


def test_workflow_installs_both_locks_with_hash_checking_in_the_single_ed25519_step():
    text = (ROOT / ".github" / "workflows" / "registry-tests.yml").read_text()
    step = text.split("- name: Install hash-locked Ed25519")[1].split("\n      - name:")[0]
    assert "--require-hashes -r requirements-ed25519.lock.txt" in step
    assert "--require-hashes -r requirements-ed25519-test-oracle.lock.txt" in step
    assert text.count("Install hash-locked Ed25519") == 1 and "permissions:\n  contents: read" in text


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


def test_adapter_does_not_import_the_core_other_registry_packages_cryptography_or_the_oracle():
    for path in (ROOT / "registry_adapters").glob("*.py"):
        bad = _imports(path) & {"registry_successor", "registry_contract", "registry_consumer", "baseline", "engine", "<relative>",
                                "cryptography", "ed25519_oracle", "tests"}
        assert not bad, (path.name, bad)


def test_adapter_contains_no_curve_or_field_arithmetic():
    tree = ast.parse((ROOT / "registry_adapters" / "ed25519_verifier.py").read_text())
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "pow"]
    defined = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert not defined & {"_decode_point", "_add", "_small_order", "_acceptable"}
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Name) and n.id in {"_P", "_D", "_I"}]


def test_core_does_not_import_the_adapter_or_the_backend():
    for path in (ROOT / "registry_successor").glob("*.py"):
        assert "registry_adapters" not in _imports(path) and not _imports(path) & {"cryptography", "nacl"}, path.name
        assert "registry_adapters" not in path.read_text(), path.name
    probe = ("import sys; sys.path.insert(0, sys.argv[1]); import registry_successor.verify, registry_successor.selection; "
             "bad=[m for m in sys.modules if m.split('.')[0] in ('cryptography','nacl','registry_adapters')]; "
             "assert not bad, bad")
    done = subprocess.run([sys.executable, "-c", probe, str(ROOT)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
