"""Family dispatch table for the registry successor contracts (docs/r08-v2-contract.md section 1; ADR EXT-S1-1 D-09, D-10).

One small, data-only table: `family -> (payload validator, composer, evaluator binding, caller normalizer, enforcing
component)`. It is the ONLY place a family is registered. `EXT-S1-2` registers the existing `f1a-local-execution-allowlist`
alone; no other family is registered here, and registering one is a later, separately authorized change.

Lookup is exact string equality. A family that is absent, spelled with a different case or whitespace, not a `str`, or not
hashable is not registered: the parse layers refuse it `family_unsupported` and composition refuses it
`composition_family_unsupported`. A refusal never carries a policy, so a required operation can never return the caller
policy through this module.

Non-authorizing and unqualified. Pure: no I/O, no clock, no state (the table is read-only). Imports no Runtime or Control
Plane module. The behaviour of every registered family is the unchanged `r08-v1` behaviour (golden-replay proved).
"""
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Optional

from registry_successor import common as c
from registry_successor import compose as compose_mod
from registry_successor.compose import CompositionResult

# Enforcing components named by the contract (section 2 table). Descriptive labels only: never an authorization.
COMPONENT_RUNTIME = "runtime"
COMPONENT_CONTROL_PLANE = "control-plane"


@dataclass(frozen=True)
class FamilySpec:
    family: str
    payload_fields: tuple
    # payload -> None when valid, else the shape code in the original v1 order: "field_type_invalid" before "field_invalid".
    payload_validator: Callable[[dict], Optional[str]]
    # (caller, record_result, operator) -> CompositionResult
    composer: Callable[..., CompositionResult]
    # (evaluator_id, binding) the family's records and selections must name.
    evaluator_binding: tuple
    # caller -> normalized caller dict or None
    caller_normalizer: Callable[[Any], Optional[dict]]
    enforcing_component: str


def _f1a_payload_validator(payload: dict) -> Optional[str]:
    if not all(isinstance(payload[k], list) for k in c.F1A_FIELDS):
        return "field_type_invalid"
    if not all(c.valid_entry_list(payload[k], allow_empty=True) for k in c.F1A_FIELDS):
        return "field_invalid"
    return None


_F1A = FamilySpec(
    family=c.FAMILY_F1A,
    payload_fields=c.F1A_FIELDS,
    payload_validator=_f1a_payload_validator,
    composer=compose_mod.compose_f1a,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=compose_mod.normalize_caller,
    enforcing_component=COMPONENT_RUNTIME,
)

# Read-only view: a family is registered by editing this file, never at run time.
FAMILIES: Mapping = MappingProxyType({_F1A.family: _F1A})

# The family the unchanged `r08-v1` entry points normalize an optional caller policy with when a refusal happens before
# (or without) a registered family being known. Part of the frozen v1 behaviour, not a general default for new families.
V1_DEFAULT_FAMILY = _F1A.family


def lookup(family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string, or None. Never raises."""
    if not isinstance(family, str):
        return None
    return FAMILIES.get(family)


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def compose(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Dispatch composition on the validated record's family. Check order is the `r08-v1` order: operator, record
    validity, family registration, then the family composer. Any refusal returns no effective policy."""
    try:
        if operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if not getattr(record, "ok", False):
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if not isinstance(body, Mapping):
            return _refuse("composition_record_invalid")
        spec = lookup(body.get("family"))
        if spec is None:
            return _refuse("composition_family_unsupported")
        return spec.composer(caller, record, operator)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
