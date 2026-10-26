"""Per-operation policy outcome for contract `r08-v1` (docs/r08-s01-contract.md section 5).

Participation is chosen per operation. Kinds:
  applied / applied_deny_all     a technically verified selection and valid record composed with the caller policy.
  overlay_not_applied            OPTIONAL operations only: any refusal leaves the caller policy unchanged. This is explicitly
                                 NOT denial and is not evidence of enforcement (frozen S04 semantics).
  required_policy_unavailable    REQUIRED operations only: any refusal. The caller policy is NEVER returned. Conceptually HOLD;
                                 the mapping to component failure classes is open decision LD-02.
`operationally_authorized` is always False: technical verification is not operational authorization.
"""
from dataclasses import dataclass, fields
from typing import Any, Optional

from registry_successor import common as c
from registry_successor import families
from registry_successor import record as record_mod
from registry_successor import selection as selection_mod
from registry_successor import v2_codes
from registry_successor import v2_selection as v2_selection_mod
from registry_successor import verify as verify_mod


@dataclass(frozen=True)
class PolicyDecision:
    kind: str
    effective: Optional[dict] = None
    deny_all: bool = False
    deny_all_fields: tuple = ()
    code: Optional[str] = None
    detail: str = ""
    caller_unchanged: bool = False
    operationally_authorized: bool = False


@dataclass(frozen=True)
class TypedPolicyDecision(PolicyDecision):
    """A refusal that also carries the typed sub-cause of its reason code (not a reason code). Returned only for a refusal
    whose verification report carried one; all other decisions keep the base class and its frozen serialized shape."""
    detail_code: Optional[str] = None
    detail_cause: Optional[str] = None
    detail_stage: Optional[str] = None   # diagnostic metadata only (never in a digest)
    detail_member: Optional[str] = None


def _refusal(participation: Any, caller: Any, code: str, detail: str = "", typed: Any = None, codes: Any = c.CODES) -> PolicyDecision:
    base = _plain_refusal(participation, caller, code, detail, codes)
    if typed is None:
        return base
    return TypedPolicyDecision(*(getattr(base, f.name) for f in fields(PolicyDecision)), detail_code=typed[0], detail_cause=typed[1],
                               detail_stage=typed[2] if len(typed) > 2 else None, detail_member=typed[3] if len(typed) > 2 else None)


def _plain_refusal(participation: Any, caller: Any, code: str, detail: str = "", codes: Any = c.CODES) -> PolicyDecision:
    assert code in codes, code
    if participation == "optional":
        normalized = families.lookup(families.V1_DEFAULT_FAMILY).caller_normalizer(caller)
        return PolicyDecision("overlay_not_applied", normalized if normalized is not None else caller, False, (), code,
                              detail or "optional overlay not applied; caller policy unchanged (not denial)", True)
    return PolicyDecision("required_policy_unavailable", None, False, (), code, detail, False)


REV2_CODES = ("not_activated", "policy_identity_mismatch", "store_unknown")  # the three additive codes of `r08-v2-reasons/2` (v2_codes.CODES_V2_REV2)


def refusal_rev2(participation: Any, code: str, detail: str = "") -> PolicyDecision:
    """The explicit revision-2 refusal path (Amendment 1 section 6.7(e) items 1 and 3; Architect Batch 6 rulings 4.7 and N-12). It takes ONLY a revision-2
    additive code (anything else is a ValueError, a programmer error: revision-1 causes keep going through `_refusal`) and passes the code through UNCHANGED
    (it is never remapped to an existing code). A revision-2 code is NEVER an optional fallback: none yields `overlay_not_applied` and none returns or
    leaves the caller policy usable, whatever the participation; `store_unknown` is HOLD (UNKNOWN_FAIL_CLOSED), `not_activated` and `policy_identity_mismatch`
    are REFUSE, and all three are `required_policy_unavailable` with no policy. A participation that is neither required nor optional is refused as
    `participation_mismatch` (a revision-1 code), as everywhere else. Technical refusal only: `operationally_authorized` is False."""
    if type(code) is not str or code not in REV2_CODES:
        raise ValueError("not a revision-2 additive code")
    if type(participation) is not str or participation not in c.PARTICIPATION:  # exact str BEFORE membership: a hostile `__eq__` is never called
        return _refusal("required", None, "participation_mismatch", "operation participation is not required or optional")
    return PolicyDecision("required_policy_unavailable", None, False, (), code, detail, False)


