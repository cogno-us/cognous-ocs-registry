"""Selection envelope structure, signing input and effective-selection resolution for contract `r08-v1`.

Spec: docs/r08-s01-contract.md section 3. Non-authorizing and unqualified. Pure: no I/O, no clock (time is injected).
Structural validity only: this module authenticates nothing. An epoch is not authorization and is never used to choose
between selections; supersession needs an explicit, exactly matching reference with a decision reference.
"""
import datetime
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from registry_successor import common as c

ENVELOPE_FIELDS = ("contract_version", "kind", "statement", "statement_digest", "signatures")
STATEMENT_FIELDS = (
    "kind", "selection_id", "epoch", "consumer_id", "scope", "operation", "participation", "family", "record",
    "evaluator", "effective", "supersedes", "revocation_ref", "selector_ref", "issued_at",
)
SCOPE_FIELDS = ("tenant", "institution", "authority_domain")
RECORD_PIN_FIELDS = ("record_id", "record_version", "record_digest")
EVALUATOR_FIELDS = ("evaluator_id", "binding", "source_blob_id", "source_sha256")
EFFECTIVE_FIELDS = ("valid_from", "valid_until")
SUPERSEDES_FIELDS = ("selection_id", "epoch", "statement_digest", "decision_ref")
SIGNATURE_FIELDS = ("alg", "key_id", "signature")
MAX_SIGNATURES = 8
MAX_SIGNATURE_CHARS = 1024
SIGNING_DOMAIN = b"ocs-reg/r08-v1/selection\n"


@dataclass(frozen=True)
class SelectionResult:
    ok: bool
    code: Optional[str] = None
    detail: str = ""
    envelope: Any = None
    statement: Any = None
    statement_digest: Optional[str] = None
    signatures: Any = None


@dataclass(frozen=True)
class ConflictResult:
    ok: bool
    code: Optional[str] = None
    detail: str = ""
    selected: Optional[SelectionResult] = None


def _no(code: str, detail: str = "") -> SelectionResult:
    assert code in c.CODES, code
    return SelectionResult(False, code, detail)


def signing_input(statement: Any) -> bytes:
    return SIGNING_DOMAIN + c.canonical_bytes(statement)


def _epoch_ok(value: Any) -> bool:
    return c.is_int(value) and 1 <= value <= c.MAX_INT


def _supersedes_code(stmt: dict) -> Optional[str]:
    sup = stmt["supersedes"]
    if sup is None:
        return None
    bad = "selection_supersession_invalid"
    if not isinstance(sup, dict) or set(sup) != set(SUPERSEDES_FIELDS):
        return bad
    if not (c.valid_identifier(sup["selection_id"]) and _epoch_ok(sup["epoch"])
            and c.valid_sha_ref(sup["statement_digest"]) and c.valid_identifier(sup["decision_ref"])):
        return bad
    if sup["selection_id"] != stmt["selection_id"] or sup["epoch"] >= stmt["epoch"]:
        return bad
    return None


def _statement_code(stmt: Any) -> Optional[str]:
    shape = c.exact_fields(stmt, STATEMENT_FIELDS)
    if shape:
        return shape
    if stmt["kind"] != "selection":
        return "kind_unsupported"
    if stmt["family"] != c.FAMILY_F1A:
        return "family_unsupported"
    for name in ("selection_id", "consumer_id", "operation", "revocation_ref", "selector_ref"):
        if not isinstance(stmt[name], str):
            return "field_type_invalid"
        if not c.valid_identifier(stmt[name]):
            return "field_invalid"
    if not c.is_int(stmt["epoch"]):
        return "field_type_invalid"
    if not _epoch_ok(stmt["epoch"]):
        return "field_invalid"
    if stmt["participation"] not in c.PARTICIPATION:
        return "field_invalid"
    for name, fields in (("scope", SCOPE_FIELDS), ("record", RECORD_PIN_FIELDS), ("evaluator", EVALUATOR_FIELDS),
                         ("effective", EFFECTIVE_FIELDS)):
        shape = c.exact_fields(stmt[name], fields)
        if shape:
            return shape
    if not all(c.valid_token(stmt["scope"][f]) for f in SCOPE_FIELDS):
        return "field_invalid"
    pin = stmt["record"]
    if not (c.valid_identifier(pin["record_id"]) and c.is_int(pin["record_version"])
            and 1 <= pin["record_version"] <= c.MAX_INT and c.valid_sha_ref(pin["record_digest"])):
        return "field_invalid"
    ev = stmt["evaluator"]
    if ev["evaluator_id"] != c.EVALUATOR_ID or ev["binding"] != c.EVALUATOR_BINDING:
        return "evaluator_unsupported"
    if not (c.valid_hex40(ev["source_blob_id"]) and c.valid_sha_ref(ev["source_sha256"])):
        return "field_invalid"
    start = c.parse_timestamp(stmt["effective"]["valid_from"])
    end = c.parse_timestamp(stmt["effective"]["valid_until"])
    if start is None or end is None or not start < end:
        return "field_invalid"
    if c.parse_timestamp(stmt["issued_at"]) is None:
        return "field_invalid"
    return _supersedes_code(stmt)


