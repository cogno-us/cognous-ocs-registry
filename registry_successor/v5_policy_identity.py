"""Effective-policy identity for contract `r08-v5` (docs/r08-v5-contract.md section 6).

`effective_policy_digest(family, effective)` is the domain-separated digest of one canonical preimage that binds the whole `class_on_unreadable` map of
`f5-action-class-unreadable-policy` (every class and its value) together with the contract version and the family version, so no class can be replaced
independently. It follows the `v2_policy_identity` / `v4_policy_identity` pattern and REUSES the `v2_policy_identity` hostile-input boundary (`_plain`),
canonical serializer and digest helper (`_sha`) and refusal type (`IdentityRefusal`); it differs in exactly:
  * the digest domain `b"ocs-reg/r08-v5/effective-policy\\n"` (a v2 or v4 digest never equals a v5 digest of the same members);
  * the registered contract version is `r08-v5` only; `r08-v4`, `r08-v3`, `r08-v2` and `r08-v1` are `contract_unsupported` here, and `v2_policy_identity`,
    `v3_policy_identity` and `v4_policy_identity` still refuse this family `family_unsupported` (none is edited);
  * the family row: `f5-action-class-unreadable-policy`, derived family version `v5`, kind `classmap-enum` (the version tag is never an input).

Values: exact `str` in `refuse|bounded_tolerance` (a non-str is `field_type_invalid`, any other string `field_invalid`); class keys: frozen tokens,
non-empty, at most MAX_LIST_ENTRIES (order is canonicalized by the digest serializer, as in `v2_policy_identity`). `refuse` is a value, not a deny-all dimension, so `deny_all` is always `[]` in the preimage.

Pure; non-authorizing; unqualified (BUILDER_TESTED). Nothing but `IdentityRefusal` escapes the public entry points.
"""
from types import MappingProxyType
from typing import Any

from registry_successor import v2_policy_identity as pid
from registry_successor import v5_class_unreadable as f
from registry_successor.v2_policy_identity import IdentityRefusal

CONTRACT_VERSION = "r08-v5"
EFFECTIVE_PROFILE = pid.EFFECTIVE_PROFILE
EFFECTIVE_PREFIX = b"ocs-reg/r08-v5/effective-policy\n"
FAMILY_VERSION = "v5"
IDENTITY_FAMILIES = MappingProxyType({f.FAMILY_F5U: pid.FamilyRow(f.FAMILY_F5U, FAMILY_VERSION, "classmap-enum", f.F5U_FIELDS)})
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
    d = pid._plain(payload)
    if type(d) is not dict:
        pid._type_refusal(None, d)
    members = set(f.F5U_FIELDS)
    missing = members - set(d)
    if missing:
        pid._refuse("field_missing", min(missing))
    unknown = set(d) - members
    if unknown:
        pid._refuse("field_unknown", min(unknown))
    classes = d[f.F5U_FIELD]
    if type(classes) is not dict:
        pid._type_refusal(f.F5U_FIELD, classes)
    for cls in sorted(classes):
        if type(classes[cls]) is not str:
            pid._type_refusal(f.F5U_FIELD + "." + cls, classes[cls])
    if not classes or len(classes) > pid.MAX_LIST_ENTRIES or not all(pid.frozen_token_valid(k) for k in classes):
        pid._refuse("field_invalid", f.F5U_FIELD)
    for cls in sorted(classes):
        if not f.is_value(classes[cls]):
            pid._refuse("field_invalid", f.F5U_FIELD + "." + cls)
    return d


def deny_all_dimensions(family: Any, payload: Any) -> list:
    """`[]` always (a `refuse` value is not a deny-all dimension) for a valid payload; the same refusals as every other entry point otherwise."""
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
