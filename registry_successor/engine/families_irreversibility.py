"""F5 family `f5-action-class-irreversibility-policy` for contract `r08-v7` (docs/r08-v7-contract.md; audit item RG-C-011, the legacy `ActionClass.irreversible` lever).

Payload: EXACTLY one member, `class_irreversible`, an object `action_class -> value` with value in the CLOSED two-string vocabulary `irreversible` |
`no_change`. The Control Plane field `ActionClass.irreversible` is a bool; the Registry never uses JSON booleans (a `true`/`false` is `field_type_invalid`)
and never coerces: the consumer maps the exact strings. A second key refuses `field_unknown`, an absent key `field_missing`. Nothing is ever clamped,
coerced, defaulted or case-folded: values and class keys are exact `str` objects (a str subclass is refused), class keys follow the frozen opaque-token
rule of the `r08-v2` F5 family (`frozen_token_valid`, 1..128, no `*`), keys must appear sorted, at most MAX_ENTRIES, and an empty map refuses.

Order. The only relation the Registry asserts is the two-point order `irreversible` (stricter) < `no_change` (looser): `irreversible` can only ADD a
restriction at the consumer (the class is treated as not reversible). `no_change` means "the Registry asserts nothing for this class": it NEVER lowers a
caller `irreversible`, and this family can NEVER assert reversibility. Whether a host class may be flipped at all is the consumer's pre-check (the
Registry cannot see the host's reversal data).

Composition (only operator `intersection`, the frozen dispatch name for narrowing): effective = the stricter of (caller, registry) per class. A Registry
`no_change` over a caller `irreversible` yields the caller value (reported in `detail` as `registry_value_not_narrowing:<classes>`); the result is never
looser than the caller. A Registry class the caller does not define is unknown and refuses `composition_record_invalid` (a class is never created); a
caller class absent from the Registry keeps the caller value. An invalid caller refuses `composition_caller_invalid` and is never replaced. Every refusal
carries no effective policy. `deny_all` is never set.

Pure and non-authorizing; unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v7` profile. Imports no Control Plane module.
"""
import itertools
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult
from registry_successor.v2_token import frozen_token_valid

FAMILY_IRREVERSIBILITY = "f5-action-class-irreversibility-policy"
IRR_FIELD = "class_irreversible"
IRR_FIELDS = (IRR_FIELD,)
MAX_CLASSES = c.MAX_ENTRIES
SCHEMA_REVISION = 1  # family_schema_revision of this payload schema; part of the effective-policy preimage

IRREVERSIBLE = "irreversible"
NO_CHANGE = "no_change"
VALUES = (IRREVERSIBLE, NO_CHANGE)  # strictest first
_RANK = MappingProxyType({IRREVERSIBLE: 0, NO_CHANGE: 1})  # immutable: no mutable module global
NOT_NARROWING = "registry_value_not_narrowing"


def is_value(v: Any) -> bool:
    """Exact `str` in the closed vocabulary. `type(v) is str` excludes every str subclass."""
    return type(v) is str and v in _RANK


def stricter(a: str, b: str) -> str:
    """The stricter of two valid values (`irreversible` < `no_change`); the first on a tie."""
    return a if _RANK[a] <= _RANK[b] else b


def payload_validator(payload: dict) -> Optional[str]:
    """None when valid, else a shape code (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    if type(payload) is not dict or not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(IRR_FIELDS):
        return "field_unknown"
    if set(IRR_FIELDS) - keys:
        return "field_missing"
    m = payload[IRR_FIELD]
    if type(m) is not dict:
        return "field_type_invalid"
    if not all(type(k) is str for k in m) or not all(type(v) is str for v in m.values()):
        return "field_type_invalid"
    if not m or len(m) > MAX_CLASSES:
        return "field_invalid"
    names = list(m)
    if not all(frozen_token_valid(k) for k in names) or names != sorted(names):
        return "field_invalid"
    if not all(is_value(v) for v in m.values()):
        return "field_invalid"
    return None


def _snapshot(m: Any, limit: int) -> Optional[dict]:
    """One read of at most `limit` entries of a caller mapping into a plain dict, or None (not a Mapping, unreadable, more than `limit` entries or a
    non-`str` key). Validation and composition then use only the copy, so a Mapping that changes between reads cannot pass validation with one value and
    compose with another."""
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
    """Copy of a well-formed caller policy (sorted by class), or None: exactly the one key, a non-empty bounded map of valid class tokens to values in
    the closed vocabulary."""
    snap = _snapshot(caller, len(IRR_FIELDS))
    if snap is None or set(snap) != set(IRR_FIELDS):
        return None
    m = _snapshot(snap[IRR_FIELD], MAX_CLASSES)
    if m is None or not m:
        return None
    if not all(frozen_token_valid(k) for k in m) or not all(is_value(v) for v in m.values()):
        return None
    return {IRR_FIELD: {k: m[k] for k in sorted(m)}}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any) -> tuple:
    """(payload copy, None) or (None, refusal code): record validity, family, payload. Each attribute is read once and the validated copy is what
    composes."""
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if type(body) is not dict:
        return None, "composition_record_invalid"
    family_seen, payload = body.get("family"), body.get("payload")
    if type(family_seen) is not str or family_seen != FAMILY_IRREVERSIBILITY:
        return None, "composition_family_unsupported"
    if type(payload) is not dict:
        return None, "composition_record_invalid"
    snap = {k: (dict(v) if type(v) is dict else v) for k, v in payload.items()}
    if payload_validator(snap) is not None:
        return None, "composition_record_invalid"
    return snap, None


def compose_irreversibility(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        reg, base = payload[IRR_FIELD], cal[IRR_FIELD]
        if set(reg) - set(base):  # a class the caller does not define is unknown: refuse, never create it
            return _refuse("composition_record_invalid", "registry class unknown to the caller")
        eff = {k: (stricter(base[k], reg[k]) if k in reg else base[k]) for k in base}
        looser = [k for k in sorted(reg) if k in base and _RANK[reg[k]] > _RANK[base[k]]]
        detail = (NOT_NARROWING + ":" + ",".join(looser)) if looser else ""
        return CompositionResult(True, None, detail, {IRR_FIELD: eff}, False, ())
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
