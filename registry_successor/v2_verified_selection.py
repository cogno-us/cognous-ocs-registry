"""Record-bound, floor-bound, fully layered verification of an `r08-v2` selection TEXT (RW-01-F4-PoC, Registry side).

Why this module exists. `decision.verify_and_decide_v2` drops the `VerificationReport` and exposes no snapshot floor input, and
`verify.verify_selection_v2` returns `ok=True` when no record is supplied (`record_binding` stays `not_evaluated`). A consumer that
wants "this exact signed selection, bound to this exact record, under explicit snapshot floors" therefore needs ONE place that
composes the existing public functions and states the admission conjunction. This is that place. It adds no verification logic of
its own: the single verifier is `verify.verify_selection_v2`; this module only (1) makes the record and both floors MANDATORY inputs,
(2) requires every one of the eleven `LAYERS_V2` layers to be exactly "pass", and (3) copies the result into an immutable value.

Scope and non-claims (read before relying on it):
  * Pure. No clock (the caller injects `now`), no I/O, no logging, no key material, no signer, no trust root, no default verifier.
  * It composes only existing public Registry functions and introduces no reason code: every `code` is a member of
    `v2_codes.CODES_V2` that an existing path already emits.
  * `admitted` is a TECHNICAL verification result against caller-supplied trust inputs. The trust snapshot carries no signature and
    has no origin evidence here; `admitted` is only as strong as the independence of the snapshot, the verifier, the floors, the
    context and `now` that the ENFORCING CONSUMER supplied. The module cannot tell whether the verifier it was handed is genuine.
  * `operationally_authorized` stays False everywhere. Admission is not operational authorization.
  * It never builds signing bytes; the canonical bytes that were signed are computed only inside `verify.py` (via the Registry's own
    canonicaliser), so a non-ASCII statement is verified over exactly the bytes the Registry defines.
  * Statement-derived fields (issuer, selection id, epoch, scope, validity, record identity) are filled ONLY when `admitted` is True;
    on a refusal they are None so an unauthenticated claim cannot be mistaken for a verified one.
"""
import copy
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from registry_successor import common as c
from registry_successor import families
from registry_successor import v2_age_bounds as ab
from registry_successor import v2_codes
from registry_successor import v2_policy_identity as pid
from registry_successor import v2_selection as v2_sel
from registry_successor import verify as verify_mod
from registry_successor import decision as decision_mod
from registry_successor.record import RecordResult

__all__ = ["VerifiedSelectionV2", "F4EffectivePolicy", "verify_selection_text_v2", "verify_f4_selection_v2",
           "recompute_f4_effective_policy"]

_LAYERS = verify_mod.LAYERS_V2
_PASS, _NOT_EVALUATED, _REFUSE = verify_mod.PASS, verify_mod.NOT_EVALUATED, verify_mod.REFUSE
_SELECT = "select"


@dataclass(frozen=True)
class VerifiedSelectionV2:
    """Immutable result. `admitted` is True iff the single conjunction in `_conjunction_holds` holds; `code` is None iff admitted.
    Statement-derived members are None unless admitted. `layers` is a tuple of (name, value) pairs in `LAYERS_V2` order (never the
    verifier's mutable dict). `record` is a deep copy of the validated record body, present only when admitted."""
    admitted: bool
    code: Optional[str]
    detail: str
    layers: Tuple[Tuple[str, str], ...]
    report_ok: bool
    authenticated: bool
    selection_digest: Optional[str]
    required_family: Optional[str]
    required_participation: Optional[str]
    min_trust_snapshot_version: Optional[int]
    last_accepted_snapshot: Optional[Tuple[int, str]]
    issuer_id: Optional[str] = None
    participation: Optional[str] = None
    selection_id: Optional[str] = None
    epoch: Optional[int] = None
    family: Optional[str] = None
    consumer_id: Optional[str] = None
    operation: Optional[str] = None
    scope: Optional[Tuple[str, str, str]] = None
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    record_id: Optional[str] = None
    record_version: Optional[int] = None
    record_digest: Optional[str] = None
    trust_snapshot_id: Optional[str] = None
    trust_snapshot_version: Optional[int] = None
    trust_snapshot_fingerprint: Optional[str] = None
    epoch_floor_applied: bool = False
    detail_code: Optional[str] = None
    detail_cause: Optional[str] = None
    record: Optional[dict] = None


