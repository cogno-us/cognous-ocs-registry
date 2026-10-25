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
from registry_successor import v2_age_bounds, v2_f1ab

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

_F1AB = FamilySpec(
    family=v2_f1ab.FAMILY_F1AB,
    payload_fields=v2_f1ab.F1AB_FIELDS,
    payload_validator=v2_f1ab.payload_validator,
    composer=v2_f1ab.compose_f1ab,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=v2_f1ab.normalize_caller,
    enforcing_component=COMPONENT_RUNTIME,
)

_F4 = FamilySpec(
    family=v2_age_bounds.FAMILY_F4,
    payload_fields=v2_age_bounds.F4_FIELDS,
    payload_validator=v2_age_bounds.f4_payload_validator,
    composer=v2_age_bounds.compose_f4,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=v2_age_bounds.normalize_caller_f4,
    enforcing_component=COMPONENT_CONTROL_PLANE,
)

_F5 = FamilySpec(
    family=v2_age_bounds.FAMILY_F5,
    payload_fields=v2_age_bounds.F5_FIELDS,
    payload_validator=v2_age_bounds.f5_payload_validator,
    composer=v2_age_bounds.compose_f5,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=v2_age_bounds.normalize_caller_f5,
    enforcing_component=COMPONENT_CONTROL_PLANE,
)

# `r08-v2` table (EXT-S1-3, EXT-S1-4): the v1 families plus `f1ab`, `f4` and `f5`. Kept SEPARATE from `FAMILIES` because the frozen `r08-v1` entry
# points (record, selection, decision) read `FAMILIES`, and the v1 golden pins that they refuse `f1ab` `family_unsupported`.
# A v2 entry point selects a table through `table_for_contract_version` (below); the v2 statement shape is EXT-S1-5/6.
FAMILIES_V2: Mapping = MappingProxyType({**FAMILIES, _F1AB.family: _F1AB, _F4.family: _F4, _F5.family: _F5})

# The family the unchanged `r08-v1` entry points normalize an optional caller policy with when a refusal happens before
# (or without) a registered family being known. Part of the frozen v1 behaviour, not a general default for new families.
V1_DEFAULT_FAMILY = _F1A.family


def lookup(family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string, or None. Never raises."""
    if not isinstance(family, str):
        return None
    try:
        return FAMILIES.get(family)
    except TypeError:  # an unhashable str subclass is simply not registered
        return None


def lookup_v2(family: Any) -> Optional[FamilySpec]:
    """Like `lookup`, against the `r08-v2` table. Exact string equality; never raises."""
    if not isinstance(family, str):
        return None
    try:
        return FAMILIES_V2.get(family)
    except TypeError:
        return None


# Contract-version strings. V1 is the frozen constant; the v2 string is the one the contract and the golden corpus use.
CONTRACT_V1 = c.CONTRACT_VERSION
CONTRACT_V2 = "r08-v2"


@dataclass(frozen=True)
class TableSelection:
    """Result of selecting a family table by `contract_version`. On refusal `table` is None and `code` is typed."""
    ok: bool
    code: Optional[str]
    version: Optional[str]
    table: Optional[Mapping]


def table_for_contract_version(version: Any) -> TableSelection:
    """Select the family table for exactly `r08-v1` (FAMILIES) or exactly `r08-v2` (FAMILIES_V2). Any other value (None,
    bytes, a str subclass, another case or whitespace, an unknown version, a non-str) refuses `contract_unsupported` with no
    table: there is no fallback, no implicit upgrade and no default. Pure; never raises."""
    if type(version) is str:  # exact str only: a subclass could override __eq__/__hash__
        if version == CONTRACT_V1:
            return TableSelection(True, None, CONTRACT_V1, FAMILIES)
        if version == CONTRACT_V2:
            return TableSelection(True, None, CONTRACT_V2, FAMILIES_V2)
    return TableSelection(False, "contract_unsupported", None, None)


def lookup_for(version: Any, family: Any) -> Optional[FamilySpec]:
    """The spec for `family` in the table of exactly this contract version, or None (unsupported version or family)."""
    if not table_for_contract_version(version).ok:
        return None
    return lookup(family) if version == CONTRACT_V1 else lookup_v2(family)


def compose_for(version: Any, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Compose with the table of exactly `version`; an unsupported version refuses `contract_unsupported` (no policy). The
    record's own `contract_version` is not consulted here and never reinterpreted: callers pass the version they validated."""
    sel = table_for_contract_version(version)
    if not sel.ok:
        return _refuse("contract_unsupported")
    return compose(caller, record, operator) if version == CONTRACT_V1 else compose_v2(caller, record, operator)


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def compose(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Dispatch composition on the validated record's family in the `r08-v1` table. Check order is the `r08-v1` order:
    operator, record validity, family registration, then the family composer. Any refusal returns no effective policy."""
    return _compose(lookup, caller, record, operator)


def compose_v2(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Same dispatch and check order against the `r08-v2` table (adds `f1ab`). Any refusal returns no effective policy."""
    return _compose(lookup_v2, caller, record, operator)


def _compose(find: Callable[[Any], Optional[FamilySpec]], caller: Any, record: Any, operator: Any) -> CompositionResult:
    try:
        if operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if not getattr(record, "ok", False):
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if not isinstance(body, Mapping):
            return _refuse("composition_record_invalid")
        spec = find(body.get("family"))
        if spec is None:
            return _refuse("composition_family_unsupported")
        return spec.composer(caller, record, operator)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refuse("composition_record_invalid", "unexpected input")
