"""`ContractProfile`: the immutable description of one contract version for the parameterised engine (docs/r08-v7-contract.md section 3).

A profile is DATA, never behaviour: a version string, the two version-specific domain-separation prefixes, a closed table of typed families (each a
`families.FamilySpec` with its own payload validator, caller normalizer and composer, plus an optional `schema_revision`) and one identity row per
family. There is no general policy interpreter, no executable rule and no mutable global: the tables are `MappingProxyType` views over private copies
made at construction, and the profile is a frozen dataclass of exact types, validated once in `__post_init__`.

The envelope protocol version (`version`) is separate from a family's schema revision (`FamilyEntry.schema_revision`, an int). A profile whose identity
rows use the member `family_schema_revision` must carry exactly that revision in each row (checked at construction); a compatibility profile whose rows
use the legacy `family_version` string tag (the frozen `r08-v6`) carries no revision.

The module-level helpers (`lookup`, `table_for_contract_version`, `compose`, `compose_for`) are the table dispatch of `v6_families` as functions of a
profile. Pure; no I/O, clock or state. Non-authorizing; unqualified.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Optional

from registry_successor import common as c
from registry_successor.compose import CompositionResult
from registry_successor.families import FamilySpec, TableSelection

VERSION_MEMBER_TAG = "family_version"  # legacy string tag member (frozen r08-v2..r08-v6 preimages)
VERSION_MEMBER_REVISION = "family_schema_revision"  # integer schema revision member (r08-v7 onward)
KINDS = ("classmap-enum", "scalar-enum", "scalar-int")  # scalar-int: one strict int value (r08-v8, additive)


@dataclass(frozen=True)
class FamilyEntry:
    spec: FamilySpec
    schema_revision: Optional[int]  # None only for a legacy-tag profile


@dataclass(frozen=True)
class IdentityRow:
    family: str
    kind: str  # classmap-enum (map of class -> value) | scalar-enum (one scalar str value) | scalar-int (one strict int value)
    members: tuple  # the payload member names, exactly one
    is_value: Callable[[Any], bool]  # the closed value vocabulary of the family
    version_member: str  # VERSION_MEMBER_TAG | VERSION_MEMBER_REVISION
    version_value: Any  # the tag (str) or the revision (int) written under version_member


def _fail(message: str):
    raise ValueError("invalid ContractProfile: " + message)


@dataclass(frozen=True)
class ContractProfile:
    version: str
    selection_signing_domain: bytes
    effective_policy_domain: bytes
    families: Mapping  # family id -> FamilyEntry (immutable view, insertion order = table order)
    identity: Mapping  # family id -> IdentityRow (immutable view, same keys as families)

    def __post_init__(self):
        if type(self.version) is not str or not c.valid_token(self.version):
            _fail("version")
        for name, prefix in (("selection_signing_domain", self.selection_signing_domain), ("effective_policy_domain", self.effective_policy_domain)):
            if type(prefix) is not bytes or not prefix.endswith(b"\n") or ("/" + self.version + "/").encode("ascii") not in prefix:
                _fail(name)
        if self.selection_signing_domain == self.effective_policy_domain:
            _fail("domains must differ")
        fam, ident = self.families, self.identity
        if not isinstance(fam, Mapping) or not isinstance(ident, Mapping) or not fam or list(fam) != list(ident):
            _fail("families and identity rows must be non-empty with the same keys in the same order")
        families, rows = {}, {}
        for key in fam:
            entry, row = fam[key], ident[key]
            if type(key) is not str or type(entry) is not FamilyEntry or type(entry.spec) is not FamilySpec or entry.spec.family != key:
                _fail("family entry " + repr(key))
            if type(row) is not IdentityRow or row.family != key or row.kind not in KINDS or type(row.members) is not tuple or len(row.members) != 1 \
                    or tuple(entry.spec.payload_fields) != row.members or not callable(row.is_value):
                _fail("identity row " + repr(key))
            if row.version_member == VERSION_MEMBER_REVISION:
                if type(entry.schema_revision) is not int or entry.schema_revision < 1 or type(row.version_value) is not int \
                        or row.version_value != entry.schema_revision:
                    _fail("schema revision of " + key)
            elif row.version_member == VERSION_MEMBER_TAG:
                if entry.schema_revision is not None or type(row.version_value) is not str or not row.version_value:
                    _fail("family version tag of " + key)
            else:
                _fail("version member of " + key)
            families[key], rows[key] = entry, row
        object.__setattr__(self, "families", MappingProxyType(families))
        object.__setattr__(self, "identity", MappingProxyType(rows))

    @property
    def specs(self) -> Mapping:
        """family id -> `FamilySpec`, an immutable view in table order."""
        return MappingProxyType({k: e.spec for k, e in self.families.items()})


def require_profile(profile: Any) -> ContractProfile:
    """The engine accepts exactly a `ContractProfile` (a programming error otherwise, never a hostile-input path)."""
    if type(profile) is not ContractProfile:
        raise TypeError("the engine requires a ContractProfile")
    return profile


def lookup(profile: ContractProfile, family: Any) -> Optional[FamilySpec]:
    """The registered spec for exactly this family string in the profile's table, or None. Never raises on hostile `family`."""
    if type(family) is not str:
        return None
    try:
        entry = profile.families.get(family)
    except TypeError:
        return None
    return None if entry is None else entry.spec


def table_for_contract_version(profile: ContractProfile, version: Any) -> TableSelection:
    """Select the table for exactly the profile's version. Any other value (a str subclass, another case or whitespace, a non-str, another contract)
    refuses `contract_unsupported` with no table: no fallback, no implicit upgrade, no default."""
    if type(version) is str and version == profile.version:
        return TableSelection(True, None, profile.version, profile.specs)
    return TableSelection(False, "contract_unsupported", None, None)


def _refuse(code: str, detail: str = "") -> CompositionResult:
    assert code in c.CODES, code
    return CompositionResult(False, code, detail)


def compose(profile: ContractProfile, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Dispatch composition on the validated record's family in the profile's table. Check order: operator, record validity, family registration, then
    the family composer. Any refusal returns no effective policy."""
    try:
        if type(operator) is not str or operator != "intersection":
            return _refuse("composition_operator_unsupported")
        if getattr(record, "ok", False) is not True:
            return _refuse("composition_record_invalid")
        body = getattr(record, "record", None)
        if not isinstance(body, Mapping):
            return _refuse("composition_record_invalid")
        spec = lookup(profile, body.get("family"))
        if spec is None:
            return _refuse("composition_family_unsupported")
        return spec.composer(caller, record, operator)
    except Exception:
        return _refuse("composition_record_invalid", "unexpected input")


def compose_for(profile: ContractProfile, version: Any, caller: Any, record: Any, operator: Any = "intersection") -> CompositionResult:
    """Compose with the table of exactly `version`; anything but the profile's version refuses `contract_unsupported` (no policy)."""
    if not table_for_contract_version(profile, version).ok:
        return _refuse("contract_unsupported")
    return compose(profile, caller, record, operator)
