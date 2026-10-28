"""Effective-policy identity for contract `r08-v3` (docs/r08-v3-contract.md section 10).

`effective_policy_digest(family, effective)` is the domain-separated digest of one canonical preimage that binds ALL SEVEN members of
`f1abc-local-execution-limits` (the five allow-sets, `max_amount`, `max_effects`) together with the contract version and the family version, so no
subset can be replaced independently. It follows the `v2_policy_identity` pattern and REUSES that module's hostile-input boundary (`_plain`), canonical
serializer and digest helper (`_sha`), refusal type (`IdentityRefusal`) and the frozen f1ab validator for the five sets; it differs in exactly:
  * the digest domain `b"ocs-reg/r08-v3/effective-policy\\n"` (a v2 digest never equals a v3 digest of the same members);
  * the registered contract version is `r08-v3` only; `r08-v2` and `r08-v1` are `contract_unsupported` here, and `v2_policy_identity` still
    refuses this family `family_unsupported` (it is not edited);
  * the family row: `f1abc-local-execution-limits`, derived family version `v3`, kind `lists+ints` (the version tag is never an input).

Effective ranges: `max_amount` 0 ..= 2**53; `max_effects` 0 ..= 2**53 - 1 (0 is the deny-all: it appears in the preimage `deny_all` list). Exact `int`
only: bool, float, str, None, subclasses are `field_type_invalid`; out of range (including integer literals of 20 or more digits, which the loader
marks `OutOfRangeInteger`) is `field_invalid`.

Pure; non-authorizing; unqualified (BUILDER_TESTED). Nothing but `IdentityRefusal` escapes the public entry points.
"""
from types import MappingProxyType
from typing import Any

from registry_successor import v2_policy_identity as pid
from registry_successor import v3_f1abc as f
from registry_successor.v2_policy_identity import IdentityRefusal

CONTRACT_VERSION = "r08-v3"
EFFECTIVE_PROFILE = pid.EFFECTIVE_PROFILE
EFFECTIVE_PREFIX = b"ocs-reg/r08-v3/effective-policy\n"
FAMILY_VERSION = "v3"
IDENTITY_FAMILIES = MappingProxyType({f.FAMILY_F1ABC: pid.FamilyRow(f.FAMILY_F1ABC, FAMILY_VERSION, "lists+ints", f.F1ABC_FIELDS)})
REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)
RANGES = MappingProxyType({"max_amount": (f.AMOUNT_MIN, f.AMOUNT_MAX), "max_effects": (f.EFFECTS_MIN, f.EFFECTS_MAX)})

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
    """Strict validator of a composed (effective) or Registry-input seven-member payload; returns a private plain copy. Phases: family, shape
    (missing, unknown), types, values; sorted path order inside a phase."""
    if type(family) is not str:
        pid._type_refusal("family", family)
    if family not in IDENTITY_FAMILIES:
        pid._refuse("family_unsupported", "family")
    d = pid._plain(payload)
    if type(d) is not dict:
        pid._type_refusal(None, d)
    members = set(f.F1ABC_FIELDS)
    missing = members - set(d)
    if missing:
        pid._refuse("field_missing", min(missing))
    unknown = set(d) - members
    if unknown:
        pid._refuse("field_unknown", min(unknown))
    for path in sorted(d):
        v = d[path]
        if path in f.SET_FIELDS:
            if type(v) is not list or not all(type(x) is str for x in v):
                pid._type_refusal(path, v)
        elif not pid._int_typed(v):
            pid._type_refusal(path, v)
    pid.validate_effective_payload("f1ab-local-execution-allowlist", {k: d[k] for k in f.SET_FIELDS})  # the frozen five-set value rules, by import
    for path in f.CEILING_FIELDS:
        lo, hi = RANGES[path]
        if not pid._in_range(d[path], lo, hi):
            pid._range_refusal(path, lo, hi)
    return d


def _deny_all(plain_payload: dict) -> list:
    names = [k for k in f.SET_FIELDS if plain_payload[k] == []]
    if plain_payload["max_effects"] == 0:
        names.append("max_effects")
    return sorted(names)


def deny_all_dimensions(family: Any, payload: Any) -> list:
    """The sorted names of the deny-all dimensions (empty sets, and `max_effects` when 0) of a valid payload."""
    return _deny_all(validate_effective_payload(family, payload))


def effective_preimage(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> dict:
    """The digest preimage. `family_version` is derived from the module table; no parameter or payload member can supply it."""
    version = registered_family_version(family, contract_version)
    plain_payload = validate_effective_payload(family, payload)
    return {"effective_policy_profile": EFFECTIVE_PROFILE, "contract_version": contract_version, "family": family, "family_version": version,
            "deny_all": _deny_all(plain_payload), "effective": plain_payload}


def effective_digest_of_preimage(preimage: dict) -> str:
    return pid._sha(EFFECTIVE_PREFIX, preimage)


def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> str:
    return effective_digest_of_preimage(effective_preimage(family, payload, contract_version))
