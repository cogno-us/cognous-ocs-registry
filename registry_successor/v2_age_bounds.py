"""F4 and F5 integer-second age-bound families for contract `r08-v2` (docs/r08-v2-contract.md section 2; ADR EXT-S1-1 D-10,
D-11, D-27; DR-CP-AGE-1; card EXT-S1-4).

F4 `f4-control-plane-age-bounds`: payload EXACTLY `status_max_age_seconds`, `approval_max_age_seconds` (workflow scalars).
F5 `f5-action-class-age-bounds`: payload EXACTLY `class_status_max_age_seconds`, an object `action_class -> int seconds`.
No other key (no amount key, no `identity_max_age_seconds`, `mandate_max_age_seconds`, `clock_tolerance_seconds`, no
evidence-obligation age): a third key refuses `field_unknown`, an absent key `field_missing`.

Registry values: `type(v) is int` exactly (bool, float, str, None, bytes, Decimal, int subclasses, lists refuse), with
AGE_MIN <= v <= AGE_MAX. Nothing is ever clamped, coerced or defaulted. No cross-bound among ages (an individually valid
inverted pair is accepted) and no five-second floor (1 is accepted). There is no amount slot, reserved or inactive.

Bounds. AGE_MIN = 1 (ADR D-27). AGE_MAX = 2147483647 is the V1 TECHNICAL REPRESENTATION CEILING recorded by the Architect
ruling of 2026-10-25 and DR-CP-AGE-1 (docs/decisions/2026-10-25-dr-cp-age-1.md); it is not an operational setting. The
constants below are a copy of that record's table; a test fails if the record and these constants differ. Caller domain is
0..AGE_MAX (the Control Plane models admit 0); registry domain is 1..AGE_MAX.

F5 class keys follow the opaque-token rule of contract section 2 (`common.valid_token`: plain `str`, 1..128, no control or
separator character, no `*`; exact string, no case folding). The Control Plane itself constrains a class id only to a non-empty
string, so this rule is stricter and fails closed: a longer or exotic class id cannot be set through the registry. Keys must
appear sorted and are bounded at MAX_ENTRIES (the canonical-list convention); an empty map refuses.

Composition (only operator `intersection`, the frozen dispatch name for narrowing): effective = min(caller, registry) per
scalar and per class. A registry value above the caller yields the caller value (reported in `detail` as
`registry_value_not_narrowing:<names>`); the result never exceeds the caller. A registry class the caller does not define is
unknown and refuses `composition_record_invalid`; a caller class absent from the registry keeps the caller value. An invalid
caller (wrong key set, any value that is not an int in 0..AGE_MAX, empty class map) refuses `composition_caller_invalid` and is
never replaced. Every refusal carries no effective policy, so no refusal can return a default or the caller value. Optional
fallback is NOT implemented here (consumer-owned, EXT-S4-2). `deny_all` is never set: a caller value of 0 stays 0.

Pure and non-authorizing; unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v2` table (`families.FAMILIES_V2`).
Imports no Control Plane module.
"""
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult

FAMILY_F4 = "f4-control-plane-age-bounds"
FAMILY_F5 = "f5-action-class-age-bounds"
F4_FIELDS = ("status_max_age_seconds", "approval_max_age_seconds")
F5_FIELD = "class_status_max_age_seconds"
F5_FIELDS = (F5_FIELD,)

# Copy of the DR-CP-AGE-1 table (Control Plane source head 7a4bcd40b3b49e61ff3c294dcca53b52f460b22c).
AGE_MIN = 1
AGE_MAX = 2147483647
CALLER_MIN = 0
MAX_CLASSES = c.MAX_ENTRIES

NOT_NARROWING = "registry_value_not_narrowing"


def is_registry_age(v: Any) -> bool:
    """Exact int in AGE_MIN..AGE_MAX. `type(v) is int` excludes bool and every int subclass."""
    return type(v) is int and AGE_MIN <= v <= AGE_MAX