@dataclass(frozen=True)
class F4EffectivePolicy:
    ok: bool
    code: Optional[str]
    effective: Optional[dict]
    effective_policy_digest: Optional[str]


def _known(code: Any, fallback: str = "selection_missing") -> str:
    return code if type(code) is str and code in v2_codes.CODES_V2 else fallback


def _all_not_evaluated(structural: str = _NOT_EVALUATED) -> Tuple[Tuple[str, str], ...]:
    return tuple((name, structural if name == "structural" else _NOT_EVALUATED) for name in _LAYERS)


def _refused(code: str, detail: str, layers=None, report_ok: bool = False, authenticated: bool = False, selection_digest=None,
             required_family=None, required_participation=None, min_version=None, last_accepted=None, detail_code=None,
             detail_cause=None) -> VerifiedSelectionV2:
    return VerifiedSelectionV2(
        admitted=False, code=_known(code, "field_invalid"), detail=detail if type(detail) is str else "",
        layers=layers if layers is not None else _all_not_evaluated(), report_ok=report_ok is True,
        authenticated=authenticated is True, selection_digest=selection_digest if type(selection_digest) is str else None,
        required_family=required_family if type(required_family) is str else None,
        required_participation=required_participation if type(required_participation) is str else None,
        min_trust_snapshot_version=min_version if type(min_version) is int else None,
        last_accepted_snapshot=last_accepted if type(last_accepted) is tuple else None,
        detail_code=detail_code if type(detail_code) is str else None, detail_cause=detail_cause if type(detail_cause) is str else None)


def _layer_pairs(report_layers: Any) -> Tuple[Tuple[str, str], ...]:
    """The verifier's layers as an immutable tuple in `LAYERS_V2` order. Anything that is not exactly one of the three layer values
    is recorded as not_evaluated, so it can never count as a pass."""
    out = []
    for name in _LAYERS:
        value = report_layers.get(name) if isinstance(report_layers, dict) else None
        out.append((name, value if type(value) is str and value in (_PASS, _REFUSE, _NOT_EVALUATED) else _NOT_EVALUATED))
    return tuple(out)


def _floors_well_formed(min_version: Any, last_accepted: Any) -> bool:
    # `min_trust_snapshot_version` is REQUIRED here (None is not "off"); both inputs are validated by the verifier's own predicate.
    return min_version is not None and verify_mod._floor_inputs_ok(min_version, last_accepted)


def _conjunction_holds(report: Any, layers: Tuple[Tuple[str, str], ...], statement: Any, rec: Any, required_participation: str) -> bool:
    """The ONE admission conjunction (family and participation mismatches are classified separately, before this is consulted):
    report.ok True AND report.code None AND authenticated True AND all eleven layers exactly "pass" AND issuer_id an exact str AND
    operationally_authorized exactly False AND statement disposition "select" AND bound_record_digest present and equal to the
    digest of the record parsed from the supplied record text AND that digest equal to the statement's own record pin."""
    if not (report.ok is True and report.code is None and report.authenticated is True):
        return False
    if len(layers) != len(_LAYERS) or any(value != _PASS for _, value in layers):
        return False
    if type(report.issuer_id) is not str or report.operationally_authorized is not False:
        return False
    if type(statement) is not dict or statement.get("disposition") != _SELECT:
        return False
    if report.participation != required_participation:
        return False
    bound = report.bound_record_digest
    if type(bound) is not str or bound != rec.record_digest:
        return False
    pin = statement.get("record")
    return type(pin) is dict and pin.get("record_digest") == bound


def _trust_echo(trust: Any, selection_id: Any) -> Tuple[Optional[str], Optional[int], Optional[str], bool]:
    """(snapshot id, version, fingerprint, epoch_floor_applied) from the private copy of the snapshot; only called after the
    trust_snapshot layer passed. Any failure yields Nones (the echo is informative, never an input to admission)."""
    try:
        if type(trust) is not verify_mod.TrustSnapshot:
            return None, None, None, False
        try:
            fingerprint = pid.trust_snapshot_fingerprint_from_verified(trust)
        except Exception:
            fingerprint = None
        try:
            floors = dict(trust.min_epochs)
            floor_applied = type(selection_id) is str and selection_id in floors
        except Exception:
            floor_applied = False
        return trust.snapshot_id, trust.version, fingerprint, floor_applied
    except Exception:
        return None, None, None, False


