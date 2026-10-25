"""F1a typed composition for contract `r08-v1` (docs/r08-s01-contract.md section 5).

effective = caller INTERSECTION registry, per F1a field. An empty intersection is a valid deny-all. Pure, deterministic,
non-widening by construction (the result is a subset of both inputs). The mandatory Runtime invariants are code-owned and
untouched: this module never constructs a `LocalExecutionPolicy`, and consumers must not build one from empty sets.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from registry_successor import common as c


@dataclass(frozen=True)
class CompositionResult:
    ok: bool
    code: Optional[str] = None
    detail: str = ""
    effective: Optional[dict] = None
    deny_all: bool = False
    deny_all_fields: tuple = ()


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def normalize_caller(caller: Any) -> Optional[dict]:
    """Sorted-tuple copy of a well-formed caller policy, or None. Empty sets are allowed (deny-all dimension)."""
    if not isinstance(caller, Mapping) or set(caller) != set(c.F1A_FIELDS):
        return None
    out = {}
    for field in c.F1A_FIELDS:
        value = caller[field]
        if not isinstance(value, (list, tuple, set, frozenset)):
            return None
        if not all(c.valid_token(item) for item in value):
            return None
        out[field] = tuple(sorted(set(value)))
    return out


def _payload(record: Any) -> tuple:
    """(payload dict, None) or (None, refusal code)."""
    if not getattr(record, "ok", False):
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if not isinstance(body, Mapping):
        return None, "composition_record_invalid"
    if body.get("family") != c.FAMILY_F1A:
        return None, "composition_family_unsupported"
    payload = body.get("payload")
    if not isinstance(payload, Mapping) or set(payload) != set(c.F1A_FIELDS):
        return None, "composition_record_invalid"
    for field in c.F1A_FIELDS:
        if not c.valid_entry_list(payload[field], allow_empty=True):
            return None, "composition_record_invalid"
    return payload, None


def compose_f1a(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _payload(record)
        if payload is None:
            return _refuse(code)
        normalized = normalize_caller(caller)
        if normalized is None:
            return _refuse("composition_caller_invalid")
        effective = {f: tuple(sorted(set(normalized[f]) & set(payload[f]))) for f in c.F1A_FIELDS}
        empty = tuple(f for f in c.F1A_FIELDS if not effective[f])
        return CompositionResult(True, None, "", effective, bool(empty), empty)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
