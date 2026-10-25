"""Per-operation policy outcome for contract `r08-v1` (docs/r08-s01-contract.md section 5).

Participation is chosen per operation. Kinds:
  applied / applied_deny_all     a technically verified selection and valid record composed with the caller policy.
  overlay_not_applied            OPTIONAL operations only: any refusal leaves the caller policy unchanged. This is explicitly
                                 NOT denial and is not evidence of enforcement (frozen S04 semantics).
  required_policy_unavailable    REQUIRED operations only: any refusal. The caller policy is NEVER returned. Conceptually HOLD;
                                 the mapping to component failure classes is open decision LD-02.
`operationally_authorized` is always False: technical verification is not operational authorization.
"""
from dataclasses import dataclass
from typing import Any, Optional

from registry_successor import common as c
from registry_successor.compose import compose_f1a, normalize_caller


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


def _refusal(participation: Any, caller: Any, code: str, detail: str = "") -> PolicyDecision:
    assert code in c.CODES, code
    if participation == "optional":
        normalized = normalize_caller(caller)
        return PolicyDecision("overlay_not_applied", normalized if normalized is not None else caller, False, (), code,
                              detail or "optional overlay not applied; caller policy unchanged (not denial)", True)
    return PolicyDecision("required_policy_unavailable", None, False, (), code, detail, False)


def decide_policy(participation: Any, caller: Any, record: Any, report: Any) -> PolicyDecision:
    try:
        if participation not in c.PARTICIPATION:
            return _refusal("required", caller, "participation_mismatch", "operation participation is not required or optional")
        if report is None:
            return _refusal(participation, caller, "selection_missing")
        if getattr(report, "ok", False) is not True:
            code = getattr(report, "code", None)
            return _refusal(participation, caller, code if code in c.CODES else "selection_missing")
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
        result = compose_f1a(caller, record)
        if not result.ok:
            return _refusal(participation, caller, result.code, result.detail)
        kind = "applied_deny_all" if result.deny_all else "applied"
        return PolicyDecision(kind, result.effective, result.deny_all, result.deny_all_fields, None, "", False)
    except Exception:  # defensive: never an acceptance on unexpected input
        return _refusal("required", caller, "selection_missing", "unexpected input")