def verify_selection_text_v2(selection_text: Any, record_text: Any, context: Any, trust: Any, verifier: Any, now: Any, *,
                             min_trust_snapshot_version: Any, last_accepted_snapshot: Any, required_family: Any,
                             required_participation: Any = "required", key_admission: Any = None) -> VerifiedSelectionV2:
    """Verify the ORIGINAL selection text against the ORIGINAL record text under explicit floors. Pure; never raises; a record and
    `min_trust_snapshot_version` are mandatory (a missing or malformed floor is `trust_snapshot_invalid`, never "floor off");
    `last_accepted_snapshot` must be None (bootstrap, recorded as not applied) or a `(int, "sha256:...")` tuple."""
    min_v = min_trust_snapshot_version if type(min_trust_snapshot_version) is int else None
    last = last_accepted_snapshot if type(last_accepted_snapshot) is tuple else None
    fam = required_family if type(required_family) is str else None
    part = required_participation if type(required_participation) is str else None
    try:
        return _verify(selection_text, record_text, context, trust, verifier, now, min_trust_snapshot_version,
                       last_accepted_snapshot, required_family, required_participation, key_admission)
    except Exception:
        return _refused("field_invalid", "internal verification error", required_family=fam, required_participation=part,
                        min_version=min_v, last_accepted=last)


def _verify(selection_text, record_text, context, trust, verifier, now, min_version, last_accepted, required_family,
            required_participation, key_admission) -> VerifiedSelectionV2:
    fam = required_family if type(required_family) is str else None
    part = required_participation if type(required_participation) is str else None
    echo = dict(required_family=fam, required_participation=part,
                min_version=min_version if type(min_version) is int else None,
                last_accepted=last_accepted if type(last_accepted) is tuple else None)
    if fam is None or families.lookup_v2(fam) is None:
        return _refused("family_unsupported", "required family is not a registered r08-v2 family", **echo)
    if part is None or part not in c.PARTICIPATION:
        return _refused("participation_mismatch", "required participation is not required or optional", **echo)
    if not _floors_well_formed(min_version, last_accepted):
        return _refused("trust_snapshot_invalid", "snapshot floor inputs are missing or malformed", **echo)
    sel = v2_sel.parse_selection_envelope_v2(selection_text)
    if sel.ok is not True:
        return _refused(sel.code, sel.detail, layers=_all_not_evaluated(_REFUSE), **echo)
    rec = decision_mod.validate_record_text_v2(record_text)
    private_trust = trust
    if type(trust) is verify_mod.TrustSnapshot:
        try:
            private_trust = copy.deepcopy(trust)  # one read; verify and echo use the same copy
        except Exception:
            private_trust = trust  # uncopyable: the verifier's own ingestion then refuses it with a typed code
    report = verify_mod.verify_selection_v2(sel, context, private_trust, verifier, now, rec, key_admission,
                                            min_trust_snapshot_version=min_version, last_accepted_snapshot=last_accepted)
    layers = _layer_pairs(getattr(report, "layers", None))
    base = dict(layers=layers, report_ok=getattr(report, "ok", False), authenticated=getattr(report, "authenticated", False),
                selection_digest=getattr(report, "selection_digest", None), detail_code=getattr(report, "detail_code", None),
                detail_cause=getattr(report, "detail_cause", None), **echo)
    if not isinstance(report, verify_mod.VerificationReport):
        return _refused("field_invalid", "verifier returned an unexpected report", **{**base, "layers": _all_not_evaluated(_REFUSE)})
    if rec.ok is not True:
        return _refused(rec.code, rec.detail or "record is not valid", **base)
    statement = sel.statement
    if statement.get("family") != fam or rec.record.get("family") != fam:
        return _refused("family_unsupported", "statement or record family is not the required family", **base)
    if report.participation != part:
        return _refused("participation_mismatch", "selection participation is not the required participation", **base)
    if not _conjunction_holds(report, layers, statement, rec, part):
        return _refused(report.code if report.code is not None else "selection_missing",
                        report.detail if type(report.detail) is str and report.detail else "verification incomplete", **base)
    snap_id, snap_version, fingerprint, floor_applied = _trust_echo(private_trust, statement["selection_id"])
    pin, eff, scope = statement["record"], statement["effective"], statement["scope"]
    return VerifiedSelectionV2(
        admitted=True, code=None, detail="", layers=layers, report_ok=True, authenticated=True, selection_digest=report.selection_digest,
        required_family=fam, required_participation=part, min_trust_snapshot_version=min_version, last_accepted_snapshot=last_accepted,
        issuer_id=report.issuer_id, participation=report.participation, selection_id=statement["selection_id"], epoch=statement["epoch"],
        family=statement["family"], consumer_id=statement["consumer_id"], operation=statement["operation"],
        scope=(scope["tenant"], scope["institution"], scope["authority_domain"]), valid_from=eff["valid_from"], valid_until=eff["valid_until"],
        record_id=pin["record_id"], record_version=pin["record_version"], record_digest=report.bound_record_digest,
        trust_snapshot_id=snap_id, trust_snapshot_version=snap_version, trust_snapshot_fingerprint=fingerprint,
        epoch_floor_applied=floor_applied, record=copy.deepcopy(rec.record))


