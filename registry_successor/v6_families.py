"""Family table and dispatch for contract `r08-v6` (docs/r08-v6-contract.md).

A NEW module: the frozen `families.py` (and its `r08-v1`/`r08-v2` tables) and `v3_families.py` .. `v6_families.py` are not edited, so
`families.table_for_contract_version("r08-v6")` still refuses `contract_unsupported` and no `r08-v2`..`r08-v6` entry point can reach an `r08-v6`
family. The `r08-v6` table holds exactly two families, `f5-action-class-revocation-assurance-policy` and `f5-terminal-revocation-enablement-policy`; no
earlier family is registered here (a v6 record of any other family refuses `family_unsupported`). The two families are independent: each record and
selection is for exactly one family under its own operation id, and sharing a contract version does NOT make them atomically applicable.

Lookup is exact string equality. An absent, differently spelled, non-`str` or unhashable family is not registered. Pure; no I/O, clock or state.
"""
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import families
from registry_successor import v6_class_revocation_assurance as ra
from registry_successor import v6_terminal_revocation as tr
from registry_successor.compose import CompositionResult
from registry_successor.families import FamilySpec, TableSelection

CONTRACT_V6 = "r08-v6"

_F5RA = FamilySpec(
    family=ra.FAMILY_F5RA,
    payload_fields=ra.F5RA_FIELDS,
    payload_validator=ra.payload_validator,
    composer=ra.compose_f5ra,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=ra.normalize_caller,
    enforcing_component=families.COMPONENT_CONTROL_PLANE,
)

_TR = FamilySpec(
    family=tr.FAMILY_TR,
    payload_fields=tr.TR_FIELDS,
    payload_validator=tr.payload_validator,
    composer=tr.compose_tr,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=tr.normalize_caller,
    enforcing_component=families.COMPONENT_CONTROL_PLANE,
)

FAMILIES_V6: Mapping = MappingProxyType({_F5RA.family: _F5RA, _TR.family: _TR})


def lookup_v6(family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string in the `r08-v6` table, or None. Never raises."""
    if type(family) is not str:
        return None
    try:
        return FAMILIES_V6.get(family)
    except TypeError:
        return None


def table_for_contract_version_v6(version: Any) -> TableSelection:
    """Select the table for exactly `r08-v6`. Any other value (including `r08-v1`..`r08-v5`, a str subclass, another case or whitespace, a
    non-str) refuses `contract_unsupported` with no table: no fallback, no implicit upgrade, no default."""
    if type(version) is str and version == CONTRACT_V6:
        return TableSelection(True, None, CONTRACT_V6, FAMILIES_V6)
    return TableSelection(False, "contract_unsupported", None, None)


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def compose_v6(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Dispatch composition on the validated record's family in the `r08-v6` table. Check order: operator, record validity, family registration,
    then the family composer. Any refusal returns no effective policy."""
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if getattr(record, "ok", False) is not True:
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if not isinstance(body, Mapping):
            return _refuse("composition_record_invalid")
        spec = lookup_v6(body.get("family"))
        if spec is None:
            return _refuse("composition_family_unsupported")
        return spec.composer(caller, record, operator)
    except Exception:
        return _refuse("composition_record_invalid", "unexpected input")


def compose_for_v6(version: Any, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Compose with the table of exactly `version`; anything but `r08-v6` refuses `contract_unsupported` (no policy)."""
    if not table_for_contract_version_v6(version).ok:
        return _refuse("contract_unsupported")
    return compose_v6(caller, record, operator)
