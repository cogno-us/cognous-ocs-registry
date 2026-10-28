"""Effective-policy identity for contract `r08-v5` (docs/r08-v5-contract.md section 6).

`effective_policy_digest(family, effective)` is the domain-separated digest of one canonical preimage that binds the ONE member of
`f4t-control-plane-clock-tolerance` (`clock_tolerance_seconds`) with the contract version and the family version. It follows the `v4_policy_identity`
pattern and REUSES `v2_policy_identity`'s hostile-input boundary (`_plain`), canonical serializer and digest helper (`_sha`) and refusal type; it differs in
the digest domain `b"ocs-reg/r08-v5/effective-policy\n"`, the registered contract version (`r08-v5` only) and the family row (derived family version `v5`).
Range 0 ..= 2147483647, exact `int`: wrong type `field_type_invalid`, out of range (including integer literals of 20 or more digits) `field_invalid`.
No deny-all dimension exists. Pure; non-authorizing; unqualified (BUILDER_TESTED). Nothing but `IdentityRefusal` escapes the public entry points.
"""
from types import MappingProxyType
from typing import Any

from registry_successor import v2_policy_identity as pid
from registry_successor import v5_f4t as f
from registry_successor.v2_policy_identity import IdentityRefusal

CONTRACT_VERSION = "r08-v5"
EFFECTIVE_PROFILE = pid.EFFECTIVE_PROFILE
EFFECTIVE_PREFIX = b"ocs-reg/r08-v5/effective-policy\n"
FAMILY_VERSION = "v5"
IDENTITY_FAMILIES = MappingProxyType({f.FAMILY_F4T: pid.FamilyRow(f.FAMILY_F4T, FAMILY_VERSION, "int", f.F4T_FIELDS)})
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
    """Strict validator of a composed (effective) or Registry-input one-member payload; returns a private plain copy. Phases: family, shape
    (missing, unknown), types, values; sorted path order inside a phase."""
    if type(family) is not str:
        pid._type_refusal("family", family)
    if family not in IDENTITY_FAMILIES:
        pid._refuse("family_unsupported", "family")
    d = pid._plain(payload)
    if type(d) is not dict:
        pid._type_refusal(None, d)
    members = set(f.F4T_FIELDS)
    missing = members - set(d)
    if missing:
        pid._refuse("field_missing", min(missing))
    unknown = set(d) - members
    if unknown:
        pid._refuse("field_unknown", min(unknown))
    if not pid._int_typed(d[f.FIELD]):
        pid._type_refusal(f.FIELD, d[f.FIELD])
    if not pid._in_range(d[f.FIELD], f.TOLERANCE_MIN, f.TOLERANCE_MAX):
        pid._range_refusal(f.FIELD, f.TOLERANCE_MIN, f.TOLERANCE_MAX)
    return d


def deny_all_dimensions(family: Any, payload: Any) -> list:
    """The sorted names of the deny-all dimensions (empty sets, and `max_effects` when 0) of a valid payload."""
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
