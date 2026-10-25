"""Layered technical verification of selection statements against explicit trusted inputs (contract section 4).

Non-authorizing and unqualified. Pure and deterministic: time, trust snapshot, verifier and context are injected.
Nothing is hardcoded or discovered: there is no default trust root, key, issuer or verifier. With no verifier the
authenticity layer refuses `verifier_unavailable`; a matching SHA-256 digest is integrity only and never authenticates.
`ok` means technically verified; `operationally_authorized` is always False.
"""
import base64
import binascii
import datetime
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

from registry_successor import common as c
from registry_successor.canonical_b64 import decode_canonical_base64
from registry_successor.common import ExpectedContext
from registry_successor.key_admission import (
    DETAIL_KEY_ADMISSION_INVALID, DETAIL_TRUST_SNAPSHOT_MALFORMED, inspect_ed25519_key)

LAYERS = (
    "structural", "integrity", "record_binding", "trust_snapshot", "authenticity",
    "authority", "scope", "time", "revocation", "epoch",
)
PASS, REFUSE, NOT_EVALUATED = "pass", "refuse", "not_evaluated"
SUPPORTED_ALG = "ed25519"

__all__ = [
    "ExpectedContext", "AuthorityGrant", "IssuerEntry", "TrustSnapshot", "SignatureVerifier", "VerificationReport",
    "LAYERS", "verify_selection", "TypedVerificationReport",
]


@dataclass(frozen=True)
class AuthorityGrant:
    """Exact-match authority of an issuer. No wildcards."""
    consumer_id: str
    tenant: str
    institution: str
    authority_domain: str
    operation: str


@dataclass(frozen=True)
class IssuerEntry:
    key_id: str
    issuer_id: str
    alg: str
    public_key: bytes
    authority: tuple


@dataclass(frozen=True)
class TrustSnapshot:
    snapshot_id: str
    version: int
    valid_until: str
    issuers: tuple
    revoked_key_ids: frozenset = frozenset()
    revoked_selections: frozenset = frozenset()
    min_epochs: Any = ()


class SignatureVerifier(Protocol):
    def verify(self, alg: str, public_key: bytes, message: bytes, signature: bytes) -> bool: ...


@dataclass(frozen=True)
class VerificationReport:
    ok: bool
    code: Optional[str]
    detail: str
    layers: Mapping
    selection_digest: Optional[str]
    authenticated: bool
    issuer_id: Optional[str]
    operationally_authorized: bool = False
    participation: Optional[str] = None
    bound_record_digest: Optional[str] = None


@dataclass(frozen=True)
class TypedVerificationReport(VerificationReport):
    """A VerificationReport that also carries a typed sub-cause of `code`. Returned ONLY when a refusal has one (today:
    the two `trust_snapshot_invalid` conditions). Every other report is the base class, so the frozen r08-v1 serialized
    shape is untouched."""
    detail_code: Optional[str] = None    # DETAIL_KEY_ADMISSION_INVALID or DETAIL_TRUST_SNAPSHOT_MALFORMED
    detail_cause: Optional[str] = None   # stable cause label (e.g. key_small_order, key_length, policy_refused)


LEGACY_CONTRACT = "r08-v1"
V2_CONTRACT = "r08-v2"


def _admission_mandatory(selection: Any, contract_version: Any) -> bool:
    """Admission is mandatory on every path except the explicit legacy `r08-v1` default. Fail closed: any other or odd
    `contract_version` value, or an envelope that itself says r08-v2, selects the mandatory path."""
    if contract_version != LEGACY_CONTRACT:
        return True
    return getattr(selection, "envelope", None) is not None and \
        isinstance(selection.envelope, dict) and selection.envelope.get("contract_version") == V2_CONTRACT


