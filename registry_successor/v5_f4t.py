"""Family `f4t-control-plane-clock-tolerance` for contract `r08-v5` (docs/r08-v5-contract.md; M11 PR-1).

Payload: EXACTLY ONE member, `clock_tolerance_seconds`, the Control Plane `BoundedAuthorizationWorkflow` constructor scalar (default 5, bare unvalidated
`int`, bounded.py:1275/1299) that `_fresh` uses to reject future-dated authority-input observations (`observed > now + tolerance`), that
`record_resolution_check` and the recorded-at check use, and that the local-authority-effect snapshot validation uses. A LARGER tolerance accepts MORE
future-dated reads, so the narrowing direction is SMALLER. The ages `status_max_age_seconds` and `approval_max_age_seconds` are NOT here: they are
already governed by the existing F4 family (`v2_age_bounds`, contract `r08-v2`); this family duplicates nothing and F4's closed two-key payload is untouched.

Domain (exact `int` only; bool, float, str, None, Decimal, bytes and int subclasses refuse; nothing is coerced, clamped or defaulted):
  * Registry value: 0 ..= 2147483647 (the DR-CP-AGE-1 technical representation ceiling, which also bounds the measured date-arithmetic overflow of
    this scalar at about 2.5e11 s). 0 is valid and is the strictest tolerance (no future-dated read is accepted); it is NOT deny-all.
  * Caller value (the host constructor value): the same 0 ..= 2147483647. A host value outside it (negative, huge, non-int) refuses
    `composition_caller_invalid`; it is never replaced.
Composition (only operator `intersection`): `min(caller, registry)`. A Registry value above the caller yields the caller, reported in `detail` as
`registry_value_not_narrowing:clock_tolerance_seconds`. The result never exceeds the caller. `deny_all` is never set. Every refusal carries no policy.

Pure, non-authorizing, unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v5` table. Imports no Control Plane module.
"""
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import v2_age_bounds
from registry_successor.compose import CompositionResult

FAMILY_F4T = "f4t-control-plane-clock-tolerance"
FIELD = "clock_tolerance_seconds"
F4T_FIELDS = (FIELD,)
TOLERANCE_MIN = 0
TOLERANCE_MAX = v2_age_bounds.AGE_MAX
NOT_NARROWING = v2_age_bounds.NOT_NARROWING


def is_tolerance(v: Any) -> bool:
    return type(v) is int and TOLERANCE_MIN <= v <= TOLERANCE_MAX


def payload_validator(payload: Any) -> Optional[str]:
    if type(payload) is not dict or not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(F4T_FIELDS):
        return "field_unknown"
    if set(F4T_FIELDS) - keys:
        return "field_missing"
    if type(payload[FIELD]) is not int:
        return "field_type_invalid"
    return None if is_tolerance(payload[FIELD]) else "field_invalid"


def normalize_caller(caller: Any) -> Optional[dict]:
    snap = v2_age_bounds._snapshot(caller, len(F4T_FIELDS))
    if snap is None or set(snap) != set(F4T_FIELDS) or not is_tolerance(snap[FIELD]):
        return None
    return {FIELD: snap[FIELD]}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any) -> tuple:
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if type(body) is not dict:
        return None, "composition_record_invalid"
    family, payload = body.get("family"), body.get("payload")
    if type(family) is not str or family != FAMILY_F4T:
        return None, "composition_family_unsupported"
    if type(payload) is not dict:
        return None, "composition_record_invalid"
    snap = dict(payload)
    if payload_validator(snap) is not None:
        return None, "composition_record_invalid"
    return snap, None


def compose_f4t(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        effective = {FIELD: min(cal[FIELD], payload[FIELD])}
        detail = (NOT_NARROWING + ":" + FIELD) if payload[FIELD] > cal[FIELD] else ""
        return CompositionResult(True, None, detail, effective, False, ())
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
