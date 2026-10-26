"""Layered technical verification of selection statements against explicit trusted inputs (contract section 4).

Non-authorizing and unqualified. Pure and deterministic: time, trust snapshot, verifier and context are injected.
Nothing is hardcoded or discovered: there is no default trust root, key, issuer or verifier. With no verifier the
authenticity layer refuses `verifier_unavailable`; a matching SHA-256 digest is integrity only and never authenticates.
`ok` means technically verified; `operationally_authorized` is always False.
"""
import base64
import binascii
import datetime
import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol

from registry_successor import common as c
from registry_successor import selection as sel_mod
from registry_successor import v2_codes
from registry_successor import v2_selection as v2_sel
from registry_successor.canonical_b64 import decode_canonical_base64
from registry_successor.common import ExpectedContext
from registry_successor.key_admission import (
    DETAIL_KEY_ADMISSION_INVALID, DETAIL_TRUST_SNAPSHOT_MALFORMED, inspect_ed25519_key)

LAYERS = (
    "structural", "integrity", "record_binding", "trust_snapshot", "authenticity",
    "authority", "scope", "time", "revocation", "epoch",
)
LAYERS_V2 = LAYERS + ("disposition",)  # r08-v2 adds a final `disposition` layer (docs/r08-v2-contract.md section 3.1)
PASS, REFUSE, NOT_EVALUATED = "pass", "refuse", "not_evaluated"
SUPPORTED_ALG = "ed25519"

