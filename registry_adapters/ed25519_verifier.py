"""Ed25519 `SignatureVerifier` adapter (EXT-S1-7). Lives outside the registry core; the core never imports it.

Implements the protocol `verify(alg, public_key, message, signature) -> bool` of `registry_successor.verify`.
Fail closed: it returns True only for a valid signature from an acceptable key and False for everything else,
including malformed input and any backend error. It holds no key, no trust root and no policy; the signing domain
(`ocs-reg/r08-v*/selection\\n`) is part of the `message` the caller supplies and is not added or removed here.

Strictness beyond RFC 8032 section 5.1.7 (which only requires the cofactor-less or cofactored equation): the adapter
refuses S >= L (non-canonical S), a public key or R that is not a canonical point encoding (y >= p), and a public key
of small order (including the identity), which would otherwise let a degenerate key verify arbitrary messages.
Synthetic keys only; nothing here is an operational trust root (GAP-G3-07 is not closed).
"""
from typing import Optional

__all__ = ["Ed25519Unavailable", "Ed25519Verifier", "load_verifier_or_none", "ALG"]

ALG = "ed25519"
_P = 2 ** 255 - 19
_L = 2 ** 252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)


class Ed25519Unavailable(RuntimeError):
    """The pinned Ed25519 backend (`cryptography`) cannot be imported. Explicit; never a silent pass."""


def _load_backend():
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except Exception as exc:  # ImportError or a broken native module: both mean unavailable
        raise Ed25519Unavailable("the 'cryptography' package is not available; install requirements-ed25519.lock.txt") from exc
    return Ed25519PublicKey, InvalidSignature


def _decode_point(enc: bytes) -> Optional[tuple]:
    """Canonical decode of a 32-byte Edwards point (extended-free affine); None if not canonical or not on the curve."""
    y = int.from_bytes(enc, "little")
    sign = y >> 255
    y &= (1 << 255) - 1
    if y >= _P:
        return None
    u, v = (y * y - 1) % _P, (_D * y * y + 1) % _P
    x2 = u * pow(v, _P - 2, _P) % _P
    x = pow(x2, (_P + 3) // 8, _P)
    if (x * x - x2) % _P:
        x = x * _I % _P
    if (x * x - x2) % _P:
        return None
    if x == 0 and sign:
        return None
    if x & 1 != sign:
        x = _P - x
    return (x, y)


def _add(a: tuple, b: tuple) -> tuple:
    (x1, y1), (x2, y2) = a, b
    t = _D * x1 * x2 * y1 * y2 % _P
    return ((x1 * y2 + x2 * y1) * pow(1 + t, _P - 2, _P) % _P, (y1 * y2 + x1 * x2) * pow(1 - t, _P - 2, _P) % _P)


def _small_order(point: tuple) -> bool:
    """True if 8*P is the identity, i.e. the order of P divides 8 (small-order or identity)."""
    for _ in range(3):
        point = _add(point, point)
    return point == (0, 1)


def _acceptable(public_key: bytes, signature: bytes) -> bool:
    point = _decode_point(public_key)
    if point is None or _small_order(point):
        return False
    if int.from_bytes(signature[32:], "little") >= _L:
        return False
    return _decode_point(signature[:32]) is not None


class Ed25519Verifier:
    """Construct once; raises `Ed25519Unavailable` if the backend is absent. `verify` never raises."""

    def __init__(self) -> None:
        self._public_key_cls, self._invalid = _load_backend()

    def verify(self, alg: str, public_key: bytes, message: bytes, signature: bytes) -> bool:
        try:
            if type(alg) is not str or alg != ALG:
                return False
            if not all(type(x) is bytes for x in (public_key, message, signature)):
                return False
            if len(public_key) != 32 or len(signature) != 64:
                return False
            if not _acceptable(public_key, signature):
                return False
            self._public_key_cls.from_public_bytes(public_key).verify(signature, message)
            return True
        except Exception:  # InvalidSignature, ValueError, backend faults: all fail closed
            return False


def load_verifier_or_none() -> Optional[Ed25519Verifier]:
    """Convenience for callers: the verifier, or None when the backend is absent.

    Passing None to the core makes the authenticity layer refuse `verifier_unavailable`; the core never treats an
    absent verifier as a pass.
    """
    try:
        return Ed25519Verifier()
    except Ed25519Unavailable:
        return None
