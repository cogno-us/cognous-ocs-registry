"""Selection envelope parser and signing input of the parameterised engine (docs/r08-v7-contract.md section 3).

The statement shape is the `r08-v2` shape (the v1 statement plus `disposition` in {select, withdraw}; a withdrawal pins no record and no evaluator and
names its predecessor), as the frozen `v3_selection`..`v6_selection` parsers use it, with exactly three profile-specific differences:
  * the envelope must declare exactly `profile.version`;
  * the family is looked up in the PROFILE's table (`profile.lookup`);
  * the signing input is `profile.selection_signing_domain + canonical_bytes(statement)`, so a signature made over another contract's domain never
    verifies and the reverse.
No new reason code. Pure; authenticates nothing. Non-authorizing; unqualified.
"""
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import selection as s1
from registry_successor import v2_selection as s2
from registry_successor.engine import profile as p
from registry_successor.selection import SelectionResult

DISPOSITIONS = s2.DISPOSITIONS
STATEMENT_FIELDS = s2.STATEMENT_FIELDS_V2


def signing_input(profile: p.ContractProfile, statement: Any) -> bytes:
    return p.require_profile(profile).selection_signing_domain + c.canonical_bytes(statement)


def _no(code: str, detail: str = "") -> SelectionResult:
    assert code in c.CODES, code
    return SelectionResult(False, code, detail)


def statement_code(profile: p.ContractProfile, stmt: Any) -> Optional[str]:
    shape = c.exact_fields(stmt, STATEMENT_FIELDS)
    if shape:
        return shape
    disposition = stmt["disposition"]
    if type(disposition) is not str:
        return "field_type_invalid"
    if disposition not in DISPOSITIONS:
        return "field_invalid"
    if stmt["kind"] != "selection":
        return "kind_unsupported"
    spec = p.lookup(profile, stmt["family"])
    if spec is None:
        return "family_unsupported"
    for name in ("selection_id", "consumer_id", "operation", "revocation_ref", "selector_ref"):
        if not isinstance(stmt[name], str):
            return "field_type_invalid"
        if not c.valid_identifier(stmt[name]):
            return "field_invalid"
    if not c.is_int(stmt["epoch"]):
        return "field_type_invalid"
    if not s1._epoch_ok(stmt["epoch"]):
        return "field_invalid"
    if stmt["participation"] not in c.PARTICIPATION:
        return "field_invalid"
    for name, fields in (("scope", s1.SCOPE_FIELDS), ("effective", s1.EFFECTIVE_FIELDS)):
        shape = c.exact_fields(stmt[name], fields)
        if shape:
            return shape
    if not all(c.valid_token(stmt["scope"][f]) for f in s1.SCOPE_FIELDS):
        return "field_invalid"
    if disposition == "withdraw":
        if stmt["record"] is not None or stmt["evaluator"] is not None or stmt["supersedes"] is None:
            return "selection_supersession_invalid"
    else:
        for name, fields in (("record", s1.RECORD_PIN_FIELDS), ("evaluator", s1.EVALUATOR_FIELDS)):
            shape = c.exact_fields(stmt[name], fields)
            if shape:
                return shape
        pin = stmt["record"]
        if not (c.valid_identifier(pin["record_id"]) and c.is_int(pin["record_version"])
                and 1 <= pin["record_version"] <= c.MAX_INT and c.valid_sha_ref(pin["record_digest"])):
            return "field_invalid"
        ev = stmt["evaluator"]
        if (ev["evaluator_id"], ev["binding"]) != spec.evaluator_binding:
            return "evaluator_unsupported"
        if not (c.valid_hex40(ev["source_blob_id"]) and c.valid_sha_ref(ev["source_sha256"])):
            return "field_invalid"
    start = c.parse_timestamp(stmt["effective"]["valid_from"])
    end = c.parse_timestamp(stmt["effective"]["valid_until"])
    if start is None or end is None or not start < end:
        return "field_invalid"
    if c.parse_timestamp(stmt["issued_at"]) is None:
        return "field_invalid"
    return s1._supersedes_code(stmt)


def _parse(profile: p.ContractProfile, text: Any) -> SelectionResult:
    loaded = c.load_document(text)
    if not loaded.ok:
        return _no(loaded.code, loaded.detail)
    env = loaded.value
    shape = c.exact_fields(env, s1.ENVELOPE_FIELDS)
    if shape:
        return _no(shape, "envelope")
    version = env["contract_version"]
    if type(version) is not str or version != profile.version:
        return _no("contract_unsupported")
    if env["kind"] != "selection-envelope":
        return _no("kind_unsupported")
    code = statement_code(profile, env["statement"])
    if code:
        return _no(code, "statement")
    if not c.valid_sha_ref(env["statement_digest"]):
        return _no("field_invalid", "statement_digest")
    code = s1._signatures_code(env["signatures"])
    if code:
        return _no(code, "signatures")
    if c.digest(env["statement"]) != env["statement_digest"]:
        return _no("digest_mismatch", "statement_digest")
    return SelectionResult(True, None, "", env, env["statement"], env["statement_digest"], env["signatures"])


def parse_selection_envelope(profile: p.ContractProfile, text: Any) -> SelectionResult:
    """Parse and structurally validate a selection envelope of the profile's contract. Never raises (a non-profile is a programming error); never
    authenticates."""
    p.require_profile(profile)
    try:
        return _parse(profile, text)
    except Exception:  # defensive: never raise, never accept
        return _no("field_invalid", "internal")
