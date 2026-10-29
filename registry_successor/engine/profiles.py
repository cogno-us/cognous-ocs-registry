"""The shipped contract profiles (docs/r08-v7-contract.md section 3; `V8` docs/r08-v8-contract.md). All are module-level frozen values; nothing registers a family at run time.

`V7` is the unified successor `r08-v7` and carries exactly ONE family now, `f5-action-class-irreversibility-policy` (schema revision 1). The families
for `anchor_deadline_to_inputs`, `ObservationPolicy.max_age_seconds` and `ObservationPolicy.clock_tolerance_seconds` are BLOCKED by decision record and
are NOT registered.

`V8` is the PROPOSED, GATED successor `r08-v8` (DRAFT; not for merge until the Architect decides): it carries ONLY the three remaining families
`f5-anchor-deadline-to-inputs-policy`, `f5-observation-max-age-policy` and `f5-observation-clock-tolerance-policy` (schema revision 1 each) and does NOT re-register
irreversibility. It is additive: `V7`, `V6_COMPAT` and `PROFILES` are unchanged, and `V8` is not a member of `PROFILES`.

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
from registry_successor.engine import families_anchor as anc
from registry_successor.engine import families_irreversibility as irr
from registry_successor.engine import families_observation as obs
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

CONTRACT_V8 = "r08-v8"
SELECTION_DOMAIN_V8 = b"ocs-reg/r08-v8/selection\n"
EFFECTIVE_DOMAIN_V8 = b"ocs-reg/r08-v8/effective-policy\n"


def _spec(family, fields, validator, composer, normalizer):
    return families.FamilySpec(
        family=family,
        payload_fields=fields,
        payload_validator=validator,
        composer=composer,
        evaluator_binding=(c.EVALUATOR_ID, c.EVALUATOR_BINDING),
        caller_normalizer=normalizer,
        enforcing_component=families.COMPONENT_CONTROL_PLANE,
    )


_ANCHOR_SPEC = _spec(anc.FAMILY_ANCHOR, anc.ANCHOR_FIELDS, anc.payload_validator, anc.compose_anchor, anc.normalize_caller)
_MAX_AGE_SPEC = _spec(obs.FAMILY_MAX_AGE, obs.MAX_AGE_FIELDS, obs.max_age_payload_validator, obs.compose_max_age, obs.normalize_caller_max_age)
_TOLERANCE_SPEC = _spec(obs.FAMILY_TOLERANCE, obs.TOLERANCE_FIELDS, obs.tolerance_payload_validator, obs.compose_tolerance, obs.normalize_caller_tolerance)

V8 = ContractProfile(
    version=CONTRACT_V8,
    selection_signing_domain=SELECTION_DOMAIN_V8,
    effective_policy_domain=EFFECTIVE_DOMAIN_V8,
    families=MappingProxyType({
        anc.FAMILY_ANCHOR: FamilyEntry(_ANCHOR_SPEC, anc.SCHEMA_REVISION),
        obs.FAMILY_MAX_AGE: FamilyEntry(_MAX_AGE_SPEC, obs.SCHEMA_REVISION),
        obs.FAMILY_TOLERANCE: FamilyEntry(_TOLERANCE_SPEC, obs.SCHEMA_REVISION),
    }),
    identity=MappingProxyType({
        anc.FAMILY_ANCHOR: IdentityRow(anc.FAMILY_ANCHOR, "scalar-enum", anc.ANCHOR_FIELDS, anc.is_value, VERSION_MEMBER_REVISION, anc.SCHEMA_REVISION),
        obs.FAMILY_MAX_AGE: IdentityRow(obs.FAMILY_MAX_AGE, "scalar-int", obs.MAX_AGE_FIELDS, obs.is_max_age, VERSION_MEMBER_REVISION, obs.SCHEMA_REVISION),
        obs.FAMILY_TOLERANCE: IdentityRow(obs.FAMILY_TOLERANCE, "scalar-int", obs.TOLERANCE_FIELDS, obs.is_tolerance, VERSION_MEMBER_REVISION, obs.SCHEMA_REVISION),
    }),
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
