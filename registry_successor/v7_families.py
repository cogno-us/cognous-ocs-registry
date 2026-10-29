"""Family table and dispatch for contract `r08-v7` (docs/r08-v7-contract.md). A thin public view over the engine profile `engine.profiles.V7`.

The `r08-v7` table registers exactly ONE family, `f5-action-class-irreversibility-policy` (schema revision 1). No earlier family is registered here (a v7
record of any other family refuses `family_unsupported`) and `families.table_for_contract_version("r08-v7")` still refuses `contract_unsupported`.
Lookup is exact string equality. Pure; no I/O, clock or state.
"""
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor.compose import CompositionResult
from registry_successor.engine import profile as _p
from registry_successor.engine import profiles as _profiles
from registry_successor.families import FamilySpec, TableSelection

CONTRACT_V7 = _profiles.CONTRACT_V7
FAMILIES_V7: Mapping = _profiles.V7.specs


def lookup_v7(family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string in the `r08-v7` table, or None. Never raises."""
    return _p.lookup(_profiles.V7, family)


def table_for_contract_version_v7(version: Any) -> TableSelection:
    """Select the table for exactly `r08-v7`; anything else refuses `contract_unsupported` (no fallback, no implicit upgrade, no default)."""
    return _p.table_for_contract_version(_profiles.V7, version)


def compose_v7(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    return _p.compose(_profiles.V7, caller, record, operator)


def compose_for_v7(version: Any, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Compose with the table of exactly `version`; anything but `r08-v7` refuses `contract_unsupported` (no policy)."""
    return _p.compose_for(_profiles.V7, version, caller, record, operator)
