"""Verify-and-decide of the parameterised engine (docs/r08-v7-contract.md section 3).

`verify_and_decide(profile, ...)` has no `contract_version` parameter: the contract is `profile.version`. It parses the selection with the profile's
envelope parser, validates the record with the profile's record validator (a document of any other contract refuses), verifies with
`verify.verify_selection`, binds the verified selection to the exact record parsed here, and composes with the profile's table only on success. Required
operations fail closed (never the caller policy); optional operations leave the caller policy unchanged and report `overlay_not_applied`, which is not
denial. `operationally_authorized` is always False. Refusals use the closed `CODES_V2` (no new code).

The decision shape is the existing `decision.PolicyDecision`. An optional-participation refusal returns the caller policy normalized with the caller
normalizer of the FIRST family in the profile's table (in table order) that accepts its shape, else the caller unchanged; it never composes anything.

A profile may hold several independent families; each record and each selection is for exactly one family under its own operation id, and this module
never combines two families.
"""
from typing import Any

from registry_successor import common as c
from registry_successor import v2_codes
from registry_successor.decision import PolicyDecision, TypedPolicyDecision
from registry_successor.engine import profile as p
from registry_successor.engine import record as record_e
from registry_successor.engine import selection as selection_e
from registry_successor.engine import verify as verify_e

CODES = v2_codes.CODES_V2


def _refusal(profile: p.ContractProfile, participation: Any, caller: Any, code: str, detail: str = "", typed: Any = None) -> PolicyDecision:
    assert code in CODES, code
    if participation == "optional":
        normalized = None
        for family in profile.families:
            normalized = p.lookup(profile, family).caller_normalizer(caller)
            if normalized is not None:
                break
        base = PolicyDecision("overlay_not_applied", normalized if normalized is not None else caller, False, (), code,
                              detail or "optional overlay not applied; caller policy unchanged (not denial)", True)
    else:
        base = PolicyDecision("required_policy_unavailable", None, False, (), code, detail, False)
    if typed is None:
        return base
    return TypedPolicyDecision(base.kind, base.effective, base.deny_all, base.deny_all_fields, base.code, base.detail, base.caller_unchanged,
                               base.operationally_authorized, detail_code=typed[0], detail_cause=typed[1],
                               detail_stage=typed[2] if len(typed) > 2 else None, detail_member=typed[3] if len(typed) > 2 else None)


def decide_verified(profile: p.ContractProfile, participation: Any, caller: Any, record: Any, report: Any) -> PolicyDecision:
    p.require_profile(profile)
    try:
        if type(participation) is not str or participation not in c.PARTICIPATION:
            return _refusal(profile, "required", caller, "participation_mismatch", "operation participation is not required or optional")
        if report is None:
            return _refusal(profile, participation, caller, "selection_missing")
        if getattr(report, "ok", False) is not True:
            code = getattr(report, "code", None)
            dc, cause = getattr(report, "detail_code", None), getattr(report, "detail_cause", None)
            stage, member = getattr(report, "detail_stage", None), getattr(report, "detail_member", None)
            typed = ((dc, cause if type(cause) is str else None) + ((stage, member) if type(stage) is str and type(member) is str else ())
                     if type(dc) is str else None)
            return _refusal(profile, participation, caller, code if code in CODES else "selection_missing", typed=typed)
        if getattr(report, "participation", None) != participation:
            return _refusal(profile, participation, caller, "participation_mismatch",
                            "the signed selection's participation does not equal the operation class")
        if record is None:
            return _refusal(profile, participation, caller, "composition_record_invalid", "no record supplied")
        if getattr(record, "ok", False) is not True:
            code = getattr(record, "code", None)
            return _refusal(profile, participation, caller, code if code in c.CODES else "composition_record_invalid")
        layers = getattr(report, "layers", None)
        if not isinstance(layers, dict) or layers.get("record_binding") != "pass":
            return _refusal(profile, participation, caller, "record_identity_mismatch", "the verification report has no passing record binding")
        body = getattr(record, "record", None)
        if not isinstance(body, dict) or not isinstance(body.get("payload"), dict):
            return _refusal(profile, participation, caller, "composition_record_invalid", "record body is missing")
        recomputed = c.digest({k: v for k, v in body.items() if k != "record_digest"})
        if recomputed != body.get("record_digest") or c.digest(body["payload"]) != body.get("payload_digest"):
            return _refusal(profile, participation, caller, "digest_mismatch", "record content was altered after validation")
        if getattr(report, "bound_record_digest", None) != recomputed:
            return _refusal(profile, participation, caller, "record_digest_mismatch", "the record is not the one the verified selection pinned")
        result = p.compose_for(profile, profile.version, caller, record)
        if not result.ok:
            return _refusal(profile, participation, caller, result.code, result.detail)
        kind = "applied_deny_all" if result.deny_all else "applied"
        return PolicyDecision(kind, result.effective, result.deny_all, result.deny_all_fields, None, result.detail, False)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal(profile, "required", caller, "selection_missing", "unexpected input")


def verify_and_decide(profile: p.ContractProfile, participation: Any, caller: Any, record_text: Any, selection_text: Any, context: Any, trust: Any,
                      verifier: Any, now: Any, key_admission: Any = None) -> PolicyDecision:
    """Pure: takes raw record and selection TEXT, parses and verifies both internally at one `now`, and composes only on success. A withdrawal is never
    an application (`selection_withdrawn`). Never raises on hostile input (a non-profile is a programming error)."""
    p.require_profile(profile)
    try:
        if type(participation) is not str or participation not in c.PARTICIPATION:
            return _refusal(profile, "required", caller, "participation_mismatch", "operation participation is not required or optional")
        if selection_text is None:
            return _refusal(profile, participation, caller, "selection_missing")
        sel = selection_e.parse_selection_envelope(profile, selection_text)
        if not sel.ok:
            return _refusal(profile, participation, caller, sel.code if sel.code in CODES else "selection_missing", sel.detail)
        rec = record_e.validate_record_text(profile, record_text)
        report = verify_e.verify_selection(profile, sel, context, trust, verifier, now, rec, key_admission)
        return decide_verified(profile, participation, caller, rec, report)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal(profile, participation if participation in c.PARTICIPATION else "required", caller, "selection_missing", "unexpected input")
