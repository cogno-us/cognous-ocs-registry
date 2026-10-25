"""F1a/F1b five-set family `f1ab-local-execution-allowlist` for contract `r08-v2` (docs/r08-v2-contract.md section 2; ADR
EXT-S1-1 D-10, D-11; card EXT-S1-3).

Payload: EXACTLY `allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`, `allowed_authority_domains`.
No other key (no amount key, no age key): a sixth key refuses `field_unknown`, an absent key `field_missing` (an absent list is
never an implicit allow or deny). An empty list is a valid explicit deny-all for that dimension.

List entries: plain `str`, sorted, duplicate-free, at most MAX_ENTRIES, each valid under `common.valid_token` (1..128, no
control, separator or `*`). Matching is exact-string: no case folding, trimming, normalization or wildcard. `allowed_institutions`
and `allowed_authority_domains` entries are values of the v2 scope identifiers, so they must also match the V1 ASCII identifier
grammar `\\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\\Z` on the raw string (non-ASCII refused, never normalized).

Composition: effective = caller INTERSECTION registry per key (subset of both, never widening). Any empty effective set is
reported as deny-all; the composer never constructs a Runtime policy and every refusal carries no effective policy, so no
refusal can return the caller policy.

Pure and non-authorizing; unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v2` table (`families.FAMILIES_V2`), never
in the `r08-v1` table: a v1 entry point still refuses this family `family_unsupported` (golden-replay proved).
"""
import re
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult

FAMILY_F1AB = "f1ab-local-execution-allowlist"
F1AB_FIELDS = ("allowed_actions", "allowed_adapters", "allowed_units", "allowed_institutions", "allowed_authority_domains")
# Dimensions whose entries are values of ASCII-grammar scope identifiers.
ASCII_GRAMMAR_FIELDS = ("allowed_institutions", "allowed_authority_domains")

_V1_ASCII_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


def valid_ascii_identifier(value: Any) -> bool:
    """V1 ASCII grammar on the raw string: no normalization, no case folding, no trimming."""
    return type(value) is str and _V1_ASCII_IDENTIFIER.match(value) is not None


def _entry_ok(field: str, item: Any) -> bool:
    if type(item) is not str or not c.valid_token(item):
        return False
    return valid_ascii_identifier(item) if field in ASCII_GRAMMAR_FIELDS else True


def _list_ok(field: str, value: Any) -> bool:
    """Plain list, sorted, duplicate-free, bounded; empty is the explicit deny-all."""
    if type(value) is not list or len(value) > c.MAX_ENTRIES:
        return False
    if not value:
        return True
    return all(_entry_ok(field, item) for item in value) and value == sorted(set(value))


def payload_validator(payload: dict) -> Optional[str]:
    """None when valid, else the shape code in the v1 order: `field_type_invalid` before `field_invalid`. The caller (record
    parse) has already enforced the exact key set; this refuses a wrong key set too, so it is safe to call alone."""
    if not isinstance(payload, Mapping) or set(payload) != set(F1AB_FIELDS):
        return "field_unknown" if isinstance(payload, Mapping) and set(payload) - set(F1AB_FIELDS) else (
            "field_missing" if isinstance(payload, Mapping) else "field_type_invalid")
    if not all(type(payload[k]) is list for k in F1AB_FIELDS):
        return "field_type_invalid"
    if not all(_list_ok(k, payload[k]) for k in F1AB_FIELDS):
        return "field_invalid"
    return None


def normalize_caller(caller: Any) -> Optional[dict]:
    """Sorted-tuple copy of a well-formed caller policy, or None. Exactly the five keys, each a list/tuple/set/frozenset of
    plain-str valid tokens; empty is allowed (deny-all dimension); a missing, extra or malformed key refuses."""
    if not isinstance(caller, Mapping) or set(caller) != set(F1AB_FIELDS):
        return None
    out = {}
    for field in F1AB_FIELDS:
        value = caller[field]
        if type(value) not in (list, tuple, set, frozenset):
            return None
        if not all(type(item) is str and c.valid_token(item) for item in value):
            return None
        out[field] = tuple(sorted(set(value)))
    return out


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def compose_f1ab(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if getattr(record, "ok", False) is not True:
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if not isinstance(body, Mapping):
            return _refuse("composition_record_invalid")
        if body.get("family") != FAMILY_F1AB:
            return _refuse("composition_family_unsupported")
        payload = body.get("payload")
        if not isinstance(payload, Mapping) or payload_validator(payload) is not None:
            return _refuse("composition_record_invalid")
        normalized = normalize_caller(caller)
        if normalized is None:
            return _refuse("composition_caller_invalid")
        effective = {f: tuple(sorted(set(normalized[f]) & set(payload[f]))) for f in F1AB_FIELDS}
        empty = tuple(f for f in F1AB_FIELDS if not effective[f])
        return CompositionResult(True, None, "", effective, bool(empty), empty)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