def _normalize_trust(trust: Any) -> Optional[dict]:
    """Return a normalized view of a well-formed snapshot, or None."""
    if not isinstance(trust, TrustSnapshot):
        return None
    if not c.valid_token(trust.snapshot_id) or not c.is_int(trust.version) or trust.version < 1:
        return None
    if c.parse_timestamp(trust.valid_until) is None:
        return None
    if not isinstance(trust.issuers, (tuple, list)):
        return None
    issuers: dict = {}
    for entry in trust.issuers:
        if not isinstance(entry, IssuerEntry) or not c.valid_token(entry.key_id) or not c.valid_token(entry.issuer_id):
            return None
        if not isinstance(entry.alg, str) or not isinstance(entry.public_key, bytes) or not entry.public_key:
            return None
        if entry.key_id in issuers or not isinstance(entry.authority, (tuple, list)):
            return None
        grants = []
        for grant in entry.authority:
            if not isinstance(grant, AuthorityGrant):
                return None
            if not all(c.valid_token(v) for v in (grant.consumer_id, grant.tenant, grant.institution,
                                                   grant.authority_domain, grant.operation)):
                return None
            grants.append(grant)
        issuers[entry.key_id] = (entry, tuple(grants))
    if not isinstance(trust.revoked_key_ids, (set, frozenset, tuple, list)):
        return None
    if not all(isinstance(k, str) for k in trust.revoked_key_ids):
        return None
    if not isinstance(trust.revoked_selections, (set, frozenset, tuple, list)):
        return None
    revoked_sel = set()
    for item in trust.revoked_selections:
        if not (isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) and c.is_int(item[1])):
            return None
        revoked_sel.add(item)
    floors_in = trust.min_epochs
    pairs = floors_in.items() if isinstance(floors_in, Mapping) else floors_in
    floors: dict = {}
    try:
        for item in pairs:
            sid, floor = item
            if not isinstance(sid, str) or not c.is_int(floor) or floor < 1 or sid in floors:
                return None
            floors[sid] = floor
    except (TypeError, ValueError):
        return None
    return {"issuers": issuers, "revoked_keys": frozenset(trust.revoked_key_ids), "revoked_selections": revoked_sel,
            "floors": floors, "valid_until": c.parse_timestamp(trust.valid_until)}


def _admission_failure(trust: dict, key_admission: Any, mandatory: bool) -> Optional[tuple]:
    """(detail text, cause) when an admitted signing key is refused, else None. Fail closed.
    The built-in Ed25519 check runs whenever admission is mandatory or any policy is supplied; a caller policy can only
    add refusals (a non-True or raising policy refuses). With `mandatory` False and no policy: legacy, no admission."""
    if key_admission is None and not mandatory:
        return None
    for key_id, (entry, _grants) in trust["issuers"].items():
        cause = inspect_ed25519_key(entry.public_key) if entry.alg == SUPPORTED_ALG else None
        admitted = True
        if key_admission is not None:
            try:
                admitted = key_admission(entry.alg, entry.public_key) is True
            except Exception:
                admitted = False
        if cause is not None or not admitted:
            cause = cause or "policy_refused"
            return (f"trust snapshot admits a signing key refused by the key-admission policy ({cause}; key_id={key_id})", cause)
    return None


def _statement_view(selection: Any) -> Optional[dict]:
    if not getattr(selection, "ok", False):
        return None
    statement = getattr(selection, "statement", None)
    digest = getattr(selection, "statement_digest", None)
    if not isinstance(statement, dict) or not isinstance(digest, str):
        return None
    return statement


def _aware(now: Any) -> Optional[datetime.datetime]:
    if isinstance(now, datetime.datetime) and now.tzinfo is not None and now.utcoffset() is not None:
        return now
    return None


def _record_binding(statement: dict, record: Any) -> Optional[tuple]:
    if not getattr(record, "ok", False) or not isinstance(getattr(record, "record", None), dict):
        return ("composition_record_invalid", "record is not a valid record")
    body = record.record
    if not isinstance(body.get("payload"), dict) or not isinstance(body.get("record_digest"), str):
        return ("composition_record_invalid", "record body is incomplete")
    if c.digest(body["payload"]) != body.get("payload_digest") or c.digest(
            {k: v for k, v in body.items() if k != "record_digest"}) != body["record_digest"]:
        return ("digest_mismatch", "record content does not match its recorded digests (altered after validation)")
    pin = statement.get("record")
    if not isinstance(pin, dict):
        return ("record_identity_mismatch", "statement carries no record pin")
    if statement.get("family") != body.get("family"):
        return ("family_unsupported", "family differs between selection and record")
    if pin.get("record_id") != body.get("record_id") or pin.get("record_version") != body.get("record_version"):
        return ("record_identity_mismatch", "selection pins a different record id or version")
    if pin.get("record_digest") != body.get("record_digest") or pin.get("record_digest") != getattr(record, "record_digest", None):
        return ("record_digest_mismatch", "selection pins a different record digest")
    if statement.get("evaluator") != body.get("evaluator"):
        return ("evaluator_mismatch", "evaluator identity differs between selection and record")
    return None


