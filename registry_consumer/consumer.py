"""Bounded registry overlay consumer for the three LocalExecutionPolicy allow-lists (S04).

Plan: OCS-REG-PLAN v1.1 S04 (blob 6ece90f6697320fd305d8eb8c1e3a7f2f1f428a2).
Constitution: cognous-engineering-constitution 1c2e920f4e58e07a52e8e2408a506cf7dbc1292b.
Authorization: docs/decisions/2026-10-24-s04-preconditions-and-authorization.md (P1-P3 as adopted).

Trust model (P1, P2): the TrustConfig is the operator's trusted configuration. It carries the pin (SHA-256 of the exact
manifest bytes) and the Runtime source commitments (the S01 blob id and SHA-256). Nothing the record or the manifest
says can establish its own authority: the manifest is accepted only if its bytes hash to the pin, the record is
accepted only if its file bytes hash to the manifest's approved value, the installed evaluator file is re-hashed
against the trusted commitments, and the S03 validator context is built from those trusted values and the manifest's
selected version, never from the record.

Semantics: effective = caller ∩ registry for exactly allowed_actions, allowed_adapters, allowed_units. Any refusal
returns the caller policy object unchanged with overlay_applied False. This is an optional-overlay profile: a refusal
is not a denial and not a compliance claim. Excluded attackers and limits are in docs/s04-implementation.md.

No discovery (explicit paths only), no network, no processes, no dynamic code, no writes. Files are read once and the
same bytes are verified and parsed. The S03 validator and the baseline Runtime are imported unchanged.
"""
import dataclasses
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

from engine.safe_executor import LocalExecutionPolicy
from registry_contract.validator import (
    CONTRACT_VERSION,
    EVALUATOR_BINDING,
    EVALUATOR_ID,
    validate_record_text,
    widening_violations,
)

MANIFEST_TYPE = "local-execution-allowlist-selection"
MANIFEST_VERSION = "s04-v1"
EFFECTIVE_FIELDS = ("allowed_actions", "allowed_adapters", "allowed_units")
MAX_FILE_BYTES = 1024 * 1024
MAX_SOURCE_BYTES = 8 * 1024 * 1024
MAX_VERSION = 2**31 - 1

CONSUMER_REASON_CODES = (
    "caller_policy_invalid",
    "trust_config_invalid",
    "runtime_source_unverified",
    "manifest_missing",
    "manifest_pin_mismatch",
    "manifest_invalid",
    "manifest_runtime_mismatch",
    "record_missing",
    "record_file_mismatch",
    "record_refused",
    "record_identity_mismatch",
    "consumer_error",
)

_SHA = r"sha256:[0-9a-f]{64}"
_HEX40 = r"[0-9a-f]{40}"
_ID = r"[a-z0-9][a-z0-9._-]{2,63}"


@dataclasses.dataclass(frozen=True)
class TrustConfig:
    """Operator-supplied trusted configuration. Never derived from a record or manifest.

    manifest_sha256: pin, `sha256:` plus the hex SHA-256 of the exact approved manifest bytes.
    runtime_source_blob_id / runtime_source_sha256: the S01 commitments for engine/safe_executor.py.
    runtime_source_path: optional path of the installed evaluator source to verify; by default the file the caller
    policy's class was loaded from. Validation happens in apply_registry_overlay, not here.
    """

    manifest_sha256: Any
    runtime_source_blob_id: Any
    runtime_source_sha256: Any
    runtime_source_path: Any = None


@dataclasses.dataclass(frozen=True)
class OverlayResult:
    disposition: str  # "ACCEPT" or "REFUSE"
    reason: Optional[str]  # None on ACCEPT; a CONSUMER_REASON_CODES member on REFUSE
    overlay_applied: bool
    policy: Any  # the effective policy on ACCEPT; the caller's policy object, unchanged, on REFUSE
    validator_reason: Optional[str] = None  # the S03 reason when reason == "record_refused"
    narrowed_fields: tuple = ()


def _refuse(policy: Any, reason: str, validator_reason: Optional[str] = None) -> OverlayResult:
    return OverlayResult("REFUSE", reason, False, policy, validator_reason, ())


def _sha256_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _is_str(value: Any, pattern: str) -> bool:
    return type(value) is str and re.fullmatch(pattern, value) is not None


def _read(path: Any, limit: int):
    """Return ("ok", bytes), ("missing", None) or ("oversize", None). One read; bounded."""
    if not isinstance(path, (str, Path)):
        return "missing", None
    try:
        with Path(path).open("rb") as handle:
            data = handle.read(limit + 1)
    except (OSError, ValueError):
        return "missing", None
    if len(data) > limit:
        return "oversize", None
    return "ok", data


def _no_duplicate_keys(pairs: list) -> dict:
    out: dict = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate key")
        out[key] = value
    return out


def _reject_constant(name: str) -> Any:
    raise ValueError("non-finite number: " + name)


def _strict_loads(raw: bytes) -> Any:
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)


def _trust_ok(trust: Any) -> bool:
    return (
        type(trust) is TrustConfig
        and _is_str(trust.manifest_sha256, _SHA)
        and _is_str(trust.runtime_source_blob_id, _HEX40)
        and _is_str(trust.runtime_source_sha256, _SHA)
        and (trust.runtime_source_path is None or isinstance(trust.runtime_source_path, (str, Path)))
    )


def _installed_source_ok(policy: LocalExecutionPolicy, trust: TrustConfig) -> bool:
    path = trust.runtime_source_path
    if path is None:
        module = sys.modules.get(type(policy).__module__)
        path = getattr(module, "__file__", None)
    status, data = _read(path, MAX_SOURCE_BYTES)
    return (
        status == "ok"
        and _blob_id(data) == trust.runtime_source_blob_id
        and _sha256_of(data) == trust.runtime_source_sha256
    )


