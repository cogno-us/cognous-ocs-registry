"""Effective-policy identity for contract `r08-v8` (docs/r08-v8-contract.md section 6). A thin public binding of the engine to the `V8` profile.

`effective_policy_digest(family, effective, contract_version="r08-v8")` is the domain-separated digest (`b"ocs-reg/r08-v8/effective-policy\\n"`) of one
canonical preimage `{effective_policy_profile, contract_version, family, family_schema_revision (int), deny_all [], effective}`. The family schema
revision is read from the profile's table (never an input) and is part of the preimage. The two ObservationPolicy families use the additive `scalar-int` identity kind. Reuses the `v2_policy_identity` boundary and `IdentityRefusal`.
"""
from types import MappingProxyType
from typing import Any

from registry_successor.engine import identity as _id
from registry_successor.engine import profiles as _profiles
from registry_successor.v2_policy_identity import IdentityRefusal

CONTRACT_VERSION = _profiles.CONTRACT_V8
EFFECTIVE_PROFILE = _id.EFFECTIVE_PROFILE
EFFECTIVE_PREFIX = _profiles.V8.effective_policy_domain
IDENTITY_FAMILIES = _profiles.V8.identity
REGISTERED_CONTRACT_VERSIONS = (CONTRACT_VERSION,)

__all__ = ["IdentityRefusal", "CONTRACT_VERSION", "EFFECTIVE_PREFIX", "IDENTITY_FAMILIES", "registered_family_version", "validate_effective_payload",
           "effective_preimage", "effective_digest_of_preimage", "effective_policy_digest", "deny_all_dimensions"]


def registered_family_version(family: Any, contract_version: Any) -> int:
    """The family schema revision (an int) of a registered family under exactly `r08-v8`."""
    return _id.registered_family_version(_profiles.V8, family, contract_version)


def validate_effective_payload(family: Any, payload: Any) -> dict:
    return _id.validate_effective_payload(_profiles.V8, family, payload)


def deny_all_dimensions(family: Any, payload: Any) -> list:
    return _id.deny_all_dimensions(_profiles.V8, family, payload)


def effective_preimage(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> dict:
    return _id.effective_preimage(_profiles.V8, family, payload, contract_version)


def effective_digest_of_preimage(preimage: dict) -> str:
    return _id.effective_digest_of_preimage(_profiles.V8, preimage)


def effective_policy_digest(family: Any, payload: Any, contract_version: Any = CONTRACT_VERSION) -> str:
    return _id.effective_policy_digest(_profiles.V8, family, payload, contract_version)
