"""F5 family `f5-terminal-revocation-enablement-policy` for contract `r08-v6` (docs/r08-v6-contract.md; audit parameter
P-RG-C-TERMINAL-REVOCATION-enabled).

Payload: EXACTLY one member, `terminal_revocation`, an exact `str` in the CLOSED vocabulary `off` | `on` (a scalar, not a map; no JSON boolean, no
coercion, no case folding, no str subclass). The Control Plane `RuntimeAuthorityProfile.terminal_revocation` is absent = off, present = on; `on` adds a
refusal `grant_revocation_recorded` for a grant revision whose revocation a retained check already observed. It grants nothing and does not decide who
may revoke. A second key refuses `field_unknown`, an absent key `field_missing`, a non-`str` value `field_type_invalid`, any other string
`field_invalid`.

Order. The only relation the Registry asserts is the two-point order `on` (stricter) < `off` (looser): `on` can only ADD a refusal. The Registry cannot
see which grants were revoked nor irreversibility; it never revokes (docs/r08-v6-contract.md section 4).

Composition (only operator `intersection`): effective = `on` if EITHER side is `on`, else `off`. A Registry `off` over a caller `on` yields `on` and is
reported in `detail` as `registry_value_not_narrowing:terminal_revocation`; Registry `off` over caller `off` yields `off` (no detail). An invalid
caller (anything but exactly `{"terminal_revocation": "off"|"on"}`) refuses `composition_caller_invalid` and is never replaced. Every refusal carries
no effective policy. `deny_all` is never set.

Pure and non-authorizing; unqualified (BUILDER_TESTED). Registered ONLY in the `r08-v6` table (`v6_families.FAMILIES_V6`). Imports no Control Plane module.
"""
import itertools
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult

FAMILY_TR = "f5-terminal-revocation-enablement-policy"
TR_FIELD = "terminal_revocation"
TR_FIELDS = (TR_FIELD,)

ON = "on"
OFF = "off"
VALUES = (ON, OFF)  # strictest first
_RANK = {ON: 0, OFF: 1}
NOT_NARROWING = "registry_value_not_narrowing"


def is_value(v: Any) -> bool:
    """Exact `str` in the closed vocabulary. `type(v) is str` excludes every str subclass."""
    return type(v) is str and v in _RANK


def stricter(a: str, b: str) -> str:
    """The stricter of two valid values (`on` < `off`); the first on a tie."""
    return a if _RANK[a] <= _RANK[b] else b


def payload_validator(payload: dict) -> Optional[str]:
    """None when valid, else a shape code (`field_type_invalid` before `field_invalid`). Safe to call alone."""
    if type(payload) is not dict or not all(type(k) is str for k in payload):
        return "field_type_invalid"
    keys = set(payload)
    if keys - set(TR_FIELDS):
        return "field_unknown"
    if set(TR_FIELDS) - keys:
        return "field_missing"
    value = payload[TR_FIELD]
    if type(value) is not str:
        return "field_type_invalid"
    if not is_value(value):
        return "field_invalid"
    return None


def _snapshot(m: Any, limit: int) -> Optional[dict]:
    """One read of at most `limit` entries of a caller mapping into a plain dict, or None (not a Mapping, unreadable, more than `limit` entries or a
    non-`str` key)."""
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
    """Copy of a well-formed caller policy, or None: exactly `{"terminal_revocation": "off"|"on"}` (a scalar, never a map)."""
    snap = _snapshot(caller, len(TR_FIELDS))
    if snap is None or set(snap) != set(TR_FIELDS) or not is_value(snap[TR_FIELD]):
        return None
    return {TR_FIELD: snap[TR_FIELD]}


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def _record_payload(record: Any) -> tuple:
    """(payload copy, None) or (None, refusal code): record validity, family, payload (each attribute read once)."""
    if getattr(record, "ok", False) is not True:
        return None, "composition_record_invalid"
    body = getattr(record, "record", None)
    if type(body) is not dict:
        return None, "composition_record_invalid"
    family_seen, payload = body.get("family"), body.get("payload")
    if type(family_seen) is not str or family_seen != FAMILY_TR:
        return None, "composition_family_unsupported"
    if type(payload) is not dict:
        return None, "composition_record_invalid"
    snap = dict(payload)
    if payload_validator(snap) is not None:
        return None, "composition_record_invalid"
    return snap, None


def compose_tr(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        payload, code = _record_payload(record)
        if payload is None:
            return _refuse(code)
        cal = normalize_caller(caller)
        if cal is None:
            return _refuse("composition_caller_invalid")
        reg, base = payload[TR_FIELD], cal[TR_FIELD]
        eff = stricter(base, reg)
        detail = (NOT_NARROWING + ":" + TR_FIELD) if _RANK[reg] > _RANK[base] else ""
        return CompositionResult(True, None, detail, {TR_FIELD: eff}, False, ())
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
