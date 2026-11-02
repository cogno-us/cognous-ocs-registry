"""Evidence-verifier adapter for a replay-style enforcing consumer (RW-01-F4-PoC). Constructed BY the enforcing consumer.

It maps one plain-dict request onto `registry_successor.v2_verified_selection` (the single place that states the eleven-layer admission
conjunction) and returns one plain-dict verdict. It lives here, and not in `registry_successor` or `registry_adapters`, because it needs
both and the repository's guards keep those two packages from importing each other.

Pins (the enforcing consumer's duties that the core cannot perform): the verifier must be EXACTLY the Ed25519 adapter class (no subclass,
no fake) and the key admission must be that verifier's own `key_admission`. A verifier that is unavailable is represented by `None` (or by
`load()` when the backend cannot be used); every request then yields `ok False`, code `verifier_unavailable`. There is NO way to pass a
verdict, report or "already verified" flag in: the only inputs are the signed texts and the operator-supplied trust inputs. The adapter
never raises into its caller, returns no signer key id, holds no key, no trust root and no state, and reads no clock (the verification time
is an input). All verdict members are verifier-asserted: this module cannot make them trustworthy, and a permissive verifier object is
excluded only by the exact-type pin above. Existing reason codes only. Mechanism with caller-supplied trust inputs: claim A only.
"""
import datetime
import hashlib
from typing import Any, Optional

from registry_adapters.ed25519_verifier import Ed25519Unavailable, Ed25519Verifier
from registry_successor import v2_age_bounds as ab
from registry_successor import v2_verified_selection as vs
from registry_successor import verify as verify_mod
from registry_successor.common import ExpectedContext

__all__ = ["RegistryEvidenceVerifierV2", "REQUEST_CONTRACT", "VERDICT_CONTRACT", "REQUEST_KEYS", "VERDICT_KEYS", "IMPLEMENTATION"]

REQUEST_CONTRACT = "registry-evidence-verification-request/0.1"
VERDICT_CONTRACT = "registry-evidence-verdict/0.1"
REGISTRY_CONTRACT = "r08-v2"
IMPLEMENTATION = {"name": "registry-evidence-verifier-v2", "registry_revision": "085db15299923c170ce201b86c59a54e2ba9e462+rw01-f4-poc"}
REQUEST_KEYS = frozenset((
    "contract", "family", "registry_contract", "selection_text", "record_text", "expected_context", "expected_operation_id",
    "trust_snapshot", "verification_time", "verification_time_utc", "min_trust_snapshot_version", "last_accepted_snapshot", "host_policy"))
VERDICT_KEYS = frozenset((
    "contract", "ok", "code", "authenticated", "layers", "family", "registry_contract", "selection_text_sha256", "record_text_sha256",
    "verification_time_utc", "trust_snapshot_id", "trust_snapshot_version", "trust_snapshot_fingerprint", "floors_applied",
    "epoch_floor_applied", "issuer_id", "selection_id", "epoch", "selection_digest", "bound_record_digest", "effective_policy_digest",
    "effective_values", "verifier_implementation"))
_CONTEXT_KEYS = ("consumer_id", "tenant", "institution", "authority_domain", "operation")
_HOST_KEYS = frozenset(ab.F4_FIELDS)


class _Refusal(Exception):
    def __init__(self, code: str):
        self.code = code


def _sha256_hex(text: Any) -> Optional[str]:
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest() if type(text) is str else None
    except Exception:
        return None


