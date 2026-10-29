"""Record validation of the parameterised engine (docs/r08-v7-contract.md section 3). The same checks, order and codes as `record.validate_record_text` and
the frozen `v3_record`..`v6_record` validators (shape, values, supersession and digest checks are reused from `record.py`), but the record must carry
exactly `contract_version` == `profile.version` and its family is looked up in the profile's table. A document of any other contract version refuses
`contract_unsupported`; no fallback or implicit upgrade. Pure; never raises. Non-authorizing; unqualified.
"""
import copy
from typing import Any

from registry_successor import common as c
from registry_successor import record as record_mod
from registry_successor.engine import profile as p


def validate_record_text(profile: p.ContractProfile, text: Any) -> "record_mod.RecordResult":
    p.require_profile(profile)
    try:
        loaded = c.load_document(text)
        if not loaded.ok:
            return record_mod._refuse(loaded.code, loaded.detail)
        body = loaded.value
        if not isinstance(body, dict):
            return record_mod._refuse("field_type_invalid", "document is not an object")
        version = body.get("contract_version")
        if type(version) is not str or version != profile.version:
            return record_mod._refuse("contract_unsupported")
        if body.get("kind") != "record":
            return record_mod._refuse("kind_unsupported")
        spec = p.lookup(profile, body.get("family"))
        if spec is None:
            return record_mod._refuse("family_unsupported")
        code = record_mod._shape(body, spec) or record_mod._values(body, spec)
        if code:
            return record_mod._refuse(code)
        if not record_mod._supersession_ok(body):
            return record_mod._refuse("supersession_invalid")
        if body["payload_digest"] != c.digest(body["payload"]):
            return record_mod._refuse("digest_mismatch", "payload_digest")
        if body["record_digest"] != c.digest({k: v for k, v in body.items() if k != "record_digest"}):
            return record_mod._refuse("digest_mismatch", "record_digest")
        return record_mod.RecordResult(True, None, "", copy.deepcopy(body), body["record_digest"])
    except Exception:  # defensive: an unexpected shape error is a refusal, never an acceptance
        return record_mod._refuse("field_type_invalid", "unexpected structure")
