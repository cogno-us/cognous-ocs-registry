"""TEST ORACLE ONLY - never imported by registry_adapters (a test asserts this). Not production code, not reviewed as such.

A transcription of the RFC 8032 section 5.1 arithmetic in plain Python, used by tests/test_adapter_ed25519.py to
  * derive synthetic public keys and signatures independently of the verifier library under test,
  * express the registry verification policy as an executable specification (`policy_verify`),
  * build deliberately weakened verifiers (`policy_verify(..., drop=...)`) to prove the test vectors catch the omission
    of each individual check (a mutation check of the vector set itself).
Slow by design (big-int affine/extended arithmetic); the tests use it on bounded corpora.
"""
from hashlib import sha512

p = 2 ** 255 - 19
L = 2 ** 252 + 27742317777372353535851937790883648493
d = -121665 * pow(121666, p - 2, p) % p
_SQRT_M1 = pow(2, (p - 1) // 4, p)
ZERO = (0, 1, 1, 0)

CHECKS = ("A_canonical", "A_small_order", "A_subgroup", "R_canonical", "R_small_order", "S_canonical")


def add(P, Q):
    A = (P[1] - P[0]) * (Q[1] - Q[0]) % p
    B = (P[1] + P[0]) * (Q[1] + Q[0]) % p
    C = 2 * P[3] * Q[3] * d % p
    D = 2 * P[2] * Q[2] % p
    E, F, G, H = B - A, D - C, D + C, B + A
    return (E * F % p, G * H % p, F * G % p, E * H % p)


def mul(s, P):
    Q = ZERO
    while s > 0:
        if s & 1:
            Q = add(Q, P)
        P = add(P, P)
        s >>= 1
    return Q


def eq(P, Q):
    return (P[0] * Q[2] - Q[0] * P[2]) % p == 0 and (P[1] * Q[2] - Q[1] * P[2]) % p == 0


def _recover_x(y, sign):
    x2 = (y * y - 1) * pow(d * y * y + 1, p - 2, p) % p
    if x2 == 0:
        return None if sign else 0
    x = pow(x2, (p + 3) // 8, p)
    if (x * x - x2) % p:
        x = x * _SQRT_M1 % p
    if (x * x - x2) % p:
        return None
    return p - x if (x & 1) != sign else x


def decompress(s, lax=False):
    """Strict RFC 8032 5.1.3 decoding (y < p, x = 0 with sign bit 1 fails). lax=True reduces y mod p and ignores a
    sign bit on x = 0 (the behaviour of some OpenSSL-based verifiers); used only to build weakened verifiers."""
    if len(s) != 32:
        return None
    y = int.from_bytes(s, "little")
    sign, y = y >> 255, y & ((1 << 255) - 1)
    if y >= p:
        if not lax:
            return None
        y -= p
    x = _recover_x(y, sign)
    if x is None and lax:
        x = _recover_x(y, 0) if sign and (y * y - 1) % p == 0 else None
    return None if x is None else (x, y, 1, x * y % p)


def compress(P):
    zi = pow(P[2], p - 2, p)
    x, y = P[0] * zi % p, P[1] * zi % p
    return int.to_bytes(y | ((x & 1) << 255), 32, "little")


_Gy = 4 * pow(5, p - 2, p) % p
_Gx = _recover_x(_Gy, 0)
G = (_Gx, _Gy, 1, _Gx * _Gy % p)


def _h(*a):
    return int.from_bytes(sha512(b"".join(a)).digest(), "little") % L


def secret_expand(seed):
    h = sha512(seed).digest()
    a = int.from_bytes(h[:32], "little") & ((1 << 254) - 8) | (1 << 254)
    return a, h[32:]


def pubkey(seed):
    return compress(mul(secret_expand(seed)[0], G))


def sign(seed, msg):
    a, prefix = secret_expand(seed)
    A = compress(mul(a, G))
    r = _h(prefix, msg)
    R = compress(mul(r, G))
    return R + int.to_bytes((r + _h(R, A, msg) * a) % L, 32, "little")


def is_small_order(P):
    return eq(mul(8, P), ZERO)


def in_prime_order_subgroup(P):
    return eq(mul(L, P), ZERO)


def key_acceptable(pub, drop=()):
    """The registry public-key policy: canonical encoding, on the curve, not small-order (identity included), prime-order subgroup."""
    A = decompress(pub, lax="A_canonical" in drop)
    if A is None:
        return False
    if "A_small_order" not in drop and is_small_order(A):
        return False
    if "A_subgroup" not in drop and not in_prime_order_subgroup(A):
        return False
    return True


def policy_verify(pub, msg, sig, drop=()):
    """Executable specification of the registry policy (cofactorless equation). `drop` removes individual checks (CHECKS)."""
    if len(pub) != 32 or len(sig) != 64 or not key_acceptable(pub, drop):
        return False
    R = decompress(sig[:32], lax="R_canonical" in drop)
    if R is None or ("R_small_order" not in drop and is_small_order(R)):
        return False
    S = int.from_bytes(sig[32:], "little")
    if "S_canonical" not in drop and S >= L:
        return False
    A = decompress(pub, lax="A_canonical" in drop)
    h = _h(sig[:32], pub, msg)
    return eq(mul(S % L if "S_canonical" in drop else S, G), add(R, mul(h, A)))


def raw_equation(pub, msg, sig):
    """Cofactorless equation only, lax decoding, no policy: what a verifier with no key/R/S checks accepts."""
    return policy_verify(pub, msg, sig, drop=CHECKS)


def cofactored_equation(pub, msg, sig):
    """RFC 8032 cofactored equation [8][S]B = [8]R + [8][h]A with strict decoding and S < L, no key/R policy (reference only)."""
    A, R = decompress(pub), decompress(sig[:32])
    S = int.from_bytes(sig[32:], "little")
    if A is None or R is None or S >= L:
        return False
    return eq(mul(8, mul(S, G)), mul(8, add(R, mul(_h(sig[:32], pub, msg), A))))