class RegistryEvidenceVerifierV2:
    def __init__(self, verifier: Any, key_admission: Any) -> None:
        if verifier is None:
            if key_admission is not None:
                raise TypeError("an unavailable verifier takes no key admission")
        else:
            if type(verifier) is not Ed25519Verifier:
                raise TypeError("the verifier must be exactly the Ed25519 adapter class")
            if getattr(key_admission, "__self__", None) is not verifier or getattr(key_admission, "__func__", None) is not Ed25519Verifier.key_admission:
                raise TypeError("the key admission must be that verifier's own key_admission")
        self._verifier = verifier
        self._key_admission = key_admission

    @classmethod
    def load(cls) -> "RegistryEvidenceVerifierV2":
        """The adapter over a freshly built Ed25519 verifier, or an adapter that answers `verifier_unavailable` when the backend is unusable."""
        try:
            verifier = Ed25519Verifier()
        except Ed25519Unavailable:
            return cls(None, None)
        return cls(verifier, verifier.key_admission)

    def verify_selection_evidence(self, request: Any) -> dict:
        echo = {}
        try:
            return self._verify(request, echo)
        except _Refusal as refusal:
            return _verdict(False, refusal.code, echo)
        except Exception:
            return _verdict(False, "field_invalid", echo)

    def _verify(self, request: Any, echo: dict) -> dict:
        if type(request) is not dict:
            raise _Refusal("field_invalid")
        req = dict(request)  # one read of every member
        if set(req) != REQUEST_KEYS:
            raise _Refusal("field_invalid")
        echo["selection_text_sha256"] = _sha256_hex(req["selection_text"])
        echo["record_text_sha256"] = _sha256_hex(req["record_text"])
        if type(req["contract"]) is not str or req["contract"] != REQUEST_CONTRACT:
            raise _Refusal("contract_unsupported")
        if type(req["registry_contract"]) is not str or req["registry_contract"] != REGISTRY_CONTRACT:
            raise _Refusal("contract_unsupported")
        if type(req["family"]) is not str or req["family"] != ab.FAMILY_F4:
            raise _Refusal("family_unsupported")
        if type(req["selection_text"]) is not str or type(req["record_text"]) is not str:
            raise _Refusal("input_not_text")
        ctx_raw = req["expected_context"]
        if type(ctx_raw) is not dict or set(ctx_raw) != set(_CONTEXT_KEYS) or any(type(ctx_raw[k]) is not str for k in _CONTEXT_KEYS):
            raise _Refusal("selection_scope_mismatch")
        context = ExpectedContext(*(ctx_raw[k] for k in _CONTEXT_KEYS))
        if type(req["expected_operation_id"]) is not str or req["expected_operation_id"] != context.operation:
            raise _Refusal("selection_operation_mismatch")
        when, when_utc = req["verification_time"], req["verification_time_utc"]
        if type(when) is not datetime.datetime or when.tzinfo is None or when.utcoffset() is None or when.microsecond != 0:
            raise _Refusal("time_unavailable")
        if type(when_utc) is not str or when_utc != when.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"):
            raise _Refusal("time_unavailable")
        echo["verification_time_utc"] = when_utc
        host = req["host_policy"]
        if type(host) is not dict or set(host) != _HOST_KEYS:
            raise _Refusal("composition_caller_invalid")
        last = req["last_accepted_snapshot"]
        if type(last) is list and len(last) == 2:
            last = (last[0], last[1])
        if self._verifier is None:
            raise _Refusal("verifier_unavailable")
        result = vs.verify_f4_selection_v2(
            req["selection_text"], req["record_text"], context, req["trust_snapshot"], self._verifier, when,
            min_trust_snapshot_version=req["min_trust_snapshot_version"], last_accepted_snapshot=last, key_admission=self._key_admission)
        echo["result"] = result
        if result.admitted is not True:
            raise _Refusal(result.code)
        policy = vs.recompute_f4_effective_policy(result, host)
        echo["policy"] = policy
        if policy.ok is not True:
            raise _Refusal(policy.code)
        return _verdict(True, None, echo)


def _verdict(ok: bool, code: Optional[str], echo: dict) -> dict:
    result, policy = echo.get("result"), echo.get("policy")
    good = ok is True and result is not None and policy is not None
    layers = dict(result.layers) if result is not None else {name: "not_evaluated" for name in verify_mod.LAYERS_V2}
    return {
        "contract": VERDICT_CONTRACT, "ok": good, "code": None if good else (code if type(code) is str else "field_invalid"),
        "authenticated": bool(result.authenticated) if result is not None else False, "layers": layers,
        "family": ab.FAMILY_F4, "registry_contract": REGISTRY_CONTRACT,
        "selection_text_sha256": echo.get("selection_text_sha256"), "record_text_sha256": echo.get("record_text_sha256"),
        "verification_time_utc": echo.get("verification_time_utc"),
        "trust_snapshot_id": result.trust_snapshot_id if result is not None else None,
        "trust_snapshot_version": result.trust_snapshot_version if result is not None else None,
        "trust_snapshot_fingerprint": result.trust_snapshot_fingerprint if result is not None else None,
        "floors_applied": {"min_trust_snapshot_version": good and result.min_trust_snapshot_version is not None,
                           "last_accepted_snapshot": good and result.last_accepted_snapshot is not None},  # reported only for an ok verdict
        "epoch_floor_applied": bool(result.epoch_floor_applied) if result is not None else False,
        "issuer_id": result.issuer_id if good else None, "selection_id": result.selection_id if good else None,
        "epoch": result.epoch if good else None, "selection_digest": result.selection_digest if good else None,
        "bound_record_digest": result.record_digest if good else None,
        "effective_policy_digest": policy.effective_policy_digest if good else None,
        "effective_values": dict(policy.effective) if good else None,
        "verifier_implementation": dict(IMPLEMENTATION),
    }