def _decide_verified(participation: Any, caller: Any, record: Any, report: Any, codes: Any = c.CODES) -> PolicyDecision:
    """INTERNAL. Only verify_and_decide may call this, with objects it produced itself. Not a public interface:
    a caller-supplied report is never authority."""
    try:
        if participation not in c.PARTICIPATION:
            return _refusal("required", caller, "participation_mismatch", "operation participation is not required or optional")
        if report is None:
            return _refusal(participation, caller, "selection_missing")
        if getattr(report, "ok", False) is not True:
            code = getattr(report, "code", None)
            dc, cause = getattr(report, "detail_code", None), getattr(report, "detail_cause", None)
            stage, member = getattr(report, "detail_stage", None), getattr(report, "detail_member", None)
            typed = ((dc, cause if type(cause) is str else None) + ((stage, member) if type(stage) is str and type(member) is str else ())
                     if type(dc) is str else None)
            return _refusal(participation, caller, code if code in codes else "selection_missing", typed=typed, codes=codes)
        if getattr(report, "participation", None) != participation:
            return _refusal(participation, caller, "participation_mismatch",
                            "the signed selection's participation does not equal the operation class")
        if record is None:
            return _refusal(participation, caller, "composition_record_invalid", "no record supplied")
        if getattr(record, "ok", False) is not True:
            code = getattr(record, "code", None)
            return _refusal(participation, caller, code if code in c.CODES else "composition_record_invalid")
        layers = getattr(report, "layers", None)
        if not isinstance(layers, dict) or layers.get("record_binding") != "pass":
            return _refusal(participation, caller, "record_identity_mismatch",
                            "the verification report has no passing record binding")
        body = getattr(record, "record", None)
        if not isinstance(body, dict) or not isinstance(body.get("payload"), dict):
            return _refusal(participation, caller, "composition_record_invalid", "record body is missing")
        recomputed = c.digest({k: v for k, v in body.items() if k != "record_digest"})
        if recomputed != body.get("record_digest") or c.digest(body["payload"]) != body.get("payload_digest"):
            return _refusal(participation, caller, "digest_mismatch", "record content was altered after validation")
        if getattr(report, "bound_record_digest", None) != recomputed:
            return _refusal(participation, caller, "record_digest_mismatch",
                            "the record is not the one the verified selection pinned")
        result = families.compose(caller, record)
        if not result.ok:
            return _refusal(participation, caller, result.code, result.detail)
        kind = "applied_deny_all" if result.deny_all else "applied"
        return PolicyDecision(kind, result.effective, result.deny_all, result.deny_all_fields, None, "", False)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal("required", caller, "selection_missing", "unexpected input")


def verify_and_decide(participation: Any, caller: Any, record_text: Any, selection_text: Any, context: Any,
                      trust: Any, verifier: Any, now: Any, key_admission: Any = None,
                      contract_version: Any = verify_mod.LEGACY_CONTRACT) -> PolicyDecision:
    """The single public verify-and-decide entrypoint. Pure: takes raw record and selection TEXT, parses and verifies both
    internally at one `now`, binds the verified selection to the exact record parsed here, and composes only on success.
    No caller-supplied report, parsed record or timestamped verification result is accepted, so reports cannot be
    fabricated, substituted, replayed (stale), mutated after verification, or paired with a different record.
    Required operations fail closed (never the caller policy); optional operations leave the caller policy unchanged.
    `key_admission` is the optional trust-boundary key policy (see `key_admission.py`); it is forwarded unchanged to
    `verify_selection`. `contract_version` selects the verification path: anything but exactly `r08-v1` makes built-in key
    admission mandatory (see `verify_selection`); the callback can only add refusals."""
    return _decide_text(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission, contract_version, False)


def _decide_text(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission, contract_version, v2):
    """The one implementation behind `verify_and_decide` (r08-v1 parser, closed `c.CODES`) and `verify_and_decide_v2` (r08-v2 parser,
    closed `CODES_V2`, `verify_selection_v2`)."""
    codes = v2_codes.CODES_V2 if v2 else c.CODES
    try:
        if participation not in c.PARTICIPATION:
            return _refusal("required", caller, "participation_mismatch", "operation participation is not required or optional")
        if selection_text is None:
            return _refusal(participation, caller, "selection_missing")
        sel = (v2_selection_mod.parse_selection_envelope_v2 if v2 else selection_mod.parse_selection_envelope)(selection_text)
        if not sel.ok:
            return _refusal(participation, caller, sel.code if sel.code in codes else "selection_missing", sel.detail, codes=codes)
        rec = record_mod.validate_record_text(record_text)
        if v2:
            report = verify_mod.verify_selection_v2(sel, context, trust, verifier, now, rec, key_admission)
        else:
            report = verify_mod.verify_selection(sel, context, trust, verifier, now, rec, key_admission, contract_version)
        return _decide_verified(participation, caller, rec, report, codes)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal(participation if participation in c.PARTICIPATION else "required", caller, "selection_missing", "unexpected input")


def verify_and_decide_v2(participation: Any, caller: Any, record_text: Any, selection_text: Any, context: Any,
                         trust: Any, verifier: Any, now: Any, key_admission: Any = None) -> PolicyDecision:
    """The r08-v2 verify-and-decide entry point: no `contract_version` parameter, hardwired to "r08-v2" (mandatory key
    admission, canonical base64, exact-type private copies). Delegates to `verify_and_decide`, the single implementation.
    Selection TEXT is parsed by the r08-v2 envelope parser (`v2_selection`); refusals use the closed `CODES_V2`. A withdrawal is
    never an application: it is `required_policy_unavailable` / `overlay_not_applied` with `selection_withdrawn`."""
    return _decide_text(participation, caller, record_text, selection_text, context, trust, verifier, now, key_admission,
                        verify_mod.V2_CONTRACT, True)
