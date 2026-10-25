"""Pure validator for `local-execution-allowlist` records, contract s03-v1 (docs/s03-contract.md).

Plan: OCS-REG-PLAN v1.1 S03 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2).
Constitution: cognous-engineering-constitution 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.

Non-authorizing and unqualified. It reads no files, imports nothing from the Runtime, holds no state and never
interprets record values: entries are opaque strings. Digests give integrity, not authenticity (contract section 3).
Any failure returns REFUSE with one reason code from a closed set; the first failing check in contract order wins.
"""
import datetime
import hashlib
import json
import re
import unicodedata
from typing import Any, NamedTuple, Optional

REASON_CODES = (
    "record_missing",
    "context_missing",
    "record_malformed",
    "contract_unsupported",
    "record_invalid",
    "digest_mismatch",
    "supersession_invalid",
    "status_not_active",
    "version_not_latest",
    "evaluator_unsupported",
    "not_applicable",
    "source_mismatch",
)

RECORD_TYPE = "local-execution-allowlist"
CONTRACT_VERSION = "s03-v1"
EVALUATOR_ID = "engine.safe_executor.LocalExecutionPolicy.check"
EVALUATOR_BINDING = "registered-code-reference"
SUPPLIES = ("allowed_actions", "allowed_adapters", "allowed_units")
STATUSES = ("proposed", "active", "superseded", "withdrawn")
MAX_ENTRIES = 256
MAX_ENTRY_CHARS = 128

TOP_LEVEL_FIELDS = (
    "record_type", "contract_version", "record_id", "record_version", "status", "non_authorizing", "supersedes",
    "source", "applicability", "evaluator", "data", "data_digest", "provenance", "record_digest",
)
NESTED_FIELDS = {
    "supersedes": ("record_id", "record_version", "record_digest"),
    "source": ("repository", "commit", "path", "blob_id", "sha256", "field_lines", "check_lines"),
    "applicability": ("runtime_source_blob_id",),
    "evaluator": ("evaluator_id", "binding", "supplies"),
    "data": ("allowed_units", "allowed_adapters", "allowed_actions"),
    "provenance": ("decision_ref", "authored_at", "authored_by"),
}
CONTEXT_FIELDS = ("runtime_source_blob_id", "runtime_source_sha256", "latest_known_version")

_ID = r"[a-z0-9][a-z0-9._-]{2,63}"
_HEX40 = r"[0-9a-f]{40}"
_SHA = r"sha256:[0-9a-f]{64}"
_LINES = r"[0-9]+-[0-9]+"


class Result(NamedTuple):
    outcome: str
    reason: Optional[str]


def _refuse(reason: str) -> Result:
    return Result("REFUSE", reason)


_ACCEPT = Result("ACCEPT", None)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _is_int(value: Any) -> bool:
    return type(value) is int


def _is_str_list(value: Any) -> bool:
    return type(value) is list and all(type(item) is str for item in value)


def _context_ok(context: Any) -> bool:
    if type(context) is not dict or set(context) != set(CONTEXT_FIELDS):
        return False
    blob, sha, latest = (context[k] for k in CONTEXT_FIELDS)
    return (
        type(blob) is str and re.fullmatch(_HEX40, blob) is not None
        and type(sha) is str and re.fullmatch(_SHA, sha) is not None
        and _is_int(latest) and latest >= 1
    )


def _shape_ok(record: dict) -> bool:
    """Check 3: exact field sets and JSON types. Value rules are check 5."""
    if set(record) != set(TOP_LEVEL_FIELDS):
        return False
    for name, fields in NESTED_FIELDS.items():
        node = record[name]
        if name == "supersedes" and node is None:
            continue
        if type(node) is not dict or set(node) != set(fields):
            return False
    if not all(type(record[k]) is str for k in (
            "record_type", "contract_version", "record_id", "status", "data_digest", "record_digest")):
        return False
    if not _is_int(record["record_version"]) or type(record["non_authorizing"]) is not bool:
        return False
    sup = record["supersedes"]
    if sup is not None and not (
            type(sup["record_id"]) is str and _is_int(sup["record_version"]) and type(sup["record_digest"]) is str):
        return False
    if not all(type(v) is str for v in record["source"].values()):
        return False
    if type(record["applicability"]["runtime_source_blob_id"]) is not str:
        return False
    ev = record["evaluator"]
    if type(ev["evaluator_id"]) is not str or type(ev["binding"]) is not str or not _is_str_list(ev["supplies"]):
        return False
    if not all(_is_str_list(v) for v in record["data"].values()):
        return False
    return all(type(v) is str for v in record["provenance"].values())


def _entries_ok(entries: list) -> bool:
    if not 1 <= len(entries) <= MAX_ENTRIES or len(set(entries)) != len(entries) or entries != sorted(entries):
        return False
    for entry in entries:
        if not 1 <= len(entry) <= MAX_ENTRY_CHARS or "*" in entry:
            return False
        if any(unicodedata.category(ch)[0] in ("C", "Z") for ch in entry):
            return False
    return True


