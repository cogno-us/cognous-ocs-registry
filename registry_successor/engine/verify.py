"""Layered selection verification of the parameterised engine (docs/r08-v7-contract.md section 3).

`verify_selection(profile, ...)` runs the SAME layered verification, in the SAME order with the SAME codes, as the frozen `v6_verify.verify_selection_v6`
(structural, integrity, record_binding, trust_snapshot, authenticity, authority, scope, time, revocation, epoch, disposition; mandatory key admission,
exact-type private copies, canonical base64, optional snapshot floor) with exactly three profile-specific differences:
  * the envelope must declare exactly `profile.version` (an envelope of any other contract version refuses `contract_unsupported` and is never verified);
  * the closed statement shape is `selection.statement_code(profile, ...)` (the profile's family table);
  * the signed message is `selection.signing_input(profile, ...)`, so a signature made over another contract's domain never verifies and the reverse.
The frozen `verify.py` is not edited; its contract-agnostic helpers (private copies, trust normalization, key admission, record binding, snapshot floor)
are imported and shared. Vocabulary: `CODES_V2` (no new code). Non-authorizing; unqualified.
"""
import base64
import binascii
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import selection as sel_mod
from registry_successor import v2_codes
from registry_successor import verify as v
from registry_successor.canonical_b64 import decode_canonical_base64
from registry_successor.common import ExpectedContext
from registry_successor.engine import profile as p
from registry_successor.engine import selection as sel_e
from registry_successor.key_admission import DETAIL_KEY_ADMISSION_INVALID, DETAIL_TRUST_SNAPSHOT_MALFORMED

LAYERS = v.LAYERS_V2
PASS, REFUSE, NOT_EVALUATED = v.PASS, v.REFUSE, v.NOT_EVALUATED
CODES = v2_codes.CODES_V2

__all__ = ["LAYERS", "CODES", "verify_selection"]


def _authenticity(profile: p.ContractProfile, statement: dict, selection: Any, trust: dict, verifier: Any) -> tuple:
    """(code_or_None, detail, valid) where valid lists every (entry, grants) whose signature verified. Signs over the profile's selection domain only; the
    signature text must be canonical base64."""
    signatures = getattr(selection, "signatures", None)
    if not isinstance(signatures, (list, tuple)) or not signatures:
        return ("signature_missing", "statement carries no signature", [])
    supported = [s for s in signatures if isinstance(s, dict) and s.get("alg") == v.SUPPORTED_ALG]
    if not supported:
        return ("signature_algorithm_unsupported", "no ed25519 signature present", [])
    try:
        message = sel_e.signing_input(profile, statement)
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
            failure = None
            raw = decode_canonical_base64(text)
            if raw is None:
                try:
                    base64.b64decode(text, validate=True)
                    failure = ("signature_invalid", "signature is not canonical base64")
                except (binascii.Error, ValueError, TypeError):
                    failure = ("signature_invalid", "signature is not valid base64")
            if raw is not None:
                try:
                    good = verifier.verify(entry.alg, entry.public_key, message, raw) if entry.alg == v.SUPPORTED_ALG else False
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


