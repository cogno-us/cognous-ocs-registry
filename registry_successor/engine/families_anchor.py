"""F5 family `f5-anchor-deadline-to-inputs-policy` for contract `r08-v8` (docs/r08-v8-contract.md; Control Plane field `FreshnessProfile.anchor_deadline_to_inputs`).

APPROVED CANDIDATE (Architect-selected successor, D-C5): BUILDER_TESTED, non-authorizing, not independently qualified. Registering this family enables NO consumer; the Control Plane consumer is not implemented. The purpose-observation residual is closed only together with the separately authorized D-07 Control Plane correction, not by this module.

Payload: EXACTLY one member, `anchor_deadline_to_inputs`, an exact `str` in the CLOSED two-string vocabulary `anchor` | `no_change`. The Control Plane field is a bool
(default False); the Registry never uses JSON booleans (a `true`/`false` is `field_type_invalid`) and never coerces: the consumer maps the exact strings. A second
key refuses `field_unknown`, an absent key `field_missing`, a value outside the vocabulary `field_invalid` (types before values). Nothing is clamped, coerced, defaulted
or case-folded; values are exact `str` objects (a str subclass is refused).

Order. The only relation asserted is the two-point order `anchor` (stricter) < `no_change` (looser): `anchor` can only ADD an earlier dispatch deadline at the consumer.
`no_change` means "the Registry asserts nothing": it NEVER lowers a caller `anchor`, and this family can NEVER assert false (there is no such word in the vocabulary).

Composition (only operator `intersection`, the frozen dispatch name for narrowing): effective = `anchor` if EITHER side is `anchor`. A Registry `no_change` over a caller
`anchor` yields `anchor`, reported in `detail` as `registry_value_not_narrowing:anchor_deadline_to_inputs`. An invalid caller refuses `composition_caller_invalid` and is
never replaced. Every refusal carries no effective policy. `deny_all` is never set.

Host preconditions (consumer-owned, invisible to the Registry): a `FreshnessProfile` must already exist, and the profile must carry no `policy_binding`. The residual for the
purpose-observation window is NOT closed by this family (see the contract document). Pure and non-authorizing; unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v8`
profile. Imports no Control Plane module.
"""
import itertools
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult

FAMILY_ANCHOR = "f5-anchor-deadline-to-inputs-policy"
ANCHOR_FIELD = "anchor_deadline_to_inputs"
ANCHOR_FIELDS = (ANCHOR_FIELD,)
SCHEMA_REVISION = 1  # family_schema_revision of this payload schema; part of the effective-policy preimage

ANCHOR = "anchor"
NO_CHANGE = "no_change"
VALUES = (ANCHOR, NO_CHANGE)  # strictest first
_RANK = MappingProxyType({ANCHOR: 0, NO_CHANGE: 1})  # immutable: no mutable module global
NOT_NARROWING = "registry_value_not_narrowing"


def is_value(v: Any) -> bool:
    """Exact `str` in the closed vocabulary. `type(v) is str` excludes every str subclass."""
    return type(v) is str and v in _RANK


def stricter(a: str, b: str) -> str:
    """The stricter of two valid values (`anchor` < `no_change`); the first on a tie."""
    return a if _RANK[a] <= _RANK[b] else b


def payload_validator(payload: dict) -> Optional[str]:
    """None when valid, else a shape code (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    if type(payload) is not dict or not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(ANCHOR_FIELDS):
        return "field_unknown"
    if set(ANCHOR_FIELDS) - keys:
        return "field_missing"
    value = payload[ANCHOR_FIELD]
    if type(value) is not str:
        return "field_type_invalid"
    return None if is_value(value) else "field_invalid"


def _snapshot(m: Any, limit: int) -> Optional[dict]:
    """One read of at most `limit` entries of a caller mapping into a plain dict, or None (not a Mapping, unreadable, more than `limit` entries or a non-`str` key).
    Validation and composition then use only the copy."""
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
    """Copy of a well-formed caller policy, or None: exactly the one key with a value in the closed vocabulary (a bool is not a value)."""
    snap = _snapshot(caller, len(ANCHOR_FIELDS))
    if snap is None or set(snap) != set(ANCHOR_FIELDS) or not is_value(snap[ANCHOR_FIELD]):
        return None
    return {ANCHOR_FIELD: snap[ANCHOR_FIELD]}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any) -> tuple:
    """(payload copy, None) or (None, refusal code): record validity, family, payload. Each attribute is read once and the validated copy is what composes."""
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if type(body) is not dict:
        return None, "composition_record_invalid"
    family_seen, payload = body.get("family"), body.get("payload")
    if type(family_seen) is not str or family_seen != FAMILY_ANCHOR:
        return None, "composition_family_unsupported"
    if type(payload) is not dict:
        return None, "composition_record_invalid"
    snap = dict(payload)
    if payload_validator(snap) is not None:
        return None, "composition_record_invalid"
    return snap, None


def compose_anchor(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        reg, base = payload[ANCHOR_FIELD], cal[ANCHOR_FIELD]
        detail = (NOT_NARROWING + ":" + ANCHOR_FIELD) if _RANK[reg] > _RANK[base] else ""
        return CompositionResult(True, None, detail, {ANCHOR_FIELD: stricter(base, reg)}, False, ())
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
