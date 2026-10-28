"""`r08-v4` record validation (docs/r08-v4-contract.md). The same checks, order and codes as `record.validate_record_text` and
`decision.validate_record_text_v2` (shape, values, supersession and digest checks are reused from `record.py`), but the record must carry exactly
`contract_version` `r08-v4` and its family is looked up in the `r08-v4` table (`v4_families.FAMILIES_V4`, one family). An `r08-v1` or `r08-v2`
document refuses `contract_unsupported` here; an `r08-v4` document refuses `contract_unsupported` at the unchanged v1 and v2 validators. No fallback
or implicit upgrade. Pure; never raises. Non-authorizing; unqualified.
"""
import copy
from typing import Any

from registry_successor import common as c
from registry_successor import record as record_mod
from registry_successor import v4_families


def validate_record_text_v4(text: Any) -> "record_mod.RecordResult":
    try:
        loaded = c.load_document(text)
        if not loaded.ok:
            return record_mod._refuse(loaded.code, loaded.detail)
        body = loaded.value
        if not isinstance(body, dict):
            return record_mod._refuse("field_type_invalid", "document is not an object")
        version = body.get("contract_version")
        if type(version) is not str or version != v4_families.CONTRACT_V4:
            return record_mod._refuse("contract_unsupported")
        if body.get("kind") != "record":
            return record_mod._refuse("kind_unsupported")
        spec = v4_families.lookup_v4(body.get("family"))
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
