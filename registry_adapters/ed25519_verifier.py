"""Ed25519 `SignatureVerifier` adapter (EXT-S1-7). Lives outside the registry core; the core never imports it.

Implements the protocol `verify(alg, public_key, message, signature) -> bool` of `registry_successor.verify`.
Fail closed: it returns True only for a valid signature from an acceptable key and False for everything else,
including malformed input and any backend error. It holds no key, no trust root and no policy; any signing domain
prefix (the core's r08-v1 selection signing input starts `ocs-reg/r08-v1/selection\\n`) is part of the `message` the caller supplies and is not added or removed here.

Verifier: PyNaCl (libsodium), the only runtime dependency. This module contains NO curve arithmetic, NO point
decompression and NO byte-level re-implementation of any check: every cryptographic decision is made by libsodium.

Verification policy (named in docs/adapters/ed25519.md), as enforced by exactly two libsodium calls:
  1. `crypto_core_ed25519_is_valid_point(public_key)`: canonical encoding (y < p), decodable, on the curve, not
     small-order (this includes the identity), and in the prime-order subgroup. A public key that is not valid refuses.
  2. `crypto_sign_open(signature || message, public_key)` (libsodium `crypto_sign_verify_detached`): S < L,
     R of small order (including the identity) refused, and the cofactorless equation checked by comparing the
     canonical re-encoding of [S]B - [h]A with the R bytes (so a non-canonical R can never match).
Both facts about libsodium were verified by test against the pinned version (tests/test_adapter_ed25519.py), not assumed;
as a second guard `Ed25519Verifier()` runs a small known-answer self-test and refuses to construct (raises
`Ed25519Unavailable`) if the loaded backend does not show these semantics.
Synthetic keys only; nothing here is an operational trust root (GAP-G3-07 is not closed).
"""
from typing import Optional

__all__ = ["Ed25519Unavailable", "Ed25519Verifier", "load_verifier_or_none", "ALG"]

ALG = "ed25519"

# Known-answer self-test data (public, synthetic; regenerated and cross-checked against an independent oracle by the tests).
_KAT_PK = bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")  # RFC 8032 section 7.1 TEST 1
_KAT_SIG = bytes.fromhex("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
_KAT_L = 2 ** 252 + 27742317777372353535851937790883648493
_KAT_SIG_S_PLUS_L = _KAT_SIG[:32] + (int.from_bytes(_KAT_SIG[32:], "little") + _KAT_L).to_bytes(32, "little")
_KAT_IDENTITY = bytes([1]) + bytes(31)
_KAT_KEYHOLDER_R_IDENTITY = (  # valid cofactorless equation, honest key, R = identity: libsodium must refuse (small-order R)
    bytes.fromhex("77c79cec2531b518dda1fa1e91d159fcd080286eb4859ec3ccbae1cf042abb13"), b"ocs-ed25519-kat/r-identity",
    bytes.fromhex("01000000000000000000000000000000000000000000000000000000000000009541ba746d17310ec7963522bac5c30565e96856a1694c5870130d710d03f70c"))
_KAT_MIXED_ORDER = (  # libsodium's signature check alone ACCEPTS this; the public-key check must refuse (torsion component)
    bytes.fromhex("f057f97f0c3a16026415c2cc59a582ea9b3865730611e410270aafac6dcdc92f"), b"ocs-ed25519-kat/mixed-order/0",
    bytes.fromhex("0e9ec3aa5c0cfedb9db06594a9ad933ffc16a912708de73646e8ed6411ff7393b00b1ecaf05a231db443e83110699483b6df81c2c4a3b44767a0ff5db0bbbb08"))


class Ed25519Unavailable(RuntimeError):
    """The pinned Ed25519 backend (PyNaCl/libsodium) cannot be used. Explicit; never a silent pass."""


def _load_backend():
    try:
        import nacl.bindings as bindings
        if not bindings.has_crypto_core_ed25519:  # libsodium built without the ed25519 point API
            raise ImportError("libsodium ed25519 core API not available")
        return bindings.crypto_core_ed25519_is_valid_point, bindings.crypto_sign_open
    except Exception as exc:  # ImportError, AttributeError or a broken native module: all mean unavailable
        raise Ed25519Unavailable("the 'pynacl' package is not usable; install requirements-ed25519.lock.txt") from exc


class Ed25519Verifier:
    """Construct once; raises `Ed25519Unavailable` if the backend is absent or fails its self-test. `verify` never raises."""

    def __init__(self) -> None:
        self._is_valid_point, self._sign_open = _load_backend()
        if not self._self_test():
            raise Ed25519Unavailable("the Ed25519 backend failed its known-answer self-test; refusing to verify")

    def acceptable_public_key(self, public_key: bytes) -> bool:
        """True only for a public key that passes the key policy of rule 1 (exactly the check `verify` applies). Never raises."""
        try:
            return type(public_key) is bytes and len(public_key) == 32 and bool(self._is_valid_point(public_key))
        except Exception:
            return False

    def _check(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        if not self._is_valid_point(public_key):  # library: canonical, on-curve, non-small-order, prime-order subgroup
            return False
        self._sign_open(signature + message, public_key)  # library: raises on any failure (S >= L, small-order R, equation)
        return True

    def _self_test(self) -> bool:
        r_pk, r_msg, r_sig = _KAT_KEYHOLDER_R_IDENTITY
        m_pk, m_msg, m_sig = _KAT_MIXED_ORDER
        refused = ((_KAT_PK, b"", _KAT_SIG_S_PLUS_L), (_KAT_IDENTITY, b"any message", _KAT_IDENTITY + bytes(32)),
                   (r_pk, r_msg, r_sig), (m_pk, m_msg, m_sig))
        try:
            return self._accepts(_KAT_PK, b"", _KAT_SIG) and not any(self._accepts(*case) for case in refused)
        except Exception:
            return False

    def _accepts(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            return self._check(public_key, message, signature) is True
        except Exception:  # BadSignatureError, ValueError, backend faults: all fail closed
            return False

    def verify(self, alg: str, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            if type(alg) is not str or alg != ALG:
                return False
            if not all(type(x) is bytes for x in (public_key, message, signature)):
                return False
            if len(public_key) != 32 or len(signature) != 64:
                return False
            return self._accepts(public_key, message, signature)
        except Exception:
            return False


def load_verifier_or_none() -> Optional[Ed25519Verifier]:
    """Convenience for callers: the verifier, or None when the backend is absent or fails its self-test.

    Passing None to the core makes the authenticity layer refuse `verifier_unavailable`; the core never treats an
    absent verifier as a pass.
    """
    try:
        return Ed25519Verifier()
    except Ed25519Unavailable:
        return None
