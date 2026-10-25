"""F1a record validation for contract `r08-v1` (docs/r08-s01-contract.md section 2).

Non-authorizing and unqualified. Pure: no I/O, clocks or state. Entries are opaque strings and are never interpreted.
An empty payload list is a valid explicit deny-all for that dimension; an absent field refuses (`field_missing`).
There is no `status` field: lifecycle state is event-derived and outside the record.
Any failure returns one code from `common.CODES`; the first failing check in contract order wins. Never raises.
"""
import copy
from dataclasses import dataclass
from typing import Any, Optional

from . import common as c

TOP_FIELDS = (
    "contract_version", "kind", "family", "record_id", "record_version", "non_authorizing", "supersedes",
    "evaluator", "source", "payload", "payload_digest", "provenance", "record_digest",
)
EVALUATOR_FIELDS = ("evaluator_id", "binding", "source_blob_id", "source_sha256")
SOURCE_FIELDS = ("repository", "commit", "path", "blob_id", "sha256")
PROVENANCE_FIELDS = ("decision_ref", "authored_at", "authored_by")
SUPERSEDES_FIELDS = ("record_id", "record_version", "record_digest")


@dataclass(frozen=True)
class RecordResult:
    ok: bool
    code: Optional[str] = None
    detail: str = ""
    record: Any = None
    record_digest: Optional[str] = None


def _refuse(code: str, detail: str = "") -> RecordResult:
    assert code in c.CODES, code
    return RecordResult(False, code, detail)


def _version_ok(value: Any) -> bool:
    return c.is_int(value) and 1 <= value <= c.MAX_INT


def _shape(record: dict) -> Optional[str]:
    code = c.exact_fields(record, TOP_FIELDS)
    if code:
        return code
    if record["supersedes"] is not None:
        code = c.exact_fields(record["supersedes"], SUPERSEDES_FIELDS)
        if code:
            return code
    for name, fields in (("evaluator", EVALUATOR_FIELDS), ("source", SOURCE_FIELDS),
                         ("payload", c.F1A_FIELDS), ("provenance", PROVENANCE_FIELDS)):
        code = c.exact_fields(record[name], fields)
        if code:
            return code
    return None


def _values(record: dict) -> Optional[str]:
    if not c.valid_identifier(record["record_id"]) or not _version_ok(record["record_version"]):
        return "field_invalid"
    if record["non_authorizing"] is not True:
        return "field_invalid"
    ev = record["evaluator"]
    if not all(isinstance(ev[k], str) for k in EVALUATOR_FIELDS):
        return "field_type_invalid"
    if ev["evaluator_id"] != c.EVALUATOR_ID or ev["binding"] != c.EVALUATOR_BINDING:
        return "evaluator_unsupported"
    if not c.valid_hex40(ev["source_blob_id"]) or not c.valid_sha_ref(ev["source_sha256"]):
        return "field_invalid"
    src = record["source"]
    if not all(isinstance(src[k], str) for k in SOURCE_FIELDS):
        return "field_type_invalid"
    if not (c.valid_token(src["repository"]) and c.valid_token(src["path"]) and c.valid_hex40(src["commit"])
            and c.valid_hex40(src["blob_id"]) and c.valid_sha_ref(src["sha256"])):
        return "field_invalid"
    payload = record["payload"]
    if not all(isinstance(payload[k], list) for k in c.F1A_FIELDS):
        return "field_type_invalid"
    if not all(c.valid_entry_list(payload[k], allow_empty=True) for k in c.F1A_FIELDS):
        return "field_invalid"
    prov = record["provenance"]
    if not all(isinstance(prov[k], str) for k in PROVENANCE_FIELDS):
        return "field_type_invalid"
    if not (c.valid_token(prov["decision_ref"]) and c.valid_token(prov["authored_by"])
            and c.parse_timestamp(prov["authored_at"]) is not None):
        return "field_invalid"
    return None


def _supersession_ok(record: dict) -> bool:
    sup = record["supersedes"]
    if sup is None:
        return True
    return (c.valid_identifier(sup["record_id"]) and sup["record_id"] == record["record_id"]
            and _version_ok(sup["record_version"]) and sup["record_version"] < record["record_version"]
            and c.valid_sha_ref(sup["record_digest"]))


def _validate(text: Any) -> RecordResult:
    loaded = c.load_document(text)
    if not loaded.ok:
        return _refuse(loaded.code, loaded.detail)
    record = loaded.value
    if not isinstance(record, dict):
        return _refuse("field_type_invalid", "document is not an object")
    if record.get("contract_version") != c.CONTRACT_VERSION:
        return _refuse("contract_unsupported")
    if record.get("kind") != "record":
        return _refuse("kind_unsupported")
    if record.get("family") != c.FAMILY_F1A:
        return _refuse("family_unsupported")
    code = _shape(record)
    if code:
        return _refuse(code)
    code = _values(record)
    if code:
        return _refuse(code)
    if not _supersession_ok(record):
        return _refuse("supersession_invalid")
    if record["payload_digest"] != c.digest(record["payload"]):
        return _refuse("digest_mismatch", "payload_digest")
    body = {k: v for k, v in record.items() if k != "record_digest"}
    if record["record_digest"] != c.digest(body):
        return _refuse("digest_mismatch", "record_digest")
    return RecordResult(True, None, "", copy.deepcopy(record), record["record_digest"])


def validate_record_text(text: Any) -> RecordResult:
    try:
        return _validate(text)
    except Exception:  # defensive: an unexpected shape error is a refusal, never an acceptance
        return _refuse("field_type_invalid", "unexpected structure")
