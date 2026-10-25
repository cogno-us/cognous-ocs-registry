"""Shared primitives for the R08-S01 successor contract `r08-v1` (docs/r08-s01-contract.md).

Plan: OCS-REG-PLAN v1.2 (blob 32319775c6e2d9c3fff1e2171c8f4c9d096911d6), R08 only.
Non-authorizing and unqualified. Pure: reads no files, holds no state, imports nothing from the Runtime or from the
frozen `registry_contract` / `registry_consumer` modules. Digests give integrity, never authentication.

This module owns the closed refusal-code set `CODES`. No other module may invent a code; a new code is a contract change.
"""
import datetime
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Optional

CONTRACT_VERSION = "r08-v1"
FAMILY_F1A = "f1a-local-execution-allowlist"
EVALUATOR_ID = "engine.safe_executor.LocalExecutionPolicy.check"
EVALUATOR_BINDING = "registered-code-reference"
F1A_FIELDS = ("allowed_actions", "allowed_adapters", "allowed_units")
PARTICIPATION = ("required", "optional")

MAX_DOCUMENT_BYTES = 65536
MAX_DEPTH = 8
MAX_ENTRIES = 256
MAX_ENTRY_CHARS = 128
MAX_INT = 2**31 - 1

# code -> (layer, meaning). Closed set; the first failing check in contract order wins.
CODES = {
    # parse
    "input_not_text": ("parse", "input is not a str or cannot be encoded as UTF-8"),
    "input_too_large": ("parse", "encoded input exceeds MAX_DOCUMENT_BYTES"),
    "json_malformed": ("parse", "not valid JSON"),
    "json_duplicate_key": ("parse", "an object repeats a key"),
    "json_nesting_too_deep": ("parse", "nesting exceeds MAX_DEPTH"),
    "json_number_unsupported": ("parse", "a float or non-finite number is present"),
    # contract
    "contract_unsupported": ("contract", "contract_version is not r08-v1"),
    "kind_unsupported": ("contract", "kind is not the expected document kind"),
    "family_unsupported": ("contract", "family is not f1a-local-execution-allowlist"),
    # shape (typed family semantics: an absent F1a field refuses; it is never an implicit allow or deny)
    "field_unknown": ("shape", "an unknown field is present"),
    "field_missing": ("shape", "a required field is absent"),
    "field_type_invalid": ("shape", "a field has the wrong type"),
    "field_invalid": ("shape", "a field violates its value constraints"),
    # integrity and identity
    "digest_mismatch": ("integrity", "a recorded digest does not match the canonical content"),
    "evaluator_unsupported": ("identity", "evaluator id or binding is not the registered F1a evaluator"),
    "evaluator_mismatch": ("identity", "evaluator identity or build differs between selection and record or expectation"),
    "record_identity_mismatch": ("identity", "selection pins a different record id or version"),
    "record_digest_mismatch": ("identity", "selection pins a different record digest"),
    "supersession_invalid": ("identity", "record supersession reference is invalid"),
    # selection structure and conflicts
    "selection_missing": ("selection", "no selection was supplied or none is effective"),
    "selection_epoch_stale": ("selection", "epoch is below the trusted floor for this selection id"),
    "selection_conflict": ("selection", "two effective selections conflict without explicit supersession"),
    "selection_supersession_invalid": ("selection", "supersession reference or decision reference is invalid"),
    "participation_mismatch": ("selection", "selection participation differs from the consumer's operation class"),
    # trust and authentication
    "trust_snapshot_missing": ("trust", "no trust snapshot was supplied"),
    "trust_snapshot_invalid": ("trust", "trust snapshot is malformed"),
    "trust_snapshot_expired": ("trust", "trust snapshot is past valid_until"),
    "time_unavailable": ("trust", "no trusted current time was supplied"),
    "verifier_unavailable": ("authenticity", "no signature verifier is available; digest match is not authentication"),
    "signature_missing": ("authenticity", "the statement carries no signature"),
    "signature_algorithm_unsupported": ("authenticity", "signature algorithm is not supported"),
    "issuer_untrusted": ("authenticity", "no trusted issuer holds the signing key id"),
    "issuer_key_revoked": ("authenticity", "the signing key id is revoked in the trust snapshot"),
    "signature_invalid": ("authenticity", "signature does not verify"),
    "issuer_not_authorized": ("authority", "issuer holds no authority for this exact consumer, scope and operation"),
    # applicability
    "selection_consumer_mismatch": ("scope", "selection names a different consumer"),
    "selection_scope_mismatch": ("scope", "tenant, institution or authority domain differs"),
    "selection_operation_mismatch": ("scope", "selection names a different operation"),
    "selection_not_yet_effective": ("time", "now is before valid_from"),
    "selection_expired": ("time", "now is at or after valid_until"),
    "selection_revoked": ("revocation", "selection id and epoch are revoked in the trust snapshot"),
    # composition
    "composition_family_unsupported": ("composition", "family is not composable"),
    "composition_operator_unsupported": ("composition", "operator is not intersection"),
    "composition_caller_invalid": ("composition", "caller policy fields are malformed"),
    "composition_record_invalid": ("composition", "record is not a valid F1a record"),
}