def _timestamp_ok(text: str) -> bool:
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", text) is None:
        return False
    try:
        datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return True


def _lines_ok(text: str) -> bool:
    if re.fullmatch(_LINES, text) is None:
        return False
    start, end = (int(part) for part in text.split("-"))
    return 1 <= start <= end


def _values_ok(record: dict) -> bool:
    """Check 5: value rules, assuming check 3 passed."""
    if re.fullmatch(_ID, record["record_id"]) is None or record["record_version"] < 1:
        return False
    if record["status"] not in STATUSES or record["non_authorizing"] is not True:
        return False
    if re.fullmatch(_SHA, record["data_digest"]) is None or re.fullmatch(_SHA, record["record_digest"]) is None:
        return False
    sup = record["supersedes"]
    if sup is not None and (
            re.fullmatch(_ID, sup["record_id"]) is None or sup["record_version"] < 1
            or re.fullmatch(_SHA, sup["record_digest"]) is None):
        return False
    src = record["source"]
    if not src["repository"] or not src["path"]:
        return False
    if re.fullmatch(_HEX40, src["commit"]) is None or re.fullmatch(_HEX40, src["blob_id"]) is None:
        return False
    if re.fullmatch(_SHA, src["sha256"]) is None or not _lines_ok(src["field_lines"]) or not _lines_ok(src["check_lines"]):
        return False
    if re.fullmatch(_HEX40, record["applicability"]["runtime_source_blob_id"]) is None:
        return False
    if not all(_entries_ok(entries) for entries in record["data"].values()):
        return False
    prov = record["provenance"]
    return (
        1 <= len(prov["decision_ref"]) <= 200
        and 1 <= len(prov["authored_by"]) <= 120
        and _timestamp_ok(prov["authored_at"])
    )


def _supersession_ok(record: dict) -> bool:
    sup = record["supersedes"]
    if record["record_version"] == 1:
        return sup is None
    return (
        sup is not None
        and sup["record_id"] == record["record_id"]
        and sup["record_version"] == record["record_version"] - 1
    )


def validate_record(record: Any, context: Any) -> Result:
    """Validate one parsed record against a verifier context. Never raises for bad input; never mutates it."""
    if record is None:
        return _refuse("record_missing")
    if not _context_ok(context):
        return _refuse("context_missing")
    if type(record) is not dict or not _shape_ok(record):
        return _refuse("record_malformed")
    if record["record_type"] != RECORD_TYPE or record["contract_version"] != CONTRACT_VERSION:
        return _refuse("contract_unsupported")
    if not _values_ok(record):
        return _refuse("record_invalid")
    body = {k: v for k, v in record.items() if k != "record_digest"}
    if digest(record["data"]) != record["data_digest"] or digest(body) != record["record_digest"]:
        return _refuse("digest_mismatch")
    if not _supersession_ok(record):
        return _refuse("supersession_invalid")
    if record["status"] != "active":
        return _refuse("status_not_active")
    if record["record_version"] != context["latest_known_version"]:
        return _refuse("version_not_latest")
    ev = record["evaluator"]
    if ev["evaluator_id"] != EVALUATOR_ID or ev["binding"] != EVALUATOR_BINDING or tuple(ev["supplies"]) != SUPPLIES:
        return _refuse("evaluator_unsupported")
    blob = record["applicability"]["runtime_source_blob_id"]
    if blob != context["runtime_source_blob_id"]:
        return _refuse("not_applicable")
    src = record["source"]
    if src["blob_id"] != blob or src["sha256"] != context["runtime_source_sha256"]:
        return _refuse("source_mismatch")
    return _ACCEPT


def _no_duplicate_keys(pairs: list) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate key")
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise ValueError("non-finite number: " + name)


def validate_record_text(text: Any, context: Any) -> Result:
    """Strict-JSON entry point: duplicate keys, NaN/Infinity, trailing data and invalid UTF-8 are record_malformed."""
    if text is None:
        return _refuse("record_missing")
    if not _context_ok(context):
        return _refuse("context_missing")
    try:
        if type(text) in (bytes, bytearray):
            text = bytes(text).decode("utf-8")
        if type(text) is not str:
            return _refuse("record_malformed")
        parsed = json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    except (ValueError, RecursionError):
        return _refuse("record_malformed")
    if parsed is None:
        return _refuse("record_malformed")
    return validate_record(parsed, context)


def widening_violations(data: Any, caller: Any) -> list:
    """CR-NW: field names where the registry-supplied set is not a subset of the caller-constructed set.

    A missing, mistyped or non-subset field is a violation (fail closed). Result is sorted.
    """
    violations = []
    for field in sorted(NESTED_FIELDS["data"]):
        mine = data.get(field) if isinstance(data, dict) else None
        theirs = caller.get(field) if isinstance(caller, dict) else None
        ok = (
            isinstance(mine, (list, tuple, set, frozenset)) and isinstance(theirs, (list, tuple, set, frozenset))
            and all(type(x) is str for x in mine) and all(type(x) is str for x in theirs)
            and set(mine) <= set(theirs)
        )
        if not ok:
            violations.append(field)
    return violations
