"""The two shipped contract profiles (docs/r08-v7-contract.md section 3). Both are module-level frozen values; nothing registers a family at run time.

`V7` is the unified successor `r08-v7` and carries exactly ONE family now, `f5-action-class-irreversibility-policy` (schema revision 1). The families
for `anchor_deadline_to_inputs`, `ObservationPolicy.max_age_seconds` and `ObservationPolicy.clock_tolerance_seconds` are BLOCKED by decision record and
are NOT registered.

`V6_COMPAT` is the exact frozen `r08-v6` contract (its version, domains, family specs and identity rows) built FROM the existing v6 modules, which are
imported and never edited: the compatibility adapter. The differential tests prove engine(V6_COMPAT) equals the frozen v6 entry points.
"""
from types import MappingProxyType

from registry_successor import common as c
from registry_successor import families
from registry_successor import v6_class_revocation_assurance as v6_ra
from registry_successor import v6_families
from registry_successor import v6_policy_identity as v6_pid
from registry_successor import v6_selection as v6_sel
from registry_successor import v6_terminal_revocation as v6_tr
from registry_successor.engine import families_irreversibility as irr
from registry_successor.engine.profile import (VERSION_MEMBER_REVISION, VERSION_MEMBER_TAG, ContractProfile, FamilyEntry, IdentityRow)

CONTRACT_V7 = "r08-v7"
SELECTION_DOMAIN_V7 = b"ocs-reg/r08-v7/selection\n"
EFFECTIVE_DOMAIN_V7 = b"ocs-reg/r08-v7/effective-policy\n"

_IRR_SPEC = families.FamilySpec(
    family=irr.FAMILY_IRREVERSIBILITY,
    payload_fields=irr.IRR_FIELDS,
    payload_validator=irr.payload_validator,
    composer=irr.compose_irreversibility,
    evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
    caller_normalizer=irr.normalize_caller,
    enforcing_component=families.COMPONENT_CONTROL_PLANE,
)

V7 = ContractProfile(
    version=CONTRACT_V7,
    selection_signing_domain=SELECTION_DOMAIN_V7,
    effective_policy_domain=EFFECTIVE_DOMAIN_V7,
    families=MappingProxyType({irr.FAMILY_IRREVERSIBILITY: FamilyEntry(_IRR_SPEC, irr.SCHEMA_REVISION)}),
    identity=MappingProxyType({irr.FAMILY_IRREVERSIBILITY: IdentityRow(
        irr.FAMILY_IRREVERSIBILITY, "classmap-enum", irr.IRR_FIELDS, irr.is_value, VERSION_MEMBER_REVISION, irr.SCHEMA_REVISION)}),
)

_V6_IS_VALUE = MappingProxyType({v6_ra.FAMILY_F5RA: v6_ra.is_value, v6_tr.FAMILY_TR: v6_tr.is_value})

V6_COMPAT = ContractProfile(
    version=v6_families.CONTRACT_V6,
    selection_signing_domain=v6_sel.SIGNING_DOMAIN_V6,
    effective_policy_domain=v6_pid.EFFECTIVE_PREFIX,
    families=MappingProxyType({k: FamilyEntry(spec, None) for k, spec in v6_families.FAMILIES_V6.items()}),
    identity=MappingProxyType({k: IdentityRow(k, row.kind, row.members, _V6_IS_VALUE[k], VERSION_MEMBER_TAG, row.family_version)
                               for k, row in v6_pid.IDENTITY_FAMILIES.items()}),
)

PROFILES = MappingProxyType({CONTRACT_V7: V7, v6_families.CONTRACT_V6: V6_COMPAT})