__all__ = [
    "ExpectedContext", "AuthorityGrant", "IssuerEntry", "TrustSnapshot", "SignatureVerifier", "VerificationReport",
    "LAYERS", "LAYERS_V2", "verify_selection", "verify_selection_v2", "TypedVerificationReport", "MAX_SNAPSHOT_VERSION",
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
    detail_stage: Optional[str] = None   # diagnostic metadata only (e.g. "ingest"); never part of any digest
    detail_member: Optional[str] = None  # the member the typed detail is about (e.g. "trust_snapshot_version")


LEGACY_CONTRACT = "r08-v1"
V2_CONTRACT = "r08-v2"


def _admission_mandatory(selection: Any, contract_version: Any) -> bool:
    """Admission is mandatory on every path except the explicit legacy `r08-v1` default. Fail closed: any other or odd
    `contract_version` value, or an envelope that itself says r08-v2, selects the mandatory path."""
    if type(contract_version) is not str or contract_version != LEGACY_CONTRACT:
        return True
    envelope = getattr(selection, "envelope", None)
    if type(envelope) is not dict:
        # Fail toward mandatory: a dict subclass, list, or any other object could declare or hide a version. Only a
        # selection that is not ok with NO envelope at all (structurally refused earlier, legacy shape) stays legacy.
        # only a selection whose `ok` is exactly False/absent with no envelope keeps the frozen legacy shape
        return envelope is not None or getattr(selection, "ok", False) is not False
    declared = envelope.get("contract_version")
    return type(declared) is not str or declared != LEGACY_CONTRACT  # only an exact-str r08-v1 envelope may be legacy


def _private_entry(entry: Any) -> Optional[IssuerEntry]:
    """Mandatory path only: exact-type, single-read private copy of an issuer entry. The public key may be of any type here
    (junk is classified later as key_type / key_length by admission). Returns None for a malformed entry shape."""
    if type(entry) is not IssuerEntry:
        return None
    key_id, issuer_id, alg, public_key, authority = entry.key_id, entry.issuer_id, entry.alg, entry.public_key, entry.authority
    if type(key_id) is not str or type(issuer_id) is not str or type(alg) is not str:
        return None
    if type(authority) not in (tuple, list):
        return None
    grants = []
    for g in authority:
        if type(g) is not AuthorityGrant:
            return None
        fields = (g.consumer_id, g.tenant, g.institution, g.authority_domain, g.operation)
        if any(type(f) is not str for f in fields):
            return None
        grants.append(AuthorityGrant(*fields))
    return IssuerEntry(key_id, issuer_id, alg, public_key, tuple(grants))


MAX_SNAPSHOT_VERSION = 2**53 - 1  # canonical snapshot-version representation bound (N-10(c)): 1 .. 2**53 - 1 inclusive


class _IngestRefusal:
    """Marker returned by `_private_trust` (mandatory path only) when a member is refused at INGESTION, before the snapshot is
    used in projection or authority evaluation. Diagnostic metadata only: stage and member never enter any canonical digest."""
    __slots__ = ("stage", "member")

    def __init__(self, stage: str, member: str):
        self.stage, self.member = stage, member


class _NotSnapshottable(Exception):
    pass


MAX_JSON_NODES = 10000  # total node budget for one private copy; far above any real selection or record (parser caps are lower)


def _json_copy(value: Any, depth: int = 0, state: Optional[dict] = None) -> Any:
    """Mandatory path: private deep copy of a JSON-shaped value using EXACT builtin types only (dict with exact-str keys,
    list, tuple, str, int, bool, None). Any subclass, float, set, bytes or other object raises `_NotSnapshottable`, so a
    stateful or lying object can never reach a later decision. Each node is read once. Fail closed on resource abuse: a
    container reached twice (a cycle OR a shared reference, which a parsed document never has) is refused, and the total
    number of nodes is bounded by MAX_JSON_NODES, so work is linear and bounded."""
    if state is None:
        state = {"seen": set(), "nodes": 0}
    state["nodes"] += 1
    if state["nodes"] > MAX_JSON_NODES or depth > 32:
        raise _NotSnapshottable()
    t = type(value)
    if t is str or t is bool or value is None:
        return value
    if t is int:
        return int(value)
    if t is dict or t is list or t is tuple:
        if id(value) in state["seen"]:
            raise _NotSnapshottable()
        state["seen"].add(id(value))
        if t is dict:
            out = {}
            for k, v in list(value.items()):
                if type(k) is not str:
                    raise _NotSnapshottable()
                out[k] = _json_copy(v, depth + 1, state)
            return out
        return t(_json_copy(v, depth + 1, state) for v in list(value))
    raise _NotSnapshottable()


def _exact_items(container: Any) -> Optional[tuple]:
    """One read of an exact list/tuple/set/frozenset into an immutable tuple, else None."""
    if type(container) not in (list, tuple, set, frozenset):
        return None
    return tuple(container)


def _private_trust(trust: Any):
    """Mandatory path: validate EXACT types and take ONE read of every TrustSnapshot field; everything later uses only the
    returned copy. Same acceptance rules as the legacy normalizer apart from the exact-type requirements."""
    if type(trust) is not TrustSnapshot:
        return None
    snapshot_id, version, valid_until, issuers_in = trust.snapshot_id, trust.version, trust.valid_until, trust.issuers
    revoked_key_ids, revoked_selections, min_epochs = trust.revoked_key_ids, trust.revoked_selections, trust.min_epochs
    if type(version) is not int or not 1 <= version <= MAX_SNAPSHOT_VERSION:  # ingest bound FIRST: strict int, no bool/float/str/subclass
        return _IngestRefusal("ingest", "trust_snapshot_version")
    if type(snapshot_id) is not str or not c.valid_token(snapshot_id):
        return None
    if type(valid_until) is not str:
        return None
    valid_until_dt = c.parse_timestamp(valid_until)
    if valid_until_dt is None:
        return None
    entries = _exact_items(issuers_in) if type(issuers_in) in (list, tuple) else None
    if entries is None:
        return None
    issuers: dict = {}
    for raw in entries:
        entry = _private_entry(raw)
        if entry is None or not c.valid_token(entry.key_id) or not c.valid_token(entry.issuer_id) or entry.key_id in issuers:
            return None
        if not all(c.valid_token(v) for g in entry.authority for v in
                   (g.consumer_id, g.tenant, g.institution, g.authority_domain, g.operation)):
            return None
        issuers[entry.key_id] = (entry, entry.authority)
    keys = _exact_items(revoked_key_ids)
    if keys is None or any(type(k) is not str for k in keys):
        return None
    sels = _exact_items(revoked_selections)
    if sels is None:
        return None
    revoked_sel = set()
    for item in sels:
        if not (type(item) is tuple and len(item) == 2 and type(item[0]) is str and type(item[1]) is int):
            return None
        revoked_sel.add((item[0], int(item[1])))
    if type(min_epochs) is dict:
        pairs = tuple(min_epochs.items())
    elif type(min_epochs) in (list, tuple):
        pairs = tuple(min_epochs)
    else:
        return None
    floors: dict = {}
    for item in pairs:
        if type(item) is not tuple or len(item) != 2:
            return None
        sid, floor = item
        if type(sid) is not str or type(floor) is not int or floor < 1 or sid in floors:
            return None
        floors[sid] = int(floor)
    return {"issuers": issuers, "revoked_keys": frozenset(keys), "revoked_selections": revoked_sel,
            "floors": floors, "valid_until": valid_until_dt, "version": version, "snapshot_id": snapshot_id,
            "valid_until_raw": valid_until}


def _private_selection(selection: Any) -> Any:
    """Mandatory path: an exact-type deep private copy of the parsed selection (statement, digest, signatures). A selection
    whose `ok` is not exactly True, or whose content is not exact JSON-shaped data, becomes a structurally refused result."""
    ok = getattr(selection, "ok", False)
    code = getattr(selection, "code", None)
    code = code if type(code) is str and code in c.CODES else None
    if ok is not True:
        return sel_mod.SelectionResult(False, code or "field_invalid", "selection is not ok")
    try:
        statement = _json_copy(getattr(selection, "statement", None))
        signatures = _json_copy(getattr(selection, "signatures", None))
        digest = getattr(selection, "statement_digest", None)
        if type(digest) is not str or type(statement) is not dict or type(signatures) not in (list, tuple):
            raise _NotSnapshottable()
    except Exception:
        return sel_mod.SelectionResult(False, "field_invalid", "selection content is not exact data")
    return sel_mod.SelectionResult(True, None, "", None, statement, digest, signatures)


def _private_record(record: Any) -> Any:
    """Mandatory path: exact-type deep private copy of a validated record result, or a refused stand-in."""
    from types import SimpleNamespace
    refused = SimpleNamespace(ok=False, record=None, record_digest=None)
    if record is None:
        return None
    try:
        if getattr(record, "ok", False) is not True:
            return refused
        body, digest = _json_copy(getattr(record, "record", None)), getattr(record, "record_digest", None)
        if type(body) is not dict or type(digest) is not str:
            return refused
        return SimpleNamespace(ok=True, record=body, record_digest=digest)
    except Exception:
        return refused


def _private_context(context: Any) -> Any:
    """Mandatory path: exact ExpectedContext with exact-str members, else None (scope refusal)."""
    if type(context) is not ExpectedContext:
        return None
    try:
        members = (context.consumer_id, context.tenant, context.institution, context.authority_domain, context.operation)
    except Exception:  # half-built object
        return None
    if any(type(m) is not str for m in members):
        return None
    return ExpectedContext(*members)


def _private_now(now: Any) -> Optional[datetime.datetime]:
    """Mandatory path: exact aware datetime read once, normalized to a plain UTC datetime (no stateful tzinfo)."""
    if type(now) is not datetime.datetime:
        return None
    try:
        offset = now.utcoffset()
        if now.tzinfo is None or offset is None:
            return None
        return (now.replace(tzinfo=None) - offset).replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def _normalize_trust(trust: Any, mandatory: bool = False) -> Optional[dict]:
    """Return a normalized view of a well-formed snapshot, or None. On the mandatory-admission path a missing, empty or
    wrong-type public key is NOT a shape error here: it is left for `_admission_failure` so it gets the typed
    key_admission_invalid detail (key_type / key_length). The legacy path is unchanged."""
    if mandatory:
        try:
            return _private_trust(trust)  # exact types, one read per field; the legacy code below is untouched
        except Exception:  # e.g. a half-built object: typed as a malformed snapshot, fail closed
            return None
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
        if not isinstance(entry.alg, str) or (not isinstance(entry.public_key, bytes) or not entry.public_key):
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
        if mandatory and cause is None and (type(entry.public_key) is not bytes or not entry.public_key):
            cause = "key_type" if type(entry.public_key) is not bytes else "key_length"  # any alg: never admit junk
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


def _authenticity(statement: dict, selection: Any, trust: dict, verifier: Any, canonical_b64: bool = False, v2: bool = False) -> tuple:
    """Returns (code_or_None, detail, valid) where valid lists every (entry, grants) whose signature verified."""
    from registry_successor import selection as sel_mod
    signatures = getattr(selection, "signatures", None)
    if not isinstance(signatures, (list, tuple)) or not signatures:
        return ("signature_missing", "statement carries no signature", [])
    supported = [s for s in signatures if isinstance(s, dict) and s.get("alg") == SUPPORTED_ALG]
    if not supported:
        return ("signature_algorithm_unsupported", "no ed25519 signature present", [])
    try:
        message = v2_sel.signing_input_v2(statement) if v2 else sel_mod.signing_input(statement)  # r08-v2 signs under its OWN domain
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
            if canonical_b64:
                raw = decode_canonical_base64(text)  # r08-v2 only: exactly the RFC 4648 section 4 spelling
                if raw is None:
                    try:
                        base64.b64decode(text, validate=True)
                        failure = ("signature_invalid", "signature is not canonical base64")
                    except (binascii.Error, ValueError, TypeError):
                        failure = ("signature_invalid", "signature is not valid base64")
            else:  # frozen r08-v1 behaviour, identical to origin/main
                try:
                    raw = base64.b64decode(text, validate=True)
                except (binascii.Error, ValueError, TypeError):
                    raw = None
                    failure = ("signature_invalid", "signature is not valid base64")
            if raw is not None:
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


_FINGERPRINT = re.compile(r"\Asha256:[0-9a-f]{64}\Z")


def _floor_inputs_ok(min_version: Any, last_accepted: Any) -> bool:
    """True when the optional snapshot-floor inputs are well formed (strict types; absent = off)."""
    if min_version is not None and not (type(min_version) is int and 1 <= min_version <= MAX_SNAPSHOT_VERSION):
        return False
    if last_accepted is not None:
        if type(last_accepted) is not tuple or len(last_accepted) != 2:
            return False
        version, fingerprint = last_accepted
        if not (type(version) is int and 1 <= version <= MAX_SNAPSHOT_VERSION):
            return False
        if type(fingerprint) is not str or not _FINGERPRINT.match(fingerprint):
            return False
    return True


def _rebuilt_snapshot(trust: dict) -> TrustSnapshot:
    """The admitted snapshot rebuilt from the verifier's private copy (never the caller's object), for fingerprinting."""
    return TrustSnapshot(
        snapshot_id=trust["snapshot_id"], version=trust["version"], valid_until=trust["valid_until_raw"],
        issuers=tuple(entry for entry, _ in trust["issuers"].values()), revoked_key_ids=frozenset(trust["revoked_keys"]),
        revoked_selections=frozenset(trust["revoked_selections"]), min_epochs=tuple(trust["floors"].items()))


def _floor_outcome(trust: dict, min_version: Any, last_accepted: Any) -> Optional[tuple]:
    """Stateless floor decision (docs/r08-v2-contract.md section 5): stale when older than the external floor, older than the last
    accepted snapshot, or the same version with a different fingerprint. None = acceptable. A fingerprint that cannot be computed
    fails closed as `trust_snapshot_invalid`."""
    stale = ("trust_snapshot_version_stale", "trust snapshot is older than the required floor")
    if min_version is not None and trust["version"] < min_version:
        return stale
    if last_accepted is not None:
        version, fingerprint = last_accepted
        if trust["version"] < version:
            return stale
        if trust["version"] == version:
            try:
                from registry_successor import v2_policy_identity as pid  # lazy: v2_policy_identity imports this module
                same = pid.trust_snapshot_fingerprint_from_verified(_rebuilt_snapshot(trust)) == fingerprint
            except Exception:
                return ("trust_snapshot_invalid", "trust snapshot cannot be fingerprinted")
            if not same:
                return ("trust_snapshot_version_stale", "same version with a different fingerprint")
    return None


def _verify(selection, context, trust_in, verifier, now, record, key_admission=None, contract_version=LEGACY_CONTRACT,
            v2=False, min_trust_snapshot_version=None, last_accepted_snapshot=None) -> VerificationReport:
    names = LAYERS_V2 if v2 else LAYERS
    layers = {name: NOT_EVALUATED for name in names}
    codes: dict = {}
    details: dict = {}
    typed: dict = {}

    def mark(layer: str, code: Optional[str], detail: str = "", typed_detail: Optional[tuple] = None) -> None:
        layers[layer] = PASS if code is None else REFUSE
        if code is not None:
            assert code in (v2_codes.CODES_V2 if v2 else c.CODES), code
            codes[layer] = code
            details[layer] = detail
            if typed_detail is not None:
                typed[layer] = typed_detail

    mandatory = _admission_mandatory(selection, contract_version)  # decided ONCE from the caller's original objects
    envelope_in = getattr(selection, "envelope", None)  # ONE read; only an exact dict can declare a version
    declared = envelope_in.get("contract_version") if type(envelope_in) is dict else None
    wrong_contract = (type(declared) is not str or declared != V2_CONTRACT) if v2 else (type(declared) is str and declared == V2_CONTRACT)
    if v2 and type(envelope_in) is not dict:
        wrong_contract = True
    if mandatory:  # exact types + one read: every later decision uses these private copies only
        selection, record, context = _private_selection(selection), _private_record(record), _private_context(context)
        when = _private_now(now)
    else:
        when = _aware(now)
    if wrong_contract and getattr(selection, "ok", False) is True:  # cross-version: never verified, never signed-over
        selection = sel_mod.SelectionResult(False, "contract_unsupported", "selection envelope is not of the entry point's contract version")
    statement = _statement_view(selection)
    shape_code = None
    if statement is not None and v2:  # defense in depth: re-check the closed r08-v2 statement shape on the private copy
        shape_code = "field_invalid" if "disposition" not in statement else v2_sel._statement_code_v2(statement)
    if statement is None:
        given = getattr(selection, "code", None)
        mark("structural", given if given in (v2_codes.CODES_V2 if v2 else c.CODES) else "field_invalid", "selection is missing or not structurally valid")
    elif shape_code is not None:
        mark("structural", shape_code, "statement is not a valid r08-v2 statement")
        statement = None
    else:
        mark("structural", None)
        if c.digest(statement) == selection.statement_digest:
            mark("integrity", None)
        else:
            mark("integrity", "digest_mismatch", "statement digest does not match canonical statement")
        if record is not None and statement.get("disposition") != "withdraw":  # a withdrawal pins no record
            bad = _record_binding(statement, record)
            mark("record_binding", *(bad if bad else (None,)))

    trust = _normalize_trust(trust_in, mandatory)
    ingest = trust if isinstance(trust, _IngestRefusal) else None
    if ingest is not None:
        trust = None
    admission = None if trust is None else _admission_failure(trust, key_admission, mandatory)
    if trust_in is None:
        mark("trust_snapshot", "trust_snapshot_missing", "no trust snapshot supplied")
    elif ingest is not None:
        mark("trust_snapshot", "trust_snapshot_invalid", "trust snapshot is malformed",
             (DETAIL_TRUST_SNAPSHOT_MALFORMED, None, ingest.stage, ingest.member))
    elif trust is None:
        mark("trust_snapshot", "trust_snapshot_invalid", "trust snapshot is malformed",
             (DETAIL_TRUST_SNAPSHOT_MALFORMED, None) if mandatory else None)  # legacy r08-v1 shape stays byte-frozen
    elif admission is not None:
        mark("trust_snapshot", "trust_snapshot_invalid", admission[0], (DETAIL_KEY_ADMISSION_INVALID, admission[1]))
    elif when is None:
        mark("trust_snapshot", "time_unavailable", "no trusted current time")
    elif when >= trust["valid_until"]:
        mark("trust_snapshot", "trust_snapshot_expired", "trust snapshot is past valid_until")
    elif v2 and not _floor_inputs_ok(min_trust_snapshot_version, last_accepted_snapshot):
        mark("trust_snapshot", "trust_snapshot_invalid", "snapshot floor input is malformed")
    else:
        floor = _floor_outcome(trust, min_trust_snapshot_version, last_accepted_snapshot) if v2 else None
        mark("trust_snapshot", *(floor if floor else (None,)))
    trust_ok = layers["trust_snapshot"] == PASS

    authenticated, issuer_id, valid_signers = False, None, []
    if statement is not None:
        if verifier is None:
            mark("authenticity", "verifier_unavailable", "no signature verifier supplied; digest match is not authentication")
        elif trust_ok:
            code, detail, valid_signers = _authenticity(statement, selection, trust, verifier, mandatory, v2)
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

    withdrawal = v2 and statement is not None and statement.get("disposition") == "withdraw"
    if v2 and statement is not None and all(layers[n] == PASS for n in LAYERS if n != "record_binding") and (
            withdrawal or record is None or layers["record_binding"] == PASS):
        if withdrawal:  # authenticated, in scope and in time: a withdrawal is a typed refusal, never a success
            mark("disposition", "selection_withdrawn", "the authenticated statement withdraws the selection")
        else:
            mark("disposition", None)
    first = next((name for name in names if layers[name] == REFUSE), None)
    required_ok = all(layers[name] == PASS for name in names if name != "record_binding")
    ok = first is None and required_ok and (withdrawal is False) and (record is None or layers["record_binding"] == PASS)
    klass, extra = VerificationReport, {}
    if not ok and first in typed:
        td = typed[first]
        klass, extra = TypedVerificationReport, {"detail_code": td[0], "detail_cause": td[1]}
        if len(td) == 4:
            extra.update(detail_stage=td[2], detail_member=td[3])
    return klass(
        ok=ok, code=None if ok else codes.get(first, "selection_missing"),
        detail="" if ok else details.get(first, "verification incomplete"),
        layers=dict(layers), selection_digest=getattr(selection, "statement_digest", None) if statement is not None else None,
        authenticated=authenticated, issuer_id=issuer_id, operationally_authorized=False,
        participation=statement.get("participation") if statement is not None else None,
        **extra,
        bound_record_digest=(statement.get("record") or {}).get("record_digest")
        if statement is not None and layers["record_binding"] == PASS and isinstance(statement.get("record"), dict) else None)


def verify_selection_v2(selection, context, trust, verifier, now, record=None, key_admission=None, *,
                        min_trust_snapshot_version=None, last_accepted_snapshot=None) -> VerificationReport:
    """The r08-v2 verification entry point. It takes NO `contract_version` parameter and hardwires `V2_CONTRACT`, so a caller
    can neither omit the version nor substitute one, and nothing in the selection or envelope can steer it to the legacy
    path. It shares `_verify` with `verify_selection`, the single verification and admission implementation: no second authority.
    Optional keyword-only snapshot-floor inputs (docs/r08-v2-contract.md section 5; both default off): `min_trust_snapshot_version`
    (an int) and `last_accepted_snapshot` (a `(version, fingerprint)` tuple). The verifier stays stateless; the caller supplies them."""
    try:
        return _verify(selection, context, trust, verifier, now, record, key_admission, V2_CONTRACT, True,
                       min_trust_snapshot_version, last_accepted_snapshot)
    except Exception:
        layers = {name: NOT_EVALUATED for name in LAYERS_V2}
        layers["structural"] = REFUSE
        return VerificationReport(False, "field_invalid", "internal verification error", layers, None, False, None, False)


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
        if type(contract_version) is str and contract_version == V2_CONTRACT:  # one implementation, one v2 semantics
            return _verify(selection, context, trust, verifier, now, record, key_admission, V2_CONTRACT, True)
        return _verify(selection, context, trust, verifier, now, record, key_admission, contract_version)
    except Exception:
        layers = {name: NOT_EVALUATED for name in LAYERS}
        layers["structural"] = REFUSE
        return VerificationReport(False, "field_invalid", "internal verification error", layers, None, False, None, False)