def is_caller_age(v: Any) -> bool:
    return type(v) is int and CALLER_MIN <= v <= AGE_MAX


def _key_shape(payload: Any, fields: tuple) -> Optional[str]:
    if not isinstance(payload, Mapping):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(fields):
        return "field_unknown"
    if set(fields) - keys:
        return "field_missing"
    return None


def f4_payload_validator(payload: dict) -> Optional[str]:
    """None when valid, else a shape code (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    code = _key_shape(payload, F4_FIELDS)
    if code:
        return code
    if not all(type(payload[k]) is int for k in F4_FIELDS):
        return "field_type_invalid"
    if not all(is_registry_age(payload[k]) for k in F4_FIELDS):
        return "field_invalid"
    return None


def f5_payload_validator(payload: dict) -> Optional[str]:
    code = _key_shape(payload, F5_FIELDS)
    if code:
        return code
    m = payload[F5_FIELD]
    if type(m) is not dict:
        return "field_type_invalid"
    if not all(type(k) is str for k in m) or not all(type(v) is int for v in m.values()):
        return "field_type_invalid"
    if not m or len(m) > MAX_CLASSES:
        return "field_invalid"
    keys = list(m)
    if not all(c.valid_token(k) for k in keys) or keys != sorted(keys):
        return "field_invalid"
    if not all(is_registry_age(v) for v in m.values()):
        return "field_invalid"
    return None


def normalize_caller_f4(caller: Any) -> Optional[dict]:
    """Copy of a well-formed F4 caller policy, or None. Exactly the two keys, each an exact int in 0..AGE_MAX."""
    if not isinstance(caller, Mapping) or set(caller) != set(F4_FIELDS):
        return None
    if not all(is_caller_age(caller[k]) for k in F4_FIELDS):
        return None
    return {k: caller[k] for k in F4_FIELDS}


def normalize_caller_f5(caller: Any) -> Optional[dict]:
    """Copy of a well-formed F5 caller policy (sorted by class), or None. A non-empty bounded class map of valid tokens to exact
    ints in 0..AGE_MAX."""
    if not isinstance(caller, Mapping) or set(caller) != set(F5_FIELDS):
        return None
    m = caller[F5_FIELD]
    if not isinstance(m, Mapping) or not m or len(m) > MAX_CLASSES:
        return None
    if not all(type(k) is str and c.valid_token(k) for k in m):
        return None
    if not all(is_caller_age(v) for v in m.values()):
        return None
    return {F5_FIELD: {k: m[k] for k in sorted(m)}}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any, family: str, validator) -> tuple:
    """(payload, None) or (None, refusal code). Checks in the dispatch order: record validity, family, payload."""
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if not isinstance(body, Mapping):
        return None, "composition_record_invalid"
    if body.get("family") != family:
        return None, "composition_family_unsupported"
    payload = body.get("payload")
    if not isinstance(payload, Mapping) or validator(payload) is not None:
        return None, "composition_record_invalid"
    return payload, None


def _ok(effective: dict, narrowed_over: list) -> CompositionResult:
    detail = (NOT_NARROWING + ":" + ",".join(narrowed_over)) if narrowed_over else ""
    return CompositionResult(True, None, detail, effective, False, ())


def compose_f4(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record, FAMILY_F4, f4_payload_validator)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller_f4(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        effective = {k: min(cal[k], payload[k]) for k in F4_FIELDS}
        return _ok(effective, [k for k in F4_FIELDS if payload[k] > cal[k]])
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")


def compose_f5(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record, FAMILY_F5, f5_payload_validator)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller_f5(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        reg, base = payload[F5_FIELD], cal[F5_FIELD]
        if set(reg) - set(base):  # a class the caller does not define is unknown: refuse, never create it
            return _refuse("composition_record_invalid", "registry class unknown to the caller")
        eff = {k: (min(base[k], reg[k]) if k in reg else base[k]) for k in base}
        return _ok({F5_FIELD: eff}, [k for k in sorted(reg) if k in base and reg[k] > base[k]])
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
