"""`r08-v5` verify-and-decide entry point (docs/r08-v5-contract.md).

`verify_and_decide_v5` has no `contract_version` parameter and is hardwired to `r08-v5`: it parses the selection with the r08-v5 envelope parser,
validates the record with the r08-v5 record validator (an r08-v1/r08-v2/r08-v3/r08-v4 document refuses; an r08-v5 document refuses at the v1/v2/v3/v4 entry points),
verifies with `v5_verify.verify_selection_v5`, binds the verified selection to the exact record parsed here, and composes with the r08-v5 table
only on success. Required operations fail closed (never the caller policy); optional operations leave the caller policy unchanged and report
`overlay_not_applied`, which is not denial. `operationally_authorized` is always False. Refusals use the closed `CODES_V2` (no new code).

The decision shape is the existing `decision.PolicyDecision` (a deny-all result carries `deny_all=True` and the deny-all field names, including
`max_effects` when the record's `max_effects` is 0: the consumer builds NO policy and dispatches NO effect). An optional-participation refusal
returns the caller policy normalized with the F5 unreadable-policy caller normalizer, not the v1 one.
"""
from typing import Any

from registry_successor import common as c
from registry_successor import decision as d
from registry_successor import v2_codes
from registry_successor import v5_class_unreadable
from registry_successor import v5_families
from registry_successor import v5_record
from registry_successor import v5_selection
from registry_successor import v5_verify
from registry_successor.decision import PolicyDecision, TypedPolicyDecision

CODES = v2_codes.CODES_V2


def _refusal(participation: Any, caller: Any, code: str, detail: str = "", typed: Any = None) -> PolicyDecision:
    assert code in CODES, code
    if participation == "optional":
        spec = v5_families.lookup_v5(v5_class_unreadable.FAMILY_F5U)
        normalized = spec.caller_normalizer(caller)
        base = PolicyDecision("overlay_not_applied", normalized if normalized is not None else caller, False, (), code,
                              detail or "optional overlay not applied; caller policy unchanged (not denial)", True)
    else:
        base = PolicyDecision("required_policy_unavailable", None, False, (), code, detail, False)
    if typed is None:
        return base
    return TypedPolicyDecision(base.kind, base.effective, base.deny_all, base.deny_all_fields, base.code, base.detail, base.caller_unchanged,
                               base.operationally_authorized, detail_code=typed[0], detail_cause=typed[1],
                               detail_stage=typed[2] if len(typed) > 2 else None, detail_member=typed[3] if len(typed) > 2 else None)


def _decide_verified(participation: Any, caller: Any, record: Any, report: Any) -> PolicyDecision:
    try:
        if type(participation) is not str or participation not in c.PARTICIPATION:
            return _refusal("required", caller, "participation_mismatch", "operation participation is not required or optional")
        if report is None:
            return _refusal(participation, caller, "selection_missing")
        if getattr(report, "ok", False) is not True:
            code = getattr(report, "code", None)
            dc, cause = getattr(report, "detail_code", None), getattr(report, "detail_cause", None)
            stage, member = getattr(report, "detail_stage", None), getattr(report, "detail_member", None)
            typed = ((dc, cause if type(cause) is str else None) + ((stage, member) if type(stage) is str and type(member) is str else ())
                     if type(dc) is str else None)
            return _refusal(participation, caller, code if code in CODES else "selection_missing", typed=typed)
        if getattr(report, "participation", None) != participation:
            return _refusal(participation, caller, "participation_mismatch", "the signed selection's participation does not equal the operation class")
        if record is None:
            return _refusal(participation, caller, "composition_record_invalid", "no record supplied")
        if getattr(record, "ok", False) is not True:
            code = getattr(record, "code", None)
            return _refusal(participation, caller, code if code in c.CODES else "composition_record_invalid")
        layers = getattr(report, "layers", None)
        if not isinstance(layers, dict) or layers.get("record_binding") != "pass":
            return _refusal(participation, caller, "record_identity_mismatch", "the verification report has no passing record binding")
        body = getattr(record, "record", None)
        if not isinstance(body, dict) or not isinstance(body.get("payload"), dict):
            return _refusal(participation, caller, "composition_record_invalid", "record body is missing")
        recomputed = c.digest({k: v for k, v in body.items() if k != "record_digest"})
        if recomputed != body.get("record_digest") or c.digest(body["payload"]) != body.get("payload_digest"):
            return _refusal(participation, caller, "digest_mismatch", "record content was altered after validation")
        if getattr(report, "bound_record_digest", None) != recomputed:
            return _refusal(participation, caller, "record_digest_mismatch", "the record is not the one the verified selection pinned")
        result = v5_families.compose_for_v5(v5_families.CONTRACT_V5, caller, record)
        if not result.ok:
            return _refusal(participation, caller, result.code, result.detail)
        kind = "applied_deny_all" if result.deny_all else "applied"
        return PolicyDecision(kind, result.effective, result.deny_all, result.deny_all_fields, None, result.detail, False)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal("required", caller, "selection_missing", "unexpected input")


def verify_and_decide_v5(participation: Any, caller: Any, record_text: Any, selection_text: Any, context: Any, trust: Any, verifier: Any,
                         now: Any, key_admission: Any = None) -> PolicyDecision:
    """The single public r08-v5 verify-and-decide entry point. Pure: takes raw record and selection TEXT, parses and verifies both internally at one
    `now`, and composes only on success. A withdrawal is never an application (`selection_withdrawn`)."""
    try:
        if type(participation) is not str or participation not in c.PARTICIPATION:
            return _refusal("required", caller, "participation_mismatch", "operation participation is not required or optional")
        if selection_text is None:
            return _refusal(participation, caller, "selection_missing")
        sel = v5_selection.parse_selection_envelope_v5(selection_text)
        if not sel.ok:
            return _refusal(participation, caller, sel.code if sel.code in CODES else "selection_missing", sel.detail)
        rec = v5_record.validate_record_text_v5(record_text)
        report = v5_verify.verify_selection_v5(sel, context, trust, verifier, now, rec, key_admission)
        return _decide_verified(participation, caller, rec, report)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal(participation if participation in c.PARTICIPATION else "required", caller, "selection_missing", "unexpected input")
