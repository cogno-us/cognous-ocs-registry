"""Two F5 scalar-int families for the Control Plane `ObservationPolicy` for contract `r08-v8` (docs/r08-v8-contract.md).

APPROVED CANDIDATE (Architect-selected successor, D-C5): BUILDER_TESTED, non-authorizing, not independently qualified. Registering these families enables NO consumer; the Control Plane consumers are not implemented, and the
observation values are bound by the Control Plane D-06 effective-configuration binding, NOT by this module.

  `f5-observation-max-age-policy`         member `observation_max_age_seconds`         (host `ObservationPolicy.max_age_seconds`)
  `f5-observation-clock-tolerance-policy` member `observation_clock_tolerance_seconds` (host `ObservationPolicy.clock_tolerance_seconds`)

Member names carry the `observation_` prefix so they can never alias the held constructor tolerance member `clock_tolerance_seconds` or the F4 age members: a record or
caller using `clock_tolerance_seconds` here refuses (`field_unknown` / `field_missing` at the record, `composition_caller_invalid` at the caller).

Values: `type(v) is int` exactly (bool, float, str, None, bytes, Decimal and int subclasses refuse; nothing is coerced or clamped). Domains: max age `1 .. 2147483647`,
tolerance `0 .. 2147483647`. The ceiling 2147483647 is `common.MAX_INT`, the STRUCTURAL Registry token range shared with `v2_age_bounds.AGE_MAX`; it is NOT a Control Plane
or host bound (the host has none). The lower bounds follow the host fields (`gt=0`, `ge=0`). A Registry tolerance of 0 is admitted ("no future allowance", not a deny-all).

Composition (only operator `intersection`): effective = `min(caller, registry)`; a Registry value above the caller yields the caller value, reported in `detail` as
`registry_value_not_narrowing:<member>`; equal values report nothing. A caller outside the domain (including a host value above 2147483647, or None) refuses the WHOLE
caller `composition_caller_invalid`: nothing is narrowed and the host value is never replaced. Every refusal carries no effective policy. `deny_all` is never set.
Lowering max age can add `observation_stale` holds and lowering the tolerance can add `observation_time_future` holds at the consumer; neither can turn a hold into a pass.

Host preconditions (consumer-owned): the host `observation_policy` exists (the Registry never supplies one). The two scalars are independent records and selections.
Pure and non-authorizing; unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v8` profile. Imports no Control Plane module.
"""
import itertools
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult

FAMILY_MAX_AGE = "f5-observation-max-age-policy"
FAMILY_TOLERANCE = "f5-observation-clock-tolerance-policy"
MAX_AGE_FIELD = "observation_max_age_seconds"
TOLERANCE_FIELD = "observation_clock_tolerance_seconds"
MAX_AGE_FIELDS = (MAX_AGE_FIELD,)
TOLERANCE_FIELDS = (TOLERANCE_FIELD,)
SCHEMA_REVISION = 1  # family_schema_revision of both payload schemas; part of each effective-policy preimage
INT_MAX = c.MAX_INT  # 2147483647: structural Registry token range, NOT a Control Plane bound
MAX_AGE_MIN = 1
TOLERANCE_MIN = 0
NOT_NARROWING = "registry_value_not_narrowing"


def is_max_age(v: Any) -> bool:
    return type(v) is int and MAX_AGE_MIN <= v <= INT_MAX


def is_tolerance(v: Any) -> bool:
    return type(v) is int and TOLERANCE_MIN <= v <= INT_MAX


def _payload_code(payload: Any, field: str, ok) -> Optional[str]:
    if type(payload) is not dict or not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - {field}:
        return "field_unknown"
    if {field} - keys:
        return "field_missing"
    if type(payload[field]) is not int:
        return "field_type_invalid"
    return None if ok(payload[field]) else "field_invalid"


def max_age_payload_validator(payload: dict) -> Optional[str]:
    """None when valid, else a shape code (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    return _payload_code(payload, MAX_AGE_FIELD, is_max_age)


def tolerance_payload_validator(payload: dict) -> Optional[str]:
    return _payload_code(payload, TOLERANCE_FIELD, is_tolerance)


def _snapshot(m: Any, limit: int) -> Optional[dict]:
    """One read of at most `limit` entries of a caller mapping into a plain dict, or None (not a Mapping, unreadable, more than `limit` entries or a non-`str` key)."""
    if not isinstance(m, Mapping):
        return None
    try:
        items = list(itertools.islice(m.items(), limit + 1))
        if len(items) > limit or any(type(k) is not str for k, _ in items):
            return None
        return {k: v for k, v in items}
    except Exception:
        return None


def _normalize(caller: Any, field: str, ok) -> Optional[dict]:
    snap = _snapshot(caller, 1)
    if snap is None or set(snap) != {field} or not ok(snap[field]):
        return None
    return {field: snap[field]}


def normalize_caller_max_age(caller: Any) -> Optional[dict]:
    """Copy of a well-formed caller policy, or None: exactly the one key with a strict int in the domain."""
    return _normalize(caller, MAX_AGE_FIELD, is_max_age)


def normalize_caller_tolerance(caller: Any) -> Optional[dict]:
    return _normalize(caller, TOLERANCE_FIELD, is_tolerance)


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _compose(family: str, field: str, validator, normalizer, caller: Any, record: Any, operator: Any) -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if getattr(record, "ok", False) is not True:
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if type(body) is not dict:
            return _refuse("composition_record_invalid")
        family_seen, payload = body.get("family"), body.get("payload")
        if type(family_seen) is not str or family_seen != family:
            return _refuse("composition_family_unsupported")
        if type(payload) is not dict:
            return _refuse("composition_record_invalid")
        snap = dict(payload)
        if validator(snap) is not None:
            return _refuse("composition_record_invalid")
        cal = normalizer(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        reg, base = snap[field], cal[field]
        detail = (NOT_NARROWING + ":" + field) if reg > base else ""
        return CompositionResult(True, None, detail, {field: min(base, reg)}, False, ())
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")


def compose_max_age(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    return _compose(FAMILY_MAX_AGE, MAX_AGE_FIELD, max_age_payload_validator, normalize_caller_max_age, caller, record, operator)


def compose_tolerance(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    return _compose(FAMILY_TOLERANCE, TOLERANCE_FIELD, tolerance_payload_validator, normalize_caller_tolerance, caller, record, operator)