def _authenticity(statement: dict, selection: Any, trust: dict, verifier: Any) -> tuple:
    """Returns (code_or_None, detail, valid) where valid lists every (entry, grants) whose signature verified."""
    from registry_successor import selection as sel_mod
    signatures = getattr(selection, "signatures", None)
    if not isinstance(signatures, (list, tuple)) or not signatures:
        return ("signature_missing", "statement carries no signature", [])
    supported = [s for s in signatures if isinstance(s, dict) and s.get("alg") == SUPPORTED_ALG]
    if not supported:
        return ("signature_algorithm_unsupported", "no ed25519 signature present", [])
    try:
        message = sel_mod.signing_input(statement)
    except Exception:
        return ("signature_invalid", "signing input cannot be built", [])
    first_failure = None
    valid = []
    for sig in supported:
        key_id = sig.get("key_id")
        found = trust["issuers"].get(key_id) if isinstance(key_id, str) else None
        if found is None:
            failure = ("issuer_untrusted", "no trusted issuer holds the key id")
        elif key_id in trust["revoked_keys"]:
            failure = ("issuer_key_revoked", "the key id is revoked")
        else:
            entry, grants = found
            text = sig.get("signature")
            raw = decode_canonical_base64(text)
            if raw is None:
                try:
                    base64.b64decode(text, validate=True)
                    failure = ("signature_invalid", "signature is not canonical base64")
                except (binascii.Error, ValueError, TypeError):
                    failure = ("signature_invalid", "signature is not valid base64")
            else:
                try:
                    good = verifier.verify(entry.alg, entry.public_key, message, raw) if entry.alg == SUPPORTED_ALG else False
                except Exception:
                    good = False
                if good is True:
                    valid.append((entry, grants))
                    continue
                failure = ("signature_invalid", "signature does not verify")
        if first_failure is None:
            first_failure = failure
    if valid:
        return (None, "", valid)
    return (first_failure[0], first_failure[1], [])