def _manifest_ok(manifest: Any) -> bool:
    """Exact shape, types and constants of the selection manifest (s04-v1)."""
    if type(manifest) is not dict or set(manifest) != {
        "manifest_type", "manifest_version", "contract_version", "record", "record_source", "evaluator", "runtime",
    }:
        return False
    if (manifest["manifest_type"], manifest["manifest_version"], manifest["contract_version"]) != (
            MANIFEST_TYPE, MANIFEST_VERSION, CONTRACT_VERSION):
        return False
    record, source, evaluator, runtime = (manifest[k] for k in ("record", "record_source", "evaluator", "runtime"))
    if type(record) is not dict or set(record) != {"record_id", "record_version", "record_digest", "file_sha256"}:
        return False
    if not _is_str(record["record_id"], _ID) or not _is_str(record["record_digest"], _SHA):
        return False
    if not _is_str(record["file_sha256"], _SHA):
        return False
    version = record["record_version"]
    if type(version) is not int or not 1 <= version <= MAX_VERSION:
        return False
    if type(source) is not dict or set(source) != {"repository", "commit", "path"}:
        return False
    if not (type(source["repository"]) is str and 1 <= len(source["repository"]) <= 200
            and type(source["path"]) is str and 1 <= len(source["path"]) <= 300 and _is_str(source["commit"], _HEX40)):
        return False
    if type(evaluator) is not dict or evaluator != {"evaluator_id": EVALUATOR_ID, "binding": EVALUATOR_BINDING}:
        return False
    return (
        type(runtime) is dict
        and set(runtime) == {"source_blob_id", "source_sha256"}
        and _is_str(runtime["source_blob_id"], _HEX40)
        and _is_str(runtime["source_sha256"], _SHA)
    )


def _apply(caller_policy: Any, trust: Any, manifest_path: Any, record_path: Any) -> OverlayResult:
    if type(caller_policy) is not LocalExecutionPolicy:
        return _refuse(caller_policy, "caller_policy_invalid")
    if not _trust_ok(trust):
        return _refuse(caller_policy, "trust_config_invalid")
    if not _installed_source_ok(caller_policy, trust):
        return _refuse(caller_policy, "runtime_source_unverified")

    status, manifest_raw = _read(manifest_path, MAX_FILE_BYTES)
    if status == "missing":
        return _refuse(caller_policy, "manifest_missing")
    if status == "oversize":
        return _refuse(caller_policy, "manifest_invalid")
    if _sha256_of(manifest_raw) != trust.manifest_sha256:
        return _refuse(caller_policy, "manifest_pin_mismatch")
    try:
        manifest = _strict_loads(manifest_raw)
    except (ValueError, RecursionError):
        return _refuse(caller_policy, "manifest_invalid")
    if not _manifest_ok(manifest):
        return _refuse(caller_policy, "manifest_invalid")
    if manifest["runtime"] != {
            "source_blob_id": trust.runtime_source_blob_id, "source_sha256": trust.runtime_source_sha256}:
        return _refuse(caller_policy, "manifest_runtime_mismatch")

    approved = manifest["record"]
    status, record_raw = _read(record_path, MAX_FILE_BYTES)
    if status == "missing":
        return _refuse(caller_policy, "record_missing")
    if status == "oversize" or _sha256_of(record_raw) != approved["file_sha256"]:
        return _refuse(caller_policy, "record_file_mismatch")

    context = {
        "runtime_source_blob_id": trust.runtime_source_blob_id,
        "runtime_source_sha256": trust.runtime_source_sha256,
        "latest_known_version": approved["record_version"],
    }
    verdict = validate_record_text(record_raw, context)
    if verdict.outcome != "ACCEPT":
        return _refuse(caller_policy, "record_refused", verdict.reason)
    record = _strict_loads(record_raw)  # same bytes the validator accepted
    if (record["record_id"], record["record_version"], record["record_digest"]) != (
            approved["record_id"], approved["record_version"], approved["record_digest"]):
        return _refuse(caller_policy, "record_identity_mismatch")

    effective = {}
    narrowed = []
    for field in EFFECTIVE_FIELDS:
        caller_set = getattr(caller_policy, field)
        registry_set = frozenset(record["data"][field])
        effective[field] = caller_set & registry_set
        if effective[field] != caller_set:
            narrowed.append(field)
    caller_view = {f: sorted(getattr(caller_policy, f)) for f in EFFECTIVE_FIELDS}
    if widening_violations({f: sorted(v) for f, v in effective.items()}, caller_view):
        raise RuntimeError("effective policy would widen the caller policy")  # unreachable; defence in depth
    policy = dataclasses.replace(caller_policy, **effective)
    return OverlayResult("ACCEPT", None, True, policy, None, tuple(narrowed))


def apply_registry_overlay(caller_policy: Any, trust: Any, manifest_path: Any, record_path: Any) -> OverlayResult:
    """Narrow `caller_policy` with one authenticated registry record, or refuse and leave it unchanged.

    Never raises. Any unexpected exception is a REFUSE (`consumer_error`) carrying the caller's policy object unchanged,
    with overlay_applied False: no narrowing and no claim that registry activation succeeded.
    """
    try:
        return _apply(caller_policy, trust, manifest_path, record_path)
    except Exception:  # noqa: BLE001 - fail closed; the result is always REFUSE
        return _refuse(caller_policy, "consumer_error")
