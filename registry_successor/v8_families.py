"""Family table and dispatch for contract `r08-v8` (docs/r08-v8-contract.md). A thin public view over the engine profile `engine.profiles.V8`.

APPROVED CANDIDATE (docs/r08-v8-contract.md). The `r08-v8` table registers exactly THREE families, `f5-anchor-deadline-to-inputs-policy`,
`f5-observation-max-age-policy` and `f5-observation-clock-tolerance-policy` (schema revision 1 each), and does NOT re-register `f5-action-class-irreversibility-policy`
or any earlier family (a v8 record of any other family refuses `family_unsupported`). `families.table_for_contract_version("r08-v8")` still refuses `contract_unsupported`.
Registering a family enables no consumer. Lookup is exact string equality. Pure; no I/O, clock or state.
"""
from collections.abc import Mapping
from typing import Any, Optional

from registry_successor.compose import CompositionResult
from registry_successor.engine import families_anchor as _anchor
from registry_successor.engine import families_observation as _obs
from registry_successor.engine import profile as _p
from registry_successor.engine import profiles as _profiles
from registry_successor.families import FamilySpec, TableSelection

CONTRACT_V8 = _profiles.CONTRACT_V8
FAMILIES_V8: Mapping = _profiles.V8.specs
# Public family ids (so a consumer never imports engine internals). Table order; each is also a key of FAMILIES_V8. The family schema revision of each is
# `v8_policy_identity.registered_family_version(family_id, CONTRACT_V8)` (an int, 1 for all three).
FAMILY_ANCHOR_V8 = _anchor.FAMILY_ANCHOR
FAMILY_OBSERVATION_MAX_AGE_V8 = _obs.FAMILY_MAX_AGE
FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8 = _obs.FAMILY_TOLERANCE
FAMILY_IDS_V8 = (FAMILY_ANCHOR_V8, FAMILY_OBSERVATION_MAX_AGE_V8, FAMILY_OBSERVATION_CLOCK_TOLERANCE_V8)


def lookup_v8(family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string in the `r08-v8` table, or None. Never raises."""
    return _p.lookup(_profiles.V8, family)


def table_for_contract_version_v8(version: Any) -> TableSelection:
    """Select the table for exactly `r08-v8`; anything else refuses `contract_unsupported` (no fallback, no implicit upgrade, no default)."""
    return _p.table_for_contract_version(_profiles.V8, version)


def compose_v8(caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    return _p.compose(_profiles.V8, caller, record, operator)


def compose_for_v8(version: Any, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Compose with the table of exactly `version`; anything but `r08-v8` refuses `contract_unsupported` (no policy)."""
    return _p.compose_for(_profiles.V8, version, caller, record, operator)
