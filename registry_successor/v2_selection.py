"""r08-v2 selection envelope parser and signing input (docs/r08-v2-contract.md sections 1, 3 and 9; ADR EXT-S1-1 D-01, D-02).

S01 (plan v1.4 Amendment 1). DEVELOPER-TESTED only. Not independently qualified. Pure: no I/O, no clock, authenticates nothing.

What it adds to the frozen `r08-v1` parser (`selection.py`, unchanged):
  * the statement member `disposition` in {select, withdraw};
  * a `withdraw` pins no record and no evaluator, names its predecessor exactly in `supersedes` (same selection id, strictly lower
    epoch) and is therefore never an unsupersessing statement;
  * the `r08-v2` family table (`families.lookup_v2`);
  * the signing input `b"ocs-reg/r08-v2/selection\\n" + canonical_bytes(statement)`, so a v1 signature never verifies a v2 statement
    and the reverse.
Every other rule is the `r08-v1` rule. No new reason code is introduced; all codes below are existing `r08-v1` codes.
"""
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import families
from registry_successor import selection as s1
from registry_successor.selection import SelectionResult

V2_CONTRACT = "r08-v2"
SIGNING_DOMAIN_V2 = b"ocs-reg/r08-v2/selection\n"
DISPOSITIONS = ("select", "withdraw")
STATEMENT_FIELDS_V2 = s1.STATEMENT_FIELDS + ("disposition",)

__all__ = ["V2_CONTRACT", "SIGNING_DOMAIN_V2", "DISPOSITIONS", "STATEMENT_FIELDS_V2", "signing_input_v2", "parse_selection_envelope_v2"]


def signing_input_v2(statement: Any) -> bytes:
    return SIGNING_DOMAIN_V2 + c.canonical_bytes(statement)


def _no(code: str, detail: str = "") -> SelectionResult:
    assert code in c.CODES, code
    return SelectionResult(False, code, detail)


def _statement_code_v2(stmt: Any) -> Optional[str]:
    shape = c.exact_fields(stmt, STATEMENT_FIELDS_V2)
    if shape:
        return shape
    disposition = stmt["disposition"]
    if type(disposition) is not str:
        return "field_type_invalid"
    if disposition not in DISPOSITIONS:
        return "field_invalid"
    if stmt["kind"] != "selection":
        return "kind_unsupported"
    spec = families.lookup_v2(stmt["family"])
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
        # A withdrawal pins no record and no evaluator and must name its predecessor exactly (contract section 3).
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
    if type(version) is not str or version != V2_CONTRACT:
        return _no("contract_unsupported")
    if env["kind"] != "selection-envelope":
        return _no("kind_unsupported")
    code = _statement_code_v2(env["statement"])
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


def parse_selection_envelope_v2(text: Any) -> SelectionResult:
    """Parse and structurally validate an `r08-v2` selection envelope. Never raises; never authenticates."""
    try:
        return _parse(text)
    except Exception:  # defensive: never raise, never accept
        return _no("field_invalid", "internal")