def verify_f4_selection_v2(selection_text: Any, record_text: Any, context: Any, trust: Any, verifier: Any, now: Any, *,
                           min_trust_snapshot_version: Any, last_accepted_snapshot: Any, key_admission: Any = None) -> VerifiedSelectionV2:
    """F4 shorthand: family `f4-control-plane-age-bounds`, participation "required"."""
    return verify_selection_text_v2(selection_text, record_text, context, trust, verifier, now,
                                    min_trust_snapshot_version=min_trust_snapshot_version, last_accepted_snapshot=last_accepted_snapshot,
                                    required_family=ab.FAMILY_F4, required_participation="required", key_admission=key_admission)


def _unusable(verified: Any) -> Optional[str]:
    """None when `verified` is a consistent admitted F4 result, else the refusal code. A hand-built or mutated result is re-checked,
    not trusted: layers, code, family, record shape and the record digest are recomputed here."""
    if type(verified) is not VerifiedSelectionV2 or verified.admitted is not True:
        return _known(getattr(verified, "code", None))
    if verified.code is not None or any(value != _PASS for _, value in verified.layers) or len(verified.layers) != len(_LAYERS):
        return "selection_missing"
    record = verified.record
    if verified.family != ab.FAMILY_F4 or type(record) is not dict or record.get("family") != ab.FAMILY_F4:
        return "family_unsupported"
    if type(verified.record_digest) is not str or record.get("record_digest") != verified.record_digest \
            or c.digest({k: v for k, v in record.items() if k != "record_digest"}) != verified.record_digest:
        return "digest_mismatch"
    return None


def recompute_f4_effective_policy(verified: Any, host_ages: Any) -> F4EffectivePolicy:
    """Recompute the F4 effective values and `effective_policy_digest` from an ADMITTED result and the host's own ages.
    `host_ages` is an INDEPENDENT input of the enforcing host (exact dict of the two age members); it must never come from the bundle.
    Same call sequence as the F4 path of `decision.verify_and_decide_v2`. The digest is integrity of the composed values only; it is
    not evidence of Registry origin. Never raises."""
    try:
        refusal = _unusable(verified)
        if refusal is not None:
            return F4EffectivePolicy(False, refusal, None, None)
        if type(host_ages) is not dict:  # stricter than the composer: an exact dict, never a subclass or a stateful mapping
            return F4EffectivePolicy(False, "composition_caller_invalid", None, None)
        rec = RecordResult(True, None, "", copy.deepcopy(verified.record), verified.record_digest)
        comp = families.compose_for(families.CONTRACT_V2, host_ages, rec)
        if comp.ok is not True or comp.deny_all is not False or type(comp.effective) is not dict:
            return F4EffectivePolicy(False, _known(comp.code, "composition_record_invalid"), None, None)
        return F4EffectivePolicy(True, None, dict(comp.effective), pid.effective_policy_digest(ab.FAMILY_F4, comp.effective))
    except Exception:
        return F4EffectivePolicy(False, "field_invalid", None, None)
