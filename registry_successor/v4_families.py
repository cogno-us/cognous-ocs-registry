"""Family table and dispatch for contract `r08-v4` (docs/r08-v4-contract.md).

A NEW module: the frozen `families.py` (and its `r08-v1`/`r08-v2` tables) and `v3_families.py` are not edited, so `families.table_for_contract_version("r08-v4")` still
refuses `contract_unsupported` and no `r08-v2` entry point can reach an `r08-v4` family. The `r08-v4` table holds exactly one family,
`f1abcd-local-execution-limits`; the v1/v2 families are NOT registered here (a v4 record of any other family refuses `family_unsupported`).

Lookup is exact string equality; an absent, differently spelled, non-`str` or unhashable family is not registered. Pure; no I/O, clock or state.
"""
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import families
from registry_successor import v4_f1abcd
from registry_successor.compose import CompositionResult
from registry_successor.families import FamilySpec, TableSelection

CONTRACT_V4 = "r08-v4"

_F1ABCD = FamilySpec(
    family=v4_f1abcd.FAMILY_F1ABCD,
    payload_fields=v4_f1abcd.F1ABCD_FIELDS,
    payload_validator=v4_f1abcd.payload_validator,
    composer=v4_f1abcd.compose_f1abcd,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=v4_f1abcd.normalize_caller,
    enforcing_component=families.COMPONENT_RUNTIME,
)

FAMILIES_V4: Mapping = MappingProxyType({_F1ABCD.family: _F1ABCD})


def lookup_v4(family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string in the `r08-v4` table, or None. Never raises."""
    if type(family) is not str:
        return None
    try:
        return FAMILIES_V4.get(family)
    except TypeError:
        return None


def table_for_contract_version_v4(version: Any) -> TableSelection:
    """Select the table for exactly `r08-v4`. Any other value (including `r08-v1`/`r08-v2`, a str subclass, another case or whitespace, a
    non-str) refuses `contract_unsupported` with no table: no fallback, no implicit upgrade, no default."""
    if type(version) is str and version == CONTRACT_V4:
        return TableSelection(True, None, CONTRACT_V4, FAMILIES_V4)
    return TableSelection(False, "contract_unsupported", None, None)


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def compose_v4(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Dispatch composition on the validated record's family in the `r08-v4` table. Check order: operator, record validity, family registration,
    then the family composer. Any refusal returns no effective policy."""
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if getattr(record, "ok", False) is not True:
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if not isinstance(body, Mapping):
            return _refuse("composition_record_invalid")
        spec = lookup_v4(body.get("family"))
        if spec is None:
            return _refuse("composition_family_unsupported")
        return spec.composer(caller, record, operator)
    except Exception:
        return _refuse("composition_record_invalid", "unexpected input")


def compose_for_v4(version: Any, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Compose with the table of exactly `version`; anything but `r08-v4` refuses `contract_unsupported` (no policy)."""
    if not table_for_contract_version_v4(version).ok:
        return _refuse("contract_unsupported")
    return compose_v4(caller, record, operator)