@dataclass(frozen=True)
class LoadResult:
    ok: bool
    code: Optional[str] = None
    detail: str = ""
    value: Any = None


def fail(code: str, detail: str = "") -> LoadResult:
    assert code in CODES, code
    return LoadResult(False, code, detail, None)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class _Duplicate(Exception):
    pass


class _Float(Exception):
    pass


def _pairs(pairs: list) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise _Duplicate(key)
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise _Float(name)


def _reject_float(text: str) -> Any:
    raise _Float(text)


def _depth_ok(value: Any) -> bool:
    stack = [(value, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_DEPTH:
            return False
        if isinstance(node, dict):
            stack.extend((child, depth + 1) for child in node.values())
        elif isinstance(node, list):
            stack.extend((child, depth + 1) for child in node)
    return True


def load_document(text: Any) -> LoadResult:
    """Strict JSON loader: str only, bounded bytes and depth, no duplicate keys, integers only."""
    if not isinstance(text, str):
        return fail("input_not_text")
    try:
        raw = text.encode("utf-8")
    except UnicodeEncodeError:
        return fail("input_not_text", "not encodable as UTF-8")
    if len(raw) > MAX_DOCUMENT_BYTES:
        return fail("input_too_large")
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_float=_reject_float, parse_constant=_reject_constant)
    except _Duplicate:
        return fail("json_duplicate_key")
    except _Float:
        return fail("json_number_unsupported")
    except RecursionError:
        return fail("json_nesting_too_deep")
    except ValueError:
        return fail("json_malformed")
    if not _depth_ok(value):
        return fail("json_nesting_too_deep")
    return LoadResult(True, None, "", value)


_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{2,63}\Z")
_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_TS_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z")


def valid_identifier(value: Any) -> bool:
    return isinstance(value, str) and _ID_RE.match(value) is not None


def valid_hex40(value: Any) -> bool:
    return isinstance(value, str) and _HEX40_RE.match(value) is not None


def valid_sha_ref(value: Any) -> bool:
    return isinstance(value, str) and _SHA_RE.match(value) is not None


def valid_token(value: Any) -> bool:
    """1..MAX_ENTRY_CHARS characters, no control or separator characters, no '*'. Opaque: never interpreted."""
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_ENTRY_CHARS or "*" in value:
        return False
    return all(unicodedata.category(ch)[0] not in ("C", "Z") for ch in value)


def parse_timestamp(value: Any) -> Optional[datetime.datetime]:
    """Strict `YYYY-MM-DDTHH:MM:SSZ` UTC, or None."""
    if not isinstance(value, str) or _TS_RE.match(value) is None:
        return None
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def valid_entry_list(value: Any, allow_empty: bool) -> bool:
    """Sorted, duplicate-free, at most MAX_ENTRIES valid tokens; empty only when allowed (explicit deny-all)."""
    if not isinstance(value, list) or len(value) > MAX_ENTRIES:
        return False
    if not value:
        return allow_empty
    if not all(valid_token(item) for item in value):
        return False
    return value == sorted(set(value))


def exact_fields(obj: Any, fields: tuple) -> Optional[str]:
    """None when `obj` is a dict with exactly `fields`; else the shape code to use."""
    if not isinstance(obj, dict):
        return "field_type_invalid"
    keys = set(obj)
    if keys - set(fields):
        return "field_unknown"
    if set(fields) - keys:
        return "field_missing"
    return None


@dataclass(frozen=True)
class ExpectedContext:
    """The consumer's own operation context. Supplied by the consumer, never read from a selection."""
    consumer_id: str
    tenant: str
    institution: str
    authority_domain: str
    operation: str