def _signatures_code(sigs: Any) -> Optional[str]:
    if not isinstance(sigs, list):
        return "field_type_invalid"
    if len(sigs) > MAX_SIGNATURES:
        return "field_invalid"
    for item in sigs:
        shape = c.exact_fields(item, SIGNATURE_FIELDS)
        if shape:
            return shape
        if not all(isinstance(item[f], str) for f in SIGNATURE_FIELDS):
            return "field_type_invalid"
        if not (c.valid_token(item["alg"]) and c.valid_identifier(item["key_id"])
                and 1 <= len(item["signature"]) <= MAX_SIGNATURE_CHARS):
            return "field_invalid"
    return None


def _parse(text: Any) -> SelectionResult:
    loaded = c.load_document(text)
    if not loaded.ok:
        return _no(loaded.code, loaded.detail)
    env = loaded.value
    shape = c.exact_fields(env, ENVELOPE_FIELDS)
    if shape:
        return _no(shape, "envelope")
    if env["contract_version"] != c.CONTRACT_VERSION:
        return _no("contract_unsupported")
    if env["kind"] != "selection-envelope":
        return _no("kind_unsupported")
    code = _statement_code(env["statement"])
    if code:
        return _no(code, "statement")
    if not c.valid_sha_ref(env["statement_digest"]):
        return _no("field_invalid", "statement_digest")
    code = _signatures_code(env["signatures"])
    if code:
        return _no(code, "signatures")
    if c.digest(env["statement"]) != env["statement_digest"]:
        return _no("digest_mismatch", "statement_digest")
    return SelectionResult(True, None, "", env, env["statement"], env["statement_digest"], env["signatures"])


def parse_selection_envelope(text: Any) -> SelectionResult:
    try:
        return _parse(text)
    except Exception:  # defensive: never raise, never accept
        return _no("field_invalid", "internal")


def _matches(stmt: dict, ctx: c.ExpectedContext) -> bool:
    scope = stmt["scope"]
    return (stmt["consumer_id"] == ctx.consumer_id and stmt["operation"] == ctx.operation
            and scope["tenant"] == ctx.tenant and scope["institution"] == ctx.institution
            and scope["authority_domain"] == ctx.authority_domain)


def _in_window(stmt: dict, now: datetime.datetime) -> bool:
    start = c.parse_timestamp(stmt["effective"]["valid_from"])
    end = c.parse_timestamp(stmt["effective"]["valid_until"])
    return start is not None and end is not None and start <= now < end


def _chain_covers(head: SelectionResult, by_key: dict, everyone: set) -> bool:
    seen = {head.statement_digest}
    node = head
    while node.statement["supersedes"] is not None:
        sup = node.statement["supersedes"]
        older = by_key.get((sup["selection_id"], sup["epoch"], sup["statement_digest"]))
        if older is None or older.statement_digest in seen:
            break
        seen.add(older.statement_digest)
        node = older
    return seen == everyone


def _resolve(selections: Any, context: Any, now: Any) -> ConflictResult:
    if not isinstance(now, datetime.datetime) or now.tzinfo is None or now.utcoffset() != datetime.timedelta(0):
        return ConflictResult(False, "time_unavailable", "now must be an aware UTC datetime")
    if not isinstance(context, c.ExpectedContext) or not isinstance(selections, (list, tuple)):
        return ConflictResult(False, "selection_missing", "no usable context or selections")
    unique: dict = {}
    for sel in selections:
        if not isinstance(sel, SelectionResult) or not sel.ok or not isinstance(sel.statement, dict):
            continue
        if _matches(sel.statement, context) and _in_window(sel.statement, now):
            unique.setdefault(sel.statement_digest, sel)
    if not unique:
        return ConflictResult(False, "selection_missing", "no effective selection for this context")
    cands = list(unique.values())
    if len(cands) == 1:
        return ConflictResult(True, None, "", cands[0])
    by_key = {(s.statement["selection_id"], s.statement["epoch"], s.statement_digest): s for s in cands}
    ids_epochs = [(s.statement["selection_id"], s.statement["epoch"]) for s in cands]
    if len(set(ids_epochs)) != len(ids_epochs):
        return ConflictResult(False, "selection_conflict", "same selection id and epoch with different content")
    everyone = {s.statement_digest for s in cands}
    heads = [s for s in cands if _chain_covers(s, by_key, everyone)]
    if len(heads) == 1:
        return ConflictResult(True, None, "", heads[0])
    return ConflictResult(False, "selection_conflict", "effective selections without an explicit supersession chain")


def resolve_effective(selections: Sequence[SelectionResult], context: c.ExpectedContext,
                      now: Optional[datetime.datetime]) -> ConflictResult:
    try:
        return _resolve(selections, context, now)
    except Exception:  # defensive: never raise, never select
        return ConflictResult(False, "selection_conflict", "internal")
