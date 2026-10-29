"""Effective-policy identity of the parameterised engine (docs/r08-v7-contract.md section 6).

`effective_policy_digest(profile, family, effective, contract_version)` is the domain-separated digest of one canonical preimage that binds the whole
effective payload of one family of the profile together with the contract version and the family's version member, so no class and no value can be
replaced independently. It REUSES the `v2_policy_identity` hostile-input boundary (`_plain`), canonical serializer and digest helper (`_sha`) and refusal
type (`IdentityRefusal`), and follows the `v6_policy_identity` pattern exactly, differing only through the profile:
  * the digest domain is `profile.effective_policy_domain`;
  * the registered contract version is `profile.version` only; every other contract version is `contract_unsupported`;
  * the preimage carries ONE version member per family row: the legacy string tag `family_version` (the frozen `r08-v6`) or the integer
    `family_schema_revision` (`r08-v7` onward). The value is read from the profile's table; no parameter or payload member can supply it.

Pure; non-authorizing; unqualified. Nothing but `IdentityRefusal` escapes the entry points for a hostile family, payload or contract version.
"""
from typing import Any

from registry_successor import v2_policy_identity as pid
from registry_successor.engine import profile as p
from registry_successor.v2_policy_identity import IdentityRefusal

EFFECTIVE_PROFILE = pid.EFFECTIVE_PROFILE
DEFAULT = object()  # sentinel: the contract version defaults to the profile's own (a caller-supplied None is a type refusal, as in the frozen modules)


def _row(profile: p.ContractProfile, family: Any) -> p.IdentityRow:
    if type(family) is not str:
        pid._type_refusal("family", family)
    if family not in profile.identity:
        pid._refuse("family_unsupported", "family")
    return profile.identity[family]


def registered_family_version(profile: p.ContractProfile, family: Any, contract_version: Any) -> Any:
    """The family's version value (tag or schema revision) after the family and contract-version checks (type, then family, then contract)."""
    p.require_profile(profile)
    if type(family) is not str:
        pid._type_refusal("family", family)
    if type(contract_version) is not str:
        pid._type_refusal("contract_version", contract_version)
    row = _row(profile, family)
    if contract_version != profile.version:
        pid._refuse("contract_unsupported", "contract_version")
    return row.version_value


def validate_effective_payload(profile: p.ContractProfile, family: Any, payload: Any) -> dict:
    """Strict validator of a composed (effective) or Registry-input payload; returns a private plain copy. Phases: family, shape (missing, unknown),
    types, values; sorted path order inside a phase."""
    p.require_profile(profile)
    row = _row(profile, family)
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
            if not row.is_value(value[cls]):
                pid._refuse("field_invalid", field + "." + cls)
    elif row.kind == "scalar-int":  # additive (r08-v8): one strict int; bool, float, str and subclasses are type refusals
        if type(value) is not int:
            pid._type_refusal(field, value)
        if not row.is_value(value):
            pid._refuse("field_invalid", field)
    else:  # scalar-enum
        if type(value) is not str:
            pid._type_refusal(field, value)
        if not row.is_value(value):
            pid._refuse("field_invalid", field)
    return d


def deny_all_dimensions(profile: p.ContractProfile, family: Any, payload: Any) -> list:
    """`[]` always (no engine family is a deny-all dimension) for a valid payload; the same refusals as every other entry point otherwise."""
    validate_effective_payload(profile, family, payload)
    return []


def effective_preimage(profile: p.ContractProfile, family: Any, payload: Any, contract_version: Any = DEFAULT) -> dict:
    """The digest preimage. The version member is derived from the profile's identity row; no parameter or payload member can supply it."""
    p.require_profile(profile)
    if contract_version is DEFAULT:
        contract_version = profile.version
    version_value = registered_family_version(profile, family, contract_version)
    plain_payload = validate_effective_payload(profile, family, payload)
    return {"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": contract_version, "family": family,
            profile.identity[family].version_member: version_value, "deny_all": [], "effective": plain_payload}


def effective_digest_of_preimage(profile: p.ContractProfile, preimage: dict) -> str:
    return pid._sha(p.require_profile(profile).effective_policy_domain, preimage)


def effective_policy_digest(profile: p.ContractProfile, family: Any, payload: Any, contract_version: Any = DEFAULT) -> str:
    return effective_digest_of_preimage(profile, effective_preimage(profile, family, payload, contract_version))
