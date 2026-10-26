"""Canonical standard-base64 decoding for signature text (SECURITY-HELD, AI-reviewed only).

Contract section 3 says `signature` is "standard base64 text". Python's `b64decode(..., validate=True)` accepts many
distinct strings that decode to the same bytes: for a 64-byte signature the final character carries four unused low
bits, so 16 spellings decode identically. A signed-envelope representation that is meant to be unique must refuse the
other 15. Canonical form here is exactly RFC 4648 section 4: alphabet A-Z a-z 0-9 + /, `=` padding present, no
whitespace or line breaks, unused trailing bits zero. It is checked by decoding and re-encoding, so there is no
separate grammar to drift.

This module is pure standard library. It decides spelling only. It does not check length or verify anything.
"""
import base64
import binascii
from typing import Optional

__all__ = ["decode_canonical_base64"]


def decode_canonical_base64(text) -> Optional[bytes]:
    """Return the decoded bytes when `text` is exactly the canonical spelling of them, else None. Never raises."""
    if type(text) is not str:
        return None
    try:
        raw = base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError):
        return None
    if base64.b64encode(raw).decode("ascii") != text:
        return None
    return raw
