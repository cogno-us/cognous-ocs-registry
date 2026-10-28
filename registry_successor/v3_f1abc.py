"""Composite family `f1abc-local-execution-limits` for contract `r08-v3` (docs/r08-v3-contract.md; M2 PR-1).

Payload: EXACTLY seven members: the five f1ab allow-sets (`allowed_actions`, `allowed_adapters`, `allowed_units`, `allowed_institutions`,
`allowed_authority_domains`) and the two ceilings `max_amount`, `max_effects`. An absent member refuses `field_missing`, an extra one
`field_unknown`; nothing is ever defaulted.

The five sets are validated and normalized by the frozen `v2_f1ab` functions, called by import on the five-member sub-mapping (no copy, no edit).
Set composition is the f1ab composition: intersection per set; an empty effective set is deny-all.

Ceilings: exact `int` only (`type(v) is int`: no bool, float, Decimal, str, None, bytes or int subclass; no coercion, rounding, truncation,
clamping or defaulting).
  * Registry `max_amount`: 0 ..= 2**53 (`safe_executor.MAX_EXACT_INTEGER_AMOUNT`). 0 is a valid ceiling, not deny-all.
  * Registry `max_effects`: 0 ..= 2**53 - 1. 0 is the explicit deny-all: composition reports `deny_all` and consumers must build no policy.
  * Caller `max_amount`: exact int 0 ..= 2**53. A caller float is REFUSED in this governed path (`composition_caller_invalid`): the effective-policy
    digest is integer-only, so a float ceiling cannot be bound to the identity (documented compatibility limitation).
  * Caller `max_effects`: exact int >= 1 (the evaluator requires a positive int); no upper bound, because the effective value is `min(caller,
    registry)` and so never exceeds the Registry bound.

Composition (only operator `intersection`, the frozen dispatch name for narrowing): sets by intersection, ceilings by `min(caller, registry)`. A
Registry ceiling above the caller yields the caller, reported in `detail` as `registry_value_not_narrowing:<names>`. The result never exceeds the
caller for any member. An invalid caller refuses `composition_caller_invalid` and is never replaced. Every refusal carries no effective policy.

Pure, non-authorizing, unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v3` table (`v3_families.FAMILIES_V3`). Imports no Runtime or Control
Plane module and builds no `LocalExecutionPolicy`.
"""
import itertools
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import v2_f1ab
from registry_successor.compose import CompositionResult

FAMILY_F1ABC = "f1abc-local-execution-limits"
SET_FIELDS = v2_f1ab.F1AB_FIELDS
CEILING_FIELDS = ("max_amount", "max_effects")
F1ABC_FIELDS = SET_FIELDS + CEILING_FIELDS

AMOUNT_MIN = 0
AMOUNT_MAX = 2 ** 53          # safe_executor.MAX_EXACT_INTEGER_AMOUNT
EFFECTS_MIN = 0               # Registry: 0 is the explicit deny-all
EFFECTS_MAX = 2 ** 53 - 1     # Registry canonical-integer convention (verify.MAX_SNAPSHOT_VERSION); see docs/r08-v3-contract.md
CALLER_EFFECTS_MIN = 1

NOT_NARROWING = "registry_value_not_narrowing"


def is_registry_amount(v: Any) -> bool:
    return type(v) is int and AMOUNT_MIN <= v <= AMOUNT_MAX


def is_registry_effects(v: Any) -> bool:
    return type(v) is int and EFFECTS_MIN <= v <= EFFECTS_MAX


def is_caller_amount(v: Any) -> bool:
    return type(v) is int and AMOUNT_MIN <= v <= AMOUNT_MAX


def is_caller_effects(v: Any) -> bool:
    return type(v) is int and v >= CALLER_EFFECTS_MIN


def payload_validator(payload: Any) -> Optional[str]:
    """None when valid, else a shape code in the v1 order (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    if type(payload) is not dict:
        return "field_type_invalid"
    if not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(F1ABC_FIELDS):
        return "field_unknown"
    if set(F1ABC_FIELDS) - keys:
        return "field_missing"
    if not all(type(payload[k]) is list for k in SET_FIELDS):
        return "field_type_invalid"
    if not all(type(payload[k]) is int for k in CEILING_FIELDS):  # bool, float, str, None, Decimal, int subclasses all fail here
        return "field_type_invalid"
    code = v2_f1ab.payload_validator({k: payload[k] for k in SET_FIELDS})  # the frozen f1ab validator, by import
    if code:
        return code
    if not is_registry_amount(payload["max_amount"]) or not is_registry_effects(payload["max_effects"]):
        return "field_invalid"
    return None


def _snapshot(m: Any, limit: int) -> Optional[dict]:
    """One bounded read of a caller mapping into a plain dict, or None (not a Mapping, unreadable, more than `limit` entries, or a non-`str`
    key). Validation and composition then use only the copy."""
    if not isinstance(m, Mapping):
        return None
    try:
        items = list(itertools.islice(m.items(), limit + 1))
        if len(items) > limit or any(type(k) is not str for k, _ in items):
            return None
        return {k: v for k, v in items}
    except Exception:
        return None


def normalize_caller(caller: Any) -> Optional[dict]:
    """Copy of a well-formed caller policy, or None: exactly the seven keys; sets as for f1ab (sorted tuples); ceilings per the module docstring."""
    snap = _snapshot(caller, len(F1ABC_FIELDS))
    if snap is None or set(snap) != set(F1ABC_FIELDS):
        return None
    sets = v2_f1ab.normalize_caller({k: snap[k] for k in SET_FIELDS})  # the frozen f1ab normalizer, by import
    if sets is None:
        return None
    if not is_caller_amount(snap["max_amount"]) or not is_caller_effects(snap["max_effects"]):
        return None
    return {**sets, "max_amount": snap["max_amount"], "max_effects": snap["max_effects"]}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any) -> tuple:
    """(payload copy, None) or (None, refusal code), in the dispatch order: record validity, family, payload. The copy is what is validated."""
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if type(body) is not dict:
        return None, "composition_record_invalid"
    family, payload = body.get("family"), body.get("payload")
    if type(family) is not str or family != FAMILY_F1ABC:
        return None, "composition_family_unsupported"
    if type(payload) is not dict:
        return None, "composition_record_invalid"
    snap = dict(payload)
    if payload_validator(snap) is not None:
        return None, "composition_record_invalid"
    return snap, None


def compose_f1abc(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        effective = {f: tuple(sorted(set(cal[f]) & set(payload[f]))) for f in SET_FIELDS}
        effective["max_amount"] = min(cal["max_amount"], payload["max_amount"])
        effective["max_effects"] = min(cal["max_effects"], payload["max_effects"])
        deny = tuple(f for f in SET_FIELDS if not effective[f]) + (("max_effects",) if payload["max_effects"] == 0 else ())
        wider = [k for k in CEILING_FIELDS if payload[k] > cal[k]]
        detail = (NOT_NARROWING + ":" + ",".join(wider)) if wider else ""
        return CompositionResult(True, None, detail, effective, bool(deny), deny)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
