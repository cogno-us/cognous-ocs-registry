"""Effective-policy identity for contract `r08-v6` (docs/r08-v6-contract.md section 6).

`effective_policy_digest(family, effective, contract_version="r08-v6")` is the domain-separated digest of one canonical preimage that binds the whole
effective payload of one of the two `r08-v6` families together with the contract version and the family version (`v6` for both), so no class and no value
can be replaced independently. It follows the `v2_policy_identity` / `v5_policy_identity` pattern and REUSES the `v2_policy_identity` hostile-input
boundary (`_plain`), canonical serializer and digest helper (`_sha`) and refusal type (`IdentityRefusal`); it differs in exactly:
  * the digest domain `b"ocs-reg/r08-v6/effective-policy\\n"` (a v2..v5 digest never equals a v6 digest of the same members);
  * the registered contract version is `r08-v6` only; `r08-v5`..`r08-v1` are `contract_unsupported` here, and `v2_policy_identity`..`v5_policy_identity`
    still refuse these families `family_unsupported` (none is edited);
  * the two family rows: `f5-action-class-revocation-assurance-policy` (kind `classmap-enum`: a class map of `required|not_required`) and
    `f5-terminal-revocation-enablement-policy` (kind `scalar-enum`: one scalar `off|on`); the derived family version `v6` is never an input.

Neither family is a deny-all dimension, so `deny_all` is always `[]` in the preimage. Pure; non-authorizing; unqualified (BUILDER_TESTED). Nothing but
`IdentityRefusal` escapes the public entry points.
"""
from types import MappingProxyType
from typing import Any

from registry_successor import v2_policy_identity as pid
from registry_successor import v6_class_revocation_assurance as ra
from registry_successor import v6_terminal_revocation as tr
from registry_successor.v2_policy_identity import IdentityRefusal

CONTRACT_VERSION = "r08-v6"
EFFECTIVE_PROFILE = pid.EFFECTIVE_PROFILE
EFFECTIVE_PREFIX = b"ocs-reg/r08-v6/effective-policy\n"
FAMILY_VERSION = "v6"
IDENTITY_FAMILIES = MappingProxyType({
    ra.FAMILY_F5RA: pid.FamilyRow(ra.FAMILY_F5RA, FAMILY_VERSION, "classmap-enum", ra.F5RA_FIELDS),
    tr.FAMILY_TR: pid.FamilyRow(tr.FAMILY_TR, FAMILY_VERSION, "scalar-enum", tr.TR_FIELDS),
})
REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)

__all__ = ["IdentityRefusal", "CONTRACT_VERSION", "EFFECTIVE_PREFIX", "IDENTITY_FAMILIES", "registered_family_version", "validate_effective_payload",
           "effective_preimage", "effective_digest_of_preimage", "effective_policy_digest", "deny_all_dimensions"]


def registered_family_version(family: Any, contract_version: Any) -> str:
    if type(family) is not str:
        pid._type_refusal("family", family)
    if type(contract_version) is not str:
        pid._type_refusal("contract_version", contract_version)
    if family not in IDENTITY_FAMILIES:
        pid._refuse("family_unsupported", "family")
    if contract_version not in REGISTERED_CONTRACT_VERSIONS:
        pid._refuse("contract_unsupported", "contract_version")
    return IDENTITY_FAMILIES[family].family_version


def validate_effective_payload(family: Any, payload: Any) -> dict:
    """Strict validator of a composed (effective) or Registry-input payload; returns a private plain copy. Phases: family, shape (missing, unknown),
    types, values; sorted path order inside a phase."""
    if type(family) is not str:
        pid._type_refusal("family", family)
    if family not in IDENTITY_FAMILIES:
        pid._refuse("family_unsupported", "family")
    row = IDENTITY_FAMILIES[family]
    d = pid._plain(payload)
    if type(d) is not dict:
        pid._type_refusal(None, d)
    members = set(row.members)
    missing = members - set(d)
    if missing:
        pid._refuse("field_missing", min(missing))
    unknown = set(d) - members
    if unknown:
        pid._refuse("field_unknown", min(unknown))
    field = row.members[0]
    value = d[field]
    if row.kind == "classmap-enum":
        if type(value) is not dict:
            pid._type_refusal(field, value)
        for cls in sorted(value):
            if type(value[cls]) is not str:
                pid._type_refusal(field + "." + cls, value[cls])
        if not value or len(value) > pid.MAX_LIST_ENTRIES or not all(pid.frozen_token_valid(k) for k in value):
            pid._refuse("field_invalid", field)
        for cls in sorted(value):
            if not ra.is_value(value[cls]):
                pid._refuse("field_invalid", field + "." + cls)
    else:  # scalar-enum
        if type(value) is not str:
            pid._type_refusal(field, value)
        if not tr.is_value(value):
            pid._refuse("field_invalid", field)
    return d


def deny_all_dimensions(family: Any, payload: Any) -> list:
    """`[]` always (neither family is a deny-all dimension) for a valid payload; the same refusals as every other entry point otherwise."""
    validate_effective_payload(family, payload)
    return []


def effective_preimage(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> dict:
    """The digest preimage. `family_version` is derived from the module table; no parameter or payload member can supply it."""
    version = registered_family_version(family, contract_version)
    plain_payload = validate_effective_payload(family, payload)
    return {"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": contract_version, "family": family, "family_version": version,
            "deny_all": [], "effective": plain_payload}


def effective_digest_of_preimage(preimage: dict) -> str:
    return pid._sha(EFFECTIVE_PREFIX, preimage)


def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> str:
    return effective_digest_of_preimage(effective_preimage(family, payload, contract_version))
