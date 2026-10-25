"""Signing-key admission at the trust boundary (SECURITY-HELD, AI-reviewed only).

The core accepts any non-empty `bytes` as an issuer public key; a bad key then fails only later, as a generic
`signature_invalid`. This module lets a caller refuse such keys when the trust snapshot is admitted instead.

What `inspect_ed25519_key` DOES check (pure standard library, no optional dependency):
  * the key is exact `bytes` of length 32;
  * the encoded y coordinate (low 255 bits, little endian) is below p = 2**255 - 19, so every non-canonical y alias
    is refused whether or not it decodes to a point;
  * the y coordinate is not one of the five values shared by the eight small-order points (0, 1, p-1 and the two
    order-8 values), for either sign bit. That refuses all eight canonical small-order encodings, including the
    identity (01 00 .. 00), and the non-canonical x = 0 sign-bit spellings.

What it does NOT check: whether the bytes decode to a point on the curve, and whether that point lies in the
prime-order subgroup. Mixed-order keys and off-curve y values pass this built-in check. Full validation needs a real
curve implementation; the Ed25519 adapter's `acceptable_public_key` (PR #26, not merged) is the stricter check and is
meant to be composed in through `compose_key_admission`. Until a subgroup-validating policy or verifier is in place, mixed-order keys and signatures made with them MAY be
accepted: libsodium's signature check alone has been reported (PR #26) to accept mixed-order cases.

Key admission is opt-in at `verify_selection(..., key_admission=...)`. With the default `None`, behaviour is exactly
the legacy behaviour (existing fixtures use non-32-byte placeholder keys). Production callers must pass a policy.
"""
from typing import Callable, Optional

__all__ = ["P", "SMALL_ORDER_Y", "inspect_ed25519_key", "builtin_key_admission", "compose_key_admission"]

P = 2**255 - 19
SMALL_ORDER_Y = frozenset({
    0,
    1,
    P - 1,
    0x5fc536d880238b13933c6d305acdfd5f098eff289f4c345b027b2c28f95e826,
    0x7a03ac9277fdc74ec6cc392cfa53202a0f67100d760b3cba4fd84d3d706a17c7,
})


def inspect_ed25519_key(public_key) -> Optional[str]:
    """Return None when the built-in checks pass, else a stable cause label. Never raises."""
    if type(public_key) is not bytes:
        return "key_type"
    if len(public_key) != 32:
        return "key_length"
    y = int.from_bytes(public_key, "little") & ((1 << 255) - 1)
    if y >= P:
        return "key_non_canonical_y"
    if y in SMALL_ORDER_Y:
        return "key_small_order"
    return None


def builtin_key_admission(alg, public_key) -> bool:
    """Policy callable: Ed25519 keys must pass `inspect_ed25519_key`. Other algorithms are not judged here."""
    if alg != "ed25519":
        return True
    return inspect_ed25519_key(public_key) is None


def compose_key_admission(*policies: Callable) -> Callable:
    """AND of policies. A policy that raises or returns anything other than exactly True refuses."""
    def admit(alg, public_key) -> bool:
        for policy in policies:
            try:
                if policy(alg, public_key) is not True:
                    return False
            except Exception:
                return False
        return True
    return admit