def _verify(selection, context, trust_in, verifier, now, record, key_admission=None, contract_version=LEGACY_CONTRACT) -> VerificationReport:
    layers = {name: NOT_EVALUATED for name in LAYERS}
    codes: dict = {}
    details: dict = {}
    typed: dict = {}

    def mark(layer: str, code: Optional[str], detail: str = "", typed_detail: Optional[tuple] = None) -> None:
        layers[layer] = PASS if code is None else REFUSE
        if code is not None:
            assert code in c.CODES, code
            codes[layer] = code
            details[layer] = detail
            if typed_detail is not None:
                typed[layer] = typed_detail

    when = _aware(now)
    statement = _statement_view(selection)
    if statement is None:
        given = getattr(selection, "code", None)
        mark("structural", given if given in c.CODES else "field_invalid", "selection is missing or not structurally valid")
    else:
        mark("structural", None)
        if c.digest(statement) == selection.statement_digest:
            mark("integrity", None)
        else:
            mark("integrity", "digest_mismatch", "statement digest does not match canonical statement")
        if record is not None:
            bad = _record_binding(statement, record)
            mark("record_binding", *(bad if bad else (None,)))

    trust = _normalize_trust(trust_in)
    mandatory = _admission_mandatory(selection, contract_version)
    admission = None if trust is None else _admission_failure(trust, key_admission, mandatory)
    if trust_in is None:
        mark("trust_snapshot", "trust_snapshot_missing", "no trust snapshot supplied")
    elif trust is None:
        mark("trust_snapshot", "trust_snapshot_invalid", "trust snapshot is malformed",
             (DETAIL_TRUST_SNAPSHOT_MALFORMED, None) if mandatory else None)  # legacy r08-v1 shape stays byte-frozen
    elif admission is not None:
        mark("trust_snapshot", "trust_snapshot_invalid", admission[0], (DETAIL_KEY_ADMISSION_INVALID, admission[1]))
    elif when is None:
        mark("trust_snapshot", "time_unavailable", "no trusted current time")
    elif when >= trust["valid_until"]:
        mark("trust_snapshot", "trust_snapshot_expired", "trust snapshot is past valid_until")
    else:
        mark("trust_snapshot", None)
    trust_ok = layers["trust_snapshot"] == PASS

    authenticated, issuer_id, valid_signers = False, None, []
    if statement is not None:
        if verifier is None:
            mark("authenticity", "verifier_unavailable", "no signature verifier supplied; digest match is not authentication")
        elif trust_ok:
            code, detail, valid_signers = _authenticity(statement, selection, trust, verifier)
            mark("authenticity", code, detail)
            if code is None:
                authenticated = True

        if layers["authenticity"] == PASS:
            scope = statement.get("scope") if isinstance(statement.get("scope"), dict) else {}
            wanted = (statement.get("consumer_id"), scope.get("tenant"), scope.get("institution"),
                      scope.get("authority_domain"), statement.get("operation"))
            authorized = [entry for entry, grants in valid_signers if any(
                (g.consumer_id, g.tenant, g.institution, g.authority_domain, g.operation) == wanted for g in grants)]
            issuer_id = (authorized or [entry for entry, _ in valid_signers])[0].issuer_id
            mark("authority", None if authorized else "issuer_not_authorized", "no valid signer holds exact authority for this consumer, scope and operation")

        if not isinstance(context, ExpectedContext):
            mark("scope", "selection_scope_mismatch", "expected context is missing or invalid")
        else:
            scope = statement.get("scope") if isinstance(statement.get("scope"), dict) else {}
            if statement.get("consumer_id") != context.consumer_id:
                mark("scope", "selection_consumer_mismatch", "selection names a different consumer")
            elif (scope.get("tenant"), scope.get("institution"), scope.get("authority_domain")) != (
                    context.tenant, context.institution, context.authority_domain):
                mark("scope", "selection_scope_mismatch", "tenant, institution or authority domain differs")
            elif statement.get("operation") != context.operation:
                mark("scope", "selection_operation_mismatch", "selection names a different operation")
            else:
                mark("scope", None)

        interval = statement.get("effective") if isinstance(statement.get("effective"), dict) else {}
        start, end = c.parse_timestamp(interval.get("valid_from")), c.parse_timestamp(interval.get("valid_until"))
        if when is None:
            mark("time", "time_unavailable", "no trusted current time")
        elif start is None or end is None or start >= end:
            mark("time", "selection_expired", "effective interval is invalid")
        elif when < start:
            mark("time", "selection_not_yet_effective", "now is before valid_from")
        elif when >= end:
            mark("time", "selection_expired", "now is at or after valid_until")
        else:
            mark("time", None)

        if trust is not None:
            revoked = (statement.get("selection_id"), statement.get("epoch")) in trust["revoked_selections"]
            mark("revocation", "selection_revoked" if revoked else None, "selection id and epoch are revoked")
            epoch, floor = statement.get("epoch"), trust["floors"].get(statement.get("selection_id"))
            if not c.is_int(epoch) or (floor is not None and epoch < floor):
                mark("epoch", "selection_epoch_stale", "epoch is below the trusted floor")
            else:
                mark("epoch", None)

    first = next((name for name in LAYERS if layers[name] == REFUSE), None)
    required_ok = all(layers[name] == PASS for name in LAYERS if name != "record_binding")
    ok = first is None and required_ok and (record is None or layers["record_binding"] == PASS)
    klass, extra = VerificationReport, {}
    if not ok and first in typed:
        klass, extra = TypedVerificationReport, {"detail_code": typed[first][0], "detail_cause": typed[first][1]}
    return klass(
        ok=ok, code=None if ok else codes.get(first, "selection_missing"),
        detail="" if ok else details.get(first, "verification incomplete"),
        layers=dict(layers), selection_digest=getattr(selection, "statement_digest", None) if statement is not None else None,
        authenticated=authenticated, issuer_id=issuer_id, operationally_authorized=False,
        participation=statement.get("participation") if statement is not None else None,
        **extra,
        bound_record_digest=(statement.get("record") or {}).get("record_digest")
        if statement is not None and layers["record_binding"] == PASS and isinstance(statement.get("record"), dict) else None)


def verify_selection(selection, context, trust, verifier, now, record=None, key_admission=None,
                     contract_version=LEGACY_CONTRACT) -> VerificationReport:
    """Layered technical verification. Never raises; never returns an acceptance on internal error.

    Public-key admission (registry_successor.key_admission) is MANDATORY unless `contract_version` is exactly the legacy
    `r08-v1` default: on every other value, and whenever the envelope says `r08-v2`, the built-in Ed25519 admission check
    is applied to every issuer key when the trust snapshot is admitted, whether or not `key_admission` is supplied.
    `key_admission`, an optional `(alg, public_key) -> bool`, can only add refusals. On the legacy path it keeps its
    old opt-in meaning (None = no admission).
    """
    try:
        return _verify(selection, context, trust, verifier, now, record, key_admission, contract_version)
    except Exception:
        layers = {name: NOT_EVALUATED for name in LAYERS}
        layers["structural"] = REFUSE
        return VerificationReport(False, "field_invalid", "internal verification error", layers, None, False, None, False)