def _verify(profile, selection, context, trust_in, verifier, now, record, key_admission=None,
               min_trust_snapshot_version=None, last_accepted_snapshot=None) -> v.VerificationReport:
    layers = {name: NOT_EVALUATED for name in LAYERS}
    codes: dict = {}
    details: dict = {}
    typed: dict = {}

    def mark(layer: str, code: Optional[str], detail: str = "", typed_detail: Optional[tuple] = None) -> None:
        layers[layer] = PASS if code is None else REFUSE
        if code is not None:
            assert code in CODES, code
            codes[layer] = code
            details[layer] = detail
            if typed_detail is not None:
                typed[layer] = typed_detail

    mandatory = True  # key admission is always mandatory on the engine path
    envelope_in = getattr(selection, "envelope", None)  # ONE read; only an exact dict can declare a version
    declared = envelope_in.get("contract_version") if type(envelope_in) is dict else None
    wrong_contract = type(envelope_in) is not dict or type(declared) is not str or declared != profile.version
    selection, record, context = v._private_selection(selection), v._private_record(record), v._private_context(context)
    when = v._private_now(now)
    if wrong_contract and getattr(selection, "ok", False) is True:  # cross-version: never verified, never signed-over
        selection = sel_mod.SelectionResult(False, "contract_unsupported", "selection envelope is not of the entry point's contract version")
    statement = v._statement_view(selection)
    shape_code = None
    if statement is not None:  # defense in depth: re-check the closed statement shape of the profile on the private copy
        shape_code = "field_invalid" if "disposition" not in statement else sel_e.statement_code(profile, statement)
    if statement is None:
        given = getattr(selection, "code", None)
        mark("structural", given if given in CODES else "field_invalid", "selection is missing or not structurally valid")
    elif shape_code is not None:
        mark("structural", shape_code, "statement is not a valid %s statement" % profile.version)
        statement = None
    else:
        mark("structural", None)
        if c.digest(statement) == selection.statement_digest:
            mark("integrity", None)
        else:
            mark("integrity", "digest_mismatch", "statement digest does not match canonical statement")
        if record is not None and statement.get("disposition") != "withdraw":  # a withdrawal pins no record
            bad = v._record_binding(statement, record)
            mark("record_binding", *(bad if bad else (None,)))

    trust = v._normalize_trust(trust_in, mandatory)
    ingest = trust if isinstance(trust, v._IngestRefusal) else None
    if ingest is not None:
        trust = None
    admission = None if trust is None else v._admission_failure(trust, key_admission, mandatory)
    if trust_in is None:
        mark("trust_snapshot", "trust_snapshot_missing", "no trust snapshot supplied")
    elif ingest is not None:
        mark("trust_snapshot", "trust_snapshot_invalid", "trust snapshot is malformed",
             (DETAIL_TRUST_SNAPSHOT_MALFORMED, None, ingest.stage, ingest.member))
    elif trust is None:
        mark("trust_snapshot", "trust_snapshot_invalid", "trust snapshot is malformed", (DETAIL_TRUST_SNAPSHOT_MALFORMED, None))
    elif admission is not None:
        mark("trust_snapshot", "trust_snapshot_invalid", admission[0], (DETAIL_KEY_ADMISSION_INVALID, admission[1]))
    elif when is None:
        mark("trust_snapshot", "time_unavailable", "no trusted current time")
    elif when >= trust["valid_until"]:
        mark("trust_snapshot", "trust_snapshot_expired", "trust snapshot is past valid_until")
    elif not v._floor_inputs_ok(min_trust_snapshot_version, last_accepted_snapshot):
        mark("trust_snapshot", "trust_snapshot_invalid", "snapshot floor input is malformed")
    else:
        floor = v._floor_outcome(trust, min_trust_snapshot_version, last_accepted_snapshot)
        mark("trust_snapshot", *(floor if floor else (None,)))
    trust_ok = layers["trust_snapshot"] == PASS

    authenticated, issuer_id, valid_signers = False, None, []
    if statement is not None:
        if verifier is None:
            mark("authenticity", "verifier_unavailable", "no signature verifier supplied; digest match is not authentication")
        elif trust_ok:
            code, detail, valid_signers = _authenticity(profile, statement, selection, trust, verifier)
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

    withdrawal = statement is not None and statement.get("disposition") == "withdraw"
    if statement is not None and all(layers[n] == PASS for n in v.LAYERS if n != "record_binding") and (
            withdrawal or record is None or layers["record_binding"] == PASS):
        if withdrawal:  # authenticated, in scope and in time: a withdrawal is a typed refusal, never a success
            mark("disposition", "selection_withdrawn", "the authenticated statement withdraws the selection")
        else:
            mark("disposition", None)
    first = next((name for name in LAYERS if layers[name] == REFUSE), None)
    required_ok = all(layers[name] == PASS for name in LAYERS if name != "record_binding")
    ok = first is None and required_ok and (withdrawal is False) and (record is None or layers["record_binding"] == PASS)
    klass, extra = v.VerificationReport, {}
    if not ok and first in typed:
        td = typed[first]
        klass, extra = v.TypedVerificationReport, {"detail_code": td[0], "detail_cause": td[1]}
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


def verify_selection(profile: p.ContractProfile, selection, context, trust, verifier, now, record=None, key_admission=None, *,
                     min_trust_snapshot_version=None, last_accepted_snapshot=None) -> v.VerificationReport:
    """The engine verification entry point for one profile. It takes NO `contract_version` parameter: the contract is `profile.version`, so no caller can
    omit or substitute it. Never raises on hostile input (a non-profile is a programming error); never accepts on error."""
    p.require_profile(profile)
    try:
        return _verify(profile, selection, context, trust, verifier, now, record, key_admission, min_trust_snapshot_version, last_accepted_snapshot)
    except Exception:
        layers = {name: NOT_EVALUATED for name in LAYERS}
        layers["structural"] = REFUSE
        return v.VerificationReport(False, "field_invalid", "internal verification error", layers, None, False, None, False)
