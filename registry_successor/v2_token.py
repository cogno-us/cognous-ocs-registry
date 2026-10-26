"""EXT-S1-5 / FU-1: the frozen Unicode 15.1.0 token predicate for r08-v2 (spec 6.1, ruling N-13), shared by the identity module and the r08-v2 family modules.

A token is valid iff it is an exact `str` of 1..128 code points, contains no `*`, and no code point lies inside an excluded range of the sha256-pinned table
embedded in `v2_token_table`. No runtime Unicode database, no file I/O, no network. The pin is checked at the FIRST evaluation (not at import), fails closed with
RuntimeError, and the failed check is not cached. `common.valid_token` (r08-v1) is NOT changed and NOT used here.
"""
import hashlib
import re
from typing import Any, Tuple

from registry_successor import common as c

TOKEN_TABLE_SHA256 = "8c85813d25f6ed53371e27f0e4895a89de44a619824486dcff8d48ff8b607474"  # pinned in the spec and the vectors (pins.token_unicode_table)
_TOKEN_TABLE: Any = None  # lazily set once (a tuple of two lists); never reset
_RANGE_RE = re.compile(rb'\[\s*"([0-9A-F]{4,6})",\s*"([0-9A-F]{4,6})"\s*\]')


def _load_token_table(raw: Any = None, expected: str = TOKEN_TABLE_SHA256) -> Tuple[list, list]:
    """Verify the sha256 of the embedded table bytes BEFORE parsing and fail closed: a mismatched or malformed table raises RuntimeError (a build defect, never a
    typed refusal and never an accepting default). No file is opened and no host Unicode database is read."""
    try:
        if raw is None:
            from .v2_token_table import TABLE_BYTES as raw
        if type(raw) is not bytes or hashlib.sha256(raw).hexdigest() != expected or b'"unicode_version": "15.1.0"' not in raw:
            raise ValueError("pin")
        head, _, tail = raw.partition(b'"excluded_ranges"')
        ranges = [(int(x, 16), int(y, 16)) for x, y in _RANGE_RE.findall(tail)]
        if not ranges or any(a > b or (i and a <= ranges[i - 1][1]) for i, (a, b) in enumerate(ranges)) or ranges[-1][1] > 0x10FFFF:
            raise ValueError("ranges")
    except Exception:
        raise RuntimeError("the pinned Unicode 15.1.0 token table does not match its sha256 pin or is malformed") from None
    return [a for a, _ in ranges], ranges


def frozen_token_valid(value: Any) -> bool:
    """The token rule with frozen membership: an exact `str` of 1..128 code points, no `*`, no code point inside an excluded range of the pinned table.
    No normalization. Consults no runtime Unicode database."""
    global _TOKEN_TABLE
    if type(value) is not str or not 1 <= len(value) <= c.MAX_ENTRY_CHARS or "*" in value:
        return False
    if _TOKEN_TABLE is None:
        _TOKEN_TABLE = _load_token_table()
    starts, ranges = _TOKEN_TABLE
    for ch in value:
        cp = ord(ch)
        lo, hi = 0, len(starts)  # binary search: the last range whose start is <= cp
        while lo < hi:
            mid = (lo + hi) // 2
            if starts[mid] <= cp:
                lo = mid + 1
            else:
                hi = mid
        i = lo - 1
        if i >= 0 and ranges[i][0] <= cp <= ranges[i][1]:
            return False
    return True
