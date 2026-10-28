"""`r08-v4` selection envelope parser and signing input (docs/r08-v4-contract.md).

The statement shape is the `r08-v2` shape (the v1 statement plus `disposition` in {select, withdraw}; a withdrawal pins no record and no evaluator
and names its predecessor), with three version-specific differences:
  * the envelope must declare exactly `r08-v4`;
  * the family is looked up in the `r08-v4` table (`v4_families.lookup_v4`);
  * the signing input is `b"ocs-reg/r08-v4/selection\\n" + canonical_bytes(statement)`, so a v1 or v2 signature never verifies a v4 statement and the
    reverse.
No new reason code. Pure; authenticates nothing. Non-authorizing; unqualified.
"""
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import selection as s1
from registry_successor import v4_families
from registry_successor import v2_selection as s2
from registry_successor.selection import SelectionResult

V4_CONTRACT = "r08-v4"
SIGNING_DOMAIN_V4 = b"ocs-reg/r08-v4/selection\n"
DISPOSITIONS = s2.DISPOSITIONS
STATEMENT_FIELDS_V4 = s2.STATEMENT_FIELDS_V2

__all__ = ["V4_CONTRACT", "SIGNING_DOMAIN_V4", "DISPOSITIONS", "STATEMENT_FIELDS_V4", "signing_input_v4", "parse_selection_envelope_v4"]


def signing_input_v4(statement: Any) -> bytes:
    return SIGNING_DOMAIN_V4 + c.canonical_bytes(statement)


def _no(code: str, detail: str = "") -> SelectionResult:
    assert code in c.CODES, code
    return SelectionResult(False, code, detail)


def _statement_code_v4(stmt: Any) -> Optional[str]:
    shape = c.exact_fields(stmt, STATEMENT_FIELDS_V4)
    if shape:
        return shape
    disposition = stmt["disposition"]
    if type(disposition) is not str:
        return "field_type_invalid"
    if disposition not in DISPOSITIONS:
        return "field_invalid"
    if stmt["kind"] != "selection":
        return "kind_unsupported"
    spec = v4_families.lookup_v4(stmt["family"])
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


def _parse(text: Any) -> SelectionResult:
    loaded = c.load_document(text)
    if not loaded.ok:
        return _no(loaded.code, loaded.detail)
    env = loaded.value
    shape = c.exact_fields(env, s1.ENVELOPE_FIELDS)
    if shape:
        return _no(shape, "envelope")
    version = env["contract_version"]
    if type(version) is not str or version != V4_CONTRACT:
        return _no("contract_unsupported")
    if env["kind"] != "selection-envelope":
        return _no("kind_unsupported")
    code = _statement_code_v4(env["statement"])
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


def parse_selection_envelope_v4(text: Any) -> SelectionResult:
    """Parse and structurally validate an `r08-v4` selection envelope. Never raises; never authenticates."""
    try:
        return _parse(text)
    except Exception:  # defensive: never raise, never accept
        return _no("field_invalid", "internal")
